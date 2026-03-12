"""
Enhanced Thinking Mode Router
Provides structured multi-step reasoning when thinking mode is invoked.
"""

import json
from typing import Dict, Any, List, Tuple
from config import OLLAMA_URL, GRAY, RESET, CYAN, GREEN, YELLOW
import requests

http_session = requests.Session()


class EnhancedThinkingRouter:
    """Routes thinking queries through specialized reasoning stages."""
    
    # Reasoning strategies
    STRATEGIES = {
        "decomposition": {
            "name": "Break-Down Approach",
            "description": "Break complex problem into smaller sub-problems",
            "steps": 5
        },
        "analogy": {
            "name": "Analogy/Pattern Matching",
            "description": "Find similar problems and apply known solutions",
            "steps": 3
        },
        "socratic": {
            "name": "Socratic Method",
            "description": "Ask clarifying questions to develop deeper understanding",
            "steps": 4
        },
        "synthesis": {
            "name": "Synthesis Method",
            "description": "Build understanding from first principles",
            "steps": 5
        },
        "critical": {
            "name": "Critical Analysis",
            "description": "Evaluate from multiple perspectives with counterarguments",
            "steps": 4
        }
    }
    
    def __init__(self, model_name: str = "llama3.2:3b"):
        self.model_name = model_name
        self.reasoning_cache = {}
    
    def route_thinking_query(self, prompt: str, depth: str = "medium") -> Dict[str, Any]:
        """
        Route thinking query through appropriate reasoning stages.
        Depths: shallow (2 steps), medium (3-4 steps), deep (5+ steps)
        """
        print(f"{CYAN}[EnhancedThinking] Routing thinking query with depth: {depth}{RESET}")
        
        # Check cache
        cache_key = f"{prompt}_{depth}"
        if cache_key in self.reasoning_cache:
            print(f"{CYAN}[EnhancedThinking] Using cached reasoning result{RESET}")
            return self.reasoning_cache[cache_key]
        
        # Select reasoning strategy
        strategy = self._select_strategy(prompt)
        
        # Execute reasoning with selected strategy
        thinking_result = self._execute_thinking_strategy(prompt, strategy, depth)
        
        # Cache result
        self.reasoning_cache[cache_key] = thinking_result
        
        return thinking_result
    
    def _select_strategy(self, prompt: str) -> str:
        """Select best reasoning strategy for the prompt."""
        prompt_lower = prompt.lower()
        
        # Pattern detection
        if any(word in prompt_lower for word in ["compare", "versus", "difference", "similar"]):
            return "analogy"
        elif any(word in prompt_lower for word in ["design", "architect", "build", "create"]):
            return "synthesis"
        elif any(word in prompt_lower for word in ["why", "reason", "explain", "cause"]):
            return "socratic"
        elif any(word in prompt_lower for word in ["evaluate", "assess", "criticize", "against"]):
            return "critical"
        else:
            return "decomposition"  # Default
    
    def _execute_thinking_strategy(self, prompt: str, strategy: str, depth: str) -> Dict[str, Any]:
        """Execute thinking with specified strategy."""
        print(f"{GREEN}[EnhancedThinking] Using strategy: {self.STRATEGIES[strategy]['name']}{RESET}")
        
        if strategy == "decomposition":
            return self._decomposition_thinking(prompt, depth)
        elif strategy == "analogy":
            return self._analogy_thinking(prompt, depth)
        elif strategy == "socratic":
            return self._socratic_thinking(prompt, depth)
        elif strategy == "synthesis":
            return self._synthesis_thinking(prompt, depth)
        elif strategy == "critical":
            return self._critical_thinking(prompt, depth)
        else:
            return self._decomposition_thinking(prompt, depth)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Reasoning Strategies Implementation
    # ─────────────────────────────────────────────────────────────────────────
    
    def _decomposition_thinking(self, prompt: str, depth: str) -> Dict[str, Any]:
        """Break down problem into sub-problems and solve each."""
        print(f"{CYAN}[Thinking] Decomposition approach: breaking down the problem${RESET}")
        
        reasoning_prompt = f"""Using DECOMPOSITION approach, break this problem into smaller parts:

Problem: {prompt}

1. What are the key components or sub-problems?
2. How do they relate to each other?
3. Solve each component systematically
4. Integrate solutions
5. Verify the complete solution

Provide structured step-by-step breakdown:"""
        
        response = self._call_llm(reasoning_prompt, enable_thinking=True)
        
        return {
            "strategy": "decomposition",
            "depth": depth,
            "reasoning": response,
            "stages": self._extract_stages(response, 5)
        }
    
    def _analogy_thinking(self, prompt: str, depth: str) -> Dict[str, Any]:
        """Find similar problems and apply known solutions."""
        print(f"{CYAN}[Thinking] Analogy approach: finding similar problems${RESET}")
        
        reasoning_prompt = f"""Using ANALOGY approach, find similar problems:

Problem: {prompt}

1. What is this problem similar to?
2. What well-known problems does it resemble?
3. What solutions exist for those problems?
4. How can those solutions apply here?
5. What adaptations are needed?

Provide analogy-based reasoning:"""
        
        response = self._call_llm(reasoning_prompt, enable_thinking=True)
        
        return {
            "strategy": "analogy",
            "depth": depth,
            "reasoning": response,
            "analogies": self._extract_analogies(response)
        }
    
    def _socratic_thinking(self, prompt: str, depth: str) -> Dict[str, Any]:
        """Ask clarifying questions to develop understanding."""
        print(f"{CYAN}[Thinking] Socratic approach: questioning for deeper understanding${RESET}")
        
        reasoning_prompt = f"""Using SOCRATIC METHOD:

Question: {prompt}

Generate clarifying questions that reveal deeper understanding:
1. What exactly are you asking?
2. What assumptions are you making?
3. What would challenge your initial answer?
4. What would prove your answer wrong?

Then provide the answer informed by these questions:"""
        
        response = self._call_llm(reasoning_prompt, enable_thinking=True)
        
        return {
            "strategy": "socratic",
            "depth": depth,
            "reasoning": response,
            "questions": self._extract_questions(response)
        }
    
    def _synthesis_thinking(self, prompt: str, depth: str) -> Dict[str, Any]:
        """Build understanding from first principles."""
        print(f"{CYAN}[Thinking] Synthesis approach: building from first principles${RESET}")
        
        reasoning_prompt = f"""Using SYNTHESIS from first principles:

Question: {prompt}

1. What are the fundamental facts?
2. What core principles apply?
3. How do these principles combine?
4. What follows logically?
5. What is the complete picture?

Build up understanding from basics:"""
        
        response = self._call_llm(reasoning_prompt, enable_thinking=True)
        
        return {
            "strategy": "synthesis",
            "depth": depth,
            "reasoning": response,
            "principles": self._extract_principles(response)
        }
    
    def _critical_thinking(self, prompt: str, depth: str) -> Dict[str, Any]:
        """Evaluate from multiple perspectives with counterarguments."""
        print(f"{CYAN}[Thinking] Critical approach: multi-perspective analysis${RESET}")
        
        reasoning_prompt = f"""Using CRITICAL ANALYSIS:

Question: {prompt}

Analyze from multiple angles:
1. What is the main argument?
2. What evidence supports it?
3. What are strong counterarguments?
4. What are weaknesses in the logic?
5. What is the most balanced conclusion?

Provide balanced critical analysis:"""
        
        response = self._call_llm(reasoning_prompt, enable_thinking=True)
        
        return {
            "strategy": "critical",
            "depth": depth,
            "reasoning": response,
            "perspectives": self._extract_perspectives(response)
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # Advanced Thinking Modes
    # ─────────────────────────────────────────────────────────────────────────
    
    def multi_stage_reasoning(self, prompt: str, stages: int = 3) -> Dict[str, Any]:
        """
        Perform reasoning in multiple stages, building on previous reasoning.
        """
        print(f"{CYAN}[EnhancedThinking] Multi-stage reasoning with {stages} stages${RESET}")
        
        stage_results = []
        current_context = prompt
        
        for stage_num in range(1, stages + 1):
            stage_prompt = f"""Stage {stage_num}/{stages} of reasoning:

Context: {current_context}

Provide the next level of reasoning that builds on what we know, moving deeper into analysis:"""
            
            stage_response = self._call_llm(stage_prompt, enable_thinking=True)
            stage_results.append({
                "stage": stage_num,
                "reasoning": stage_response
            })
            
            # Update context for next stage
            current_context = f"Previous findings: {stage_response}"
        
        return {
            "approach": "multi_stage",
            "total_stages": stages,
            "stage_results": stage_results,
            "final_synthesis": self._synthesize_stages(stage_results)
        }
    
    def adversarial_thinking(self, prompt: str) -> Dict[str, Any]:
        """
        Generate opposing viewpoints and then resolve them.
        """
        print(f"{CYAN}[EnhancedThinking] Adversarial reasoning: generating opposing viewpoints${RESET}")
        
        # Generate supporting argument
        support_prompt = f"""Generate the STRONGEST argument IN FAVOR of: {prompt}

Be thorough and convincing, even if you don't agree."""
        
        support_reasoning = self._call_llm(support_prompt, enable_thinking=True)
        
        # Generate opposing argument
        oppose_prompt = f"""Generate the STRONGEST argument AGAINST: {prompt}

Be thorough and convincing, even if you don't agree."""
        
        oppose_reasoning = self._call_llm(oppose_prompt, enable_thinking=True)
        
        # Synthesize and resolve
        synthesis_prompt = f"""Given these two perspectives:

FOR: {support_reasoning[:300]}...

AGAINST: {oppose_reasoning[:300]}...

Provide the most balanced and nuanced conclusion:"""
        
        synthesis = self._call_llm(synthesis_prompt, enable_thinking=True)
        
        return {
            "approach": "adversarial",
            "supporting_argument": support_reasoning,
            "opposing_argument": oppose_reasoning,
            "balanced_conclusion": synthesis
        }
    
    def recursive_why_analysis(self, prompt: str, depth: int = 3) -> Dict[str, Any]:
        """
        Recursively ask 'why' to understand root causes.
        """
        print(f"{CYAN}[EnthancedThinking] Recursive 'why' analysis, depth: {depth}${RESET}")
        
        why_chain = [{"level": 0, "question": prompt}]
        current_question = prompt
        
        for level in range(1, depth + 1):
            why_prompt = f"""The previous question/statement was: {current_question}

Ask 'WHY?' to go one level deeper in understanding the root cause:"""
            
            why_response = self._call_llm(why_prompt, enable_thinking=True)
            why_chain.append({"level": level, "analysis": why_response})
            
            # Extract the next question for the chain
            current_question = why_response[:200]
        
        return {
            "approach": "recursive_why",
            "depth": depth,
            "why_chain": why_chain,
            "root_cause": why_chain[-1].get("analysis", "Analysis complete")
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    def _call_llm(self, prompt: str, enable_thinking: bool = False) -> str:
        """Call LLM for thinking."""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "5m"
            }
            
            response = http_session.post(
                f"{OLLAMA_URL}/generate",
                json=payload,
                timeout=90  # Longer timeout for thinking mode
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return response_data.get("response", "")
            else:
                print(f"{GRAY}[EnhancedThinking] LLM call failed{RESET}")
                return ""
        
        except Exception as e:
            print(f"{GRAY}[EnhancedThinking] Error: {e}{RESET}")
            return ""
    
    def _extract_stages(self, text: str, expected_count: int = 5) -> List[str]:
        """Extract numbered stages from reasoning."""
        import re
        lines = text.split("\n")
        stages = [line.strip() for line in lines if re.match(r'^\d+\.\s', line.strip())]
        return stages[:expected_count]
    
    def _extract_analogies(self, text: str) -> List[str]:
        """Extract analogies from reasoning."""
        analogies = []
        lines = text.split("\n")
        for line in lines:
            if "similar" in line.lower() or "like" in line.lower() or "analogy" in line.lower():
                analogies.append(line.strip())
        return analogies[:3]
    
    def _extract_questions(self, text: str) -> List[str]:
        """Extract questions from reasoning."""
        import re
        questions = [line.strip() for line in text.split("\n") if line.strip().endswith("?")]
        return questions[:4]
    
    def _extract_principles(self, text: str) -> List[str]:
        """Extract core principles from reasoning."""
        principles = []
        lines = text.split("\n")
        for line in lines:
            if "principle" in line.lower() or "law" in line.lower() or "rule" in line.lower():
                principles.append(line.strip())
        return principles[:3]
    
    def _extract_perspectives(self, text: str) -> Dict[str, str]:
        """Extract different perspectives from reasoning."""
        perspectives = {
            "pro": "",
            "con": ""
        }
        
        if "for:" in text.lower():
            perspectives["pro"] = text.lower().split("for:")[1].split("\n")[0][:100]
        if "against:" in text.lower():
            perspectives["con"] = text.lower().split("against:")[1].split("\n")[0][:100]
        
        return perspectives
    
    def _synthesize_stages(self, stage_results: List[Dict]) -> str:
        """Synthesize final conclusion from all stages."""
        if not stage_results:
            return "No stages to synthesize"
        
        final_stage = stage_results[-1]
        key = "reasoning" if "reasoning" in final_stage else "analysis"
        return final_stage.get(key, "Synthesis complete")[:200]


# Global instance
enhanced_thinking_router = EnhancedThinkingRouter()
