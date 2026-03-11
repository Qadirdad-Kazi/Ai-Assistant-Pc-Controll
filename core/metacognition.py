"""
Metacognition Engine
Enables self-monitoring, thinking-about-thinking, and recognition of limitations.
Adds realistic self-doubt and uncertainty expressions to responses.
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ThinkingMetadata:
    """Metadata about the thinking process."""
    process_steps: List[str]
    confidence_levels: List[float]
    uncertainty_indicators: List[str]
    reasoning_quality: float
    potential_gaps: List[str]
    alternative_approaches: List[str]


class SelfMonitor:
    """Monitors AI's own reasoning and response quality."""
    
    # Metrics that indicate problematic thinking
    RED_FLAGS = {
        'circular_logic': 'reasoning returns to same point',
        'unverified_assumption': 'making assumption without basis',
        'hasty_generalization': 'generalizing from limited evidence',
        'false_certainty': 'claiming certainty without evidence',
        'cognitive_bias': 'showing systematic bias in reasoning',
        'insufficient_evidence': 'conclusion not supported by evidence',
        'logical_fallacy': 'using invalid logical form'
    }
    
    def __init__(self):
        self.monitoring_history = []
        self.detected_errors = []
        self.reasoning_patterns = {}
    
    def analyze_reasoning_chain(self, reasoning_steps: List[str]) -> Dict:
        """Analyze a chain of reasoning for issues."""
        analysis = {
            'step_count': len(reasoning_steps),
            'red_flags': [],
            'confidence_by_step': [],
            'potential_issues': [],
            'overall_quality': 0.8  # Start at 0.8, deduct for issues
        }
        
        # Check for circular logic
        if len(reasoning_steps) > 2:
            if reasoning_steps[0].lower() == reasoning_steps[-1].lower():
                analysis['red_flags'].append('circular_logic')
                analysis['overall_quality'] -= 0.2
        
        # Check for unverified assumptions
        assumption_keywords = ['assume', 'must be', 'clearly', 'obviously', 'obviously true']
        for step in reasoning_steps:
            if any(keyword in step.lower() for keyword in assumption_keywords):
                if 'evidence' not in step.lower():
                    analysis['red_flags'].append('unverified_assumption')
                    analysis['potential_issues'].append(f"Step may make unverified assumption: {step}")
                    analysis['overall_quality'] -= 0.1
        
        # Check for hasty generalization
        if len(reasoning_steps) < 3 and 'all' in ' '.join(reasoning_steps).lower():
            analysis['red_flags'].append('hasty_generalization')
            analysis['overall_quality'] -= 0.15
        
        # Check for false certainty markers
        false_certainty = ['definitely', 'absolutely', 'impossible that', 'must']
        for step in reasoning_steps:
            if any(word in step.lower() for word in false_certainty):
                analysis['red_flags'].append('false_certainty')
                analysis['potential_issues'].append(f"Using inappropriate certainty marker: {step}")
                analysis['overall_quality'] -= 0.05
        
        analysis['overall_quality'] = max(0.3, min(1.0, analysis['overall_quality']))
        
        self.monitoring_history.append({
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis
        })
        
        return analysis
    
    def detect_logical_fallacies(self, reasoning_steps: List[str]) -> List[str]:
        """Detect common logical fallacies in reasoning."""
        fallacies_detected = []
        reasoning_text = ' '.join(reasoning_steps).lower()
        
        # Ad hominem
        if any(word in reasoning_text for word in ['he said', 'she believes', 'they think']):
            if 'therefore' in reasoning_text or 'thus' in reasoning_text:
                fallacies_detected.append('ad_hominem')
        
        # Straw man
        if 'people say' in reasoning_text or 'someone claims' in reasoning_text:
            if 'but that\'s wrong' in reasoning_text:
                fallacies_detected.append('straw_man')
        
        # False dilemma
        if 'either' in reasoning_text and 'or' in reasoning_text:
            if len(reasoning_steps) < 3:
                fallacies_detected.append('false_dilemma')
        
        # Appeal to authority
        if 'expert said' in reasoning_text or 'study shows' in reasoning_text:
            if 'therefore' in reasoning_text and len(reasoning_steps) < 2:
                fallacies_detected.append('appeal_to_authority')
        
        return fallacies_detected
    
    def get_self_awareness_assessment(self) -> Dict:
        """Generate self-awareness assessment."""
        recent_analyses = self.monitoring_history[-10:] if self.monitoring_history else []
        
        if not recent_analyses:
            return {
                'analyses_performed': 0,
                'avg_reasoning_quality': 0.8,
                'error_detection_rate': 0.0,
                'self_awareness_level': 'developing'
            }
        
        avg_quality = sum(a['analysis']['overall_quality'] for a in recent_analyses) / len(recent_analyses)
        error_count = sum(len(a['analysis']['red_flags']) for a in recent_analyses)
        
        return {
            'analyses_performed': len(self.monitoring_history),
            'recent_analyses': len(recent_analyses),
            'avg_reasoning_quality': avg_quality,
            'error_detection_rate': error_count / len(recent_analyses) if recent_analyses else 0.0,
            'self_awareness_level': 'high' if avg_quality > 0.75 else 'moderate' if avg_quality > 0.6 else 'developing'
        }


