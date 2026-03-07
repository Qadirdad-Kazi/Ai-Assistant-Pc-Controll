"""
PC Control module for system-level automation on Windows.
"""
import ctypes
import os
import subprocess
import time
import shutil
from typing import Dict, Any

try:
    import pyautogui
except Exception as e:
    pyautogui = None
    print(f"[PC Control] pyautogui failed to load. Volume/Media controls will be limited. ERROR: {e}")

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
            "terminal": "wt.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "code": "code.exe",
            "vscode": "code.exe",
            "vs code": "code.exe",
            "visual studio code": "code.exe",
            "discord": "Update.exe --processStart Discord.exe"
        }

    def execute(self, action: str, target: str = "") -> Dict[str, Any]:
        """Execute a PC control action with intelligent command parsing."""
        action = action.lower().strip()
        target = target.lower().strip()
        
        print(f"[PC Control] Executing: action='{action}', target='{target}'")
        
        try:
            if action in ("open_app", "open"):
                return self._open_app_intelligent(target)
            elif action in ("close_app", "close"):
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

    def _open_app_intelligent(self, target: str) -> Dict[str, Any]:
        """Intelligently open an app with complex commands like 'select profile' or 'search for gmail'."""
        print(f"[PC Control] Intelligent app opening: '{target}'")
        
        # Parse the command to understand what the user wants
        target_lower = target.lower()
        
        # Check for complex patterns
        if "select any profile" in target_lower and "gmail" in target_lower:
            # Open Chrome and select Gmail profile
            return self._open_chrome_with_profile("gmail")
        elif "search for" in target_lower and ("gmail" in target_lower or "email" in target_lower):
            # Open Chrome and search for Gmail
            return self._open_chrome_and_search("gmail")
        elif "profile" in target_lower:
            # Open Chrome with profile selection
            return self._open_chrome_with_profile_selection()
        else:
            # Simple app opening - use existing logic
            return self._open_app(target)
    
    def _open_chrome_with_profile(self, profile_type: str) -> Dict[str, Any]:
        """Open Chrome and navigate to a specific profile."""
        try:
            # Open Chrome first
            result = self._open_app("chrome")
            if result.get("success"):
                # Wait for Chrome to load
                time.sleep(2)
                
                # Try to find and click the profile
                if pyautogui:
                    # Look for profile element
                    profile_element = None
                    for i in range(10):  # Search for 10 seconds max
                        try:
                            profile_element = pyautogui.locateOnScreen(f"*{profile_type}* profile", confidence=0.8)
                            if profile_element:
                                print(f"[PC Control] Found {profile_type} profile element")
                                pyautogui.moveTo(profile_element[0], profile_element[1])
                                pyautogui.click()
                                time.sleep(1)
                                break
                        except:
                            continue
                    
                    if profile_element:
                        return {"success": True, "message": f"Opened Chrome and selected {profile_type} profile."}
                    else:
                        return {"success": True, "message": "Opened Chrome but couldn't find profile element."}
                else:
                    return {"success": True, "message": "Opened Chrome but pyautogui not available."}
            else:
                return result
                
        except Exception as e:
            return {"success": False, "message": f"Error opening Chrome with profile: {str(e)}"}
    
    def _open_chrome_and_search(self, search_type: str) -> Dict[str, Any]:
        """Open Chrome and search for Gmail or email."""
        try:
            # Open Chrome first
            result = self._open_app("chrome")
            if result.get("success"):
                # Wait for Chrome to load
                time.sleep(2)
                
                # Navigate to search and execute search
                if pyautogui:
                    # Click on address bar
                    try:
                        address_bar = pyautogui.locateOnScreen("address bar", confidence=0.8)
                        if address_bar:
                            pyautogui.click(address_bar[0], address_bar[1])
                            time.sleep(0.5)
                            pyautogui.write(f"{search_type} for gmail")
                            time.sleep(1)
                            pyautogui.press("enter")
                            time.sleep(2)
                            return {"success": True, "message": f"Opened Chrome and searched for {search_type}."}
                    except Exception as e:
                        return {"success": True, "message": f"Opened Chrome but search failed: {str(e)}"}
                else:
                    return {"success": True, "message": "Opened Chrome but pyautogui not available for search."}
            else:
                return result
                
        except Exception as e:
            return {"success": False, "message": f"Error opening Chrome for search: {str(e)}"}
    
    def _open_chrome_with_profile_selection(self) -> Dict[str, Any]:
        """Open Chrome and show profile selection dialog."""
        try:
            # Open Chrome first
            result = self._open_app("chrome")
            if result.get("success"):
                # Wait for Chrome to load
                time.sleep(2)
                
                if pyautogui:
                    # Look for profile icon
                    try:
                        profile_button = pyautogui.locateOnScreen("profile", confidence=0.8)
                        if profile_button:
                            pyautogui.moveTo(profile_button[0], profile_button[1])
                            pyautogui.click()
                            time.sleep(1)
                            
                            # Look for profile options
                            time.sleep(1)
                            profile_options = pyautogui.locateAllOnScreen()
                            
                            # Find Gmail profile option
                            gmail_profile = None
                            for option in profile_options:
                                if "gmail" in option.text.lower():
                                    gmail_profile = option
                                    break
                            
                            if gmail_profile:
                                pyautogui.moveTo(gmail_profile[0], gmail_profile[1])
                                pyautogui.click()
                                return {"success": True, "message": "Opened Chrome and selected Gmail profile."}
                            else:
                                return {"success": True, "message": "Opened Chrome but couldn't find Gmail profile option."}
                    except Exception as e:
                        return {"success": True, "message": f"Opened Chrome but profile selection failed: {str(e)}"}
                else:
                    return {"success": True, "message": "Opened Chrome but pyautogui not available for profile selection."}
            else:
                return result
                
        except Exception as e:
            return {"success": False, "message": f"Error opening Chrome with profile selection: {str(e)}"}
        if not app_name:
            return {"success": False, "message": "No app specified to open."}
            
        # Clean the input (LLMs often use underscores)
        app_name = app_name.replace("_", " ").strip().lower()
        
        # Strip common conversational prefixes/suffixes the STT might inject
        import re
        app_name = re.sub(r'^(please\s+)?(could you\s+)?(can you\s+)?(open\s+)?(the\s+)?(app\s+)?(application\s+)?', '', app_name).strip()
        app_name = re.sub(r'\s+(for me|please)\b', '', app_name).strip()
        
        # Fuzzy match to correct STT typos (e.g. "visul studio" -> "visual studio code")
        import difflib
        matches = difflib.get_close_matches(app_name, self.app_map.keys(), n=1, cutoff=0.6)
        if matches:
            corrected = matches[0]
            print(f"[PC Control] Autocorrected typo: '{app_name}' -> '{corrected}'")
            app_name = corrected
            
        executable = self.app_map.get(app_name, app_name)
        
        try:
            # First try os.startfile for known Executables/Paths. 
            # This correctly throws FileNotFoundError if it doesn't exist.
            if hasattr(os, 'startfile'):
                try:
                    os.startfile(executable)
                    return {"success": True, "message": f"I have opened {app_name}."}
                except (FileNotFoundError, OSError):
                    pass
            
            # Second try: "Human-like" Windows Search Fallback (Move mouse, Press Win, type Name, press Enter)
            if pyautogui:
                print(f"[PC Control] Could not find {app_name} executable. Trying Windows Search...")
                # Visually move the cursor to prove control
                screen_width, screen_height = pyautogui.size()
                pyautogui.moveTo(screen_width / 2, screen_height / 2, duration=0.5, tween=pyautogui.easeInOutQuad)
                
                # Use press instead of hotkey (more reliable on Windows 11)
                pyautogui.press("win")
                time.sleep(0.8)
                
                # Type out the app name character by character
                pyautogui.write(app_name, interval=0.1)
                time.sleep(1.5) # Wait for search results
                
                pyautogui.press("enter")
                return {
                    "success": True, 
                    "message": f"I couldn't find {app_name} explicitly, so I tried using Windows Search to open it."
                }
                
            return {
                "success": False, 
                "message": f"I cannot find the application '{app_name}' installed on your PC. Do you want me to help you download it or look for something else?"
            }
            
        except Exception as e:
            return {"success": False, "message": f"I encountered an error trying to open {app_name}. {e}"}

    def _close_app(self, app_name: str) -> Dict[str, Any]:
        if not app_name:
            return {"success": False, "message": "No app specified to close."}
            
        app_name = app_name.replace("_", " ").strip().lower()
        
        import difflib
        matches = difflib.get_close_matches(app_name, self.app_map.keys(), n=1, cutoff=0.65)
        if matches:
            app_name = matches[0]
            
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
