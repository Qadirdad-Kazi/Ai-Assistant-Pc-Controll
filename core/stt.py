"""
Speech-to-Text with Wake Word Detection for Voice Assistant.
Uses RealTimeSTT for real-time transcription with built-in wake word detection.
"""

import threading
import time
import os
from typing import Optional, Callable
from config import (
    WAKE_WORD, REALTIMESTT_MODEL, WAKE_WORD_SENSITIVITY,
    CUSTOM_PPN_PATH, GRAY, RESET, CYAN, YELLOW, GREEN
)


class STTListener:
    """
    Real-time STT listener with wake word detection using RealTimeSTT.
    Uses RealTimeSTT's built-in wake word detection and text() method.
    """
    
    def __init__(self, wake_word_callback: Callable, speech_callback: Callable):
        self.wake_word_callback = wake_word_callback
        self.speech_callback = speech_callback
        self.running = False
        self.listening_thread = None
        
        # RealTimeSTT recorder
        self.recorder = None
        self.initialized = False
        
        print(f"{CYAN}[STT] Initializing RealTimeSTT listener...{RESET}")
        print(f"{CYAN}[STT] Wake word: '{WAKE_WORD}'{RESET}")
        print(f"{CYAN}[STT] Detection method: RealTimeSTT built-in wake word detection{RESET}")
    
    def initialize(self) -> bool:
        """Initialize RealTimeSTT with wake word detection."""
        import os  # Explicit local import to prevent NameError
        try:
            from RealtimeSTT import AudioToTextRecorder
            import torch
            import pvporcupine
            
            print(f"{CYAN}[STT] Loading RealTimeSTT...{RESET}")
            
            # Check CUDA availability
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                cuda_device = torch.cuda.current_device()
                cuda_name = torch.cuda.get_device_name(cuda_device)
                print(f"{GREEN}[STT] ✓ CUDA is available (Device: {cuda_name}){RESET}")
            else:
                print(f"{YELLOW}[STT] ⚠ CUDA is not available, will use CPU{RESET}")
            
            # Switch backend depending on config
            from core.settings_store import settings
            porcupine_key = settings.get("picovoice.key", "")
            ppn_path = settings.get("picovoice.ppn_path", "")
            
            # Auto-detect in resources if not set
            if not ppn_path or not os.path.exists(ppn_path):
                if os.path.exists(CUSTOM_PPN_PATH):
                    ppn_path = CUSTOM_PPN_PATH
                    print(f"{GREEN}[STT] ✨ Auto-detected high-performance wake word at: {ppn_path}{RESET}")

            # MONKEY-PATCH: RealtimeSTT 0.3.104 doesn't support passing Picovoice Access Key.
            # We patch pvporcupine.create to inject it automatically.
            original_pv_create = pvporcupine.create
            def patched_pv_create(*args, **kwargs):
                import os  # Scoping safety for threads
                # Inject access key from settings
                if porcupine_key:
                    kwargs['access_key'] = porcupine_key
                
                # Inject custom .ppn path if it exists
                # We prioritize the settings path, then the auto-detected path
                active_ppn = settings.get("picovoice.ppn_path", ppn_path)
                if active_ppn and os.path.exists(active_ppn):
                    kwargs['keyword_paths'] = [active_ppn]
                    if 'keywords' in kwargs:
                        del kwargs['keywords']
                return original_pv_create(*args, **kwargs)
            
            pvporcupine.create = patched_pv_create
            
            if porcupine_key:
                print(f"{GREEN}[STT] 🦔 High-performance Porcupine engine requested.{RESET}")
                backend = "pvporcupine"
                detect_word = "wolf" # Placeholder
            elif WAKE_WORD.lower() in ["jarvis", "alexa", "hey_mycroft", "hey_jarvis", "hey_rhasspy"]:
                print(f"{CYAN}[STT] Using built-in wake word model for '{WAKE_WORD}'{RESET}")
                backend = "openwakeword"
                detect_word = WAKE_WORD
            else:
                print(f"{YELLOW}[STT] Custom wake word '{WAKE_WORD}' detected. Switching to transcription mode.{RESET}")
                backend = "none"
                detect_word = ""

            self.recorder = AudioToTextRecorder(
                model=REALTIMESTT_MODEL,
                language="en",
                device="cuda" if cuda_available else "cpu",
                spinner=False,
                wakeword_backend=backend,
                wake_words=detect_word,
                wake_words_sensitivity=WAKE_WORD_SENSITIVITY,
                on_wakeword_detected=self._on_wakeword_detected
            )
            
            # Verify device after initialization
            if hasattr(self.recorder, 'model') and hasattr(self.recorder.model, 'device'):
                actual_device = str(self.recorder.model.device)
                print(f"{GREEN}[STT] ✓ Model device: {actual_device}{RESET}")
            elif hasattr(self.recorder, '_device'):
                print(f"{GREEN}[STT] ✓ Recorder device: {self.recorder._device}{RESET}")
            
            self.initialized = True
            print(f"{CYAN}[STT] ✓ RealTimeSTT initialized successfully (model: {REALTIMESTT_MODEL}, wake word: '{WAKE_WORD}'){RESET}")
            return True
        except ImportError:
            print(f"{GRAY}[STT] ✗ RealTimeSTT not installed. Install with: pip install realtimestt{RESET}")
            return False
        except Exception as e:
            print(f"{GRAY}[STT] ✗ RealTimeSTT initialization error: {e}{RESET}")
            import traceback
            traceback.print_exc()
            return False
    
    def _on_wakeword_detected(self):
        """Callback when wake word is detected."""
        print(f"\n{CYAN}[STT] 👂 Wake word '{WAKE_WORD}' detected! Listening...{RESET}")
        # Notify callback if set
        if self.wake_word_callback:
            self.wake_word_callback()

    def start(self):
        """Start listening."""
        if not self.initialized:
            print(f"{YELLOW}[STT] Not initialized. Call initialize() first.{RESET}")
            return False
        
        if self.running:
            print(f"{YELLOW}[STT] Already running.{RESET}")
            return True
        
        self.running = True
        print(f"{CYAN}[STT] Starting RealTimeSTT listener...{RESET}")
        
        # Start RealTimeSTT in a background thread
        try:
            self.listening_thread = threading.Thread(
                target=self._run_listener,
                daemon=True
            )
            self.listening_thread.start()
            print(f"{CYAN}[STT] ✓ Listener started{RESET}")
            return True
        except Exception as e:
            print(f"{GRAY}[STT] Failed to start listener: {e}{RESET}")
            self.running = False
            return False
    
    def _run_listener(self):
        """Main listening loop using RealTimeSTT's text() method."""
        try:
            print(f"{GRAY}[STT] 🔄 Starting transcription loop...{RESET}")
            while self.running:
                if not self.recorder:
                    break
                
                print(f"{GRAY}[STT] ⏳ Waiting for wake word '{WAKE_WORD}'...{RESET}")
                
                # recorder.text() blocks until wake word is detected, then returns transcribed text
                transcription_start = time.time()
                text = self.recorder.text()
                transcription_time = time.time() - transcription_start
                text_clean = ""
                
                print(f"{CYAN}[STT] ✓ Transcription completed in {transcription_time:.2f}s{RESET}")
                print(f"{CYAN}[STT] 📝 Raw transcribed text: '{text}'{RESET}")
                
                if text and text.strip():
                    text_lower = text.lower()
                    text_original = text.strip()
                    text_clean = text_original
                    
                    # Phonetic aliases for 'wolf' to handle mis-transcriptions
                    WOLF_ALIASES = ["wolf", "wolff", "woof", "who", "wall", "well", "holy", "bolly", "wulf", "world", "worth"]
                    
                    # 1. Check if ANY wake word alias is in the text
                    found_alias = None
                    for alias in WOLF_ALIASES:
                        if alias in text_lower:
                            found_alias = alias
                            break
                    
                    # 2. If we found an alias in the text, clean it out
                    if found_alias:
                        import re
                        pattern = re.compile(re.escape(found_alias), re.IGNORECASE)
                        match = pattern.search(text_original)
                        if match:
                            text_clean = text_original[match.end():].strip()
                            print(f"{GREEN}[STT] ✨ Wake word '{found_alias}' stripped from command.{RESET}")
                        
                        # Trigger the callback if it wasn't already triggered by hardware
                        if self.wake_word_callback:
                            self.wake_word_callback()

                    # 3. Final check: if text_clean is empty but text wasn't, 
                    # it means the user only said the wake word.
                    if not text_clean and text_original:
                        print(f"{GRAY}[STT] ⚠ Only wake word detected, no command. Waiting...{RESET}")
                        continue
                        
                    if text_clean:
                        print(f"{CYAN}[STT] 🔊 Speech recognized: '{text_clean}'{RESET}")
                        # Pass transcribed speech to callback
                        self.speech_callback(text_clean)
                    else:
                        print(f"{GRAY}[STT] ⚠ Text is empty after processing, skipping...{RESET}")
                else:
                    print(f"{GRAY}[STT] ⚠ No text received or text is empty{RESET}")
                
        except Exception as e:
            print(f"{GRAY}[STT] Listener error: {e}{RESET}")
            import traceback
            traceback.print_exc()
            self.running = False
    
    def stop(self):
        """Stop listening."""
        self.running = False
        if self.recorder:
            try:
                print(f"{CYAN}[STT] Shutting down recorder...{RESET}")
                self.recorder.shutdown()
            except Exception as e:
                print(f"{GRAY}[STT] Error stopping recorder: {e}{RESET}")
        if self.listening_thread:
            self.listening_thread.join(timeout=2.0)
        print(f"{CYAN}[STT] Listener stopped{RESET}")
