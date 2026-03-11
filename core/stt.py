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
from config import (  # type: ignore
    WAKE_WORD, REALTIMESTT_MODEL, WAKE_WORD_SENSITIVITY,
    CUSTOM_PPN_PATH, GRAY, RESET, CYAN, YELLOW, GREEN
)

# ── Constants ────────────────────────────────────────────────────────────────
CONVERSATION_TIMEOUT = 60          # Seconds of silence before leaving convo mode
STOP_PHRASES  = {"stop", "please stop", "shut up", "be quiet", "quit", "please quit", "cancel", "abort", "halt", "stop talking", "quiet"}
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
        self.conversation_recorder: Optional[Any] = None
        self.initialized = False
        self.listening_thread: Optional[threading.Thread] = None

        # Conversation-mode state
        self._mode = self.MODE_WAKE_WORD
        self._mode_lock = threading.Lock()
        self._last_activity = 0.0          # timestamp of last user speech
        self._timeout_timer: Optional[threading.Timer] = None

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
        print(f"{GREEN}[STT] 💬 Conversation mode active (timeout: {CONVERSATION_TIMEOUT}s){RESET}")

    def exit_conversation_mode(self):
        """Return to wake-word gating."""
        with self._mode_lock:
            self._mode = self.MODE_WAKE_WORD
        self._cancel_timeout_timer()
        print(f"{CYAN}[STT] 🔇 Returned to wake-word mode.{RESET}")

    @property
    def in_conversation_mode(self) -> bool:
        with self._mode_lock:
            return self._mode == self.MODE_CONVERSATION

    # ── Initialization ────────────────────────────────────────────────────────

    def initialize(self) -> bool:
        """Initialize RealTimeSTT with wake word detection."""
        import os as _os
        try:
            from RealtimeSTT import AudioToTextRecorder  # type: ignore
            import torch  # type: ignore
            import pvporcupine  # type: ignore

            print(f"{CYAN}[STT] Loading RealTimeSTT...{RESET}")

            cuda_available = torch.cuda.is_available()
            if cuda_available:
                cuda_name = torch.cuda.get_device_name(torch.cuda.current_device())
                print(f"{GREEN}[STT] ✓ CUDA is available (Device: {cuda_name}){RESET}")
            else:
                print(f"{YELLOW}[STT] ⚠ CUDA not available, will use CPU{RESET}")

            from core.settings_store import settings  # type: ignore
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

            self.recorder = AudioToTextRecorder(
                model=REALTIMESTT_MODEL,
                language="en",
                device="cuda" if cuda_available else "cpu",
                spinner=False,
                wakeword_backend=backend,
                wake_words=detect_word,
                wake_words_sensitivity=WAKE_WORD_SENSITIVITY,
                on_wakeword_detected=self._on_wakeword_detected,
            )

            # Dedicated recorder for conversation mode (wake word disabled).
            self.conversation_recorder = AudioToTextRecorder(
                model=REALTIMESTT_MODEL,
                language="en",
                device="cuda" if cuda_available else "cpu",
                spinner=False,
                wakeword_backend="none",
                wake_words="",
                wake_words_sensitivity=WAKE_WORD_SENSITIVITY,
            )

            self.initialized = True
            print(f"{CYAN}[STT] ✓ RealTimeSTT initialized (model: {REALTIMESTT_MODEL}, wake word: '{WAKE_WORD}'){RESET}")
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
            self.wake_word_callback()  # type: ignore

    # ── Timeout timer ─────────────────────────────────────────────────────────

    def _reset_timeout_timer(self):
        self._cancel_timeout_timer()
        self._timeout_timer = threading.Timer(CONVERSATION_TIMEOUT, self._on_conversation_timeout)
        self._timeout_timer.daemon = True  # type: ignore
        self._timeout_timer.start()  # type: ignore

    def _cancel_timeout_timer(self):
        if self._timeout_timer:
            self._timeout_timer.cancel()  # type: ignore
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
        self.listening_thread.start()  # type: ignore
        print(f"{CYAN}[STT] ✓ Listener started{RESET}")
        return True

    def _run_listener(self):
        """Main loop. Handles both wake-word mode and conversation mode."""
        try:
            print(f"{GRAY}[STT] 🔄 Starting transcription loop...{RESET}")

            while self.running:
                active_recorder = self.conversation_recorder if self.in_conversation_mode and self.conversation_recorder else self.recorder
                if not active_recorder:
                    time.sleep(0.05)
                    continue

                in_convo = self.in_conversation_mode

                if in_convo:
                    # ── Conversation mode: listen directly, no wake word gate ──
                    print(f"{GRAY}[STT] 💬 Listening for follow-up...{RESET}")
                else:
                    print(f"{GRAY}[STT] ⏳ Waiting for wake word '{WAKE_WORD}'...{RESET}")

                t0   = time.time()
                try:
                    text = str(active_recorder.text() or "")  # type: ignore
                except Exception:
                    if not self.running:
                        break
                    # Recorder may have just been swapped; continue with new one.
                    continue
                elapsed = time.time() - t0

                if not text or not text.strip():
                    if in_convo:
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
                # This prevents accidentally dropping commands like "stop the music" or "quit vim"
                check_text = text_lower
                for alias in WOLF_ALIASES + ["hey wolf", "hey wolff"]:
                    if check_text.startswith(alias):  # type: ignore
                        check_text = check_text[len(alias):].strip()  # type: ignore
                        break
                
                is_stop = check_text in STOP_PHRASES
                if not is_stop:
                    normalized = re.sub(r"\s+", " ", check_text).strip()
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
                        self.stop_callback()  # type: ignore
                    # Keep follow-up listening open after interruption.
                    self.enter_conversation_mode()
                    continue

                # ── Wake-word stripping ───────────────────────────────────────
                found_alias = next((a for a in WOLF_ALIASES if a in text_lower), None)
                if found_alias:
                    pattern = re.compile(re.escape(found_alias), re.IGNORECASE)
                    m = pattern.search(text_original)
                    if m:
                        text_clean = text_original[m.end():].strip()  # type: ignore
                        print(f"{GREEN}[STT] ✨ Wake word '{found_alias}' stripped.{RESET}")

                    # Fire wake-word callback if hardware hasn't already
                    if not in_convo and self.wake_word_callback:
                        self.wake_word_callback()  # type: ignore

                # ── Guard: only wake-word said, no command ────────────────────
                if not text_clean:
                    print(f"{GRAY}[STT] ⚠ Only wake word detected, waiting for command...{RESET}")
                    continue

                # ── Dispatch to voice assistant ───────────────────────────────
                print(f"{CYAN}[STT] 🔊 Speech recognized: '{text_clean}'{RESET}")

                # Reset conversation timer on new speech
                if in_convo:
                    self._reset_timeout_timer()

                self.speech_callback(text_clean)  # type: ignore

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
                self.recorder.shutdown()  # type: ignore
            except Exception as e:
                print(f"{GRAY}[STT] Error stopping recorder: {e}{RESET}")
        if self.conversation_recorder:
            try:
                print(f"{CYAN}[STT] Shutting down conversation recorder...{RESET}")
                self.conversation_recorder.shutdown()  # type: ignore
            except Exception as e:
                print(f"{GRAY}[STT] Error stopping conversation recorder: {e}{RESET}")
        if self.listening_thread:
            self.listening_thread.join(timeout=2.0)  # type: ignore
        print(f"{CYAN}[STT] Listener stopped{RESET}")
