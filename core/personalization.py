"""
Adaptive Personalization Module
Learns and adapts to individual user preferences and communication styles.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import GRAY, RESET, CYAN, GREEN, YELLOW


class UserProfile:
    """Maintains personalized profile for each user."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.communication_style = "neutral"
        self.technical_level = "intermediate"
        self.interests = []
        self.preferences = {}
        self.interaction_history = []
        self.learned_traits = {}
        self.created_at = datetime.now().isoformat()
    
    def record_interaction(self, query: str, response_style: str, satisfaction: float):
        """Record an interaction for learning."""
        self.interaction_history.append({
            "query": query,
            "response_style": response_style,
            "satisfaction": satisfaction,
            "timestamp": datetime.now().isoformat()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "user_id": self.user_id,
            "communication_style": self.communication_style,
            "technical_level": self.technical_level,
            "interests": self.interests,
            "preferences": self.preferences,
            "learned_traits": self.learned_traits,
            "interaction_count": len(self.interaction_history)
        }


class CommunicationStyleAdapter:
    """Adapts communication style based on user preferences."""
    
    STYLES = {
        "formal": {
            "greeting": "Good day. How may I assist you?",
            "confirmation": "Understood. I shall proceed.",
            "emphasis": "This is of significant importance.",
            "explanation": "The technical specification is as follows:"
        },
        "casual": {
            "greeting": "Hey! What's up?",
            "confirmation": "You got it!",
            "emphasis": "This is pretty important, actually.",
            "explanation": "So here's the deal:"
        },
        "technical": {
            "greeting": "Ready to execute. What's the task?",
            "confirmation": "Confirmed. Processing.",
            "emphasis": "Critical parameter.",
            "explanation": "Breaking down the algorithm:"
        },
        "friendly": {
            "greeting": "Hi there! Great to chat with you!",
            "confirmation": "Absolutely, I'm on it!",
            "emphasis": "This really matters to you, doesn't it?",
            "explanation": "Let me walk you through this:"
        },
        "support": {
            "greeting": "Hello! How can I help make your day better?",
            "confirmation": "I'm here to help with that.",
            "emphasis": "Your satisfaction is my priority.",
            "explanation": "Let me explain this simply:"
        }
    }
    
    def __init__(self):
        self.user_styles = {}
    
    def detect_preferred_style(self, user_interactions: List[Dict[str, Any]]) -> str:
        """
        Detect user's preferred communication style from interactions.
        """
        if not user_interactions:
            return "neutral"
        
        # Analyze interaction patterns
        technical_term_count = 0
        punctuation_count = 0
        emoji_count = 0
        informal_count = 0
        
        for interaction in user_interactions[-20:]:  # Last 20 interactions
            query = interaction.get("query", "").lower()
            
            # Check for technical terms
            if any(term in query for term in ["code", "api", "algorithm", "debug", "repository"]):
                technical_term_count += 1
            
            # Check for punctuation (more = more formal)
            punctuation_count += query.count(".")
            
            # Check for emojis or casual language
            if any(word in query for word in ["lol", "omg", "haha", "cool", "awesome"]):
                informal_count += 1
        
        # Determine style
        if technical_term_count > len(user_interactions) * 0.5:
            return "technical"
        elif informal_count > len(user_interactions) * 0.3:
            return "casual"
        elif punctuation_count > len(user_interactions) * 2:
            return "formal"
        
        return "friendly"
    
    def adapt_response(self, response: str, style: str) -> str:
        """
        Adapt response to match user's communication style.
        """
        if style not in self.STYLES:
            return response
        
        style_dict = self.STYLES[style]
        
        # Apply style markers
        if response.startswith("I can"):
            opening = style_dict.get("confirmation", "I can")
            response = opening + " " + response[5:].lstrip()
        
        return response


class TechnicalLevelAdapter:
    """Adapts technical explanation depth based on user level."""
    
    LEVELS = {
        "beginner": {
            "use_jargon": False,
            "explanation_depth": "simple",
            "code_examples": False,
            "analogies": True
        },
        "intermediate": {
            "use_jargon": True,
            "explanation_depth": "balanced",
            "code_examples": True,
            "analogies": True
        },
        "advanced": {
            "use_jargon": True,
            "explanation_depth": "detailed",
            "code_examples": True,
            "analogies": False
        },
        "expert": {
            "use_jargon": True,
            "explanation_depth": "exhaustive",
            "code_examples": True,
            "analogies": False
        }
    }
    
    def __init__(self):
        self.user_levels = {}
    
    def detect_technical_level(self, user_interactions: List[Dict[str, Any]]) -> str:
        """
        Detect user's technical level from their queries.
        """
        if not user_interactions:
            return "intermediate"
        
        # Analyze recent interactions
        technical_queries = 0
        complex_terms = 0
        simple_queries = 0
        
        for interaction in user_interactions[-20:]:
            query = interaction.get("query", "").lower()
            
            # Check for technical depth
            if any(term in query for term in ["api", "algorithm", "architecture", "scalability"]):
                technical_queries += 1
                complex_terms += query.count("how")
            
            # Check for beginner questions
            if any(term in query for term in ["what is", "how do i", "how to"]):
                simple_queries += 1
        
        ratio = technical_queries / max(len(user_interactions), 1)
        
        if ratio > 0.7:
            return "expert"
        elif ratio > 0.4:
            return "advanced"
        elif simple_queries > technical_queries * 2:
            return "beginner"
        
        return "intermediate"
    
    def adapt_explanation(self, explanation: str, level: str) -> str:
        """
        Adjust explanation based on user's technical level.
        """
        if level not in self.LEVELS:
            return explanation
        
        level_config = self.LEVELS[level]
        
        # Remove code examples if beginner
        if not level_config["code_examples"]:
            lines = explanation.split("\n")
            filtered = [line for line in lines if not line.strip().startswith("`")]
            explanation = "\n".join(filtered)
        
        # Add analogies if beginner/intermediate
        if level_config["analogies"] and level in ["beginner", "intermediate"]:
            explanation += "\n\nThink of it like this: [analogy would go here]"
        
        return explanation


class InterestTracker:
    """Tracks user interests and topics."""
    
    def __init__(self):
        self.user_interests = {}
    
    def extract_interests(self, interactions: List[Dict[str, Any]]) -> List[str]:
        """Extract topics/interests from user interactions."""
        interests = {}
        
        topic_keywords = {
            "programming": ["python", "javascript", "java", "coding", "code", "algorithm"],
            "music": ["music", "song", "artist", "album", "playlist"],
            "gaming": ["game", "gaming", "play", "console", "fps"],
            "sports": ["sports", "game", "team", "score", "coach"],
            "entertainment": ["movie", "show", "tv", "cinema", "netflix"],
            "health": ["health", "fitness", "exercise", "diet", "workout"],
            "business": ["business", "startup", "entrepreneur", "sales", "market"],
            "science": ["science", "research", "study", "experiment", "theory"]
        }
        
        for interaction in interactions:
            query = interaction.get("query", "").lower()
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in query for keyword in keywords):
                    interests[topic] = interests.get(topic, 0) + 1
        
        # Return top interests
        sorted_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in sorted_interests[:5]]


