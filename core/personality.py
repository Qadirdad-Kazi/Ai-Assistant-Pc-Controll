"""
Personality System
Maintains consistent personality traits based on Big Five model.
Ensures the AI responds with a coherent, consistent character across all interactions.
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PersonalityTraits:
    """Big Five personality model: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism."""
    openness: float = 0.65  # Creativity, curiosity (0-1)
    conscientiousness: float = 0.75  # Organized, reliable (0-1)
    extraversion: float = 0.55  # Social, energetic (0-1)
    agreeableness: float = 0.70  # Cooperative, empathetic (0-1)
    neuroticism: float = 0.35  # Emotional stability (0-1, high=unstable)
    
    def to_dict(self) -> Dict:
        """Convert traits to dictionary."""
        return {
            'openness': self.openness,
            'conscientiousness': self.conscientiousness,
            'extraversion': self.extraversion,
            'agreeableness': self.agreeableness,
            'neuroticism': self.neuroticism
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PersonalityTraits':
        """Create from dictionary."""
        return cls(**data)


class TraitVocabularyMapper:
    """Maps personality traits to vocabulary and communication patterns."""
    
    TRAIT_VOCABULARIES = {
        'openness': {
            'high': ['innovative', 'creative', 'imaginative', 'theoretical', 'abstract', 'philosophical'],
            'low': ['practical', 'realistic', 'concrete', 'straightforward', 'conventional', 'proven']
        },
        'conscientiousness': {
            'high': ['organized', 'thorough', 'detailed', 'systematic', 'precise', 'methodical'],
            'low': ['flexible', 'adaptive', 'spontaneous', 'intuitive', 'casual', 'relaxed']
        },
        'extraversion': {
            'high': ['enthusiastic', 'energetic', 'talkative', 'sociable', 'outgoing', 'collaborative'],
            'low': ['thoughtful', 'reserved', 'introspective', 'independent', 'focused', 'quiet']
        },
        'agreeableness': {
            'high': ['compassionate', 'understanding', 'supportive', 'cooperative', 'gentle', 'harmonic'],
            'low': ['direct', 'competitive', 'assertive', 'analytical', 'critical', 'objective']
        },
        'neuroticism': {
            'high': ['cautious', 'anxious', 'sensitive', 'reactive', 'worried', 'vigilant'],
            'low': ['calm', 'stable', 'confident', 'composed', 'resilient', 'secure']
        }
    }
    
    RESPONSE_PATTERNS = {
        'openness': {
            'high': 'Would you consider that from a different angle? What if we explored...',
            'low': 'Here are the facts. Based on proven methods...'
        },
        'conscientiousness': {
            'high': 'Let me break this down systematically. First... Second... Third...',
            'low': 'Here\'s the main idea. Feel free to adjust based on what works for you.'
        },
        'extraversion': {
            'high': 'Great question! Let\'s dive in together! I\'m excited to explore this with you.',
            'low': 'Here\'s what I\'ve found. I believe this is the core issue.'
        },
        'agreeableness': {
            'high': 'I understand this might be frustrating. Let me help you work through it gently.',
            'low': 'Here\'s the objective analysis. This is what the data shows.'
        },
        'neuroticism': {
            'high': 'I want to make sure we get this right. Let me double-check all possibilities.',
            'low': 'I\'m confident in this approach. Let\'s move forward decisively.'
        }
    }
    
    def get_vocabulary(self, trait_name: str, trait_value: float) -> List[str]:
        """Get vocabulary words for a trait level."""
        if trait_value > 0.65:
            return self.TRAIT_VOCABULARIES[trait_name]['high']
        else:
            return self.TRAIT_VOCABULARIES[trait_name]['low']
    
    def get_response_opening(self, trait_name: str, trait_value: float) -> str:
        """Get opening phrase matching trait level."""
        if trait_value > 0.65:
            return self.RESPONSE_PATTERNS[trait_name]['high']
        else:
            return self.RESPONSE_PATTERNS[trait_name]['low']


class PersonalityConsistencyTracker:
    """Tracks personality consistency across interactions."""
    
    def __init__(self, traits: PersonalityTraits):
        self.base_traits = traits
        self.current_traits = PersonalityTraits(**traits.to_dict())
        self.interaction_history: List[Dict] = []
        self.consistency_score = 1.0
        self.last_trait_drift = 0.0
    
    def record_interaction(self, response: str, detected_traits: Dict = None):
        """Record an interaction to track consistency."""
        drift = 0.0
        
        if detected_traits:
            # Calculate drift from base traits
            for trait_name, value in detected_traits.items():
                if hasattr(self.base_traits, trait_name):
                    diff = abs(value - getattr(self.base_traits, trait_name))
                    drift += diff
            
            drift /= len(detected_traits) if detected_traits else 1
        
        self.last_trait_drift = drift
        
        # Update consistency score (higher is more consistent)
        self.consistency_score = max(0.5, self.consistency_score - (drift * 0.1))
        
        self.interaction_history.append({
            'timestamp': datetime.now().isoformat(),
            'response_length': len(response),
            'trait_drift': drift,
            'consistency_score': self.consistency_score
        })
    
    def enforce_consistency(self, current_response: str) -> str:
        """Ensure response matches base personality traits."""
        # Get dominant trait
        traits_dict = self.base_traits.to_dict()
        dominant_trait = max(traits_dict.items(), key=lambda x: abs(x[1] - 0.5))
        
        # Prepend personality-consistent opening if consistency drifting
        if self.consistency_score < 0.8:
            mapper = TraitVocabularyMapper()
            opening = mapper.get_response_opening(dominant_trait[0], dominant_trait[1])
            current_response = f"{opening}\n\n{current_response}"
        
        return current_response
    
    def get_consistency_report(self) -> Dict:
        """Get consistency metrics."""
        avg_drift = (
            sum(i['trait_drift'] for i in self.interaction_history) 
            / len(self.interaction_history) 
            if self.interaction_history else 0
        )
        
        return {
            'consistency_score': self.consistency_score,
            'avg_trait_drift': avg_drift,
            'interactions_logged': len(self.interaction_history),
            'is_consistent': self.consistency_score > 0.75
        }


class ToneModulator:
    """Modulates response tone based on personality traits."""
    
    TONE_TEMPLATES = {
        'formal': {
            'greeting': 'Good day. I shall assist you.',
            'acknowledgment': 'I acknowledge your inquiry.',
            'closing': 'I remain at your service.'
        },
        'casual': {
            'greeting': 'Hey! What\'s up?',
            'acknowledgment': 'Yeah, I got that.',
            'closing': 'Let me know if you need anything else!'
        },
        'technical': {
            'greeting': 'System ready. Awaiting input.',
            'acknowledgment': 'Query received. Processing...',
            'closing': 'Execution complete.'
        },
        'supportive': {
            'greeting': 'I\'m here to help!',
            'acknowledgment': 'I completely understand. Let\'s work through this together.',
            'closing': 'You\'ve got this! I\'m here anytime.'
        },
        'analytical': {
            'greeting': 'Data set loaded. Ready for analysis.',
            'acknowledgment': 'Noted. Analyzing parameters...',
            'closing': 'Based on the analysis, here\'s what I recommend.'
        }
    }
    
    def __init__(self, traits: PersonalityTraits):
        self.traits = traits
        self.current_tone = self._determine_tone()
    
    def _determine_tone(self) -> str:
        """Determine tone based on traits."""
        traits_dict = self.traits.to_dict()
        
        # Conscientiousness high + Neuroticism low = Formal/Technical
        if traits_dict['conscientiousness'] > 0.7 and traits_dict['neuroticism'] < 0.4:
            return 'formal' if traits_dict['openness'] < 0.6 else 'technical'
        
        # Extraversion high + Agreeableness high = Casual/Supportive
        elif traits_dict['extraversion'] > 0.6 and traits_dict['agreeableness'] > 0.65:
            return 'casual' if traits_dict['neuroticism'] < 0.4 else 'supportive'
        
        # Openness high + Conscientiousness high = Analytical
        elif traits_dict['openness'] > 0.7 and traits_dict['conscientiousness'] > 0.7:
            return 'analytical'
        
        # Default: Supportive
        else:
            return 'supportive'
    
    def apply_tone(self, response: str) -> str:
        """Apply personality tone to response."""
        tone = self.current_tone
        template = self.TONE_TEMPLATES[tone]
        
        # Don't add greeting/closing to internal processing, only where appropriate
        if response.startswith('Processing') or response.startswith('Query'):
            return response
        
        return response
    
    def get_tone_descriptor(self) -> str:
        """Get description of current tone."""
        tone_descriptions = {
            'formal': 'Professional, structured, respectful',
            'casual': 'Friendly, relaxed, conversational',
            'technical': 'Data-focused, precise, objective',
            'supportive': 'Empathetic, helpful, encouraging',
            'analytical': 'Thorough, logical, detailed'
        }
        return tone_descriptions.get(self.current_tone, 'Balanced')


class PersonalitySystem:
    """Main personality system - integrates all personality components."""
    
    def __init__(self, base_traits: Optional[PersonalityTraits] = None):
        self.base_traits = base_traits or PersonalityTraits()
        self.consistency_tracker = PersonalityConsistencyTracker(self.base_traits)
        self.tone_modulator = ToneModulator(self.base_traits)
        self.vocabulary_mapper = TraitVocabularyMapper()
    
    def get_personality_profile(self) -> Dict:
        """Get comprehensive personality profile."""
        traits = self.base_traits.to_dict()
        return {
            'traits': traits,
            'dominant_traits': {
                k: v for k, v in sorted(traits.items(), key=lambda x: x[1], reverse=True)[:2]
            },
            'tone': self.tone_modulator.get_tone_descriptor(),
            'consistency_score': self.consistency_tracker.consistency_score
        }
    
    def personalize_response_with_traits(self, response: str) -> str:
        """Apply personality traits to response."""
        # Apply tone
        response = self.tone_modulator.apply_tone(response)
        
        # Ensure consistency
        response = self.consistency_tracker.enforce_consistency(response)
        
        # Record for consistency tracking
        self.consistency_tracker.record_interaction(response)
        
        return response
    
    def modify_for_conscientiousness(self, response: str) -> str:
        """Modify response based on conscientiousness level."""
        if self.base_traits.conscientiousness > 0.7:
            # High conscientiousness: add detailed structure
            lines = response.split('\n')
            if len(lines) > 3:
                # Number the points
                structured = []
                counter = 1
                for line in lines:
                    if line.strip():
                        structured.append(f"{counter}. {line}")
                        counter += 1
                return '\n'.join(structured)
        return response
    
    def modify_for_agreeableness(self, response: str) -> str:
        """Modify response based on agreeableness level."""
        if self.base_traits.agreeableness > 0.7:
            # High agreeableness: add empathetic elements
            if not any(word in response.lower() for word in ['understand', 'appreciate', 'value', 'respect']):
                response = f"I appreciate your question. {response}"
        return response
    
    def modify_for_openness(self, response: str) -> str:
        """Modify response based on openness level."""
        if self.base_traits.openness > 0.7:
            # High openness: encourage exploration
            if not response.endswith('?'):
                response += f"\n\nWould you like to explore other perspectives on this?"
        return response
    
    def apply_all_trait_modifications(self, response: str) -> str:
        """Apply all personality modifications to response."""
        response = self.modify_for_conscientiousness(response)
        response = self.modify_for_agreeableness(response)
        response = self.modify_for_openness(response)
        return self.personalize_response_with_traits(response)
    
    def set_temporary_trait_override(self, **trait_overrides) -> 'PersonalityTraits':
        """Temporarily modify traits (e.g., be more formal for official response)."""
        temp_traits = PersonalityTraits(**self.base_traits.to_dict())
        for trait_name, value in trait_overrides.items():
            if hasattr(temp_traits, trait_name):
                setattr(temp_traits, trait_name, max(0, min(1, value)))
        return temp_traits
    
    def get_trait_explanation(self, trait_name: str) -> str:
        """Get explanation of how a trait affects responses."""
        explanations = {
            'openness': 'High openness means I\'m creative and curious. Low means I\'m practical and conventional.',
            'conscientiousness': 'High conscientiousness means I\'m organized and thorough. Low means I\'m flexible and spontaneous.',
            'extraversion': 'High extraversion means I\'m sociable and enthusiastic. Low means I\'m reserved and thoughtful.',
            'agreeableness': 'High agreeableness means I\'m compassionate and cooperative. Low means I\'m direct and analytical.',
            'neuroticism': 'High neuroticism means I\'m cautious and sensitive. Low means I\'m calm and confident.'
        }
        return explanations.get(trait_name, 'Unknown trait.')
    
    def get_consistency_status(self) -> str:
        """Get status of personality consistency."""
        report = self.consistency_tracker.get_consistency_report()
        if report['is_consistent']:
            return f"Personality consistent ({report['consistency_score']:.2f}). No drift detected."
        else:
            return f"Personality consistency at {report['consistency_score']:.2f}. Average drift: {report['avg_trait_drift']:.3f}"


# Global instances
default_personality_traits = PersonalityTraits(
    openness=0.65,
    conscientiousness=0.75,
    extraversion=0.55,
    agreeableness=0.70,
    neuroticism=0.35
)

personality_system = PersonalitySystem(default_personality_traits)
