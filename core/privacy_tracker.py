import time
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

class PrivacyTracker:
    """
    Centralized tracker to log what data is sent to and received from external services.
    Provides data to the Privacy Dashboard for professional transparency.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PrivacyTracker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.logs: List[Dict[str, Any]] = []
        self.max_logs = 1000  # Keep last 1000 events
        self.log_file = "data/privacy_logs.json"
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Load existing logs if any
        self._load_logs()
        self._initialized = True

    def log_event(self, service: str, direction: str, data_type: str, data_summary: str, size_bytes: int = 0):
        """
        Log a privacy event.
        
        Args:
            service: The external service name (e.g., 'DuckDuckGo', 'Ollama', 'Picovoice')
            direction: 'SENT' or 'RECEIVED'
            data_type: 'Query', 'Model Response', 'Voice Data', etc.
            data_summary: A brief, non-sensitive summary of the data
            size_bytes: Size of the data in bytes
        """
        event = {
            "id": int(time.time() * 1000),
            "timestamp": datetime.now().isoformat(),
            "service": service,
            "direction": direction,
            "type": data_type,
            "summary": data_summary,
            "size": size_bytes
        }
        
        self.logs.insert(0, event)  # Newest first
        
        # Trim logs
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[:self.max_logs]
            
        # Perodically save or just save on every event for now
        self._save_logs()

    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.logs[:limit]

    def clear_logs(self):
        self.logs = []
        self._save_logs()

    def _save_logs(self):
        try:
            with open(self.log_file, "w") as f:
                json.dump(self.logs, f, indent=2)
        except Exception as e:
            print(f"[PrivacyTracker] Error saving logs: {e}")

    def _load_logs(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    self.logs = json.load(f)
            except Exception as e:
                print(f"[PrivacyTracker] Error loading logs: {e}")
                self.logs = []

# Global singleton instance
privacy_tracker = PrivacyTracker()
