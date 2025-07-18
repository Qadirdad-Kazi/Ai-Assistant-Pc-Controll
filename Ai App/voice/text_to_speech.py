"""
Text-to-Speech module for Wolf AI Assistant
Handles converting text to speech using various engines.
"""

import pyttsx3
import threading
import queue
import logging
from typing import Optional, Callable

class TextToSpeech:
    """Handles text-to-speech functionality."""
    
    def __init__(self, rate: int = 200, volume: float = 1.0, voice: str = None):
        """Initialize the TTS engine.
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            voice: Voice ID to use (if None, uses system default)
        """
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        
        if voice:
            self.set_voice(voice)
            
        self.queue = queue.Queue()
        self.is_speaking = False
        self.stop_requested = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
        
        # Start the TTS processing thread
        self._start_processing()
        self.logger.info("TextToSpeech initialized")
    
    def set_voice(self, voice_id: str) -> bool:
        """Set the voice to use for TTS.
        
        Args:
            voice_id: ID of the voice to use
            
        Returns:
            bool: True if voice was set successfully, False otherwise
        """
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if voice_id in voice.id or voice_id in voice.name:
                self.engine.setProperty('voice', voice.id)
                return True
        return False
    
    def set_rate(self, rate: int):
        """Set the speech rate.
        
        Args:
            rate: Words per minute
        """
        self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume: float):
        """Set the volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
    
    def speak(self, text: str, callback: Optional[Callable[[], None]] = None):
        """Add text to the TTS queue to be spoken.
        
        Args:
            text: The text to speak
            callback: Optional function to call when speaking is done
        """
        self.queue.put((text, callback))
    
    def stop(self):
        """Stop the current speech and clear the queue."""
        self.stop_requested = True
        with self.queue.mutex:
            self.queue.queue.clear()
        self.engine.stop()
        self.stop_requested = False
    
    def _start_processing(self):
        """Start the TTS processing thread."""
        if self.thread and self.thread.is_alive():
            return
            
        def process_queue():
            while True:
                try:
                    text, callback = self.queue.get(timeout=1)
                    if text is None:  # Shutdown signal
                        break
                        
                    self.is_speaking = True
                    self.engine.say(text)
                    self.engine.runAndWait()
                    self.is_speaking = False
                    
                    if callback:
                        callback()
                        
                except queue.Empty:
                    continue
                except Exception as e:
                    self.logger.error(f"Error in TTS processing: {e}", exc_info=True)
                    self.is_speaking = False
        
        self.thread = threading.Thread(target=process_queue, daemon=True)
        self.thread.start()
    
    def shutdown(self):
        """Shut down the TTS engine."""
        self.stop()
        self.queue.put((None, None))  # Signal thread to exit
        if self.thread:
            self.thread.join(timeout=1)
        self.engine.stop()
        
    def __del__(self):
        """Ensure resources are cleaned up."""
        self.shutdown()
