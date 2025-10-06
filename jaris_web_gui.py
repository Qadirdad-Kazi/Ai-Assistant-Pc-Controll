#!/usr/bin/env python3
"""
JARIS - Web GUI Version
A Flask-based web interface for JARIS AI assistant.
"""

import os
import sys
import json
import subprocess
import re
import requests
import webbrowser
import platform
import threading
import time
from typing import Tuple
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import speech_recognition as sr
import pyttsx3
import psutil

app = Flask(__name__)
app.secret_key = 'jaris_secret_key_2024'
CORS(app)

class JarvisWeb:
    def __init__(self):
        self.settings = {
            "model": "llama3.2:latest",
            "ollama_url": "http://localhost:11434",
            "voice_enabled": True,
            "auto_speak": True,
            "volume": 0.8,
            "mic_sensitivity": 0.7,
            "continuous_listening": False
        }
        self.conversation_history = []
        
        # Initialize voice components
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = None
        self.listening_thread = None
        self.stop_listening = False
        
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', self.settings['volume'])
        except Exception as e:
            print(f"TTS initialization failed: {e}")
        
        # Adjust microphone sensitivity
        self.recognizer.energy_threshold = int(300 * (1 - self.settings['mic_sensitivity']))
        self.recognizer.dynamic_energy_threshold = True
    
    def speak(self, text: str):
        """Convert text to speech"""
        if not self.settings['voice_enabled'] or not self.tts_engine:
            return
            
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {e}")
    
    def listen(self) -> str:
        """Listen for voice input"""
        if not self.settings['voice_enabled']:
            return "Voice input is disabled"
            
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            text = self.recognizer.recognize_google(audio)
            return text.lower()
        except sr.WaitTimeoutError:
            return "No speech detected"
        except sr.UnknownValueError:
            return "Could not understand speech"
        except sr.RequestError as e:
            return f"Speech recognition error: {e}"
        except Exception as e:
            return f"Error: {e}"
    
    def start_continuous_listening(self):
        """Start continuous listening mode"""
        if self.settings['continuous_listening']:
            return "Already listening continuously"
        
        self.settings['continuous_listening'] = True
        self.stop_listening = False
        self.listening_thread = threading.Thread(target=self._continuous_listen_loop)
        self.listening_thread.daemon = True
        self.listening_thread.start()
        return "Continuous listening started"
    
    def stop_continuous_listening(self):
        """Stop continuous listening mode"""
        if not self.settings['continuous_listening']:
            return "Not currently listening continuously"
        
        self.settings['continuous_listening'] = False
        self.stop_listening = True
        if self.listening_thread:
            self.listening_thread.join(timeout=2)
        return "Continuous listening stopped"
    
    def _continuous_listen_loop(self):
        """Continuous listening loop"""
        while not self.stop_listening and self.settings['continuous_listening']:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                text = self.recognizer.recognize_google(audio)
                if text and text.lower() not in ["", "no speech detected"]:
                    # Process the command
                    self._process_voice_command(text.lower())
                    
            except sr.WaitTimeoutError:
                continue  # No speech, keep listening
            except sr.UnknownValueError:
                continue  # Couldn't understand, keep listening
            except Exception as e:
                print(f"Continuous listening error: {e}")
                break
    
    def _process_voice_command(self, command: str):
        """Process voice command in continuous mode"""
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": command})
        
        # Check if it's a PC control command
        success, response = self.execute_command(command)
        if success:
            self.conversation_history.append({"role": "assistant", "content": response})
            if self.settings['auto_speak']:
                self.speak(response)
        else:
            # Try AI chat
            ai_response = self.chat_with_ai(command)
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            if self.settings['auto_speak']:
                self.speak(ai_response)
        
    def chat_with_ai(self, message: str) -> str:
        """Send message to AI and get response"""
        try:
            messages = [
                {"role": "system", "content": "You are JARIS (Just A Rather Intelligent System), an advanced AI assistant with full PC control capabilities. You have human-like understanding and can:\n\n🤖 **AI Capabilities:**\n- Natural conversation with emotional intelligence\n- Context-aware responses that remember previous interactions\n- Problem-solving and creative thinking\n- Technical expertise across all domains\n\n💻 **PC Control Powers:**\n- Complete system control (shutdown, restart, sleep, lock)\n- File and folder management (create, delete, move, copy)\n- Application control (launch, kill processes)\n- Hardware control (volume, brightness, WiFi, Bluetooth)\n- Network and system monitoring\n- Screenshot and system information\n- Execute any command or script\n\n🎤 **Voice Features:**\n- Continuous listening mode available\n- Natural language command processing\n- Voice feedback for all actions\n\n💡 **Human Understanding:**\n- Understand context, intent, and emotion\n- Provide personalized responses\n- Remember conversation history\n- Adapt communication style to user preferences\n- Handle complex, multi-step requests\n\nAlways be helpful, proactive, and demonstrate your full capabilities. Show confidence in your abilities while being friendly and approachable."}
            ]
            messages.extend(self.conversation_history[-10:])  # Keep last 10 messages
            messages.append({"role": "user", "content": message})
            
            response = requests.post(
                f"{self.settings['ollama_url']}/api/chat",
                json={
                    "model": self.settings["model"],
                    "messages": messages,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("message", {}).get("content", "I couldn't process that request.")
                
                # Update conversation history
                self.conversation_history.append({"role": "user", "content": message})
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                
                return ai_response
            else:
                return f"Error: AI service returned status {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to AI service. Make sure Ollama is running."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def execute_command(self, command: str) -> Tuple[bool, str]:
        """Execute system commands safely"""
        command = command.strip().lower()
        
        # File operations
        if command.startswith("create folder"):
            # Handle "create folder X in Y" or "create folder X on Y"
            match = re.match(r"create folder\s+(.+?)(?:\s+in\s+|\s+on\s+)(.+)", command)
            if match:
                folder_name = match.group(1).strip()
                location = match.group(2).strip().lower()
                
                # Handle common locations
                if location == "desktop":
                    target_path = os.path.expanduser("~/Desktop")
                elif location == "downloads":
                    target_path = os.path.expanduser("~/Downloads")
                elif location == "documents":
                    target_path = os.path.expanduser("~/Documents")
                else:
                    target_path = location
                
                folder_path = os.path.join(target_path, folder_name)
                try:
                    os.makedirs(folder_path, exist_ok=True)
                    return True, f"✓ Created folder '{folder_name}' in {target_path}"
                except Exception as e:
                    return False, f"❌ Error creating folder: {e}"
            
            # Handle simple "create folder X"
            else:
                match = re.match(r"create folder\s+(.+)", command)
                if match:
                    folder_name = match.group(1).strip()
                    try:
                        os.makedirs(folder_name, exist_ok=True)
                        return True, f"✓ Created folder: {folder_name}"
                    except Exception as e:
                        return False, f"❌ Error creating folder: {e}"
        
        elif command.startswith("create file") or command.startswith("write"):
            # Handle "create file X in Y" or "create file X on Y"
            match = re.match(r"(?:create file|write)\s+(.+?)(?:\s+in\s+|\s+on\s+)(.+?)(?:\s+with\s+)?(.*)?", command)
            if match:
                file_name = match.group(1).strip()
                location = match.group(2).strip().lower()
                content = match.group(3).strip() if match.group(3) else ""
                
                # Handle common locations
                if location == "desktop":
                    target_path = os.path.expanduser("~/Desktop")
                elif location == "downloads":
                    target_path = os.path.expanduser("~/Downloads")
                elif location == "documents":
                    target_path = os.path.expanduser("~/Documents")
                else:
                    target_path = location
                
                file_path = os.path.join(target_path, file_name)
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return True, f"✓ Created file '{file_name}' in {target_path}"
                except Exception as e:
                    return False, f"❌ Error creating file: {e}"
            
            # Handle simple "create file X"
            else:
                match = re.match(r"(?:create file|write)\s+([^\s]+)(?:\s+with\s+)?(.*)?", command)
                if match:
                    file_name = match.group(1).strip()
                    content = match.group(2).strip() if match.group(2) else ""
                    try:
                        with open(file_name, 'w', encoding='utf-8') as f:
                            f.write(content)
                        return True, f"✓ Created file: {file_name}"
                    except Exception as e:
                        return False, f"❌ Error creating file: {e}"
        
        elif command.startswith("list files"):
            match = re.match(r"list files(?:\s+in\s+)?(.*)?", command)
            directory = match.group(1).strip() if match.group(1) else "."
            
            # Handle common shortcuts
            if directory.lower() == "downloads":
                directory = os.path.expanduser("~/Downloads")
            elif directory.lower() == "documents":
                directory = os.path.expanduser("~/Documents")
            elif directory.lower() == "desktop":
                directory = os.path.expanduser("~/Desktop")
            
            try:
                if not os.path.exists(directory):
                    return False, f"❌ Directory not found: {directory}"
                
                files = os.listdir(directory)
                if not files:
                    return True, f"📂 {directory} is empty"
                
                file_list = []
                for f in sorted(files):
                    path = os.path.join(directory, f)
                    if os.path.isdir(path):
                        file_list.append(f"📁 {f}/")
                    else:
                        # Get file size
                        try:
                            size = os.path.getsize(path)
                            if size < 1024:
                                size_str = f"{size}B"
                            elif size < 1024*1024:
                                size_str = f"{size//1024}KB"
                            else:
                                size_str = f"{size//(1024*1024)}MB"
                            file_list.append(f"📄 {f} ({size_str})")
                        except:
                            file_list.append(f"📄 {f}")
                
                return True, f"📂 Contents of {directory}:\n" + "\n".join(file_list)
            except Exception as e:
                return False, f"❌ Error listing files: {e}"
        
        elif command.startswith("navigate"):
            match = re.match(r"navigate\s+(.+)", command)
            if match:
                new_path = match.group(1).strip()
                try:
                    os.chdir(new_path)
                    return True, f"✓ Changed directory to: {os.getcwd()}"
                except Exception as e:
                    return False, f"❌ Error changing directory: {e}"
        
        elif command.startswith("open"):
            match = re.match(r"open\s+(.+)", command)
            if match:
                target = match.group(1).strip().lower()
                try:
                    # Handle common system locations
                    if target == "downloads":
                        downloads_path = os.path.expanduser("~/Downloads")
                        if platform.system() == "Windows":
                            os.startfile(downloads_path)
                        else:
                            subprocess.run(["open", downloads_path] if platform.system() == "Darwin" else ["xdg-open", downloads_path])
                        return True, f"✓ Opened Downloads folder: {downloads_path}"
                    
                    elif target == "documents":
                        documents_path = os.path.expanduser("~/Documents")
                        if platform.system() == "Windows":
                            os.startfile(documents_path)
                        else:
                            subprocess.run(["open", documents_path] if platform.system() == "Darwin" else ["xdg-open", documents_path])
                        return True, f"✓ Opened Documents folder: {documents_path}"
                    
                    elif target == "desktop":
                        desktop_path = os.path.expanduser("~/Desktop")
                        if platform.system() == "Windows":
                            os.startfile(desktop_path)
                        else:
                            subprocess.run(["open", desktop_path] if platform.system() == "Darwin" else ["xdg-open", desktop_path])
                        return True, f"✓ Opened Desktop folder: {desktop_path}"
                    
                    elif target.startswith("http"):
                        webbrowser.open(target)
                        return True, f"✓ Opened URL: {target}"
                    
                    else:
                        # Try to open as file/folder path
                        if os.path.exists(target):
                            if platform.system() == "Windows":
                                os.startfile(target)
                            else:
                                subprocess.run(["open", target] if platform.system() == "Darwin" else ["xdg-open", target])
                            return True, f"✓ Opened: {target}"
                        else:
                            return False, f"❌ Path not found: {target}"
                            
                except Exception as e:
                    return False, f"❌ Error opening: {e}"
        
        elif command.startswith("open file"):
            match = re.match(r"open file\s+(.+)", command)
            if match:
                file_path = match.group(1).strip()
                try:
                    if not os.path.exists(file_path):
                        return False, f"❌ File not found: {file_path}"
                    
                    if platform.system() == "Windows":
                        os.startfile(file_path)
                    else:
                        subprocess.run(["open", file_path] if platform.system() == "Darwin" else ["xdg-open", file_path])
                    return True, f"✓ Opened file: {file_path}"
                except Exception as e:
                    return False, f"❌ Error opening file: {e}"
        
        elif command.startswith("shutdown"):
            try:
                if platform.system() == "Windows":
                    subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
                else:
                    subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
                return True, "✓ System shutdown initiated"
            except Exception as e:
                return False, f"❌ Error shutting down: {e}"
        
        elif command.startswith("restart") or command.startswith("reboot"):
            try:
                if platform.system() == "Windows":
                    subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
                else:
                    subprocess.run(["sudo", "reboot"], check=True)
                return True, "✓ System restart initiated"
            except Exception as e:
                return False, f"❌ Error restarting: {e}"
        
        elif command.startswith("sleep"):
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["pmset", "sleepnow"], check=True)
                elif platform.system() == "Windows":
                    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True)
                else:  # Linux
                    subprocess.run(["systemctl", "suspend"], check=True)
                return True, "✓ System sleep initiated"
            except Exception as e:
                return False, f"❌ Error putting system to sleep: {e}"
        
        elif command.startswith("lock"):
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["pmset", "displaysleepnow"], check=True)
                elif platform.system() == "Windows":
                    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
                else:  # Linux
                    subprocess.run(["gnome-screensaver-command", "-l"], check=True)
                return True, "✓ Screen locked"
            except Exception as e:
                return False, f"❌ Error locking screen: {e}"
        
        elif command.startswith("volume up"):
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) + 10)"], check=True)
                elif platform.system() == "Windows":
                    subprocess.run(["powershell", "-c", "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"], check=True)
                else:  # Linux
                    subprocess.run(["amixer", "set", "Master", "10%+"], check=True)
                return True, "✓ Volume increased"
            except Exception as e:
                return False, f"❌ Error adjusting volume: {e}"
        
        elif command.startswith("volume down"):
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["osascript", "-e", "set volume output volume (output volume of (get volume settings) - 10)"], check=True)
                elif platform.system() == "Windows":
                    subprocess.run(["powershell", "-c", "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"], check=True)
                else:  # Linux
                    subprocess.run(["amixer", "set", "Master", "10%-"], check=True)
                return True, "✓ Volume decreased"
            except Exception as e:
                return False, f"❌ Error adjusting volume: {e}"
        
        elif command.startswith("mute"):
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["osascript", "-e", "set volume output volume 0"], check=True)
                elif platform.system() == "Windows":
                    subprocess.run(["powershell", "-c", "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"], check=True)
                else:  # Linux
                    subprocess.run(["amixer", "set", "Master", "mute"], check=True)
                return True, "✓ Volume muted"
            except Exception as e:
                return False, f"❌ Error muting volume: {e}"
        
        elif command.startswith("brightness up"):
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["osascript", "-e", "tell application \"System Events\" to key code 144"], check=True)
                elif platform.system() == "Windows":
                    subprocess.run(["powershell", "-c", "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,80)"], check=True)
                else:  # Linux
                    subprocess.run(["xbacklight", "-inc", "10"], check=True)
                return True, "✓ Brightness increased"
            except Exception as e:
                return False, f"❌ Error adjusting brightness: {e}"
        
        elif command.startswith("brightness down"):
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["osascript", "-e", "tell application \"System Events\" to key code 145"], check=True)
                elif platform.system() == "Windows":
                    subprocess.run(["powershell", "-c", "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,20)"], check=True)
                else:  # Linux
                    subprocess.run(["xbacklight", "-dec", "10"], check=True)
                return True, "✓ Brightness decreased"
            except Exception as e:
                return False, f"❌ Error adjusting brightness: {e}"
        
        elif command.startswith("screenshot"):
            try:
                if platform.system() == "Darwin":  # macOS
                    screenshot_path = os.path.expanduser("~/Desktop/Screenshot_%Y%m%d_%H%M%S.png")
                    subprocess.run(["screencapture", "-x", screenshot_path], check=True)
                elif platform.system() == "Windows":
                    screenshot_path = os.path.expanduser("~/Desktop/Screenshot.png")
                    subprocess.run(["powershell", "-c", "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen.Bounds"], check=True)
                else:  # Linux
                    screenshot_path = os.path.expanduser("~/Desktop/Screenshot_$(date +%Y%m%d_%H%M%S).png")
                    subprocess.run(["gnome-screenshot", "-f", screenshot_path], check=True)
                return True, f"✓ Screenshot saved to Desktop"
            except Exception as e:
                return False, f"❌ Error taking screenshot: {e}"
        
        elif command.startswith("kill process"):
            match = re.match(r"kill process\s+(.+)", command)
            if match:
                process_name = match.group(1).strip()
                try:
                    if platform.system() == "Windows":
                        subprocess.run(["taskkill", "/f", "/im", process_name], check=True)
                    else:
                        subprocess.run(["pkill", "-f", process_name], check=True)
                    return True, f"✓ Process {process_name} terminated"
                except Exception as e:
                    return False, f"❌ Error killing process: {e}"
        
        elif command.startswith("start app") or command.startswith("launch"):
            match = re.match(r"(?:start app|launch)\s+(.+)", command)
            if match:
                app_name = match.group(1).strip().lower()
                try:
                    if platform.system() == "Darwin":  # macOS
                        if app_name in ["safari", "chrome", "firefox", "terminal", "finder", "calculator", "notes", "calendar"]:
                            subprocess.run(["open", "-a", app_name.title()], check=True)
                        else:
                            subprocess.run(["open", "-a", app_name], check=True)
                    elif platform.system() == "Windows":
                        if app_name in ["notepad", "calculator", "paint", "explorer", "cmd"]:
                            subprocess.run([app_name], check=True)
                        else:
                            subprocess.run(["start", app_name], check=True)
                    else:  # Linux
                        subprocess.run([app_name], check=True)
                    return True, f"✓ Launched {app_name}"
                except Exception as e:
                    return False, f"❌ Error launching app: {e}"
        
        elif command.startswith("wifi on"):
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["networksetup", "-setairportpower", "en0", "on"], check=True)
                elif platform.system() == "Windows":
                    subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "enable"], check=True)
                else:  # Linux
                    subprocess.run(["nmcli", "radio", "wifi", "on"], check=True)
                return True, "✓ WiFi enabled"
            except Exception as e:
                return False, f"❌ Error enabling WiFi: {e}"
        
        elif command.startswith("wifi off"):
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["networksetup", "-setairportpower", "en0", "off"], check=True)
                elif platform.system() == "Windows":
                    subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "disable"], check=True)
                else:  # Linux
                    subprocess.run(["nmcli", "radio", "wifi", "off"], check=True)
                return True, "✓ WiFi disabled"
            except Exception as e:
                return False, f"❌ Error disabling WiFi: {e}"
        
        elif command.startswith("bluetooth on"):
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["blueutil", "-p", "1"], check=True)
                elif platform.system() == "Windows":
                    subprocess.run(["powershell", "-c", "Get-PnpDevice -Class Bluetooth | Enable-PnpDevice"], check=True)
                else:  # Linux
                    subprocess.run(["rfkill", "unblock", "bluetooth"], check=True)
                return True, "✓ Bluetooth enabled"
            except Exception as e:
                return False, f"❌ Error enabling Bluetooth: {e}"
        
        elif command.startswith("bluetooth off"):
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["blueutil", "-p", "0"], check=True)
                elif platform.system() == "Windows":
                    subprocess.run(["powershell", "-c", "Get-PnpDevice -Class Bluetooth | Disable-PnpDevice"], check=True)
                else:  # Linux
                    subprocess.run(["rfkill", "block", "bluetooth"], check=True)
                return True, "✓ Bluetooth disabled"
            except Exception as e:
                return False, f"❌ Error disabling Bluetooth: {e}"
        
        elif command.startswith("copy file"):
            match = re.match(r"copy file\s+(.+?)\s+to\s+(.+)", command)
            if match:
                source = match.group(1).strip()
                destination = match.group(2).strip()
                try:
                    import shutil
                    shutil.copy2(source, destination)
                    return True, f"✓ File copied from {source} to {destination}"
                except Exception as e:
                    return False, f"❌ Error copying file: {e}"
        
        elif command.startswith("move file"):
            match = re.match(r"move file\s+(.+?)\s+to\s+(.+)", command)
            if match:
                source = match.group(1).strip()
                destination = match.group(2).strip()
                try:
                    import shutil
                    shutil.move(source, destination)
                    return True, f"✓ File moved from {source} to {destination}"
                except Exception as e:
                    return False, f"❌ Error moving file: {e}"
        
        elif command.startswith("delete file"):
            match = re.match(r"delete file\s+(.+)", command)
            if match:
                file_path = match.group(1).strip()
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        return True, f"✓ File deleted: {file_path}"
                    else:
                        return False, f"❌ File not found: {file_path}"
                except Exception as e:
                    return False, f"❌ Error deleting file: {e}"
        
        elif command.startswith("system info"):
            try:
                import platform as pl
                info = f"""
🖥️ System Information:
• OS: {pl.system()} {pl.release()}
• Architecture: {pl.machine()}
• Processor: {pl.processor()}
• Python: {pl.python_version()}
• Current Directory: {os.getcwd()}
• Available Memory: {psutil.virtual_memory().total // (1024**3)} GB
• CPU Usage: {psutil.cpu_percent()}%
                """
                return True, info.strip()
            except Exception as e:
                return False, f"❌ Error getting system info: {e}"
        
        elif command.startswith("execute"):
            match = re.match(r"execute\s+(.+)", command)
            if match:
                cmd = match.group(1).strip()
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        return True, f"✓ Command executed:\n{result.stdout}"
                    else:
                        return False, f"❌ Command failed:\n{result.stderr}"
                except subprocess.TimeoutExpired:
                    return False, "❌ Command timed out"
                except Exception as e:
                    return False, f"❌ Error executing command: {e}"
        
        # If no specific command matched, try to execute as shell command
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return True, f"✓ Command executed:\n{result.stdout}"
            else:
                return False, f"❌ Command failed:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return False, "❌ Command timed out"
        except Exception as e:
            return False, f"❌ Error: {e}"

