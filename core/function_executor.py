"""
Simplified Function Executor for Wolf AI.
"""

from typing import Dict, Any

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
        # Actual implementation will be in core/pc_control.py later
        return {
            "success": True, 
            "message": f"System action: {action} {target}", 
            "data": {"action": action, "target": target}
        }

    def _play_music(self, params: Dict):
        """Handle music commands."""
        query = params.get("query", "unknown")
        service = params.get("service", "youtube")
        return {
            "success": True, 
            "message": f"Now playing {query} on {service}", 
            "data": {"query": query, "service": service}
        }

# Global instance
executor = FunctionExecutor()
