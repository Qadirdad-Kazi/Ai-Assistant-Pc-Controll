import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import route_query

class TestRouter(unittest.TestCase):
    
    @patch('requests.post')
    @patch('core.settings_store.settings.get')
    def test_ollama_fallback(self, mock_settings, mock_post):
        """Test that the router falls back to Ollama when local model is missing."""
        mock_settings.return_value = "http://localhost:11434/api"
        
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": 'call:pc_control{action:open_app,target:notepad}'
        }
        mock_post.return_value = mock_response
        
        # Force local router to be in fallback mode
        from core import llm
        with patch('core.router.ensure_model_available', return_value=None):
            # We need to clear the global router to trigger re-init in test
            llm.router = None
            calls = llm.route_query("Open notepad")
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0], "pc_control")
            self.assertEqual(calls[0][1]["target"], "notepad")

    def test_empty_query_routing(self):
        """Test routing with empty or nonsense input."""
        # route_query returns a fallback list for empty input
        calls = route_query("")
        self.assertEqual(len(calls), 1)
        self.assertIn(calls[0][0], ["nonthinking", "thinking"])

if __name__ == '__main__':
    unittest.main()
