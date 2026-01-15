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
wolf = WolfDesktop()

@eel.expose
def send_message(message):
    """Send message to AI and get response"""
    try:
        if not message.strip():
            return {"error": "Empty message"}
        
        # Check if this is a PC control command
        pc_control_result = check_pc_control_command(message)
        if pc_control_result:
            return pc_control_result
        
        # Add to conversation history
        wolf.conversation_history.append({"role": "user", "content": message})
        
        # Prepare request to Ollama
        payload = {
            "model": wolf.settings["model"],
            "messages": wolf.conversation_history,
            "stream": False
        }
        
        response = requests.post(
            f"{wolf.settings['ollama_url']}/api/chat",
            json=payload,
            timeout=30
        )
        
        # Handle model not found error by auto-detecting available models
        if response.status_code == 404 and "not found" in response.text.lower():
            print(f"⚠️ Model '{wolf.settings['model']}' not found, detecting available models...")
            wolf.detect_available_models()
            
            if wolf.available_models:
                # Retry with the new detected model
                payload["model"] = wolf.settings["model"]
                response = requests.post(
                    f"{wolf.settings['ollama_url']}/api/chat",
                    json=payload,
                    timeout=30
                )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result["message"]["content"]
            
            # Add AI response to conversation history
            wolf.conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Speak response if enabled
            if wolf.settings["auto_speak"] and wolf.tts_engine:
                threading.Thread(target=speak_text, args=(ai_response,), daemon=True).start()
            
            return {
                "success": True,
                "response": ai_response,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
        elif response.status_code == 404:
            if not wolf.available_models:
                return {"error": "No Ollama models available. Please install a model using: ollama pull llama3.2"}
            else:
                return {"error": f"Model error. Available models: {', '.join(wolf.available_models)}"}
        else:
            return {"error": f"API Error: {response.status_code} - {response.text}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}. Make sure Ollama is running."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@eel.expose
def start_voice_input():
    """Start voice input"""
    if not wolf.microphone:
        return {"error": "Microphone not available"}
    
    try:
        wolf.listening = True
        
        with wolf.microphone as source:
            audio = wolf.recognizer.listen(source, timeout=10, phrase_time_limit=10)
        
        text = wolf.recognizer.recognize_google(audio)
        wolf.listening = False
        
        return {
            "success": True,
            "text": text,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
    except sr.WaitTimeoutError:
        wolf.listening = False
        return {"error": "Voice input timed out"}
    except sr.UnknownValueError:
        wolf.listening = False
        return {"error": "Could not understand audio"}
    except sr.RequestError as e:
        wolf.listening = False
        return {"error": f"Speech recognition error: {e}"}
    except Exception as e:
        wolf.listening = False
        return {"error": f"Unexpected error: {e}"}

@eel.expose
def speak_text(text):
    """Speak text using TTS"""
    if wolf.tts_engine:
        try:
            wolf.tts_engine.say(text)
            wolf.tts_engine.runAndWait()
            return {"success": True}
        except Exception as e:
            return {"error": f"TTS Error: {e}"}
    return {"error": "TTS not available"}

@eel.expose
def get_settings():
    """Get current settings"""
    return wolf.settings

@eel.expose
def save_settings(settings):
    """Save settings"""
    try:
        wolf.settings.update(settings)
        
        # Update TTS volume if available
        if wolf.tts_engine and "volume" in settings:
            wolf.tts_engine.setProperty('volume', settings["volume"])
        
        return {"success": True}
    except Exception as e:
        return {"error": f"Failed to save settings: {e}"}

@eel.expose
def clear_conversation():
    """Clear conversation history"""
    wolf.conversation_history = []
    return {"success": True}

@eel.expose
def get_available_models():
    """Get available Ollama models"""
    return {
        "success": True,
        "models": wolf.available_models,
        "current_model": wolf.settings["model"]
    }

@eel.expose
def get_system_status():
    """Get system status"""
    try:
        # Check Ollama status
        ollama_status = "Unknown"
        try:
            response = requests.get(f"{wolf.settings['ollama_url']}/api/tags", timeout=3)
            ollama_status = "Running" if response.status_code == 200 else "Error"
        except:
            ollama_status = "Not Running"
        
        return {
            "ollama_status": ollama_status,
            "voice_available": wolf.microphone is not None,
            "tts_available": wolf.tts_engine is not None,
            "conversation_length": len(wolf.conversation_history),
            "available_models": wolf.available_models,
            "current_model": wolf.settings["model"]
        }
    except Exception as e:
        return {"error": f"Failed to get status: {e}"}

def check_pc_control_command(message):
    """Check if message is a PC control command and execute it"""
    try:
        # Define PC control keywords
        pc_control_keywords = [
            'system info', 'computer info', 'hardware info',
            'create folder', 'make directory', 'new folder',
            'list files', 'show files', 'directory contents',
            'delete file', 'remove file',
            'open application', 'launch app', 'start program', 'open',
            'close application', 'quit app', 'kill process', 'close',
            'take screenshot', 'capture screen', 'screenshot',
            'minimize window', 'maximize window',
            'copy text', 'paste text', 'clipboard',
            'volume up', 'volume down', 'mute',
            'play music', 'pause music', 'play/pause', 'media play',
            'next track', 'next song', 'skip song',
            'previous track', 'previous song', 'last song',
            'running processes', 'memory usage', 'cpu usage',
            'open website', 'browse to', 'visit site',
            'search google', 'google search'
        ]
        
        message_lower = message.lower()
        
        # Check if any PC control keywords are in the message
        is_pc_command = any(keyword in message_lower for keyword in pc_control_keywords)
        
        if is_pc_command:
            # Execute PC control command
            result = wolf.pc_control.execute_command(message)
            return format_pc_control_response(result, message)
        
        return None  # Not a PC control command
        
    except Exception as e:
        return {
            "success": False,
            "error": f"PC control error: {str(e)}",
            "pc_control": True
        }

def format_pc_control_response(result, command=""):
    """Format PC control result into a chat response"""
    if result.get("success"):
        # Format success response for chat
        response_text = result.get("message", "Command executed successfully")
        
        # Add detailed information if available
        if "system" in result:
            sys_info = result["system"]
            response_text += f"\n\nSystem Information:\n"
            response_text += f"• OS: {sys_info.get('os')} {sys_info.get('version')}\n"
            response_text += f"• CPU: {sys_info.get('processor')}\n"
            response_text += f"• Cores: {sys_info.get('cpu_cores')} physical, {sys_info.get('logical_cores')} logical\n"
            response_text += f"• CPU Usage: {sys_info.get('cpu_usage')}\n"
            
            if "memory" in result:
                mem_info = result["memory"]
                response_text += f"• Memory: {mem_info.get('used')} / {mem_info.get('total')} ({mem_info.get('percentage')})\n"
            
            if "disk" in result:
                disk_info = result["disk"]
                response_text += f"• Disk: {disk_info.get('used')} / {disk_info.get('total')} ({disk_info.get('percentage')})"
        
        elif "files" in result:
            response_text += f"\n\nDirectory: {result.get('path')}\n"
            response_text += f"Folders: {len(result.get('folders', []))}, Files: {len(result.get('files', []))}\n\n"
            
            folders = result.get("folders", [])[:5]  # Show first 5 folders
            files = result.get("files", [])[:5]      # Show first 5 files
            
            if folders:
                response_text += "📁 Folders:\n"
                for folder in folders:
                    response_text += f"  • {folder['name']}\n"
            
            if files:
                response_text += "📄 Files:\n"
                for file in files:
                    size_kb = file['size'] // 1024 if file['size'] > 1024 else file['size']
                    unit = "KB" if file['size'] > 1024 else "B"
                    response_text += f"  • {file['name']} ({size_kb} {unit})\n"
        
        elif "processes" in result:
            processes = result["processes"][:5]  # Show top 5 processes
            response_text += "\n\nTop Processes by CPU Usage:\n"
            for proc in processes:
                response_text += f"• {proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu_percent']:.1f}%\n"
        
        elif "memory" in result:
            mem_info = result["memory"]
            response_text += f"\n\nMemory Usage:\n"
            response_text += f"• Total: {mem_info.get('total')}\n"
            response_text += f"• Used: {mem_info.get('used')} ({mem_info.get('percentage')})\n"
            response_text += f"• Available: {mem_info.get('available')}"
        
        elif "cpu" in result:
            cpu_info = result["cpu"]
            response_text += f"\n\nCPU Usage:\n"
            response_text += f"• Average: {cpu_info.get('average')}\n"
            response_text += f"• Cores: {cpu_info.get('cores')}"
        
        # Handle screenshot specifically
        if "screenshot" in command.lower() and "path" in result:
            try:
                # Copy screenshot to web assets
                import shutil
                original_path = result["path"]
                filename = os.path.basename(original_path)
                web_assets_dir = os.path.join(os.path.dirname(__file__), 'desktop_app', 'assets', 'screenshots')
                
                if not os.path.exists(web_assets_dir):
                    os.makedirs(web_assets_dir)
                    
                target_path = os.path.join(web_assets_dir, filename)
                shutil.copy2(original_path, target_path)
                
                # Add image URL to response
                return {
                    "success": True,
                    "response": response_text,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "pc_control": True,
                    "image_url": f"assets/screenshots/{filename}"
                }
            except Exception as e:
                print(f"Failed to copy screenshot: {e}")
        
        return {
            "success": True,
            "response": response_text,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "pc_control": True
        }
    else:
        return {
            "success": False,
            "error": result.get("error", "PC control command failed"),
            "pc_control": True
        }

@eel.expose
def execute_pc_command(command):
    """Execute a specific PC control command"""
    try:
        result = wolf.pc_control.execute_command(command)
        formatted_result = format_pc_control_response(result, command)
        
        # Speak response if enabled
        if wolf.settings["auto_speak"] and wolf.tts_engine and formatted_result.get("success"):
            # Speak only the main message, not the detailed stats to avoid being too verbose
            text_to_speak = result.get("message", "Command executed")
            threading.Thread(target=speak_text, args=(text_to_speak,), daemon=True).start()
            
        return formatted_result
    except Exception as e:
        return {"success": False, "error": f"Failed to execute PC command: {str(e)}"}

@eel.expose
def get_available_pc_commands():
    """Get list of available PC control commands"""
    try:
        commands = wolf.pc_control.get_available_commands()
        return {"success": True, "commands": commands}
    except Exception as e:
        return {"success": False, "error": f"Failed to get PC commands: {str(e)}"}

def main():
    """Main function to start the desktop app"""
    print("🚀 Starting Wolf AI Desktop Assistant...")
    
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