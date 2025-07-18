"""
Wake Word Detection module for Wolf AI Assistant
Handles wake word/phrase detection.
"""

import pvporcupine
import pyaudio
import numpy as np
import logging
import threading
from typing import Callable, Optional, List, Dict, Any

class WakeWordDetector:
    """Handles wake word/phrase detection using Porcupine."""
    
    def __init__(self, 
                 wake_word: str = "hey wolf",
                 sensitivity: float = 0.5,
                 keyword_paths: Optional[List[str]] = None,
                 model_path: Optional[str] = None,
                 library_path: Optional[str] = None):
        """Initialize the wake word detector.
        
        Args:
            wake_word: The wake word or phrase to detect
            sensitivity: Detection sensitivity (0.0 to 1.0)
            keyword_paths: Paths to custom keyword model files
            model_path: Path to the Porcupine model file
            library_path: Path to the Porcupine dynamic library
        """
        self.wake_word = wake_word.lower()
        self.sensitivity = sensitivity
        self.keyword_paths = keyword_paths
        self.model_path = model_path
        self.library_path = library_path
        self.callback = None
        self.is_running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize Porcupine if paths are provided
        self.porcupine = None
        self.audio_stream = None
        self.pa = None
        
        self.logger.info(f"WakeWordDetector initialized for wake word: {wake_word}")
    
    def start(self, callback: Callable[[], None]):
        """Start listening for the wake word.
        
        Args:
            callback: Function to call when the wake word is detected
        """
        if self.is_running:
            self.logger.warning("Wake word detector is already running")
            return
            
        self.callback = callback
        self.is_running = True
        
        # Start the detection thread
        self.thread = threading.Thread(target=self._detect_loop, daemon=True)
        self.thread.start()
        
        self.logger.info("Wake word detection started")
    
    def stop(self):
        """Stop listening for the wake word."""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Clean up resources
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        
        self._cleanup()
        self.logger.info("Wake word detection stopped")
    
    def _initialize_porcupine(self):
        """Initialize the Porcupine wake word engine."""
        try:
            self.porcupine = pvporcupine.create(
                keywords=[self.wake_word],
                keyword_paths=self.keyword_paths,
                sensitivities=[self.sensitivity],
                model_path=self.model_path,
                library_path=self.library_path
            )
            
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
                input_device_index=None
            )
            
            self.logger.debug("Porcupine wake word engine initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Porcupine: {e}", exc_info=True)
            self._cleanup()
            return False
    
    def _cleanup(self):
        """Clean up resources."""
        if self.audio_stream:
            try:
                self.audio_stream.close()
            except:
                pass
            self.audio_stream = None
            
        if self.porcupine:
            try:
                self.porcupine.delete()
            except:
                pass
            self.porcupine = None
            
        if self.pa:
            try:
                self.pa.terminate()
            except:
                pass
            self.pa = None
    
    def _detect_loop(self):
        """Main detection loop running in a separate thread."""
        if not self._initialize_porcupine():
            self.logger.error("Failed to initialize Porcupine, wake word detection disabled")
            return
            
        self.logger.info("Starting wake word detection loop")
        
        try:
            while self.is_running:
                try:
                    pcm = self.audio_stream.read(
                        self.porcupine.frame_length,
                        exception_on_overflow=False
                    )
                    pcm = np.frombuffer(pcm, dtype=np.int16)
                    
                    # Check for wake word
                    result = self.porcupine.process(pcm)
                    if result >= 0:  # Wake word detected
                        self.logger.info(f"Wake word '{self.wake_word}' detected!")
                        if self.callback:
                            self.callback()
                            
                except Exception as e:
                    self.logger.error(f"Error in wake word detection: {e}", exc_info=True)
                    break
                    
        finally:
            self._cleanup()
            self.is_running = False
    
    def update_wake_word(self, new_wake_word: str, sensitivity: Optional[float] = None):
        """Update the wake word and/or sensitivity.
        
        Args:
            new_wake_word: New wake word or phrase
            sensitivity: New detection sensitivity (0.0 to 1.0)
        """
        was_running = self.is_running
        
        if was_running:
            self.stop()
            
        self.wake_word = new_wake_word.lower()
        
        if sensitivity is not None:
            self.sensitivity = max(0.0, min(1.0, sensitivity))
            
        self.logger.info(f"Updated wake word to '{self.wake_word}' with sensitivity {self.sensitivity}")
        
        if was_running and self.callback:
            self.start(self.callback)
    
    def is_listening(self) -> bool:
        """Check if the detector is currently running.
        
        Returns:
            bool: True if the detector is running, False otherwise
        """
        return self.is_running
    
    def __del__(self):
        """Ensure resources are cleaned up."""
        self.stop()
        self._cleanup()
