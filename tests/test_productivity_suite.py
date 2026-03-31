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
        result = self.ps.draft_followup_email(
            recipient="client@example.com",
            context="Interested in mobile app for 5k",
            tone="Professional"
        )
        
        self.assertTrue(result["success"])
        # Check if AppleScript mentioned 'Mail' app
        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        self.assertIn("Mail", str(cmd))

    def test_document_generation(self):
        """Test Markdown proposal generation."""
        target_path = "tests/test_proposal.md"
        if os.path.exists(target_path): os.remove(target_path)
        
        result = self.ps.generate_proposal(
            client_name="Test Corp",
            project_details="AI Automation Suite",
            est_value=12000,
            output_path=target_path
        )
        
        self.assertTrue(result["success"])
        self.assertTrue(os.path.exists(target_path))
        
        with open(target_path, 'r') as f:
            content = f.read()
            self.assertIn("Test Corp", content)
            self.assertIn("12,000", content)
        
        # Cleanup
        os.remove(target_path)

if __name__ == '__main__':
    unittest.main()
