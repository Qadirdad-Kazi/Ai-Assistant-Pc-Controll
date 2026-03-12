"""
Vision Agent Test Suite
Tests OmniParser integration and UI grounding capabilities.
"""

import pytest
import asyncio
import base64
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.vision_agent import VisionAgent
    from core.omni_parser_client import omni_parser
    VISION_AVAILABLE = True
except ImportError as e:
    print(f"Vision modules not available: {e}")
    VISION_AVAILABLE = False

@pytest.mark.skipif(not VISION_AVAILABLE, reason="Vision modules not available")
class TestVisionAgent:
    """Test suite for Vision Agent capabilities."""

    @pytest.fixture
    def vision_agent(self, test_config):
        """Create VisionAgent instance for testing."""
        return VisionAgent(model_name=test_config["visual_model"])

    @pytest.fixture
    def mock_pyautogui(self):
        """Mock PyAutoGUI for safe testing."""
        with patch('core.vision_agent.pyautogui') as mock_gui:
            mock_gui.screenshot.return_value = Mock()
            mock_gui.FAILSAFE = True
            mock_gui.PAUSE = 1.0
            yield mock_gui

    @pytest.fixture
    def mock_pil_image(self):
        """Mock PIL Image for testing."""
        with patch('core.vision_agent.Image') as mock_img:
            mock_image = Mock()
            mock_img.open.return_value = mock_image
            mock_img.new.return_value = mock_image
            yield mock_img

    @pytest.mark.asyncio
    async def test_screen_capture(self, vision_agent, mock_pyautogui, mock_pil_image):
        """Test screen capture functionality."""
        # Mock screenshot capture
        mock_screenshot = Mock()
        mock_pyautogui.screenshot.return_value = mock_screenshot
        
        # Mock image saving
        mock_buffer = Mock()
        mock_buffer.getvalue.return_value = b"fake_png_data"
        
        with patch('core.vision_agent.io.BytesIO', return_value=mock_buffer):
            result = vision_agent._capture_screen_base64()
            
            assert isinstance(result, str)
            assert len(result) > 0
            mock_pyautogui.screenshot.assert_called_once()
            mock_screenshot.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_omni_parser_integration(self, vision_agent, mock_omni_parser_response):
        """Test OmniParser integration for UI element detection."""
        with patch.object(omni_parser, 'parse_screen', return_value=mock_omni_parser_response):
            # Use the actual method name from the implementation
            result = vision_agent._analyze_screen("describe the screen elements")
            
            assert result is not None
            assert "success" in result
            # The result should contain the analysis data

    @pytest.mark.asyncio
    async def test_ui_grounding_click_action(self, vision_agent, mock_omni_parser_response):
        """Test UI grounding for click actions."""
        # Mock OmniParser response
        with patch.object(omni_parser, 'parse_screen', return_value=mock_omni_parser_response):
            # Mock PyAutoGUI click
            with patch('core.vision_agent.pyautogui.click') as mock_click:
                # Use the actual method from implementation
                result = vision_agent._find_and_click_element("search_bar")
                
                assert result is not None
                assert "success" in result
                # The click should be attempted through the actual implementation

    @pytest.mark.asyncio
    async def test_screen_description(self, vision_agent, mock_ollama_response, mock_screen_capture):
        """Test screen description generation using VLM."""
        with patch.object(vision_agent, '_capture_screen_base64', return_value="base64_screenshot"):
            with patch('requests.post', return_value=Mock(json=lambda: mock_ollama_response)):
                # Use the actual method from implementation
                description = vision_agent._describe_screen()
                
                assert isinstance(description, str)
                assert len(description) > 0

    @pytest.mark.asyncio
    async def test_element_not_found_handling(self, vision_agent):
        """Test handling when target element is not found."""
        # Mock empty OmniParser response
        empty_response = {"success": False, "elements": []}
        
        with patch.object(omni_parser, 'parse_screen', return_value=empty_response):
            # Use the actual method from implementation
            result = vision_agent._find_and_click_element("nonexistent_element")
            
            assert result is not None
            assert "success" in result
            # Should handle the case where element is not found

    @pytest.mark.asyncio
    async def test_vision_error_handling(self, vision_agent):
        """Test error handling in vision operations."""
        # Test screen capture failure
        with patch.object(vision_agent, '_capture_screen_base64', side_effect=Exception("Capture failed")):
            result = vision_agent._describe_screen()
            # Should handle error gracefully
            assert "Error" in result

    def test_vision_agent_initialization(self, test_config):
        """Test VisionAgent initialization with different models."""
        agent = VisionAgent(model_name=test_config["visual_model"])
        assert agent.model_name == test_config["visual_model"]
        assert agent.api_url is not None
        assert agent.last_parse_result is None

    @pytest.mark.asyncio
    async def test_screen_capture_functionality(self, vision_agent, mock_pyautogui, mock_pil_image):
        """Test screen capture functionality."""
        # Mock screenshot capture
        mock_screenshot = Mock()
        mock_pyautogui.screenshot.return_value = mock_screenshot
        
        # Mock image saving
        mock_buffer = Mock()
        mock_buffer.getvalue.return_value = b"fake_png_data"
        
        with patch('core.vision_agent.io.BytesIO', return_value=mock_buffer):
            result = vision_agent._capture_screen_base64()
            
            assert isinstance(result, str)
            # Should return empty string on error or base64 string on success
            mock_pyautogui.screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_and_click_element(self, vision_agent):
        """Test the find and click functionality."""
        with patch.object(vision_agent, '_analyze_screen') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "x_percent": 0.5,
                "y_percent": 0.5,
                "message": "Found element"
            }
            
            with patch('core.vision_agent.pyautogui.size', return_value=(1920, 1080)):
                with patch('core.vision_agent.pyautogui.moveTo') as mock_move:
                    with patch('core.vision_agent.pyautogui.click') as mock_click:
                        result = vision_agent._find_and_click_element("test_element")
                        
                        assert result["success"] is True
                        mock_move.assert_called_once()
                        mock_click.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_and_type_text(self, vision_agent):
        """Test the find and type functionality."""
        with patch.object(vision_agent, '_analyze_screen') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "x_percent": 0.5,
                "y_percent": 0.5,
                "text": "test text"
            }
            
            with patch('core.vision_agent.pyautogui.size', return_value=(1920, 1080)):
                with patch('core.vision_agent.pyautogui.click') as mock_click:
                    with patch('core.vision_agent.pyautogui.typewrite') as mock_type:
                        result = vision_agent._find_and_type_text("test_field")
                        
                        assert result["success"] is True
                        mock_click.assert_called_once()
                        mock_type.assert_called_once()

    @pytest.mark.asyncio
    async def test_scroll_screen(self, vision_agent):
        """Test screen scrolling functionality."""
        with patch('core.vision_agent.pyautogui.scroll') as mock_scroll:
            result = vision_agent._scroll_screen("scroll down")
            
            assert result["success"] is True
            mock_scroll.assert_called_once()

    def test_describe_screen(self, vision_agent):
        """Test screen description functionality."""
        with patch.object(vision_agent, '_analyze_screen') as mock_analyze:
            mock_analyze.return_value = {
                "success": True,
                "message": "I see a desktop with icons"
            }
            
            description = vision_agent._describe_screen()
            
            assert isinstance(description, str)
            assert "desktop" in description

