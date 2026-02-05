import sqlite3
import uuid
import os
from datetime import datetime
from typing import List, Dict, Optional

class CalendarManager:
    """Manages calendar events using a local SQLite database."""
    
    def __init__(self, db_path: str = "data/calendar.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize the database and create table if not exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    category TEXT DEFAULT 'WORK',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            
    def get_events(self, date_str: str) -> List[Dict]:
        """
        Retrieve events for a specific date (YYYY-MM-DD).
        """
        try:
            # Create range for the entire day
            start_of_day = f"{date_str} 00:00:00"
            end_of_day = f"{date_str} 23:59:59"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM events 
                    WHERE start_time BETWEEN ? AND ? 
                    ORDER BY start_time ASC
                """, (start_of_day, end_of_day))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error loading events: {e}")
            return []

    def add_event(self, title: str, start_time: str, end_time: str, category: str = "WORK", description: str = "") -> Optional[Dict]:
        """
        Add a new event.
        Time format: 'YYYY-MM-DD HH:MM:SS'
        """
        event_id = str(uuid.uuid4())
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO events (id, title, start_time, end_time, category, description) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (event_id, title, start_time, end_time, category, description))
                conn.commit()
                
                return {
                    "id": event_id,
                    "title": title,
                    "start_time": start_time,
                    "end_time": end_time,
                    "category": category,
                    "description": description
                }
        except Exception as e:
            print(f"Error adding event: {e}")
            return None

    def delete_event(self, event_id: str):
        """Delete an event by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
                conn.commit()
        except Exception as e:
            print(f"Error deleting event: {e}")

# Global instance
calendar_manager = CalendarManager()