class LimitationRecognizer:
    """Recognizes and expresses AI model limitations."""
    
    EXPERTISE_BOUNDARIES = {
        'medical': {
            'expertise_level': 'low',
            'warning': 'This involves medical decisions - I\'m not a physician',
            'requires_disclaimer': True,
            'suggested_action': 'Consult a healthcare professional'
        },
        'legal': {
            'expertise_level': 'low',
            'warning': 'This involves legal matters - I\'m not a lawyer',
            'requires_disclaimer': True,
            'suggested_action': 'Consult a legal professional'
        },
        'financial': {
            'expertise_level': 'low',
            'warning': 'This involves financial advice - not my area of expertise',
            'requires_disclaimer': True,
            'suggested_action': 'Consult a financial advisor'
        },
        'mental_health': {
            'expertise_level': 'very_low',
            'warning': 'This involves mental health - I cannot provide therapy',
            'requires_disclaimer': True,
            'suggested_action': 'Speak with a mental health professional'
        },
        'current_events': {
            'expertise_level': 'moderate',
            'warning': 'My knowledge has a cutoff date',
            'requires_disclaimer': False,
            'suggested_action': 'Verify current information'
        },
        'programming': {
            'expertise_level': 'high',
            'warning': None,
            'requires_disclaimer': False,
            'suggested_action': None
        },
        'math': {
            'expertise_level': 'high',
            'warning': None,
            'requires_disclaimer': False,
            'suggested_action': None
        },
        'technical': {
            'expertise_level': 'high',
            'warning': None,
            'requires_disclaimer': False,
            'suggested_action': None
        }
    }
    
    # Personal limitations
    KNOWN_LIMITATIONS = [
        'Cannot truly understand human emotions',
        'Cannot access real-time information',
        'Cannot learn permanently from conversations',
        'Cannot see or process images',
        'Cannot access external URLs directly',
        'Cannot execute code on user\'s system',
        'May have knowledge cutoffs',
        'Can be fooled by well-crafted misleading information',
        'May exhibit biases from training data',
        'Cannot maintain perfect memory across sessions'
    ]
    
    def __init__(self):
        self.acknowledged_limitations = []
        self.expertise_queries = {}
    
    def detect_domain(self, query: str) -> Optional[str]:
        """Detect if query is in a domain with known limitations."""
        query_lower = query.lower()
        
        for domain, info in self.EXPERTISE_BOUNDARIES.items():
            domain_keywords = {
                'medical': ['doctor', 'health', 'disease', 'symptom', 'medicine', 'prescription'],
                'legal': ['lawyer', 'law', 'contract', 'lawsuit', 'legal', 'court'],
                'financial': ['invest', 'money', 'stock', 'crypto', 'currency', 'loan', 'mortgage'],
                'mental_health': ['depression', 'anxiety', 'therapy', 'suicide', 'mental', 'trauma'],
                'current_events': ['today', 'now', 'latest', 'recent', 'news', '2024'],
            }
            
            keywords = domain_keywords.get(domain, [])
            if any(keyword in query_lower for keyword in keywords):
                return domain
        
        return None
    
    def get_limitation_warning(self, domain: Optional[str]) -> Optional[str]:
        """Get warning/disclaimer for domain if needed."""
        if not domain or domain not in self.EXPERTISE_BOUNDARIES:
            return None
        
        info = self.EXPERTISE_BOUNDARIES[domain]
        if info['requires_disclaimer']:
            self.acknowledged_limitations.append(domain)
            return info['warning']
        
        return None
    
    def should_add_disclaimer(self, domain: Optional[str]) -> bool:
        """Check if domain requires disclaimer."""
        if not domain or domain not in self.EXPERTISE_BOUNDARIES:
            return False
        
        return self.EXPERTISE_BOUNDARIES[domain]['requires_disclaimer']
    
    def get_expertise_admission(self, topic: str) -> str:
        """Get an honest admission of expertise level."""
        domain = self.detect_domain(topic)
        
        if not domain:
            return "I can provide general information, but the accuracy depends on the specific topic."
        
        info = self.EXPERTISE_BOUNDARIES[domain]
        level = info['expertise_level']
        
        if level == 'very_low':
            return f"I have very limited expertise in this area. {info['suggested_action']}."
        elif level == 'low':
            return f"I have limited expertise here. My response is general only. {info['suggested_action']}."
        elif level == 'moderate':
            return f"I can help with general aspects, but {info['suggested_action']}."
        else:
            return "I should be able to help with this."


