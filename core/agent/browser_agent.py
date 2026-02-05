from PySide6.QtCore import QObject, Signal, QThread, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage
import base64
import time
import json

from .browser_controller import BrowserController
from .vlm_client import VLMClient

from core.model_manager import ensure_exclusive_qwen
from core.model_persistence import unload_qwen

class BrowserAgent(QObject):
    """
    Worker agent that runs the VLM-Browser loop.
    Intended to be moved to a QThread.
    """
    screenshot_updated = Signal(QImage)
    thinking_update = Signal(str)
    action_updated = Signal(str)
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, model_name="qwen3-vl:4b"):
        super().__init__()
        self.controller = BrowserController(headless=True) # Headed for debugging/visibility
        self.client = VLMClient(
            model_name=model_name,
            model_params={
                "temperature": 1,
                "top_k": 20,
                "top_p": 0.95
            }
        )
        self.running = False
        self.history = []

    def start_task(self, instruction: str):
        # Unload Qwen model to free VRAM for VLM
        unload_qwen("browser_agent_using_vlm")
        # Unload other models to free VRAM
        ensure_exclusive_qwen(self.client.model_name)
        
        self.running = True
        self.history = []
        
        try:
            self.controller.start()
            # Initial system prompt
            self.history.append({
                "role": "system",
                "content": self.client.construct_system_prompt()
            })
            # User instruction
            self.history.append({
                "role": "user",
                "content": instruction
            })

            # Run the loop
            self._run_loop()

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.running = False
            self.finished.emit()

    def stop(self):
        self.running = False

    def _run_loop(self):
        while self.running:
            # 1. Capture Screenshot
            b64_img = self.controller.get_screenshot()
            if not b64_img:
                time.sleep(1)
                continue

            # Update GUI with screenshot
            self._emit_screenshot(b64_img)

            # 2. Append screenshot to the LAST user message or as a new user message
            # Qwen VL expects image input.
            # We construct the message for the current turn
            current_message = {
                "role": "user",
                "content": self.history[-1]["content"] if self.history[-1]["role"] == "user" else "Assessment of the screen."
            }
            
            # If the last message was the initial instruction, we shouldn't overwrite it, 
            # but we need to attach the image to it or a new message.
            # Best practice for VLM agents:
            # 1. User says "Do X".
            # 2. Agent receives User("Do X" + Image).
            # 3. Agent output Action.
            # 4. Agent receives User(Image of result).
            
            # Let's verify if the last item has an image. If not, add it.
            # For Qwen via Ollama, images are passed in the 'images' list field of the message object?
            # Or formatted in text? Ollama VLM support usually expects "images": [b64]
            
            # Prepare messages for Ollama
            ollama_messages = []
            for msg in self.history:
                # Copy message to avoid mutating history directly with ephemeral data if needed
                m = msg.copy()
                if m["role"] == "user" and msg is self.history[-1]:
                    # Attach current screenshot to the LATEST user message (which triggers the assistant)
                    m["images"] = [b64_img]
                ollama_messages.append(m)

            # 3. Stream Response
            action_data = None
            response_text = ""
            
            for chunk in self.client.generate_action(ollama_messages):
                if chunk["type"] == "thinking":
                    self.thinking_update.emit(chunk["content"])
                elif chunk["type"] == "text":
                    # Stream normal text (reasoning or chat) to action log for visibility
                    # We might want to stream this differently if UI supported it, but for now:
                    text_chunk = chunk["content"]
                    response_text += text_chunk
                elif chunk["type"] == "action":
                    action_data = chunk["content"]
                elif chunk["type"] == "error":
                    self.error_occurred.emit(chunk["content"])
                    return

            # 4. Log Action
            # 4. Log Action
            if action_data:
                action_name = action_data.get("action", "unknown")
                log_str = f"Action: {action_name} {json.dumps(action_data)}"
                
                self.action_updated.emit(log_str)
                
                # Append assistant response to history
                # We save the full text response (thinking + tool call) to history to maintain context
                tool_call_str = f"\n<tool_call>\n{json.dumps({'name': 'computer_use', 'arguments': action_data})}\n</tool_call>"
                self.history.append({
                    "role": "assistant",
                    "content": response_text + tool_call_str
                })

                # 5. Execute Action
                if action_name == "terminate":
                    self.action_updated.emit("Task Terminated: " + action_data.get("status", "unknown"))
                    self.running = False
                    return
                
                try:
                    self.controller.execute_action(action_name, action_data)
                except Exception as e:
                    self.action_updated.emit(f"Execution Error: {e}")
                
                # 6. Prepare next turn
                self.history.append({
                    "role": "user",
                    "content": "Action executed. Here is the new screen."
                })
                
                # Wait a bit for page to settle
                time.sleep(1.0) 

            else:
                # No action found, but maybe there's a text response?
                if response_text.strip():
                    self.action_updated.emit(f"Model Reasoned: {response_text[:100]}...") # Log summary
                    # Add reasoning to history
                    self.history.append({
                        "role": "assistant",
                        "content": response_text
                    })
                    
                    # AUTOMATIC REPROMPT
                    self.action_updated.emit("Reprompting for tool call...")
                    self.history.append({
                        "role": "user",
                        "content": "You analyzed the situation but did not output a function call. Please output the <tool_call> XML block now."
                    })
                    # Loop will continue naturally? No, outer loop is 'while self.running'.
                    # We need to restart the loop logic immediately or just 'continue' to let next iteration handle it?
                    # The next iteration effectively calls client.generate_action with the new history!
                    # So 'continue' is correct.
                    continue
                else:
                    self.action_updated.emit("No action parsed and no text response.")
                    # Reprompt anyway?
                    time.sleep(1)

    def _emit_screenshot(self, b64_str):
        try:
            # Convert base64 to QImage
            # QImage.fromData expects bytes
            img_data = base64.b64decode(b64_str)
            image = QImage.fromData(img_data)
            self.screenshot_updated.emit(image)
        except Exception as e:
            print(f"Image conversion error: {e}")
            self.action_updated.emit(f"Screenshot Error: {e}")

    def cleanup(self):
        self.controller.stop()
