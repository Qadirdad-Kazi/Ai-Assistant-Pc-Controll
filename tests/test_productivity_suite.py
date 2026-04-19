import unittest
from unittest.mock import patch
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.productivity_suite import ProductivitySuite

class TestProductivitySuite(unittest.TestCase):
    def setUp(self):
        self.ps = ProductivitySuite()

    @patch('subprocess.run')
    def test_email_drafting_macos(self, mock_run):
        """Test autonomous email drafting (AppleScript)."""
        mock_run.return_value.returncode = 0
        
        # Action: Draft follow-up
        result = self.ps.draft_follow_up_email(
            caller="+1234567890",
            transcript="I want a project for 5k",
            sentiment={"mood": "Positive", "score": 9, "next_steps": ["Prepare quote"]}
        )
        
        # This function doesn't return a dict currently, it just prints/runs subprocess.
        # But we check that subprocess was called.
        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        self.assertIn("Mail", str(cmd))

    def test_document_generation(self):
        """Test Markdown proposal generation."""
        # Setup mock sentiment
        sentiment = {
            "mood": "Positive",
            "score": 9,
            "summary": "Great call.",
            "next_steps": ["Step 1", "Step 2"]
        }
        
        # Use the correct method name
        file_path = self.ps.generate_call_document(
            caller="TestCaller",
            transcript="Sample transcript",
            sentiment=sentiment
        )
        
        self.assertTrue(os.path.exists(file_path))
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("TestCaller", content)
            self.assertIn("Great call", content)
        
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    unittest.main()
