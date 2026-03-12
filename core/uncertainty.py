"""
Uncertainty Quantification Module
Enables the AI to quantify and communicate confidence in responses.
"""

import json
import re
from typing import Dict, Any, List, Tuple, Optional
from config import OLLAMA_URL, GRAY, RESET, CYAN, GREEN, YELLOW, RESPONDER_MODEL
import requests

http_session = requests.Session()


class UncertaintyAnalyzer:
    """Analyzes and quantifies uncertainty in AI responses."""
    
    # Uncertainty markers
    CONFIDENCE_KEYWORDS = {
        "high": ["definitely", "certainly", "absolutely", "clearly", "obviously", "no doubt"],
        "medium": ["likely", "probably", "appears", "seems", "generally", "typically"],
        "low": ["might", "possibly", "could", "perhaps", "may be", "uncertain", "unclear"]
    }
    
    def __init__(self):
        self.uncertainty_log = []
    
    def quantify_uncertainty(self, response: str) -> Dict[str, Any]:
        """
        Analyze response and quantify uncertainty level.
        Returns: confidence_score (0-100), confidence_level (low/medium/high)
        """
        # Count confidence markers
        confidence_scores = {
            "high": len([w for w in self.CONFIDENCE_KEYWORDS["high"] if w.lower() in response.lower()]),
            "medium": len([w for w in self.CONFIDENCE_KEYWORDS["medium"] if w.lower() in response.lower()]),
            "low": len([w for w in self.CONFIDENCE_KEYWORDS["low"] if w.lower() in response.lower()])
        }
        
        # Calculate confidence score
        total_markers = sum(confidence_scores.values())
        
        if total_markers == 0:
            confidence_score = 50  # Neutral
            confidence_level = "medium"
        else:
            # Weighted scoring
            score = (confidence_scores["high"] * 100 + 
                    confidence_scores["medium"] * 50 + 
                    confidence_scores["low"] * 10) / total_markers
            confidence_score = int(score)
            
            if confidence_score >= 70:
                confidence_level = "high"
            elif confidence_score >= 40:
                confidence_level = "medium"
            else:
                confidence_level = "low"
        
        # Detect uncertainty indicators
        uncertainty_indicators = self._detect_uncertainty_indicators(response)
        
        # Detect assumptions
        assumptions = self._extract_assumptions(response)
        
        return {
            "confidence_score": confidence_score,
            "confidence_level": confidence_level,
            "confidence_markers": confidence_scores,
            "uncertainty_indicators": uncertainty_indicators,
            "assumptions": assumptions,
            "response_length": len(response),
            "specificity_score": self._calculate_specificity(response)
        }
    
    def _detect_uncertainty_indicators(self, response: str) -> List[str]:
        """Detect phrases indicating uncertainty."""
        indicators = []
        patterns = [
            r"i'm not sure",
            r"it seems",
            r"it appears",
            r"possibly",
            r"might be",
            r"could be",
            r"i could be wrong",
            r"not certain",
            r"unclear"
        ]
        
        for pattern in patterns:
            if re.search(pattern, response.lower()):
                indicators.append(pattern.replace(r"\\", ""))
        
        return indicators
    
    def _extract_assumptions(self, response: str) -> List[str]:
        """Extract stated or implied assumptions."""
        assumptions = []
        patterns = [
            r"assuming\s+[^.]+",
            r"assuming that\s+[^.]+",
            r"given that\s+[^.]+",
            r"provided that\s+[^.]+",
            r"on the assumption that\s+[^.]+"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            assumptions.extend(matches)
        
        return assumptions[:3]  # Return top 3
    
    def _calculate_specificity(self, response: str) -> float:
        """Calculate how specific/detailed the response is (0-100)."""
        response_length = len(response)
        word_count = len(response.split())
        
        # Longer, more detailed responses are typically more specific
        # Max out at 100 words and 500 characters for high specificity
        length_score = min(100, (response_length / 500) * 100)
        word_score = min(100, (word_count / 100) * 100)
        
        specificity = (length_score + word_score) / 2
        return round(specificity, 1)
    
    def identify_confidence_gaps(self, response: str) -> List[str]:
        """Identify areas where the response might lack confidence."""
        gaps = []
        
        # Check for vague terms
        vague_terms = ["something", "someone", "somehow", "somewhere", "thing", "stuff"]
        for term in vague_terms:
            if re.search(rf"\b{term}\b", response.lower()):
                gaps.append(f"Vague term used: '{term}'")
        
        # Check for incomplete sentences
        if response.count("...") > 1:
            gaps.append("Multiple incomplete thoughts indicated by ellipsis")
        
        # Check for contradictions
        if "but" in response.lower() or "however" in response.lower():
            gaps.append("Contains contradictory or revised statements")
        
        return gaps
    
    def generate_confidence_disclosure(self, confidence_data: Dict[str, Any]) -> str:
        """Generate human-readable confidence disclosure."""
        score = confidence_data.get("confidence_score", 50)
        level = confidence_data.get("confidence_level", "medium")
        gaps = confidence_data.get("uncertainty_indicators", [])
        assumptions = confidence_data.get("assumptions", [])
        specificity = confidence_data.get("specificity_score", 50)
        
        disclosure_parts = []
        
        # Main confidence statement
        if level == "high":
            disclosure_parts.append(f"I'm quite confident in this response (confidence: {score}%).")
        elif level == "medium":
            disclosure_parts.append(f"I have moderate confidence in this response (confidence: {score}%).")
        else:
            disclosure_parts.append(f"I have low confidence in this response (confidence: {score}%). Take this with a grain of salt.")
        
        # Specificity note
        if specificity < 40:
            disclosure_parts.append("The response is somewhat general and could benefit from more specific details.")
        elif specificity > 80:
            disclosure_parts.append("The response is quite detailed and specific.")
        
        # Uncertainty indicators
        if gaps:
            disclosure_parts.append(f"Areas of uncertainty: {', '.join(gaps[:2])}")
        
        # Assumptions
        if assumptions:
            disclosure_parts.append(f"Key assumptions made: {assumptions[0]}")
        
        return " ".join(disclosure_parts)


class ConfidenceAdjuster:
    """Adjusts response based on confidence levels."""
    
    def __init__(self, model_name: str = RESPONDER_MODEL):
        self.model_name = model_name
        self.analyzer = UncertaintyAnalyzer()
    
    def adjust_response_for_uncertainty(self, original_response: str, confidence_score: int) -> str:
        """
        Adjust response based on confidence level.
        - High confidence: Present more assertively
        - Low confidence: Add caveats and alternatives
        """
        if confidence_score >= 70:
            # High confidence - keep as is or make more assertive
            return original_response
        
        elif confidence_score >= 40:
            # Medium confidence - add calm caveats
            prefix = "Based on my analysis, "
            return prefix + original_response
        
        else:
            # Low confidence - add significant caveats
            prefix = "This is speculative, but "
            suffix = " However, I recommend verifying this independently as I'm not highly confident."
            return prefix + original_response + suffix
    
    def generate_alternatives(self, response: str, confidence_score: int) -> List[str]:
        """
        If confidence is low, generate alternative responses/interpretations.
        """
        if confidence_score >= 70:
            return []  # No need for alternatives
        
        print(f"{CYAN}[UncertaintyAnalyzer] Generating alternatives for low-confidence response${RESET}")
        
        alternatives_prompt = f"""Given this response with moderate uncertainty:

Original Response: {response}

Generate 2-3 alternative interpretations or responses that might be more accurate:"""
        
        try:
            response_data = http_session.post(
                f"{OLLAMA_URL}/generate",
                json={
                    "model": self.model_name,
                    "prompt": alternatives_prompt,
                    "stream": False,
                    "keep_alive": "5m"
                },
                timeout=60
            )
            
            if response_data.status_code == 200:
                alternatives = response_data.json().get("response", "").split("\n")
                return [alt.strip() for alt in alternatives if alt.strip()][:3]
        
        except Exception as e:
            print(f"{GRAY}[UncertaintyAnalyzer] Error generating alternatives: {e}{RESET}")
        
        return []
    
    def request_clarification(self, original_query: str, confidence_score: int) -> Optional[str]:
        """
        If confidence is very low, suggest clarifying questions.
        """
        if confidence_score > 30:
            return None  # Confidence acceptable
        
        print(f"{YELLOW}[UncertaintyAnalyzer] Requesting clarification due to low confidence${RESET}")
        
        clarification_prompt = f"""To better answer this question with higher confidence:

Original Query: {original_query}

Generate 2-3 clarifying questions that would help me provide a better, more confident answer:"""
        
        try:
            response_data = http_session.post(
                f"{OLLAMA_URL}/generate",
                json={
                    "model": self.model_name,
                    "prompt": clarification_prompt,
                    "stream": False,
                    "keep_alive": "5m"
                },
                timeout=60
            )
            
            if response_data.status_code == 200:
                return response_data.json().get("response", "")
        
        except Exception as e:
            print(f"{GRAY}[UncertaintyAnalyzer] Error requesting clarification: {e}{RESET}")
        
        return None


class BayesianConfidenceEstimator:
    """
    Advanced uncertainty estimation using Bayesian concepts.
    Tracks priors, updates beliefs based on evidence.
    """
    
    def __init__(self):
        self.prior_beliefs = {}
        self.evidence_log = []
    
    def update_belief(self, topic: str, evidence: str, strength: float = 0.5) -> float:
        """
        Update belief about a topic based on new evidence.
        Strength: 0.0 (weak) to 1.0 (strong evidence)
        
        Returns: Updated confidence level (0-100)
        """
        # Get or initialize prior
        prior = self.prior_beliefs.get(topic, 50)  # Default to neutral
        
        # Log evidence
        self.evidence_log.append({
            "topic": topic,
            "evidence": evidence,
            "strength": strength
        })
        
        # Simple Bayesian update
        # Higher strength = more extreme adjustment
        adjustment = (strength - 0.5) * 40  # Scale to -20 to +20
        updated_belief = max(0, min(100, prior + adjustment))
        
        self.prior_beliefs[topic] = updated_belief
        
        print(f"{CYAN}[Bayesian] Updated belief on '{topic}': {prior:.0f} → {updated_belief:.0f}{RESET}")
        
        return updated_belief
    
    def get_confidence_for_topic(self, topic: str) -> Dict[str, Any]:
        """Get current confidence level for a topic."""
        confidence = self.prior_beliefs.get(topic, 50)
        
        # Count supporting and conflicting evidence
        supporting_evidence = [e for e in self.evidence_log 
                              if e["topic"] == topic and e["strength"] > 0.5]
        conflicting_evidence = [e for e in self.evidence_log 
                               if e["topic"] == topic and e["strength"] < 0.5]
        
        return {
            "topic": topic,
            "confidence": int(confidence),
            "supporting_evidence_count": len(supporting_evidence),
            "conflicting_evidence_count": len(conflicting_evidence),
            "evidence_consensus": "strong" if len(supporting_evidence) > len(conflicting_evidence) * 2 else "weak"
        }


# Global instances
uncertainty_analyzer = UncertaintyAnalyzer()
confidence_adjuster = ConfidenceAdjuster()
bayesian_estimator = BayesianConfidenceEstimator()


def quantify_and_disclose_uncertainty(response: str) -> Dict[str, Any]:
    """
    Complete pipeline: Quantify uncertainty and generate disclosure.
    """
    uncertainty_data = uncertainty_analyzer.quantify_uncertainty(response)
    disclosure = uncertainty_analyzer.generate_confidence_disclosure(uncertainty_data)
    
    adjusted_response = confidence_adjuster.adjust_response_for_uncertainty(
        response,
        uncertainty_data["confidence_score"]
    )
    
    alternatives = []
    if uncertainty_data["confidence_score"] < 50:
        alternatives = confidence_adjuster.generate_alternatives(
            response,
            uncertainty_data["confidence_score"]
        )
    
    return {
        "original_response": response,
        "adjusted_response": adjusted_response,
        "uncertainty_data": uncertainty_data,
        "confidence_disclosure": disclosure,
        "alternatives": alternatives,
        "should_request_clarification": uncertainty_data["confidence_score"] < 30
    }
