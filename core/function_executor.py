"""
Simplified Function Executor for Wolf AI.
"""

from core.llm import route_query, should_bypass_router, http_session
from core.pc_control import pc_controller
from core.vision_agent import vision_agent
import json
import re
from datetime import datetime
from typing import Dict, Any

class FunctionExecutor:
    """Central executor for simplified core functions."""
    
    def __init__(self):
        # Placeholder for managers if needed later
        self.tasks_file = "tasks.json"
        self.tasks = self._load_tasks()

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
            elif func_name == "list_tasks":
                return self._list_tasks(params)
            elif func_name == "execute_task":
                return self._execute_task(params)
            elif func_name in ("thinking", "nonthinking"):
                prompt = params.get("prompt", "")
                # Check if this is a capability question
                if self._is_capability_question(prompt):
                    return self._capability_overview()
                # Check if this is an app opening command that was misrouted
                elif self._is_app_opening_command(prompt):
                    print(f"[FunctionExecutor] Detected misrouted app command: '{prompt}'")
                    return self._pc_control({"action": "open_app", "target": prompt})
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
        return vision_agent.execute_visual_task(task)

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
        from core.llm import route_query
        
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
            print(f"[FunctionExecutor] Executing task with AI: '{description}'")
            
            # Use AI to understand the task and break it down into steps
            func_name, route_params = route_query(description)
            
            print(f"[FunctionExecutor] AI routed task to: {func_name} with params: {route_params}")
            
            # Execute the routed function
            result = self.execute(func_name, route_params)
            
            # Update task status if we have a task_id
            if task_id:
                for task in self.tasks:
                    if task.get('id') == task_id:
                        task["status"] = "completed" if result.get("success") else "failed"
                        task["updated_at"] = datetime.now().isoformat()
                        break
                self._save_tasks()
            
            # Add AI reasoning to the result
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"Task completed successfully! I understood: '{description}' and executed: {func_name}. {result.get('message', '')}",
                    "data": {
                        "original_task": description,
                        "ai_reasoning": f"Analyzed task and determined to use {func_name}",
                        "executed_function": func_name,
                        "result": result
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"Task execution failed. I tried: {func_name} but: {result.get('message', 'Unknown error')}",
                    "data": {
                        "original_task": description,
                        "ai_reasoning": f"Analyzed task and attempted to use {func_name}",
                        "executed_function": func_name,
                        "result": result
                    }
                }
                
        except Exception as e:
            print(f"[FunctionExecutor] Error executing task: {e}")
            return {"success": False, "message": f"Error executing task: {str(e)}"}

# Global instance
executor = FunctionExecutor()
