"""
Simplified Function Executor for Wolf AI.
"""

from typing import Dict, Any
from core.pc_control import pc_controller
from core.dev_agent import dev_agent
from core.receptionist import receptionist
from core.vision_agent import vision_agent
import json
from datetime import datetime

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
                return {"success": True, "message": "Direct LLM response."}
            else:
                return {"success": False, "message": f"Unknown function: {func_name}"}
        except Exception as e:
            return {"success": False, "message": f"Execution error: {str(e)}"}

    def _pc_control(self, params: Dict):
        """Handle system level commands."""
        action = params.get("action", "unknown")
        target = params.get("target", "")
        
        result = pc_controller.execute(action, target)
        result["data"] = {"action": action, "target": target}
        return result

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
        """Execute a task by ID or description."""
        from core.llm import route_query
        
        task_id = params.get("task_id")
        description = params.get("description")
        
        if task_id:
            # Find task by ID
            task = next((t for t in self.tasks if t.get("id") == task_id), None)
            if not task:
                return {"success": False, "message": f"Task with ID '{task_id}' not found."}
            description = task.get("description", "")
        
        if not description:
            return {"success": False, "message": "No task description provided."}
        
        try:
            # Route the task description through the existing system
            func_name, route_params = route_query(description)
            
            # Execute the routed function
            result = self.execute(func_name, route_params)
            
            # Update task status if we have a task_id
            if task_id:
                for task in self.tasks:
                    if task.get("id") == task_id:
                        task["status"] = "completed" if result.get("success") else "failed"
                        task["updated_at"] = datetime.now().isoformat()
                        break
                self._save_tasks()
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"Task executed successfully. {result.get('message', '')}",
                    "data": {"executed_function": func_name, "result": result}
                }
            else:
                return {
                    "success": False,
                    "message": f"Task execution failed: {result.get('message', 'Unknown error')}",
                    "data": {"executed_function": func_name, "result": result}
                }
                
        except Exception as e:
            return {"success": False, "message": f"Error executing task: {str(e)}"}

# Global instance
executor = FunctionExecutor()
