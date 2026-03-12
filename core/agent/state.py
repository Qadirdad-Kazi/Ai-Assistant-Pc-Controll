from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AgentAction(BaseModel):
    """Structured action for the agent to take."""
    tool_name: str = Field(description="Name of the tool to call")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")
    thought: str = Field(description="Internal reasoning for this action")

class AgentState(BaseModel):
    """State managed by LangGraph."""
    task_id: str
    description: str
    history: List[Dict[str, Any]] = Field(default_factory=list)
    steps_taken: int = 0
    max_steps: int = 15
    final_result: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    current_thought: Optional[str] = None
