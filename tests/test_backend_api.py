import unittest
from fastapi.testclient import TestClient
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock core components before importing app to avoid hardware/model initialization
with patch('core.voice_assistant.voice_assistant'), \
     patch('core.tts.tts'), \
     patch('core.function_executor.executor'), \
     patch('core.productivity_suite.productivity_suite'), \
     patch('core.analytics_engine.analytics_engine'), \
     patch('core.database.db'), \
     patch('core.receptionist.receptionist'), \
     patch('core.settings_store.settings'), \
     patch('core.privacy_tracker.privacy_tracker'), \
     patch('core.advanced_task_executor.advanced_executor'):
    from backend_api import app

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_system_status(self):
        """Test basic system status retrieval."""
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Voice Core", data)
        self.assertIn("System Control", data)

    def test_diagnostics_structure(self):
        """Verify the diagnostics payload structure."""
        response = self.client.get("/api/diagnostics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("diagnostics", data)
        self.assertTrue(isinstance(data["diagnostics"], list))

    @patch('backend_api.run_single_diagnostic')
    @patch('backend_api.diagnostics_state', {'test': {'ok': True, 'status': 'PASS'}})
    def test_run_diagnostic(self, mock_run):
        """Test running a specific diagnostic."""
        mock_run.return_value = {"key": "test", "ok": True, "detail": "Success", "status": "PASS"}
        response = self.client.post("/api/diagnostics/run", json={"key": "test"})
        self.assertEqual(response.status_code, 200)
        # Check result field in response (from backend_api.py:809)
        self.assertTrue(response.json()["result"]["ok"])

if __name__ == '__main__':
    unittest.main()
