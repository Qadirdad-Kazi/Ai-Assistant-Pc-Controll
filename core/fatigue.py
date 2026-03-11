"""
Energy & Fatigue System
Simulates human-like energy depletion and recovery.
Performance degrades as energy decreases. System suggests breaks when fatigued.
"""

import json
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class EnergyMetrics:
    """Tracks energy-related metrics."""
    current_energy: float = 100.0  # 0-100
    max_energy: float = 100.0
    energy_threshold_warning = 30.0  # Below this, warn user
    energy_threshold_critical = 10.0  # Below this, refuse complex tasks
    operations_completed = 0
    break_duration_seconds = 0
    last_break_time: Optional[datetime] = None
    peak_usage_time: Optional[datetime] = None
    total_fatigue_time_seconds = 0.0


class EnergyConsumption:
    """Defines energy costs for different operation types."""
    
    # Base energy costs for operations (per unit/iteration)
    ENERGY_COSTS = {
        'simple_query': 2.0,  # Simple Q&A
        'reasoning_step': 5.0,  # Each reasoning step
        'model_switching': 3.0,  # Selecting different model
        'multi_step_task': 8.0,  # Complex task sequence
        'function_execution': 4.0,  # External function call
        'creative_task': 10.0,  # Brainstorming, creation
        'decision_making': 7.0,  # Complex decision
        'complex_analysis': 12.0,  # Deep analysis
        'learning_update': 6.0,  # Learning pattern
    }
    
    # Modifiers based on difficulty/complexity
    COMPLEXITY_MULTIPLIER = {
        'trivial': 0.3,
        'simple': 0.6,
        'moderate': 1.0,
        'complex': 1.5,
        'very_complex': 2.0,
        'extreme': 3.0
    }
    
    @staticmethod
    def get_cost(operation_type: str, complexity: str = 'moderate') -> float:
        """Calculate energy cost for an operation."""
        base_cost = EnergyConsumption.ENERGY_COSTS.get(operation_type, 5.0)
        multiplier = EnergyConsumption.COMPLEXITY_MULTIPLIER.get(complexity, 1.0)
        return base_cost * multiplier


class FatigueEffects:
    """Describes performance degradation effects based on energy level."""
    
    @staticmethod
    def get_performance_degradation(energy_level: float) -> Dict:
        """Get performance degradation based on energy level."""
        
        if energy_level > 70:
            return {
                'level': 'optimal',
                'response_speed_multiplier': 1.0,
                'quality_bonus': 1.0,
                'error_rate': 0.02,
                'can_do_complex_tasks': True,
                'description': 'Fresh and energized - operating at peak performance'
            }
        
        elif energy_level > 50:
            return {
                'level': 'normal',
                'response_speed_multiplier': 0.95,
                'quality_bonus': 0.95,
                'error_rate': 0.04,
                'can_do_complex_tasks': True,
                'description': 'Normal operations - functioning well'
            }
        
        elif energy_level > 30:
            return {
                'level': 'fatigued',
                'response_speed_multiplier': 0.85,
                'quality_bonus': 0.85,
                'error_rate': 0.08,
                'can_do_complex_tasks': True,
                'description': 'Starting to feel fatigued - performance declining'
            }
        
        elif energy_level > 15:
            return {
                'level': 'very_fatigued',
                'response_speed_multiplier': 0.70,
                'quality_bonus': 0.70,
                'error_rate': 0.15,
                'can_do_complex_tasks': False,
                'description': 'Very tired - should consider taking a break'
            }
        
        elif energy_level > 5:
            return {
                'level': 'critical',
                'response_speed_multiplier': 0.50,
                'quality_bonus': 0.50,
                'error_rate': 0.25,
                'can_do_complex_tasks': False,
                'description': 'Critical fatigue - needs immediate break'
            }
        
        else:  # 0-5
            return {
                'level': 'burnout',
                'response_speed_multiplier': 0.0,
                'quality_bonus': 0.0,
                'error_rate': 1.0,
                'can_do_complex_tasks': False,
                'description': 'Complete burnout - must take break'
            }
    
    @staticmethod
    def apply_fatigue_to_response_quality(base_quality: float, energy_level: float) -> float:
        """Apply fatigue modifier to response quality score."""
        degradation = FatigueEffects.get_performance_degradation(energy_level)
        return base_quality * degradation['quality_bonus']
    
    @staticmethod
    def get_fatigue_warning_message(energy_level: float) -> Optional[str]:
        """Get warning message based on energy level."""
        
        if energy_level > 30:
            return None  # No warning
        
        elif energy_level > 15:
            return f"Energy level at {energy_level:.1f}%. You may want to consider taking a break soon."
        
        elif energy_level > 5:
            return f"⚠️ CRITICAL: Energy at only {energy_level:.1f}%. Please take a break - I need to rest!"
        
        else:
            return f"🔴 BURNOUT: Energy exhausted ({energy_level:.1f}%). Refusing further complex tasks. MUST REST NOW."


