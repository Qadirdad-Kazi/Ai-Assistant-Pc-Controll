#!/usr/bin/env python3
"""
Wolf AI Voice Assistant Backend
Handles voice processing, wake word detection, and system control
"""

import sys
import json
import threading
import json # Ensure json is imported
import time # Ensure time is imported
import sys # Ensure sys is imported
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
    def __init__(self, send_ws_func=None): # MODIFIED: Added send_ws_func
        self.config = Config()
        self.db = Database()
        self.recognizer = sr.Recognizer()
        
        self._send_websocket_message_actual = send_ws_func # MODIFIED: Store the passed-in function
        self.microphone = sr.Microphone()
        
        # Initialize components
        self.wake_word_detector = WakeWordDetector()
        self.pc_controller = PCController()
        self.ollama_client = OllamaClient()
        
        # State
        self.is_listening = False
        self.wake_word_active = True
        self.current_mode = 'ai'  # Default operation mode
        self.cancel_requested = False
        self._stop_speaking = False  # Flag to stop current speech
        self.settings = self.load_settings()
        
        # TTS Queue and state
        self.tts_queue = []
        self.tts_lock = threading.Lock()
        self.tts_running = True
        self.current_tts_engine = None
        
        # Start the TTS processing thread
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        # Start background threads
        self.start_wake_word_detection()

    def notify_websocket_ready(self):
        """Called by WebSocketServer when it's ready to send messages."""
        self.send_message("status", "Voice backend initialized and WebSocket ready")

    def _create_tts_engine(self):
        """Create and configure a new TTS engine instance"""
        try:
            engine = pyttsx3.init()
            if not engine:
                print("[TTS] Failed to create TTS engine")
                return None
            
            # Configure TTS engine
            voices = engine.getProperty('voices')
            if voices:
                gender = self.settings.get('voiceGender', 'female')
                print(f"[TTS] Looking for {gender} voice...")
                for voice in voices:
                    if gender.lower() in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        print(f"[TTS] Using voice: {voice.name}")
                        break
            
            # Set speech rate and volume
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 0.8)
            
            return engine
            
        except Exception as e:
            print(f"[TTS] Error creating TTS engine: {str(e)}", file=sys.stderr)
            return None
    
    def _tts_worker(self):
        """Worker thread that processes TTS requests from the queue"""
        print("[TTS] TTS worker thread started")
        
        while self.tts_running:
            engine = None
            try:
                # Small sleep to prevent CPU overuse
                time.sleep(0.1)
                
                # Get the next text to speak, if any
                with self.tts_lock:
                    if not self.tts_queue or not self.tts_running:
                        continue
                    text = self.tts_queue.pop(0)
                
                # Skip empty text
                if not text or not text.strip():
                    print("[TTS] Skipping empty text")
                    continue
                
                # Handle cancel request
                if self.cancel_requested:
                    print("[TTS] Cancellation requested, skipping message")
                    self.cancel_requested = False
                    continue
                
                print(f"[TTS] Processing: {text[:100]}...")
                
                # Create a new TTS engine for this message
                engine = pyttsx3.init()
                if not engine:
                    print("[TTS] Failed to create TTS engine")
                    time.sleep(1)  # Prevent tight loop on error
                    continue
                
                # Configure the engine
                try:
                    voices = engine.getProperty('voices')
                    if voices:
                        gender = self.settings.get('voiceGender', 'female')
                        for voice in voices:
                            if gender.lower() in voice.name.lower():
                                engine.setProperty('voice', voice.id)
                                break
                    
                    engine.setProperty('rate', 180)
                    engine.setProperty('volume', 0.8)
                    
                    # Store the current engine for potential cancellation
                    with self.tts_lock:
                        self.current_tts_engine = engine
                    
                    print(f"[TTS] Speaking: {text[:100]}...")
                    
                    # Simple blocking speak - we'll handle one message at a time
                    engine.say(text)
                    engine.runAndWait()
                    
                    print("[TTS] Finished speaking")
                    
                except Exception as e:
                    print(f"[TTS] Error during speech: {str(e)}", file=sys.stderr)
                    # If we get a run loop error, try to clean up and continue
                    if "run loop already started" in str(e):
                        print("[TTS] Detected run loop error, attempting to recover...")
                    
            except Exception as e:
                print(f"[TTS] Error in TTS worker: {str(e)}", file=sys.stderr)
                time.sleep(1)  # Prevent tight loop on error
                
            finally:
                # Clean up the engine
                if engine:
                    try:
                        with self.tts_lock:
                            if self.current_tts_engine is engine:
                                self.current_tts_engine = None
                        try:
                            engine.stop()
                        except:
                            pass
                        try:
                            engine.endLoop()
                        except:
                            pass
                    except Exception as e:
                        print(f"[TTS] Error during engine cleanup: {str(e)}", file=sys.stderr)

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
                if self.cancel_requested:
                    print("[VoiceBackend] Wake word detection paused due to cancel request.")
                    # Potentially add a small sleep here or a mechanism to resume
                    # For now, just skip detection until flag is reset (e.g., by next command)
                    # Or reset it here if cancel is a one-time interruption for wake word too.
                    # Let's assume cancel should also stop wake word listening temporarily.
                    self.cancel_requested = False # Resetting here, implies cancel stops current listen, then wake word resumes
                    time.sleep(0.5) # Give a small pause
                    continue
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

    def set_operation_mode(self, mode):
        print(f"[VoiceBackend] Attempting to set mode to: {mode}")
        if mode in ['ai', 'pc_control']:
            self.current_mode = mode
            print(f"[VoiceBackend] SUCCESSFULLY SET self.current_mode to: {self.current_mode}")
            self.send_message("mode_changed", {"mode": self.current_mode, "status": f"Mode changed to {mode.replace('_', ' ').title() }"})
        else:
            print(f"[VoiceBackend] ERROR: Invalid mode '{mode}' received. Mode not changed.")
            self.send_message("error", f"Invalid operation mode: {mode}")

    def cancel_current_actions(self):
        print("[VoiceBackend] cancel_current_actions called.")
        self.cancel_requested = True
        
        # Attempt to stop TTS
        if self.tts_engine:
            try:
                self.tts_engine.stop() # Stop current speech
            except Exception as e:
                print(f"[VoiceBackend] Error stopping TTS engine: {e}")
        # Clear the TTS queue to prevent further speech
        with self.tts_lock:
            self.tts_queue.clear()
            print("[VoiceBackend] TTS queue cleared.")

        # The listening thread will check this flag and stop processing
        # Wake word detection loop will also check this flag
        
        self.is_listening = False # Explicitly set listening to false
        self.send_message("status", "Action cancelled by user.")
        # Reset the flag after a short delay or when the next action starts
        # For now, let it be reset by the methods that check it.

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
                if self.cancel_requested:
                    print("[VoiceBackend] Cancellation requested before listening started.")
                    self.cancel_requested = False # Reset flag
                    self.is_listening = False
                    self.send_message("status", "Listening cancelled.")
                    return

                with self.microphone as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Listen for audio with timeout
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=5)
                
                # Recognize speech
                if self.cancel_requested:
                    print("[VoiceBackend] Cancellation requested after listening, before recognition.")
                    self.cancel_requested = False # Reset flag
                    self.is_listening = False
                    self.send_message("status", "Processing cancelled.")
                    return
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
        """Process voice or text command based on current mode."""
        try:
            # Log the interaction
            self.send_message("user_command", {"text": text, "mode": self.current_mode})

            if self.current_mode == 'ai':
                # In AI mode, primarily use AI for responses
                self.get_ai_response(text)
            elif self.current_mode == 'pc_control':
                # In PC control mode, directly use PCController
                response_data = self.pc_controller.execute_command(text)
                final_message_to_log_and_speak = ""

                # Ensure response_data is a dictionary for consistent access and modification
                if not isinstance(response_data, dict):
                    response_data = {} # Initialize if it's None or not a dict

                if response_data.get('message'): # Check if a message exists from pc_controller
                    final_message_to_log_and_speak = response_data['message']
                    # 'success' should ideally be set by handle_command.
                    # If 'success' is not in response_data, we assume True if a message is present.
                    if 'success' not in response_data:
                        response_data['success'] = True 
                else:
                    final_message_to_log_and_speak = f"I couldn't execute the PC command: {text}"
                    response_data['success'] = False # Explicitly set success to False for fallback
                    response_data['message'] = final_message_to_log_and_speak
                
                # Log the PC control interaction
                self.db.log_interaction(text, final_message_to_log_and_speak, "pc_control")
                
                # Send result to frontend
                self.send_message("pc_control_result", response_data)
                
                # Speak the response
                self.speak(final_message_to_log_and_speak)
            else:
                unknown_mode_msg = f"Unknown operation mode: {self.current_mode}. Cannot process command."
                self.send_message("error", unknown_mode_msg)
                self.speak("I'm in an unrecognized operational mode.")
                
        except Exception as e:
            error_msg = f"Error processing command '{text}' in mode '{self.current_mode}': {str(e)}"
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

    def send_message(self, msg_type, data_payload):
        """Send message to Electron frontend via WebSocket using the injected function."""
        if not hasattr(self, '_send_websocket_message_actual') or not self._send_websocket_message_actual:
            # Fallback if no send function provided
            print(json.dumps({
                "type": msg_type, 
                "data": data_payload,
                "timestamp": time.time(), 
                "source": "VoiceBackend_fallback_print"
            }), flush=True)
            return
        try:
            # This will call WebSocketServer.send_message_sync (or whatever was passed)
            self._send_websocket_message_actual(msg_type, data_payload)
        except Exception as e:
            print(f"VoiceBackend.send_message (via actual) error: {str(e)}", file=sys.stderr, flush=True)



    def speak(self, text):
        """Add text to TTS queue"""
        if not text:
            return
            
        print(f"[TTS] Adding to queue: {text[:100]}...")
        with self.tts_lock:
            self.tts_queue.append(text)
            print(f"[TTS] Queue size: {len(self.tts_queue)}")
    
    def cancel_current_speech(self):
        """Stop the current speech and clear the queue"""
        print("[TTS] Cancelling current speech")
        with self.tts_lock:
            self.cancel_requested = True
            self.tts_queue.clear()
            if self.current_tts_engine:
                try:
                    self.current_tts_engine.stop()
                    self.current_tts_engine.endLoop()
                except:
                    pass
                self.current_tts_engine = None

    def handle_input(self, input_data_str):
        """Handle input from Electron frontend (placeholder if primarily using WebSockets)"""
        try:
            print(f"[VoiceBackend] handle_input (placeholder) called with: {input_data_str[:100]}", flush=True)
            # If this method is actively used for commands via stdin:
            # data = json.loads(input_data_str.strip()) 
            # msg_type = data.get('type')
            # msg_data = data.get('data', {})
            # ... (logic to handle parsed commands) ...
            # For example:
            # if msg_type == 'some_command_via_stdin':
            #    self.process_command(msg_data.get('command_text'))
        except json.JSONDecodeError as e:
            # Or print to stderr if send_message itself might be problematic during early init
            print(f"JSON decode error in handle_input: {str(e)}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"Input handling error in handle_input: {str(e)}", file=sys.stderr, flush=True)

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
        
        # Stop the TTS worker thread
        with self.tts_lock:
            self.tts_running = False
            self.tts_queue.clear()
            if self.current_tts_engine:
                try:
                    self.current_tts_engine.stop()
                    self.current_tts_engine.endLoop()
                except:
                    pass
                self.current_tts_engine = None

if __name__ == "__main__":
    try:
        backend = VoiceBackend()
        backend.run()
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc()
