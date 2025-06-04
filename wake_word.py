"""
Wake Word Detection Module
Implements lightweight wake word detection for "Hey Wolf", "Hi Wolf", "Hello Wolf"
"""

import speech_recognition as sr
import threading
import time
import re
from config import Config

class WakeWordDetector:
    def __init__(self):
        self.config = Config()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_active = True
        self.wake_words = [
            "hey wolf",
            "hi wolf", 
            "hello wolf",
            "ok wolf",
            "wolf"
        ]
        
        # Configure recognizer for better performance
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        
        # Calibrate microphone
        self.calibrate_microphone()

    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            print(f"Microphone calibration error: {e}")

    def detect(self):
        """
        Detect wake word in audio stream
        Returns True if wake word is detected
        """
        try:
            with self.microphone as source:
                # Listen for short phrases (wake words are typically short)
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=2)
            
            try:
                # Use Google's speech recognition with shorter timeout
                text = self.recognizer.recognize_google(audio, language='en-US')
                return self.is_wake_word(text)
                
            except sr.UnknownValueError:
                # No speech detected or couldn't understand
                return False
            except sr.RequestError:
                # API error - could implement offline recognition here
                return False
                
        except sr.WaitTimeoutError:
            # No audio detected within timeout
            return False
        except Exception as e:
            print(f"Wake word detection error: {e}")
            return False

    def is_wake_word(self, text):
        """
        Check if the recognized text contains a wake word
        """
        if not text:
            return False
        
        text_lower = text.lower().strip()
        
        # Direct match check
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                print(f"Wake word detected: '{wake_word}' in '{text_lower}'")
                return True
        
        # Fuzzy matching for variations
        patterns = [
            r'\b(hey|hi|hello|ok)\s+wolf\b',
            r'\bwolf\b'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text_lower):
                print(f"Wake word pattern matched: '{pattern}' in '{text_lower}'")
                return True
        
        return False

    def start_continuous_detection(self, callback):
        """
        Start continuous wake word detection in background thread
        """
        def detection_loop():
            while self.is_active:
                try:
                    if self.detect():
                        callback()
                    time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                except Exception as e:
                    print(f"Continuous detection error: {e}")
                    time.sleep(1)  # Longer delay on error
        
        thread = threading.Thread(target=detection_loop, daemon=True)
        thread.start()
        return thread

    def stop(self):
        """Stop wake word detection"""
        self.is_active = False

# Simple test function
if __name__ == "__main__":
    detector = WakeWordDetector()
    
    def on_wake_word():
        print("🐺 Wake word detected! Wolf is listening...")
    
    print("Starting wake word detection... Say 'Hey Wolf', 'Hi Wolf', or 'Hello Wolf'")
    print("Press Ctrl+C to stop")
    
    try:
        detector.start_continuous_detection(on_wake_word)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping wake word detection...")
        detector.stop()
