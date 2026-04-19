"""
Central database management for Wolf AI.
Handles persistence for chat sessions, messages, receptionist logs, and learned heuristics.
"""

import sqlite3
import uuid
import datetime
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Constants
DB_PATH = "data/wolf_core.db"

class WolfCoreDatabase:
    """Persistent storage engine for Wolf AI."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initializes the entire database schema for all application modules."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # ---------------------------------------------------------
            # TABLE 1: CHAT SESSIONS (For the Chat UI sidebar)
            # ---------------------------------------------------------
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT,
                updated_at TEXT,
                pinned INTEGER DEFAULT 0
            )''')
            
            # ---------------------------------------------------------
            # TABLE 2: CHAT MESSAGES (The actual LLM conversations)
            # ---------------------------------------------------------
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            )''')
            
            # ---------------------------------------------------------
            # TABLE 3: RECEPTIONIST LOGS (Phone integration logs)
            # ---------------------------------------------------------
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caller_id TEXT,
                status TEXT,
                intent_executed TEXT,
                transcript TEXT,
                sentiment_score INTEGER,
                client_mood TEXT,
                estimated_deal_size REAL DEFAULT 0.0,
                document_path TEXT,
                timestamp TEXT
            )''')
            
            # Action Logs
            conn.execute('''CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_name TEXT,
                status TEXT,
                details TEXT,
                timestamp TEXT
            )''')

            # Learned Heuristics (Synaptic Layer)
            conn.execute('''CREATE TABLE IF NOT EXISTS learned_heuristics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT UNIQUE,
                learned_plan TEXT,
                success_count INTEGER DEFAULT 0,
                timestamp TEXT
            )''')
            
            # ---------------------------------------------------------
            # TABLE 4: ACTION TASKS (Trello/Notion Inbox)
            # ---------------------------------------------------------
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                priority TEXT,
                status TEXT DEFAULT 'pending',
                related_call_id INTEGER,
                created_at TEXT,
                FOREIGN KEY(related_call_id) REFERENCES call_logs(id) ON DELETE SET NULL
            )''')
            
            # ---------------------------------------------------------
            # TABLE 4: BUG WATCHER INCIDENTS (Proactive layer screen crashes)
            # ---------------------------------------------------------
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS bug_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_type TEXT,
                detected_text TEXT,
                timestamp TEXT
            )''')

            conn.commit()
        finally:
            conn.close()

    # =========================================================================
    # CHAT HISTORY API
    # =========================================================================

    def create_session(self, title: str = "New Chat") -> str:
        session_id = str(uuid.uuid4())
        now = datetime.datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO chat_sessions (id, title, created_at, updated_at, pinned) VALUES (?, ?, ?, ?, ?)',
                (session_id, title, now, now, 0)
            )
            conn.commit()
        return session_id

    def update_session_title(self, session_id: str, title: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?',
                (title, datetime.datetime.now().isoformat(), session_id)
            )
            conn.commit()

    def delete_session(self, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            # Foreign key cascade handles messages
            conn.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
            conn.commit()

    def get_sessions(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM chat_sessions ORDER BY pinned DESC, updated_at DESC')
            return [dict(row) for row in cursor.fetchall()]

    def save_message(self, session_id: str, role: str, content: str):
        now = datetime.datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO chat_messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
                (session_id, role, content, now)
            )
            # Update parent session's update time
            conn.execute('UPDATE chat_sessions SET updated_at = ? WHERE id = ?', (now, session_id))
            conn.commit()

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT role, content, timestamp FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC', (session_id,))
            return [dict(row) for row in cursor.fetchall()]


    # =========================================================================
    # RECEPTIONIST & AUDIT LOGS
    # =========================================================================

    def log_call(self, caller_id: str, status: str, transcript: str = "", intent: str = "", mood: str = "Neutral", sentiment: int = 5) -> int:
        now = datetime.datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO call_logs (caller_id, status, transcript, intent_executed, client_mood, sentiment_score, timestamp) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (caller_id, status, transcript, intent, mood, sentiment, now)
            )
            conn.commit()
            return cursor.lastrowid

    def add_task(self, title: str, description: str, priority: str = "Medium", related_call_id: int = None):
        now = datetime.datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO tasks (title, description, priority, related_call_id, created_at) VALUES (?, ?, ?, ?, ?)',
                (title, description, priority, related_call_id, now)
            )
            conn.commit()

    def log_action_step(self, action_name: str, status: str, details: str = ""):
        """Audit trail for system actions (opening apps, file ops, etc)."""
        now = datetime.datetime.now().isoformat(timespec="seconds")
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'INSERT INTO action_logs (action_name, status, details, timestamp) VALUES (?, ?, ?, ?)',
                    (action_name, status, details, now)
                )
                conn.commit()
        except Exception as e:
            print(f"[Database] Failed to log action: {e}")

    def save_experience(self, query: str, plan: List[Dict[str, Any]]):
        """Save a learned correction workflow for a specific query."""
        now = datetime.datetime.now().isoformat(timespec="seconds")
        plan_json = json.dumps(plan)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    '''INSERT OR REPLACE INTO learned_heuristics (query, learned_plan, timestamp) 
                       VALUES (?, ?, ?)''',
                    (query.lower().strip(), plan_json, now)
                )
                conn.commit()
                print(f"[Database] OK: Learned new heuristic for: '{query}'")
        except Exception as e:
            print(f"[Database] Failed to save experience: {e}")

    def get_learned_heuristic(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Check if we have a learned approaching for this query."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # Simple exact match for now - could be fuzzy later
                cursor.execute('SELECT learned_plan FROM learned_heuristics WHERE query = ?', (query.lower().strip(),))
                row = cursor.fetchone()
                if row:
                    return json.loads(row['learned_plan'])
            return None
        except Exception as e:
            print(f"[Database] Error retrieving heuristic: {e}")
            return None

    def increment_heuristic_success(self, query: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'UPDATE learned_heuristics SET success_count = success_count + 1 WHERE query = ?',
                    (query.lower().strip(),)
                )
                conn.commit()
        except Exception as e:
            print(f"[Database] Failed to increment success: {e}")


# Global database instance
db = WolfCoreDatabase()
