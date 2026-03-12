"""
Self-Reflection & Error Correction Module
Enables the AI to verify its own outputs and automatically correct mistakes.
"""

import json
from typing import Dict, Any, Optional, List
from config import OLLAMA_URL, GREEN, CYAN, YELLOW, GRAY, RESET, RESPONDER_MODEL
import requests

http_session = requests.Session()


class SelfReflectionEngine:
    """Handles verification and self-correction of AI responses."""
    
    def __init__(self, model_name: str = RESPONDER_MODEL):
        self.model_name = model_name
        self.correction_attempts = 0
        self.max_correction_attempts = 3
        self.correction_history = []
    
    def verify_response(self, user_query: str, response: str, action_taken: str = "") -> Dict[str, Any]:
        """
        Verify if the response correctly addresses the original query.
        
        Returns:
            {
                "is_valid": bool,
                "confidence": 1-10,
                "issues": [list of issues found],
                "feedback": str,
                "needs_correction": bool
            }
        """
        print(f"{CYAN}[SelfReflection] Verifying response validity...{RESET}")
        
        verification_prompt = f"""Verify this response:

Original Query: {user_query}
{f'Action Taken: {action_taken}' if action_taken else ''}
Response: {response}

Answer these questions:
1. Does the response actually address the user's query?
2. Is the information accurate based on the action taken?
3. Is it complete or missing important details?
4. Are there any contradictions or logical errors?
5. Confidence this response is correct (1-10): __

Format your response as:
VALID: YES/NO
CONFIDENCE: [1-10]
ISSUES: [List issues or "None"]
FEEDBACK: [Brief explanation]"""
        
        verification = self._call_llm(verification_prompt, enable_thinking=True)
        
        parsed = self._parse_verification(verification)
        
        return {
            "is_valid": parsed.get("valid", False),
            "confidence": parsed.get("confidence", 5),
            "issues": parsed.get("issues", []),
            "feedback": verification,
            "needs_correction": parsed.get("confidence", 5) < 7 or not parsed.get("valid", False)
        }
    
    def self_correct(self, user_query: str, wrong_response: str, issues: List[str], 
                     action_context: str = "", attempt_number: int = 1) -> Dict[str, Any]:
        """
        Generate a corrected response after identifying issues.
        
        Implements retry logic with learning.
        """
        print(f"{YELLOW}[SelfReflection] Attempting self-correction (attempt {attempt_number}/{self.max_correction_attempts})...{RESET}")
        
        if attempt_number > self.max_correction_attempts:
            return {
                "success": False,
                "message": "Max correction attempts reached. Returning original response.",
                "corrected_response": wrong_response
            }
        
        correction_prompt = f"""The previous response had issues and needs correction.

User Query: {user_query}
Previous Response: {wrong_response}
Issues Found: {', '.join(issues)}
{f'Context: {action_context}' if action_context else ''}

Generate a corrected response that:
1. Addresses the original query more accurately
2. Avoids the identified issues
3. Provides complete information
4. Uses clear, concise language

Corrected Response:"""
        
        corrected = self._call_llm(correction_prompt, enable_thinking=True)
        
        # Record correction attempt
        self.correction_history.append({
            "attempt": attempt_number,
            "issues": issues,
            "corrected_response": corrected
        })
        
        return {
            "success": True,
            "corrected_response": corrected,
            "attempt_number": attempt_number,
            "previous_issues": issues
        }
    
    def verify_and_correct(self, user_query: str, response: str, action_context: str = "") -> Dict[str, Any]:
        """
        Complete verification and correction pipeline.
        Automatically retries until response is satisfactory or max attempts reached.
        
        Returns the best response found.
        """
        print(f"{CYAN}[SelfReflection] Starting verify-and-correct pipeline...{RESET}")
        
        current_response = response
        self.correction_attempts = 0
        
        while self.correction_attempts < self.max_correction_attempts:
            # Verify current response
            verification = self.verify_response(user_query, current_response, action_context)
            
            if verification["is_valid"] and verification["confidence"] >= 7:
                # Response is good
                print(f"{GREEN}[SelfReflection] ✓ Response verified successfully (confidence: {verification['confidence']}/10){RESET}")
                return {
                    "success": True,
                    "final_response": current_response,
                    "confidence": verification["confidence"],
                    "attempts": self.correction_attempts,
                    "verified": True
                }
            
            # Response needs correction
            self.correction_attempts += 1
            correction = self.self_correct(
                user_query, 
                current_response, 
                verification["issues"],
                action_context,
                self.correction_attempts
            )
            
            if correction["success"]:
                current_response = correction["corrected_response"]
                print(f"{YELLOW}[SelfReflection] Response corrected (attempt {self.correction_attempts}){RESET}")
            else:
                # Max attempts reached
                break
        
        # Return best response found
        return {
            "success": True,
            "final_response": current_response,
            "confidence": verification.get("confidence", 5),
            "attempts": self.correction_attempts,
            "verified": False,
            "max_attempts_reached": True
        }
    
    def validate_reasoning_chain(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate that a chain of reasoning steps is logically consistent.
        
        Args:
            steps: List of {"action": str, "result": str} dicts
        
        Returns:
            Validation report with logical consistency score
        """
        print(f"{CYAN}[SelfReflection] Validating reasoning chain consistency...{RESET}")
        
        steps_text = "\n".join([f"{i+1}. {s.get('action', 'Unknown')} → {s.get('result', 'No result')}" 
                               for i, s in enumerate(steps)])
        
        validation_prompt = f"""Validate this reasoning chain for logical consistency:

Steps:
{steps_text}

Analyze:
1. Do the steps logically follow each other?
2. Are there any contradictions or jumps in logic?
3. Are all assumptions valid?
4. Does the chain build toward a coherent conclusion?
5. Rate overall consistency (1-10): __

Provide validation feedback:"""
        
        validation = self._call_llm(validation_prompt, enable_thinking=True)
        
        consistency_score = self._extract_score(validation)
        
        return {
            "consistency_score": consistency_score,
            "is_consistent": consistency_score >= 7,
            "validation_feedback": validation,
            "step_count": len(steps)
        }
    
    def check_for_hallucinations(self, response: str, knowledge_base: str = "") -> Dict[str, Any]:
        """
        Check if the response contains hallucinations or unsupported claims.
        
        Args:
            response: The response to check
            knowledge_base: Optional reference text to verify against
        
        Returns:
            Hallucination report
        """
        print(f"{CYAN}[SelfReflection] Checking for hallucinations...{RESET}")
        
        hallucination_prompt = f"""Analyze this response for potential hallucinations or unsupported claims:

Response: {response}

{f'Reference Knowledge: {knowledge_base}' if knowledge_base else 'Note: No reference knowledge provided.'}

For each claim in the response:
1. Can it be verified or is it common knowledge?
2. Is there evidence it might be false?
3. Are there unsupported leaps of logic?
4. Estimate hallucination risk (LOW/MEDIUM/HIGH): __

List any potential hallucinations found:"""
        
        analysis = self._call_llm(hallucination_prompt, enable_thinking=True)
        
        hallucination_risk = "HIGH" if "high" in analysis.lower() else ("MEDIUM" if "medium" in analysis.lower() else "LOW")
        
        return {
            "hallucination_risk": hallucination_risk,
            "analysis": analysis,
            "response": response,
            "has_hallucinations": hallucination_risk in ["HIGH", "MEDIUM"]
        }
    
    def rate_response_quality(self, response: str, query: str, context: str = "") -> Dict[str, Any]:
        """
        Rate overall response quality across multiple dimensions.
        """
        print(f"{CYAN}[SelfReflection] Rating response quality...{RESET}")
        
        rating_prompt = f"""Rate this response across multiple quality dimensions:

Query: {query}
Response: {response}
{f'Context: {context}' if context else ''}

Rate each dimension (1-10):
1. Accuracy: Does it answer correctly?
2. Completeness: Does it cover all aspects?
3. Clarity: Is it clear and well-written?
4. Relevance: Is it focused?
5. Usefulness: Is it actionable/helpful?

Provide individual scores and overall quality assessment:"""
        
        rating = self._call_llm(rating_prompt, enable_thinking=True)
        
        scores = self._extract_scores(rating)
        overall_score = sum(scores.values()) / len(scores) if scores else 5
        
        return {
            "overall_score": overall_score,
            "dimension_scores": scores,
            "quality_level": "High" if overall_score >= 8 else ("Medium" if overall_score >= 6 else "Low"),
            "assessment": rating
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    def _call_llm(self, prompt: str, enable_thinking: bool = False) -> str:
        """Call LLM for verification/correction."""
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
                timeout=60
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return response_data.get("response", "")
            else:
                print(f"{GRAY}[SelfReflection] LLM call failed{RESET}")
                return ""
        
        except Exception as e:
            print(f"{GRAY}[SelfReflection] Error: {e}{RESET}")
            return ""
    
    def _parse_verification(self, verification_text: str) -> Dict[str, Any]:
        """Parse verification response."""
        import re
        
        # Extract confidence score
        confidence_match = re.search(r'CONFIDENCE[:\s]*(\d+)', verification_text, re.IGNORECASE)
        confidence = int(confidence_match.group(1)) if confidence_match else 5
        
        # Extract validity
        valid = "YES" in verification_text.upper().split("VALID")[1].split("\n")[0] if "VALID" in verification_text.upper() else False
        
        # Extract issues
        issues = []
        if "ISSUES:" in verification_text.upper():
            issues_section = verification_text.upper().split("ISSUES:")[1].split("\n")[0]
            if "NONE" not in issues_section:
                issues = [i.strip() for i in issues_section.split(",") if i.strip()]
        
        return {
            "valid": valid,
            "confidence": min(confidence, 10),
            "issues": issues
        }
    
    def _extract_score(self, text: str) -> int:
        """Extract numeric score from text."""
        import re
        matches = re.findall(r'(\d+)\s*(?:/10|out of 10)?', text)
        if matches:
            try:
                return min(int(matches[0]), 10)
            except:
                pass
        return 5
    
    def _extract_scores(self, text: str) -> Dict[str, float]:
        """Extract multiple dimension scores."""
        import re
        dimensions = ["Accuracy", "Completeness", "Clarity", "Relevance", "Usefulness"]
        scores = {}
        
        for dim in dimensions:
            pattern = f"{dim}[:\s]*(\d+)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                scores[dim] = float(match.group(1))
        
        return scores
    
    def get_correction_history(self) -> List[Dict[str, Any]]:
        """Get history of all corrections made."""
        return self.correction_history


# Global instance
self_reflection_engine = SelfReflectionEngine()
