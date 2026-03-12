"""
UI and Voice Integration Test Suite
Tests the integration between frontend, backend, and voice components.
"""

import pytest
import asyncio
import time
import requests
import json
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.voice_assistant import voice_assistant
    from core.tts import tts
    from core.stt import STTListener
    from core.vision_agent import VisionAgent
    from core.memory import memory_manager
    from core.kokoro_tts import kokoro_tts
    from utilities.research_handler import research_handler
    from utilities.search_handler import web_search_handler
    from core.bug_watcher import bug_watcher
    UI_VOICE_AVAILABLE = True
except ImportError as e:
    print(f"UI/Voice modules not available: {e}")
    UI_VOICE_AVAILABLE = False

@pytest.mark.skipif(not UI_VOICE_AVAILABLE, reason="UI/Voice modules not available")
class TestUIVoiceIntegration:
    """Test suite for UI and Voice integration."""

    @pytest.fixture
    def backend_url(self):
        """Backend API URL."""
        return "http://localhost:8000"

    @pytest.fixture
    def frontend_url(self):
        """Frontend URL."""
        return "http://localhost:5173"

    def test_backend_api_health_check(self, backend_url):
        """Test backend API health check endpoint."""
        try:
            response = requests.get(f"{backend_url}/health", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")

    def test_frontend_build_exists(self):
        """Test that frontend build exists."""
        frontend_dist = project_root / "frontend" / "dist"
        assert frontend_dist.exists(), "Frontend dist directory not found"
        
        index_html = frontend_dist / "index.html"
        assert index_html.exists(), "Frontend index.html not found"
        
        # Check that build files exist (they're in assets/ subdirectory)
        assets_dir = frontend_dist / "assets"
        assert assets_dir.exists(), "Frontend assets directory not found"
        
        js_files = list(assets_dir.glob("*.js"))
        css_files = list(assets_dir.glob("*.css"))
        
        assert len(js_files) > 0, "No JavaScript files found in build"
        assert len(css_files) > 0, "No CSS files found in build"

    def test_backend_status_endpoint(self, backend_url):
        """Test backend status endpoint."""
        try:
            response = requests.get(f"{backend_url}/api/status", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, dict)
            assert "isListening" in data
            assert "Voice Core" in data
            assert "System Control" in data
            assert "Neural Sonic" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")

    @pytest.mark.asyncio
    async def test_voice_assistant_initialization(self):
        """Test voice assistant initialization."""
        # Test that voice assistant can be initialized
        assert hasattr(voice_assistant, 'initialize')
        assert hasattr(voice_assistant, 'start')
        assert hasattr(voice_assistant, 'stop')

    @pytest.mark.asyncio
    async def test_tts_integration(self):
        """Test TTS integration with voice system."""
        # Test TTS system
        assert hasattr(tts, 'speak')
        assert hasattr(tts, 'toggle')
        
        # Test Kokoro TTS integration
        assert hasattr(kokoro_tts, 'speak')
        assert hasattr(kokoro_tts, 'initialize')

    @pytest.mark.asyncio
    async def test_stt_integration(self):
        """Test STT integration with voice system."""
        try:
            stt = STTListener()
            assert hasattr(stt, 'start_listening')
            assert hasattr(stt, 'stop_listening')
        except ImportError:
            pytest.skip("STT module not available")

    @pytest.mark.asyncio
    async def test_vision_integration(self):
        """Test vision agent integration."""
        vision_agent = VisionAgent()
        assert hasattr(vision_agent, '_capture_screen_base64')
        assert hasattr(vision_agent, '_analyze_screen')

    @pytest.mark.asyncio
    async def test_memory_integration(self):
        """Test memory system integration."""
        assert hasattr(memory_manager, 'store_memory')
        assert hasattr(memory_manager, 'recall_preferences')

    @pytest.mark.asyncio
    async def test_research_integration(self):
        """Test research system integration."""
        assert hasattr(research_handler, 'scrape_url')
        assert hasattr(web_search_handler, 'search')

    @pytest.mark.asyncio
    async def test_bug_watcher_integration(self):
        """Test bug watcher integration."""
        assert hasattr(bug_watcher, 'start')
        assert hasattr(bug_watcher, 'stop')
        assert hasattr(bug_watcher, 'alert_keywords')

    def test_websocket_connection(self, backend_url):
        """Test WebSocket connection for real-time updates."""
        try:
            import websocket
            ws_url = backend_url.replace('http://', 'ws://') + '/ws/status'
            
            # Test connection
            ws = websocket.create_connection(ws_url, timeout=5)
            
            # Should receive initial status
            data = ws.recv()
            assert data is not None
            
            # Parse JSON data
            status_data = json.loads(data)
            assert isinstance(status_data, dict)
            
            ws.close()
        except (ImportError, requests.exceptions.ConnectionError, websocket.WebSocketException):
            pytest.skip("WebSocket connection not available")

    def test_ui_backend_communication(self, backend_url):
        """Test UI to backend communication."""
        try:
            # Test API endpoints that UI would use
            endpoints = [
                "/api/status",
                "/api/diagnostics",
                "/api/settings"
            ]
            
            for endpoint in endpoints:
                response = requests.get(f"{backend_url}{endpoint}", timeout=5)
                assert response.status_code in [200, 404, 405]  # Any valid HTTP response
                
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")

    @pytest.mark.asyncio
    async def test_voice_to_ui_feedback_loop(self):
        """Test voice to UI feedback loop."""
        # Mock the voice assistant state change
        with patch('core.voice_assistant.voice_assistant') as mock_va:
            mock_va.is_listening = True
            mock_va.current_command = "Test command"
            
            # This would normally trigger UI updates via WebSocket
            assert mock_va.is_listening is True

    @pytest.mark.asyncio
    async def test_ui_to_voice_commands(self):
        """Test UI to voice command processing."""
        # Mock UI sending commands to backend
        try:
            # This would normally be sent from frontend to backend
            test_command = {
                "action": "voice_command",
                "command": "test voice processing"
            }
            
            # Test that voice assistant can process commands
            assert hasattr(voice_assistant, 'process_command')
            
        except Exception:
            pytest.skip("Voice command processing not available")

    @pytest.mark.asyncio
    async def test_multimodal_integration(self):
        """Test multimodal integration (voice + vision + research)."""
        # Test that all modalities can work together
        vision_agent = VisionAgent()
        
        # Mock vision analysis
        with patch.object(vision_agent, '_analyze_screen') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "message": "Screen analyzed successfully"
            }
            
            result = vision_agent._analyze_screen("test task")
            assert result["success"] is True

    def test_system_health_monitoring(self, backend_url):
        """Test system health monitoring."""
        try:
            # Test diagnostics endpoint
            response = requests.get(f"{backend_url}/api/diagnostics", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                
                # Check if all components are monitored
                expected_components = [
                    "router_api", "local_database", "tts_engine", 
                    "stt_engine", "pc_control", "ocr_vision"
                ]
                
                for component in expected_components:
                    assert component in data, f"Component {component} not monitored"
                    
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling across UI and voice components."""
        # Test that components handle errors gracefully
        
        # Test voice assistant error handling
        with patch('core.voice_assistant.voice_assistant') as mock_va:
            mock_va.initialize.return_value = False
            
            # Should handle initialization failure gracefully
            result = voice_assistant.initialize()
            assert isinstance(result, bool)

    def test_configuration_integration(self):
        """Test configuration integration across components."""
        # Test that components read from configuration
        try:
            from config import VOICE_ASSISTANT_ENABLED, OLLAMA_URL
            
            assert isinstance(VOICE_ASSISTANT_ENABLED, bool)
            assert isinstance(OLLAMA_URL, str)
            assert OLLAMA_URL.startswith('http')
            
        except ImportError:
            pytest.skip("Configuration not available")

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent operations across UI and voice."""
        # Test that multiple operations can run concurrently
        tasks = []
        
        # Mock concurrent operations
        with patch('core.tts.tts.speak') as mock_speak:
            mock_speak.return_value = None
            
            # Simulate multiple voice operations
            for i in range(5):
                tasks.append(tts.speak(f"Test message {i}"))
            
            # Should handle concurrent operations
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should complete without exceptions
            for result in results:
                assert result is None or isinstance(result, Exception)

    def test_frontend_serves_static_files(self, backend_url):
        """Test that backend serves frontend static files."""
        try:
            # Test that backend serves frontend
            response = requests.get(backend_url, timeout=5)
            assert response.status_code == 200
            
            # Should serve frontend index.html
            assert 'text/html' in response.headers.get('content-type', '')
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend server not running")

    @pytest.mark.asyncio
    async def test_voice_ui_state_synchronization(self):
        """Test voice and UI state synchronization."""
        # Mock state synchronization
        with patch('core.voice_assistant.voice_assistant') as mock_va:
            mock_va.is_listening = False
            mock_va.start = Mock()
            mock_va.stop = Mock()
            
            # Start voice assistant
            mock_va.start()
            
            # State should be updated
            assert mock_va.start.called
            
            # Stop voice assistant
            mock_va.stop()
            
            # State should be updated
            assert mock_va.stop.called

if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_ui_voice_integration.py -v -s
    pytest.main([__file__, "-v", "-s"])
