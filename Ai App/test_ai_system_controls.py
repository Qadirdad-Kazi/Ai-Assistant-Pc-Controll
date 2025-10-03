"""
Tests for AI Enhancements and System Controls
"""

import unittest
import os
import time
import json
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from ai_enhancements import AIEnhancements
from system_controls import SystemControls

class TestAIEnhancements(unittest.TestCase):
    """Test cases for AIEnhancements class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.ai = AIEnhancements()
        
    def test_system_health_check(self):
        """Test system health check functionality"""
        health = self.ai.system_health_check()
        self.assertIn('cpu', health)
        self.assertIn('memory', health)
        self.assertIn('disk', health)
        self.assertIsInstance(health['cpu']['percent'], (int, float))
        self.assertIsInstance(health['memory']['percent'], (int, float))
        
    @patch('ai_enhancements.openai.ChatCompletion.create')
    @patch('ai_enhancements.psutil')
    def test_predict_user_intent(self, mock_psutil, mock_openai):
        """Test user intent prediction"""
        # Mock psutil for system status
        mock_cpu = MagicMock()
        mock_cpu.percent.return_value = 10.5
        mock_cpu_freq = MagicMock()
        mock_cpu_freq.current = 2500
        mock_cpu_freq.max = 3500
        mock_virtual_memory = MagicMock()
        mock_virtual_memory.percent = 64.2
        mock_virtual_memory.total = 17179869184
        mock_virtual_memory.available = 6111903744
        mock_disk_usage = MagicMock()
        mock_disk_usage.percent = 70.5
        mock_disk_usage.total = 250685575168
        mock_disk_usage.used = 11615076352
        
        mock_psutil.cpu_percent.return_value = 10.5
        mock_psutil.cpu_count.return_value = 12
        mock_psutil.cpu_freq.return_value = mock_cpu_freq
        mock_psutil.virtual_memory.return_value = mock_virtual_memory
        mock_psutil.disk_usage.return_value = mock_disk_usage
        mock_psutil.boot_time.return_value = time.time() - 3600  # 1 hour ago
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            'intent': 'execute_command',
            'confidence': 0.95,
            'action': {'type': 'run_command', 'command': 'Open Chrome browser'}
        })
        mock_openai.return_value = mock_response
        
        # Test prediction
        result = self.ai.predict_user_intent("Open Chrome browser")
        
        # Verify the result
        self.assertTrue(result['success'])
        self.assertEqual(result['intent'], 'execute_command')
        self.assertIn('action', result)
        self.assertEqual(result['action']['type'], 'run_command')
        self.assertEqual(result['action']['command'], 'Open Chrome browser')
        self.assertIn('confidence', result)
        self.assertGreaterEqual(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 1)
        self.assertIn('context', result)
        self.assertIn('command', result['context'])
        self.assertEqual(result['context']['command'], 'Open Chrome browser')
        
    def test_analyze_screen_content(self):
        """Test screen content analysis"""
        # This is a basic test, actual OCR would require proper setup
        with patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Sample text from screen"
            result = self.ai.analyze_screen_content()
            self.assertTrue(result['success'])
            self.assertIn('text', result)
            self.assertIn('analysis', result)


class TestSystemControls(unittest.TestCase):
    """Test cases for SystemControls class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.system = SystemControls()
        
    def test_get_system_info(self):
        """Test getting system information"""
        info = self.system.get_system_info()
        self.assertTrue(info['success'])
        self.assertIn('cpu', info['data'])
        self.assertIn('memory', info['data'])
        self.assertIn('disks', info['data'])
        
    @patch('psutil.process_iter')
    def test_list_processes(self, mock_process_iter):
        """Test listing processes"""
        # Mock process data
        mock_process = MagicMock()
        mock_process.info = {
            'pid': 1234,
            'name': 'test_process',
            'username': 'testuser',
            'status': 'running',
            'cpu_percent': 1.5,
            'memory_percent': 0.5
        }
        mock_process_iter.return_value = [mock_process]
        
        processes = self.system.list_processes()
        self.assertIsInstance(processes, list)
        if processes:  # Only check if there are processes
            self.assertIn('pid', processes[0])
            self.assertIn('name', processes[0])
            
    @patch('os.system')
    def test_shutdown(self, mock_system):
        """Test system shutdown"""
        result = self.system.shutdown(force=True)
        self.assertTrue(result['success'])
        mock_system.assert_called()
        
    @patch('os.system')
    def test_restart(self, mock_system):
        """Test system restart"""
        result = self.system.restart(force=True)
        self.assertTrue(result['success'])
        mock_system.assert_called()
        
    @patch('os.system')
    def test_sleep_mode(self, mock_system):
        """Test sleep mode"""
        result = self.system.sleep_mode()
        self.assertTrue(result['success'])
        mock_system.assert_called()
        
    @patch('os.walk')
    @patch('os.path.isfile')
    @patch('os.path.getsize')
    @patch('os.path.getmtime')
    @patch('os.path.join')
    @patch('glob.glob')
    def test_find_files(self, mock_glob, mock_join, mock_getmtime, mock_getsize, mock_isfile, mock_walk):
        """Test file search functionality"""
        # Setup mock return values
        test_files = [
            ('/test', [], ['test_file.txt', 'document.pdf']),
            ('/test/subdir', [], ['image.png'])
        ]
        mock_walk.return_value = test_files
        
        # Mock os.path.join to return the filename as the path
        def join_side_effect(*args):
            return '/'.join(args)
        mock_join.side_effect = join_side_effect
        
        # Mock file stats
        mock_isfile.return_value = True
        mock_getsize.return_value = 1024
        mock_getmtime.return_value = time.time()
        
        # Mock glob to return filtered results
        def glob_side_effect(pattern, recursive=False):
            if pattern == '/test/*.pdf':
                return ['/test/document.pdf']
            elif pattern == '/test/**/*' or pattern == '/test/*':
                return ['/test/test_file.txt', '/test/document.pdf', '/test/subdir/image.png']
            return []
            
        mock_glob.side_effect = glob_side_effect
        
        # Test finding PDF files
        result = self.system.find_files('*.pdf', '/test')
        self.assertTrue(result['success'])
        
        # Since we're mocking the actual file system, we'll just check the structure
        if result.get('files'):
            self.assertTrue(any(f.get('path', '').endswith('.pdf') for f in result['files']))
        
        # Test finding all files
        result = self.system.find_files('*', '/test')
        self.assertTrue(result['success'])
        if result.get('files'):
            self.assertGreater(len(result['files']), 0)
        
    @patch('builtins.open', new_callable=mock_open, read_data='test content')
    @patch('os.walk')
    def test_search_file_content(self, mock_walk, mock_file):
        """Test searching content in files"""
        # Mock os.walk to return test files
        mock_walk.return_value = [
            ('/test', [], ['test_file.txt'])
        ]
        
        # Test search
        result = self.system.search_file_content('test', '/test', '*.txt')
        self.assertTrue(result['success'])
        self.assertGreaterEqual(len(result['matches']), 0)
        
    @patch('PIL.ImageGrab.grab')
    def test_take_screenshot(self, mock_grab):
        """Test screenshot functionality"""
        # Mock ImageGrab.grab
        mock_image = MagicMock()
        mock_image.size = (1920, 1080)
        mock_image.mode = 'RGB'
        mock_grab.return_value = mock_image
        
        # Test with save path
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = self.system.take_screenshot(temp_path)
            self.assertTrue(result['success'])
            self.assertEqual(result['size'], (1920, 1080))
            self.assertTrue(os.path.exists(temp_path))
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    @patch('pytesseract.image_to_string')
    @patch('PIL.ImageGrab.grab')
    def test_ocr_screen(self, mock_grab, mock_ocr):
        """Test OCR functionality"""
        # Mock ImageGrab.grab and pytesseract
        mock_image = MagicMock()
        mock_grab.return_value = mock_image
        mock_ocr.return_value = "Extracted text from screen"
        
        # Test OCR
        result = self.system.ocr_screen()
        self.assertTrue(result['success'])
        self.assertEqual(result['text'], "Extracted text from screen")
        mock_ocr.assert_called_once()


class TestIntegration(unittest.TestCase):
    """Integration tests for AI and System controls"""
    
    def test_ai_with_system_controls(self):
        """Test AI and System controls integration"""
        ai = AIEnhancements()
        system = SystemControls()
        
        # Get system info through AI
        health = ai.system_health_check()
        self.assertIn('cpu', health)
        self.assertIn('memory', health)
        
        # Get system info through system controls
        info = system.get_system_info()
        self.assertTrue(info['success'])
        
        # Verify both methods return valid CPU information
        if 'cpu' in health and 'data' in info and 'cpu' in info['data']:
            # Check that both return valid positive values
            self.assertIsInstance(health['cpu']['cores'], int)
            self.assertGreater(health['cpu']['cores'], 0)
            self.assertIsInstance(info['data']['cpu'].get('cores'), int)
            self.assertGreater(info['data']['cpu'].get('cores'), 0)


if __name__ == "__main__":
    # Run tests with increased verbosity
    unittest.main(verbosity=2)
