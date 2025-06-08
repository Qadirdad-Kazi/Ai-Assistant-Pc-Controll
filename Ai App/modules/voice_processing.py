"""
Voice Processing Module for Wolf AI Voice Assistant
Handles speech recognition and text-to-speech functionality.
"""

import os
import sys
import time
import queue
import threading
import speech_recognition as sr
import pyttsx3
from typing import Optional, Callable, Dict, Any, List
import numpy as np
from dataclasses import dataclass
from enum import Enum, auto

class VoiceGender(Enum):
    """Voice gender options for TTS."""
    MALE = auto()
    FEMALE = auto()
    NEUTRAL = auto()

@dataclass
class VoiceProfile:
    """Configuration for TTS voice profiles."""
    name: str
    gender: VoiceGender
    languages: List[str]
    rate: int = 200  # Words per minute
    volume: float = 1.0  # 0.0 to 1.0

class VoiceProcessor:
    """
    Handles speech recognition and text-to-speech functionality.
    Supports multiple languages and voice profiles.
    """
    
    def __init__(self, language: str = 'en-US', gender: VoiceGender = VoiceGender.FEMALE):
        """
        Initialize the voice processor.
        
        Args:
            language (str): Default language code (e.g., 'en-US', 'ur-PK')
            gender (VoiceGender): Default voice gender
        """
        self.language = language
        self.gender = gender
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000  # Adjust based on your microphone
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Seconds of non-speaking audio before a phrase is considered complete
        
        # Initialize TTS engine
        self.tts_engine = self._init_tts_engine()
        
        # Available voice profiles
        self.voice_profiles = self._init_voice_profiles()
        self.current_voice_profile = self._get_default_voice_profile()
        
        # Audio processing thread
        self.processing_thread = None
        self.stop_event = threading.Event()
    
    def _init_tts_engine(self):
        """Initialize the TTS engine with appropriate settings."""
        try:
            engine = pyttsx3.init()
            # Set default rate (words per minute)
            engine.setProperty('rate', 150)
            # Set default volume (0.0 to 1.0)
            engine.setProperty('volume', 0.9)
            return engine
        except Exception as e:
            print(f"Error initializing TTS engine: {e}")
            return None
    
    def _init_voice_profiles(self) -> Dict[str, VoiceProfile]:
        """Initialize available voice profiles."""
        return {
            'en-US-female': VoiceProfile(
                name='en-US-female',
                gender=VoiceGender.FEMALE,
                languages=['en-US', 'en-GB', 'en-AU'],
                rate=150
            ),
            'en-US-male': VoiceProfile(
                name='en-US-male',
                gender=VoiceGender.MALE,
                languages=['en-US', 'en-GB', 'en-AU'],
                rate=160
            ),
            'ur-PK-female': VoiceProfile(
                name='ur-PK-female',
                gender=VoiceGender.FEMALE,
                languages=['ur-PK', 'ur'],
                rate=140
            ),
            'ur-PK-male': VoiceProfile(
                name='ur-PK-male',
                gender=VoiceGender.MALE,
                languages=['ur-PK', 'ur'],
                rate=145
            )
        }
    
    def _get_default_voice_profile(self) -> Optional[VoiceProfile]:
        """Get the default voice profile based on current language and gender."""
        profile_id = f"{self.language.lower()}-{'female' if self.gender == VoiceGender.FEMALE else 'male'}"
        return self.voice_profiles.get(profile_id, list(self.voice_profiles.values())[0])
    
    def set_language(self, language: str) -> bool:
        """
        Set the language for speech recognition and TTS.
        
        Args:
            language (str): Language code (e.g., 'en-US', 'ur-PK')
            
        Returns:
            bool: True if language was set successfully, False otherwise
        """
        self.language = language
        # Update voice profile based on new language
        self.current_voice_profile = self._get_default_voice_profile()
        return True
    
    def set_gender(self, gender: VoiceGender) -> bool:
        """
        Set the gender for TTS voice.
        
        Args:
            gender (VoiceGender): Voice gender
            
        Returns:
            bool: True if gender was set successfully, False otherwise
        """
        self.gender = gender
        # Update voice profile based on new gender
        self.current_voice_profile = self._get_default_voice_profile()
        return True
    
    def set_voice_profile(self, profile_id: str) -> bool:
        """
        Set the voice profile by ID.
        
        Args:
            profile_id (str): ID of the voice profile
            
        Returns:
            bool: True if profile was set successfully, False otherwise
        """
        if profile_id in self.voice_profiles:
            self.current_voice_profile = self.voice_profiles[profile_id]
            return True
        return False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get a list of available voices.
        
        Returns:
            List[Dict[str, Any]]: List of available voices with their properties
        """
        voices = []
        for voice in self.tts_engine.getProperty('voices'):
            voices.append({
                'id': voice.id,
                'name': voice.name,
                'languages': voice.languages,
                'gender': 'male' if 'male' in voice.name.lower() else 'female' if 'female' in voice.name.lower() else 'unknown'
            })
        return voices
    
    def speak(self, text: str, block: bool = True) -> bool:
        """
        Convert text to speech.
        
        Args:
            text (str): Text to speak
            block (bool): If True, block until speech is complete
            
        Returns:
            bool: True if speech was successful, False otherwise
        """
        if not self.tts_engine:
            print("TTS engine not initialized")
            return False
        
        try:
            # Set voice properties based on current profile
            if self.current_voice_profile:
                self.tts_engine.setProperty('rate', self.current_voice_profile.rate)
                self.tts_engine.setProperty('volume', self.current_voice_profile.volume)
                
                # Try to find a matching voice
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    # Check if voice matches language and gender
                    if (any(lang in voice.languages[0].lower() for lang in self.current_voice_profile.languages) and
                        ((self.current_voice_profile.gender == VoiceGender.FEMALE and 'female' in voice.name.lower()) or
                         (self.current_voice_profile.gender == VoiceGender.MALE and 'male' in voice.name.lower()))):
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            # Speak the text
            self.tts_engine.say(text)
            if block:
                self.tts_engine.runAndWait()
            else:
                # Run in a separate thread to avoid blocking
                threading.Thread(target=self.tts_engine.runAndWait, daemon=True).start()
            
            return True
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return False
    
    def listen(self, timeout: Optional[float] = None, phrase_time_limit: Optional[float] = None) -> Optional[str]:
        """
        Listen for speech and convert it to text.
        
        Args:
            timeout (float, optional): Seconds to wait for speech before giving up
            phrase_time_limit (float, optional): Maximum seconds a phrase can be
            
        Returns:
            Optional[str]: Recognized text, or None if no speech was detected
        """
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source)
            
            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                print("Recognizing...")
                text = self.recognizer.recognize_google(audio, language=self.language)
                print(f"Recognized: {text}")
                return text
                
            except sr.WaitTimeoutError:
                print("No speech detected.")
                return None
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
                return None
    
    def start_listening(self, callback: Callable[[str], None], 
                       wake_word: Optional[str] = None,
                       continuous: bool = False) -> bool:
        """
        Start listening for speech in a background thread.
        
        Args:
            callback (Callable[[str], None]): Function to call with recognized text
            wake_word (str, optional): Optional wake word to listen for
            continuous (bool): If True, continue listening after each phrase
            
        Returns:
            bool: True if listening started successfully, False otherwise
        """
        if self.is_listening:
            print("Already listening")
            return False
        
        self.is_listening = True
        self.stop_event.clear()
        
        def listen_loop():
            while self.is_listening and not self.stop_event.is_set():
                text = self.listen(phrase_time_limit=5)
                if text:
                    # Check for wake word if specified
                    if wake_word and wake_word.lower() in text.lower():
                        # Remove wake word from the text
                        text = text.lower().replace(wake_word.lower(), '').strip()
                        if text:  # Only process if there's text after the wake word
                            callback(text)
                    elif not wake_word:  # No wake word, process all input
                        callback(text)
                
                if not continuous:
                    self.is_listening = False
        
        self.processing_thread = threading.Thread(target=listen_loop, daemon=True)
        self.processing_thread.start()
        return True
    
    def stop_listening(self):
        """Stop the background listening thread."""
        self.is_listening = False
        self.stop_event.set()
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
    
    def adjust_for_ambient_noise(self, duration: float = 1.0):
        """
        Adjust the recognizer sensitivity to ambient noise.
        
        Args:
            duration (float): How many seconds to analyze ambient noise
        """
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)
    
    def save_speech_to_file(self, text: str, filename: str) -> bool:
        """
        Save speech to an audio file.
        
        Args:
            text (str): Text to convert to speech
            filename (str): Path to save the audio file
            
        Returns:
            bool: True if file was saved successfully, False otherwise
        """
        if not self.tts_engine:
            return False
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # Save to file
            self.tts_engine.save_to_file(text, filename)
            self.tts_engine.runAndWait()
            return True
        except Exception as e:
            print(f"Error saving speech to file: {e}")
            return False
    
    def __del__(self):
        """Clean up resources."""
        self.stop_listening()
        if hasattr(self, 'tts_engine') and self.tts_engine:
            self.tts_engine.stop()

# Singleton instance
voice_processor = VoiceProcessor()
