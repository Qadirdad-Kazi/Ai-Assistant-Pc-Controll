import os
import json
from PySide6.QtCore import QObject, Signal

class GamificationManager(QObject):
    """
    Gamification Manager: Handles XP, Levels, and Rewards.
    """
    stats_updated = Signal(dict) # xp, level, xp_to_next
    level_up = Signal(int) # new level
    
    def __init__(self, stats_file="data/user_stats.json"):
        super().__init__()
        self.stats_file = stats_file
        self.stats = self._load_stats()

    def _load_stats(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r") as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "xp": 0,
            "level": 1,
            "total_tasks_done": 0,
            "total_messages_sent": 0
        }

    def _save_stats(self):
        with open(self.stats_file, "w") as f:
            json.dump(self.stats, f, indent=4)
        
        # Calculate next level info
        # Formula: XP for level N = 100 * (N^1.5)
        next_xp = int(100 * ((self.stats["level"] + 1)**1.5))
        current_xp = self.stats["xp"]
        
        self.stats_updated.emit({
            "xp": current_xp,
            "level": self.stats["level"],
            "xp_to_next": next_xp,
            "progress": (current_xp / next_xp) * 100 if next_xp > 0 else 0
        })

    def add_xp(self, amount):
        self.stats["xp"] += amount
        print(f"[Leveling] +{amount} XP")
        
        # Check level up
        while True:
            next_xp = int(100 * ((self.stats["level"] + 1)**1.5))
            if self.stats["xp"] >= next_xp:
                self.stats["level"] += 1
                self.level_up.emit(self.stats["level"])
                print(f"[Leveling] LEVEL UP! Now Level {self.stats['level']}")
            else:
                break
        
        self._save_stats()

    def task_completed(self):
        self.stats["total_tasks_done"] += 1
        self.add_xp(50) # reward for productivity

    def message_sent(self):
        self.stats["total_messages_sent"] += 1
        self.add_xp(5) # small reward for interaction

# Global instance
game_manager = GamificationManager()
