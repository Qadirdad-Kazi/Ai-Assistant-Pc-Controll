"""
Voice Controller module for Wolf AI Assistant
Manages the integration of speech recognition, text-to-speech, and wake word detection.
"""

import logging
import threading
import queue
import json
from typing import Optional, Callable, Dict, Any

class VoiceController:
    """Main controller for voice interaction functionality."""
    
    def __init__(self, 
                 wake_word: str = "hey wolf",
                 speech_timeout: int = 5,
                 speech_phrase_limit: int = 10,
                 tts_rate: int = 200,
                 tts_volume: float = 1.0,
                 tts_voice: str = None):
        """Initialize the voice controller.
        
        Args:
            wake_word: The wake word/phrase to use
            speech_timeout: Timeout in seconds for speech recognition
            speech_phrase_limit: Maximum length of a speech phrase in seconds
            tts_rate: Speech rate for text-to-speech
            tts_volume: Volume level for text-to-speech (0.0 to 1.0)
            tts_voice: Voice ID to use for text-to-speech
        """
        self.wake_word = wake_word
        self.speech_timeout = speech_timeout
        self.speech_phrase_limit = speech_phrase_limit
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.speech_to_text = None
        self.text_to_speech = None
        self.wake_word_detector = None
        
        # State
        self.is_listening = False
        self.is_processing = False
        self.callbacks = {
            'on_wake': [],
            'on_speech': [],
            'on_tts_start': [],
            'on_tts_end': [],
            'on_error': []
        }
        
        # Initialize components
        self._initialize_components(tts_rate, tts_volume, tts_voice)
        
        self.logger.info("VoiceController initialized")
    
    def _initialize_components(self, tts_rate: int, tts_volume: float, tts_voice: str):
        """Initialize the voice components."""
        try:
            from .speech_to_text import SpeechToText
            from .text_to_speech import TextToSpeech
            from .wake_word import WakeWordDetector
            
            self.speech_to_text = SpeechToText()
            self.text_to_speech = TextToSpeech(rate=tts_rate, volume=tts_volume, voice=tts_voice)
            self.wake_word_detector = WakeWordDetector(wake_word=self.wake_word)
            
            # Set up wake word detection callback
            self.wake_word_detector.callback = self._on_wake_word_detected
            
        except Exception as e:
            self.logger.error(f"Failed to initialize voice components: {e}", exc_info=True)
            raise
    
    def start(self):
        """Start the voice controller."""
        if self.is_listening:
            self.logger.warning("Voice controller is already running")
            return
            
        try:
            # Start wake word detection
            self.wake_word_detector.start()
            self.is_listening = True
            self.logger.info("Voice controller started")
            
        except Exception as e:
            self.logger.error(f"Failed to start voice controller: {e}", exc_info=True)
            self._trigger_callbacks('on_error', {'error': str(e)})
    
    def stop(self):
        """Stop the voice controller."""
        if not self.is_listening:
            return
            
        try:
            self.wake_word_detector.stop()
            self.text_to_speech.stop()
            self.is_listening = False
            self.is_processing = False
            self.logger.info("Voice controller stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping voice controller: {e}", exc_info=True)
    
    def toggle_listening(self, force_state: Optional[bool] = None) -> bool:
        """Toggle listening state.
        
        Args:
            force_state: If provided, force the listening state to this value
            
        Returns:
            bool: The new listening state
        """
        new_state = not self.is_listening if force_state is None else force_state
        
        if new_state:
            self.start()
        else:
            self.stop()
            
        return self.is_listening
    
    def speak(self, text: str, callback: Optional[Callable[[], None]] = None):
        """Speak the given text.
        
        Args:
            text: The text to speak
            callback: Optional function to call when speaking is done
        """
        self._trigger_callbacks('on_tts_start', {'text': text})
        
        def on_speak_done():
            self._trigger_callbacks('on_tts_end', {'text': text})
            if callback:
                callback()
        
        self.text_to_speech.speak(text, on_speak_done)
    
    def process_text_command(self, text: str):
        """Process a text command.
        
        Args:
            text: The text command to process
        """
        self._trigger_callbacks('on_speech', {'text': text})
    
    def _on_wake_word_detected(self):
        """Handle wake word detection."""
        if self.is_processing:
            return
            
        self._trigger_callbacks('on_wake', {})
        self._start_speech_recognition()
    
    def _start_speech_recognition(self):
        """Start listening for a voice command."""
        if self.is_processing:
            return
            
        self.is_processing = True
        self.logger.info("Listening for voice command...")
        
        def recognition_callback(text: str):
            if text:
                self.process_text_command(text)
            self.is_processing = False
            
        self.speech_to_text.listen_in_background(
            recognition_callback,
            timeout=self.speech_timeout,
            phrase_time_limit=self.speech_phrase_limit
        )
    
    def register_callback(self, event: str, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for voice events.
        
        Args:
            event: The event to listen for ('on_wake', 'on_speech', 'on_tts_start', 'on_tts_end', 'on_error')
            callback: Function to call when the event occurs
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)
        else:
            self.logger.warning(f"Unknown event type: {event}")
    
    def _trigger_callbacks(self, event: str, data: Dict[str, Any]):
        """Trigger all callbacks for an event.
        
        Args:
            event: The event that occurred
            data: Data to pass to the callbacks
        """
        for callback in self.callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Error in {event} callback: {e}", exc_info=True)
    
    def update_settings(self, settings: Dict[str, Any]):
        """Update voice settings.
        
        Args:
            settings: Dictionary of settings to update
        """
        if 'wake_word' in settings:
            self.wake_word = settings['wake_word']
            self.wake_word_detector.update_wake_word(self.wake_word)
            
        if 'tts_rate' in settings:
            self.text_to_speech.set_rate(settings['tts_rate'])
            
        if 'tts_volume' in settings:
            self.text_to_speech.set_volume(settings['tts_volume'])
            
        if 'tts_voice' in settings:
            self.text_to_speech.set_voice(settings['tts_voice'])
    
    def shutdown(self):
        """Shut down the voice controller and release resources."""
        self.stop()
        
        if hasattr(self, 'text_to_speech') and self.text_to_speech:
            self.text_to_speech.shutdown()
        
        self.logger.info("Voice controller shut down")
    
    def __del__(self):
        """Ensure resources are cleaned up."""
        self.shutdown()
