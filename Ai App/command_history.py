"""
Command History Module
Handles tracking and managing command history
"""
import json
import os
from datetime import datetime

class CommandHistory:
    def __init__(self, max_history=100):
        """
        Initialize command history with a maximum number of entries
        
        Args:
            max_history (int): Maximum number of history entries to keep
        """
        self.max_history = max_history
        self.history_file = os.path.expanduser('~/.wolf_assistant_history.json')
        self.history = self._load_history()
    
    def _load_history(self):
        """Load command history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return []
    
    def _save_history(self):
        """Save command history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history[-self.max_history:], f, indent=2)
            return True
        except IOError:
            return False
    
    def add(self, command, result=None):
        """
        Add a command to the history
        
        Args:
            command (str): The command that was executed
            result (dict): The result of the command execution
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'success': result.get('success', False) if result else False,
            'message': result.get('message', '') if result else '',
            'type': result.get('type', 'command') if result else 'command'
        }
        self.history.append(entry)
        self._save_history()
        return entry
    
    def get_history(self, limit=10):
        """
        Get recent command history
        
        Args:
            limit (int): Maximum number of history entries to return
            
        Returns:
            list: List of recent command entries
        """
        return self.history[-limit:]
    
    def clear(self):
        """Clear command history"""
        self.history = []
        try:
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
            return True
        except OSError:
            return False
