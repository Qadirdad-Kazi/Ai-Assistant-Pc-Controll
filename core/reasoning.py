"""
Chain-of-Thought Reasoning Module
Provides self-thinking and multi-step reasoning capabilities to the AI assistant.
"""

import json
import threading
from typing import Dict, Any, List, Optional
from config import OLLAMA_URL, GREEN, CYAN, YELLOW, GRAY, RESET, RESPONDER_MODEL
import requests

# HTTP session for faster requests
http_session = requests.Session()


class ChainOfThoughtReasoner:
    """Handles structured reasoning with multiple steps."""
    
    def __init__(self, model_name: str = "qwen3-vl:4b"):
        self.model_name = model_name
        self.reasoning_steps = []
        self.current_thinking = ""
    
    def think_step_by_step(self, user_query: str, context: str = "") -> Dict[str, Any]:
        """
        Process a query with explicit step-by-step reasoning.
        Returns structured thinking output.
        """
        print(f"{CYAN}[CoT] Starting chain-of-thought reasoning...{RESET}")
        
        thinking_prompt = f"""Think about this step-by-step:

User asked: {user_query}

{f'Context: {context}' if context else ''}

1. What is the user actually asking for?
2. What information do I need to complete this task?
3. What are the main steps I need to take?
4. What assumptions am I making?
5. What could go wrong, and how will I verify the result?

Be precise and structured. Break each step clearly."""
        
        thinking_response = self._call_llm(
            thinking_prompt, 
            model=self.model_name,
            enable_thinking=True
        )
        
        # Parse and structure the thinking
        structured_thinking = self._parse_thinking(thinking_response)
        self.reasoning_steps.append(structured_thinking)
        
        return {
            "success": True,
            "thinking": structured_thinking,
            "steps": self._extract_steps(structured_thinking),
            "assumptions": self._extract_assumptions(structured_thinking),
            "verification_plan": self._extract_verification(structured_thinking)
        }
    
    def reason_about_result(self, query: str, action: str, result: Any, thinking_context: str = "") -> Dict[str, Any]:
        """
        Verify result by reasoning about whether it answers the original query.
        """
        print(f"{CYAN}[CoT] Reasoning about result...{RESET}")
        
        verification_prompt = f"""Evaluate this outcome:

Original query: {query}
Action taken: {action}
Result: {json.dumps(result) if isinstance(result, dict) else str(result)}

{f'Previous thinking: {thinking_context}' if thinking_context else ''}

1. Did this action address the original query?
2. Is the result complete and accurate?
3. Rate confidence (1-10): __
4. What's missing (if anything)?
5. Should we take additional steps?

Be honest about confidence level."""
        
        evaluation = self._call_llm(
            verification_prompt,
            model=self.model_name,
            enable_thinking=True
        )
        
        return {
            "evaluation": evaluation,
            "confidence": self._extract_confidence(evaluation),
            "is_complete": self._is_result_sufficient(evaluation),
            "next_steps": self._extract_next_steps(evaluation)
        }
    
    def self_correct(self, query: str, action: str, failed_result: Any, thinking_context: str = "") -> Dict[str, Any]:
        """
        When a result is unsatisfactory, reason about better approaches.
        """
        print(f"{YELLOW}[CoT] Self-correction: reconsidering approach...{RESET}")
        
        correction_prompt = f"""The initial approach didn't work well.

Original query: {query}
First approach: {action}
Result: {json.dumps(failed_result) if isinstance(failed_result, dict) else str(failed_result)}

{f'Previous thinking: {thinking_context}' if thinking_context else ''}

1. Why did the first approach fail?
2. What alternative approaches could work?
3. What did I miss in my initial reasoning?
4. Rank the alternative approaches by likelihood of success.
5. Recommend the best alternative.

Think critically and consider edge cases."""
        
        alternative_reasoning = self._call_llm(
            correction_prompt,
            model=self.model_name,
            enable_thinking=True
        )
        
        return {
            "alternative_reasoning": alternative_reasoning,
            "recommended_action": self._extract_recommendation(alternative_reasoning),
            "hidden_assumptions": self._extract_hidden_assumptions(alternative_reasoning),
            "risk_assessment": self._extract_risks(alternative_reasoning)
        }
    
    def validate_reasoning_chain(self, query: str, steps: List[str], final_response: str) -> Dict[str, Any]:
        """
        Validate that all reasoning steps are logically connected and consistent.
        """
        print(f"{CYAN}[CoT] Validating reasoning chain consistency...{RESET}")
        
        validation_prompt = f"""Validate this reasoning chain:

Query: {query}

Steps taken:
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(steps))}

Final response: {final_response}

1. Are all steps logically connected?
2. Are there any contradictions?
3. Did we fully address the original query?
4. Is the logic sound (rate 1-10)?
5. Are there missing links in the reasoning?

Provide detailed validation feedback."""
        
        validation_result = self._call_llm(
            validation_prompt,
            model=self.model_name,
            enable_thinking=True
        )
        
        return {
            "is_valid": "valid" in validation_result.lower() or "sound" in validation_result.lower(),
            "validation_feedback": validation_result,
            "logic_score": self._extract_score(validation_result),
            "issues": self._extract_issues(validation_result)
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    def _call_llm(self, prompt: str, model: str = None, enable_thinking: bool = False) -> str:
        """Call LLM with the given prompt."""
        if model is None:
            model = self.model_name
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "think": enable_thinking,
                "keep_alive": "5m"
            }
            
            response = http_session.post(
                f"{OLLAMA_URL}/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return response_data.get("response", "")
            else:
                print(f"{GRAY}[CoT] LLM call failed with status {response.status_code}{RESET}")
                return ""
        
        except Exception as e:
            print(f"{GRAY}[CoT] LLM error: {e}{RESET}")
            return ""
    
    def _parse_thinking(self, thinking_text: str) -> Dict[str, Any]:
        """Parse thinking output into structured format."""
        return {
            "raw_thinking": thinking_text,
            "parsed_at": len(self.reasoning_steps)
        }
    
    def _extract_steps(self, thinking: Dict[str, Any]) -> List[str]:
        """Extract numbered steps from thinking."""
        lines = thinking.get("raw_thinking", "").split("\n")
        steps = [line.strip() for line in lines if line.strip() and any(c.isdigit() for c in line[:3])]
        return steps[:5]  # Return first 5 steps
    
    def _extract_assumptions(self, thinking: Dict[str, Any]) -> List[str]:
        """Extract assumptions from thinking."""
        text = thinking.get("raw_thinking", "").lower()
        assumptions = []
        if "assume" in text:
            lines = text.split("\n")
            assumptions = [l.strip() for l in lines if "assume" in l]
        return assumptions
    
    def _extract_verification(self, thinking: Dict[str, Any]) -> str:
        """Extract verification plan."""
        text = thinking.get("raw_thinking", "")
        lines = text.split("\n")
        for line in lines:
            if "verif" in line.lower():
                return line.strip()
        return "Standard verification applied"
    
    def _extract_confidence(self, evaluation: str) -> int:
        """Extract confidence score from evaluation."""
        import re
        matches = re.findall(r'(\d+)\s*(?:/10|out of 10)?', evaluation)
        if matches:
            try:
                return min(int(matches[0]), 10)
            except:
                return 5
        return 5
    
    def _is_result_sufficient(self, evaluation: str) -> bool:
        """Check if result is sufficient."""
        positive_words = ["complete", "sufficient", "good", "well", "yes", "addressed", "satisfied"]
        return any(word in evaluation.lower() for word in positive_words)
    
    def _extract_next_steps(self, evaluation: str) -> List[str]:
        """Extract recommended next steps."""
        lines = evaluation.split("\n")
        next_steps = [l.strip() for l in lines if "step" in l.lower() or "should" in l.lower()]
        return next_steps[:3]
    
    def _extract_recommendation(self, reasoning: str) -> str:
        """Extract recommended action."""
        lines = reasoning.split("\n")
        for line in lines:
            if "recommend" in line.lower() or "best" in line.lower():
                return line.strip()
        return "Reconsider the approach"
    
    def _extract_hidden_assumptions(self, reasoning: str) -> List[str]:
        """Extract hidden assumptions that were missed."""
        lines = reasoning.split("\n")
        assumptions = [l.strip() for l in lines if "assume" in l.lower() or "missed" in l.lower()]
        return assumptions[:3]
    
    def _extract_risks(self, reasoning: str) -> List[str]:
        """Extract risk assessment."""
        lines = reasoning.split("\n")
        risks = [l.strip() for l in lines if "risk" in l.lower() or "danger" in l.lower() or "fail" in l.lower()]
        return risks[:3]
    
    def _extract_score(self, validation: str) -> int:
        """Extract logic score."""
        import re
        matches = re.findall(r'(\d+)\s*(?:/10|out of 10)?', validation)
        if matches:
            try:
                return min(int(matches[0]), 10)
            except:
                return 7
        return 7
    
    def _extract_issues(self, validation: str) -> List[str]:
        """Extract validation issues."""
        lines = validation.split("\n")
        issues = [l.strip() for l in lines if "issue" in l.lower() or "problem" in l.lower() or "missing" in l.lower()]
        return issues[:3]
    
    def get_reasoning_history(self) -> List[Dict[str, Any]]:
        """Get all reasoning steps from this session."""
        return self.reasoning_steps


# Global instance
reasoning_engine = ChainOfThoughtReasoner()
