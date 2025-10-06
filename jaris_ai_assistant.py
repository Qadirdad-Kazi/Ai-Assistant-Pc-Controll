#!/usr/bin/env python3
"""
JARIS - Just A Rather Intelligent System
A Python-based AI assistant with voice control and PC management capabilities.
"""

import os
import sys
import json
import subprocess
import threading
import time
import re
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import speech_recognition as sr
import pyttsx3
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import webbrowser
import platform

# Configuration
@dataclass
class Settings:
    # Voice Settings
    voice_enabled: bool = True
    auto_speak: bool = True
    volume: float = 0.8
    mic_sensitivity: float = 0.7
    
    # AI Settings
    model: str = "llama3.2:latest"
    ollama_url: str = "http://localhost:11434"
    
    # Appearance Settings
    theme: str = "dark"
    font_family: str = "Arial"
    font_size: int = 12
    
    def save(self, filepath: str = "settings.json"):
        """Save settings to file"""
        with open(filepath, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load(cls, filepath: str = "settings.json"):
        """Load settings from file"""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()

class JarvisAI:
    def __init__(self):
        self.settings = Settings.load()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_engine = None
        self.is_listening = False
        self.is_speaking = False
        self.conversation_history = []
        
        # Initialize TTS engine
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', self.settings.volume)
        except Exception as e:
            print(f"TTS initialization failed: {e}")
        
        # Adjust microphone sensitivity
        self.recognizer.energy_threshold = int(300 * (1 - self.settings.mic_sensitivity))
        self.recognizer.dynamic_energy_threshold = True
        
    def speak(self, text: str):
        """Convert text to speech"""
        if not self.settings.voice_enabled or not self.tts_engine:
            return
            
        self.is_speaking = True
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS error: {e}")
        finally:
            self.is_speaking = False
    
    def listen(self) -> Optional[str]:
        """Listen for voice input"""
        if not self.settings.voice_enabled:
            return None
            
        self.is_listening = True
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            text = self.recognizer.recognize_google(audio)
            return text.lower()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return None
        finally:
            self.is_listening = False
    
    def chat_with_ai(self, message: str) -> str:
        """Send message to AI and get response"""
        try:
            # Add system message and conversation history
            messages = [
                {"role": "system", "content": "You are JARIS, a helpful AI assistant. Provide concise and helpful responses."}
            ]
            messages.extend(self.conversation_history[-10:])  # Keep last 10 messages
            messages.append({"role": "user", "content": message})
            
            response = requests.post(
                f"{self.settings.ollama_url}/api/chat",
                json={
                    "model": self.settings.model,
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
            match = re.match(r"create folder\s+(.+)", command)
            if match:
                folder_name = match.group(1).strip()
                try:
                    os.makedirs(folder_name, exist_ok=True)
                    return True, f"✓ Created folder: {folder_name}"
                except Exception as e:
                    return False, f"❌ Error creating folder: {e}"
        
        elif command.startswith("create file") or command.startswith("write"):
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
            try:
                files = os.listdir(directory)
                file_list = []
                for f in files:
                    path = os.path.join(directory, f)
                    if os.path.isdir(path):
                        file_list.append(f"📁 {f}")
                    else:
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
                target = match.group(1).strip()
                try:
                    if target.startswith("http"):
                        webbrowser.open(target)
                        return True, f"✓ Opened URL: {target}"
                    else:
                        if platform.system() == "Windows":
                            os.startfile(target)
                        else:
                            subprocess.run(["xdg-open", target])
                        return True, f"✓ Opened: {target}"
                except Exception as e:
                    return False, f"❌ Error opening: {e}"
        
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

class JarvisGUI:
    def __init__(self):
        self.ai = JarvisAI()
        self.root = tk.Tk()
        self.setup_gui()
        self.load_settings()
        
    def setup_gui(self):
        """Setup the GUI components"""
        self.root.title("JARIS - Just A Rather Intelligent System")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1a1a1a' if self.ai.settings.theme == 'dark' else '#ffffff')
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # AI Chat Tab
        self.setup_ai_tab()
        
        # PC Control Tab
        self.setup_control_tab()
        
        # Settings Tab
        self.setup_settings_tab()
        
    def setup_ai_tab(self):
        """Setup AI chat interface"""
        self.ai_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.ai_frame, text="🤖 AI Mode")
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            self.ai_frame, 
            height=20, 
            font=(self.ai.settings.font_family, self.ai.settings.font_size),
            bg='#2d2d2d' if self.ai.settings.theme == 'dark' else '#ffffff',
            fg='#ffffff' if self.ai.settings.theme == 'dark' else '#000000',
            insertbackground='#ffffff' if self.ai.settings.theme == 'dark' else '#000000'
        )
        self.chat_display.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Input frame
        input_frame = ttk.Frame(self.ai_frame)
        input_frame.pack(fill='x', padx=10, pady=5)
        
        self.input_entry = ttk.Entry(input_frame, font=(self.ai.settings.font_family, self.ai.settings.font_size))
        self.input_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.input_entry.bind('<Return>', self.send_message)
        
        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side='right')
        
        self.voice_button = ttk.Button(button_frame, text="🎤", command=self.toggle_voice)
        self.voice_button.pack(side='left', padx=2)
        
        self.send_button = ttk.Button(button_frame, text="Send", command=self.send_message)
        self.send_button.pack(side='left', padx=2)
        
        # Status
        self.status_label = ttk.Label(self.ai_frame, text="Ready")
        self.status_label.pack(pady=5)
        
        # Welcome message
        self.add_to_chat("JARIS", "Hello! I'm JARIS, your AI assistant. How can I help you today?")
        
    def setup_control_tab(self):
        """Setup PC control interface"""
        self.control_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.control_frame, text="💻 PC Control")
        
        # Command display
        self.command_display = scrolledtext.ScrolledText(
            self.control_frame,
            height=20,
            font=(self.ai.settings.font_family, self.ai.settings.font_size),
            bg='#2d2d2d' if self.ai.settings.theme == 'dark' else '#ffffff',
            fg='#ffffff' if self.ai.settings.theme == 'dark' else '#000000',
            insertbackground='#ffffff' if self.ai.settings.theme == 'dark' else '#000000'
        )
        self.command_display.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Input frame
        control_input_frame = ttk.Frame(self.control_frame)
        control_input_frame.pack(fill='x', padx=10, pady=5)
        
        self.command_entry = ttk.Entry(control_input_frame, font=(self.ai.settings.font_family, self.ai.settings.font_size))
        self.command_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.command_entry.bind('<Return>', self.execute_command)
        
        self.execute_button = ttk.Button(control_input_frame, text="Execute", command=self.execute_command)
        self.execute_button.pack(side='right', padx=2)
        
        # Quick actions
        quick_frame = ttk.Frame(self.control_frame)
        quick_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(quick_frame, text="Quick Actions:").pack(side='left')
        
        quick_buttons = [
            ("Create Folder", "create folder MyProject"),
            ("List Files", "list files"),
            ("Open Downloads", "open downloads"),
            ("Current Directory", "list files .")
        ]
        
        for text, command in quick_buttons:
            btn = ttk.Button(quick_frame, text=text, 
                           command=lambda c=command: self.run_quick_command(c))
            btn.pack(side='left', padx=2)
        
        # Welcome message
        self.add_to_control("JARIS PC Control", "Ready for commands. Try: 'create folder MyProject' or 'list files'")
        
    def setup_settings_tab(self):
        """Setup settings interface"""
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="⚙️ Settings")
        
        # Voice Settings
        voice_frame = ttk.LabelFrame(self.settings_frame, text="Voice Settings")
        voice_frame.pack(fill='x', padx=10, pady=5)
        
        self.voice_enabled_var = tk.BooleanVar(value=self.ai.settings.voice_enabled)
        ttk.Checkbutton(voice_frame, text="Enable Voice", variable=self.voice_enabled_var).pack(anchor='w')
        
        self.auto_speak_var = tk.BooleanVar(value=self.ai.settings.auto_speak)
        ttk.Checkbutton(voice_frame, text="Auto Speak Responses", variable=self.auto_speak_var).pack(anchor='w')
        
        # Volume
        ttk.Label(voice_frame, text="Volume:").pack(anchor='w')
        self.volume_var = tk.DoubleVar(value=self.ai.settings.volume)
        volume_scale = ttk.Scale(voice_frame, from_=0.0, to=1.0, variable=self.volume_var, orient='horizontal')
        volume_scale.pack(fill='x', padx=5)
        
        # AI Settings
        ai_frame = ttk.LabelFrame(self.settings_frame, text="AI Settings")
        ai_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(ai_frame, text="Ollama Model:").pack(anchor='w')
        self.model_var = tk.StringVar(value=self.ai.settings.model)
        model_entry = ttk.Entry(ai_frame, textvariable=self.model_var)
        model_entry.pack(fill='x', padx=5)
        
        ttk.Label(ai_frame, text="Ollama URL:").pack(anchor='w')
        self.ollama_url_var = tk.StringVar(value=self.ai.settings.ollama_url)
        url_entry = ttk.Entry(ai_frame, textvariable=self.ollama_url_var)
        url_entry.pack(fill='x', padx=5)
        
        # Appearance Settings
        appearance_frame = ttk.LabelFrame(self.settings_frame, text="Appearance")
        appearance_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(appearance_frame, text="Theme:").pack(anchor='w')
        self.theme_var = tk.StringVar(value=self.ai.settings.theme)
        theme_combo = ttk.Combobox(appearance_frame, textvariable=self.theme_var, values=['light', 'dark'])
        theme_combo.pack(fill='x', padx=5)
        
        ttk.Label(appearance_frame, text="Font Size:").pack(anchor='w')
        self.font_size_var = tk.IntVar(value=self.ai.settings.font_size)
        font_size_scale = ttk.Scale(appearance_frame, from_=8, to=20, variable=self.font_size_var, orient='horizontal')
        font_size_scale.pack(fill='x', padx=5)
        
        # Save button
        ttk.Button(self.settings_frame, text="Save Settings", command=self.save_settings).pack(pady=10)
        
    def add_to_chat(self, sender: str, message: str):
        """Add message to chat display"""
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_display.see(tk.END)
        
    def add_to_control(self, sender: str, message: str):
        """Add message to control display"""
        self.command_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.command_display.see(tk.END)
        
    def send_message(self, event=None):
        """Send message to AI"""
        message = self.input_entry.get().strip()
        if not message:
            return
            
        self.input_entry.delete(0, tk.END)
        self.add_to_chat("You", message)
        
        # Show typing indicator
        self.status_label.config(text="AI is thinking...")
        self.root.update()
        
        # Get AI response
        response = self.ai.chat_with_ai(message)
        self.add_to_chat("JARIS", response)
        
        # Speak response if enabled
        if self.ai.settings.auto_speak and self.ai.settings.voice_enabled:
            self.ai.speak(response)
            
        self.status_label.config(text="Ready")
        
    def toggle_voice(self):
        """Toggle voice input"""
        if self.ai.is_listening:
            self.voice_button.config(text="🎤")
            self.status_label.config(text="Voice input stopped")
        else:
            self.voice_button.config(text="🔴")
            self.status_label.config(text="Listening...")
            self.root.after(100, self.listen_for_voice)
            
    def listen_for_voice(self):
        """Listen for voice input in a separate thread"""
        def voice_thread():
            text = self.ai.listen()
            if text:
                self.root.after(0, lambda: self.input_entry.insert(0, text))
                self.root.after(0, lambda: self.voice_button.config(text="🎤"))
                self.root.after(0, lambda: self.status_label.config(text="Voice input received"))
            else:
                self.root.after(0, lambda: self.voice_button.config(text="🎤"))
                self.root.after(0, lambda: self.status_label.config(text="No voice input detected"))
                
        threading.Thread(target=voice_thread, daemon=True).start()
        
    def execute_command(self, event=None):
        """Execute system command"""
        command = self.command_entry.get().strip()
        if not command:
            return
            
        self.command_entry.delete(0, tk.END)
        self.add_to_control("You", f"> {command}")
        
        # Show executing indicator
        self.status_label.config(text="Executing command...")
        self.root.update()
        
        # Execute command
        success, output = self.ai.execute_command(command)
        
        if success:
            self.add_to_control("JARIS", f"✓ {output}")
        else:
            self.add_to_control("JARIS", f"❌ {output}")
            
        self.status_label.config(text="Ready")
        
    def run_quick_command(self, command: str):
        """Run a quick command"""
        self.command_entry.delete(0, tk.END)
        self.command_entry.insert(0, command)
        self.execute_command()
        
    def save_settings(self):
        """Save current settings"""
        self.ai.settings.voice_enabled = self.voice_enabled_var.get()
        self.ai.settings.auto_speak = self.auto_speak_var.get()
        self.ai.settings.volume = self.volume_var.get()
        self.ai.settings.model = self.model_var.get()
        self.ai.settings.ollama_url = self.ollama_url_var.get()
        self.ai.settings.theme = self.theme_var.get()
        self.ai.settings.font_size = self.font_size_var.get()
        
        # Update TTS volume
        if self.ai.tts_engine:
            self.ai.tts_engine.setProperty('volume', self.ai.settings.volume)
            
        # Save to file
        self.ai.settings.save()
        messagebox.showinfo("Settings", "Settings saved successfully!")
        
    def load_settings(self):
        """Load settings into GUI"""
        self.voice_enabled_var.set(self.ai.settings.voice_enabled)
        self.auto_speak_var.set(self.ai.settings.auto_speak)
        self.volume_var.set(self.ai.settings.volume)
        self.model_var.set(self.ai.settings.model)
        self.ollama_url_var.set(self.ai.settings.ollama_url)
        self.theme_var.set(self.ai.settings.theme)
        self.font_size_var.set(self.ai.settings.font_size)
        
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    print("Starting JARIS - Just A Rather Intelligent System")
    print("Make sure Ollama is running on localhost:11434")
    
    try:
        app = JarvisGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down JARIS...")
    except Exception as e:
        print(f"Error starting JARIS: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
