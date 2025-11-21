#!/usr/bin/env python3
"""
AiNest - Desktop Application
A modern desktop app using Eel (web technologies in a desktop window)
"""

import eel
import os
import sys
import json
import threading
import time
import requests
import speech_recognition as sr
import pyttsx3
import psutil
from datetime import datetime

# Initialize Eel
eel.init('desktop_app')

class AiNestDesktop:
    def __init__(self):
        self.settings = {
            "model": "llama3.2:latest",
            "ollama_url": "http://localhost:11434",
            "voice_enabled": True,
            "auto_speak": True,
            "volume": 0.8,
            "mic_sensitivity": 0.7,
        }
        self.conversation_history = []
        self.available_models = []
        
        # Initialize voice components
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.tts_engine = None
        self.listening = False
        
        # Try to initialize microphone
        try:
            self.microphone = sr.Microphone()
            self.recognizer.adjust_for_ambient_noise(self.microphone)
            print("🎤 Microphone initialized successfully")
        except Exception as e:
            print(f"⚠️ Microphone initialization failed: {e}")
        
        # Initialize TTS engine
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', self.settings["volume"])
            print("🔊 TTS engine initialized successfully")
        except Exception as e:
            print(f"⚠️ TTS initialization failed: {e}")
        
        # Detect available Ollama models
        self.detect_available_models()
    
    def detect_available_models(self):
        """Detect available Ollama models and set the first one as default"""
        try:
            response = requests.get(f"{self.settings['ollama_url']}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.available_models = [model['name'] for model in data.get('models', [])]
                
                if self.available_models:
                    # Prefer llama models, then any available model
                    preferred_models = [
                        'llama3.2:latest', 'llama3.1:latest', 'llama3:latest',
                        'llama2:latest', 'mistral:latest', 'codellama:latest'
                    ]
                    
                    # Find first preferred model that's available
                    selected_model = None
                    for preferred in preferred_models:
                        if preferred in self.available_models:
                            selected_model = preferred
                            break
                    
                    # If no preferred model found, use the first available
                    if not selected_model:
                        selected_model = self.available_models[0]
                    
                    self.settings['model'] = selected_model
                    print(f"🤖 Auto-detected model: {selected_model}")
                    print(f"📋 Available models: {', '.join(self.available_models)}")
                else:
                    print("⚠️ No Ollama models found. Please install a model first.")
            else:
                print(f"⚠️ Failed to get Ollama models: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Cannot connect to Ollama: {e}")
        except Exception as e:
            print(f"⚠️ Model detection failed: {e}")

# Create global instance
jarvis = AiNestDesktop()

@eel.expose
def send_message(message):
    """Send message to AI and get response"""
    try:
        if not message.strip():
            return {"error": "Empty message"}
        
        # Add to conversation history
        jarvis.conversation_history.append({"role": "user", "content": message})
        
        # Prepare request to Ollama
        payload = {
            "model": jarvis.settings["model"],
            "messages": jarvis.conversation_history,
            "stream": False
        }
        
        response = requests.post(
            f"{jarvis.settings['ollama_url']}/api/chat",
            json=payload,
            timeout=30
        )
        
        # Handle model not found error by auto-detecting available models
        if response.status_code == 404 and "not found" in response.text.lower():
            print(f"⚠️ Model '{jarvis.settings['model']}' not found, detecting available models...")
            jarvis.detect_available_models()
            
            if jarvis.available_models:
                # Retry with the new detected model
                payload["model"] = jarvis.settings["model"]
                response = requests.post(
                    f"{jarvis.settings['ollama_url']}/api/chat",
                    json=payload,
                    timeout=30
                )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result["message"]["content"]
            
            # Add AI response to conversation history
            jarvis.conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Speak response if enabled
            if jarvis.settings["auto_speak"] and jarvis.tts_engine:
                threading.Thread(target=speak_text, args=(ai_response,), daemon=True).start()
            
            return {
                "success": True,
                "response": ai_response,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
        elif response.status_code == 404:
            if not jarvis.available_models:
                return {"error": "No Ollama models available. Please install a model using: ollama pull llama3.2"}
            else:
                return {"error": f"Model error. Available models: {', '.join(jarvis.available_models)}"}
        else:
            return {"error": f"API Error: {response.status_code} - {response.text}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}. Make sure Ollama is running."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@eel.expose
def start_voice_input():
    """Start voice input"""
    if not jarvis.microphone:
        return {"error": "Microphone not available"}
    
    try:
        jarvis.listening = True
        
        with jarvis.microphone as source:
            audio = jarvis.recognizer.listen(source, timeout=10, phrase_time_limit=10)
        
        text = jarvis.recognizer.recognize_google(audio)
        jarvis.listening = False
        
        return {
            "success": True,
            "text": text,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
    except sr.WaitTimeoutError:
        jarvis.listening = False
        return {"error": "Voice input timed out"}
    except sr.UnknownValueError:
        jarvis.listening = False
        return {"error": "Could not understand audio"}
    except sr.RequestError as e:
        jarvis.listening = False
        return {"error": f"Speech recognition error: {e}"}
    except Exception as e:
        jarvis.listening = False
        return {"error": f"Unexpected error: {e}"}

@eel.expose
def speak_text(text):
    """Speak text using TTS"""
    if jarvis.tts_engine:
        try:
            jarvis.tts_engine.say(text)
            jarvis.tts_engine.runAndWait()
            return {"success": True}
        except Exception as e:
            return {"error": f"TTS Error: {e}"}
    return {"error": "TTS not available"}

@eel.expose
def get_settings():
    """Get current settings"""
    return jarvis.settings

@eel.expose
def save_settings(settings):
    """Save settings"""
    try:
        jarvis.settings.update(settings)
        
        # Update TTS volume if available
        if jarvis.tts_engine and "volume" in settings:
            jarvis.tts_engine.setProperty('volume', settings["volume"])
        
        return {"success": True}
    except Exception as e:
        return {"error": f"Failed to save settings: {e}"}

@eel.expose
def clear_conversation():
    """Clear conversation history"""
    jarvis.conversation_history = []
    return {"success": True}

@eel.expose
def get_available_models():
    """Get available Ollama models"""
    return {
        "success": True,
        "models": jarvis.available_models,
        "current_model": jarvis.settings["model"]
    }

@eel.expose
def get_system_status():
    """Get system status"""
    try:
        # Check Ollama status
        ollama_status = "Unknown"
        try:
            response = requests.get(f"{jarvis.settings['ollama_url']}/api/tags", timeout=3)
            ollama_status = "Running" if response.status_code == 200 else "Error"
        except:
            ollama_status = "Not Running"
        
        return {
            "ollama_status": ollama_status,
            "voice_available": jarvis.microphone is not None,
            "tts_available": jarvis.tts_engine is not None,
            "conversation_length": len(jarvis.conversation_history),
            "available_models": jarvis.available_models,
            "current_model": jarvis.settings["model"]
        }
    except Exception as e:
        return {"error": f"Failed to get status: {e}"}

def main():
    """Main function to start the desktop app"""
    print("🚀 Starting AiNest Desktop Application...")
    
    # Check if web files directory exists
    web_dir = os.path.join(os.path.dirname(__file__), 'desktop_app')
    if not os.path.exists(web_dir):
        os.makedirs(web_dir)
    
    # Check if Ollama is running
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
        else:
            print("⚠️ Ollama may not be running properly")
    except requests.exceptions.RequestException:
        print("❌ Ollama is not running. Please start Ollama first:")
        print("   brew install ollama")
        print("   ollama serve")
        print("   ollama pull llama3.2:latest")
    
    # Start the desktop app
    try:
        eel.start('index.html', 
                 size=(1000, 700), 
                 port=8080,
                 block=True)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"Application error: {e}")

if __name__ == "__main__":
    main()