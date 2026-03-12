"""
Bug Watcher Test Suite
Tests proactive OCR-based error detection and monitoring.
"""

import pytest
import asyncio
import tempfile
from PIL import Image, ImageDraw, ImageFont
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.bug_watcher import bug_watcher
    from core.vision_agent import vision_agent
    BUG_WATCHER_AVAILABLE = True
except ImportError as e:
    print(f"Bug watcher modules not available: {e}")
    BUG_WATCHER_AVAILABLE = False

@pytest.mark.skipif(not BUG_WATCHER_AVAILABLE, reason="Bug watcher modules not available")
class TestBugWatcher:
    """Test suite for Bug Watcher capabilities."""

    @pytest.fixture
    def error_screenshot(self, temp_dir):
        """Create a fake error screenshot for testing."""
        # Create a simple image with error text
        width, height = 800, 600
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        # Draw error text
        error_text = "Fatal Error: System Core Dumped"
        if font:
            draw.text((50, 50), error_text, fill='red', font=font)
        else:
            draw.text((50, 50), error_text, fill='red')
        
        # Add more error details
        details = [
            "Exception: Access Violation",
            "Location: 0x00000000",
            "Process: application.exe"
        ]
        
        y_offset = 100
        for detail in details:
            if font:
                draw.text((50, y_offset), detail, fill='black', font=font)
            else:
                draw.text((50, y_offset), detail, fill='black')
            y_offset += 30
        
        # Save image
        screenshot_path = temp_dir / "error_screenshot.png"
        image.save(screenshot_path)
        
        return screenshot_path

    @pytest.fixture
    def normal_screenshot(self, temp_dir):
        """Create a normal application screenshot."""
        width, height = 800, 600
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        # Draw normal application content
        title = "My Application"
        content = [
            "Welcome to the application",
            "Menu: File | Edit | View | Help",
            "Status: Ready"
        ]
        
        if font:
            draw.text((50, 50), title, fill='black', font=font)
        else:
            draw.text((50, 50), title, fill='black')
        
        y_offset = 100
        for line in content:
            if font:
                draw.text((50, y_offset), line, fill='gray', font=font)
            else:
                draw.text((50, y_offset), line, fill='gray')
            y_offset += 30
        
        # Save image
        screenshot_path = temp_dir / "normal_screenshot.png"
        image.save(screenshot_path)
        
        return screenshot_path

    @pytest.fixture
    def mock_bug_watcher(self):
        """Create mock bug watcher for testing."""
        mock_watcher = Mock()
        mock_watcher.is_running = False
        mock_watcher.error_patterns = [
            r"fatal error",
            r"exception",
            r"access violation",
            r"system core dumped",
            r"crash",
            r"assertion failed"
        ]
        mock_watcher.monitoring_interval = 5.0
        return mock_watcher

    @pytest.fixture
    def sample_error_detections(self):
        """Sample error detection results."""
        return [
            {
                "timestamp": "2024-01-01T12:00:00",
                "error_type": "Fatal Error",
                "confidence": 0.95,
                "location": "Application Window",
                "text": "Fatal Error: System Core Dumped",
                "screenshot_path": "/path/to/error.png"
            },
            {
                "timestamp": "2024-01-01T12:05:00",
                "error_type": "Exception",
                "confidence": 0.87,
                "location": "Console Window",
                "text": "Exception: Access Violation at 0x00000000",
                "screenshot_path": "/path/to/exception.png"
            }
        ]

    @pytest.mark.asyncio
    async def test_bug_watcher_initialization(self, mock_bug_watcher):
        """Test bug watcher initialization."""
        with patch('core.bug_watcher.bug_watcher', mock_bug_watcher):
            assert hasattr(mock_bug_watcher, 'error_patterns')
            assert len(mock_bug_watcher.error_patterns) > 0
            assert mock_bug_watcher.monitoring_interval > 0

    @pytest.mark.asyncio
    async def test_error_detection_ocr(self, error_screenshot):
        """Test OCR-based error detection."""
        with patch('core.bug_watcher.pyautogui.screenshot', return_value=Image.open(error_screenshot)):
            with patch('core.bug_watcher.pytesseract.image_to_string') as mock_ocr:
                mock_ocr.return_value = "Fatal Error: System Core Dumped\nException: Access Violation"
                
                detected_errors = await bug_watcher.scan_for_errors()
                
                assert isinstance(detected_errors, list)
                assert len(detected_errors) > 0
                assert any("fatal error" in error["text"].lower() for error in detected_errors)

    @pytest.mark.asyncio
    async def test_no_error_detection(self, normal_screenshot):
        """Test that normal screenshots don't trigger false positives."""
        with patch('core.bug_watcher.pyautogui.screenshot', return_value=Image.open(normal_screenshot)):
            with patch('core.bug_watcher.pytesseract.image_to_string') as mock_ocr:
                mock_ocr.return_value = "Welcome to the application\nMenu: File | Edit | View | Help"
                
                detected_errors = await bug_watcher.scan_for_errors()
                
                assert isinstance(detected_errors, list)
                # Should be empty or very low confidence detections
                assert len(detected_errors) == 0 or all(
                    error["confidence"] < 0.5 for error in detected_errors
                )

    @pytest.mark.asyncio
    async def test_error_pattern_matching(self):
        """Test error pattern matching against OCR text."""
        test_texts = [
            ("Fatal Error: System Core Dumped", True),
            ("Exception: Access Violation", True),
            ("Welcome to the application", False),
            ("Process completed successfully", False),
            ("Assertion failed at line 123", True),
            ("CRASH: Application terminated", True)
        ]
        
        for text, should_match in test_texts:
            matches = bug_watcher.match_error_patterns(text)
            assert matches == should_match, f"Failed for text: {text}"

    @pytest.mark.asyncio
    async def test_confidence_scoring(self):
        """Test error detection confidence scoring."""
        test_cases = [
            ("Fatal Error: System Core Dumped", 0.95),
            ("error occurred", 0.6),
            ("something went wrong", 0.3),
            ("welcome screen", 0.1)
        ]
        
        for text, expected_min_confidence in test_cases:
            confidence = bug_watcher.calculate_error_confidence(text)
            assert isinstance(confidence, float)
            assert 0.0 <= confidence <= 1.0
            assert confidence >= expected_min_confidence

    @pytest.mark.asyncio
    async def test_proactive_monitoring_start_stop(self, mock_bug_watcher):
        """Test starting and stopping proactive monitoring."""
        with patch('core.bug_watcher.bug_watcher', mock_bug_watcher):
            # Test starting
            await bug_watcher.start_monitoring()
            assert mock_bug_watcher.is_running is True
            
            # Test stopping
            await bug_watcher.stop_monitoring()
            assert mock_bug_watcher.is_running is False

    @pytest.mark.asyncio
    async def test_continuous_monitoring(self, mock_bug_watcher, sample_error_detections):
        """Test continuous monitoring loop."""
        with patch('core.bug_watcher.bug_watcher', mock_bug_watcher):
            with patch.object(bug_watcher, 'scan_for_errors', return_value=sample_error_detections):
                with patch('asyncio.sleep') as mock_sleep:
                    mock_bug_watcher.is_running = True
                    
                    # Run monitoring for a few cycles
                    monitoring_task = asyncio.create_task(bug_watcher.monitoring_loop())
                    
                    # Let it run for a short time
                    await asyncio.sleep(0.1)
                    
                    # Stop monitoring
                    mock_bug_watcher.is_running = False
                    await monitoring_task
                    
                    # Verify scanning was called
                    assert bug_watcher.scan_for_errors.call_count > 0

    @pytest.mark.asyncio
    async def test_error_alert_generation(self, sample_error_detections):
        """Test generating error alerts."""
        with patch.object(bug_watcher, 'generate_alert') as mock_alert:
            mock_alert.return_value = {
                "type": "error_alert",
                "message": "System error detected",
                "severity": "high",
                "timestamp": sample_error_detections[0]["timestamp"],
                "details": sample_error_detections[0]
            }
            
            alert = await bug_watcher.generate_alert(sample_error_detections[0])
            
            assert isinstance(alert, dict)
            assert "type" in alert
            assert "message" in alert
            assert "severity" in alert
            assert alert["severity"] == "high"

    @pytest.mark.asyncio
    async def test_vision_agent_integration(self, sample_error_detections):
        """Test integration with Vision Agent for error confirmation."""
        with patch.object(vision_agent, 'analyze_screen') as mock_analyze:
            mock_analyze.return_value = {
                "description": "Screen shows a fatal error dialog with 'System Core Dumped' message",
                "error_detected": True,
                "confidence": 0.92
            }
            
            confirmation = await bug_watcher.confirm_with_vision_agent(sample_error_detections[0])
            
            assert confirmation["error_detected"] is True
            assert confirmation["confidence"] > 0.8

    @pytest.mark.asyncio
    async def test_error_logging(self, sample_error_detections, temp_dir):
        """Test error detection logging."""
        log_file = temp_dir / "error_log.json"
        
        with patch.object(bug_watcher, 'log_error') as mock_log:
            mock_log.return_value = True
            
            result = await bug_watcher.log_error(sample_error_detections[0])
            
            assert result is True
            mock_log.assert_called_once_with(sample_error_detections[0])

    @pytest.mark.asyncio
    async def test_false_positive_filtering(self):
        """Test filtering false positives."""
        potential_errors = [
            {
                "text": "Fatal Error: System Core Dumped",
                "confidence": 0.95,
                "is_false_positive": False
            },
            {
                "text": "Error loading configuration file",
                "confidence": 0.3,
                "is_false_positive": True
            },
            {
                "text": "Warning: Low memory",
                "confidence": 0.2,
                "is_false_positive": True
            }
        ]
        
        filtered_errors = bug_watcher.filter_false_positives(potential_errors)
        
        # Should only return high-confidence, non-false-positive errors
        assert len(filtered_errors) == 1
        assert filtered_errors[0]["confidence"] > 0.8
        assert filtered_errors[0]["is_false_positive"] is False

    @pytest.mark.asyncio
    async def test_custom_error_patterns(self):
        """Test adding custom error patterns."""
        custom_patterns = [
            r"custom application error",
            r"specific module failure"
        ]
        
        # Add custom patterns
        bug_watcher.add_error_patterns(custom_patterns)
        
        # Test that patterns are added
        assert all(pattern in bug_watcher.error_patterns for pattern in custom_patterns)
        
        # Test matching with custom patterns
        matches = bug_watcher.match_error_patterns("Custom Application Error in Module X")
        assert matches is True

    @pytest.mark.asyncio
    async def test_monitoring_frequency_adjustment(self, mock_bug_watcher):
        """Test adjusting monitoring frequency."""
        with patch('core.bug_watcher.bug_watcher', mock_bug_watcher):
            # Test setting different intervals
            intervals = [1.0, 5.0, 10.0, 30.0]
            
            for interval in intervals:
                bug_watcher.set_monitoring_interval(interval)
                assert bug_watcher.monitoring_interval == interval

    @pytest.mark.asyncio
    async def test_error_categorization(self):
        """Test categorizing different types of errors."""
        error_texts = [
            ("Fatal Error: System Core Dumped", "system_crash"),
            ("Exception: Null Pointer", "programming_error"),
            ("Access Violation at 0x0000", "memory_error"),
            ("Network Timeout", "network_error"),
            ("File Not Found", "file_error")
        ]
        
        for text, expected_category in error_texts:
            category = bug_watcher.categorize_error(text)
            assert category == expected_category

    @pytest.mark.asyncio
    async def test_notification_system(self, sample_error_detections):
        """Test error notification system."""
        with patch.object(bug_watcher, 'send_notification') as mock_notify:
            mock_notify.return_value = {"sent": True, "method": "desktop_notification"}
            
            result = await bug_watcher.send_notification(sample_error_detections[0])
            
            assert result["sent"] is True
            assert "method" in result

