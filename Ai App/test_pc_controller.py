"""
Test Suite for PC Controller
"""
import unittest
import os
import tempfile
import time
from unittest.mock import patch, MagicMock
from pc_controller import PCController

class TestPCController(unittest.TestCase):    
    def setUp(self):
        """Set up test environment before each test"""
        self.controller = PCController()
        # Create a temporary directory for testing file operations
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after each test"""
        # Clean up any created files or directories
        if os.path.exists(self.test_dir):
            for root, dirs, files in os.walk(self.test_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.test_dir)
    
    def test_create_folder_success(self):
        """Test successful folder creation"""
        folder_name = "test_folder"
        test_path = os.path.join(self.test_dir, folder_name)
        
        result = self.controller.execute_command(f"create folder in {self.test_dir} named {folder_name}")
        
        self.assertTrue(result['success'])
        self.assertIn('Successfully created folder', result['message'])
        self.assertTrue(os.path.exists(test_path))
        self.assertTrue(os.path.isdir(test_path))
    
    def test_create_folder_invalid_path(self):
        """Test folder creation with invalid path"""
        invalid_path = "/invalid/path/that/does/not/exist"
        result = self.controller.execute_command(f"create folder in {invalid_path} named test")
        
        self.assertFalse(result['success'])
        self.assertIn('Error creating folder', result['message'])
    
    @patch('pyautogui.moveTo')
    def test_mouse_movement(self, mock_move):
        """Test mouse movement command"""
        mock_move.return_value = None
        
        result = self.controller.execute_command("mouse move to 100 200")
        
        self.assertTrue(result['success'])
        mock_move.assert_called_once()
    
    @patch('webbrowser.open')
    def test_open_url(self, mock_open):
        """Test URL opening"""
        test_url = "https://example.com"
        
        result = self.controller.execute_command(f"open {test_url}")
        
        self.assertTrue(result['success'])
        mock_open.assert_called_once_with(test_url)
    
    def test_get_time_date(self):
        """Test getting current time and date"""
        result = self.controller.execute_command("what time is it")
        
        self.assertTrue(result['success'])
        self.assertIn('Current time', result['message'])
    
    def test_invalid_command(self):
        """Test handling of invalid commands"""
        result = self.controller.execute_command("this is not a valid command")
        
        self.assertFalse(result['success'])
        self.assertIn('Unrecognized command', result['message'])
    
    def test_command_history(self):
        """Test command history tracking"""
        commands = [
            "open https://example.com",
            "what time is it",
            "create folder test"
        ]
        
        # Execute test commands
        for cmd in commands:
            self.controller.execute_command(cmd)
        
        # Check history
        history = self.controller.command_history.get_history(len(commands))
        self.assertEqual(len(history), min(len(commands), 10))  # Default limit is 10
        
        # Verify the last command is in history
        self.assertIn(commands[-1].lower(), history[-1]['command'].lower())

if __name__ == '__main__':
    unittest.main()
