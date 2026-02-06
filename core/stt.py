"""
Speech-to-Text with Wake Word Detection for Voice Assistant.
Uses RealTimeSTT for real-time transcription with built-in wake word detection.
"""

import threading
import time
from typing import Optional, Callable
from config import (
    WAKE_WORD, REALTIMESTT_MODEL, WAKE_WORD_SENSITIVITY,
    GRAY, RESET, CYAN, YELLOW, GREEN
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
        try:
            from RealtimeSTT import AudioToTextRecorder
            import torch
            
            print(f"{CYAN}[STT] Loading RealTimeSTT...{RESET}")
            
            # Check CUDA availability
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                cuda_device = torch.cuda.current_device()
                cuda_name = torch.cuda.get_device_name(cuda_device)
                print(f"{GREEN}[STT] ✓ CUDA is available (Device: {cuda_name}){RESET}")
            else:
                print(f"{YELLOW}[STT] ⚠ CUDA is not available, will use CPU{RESET}")
            
            print(f"{CYAN}[STT] Initializing AudioToTextRecorder with device='cuda'...{RESET}")
            
            # Check if wake word is built-in (jarvis, alexa, etc.)
            built_in_words = ["jarvis", "alexa", "hey_mycroft", "hey_jarvis", "hey_rhasspy"]
            is_built_in = WAKE_WORD.lower() in built_in_words
            
            if is_built_in:
                print(f"{CYAN}[STT] Using built-in wake word model for '{WAKE_WORD}'{RESET}")
                backend = "openwakeword"
                detect_word = WAKE_WORD
            else:
                print(f"{YELLOW}[STT] Custom wake word '{WAKE_WORD}' detected. Switching to transcription mode.{RESET}")
                backend = "none" # No hardware backend, use whisper transcription
                detect_word = "" # recorder.text() will return everything
            
            self.recorder = AudioToTextRecorder(
                model=REALTIMESTT_MODEL,
                language="en",
                device="cuda",
                spinner=False,
                wakeword_backend=backend,
                wake_words=detect_word,
                wake_words_sensitivity=WAKE_WORD_SENSITIVITY,
                on_wakeword_detected=self._on_wakeword_detected,
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
                    
                    # Phonetic aliases for 'wolf' to handle mis-transcriptions
                    WOLF_ALIASES = ["wolf", "wolff", "woof", "who", "wall", "well", "holy", "bolly", "wulf", "world", "worth"]
                    
                    # Check if wake word or any phonetic alias is in the text
                    detected = False
                    for alias in WOLF_ALIASES:
                        if alias in text_lower:
                            detected = True
                            print(f"{GREEN}[STT] ✨ Wake word detected via alias: '{alias}'{RESET}")
                            break
                    
                    if detected:
                        if self.wake_word_callback:
                            self.wake_word_callback()
                    
                    if detected:
                        # Clean the text: find the best alias match to remove
                        best_match = WAKE_WORD
                        for alias in WOLF_ALIASES:
                            if alias in text_lower:
                                best_match = alias
                                break

                        import re
                        pattern = re.compile(re.escape(best_match), re.IGNORECASE)
                        match = pattern.search(text)
                        if match:
                            text_clean = text[match.end():].strip()
                        else:
                            text_clean = text.strip()
                            
                        print(f"{CYAN}[STT] 🧹 Cleaned text: '{text_clean}'{RESET}")
                    
                    if text_clean:
                        print(f"{CYAN}[STT] 🔊 Speech recognized: '{text_clean}'{RESET}")
                        
                        # Pass transcribed speech to callback
                        self.speech_callback(text_clean)
                    else:
                        print(f"{GRAY}[STT] ⚠ Text is empty after cleaning, skipping...{RESET}")
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
