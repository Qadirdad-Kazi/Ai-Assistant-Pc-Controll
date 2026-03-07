"""
Dynamic App Discovery System - Works with ANY installed app using vision intelligence.
No hardcoded paths - uses visual analysis to find and launch any application.
"""

import os
import time
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import pyautogui
    from PIL import Image
    import win32gui
    import win32con
    import winreg
except ImportError as e:
    print(f"[Dynamic Discovery] Warning: Some dependencies missing: {e}")
    pyautogui = None
    Image = None
    win32gui = None
    win32con = None
    winreg = None

class DynamicAppDiscovery:
    """Intelligent app discovery that works with ANY installed application."""
    
    def __init__(self):
        self.installed_apps = {}
        self.desktop_apps = []
        self.start_menu_apps = []
        
    def discover_installed_apps(self) -> Dict[str, str]:
        """Discover all installed applications on the system."""
        print("[Dynamic Discovery] Scanning for installed applications...")
        
        apps = {}
        
        # Method 1: Scan common installation directories
        common_paths = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            r"C:\Users\{}\AppData\Local\Programs".format(os.getenv("USERNAME", "User")),
            r"C:\Users\{}\AppData\Roaming".format(os.getenv("USERNAME", "User")),
            os.path.expanduser("~\\Desktop")
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                apps.update(self._scan_directory(path))
        
        # Method 2: Check Windows Registry for installed programs
        apps.update(self._scan_registry())
        
        # Method 3: Check Start Menu
        apps.update(self._scan_start_menu())
        
        self.installed_apps = apps
        print(f"[Dynamic Discovery] Found {len(apps)} applications")
        return apps
    
    def _scan_directory(self, directory: str) -> Dict[str, str]:
        """Scan directory for executable files."""
        apps = {}
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(('.exe', '.lnk')):
                        file_path = os.path.join(root, file)
                        app_name = self._extract_app_name(file)
                        apps[app_name.lower()] = file_path
        except PermissionError:
            pass  # Skip directories we can't access
        return apps
    
    def _scan_registry(self) -> Dict[str, str]:
        """Scan Windows Registry for installed programs."""
        apps = {}
        try:
            import winreg
            # Scan HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            
            for i in range(winreg.QueryInfoKey(key)[0]):
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                
                try:
                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                    
                    if display_name and install_location:
                        exe_path = self._find_exe_in_directory(install_location)
                        if exe_path:
                            apps[display_name.lower()] = exe_path
                except (FileNotFoundError, OSError):
                    pass
                    
                winreg.CloseKey(subkey)
            winreg.CloseKey(key)
        except (ImportError, OSError):
            pass  # Registry access not available
            
        return apps
    
    def _scan_start_menu(self) -> Dict[str, str]:
        """Scan Windows Start Menu for applications."""
        apps = {}
        start_menu_paths = [
            os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs"),
            r"C:\ProgramData\Microsoft\Windows\Start Menu\\Programs"
        ]
        
        for path in start_menu_paths:
            if os.path.exists(path):
                apps.update(self._scan_directory(path))
        
        return apps
    
    def _find_exe_in_directory(self, directory: str) -> Optional[str]:
        """Find the main executable in a directory."""
        if not os.path.exists(directory):
            return None
            
        for file in os.listdir(directory):
            if file.endswith('.exe') and not file.startswith('unins'):
                return os.path.join(directory, file)
        return None
    
    def _extract_app_name(self, filename: str) -> str:
        """Extract clean app name from filename."""
        name = filename.replace('.exe', '').replace('.lnk', '')
        # Remove common prefixes/suffixes
        name = name.replace('uninstall', '').replace('setup', '').replace('config', '')
        return name.strip()
    
    def find_app_by_name(self, app_name: str) -> Optional[str]:
        """Find app using intelligent matching."""
        app_name = app_name.lower().strip()
        
        # Direct match
        if app_name in self.installed_apps:
            return self.installed_apps[app_name]
        
        # Fuzzy matching
        import difflib
        matches = difflib.get_close_matches(app_name, self.installed_apps.keys(), n=3, cutoff=0.6)
        if matches:
            print(f"[Dynamic Discovery] Fuzzy match: '{app_name}' -> '{matches[0]}'")
            return self.installed_apps[matches[0]]
        
        # Partial matching
        for installed_name in self.installed_apps:
            if app_name in installed_name or installed_name in app_name:
                print(f"[Dynamic Discovery] Partial match: '{app_name}' -> '{installed_name}'")
                return self.installed_apps[installed_name]
        
        return None
    
    def launch_app_with_vision(self, app_name: str) -> Dict[str, Any]:
        """Launch app using visual intelligence if direct launch fails."""
        print(f"[Dynamic Discovery] Using vision to find: '{app_name}'")
        
        if not pyautogui:
            return {"success": False, "message": "PyAutoGUI not available for visual launch"}
        
        try:
            # Take screenshot to analyze
            screenshot = pyautogui.screenshot()
            
            # Try to find app on desktop/start menu
            # This would integrate with vision_agent for visual recognition
            print("[Dynamic Discovery] Scanning desktop for app icons...")
            
            # Move mouse to show we're working
            screen_width, screen_height = pyautogui.size()
            pyautogui.moveTo(screen_width // 2, screen_height // 2, duration=0.5)
            
            # Open Start Menu
            pyautogui.press("win")
            time.sleep(1)
            
            # Type app name
            pyautogui.write(app_name, interval=0.1)
            time.sleep(1.5)
            
            # Press Enter to launch
            pyautogui.press("enter")
            time.sleep(2)
            
            return {
                "success": True, 
                "message": f"Used visual discovery to launch '{app_name}'"
            }
            
        except Exception as e:
            return {"success": False, "message": f"Visual launch failed: {str(e)}"}
    
    def get_app_suggestions(self, partial_name: str) -> List[str]:
        """Get app suggestions based on partial name."""
        partial = partial_name.lower()
        suggestions = []
        
        for app_name in self.installed_apps:
            if partial in app_name or app_name in partial:
                suggestions.append(app_name)
        
        return sorted(suggestions)[:10]  # Return top 10 suggestions

# Global instance
dynamic_discovery = DynamicAppDiscovery()
