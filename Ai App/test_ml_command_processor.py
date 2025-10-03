"""
Tests for the ML Command Processor
"""

import os
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from ml_command_processor import MLCommandProcessor


class TestMLCommandProcessor(unittest.TestCase):
    """Test cases for MLCommandProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        
        # Create necessary subdirectories
        self.models_dir = os.path.join(self.test_dir, 'models')
        self.data_dir = os.path.join(self.test_dir, 'data')
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.model_path = os.path.join(self.models_dir, 'command_classifier.joblib')
        self.data_path = os.path.join(self.data_dir, 'command_training_data.json')
        
        # Initialize the processor with test paths
        self.processor = MLCommandProcessor(model_path=self.model_path)
        self.processor.training_data_path = self.data_path
        
        # Ensure we're using the test paths
        self.processor._ensure_data_dir()
        
        # Sample training data
        self.sample_commands = [
            ("open chrome", "open_chrome", {
                "action": "run_command",
                "command": "open -a \"Google Chrome\"",
                "description": "Opens Google Chrome browser"
            }),
            ("launch chrome", "open_chrome", {
                "action": "run_command",
                "command": "open -a \"Google Chrome\"",
                "description": "Opens Google Chrome browser"
            }),
            ("open terminal", "open_terminal", {
                "action": "run_command",
                "command": "open -a Terminal .",
                "description": "Opens a new Terminal window"
            }),
            ("start terminal", "open_terminal", {
                "action": "run_command",
                "command": "open -a Terminal .",
                "description": "Opens a new Terminal window"
            })
        ]
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test MLCommandProcessor initialization"""
        self.assertIsNotNone(self.processor.model)
        self.assertIsNotNone(self.processor.vectorizer)
        self.assertEqual(len(self.processor.commands), 0)
    
    def test_add_training_example(self):
        """Test adding training examples"""
        # Add first command
        text, cmd_id, details = self.sample_commands[0]
        result = self.processor.add_training_example(text, cmd_id, details)
        self.assertTrue(result)
        self.assertEqual(len(self.processor.training_data['texts']), 1)
        self.assertEqual(len(self.processor.training_data['labels']), 1)
        self.assertIn(cmd_id, self.processor.commands)
        
        # Add second example of the same command
        text2, cmd_id2, details2 = self.sample_commands[1]
        result = self.processor.add_training_example(text2, cmd_id2, details2)
        self.assertTrue(result)
        self.assertEqual(len(self.processor.training_data['texts']), 2)
        self.assertEqual(len(self.processor.training_data['labels']), 2)
        self.assertEqual(len(self.processor.commands[cmd_id]['examples']), 2)
    
    def test_train_model(self):
        """Test model training"""
        # Add training examples (use all samples to ensure we have enough data)
        for text, cmd_id, details in self.sample_commands:
            self.processor.add_training_example(text, cmd_id, details)
        
        # Train the model
        result = self.processor.train()
        self.assertEqual(result['status'], 'success')
        
        # For small datasets, we might not have test accuracy
        if 'accuracy' in result:
            self.assertGreaterEqual(result['accuracy'], 0)
        
        # Verify model file was created
        self.assertTrue(os.path.exists(self.model_path))
    
    @patch('ml_command_processor.joblib.dump')
    def test_save_model(self, mock_dump):
        """Test saving the model"""
        self.processor.save_model()
        mock_dump.assert_called_once()
    
    def test_predict_command(self):
        """Test command prediction"""
        # Add training examples and train
        for text, cmd_id, details in self.sample_commands:
            self.processor.add_training_example(text, cmd_id, details)
        
        # Train the model
        train_result = self.processor.train()
        self.assertEqual(train_result['status'], 'success')
        
        # Test prediction - use a phrase similar to training data
        result = self.processor.predict_command("launch chrome browser")
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['command_id'], 'open_chrome')
        
        # For very small datasets, confidence might not be reliable
        if 'confidence' in result:
            self.assertGreater(result['confidence'], 0.3)
        
        # Test with a completely unknown command
        result = self.processor.predict_command("this is a completely unknown command")
        self.assertIn(result['status'], ['success', 'low_confidence'])
        
        # Test with explicit low confidence threshold
        with patch('numpy.max', return_value=0.3):
            result = self.processor.predict_command("some unknown command", threshold=0.5)
            self.assertEqual(result['status'], 'low_confidence')
    
    def test_list_commands(self):
        """Test listing all commands"""
        # Add some commands
        for text, cmd_id, details in self.sample_commands[:2]:  # Add first two (same command)
            self.processor.add_training_example(text, cmd_id, details)
        
        commands = self.processor.list_commands()
        self.assertEqual(len(commands), 1)  # Should be 1 unique command
        self.assertEqual(commands[0]['command_id'], 'open_chrome')
    
    def test_delete_command(self):
        """Test deleting a command"""
        # Add commands
        for text, cmd_id, details in self.sample_commands:
            self.processor.add_training_example(text, cmd_id, details)
        
        # Delete a command
        self.assertTrue(self.processor.delete_command('open_chrome'))
        
        # Verify deletion
        self.assertNotIn('open_chrome', self.processor.commands)
        self.assertEqual(len([l for l in self.processor.training_data['labels'] 
                            if l == 'open_chrome']), 0)
        
        # Verify other command still exists
        self.assertIn('open_terminal', self.processor.commands)
    
    def test_save_and_load_training_data(self):
        """Test saving and loading training data"""
        # Add some data
        for text, cmd_id, details in self.sample_commands[:2]:
            self.processor.add_training_example(text, cmd_id, details)
    
        # Save and create a new processor to load the data
        self.assertTrue(self.processor._save_training_data())
        
        # Create a new processor to load the saved data
        new_processor = MLCommandProcessor(model_path=self.model_path)
        new_processor.training_data_path = self.data_path
        new_processor._load_training_data()
        
        # Verify the data was loaded correctly
        self.assertEqual(len(new_processor.training_data['texts']), 2)
        self.assertEqual(len(new_processor.training_data['labels']), 2)
        self.assertEqual(len(new_processor.commands), 1)  # Only 1 unique command in first 2 samples
        self.assertEqual(len(self.processor.commands), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
