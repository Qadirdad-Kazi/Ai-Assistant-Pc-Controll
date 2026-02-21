"""
The central unified database for Wolf AI 2.0.
Managed via SQLite for zero-configuration persistence.
Creates a single 'wolf_core.db' file in the data/ directory.
"""

import sqlite3
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_DIR = "data"
DB_PATH = f"{DB_DIR}/wolf_core.db"

class WolfCoreDatabase:
    """Master manager for all application data storage."""

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
                timestamp TEXT
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

    def toggle_pin(self, session_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT pinned FROM chat_sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            new_pinned = 0 if (row and row[0]) else 1
            cursor.execute('UPDATE chat_sessions SET pinned = ? WHERE id = ?', (new_pinned, session_id))
            conn.commit()
            return bool(new_pinned)

    def add_message(self, session_id: str, role: str, content: str):
        now = datetime.datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO chat_messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
                (session_id, role, content, now)
            )
            conn.execute(
                'UPDATE chat_sessions SET updated_at = ? WHERE id = ?',
                (now, session_id)
            )
            conn.commit()

    def get_sessions(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, title, created_at, pinned FROM chat_sessions ORDER BY pinned DESC, updated_at DESC')
            return [{'id': row[0], 'title': row[1], 'created_at': row[2], 'pinned': bool(row[3])} for row in cursor.fetchall()]

    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY id ASC', (session_id,))
            return [{'role': row[0], 'content': row[1]} for row in cursor.fetchall()]

    def delete_session(self, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            # PRAGMA foreign_keys = ON; will auto-delete messages if standard sqlite is configured, 
            # but to be safe we explicitly delete messages first
            conn.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_id,))
            conn.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
            conn.commit()

    # =========================================================================
    # RECEPTIONIST CALL LOGS API
    # =========================================================================

    def log_call(self, caller_id: str, status: str, intent: str, transcript: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO call_logs (caller_id, status, intent_executed, transcript, timestamp) VALUES (?, ?, ?, ?, ?)',
                (caller_id, status, intent, transcript, datetime.datetime.now().isoformat())
            )
            conn.commit()

    def get_call_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT caller_id, status, intent_executed, transcript, timestamp FROM call_logs ORDER BY id DESC LIMIT ?', (limit,))
            return [{
                "caller": row[0], 
                "status": row[1], 
                "instructions": row[2], 
                "transcript": row[3], 
                "timestamp": row[4]
            } for row in cursor.fetchall()]

    # =========================================================================
    # BUG WATCHER API
    # =========================================================================

    def log_bug(self, error_type: str, context: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO bug_reports (error_type, detected_text, timestamp) VALUES (?, ?, ?)',
                (error_type, context, datetime.datetime.now().isoformat())
            )
            conn.commit()

# Expose a global connection instance for the entire app
db = WolfCoreDatabase()
