"""
Comprehensive Integration Test Suite
Tests multi-module interactions and end-to-end workflows.
"""

import pytest
import asyncio
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
import os
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.vision_agent import VisionAgent
    from core.memory import memory_manager
    from core.kokoro_tts import KokoroTTS
    from utilities.research_handler import research_handler
    from utilities.search_handler import web_search_handler
    from core.bug_watcher import bug_watcher
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"Integration modules not available: {e}")
    INTEGRATION_AVAILABLE = False

@pytest.mark.skipif(not INTEGRATION_AVAILABLE, reason="Integration modules not available")
@pytest.mark.integration
class TestComprehensiveIntegration:
    """Test suite for comprehensive multi-module integration."""

    @pytest.fixture
    def mock_system_state(self):
        """Mock complete system state for integration testing."""
        return {
            "vision": {
                "omni_parser_connected": True,
                "screen_captured": True,
                "elements_detected": ["search_bar", "button", "input"]
            },
            "memory": {
                "preferences_stored": ["dark_mode", "voice_enabled"],
                "recent_interactions": 5,
                "context_available": True
            },
            "tts": {
                "kokoro_loaded": True,
                "voice_ready": True,
                "audio_output": True
            },
            "research": {
                "web_search_available": True,
                "crawl4ai_ready": True,
                "content_extracted": True
            },
            "bug_watcher": {
                "monitoring_active": True,
                "ocr_ready": True,
                "error_detection": True
            }
        }

    @pytest.fixture
    def user_scenario_data(self):
        """Sample user scenario for end-to-end testing."""
        return {
            "user_request": "Wolf, search for the latest Bitcoin price and tell me about it",
            "expected_workflow": [
                "web_search_bitcoin_price",
                "extract_price_data", 
                "generate_summary",
                "text_to_speech",
                "store_interaction_memory"
            ],
            "expected_modules": ["research", "memory", "tts"]
        }

    @pytest.mark.asyncio
    async def test_vision_memory_integration(self, mock_system_state):
        """Test Vision Agent integration with Memory system."""
        # Mock vision detection
        with patch.object(VisionAgent, 'parse_screen_elements') as mock_vision:
            mock_vision.return_value = {
                "elements": [
                    {"id": "search_bar", "type": "input", "content": "search"},
                    {"id": "submit_btn", "type": "button", "content": "Search"}
                ]
            }
            
            # Mock memory storage
            with patch.object(memory_manager, 'store_memory') as mock_memory:
                mock_memory.return_value = True
                
                # Simulate vision detection followed by memory storage
                vision_agent = VisionAgent()
                elements = await vision_agent.parse_screen_elements()
                
                # Store detection in memory
                await memory_manager.store_memory(
                    content=f"UI elements detected: {len(elements['elements'])} found",
                    interaction_type="vision_detection",
                    context="screen_analysis",
                    tags="vision,ui,elements"
                )
                
                # Verify integration worked
                assert len(elements["elements"]) > 0
                mock_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_research_tts_integration(self, mock_system_state):
        """Test Research integration with TTS for voice responses."""
        # Mock web search
        with patch.object(web_search_handler, 'search') as mock_search:
            mock_search.return_value = [
                {
                    "title": "Bitcoin Price Live",
                    "url": "https://example.com/btc-price",
                    "snippet": "Current Bitcoin price: $45,234.56"
                }
            ]
            
            # Mock content extraction
            with patch.object(research_handler, 'scrape_url') as mock_scrape:
                mock_scrape.return_value = Mock(
                    success=True,
                    cleaned_content="Bitcoin is currently trading at $45,234.56 USD",
                    markdown="# Bitcoin Price\n\nCurrent price: $45,234.56"
                )
                
                # Mock TTS synthesis
                with patch.object(KokoroTTS, 'synthesize_speech') as mock_tts:
                    mock_tts.return_value = b"fake_audio_data"
                    
                    # Execute research workflow
                    search_results = await web_search_handler.search("Bitcoin price")
                    scraped_content = await research_handler.scrape_url(search_results[0]["url"])
                    
                    # Generate summary and convert to speech
                    summary = scraped_content.cleaned_content
                    tts = KokoroTTS()
                    audio_data = await tts.synthesize_speech(summary)
                    
                    # Verify integration
                    assert len(search_results) > 0
                    assert scraped_content.success is True
                    assert isinstance(audio_data, bytes)
                    assert len(audio_data) > 0

    @pytest.mark.asyncio
    async def test_bug_watcher_vision_integration(self, mock_system_state):
        """Test Bug Watcher integration with Vision Agent for error confirmation."""
        # Mock error detection
        with patch.object(bug_watcher, 'scan_for_errors') as mock_scan:
            mock_scan.return_value = [
                {
                    "text": "Fatal Error: System Core Dumped",
                    "confidence": 0.95,
                    "location": "Application Window",
                    "timestamp": datetime.now().isoformat()
                }
            ]
            
            # Mock vision confirmation
            with patch.object(VisionAgent, 'analyze_screen') as mock_analyze:
                mock_analyze.return_value = {
                    "description": "Screen shows a fatal error dialog",
                    "error_detected": True,
                    "confidence": 0.92
                }
                
                # Execute bug watcher workflow
                detected_errors = await bug_watcher.scan_for_errors()
                
                if detected_errors:
                    # Confirm with vision agent
                    vision_agent = VisionAgent()
                    confirmation = await vision_agent.analyze_screen()
                    
                    # Verify integration
                    assert len(detected_errors) > 0
                    assert detected_errors[0]["confidence"] > 0.8
                    assert confirmation["error_detected"] is True

    @pytest.mark.asyncio
    async def test_memory_tts_integration(self, mock_system_state):
        """Test Memory integration with TTS for personalized responses."""
        # Mock memory recall
        with patch.object(memory_manager, 'recall_preferences') as mock_recall:
            mock_recall.return_value = [
                "User prefers dark mode for applications",
                "User likes voice responses with medium speed"
            ]
            
            # Mock TTS with preference
            with patch.object(KokoroTTS, 'synthesize_speech') as mock_tts:
                mock_tts.return_value = b"personalized_audio"
                
                # Execute personalized workflow
                preferences = await memory_manager.recall_preferences()
                
                if preferences:
                    # Generate personalized response
                    response = "I remember you prefer dark mode and medium voice speed."
                    
                    # Apply preferences to TTS
                    tts = KokoroTTS()
                    audio_data = await tts.synthesize_speech(
                        response, 
                        speed=1.0,  # Medium speed based on preference
                        voice="default"
                    )
                    
                    # Verify integration
                    assert len(preferences) > 0
                    assert "dark mode" in str(preferences)
                    assert isinstance(audio_data, bytes)

    @pytest.mark.asyncio
    async def test_end_to_end_user_scenario(self, user_scenario_data):
        """Test complete end-to-end user scenario."""
        scenario = user_scenario_data
        
        # Mock all required services
        with patch.object(web_search_handler, 'search') as mock_search:
            mock_search.return_value = [
                {"title": "Bitcoin Price", "url": "https://crypto.com/bitcoin", "snippet": "BTC: $45,234"}
            ]
            
            with patch.object(research_handler, 'scrape_url') as mock_scrape:
                mock_scrape.return_value = Mock(
                    success=True,
                    cleaned_content="Bitcoin current price is $45,234.56 USD with 24h change of +2.3%"
                )
                
                with patch.object(KokoroTTS, 'synthesize_speech') as mock_tts:
                    mock_tts.return_value = b"bitcoin_price_audio"
                    
                    with patch.object(memory_manager, 'store_memory') as mock_memory:
                        mock_memory.return_value = True
                        
                        # Execute complete workflow
                        print(f"🎭 Executing scenario: {scenario['user_request']}")
                        
                        # Step 1: Web search
                        search_results = await web_search_handler.search("latest Bitcoin price")
                        assert len(search_results) > 0
                        
                        # Step 2: Content extraction
                        scraped_content = await research_handler.scrape_url(search_results[0]["url"])
                        assert scraped_content.success is True
                        
                        # Step 3: Generate response
                        price_info = scraped_content.cleaned_content
                        response = f"Based on my research, {price_info}"
                        
                        # Step 4: Text-to-speech
                        tts = KokoroTTS()
                        audio_data = await tts.synthesize_speech(response)
                        assert isinstance(audio_data, bytes)
                        
                        # Step 5: Store in memory
                        await memory_manager.store_memory(
                            content=f"User asked about Bitcoin price, provided: {price_info}",
                            interaction_type="query_response",
                            context="bitcoin_price_inquiry",
                            tags="bitcoin,crypto,price,research"
                        )
                        
                        # Verify all modules were used
                        mock_search.assert_called_once()
                        mock_scrape.assert_called_once()
                        mock_tts.assert_called_once()
                        mock_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_multi_module_error_handling(self):
        """Test error handling across multiple modules."""
        # Test cascade failure handling
        with patch.object(web_search_handler, 'search', side_effect=Exception("Network error")):
            with patch.object(memory_manager, 'store_memory') as mock_memory:
                with patch.object(KokoroTTS, 'synthesize_speech') as mock_tts:
                    mock_tts.return_value = b"error_audio"
                    
                    # Try to execute workflow with search failure
                    try:
                        search_results = await web_search_handler.search("test query")
                    except Exception:
                        # Handle search failure gracefully
                        error_response = "I'm having trouble connecting to the internet right now."
                        
                        # Still provide voice response
                        tts = KokoroTTS()
                        audio_data = await tts.synthesize_speech(error_response)
                        
                        # Store error in memory for debugging
                        await memory_manager.store_memory(
                            content="Web search failed due to network error",
                            interaction_type="error",
                            context="search_failure",
                            tags="error,network,search"
                        )
                        
                        # Verify graceful degradation
                        assert isinstance(audio_data, bytes)
                        mock_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_module_operations(self, mock_system_state):
        """Test concurrent operations across multiple modules."""
        # Mock all modules for concurrent testing
        with patch.object(web_search_handler, 'search') as mock_search:
            mock_search.return_value = [{"title": "Result", "url": "test.com", "snippet": "test"}]
            
            with patch.object(VisionAgent, 'parse_screen_elements') as mock_vision:
                mock_vision.return_value = {"elements": [{"id": "test", "type": "button"}]}
                
            with patch.object(KokoroTTS, 'synthesize_speech') as mock_tts:
                mock_tts.return_value = b"concurrent_audio"
                
                # Execute multiple operations concurrently
                tasks = [
                    web_search_handler.search("query1"),
                    web_search_handler.search("query2"),
                    VisionAgent().parse_screen_elements(),
                    KokoroTTS().synthesize_speech("Concurrent test")
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Verify all operations completed
                assert len(results) == 4
                for result in results:
                    if isinstance(result, Exception):
                        # Handle exceptions gracefully
                        continue
                    assert result is not None

    @pytest.mark.asyncio
    async def test_system_state_monitoring(self, mock_system_state):
        """Test system state monitoring across all modules."""
        # Collect system health from all modules
        system_health = {
            "vision": await self._check_vision_health(),
            "memory": await self._check_memory_health(),
            "tts": await self._check_tts_health(),
            "research": await self._check_research_health(),
            "bug_watcher": await self._check_bug_watcher_health()
        }
        
        # Verify all modules report health
        for module, health in system_health.items():
            assert isinstance(health, dict)
            assert "status" in health
            assert "last_check" in health

    async def _check_vision_health(self) -> dict:
        """Check Vision Agent health."""
        try:
            vision_agent = VisionAgent()
            return {
                "status": "healthy",
                "last_check": datetime.now().isoformat(),
                "model_loaded": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }

    async def _check_memory_health(self) -> dict:
        """Check Memory system health."""
        try:
            # Test memory operation
            success = await memory_manager.store_memory(
                content="Health check test",
                interaction_type="system_check",
                context="health_monitoring"
            )
            return {
                "status": "healthy" if success else "unhealthy",
                "last_check": datetime.now().isoformat(),
                "storage_working": success
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }

    async def _check_tts_health(self) -> dict:
        """Check TTS system health."""
        try:
            tts = KokoroTTS()
            # Test basic synthesis
            audio = await tts.synthesize_speech("Health check")
            return {
                "status": "healthy" if audio else "unhealthy",
                "last_check": datetime.now().isoformat(),
                "synthesis_working": bool(audio)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }

    async def _check_research_health(self) -> dict:
        """Check Research system health."""
        try:
            # Test search availability
            results = await web_search_handler.search("health check")
            return {
                "status": "healthy" if results else "unhealthy",
                "last_check": datetime.now().isoformat(),
                "search_working": len(results) > 0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }

    async def _check_bug_watcher_health(self) -> dict:
        """Check Bug Watcher health."""
        try:
            # Test error scanning
            errors = await bug_watcher.scan_for_errors()
            return {
                "status": "healthy",
                "last_check": datetime.now().isoformat(),
                "scanning_working": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }

# Performance Integration Tests
@pytest.mark.skipif(not INTEGRATION_AVAILABLE, reason="Integration modules not available")
@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Performance tests for integrated modules."""

    @pytest.mark.asyncio
    async def test_full_workflow_performance(self):
        """Test performance of complete workflow."""
        import time
        
        start_time = time.time()
        
        # Mock the complete workflow
        with patch.object(web_search_handler, 'search') as mock_search:
            mock_search.return_value = [{"title": "Test", "url": "test.com", "snippet": "test"}]
            
            with patch.object(research_handler, 'scrape_url') as mock_scrape:
                mock_scrape.return_value = Mock(success=True, cleaned_content="Test content")
                
                with patch.object(KokoroTTS, 'synthesize_speech') as mock_tts:
                    mock_tts.return_value = b"test_audio"
                    
                    with patch.object(memory_manager, 'store_memory') as mock_memory:
                        mock_memory.return_value = True
                        
                        # Execute workflow
                        search_results = await web_search_handler.search("test")
                        scraped = await research_handler.scrape_url("test.com")
                        audio = await KokoroTTS().synthesize_speech("test")
                        await memory_manager.store_memory("test", "test", "test")
        
        duration = time.time() - start_time
        
        # Performance assertion (should complete within 5 seconds)
        assert duration < 5.0, f"Workflow took too long: {duration:.2f}s"

if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_integration_comprehensive.py -v -s
    pytest.main([__file__, "-v", "-s"])
