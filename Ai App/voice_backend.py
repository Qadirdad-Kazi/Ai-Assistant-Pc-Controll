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
        
        # Audio processing state
        self.audio_buffer = bytearray()
        self.audio_buffer_lock = threading.Lock()
        self.processing_audio = False
        
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
        
        # Initialize TTS engine with enhanced settings
        try:
            self.tts_engine = pyttsx3.init()
            
            # Get available voices
            voices = self.tts_engine.getProperty('voices')
            
            # Print available voices for debugging
            print("[VoiceBackend] Available voices:")
            for i, voice in enumerate(voices):
                print(f"  {i}: {voice.name} ({voice.id})")
            
            # Try to find a high-quality voice (usually the last ones in the list)
            if voices:
                # Try to select a better voice (usually higher index voices are better quality)
                voice_index = -1  # Default to last voice
                
                # Look for specific high-quality voices first
                for i, voice in enumerate(voices):
                    if 'Karen' in voice.name:  # macOS high-quality voice
                        voice_index = i
                        break
                    elif 'Daniel' in voice.name:  # Another good macOS voice
                        voice_index = i
                        break
                
                if voice_index == -1 and len(voices) > 0:
                    voice_index = -1  # Default to last voice
                
                self.tts_engine.setProperty('voice', voices[voice_index].id)
                print(f"[VoiceBackend] Using voice: {voices[voice_index].name}")
            
            # Optimize speech parameters for clarity
            self.tts_engine.setProperty('rate', 175)  # Slightly faster than default (150)
            self.tts_engine.setProperty('volume', 1.0)  # Maximum volume (0.0 to 1.0)
            
            # Additional settings for better clarity
            if hasattr(self.tts_engine, 'setProperty'):
                try:
                    # These properties might not be available on all platforms
                    self.tts_engine.setProperty('pitch', 1.0)  # Slightly higher pitch can improve clarity
                except Exception as e:
                    print(f"[VoiceBackend] Could not set pitch (may not be supported): {e}")
            
            print(f"[VoiceBackend] TTS engine initialized with rate: {self.tts_engine.getProperty('rate')}")
            
        except Exception as e:
            print(f"[VoiceBackend] Error initializing TTS engine: {e}")
            self.tts_engine = None
        
        # Start the TTS processing thread
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        # Start background threads
        self.start_wake_word_detection()

    def notify_websocket_ready(self):
        """Called by WebSocketServer when it's ready to send messages."""
        self.send_message("status", "Voice backend initialized and WebSocket ready")

    def _preprocess_text(self, text):
        """Preprocess text to improve TTS output quality.
        
        Args:
            text (str): The input text to preprocess
            
        Returns:
            str: Preprocessed text ready for TTS
        """
        if not text or not isinstance(text, str):
            return ""
            
        # Common replacements for better TTS
        replacements = {
            # Remove or replace special characters
            '"': '',
            "'": '',
            '  ': ' ',  # Double spaces to single
            ' .': '.',  # Fix spaces before periods
            ' ,': ',',  # Fix spaces before commas
            ' ;': ';',  # Fix spaces before semicolons
            ' ?': '?',  # Fix spaces before question marks
            ' !': '!',  # Fix spaces before exclamation marks
            '``': '"',  # Replace backticks with quotes
            "''": '"',  # Replace single quotes with double quotes
            '...': '. ',  # Handle ellipsis
            # Add any other replacements needed for your use case
        }
        
        # Apply replacements
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Ensure proper sentence ending
        if text and text[-1] not in {'.', '!', '?'}:
            text += '.'
            
        return text
        
    def _create_tts_engine(self):
        """Create and configure a new TTS engine instance"""
        try:
            engine = pyttsx3.init()
            if not engine:
                print("[TTS] Failed to initialize TTS engine")
                return None
            
            # Configure default properties
            engine.setProperty('rate', 180)  # Words per minute
            engine.setProperty('volume', 1.0)  # Full volume
            
            # Try to set a good voice
            try:
                voices = engine.getProperty('voices')
                if voices:
                    # Try to find a high-quality voice (usually the last ones in the list)
                    preferred_voices = ['Karen', 'Samantha', 'Daniel', 'Alex', 'Fiona']
                    for voice in voices:
                        if any(name.lower() in voice.name.lower() for name in preferred_voices):
                            engine.setProperty('voice', voice.id)
                            print(f"[TTS] Using voice: {voice.name}")
                            break
                    else:
                        # Fall back to first available voice
                        engine.setProperty('voice', voices[0].id)
                        print(f"[TTS] Using default voice: {voices[0].name}")
            except Exception as e:
                print(f"[TTS] Warning: Could not set voice: {str(e)}")
            
            return engine
            
        except Exception as e:
            print(f"[TTS] Error creating TTS engine: {str(e)}", file=sys.stderr)
            return None
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
        while self.tts_running:
            engine = None
            try:
                with self.tts_lock:
                    if not self.tts_queue or not self.tts_running:
                        time.sleep(0.1)
                        continue
                    text = self.tts_queue.pop(0)
                
                # Skip empty text
                if not text or not isinstance(text, str):
                    print("[TTS] Skipping empty text")
                    continue
                
                # Handle cancel request
                if self.cancel_requested:
                    print("[TTS] Cancellation requested, skipping message")
                    self.cancel_requested = False
                    continue
                
                print(f"[TTS] Processing: {text[:100]}...")
                
                # Create a new TTS engine for this message
                engine = self._create_tts_engine()
                if not engine:
                    print("[TTS] Failed to create TTS engine")
                    time.sleep(1)  # Prevent tight loop on error
                    continue
                
                # Configure the engine
                try:
                    # Get voices and select based on settings
                    voices = engine.getProperty('voices') or []
                    if voices:
                        gender = self.settings.get('voiceGender', 'female').lower()
                        # Try to find a matching voice
                        for voice in voices:
                            if gender in voice.name.lower():
                                engine.setProperty('voice', voice.id)
                                break
                
                    # Set speech properties
                    engine.setProperty('rate', 180)  # Slightly faster for better flow
                    engine.setProperty('volume', 1.0)  # Maximum volume
                    
                    # Store the current engine for potential cancellation
                    with self.tts_lock:
                        self.current_tts_engine = engine
                    
                    print(f"[TTS] Speaking: {text[:100]}...")
                    
                    # Simple blocking speak - handle one message at a time
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
            print(f"[VoiceBackend] Invalid mode: {mode}")
            self.send_message("error", f"Invalid mode: {mode}")

    def stop_background_listener(self):
        """Stop the background listener if it's running"""
        was_listening = self.is_listening
        self.cancel_requested = True
        self.is_listening = False
        
        # If we were listening, wait for the thread to finish
        if was_listening and hasattr(self, 'listen_thread') and self.listen_thread.is_alive():
            print("[VoiceBackend] Stopping listener thread...")
            try:
                # Set a timeout to prevent hanging
                self.listen_thread.join(timeout=3.0)
                if self.listen_thread.is_alive():
                    print("[VoiceBackend] Listener thread did not stop gracefully")
            except Exception as e:
                print(f"[VoiceBackend] Error stopping listener thread: {e}")
        
        # Ensure we're in a clean state
        self.cancel_requested = False
        print("[VoiceBackend] Background listener stopped")
        
    def stop_listening(self):
        """Stop listening for voice commands"""
        self.stop_background_listener()

    def cancel_current_actions(self):
        """Cancel any ongoing actions."""
        try:
            print("[VoiceBackend] Canceling current actions...")
            
            # Stop the background listener first
            self.stop_background_listener()
            
            # Stop TTS if it's running
            if hasattr(self, 'tts_engine') and self.tts_engine is not None:
                try:
                    print("[VoiceBackend] Stopping TTS engine...")
                    self.tts_engine.stop()
                    print("[VoiceBackend] TTS engine stopped")
                except Exception as e:
                    print(f"[VoiceBackend] Error stopping TTS engine: {e}")
            
            # Clear any pending TTS queue
            with self.tts_lock:
                queue_size = len(self.tts_queue)
                if queue_size > 0:
                    print(f"[VoiceBackend] Clearing TTS queue (had {queue_size} items)")
                    self.tts_queue = []
            
            # Update state
            self.is_listening = False
            self.cancel_requested = True
            
            # Notify the frontend
            self.send_message("listening_state", {"listening": False})
            print("[VoiceBackend] Actions cancelled and state reset")
            
        except Exception as e:
            print(f"[VoiceBackend] Error in cancel_current_actions: {e}")
            # Make sure we still update the state even if there was an error
            self.is_listening = False
            self.cancel_requested = True
            self.send_message("listening_state", {"listening": False})

    def handle_wake_word(self):
        """Handle wake word detection"""
        self.speak("Yes, I'm listening.")
        self.start_listening()

    def start_listening(self):
        """Start listening for voice commands"""
        if self.is_listening:
            print("[VoiceBackend] Already listening, ignoring start_listening")
            return
            
        print("[VoiceBackend] Starting to listen for voice commands...")
        self.is_listening = True
        self.cancel_requested = False
        
        def listen_thread():
            try:
                # Notify frontend
                self.send_message("listening_state", {"listening": True})
                self.send_message("status", "Listening...")
                
                # Use a fresh recognizer instance
                recognizer = sr.Recognizer()
                
                # Get default microphone
                with sr.Microphone() as source:
                    print("[VoiceBackend] Adjusting for ambient noise...")
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    print("[VoiceBackend] Ready to listen")
                    
                    while self.is_listening and not self.cancel_requested:
                        try:
                            print("[VoiceBackend] Listening...")
                            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                            
                            print("[VoiceBackend] Processing audio...")
                            try:
                                # Convert speech to text
                                text = recognizer.recognize_google(audio)
                                print(f"[VoiceBackend] Recognized: {text}")
                                
                                # Process the recognized text as if it was manual input
                                if text and isinstance(text, str):
                                    self.process_command(text)
                                    
                            except sr.UnknownValueError:
                                print("[VoiceBackend] Could not understand audio")
                                self.send_message("status", "Could not understand audio")
                                
                            except sr.RequestError as e:
                                error_msg = f"Could not request results; {e}"
                                print(f"[VoiceBackend] {error_msg}")
                                self.send_message("error", error_msg)
                                
                        except sr.WaitTimeoutError:
                            # No speech detected, continue listening
                            continue
                            
                        except Exception as e:
                            error_msg = f"Error in voice recognition: {str(e)}"
                            print(f"[VoiceBackend] {error_msg}")
                            self.send_message("error", error_msg)
                            break
                            
            except Exception as e:
                error_msg = f"Fatal error in voice recognition: {str(e)}"
                print(f"[VoiceBackend] {error_msg}")
                print(traceback.format_exc())
                self.send_message("error", error_msg)
                
            finally:
                print("[VoiceBackend] Stopped listening")
                self.is_listening = False
                self.send_message("status", "Ready")
                self.send_message("listening_state", {"listening": False})
        
        # Start the listening in a separate thread
        self.listen_thread = threading.Thread(target=listen_thread, daemon=True)
        self.listen_thread.start()
        print("[VoiceBackend] Voice recognition started")
        
    def handle_audio_data(self, audio_data):
        """
        Handle incoming audio data from WebSocket
        """
        if not self.is_listening or self.cancel_requested:
            return
            
        try:
            # Process audio data in a separate thread to avoid blocking
            threading.Thread(
                target=self._process_audio_data,
                args=(audio_data,),
                daemon=True
            ).start()
        except Exception as e:
            print(f"[VoiceBackend] Error processing audio data: {e}")
            self.send_message("error", f"Error processing audio data: {str(e)}")
    
    def _process_audio_data(self, audio_data):
        """
        Process audio data in a separate thread
        """
        try:
            # Convert the audio data to an AudioData object
            audio = sr.AudioData(
                audio_data,
                sample_rate=16000,  # Adjust based on your audio format
                sample_width=2      # 16-bit audio
            )
            
            # Process the audio using the existing callback
            self._process_audio_instance(audio)
            
        except Exception as e:
            print(f"[VoiceBackend] Error in audio data processing: {e}")
            self.send_message("error", f"Error in audio processing: {str(e)}")
    
    def _process_audio_instance(self, audio):
        """
        Process an audio instance (either from microphone or WebSocket)
        """
        if not self.is_listening or self.cancel_requested:
            return
            
        try:
            # Use the recognizer to process the audio
            text = self.recognizer.recognize_google(audio)
            print(f"[VoiceBackend] Recognized speech: {text}")
            
            # Update UI with the recognized text
            self.send_message("speech_recognized", {
                "text": text,
                "timestamp": time.time(),
                "confidence": 1.0
            })
            
            # Process the recognized text
            if text:
                if self.wake_word_active and self.current_mode == 'wake_word':
                    wake_word = self.settings.get('wake_word', 'hey wolf').lower()
                    if wake_word.lower() in text.lower():
                        # Extract command after wake word
                        command = text.lower().split(wake_word.lower(), 1)[-1].strip()
                        if command:
                            self.process_command(command)
                else:
                    # Process the full command in direct mode
                    self.process_command(text)
                    
        except sr.UnknownValueError:
            print("[VoiceBackend] Could not understand audio")
            self.send_message("status", "Could not understand audio")
            
        except sr.RequestError as e:
            error_msg = f"Speech recognition error: {str(e)}"
            print(f"[VoiceBackend] {error_msg}")
            self.send_message("error", error_msg)
            
        except Exception as e:
            print(f"[VoiceBackend] Error in speech recognition: {e}")
            self.send_message("error", f"Error processing speech: {str(e)}")
    
    def _process_audio_callback(self, recognizer, audio):
        """
        Callback function that processes the captured audio.
        This runs in a separate thread from the main listening thread.
        """
        if self.cancel_requested:
            print("[VoiceBackend] Ignoring audio - cancellation requested")
            return
            
        print("[VoiceBackend] Processing captured audio...")
        try:
            # Send a processing status update to the UI
            self.send_message("status", "Processing speech...")
            
            # Check if we have valid audio data
            if not audio or len(audio.get_raw_data()) < 100:  # Minimum audio length check
                print("[VoiceBackend] Audio data too short or empty, ignoring...")
                return
            
            # Process the audio using our instance method
            self._process_audio_instance(audio)
                
        except Exception as e:
            print(f"[VoiceBackend] Error in audio processing: {e}")
            self.send_message("error", f"Error processing audio: {str(e)}")
            
        finally:
            # Ensure we always send a ready status, even if there was an error
            if not self.cancel_requested:
                self.send_message("status", "Ready")
            # The listening state is controlled by the main listening thread
            # Don't reset it here to allow for continuous listening

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



    def speak(self, text, priority=False):
        """Add text to TTS queue with optional priority
        
        Args:
            text (str): The text to speak
            priority (bool): If True, add to front of queue (default: False)
        """
        if not text or not isinstance(text, str):
            print("[TTS] Cannot speak empty or invalid text")
            return
            
        # Preprocess the text for better TTS
        text = self._preprocess_text(text)
        
        with self.tts_lock:
            if priority and self.tts_queue:
                # Insert as next item to be spoken
                self.tts_queue.insert(0, text)
                print(f"[TTS] Added to front of queue: {text[:100]}...")
            else:
                # Add to end of queue
                self.tts_queue.append(text)
                print(f"[TTS] Added to queue: {text[:100]}...")
                
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
                except Exception as e:
                    print(f"[TTS] Error stopping TTS engine: {str(e)}", file=sys.stderr, flush=True)
                finally:
                    self.current_tts_engine = None

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
                except Exception as e:
                    print(f"[TTS] Error stopping TTS engine: {str(e)}", file=sys.stderr, flush=True)
                finally:
                    self.current_tts_engine = None

    def handle_input(self, input_data_str):
        """Handle input from Electron frontend"""
        try:
            print(f"[VoiceBackend] Received input: {input_data_str}")
            
            # Parse the input data
            try:
                if isinstance(input_data_str, dict):
                    data = input_data_str
                else:
                    data = json.loads(input_data_str)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"[VoiceBackend] Invalid input format: {e}")
                return
                
            msg_type = data.get('type')
            msg_data = data.get('data', {})
            
            print(f"[VoiceBackend] Processing message type: {msg_type}")
            print(f"[VoiceBackend] Message data: {msg_data}")
            
            if msg_type == 'toggle-listening':
                listening = msg_data.get('listening', False)
                print(f"[VoiceBackend] Toggle listening request: {listening}")
                
                if listening:
                    if not self.is_listening:
                        print("[VoiceBackend] Starting voice recognition...")
                        self.start_listening()
                        self.send_message("status", "Listening...")
                        self.send_message("listening_state", {"listening": True})
                    else:
                        print("[VoiceBackend] Already listening")
                else:
                    if self.is_listening:
                        print("[VoiceBackend] Stopping voice recognition...")
                        self.stop_background_listener()
                        self.send_message("status", "Ready")
                        self.send_message("listening_state", {"listening": False})
                    else:
                        print("[VoiceBackend] Not currently listening")
                    
            elif msg_type == 'text-input':
                text = msg_data.get('text', '').strip()
                if text:
                    print(f"[VoiceBackend] Processing text input: {text}")
                    self.process_command(text)
                    return {"success": True, "command_processed": True}
            else:
                print(f"[VoiceBackend] Unknown message type: {msg_type}", flush=True)
                return {"success": False, "error": f"Unknown message type: {msg_type}"}
                
        except json.JSONDecodeError as e:
            error_msg = f"JSON decode error in handle_input: {str(e)}"
            print(f"[VoiceBackend] {error_msg}", file=sys.stderr, flush=True)
            return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"Error in handle_input: {str(e)}"
            print(f"[VoiceBackend] {error_msg}", file=sys.stderr, flush=True)
            print(f"[VoiceBackend] Traceback:\n{traceback.format_exc()}", file=sys.stderr, flush=True)
            return {"success": False, "error": error_msg}

    def run(self):
        """Main loop to handle input from Electron"""
        try:
            self.send_message("status", "Wolf AI Backend ready")
            
            while True:
                try:
                    line = sys.stdin.readline()
                    if not line:
                        break
                        
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                        
                    # Process the input
                    result = self.handle_input(line)
                    
                    # If we have a result, send it back to the frontend
                    if result and isinstance(result, dict):
                        # Add a timestamp to the response
                        result['timestamp'] = time.time()
                        # Send the response back to the frontend
                        print(json.dumps(result), flush=True)
                        
                except KeyboardInterrupt:
                    print("\n[VoiceBackend] Received keyboard interrupt, shutting down...", flush=True)
                    break
                    
                except Exception as e:
                    error_msg = f"Error in main loop: {str(e)}"
                    print(f"[VoiceBackend] {error_msg}", file=sys.stderr, flush=True)
                    print(f"[VoiceBackend] Traceback:\n{traceback.format_exc()}", file=sys.stderr, flush=True)
                    
        except Exception as e:
            error_msg = f"Fatal error in VoiceBackend: {str(e)}"
            print(f"[VoiceBackend] {error_msg}", file=sys.stderr, flush=True)
            print(f"[VoiceBackend] Traceback:\n{traceback.format_exc()}", file=sys.stderr, flush=True)
            
        except Exception as e:
            error_msg = f"Backend runtime error: {str(e)}"
            print(f"[VoiceBackend] {error_msg}", file=sys.stderr, flush=True)
            print(f"[VoiceBackend] Traceback:\n{traceback.format_exc()}", file=sys.stderr, flush=True)
            self.send_message("error", error_msg)
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        print("[VoiceBackend] Cleaning up resources...", flush=True)
        
        # Update state flags
        self.wake_word_active = False
        self.is_listening = False
        
        # Stop the TTS worker thread
        with self.tts_lock:
            self.tts_running = False
            self.tts_queue.clear()
            
            # Stop any ongoing TTS
            if self.current_tts_engine:
                try:
                    self.current_tts_engine.stop()
                    self.current_tts_engine.endLoop()
                except Exception as e:
                    print(f"[VoiceBackend] Error during TTS cleanup: {str(e)}", file=sys.stderr, flush=True)
                finally:
                    self.current_tts_engine = None
        
        print("[VoiceBackend] Cleanup complete", flush=True)

if __name__ == "__main__":
    try:
        backend = VoiceBackend()
        backend.run()
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc()
