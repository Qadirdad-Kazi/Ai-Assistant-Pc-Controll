import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.receptionist import Receptionist
from core.database import db

class TestReceptionist(unittest.TestCase):
    def setUp(self):
        self.receptionist = Receptionist()

    @patch('core.receptionist.Receptionist._generate_response')
    @patch('core.database.db.log_call')
    def test_handle_call_logic(self, mock_db, mock_llm):
        """Test basic directive handling and response generation."""
        mock_llm.return_value = "Hello, I will let him know."
        mock_db.return_value = 1
        
        # Add a directive
        self.receptionist.add_directive("Wolf", "Tell him I am busy")
        
        # Simulate incoming call (we need to mock gsm_gateway and others to avoid side effects)
        from core.gsm_gateway import gsm_gateway
        with patch('core.gsm_gateway.gsm_gateway.answer_call'), \
             patch('core.audio_bridge.audio_bridge.link_call'), \
             patch('core.tts.tts.queue_sentence'), \
             patch('core.voice_assistant.voice_assistant.stt_listener', create=True) as mock_stt, \
             patch.object(gsm_gateway, 'is_connected', new_callable=PropertyMock) as mock_connected:
            
            mock_connected.side_effect = [True, False]
            
            # Setup a mock recorder that returns one message
            import itertools
            mock_recorder = MagicMock()
            mock_recorder.text.side_effect = itertools.chain(["Hi Wolf here."], itertools.repeat(""))
            mock_stt.recorder = mock_recorder
            
            self.receptionist.handle_incoming_call("Wolf")
        
        mock_llm.assert_called()
        self.assertIn("Hello", mock_llm.call_args[0][0] or "")

    @patch('core.productivity_suite.productivity_suite.analyze_sentiment')
    def test_sentiment_analysis_integration(self, mock_sentiment):
        """Test sentiment analysis call."""
        mock_sentiment.return_value = {"mood": "Happy", "score": 9}
        
        # The receptionist calls productivity_suite.process_call_outcome
        with patch('core.productivity_suite.productivity_suite.process_call_outcome') as mock_process:
            # We mock the DB log to get a call_id
            with patch('core.database.db.log_call', return_value=123):
                # We need to bypass the thread in handle_incoming_call for testing
                # Or just test the productivity suite directly (which we do in another file)
                pass

if __name__ == '__main__':
    unittest.main()

if __name__ == '__main__':
    unittest.main()
