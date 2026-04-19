"""
Speech-to-Text with Wake Word Detection for Voice Assistant.
Uses RealTimeSTT for real-time transcription with built-in wake word detection.

Conversation Mode:
  - After the AI responds, the mic stays open for follow-up questions
  - No need to say "Wolf" again within 60 seconds
  - Say "stop" or "wolf stop" to interrupt TTS and go back to listening
  - After 60 seconds of silence, returns to wake word mode
"""

import re
import threading
import time
import os
from typing import Optional, Callable, Any
from config import (  
    WAKE_WORD, REALTIMESTT_MODEL, WAKE_WORD_SENSITIVITY,
    CUSTOM_PPN_PATH, GRAY, RESET, CYAN, YELLOW, GREEN, RED,
    WAKE_WORD_DETECTION_METHOD
)

# ── Constants ────────────────────────────────────────────────────────────────
CONVERSATION_TIMEOUT = 60          # Seconds of silence before leaving convo mode
STOP_PHRASES  = {"stop", "please stop", "shut up", "be quiet", "quit", "please quit", "cancel", "abort", "halt", "stop talking", "quiet", "hey stop", "wolf stop", "stop now"}
WOLF_ALIASES  = ["wolf", "wolff", "woof", "wall", "well", "holy", "bolly", "wulf", "worth"]


