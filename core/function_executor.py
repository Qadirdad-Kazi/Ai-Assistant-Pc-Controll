"""
Simplified Function Executor for Wolf AI.
"""

from core.llm import route_query, should_bypass_router, http_session  # type: ignore
from core.pc_control import pc_controller  # type: ignore
from core.vision_agent import vision_agent  # type: ignore
from core.dev_agent import dev_agent  # type: ignore
from core.receptionist import receptionist  # type: ignore
from core.router import FunctionGemmaRouter  # type: ignore
from config import OLLAMA_URL, RESPONDER_MODEL  # type: ignore
import json
import re
import requests  # type: ignore
from datetime import datetime
from typing import Dict, Any

class FunctionExecutor:
    """Central executor for simplified core functions."""
    
    def __init__(self):
        # Placeholder for managers if needed later
        self.tasks_file = "tasks.json"
        self.tasks = self._load_tasks()
        self.app_map = {
            "visual studio code": "C:\\Users\\User\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
            "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            "edge": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            "safari": "C:\\Program Files\\Safari\\Application\\safari.exe",
            "notepad": "C:\\Windows\\notepad.exe",
            "word": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
            "excel": "C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE",
            "powerpoint": "C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE",
            "spotify": "C:\\Users\\User\\AppData\\Roaming\\Spotify\\spotify.exe",
            "vlc": "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
            "telegram": "C:\\Users\\User\\AppData\\Roaming\\Telegram Desktop\\Telegram.exe",
            "discord": "C:\\Users\\User\\AppData\\Local\\Discord\\app-1.0.9003\\Discord.exe",
            "slack": "C:\\Users\\User\\AppData\\Local\\slack\\app-4.23.0\\slack.exe"
        }
    
    def execute(self, func_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function and return result."""
        try:
            if func_name == "pc_control":
                return self._pc_control(params)
            elif func_name == "play_music":
                return self._play_music(params)
            elif func_name == "scaffold_website":
                return self._scaffold_website(params)
            elif func_name == "set_call_directive":
                return self._set_call_directive(params)
            elif func_name == "visual_agent":
                return self._visual_agent(params)
            elif func_name == "create_task":
                return self._create_task(params)
            elif func_name == "edit_task":
                return self._edit_task(params)
            elif func_name == "list_tasks":
                return self._list_tasks(params)
            elif func_name == "execute_task":
                return self._execute_task(params)
            elif func_name in ("thinking", "nonthinking"):
                prompt = params.get("prompt", "")
                # Check if this is a capability question
                if self._is_capability_question(prompt):
                    return self._capability_overview()
                else:
                    return {"success": True, "message": "Direct LLM response."}
            else:
                return {"success": False, "message": f"Unknown function: {func_name}"}
        except Exception as e:
            return {"success": False, "message": f"Execution error: {str(e)}"}
    
    def _is_capability_question(self, prompt: str) -> bool:
        """Check if the prompt is asking about capabilities."""
        capability_keywords = [
            "tell me about yourself", "what can you do", "who are you", "what are you",
            "your capabilities", "what do you do", "help", "abilities", "features",
            "what are your features", "introduction", "introduce yourself"
        ]
        
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in capability_keywords)
    
    def _is_app_opening_command(self, prompt: str) -> bool:
        """Check if prompt is trying to open an app but was misrouted."""
        # More aggressive detection for app opening commands
        prompt_lower = prompt.lower()
        
        # Direct app opening patterns
        open_patterns = [
            r"open\s+(\w+)",
            r"launch\s+(\w+)", 
            r"start\s+(\w+)",
            r"run\s+(\w+)"
        ]
        
        # Check for direct patterns first
        for pattern in open_patterns:
            if re.search(pattern, prompt_lower):
                print(f"[FunctionExecutor] Found app opening pattern: {pattern}")
                return True
        
        # Check for UI-related terms that indicate complex commands
        ui_terms = ["select", "choose", "profile", "search", "find", "click", "type", "navigate", "scroll", "wait"]
        
        # If any UI term is found, it's likely a complex command
        if any(term in prompt_lower for term in ui_terms):
            print(f"[FunctionExecutor] Detected UI-related command: '{prompt}'")
            return True
        
        # Check for app names in the prompt
        app_keywords = [
            "chrome", "firefox", "edge", "safari", "visual studio", "vs code", 
            "visualstudio", "notepad", "word", "excel", "powerpoint", 
            "spotify", "vlc", "telegram", "discord", "slack"
        ]
        
        # If any app name is mentioned, treat as app command
        if any(app in prompt_lower for app in app_keywords):
            print(f"[FunctionExecutor] Found app keyword in: '{prompt}'")
            return True
            
        return False
    
    def _capability_overview(self) -> Dict[str, Any]:
        """Return an overview of Wolf AI's capabilities."""
        capabilities = """I'm Wolf AI, your voice assistant! I can control your computer, manage tasks, play music, and help with complex problems.

Here's what I can do:
• Open apps like Visual Studio, Chrome, or Spotify
• Control volume, take screenshots, lock your screen
• Create and manage tasks with plain English descriptions
• Play music on YouTube or Spotify
• Find and click elements on your screen using visual AI
• Solve complex problems through reasoning
• Build websites and applications
• Have natural conversations

Just say "Hey Wolf" followed by any command. For example: "Hey Wolf, open Visual Studio" or "Hey Wolf, what can you do?"

Say "stop" or "quit" at any time to interrupt me."""
        
        return {
            "success": True,
            "message": capabilities.strip(),
            "data": {"type": "capability_overview"}
        }

    def _pc_control(self, params: Dict):
        """Handle system level commands."""
        action = params.get("action", "unknown")
        target = params.get("target", "")
        
        print(f"[FunctionExecutor] PC Control: action='{action}', target='{target}'")
        
        try:
            result = pc_controller.execute(action, target)
            result["data"] = {"action": action, "target": target}
            print(f"[FunctionExecutor] PC Control result: {result}")
            return result
        except Exception as e:
            print(f"[FunctionExecutor] PC Control error: {e}")
            return {"success": False, "message": f"PC Control error: {str(e)}"}

    def _play_music(self, params: Dict):
        """Handle music commands."""
        query = params.get("query", "unknown")
        service = params.get("service", "youtube")
        return {
            "success": True, 
            "message": f"Now playing {query} on {service}", 
            "data": {"query": query, "service": service}
        }

    def _scaffold_website(self, params: Dict):
        """Handle website scaffolding."""
        prompt = params.get("prompt", "")
        framework = params.get("framework", "html")
        
        return dev_agent.scaffold_project(prompt, framework)

    def _set_call_directive(self, params: Dict):
        """Handle expecting an incoming call."""
        caller = params.get("caller_name", "Unknown caller")
        instructions = params.get("instructions", "Say hello")
        return receptionist.add_directive(caller, instructions)

    def _visual_agent(self, params: Dict):
        """Handle visual UI interactions using VisionAgent."""
        task = params.get("task", "click on something")
        return vision_agent._find_and_click_element(task)

    def _load_tasks(self):
        """Load tasks from JSON file."""
        try:
            with open(self.tasks_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_tasks(self):
        """Save tasks to JSON file."""
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(self.tasks, f, indent=2)
            return True
        except Exception as e:
            print(f"[FunctionExecutor] Error saving tasks: {e}")
            return False

    def _create_task(self, params: Dict):
        """Create a new task."""
        title = params.get("title", "Untitled Task")
        description = params.get("description", "")
        
        task = {
            "id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": title,
            "description": description,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.tasks.append(task)
        if self._save_tasks():
            return {
                "success": True, 
                "message": f"Task '{title}' created successfully.", 
                "data": {"task_id": task["id"], "task": task}
            }
        else:
            return {"success": False, "message": "Failed to save task."}

    def _edit_task(self, params: Dict):
        """Edit an existing task."""
        task_id = params.get("task_id")
        title = params.get("title")
        description = params.get("description")
        
        for task in self.tasks:
            if task.get("id") == task_id:
                if title:
                    task["title"] = title
                if description:
                    task["description"] = description
                task["updated_at"] = datetime.now().isoformat()
                
                if self._save_tasks():
                    return {"success": True, "message": f"Task '{task_id}' updated successfully.", "data": {"task": task}}
                else:
                    return {"success": False, "message": "Failed to save updated task."}
                    
        return {"success": False, "message": f"Task '{task_id}' not found."}

    def _list_tasks(self, params: Dict):
        """List all tasks."""
        status_filter = params.get("status", None)
        
        if status_filter:
            filtered_tasks = [t for t in self.tasks if t.get("status") == status_filter]
        else:
            filtered_tasks = self.tasks
        
        return {
            "success": True,
            "message": f"Found {len(filtered_tasks)} tasks.",
            "data": {"tasks": filtered_tasks, "count": len(filtered_tasks)}
        }

    def _execute_task(self, params: Dict):
        """Execute a task using AI intelligence to understand and complete it."""
        
        task_id = params.get("task_id")
        description = params.get("description")
        
        if task_id:
            # Find task by ID
            task = next((t for t in self.tasks if t.get('id') == task_id), None)
            if not task:
                return {"success": False, "message": f"Task with ID '{task_id}' not found."}
            description = task.get('description', '')
        
        if not description:
            return {"success": False, "message": "No task description provided."}
        
        try:
            print(f"[FunctionExecutor] Executing autonomous agent task: '{description}'")
            
            prompt = f"""You are an autonomous AI executing a multi-step task on the user's computer: '{description}'.
            
            Available functions:
            - pc_control(action, target): [action: 'open_app', 'close_app', 'volume', 'lock', 'shutdown', 'command'] -> 'command' runs Powershell code in target.
            - play_music(query, service): Search and play music.
            - visual_agent(task): Use visual AI to find and click elements on screen.
            - task_complete(message): Call this EXACTLY when the goal is fully achieved!
            
            You MUST output EXACTLY ONE function call. After you output it, it will be executed and you will see the RESULT. 
            CRITICAL FORMAT RULE: You must use this exact syntax with curly braces, NO python syntax.
            CRITICAL RULE 2: NEVER output any other text or reasoning. ONLY output the function call line!
            call:function_name{{arg1:value1,arg2:value2}}
            
            Example 1 (Open App): call:pc_control{{action:open_app,target:Visual Studio Code}}
            Example 2 (Run Script): call:pc_control{{action:command,target:mkdir C:\\temp}}
            Example 3 (Finished): call:task_complete{{message:I finished everything.}}
            
            HISTORY OF EXECUTED STEPS:
            """
            
            history_str = "No steps executed yet.\n"
            success = False
            final_message = "Task stopped."
            executed_funcs = []
            results = []
            router = FunctionGemmaRouter()
            
            for step in range(10): # Max 10 steps to prevent infinite loops
                # Ask LLM for next step based on history
                try:
                    full_prompt = prompt + history_str + "\nBased on the history, what is the SINGLE next function call?"
                    print(f"[AgentLoop] Step {step+1}: Thinking...")
                    
                    response = requests.post(f"{OLLAMA_URL}/generate", json={
                        "model": RESPONDER_MODEL,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {"num_predict": 150, "temperature": 0.1}
                    }, timeout=15).json()
                    
                    raw_response = response.get("response", "").strip()
                    calls = router._parse_function_call(raw_response, description)
                    
                    if not calls:
                        history_str += f"\n- AI Output: '{raw_response}'\n- Result: ERROR - No valid function call found. Use call:function{{...}} syntax.\n"
                        continue
                        
                    func_name, route_params = calls[0] # Take strictly the first call
                    
                    if func_name == "task_complete":
                        final_message = route_params.get("message", "Task completed via agent logic.")
                        success = True
                        break
                        
                    print(f"[AgentLoop] Step {step+1}: Executing {func_name} with {route_params}")
                    executed_funcs.append(func_name)
                        
                    # Execute the function
                    result = self.execute(func_name, route_params)  # type: ignore
                    results.append(result)
                    
                    # Update history
                    res_msg = result.get("message", "No message")
                    history_str += f"\n- Step: call:{func_name}{route_params}\n- Result: {res_msg}\n"
                    
                    print(f"[AgentLoop] Step {step+1} Result: {res_msg}")
                        
                except Exception as e:
                    print(f"[AgentLoop] Error in LLM step: {e}")
                    success = False
                    final_message = f"Error communicating with AI: {e}"
                    break
            
            if not success and final_message == "Task stopped.":
                final_message = "Reached maximum steps without calling task_complete."
            
            # Update task status if we have a task_id
            if task_id:
                for task in self.tasks:
                    if task.get('id') == task_id:
                        task["status"] = "completed" if success else "failed"
                        task["updated_at"] = datetime.now().isoformat()
                        break
                self._save_tasks()
            
            result_data = {
                "success": success,
                "message": f"Agent finished! Goal: '{description}'. Result: {final_message}",
                "data": {
                    "original_task": description,
                    "ai_reasoning": history_str,
                    "executed_functions": executed_funcs,
                    "result": results[-1] if results else {}
                }
            }
            return result_data
                
        except Exception as e:
            print(f"[FunctionExecutor] Error executing task: {e}")
            return {"success": False, "message": f"Error executing task: {str(e)}"}

# Global instance
executor = FunctionExecutor()
