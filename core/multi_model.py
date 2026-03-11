"""
Multi-Model Reasoning Pipeline
Routes queries to specialized models based on complexity and task type.
"""

import json
import re
from typing import Dict, Any, List, Tuple, Optional
from config import OLLAMA_URL, GRAY, RESET, CYAN, GREEN, YELLOW
import requests

http_session = requests.Session()


class ComplexityAnalyzer:
    """Analyzes query complexity to determine best model."""
    
    COMPLEXITY_KEYWORDS = {
        "simple": ["hello", "hi", "what is", "where is", "when is", "who is", "how much", "yes", "no"],
        "medium": ["explain", "compare", "analyze", "calculate", "create", "write", "summarize"],
        "complex": ["design", "architect", "optimize", "debug", "refactor", "implement", "solve", "predict"]
    }
    
    def __init__(self):
        self.analysis_cache = {}
    
    def analyze_complexity(self, query: str) -> Tuple[str, float]:
        """
        Analyze query complexity.
        Returns: (complexity_level, confidence_score)
        """
        # Check cache
        if query in self.analysis_cache:
            return self.analysis_cache[query]
        
        query_lower = query.lower()
        
        # Count keyword matches for each level
        scores = {
            "simple": self._count_keyword_matches(query_lower, self.COMPLEXITY_KEYWORDS["simple"]),
            "medium": self._count_keyword_matches(query_lower, self.COMPLEXITY_KEYWORDS["medium"]),
            "complex": self._count_keyword_matches(query_lower, self.COMPLEXITY_KEYWORDS["complex"])
        }
        
        # Check for indicators
        mathematical = bool(re.search(r'\d+[\+\-\*/]|\bsum\b|\bcalculate\b|\balgorithm\b', query_lower))
        reasoning = "think" in query_lower or "reason" in query_lower or "logic" in query_lower
        creative = "create" in query_lower or "write" in query_lower or "generate" in query_lower
        
        if mathematical:
            scores["complex"] += 2
        if reasoning and not creative:
            scores["complex"] += 1
        if creative:
            scores["medium"] += 1
        
        # Query length indicator
        query_words = len(query.split())
        if query_words < 5:
            scores["simple"] += 1
        elif query_words > 30:
            scores["complex"] += 1
        
        # Determine complexity level
        max_score = max(scores.values())
        if max_score == 0:
            complexity = "simple"
            confidence = 0.5
        else:
            complexity = [k for k, v in scores.items() if v == max_score][0]
            confidence = max_score / (sum(scores.values()) + 1)
        
        result = (complexity, confidence)
        self.analysis_cache[query] = result
        
        return result
    
    def _count_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """Count keyword matches in text."""
        count = 0
        for keyword in keywords:
            # Use word boundary for more precise matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count
    
    def detect_task_type(self, query: str) -> str:
        """Detect specific task type."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["code", "program", "debug", "error"]):
            return "coding"
        elif any(word in query_lower for word in ["math", "calculate", "solve", "equation"]):
            return "mathematical"
        elif any(word in query_lower for word in ["creative", "write", "poem", "story", "generate"]):
            return "creative"
        elif any(word in query_lower for word in ["image", "visual", "see", "look"]):
            return "vision"
        elif any(word in query_lower for word in ["compare", "difference", "vs", "better"]):
            return "comparison"
        else:
            return "general"


class MultiModelReasoner:
    """Routes queries to optimal models based on analysis."""
    
    # Model definitions with strengths
    MODELS = {
        "fast": {
            "name": "gemma:2b",
            "strengths": ["fast responses", "simple queries", "quick reasoning"],
            "latency": "low",
            "reasoning_depth": "shallow"
        },
        "balanced": {
            "name": "mistral:7b",
            "strengths": ["balanced analysis", "medium complexity", "general purpose"],
            "latency": "medium",
            "reasoning_depth": "medium"
        },
        "deep": {
            "name": "qwen3-vl:4b",
            "strengths": ["complex reasoning", "detailed analysis", "vision capabilities"],
            "latency": "high",
            "reasoning_depth": "deep"
        },
        "specialized": {
            "name": "neural-chat:7b",
            "strengths": ["creative content", "conversational", "nuanced understanding"],
            "latency": "medium",
            "reasoning_depth": "medium"
        }
    }
    
    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()
        self.usage_log = []
    
    def select_model(self, query: str, task_type: str = "general") -> Tuple[str, Dict[str, Any]]:
        """
        Select optimal model for query.
        Returns: (model_name, model_info)
        """
        print(f"{CYAN}[MultiModel] Analyzing query for optimal model selection...{RESET}")
        
        # Analyze complexity
        complexity, confidence = self.complexity_analyzer.analyze_complexity(query)
        
        # Detect task type
        if task_type == "general":
            task_type = self.complexity_analyzer.detect_task_type(query)
        
        print(f"{CYAN}[MultiModel] Complexity: {complexity} (confidence: {confidence:.2f}), Task: {task_type}{RESET}")
        
        # Select model based on complexity and task
        if task_type == "vision":
            selected_model = "deep"
        elif task_type == "coding":
            selected_model = "balanced" if complexity == "simple" else "deep"
        elif task_type == "mathematical":
            selected_model = "deep"
        elif task_type == "creative":
            selected_model = "specialized"
        elif complexity == "simple":
            selected_model = "fast"
        elif complexity == "medium":
            selected_model = "balanced"
        else:  # complex
            selected_model = "deep"
        
        model_info = self.MODELS[selected_model].copy()
        model_info.update({
            "selected_for": task_type,
            "complexity_level": complexity,
            "confidence": confidence
        })
        
        print(f"{GREEN}[MultiModel] Selected model: {model_info['name']} ({selected_model}){RESET}")
        
        return model_info["name"], model_info
    
    def route_with_reasoning_depth(self, query: str, requested_depth: str = "medium") -> Dict[str, Any]:
        """
        Route query with specified reasoning depth.
        Depths: "fast" (1 step), "medium" (3 steps), "deep" (5+ steps)
        """
        if requested_depth == "fast":
            model = self.MODELS["fast"]["name"]
            reasoning_steps = 1
        elif requested_depth == "deep":
            model = self.MODELS["deep"]["name"]
            reasoning_steps = 5
        else:  # medium
            model = self.MODELS["balanced"]["name"]
            reasoning_steps = 3
        
        return {
            "model": model,
            "reasoning_steps": reasoning_steps,
            "depth": requested_depth,
            "temperature": 0.5 if requested_depth == "fast" else 0.7
        }
    
    def get_specialized_reasoning(self, query: str, focus_area: str) -> Optional[str]:
        """
        Get reasoning from specialized model for specific area.
        Focus areas: "logic", "creativity", "code", "analysis"
        """
        print(f"{CYAN}[MultiModel] Generating specialized reasoning for: {focus_area}{RESET}")
        
        if focus_area == "code":
            model = "mistral:7b"
            prompt = f"""As a code specialist, analyze this query and provide deep reasoning:
{query}

