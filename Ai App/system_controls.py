"""
System Controls Module

This module provides enhanced system control functionalities for the AI Assistant.
It includes features for process management, system monitoring, and automation.
"""

import os
import sys
import time
import ctypes
import psutil
import platform
import subprocess
import shutil
from typing import Dict, List, Optional, Union, Tuple
from pathlib import Path
import pyautogui
import pygetwindow as gw
from PIL import ImageGrab, Image
import pytesseract

class SystemControls:
    """Class for managing system controls and automation."""
    
    def __init__(self):
        """Initialize system controls with platform-specific settings."""
        self.platform = platform.system().lower()
        self.is_admin = self._check_admin()
        self.screen_width, self.screen_height = pyautogui.size()
        
    def _check_admin(self) -> bool:
        """Check if the script is running with administrator/root privileges."""
        try:
            if self.platform == 'windows':
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception:
            return False
    
    # Process Management
    def list_processes(self) -> List[Dict]:
        """Get a list of all running processes with details."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_percent']):
            try:
                process_info = proc.info
                processes.append({
                    'pid': process_info['pid'],
                    'name': process_info['name'],
                    'username': process_info['username'],
                    'status': process_info['status'],
                    'cpu_percent': process_info['cpu_percent'],
                    'memory_percent': process_info['memory_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return processes
    
    def kill_process(self, pid: int) -> Dict:
        """Terminate a process by PID."""
        try:
            process = psutil.Process(pid)
            process.terminate()
            return {'success': True, 'message': f'Process {pid} terminated'}
        except psutil.NoSuchProcess:
            return {'success': False, 'error': f'No such process: {pid}'}
        except psutil.AccessDenied:
            return {'success': False, 'error': f'Access denied when trying to terminate process {pid}'}
    
    def start_process(self, command: str, args: List[str] = None, wait: bool = False) -> Dict:
        """Start a new process."""
        try:
            args = args or []
            if wait:
                result = subprocess.run(
                    [command] + args,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return {
                    'success': True,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }
            else:
                subprocess.Popen(
                    [command] + args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    start_new_session=True
                )
                return {'success': True, 'message': 'Process started in background'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # System Information
    def get_system_info(self) -> Dict:
        """Get detailed system information."""
        try:
            # CPU Information
            cpu_info = {
                'cores': psutil.cpu_count(logical=False),
                'logical_cores': psutil.cpu_count(),
                'usage_percent': psutil.cpu_percent(interval=1),
                'per_cpu_percent': psutil.cpu_percent(interval=1, percpu=True),
                'freq': psutil.cpu_freq()._asdict() if hasattr(psutil, 'cpu_freq') else {}
            }
            
            # Memory Information
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            memory_info = {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'free': mem.free,
                'percent': mem.percent,
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percent': swap.percent
                }
            }
            
            # Disk Information
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'opts': partition.opts,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    })
                except Exception:
                    continue
            
            # Network Information
            net_io = psutil.net_io_counters()
            net_info = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'interfaces': []
            }
            
            for name, addrs in psutil.net_if_addrs().items():
                interface = {'name': name, 'addresses': []}
                for addr in addrs:
                    interface['addresses'].append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    })
                net_info['interfaces'].append(interface)
            
            # System Info
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            system_info = {
                'platform': platform.platform(),
                'system': platform.system(),
                'node': platform.node(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'boot_time': boot_time,
                'uptime': uptime,
                'users': [user._asdict() for user in psutil.users()],
                'cpu': cpu_info,
                'memory': memory_info,
                'disks': partitions,
                'network': net_info
            }
            
            return {'success': True, 'data': system_info}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # System Controls
    def shutdown(self, force: bool = False, timer: int = 0) -> Dict:
        """Shut down the system."""
        try:
            if timer > 0:
                time.sleep(timer)
                
            if self.platform == 'windows':
                if force:
                    os.system('shutdown /s /f /t 0')
                else:
                    os.system('shutdown /s /t 0')
            elif self.platform == 'darwin':  # macOS
                if force:
                    os.system('shutdown -h now')
                else:
                    os.system('osascript -e \'tell app "System Events" to shut down\'')
            else:  # Linux/Unix
                if force:
                    os.system('shutdown -h now')
                else:
                    os.system('shutdown -h +1')
            
            return {'success': True, 'message': 'System is shutting down'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def restart(self, force: bool = False) -> Dict:
        """Restart the system."""
        try:
            if self.platform == 'windows':
                if force:
                    os.system('shutdown /r /f /t 0')
                else:
                    os.system('shutdown /r /t 0')
            elif self.platform == 'darwin':  # macOS
                if force:
                    os.system('shutdown -r now')
                else:
                    os.system('osascript -e \'tell app "System Events" to restart\'')
            else:  # Linux/Unix
                if force:
                    os.system('reboot -f')
                else:
                    os.system('reboot')
            
            return {'success': True, 'message': 'System is restarting'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sleep_mode(self) -> Dict:
        """Put the system to sleep."""
        try:
            if self.platform == 'windows':
                os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
            elif self.platform == 'darwin':  # macOS
                os.system('pmset sleepnow')
            else:  # Linux/Unix
                os.system('systemctl suspend')
            
            return {'success': True, 'message': 'System is going to sleep'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # File Operations
    def find_files(self, pattern: str, path: str = None) -> Dict:
        """Find files matching a pattern."""
        try:
            path = path or os.path.expanduser('~')
            found = []
            
            for root, _, files in os.walk(path):
                for file in files:
                    if pattern.lower() in file.lower():
                        file_path = os.path.join(root, file)
                        try:
                            stat = os.stat(file_path)
                            found.append({
                                'path': file_path,
                                'size': stat.st_size,
                                'modified': stat.st_mtime,
                                'is_dir': False
                            })
                        except (OSError, PermissionError):
                            continue
            
            return {'success': True, 'files': found}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def search_file_content(self, search_term: str, path: str = None, file_pattern: str = '*.txt') -> Dict:
        """Search for text in files."""
        try:
            path = path or os.path.expanduser('~')
            matches = []
            
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(file_pattern.lower().lstrip('*.')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                for line_num, line in enumerate(f, 1):
                                    if search_term.lower() in line.lower():
                                        matches.append({
                                            'file': file_path,
                                            'line': line_num,
                                            'content': line.strip()
                                        })
                        except (OSError, PermissionError, UnicodeDecodeError):
                            continue
            
            return {'success': True, 'matches': matches}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Automation
    def take_screenshot(self, save_path: str = None, region: tuple = None) -> Dict:
        """Take a screenshot of the screen or a region."""
        try:
            if region:
                screenshot = ImageGrab.grab(bbox=region)
            else:
                screenshot = ImageGrab.grab()
            
            if save_path:
                screenshot.save(save_path)
            
            return {
                'success': True,
                'size': screenshot.size,
                'mode': screenshot.mode,
                'path': save_path or 'in-memory',
                'format': save_path.split('.')[-1].lower() if save_path else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def ocr_screen(self, region: tuple = None, language: str = 'eng') -> Dict:
        """Extract text from the screen using OCR."""
        try:
            screenshot = ImageGrab.grab(bbox=region) if region else ImageGrab.grab()
            text = pytesseract.image_to_string(screenshot, lang=language)
            
            return {
                'success': True,
                'text': text.strip(),
                'language': language,
                'region': region
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_active_window(self) -> Dict:
        """Get information about the currently active window."""
        try:
            window = gw.getActiveWindow()
            if window:
                return {
                    'success': True,
                    'title': window.title,
                    'size': window.size,
                    'position': window.topleft,
                    'is_maximized': window.isMaximized,
                    'is_minimized': window.isMinimized,
                    'is_active': window.isActive,
                    'window_id': window._hWnd if hasattr(window, '_hWnd') else None
                }
            return {'success': False, 'error': 'No active window found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_windows(self) -> Dict:
        """List all open windows."""
        try:
            windows = []
            for window in gw.getAllWindows():
                try:
                    if window.title:  # Only include windows with titles
                        windows.append({
                            'title': window.title,
                            'size': window.size,
                            'position': window.topleft,
                            'is_visible': window.visible,
                            'is_active': window.isActive
                        })
                except Exception:
                    continue
            
            return {'success': True, 'windows': windows}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def switch_to_window(self, title: str) -> Dict:
        """Switch to a window by title."""
        try:
            window = gw.getWindowsWithTitle(title)
            if window:
                window[0].activate()
                return {'success': True, 'message': f'Switched to window: {title}'}
            return {'success': False, 'error': f'Window not found: {title}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Example usage
if __name__ == "__main__":
    system = SystemControls()
    
    # Example: Get system info
    print("System Info:", json.dumps(system.get_system_info(), indent=2))
    
    # Example: List processes
    print("Processes:", json.dumps(system.list_processes()[:5], indent=2))  # First 5 processes
    
    # Example: Take a screenshot
    print("Screenshot:", json.dumps(system.take_screenshot('screenshot.png'), indent=2))
    
    # Example: Get active window
    print("Active Window:", json.dumps(system.get_active_window(), indent=2))
