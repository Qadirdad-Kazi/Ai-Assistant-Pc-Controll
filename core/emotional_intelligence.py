"""
Emotional Intelligence System
Enables the AI to understand, recognize, and respond to emotions in a human-like way.
"""

import json
import re
from typing import Dict, Any, List, Tuple, Optional
from config import OLLAMA_URL, GRAY, RESET, CYAN, GREEN, YELLOW
import requests

http_session = requests.Session()


class EmotionalAnalyzer:
    """Analyzes emotional content in user queries and context."""
    
    # Emotion keywords mapping
    EMOTION_KEYWORDS = {
        "angry": ["angry", "furious", "rage", "hate", "frustrated", "annoyed", "irritated"],
        "sad": ["sad", "depressed", "down", "unhappy", "miserable", "heartbroken", "grief"],
        "happy": ["happy", "excited", "joyful", "thrilled", "delighted", "great", "wonderful"],
        "anxious": ["worried", "anxious", "nervous", "afraid", "scared", "stressed", "panicked"],
        "confused": ["confused", "lost", "bewildered", "unclear", "puzzled", "confused"],
        "confident": ["confident", "sure", "certain", "believe", "convinced"],
        "tired": ["tired", "exhausted", "fatigue", "weary", "sleepy", "worn out"],
        "overwhelmed": ["overwhelmed", "swamped", "drowning", "flooded", "burdened"]
    }
    
    # Sentiment intensity markers
    INTENSITY_MARKERS = {
        "high": ["very", "absolutely", "completely", "totally", "extremely", "so", "incredibly"],
        "low": ["slightly", "a bit", "somewhat", "kind of", "sort of", "maybe"]
    }
    
    def __init__(self):
        self.emotion_history = []
        self.user_emotional_baseline = {}
    
    def detect_user_emotion(self, user_input: str) -> Dict[str, Any]:
        """
        Detect primary emotion(s) in user input.
        Returns: emotion, intensity, confidence
        """
        input_lower = user_input.lower()
        emotions_found = {}
        
        # Count keyword matches for each emotion
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            count = sum(1 for keyword in keywords if keyword in input_lower)
            if count > 0:
                emotions_found[emotion] = count
        
        if not emotions_found:
            return {
                "primary_emotion": "neutral",
                "intensity": "neutral",
                "confidence": 0.3,
                "all_emotions": {}
            }
        
        # Sort by frequency
        sorted_emotions = sorted(emotions_found.items(), key=lambda x: x[1], reverse=True)
        primary_emotion = sorted_emotions[0][0]
        
        # Detect intensity
        intensity = "medium"
        if any(marker in input_lower for marker in self.INTENSITY_MARKERS["high"]):
            intensity = "high"
        elif any(marker in input_lower for marker in self.INTENSITY_MARKERS["low"]):
            intensity = "low"
        
        # Calculate confidence
        max_matches = sorted_emotions[0][1]
        confidence = min(0.9, max_matches / 3.0)
        
        # Log emotion
        emotion_record = {
            "emotion": primary_emotion,
            "intensity": intensity,
            "confidence": confidence,
            "raw_matches": dict(sorted_emotions)
        }
        self.emotion_history.append(emotion_record)
        
        return {
            "primary_emotion": primary_emotion,
            "intensity": intensity,
            "confidence": confidence,
            "all_emotions": dict(sorted_emotions),
            "raw_input": user_input[:100]
        }
    
    def set_user_emotional_baseline(self, user_id: str, baseline_emotion: str = "neutral"):
        """Set or update emotional baseline for a user."""
        self.user_emotional_baseline[user_id] = baseline_emotion
    
    def get_emotional_shift(self, user_id: str, current_emotion: str) -> str:
        """
        Detect if user's emotional state has shifted from baseline.
        Returns: "negative_shift", "positive_shift", "no_shift"
        """
        baseline = self.user_emotional_baseline.get(user_id, "neutral")
        
        # Simple emotion hierarchy
        emotion_positivity = {
            "happy": 3,
            "confident": 2,
            "neutral": 1,
            "tired": 0,
            "confused": -1,
            "anxious": -2,
            "sad": -3,
            "angry": -4,
            "overwhelmed": -5
        }
        
        baseline_score = emotion_positivity.get(baseline, 1)
        current_score = emotion_positivity.get(current_emotion, 1)
        
        diff = current_score - baseline_score
        
        if diff > 1:
            return "positive_shift"
        elif diff < -1:
            return "negative_shift"
        else:
            return "no_shift"
    
    def generate_empathetic_response(self, emotion: str, intensity: str) -> str:
        """Generate empathetic opening based on detected emotion."""
        empathy_responses = {
            "angry_high": "I can see this is really frustrating for you. Let me help make this better.",
            "angry_medium": "I understand you're frustrated. Let me work through this carefully with you.",
            "angry_low": "I know this is annoying. I'll try to sort it out quickly.",
            
            "sad_high": "I can hear the sadness in your message. I'm here to help if I can.",
            "sad_medium": "I sense you're feeling down. What can I do to help?",
            "sad_low": "You seem a bit down. Let me see what I can do.",
            
            "happy_high": "Your enthusiasm is great! I'm excited to help.",
            "happy_medium": "I'm glad you're in a good mood. Let's make the most of it.",
            "happy_low": "You seem in good spirits. What can I help with?",
            
            "anxious_high": "I can feel your stress. Let me give you clear, simple steps.",
            "anxious_medium": "You seem a bit worried. I'll be thorough and clear.",
            "anxious_low": "No need to worry, I've got this covered.",
            
            "confused_high": "I can tell you're really lost. Let me break it down step by step.",
            "confused_medium": "This seems confusing. Let me clarify each part.",
            "confused_low": "You're a bit puzzled. Let me explain it differently.",
            
            "overwhelmed_high": "You sound swamped. Let's tackle this one piece at a time.",
            "overwhelmed_medium": "You seem overloaded. Let me simplify this.",
            "overwhelmed_low": "Feeling a bit much? I'll keep it focused.",
            
            "tired_high": "You sound exhausted. I'll keep this quick and simple.",
            "tired_medium": "You seem a bit tired. Let me be efficient.",
            "tired_low": "You're running on fumes. This won't take long.",
            
            "confident_high": "I love your confidence! Let's tackle something ambitious.",
            "confident_medium": "You seem sure about this. Good attitude to have.",
            "confident_low": "You're reasonably confident. That's a good start.",
            
            "neutral_high": "What can I help you with?",
            "neutral_medium": "Ready when you are.",
            "neutral_low": "I'm listening."
        }
        
        key = f"{emotion}_{intensity}"
        return empathy_responses.get(key, "I'm here to help. What do you need?")