class MetacognitiveResponder:
    """Generates responses that include metacognitive elements."""
    
    SELF_DOUBT_EXPRESSIONS = {
        'mild': [
            'I think...',
            'It seems like...',
            "I'd say...",
            'From my perspective...',
            'If I understand correctly...',
            'This could mean...',
            'One possibility is...'
        ],
        'moderate': [
            'I\'m not entirely sure, but...',
            'I could be wrong, but...',
            'Based on limited information...',
            'This is uncertain, but...',
            'I should note that I\'m not certain...',
            'There\'s some ambiguity here...',
            'I may be missing context, but...'
        ],
        'strong': [
            'I\'m quite uncertain about this, but...',
            'I should be honest - I don\'t fully understand this...',
            'This is outside my confidence zone...',
            'I could easily be wrong about this...',
            'I lack sufficient information here...',
            'I\'m reluctant to claim expertise, but...',
            'This requires more context than I have...'
        ]
    }
    
    THINKING_TRANSPARENCY = {
        'show_reasoning': 'Here\'s my thinking: ',
        'acknowledge_alternative': 'That said, I could be wrong and...',
        'express_uncertainty': 'I\'m less confident about this part: ',
        'admit_gap': 'I don\'t have enough info on this: ',
        'consider_edge_case': 'An edge case I should mention: '
    }
    
    def __init__(self):
        self.responses_with_metacognition = []
    
    def add_self_doubt(self, response: str, certainty_level: float = 0.5) -> str:
        """Add appropriate self-doubt/uncertainty to response."""
        if certainty_level > 0.85:
            doubt_level = 'mild'
        elif certainty_level > 0.65:
            doubt_level = 'moderate'
        else:
            doubt_level = 'strong'
        
        import random
        doubt_expression = random.choice(self.SELF_DOUBT_EXPRESSIONS[doubt_level])
        
        # Add doubt expression only if response doesn't already have it
        if not any(expr in response for expr in self.SELF_DOUBT_EXPRESSIONS['mild']):
            response = f"{doubt_expression} {response.lower() if response[0].isupper() else response}"
        
        return response
    
    def add_reasoning_transparency(self, response: str, reasoning_steps: List[str]) -> str:
        """Add transparency about thinking process."""
        if not reasoning_steps or len(reasoning_steps) < 2:
            return response
        
        transparent_response = response + "\n\n**My thinking process:**"
        for i, step in enumerate(reasoning_steps[:3], 1):  # Show first 3 steps
            transparent_response += f"\n{i}. {step}"
        
        return transparent_response
    
    def add_uncertainty_markers(self, response: str, uncertainty_aspects: List[str]) -> str:
        """Add markers about uncertain aspects."""
        if not uncertainty_aspects:
            return response
        
        marked_response = response + "\n\n**Aspects I'm less certain about:**"
        for aspect in uncertainty_aspects[:2]:  # Show first 2 uncertain aspects
            marked_response += f"\n- {aspect}"
        
        return marked_response
    
    def add_limitation_acknowledgment(self, response: str, limitations: List[str]) -> str:
        """Add acknowledgment of relevant limitations."""
        if not limitations:
            return response
        
        acknowledged = response + "\n\n**Relevant limitations:**"
        for limitation in limitations[:2]:
            acknowledged += f"\n- {limitation}"
        
        return acknowledged
    
    def generate_metacognitive_response(self, base_response: str, 
                                       reasoning_steps: List[str] = None,
                                       uncertainty_aspects: List[str] = None,
                                       limitations: List[str] = None,
                                       certainty_level: float = 0.7) -> str:
        """Generate response with metacognitive elements."""
        response = base_response
        
        # Add self-doubt if low certainty
        if certainty_level < 0.6:
            response = self.add_self_doubt(response, certainty_level)
        
        # Add reasoning transparency
        if reasoning_steps:
            response = self.add_reasoning_transparency(response, reasoning_steps)
        
        # Mark uncertain aspects
        if uncertainty_aspects:
            response = self.add_uncertainty_markers(response, uncertainty_aspects)
        
        # Acknowledge limitations
        if limitations:
            response = self.add_limitation_acknowledgment(response, limitations)
        
        self.responses_with_metacognition.append({
            'timestamp': datetime.now().isoformat(),
            'original_length': len(base_response),
            'enhanced_length': len(response),
            'certainty_level': certainty_level
        })
        
        return response


