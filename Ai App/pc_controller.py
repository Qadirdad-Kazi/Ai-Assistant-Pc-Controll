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
from PIL import ImageGrab, Image
import pytesseract
from config import Config

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

    def take_screenshot(self):
        """Take a screenshot"""
        if not GUI_AVAILABLE:
            return {
                'success': False,
                'message': "Screenshot functionality requires GUI access (not available in this environment)"
            }
            
            # Take screenshot
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

    def move_mouse_to_coordinates(self, x, y, duration=0.25):
        """Move mouse to specified X, Y coordinates"""
        if not GUI_AVAILABLE:
            return {'success': False, 'message': 'GUI control (pyautogui) is not available.'}
        try:
            pyautogui.moveTo(int(x), int(y), duration=float(duration))
            return {'success': True, 'message': f'Mouse moved to ({x}, {y})'}
        except Exception as e:
            return {'success': False, 'message': f'Error moving mouse: {str(e)}'}

    def click_mouse_button(self, x=None, y=None, button='left', clicks=1, interval=0.1):
        """Click mouse button at specified X, Y coordinates or current position"""
        if not GUI_AVAILABLE:
            return {'success': False, 'message': 'GUI control (pyautogui) is not available.'}
        try:
            if x is not None and y is not None:
                pyautogui.click(int(x), int(y), button=button.lower(), clicks=int(clicks), interval=float(interval))
            else:
                pyautogui.click(button=button.lower(), clicks=int(clicks), interval=float(interval))
            return {'success': True, 'message': f'{button.title()} click performed'}
        except Exception as e:
            return {'success': False, 'message': f'Error clicking mouse: {str(e)}'}

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