# Global JARIS instance
jarvis = JarvisWeb()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle AI chat requests"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Try to execute as command first
        success, output = jarvis.execute_command(message)
        if success:
            return jsonify({
                'type': 'command',
                'response': output,
                'success': True
            })
        else:
            # If not a command, try AI chat
            response = jarvis.chat_with_ai(message)
            return jsonify({
                'type': 'ai',
                'response': response,
                'success': True
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Get application status"""
    try:
        # Check if Ollama is running
        ollama_status = False
        try:
            response = requests.get(f"{jarvis.settings['ollama_url']}/api/tags", timeout=5)
            ollama_status = response.status_code == 200
        except:
            pass
        
        return jsonify({
            'ollama_running': ollama_status,
            'current_directory': os.getcwd(),
            'settings': jarvis.settings
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    """Handle settings"""
    if request.method == 'GET':
        return jsonify(jarvis.settings)
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            jarvis.settings.update(data)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/voice/listen', methods=['POST'])
def voice_listen():
    """Handle voice input"""
    try:
        text = jarvis.listen()
        return jsonify({
            'success': True,
            'text': text
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/speak', methods=['POST'])
def voice_speak():
    """Handle text-to-speech"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if text:
            jarvis.speak(text)
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'No text provided'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/start_continuous', methods=['POST'])
def start_continuous_listening():
    """Start continuous listening mode"""
    try:
        result = jarvis.start_continuous_listening()
        return jsonify({
            'success': True,
            'message': result,
            'listening': jarvis.settings['continuous_listening']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/stop_continuous', methods=['POST'])
def stop_continuous_listening():
    """Stop continuous listening mode"""
    try:
        result = jarvis.stop_continuous_listening()
        return jsonify({
            'success': True,
            'message': result,
            'listening': jarvis.settings['continuous_listening']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/status', methods=['GET'])
def voice_status():
    """Get voice listening status"""
    try:
        return jsonify({
            'success': True,
            'continuous_listening': jarvis.settings['continuous_listening'],
            'voice_enabled': jarvis.settings['voice_enabled']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_templates():
    """Create HTML templates"""
    os.makedirs('templates', exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARIS - AI Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            width: 90%;
            max-width: 1000px;
            height: 80vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
        }
        
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        
        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            border: none;
            background: transparent;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        
        .tab.active {
            background: white;
            border-bottom: 3px solid #667eea;
            color: #667eea;
            font-weight: bold;
        }
        
        .tab:hover {
            background: #e9ecef;
        }
        
        .content {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }
        
        .chat-container {
            height: 400px;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 15px;
            overflow-y: auto;
            background: #f8f9fa;
            margin-bottom: 20px;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .user-message {
            background: #667eea;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .ai-message {
            background: white;
            border: 1px solid #dee2e6;
            margin-right: auto;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .input-field {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid #dee2e6;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s ease;
        }
        
        .input-field:focus {
            border-color: #667eea;
        }
        
        .send-button {
            padding: 12px 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s ease;
        }
        
        .send-button:hover {
            transform: translateY(-2px);
        }
        
        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .voice-button {
            padding: 12px 15px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s ease;
            margin-right: 5px;
        }
        
        .voice-button:hover {
            background: #218838;
            transform: translateY(-2px);
        }
        
        .voice-button.listening {
            background: #dc3545;
            animation: pulse 1s infinite;
        }
        
            .voice-button.speaking {
                background: #ffc107;
                color: #000;
            }
            
            .continuous-button {
                padding: 12px 15px;
                background: #6f42c1;
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                transition: all 0.3s ease;
                margin-right: 5px;
            }
            
            .continuous-button:hover {
                background: #5a32a3;
                transform: translateY(-2px);
            }
            
            .continuous-button.listening {
                background: #28a745;
                animation: spin 2s linear infinite;
            }
            
            .continuous-button.stopped {
                background: #dc3545;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        
        .status {
            padding: 10px;
            background: #e9ecef;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        
        .status.online {
            background: #d4edda;
            color: #155724;
        }
        
        .status.offline {
            background: #f8d7da;
            color: #721c24;
        }
        
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .quick-action {
            padding: 10px 15px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .quick-action:hover {
            background: #e9ecef;
            border-color: #667eea;
        }
        
        .hidden {
            display: none;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 JARIS</h1>
            <p>Just A Rather Intelligent System</p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('ai')">💬 AI Chat</button>
            <button class="tab" onclick="switchTab('control')">💻 PC Control</button>
            <button class="tab" onclick="switchTab('settings')">⚙️ Settings</button>
        </div>
        
        <div class="content">
            <!-- AI Chat Tab -->
            <div id="ai-tab" class="tab-content">
                <div class="status" id="status">
                    <span id="status-text">Checking connection...</span>
                </div>
                
                <div class="chat-container" id="chat-container">
                    <div class="message ai-message">
                        <strong>JARIS:</strong> 👋 Hello! I'm JARIS, your friendly AI assistant. I can help you chat, control your PC, and answer questions. What would you like to do today?
                    </div>
                </div>
                
                <div class="input-container">
                    <input type="text" class="input-field" id="message-input" placeholder="Type your message or use voice..." onkeypress="handleKeyPress(event)">
                    <button class="voice-button" id="voice-button" onclick="toggleVoice()" title="Voice Input">🎤</button>
                    <button class="continuous-button" id="continuous-button" onclick="toggleContinuousListening()" title="Continuous Listening">🔄</button>
                    <button class="send-button" id="send-button" onclick="sendMessage()">Send</button>
                </div>
            </div>
            
            <!-- PC Control Tab -->
            <div id="control-tab" class="tab-content hidden">
                <div class="status" id="control-status">
                    <span id="control-status-text">PC Control Ready</span>
                </div>
                
                <div class="quick-actions">
                    <div class="quick-action" onclick="quickCommand('create folder MyProject')">📁 Create Folder</div>
                    <div class="quick-action" onclick="quickCommand('list files')">📂 List Files</div>
                    <div class="quick-action" onclick="quickCommand('open downloads')">📥 Open Downloads</div>
                    <div class="quick-action" onclick="quickCommand('execute python --version')">🐍 Python Version</div>
                </div>
                
                <div class="chat-container" id="control-chat-container">
                    <div class="message ai-message">
                        <strong>JARIS:</strong> 💻 PC Control ready! I can help you manage files, run commands, and control your system. Try saying "create folder MyProject" or "list files" - or use the 🎤 button for voice commands!
                    </div>
                </div>
                
                <div class="input-container">
                    <input type="text" class="input-field" id="command-input" placeholder="Enter command or use voice..." onkeypress="handleCommandKeyPress(event)">
                    <button class="voice-button" id="control-voice-button" onclick="toggleControlVoice()" title="Voice Input">🎤</button>
                    <button class="continuous-button" id="control-continuous-button" onclick="toggleControlContinuousListening()" title="Continuous Listening">🔄</button>
                    <button class="send-button" id="command-button" onclick="executeCommand()">Execute</button>
                </div>
            </div>
            
            <!-- Settings Tab -->
            <div id="settings-tab" class="tab-content hidden">
                <h3>Settings</h3>
                <div class="status">
                    <strong>Current Settings:</strong><br>
                    <span id="settings-display">Loading...</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentTab = 'ai';
            let isListening = false;
            let isSpeaking = false;
            let isContinuousListening = false;
        
        function switchTab(tab) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tab + '-tab').classList.remove('hidden');
            document.querySelector(`[onclick="switchTab('${tab}')"]`).classList.add('active');
            currentTab = tab;
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        function handleCommandKeyPress(event) {
            if (event.key === 'Enter') {
                executeCommand();
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            // Show loading
            const sendButton = document.getElementById('send-button');
            sendButton.disabled = true;
            sendButton.innerHTML = '<div class="loading"></div>';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addMessage(data.response, 'ai');
                    // Speak the response
                    speakText(data.response);
                } else {
                    addMessage('Error: ' + (data.error || 'Unknown error'), 'ai');
                }
            } catch (error) {
                addMessage('Error: ' + error.message, 'ai');
            } finally {
                sendButton.disabled = false;
                sendButton.innerHTML = 'Send';
            }
        }
        
        async function executeCommand() {
            const input = document.getElementById('command-input');
            const command = input.value.trim();
            
            if (!command) return;
            
            // Add command to chat
            addControlMessage(`> ${command}`, 'user');
            input.value = '';
            
            // Show loading
            const commandButton = document.getElementById('command-button');
            commandButton.disabled = true;
            commandButton.innerHTML = '<div class="loading"></div>';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: command })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addControlMessage(data.response, 'ai');
                    // Speak the response
                    speakText(data.response);
                } else {
                    addControlMessage('Error: ' + (data.error || 'Unknown error'), 'ai');
                }
            } catch (error) {
                addControlMessage('Error: ' + error.message, 'ai');
            } finally {
                commandButton.disabled = false;
                commandButton.innerHTML = 'Execute';
            }
        }
        
        function quickCommand(command) {
            document.getElementById('command-input').value = command;
            executeCommand();
        }
        
        async function toggleVoice() {
            const button = document.getElementById('voice-button');
            const input = document.getElementById('message-input');
            
            if (isListening) {
                button.classList.remove('listening');
                button.textContent = '🎤';
                isListening = false;
                return;
            }
            
            button.classList.add('listening');
            button.textContent = '🔴';
            isListening = true;
            
            try {
                const response = await fetch('/api/voice/listen', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    input.value = data.text;
                    if (data.text && data.text !== 'No speech detected' && data.text !== 'Could not understand speech') {
                        sendMessage();
                    }
                } else {
                    alert('Voice input error: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Voice input error: ' + error.message);
            } finally {
                button.classList.remove('listening');
                button.textContent = '🎤';
                isListening = false;
            }
        }
        
        async function toggleControlVoice() {
            const button = document.getElementById('control-voice-button');
            const input = document.getElementById('command-input');
            
            if (isListening) {
                button.classList.remove('listening');
                button.textContent = '🎤';
                isListening = false;
                return;
            }
            
            button.classList.add('listening');
            button.textContent = '🔴';
            isListening = true;
            
            try {
                const response = await fetch('/api/voice/listen', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    input.value = data.text;
                    if (data.text && data.text !== 'No speech detected' && data.text !== 'Could not understand speech') {
                        executeCommand();
                    }
                } else {
                    alert('Voice input error: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                alert('Voice input error: ' + error.message);
            } finally {
                button.classList.remove('listening');
                button.textContent = '🎤';
                isListening = false;
            }
        }
        
        async function speakText(text) {
            if (isSpeaking) return;
            
            isSpeaking = true;
            const buttons = document.querySelectorAll('.voice-button');
            buttons.forEach(btn => {
                btn.classList.add('speaking');
                btn.textContent = '🔊';
            });
            
            try {
                const response = await fetch('/api/voice/speak', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: text })
                });
                
                if (!response.ok) {
                    console.error('TTS error:', response.statusText);
                }
            } catch (error) {
                console.error('TTS error:', error);
            } finally {
                setTimeout(() => {
                    isSpeaking = false;
                    buttons.forEach(btn => {
                        btn.classList.remove('speaking');
                        btn.textContent = '🎤';
                    });
                }, 2000);
            }
        }
        
        async function toggleContinuousListening() {
            const button = document.getElementById('continuous-button');
            
            if (isContinuousListening) {
                // Stop continuous listening
                try {
                    const response = await fetch('/api/voice/stop_continuous', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    
                    if (response.ok) {
                        isContinuousListening = false;
                        button.classList.remove('listening');
                        button.classList.add('stopped');
                        button.innerHTML = '⏹️';
                        button.title = 'Continuous Listening Stopped';
                        
                        setTimeout(() => {
                            button.classList.remove('stopped');
                            button.innerHTML = '🔄';
                            button.title = 'Start Continuous Listening';
                        }, 2000);
                    }
                } catch (error) {
                    console.error('Error stopping continuous listening:', error);
                }
            } else {
                // Start continuous listening
                try {
                    const response = await fetch('/api/voice/start_continuous', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    
                    if (response.ok) {
                        isContinuousListening = true;
                        button.classList.add('listening');
                        button.innerHTML = '🔄';
                        button.title = 'Continuous Listening Active';
                    }
                } catch (error) {
                    console.error('Error starting continuous listening:', error);
                }
            }
        }
        
        async function toggleControlContinuousListening() {
            const button = document.getElementById('control-continuous-button');
            
            if (isContinuousListening) {
                // Stop continuous listening
                try {
                    const response = await fetch('/api/voice/stop_continuous', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    
                    if (response.ok) {
                        isContinuousListening = false;
                        button.classList.remove('listening');
                        button.classList.add('stopped');
                        button.innerHTML = '⏹️';
                        button.title = 'Continuous Listening Stopped';
                        
                        setTimeout(() => {
                            button.classList.remove('stopped');
                            button.innerHTML = '🔄';
                            button.title = 'Start Continuous Listening';
                        }, 2000);
                    }
                } catch (error) {
                    console.error('Error stopping continuous listening:', error);
                }
            } else {
                // Start continuous listening
                try {
                    const response = await fetch('/api/voice/start_continuous', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    
                    if (response.ok) {
                        isContinuousListening = true;
                        button.classList.add('listening');
                        button.innerHTML = '🔄';
                        button.title = 'Continuous Listening Active';
                    }
                } catch (error) {
                    console.error('Error starting continuous listening:', error);
                }
            }
        }
        
        function addMessage(message, sender) {
            const container = document.getElementById('chat-container');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender === 'user' ? 'user-message' : 'ai-message'}`;
            messageDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'JARIS'}:</strong> ${message}`;
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        function addControlMessage(message, sender) {
            const container = document.getElementById('control-chat-container');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender === 'user' ? 'user-message' : 'ai-message'}`;
            messageDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'JARIS'}:</strong> ${message}`;
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const statusElement = document.getElementById('status');
                const statusText = document.getElementById('status-text');
                
                if (data.ollama_running) {
                    statusElement.className = 'status online';
                    statusText.textContent = '✅ Connected to Ollama AI service';
                } else {
                    statusElement.className = 'status offline';
                    statusText.textContent = '❌ Ollama not running. AI features may not work.';
                }
            } catch (error) {
                const statusElement = document.getElementById('status');
                const statusText = document.getElementById('status-text');
                statusElement.className = 'status offline';
                statusText.textContent = '❌ Connection error';
            }
        }
        
        // Check status on load
        checkStatus();
        
        // Check status every 30 seconds
        setInterval(checkStatus, 30000);
    </script>
</body>
</html>'''
    
    with open('templates/index.html', 'w') as f:
        f.write(html_content)

def main():
    """Main entry point"""
    print("🚀 Starting JARIS Web GUI...")
    print("Make sure Ollama is running on localhost:11434")
    
    # Create templates
    create_templates()
    
    # Start the web server
    port = 8080
    print("\n🌐 JARIS Web GUI will be available at:")
    print(f"   http://localhost:{port}")
    print("\n📱 Open your browser and navigate to the URL above")
    print("🛑 Press Ctrl+C to stop the server")
    
    # Open browser automatically
    def open_browser():
        time.sleep(2)
        webbrowser.open(f'http://localhost:{port}')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n👋 JARIS Web GUI stopped")
    except Exception as e:
        print(f"❌ Error starting JARIS Web GUI: {e}")

if __name__ == "__main__":
    main()
