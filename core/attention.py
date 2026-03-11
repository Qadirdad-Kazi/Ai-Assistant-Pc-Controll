"""
Attention Manager System
Simulates human-like attention span, task focus, and working memory limitations.
Prevents the AI from being context-overloaded by limiting concurrent tasks and detecting distractions.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Task:
    """Represents a task with focus duration and importance."""
    task_id: str
    description: str
    priority: int  # 1-10, higher = more important
    created_at: datetime
    last_accessed: datetime
    focus_duration_seconds: int = 0
    completed: bool = False
    importance_decay: float = 1.0  # Decreases over time


class WorkingMemoryBuffer:
    """Simulates limited working memory - can only hold ~7±2 items."""
    
    MAX_CAPACITY = 7
    DECAY_FACTOR = 0.95  # Memory items decay value over time
    
    def __init__(self):
        self.buffer: List[Dict] = []
        self.access_history: List[Tuple[str, datetime]] = []
    
    def add_to_memory(self, item: Dict, priority: int = 5) -> bool:
        """Add item to working memory. Returns True if added, False if buffer full."""
        if len(self.buffer) >= self.MAX_CAPACITY:
            # Remove lowest priority item
            if self.buffer:
                self.buffer.sort(key=lambda x: x.get('priority', 0))
                self.buffer.pop(0)
        
        item['priority'] = priority
        item['added_at'] = datetime.now().isoformat()
        self.buffer.append(item)
        self.access_history.append((item.get('id', 'unknown'), datetime.now()))
        return True
    
    def get_working_memory(self) -> List[Dict]:
        """Get current working memory items, sorted by recency & importance."""
        now = datetime.now()
        for item in self.buffer:
            age = (now - datetime.fromisoformat(item['added_at'])).total_seconds()
            # Decay priority over time (older items less important)
            item['current_priority'] = item.get('priority', 5) * (self.DECAY_FACTOR ** (age / 3600))
        
        return sorted(self.buffer, key=lambda x: x.get('current_priority', 0), reverse=True)
    
    def clear_old_items(self, max_age_minutes: int = 30):
        """Remove items older than max_age_minutes."""
        now = datetime.now()
        self.buffer = [
            item for item in self.buffer
            if (now - datetime.fromisoformat(item['added_at'])).total_seconds() < max_age_minutes * 60
        ]
    
    def forget_least_important(self):
        """Simulate forgetting least important item when overwhelmed."""
        if self.buffer:
            self.buffer.sort(key=lambda x: x.get('priority', 0))
            forgotten = self.buffer.pop(0)
            return forgotten
        return None


class TaskFocusManager:
    """Manages primary task focus and attention allocation."""
    
    FOCUS_TIMEOUT_SECONDS = 600  # 10 minutes default focus window
    CONTEXT_SWITCH_COST = 0.1  # 10% efficiency loss per context switch
    
    def __init__(self):
        self.active_task: Optional[Task] = None
        self.secondary_tasks: List[Task] = []
        self.task_history: List[Task] = []
        self.total_context_switches = 0
        self.efficiency_score = 1.0  # Decreases with context switching
    
    def set_focus_task(self, task_id: str, description: str, priority: int = 5) -> Task:
        """Set the primary task for focus."""
        now = datetime.now()
        
        # If there's an active task, move it to secondary
        if self.active_task:
            self.active_task.last_accessed = now
            self.secondary_tasks.append(self.active_task)
            self.total_context_switches += 1
            self.efficiency_score *= (1 - self.CONTEXT_SWITCH_COST)
        
        task = Task(
            task_id=task_id,
            description=description,
            priority=priority,
            created_at=now,
            last_accessed=now
        )
        self.active_task = task
        return task
    
    def get_active_task(self) -> Optional[Task]:
        """Get the current primary task."""
        if self.active_task:
            self.active_task.last_accessed = datetime.now()
        return self.active_task
    
    def get_secondary_tasks(self) -> List[Task]:
        """Get secondary tasks (context not fully loaded)."""
        return self.secondary_tasks[:3]  # Limited to 3 secondary tasks
    
    def complete_task(self) -> Optional[Task]:
        """Mark active task as complete and move to history."""
        if self.active_task:
            self.active_task.completed = True
            self.task_history.append(self.active_task)
            
            # Switch to secondary task if available
            if self.secondary_tasks:
                self.active_task = self.secondary_tasks.pop(0)
            else:
                self.active_task = None
            
            return self.task_history[-1]
        return None
    
    def is_task_focus_timeout(self) -> bool:
        """Check if current task focus has timed out."""
        if not self.active_task:
            return False
        
        elapsed = (datetime.now() - self.active_task.last_accessed).total_seconds()
        return elapsed > self.FOCUS_TIMEOUT_SECONDS
    
    def get_efficiency_score(self) -> float:
        """Get current efficiency based on context switches."""
        return self.efficiency_score


class DistractionDetector:
    """Detects when AI is getting distracted or context-overloaded."""
    
    # Patterns that indicate distraction
    DISTRACTION_KEYWORDS = [
        'also', 'by the way', 'speaking of', 'unrelated', 'anyway',
        'just thought of', 'tangent', 'different topic', 'change subject'
    ]
    
    OVERLOAD_INDICATORS = {
        'too_many_tasks': 5,  # More than 5 simultaneous task requests
        'rapid_switching': 3,  # More than 3 switches in 60 seconds
        'memory_pressure': 8,  # Working memory at 8+ items
        'long_query': 500,  # Query longer than 500 chars
    }
    
    def __init__(self):
        self.distraction_level = 0.0  # 0.0 = focused, 1.0 = completely distracted
        self.recent_topics: List[str] = []
        self.topic_switch_times: List[datetime] = []
    
    def detect_distraction_keywords(self, text: str) -> float:
        """Detect distraction keywords in text. Returns distraction score 0-1."""
        score = 0.0
        text_lower = text.lower()
        
        for keyword in self.DISTRACTION_KEYWORDS:
            if keyword in text_lower:
                score += 0.15
        
        return min(score, 1.0)
    
    def assess_context_overload(self, 
                                 active_tasks: int,
                                 recent_switches: int,
                                 working_memory_size: int,
                                 current_query_length: int) -> float:
        """Assess overall context overload. Returns score 0-1."""
        overload_score = 0.0
        
        # Task load
        if active_tasks > self.OVERLOAD_INDICATORS['too_many_tasks']:
            overload_score += 0.3
        else:
            overload_score += (active_tasks / self.OVERLOAD_INDICATORS['too_many_tasks']) * 0.3
        
        # Context switching speed
        if recent_switches > self.OVERLOAD_INDICATORS['rapid_switching']:
            overload_score += 0.3
        else:
            overload_score += (recent_switches / self.OVERLOAD_INDICATORS['rapid_switching']) * 0.3
        
        # Working memory pressure
        if working_memory_size > self.OVERLOAD_INDICATORS['memory_pressure']:
            overload_score += 0.2
        else:
            overload_score += (working_memory_size / self.OVERLOAD_INDICATORS['memory_pressure']) * 0.2
        
        # Query complexity
        if current_query_length > self.OVERLOAD_INDICATORS['long_query']:
            overload_score += 0.2
        else:
            overload_score += (current_query_length / self.OVERLOAD_INDICATORS['long_query']) * 0.2
        
        return min(overload_score, 1.0)
    
    def update_distraction_level(self, 
                                  keyword_score: float,
                                  overload_score: float) -> float:
        """Update overall distraction level."""
        self.distraction_level = (keyword_score * 0.3) + (overload_score * 0.7)
        return self.distraction_level
    
    def get_distraction_assessment(self) -> Dict[str, any]:
        """Get comprehensive distraction assessment."""
        return {
            'distraction_level': self.distraction_level,
            'is_focused': self.distraction_level < 0.3,
            'is_moderately_distracted': 0.3 <= self.distraction_level < 0.7,
            'is_overwhelmed': self.distraction_level >= 0.7,
            'recommendation': self._get_recommendation()
        }
    
    def _get_recommendation(self) -> str:
        """Get recommendation based on distraction level."""
        if self.distraction_level < 0.3:
            return "Focused - can handle complex tasks"
        elif self.distraction_level < 0.7:
            return "Moderately distracted - should focus on main task"
        else:
            return "Overwhelmed - should simplify current task or take a break"


class ContextSwitcher:
    """Manages attention transitions between different contexts/tasks."""
    
    REORIENT_TIME_SECONDS = 3  # Time to re-orient to new context
    
    def __init__(self):
        self.last_context: Optional[str] = None
        self.current_context: Optional[str] = None
        self.context_history: List[Tuple[str, datetime]] = []
        self.reorientation_needed = False
    
    def switch_context(self, new_context: str) -> Dict:
        """Switch attention to a new context."""
        now = datetime.now()
        
        if self.current_context:
            self.last_context = self.current_context
            self.context_history.append((self.current_context, now))
            self.reorientation_needed = True
        
        self.current_context = new_context
        return {
            'switched_from': self.last_context,
            'switched_to': new_context,
            'reorientation_needed': self.reorientation_needed,
            'reorient_time_seconds': self.REORIENT_TIME_SECONDS if self.reorientation_needed else 0
        }
    
    def get_context_recovery_prompt(self) -> str:
        """Get prompt text to help recover context."""
        if not self.last_context:
            return "Starting fresh context."
        
        return f"Switching context from: {self.last_context}. Please re-orient to current task."
    
    def context_reoriented(self):
        """Signal that reorientation is complete."""
        self.reorientation_needed = False


class AttentionManager:
    """Main attention management system - coordinates all attention components."""
    
    def __init__(self):
        self.focus_manager = TaskFocusManager()
        self.working_memory = WorkingMemoryBuffer()
        self.distraction_detector = DistractionDetector()
        self.context_switcher = ContextSwitcher()
        self.stats = {
            'total_queries': 0,
            'total_context_switches': 0,
            'avg_distraction_level': 0.0,
            'total_tasks_completed': 0
        }
    
    def process_query(self, query: str, task_id: str = None, task_priority: int = 5) -> Dict:
        """Process query through attention system."""
        self.stats['total_queries'] += 1
        
        # Detect distractions
        keyword_distraction = self.distraction_detector.detect_distraction_keywords(query)
        
        # Assess current overload
        overload = self.distraction_detector.assess_context_overload(
            active_tasks=len(self.focus_manager.secondary_tasks) + (1 if self.focus_manager.active_task else 0),
            recent_switches=self.focus_manager.total_context_switches % 10,  # Last 10 switches
            working_memory_size=len(self.working_memory.buffer),
            current_query_length=len(query)
        )
        
        distraction_level = self.distraction_detector.update_distraction_level(
            keyword_distraction, overload
        )
        
        # Handle if overwhelmed
        if distraction_level >= 0.7:
            self.working_memory.forget_least_important()
        
        # Set or update focus task
        if task_id:
            self.focus_manager.set_focus_task(task_id, query[:50], task_priority)
        
        # Add query context to working memory
        self.working_memory.add_to_memory({
            'id': task_id or f'query_{self.stats["total_queries"]}',
            'content': query[:100],
            'priority': task_priority
        })
        
        return {
            'can_process': distraction_level < 0.8,  # Can process unless overwhelmed
            'distraction_level': distraction_level,
            'distraction_assessment': self.distraction_detector.get_distraction_assessment(),
            'active_task': self.focus_manager.active_task.task_id if self.focus_manager.active_task else None,
            'efficiency_score': self.focus_manager.get_efficiency_score(),
            'working_memory_items': len(self.working_memory.buffer),
            'recommendation': self.distraction_detector.get_distraction_assessment()['recommendation']
        }
    
    def get_attention_state(self) -> Dict:
        """Get comprehensive attention state."""
        return {
            'active_task': (
                {
                    'id': self.focus_manager.active_task.task_id,
                    'description': self.focus_manager.active_task.description,
                    'priority': self.focus_manager.active_task.priority
                } if self.focus_manager.active_task else None
            ),
            'secondary_tasks_count': len(self.focus_manager.secondary_tasks),
            'working_memory_items': self.working_memory.get_working_memory(),
            'distraction_level': self.distraction_detector.distraction_level,
            'efficiency_score': self.focus_manager.get_efficiency_score(),
            'context_switches': self.focus_manager.total_context_switches,
            'stats': self.stats
        }
    
    def complete_current_task(self) -> Optional[Dict]:
        """Complete the current task and move to next."""
        completed = self.focus_manager.complete_task()
        if completed:
            self.stats['total_tasks_completed'] += 1
        return asdict(completed) if completed else None
    
    def should_take_break(self) -> Tuple[bool, str]:
        """Determine if AI should suggest a break."""
        if self.focus_manager.is_task_focus_timeout():
            return True, "Primary task focus timeout reached - suggest break"
        
        if self.distraction_detector.distraction_level >= 0.8:
            return True, "Attention severely overloaded - need break"
        
        if len(self.working_memory.buffer) >= 7:
            return True, "Working memory saturated - need reset"
        
        return False, ""


# Global instance
attention_manager = AttentionManager()
