#!/usr/bin/env python3
"""
Wolf AI Voice Assistant Backend
Handles voice processing, wake word detection, and system control
"""

import sys
import json
import threading
import time
import speech_recognition as sr
import pyttsx3
from wake_word import WakeWordDetector
from pc_controller import PCController
from ollama_client import OllamaClient
from database import Database
from config import Config
import traceback

class VoiceBackend:
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = pyttsx3.init()
        
        # Initialize components
        self.wake_word_detector = WakeWordDetector()
        self.pc_controller = PCController()
        self.ollama_client = OllamaClient()
        
        # State
        self.is_listening = False
        self.wake_word_active = True
        self.settings = self.load_settings()
        
        # Setup TTS
        self.setup_tts()
        
        # Start background threads
        self.start_wake_word_detection()
        
        self.send_message("status", "Voice backend initialized")

    def setup_tts(self):
        """Configure text-to-speech engine"""
        try:
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Select voice based on gender preference
                gender = self.settings.get('voiceGender', 'female')
                for voice in voices:
                    if gender.lower() in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            # Set speech rate and volume
            self.tts_engine.setProperty('rate', 180)
            self.tts_engine.setProperty('volume', 0.8)
        except Exception as e:
            self.send_message("error", f"TTS setup failed: {str(e)}")

    def load_settings(self):
        """Load user settings from database"""
        try:
            settings = self.db.get_settings()
            return settings or {
                'theme': 'dark',
                'voiceGender': 'female',
                'language': 'en',
                'wakeWord': 'Hey Wolf',
                'alwaysListen': False
            }
        except Exception as e:
            self.send_message("error", f"Failed to load settings: {str(e)}")
            return {}

    def save_settings(self, settings):
        """Save user settings to database"""
        try:
            self.db.save_settings(settings)
            self.settings = settings
            self.setup_tts()  # Reconfigure TTS with new settings
            return True
        except Exception as e:
            self.send_message("error", f"Failed to save settings: {str(e)}")
            return False

    def start_wake_word_detection(self):
        """Start wake word detection in background thread"""
        def detection_loop():
            while self.wake_word_active:
                try:
                    if self.wake_word_detector.detect():
                        self.send_message("wake_word_detected", {})
                        self.handle_wake_word()
                    time.sleep(0.1)
                except Exception as e:
                    self.send_message("error", f"Wake word detection error: {str(e)}")
                    time.sleep(1)
        
        thread = threading.Thread(target=detection_loop, daemon=True)
        thread.start()

    def handle_wake_word(self):
        """Handle wake word detection"""
        self.speak("Yes, I'm listening.")
        self.start_listening()

    def start_listening(self):
        """Start listening for voice commands"""
        if self.is_listening:
            return
        
        self.is_listening = True
        self.send_message("status", "Listening for commands...")
        
        def listen_thread():
            try:
                with self.microphone as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Listen for audio with timeout
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=5)
                
                # Recognize speech
                try:
                    text = self.recognizer.recognize_google(audio)
                    self.send_message("speech_recognized", {"text": text})
                    self.process_command(text)
                except sr.UnknownValueError:
                    self.send_message("error", "Could not understand audio")
                except sr.RequestError as e:
                    self.send_message("error", f"Speech recognition error: {str(e)}")
                
            except sr.WaitTimeoutError:
                self.send_message("status", "Listening timeout")
            except Exception as e:
                self.send_message("error", f"Listening error: {str(e)}")
            finally:
                self.is_listening = False
                self.send_message("status", "Ready")
        
        thread = threading.Thread(target=listen_thread, daemon=True)
        thread.start()

    def process_command(self, text):
        """Process voice command"""
        try:
            # Log the interaction
            self.db.log_interaction(text, "", "command")
            
            # Check if it's a system command
            if self.is_system_command(text):
                result = self.pc_controller.execute_command(text)
                self.send_message("command_executed", {
                    "command": text,
                    "result": result["message"],
                    "success": result["success"]
                })
                if result["success"]:
                    self.speak(result["message"])
            else:
                # Send to AI for conversational response
                self.get_ai_response(text)
                
        except Exception as e:
            error_msg = f"Command processing error: {str(e)}"
            self.send_message("error", error_msg)
            self.speak("Sorry, I encountered an error processing your command.")

    def is_system_command(self, text):
        """Check if text is a system command"""
        system_keywords = [
            'open', 'close', 'start', 'launch', 'quit', 'exit',
            'volume', 'screenshot', 'shutdown', 'restart', 'sleep',
            'minimize', 'maximize', 'window', 'browser', 'notepad',
            'calculator', 'time', 'date'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in system_keywords)

    def get_ai_response(self, text):
        """Get AI response from Ollama"""
        try:
            response = self.ollama_client.get_response(text, self.settings.get('language', 'en'))
            
            # Log the interaction
            self.db.log_interaction(text, response, "conversation")
            
            self.send_message("ai_response", {
                "text": response,
                "type": "conversation"
            })
            
            # Speak the response
            self.speak(response)
            
        except Exception as e:
            error_msg = f"AI response error: {str(e)}"
            self.send_message("error", error_msg)
            self.speak("Sorry, I'm having trouble connecting to my AI brain right now.")

    def speak(self, text):
        """Convert text to speech"""
        try:
            def speak_thread():
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            
            thread = threading.Thread(target=speak_thread, daemon=True)
            thread.start()
        except Exception as e:
            self.send_message("error", f"TTS error: {str(e)}")

    def send_message(self, msg_type, data):
        """Send message to Electron frontend"""
        try:
            message = {
                "type": msg_type,
                "data": data,
                "timestamp": time.time()
            }
            print(json.dumps(message), flush=True)
        except Exception as e:
            print(f"Message send error: {str(e)}", file=sys.stderr, flush=True)

    def handle_input(self, input_data):
        """Handle input from Electron frontend"""
        try:
            data = json.loads(input_data.strip())
            msg_type = data.get('type')
            msg_data = data.get('data', {})
            
            if msg_type == 'command':
                self.process_command(msg_data)
            elif msg_type == 'toggle-listening':
                if msg_data.get('listening'):
                    self.start_listening()
                else:
                    self.is_listening = False
            elif msg_type == 'save-settings':
                self.save_settings(msg_data)
            else:
                self.send_message("error", f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError as e:
            self.send_message("error", f"JSON decode error: {str(e)}")
        except Exception as e:
            self.send_message("error", f"Input handling error: {str(e)}")

    def run(self):
        """Main loop to handle input from Electron"""
        try:
            self.send_message("status", "Wolf AI Backend ready")
            
            while True:
                try:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    self.handle_input(line)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.send_message("error", f"Main loop error: {str(e)}")
                    
        except Exception as e:
            self.send_message("error", f"Backend runtime error: {str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        self.wake_word_active = False
        self.is_listening = False
        if hasattr(self, 'tts_engine'):
            try:
                self.tts_engine.stop()
            except:
                pass

if __name__ == "__main__":
    try:
        backend = VoiceBackend()
        backend.run()
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc()
