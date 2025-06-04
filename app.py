#!/usr/bin/env python3
"""
Wolf AI Voice Assistant - Web Version
A web-based voice assistant with PC control capabilities
"""

from flask import Flask, render_template, request, jsonify, session
import threading
import time
import json
import speech_recognition as sr
import pyttsx3
from wake_word import WakeWordDetector
from pc_controller import PCController
from ollama_client import OllamaClient
from database import Database
from config import Config
import traceback
import os

# Try to load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not available, using system environment variables")

app = Flask(__name__)
app.secret_key = os.urandom(24)

class WebVoiceBackend:
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
        except OSError:
            print("Warning: No microphone detected. Voice input will be disabled.")
            self.microphone = None
        
        # Initialize TTS
        try:
            self.tts_engine = pyttsx3.init()
            self.setup_tts()
        except Exception as e:
            print(f"Warning: TTS initialization failed: {e}")
            self.tts_engine = None
        
        # Initialize components
        self.wake_word_detector = WakeWordDetector() if self.microphone else None
        self.pc_controller = PCController()
        self.ollama_client = OllamaClient()
        
        # State
        self.is_listening = False
        self.wake_word_listening = False
        self.settings = self.load_settings()
        
        # Start background wake word detection if microphone is available
        if self.microphone and self.wake_word_detector:
            self.start_background_wake_word_detection()
        
        print("Wolf AI Web Backend initialized")

    def setup_tts(self):
        """Configure text-to-speech engine"""
        if not self.tts_engine:
            return
        try:
            voices = self.tts_engine.getProperty('voices')
            if voices:
                gender = self.settings.get('voiceGender', 'female')
                for voice in voices:
                    if gender.lower() in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            self.tts_engine.setProperty('rate', 180)
            self.tts_engine.setProperty('volume', 0.8)
        except Exception as e:
            print(f"TTS setup error: {e}")

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
            print(f"Failed to load settings: {e}")
            return {}

    def save_settings(self, settings):
        """Save user settings"""
        try:
            self.db.save_settings(settings)
            self.settings = settings
            if self.tts_engine:
                self.setup_tts()
            return True
        except Exception as e:
            print(f"Failed to save settings: {e}")
            return False

    def listen_for_voice(self):
        """Listen for voice input"""
        if not self.microphone:
            return {"success": False, "error": "No microphone available"}
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=5)
            
            try:
                text = self.recognizer.recognize_google(audio)
                return {"success": True, "text": text}
            except sr.UnknownValueError:
                return {"success": False, "error": "Could not understand audio"}
            except sr.RequestError as e:
                return {"success": False, "error": f"Speech recognition error: {str(e)}"}
                
        except sr.WaitTimeoutError:
            return {"success": False, "error": "Listening timeout"}
        except Exception as e:
            return {"success": False, "error": f"Listening error: {str(e)}"}

    def process_command(self, text):
        """Process voice or text command"""
        try:
            self.db.log_interaction(text, "", "command")
            
            if self.is_system_command(text):
                result = self.pc_controller.execute_command(text)
                self.db.log_command(text, result["success"], result["message"])
                
                if self.tts_engine and result["success"]:
                    def speak_thread():
                        try:
                            self.tts_engine.say(result["message"])
                            self.tts_engine.runAndWait()
                        except:
                            pass
                    threading.Thread(target=speak_thread, daemon=True).start()
                
                return {
                    "type": "command",
                    "success": result["success"],
                    "message": result["message"]
                }
            else:
                response = self.ollama_client.get_response(text, self.settings.get('language', 'en'))
                self.db.log_interaction(text, response, "conversation")
                
                if self.tts_engine:
                    def speak_thread():
                        try:
                            self.tts_engine.say(response)
                            self.tts_engine.runAndWait()
                        except:
                            pass
                    threading.Thread(target=speak_thread, daemon=True).start()
                
                return {
                    "type": "conversation",
                    "success": True,
                    "message": response
                }
                
        except Exception as e:
            error_msg = f"Command processing error: {str(e)}"
            return {
                "type": "error", 
                "success": False,
                "message": error_msg
            }

    def start_background_wake_word_detection(self):
        """Start background wake word detection"""
        def wake_word_loop():
            self.wake_word_listening = True
            print("Background wake word detection started - listening for 'Hey Wolf'...")
            
            while self.wake_word_listening:
                try:
                    if self.wake_word_detector and self.wake_word_detector.detect():
                        print("Wake word detected! Starting voice recognition...")
                        # Automatically start listening for commands
                        result = self.listen_for_voice()
                        if result["success"] and result["text"]:
                            response = self.process_command(result["text"])
                            print(f"Wake word command processed: {result['text']}")
                    time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                except Exception as e:
                    print(f"Wake word detection error: {e}")
                    time.sleep(1)
        
        # Start wake word detection in background thread
        wake_thread = threading.Thread(target=wake_word_loop, daemon=True)
        wake_thread.start()

    def stop_background_wake_word_detection(self):
        """Stop background wake word detection"""
        self.wake_word_listening = False
        print("Background wake word detection stopped")

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

# Initialize backend
backend = WebVoiceBackend()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings"""
    return jsonify(backend.settings)

@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save settings"""
    try:
        settings = request.json
        if backend.save_settings(settings):
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to save settings"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/listen', methods=['POST'])
def listen():
    """Start voice listening"""
    try:
        result = backend.listen_for_voice()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/command', methods=['POST'])
def process_command():
    """Process text or voice command"""
    try:
        data = request.json
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"success": False, "error": "No command provided"})
        
        result = backend.process_command(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get usage analytics"""
    try:
        analytics = backend.db.get_usage_analytics()
        return jsonify(analytics)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        history = backend.db.get_recent_interactions(limit)
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/test-ollama', methods=['GET'])
def test_ollama():
    """Test Ollama connection"""
    try:
        result = backend.ollama_client.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/wake-word/start', methods=['POST'])
def start_wake_word():
    """Start background wake word detection"""
    try:
        if backend.microphone and backend.wake_word_detector:
            if not backend.wake_word_listening:
                backend.start_background_wake_word_detection()
                return jsonify({"success": True, "message": "Wake word detection started"})
            else:
                return jsonify({"success": True, "message": "Wake word detection already running"})
        else:
            return jsonify({"success": False, "error": "Microphone or wake word detector not available"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/wake-word/stop', methods=['POST'])
def stop_wake_word():
    """Stop background wake word detection"""
    try:
        backend.stop_background_wake_word_detection()
        return jsonify({"success": True, "message": "Wake word detection stopped"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/wake-word/status', methods=['GET'])
def wake_word_status():
    """Get wake word detection status"""
    try:
        return jsonify({
            "listening": backend.wake_word_listening,
            "available": bool(backend.microphone and backend.wake_word_detector)
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    print("Starting Wolf AI Voice Assistant Web Server...")
    print("Access the app at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)