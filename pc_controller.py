"""
PC Controller Module
Handles system-level commands and PC control functionality
"""

import os
import sys
import subprocess
import psutil
import pyautogui
import time
from datetime import datetime
import webbrowser
import platform
from config import Config

class PCController:
    def __init__(self):
        self.config = Config()
        self.system = platform.system().lower()
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

    def execute_command(self, command):
        """
        Execute a system command based on natural language input
        Returns dict with success status and message
        """
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
            
            # Screenshot command
            elif 'screenshot' in command_lower:
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
            return {
                'success': False,
                'message': "I couldn't identify which application to open."
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

    def take_screenshot(self):
        """Take a screenshot"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Save to desktop or current directory
            if self.system == 'windows':
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            else:
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            
            if os.path.exists(desktop):
                filepath = os.path.join(desktop, filename)
            else:
                filepath = filename
            
            screenshot.save(filepath)
            
            return {
                'success': True,
                'message': f"Screenshot saved as {filename}"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Screenshot error: {str(e)}"
            }

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

    def get_time_date(self):
        """Get current time and date"""
        try:
            now = datetime.now()
            time_str = now.strftime("%I:%M %p")
            date_str = now.strftime("%A, %B %d, %Y")
            
            return {
                'success': True,
                'message': f"Current time is {time_str} on {date_str}"
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Time/date error: {str(e)}"
            }

    def handle_media_control(self, command):
        """Handle media control commands"""
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
