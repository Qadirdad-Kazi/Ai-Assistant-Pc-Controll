"""
PC Control module for system-level automation on Windows.
"""
import ctypes
import os
import subprocess
import time
from typing import Dict, Any

try:
    import pyautogui
except ImportError:
    pyautogui = None
    print("[PC Control] pyautogui not found. Volume/Media controls will be limited.")

class PCController:
    """Handles system level commands like controlling volume, opening apps, or locking the PC."""
    
    def __init__(self):
        # We can map standard app names to their executables
        self.app_map = {
            "spotify": "spotify.exe",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "calculator": "calc.exe",
            "notepad": "notepad.exe",
            "explorer": "explorer.exe",
            "settings": "ms-settings:",
            "browser": "chrome.exe",
            "terminnal": "wt.exe",
            "discord": "Update.exe --processStart Discord.exe" # usually needs special path, but let's stick to basics if possible
        }

    def execute(self, action: str, target: str = "") -> Dict[str, Any]:
        """Execute a PC control action."""
        action = action.lower().strip()
        target = target.lower().strip()
        
        try:
            if action == "open_app":
                return self._open_app(target)
            elif action == "close_app":
                return self._close_app(target)
            elif action == "volume":
                return self._set_volume(target)
            elif action == "lock":
                return self._lock_pc()
            elif action == "shutdown":
                return self._shutdown_pc()
            elif action == "restart":
                return self._restart_pc()
            elif action == "sleep":
                return self._sleep_pc()
            elif action == "empty_trash":
                return self._empty_recycle_bin()
            elif action == "minimize_all":
                return self._minimize_all()
            elif action == "screenshot":
                return self._screenshot()
            elif action in ("mute", "unmute"):
                return self._mute_volume()
            elif action == "media":
                return self._media_control(target)
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to execute {action}: {e}"}

    def _open_app(self, app_name: str) -> Dict[str, Any]:
        if not app_name:
            return {"success": False, "message": "No app specified to open."}
            
        executable = self.app_map.get(app_name, app_name)
        
        try:
            # First try using os.startfile if it exists on Windows
            if hasattr(os, 'startfile'):
                try:
                    os.startfile(executable)
                    return {"success": True, "message": f"Opened {app_name}."}
                except FileNotFoundError:
                    pass
            
            # Fallback to subprocess, might need to rely on cmd /c start
            subprocess.Popen(f"cmd /c start {executable}", shell=True)
            return {"success": True, "message": f"Started {app_name}."}
        except Exception as e:
            return {"success": False, "message": f"Could not open {app_name}: {e}"}

    def _close_app(self, app_name: str) -> Dict[str, Any]:
        if not app_name:
            return {"success": False, "message": "No app specified to close."}
            
        executable = self.app_map.get(app_name, app_name)
        if not executable.endswith(".exe"):
            executable += ".exe"
            
        try:
            result = subprocess.run(f"taskkill /IM {executable} /F", capture_output=True, text=True, shell=True)
            if result.returncode == 0 or "SUCCESS" in result.stdout:
                return {"success": True, "message": f"Closed {app_name}."}
            else:
                # Process might not exist
                return {"success": False, "message": f"Could not close {app_name}. {result.stderr or result.stdout}"}
        except Exception as e:
            return {"success": False, "message": repr(e)}

    def _set_volume(self, target: str) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "message": "pyautogui is missing."}
            
        target = target.replace("%", "").strip()
        num_presses = 50 # max out or something generic
        
        if target.isdigit():
            # A hacky volume control. Alternatively, you can use Pycaw.
            # Volume steps in Windows are 2 points per key press. We can just set it to 0 then up.
            for _ in range(50):
                pyautogui.press("volumedown")
            
            target_vol = int(target)
            presses = target_vol // 2
            for _ in range(presses):
                pyautogui.press("volumeup")
            return {"success": True, "message": f"Set volume to {target}%."}
            
        elif target in ("up", "down"):
            action_key = "volumeup" if target == "up" else "volumedown"
            for _ in range(5): # move by 10%
                pyautogui.press(action_key)
            return {"success": True, "message": f"Turned volume {target}."}
            
        return {"success": False, "message": f"Invalid volume target: {target}"}

    def _mute_volume(self) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "message": "pyautogui is missing."}
        pyautogui.press("volumemute")
        return {"success": True, "message": "Toggled volume mute."}

    def _media_control(self, action: str) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "message": "pyautogui is missing."}
            
        if action in ("play", "pause", "playpause"):
            pyautogui.press("playpause")
            return {"success": True, "message": "Toggled media playback."}
        elif action == "next":
            pyautogui.press("nexttrack")
            return {"success": True, "message": "Skipped to next track."}
        elif action == "prev" or action == "previous":
            pyautogui.press("prevtrack")
            return {"success": True, "message": "Skipped to previous track."}
            
        return {"success": False, "message": f"Invalid media action: {action}"}

    def _lock_pc(self) -> Dict[str, Any]:
        try:
            # Lock workstation on Windows
            ctypes.windll.user32.LockWorkStation()
            return {"success": True, "message": "Locked the PC."}
        except Exception as e:
            return {"success": False, "message": f"Could not lock PC: {e}"}

    def _shutdown_pc(self) -> Dict[str, Any]:
        try:
            os.system("shutdown /s /t 1")
            return {"success": True, "message": "Shutting down the PC."}
        except Exception as e:
            return {"success": False, "message": f"Could not shutdown PC: {e}"}

    def _restart_pc(self) -> Dict[str, Any]:
        try:
            os.system("shutdown /r /t 1")
            return {"success": True, "message": "Restarting the PC."}
        except Exception as e:
            return {"success": False, "message": f"Could not restart PC: {e}"}

    def _sleep_pc(self) -> Dict[str, Any]:
        try:
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return {"success": True, "message": "Put the PC to sleep."}
        except Exception as e:
            return {"success": False, "message": f"Could not sleep PC: {e}"}

    def _empty_recycle_bin(self) -> Dict[str, Any]:
        try:
            # SHEmptyRecycleBinW
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7) # 7 = no confirmation, no progress, no sound
            if result == 0:
                return {"success": True, "message": "Emptied the recycle bin."}
            else:
                return {"success": False, "message": "Recycle bin might already be empty."}
        except Exception as e:
            return {"success": False, "message": f"Could not empty recycle bin: {e}"}

    def _minimize_all(self) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "message": "pyautogui is missing."}
        try:
            pyautogui.hotkey('win', 'd')
            return {"success": True, "message": "Toggled minimize all windows."}
        except Exception as e:
            return {"success": False, "message": f"Could not minimize windows: {e}"}

    def _screenshot(self) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "message": "pyautogui is missing."}
        try:
            out_file = "screenshot.png"
            pyautogui.screenshot(out_file)
            return {"success": True, "message": f"Saved screenshot to {os.path.abspath(out_file)}."}
        except Exception as e:
            return {"success": False, "message": f"Could not take screenshot: {e}"}

# Global instance
pc_controller = PCController()