class AdaptivePersonalizer:
    """Main personalization engine."""
    
    def __init__(self):
        self.user_profiles = {}
        self.style_adapter = CommunicationStyleAdapter()
        self.level_adapter = TechnicalLevelAdapter()
        self.interest_tracker = InterestTracker()
    
    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get existing profile or create new one."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id)
        return self.user_profiles[user_id]
    
    def personalize_response(self, response: str, user_id: str) -> str:
        """Personalize response based on user profile."""
        profile = self.get_or_create_profile(user_id)
        
        # Adapt to communication style
        if profile.communication_style != "neutral":
            response = self.style_adapter.adapt_response(response, profile.communication_style)
        
        # Adapt to technical level
        response = self.level_adapter.adapt_explanation(response, profile.technical_level)
        
        return response

    def adapt_communication_style(self, response: str, user_id: str) -> str:
        """Backwards-compatible API used by voice assistant for style-only adaptation."""
        profile = self.get_or_create_profile(user_id)
        if profile.communication_style == "neutral":
            return response
        return self.style_adapter.adapt_response(response, profile.communication_style)
    
    def update_profile_from_interactions(self, user_id: str, interactions: List[Dict[str, Any]]):
        """Update user profile based on recent interactions."""
        profile = self.get_or_create_profile(user_id)
        
        # Detect and update communication style
        profile.communication_style = self.style_adapter.detect_preferred_style(interactions)
        
        # Detect and update technical level
        profile.technical_level = self.level_adapter.detect_technical_level(interactions)
        
        # Extract interests
        profile.interests = self.interest_tracker.extract_interests(interactions)
        
        print(f"{GREEN}[Personalization] Updated profile for {user_id}${RESET}")
        print(f"{CYAN}Style: {profile.communication_style}, Level: {profile.technical_level}${RESET}")


# Global instance
adaptive_personalizer = AdaptivePersonalizer()
