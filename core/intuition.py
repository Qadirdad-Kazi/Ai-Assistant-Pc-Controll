"""
Intuition Engine
Fast pattern recognition and gut feeling responses without full reasoning.
"""

import json
import hashlib
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from config import OLLAMA_URL, GRAY, RESET, CYAN, GREEN, YELLOW
import requests

http_session = requests.Session()


class IntuitivePatternMatcher:
    """Recognizes patterns quickly without full reasoning."""
    
    def __init__(self):
        self.pattern_library = {}
        self.quick_responses = {}
        self.pattern_confidence_scores = {}
        self.last_accessed = {}
    
    def learn_pattern(self, query_pattern: str, response: str, success_rating: float = 0.8):
        """
        Learn a query-response pattern pairing.
        success_rating: 0.0-1.0 indicating how well this response worked
        """
        pattern_hash = self._hash_pattern(query_pattern)
        
        entry = {
            "pattern": query_pattern,
            "response": response,
            "success_rating": success_rating,
            "learned_at": datetime.now().isoformat(),
            "access_count": 0,
            "last_used": None
        }
        
        self.pattern_library[pattern_hash] = entry
        self.pattern_confidence_scores[pattern_hash] = success_rating
        
        return pattern_hash
    
    def recognize_pattern(self, query: str) -> Optional[Tuple[str, float]]:
        """
        Try to instantly recognize a query pattern.
        Returns: (response, confidence) or None
        """
        query_lower = query.lower().strip()
        
        # Try exact match first (fastest intuition)
        for pattern_hash, entry in self.pattern_library.items():
            stored_pattern = entry["pattern"].lower().strip()
            
            # Check similarity
            similarity = self._calculate_similarity(query_lower, stored_pattern)
            confidence = entry["success_rating"] * similarity
            
            # Threshold for instant recognition
            if confidence > 0.75:
                # Update usage stats
                self.pattern_library[pattern_hash]["access_count"] += 1
                self.pattern_library[pattern_hash]["last_used"] = datetime.now().isoformat()
                self.last_accessed[pattern_hash] = datetime.now()
                
                return (entry["response"], confidence)
        
        return None
    
    def get_gut_feeling_response(self, query: str, category: str = "") -> Optional[Dict[str, Any]]:
        """
        Get fast, intuitive response based on pattern library.
        Useful for common queries that don't need full reasoning.
        """
        pattern_match = self.recognize_pattern(query)
        
        if pattern_match:
            response, confidence = pattern_match
            return {
                "type": "intuitive",
                "response": response,
                "confidence": confidence,
                "reasoning_used": False,
                "response_time": "instant"
            }
        
        return None
    
    def _hash_pattern(self, pattern: str) -> str:
        """Create hash of pattern for quick lookup."""
        return hashlib.md5(pattern.lower().encode()).hexdigest()
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0-1)."""
        # Simple word overlap similarity
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / max(union, 1)


class GutFeelingEngine:
    """Rapid decision-making without explicit reasoning."""
    
    def __init__(self):
        self.pattern_matcher = IntuitivePatternMatcher()
        self.quick_decision_log = []
    
    def make_quick_decision(self, query: str, context: str = "") -> Optional[Dict[str, Any]]:
        """
        Make a quick intuitive decision without full reasoning chain.
        Used for common/simple queries.
        """
        # Try pattern matching first
        pattern_response = self.pattern_matcher.get_gut_feeling_response(query)
        
        if pattern_response:
            self.quick_decision_log.append({
                "query": query,
                "decision": pattern_response,
                "timestamp": datetime.now().isoformat(),
                "method": "pattern_matching"
            })
            return pattern_response
        
        return None
    
    def learn_from_feedback(self, query: str, response: str, user_satisfaction: float):
        """
        Learn from user feedback to improve intuition.
        user_satisfaction: 0.0-1.0 (how satisfied was user)
        """
        if user_satisfaction > 0.6:
            # Good response - learn this pattern
            self.pattern_matcher.learn_pattern(query, response, user_satisfaction)
    
    def get_intuition_confidence(self, query: str) -> float:
        """
        How confident is the intuition engine about this query?
        Returns 0.0-1.0
        """
        pattern = self.pattern_matcher.recognize_pattern(query)
        
        if pattern:
            _, confidence = pattern
            return confidence
        
        return 0.0  # No pattern known


class CommonKnowledgeCache:
    """
    Cache for common knowledge queries that can be answered intuitively.
    """
    
    COMMON_FACTS = {
        "what is 2+2": "2 plus 2 equals 4.",
        "what is 2+2?": "2 plus 2 equals 4.",
        "hello": "Hello! How can I help you?",
        "hi": "Hi there! What do you need?",
        "hey": "Hey! What's up?",
        "how are you": "I'm doing well, thanks for asking! How about you?",
        "what's your name": "I'm Wolf AI, your voice assistant.",
        "who are you": "I'm Wolf AI, your voice assistant.",
        "goodbye": "Goodbye! See you later!",
        "bye": "Bye! Take care!",
        "thanks": "You're welcome!",
        "thank you": "Happy to help!",
        "ok": "Got it!",
        "okay": "Understood!",
        "yes": "You got it!",
        "no": "Alright, no problem.",
    }
    
    @staticmethod
    def get_cached_response(query: str) -> Optional[str]:
        """Get instant response if query is in common knowledge."""
        query_lower = query.lower().strip()
        
        # Try exact match
        if query_lower in CommonKnowledgeCache.COMMON_FACTS:
            return CommonKnowledgeCache.COMMON_FACTS[query_lower]
        
        # Try partial match
        for key, value in CommonKnowledgeCache.COMMON_FACTS.items():
            if key in query_lower or query_lower in key:
                return value
        
        return None


class IntuitionStatistics:
    """Track intuition engine performance."""
    
    def __init__(self):
        self.total_intuitive_responses = 0
        self.successful_intuitive_responses = 0
        self.failed_intuitive_responses = 0
        self.average_response_time = 0.0
    
    def record_intuitive_response(self, was_successful: bool):
        """Record the result of an intuitive response."""
        self.total_intuitive_responses += 1
        
        if was_successful:
            self.successful_intuitive_responses += 1
        else:
            self.failed_intuitive_responses += 1
    
    def get_intuition_accuracy(self) -> float:
        """Get accuracy rate of intuitive responses (0-100%)."""
        if self.total_intuitive_responses == 0:
            return 0.0
        
        return (self.successful_intuitive_responses / self.total_intuitive_responses) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """Get complete intuition statistics."""
        return {
            "total_intuitive_responses": self.total_intuitive_responses,
            "successful": self.successful_intuitive_responses,
            "failed": self.failed_intuitive_responses,
            "accuracy_percent": self.get_intuition_accuracy(),
            "avg_response_time_ms": self.average_response_time
        }


# Global instances
intuition_engine = GutFeelingEngine()
intuition_stats = IntuitionStatistics()