class EmotionalResponseGenerator:
    """Generates emotionally intelligent responses."""
    
    def __init__(self, model_name: str = "qwen3-vl:4b"):
        self.model_name = model_name
        self.analyzer = EmotionalAnalyzer()
    
    def generate_empathetic_response(self, user_query: str, response: str, 
                                    detected_emotion: Dict[str, Any]) -> str:
        """
        Modify response to be more empathetic based on detected emotion.
        """
        emotion = detected_emotion.get("primary_emotion", "neutral")
        intensity = detected_emotion.get("intensity", "medium")
        
        # Get empathetic opening
        empathy_opening = self.analyzer.generate_empathetic_response(emotion, intensity)
        
        # Adjust response tone based on emotion
        if emotion == "angry" and intensity in ["high", "medium"]:
            # Be more concise and action-oriented
            return f"{empathy_opening} Here's what we'll do:\n\n{response}"
        
        elif emotion == "sad":
            # Be more gentle and supportive
            return f"{empathy_opening} {response}\n\nRemember, things often get better. I'm here if you need anything else."
        
        elif emotion == "anxious":
            # Be clear and reassuring
            return f"{empathy_opening} {response}\n\nYou've got this. Take it one step at a time."
        
        elif emotion == "overwhelmed":
            # Break things down
            return f"{empathy_opening} Let's take this one piece at a time:\n\n{response}"
        
        elif emotion == "confused":
            # Extra clarity
            return f"{empathy_opening} {response}\n\nDoes this make sense? Feel free to ask for clarification."
        
        elif emotion == "happy" and intensity == "high":
            # Match energy
            return f"{empathy_opening} {response}\n\nLet's make it happen!"
        
        elif emotion == "tired":
            # Be brief and efficient
            return f"{empathy_opening}\n\n{response}\n\nRest well!"
        
        else:
            # Neutral emotion - standard response
            return f"{empathy_opening}\n\n{response}"
    
    def add_emotional_support(self, response: str, emotion: str) -> str:
        """Add supportive language appropriate to emotion."""
        support_phrases = {
            "angry": [
                "\nI understand this is frustrating.",
                "Let me make this right.",
                "Your patience means a lot."
            ],
            "sad": [
                "\nFeel free to reach out if you need more help.",
                "Things have a way of working out.",
                "I'm here for you."
            ],
            "anxious": [
                "\nTake your time. There's no rush.",
                "You're doing great.",
                "I believe in you."
            ],
            "overwhelmed": [
                "\nBreak it into smaller pieces.",
                "You don't have to do it all at once.",
                "Progress over perfection."
            ]
        }
        
        phrases = support_phrases.get(emotion, [])
        if phrases:
            # Add random support phrase
            import random
            return response + random.choice(phrases)
        
        return response
    
    def detect_need_for_check_in(self, emotion: str, intensity: str) -> Optional[str]:
        """
        Detect if AI should do an emotional check-in.
        """
        if emotion in ["sad", "angry", "anxious", "overwhelmed"] and intensity == "high":
            return f"I noticed you seem {emotion}. Are you doing okay? I'm concerned."
        elif emotion == "overwhelmed":
            return "There's a lot on your plate. Would it help to talk about what's bothering you most?"
        elif emotion == "tired":
            return "You sound exhausted. Maybe we should tackle this when you're fresher?"
        
        return None


# Global instances
emotional_analyzer = EmotionalAnalyzer()
emotional_response_generator = EmotionalResponseGenerator()