class RecoveryManager:
    """Manages energy recovery and break mechanics."""
    
    # Recovery rates (energy per second during break)
    RECOVERY_RATES = {
        'micro_break': 0.5,  # 10-30 second break
        'short_break': 2.0,  # 5-15 minute break
        'long_break': 5.0,  # 30+ minute break
        'full_reset': 100.0,  # Instant reset (game mechanic)
    }
    
    # Required break duration for full recovery
    BREAK_TIMES = {
        'micro_break': 30,  # seconds
        'short_break': 300,  # seconds (5 min)
        'long_break': 1800,  # seconds (30 min)
    }
    
    def __init__(self):
        self.break_start_time: Optional[datetime] = None
        self.break_type: Optional[str] = None
        self.breaks_taken = 0
        self.total_break_duration_seconds = 0.0
        self.recovery_history = []
    
    def start_break(self, break_type: str = 'short_break') -> Dict:
        """Start a break session."""
        self.break_start_time = datetime.now()
        self.break_type = break_type
        self.breaks_taken += 1
        
        return {
            'break_started': True,
            'break_type': break_type,
            'expected_duration_seconds': self.BREAK_TIMES.get(break_type, 60),
            'message': f"Taking a {break_type}. Recovery rate: {self.RECOVERY_RATES[break_type]} energy/sec"
        }
    
    def end_break(self) -> Tuple[float, float]:
        """End break and calculate recovered energy."""
        if not self.break_start_time:
            return 0.0, 0.0
        
        duration = (datetime.now() - self.break_start_time).total_seconds()
        recovery_rate = self.RECOVERY_RATES.get(self.break_type, 1.0)
        recovered_energy = duration * recovery_rate
        
        self.total_break_duration_seconds += duration
        self.recovery_history.append({
            'timestamp': datetime.now().isoformat(),
            'break_type': self.break_type,
            'duration_seconds': duration,
            'energy_recovered': recovered_energy
        })
        
        self.break_start_time = None
        self.break_type = None
        
        return recovered_energy, duration
    
    def is_on_break(self) -> bool:
        """Check if currently on break."""
        return self.break_start_time is not None
    
    def get_recovery_stats(self) -> Dict:
        """Get recovery statistics."""
        total_recovered = sum(h['energy_recovered'] for h in self.recovery_history)
        avg_break_duration = (
            sum(h['duration_seconds'] for h in self.recovery_history) / len(self.recovery_history)
            if self.recovery_history else 0
        )
        
        return {
            'breaks_taken': self.breaks_taken,
            'total_break_duration_seconds': self.total_break_duration_seconds,
            'total_energy_recovered': total_recovered,
            'avg_break_duration_seconds': avg_break_duration,
            'most_common_break': self._get_most_common_break()
        }
    
    def _get_most_common_break(self) -> str:
        """Get most commonly used break type."""
        if not self.recovery_history:
            return 'none'
        
        break_types = {}
        for h in self.recovery_history:
            break_type = h['break_type']
            break_types[break_type] = break_types.get(break_type, 0) + 1
        
        return max(break_types.items(), key=lambda x: x[1])[0]


