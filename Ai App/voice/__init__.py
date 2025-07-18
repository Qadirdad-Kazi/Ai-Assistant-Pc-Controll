"""
Voice Module for Wolf AI Assistant
Handles all voice-related functionality including speech recognition, TTS, and wake word detection.
"""

# Import core components
from .speech_to_text import SpeechToText
from .text_to_speech import TextToSpeech
from .wake_word import WakeWordDetector
from .voice_controller import VoiceController

__all__ = ['SpeechToText', 'TextToSpeech', 'WakeWordDetector', 'VoiceController']