class MetacognitionEngine:
    """Main metacognition system - coordinates all metacognitive components."""
    
    def __init__(self):
        self.self_monitor = SelfMonitor()
        self.limitation_recognizer = LimitationRecognizer()
        self.metacognitive_responder = MetacognitiveResponder()
        self.processing_log = []
    
    def process_with_metacognition(self, 
                                   query: str,
                                   response: str,
                                   reasoning_steps: List[str] = None,
                                   confidence: float = 0.7) -> Dict:
        """Process response through full metacognition system."""
        
        # Step 1: Analyze reasoning for issues
        reasoning_analysis = {}
        if reasoning_steps:
            reasoning_analysis = self.self_monitor.analyze_reasoning_chain(reasoning_steps)
        
        # Step 2: Detect domain and limitations
        domain = self.limitation_recognizer.detect_domain(query)
        warning = self.limitation_recognizer.get_limitation_warning(domain)
        
        # Step 3: Detect logical fallacies
        fallacies = []
        if reasoning_steps:
            fallacies = self.self_monitor.detect_logical_fallacies(reasoning_steps)
        
        # Step 4: Adjust confidence if issues found
        adjusted_confidence = confidence
        if reasoning_analysis.get('red_flags'):
            adjusted_confidence *= 0.8  # Reduce confidence by 20%
        if fallacies:
            adjusted_confidence *= 0.85  # Reduce further for fallacies
        
        # Step 5: Generate uncertainty aspects
        uncertainty_aspects = []
        if adjusted_confidence < 0.5:
            uncertainty_aspects.append('Low confidence in reasoning quality')
        if domain and self.limitation_recognizer.should_add_disclaimer(domain):
            uncertainty_aspects.append(f'Limited expertise in {domain}')
        if fallacies:
            uncertainty_aspects.append(f'Detected logical issues: {", ".join(fallacies)}')
        
        # Step 6: Generate metacognitive response
        final_response = self.metacognitive_responder.generate_metacognitive_response(
            response,
            reasoning_steps=reasoning_steps,
            uncertainty_aspects=uncertainty_aspects,
            limitations=[],
            certainty_level=adjusted_confidence
        )
        
        # Add warning if domain-specific
        if warning:
            final_response = f"⚠️ {warning}\n\n{final_response}"
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query[:100],
            'original_confidence': confidence,
            'adjusted_confidence': adjusted_confidence,
            'domain': domain,
            'reasoning_red_flags': reasoning_analysis.get('red_flags', []),
            'fallacies_detected': fallacies,
            'response_output_token_increase': len(final_response) - len(response)
        }
        
        self.processing_log.append(log_entry)
        
        return {
            'final_response': final_response,
            'confidence': adjusted_confidence,
            'has_warning': warning is not None,
            'warning_message': warning,
            'red_flags': reasoning_analysis.get('red_flags', []),
            'fallacies': fallacies,
            'analysis': log_entry
        }
    
    def get_metacognition_report(self) -> Dict:
        """Get comprehensive metacognition report."""
        self_awareness = self.self_monitor.get_self_awareness_assessment()
        acknowledged_limitations = self.limitation_recognizer.acknowledged_limitations
        
        return {
            'self_awareness': self_awareness,
            'acknowledged_limitations': acknowledged_limitations,
            'total_queries_metacognitive': len(self.processing_log),
            'avg_confidence_adjustment': (
                sum(abs(entry['adjusted_confidence'] - entry['original_confidence']) 
                    for entry in self.processing_log) / len(self.processing_log)
                if self.processing_log else 0.0
            ),
            'warnings_issued': sum(1 for entry in self.processing_log if entry['warning_message'] is not None),
            'processing_history': self.processing_log[-10:] if self.processing_log else []
        }
    
    def get_honest_self_assessment(self) -> str:
        """Get an honest self-assessment of capabilities."""
        report = self.get_metacognition_report()
        
        assessment = (
            f"Self-Assessment Report:\n"
            f"- Self-awareness level: {report['self_awareness']['self_awareness_level']}\n"
            f"- Average reasoning quality: {report['self_awareness']['avg_reasoning_quality']:.2f}/1.0\n"
            f"- Confidence adjustment frequency: {report['avg_confidence_adjustment']:.3f}\n"
            f"- Domains where I admit limitations: {len(report['acknowledged_limitations'])}\n"
            f"- Known personal limitations:\n"
        )
        
        for limitation in LimitationRecognizer.KNOWN_LIMITATIONS[:5]:
            assessment += f"  • {limitation}\n"
        
        return assessment


# Global instance
metacognition_engine = MetacognitionEngine()
