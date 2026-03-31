import unittest
from unittest.mock import patch
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import route_query

class TestVoicePipeline(unittest.TestCase):
    
    @patch('core.router.FunctionGemmaRouter.route_with_timing')
    def test_intent_detection_basic(self, mock_route):
        """Test basic intent mapping (Mocked Gemma)."""
        # Mocking the FunctionGemmaRouter result
        mock_route.return_value = ([("pc_control", {"action": "open_app", "target": "chrome"})], 1.2)
        
        # Test routing
        calls = route_query("Open Google Chrome")
        func, params = calls[0]
        
        self.assertEqual(func, "pc_control")
        self.assertEqual(params["action"], "open_app")
        self.assertEqual(params["target"], "chrome")

    @patch('core.router.FunctionGemmaRouter.route_with_timing')
    def test_multistep_intent(self, mock_route):
        """Test complex multi-step intentions."""
        mock_output = [
            ("pc_control", {"action": "create_folder", "path": "Desktop/NewProject"}),
            ("pc_control", {"action": "open_app", "target": "vscode"})
        ]
        mock_route.return_value = (mock_output, 2.5)
        
        calls = route_query("Create a project folder on my desktop and open code.")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0], "pc_control")
        self.assertEqual(calls[1][1]["target"], "vscode")

if __name__ == '__main__':
    unittest.main()
