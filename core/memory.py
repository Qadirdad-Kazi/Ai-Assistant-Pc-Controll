"""
Memory & Context Persistence Module
Enables the AI to retain information across interactions and learn from past experiences.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import GRAY, RESET, CYAN, GREEN, YELLOW

# Memory storage path
MEMORY_DIR = "data/memory"
REASONING_LOG = os.path.join(MEMORY_DIR, "reasoning_log.json")
INTERACTION_HISTORY = os.path.join(MEMORY_DIR, "interaction_history.json")
LEARNED_PATTERNS = os.path.join(MEMORY_DIR, "learned_patterns.json")
USER_PREFERENCES = os.path.join(MEMORY_DIR, "user_preferences.json")


class MemoryManager:
    """Manages persistent memory storage and retrieval."""
    
    def __init__(self):
        self._ensure_directories()
        self.current_session_id = self._generate_session_id()
        self.session_memory = {}
        self.loaded_patterns = self._load_learned_patterns()
        self.loaded_preferences = self._load_user_preferences()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Session Management
    # ─────────────────────────────────────────────────────────────────────────
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def get_session_id(self) -> str:
        """Get current session ID."""
        return self.current_session_id
    
    # ─────────────────────────────────────────────────────────────────────────
    # Reasoning Log
    # ─────────────────────────────────────────────────────────────────────────
    
    def log_reasoning(self, query: str, reasoning_steps: List[str], action_taken: str, result: Any, confidence: float = 0.0) -> bool:
        """Log reasoning process for future reference."""
        try:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.current_session_id,
                "query": query,
                "reasoning_steps": reasoning_steps,
                "action_taken": action_taken,
                "result": str(result)[:500],  # Truncate long results
                "confidence": confidence
            }
            
            log_data = self._load_json_file(REASONING_LOG, default=[])
            log_data.append(entry)
            
            # Keep only last 1000 entries
            if len(log_data) > 1000:
                log_data = log_data[-1000:]
            
            self._save_json_file(REASONING_LOG, log_data)
            print(f"{CYAN}[Memory] Reasoning logged.{RESET}")
            return True
        
        except Exception as e:
            print(f"{GRAY}[Memory] Failed to log reasoning: {e}{RESET}")
            return False
    
    def get_similar_reasoning(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieve similar past reasoning for reference."""
        try:
            log_data = self._load_json_file(REASONING_LOG, default=[])
            
            # Simple keyword matching for similarity
            query_words = set(query.lower().split())
            scored_entries = []
            
            for entry in log_data:
                entry_words = set(entry.get("query", "").lower().split())
                similarity = len(query_words & entry_words) / max(len(query_words), 1)
                
                if similarity > 0.3:  # At least 30% match
                    scored_entries.append((similarity, entry))
            
            # Sort by similarity and return top N
            scored_entries.sort(key=lambda x: x[0], reverse=True)
            return [entry for _, entry in scored_entries[:limit]]
        
        except Exception as e:
            print(f"{GRAY}[Memory] Error retrieving similar reasoning: {e}{RESET}")
            return []
    
    # ─────────────────────────────────────────────────────────────────────────
    # Interaction History
    # ─────────────────────────────────────────────────────────────────────────
    
    def log_interaction(self, user_input: str, ai_response: str, interaction_type: str = "chat", metadata: Dict[str, Any] = None) -> bool:
        """Log user-AI interaction."""
        try:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.current_session_id,
                "user_input": user_input,
                "ai_response": ai_response[:500],  # Truncate
                "interaction_type": interaction_type,
                "metadata": metadata or {}
            }
            
            history_data = self._load_json_file(INTERACTION_HISTORY, default=[])
            history_data.append(entry)
            
            # Keep only last 2000 entries
            if len(history_data) > 2000:
                history_data = history_data[-2000:]
            
            self._save_json_file(INTERACTION_HISTORY, history_data)
            print(f"{CYAN}[Memory] Interaction logged.{RESET}")
            return True
        
        except Exception as e:
            print(f"{GRAY}[Memory] Failed to log interaction: {e}{RESET}")
            return False
    
    def get_conversation_context(self, limit: int = 5) -> List[Dict[str, str]]:
        """Get recent conversation history for context."""
        try:
            history_data = self._load_json_file(INTERACTION_HISTORY, default=[])
            
            # Filter by current session
            session_interactions = [
                {"user": h["user_input"], "ai": h["ai_response"]}
                for h in history_data if h.get("session_id") == self.current_session_id
            ]
            
            return session_interactions[-limit:]
        
        except Exception as e:
            print(f"{GRAY}[Memory] Error retrieving context: {e}{RESET}")
            return []
    
    # ─────────────────────────────────────────────────────────────────────────
    # Pattern Learning
    # ─────────────────────────────────────────────────────────────────────────
    
    def learn_pattern(self, pattern_name: str, pattern_data: Dict[str, Any]) -> bool:
        """Learn and store a recurring pattern."""
        try:
            patterns = self._load_json_file(LEARNED_PATTERNS, default={})
            
            if pattern_name in patterns:
                # Update existing pattern
                patterns[pattern_name]["occurrences"] = patterns[pattern_name].get("occurrences", 0) + 1
                patterns[pattern_name]["last_seen"] = datetime.now().isoformat()
                patterns[pattern_name]["data"].update(pattern_data)
            else:
                # New pattern
                patterns[pattern_name] = {
                    "first_seen": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat(),
                    "occurrences": 1,
                    "data": pattern_data
                }
            
            self._save_json_file(LEARNED_PATTERNS, patterns)
            print(f"{GREEN}[Memory] Pattern '{pattern_name}' learned.{RESET}")
            return True
        
        except Exception as e:
            print(f"{GRAY}[Memory] Failed to learn pattern: {e}{RESET}")
            return False
    
    def get_learned_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get all learned patterns."""
        return self.loaded_patterns
    
    def get_pattern(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """Get specific learned pattern."""
        return self.loaded_patterns.get(pattern_name)
    
    def find_similar_patterns(self, keywords: List[str], limit: int = 3) -> List[tuple]:
        """Find patterns matching keywords."""
        try:
            matching_patterns = []
            keywords_set = set(keywords)
            
            for name, data in self.loaded_patterns.items():
                pattern_keywords = set(
                    data.get("data", {}).get("keywords", [])
                )
                
                overlap = len(keywords_set & pattern_keywords)
                if overlap > 0:
                    matching_patterns.append((overlap, name, data))
            
            matching_patterns.sort(reverse=True)
            return [(name, data) for _, name, data in matching_patterns[:limit]]
        
        except Exception as e:
            print(f"{GRAY}[Memory] Error finding patterns: {e}{RESET}")
            return []
    
    # ─────────────────────────────────────────────────────────────────────────
    # User Preferences
    # ─────────────────────────────────────────────────────────────────────────
    
    def save_user_preference(self, key: str, value: Any) -> bool:
        """Save user preference."""
        try:
            preferences = self._load_json_file(USER_PREFERENCES, default={})
            preferences[key] = value
            self._save_json_file(USER_PREFERENCES, preferences)
            print(f"{CYAN}[Memory] Preference '{key}' saved.{RESET}")
            return True
        
        except Exception as e:
            print(f"{GRAY}[Memory] Failed to save preference: {e}{RESET}")
            return False
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference."""
        return self.loaded_preferences.get(key, default)
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all user preferences."""
        return self.loaded_preferences.copy()
    
    # ─────────────────────────────────────────────────────────────────────────
    # Context Window Management
    # ─────────────────────────────────────────────────────────────────────────
    
    def build_context_window(self, recent_limit: int = 5, include_patterns: bool = True) -> str:
        """Build context string from memory for use in prompts."""
        context_parts = []
        
        # Add recent conversation history
        recent_history = self.get_conversation_context(recent_limit)
        if recent_history:
            context_parts.append("\n=== Recent Conversation ===")
            for i, interaction in enumerate(recent_history, 1):
                context_parts.append(f"Turn {i}:")
                context_parts.append(f"  User: {interaction['user']}")
                context_parts.append(f"  AI: {interaction['ai']}")
        
        # Add relevant learned patterns
        if include_patterns:
            relevant_patterns = self.get_learned_patterns()
            if relevant_patterns:
                context_parts.append("\n=== Learned Patterns ===")
                for name, data in list(relevant_patterns.items())[:3]:
                    context_parts.append(f"- {name}: {data.get('data', {}).get('description', 'N/A')}")
        
        # Add user preferences
        prefs = self.get_all_preferences()
        if prefs:
            context_parts.append("\n=== User Preferences ===")
            for key, value in list(prefs.items())[:3]:
                context_parts.append(f"- {key}: {value}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    # ─────────────────────────────────────────────────────────────────────────
    # File Operations
    # ─────────────────────────────────────────────────────────────────────────
    
    def _ensure_directories(self):
        """Ensure memory directories exist."""
        os.makedirs(MEMORY_DIR, exist_ok=True)
    
    def _load_json_file(self, filepath: str, default: Any = None) -> Any:
        """Load JSON file safely."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"{GRAY}[Memory] Error loading {filepath}: {e}{RESET}")
        
        return default if default is not None else {}
    
    def _save_json_file(self, filepath: str, data: Any) -> bool:
        """Save JSON file safely."""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"{GRAY}[Memory] Error saving {filepath}: {e}{RESET}")
            return False
    
    def _load_learned_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load learned patterns on init."""
        return self._load_json_file(LEARNED_PATTERNS, default={})
    
    def _load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences on init."""
        return self._load_json_file(USER_PREFERENCES, default={})
    
    # ─────────────────────────────────────────────────────────────────────────
    # Export/Analysis
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored memory."""
        try:
            reasoning_log = self._load_json_file(REASONING_LOG, default=[])
            interaction_history = self._load_json_file(INTERACTION_HISTORY, default=[])
            learned_patterns = self._load_json_file(LEARNED_PATTERNS, default={})
            user_preferences = self._load_json_file(USER_PREFERENCES, default={})
            
            return {
                "total_reasoning_logs": len(reasoning_log),
                "total_interactions": len(interaction_history),
                "learned_pattern_count": len(learned_patterns),
                "user_preferences_count": len(user_preferences),
                "session_id": self.current_session_id,
                "memory_dir_size": self._get_dir_size(MEMORY_DIR)
            }
        except Exception as e:
            print(f"{GRAY}[Memory] Error getting statistics: {e}{RESET}")
            return {}
    
    def _get_dir_size(self, path: str) -> str:
        """Get directory size in human-readable format."""
        try:
            total = sum(os.path.getsize(os.path.join(d, f)) for d, _, files in os.walk(path) for f in files)
            for unit in ['B', 'KB', 'MB']:
                if total < 1024:
                    return f"{total:.1f} {unit}"
                total /= 1024
            return f"{total:.1f} GB"
        except:
            return "Unknown"
    
    def export_memory(self, export_path: str) -> bool:
        """Export all memory data to a file."""
        try:
            export_data = {
                "session_id": self.current_session_id,
                "exported_at": datetime.now().isoformat(),
                "reasoning_log": self._load_json_file(REASONING_LOG, default=[]),
                "interaction_history": self._load_json_file(INTERACTION_HISTORY, default=[]),
                "learned_patterns": self._load_json_file(LEARNED_PATTERNS, default={}),
                "user_preferences": self._load_json_file(USER_PREFERENCES, default={})
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"{GREEN}[Memory] Exported to {export_path}{RESET}")
            return True
        
        except Exception as e:
            print(f"{GRAY}[Memory] Export failed: {e}{RESET}")
            return False


# Global instance
memory_manager = MemoryManager()
