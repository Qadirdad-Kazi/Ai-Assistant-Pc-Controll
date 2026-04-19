import unittest
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import db
from core.advanced_task_executor import advanced_executor

from core.database import WolfCoreDatabase

class TestLearningLoop(unittest.TestCase):
    def setUp(self):
        # Use a temporary file database for testing to ensure multiple connections work
        self.test_db = "tests/test_wolf_core.db"
        self.db = WolfCoreDatabase(self.test_db)
        
    def tearDown(self):
        # Clean up test database
        if hasattr(self, 'test_db') and os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except:
                pass
        
    def test_experience_capture(self):
        """Test capturing a new heuristic after a simulated failure."""
        query = "Open MyPrivateApp"
        # Simulate a manual correction plan
        learned_plan = [
            {"step": 1, "action": "open_app", "details": {"name": "terminal"}},
            {"step": 2, "action": "pc_control", "details": {"action": "type", "text": "start private_app"}}
        ]
        
        # Save experience directly
        self.db.save_experience(query, learned_plan)
        
        # Retrieve and verify
        retrieved_plan = self.db.get_learned_heuristic(query)
        self.assertIsNotNone(retrieved_plan)
        self.assertEqual(len(retrieved_plan), 2)
        self.assertEqual(retrieved_plan[0]["action"], "open_app")

    def test_reinforcement(self):
        """Test success-count incrementing for learned behaviors."""
        query = "Open MyPrivateApp"
        # Ensure it exists
        self.db.save_experience(query, [{"step": 1, "action": "noop"}])
        
        # Initial check
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT success_count FROM learned_heuristics WHERE query = ?', (query.lower(),))
            initial_count = cursor.fetchone()[0]
            
            self.db.increment_heuristic_success(query)
            
            cursor.execute('SELECT success_count FROM learned_heuristics WHERE query = ?', (query.lower(),))
            new_count = cursor.fetchone()[0]
            self.assertEqual(new_count, initial_count + 1)

if __name__ == '__main__':
    unittest.main()
