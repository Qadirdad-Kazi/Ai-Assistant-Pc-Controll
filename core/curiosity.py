"""
Curiosity & Questioning Module
Enables the AI to ask proactive clarifying questions and seek information.
"""

import json
from typing import Dict, Any, List, Optional
from config import OLLAMA_URL, GRAY, RESET, CYAN, GREEN, YELLOW
import requests

http_session = requests.Session()


class CuriosityEngine:
    """Drives curiosity-based interactions and proactive questioning."""
    
    def __init__(self, model_name: str = "qwen3-vl:4b"):
        self.model_name = model_name
        self.knowledge_gaps = []
        self.clarification_history = []
    
    def identify_ambiguities(self, user_query: str) -> List[str]:
        """
        Identify ambiguous or unclear aspects of user query.
        """
        ambiguities = []
        query_lower = user_query.lower()
        
        # Check for common ambiguous patterns
        ambiguous_patterns = {
            "it": "Are you referring to something specific?",
            "that": "Which specific thing are you talking about?",
            "there": "Is there a specific location you mean?",
            "they": "Who exactly are you referring to?",
            "some": "How much exactly?",
            "soon": "When specifically do you need this?",
            "fast": "How fast does it need to be?",
            "big": "How large or significant?",
            "small": "How small or minor?",
        }
        
        for pattern, question in ambiguous_patterns.items():
            if f" {pattern} " in f" {query_lower} " or query_lower.startswith(pattern) or query_lower.endswith(pattern):
                ambiguities.append(question)
        
        return ambiguities
    
    def generate_clarifying_questions(self, user_query: str, context: str = "") -> List[str]:
        """
        Generate proactive clarifying questions before attempting answer.
        """
        print(f"{CYAN}[Curiosity] Generating clarifying questions...{RESET}")
        
        questions = []
        
        # Check for missing context
        if len(user_query) < 10:
            questions.append("Can you provide more details about what you're asking?")
        
        # Identify ambiguities
        ambiguities = self.identify_ambiguities(user_query)
        questions.extend(ambiguities)
        
        # Use LLM to generate intelligent questions
        try:
            smart_questions = self._generate_smart_questions(user_query, context)
            questions.extend(smart_questions)
        except:
            pass
        
        # Remove duplicates
        questions = list(dict.fromkeys(questions))[:3]  # Max 3 questions
        
        return questions
    
    def _generate_smart_questions(self, query: str, context: str = "") -> List[str]:
        """Use LLM to generate intelligent clarifying questions."""
        
        prompt = f"""Generate 2 clarifying questions that would help you better understand and assist with this query:

Query: {query}
{f'Context: {context}' if context else ''}

Focus on:
1. What specific information is missing?
2. What assumptions might be wrong?
3. What is the actual goal/intent?

Generate ONLY the questions, one per line, starting with "1. " and "2. "
Keep questions brief and natural."""
        
        try:
            response = http_session.post(
                f"{OLLAMA_URL}/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": "5m"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                response_text = response.json().get("response", "")
                # Extract questions
                lines = [line.strip() for line in response_text.split("\n") if line.strip()]
                # Filter to actual questions
                questions = [q.lstrip("0123456789. ") for q in lines if "?" in q]
                return questions[:2]
        
        except Exception as e:
            print(f"{GRAY}[Curiosity] Error generating questions: {e}{RESET}")
        
        return []
    
    def should_ask_clarifying_questions(self, query: str) -> bool:
        """
        Determine if clarifying questions are needed.
        """
        # Don't ask for very simple/clear queries
        if any(indicator in query.lower() for indicator in ["show me", "tell me", "open", "close", "play"]):
            ambiguities = self.identify_ambiguities(query)
            return len(ambiguities) > 0
        
        # Ask for complex or ambiguous queries
        if len(query) < 8:
            return True
        
        if any(word in query.lower() for word in ["that", "it", "this", "they"]):
            return True
        
        return False
    
    def record_clarification(self, original_query: str, clarifying_questions: List[str], user_clarification: str):
        """
        Record a clarification exchange for learning.
        """
        self.clarification_history.append({
            "original_query": original_query,
            "clarifying_questions": clarifying_questions,
            "user_clarification": user_clarification,
            "timestamp": str(__import__('datetime').datetime.now())
        })


class KnowledgeGapDetector:
    """Detects areas where AI lacks information or knowledge."""
    
    def __init__(self):
        self.detected_gaps = []
        self.gap_followups = {}
    
    def detect_knowledge_gaps(self, query: str) -> List[str]:
        """
        Identify what information the AI doesn't know.
        """
        gaps = []
        
        # Domain-specific gaps
        specialized_domains = {
            "medical": "This involves medical knowledge I should be cautious about",
            "legal": "This requires legal expertise I may not have",
            "financial": "This involves financial advice I shouldn't give",
            "personal": "This is personal and I should ask more details",
            "technical": "This requires specific technical knowledge",
        }
        
        for domain, gap_description in specialized_domains.items():
            if domain in query.lower():
                gaps.append(gap_description)
        
        return gaps
    
    def acknowledge_knowledge_limits(self, gap: str) -> str:
        """
        Generate honest acknowledgment of knowledge limits.
        """
        acknowledgments = {
            "medical": "I'm not a doctor - you should consult a medical professional.",
            "legal": "I'm not a lawyer - consider seeking legal advice.",
            "financial": "I can't give financial advice - consult a financial advisor.",
            "personal": "I want to understand your situation better.",
            "technical": "Let me make sure I understand the technical specifics..."
        }
        
        for domain, ack in acknowledgments.items():
            if domain in gap.lower():
                return ack
        
        return "I want to make sure I understand this correctly."
    
    def generate_follow_up_research(self, gap: str) -> Optional[str]:
        """
        Suggest what research/clarification would help fill the gap.
        """
        suggestions = {
            "medical": "Could you describe the symptoms more specifically?",
            "legal": "What specific legal issue are you facing?",
            "financial": "What is your financial goal or concern?",
            "personal": "Can you tell me more about your specific situation?",
            "technical": "What technology stack or system are you working with?",
        }
        
        for domain, suggestion in suggestions.items():
            if domain in gap.lower():
                return suggestion
        
        return "Could you provide more context?"


class ProactiveQuestionGenerator:
    """Generates follow-up questions based on previous responses."""
    
    def __init__(self, model_name: str = "qwen3-vl:4b"):
        self.model_name = model_name
    
    def generate_follow_up_questions(self, user_query: str, ai_response: str) -> List[str]:
        """
        Generate natural follow-up questions after responding.
        """
        print(f"{CYAN}[Curiosity] Generating contextual follow-up questions...{RESET}")
        
        prompt = f"""Based on this query and response, what would be natural follow-up questions the user might have?

Original Query: {user_query}
Response: {ai_response[:300]}

Generate 2 follow-up questions that would be helpful, realistic, and show curiosity about what comes next.
Keep them brief and natural. Format: "1. " and "2. "
Only output the questions, nothing else."""
        
        try:
            response = http_session.post(
                f"{OLLAMA_URL}/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": "5m"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                response_text = response.json().get("response", "")
                lines = [line.strip() for line in response_text.split("\n") if line.strip()]
                questions = [q.lstrip("0123456789. ") for q in lines if "?" in q]
                return questions[:2]
        
        except Exception as e:
            print(f"{GRAY}[Curiosity] Error: {e}{RESET}")
        
        return []


# Global instances
curiosity_engine = CuriosityEngine()
knowledge_gap_detector = KnowledgeGapDetector()
proactive_question_generator = ProactiveQuestionGenerator()
