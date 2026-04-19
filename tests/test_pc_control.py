import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pc_control import PCController

class TestPCControl(unittest.TestCase):
    def setUp(self):
        self.controller = PCController()

    @patch('subprocess.run')
    @patch('os.startfile')
    @patch('core.vision_agent.vision_agent.human_launch_app')
    @patch('core.dynamic_app_discovery.dynamic_discovery.find_app_by_name')
    def test_open_app_mock(self, mock_discover, mock_human_launch, mock_start, mock_run):
        """Test application launching via mocked components."""
        mock_run.return_value.returncode = 0
        mock_human_launch.return_value = {"success": True}
        
        result = self.controller.execute("open_app", "calculator")
        self.assertTrue(result["success"])
        self.assertIn("successfully", result["message"].lower())

    @patch('subprocess.run')
    def test_window_tiling_macos(self, mock_run):
        """Test macOS window tiling (AppleScript execution)."""
        mock_run.return_value.returncode = 0
        result = self.controller.execute("tile_windows", "dev")
        self.assertTrue(result["success"])
        self.assertIn("organized", result["message"].lower())
        # Verify AppleScript was called
        mock_run.assert_called_with(['osascript', '-e', unittest.mock.ANY], check=True)

    @patch('pyautogui.press')
    def test_volume_control(self, mock_press):
        """Test volume adjustment via pyautogui mocks."""
        result = self.controller.execute("volume", "up")
        self.assertTrue(result["success"])
        self.assertEqual(mock_press.call_count, 5) # 5 presses for 10%

    def test_lock_pc(self):
        """Test PC Locking logic (Mocked)."""
        with patch('ctypes.windll.user32.LockWorkStation') as mock_lock:
            # Note: This specifically tests the Windows logic in the code
            result = self.controller.execute("lock")
            if os.name == 'nt':
                mock_lock.assert_called_once()
                self.assertTrue(result["success"])
            else:
                # On macOS/Linux it should fail gracefully or say not supported
                # In current implementation, it tries ctypes.windll which fails on Mac
                self.assertFalse(result["success"])

if __name__ == '__main__':
    unittest.main()