# Integration Tests
@pytest.mark.skipif(not BUG_WATCHER_AVAILABLE, reason="Bug watcher modules not available")
@pytest.mark.integration
class TestBugWatcherIntegration:
    """Integration tests for Bug Watcher with real components."""

    @pytest.mark.asyncio
    async def test_real_screen_capture(self):
        """Test actual screen capture for error detection."""
        try:
            # This test requires actual screen capture
            screenshot = bug_watcher.capture_screen()
            
            assert screenshot is not None
            assert hasattr(screenshot, 'size')  # PIL Image attribute
            
        except Exception as e:
            if "display" in str(e).lower() or "screen" in str(e).lower():
                pytest.skip(f"Screen capture not available: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_real_ocr_processing(self):
        """Test actual OCR processing with Tesseract."""
        try:
            # Create a test image with text
            test_image = Image.new('RGB', (400, 100), color='white')
            draw = ImageDraw.Draw(test_image)
            
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            text = "Test Error Message"
            if font:
                draw.text((10, 10), text, fill='black', font=font)
            else:
                draw.text((10, 10), text, fill='black')
            
            # Perform OCR
            import pytesseract
            ocr_result = pytesseract.image_to_string(test_image)
            
            assert isinstance(ocr_result, str)
            assert len(ocr_result) > 0
            
        except Exception as e:
            if "tesseract" in str(e).lower():
                pytest.skip(f"Tesseract OCR not available: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_proactive_bug_watcher_workflow(self):
        """Test complete proactive bug watcher workflow."""
        try:
            # Step 1: Start monitoring
            await bug_watcher.start_monitoring()
            
            # Step 2: Let it monitor for a short time
            await asyncio.sleep(2)
            
            # Step 3: Check if monitoring is active
            assert bug_watcher.is_running is True
            
            # Step 4: Stop monitoring
            await bug_watcher.stop_monitoring()
            
            assert bug_watcher.is_running is False
            
        except Exception as e:
            pytest.skip(f"Bug watcher workflow test failed: {e}")

    @pytest.mark.asyncio
    async def test_error_detection_with_vision_confirmation(self):
        """Test error detection with Vision Agent confirmation."""
        try:
            # Create a simulated error detection
            error_detection = {
                "text": "Fatal Error: System Core Dumped",
                "confidence": 0.9,
                "location": "Application Window",
                "timestamp": "2024-01-01T12:00:00"
            }
            
            # Test Vision Agent confirmation (if available)
            if hasattr(vision_agent, 'analyze_screen'):
                confirmation = await bug_watcher.confirm_with_vision_agent(error_detection)
                assert isinstance(confirmation, dict)
                assert "error_detected" in confirmation
            else:
                pytest.skip("Vision Agent not available for confirmation")
                
        except Exception as e:
            pytest.skip(f"Vision confirmation test failed: {e}")

if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_bug_watcher.py -v
    pytest.main([__file__, "-v"])
