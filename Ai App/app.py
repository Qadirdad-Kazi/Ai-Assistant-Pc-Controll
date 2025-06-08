#!/usr/bin/env python3
"""
Wolf AI Voice Assistant - Web Version
A web-based voice assistant with PC control capabilities
"""

from flask import Flask, render_template, request, jsonify, session, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
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
from voice_backend import VoiceBackend
import traceback
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not available, using system environment variables")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['CORS_HEADERS'] = 'Content-Type'

# Allow all origins for development
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins for development
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configure Socket.IO with CORS
socketio = SocketIO(
    app,
    cors_allowed_origins="*",  # Allow all origins for development
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)

# Global state
wake_word_detector = None
assistant_active = False

# Initialize components
def init_components():
    pass  # Placeholder for component initialization

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle new client connection."""
    logger.info('Client connected: %s', request.sid)
    emit('connection_established', {
        'status': 'connected',
        'timestamp': datetime.now().isoformat(),
        'settings': app_state.settings,
        'state': {
            'is_listening': app_state.is_listening,
            'is_processing': app_state.is_processing,
            'is_speaking': app_state.is_speaking,
            'current_language': app_state.current_language,
            'voice_gender': app_state.voice_gender.name.lower()
        }
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected: %s', request.sid)
    if app_state.is_listening:
        stop_listening()

@socketio.on('start_listening')
def handle_start_listening(data=None):
    """Start listening for voice input."""
    try:
        if app_state.is_processing:
            emit('status', {'status': 'error', 'message': 'Already processing a request'})
            return
        
        if app_state.is_listening:
            emit('status', {'status': 'warning', 'message': 'Already listening'})
            return
        
        app_state.is_listening = True
        
        # Start listening in a separate thread to avoid blocking
        def listen_thread():
            try:
                logger.info('Starting voice input listener')
                emit('status', {'status': 'listening', 'message': 'Listening...'})
                
                # Use the voice processor to listen for input
                text = voice_processor.listen(timeout=10, phrase_time_limit=5)
                
                if text:
                    emit('user_input', {'text': text})
                    process_user_input(text)
                else:
                    emit('status', {'status': 'idle', 'message': 'No speech detected'})
                
            except Exception as e:
                logger.error('Error in listen thread: %s', str(e))
                emit('error', {'message': f'Error: {str(e)}'})
            finally:
                app_state.is_listening = False
                if not app_state.is_processing:
                    emit('status', {'status': 'idle', 'message': 'Ready'})
        
        # Start the listening thread
        thread = threading.Thread(target=listen_thread, daemon=True)
        thread.start()
        
        return {'status': 'success', 'message': 'Started listening'}
    
    except Exception as e:
        logger.error('Error starting listening: %s', str(e))
        app_state.is_listening = False
        emit('error', {'message': f'Failed to start listening: {str(e)}'})
        return {'status': 'error', 'message': str(e)}

@socketio.on('stop_listening')
def handle_stop_listening():
    """Stop listening for voice input."""
    stop_listening()
    return {'status': 'success', 'message': 'Stopped listening'}

def stop_listening():
    """Helper function to stop listening."""
    if app_state.is_listening:
        app_state.is_listening = False
        voice_processor.stop_listening()
        emit('status', {'status': 'idle', 'message': 'Stopped listening'})
        logger.info('Stopped listening')

@socketio.on('process_text')
def handle_process_text(data):
    """Process text input from the user."""
    try:
        text = data.get('text', '').strip()
        if not text:
            emit('error', {'message': 'No text provided'})
        
        # Process the text input
        process_user_input(text)
        
    except Exception as e:
        logger.error(f'Error processing text: {str(e)}')
        emit('error', {'message': f'Error processing text: {str(e)}'})

def load_settings():
    """Load user settings from database"""
    try:
        return {
            'theme': 'dark',
            'voiceGender': 'female',
            'language': 'en',
            'wakeWord': 'Hey Wolf',
            'alwaysListen': False
        }
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return {
            'theme': 'dark',
            'voiceGender': 'female',
            'language': 'en',
            'wakeWord': 'Hey Wolf',
            'alwaysListen': False
        }

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
    """
    Process voice or text command
    
    Args:
        text (str): The command text to process
        
    Returns:
        dict: A dictionary containing the command result with the following keys:
            - type (str): The type of response ("command" or "error")
            - success (bool): Whether the command was processed successfully
            - message (str): The result message or error message
    """
    try:
        # Log the command interaction
        self.db.log_interaction(text, "", "command")
        
        if self.is_system_command(text):
            # Execute the system command
            result = self.pc_controller.execute_command(text)
            self.db.log_command(text, result["success"], result["message"])
            
            # If command was successful and TTS is available, speak the response
            if self.tts_engine and result["success"]:
                def speak_thread():
                    try:
                        self.tts_engine.say(result["message"])
                        self.tts_engine.runAndWait()
                    except Exception as e:
                        logger.error(f"Error in TTS: {e}")
                
                # Start TTS in a separate thread
                threading.Thread(target=speak_thread, daemon=True).start()
            
            # Return command result
            return {
                "type": "command",
                "success": result["success"],
                "message": result["message"]
            }
            
        # If not a system command, return appropriate response
        return {
            "type": "command",
            "success": False,
            "message": "Command not recognized as a system command"
        }
        
    except Exception as e:
        error_msg = f"Error processing command: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "type": "error",
            "success": False,
            "message": error_msg
        }

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

    def process_text_command(self, text, language='en'):
        """Process a text command and return the response"""
        try:
            # Log the user input
            logger.info(f"Processing text command: {text}")
            
            # Check if this is a system command
            if text.lower().startswith('wolf'):
                command = text[4:].strip().lower()
                return self.handle_system_command(command, language)
            
            # Check for empty input
            if not text.strip():
                return "I didn't catch that. Could you please repeat?"
                
            # Process as a regular query - get_response will handle static responses first
            response = self.ollama_client.get_response(text, language)
            
            # Log the interaction
            self.db.log_interaction(text, response, 'text')
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing text command: {e}")
            logger.error(traceback.format_exc())
            return "I'm sorry, I encountered an error processing your request."

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
backend = VoiceBackend()

# WebSocket event handlers for voice backend
@socketio.on('voice_command')
def handle_voice_command(data):
    try:
        command = data.get('command', '').lower()
        logger.info(f"Received voice command: {command}")
        
        # Process the command
        response = backend.process_command(command)
        
        # Send the response back to the client
        emit('assistant_response', {'text': response})
        
    except Exception as e:
        logger.error(f"Error processing voice command: {e}")
        emit('error', {'message': str(e)})

@app.route('/')
def index():
    return render_template('index.html')

# Initialize components when starting the app
def init_components():
    # Add initialization code here if needed
    return True

if not init_components():
    logger.error("Failed to initialize required components. Exiting.")
    sys.exit(1)

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
    port = int(os.environ.get('PORT', 5002))  # Use port from environment or default to 5002
    print("Starting Wolf AI Voice Assistant Web Server...")
    print(f"Access the app at: http://localhost:{port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=True)