#!/usr/bin/env python3
"""
Wolf - Desktop Application
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
import pyautogui
from datetime import datetime
from Wolf_pc_control import WolfPCControl

# Initialize Eel
eel.init('desktop_app')

class WolfDesktop:
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
        
        # Initialize PC Control
        self.pc_control = WolfPCControl()
        
        # Flag to stop AI processes
        self.kill_flag = False
        
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
                    preferred_models = [
                        'llama3.2:latest', 'llama3.1:latest', 'llama3:latest',
                        'llama2:latest', 'mistral:latest', 'codellama:latest'
                    ]
                    selected_model = None
                    for preferred in preferred_models:
                        if preferred in self.available_models:
                            selected_model = preferred
                            break
                    if not selected_model:
                        selected_model = self.available_models[0]
                    self.settings['model'] = selected_model
                    print(f"🤖 Auto-detected model: {selected_model}")
                else:
                    print("⚠️ No Ollama models found.")
            else:
                print(f"⚠️ Failed to get Ollama models: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Cannot connect to Ollama: {e}")

    def check_pc_control_command(self, message):
        """Check if message is a PC control command and execute it"""
        try:
            # 1st attempt: Fast keyword matching
            result = self.pc_control.execute_command(message)
            if result.get("success") or "Protocol unrecognized" not in str(result.get("error", "")):
                return format_pc_control_response(result, message)
            
            # 2nd attempt: LLM Intent Identification for fuzzy commands
            if self.is_likely_command(message):
                intent_cmd = self.identify_intent_via_ai(message)
                if intent_cmd:
                    result = self.pc_control.execute_command(intent_cmd)
                    if result.get("success"):
                        return format_pc_control_response(result, intent_cmd)
            return None
        except Exception as e:
            print(f"Intent Error: {e}")
            return None

    def is_likely_command(self, message):
        words = message.lower().split()
        if len(words) > 12: return False
        verbs = ['open', 'close', 'show', 'list', 'take', 'maximize', 'minimize', 'create', 'search', 'volume', 'mute', 'play', 'pause', 'next', 'previous']
        return any(message.lower().startswith(v) for v in verbs) or len(words) < 5

    def identify_intent_via_ai(self, user_input):
        try:
            prompt = f"Map this to a system command (e.g. 'open calculator', 'volume up', 'take screenshot'). Request: '{user_input}'. Return ONLY the command or 'None':"
            payload = {"model": self.settings["model"], "messages": [{"role": "system", "content": prompt}], "stream": False, "options": {"temperature": 0.1}}
            response = requests.post(f"{self.settings['ollama_url']}/api/chat", json=payload, timeout=5)
            if response.status_code == 200:
                cmd = response.json()["message"]["content"].strip().lower()
                return cmd if cmd != "none" else None
        except: return None
        return None

# Global instance
wolf = WolfDesktop()

@eel.expose
def send_message(message):
    """Send message to AI and get response"""
    try:
        if not message.strip(): return {"error": "Empty message"}
        
        # Check command first
        pc_control_result = wolf.check_pc_control_command(message)
        if pc_control_result: return pc_control_result
        
        # AI Chat
        wolf.kill_flag = False
        wolf.conversation_history.append({"role": "user", "content": message})
        payload = {"model": wolf.settings["model"], "messages": wolf.conversation_history, "stream": False}
        
        # Note: Since this is synchronous, the kill btn will likely trigger a separate thread 
        # but the request itself can't be aborted easily without a session.
        # However, we can check the flag immediately after the request returns.
        response = requests.post(f"{wolf.settings['ollama_url']}/api/chat", json=payload, timeout=30)
        
        if wolf.kill_flag:
            return {"success": False, "error": "Neural link severed by user."}
        if response.status_code == 200:
            ai_response = response.json()["message"]["content"]
            wolf.conversation_history.append({"role": "assistant", "content": ai_response})
            if wolf.settings["auto_speak"] and wolf.tts_engine:
                threading.Thread(target=speak_text, args=(ai_response,), daemon=True).start()
            return {"success": True, "response": ai_response, "timestamp": datetime.now().strftime("%H:%M:%S")}
        return {"error": "AI service unavailable"}
    except Exception as e:
        return {"error": str(e)}

@eel.expose
def start_voice_input():
    if not wolf.microphone: return {"error": "Mic missing"}
    try:
        wolf.listening = True
        with wolf.microphone as source:
            audio = wolf.recognizer.listen(source, timeout=8, phrase_time_limit=10)
        text = wolf.recognizer.recognize_google(audio)
        return {"success": True, "text": text}
    except Exception as e: return {"error": str(e)}
    finally: wolf.listening = False

@eel.expose
def speak_text(text):
    if wolf.tts_engine:
        try:
            wolf.tts_engine.say(text)
            wolf.tts_engine.runAndWait()
            return {"success": True}
        except: pass
    return {"error": "TTS failed"}

@eel.expose
def kill_ai_process():
    """Kill/Abort current AI generation"""
    wolf.kill_flag = True
    # If TTS is running, stop it
    if wolf.tts_engine:
        try:
            wolf.tts_engine.stop()
        except: pass
    return {"success": True}

@eel.expose
def get_settings(): return wolf.settings

@eel.expose
def save_settings(settings):
    wolf.settings.update(settings)
    if wolf.tts_engine and "volume" in settings:
        wolf.tts_engine.setProperty('volume', settings["volume"])
    return {"success": True}

@eel.expose
def clear_conversation():
    wolf.conversation_history = []
    return {"success": True}

@eel.expose
def get_available_models():
    return {"success": True, "models": wolf.available_models, "current_model": wolf.settings["model"]}

@eel.expose
def get_system_status():
    ollama_status = "Not Running"
    try:
        if requests.get(f"{wolf.settings['ollama_url']}/api/tags", timeout=2).status_code == 200:
            ollama_status = "Running"
    except: pass
    return {
        "ollama_status": ollama_status,
        "voice_available": wolf.microphone is not None,
        "tts_available": wolf.tts_engine is not None,
        "conversation_length": len(wolf.conversation_history),
        "current_model": wolf.settings["model"]
    }

def format_pc_control_response(result, command=""):
    if result.get("success"):
        response_text = result.get("message", "Command executed successfully.")
        
        if "system" in result:
            sys = result["system"]
            response_text += f"\n\nSystem: {sys['os']} {sys['version']}\nCPU: {sys['cpu_usage']}"
            if "memory" in result:
                response_text += f"\nRAM: {result['memory']['percentage']}"
        
        elif "files" in result:
            response_text += f"\nContent: {len(result.get('files', []))} files, {len(result.get('folders', []))} folders."

        if "screenshot" in command.lower() and "path" in result:
            try:
                import shutil
                original_path = result["path"]
                filename = os.path.basename(original_path)
                target_dir = os.path.join('desktop_app', 'assets', 'screenshots')
                os.makedirs(target_dir, exist_ok=True)
                shutil.copy2(original_path, os.path.join(target_dir, filename))
                return {"success": True, "response": response_text, "pc_control": True, "image_url": f"assets/screenshots/{filename}"}
            except: pass

        return {"success": True, "response": response_text, "pc_control": True}
    return {"success": False, "error": result.get("error", "Command failed"), "pc_control": True}

@eel.expose
def execute_pc_command(command):
    result = wolf.pc_control.execute_command(command)
    fmt = format_pc_control_response(result, command)
    if wolf.settings["auto_speak"] and wolf.tts_engine and fmt.get("success"):
        threading.Thread(target=speak_text, args=(result.get("message", "Executed"),), daemon=True).start()
    return fmt

@eel.expose
def get_available_pc_commands():
    return {"success": True, "commands": wolf.pc_control.get_available_commands()}

def main():
    print("🚀 Starting Wolf AI Assistant...")
    os.makedirs(os.path.join('desktop_app', 'assets', 'screenshots'), exist_ok=True)
    try:
        eel.start('index.html', size=(1000, 750), port=8080)
    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    main()