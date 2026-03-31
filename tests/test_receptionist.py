import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.receptionist import Receptionist
from core.database import db

class TestReceptionist(unittest.TestCase):
    def setUp(self):
        self.receptionist = Receptionist()

    @patch('core.receptionist.llm_responder.generate_response')
    def test_handle_call_logic(self, mock_llm):
        """Test full call life-cycle with mocked SIM800L input."""
        mock_llm.return_value = "Hello, I am interested in a 5000 dollar project."
        
        # Simulate incoming call data
        call_data = {
            "caller_id": "+1234567890",
            "transcript": "I want to talk about a project worth 5000 dollars."
        }
        
        # Test the high-level handling
        result = self.receptionist.process_call_transcript(call_data["transcript"], call_data["caller_id"])
        
        self.assertTrue(result["success"])
        # Verify extraction of deal size if implemented in receptionist
        # Or verify it's logged in call_logs correctly
        logs = db.get_call_logs(limit=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["transcript"], call_data["transcript"])

    def test_sentiment_analysis_mock(self):
        """Test client mood categorization (Mocked AI Analysis)."""
        # Mocking the internal productivity suite analysis
        with patch('core.productivity_suite.productivity_suite.analyze_and_act') as mock_act:
            mock_act.return_value = {"mood": "Frustrated", "tasks": 2}
            
            # This would be triggered post-call
            analysis = self.receptionist.finalize_call_workflow("I am unhappy with the service.")
            self.assertEqual(analysis["mood"], "Frustrated")

if __name__ == '__main__':
    unittest.main()