Provide structured analysis suitable for code generation or debugging."""
        
        elif focus_area == "creativity":
            model = "neural-chat:7b"
            prompt = f"""As a creative specialist, analyze this query:
{query}

Provide imaginative, nuanced reasoning that considers multiple perspectives."""
        
        elif focus_area == "logic":
            model = "qwen3-vl:4b"
            prompt = f"""As a logic specialist, analyze this query:
{query}

Provide step-by-step logical reasoning with clear premises and conclusions."""
        
        elif focus_area == "analysis":
            model = "mistral:7b"
            prompt = f"""As an analytical specialist, analyze this query:
{query}

Provide detailed analysis considering multiple dimensions and implications."""
        
        else:
            return None
        
        try:
            response = http_session.post(
                f"{OLLAMA_URL}/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                    "keep_alive": "5m"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
        
        except Exception as e:
            print(f"{GRAY}[MultiModel] Specialized reasoning failed: {e}{RESET}")
        
        return None
    
    def compare_model_responses(self, query: str) -> Dict[str, Any]:
        """
        Get responses from multiple models and compare.
        Useful for complex decisions or validation.
        """
        print(f"{CYAN}[MultiModel] Getting responses from multiple models for comparison...{RESET}")
        
        responses = {}
        
        for model_key in ["fast", "balanced", "deep"]:
            model_name = self.MODELS[model_key]["name"]
            
            try:
                response = http_session.post(
                    f"{OLLAMA_URL}/generate",
                    json={
                        "model": model_name,
                        "prompt": query,
                        "stream": False,
                        "keep_alive": "5m"
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    responses[model_key] = {
                        "model": model_name,
                        "response": response.json().get("response", "")[:300]  # Truncate
                    }
            
            except Exception as e:
                print(f"{GRAY}[MultiModel] Failed to get response from {model_name}: {e}{RESET}")
        
        # Rank responses by length and coherence (simple heuristic)
        ranked = sorted(
            responses.items(),
            key=lambda x: len(x[1]["response"]),
            reverse=True
        )
        
        return {
            "responses": dict(ranked),
            "recommended": ranked[0][0] if ranked else None,
            "count": len(responses)
        }
    
    def adaptive_model_selection(self, query: str, user_model_preference: Optional[str] = None, 
                                  time_constraint: Optional[float] = None) -> Dict[str, Any]:
        """
        Adaptive model selection considering user preferences and constraints.
        """
        # Base selection
        model_name, model_info = self.select_model(query)
        
        # Apply user preference if specified
        if user_model_preference in self.MODELS:
            print(f"{YELLOW}[MultiModel] Applying user model preference: {user_model_preference}{RESET}")
            model_name = self.MODELS[user_model_preference]["name"]
            model_info = self.MODELS[user_model_preference].copy()
        
        # Apply time constraint
        if time_constraint:
            if time_constraint < 1:
                model_name = self.MODELS["fast"]["name"]
                print(f"{YELLOW}[MultiModel] Applying speed constraint, using fast model${RESET}")
            elif time_constraint < 5:
                model_name = self.MODELS["balanced"]["name"]
                print(f"{YELLOW}[MultiModel] Time constraint applied, using balanced model${RESET}")
        
        return {
            "model": model_name,
            "model_info": model_info,
            "constraints_applied": {
                "user_preference": user_model_preference is not None,
                "time_constraint": time_constraint is not None
            }
        }
    
    def log_model_usage(self, query: str, model_used: str, result_quality: float) -> None:
        """Log model usage for analytics."""
        self.usage_log.append({
            "query": query[:100],
            "model": model_used,
            "result_quality": result_quality,
            "timestamp": str(__import__('datetime').datetime.now())
        })
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics on model usage."""
        if not self.usage_log:
            return {"message": "No usage data yet"}
        
        model_counts = {}
        model_quality = {}
        
        for entry in self.usage_log:
            model = entry["model"]
            model_counts[model] = model_counts.get(model, 0) + 1
            model_quality[model] = (model_quality.get(model, 0) + entry["result_quality"]) / 2
        
        return {
            "total_queries": len(self.usage_log),
            "model_counts": model_counts,
            "model_avg_quality": model_quality
        }


# Global instance
multi_model_reasoner = MultiModelReasoner()
