"""
PC Control module for system-level automation on Windows.
"""
import ctypes
import os
import subprocess
import time
import shutil
import threading
from typing import Dict, Any

try:
    import pyautogui  
except Exception as e:
    pyautogui = None  
    print(f"[PC Control] pyautogui failed to load. Volume/Media controls will be limited. ERROR: {e}")

# Import dynamic app discovery
from core.dynamic_app_discovery import dynamic_discovery  
from core.omni_parser_client import omni_parser
import base64
from io import BytesIO

class PCController:
    """Handles system level commands like controlling volume, opening apps, or locking the PC."""
    _global_lock = threading.Lock()
    _global_discovery_started = False
    _global_discovered_apps: Dict[str, str] = {}
    _global_discovery_in_progress = False
    _instance_count = 0
    
    def __init__(self):
        with self.__class__._global_lock:
            self.__class__._instance_count += 1
            instance_no = self.__class__._instance_count

        # Initialize app discovery lazily in background to speed startup.
        self.discovered_apps: Dict[str, str] = dict(self.__class__._global_discovered_apps)
        self._discovery_lock = threading.Lock()
        self._discovery_started = False
        
        # Safety Sandbox & Clarification Callbacks
        self.confirmation_callback = None
        self.clarification_callback = None
        
        # Keep some common mappings as fallback
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
        
        if instance_no == 1:
            print("[PC Control] Initialized (app discovery will start on first app request)")
        else:
            print(f"[PC Control] Initialized (instance #{instance_no}, using shared discovery state)")

    def _start_discovery_background(self):
        with self.__class__._global_lock:
            if self.__class__._global_discovered_apps:
                self.discovered_apps = dict(self.__class__._global_discovered_apps)
                return
            if self.__class__._global_discovery_in_progress:
                return
            self.__class__._global_discovery_in_progress = True

        with self._discovery_lock:
            if self._discovery_started:
                return
            self._discovery_started = True

        def _worker():
            try:
                apps = dynamic_discovery.discover_installed_apps()
                self.discovered_apps = apps
                with self.__class__._global_lock:
                    self.__class__._global_discovered_apps = dict(apps)
                    self.__class__._global_discovery_started = True
                    self.__class__._global_discovery_in_progress = False
                print(f"[PC Control] App discovery completed: {len(apps)} apps")
            except Exception as e:
                with self.__class__._global_lock:
                    self.__class__._global_discovery_in_progress = False
                print(f"[PC Control] App discovery failed: {e}")

        threading.Thread(target=_worker, daemon=True).start()

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
            elif action == "tile_windows":
                return self._tile_windows_macos(target)
            elif action == "command":
                return self._run_command(target)
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to execute {action}: {e}"}

    def _request_confirmation(self, action_name: str, details: str = "") -> bool:
        """Helper to request user confirmation for high-risk actions."""
        if not self.confirmation_callback:
            # If no callback (e.g. CLI mode), default to True or False based on choice
            # But the user asked for professional "ensure", so we should ideally force confirmation.
            print(f"[PC Control] [SAFETY] Confirmation required for: {action_name} ({details})")
            return False 

        print(f"[PC Control] [SAFETY] Awaiting confirmation for: {action_name}")
        return self.confirmation_callback(action_name, details)

    def _request_clarification(self, question: str, screenshot_base64: str) -> Dict[str, Any]:
        """Helper to request visual clarification from the user."""
        if not self.clarification_callback:
            print(f"[PC Control] [VISION] Clarification required but no callback set: {question}")
            return {"success": False, "message": "Clarification required"}
            
        print(f"[PC Control] [VISION] Awaiting user clarification: {question}")
        return self.clarification_callback(question, screenshot_base64)

    def _get_screen_elements_via_omni(self) -> List[Dict[str, Any]]:
        """Capture screen and parse UI elements using OmniParser."""
        if not omni_parser.is_available():
            return []
            
        try:
            # Capture screenshot
            import pyautogui
            screenshot = pyautogui.screenshot()
            
            # Convert to base64
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Parse via OmniParser
            result = omni_parser.parse_screen(img_str)
            if result.get("success"):
                return result.get("elements", [])
            return []
        except Exception as e:
            print(f"[PC Control] [OmniParser] Screenshot/Parse failed: {e}")
            return []

    def _click_element_visually(self, query: str) -> bool:
        """Try to find and click an element using Vision (OmniParser) with human-like verification."""
        from core.vision_agent import vision_agent
        
        # 1. Capture and analyze
        import pyautogui
        sw, sh = pyautogui.size()
        
        # We'll use the vision_agent's built-in click method which handles OmniParser grounding
        result = vision_agent._find_and_click_element(query)
        
        if result.get("success"):
            # 2. Verify
            verify = vision_agent.verify_action_result(f"after clicking {query}")
            if verify.get("success"):
                return True
            else:
                print(f"[PC Control] [Vision] Click performed but verification failed. Confidence: {verify.get('confidence')}")
                # This is where we might ask for clarification if we are unsure
                if verify.get("confidence", 0) < 0.4:
                    screenshot = vision_agent._capture_screen_base64()
                    clarification = self._request_clarification(f"I clicked on what I thought was '{query}', but the screen didn't change as expected. Could you show me the correct spot?", screenshot)
                    if clarification.get("success") and clarification.get("mode") == "point":
                         x = int(clarification.get("x_percent", 0.5) * sw)
                         y = int(clarification.get("y_percent", 0.5) * sh)
                         pyautogui.click(x, y)
                         return True
        return False

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
            
    def _run_command(self, target: str) -> Dict[str, Any]:
        """Execute a terminal or shell command."""
        print(f"[PC Control] Running terminal command: '{target}'")
        
        # SAFETY CHECK
        if not self._request_confirmation("Run Shell Command", target):
            return {"success": False, "message": "Command execution cancelled by user safety check."}
            
        try:
            # We use powershell to execute terminal commands on Windows
            process = subprocess.run(
                ["powershell", "-Command", target], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            output = process.stdout.strip()
            error = process.stderr.strip()
            
            if process.returncode == 0:
                msg = f"Command executed successfully.\nOutput: {output}" if output else "Command executed successfully with no output."
                return {"success": True, "message": msg}
            else:
                return {"success": False, "message": f"Command failed (Code {process.returncode}).\nError: {error}\nOutput: {output}"}
                
        except Exception as e:
            return {"success": False, "message": f"Failed to run command: {e}"}
    
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
                        return {"success": False, "message": "Address bar not found"}
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
                    return {"success": False, "message": "Profile button not found."}
                else:
                    return {"success": True, "message": "Opened Chrome but pyautogui not available for profile selection."}
            else:
                return result
                
        except Exception as e:
            return {"success": False, "message": f"Error opening Chrome with profile selection: {str(e)}"}
        
    def _open_app(self, app_name: str) -> Dict[str, Any]:
        """Open an application using dynamic discovery - works with ANY installed app!"""
        if not app_name:
            return {"success": False, "message": "No app specified to open."}
            
        # Clean up input (LLMs often use underscores)
        app_name = app_name.replace("_", " ").strip().lower()
        
        # Strip common conversational prefixes/suffixes the STT might inject
        import re
        app_name = re.sub(r'^(please\s+)?(could you\s+)?(can you\s+)?(open\s+)?(the\s+)?(app\s+)?(application\s+)?', '', app_name).strip()
        app_name = re.sub(r'\s+(for me|please)\b', '', app_name).strip()
        
        print(f"[PC Control] Searching for app: '{app_name}'")

        # Method 0: PROFESSIONAL HUMAN-LIKE VISION FLOW (PRIORITY)
        print(f"[PC Control] Attempting professional human-like launch for: '{app_name}'")
        from core.vision_agent import vision_agent
        
        # Use the human launch flow: Start -> Type -> Click -> Verify
        visual_result = vision_agent.human_launch_app(app_name)
        
        if visual_result.get("success"):
            return {"success": True, "message": f"I have successfully recognized and launched {app_name} as a human would."}
        else:
            print(f"[PC Control] [Vision] Human launch failed or was ambiguous. Confidence: {visual_result.get('confidence', 0)}")
            # Handle ambiguity/low confidence
            if visual_result.get('confidence', 1.0) < 0.5:
                # Take a fresh screenshot for the user
                screenshot = vision_agent._capture_screen_base64()
                clarification = self._request_clarification(f"I'm trying to open '{app_name}' but I see multiple options or I'm not sure which icon to click. Could you point it out for me?", screenshot)
                
                if clarification.get("success"):
                    if clarification.get("mode") == "point":
                         import pyautogui
                         sw, sh = pyautogui.size()
                         x = int(clarification.get("x_percent", 0.5) * sw)
                         y = int(clarification.get("y_percent", 0.5) * sh)
                         pyautogui.click(x, y)
                         return {"success": True, "message": f"I have opened {app_name} with your guidance."}
                    elif clarification.get("mode") == "confirm":
                         # User just said yes to a general query
                         pyautogui.press("enter")
                         return {"success": True, "message": f"I used your confirmation to proceed with opening {app_name}."}

        # Method 1: Try dynamic discovery as fallback (if vision fails)
        app_path = dynamic_discovery.find_app_by_name(app_name)
        if app_path:
            try:
                print(f"[PC Control] Found app via dynamic discovery: {app_path}")
                print(f"[PC Control] Launching: {app_path}")
                
                # Show visual feedback that we're working
                if pyautogui:
                    screen_width, screen_height = pyautogui.size()
                    pyautogui.moveTo(screen_width // 2, screen_height // 2, duration=0.5)
                    time.sleep(0.5)
                
                os.startfile(app_path)  
                print(f"[PC Control] ✓ App launched successfully!")
                time.sleep(2)  # Wait for app to actually open
                
                return {"success": True, "message": f"I have opened {app_name} using dynamic discovery."}
            except Exception as e:
                print(f"[PC Control] Dynamic discovery found app but failed to launch: {e}")
        
        # Method 2: Try Windows Search (human-like fallback)
        if pyautogui:
            print(f"[PC Control] Using Windows Search to find: '{app_name}'")
            return self._windows_search_launch(app_name)
        
        # Method 3: Get suggestions if app not found
        suggestions = dynamic_discovery.get_app_suggestions(app_name)
        if suggestions:
            suggestion_list = ", ".join(suggestions[:5])
            return {
                "success": False, 
                "message": f"I couldn't find '{app_name}'. Did you mean: {suggestion_list}?"
            }
        
        return {
            "success": False, 
            "message": f"I cannot find the application '{app_name}' installed on your PC. It might not be installed or have a different name."
        }
    
    def _windows_search_launch(self, app_name: str) -> Dict[str, Any]:
        """Launch app using Windows Search - works like a human would."""
        try:
            print(f"[PC Control] Starting Windows Search for: '{app_name}'")
            
            # Visually move the cursor to prove control
            screen_width, screen_height = pyautogui.size()  
            pyautogui.moveTo(screen_width / 2, screen_height / 2, duration=0.5, tween=pyautogui.easeInOutQuad)  
            print(f"[PC Control] ✓ Mouse moved to center")
            
            # Use press instead of hotkey (more reliable on Windows 11)
            pyautogui.press("win")  
            print(f"[PC Control] ✓ Pressed Windows key")
            time.sleep(1.0)  # Wait for search to appear
            
            # Type out the app name character by character
            pyautogui.write(app_name, interval=0.1)  
            print(f"[PC Control] ✓ Typed: '{app_name}'")
            time.sleep(2.0) # Wait for search results to load
            
            # Press Enter to launch
            pyautogui.press("enter")  
            print(f"[PC Control] ✓ Pressed Enter to launch")
            time.sleep(3.0)  # Wait for app to fully open
            
            print(f"[PC Control] ✓ App should now be open!")
            
            return {
                "success": True, 
                "message": f"I used Windows Search to find and open '{app_name}'."
            }
        except Exception as e:
            print(f"[PC Control] ✗ Windows Search failed: {str(e)}")
            return {"success": False, "message": f"Windows Search launch failed: {str(e)}"}

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
            # SAFETY CHECK
            if not self._request_confirmation("Shutdown PC"):
                return {"success": False, "message": "Shutdown cancelled by user safety check."}
                
            os.system("shutdown /s /t 1")
            return {"success": True, "message": "Shutting down the PC."}
        except Exception as e:
            return {"success": False, "message": f"Could not shutdown PC: {e}"}

    def _restart_pc(self) -> Dict[str, Any]:
        try:
            # SAFETY CHECK
            if not self._request_confirmation("Restart PC"):
                return {"success": False, "message": "Restart cancelled by user safety check."}
                
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
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7) 
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

    def _tile_windows_macos(self, layout: str = "dev") -> Dict[str, Any]:
        """Proportional window tiling for macOS using AppleScript."""
        print(f"[PC Control] Tiling windows for layout: {layout}")
        
        # Standard Dev Layout: VS Code (Left 60%), Finder (Top Right 40%), Browser (Bottom Right 40%)
        # Bounds format: {x, y, width, height} or {left, top, right, bottom}
        script = '''
        tell application "Finder"
            set screen_bounds to bounds of window of desktop
            set screen_width to item 3 of screen_bounds
            set screen_height to item 4 of screen_bounds
        end tell

        -- 1. VS Code: Left 60%
        if application "Visual Studio Code" is running then
            tell application "Visual Studio Code"
                set bounds of window 1 to {0, 0, screen_width * 0.6, screen_height}
                activate
            end tell
        end if

        -- 2. Finder (Project Folder): Top Right 40%
        if application "Finder" is running then
            tell application "Finder"
                set bounds of window 1 to {screen_width * 0.6, 0, screen_width, screen_height * 0.5}
                activate
            end tell
        end if

        -- 3. Browser (Chrome/Safari): Bottom Right 40%
        if application "Google Chrome" is running then
            tell application "Google Chrome"
                set bounds of window 1 to {screen_width * 0.6, screen_height * 0.5, screen_width, screen_height}
                activate
            end tell
        else if application "Safari" is running then
            tell application "Safari"
                set bounds of window 1 to {screen_width * 0.6, screen_height * 0.5, screen_width, screen_height}
                activate
            end tell
        end if
        '''
        
        try:
            subprocess.run(['osascript', '-e', script], check=True)
            return {"success": True, "message": f"I have organized your workspace into a {layout} layout."}
        except Exception as e:
            return {"success": False, "message": f"Failed to tile windows: {e}"}

class _LazyPCController:
    """Lazy proxy to avoid heavy startup work during module import."""

    def __init__(self):
        self._instance = None
        self._lock = threading.Lock()

    def _get_instance(self) -> PCController:
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    self._instance = PCController()
        return self._instance

    def __getattr__(self, item):
        return getattr(self._get_instance(), item)


# Global lazy instance
pc_controller = _LazyPCController()
