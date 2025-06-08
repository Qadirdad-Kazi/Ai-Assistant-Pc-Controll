"""
Database Module
Handles data storage and retrieval for Wolf AI Assistant
"""

import sqlite3
import json
import os
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.config = Config()
        self.db_path = self.config.get('database_path', 'wolf_ai.db')
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create interactions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_input TEXT NOT NULL,
                        ai_response TEXT,
                        interaction_type TEXT DEFAULT 'conversation',
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        language TEXT DEFAULT 'en'
                    )
                ''')
                
                # Create settings table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create commands_log table for PC control commands
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS commands_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        command TEXT NOT NULL,
                        success BOOLEAN DEFAULT 0,
                        result TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create usage_stats table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS usage_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        feature TEXT NOT NULL,
                        count INTEGER DEFAULT 1,
                        last_used DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                print("Database initialized successfully")
                
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")

    def log_interaction(self, user_input, ai_response, interaction_type='conversation', language='en'):
        """Log user interactions with the AI"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO interactions (user_input, ai_response, interaction_type, language)
                    VALUES (?, ?, ?, ?)
                ''', (user_input, ai_response, interaction_type, language))
                conn.commit()
                
                # Update usage stats
                self.update_usage_stats(interaction_type)
                
        except sqlite3.Error as e:
            print(f"Error logging interaction: {e}")

    def log_command(self, command, success, result):
        """Log PC control commands"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO commands_log (command, success, result)
                    VALUES (?, ?, ?)
                ''', (command, success, result))
                conn.commit()
                
                # Update usage stats
                self.update_usage_stats('pc_control')
                
        except sqlite3.Error as e:
            print(f"Error logging command: {e}")

    def update_usage_stats(self, feature):
        """Update usage statistics for features"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if feature exists
                cursor.execute('SELECT count FROM usage_stats WHERE feature = ?', (feature,))
                result = cursor.fetchone()
                
                if result:
                    # Update existing record
                    cursor.execute('''
                        UPDATE usage_stats 
                        SET count = count + 1, last_used = CURRENT_TIMESTAMP 
                        WHERE feature = ?
                    ''', (feature,))
                else:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO usage_stats (feature, count)
                        VALUES (?, 1)
                    ''', (feature,))
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Error updating usage stats: {e}")

    def get_recent_interactions(self, limit=50):
        """Get recent interactions for chat history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_input, ai_response, interaction_type, timestamp, language
                    FROM interactions
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                interactions = []
                for row in results:
                    interactions.append({
                        'user_input': row[0],
                        'ai_response': row[1],
                        'interaction_type': row[2],
                        'timestamp': row[3],
                        'language': row[4]
                    })
                
                return list(reversed(interactions))  # Return in chronological order
                
        except sqlite3.Error as e:
            print(f"Error getting interactions: {e}")
            return []

    def get_usage_analytics(self):
        """Get usage analytics data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total interactions
                cursor.execute('SELECT COUNT(*) FROM interactions')
                total_interactions = cursor.fetchone()[0]
                
                # Get interactions by type
                cursor.execute('''
                    SELECT interaction_type, COUNT(*) 
                    FROM interactions 
                    GROUP BY interaction_type
                ''')
                interactions_by_type = dict(cursor.fetchall())
                
                # Get most used commands
                cursor.execute('''
                    SELECT command, COUNT(*) as count
                    FROM commands_log
                    WHERE success = 1
                    GROUP BY command
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                top_commands = cursor.fetchall()
                
                # Get language usage
                cursor.execute('''
                    SELECT language, COUNT(*) 
                    FROM interactions 
                    GROUP BY language
                ''')
                language_usage = dict(cursor.fetchall())
                
                # Get usage by hour (for usage patterns)
                cursor.execute('''
                    SELECT strftime('%H', timestamp) as hour, COUNT(*) 
                    FROM interactions 
                    GROUP BY hour
                    ORDER BY hour
                ''')
                hourly_usage = dict(cursor.fetchall())
                
                return {
                    'total_interactions': total_interactions,
                    'interactions_by_type': interactions_by_type,
                    'top_commands': top_commands,
                    'language_usage': language_usage,
                    'hourly_usage': hourly_usage
                }
                
        except sqlite3.Error as e:
            print(f"Error getting analytics: {e}")
            return {}

    def save_settings(self, settings):
        """Save user settings to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for key, value in settings.items():
                    # Convert complex values to JSON
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO settings (key, value, updated_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    ''', (key, str(value)))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"Error saving settings: {e}")
            return False

    def get_settings(self):
        """Get user settings from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT key, value FROM settings')
                results = cursor.fetchall()
                
                settings = {}
                for key, value in results:
                    # Try to parse JSON values
                    try:
                        if value.startswith('{') or value.startswith('['):
                            settings[key] = json.loads(value)
                        else:
                            # Handle boolean strings
                            if value.lower() == 'true':
                                settings[key] = True
                            elif value.lower() == 'false':
                                settings[key] = False
                            else:
                                settings[key] = value
                    except json.JSONDecodeError:
                        settings[key] = value
                
                return settings
                
        except sqlite3.Error as e:
            print(f"Error getting settings: {e}")
            return {}

    def clear_history(self, days=None):
        """Clear interaction history (optionally older than specified days)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if days:
                    cursor.execute('''
                        DELETE FROM interactions 
                        WHERE timestamp < datetime('now', '-{} days')
                    '''.format(days))
                else:
                    cursor.execute('DELETE FROM interactions')
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            print(f"Error clearing history: {e}")
            return False

    def backup_database(self, backup_path=None):
        """Create a backup of the database"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"wolf_ai_backup_{timestamp}.db"
            
            # Create backup using sqlite3 backup API
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            
            return backup_path
            
        except sqlite3.Error as e:
            print(f"Error creating backup: {e}")
            return None

    def get_database_info(self):
        """Get database information and statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get table information
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                table_info = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_info[table] = count
                
                # Get database size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return {
                    'database_path': self.db_path,
                    'database_size_bytes': db_size,
                    'tables': table_info
                }
                
        except sqlite3.Error as e:
            print(f"Error getting database info: {e}")
            return {}

# Test the database
if __name__ == "__main__":
    db = Database()
    
    # Test logging interactions
    db.log_interaction("Hello Wolf", "Hello! How can I help you?", "conversation", "en")
    db.log_command("open chrome", True, "Chrome opened successfully")
    
    # Test getting recent interactions
    interactions = db.get_recent_interactions(10)
    print(f"Recent interactions: {len(interactions)}")
    
    # Test analytics
    analytics = db.get_usage_analytics()
    print(f"Analytics: {analytics}")
    
    # Test settings
    test_settings = {
        'theme': 'dark',
        'voice_gender': 'female',
        'language': 'en'
    }
    db.save_settings(test_settings)
    
    saved_settings = db.get_settings()
    print(f"Saved settings: {saved_settings}")
    
    # Get database info
    db_info = db.get_database_info()
    print(f"Database info: {db_info}")