class EnergyManager:
    """Main energy management system."""
    
    def __init__(self):
        self.metrics = EnergyMetrics()
        self.recovery_manager = RecoveryManager()
        self.operation_log = []
    
    def consume_energy(self, operation_type: str, complexity: str = 'moderate') -> float:
        """Consume energy for an operation."""
        cost = EnergyConsumption.get_cost(operation_type, complexity)
        self.metrics.current_energy = max(0, self.metrics.current_energy - cost)
        
        self.operation_log.append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation_type,
            'complexity': complexity,
            'energy_cost': cost,
            'energy_after': self.metrics.current_energy
        })
        
        self.metrics.operations_completed += 1
        
        if self.metrics.current_energy == 0:
            self.trigger_fatigue_mode()
        
        return cost
    
    def trigger_fatigue_mode(self):
        """Trigger fatigue mode when energy depleted."""
        self.metrics.last_break_time = datetime.now()
        self.metrics.peak_usage_time = datetime.now()
    
    def recover_energy(self, break_type: str = 'short_break'):
        """Recover energy during break."""
        self.recovery_manager.start_break(break_type)
        recovered, duration = self.recovery_manager.end_break()
        
        self.metrics.current_energy = min(
            self.metrics.max_energy,
            self.metrics.current_energy + recovered
        )
        
        self.metrics.break_duration_seconds = duration
        return recovered
    
    def get_energy_status(self) -> Dict:
        """Get comprehensive energy status."""
        degradation = FatigueEffects.get_performance_degradation(self.metrics.current_energy)
        warning = FatigueEffects.get_fatigue_warning_message(self.metrics.current_energy)
        
        return {
            'current_energy': self.metrics.current_energy,
            'energy_percentage': (self.metrics.current_energy / self.metrics.max_energy) * 100,
            'degradation_level': degradation['level'],
            'response_speed_multiplier': degradation['response_speed_multiplier'],
            'quality_multiplier': degradation['quality_bonus'],
            'error_rate': degradation['error_rate'],
            'can_do_complex_tasks': degradation['can_do_complex_tasks'],
            'degradation_description': degradation['description'],
            'warning_message': warning,
            'operations_completed': self.metrics.operations_completed,
            'should_take_break': self.metrics.current_energy < self.metrics.energy_threshold_warning
        }
    
    def should_refuse_complex_task(self) -> Tuple[bool, Optional[str]]:
        """Check if should refuse complex task due to fatigue."""
        if self.metrics.current_energy > 30:
            return False, None
        
        if self.metrics.current_energy <= 5:
            return True, f"System burnout ({self.metrics.current_energy:.1f}% energy). Refusing all tasks. MUST REST."
        
        if self.metrics.current_energy <= 15:
            return True, f"Critical fatigue ({self.metrics.current_energy:.1f}% energy). Complex tasks refused. Simple tasks only."
        
        if self.metrics.current_energy <= 30:
            return True, f"Fatigued ({self.metrics.current_energy:.1f}% energy). Complex multistep tasks refused. Single-action tasks only."
        
        return False, None
    
    def get_estimated_break_needed(self) -> Optional[str]:
        """Get recommendation for break type needed."""
        if self.metrics.current_energy > 50:
            return None
        
        elif self.metrics.current_energy > 30:
            return f"Micro break recommended (30 sec) to recover 15 energy"
        
        elif self.metrics.current_energy > 15:
            return f"Short break recommended (5 min) to recover 600 energy + fatigue relief"
        
        else:
            return f"LONG BREAK REQUIRED (30 min) to fully recover. Current energy too low for meaningful operations."
    
    def get_performance_report(self) -> Dict:
        """Get detailed performance report including fatigue effects."""
        return {
            'energy_metrics': {
                'current': self.metrics.current_energy,
                'max': self.metrics.max_energy,
                'percentage': (self.metrics.current_energy / self.metrics.max_energy) * 100
            },
            'performance': FatigueEffects.get_performance_degradation(self.metrics.current_energy),
            'operations': self.metrics.operations_completed,
            'recovery': self.recovery_manager.get_recovery_stats(),
            'warnings': {
                'warning_threshold': self.metrics.energy_threshold_warning,
                'critical_threshold': self.metrics.energy_threshold_critical,
                'current_warning': FatigueEffects.get_fatigue_warning_message(self.metrics.current_energy)
            }
        }
    
    def simulate_work_session(self, duration_minutes: int = 60) -> Dict:
        """Simulate an extended work session to show fatigue progression."""
        initial_energy = self.metrics.current_energy
        session_log = []
        
        # Simulate operations every 2 minutes
        operations_in_session = int(duration_minutes / 2)
        for op in range(operations_in_session):
            # Randomly select operation type and complexity
            op_type = 'reasoning_step' if op % 3 == 0 else 'simple_query'
            complexity = 'moderate' if op % 4 < 2 else 'complex'
            
            self.consume_energy(op_type, complexity)
            session_log.append({
                'operation': op,
                'time_minutes': op * 2,
                'energy_remaining': self.metrics.current_energy,
                'status': FatigueEffects.get_performance_degradation(self.metrics.current_energy)['level']
            })
        
        return {
            'session_duration_minutes': duration_minutes,
            'initial_energy': initial_energy,
            'final_energy': self.metrics.current_energy,
            'energy_consumed': initial_energy - self.metrics.current_energy,
            'operations_performed': operations_in_session,
            'session_timeline': session_log,
            'final_status': FatigueEffects.get_performance_degradation(self.metrics.current_energy)['level']
        }
    
    def reset_energy(self):
        """Reset energy to max (full rest)."""
        self.metrics.current_energy = self.metrics.max_energy
        self.recovery_manager.start_break('full_reset')
        self.recovery_manager.end_break()


# Global instance
energy_manager = EnergyManager()
