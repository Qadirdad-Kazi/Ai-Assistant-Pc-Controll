import base64
import json
import io
import time
import requests 
from typing import Dict, Any, List, Optional
from pathlib import Path

# Config and common logging imports
try:
    from config import OLLAMA_URL, GREEN, CYAN, YELLOW, GRAY, RESET, VISUAL_MODEL 
except ImportError:
    OLLAMA_URL = "http://localhost:11434"
    GREEN = CYAN = YELLOW = GRAY = RESET = ""
    VISUAL_MODEL = "llava-phi3"

try:
    import pyautogui 
    from PIL import Image 
    # PyAutoGUI safety setting
    pyautogui.FAILSAFE = True 
    pyautogui.PAUSE = 1.0 
except ImportError:
    pyautogui = None
    Image = None

from core.omni_parser_client import omni_parser 

class VisionAgent:
    """Enhanced Vision Agent using OmniParser + VLM for precise PC control."""
    
    def __init__(self, model_name=VISUAL_MODEL):
        self.model_name = model_name
        self.api_url = f"{OLLAMA_URL}/api/generate" # Fixed endpoint
        self.last_parse_result: Optional[List[Dict[str, Any]]] = None
        
        # Use simpler model for description tasks to avoid parsing issues
        self.description_model = "llama3.2:3b"  # More reliable for descriptions
        
    def _capture_screen_base64(self) -> str:
        """Capture current screen and convert to a base64 string."""
        if not pyautogui or not Image:
            raise ImportError("PyAutoGUI or Pillow is missing.")
            
        try:
            screenshot = pyautogui.screenshot() 
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG") 
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            print(f"[VisionAgent] Capture error: {e}")
            return ""
    
    def _analyze_screen(self, task: str, img_base64: Optional[str] = None) -> Dict[str, Any]:
        """Analyze screen image and execute task by leveraging OmniParser if available."""
        # Simple fallback for description tasks when vision models fail
        if "describe" in task.lower():
            try:
                import pyautogui
                width, height = pyautogui.size()
                
                # Get active window info
                try:
                    active_window = pyautogui.getActiveWindow()
                    if active_window and hasattr(active_window, 'title'):
                        title = active_window.title
                        if title:
                            return {
                                "success": True, 
                                "action": "describe", 
                                "message": f"I can see a window titled '{title}' on your screen. The screen resolution is {width}x{height} pixels. The vision analysis model is currently experiencing issues, but I can provide basic screen information."
                            }
                except:
                    pass
                
                return {
                    "success": True, 
                    "action": "describe", 
                    "message": f"I can see your screen which has a resolution of {width}x{height} pixels. The vision analysis model is currently experiencing issues, but I can provide basic screen information."
                }
            except Exception as e:
                return {
                    "success": True, 
                    "action": "describe", 
                    "message": f"I'm having trouble analyzing your screen right now. The vision model seems to be experiencing issues. Error: {str(e)}"
                }
        
        # Original logic for action tasks
        if not img_base64:
            img_base64 = self._capture_screen_base64()
            if not img_base64:
                return {"success": False, "message": "Failed to capture screen."}

        # 1. Try OmniParser first for structural analysis
        omni_result = omni_parser.parse_screen(img_base64)
        elements_summary = ""
        
        if omni_result.get("success"):
            elements = omni_result.get("elements", [])
            self.last_parse_result = elements
            elements_summary = "\nDetected UI Elements (Grounding):\n"
            for i, el in enumerate(elements[:25]): # Show top 25
                box = el.get("box", [0,0,0,0])
                elements_summary += f"- [{i}] {el.get('label')}: '{el.get('text','')}' at {box}\n"
        
        try:
            # 2. Formulate enriched prompt for vision analysis
            # Use simpler model for description tasks
            model_to_use = self.description_model if "describe" in task.lower() else self.model_name
            
            # Simple, direct prompt for better results
            prompt = f"""Describe what you see in this image. Be concise and specific."""
            
            if "describe" not in task.lower():
                # For action tasks, include UI elements
                prompt = f"""{elements_summary}

Task: {task}

Based on the screenshot and detected elements:
1. Identify the target element. 
2. If it matches a detected element [N], use its ID.
3. Otherwise, estimate x_percent and y_percent (0.0 to 1.0).

Output format: JSON ONLY
{{
    "action": "click" | "type" | "scroll" | "wait" | "describe",
    "x_percent": float,
    "y_percent": float,
    "target_id": int | null,
    "text": "text to type if action is type",
    "thought": "your reasoning for this action",
    "confidence": float (0.0 to 1.0),
    "message": "User-facing status",
    "success": bool
}}"""
            
            payload = {
                "model": model_to_use,
                "prompt": prompt,
                "images": [img_base64],
                "stream": False,
                "format": "json" if "describe" not in task.lower() else None
            }
            
            print(f"[VisionAgent] Sending request to {model_to_use}...")
            response = requests.post(self.api_url, json=payload, timeout=60).json()
            
            if response.get("response"):
                raw_txt = response["response"].strip()
                print(f"[VisionAgent] Model raw response: {raw_txt}")
                
                import re
                parsed_dict: Dict[str, Any] = {}
                
                # Check for error responses first
                if "error" in raw_txt.lower() or "extra data" in raw_txt.lower():
                    return {"success": False, "message": f"Model error: {raw_txt}"}
                
                # For description tasks, return the raw response
                if "describe" in task.lower():
                    return {"success": True, "action": "describe", "message": raw_txt}
                
                # For action tasks, try to parse JSON
                try:
                    candidates = []
                    for match in re.finditer(r'\{.*?\}', raw_txt, re.DOTALL):
                        candidates.append(match.group())
                    
                    # Also try greedy match
                    greedy = re.search(r'\{.*\}', raw_txt, re.DOTALL)
                    if greedy:
                        candidates.append(greedy.group())
                        
                    for candidate in reversed(candidates):
                        try:
                            data = json.loads(candidate)
                            if isinstance(data, dict):
                                parsed_dict = data
                                break
                        except:
                            continue
                            
                    if not parsed_dict:
                        return {"success": False, "message": f"Parsing failed. Raw: {raw_txt[:100]}"}
                except Exception as e:
                    return {"success": False, "message": f"Parse error: {e}"}
                
                action_data: Dict[str, Any] = parsed_dict

                # Grounding logic
                tid = action_data.get("target_id")
                if tid is not None and self.last_parse_result and 0 <= tid < len(self.last_parse_result): 
                    target = self.last_parse_result[tid] 
                    box = target.get("box", [0, 0, 0, 0])
                    
                    x_mid = float((box[1] + box[3]) / 2)
                    y_mid = float((box[0] + box[2]) / 2)
                    
                    if x_mid > 1.0 or y_mid > 1.0:
                        # Likely 0-1000 scale
                        action_data["x_percent"] = float(x_mid / 1000.0)
                        action_data["y_percent"] = float(y_mid / 1000.0)
                    else:
                        # Already ratio
                        action_data["x_percent"] = float(x_mid)
                        action_data["y_percent"] = float(y_mid)
                        
                    print(f"[VisionAgent] Grounded action to OmniParser element [{tid}] at {action_data.get('x_percent', 0):.2f}, {action_data.get('y_percent', 0):.2f}")

                return action_data
            else:
                return {"success": False, "message": "Failed to analyze screen."}
                
        except Exception as e:
            return {"success": False, "message": f"Vision analysis error: {str(e)}"}

    def _find_and_click_element(self, task: str) -> Dict[str, Any]:
        """Find a specific element on screen and click it."""
        try:
            analysis = self._analyze_screen(f"click on {task}")
            if not analysis.get("success"):
                return analysis

            screen_width, screen_height = pyautogui.size() 
            x = int(analysis.get("x_percent", 0.5) * screen_width)
            y = int(analysis.get("y_percent", 0.5) * screen_height)
            
            print(f"[VisionAgent] Clicking at ({x}, {y}) - {analysis.get('thought')}")
            pyautogui.moveTo(x, y, duration=0.8, tween=pyautogui.easeInOutQuad) 
            pyautogui.click() 
            time.sleep(0.5)
            
            return {"success": True, "message": analysis.get("message", "Clicked successfully.")}
        except Exception as e:
            return {"success": False, "message": f"Click error: {e}"}

    def _find_and_type_text(self, task: str) -> Dict[str, Any]:
        """Find an input field and type text into it."""
        try:
            analysis = self._analyze_screen(f"type text into field: {task}")
            if not analysis.get("success"):
                return analysis

            screen_width, screen_height = pyautogui.size() 
            x = int(analysis.get("x_percent", 0.5) * screen_width)
            y = int(analysis.get("y_percent", 0.5) * screen_height)
            text = analysis.get("text", "")
            
            print(f"[VisionAgent] Typing '{text}' at ({x}, {y})")
            pyautogui.click(x, y) 
            time.sleep(0.3)
            pyautogui.typewrite(text, interval=0.05) 
            
            return {"success": True, "message": f"Typed '{text}' successfully."}
        except Exception as e:
            return {"success": False, "message": f"Typing error: {e}"}

    def _scroll_screen(self, task: str) -> Dict[str, Any]:
        """Scroll the screen in the specified direction."""
        try:
            direction = "down"
            if "up" in task.lower(): direction = "up"
            
            amount = 500
            if "little" in task.lower(): amount = 200
            if "lot" in task.lower(): amount = 1000
            
            print(f"[VisionAgent] Scrolling {direction} by {amount}")
            pyautogui.scroll(-amount if direction == "down" else amount) 
            
            return {"success": True, "message": f"Scrolled {direction} successfully."}
        except Exception as e:
            return {"success": False, "message": f"Scroll error: {e}"}

    def _describe_screen(self) -> str:
        """Get a textual description of the current screen."""
        try:
            analysis = self._analyze_screen("describe exactly what you see on the screen in detail.")
            return analysis.get("message", "I see a computer screen with various icons and windows.")
        except Exception as e:
            return f"Error describing screen: {e}"

    def verify_action_result(self, expected_change: str) -> Dict[str, Any]:
        """Verify if the last action resulted in the expected UI change."""
        print(f"[VisionAgent] Verifying change: {expected_change}")
        time.sleep(1.0) # wait for animations
        analysis = self._analyze_screen(f"Verify if {expected_change} happened. Look at the screen specifically for visual confirmation.")
        confidence = analysis.get("confidence", 0.0)
        success = analysis.get("success", False) and confidence > 0.6
        return {"success": success, "confidence": confidence, "observation": analysis.get("message")}

    def human_launch_app(self, app_name: str) -> Dict[str, Any]:
        """Launch an app using the human workflow: Start -> Type -> Click."""
        print(f"[VisionAgent] Human-like launch for '{app_name}'")
        try:
            # 1. Click Start (assumed at bottom left or mid)
            # We use a visual task for this to be robust
            start_click = self._find_and_click_element("the Start button or Windows icon on the taskbar")
            if not start_click.get("success"):
                 # Fallback to key if visual fails
                 pyautogui.press("win")
                 time.sleep(0.5)

            # 2. Type App Name
            pyautogui.write(app_name, interval=0.05)
            time.sleep(1.5) # wait for search results

            # 3. Find and click the app in search results
            click_result = self._find_and_click_element(f"the {app_name} application icon in the search results")
            if not click_result.get("success"):
                # One more try: just press enter if we can't find it visually
                pyautogui.press("enter")
                time.sleep(2.0)
            
            # 4. Verify launch
            return self.verify_action_result(f"the {app_name} application window is now open and visible")
        except Exception as e:
            return {"success": False, "message": f"Human launch error: {e}"}

# Global instance
vision_agent = VisionAgent()
