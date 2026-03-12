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
    """Local Vision Agent using LLaVA-phi3 via Ollama to control PC UI."""
    
    def __init__(self, model_name="llava-phi3"):
        self.model_name = model_name
        self.api_url = f"{OLLAMA_URL}/generate"
        
    def _capture_screen_base64(self) -> str:
        """Capture current screen and convert to a base64 string."""
        if not pyautogui or not Image:
            raise ImportError("PyAutoGUI or Pillow is missing.")
            
        try:
            # Capture screenshot
            screenshot = pyautogui.screenshot()  
            
            # Convert to base64
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
            
            return img_base64
        except Exception as e:
            return f"Error capturing screen: {str(e)}"
    
    def _analyze_screen(self, task: str, img_base64: str) -> Dict[str, Any]:
        """Analyze screen image and execute task using LLaVA-phi3."""
        try:
            # Create prompt for vision analysis
            prompt = f"""
            You are a visual AI assistant that can see and control the user's computer screen.
            
            Task: {task}
            
            Look at the screenshot carefully and identify:
            - UI elements (buttons, text fields, icons, windows, etc.)
            - Application interfaces and their current state
            - Any relevant information displayed on screen
            - Spatial relationships between elements
            
            Based on what you see, determine the best action to complete the task.
            
            If you're confused about what to do or can't find the required element:
            1. Ask a clarifying question to the user
            2. Wait for their response
            3. Try again with their clarification
            
            Available actions:
            - click: Click on a specific element
            - type: Type text into a text field
            - scroll: Scroll the screen
            - wait: Wait for an element to appear
            - describe: Describe what you see
            
            Examples:
            - If user asks "Open Chrome and click Gmail profile", you should:
              * Look for Chrome browser
              * Look for Gmail profile option
              * Click on the Gmail profile
              * If successful, report completion
            
            - If you can't find something, say: "I can see the screen but I'm having trouble finding [element]. Could you describe where it is or help me locate it?"
            
            Output format:
            Always return a JSON object with these keys:
            - action: The action to take (click, type, scroll, wait, describe)
            - x_percent, y_percent: Coordinates (0-100%) for the action
            - thought: Your reasoning process
            - message: Human-readable description of what you did
            - success: Boolean indicating if action was successful
            - followup: Boolean indicating if user clarification is needed
            
            """
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [{"data": img_base64, "type": "image_url"}],
                "stream": False
            }
            
            response = requests.post(self.api_url, json=payload, timeout=30).json()
            
            if response.get("response"):
                result = response["response"].strip()
                print(f"[VisionAgent] Analysis result: {result}")
                
                # Try to extract action from the response
                action = None
                thought = "I can see the screen but I'm not sure how to complete this task."
                
                # Look for action keywords in the response
                if "click" in result.lower():
                    action = "click"
                    # Extract element description from task
                    element_desc = task.split("click")[-1] if "click" in task else "element"
                elif "type" in result.lower():
                    action = "type"
                    # Extract text to type from task
                    text_to_type = task.split("type")[-1] if "type" in task else "text"
                elif "scroll" in result.lower():
                    action = "scroll"
                    # Extract direction from task
                    direction = task.split("scroll")[-1] if "scroll" in task else "down"
                elif "wait" in result.lower():
                    action = "wait"
                    followup = True
                elif "describe" in result.lower():
                    action = "describe"
                    thought = "I can see the screen and will describe what I observe."
                    message = self._describe_screen()
                else:
                    thought = "I analyzed the screen but I'm not sure how to complete this task. I can see: " + self._describe_screen()
                    followup = True
                
                return {
                    "action": action,
                    "thought": thought,
                    "message": message,
                    "followup": followup if action in ["click", "type", "scroll", "wait"] else False,
                    "success": action in ["click", "type", "scroll"]
                }
            else:
                return {"success": False, "message": "Failed to analyze screen."}
                
        except Exception as e:
            return {"success": False, "message": f"Vision analysis error: {str(e)}"}
    
    def _find_and_click_element(self, task: str) -> Dict[str, Any]:
        """Find a specific element on screen and click it."""
        try:
            # Step 1: Capture screenshot
            b64_image = self._capture_screen_base64()
            screen_width, screen_height = pyautogui.size()  
            
            # Step 2: Formulate prompt for LLaVA
            prompt = (
                f"You are an AI controlling a graphical user interface. The user wants to: '{task}'.\n"
                "Look at the provided screenshot of the PC screen.\n"
                "To accomplish this task, you need to find the specific element on the screen to click on.\n"
                "Identify the coordinates (in percentages from 0.0 to 1.0 where 0,0 is top-left and 1,1 is bottom-right) "
                "of the exact center of this element.\n"
                "Output ONLY a valid JSON object in this format, and absolutely nothing else: "
                "{\"action\": \"click\", \"x_percent\": 0.5, \"y_percent\": 0.5, \"thought\": \"I see: element here.\"}"
            )
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [b64_image],
                "stream": False,
                "format": "json"
            }
            
            start_time = time.time()
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            ai_time = time.time() - start_time
            
            result_json = response.json().get("response", "{}")
            print(f"[VisionAgent] ✓ AI analysis completed in {ai_time:.2f}s.{RESET}")
            
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
                
                # Smooth move and click
                pyautogui.moveTo(target_x, target_y, duration=0.8, tween=pyautogui.easeInOutQuad)  
                pyautogui.click()  
                time.sleep(1)
                
                return {
                    "success": True, 
                    "message": f"I used my vision to locate the target and clicked on it. Thought: {thought}",
                    "data": {"x": target_x, "y": target_y, "screen_size": [screen_width, screen_height]}
                }
            except (json.JSONDecodeError, ValueError) as e:
                print(f"{YELLOW}[VisionAgent] AI failed to output valid JSON coordinates: {result_json}{RESET}")
                return {"success": False, "message": "Failed to visually locate the target on screen."}
                
        except Exception as e:
            return {"success": False, "message": f"Error clicking element: {str(e)}"}
    
    def _find_and_type_text(self, task: str) -> Dict[str, Any]:
        return {"success": False, "message": "Not implemented"}
    
    def _scroll_screen(self, task: str) -> Dict[str, Any]:
        return {"success": False, "message": "Not implemented"}
    
    def _describe_screen(self) -> str:
        return ""
