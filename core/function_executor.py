"""
Simplified Function Executor for Wolf AI.
"""

from typing import Dict, Any
from core.pc_control import pc_controller
from core.dev_agent import dev_agent
from core.receptionist import receptionist

class FunctionExecutor:
    """Central executor for simplified core functions."""
    
    def __init__(self):
        # Placeholder for managers if needed later
        pass

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

# Global instance
executor = FunctionExecutor()
