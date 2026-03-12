import base64
import json
import io
import time
import requests # type: ignore
from typing import Dict, Any, List, Optional
from pathlib import Path

# Config and common logging imports
try:
    from config import OLLAMA_URL, GREEN, CYAN, YELLOW, GRAY, RESET # type: ignore
except ImportError:
    OLLAMA_URL = "http://localhost:11434"
    GREEN = CYAN = YELLOW = GRAY = RESET = ""

try:
    import pyautogui # type: ignore
    from PIL import Image # type: ignore
    # PyAutoGUI safety setting
    pyautogui.FAILSAFE = True # type: ignore
    pyautogui.PAUSE = 1.0 # type: ignore
except ImportError:
    pyautogui = None
    Image = None

from core.omni_parser_client import omni_parser # type: ignore

class VisionAgent:
    """Enhanced Vision Agent using OmniParser + VLM for precise PC control."""
    
    def __init__(self, model_name="llava-phi3"):
        self.model_name = model_name
        self.api_url = f"{OLLAMA_URL}/api/generate" # Fixed endpoint
        self.last_parse_result: Optional[List[Dict[str, Any]]] = None
        
    def _capture_screen_base64(self) -> str:
        """Capture current screen and convert to a base64 string."""
        if not pyautogui or not Image:
            raise ImportError("PyAutoGUI or Pillow is missing.")
            
        try:
            screenshot = pyautogui.screenshot() # type: ignore
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG") # type: ignore
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            print(f"[VisionAgent] Capture error: {e}")
            return ""
    
    def _analyze_screen(self, task: str, img_base64: Optional[str] = None) -> Dict[str, Any]:
        """Analyze screen image and execute task by leveraging OmniParser if available."""
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
            prompt = f"""
            You are a visual AI assistant with pixel-perfect precision.
            Current Screen Size: {pyautogui.size() if pyautogui else "Unknown"} # type: ignore
            Task: {task}
            {elements_summary}
            
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
                "thought": "your reasoning",
                "message": "User-facing status",
                "success": bool
            }}
            """
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [img_base64],
                "stream": False,
                "format": "json"
            }
            
            print(f"[VisionAgent] Sending request to {self.model_name}...")
            response = requests.post(self.api_url, json=payload, timeout=60).json()
            
            if response.get("response"):
                action_data = json.loads(response["response"])
                
                # Grounding logic
                tid = action_data.get("target_id")
                if tid is not None and self.last_parse_result and 0 <= tid < len(self.last_parse_result): # type: ignore
                    target = self.last_parse_result[tid] # type: ignore
                    box = target.get("box", [0, 0, 0, 0])
                    
                    # OmniParser V2 often returns coords in 0-1000 range, 
                    # but some versions return 0.0-1.0. We detect and normalize.
                    x_mid = (box[1] + box[3]) / 2
                    y_mid = (box[0] + box[2]) / 2
                    
                    if x_mid > 1.0 or y_mid > 1.0:
                        # Likely 0-1000 scale
                        action_data["x_percent"] = x_mid / 1000.0
                        action_data["y_percent"] = y_mid / 1000.0
                    else:
                        # Already ratio
                        action_data["x_percent"] = x_mid
                        action_data["y_percent"] = y_mid
                        
                    print(f"[VisionAgent] Grounded action to OmniParser element [{tid}] at {action_data['x_percent']:.2f}, {action_data['y_percent']:.2f}")

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

            screen_width, screen_height = pyautogui.size() # type: ignore
            x = int(analysis.get("x_percent", 0.5) * screen_width)
            y = int(analysis.get("y_percent", 0.5) * screen_height)
            
            print(f"[VisionAgent] Clicking at ({x}, {y}) - {analysis.get('thought')}")
            pyautogui.moveTo(x, y, duration=0.8, tween=pyautogui.easeInOutQuad) # type: ignore
            pyautogui.click() # type: ignore
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

            screen_width, screen_height = pyautogui.size() # type: ignore
            x = int(analysis.get("x_percent", 0.5) * screen_width)
            y = int(analysis.get("y_percent", 0.5) * screen_height)
            text = analysis.get("text", "")
            
            print(f"[VisionAgent] Typing '{text}' at ({x}, {y})")
            pyautogui.click(x, y) # type: ignore
            time.sleep(0.3)
            pyautogui.typewrite(text, interval=0.05) # type: ignore
            
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
            pyautogui.scroll(-amount if direction == "down" else amount) # type: ignore
            
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

# Global instance
vision_agent = VisionAgent()
