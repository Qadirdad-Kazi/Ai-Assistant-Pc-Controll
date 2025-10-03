"""
PC Controller Module
Handles system-level commands and PC control functionality
"""

import os
import sys
import subprocess
import psutil
import time
from datetime import datetime
import webbrowser
import platform
import pygetwindow as gw
from PIL import ImageGrab, Image, ImageDraw, ImageFont
import pytesseract
import openai
from config import Config
import json
import subprocess
import re
import tempfile
import threading
from command_history import CommandHistory
from screen_reader import ScreenReader

# Configure Tesseract path if needed (for Windows)
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Handle GUI module imports gracefully
try:
    import pyautogui
    GUI_AVAILABLE = True
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5
except ImportError:
    GUI_AVAILABLE = False
    print("Warning: GUI features disabled - pyautogui not available")
except Exception as e:
    GUI_AVAILABLE = False
    print(f"Warning: GUI features disabled - {e}")

class PCController:
    def __init__(self):
        self.config = Config()
        self.system = platform.system().lower()
        self.ai_enabled = hasattr(self.config, 'OLLAMA_API_BASE') and self.config.OLLAMA_API_BASE
        self.command_history = CommandHistory()
        
        # Visual feedback settings
        self.visual_feedback_enabled = True
        self.feedback_window = None
        self.feedback_thread = None
        
        # Initialize screen reader
        self.screen_reader = ScreenReader(update_interval=2.0)
        self.screen_reader_content = ""
        self.screen_reader_callback = None

    def _on_screen_content_update(self, content_data):
        """Handle screen content updates"""
        self.screen_reader_content = content_data['content']
        if self.screen_reader_callback:
            self.screen_reader_callback(content_data)
    
    def start_screen_reader(self, callback=None):
        """
        Start the screen reader
        
        Args:
            callback (callable): Function to call when screen content updates
            
        Returns:
            dict: Result with success status and message
        """
        try:
            self.screen_reader_callback = callback
            self.screen_reader.start(self._on_screen_content_update)
            return {
                'success': True,
                'message': 'Screen reader started',
                'type': 'screen_reader',
                'status': 'started'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to start screen reader: {str(e)}',
                'type': 'screen_reader_error'
            }
    
    def stop_screen_reader(self):
        """Stop the screen reader"""
        try:
            self.screen_reader.stop()
            return {
                'success': True,
                'message': 'Screen reader stopped',
                'type': 'screen_reader',
                'status': 'stopped'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to stop screen reader: {str(e)}',
                'type': 'screen_reader_error'
            }
    
    def toggle_screen_reader_pause(self):
        """Toggle pause/resume of the screen reader"""
        try:
            if self.screen_reader.is_paused:
                self.screen_reader.resume()
                status = 'resumed'
                message = 'Screen reader resumed'
            else:
                self.screen_reader.pause()
                status = 'paused'
                message = 'Screen reader paused'
                
            return {
                'success': True,
                'message': message,
                'type': 'screen_reader',
                'status': status,
                'is_paused': self.screen_reader.is_paused
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to toggle screen reader: {str(e)}',
                'type': 'screen_reader_error'
            }
    
    def get_screen_reader_status(self):
        """Get the current status of the screen reader"""
        return {
            'is_running': self.screen_reader.is_running,
            'is_paused': self.screen_reader.is_paused,
            'last_update': self.screen_reader.last_update_time if hasattr(self.screen_reader, 'last_update_time') else None,
            'content_length': len(self.screen_reader_content)
        }
    
    def _show_visual_feedback(self, message, duration=2):
        """
        Show a visual feedback message on screen
        
        Args:
            message (str): Message to display
            duration (int): How long to show the message in seconds
        """
        if not self.visual_feedback_enabled or not GUI_AVAILABLE:
            return
            
        def show_message():
            try:
                # Create a semi-transparent overlay
                screen_width, screen_height = pyautogui.size()
                img = Image.new('RGBA', (screen_width, 100), (0, 0, 0, 180))
                draw = ImageDraw.Draw(img)
                
                # Try to use a nice font, fall back to default if not available
                try:
                    font = ImageFont.truetype("Arial", 24)
                except:
                    font = ImageFont.load_default()
                
                # Calculate text size and position
                text_bbox = draw.textbbox((0, 0), message, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                x = (screen_width - text_width) // 2
                y = (100 - text_height) // 2
                
                # Draw text with a slight shadow for better visibility
                draw.text((x+1, y+1), message, fill=(0, 0, 0), font=font)
                draw.text((x, y), message, fill=(255, 255, 255), font=font)
                
                # Save to a temporary file and display
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    img_path = tmp.name
                    img.save(img_path)
                    
                    # Show the image using the default image viewer
                    if platform.system() == 'Darwin':  # macOS
                        subprocess.run(['open', img_path])
                    elif platform.system() == 'Windows':
                        os.startfile(img_path)
                    else:  # Linux and others
                        subprocess.run(['xdg-open', img_path])
                    
                    # Schedule removal of the temp file
                    def remove_temp():
                        time.sleep(duration)
                        try:
                            if os.path.exists(img_path):
                                os.remove(img_path)
                        except:
                            pass
                    
                    threading.Thread(target=remove_temp, daemon=True).start()
                    
            except Exception as e:
                print(f"Error showing visual feedback: {e}")
        
        # Run in a separate thread to not block
        self.feedback_thread = threading.Thread(target=show_message, daemon=True)
        self.feedback_thread.start()
    
    def execute_command(self, command):
        """
        Execute a system command based on natural language input
        
        Args:
            command (str): The command to execute
            
        Returns:
            dict: {
                'success': bool,  # Whether the command was successful
                'message': str,   # Human-readable result message
                'type': str,      # Type of operation (e.g., 'folder_created', 'error')
                'details': dict   # Additional debug information
            }
        """
        if not command or not isinstance(command, str):
            return {
                'success': False,
                'message': 'Invalid command: Command cannot be empty',
                'type': 'error',
                'details': {'command': command, 'error_type': 'empty_command'}
            }
            
        # Show visual feedback that command is being processed
        self._show_visual_feedback(f"Executing: {command}")
        
        # Store the start time for performance tracking
        start_time = time.time()
        command_lower = command.lower().strip()
        
        try:
            # Application launching commands
            if any(word in command_lower for word in ['open', 'start', 'launch']):
                return self.handle_app_launch(command_lower)
            
            # Window management commands
            elif any(word in command_lower for word in ['close', 'minimize', 'maximize']):
                return self.handle_window_management(command_lower)
            
            # Volume control commands
            elif 'volume' in command_lower:
                return self.handle_volume_control(command_lower)
            
            # Screenshot and screen scanning commands
            elif 'screenshot' in command_lower or 'scan screen' in command_lower or 'what\'s on screen' in command_lower:
                if 'scan' in command_lower or 'what\'s' in command_lower:
                    return self.scan_screen()
                return self.take_screenshot()
            
            # System control commands
            elif any(word in command_lower for word in ['shutdown', 'restart', 'sleep', 'hibernate']):
                return self.handle_system_control(command_lower)
            
            # Time and date commands
            elif any(word in command_lower for word in ['time', 'date', 'clock']):
                return self.get_time_date()
            
            # Media control commands
            elif any(word in command_lower for word in ['play', 'pause', 'stop', 'next', 'previous']):
                return self.handle_media_control(command_lower)

            # Mouse move command: "mouse move to X Y [duration DURATION]"
            elif command_lower.startswith("mouse move to"):
                parts = command_lower.split()
                try:
                    x = parts[3]
                    y = parts[4]
                    duration = 0.25 # default duration
                    if len(parts) > 6 and parts[5] == "duration":
                        duration = parts[6]
                    return self.move_mouse_to_coordinates(x, y, duration)
                except (IndexError, ValueError):
                    return {'success': False, 'message': 'Invalid mouse move command. Use "mouse move to X Y [duration DURATION]"'}
            
            # Mouse click command: "mouse click [X Y] [button BUTTON] [clicks CLICKS]"
            # Folder creation command
            elif any(phrase in command_lower for phrase in ['create folder', 'make directory', 'new folder']):
                try:
                    # Extract folder name and path from command
                    parts = command_lower.split()
                    folder_name = ""
                    base_path = os.path.expanduser("~")
                    
                    # Check for "in [path]" pattern
                    if ' in ' in command_lower and ' named ' in command_lower:
                        in_index = parts.index('in')
                        named_index = parts.index('named')
                        
                        # Get the base path
                        path_parts = parts[in_index + 1:named_index]
                        base_path = os.path.expanduser(os.path.join(*path_parts))
                        
                        # Get the folder name
                        folder_name = ' '.join(parts[named_index + 1:])
                    elif 'named' in command_lower:
                        # Just get the folder name after 'named'
                        named_index = parts.index('named')
                        folder_name = ' '.join(parts[named_index + 1:])
                    else:
                        # If no 'named' keyword, use the last part as folder name
                        folder_name = parts[-1]
                    
                    # Create the full path
                    full_path = os.path.join(os.path.expanduser(base_path), folder_name)
                    
                    # Create the folder
                    os.makedirs(full_path, exist_ok=True)
                    
                    return {
                        'success': True,
                        'message': f'Successfully created folder: {full_path}',
                        'path': full_path,
                        'type': 'folder_created'
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'message': f'Error creating folder: {str(e)}',
                        'type': 'error'
                    }
            
            # AI-powered task execution
            elif command_lower.startswith(('do ', 'perform ', 'execute ', 'run ')) or \
                 'task' in command_lower or 'help me' in command_lower:
                task = command_lower
                if 'create a basic contact form' in command_lower or 'create contact form' in command_lower:
                    return self.create_contact_form()
                return self.execute_ai_task(task)
                
            elif command_lower.startswith("mouse click"):
                parts = command_lower.split()
                x, y, button, clicks_num = None, None, 'left', 1
                try:
                    idx = 2
                    # Check for coordinates
                    if idx < len(parts) and parts[idx].isdigit() and idx + 1 < len(parts) and parts[idx+1].isdigit():
                        x = parts[idx]
                        y = parts[idx+1]
                        idx += 2
                    # Check for button
                    if idx < len(parts) and parts[idx] == "button" and idx + 1 < len(parts):
                        button = parts[idx+1]
                        idx += 2
                    # Check for clicks
                    if idx < len(parts) and parts[idx] == "clicks" and idx + 1 < len(parts):
                        clicks_num = parts[idx+1]
                        idx += 2
                    return self.click_mouse_button(x, y, button, clicks_num)
                except (IndexError, ValueError):
                     return {'success': False, 'message': 'Invalid mouse click command. Use "mouse click [X Y] [button BUTTON] [clicks CLICKS]"'}

            # Type text command: "type TEXT_TO_TYPE"
            elif command_lower.startswith("type"):
                text_to_type = command_lower[len("type"):].strip()
                if text_to_type:
                    return self.type_keyboard_input(text_to_type)
                else:
                    return {'success': False, 'message': 'No text specified to type. Use "type YOUR_TEXT_HERE"'}

            
            # Press keys command: "press KEY_OR_HOTKEY"
            # For hotkeys, they should be space separated if multiple, e.g., "press ctrl shift esc"
            elif command_lower.startswith("press"):
                keys_to_press = command_lower[len("press"):].strip().split()
                if keys_to_press:
                    if len(keys_to_press) == 1:
                        return self.press_special_keys(keys_to_press[0])
                    else:
                        return self.press_special_keys(keys_to_press) # Pass as a list for hotkey
                else:
                    return {'success': False, 'message': 'No key specified to press. Use "press KEY_NAME" or "press ctrl c"'}
            
            else:
                return {
                    'success': False,
                    'message': "I don't understand that command. Try asking me to open an app, take a screenshot, or control the volume."
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error executing command: {str(e)}"
            }

    def handle_app_launch(self, command):
        """Handle application launching commands"""
        apps = {
            'chrome': ['chrome', 'google chrome', 'browser'],
            'firefox': ['firefox', 'mozilla'],
            'notepad': ['notepad', 'text editor'],
            'calculator': ['calculator', 'calc'],
            'code': ['vscode', 'visual studio code', 'code'],
            'explorer': ['explorer', 'file manager', 'files'],
            'cmd': ['command prompt', 'terminal', 'cmd'],
            'powershell': ['powershell', 'power shell'],
            'spotify': ['spotify', 'music'],
            'discord': ['discord'],
            'teams': ['teams', 'microsoft teams'],
            'word': ['word', 'microsoft word'],
            'excel': ['excel', 'microsoft excel'],
            'outlook': ['outlook', 'email']
        }
        
        app_to_launch = None
        for app, keywords in apps.items():
            if any(keyword in command for keyword in keywords):
                app_to_launch = app
                break
        
        if not app_to_launch:
            # Quick special-case handlers for common voice requests
            if 'youtube' in command or 'open youtube' in command:
                # Prefer YouTube in browser
                return self.open_url('https://www.youtube.com')
            if 'create web' in command or 'create website' in command or 'create website' in command:
                return self.handle_create_web_project(command)

            # Try to extract app name directly from command if not in predefined list
            command_parts = command.split()
            launch_keywords = ['open', 'start', 'launch']
            extracted_app_name = []
            can_extract = False
            for i, part in enumerate(command_parts):
                if part in launch_keywords and i + 1 < len(command_parts):
                    extracted_app_name = command_parts[i+1:]
                    can_extract = True
                    break
        
            if can_extract and extracted_app_name:
                app_to_launch = " ".join(extracted_app_name)
                # For macOS, try to capitalize for app names like 'Google Chrome'
                if self.system == 'darwin':
                    app_to_launch = app_to_launch.title()
            else:
                return {
                    'success': False,
                    'message': "I couldn't identify which application to open from your command."
                }
        
        try:
            if self.system == 'windows':
                success = self.launch_windows_app(app_to_launch)
            elif self.system == 'darwin':  # macOS
                success = self.launch_mac_app(app_to_launch)
            else:  # Linux
                success = self.launch_linux_app(app_to_launch)
            
            if success:
                return {
                    'success': True,
                    'message': f"Opened {app_to_launch.title()}"
                }
            else:
                return {
                    'success': False,
                    'message': f"Could not open {app_to_launch.title()}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error opening {app_to_launch}: {str(e)}"
            }

    def launch_windows_app(self, app):
        """Launch application on Windows"""
        try:
            if app == 'chrome':
                subprocess.Popen(['start', 'chrome'], shell=True)
            elif app == 'firefox':
                subprocess.Popen(['start', 'firefox'], shell=True)
            elif app == 'notepad':
                subprocess.Popen(['notepad'])
            elif app == 'calculator':
                subprocess.Popen(['calc'])
            elif app == 'code':
                subprocess.Popen(['code'])
            elif app == 'explorer':
                subprocess.Popen(['explorer'])
            elif app == 'cmd':
                subprocess.Popen(['cmd'])
            elif app == 'powershell':
                subprocess.Popen(['powershell'])
            else:
                subprocess.Popen(['start', app], shell=True)
            
            return True
        except:
            return False

    def launch_mac_app(self, app):
        """Launch application on macOS"""
        try:
            app_map = {
                'chrome': 'Google Chrome',
                'firefox': 'Firefox',
                'notepad': 'TextEdit',
                'calculator': 'Calculator',
                'code': 'Visual Studio Code',
                'explorer': 'Finder'
            }
            
            app_name = app_map.get(app, app)
            subprocess.Popen(['open', '-a', app_name])
            return True
        except:
            return False

    def open_url(self, url):
        """Open a URL using the most appropriate installed browser.

        Preference order (where applicable):
          - Chrome Canary
          - Google Chrome
          - Chromium
          - Brave
          - Microsoft Edge
          - Firefox
          - Safari (macOS)
          - system default
        """
        try:
            system = self.system

            candidates = []
            if system == 'darwin':
                candidates = [
                    'Google Chrome Canary',
                    'Google Chrome',
                    'Chromium',
                    'Brave Browser',
                    'Microsoft Edge',
                    'Firefox',
                    'Safari'
                ]
                for app_name in candidates:
                    # Check for app bundle presence
                    app_path = f'/Applications/{app_name}.app'
                    if os.path.exists(app_path):
                        subprocess.Popen(['open', '-a', app_name, url])
                        return {'success': True, 'message': f'Opened {url} in {app_name}'}

            elif system == 'windows':
                # Windows detection: check program files common locations
                possible = [
                    (r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe", 'chrome'),
                    (r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", 'chrome'),
                    (r"C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe", 'brave'),
                    (r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe", 'edge'),
                    (r"C:\\Program Files\\Mozilla Firefox\\firefox.exe", 'firefox')
                ]
                for path, name in possible:
                    if os.path.exists(path):
                        subprocess.Popen([path, url], shell=False)
                        return {'success': True, 'message': f'Opened {url} in {name}'}

            else:
                # Linux: check common executables
                possible_execs = ['google-chrome-unstable', 'google-chrome-stable', 'google-chrome', 'chromium-browser', 'chromium', 'brave-browser', 'brave', 'microsoft-edge', 'firefox']
                for exe in possible_execs:
                    try:
                        res = subprocess.run(['which', exe], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        if res.returncode == 0 and res.stdout.strip():
                            subprocess.Popen([exe, url])
                            return {'success': True, 'message': f'Opened {url} in {exe}'}
                    except Exception:
                        continue

            # Fallback to system default
            webbrowser.open(url, new=2)
            return {'success': True, 'message': f'Opened {url} in default browser'}

        except Exception as e:
            return {'success': False, 'message': f'Failed to open URL: {str(e)}'}

    def handle_create_web_project(self, command):
        """Scaffold a simple web project folder with basic files and open it in VS Code.

        The method will attempt to use the local Ollama AI (via `OllamaClient`) to generate file contents.
        If Ollama isn't available, it falls back to conservative boilerplate templates.
        """
        try:
            # Parse a project name and requested framework if provided, e.g. "create web mysite react" -> mysite, react
            parts = command.split()
            name = None
            requested_framework = None
            framework_keywords = {
                'vite': ['vite'],
                'react': ['react'],
                'next': ['next', 'nextjs', 'next.js']
            }

            if 'create' in parts:
                try:
                    idx = parts.index('create')
                    candidate = parts[idx+1:]
                    if candidate and candidate[0] in ('web', 'website'):
                        candidate = candidate[1:]
                    # detect framework keywords at the end
                    if candidate:
                        # look for framework mention
                        for fmt, keys in framework_keywords.items():
                            for k in keys:
                                if k in candidate:
                                    requested_framework = fmt
                                    # remove the framework token from name parts
                                    candidate = [c for c in candidate if c != k]
                                    break
                            if requested_framework:
                                break
                        if candidate:
                            name = '_'.join(candidate)
                except Exception:
                    name = None

            if not name:
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                name = f'web_project_{timestamp}'

            project_dir = os.path.join(os.getcwd(), name)
            os.makedirs(project_dir, exist_ok=True)

            # Prepare file map for different project types
            files = {}

            # Try AI generation via OllamaClient if present
            oc = None
            try:
                from ollama_client import OllamaClient
                oc = OllamaClient()
            except Exception:
                oc = None

            def ai_or_fallback(prompt, fallback):
                try:
                    if oc:
                        return oc.get_response(prompt, 'en')
                except Exception:
                    pass
                return fallback

            # Determine scaffolding type
            project_type = 'static'
            if requested_framework == 'vite' or requested_framework == 'react':
                project_type = 'vite-react'
            elif requested_framework == 'next':
                project_type = 'nextjs'

            if project_type == 'vite-react':
                # Vite + React minimal structure
                files['package.json'] = ai_or_fallback(
                    f"Generate a minimal package.json for a Vite + React project named {name} with scripts: dev, build, preview.",
                    '{\n  "name": "' + name + '",\n  "version": "0.0.1",\n  "private": true,\n  "scripts": {\n    "dev": "vite",\n    "build": "vite build",\n    "preview": "vite preview"\n  },\n  "dependencies": {\n    "react": "^18.0.0",\n    "react-dom": "^18.0.0"\n  },\n  "devDependencies": {\n    "vite": "^4.0.0"\n  }\n}'
                )

                files['index.html'] = ai_or_fallback(
                    f"Generate a minimal Vite index.html that mounts a React app from /src/main.jsx for project {name}.",
                    f"<!doctype html>\n<html>\n  <head>\n    <meta charset=\"utf-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>{name}</title>\n  </head>\n  <body>\n    <div id=\"root\"></div>\n    <script type=\"module\" src=\"/src/main.jsx\"></script>\n  </body>\n</html>"
                )

                files[os.path.join('src', 'main.jsx')] = ai_or_fallback(
                    f"Generate a minimal src/main.jsx for a Vite + React project that renders App into #root.",
                    "import React from 'react'\nimport { createRoot } from 'react-dom/client'\nimport App from './App'\nimport './index.css'\n\ncreateRoot(document.getElementById('root')).render(React.createElement(App))\n"
                )

                files[os.path.join('src', 'App.jsx')] = ai_or_fallback(
                    f"Generate a minimal React App component that shows a header and a button that alerts on click for project {name}.",
                    "import React from 'react'\n\nexport default function App(){\n  return (\n    <main style={{display:'flex',height:'100vh',alignItems:'center',justifyContent:'center',flexDirection:'column'}}>\n      <h1>'" + name + "'</h1>\n      <button onClick={() => alert('Hello from " + name + "')}>Click me</button>\n    </main>\n  )\n}\n"
                )

                files[os.path.join('src', 'index.css')] = ai_or_fallback(
                    f"Generate a small index.css for a clean modern look for project {name}.",
                    ":root{--bg:#f7f7f7;--accent:#0077ff}\nhtml,body,#root{height:100%}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial;background:var(--bg)}\nbutton{background:var(--accent);color:#fff;padding:8px 12px;border-radius:6px;border:none;cursor:pointer}"
                )

                files['README.md'] = ai_or_fallback(
                    f"Generate a short README for a Vite + React project named {name} with instructions to run dev.",
                    f"# {name}\n\nVite + React scaffolded by Wolf assistant.\n\nInstall dependencies:\n\n```\nnpm install\n```\n\nRun dev server:\n\n```\nnpm run dev\n```"
                )

            elif project_type == 'nextjs':
                # Minimal Next.js project structure
                files['package.json'] = ai_or_fallback(
                    f"Generate a minimal package.json for a Next.js project named {name} with scripts: dev, build, start.",
                    '{\n  "name": "' + name + '",\n  "version": "0.1.0",\n  "private": true,\n  "scripts": {\n    "dev": "next dev",\n    "build": "next build",\n    "start": "next start"\n  },\n  "dependencies": {\n    "next": "^14.0.0",\n    "react": "^18.0.0",\n    "react-dom": "^18.0.0"\n  }\n}'
                )

                files[os.path.join('pages', '_app.js')] = ai_or_fallback(
                    f"Generate pages/_app.js for Next.js that includes global styles for project {name}.",
                    "import '../styles/globals.css'\n\nexport default function MyApp({ Component, pageProps }){\n  return <Component {...pageProps} />\n}\n"
                )

                files[os.path.join('pages', 'index.js')] = ai_or_fallback(
                    f"Generate pages/index.js for Next.js that shows a welcome message for {name}.",
                    "export default function Home(){\n  return (<main style={{padding:40}}>\n    <h1>Welcome to " + name + "</h1>\n    <p>Scaffolded by Wolf assistant.</p>\n  </main>)\n}\n"
                )

                files[os.path.join('styles', 'globals.css')] = ai_or_fallback(
                    f"Generate globals.css for Next.js minimal styling for project {name}.",
                    "html,body{padding:0;margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial}main{max-width:960px;margin:40px auto}"
                )

                files['README.md'] = ai_or_fallback(
                    f"Generate a short README for a Next.js project named {name} with instructions to run dev.",
                    f"# {name}\n\nNext.js scaffolded by Wolf assistant.\n\nInstall dependencies:\n\n```\nnpm install\n```\n\nRun dev server:\n\n```\nnpm run dev\n```"
                )

            else:
                # Static fallback (original behavior)
                files['index.html'] = ai_or_fallback(
                    f"Generate a minimal responsive index.html for a website called {name} that links to styles.css and app.js and has a header and main content area.",
                    f"<!doctype html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n  <title>{name}</title>\n  <link rel=\"stylesheet\" href=\"styles.css\">\n</head>\n<body>\n  <header>\n    <h1>{name}</h1>\n  </header>\n  <main>\n    <p>Welcome to {name} — generated by Wolf assistant.</p>\n    <button id=\"sampleBtn\">Click me</button>\n  </main>\n  <script src=\"app.js\"></script>\n</body>\n</html>"
                )
                files['styles.css'] = ai_or_fallback(
                    f"Generate a minimal styles.css for a website called {name} with a modern clean look.",
                    "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; margin:0; padding:0; display:flex; align-items:center; justify-content:center; height:100vh; background:#f7f7f7; } header{position:absolute; top:16px; left:16px;} main{max-width:800px; text-align:center;} #sampleBtn{padding:10px 16px; border-radius:6px; background:#0077ff; color:#fff; border:none; cursor:pointer;}"
                )
                files['app.js'] = ai_or_fallback(
                    f"Generate a minimal app.js that adds a DOMContentLoaded listener and a sample interactive button.",
                    "document.addEventListener('DOMContentLoaded', () => { const btn = document.getElementById('sampleBtn'); if(btn){ btn.addEventListener('click', ()=> alert('Hello from your new project!')); } });"
                )
                files['README.md'] = ai_or_fallback(
                    f"Generate a short README for the project {name} with instructions to run locally.",
                    f"# {name}\n\nThis project was scaffolded by Wolf AI Assistant. Open index.html in your browser to view."
                )
                files['package.json'] = ai_or_fallback(
                    f"Generate a minimal package.json for a static web project named {name}.",
                    '{\n  "name": "' + name + '",\n  "version": "1.0.0",\n  "private": true\n}'
                )

            # Write all files to disk, creating subdirectories as needed
            for rel_path, content in files.items():
                full_path = os.path.join(project_dir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content or '')

            # Try to open in VS Code
            try:
                res = subprocess.run(['code', project_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if res.returncode != 0:
                    if self.system == 'darwin':
                        subprocess.Popen(['open', '-a', 'Visual Studio Code', project_dir])
            except Exception:
                try:
                    if self.system == 'darwin':
                        subprocess.Popen(['open', project_dir])
                    else:
                        webbrowser.open('file://' + project_dir)
                except Exception:
                    pass

            return {
                'success': True,
                'message': f'Project {name} created at {project_dir} (type: {project_type})',
                'path': project_dir,
                'project_type': project_type
            }

        except Exception as e:
            return {'success': False, 'message': f'Failed to create project: {str(e)}'}

    def launch_linux_app(self, app):
        """Launch application on Linux"""
        try:
            if app == 'chrome':
                subprocess.Popen(['google-chrome'])
            elif app == 'firefox':
                subprocess.Popen(['firefox'])
            elif app == 'notepad':
                subprocess.Popen(['gedit'])
            elif app == 'calculator':
                subprocess.Popen(['gnome-calculator'])
            elif app == 'code':
                subprocess.Popen(['code'])
            elif app == 'explorer':
                subprocess.Popen(['nautilus'])
            else:
                subprocess.Popen([app])
            
            return True
        except:
            return False

    def handle_window_management(self, command):
        """Handle window management commands"""
        if not GUI_AVAILABLE:
            return {
                'success': False,
                'message': "Window management requires GUI access (not available in this environment)"
            }
        
        try:
            if 'close' in command:
                pyautogui.hotkey('alt', 'f4')
                return {
                    'success': True,
                    'message': "Closed the current window"
                }
            elif 'minimize' in command:
                pyautogui.hotkey('win', 'down')
                return {
                    'success': True,
                    'message': "Minimized the current window"
                }
            elif 'maximize' in command:
                pyautogui.hotkey('win', 'up')
                return {
                    'success': True,
                    'message': "Maximized the current window"
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Window management error: {str(e)}"
            }

    def handle_volume_control(self, command):
        """Handle volume control commands"""
        if not GUI_AVAILABLE:
            return {
                'success': False,
                'message': "Volume control requires GUI access (not available in this environment)"
            }
        
        try:
            if any(word in command for word in ['up', 'increase', 'raise']):
                for _ in range(5):  # Increase volume by ~10%
                    pyautogui.press('volumeup')
                return {
                    'success': True,
                    'message': "Volume increased"
                }
            elif any(word in command for word in ['down', 'decrease', 'lower']):
                for _ in range(5):  # Decrease volume by ~10%
                    pyautogui.press('volumedown')
                return {
                    'success': True,
                    'message': "Volume decreased"
                }
            elif any(word in command for word in ['mute', 'silent']):
                pyautogui.press('volumemute')
                return {
                    'success': True,
                    'message': "Volume muted/unmuted"
                }
            else:
                return {
                    'success': False,
                    'message': "Volume command not recognized. Try 'volume up', 'volume down', or 'mute volume'"
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Volume control error: {str(e)}"
            }

    def take_screenshot(self, region=None, filename=None):
        """Take a screenshot and save it to disk.

        Args:
            region (tuple|None): (left, top, width, height) or None for full screen
            filename (str|None): desired filename (defaults to screenshot_<timestamp>.png)

        Returns:
            dict: {success: bool, message: str, filepath?: str, type?: 'screenshot'}
        """
        if not GUI_AVAILABLE:
            return {
                'success': False,
                'message': "Screenshot functionality requires GUI access (not available in this environment)"
            }

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if not filename:
                filename = f'screenshot_{timestamp}.png'
            filepath = os.path.join(os.getcwd(), filename)

            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()

            screenshot.save(filepath)

            return {
                'success': True,
                'message': f'Screenshot saved as {filename}',
                'filepath': filepath,
                'type': 'screenshot'
            }

        except Exception as e:
            return {'success': False, 'message': f'Error taking screenshot: {str(e)}'}
            
    def scan_screen(self, region=None, ocr=True):
        """
        Scan the screen content and optionally perform OCR
        
        Args:
            region (tuple, optional): (left, top, width, height) of the region to scan.
                                    If None, scans the entire screen.
            ocr (bool): Whether to perform OCR on the captured image
            
        Returns:
            dict: Result with success status, extracted text, and screenshot info
        """
        if not GUI_AVAILABLE:
            return {'success': False, 'message': 'Screen scanning requires pyautogui'}
            
        try:
            # First take a screenshot
            result = self.take_screenshot(region)
            if not result['success']:
                return result
                
            response = {
                'success': True,
                'message': 'Screen scanned successfully',
                'screenshot_path': result['filepath'],
                'type': 'screen_scan'
            }
            
            # If OCR is enabled, extract text from the screenshot
            if ocr:
                try:
                    # Use pytesseract to extract text
                    text = pytesseract.image_to_string(Image.open(result['filepath']))
                    if text.strip():
                        response['extracted_text'] = text.strip()
                        response['message'] = 'Text extracted from screen'
                    else:
                        response['extracted_text'] = ''
                        response['message'] = 'No text detected on screen'
                except Exception as e:
                    response['message'] = f'Screen captured but could not extract text: {str(e)}'
                    response['extracted_text'] = ''
            
            return response
            
        except Exception as e:
            return {'success': False, 'message': f'Error scanning screen: {str(e)}'}
            
    def get_active_window_info(self):
        """
        Get information about the currently active window
        
        Returns:
            dict: Information about the active window
        """
        if not GUI_AVAILABLE:
            return {'success': False, 'message': 'Window info requires pygetwindow'}
            
        try:
            window = gw.getActiveWindow()
            if not window:
                return {'success': False, 'message': 'No active window found'}
                
            return {
                'success': True,
                'window_title': window.title,
                'window_rect': {
                    'left': window.left,
                    'top': window.top,
                    'width': window.width,
                    'height': window.height
                },
                'is_maximized': window.isMaximized,
                'is_minimized': window.isMinimized,
                'is_active': window.isActive
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error getting window info: {str(e)}'}

    def handle_system_control(self, command):
        """Handle system control commands (with safety confirmation)"""
        # These commands are potentially dangerous, so we'll just return what would happen
        if 'shutdown' in command:
            return {
                'success': True,
                'message': "System shutdown command received. For safety, actual shutdown is disabled in this demo."
            }
        elif 'restart' in command:
            return {
                'success': True,
                'message': "System restart command received. For safety, actual restart is disabled in this demo."
            }
        elif any(word in command for word in ['sleep', 'hibernate']):
            return {
                'success': True,
                'message': "System sleep command received. For safety, actual sleep is disabled in this demo."
            }

    def create_contact_form(self):
        """Create a basic HTML contact form"""
        try:
            # Create a basic HTML contact form
            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact Form</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"],
        input[type="email"],
        textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        textarea {
            height: 120px;
            resize: vertical;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <h1>Contact Us</h1>
    <form action="/submit" method="POST">
        <div class="form-group">
            <label for="name">Name:</label>
            <input type="text" id="name" name="name" required>
        </div>
        
        <div class="form-group">
            <label for="email">Email:</label>
            <input type="email" id="email" name="email" required>
        </div>
        
        <div class="form-group">
            <label for="subject">Subject:</label>
            <input type="text" id="subject" name="subject" required>
        </div>
        
        <div class="form-group">
            <label for="message">Message:</label>
            <textarea id="message" name="message" required></textarea>
        </div>
        
        <button type="submit">Send Message</button>
    </form>
</body>
</html>"""

            # Create the contact form file
            os.makedirs('contact_forms', exist_ok=True)
            file_path = os.path.join('contact_forms', 'contact_form.html')
            
            with open(file_path, 'w') as f:
                f.write(html_content)
            
            # Open the file in the default browser
            webbrowser.open(f'file://{os.path.abspath(file_path)}')
            
            # Try to open in VS Code if available
            try:
                if platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', '-a', 'Visual Studio Code', os.path.abspath(file_path)])
                elif platform.system() == 'Windows':
                    subprocess.run(['code', os.path.abspath(file_path)], shell=True)
                elif platform.system() == 'Linux':
                    subprocess.run(['code', os.path.abspath(file_path)])
            except Exception as e:
                print(f"Could not open VS Code: {e}")
            
            return {
                'success': True,
                'message': 'Created a basic contact form and opened it in your browser and VS Code.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating contact form: {str(e)}'
            }
    
    def get_time_date(self):
        """Get current time and date"""
        try:
            now = datetime.now()
            return {
                'success': True,
                'message': f"Current time is {now.strftime('%I:%M %p')} and the date is {now.strftime('%A, %B %d, %Y')}"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Time/date error: {str(e)}"
            }
            
    def execute_ai_task(self, task_description):
        """Execute a general task using AI"""
        if not self.ai_enabled:
            return {
                'success': False,
                'message': 'AI features are not enabled. Please set OPENAI_API_KEY in config.py'
            }
            
        try:
            # First, determine if this is a programming task
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that helps with general tasks and programming. "
                                                "Determine if the following task is a programming task that requires code execution. "
                                                "Respond with JSON: {\"is_programming\": boolean, \"language\": string or null}"},
                    {"role": "user", "content": task_description}
                ],
                temperature=0.3
            )
            
            try:
                task_info = json.loads(response.choices[0].message['content'])
                is_programming = task_info.get('is_programming', False)
                language = task_info.get('language')
            except (json.JSONDecodeError, KeyError):
                is_programming = False
                language = None
            
            if is_programming and language:
                return self._handle_programming_task(task_description, language)
            else:
                return self._handle_general_task(task_description)
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error executing AI task: {str(e)}'
            }
    
    def _handle_programming_task(self, task_description, language):
        """Handle programming tasks by generating and executing code"""
        try:
            # Get code from AI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are a {language} programming assistant. Generate code to complete the task. "
                                                "Include the code in a markdown code block. Only provide the code, no explanations."},
                    {"role": "user", "content": task_description}
                ],
                temperature=0.3
            )
            
            # Extract code from markdown code block
            code = response.choices[0].message['content']
            code = re.sub(r'```(?:\w+)?\s*', '', code).strip('` ')
            
            # Save to a temporary file
            ext = {
                'python': 'py',
                'javascript': 'js',
                'html': 'html',
                'css': 'css',
                'bash': 'sh'
            }.get(language.lower(), 'txt')
            
            os.makedirs('ai_tasks', exist_ok=True)
            timestamp = int(time.time())
            filename = f"ai_tasks/task_{timestamp}.{ext}"
            
            with open(filename, 'w') as f:
                f.write(code)
            
            # Execute the code if it's a script
            if ext in ['py', 'js', 'sh']:
                try:
                    if ext == 'py':
                        result = subprocess.run(
                            [sys.executable, filename],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                    elif ext == 'js':
                        result = subprocess.run(
                            ['node', filename],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                    else:  # sh
                        result = subprocess.run(
                            ['bash', filename],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                    
                    output = f"Task completed. Output:\n{result.stdout}"
                    if result.stderr:
                        output += f"\nErrors:\n{result.stderr}"
                    
                    return {
                        'success': True,
                        'message': output,
                        'file': os.path.abspath(filename)
                    }
                    
                except subprocess.TimeoutExpired:
                    return {
                        'success': False,
                        'message': 'Task timed out after 30 seconds',
                        'file': os.path.abspath(filename)
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'message': f'Error executing code: {str(e)}',
                        'file': os.path.abspath(filename)
                    }
            else:
                # For non-executable files, just return the file path
                return {
                    'success': True,
                    'message': f'Task completed. File saved to: {os.path.abspath(filename)}',
                    'file': os.path.abspath(filename)
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error handling programming task: {str(e)}'
            }
    
    def _handle_general_task(self, task_description):
        """Handle general non-programming tasks using AI"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that helps with general tasks. "
                                                "Provide a clear, concise, and helpful response to the user's request."},
                    {"role": "user", "content": task_description}
                ],
                temperature=0.7
            )
            
            return {
                'success': True,
                'message': response.choices[0].message['content']
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error processing general task: {str(e)}'
            }
            
    def move_mouse_to_coordinates(self, x, y, duration=0.25):
        """Move mouse to specified X, Y coordinates"""
        if not GUI_AVAILABLE:
            return {'success': False, 'message': 'GUI control (pyautogui) is not available.'}
        try:
            pyautogui.moveTo(int(x), int(y), duration=float(duration))
            result = {'success': True, 'message': f'Mouse moved to ({x}, {y})'}
            return result

        except Exception as e:
            result = {'success': False, 'message': f'Error moving mouse: {str(e)}'}
            return result
            
        finally:
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Add to command history
            if 'result' in locals():
                self.command_history.add(command, result)
                
                # Show visual feedback for completion
                status = '✓' if result.get('success', False) else '✗'
                self._show_visual_feedback(
                    f"{status} {result.get('message', 'Command completed')} ({execution_time:.1f}s)",
                    duration=3
                )
            else:
                self.command_history.add(command, {'success': False, 'message': 'Command execution failed'})
                self._show_visual_feedback(
                    f"⚠ Command completed in {execution_time:.1f}s",
                    duration=3
                )

    def click_mouse_button(self, x=None, y=None, button='left', clicks=1, interval=0.1, command=None):
        """Click mouse button at specified X, Y coordinates or current position
        
        Args:
            x (int, optional): X coordinate. If None, uses current position.
            y (int, optional): Y coordinate. If None, uses current position.
            button (str): Mouse button to click ('left', 'right', 'middle').
            clicks (int): Number of clicks to perform.
            interval (float): Time between clicks in seconds.
            command (str, optional): Optional command string for error reporting.
            
        Returns:
            dict: Result of the operation with success status and details.
        """
        if not GUI_AVAILABLE:
            return {'success': False, 'message': 'GUI control (pyautogui) is not available.'}
            
        try:
            if x is not None and y is not None:
                pyautogui.click(int(x), int(y), button=button.lower(), 
                             clicks=int(clicks), interval=float(interval))
            else:
                pyautogui.click(button=button.lower(), 
                             clicks=int(clicks), interval=float(interval))
            return {
                'success': True,
                'message': f'{button.title()} click performed',
                'type': 'mouse_click',
                'details': {
                    'x': x,
                    'y': y,
                    'button': button,
                    'clicks': clicks,
                    'interval': interval
                }
            }

        except Exception as e:
            import traceback
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'command': command,
                'traceback': traceback.format_exc(),
                'system': platform.system(),
                'python_version': sys.version
            }
            
            # Add more context for common errors
            if 'No such file or directory' in str(e):
                error_details['suggestion'] = 'The specified path does not exist. Check the path and try again.'
            elif 'Permission denied' in str(e):
                error_details['suggestion'] = 'Permission denied. Try running with elevated privileges.'
            
            return {
                'success': False,
                'message': f'Error executing command: {str(e)}',
                'type': 'execution_error',
                'details': error_details
            }

    def type_keyboard_input(self, text_to_type, interval=0.01):
        """Type the given text using the keyboard"""
        if not GUI_AVAILABLE:
            return {'success': False, 'message': 'GUI control (pyautogui) is not available.'}
        try:
            pyautogui.typewrite(text_to_type, interval=float(interval))
            return {'success': True, 'message': f'Typed: {text_to_type}'}
        except Exception as e:
            return {'success': False, 'message': f'Error typing: {str(e)}'}

    def press_special_keys(self, keys):
        """Press special keys or a sequence of keys (hotkey)"""
        if not GUI_AVAILABLE:
            return {'success': False, 'message': 'GUI control (pyautogui) is not available.'}
        try:
            if isinstance(keys, list):
                pyautogui.hotkey(*keys)
                action = f'Pressed hotkey: {" + ".join(keys)}'
            else:
                pyautogui.press(keys)
                action = f'Pressed key: {keys}'
            return {'success': True, 'message': action}
        except Exception as e:
            return {'success': False, 'message': f'Error pressing keys: {str(e)}'}

    def handle_media_control(self, command):
        """Handle media control commands"""
        if not GUI_AVAILABLE:
            return {
                'success': False,
                'message': "Media control requires GUI access (not available in this environment)"
            }
        
        try:
            if 'play' in command or 'pause' in command:
                pyautogui.press('playpause')
                return {
                    'success': True,
                    'message': "Media play/pause toggled"
                }
            elif 'next' in command:
                pyautogui.press('nexttrack')
                return {
                    'success': True,
                    'message': "Skipped to next track"
                }
            elif 'previous' in command:
                pyautogui.press('prevtrack')
                return {
                    'success': True,
                    'message': "Went to previous track"
                }
            elif 'stop' in command:
                pyautogui.press('stop')
                return {
                    'success': True,
                    'message': "Media stopped"
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Media control error: {str(e)}"
            }

# Test the controller
if __name__ == "__main__":
    controller = PCController()
    
    test_commands = [
        "open chrome",
        "take a screenshot", 
        "what time is it",
        "increase volume",
        "close window"
    ]
    
    for cmd in test_commands:
        print(f"\nTesting: {cmd}")
        result = controller.execute_command(cmd)
        print(f"Result: {result}")
