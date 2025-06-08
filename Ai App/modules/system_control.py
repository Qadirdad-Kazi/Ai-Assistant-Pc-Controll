"""
System Control Module for Wolf AI Voice Assistant
Handles all system-level operations including app control, system commands, and hardware interactions.
"""

import os
import sys
import platform
import subprocess
import psutil
import pyautogui
import pygetwindow as gw
from typing import Dict, Any, List, Optional
import time

class SystemController:
    """
    Handles system-level operations like controlling applications, system commands,
    and hardware interactions.
    """
    
    def __init__(self):
        """Initialize the system controller with default settings."""
        self.os_name = platform.system().lower()
        self.app_aliases = self._load_app_aliases()
        self.setup_pyautogui()
    
    def setup_pyautogui(self):
        """Configure pyautogui fail-safes and settings."""
        pyautogui.FAIL_SAFE = True
        pyautogui.PAUSE = 0.1
    
    def _load_app_aliases(self) -> Dict[str, List[str]]:
        """Load application aliases for different operating systems."""
        common_aliases = {
            'chrome': ['chrome', 'google chrome', 'browser'],
            'firefox': ['firefox', 'mozilla'],
            'safari': ['safari'],
            'code': ['code', 'vs code', 'visual studio code'],
            'notepad': ['notepad', 'text editor', 'notes'],
            'terminal': ['terminal', 'command prompt', 'cmd', 'powershell'],
            'spotify': ['spotify', 'music'],
            'outlook': ['outlook', 'email', 'mail'],
            'word': ['word', 'microsoft word'],
            'excel': ['excel', 'microsoft excel'],
            'powerpoint': ['powerpoint', 'microsoft powerpoint'],
            'calculator': ['calculator', 'calc'],
            'settings': ['settings', 'preferences'],
            'explorer': ['explorer', 'file explorer', 'files'],
            'calendar': ['calendar', 'schedule']
        }
        
        if self.os_name == 'windows':
            common_aliases.update({
                'notepad': ['notepad', 'notepad.exe'],
                'cmd': ['cmd', 'command prompt', 'command'],
                'powershell': ['powershell', 'ps'],
                'calculator': ['calculator', 'calc.exe']
            })
        elif self.os_name == 'darwin':  # macOS
            common_aliases.update({
                'terminal': ['terminal', 'iterm', 'iterm2'],
                'textedit': ['textedit', 'text editor'],
                'calculator': ['calculator', 'calc'],
                'finder': ['finder', 'files']
            })
        elif self.os_name == 'linux':
            common_aliases.update({
                'gedit': ['gedit', 'text editor'],
                'terminal': ['terminal', 'gnome-terminal', 'konsole', 'xterm'],
                'nautilus': ['nautilus', 'files'],
                'libreoffice': ['libreoffice', 'writer', 'calc', 'impress']
            })
            
        return common_aliases
    
    def open_application(self, app_name: str) -> Dict[str, Any]:
        """
        Open an application by name or alias.
        
        Args:
            app_name (str): Name or alias of the application to open
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            app_name = app_name.lower()
            app_to_open = None
            
            # Check for matches in aliases
            for app, aliases in self.app_aliases.items():
                if app_name in aliases or app_name == app:
                    app_to_open = app
                    break
            
            if not app_to_open:
                app_to_open = app_name  # Try with the provided name
            
            if self.os_name == 'windows':
                os.startfile(app_to_open)
            elif self.os_name == 'darwin':  # macOS
                subprocess.run(['open', '-a', app_to_open], check=True)
            else:  # Linux
                subprocess.run([app_to_open], check=True)
                
            return {'success': True, 'message': f'Opened {app_name}'}
        except Exception as e:
            return {'success': False, 'message': f'Failed to open {app_name}: {str(e)}'}
    
    def close_application(self, app_name: str) -> Dict[str, Any]:
        """
        Close an application by name.
        
        Args:
            app_name (str): Name of the application to close
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            app_name = app_name.lower()
            closed = False
            
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    process_name = proc.info['name'].lower()
                    if app_name in process_name or any(alias in process_name for alias in self.app_aliases.get(app_name, [])):
                        proc.terminate()
                        closed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            if closed:
                return {'success': True, 'message': f'Closed {app_name}'}
            return {'success': False, 'message': f'Application {app_name} not found'}
        except Exception as e:
            return {'success': False, 'message': f'Error closing {app_name}: {str(e)}'}
    
    def control_window(self, action: str) -> Dict[str, Any]:
        """
        Control the active window.
        
        Args:
            action (str): Action to perform (minimize, maximize, close)
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            action = action.lower()
            if action == 'minimize':
                if self.os_name == 'windows':
                    pyautogui.hotkey('win', 'down')
                elif self.os_name == 'darwin':
                    pyautogui.hotkey('command', 'm')
                else:  # Linux
                    pyautogui.hotkey('ctrl', 'super', 'down')
            elif action == 'maximize':
                if self.os_name == 'windows':
                    pyautogui.hotkey('win', 'up')
                elif self.os_name == 'darwin':
                    pyautogui.hotkey('option', 'command', 'f')
                else:  # Linux
                    pyautogui.hotkey('super', 'up')
            elif action == 'close':
                pyautogui.hotkey('alt', 'f4') if self.os_name == 'windows' else \
                pyautogui.hotkey('command', 'w') if self.os_name == 'darwin' else \
                pyautogui.hotkey('alt', 'f4')
            return {'success': True, 'message': f'Window {action}d'}
        except Exception as e:
            return {'success': False, 'message': f'Error controlling window: {str(e)}'}
    
    def system_command(self, command: str) -> Dict[str, Any]:
        """
        Execute system commands like shutdown, restart, etc.
        
        Args:
            command (str): System command to execute
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            command = command.lower()
            if 'shutdown' in command:
                if self.os_name == 'windows':
                    os.system('shutdown /s /t 1')
                else:  # macOS and Linux
                    os.system('shutdown -h now')
                return {'success': True, 'message': 'Shutting down system...'}
            
            elif 'restart' in command or 'reboot' in command:
                if self.os_name == 'windows':
                    os.system('shutdown /r /t 1')
                else:  # macOS and Linux
                    os.system('reboot')
                return {'success': True, 'message': 'Restarting system...'}
            
            elif 'sleep' in command or 'suspend' in command:
                if self.os_name == 'windows':
                    os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
                elif self.os_name == 'darwin':
                    os.system('pmset sleepnow')
                else:  # Linux
                    os.system('systemctl suspend')
                return {'success': True, 'message': 'Putting system to sleep...'}
            
            elif 'lock' in command:
                if self.os_name == 'windows':
                    import ctypes
                    ctypes.windll.user32.LockWorkStation()
                elif self.os_name == 'darwin':
                    os.system('/System/Library/CoreServices/Menu\ Extras/User.menu/Contents/Resources/CGSession -suspend')
                else:  # Linux
                    os.system('gnome-screensaver-command -l' if 'gnome' in os.getenv('XDG_CURRENT_DESKTOP', '').lower() 
                              else 'i3lock -c 000000' if 'i3' in os.getenv('XDG_CURRENT_DESKTOP', '').lower() 
                              else 'loginctl lock-session')
                return {'success': True, 'message': 'Locking system...'}
            
            elif 'log off' in command or 'logout' in command:
                if self.os_name == 'windows':
                    os.system('shutdown /l')
                elif self.os_name == 'darwin':
                    os.system('osascript -e \'tell app "System Events" to log out\'')
                else:  # Linux
                    os.system('gnome-session-quit --no-prompt' if 'gnome' in os.getenv('XDG_CURRENT_DESKTOP', '').lower() 
                              else 'i3-msg exit' if 'i3' in os.getenv('XDG_CURRENT_DESKTOP', '').lower() 
                              else 'loginctl terminate-user $USER')
                return {'success': True, 'message': 'Logging out...'}
            
            return {'success': False, 'message': 'Command not recognized'}
        except Exception as e:
            return {'success': False, 'message': f'Error executing system command: {str(e)}'}
    
    def take_screenshot(self, filename: str = None) -> Dict[str, Any]:
        """
        Take a screenshot.
        
        Args:
            filename (str, optional): Path to save the screenshot. Defaults to 'screenshot_<timestamp>.png'.
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f'screenshot_{timestamp}.png'
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            return {'success': True, 'message': f'Screenshot saved as {filename}', 'filename': filename}
        except Exception as e:
            return {'success': False, 'message': f'Error taking screenshot: {str(e)}'}
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information.
        
        Returns:
            Dict[str, Any]: System information
        """
        try:
            import platform
            import datetime
            
            # Basic system info
            system_info = {
                'system': platform.system(),
                'node': platform.node(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'boot_time': datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
                'os_name': os.name,
                'platform': platform.platform(),
                'architecture': platform.architecture(),
                'python_version': platform.python_version()
            }
            
            # CPU info
            cpu_info = {
                'physical_cores': psutil.cpu_count(logical=False),
                'total_cores': psutil.cpu_count(logical=True),
                'cpu_usage': f"{psutil.cpu_percent(interval=1)}%"
            }
            
            # Memory info
            memory = psutil.virtual_memory()
            memory_info = {
                'total': f"{memory.total / (1024 ** 3):.2f} GB",
                'available': f"{memory.available / (1024 ** 3):.2f} GB",
                'used': f"{memory.used / (1024 ** 3):.2f} GB",
                'percentage': f"{memory.percent}%"
            }
            
            # Disk info
            disk = psutil.disk_usage('/')
            disk_info = {
                'total': f"{disk.total / (1024 ** 3):.2f} GB",
                'used': f"{disk.used / (1024 ** 3):.2f} GB",
                'free': f"{disk.free / (1024 ** 3):.2f} GB",
                'percentage': f"{disk.percent}%"
            }
            
            # Network info
            net_io = psutil.net_io_counters()
            network_info = {
                'bytes_sent': f"{net_io.bytes_sent / (1024 ** 2):.2f} MB",
                'bytes_recv': f"{net_io.bytes_recv / (1024 ** 2):.2f} MB"
            }
            
            # Battery info
            battery_info = {}
            if hasattr(psutil, 'sensors_battery'):
                battery = psutil.sensors_battery()
                if battery:
                    battery_info = {
                        'percent': battery.percent,
                        'power_plugged': battery.power_plugged,
                        'time_left': f"{battery.secsleft // 3600}h {(battery.secsleft % 3600) // 60}m" if battery.secsleft > 0 else 'Unknown'
                    }
            
            return {
                'success': True,
                'system': system_info,
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'network': network_info,
                'battery': battery_info
            }
        except Exception as e:
            return {'success': False, 'message': f'Error getting system info: {str(e)}'}
    
    def control_media(self, action: str) -> Dict[str, Any]:
        """
        Control media playback.
        
        Args:
            action (str): Media action (play, pause, next, previous, volumeup, volumedown, mute)
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            action = action.lower()
            if action in ['play', 'pause']:
                pyautogui.press('playpause')
            elif action == 'next':
                pyautogui.press('nexttrack')
            elif action == 'previous':
                pyautogui.press('prevtrack')
            elif action == 'volumeup':
                pyautogui.press('volumeup')
            elif action == 'volumedown':
                pyautogui.press('volumedown')
            elif action == 'mute':
                pyautogui.press('volumemute')
            return {'success': True, 'message': f'Media {action} command executed'}
        except Exception as e:
            return {'success': False, 'message': f'Error controlling media: {str(e)}'}

# Singleton instance
system_controller = SystemController()
