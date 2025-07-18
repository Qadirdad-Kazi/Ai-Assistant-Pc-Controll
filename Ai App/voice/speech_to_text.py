"""
Speech-to-Text module for Wolf AI Assistant
Handles converting speech to text using various engines.
"""

import speech_recognition as sr
import logging
from typing import Optional, Callable

class SpeechToText:
    """Handles speech recognition functionality."""
    
    def __init__(self, energy_threshold: int = 300, dynamic_energy_threshold: bool = True):
        """Initialize the speech recognizer.
        
        Args:
            energy_threshold: Energy level for mic to detect as speech
            dynamic_energy_threshold: Whether to adjust energy threshold dynamically
        """
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.dynamic_energy_threshold = dynamic_energy_threshold
        self.microphone = sr.Microphone()
        self.logger = logging.getLogger(__name__)
        
        # Adjust for ambient noise when initializing
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
        self.logger.info("SpeechToText initialized")
    
    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """Listen for audio and convert to text.
        
        Args:
            timeout: Time in seconds to wait for speech before timing out
            phrase_time_limit: Maximum time in seconds for a phrase
            
        Returns:
            str: The recognized text, or None if no speech was detected
        """
        try:
            with self.microphone as source:
                self.logger.info("Listening for speech...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
            self.logger.info("Processing speech...")
            text = self.recognizer.recognize_google(audio)
            self.logger.info(f"Recognized: {text}")
            return text
            
        except sr.WaitTimeoutError:
            self.logger.debug("No speech detected within the timeout period")
            return None
        except sr.UnknownValueError:
            self.logger.debug("Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Could not request results from Google Speech Recognition service; {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error in speech recognition: {e}", exc_info=True)
            return None
    
    def listen_in_background(self, callback: Callable[[str], None], **kwargs):
        """Start listening in the background and call the callback with the result.
        
        Args:
            callback: Function to call with the recognized text
            **kwargs: Additional arguments to pass to the listen method
        """
        def listen_thread():
            text = self.listen(**kwargs)
            if text:
                callback(text)
        
        import threading
        thread = threading.Thread(target=listen_thread)
        thread.daemon = True
        thread.start()
        return thread