class STTListener:
    """
    Real-time STT listener with wake word detection and conversation mode.

    Modes:
      WAKE_WORD  – waits for 'Wolf' before recording
      CONVERSATION – stays open after AI responds; times out after 60 s silence
    """

    MODE_WAKE_WORD    = "wake_word"
    MODE_CONVERSATION = "conversation"

    def __init__(self, wake_word_callback: Callable, speech_callback: Callable,
                 stop_callback: Optional[Callable] = None):
        self.wake_word_callback = wake_word_callback
        self.speech_callback    = speech_callback
        self.stop_callback      = stop_callback   # called when user says "stop"

        self.running  = False
        self.recorder: Optional[Any] = None
        self.initialized = False
        self.listening_thread: Optional[threading.Thread] = None

        # Conversation-mode state
        self._mode = self.MODE_WAKE_WORD
        self._mode_lock = threading.Lock()
        self._last_activity = 0.0          # timestamp of last user speech
        self._timeout_timer: Optional[threading.Timer] = None

        self._is_paused = False
        print(f"{CYAN}[STT] Initializing RealTimeSTT listener...{RESET}")
        print(f"{CYAN}[STT] Wake word: '{WAKE_WORD}'{RESET}")
        print(f"{CYAN}[STT] Detection method: RealTimeSTT built-in wake word detection{RESET}")

    # ── Public API ────────────────────────────────────────────────────────────

    def enter_conversation_mode(self):
        """Call this after the AI finishes responding to keep the mic open."""
        with self._mode_lock:
            self._mode = self.MODE_CONVERSATION
            self._last_activity = time.time()
        self._reset_timeout_timer()
        
        # Update system status to show listening
        try:
            from backend_api import system_status
            system_status["isListening"] = True
        except ImportError:
            # Backend not available, skip status update
            pass
        
        print(f"{GREEN}[STT] 💬 Conversation mode active (timeout: {CONVERSATION_TIMEOUT}s){RESET}")

    def exit_conversation_mode(self):
        """Return to wake-word gating."""
        with self._mode_lock:
            self._mode = self.MODE_WAKE_WORD
        self._cancel_timeout_timer()
        
        # Update system status to show not listening
        try:
            from backend_api import system_status
            system_status["isListening"] = False
        except ImportError:
            # Backend not available, skip status update
            pass
        
        print(f"{CYAN}[STT] 🔇 Returned to wake-word mode.{RESET}")

    @property
    def in_conversation_mode(self) -> bool:
        with self._mode_lock:
            return self._mode == self.MODE_CONVERSATION

    def pause_listening(self):
        """Pause processing of incoming audio (used during TTS speaking)."""
        self._is_paused = True
        print(f"{YELLOW}[STT] ⏸ Listening paused (AI is speaking).{RESET}")

    def resume_listening(self):
        """Resume processing of incoming audio."""
        self._is_paused = False
        # Small delay to ensure any echo from speakers is gone
        time.sleep(0.1)
        print(f"{GREEN}[STT] ▶ Listening resumed.{RESET}")

    # ── Initialization ────────────────────────────────────────────────────────

    def initialize(self) -> bool:
        """Initialize RealTimeSTT with wake word detection."""
        import os as _os
        try:
            from RealtimeSTT import AudioToTextRecorder  
            import torch  
            import pvporcupine  

            print(f"{CYAN}[STT] Loading RealTimeSTT...{RESET}")

            cuda_available = torch.cuda.is_available()
            if cuda_available:
                cuda_name = torch.cuda.get_device_name(torch.cuda.current_device())
                print(f"{GREEN}[STT] ✓ CUDA is available (Device: {cuda_name}){RESET}")
            else:
                print(f"{YELLOW}[STT] ⚠ CUDA not available, will use CPU{RESET}")

            from core.settings_store import settings  
            porcupine_key = settings.get("picovoice.key", "")
            ppn_path      = settings.get("picovoice.ppn_path", "")

            if not ppn_path or not _os.path.exists(ppn_path):
                if _os.path.exists(CUSTOM_PPN_PATH):
                    ppn_path = CUSTOM_PPN_PATH
                    print(f"{GREEN}[STT] ✨ Auto-detected high-performance wake word at: {ppn_path}{RESET}")

            # MONKEY-PATCH: inject access_key + keyword_paths into pvporcupine.create
            original_pv_create = pvporcupine.create
            def patched_pv_create(*args, **kwargs):
                import os as _os2
                if porcupine_key:
                    kwargs['access_key'] = porcupine_key
                active_ppn = settings.get("picovoice.ppn_path", ppn_path)
                if active_ppn and _os2.path.exists(active_ppn):
                    kwargs['keyword_paths'] = [active_ppn]
                    kwargs.pop('keywords', None)
                return original_pv_create(*args, **kwargs)
            pvporcupine.create = patched_pv_create

            if porcupine_key:
                print(f"{GREEN}[STT] 🦔 High-performance Porcupine engine requested.{RESET}")
                backend     = "pvporcupine"
                detect_word = "wolf"
            elif WAKE_WORD.lower() in ["jarvis", "alexa", "hey_mycroft", "hey_jarvis", "hey_rhasspy"]:
                print(f"{CYAN}[STT] Using built-in wake word for '{WAKE_WORD}'{RESET}")
                backend     = "openwakeword"
                detect_word = WAKE_WORD
            else:
                print(f"{YELLOW}[STT] Custom wake word detected. Using transcription mode.{RESET}")
                backend     = "none"
                detect_word = ""

            try:
                device = "cuda" if cuda_available else "cpu"
                print(f"{CYAN}[STT] 🚀 Initializing recorder (device={device}, compute_type=int8)...{RESET}")
                self.recorder = AudioToTextRecorder(
                    model=REALTIMESTT_MODEL,
                    language="en",
                    device=device,
                    compute_type="int8", # Dramatically reduces VRAM usage
                    spinner=False,
                    use_microphone=True,
                    wakeword_backend="none" if WAKE_WORD_DETECTION_METHOD == "transcription" else backend,
                    wake_words=detect_word if WAKE_WORD_DETECTION_METHOD != "transcription" else "",
                )
            except RuntimeError as e:
                if "cudaErrorMemoryAllocation" in str(e) or "out of memory" in str(e).lower():
                    print(f"{RED}[STT] ⚠️ CUDA Out of Memory! Falling back to CPU for STT...{RESET}")
                    self.recorder = AudioToTextRecorder(
                        model=REALTIMESTT_MODEL,
                        language="en",
                        device="cpu",
                        compute_type="int8",
                        spinner=False,
                        use_microphone=True,
                        wakeword_backend="none" if WAKE_WORD_DETECTION_METHOD == "transcription" else backend,
                        wake_words=detect_word if WAKE_WORD_DETECTION_METHOD != "transcription" else "",
                    )
                else:
                    raise e
            except Exception as e:
                print(f"{RED}[STT] ✗ Failed to initialize recorder: {e}{RESET}")
                # Fallback to basic configuration
                try:
                    self.recorder = AudioToTextRecorder(
                        model="tiny.en",
                        language="en", 
                        device="cpu",
                        spinner=False,
                        use_microphone=True,
                        wakeword_backend="none"
                    )
                    print(f"{GREEN}[STT] ✓ Using fallback configuration{RESET}")
                except Exception as fallback_error:
                    print(f"{RED}[STT] ✗ Complete STT failure: {fallback_error}{RESET}")
                    raise

            self.initialized = True
            print(f"{CYAN}[STT] ✓ RealTimeSTT initialized (model: {REALTIMESTT_MODEL}){RESET}")
            return True

        except ImportError:
            print(f"{GRAY}[STT] ✗ RealTimeSTT not installed. Install with: pip install realtimestt{RESET}")
            return False
        except Exception as e:
            print(f"{GRAY}[STT] ✗ Initialization error: {e}{RESET}")
            import traceback; traceback.print_exc()
            return False

    # ── Wake-word callback ────────────────────────────────────────────────────

    def _on_wakeword_detected(self):
        """Fired by Porcupine when the hardware detects 'Wolf'."""
        print(f"\n{CYAN}[STT] 👂 Wake word '{WAKE_WORD}' detected! Listening...{RESET}")
        if self.wake_word_callback:
            self.wake_word_callback()  

    # ── Timeout timer ─────────────────────────────────────────────────────────

    def _reset_timeout_timer(self):
        self._cancel_timeout_timer()
        self._timeout_timer = threading.Timer(CONVERSATION_TIMEOUT, self._on_conversation_timeout)
        self._timeout_timer.daemon = True  
        self._timeout_timer.start()  

    def _cancel_timeout_timer(self):
        if self._timeout_timer:
            self._timeout_timer.cancel()  
            self._timeout_timer = None

    def _on_conversation_timeout(self):
        print(f"{CYAN}[STT] ⏰ Conversation timed out after {CONVERSATION_TIMEOUT}s. Returning to wake-word mode.{RESET}")
        self.exit_conversation_mode()

    # ── Main listener loop ────────────────────────────────────────────────────

    def start(self):
        if not self.initialized:
            print(f"{YELLOW}[STT] Not initialized. Call initialize() first.{RESET}")
            return False
        if self.running:
            return True

        self.running = True
        print(f"{CYAN}[STT] Starting RealTimeSTT listener...{RESET}")
        self.listening_thread = threading.Thread(target=self._run_listener, daemon=True)
        self.listening_thread.start()  
        print(f"{CYAN}[STT] ✓ Listener started{RESET}")
        return True

    def _run_listener(self):
        """Main loop. Handles both wake-word mode and conversation mode."""
        try:
            print(f"{GRAY}[STT] 🔄 Starting transcription loop...{RESET}")

            while self.running:
                if not self.recorder:
                    time.sleep(0.05)
                    continue

                if self.in_conversation_mode:
                    # ── Conversation mode: listen directly, no wake word gate ──
                    print(f"{GRAY}[STT] 💬 Listening for follow-up...{RESET}")
                else:
                    print(f"{GRAY}[STT] ⏳ Waiting for wake word '{WAKE_WORD}'...{RESET}")

                t0   = time.time()
                try:
                    text = str(self.recorder.text() or "")  
                except (BrokenPipeError, ConnectionError) as e:
                    print(f"{RED}[STT] ✗ Broken Pipe detected: {e}. Attempting recovery...{RESET}")
                    if self.running:
                        self.initialize()  # Re-initialize recorder
                    continue
                except Exception as e:
                    print(f"{RED}[STT] ✗ Recorder error: {e}{RESET}")
                    if not self.running:
                        break
                    time.sleep(0.5)
                    continue

                elapsed = time.time() - t0

                if self._is_paused:
                    # Continue the loop but discard everything until resumed
                    # This prevents the feedback loop where AI hears itself
                    continue

                if not text or not text.strip():
                    if self.in_conversation_mode:
                        # Silence in convo mode — timer handles exit
                        continue
                    print(f"{GRAY}[STT] ⚠ No text received or text is empty{RESET}")
                    continue

                print(f"{CYAN}[STT] ✓ Transcription ({elapsed:.2f}s): '{text}'{RESET}")

                text_lower    = text.lower().strip()
                text_original = text.strip()
                text_clean    = text_original

                # ── Stop / interrupt detection ────────────────────────────────
                # Check for exact stop commands (optionally prefixed by wake word)
                check_text = text_lower
                for alias in WOLF_ALIASES + ["hey wolf", "hey wolff"]:
                    if check_text.startswith(alias):  
                        check_text = check_text[len(alias):].strip()  
                        break
                
                normalized = re.sub(r"[^a-z\s]", " ", check_text.lower())
                normalized = re.sub(r"\s+", " ", normalized).strip()
                
                print(f"{YELLOW}[STT] Checking for stop command in: '{normalized}'{RESET}")
                
                is_stop = normalized in STOP_PHRASES
                if not is_stop:
                    natural_stop_patterns = [
                        r"^(please\s+)?stop(\s+now)?$",
                        r"^(please\s+)?(can you\s+)?stop(\s+talking)?(\s+please)?$",
                        r"^(please\s+)?(be\s+quiet|shut\s+up|cancel|abort|halt)(\s+please)?$",
                    ]
                    is_stop = any(re.match(p, normalized) for p in natural_stop_patterns)
                
                if is_stop:
                    print(f"{YELLOW}[STT] 🛑 Stop command detected! Text: '{check_text}'{RESET}")
                    if self.stop_callback:
                        print(f"{YELLOW}[STT] 📞 Calling stop callback...{RESET}")
                        self.stop_callback()  
                    # Keep follow-up listening open after interruption.
                    self.enter_conversation_mode()
                    continue

                # ── Wake-word stripping ───────────────────────────────────────
                found_alias = next((a for a in WOLF_ALIASES if a in text_lower), None)
                if found_alias:
                    pattern = re.compile(re.escape(found_alias), re.IGNORECASE)
                    m = pattern.search(text_original)
                    if m:
                        text_clean = text_original[m.end():].strip()  
                        print(f"{GREEN}[STT] ✨ Wake word '{found_alias}' stripped.{RESET}")

                    # Fire wake-word callback if hardware hasn't already
                    if not self.in_conversation_mode and self.wake_word_callback:
                        self.wake_word_callback()  
                    
                    # Enter conversation mode immediately after wake word detection
                    if not self.in_conversation_mode:
                        self.enter_conversation_mode()

                # ── Guard: only wake-word said, no command ────────────────────
                if not text_clean:
                    print(f"{GRAY}[STT] ⚠ Only wake word detected, waiting for command...{RESET}")
                    continue

                # Reset conversation timer on new speech
                if self.in_conversation_mode:
                    self._reset_timeout_timer()

                self.speech_callback(text_clean)
        except Exception as e:
            print(f"{GRAY}[STT] Listener error: {e}{RESET}")
            import traceback; traceback.print_exc()
            self.running = False

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def stop(self):
        self.running = False
        self._cancel_timeout_timer()
        if self.recorder:
            try:
                print(f"{CYAN}[STT] Shutting down recorder...{RESET}")
                self.recorder.shutdown()  
                self.recorder = None
            except Exception as e:
                print(f"{GRAY}[STT] Error stopping recorder: {e}{RESET}")
        if self.listening_thread:
            self.listening_thread.join(timeout=2.0)  
        print(f"{CYAN}[STT] Listener stopped{RESET}")
