import base64
import json
import io
import time
from typing import Dict, Any
import requests
from config import OLLAMA_URL, GREEN, CYAN, YELLOW, GRAY, RESET

try:
    import pyautogui
    from PIL import Image
    # PyAutoGUI safety setting
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 1.0
except ImportError:
    pyautogui = None
    Image = None

class VisionAgent:
    """Local Vision Agent using LLaVA-phi3 via Ollama to control the PC UI."""
    
    def __init__(self, model_name="llava-phi3"):
        self.model_name = model_name
        self.api_url = f"{OLLAMA_URL}/generate"
        
    def _capture_screen_base64(self) -> str:
        """Capture the current screen and convert to a base64 string."""
        if not pyautogui or not Image:
            raise ImportError("PyAutoGUI or Pillow is missing.")
            
        print(f"{GRAY}[VisionAgent] 📸 Taking a screenshot of your PC...{RESET}")
        screenshot = pyautogui.screenshot()
        
        # Resize to 1024x1024 max so the model processes it quickly without losing too much detail
        screenshot.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        
        # Save to memory buffer as PNG
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG", optimize=True)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str, screenshot.width, screenshot.height

    def execute_visual_task(self, task_description: str) -> Dict[str, Any]:
        """Ask the Vision AI to locate an object and click on it."""
        if not pyautogui:
            return {"success": False, "message": "pyautogui is not installed."}
            
        try:
            print(f"{CYAN}[VisionAgent] 🧠 Task: {task_description}{RESET}")
            
            # Step 1: Capture screenshot
            b64_image, img_width, img_height = self._capture_screen_base64()
            screen_width, screen_height = pyautogui.size()
            
            # Step 2: Formulate prompt for LLaVA
            prompt = (
                f"You are an AI controlling a graphical user interface. The user wants to: '{task_description}'.\n"
                "Look at the provided screenshot of the PC screen.\n"
                "To accomplish this task, you need to find the specific element on the screen to click on.\n"
                "Identify the coordinates (in percentages from 0.0 to 1.0 where 0,0 is top-left and 1,1 is bottom-right) "
                "of the exact center of this element.\n"
                "Output ONLY a valid JSON object in this format, and absolutely nothing else: "
                "{\"action\": \"click\", \"x_percent\": 0.5, \"y_percent\": 0.5, \"thought\": \"I see the element here.\"}"
            )
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [b64_image],
                "stream": False,
                "format": "json"
            }
            
            print(f"{GRAY}[VisionAgent] ⏳ Analyzing screen with {self.model_name}...{RESET}")
            start_time = time.time()
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            ai_time = time.time() - start_time
            
            result_json = response.json().get("response", "{}")
            print(f"{GREEN}[VisionAgent] ✓ AI analysis completed in {ai_time:.2f}s.{RESET}")
            
            # Step 3: Parse response and execute
            try:
                action_data = json.loads(result_json)
                x_percent = float(action_data.get("x_percent", 0.5))
                y_percent = float(action_data.get("y_percent", 0.5))
                thought = action_data.get("thought", "No thought provided.")
                
                print(f"{CYAN}[VisionAgent] 🤔 AI Thought: {thought}{RESET}")
                
                # Scale from percentage mapping back to actual screen resolution
                target_x = int(x_percent * screen_width)
                target_y = int(y_percent * screen_height)
                
                # Constrain to screen boundaries
                target_x = max(0, min(screen_width - 1, target_x))
                target_y = max(0, min(screen_height - 1, target_y))
                
                print(f"{GREEN}[VisionAgent] 🖱️ Moving mouse to coordinates: ({target_x}, {target_y}){RESET}")
                
                # Smooth move and click
                pyautogui.moveTo(target_x, target_y, duration=0.8, tween=pyautogui.easeInOutQuad)
                pyautogui.click()
                
                return {
                    "success": True, 
                    "message": f"I used my vision to locate the target and clicked on it. Thought: {thought}",
                    "data": {"x": target_x, "y": target_y, "screen_size": [screen_width, screen_height]}
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"{YELLOW}[VisionAgent] AI failed to output valid JSON coordinates: {result_json}{RESET}")
                return {"success": False, "message": "Failed to visually locate the target on the screen."}

        except Exception as e:
            print(f"{YELLOW}[VisionAgent] Error executing visual task: {e}{RESET}")
            return {"success": False, "message": f"Error performing visual action: {e}"}

# Global instance
vision_agent = VisionAgent()
