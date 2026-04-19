import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tts import UnifiedTTS
from core.kokoro_tts import KokoroTTS

class TestTTSSTT(unittest.TestCase):
    
    def setUp(self):
        self.unified_tts = UnifiedTTS()

    @patch('core.tts.PiperTTS.initialize')
    @patch('core.settings_store.settings.get')
    def test_unified_tts_default_engine(self, mock_settings, mock_piper_init):
        """Test that UnifiedTTS defaults to Piper and initializes it."""
        mock_settings.return_value = "piper"
        mock_piper_init.return_value = True
        self.unified_tts.initialize()
        mock_piper_init.assert_called_once()
    
    @patch('core.kokoro_tts.KokoroTTS.initialize')
    @patch('core.settings_store.settings.get')
    def test_unified_tts_kokoro_selection(self, mock_settings, mock_kokoro_init):
        """Test switching to Kokoro engine via settings."""
        mock_settings.return_value = "kokoro"
        mock_kokoro_init.return_value = True
        
        self.unified_tts.initialize()
        self.assertEqual(self.unified_tts.engine, "kokoro")
        mock_kokoro_init.assert_called_once()

    @patch('core.tts.PiperTTS.speak')
    def test_unified_tts_speak_routing(self, mock_piper_speak):
        """Test that speak calls are routed to the active engine."""
        self.unified_tts.engine = "piper"
        self.unified_tts.speak("Hello")
        mock_piper_speak.assert_called_with("Hello")

    @patch('os.path.exists')
    def test_kokoro_initialization_no_model(self, mock_exists):
        """Test Kokoro fails gracefully if model file is missing."""
        mock_exists.return_value = False
        k = KokoroTTS()
        
        # We need to mock the import too
        with patch('kokoro.KPipeline', create=True) as mock_pipeline:
            # If we want to simulate failure, we can make KPipeline raise an error or return something invalid
            mock_pipeline.side_effect = Exception("Model not found")
            result = k.initialize()
            self.assertFalse(result)
            self.assertFalse(k.is_initialized)

if __name__ == '__main__':
    unittest.main()