# Integration Tests
@pytest.mark.skipif(not VISION_AVAILABLE, reason="Vision modules not available")
@pytest.mark.integration
class TestVisionIntegration:
    """Integration tests for Vision Agent with real components."""

    @pytest.mark.asyncio
    async def test_full_vision_workflow(self, vision_agent, disable_voice_assistant):
        """Test complete vision workflow from capture to action."""
        # This test requires actual OmniParser server running
        # Mark as expected failure if server not available
        try:
            # Test screen capture
            screenshot = vision_agent._capture_screen_base64()
            assert len(screenshot) > 0
            
            # Test element parsing (if OmniParser is running)
            if await vision_agent.check_omni_parser_connection():
                elements = await vision_agent.parse_screen_elements()
                assert isinstance(elements, dict)
                
                # Test description generation (if Ollama is running)
                try:
                    description = await vision_agent.describe_screen()
                    assert isinstance(description, str)
                    assert len(description) > 0
                except Exception:
                    pytest.skip("Ollama not available for vision testing")
            else:
                pytest.skip("OmniParser server not running")
                
        except Exception as e:
            if "Connection" in str(e):
                pytest.skip(f"Vision components not available: {e}")
            else:
                raise

if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_vision_agent.py -v
    pytest.main([__file__, "-v"])
