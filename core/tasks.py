import sqlite3
import uuid
import os
from typing import List, Dict, Optional

class TaskManager:
    """Manages tasks using a local SQLite database."""
    
    def __init__(self, db_path: str = "data/tasks.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize the database and create table if not exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    completed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            
    def get_tasks(self) -> List[Dict]:
        """Retrieve all tasks ordered by creation time."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tasks ORDER BY created_at ASC")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error loading tasks: {e}")
            return []

    def add_task(self, text: str) -> Optional[Dict]:
        """Add a new task and return the task object."""
        task_id = str(uuid.uuid4())
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tasks (id, text, completed) VALUES (?, ?, ?)",
                    (task_id, text, False)
                )
                conn.commit()
                
                # return the new task
                return {
                    "id": task_id,
                    "text": text,
                    "completed": False,
                    "created_at": None # We don't need accurate timestamp immediately for UI
                }
        except Exception as e:
            print(f"Error adding task: {e}")
            return None

    def delete_task(self, task_id: str):
        """Delete a task by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
        except Exception as e:
            print(f"Error deleting task: {e}")

    def toggle_task(self, task_id: str, completed: bool):
        """Update task completion status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE tasks SET completed = ? WHERE id = ?",
                    (completed, task_id)
                )
                conn.commit()
        except Exception as e:
            print(f"Error toggling task: {e}")

    def add_alarm(self, time: str, label: str):
        """Add a new alarm."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Ensure table exists (lazy init for existing users)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alarms (
                        id TEXT PRIMARY KEY,
                        time TEXT NOT NULL,
                        label TEXT,
                        enabled BOOLEAN DEFAULT 1
                    )
                """)
                alarm_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO alarms (id, time, label) VALUES (?, ?, ?)",
                    (alarm_id, time, label)
                )
                conn.commit()
                return alarm_id
        except Exception as e:
            print(f"Error adding alarm: {e}")
            return None

    def get_alarms(self) -> List[Dict]:
        """Get all alarms."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alarms'")
                if not cursor.fetchone():
                    return []
                    
                cursor.execute("SELECT * FROM alarms ORDER BY time ASC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            return []

    def delete_alarm(self, alarm_id: str):
        """Delete an alarm."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))
                conn.commit()
        except Exception as e:
            print(f"Error deleting alarm: {e}")

# Global instance
task_manager = TaskManager()
