"""
Performance and Stress Test Suite
Tests system performance under various load conditions.
"""

import pytest
import asyncio
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
import os
import gc
from datetime import datetime, timedelta

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
    PERFORMANCE_AVAILABLE = True
except ImportError as e:
    print(f"Performance modules not available: {e}")
    PERFORMANCE_AVAILABLE = False

@pytest.mark.skipif(not PERFORMANCE_AVAILABLE, reason="Performance modules not available")
@pytest.mark.slow
class TestPerformanceStress:
    """Performance and stress testing suite."""

    @pytest.fixture
    def performance_monitor(self):
        """Monitor system performance during tests."""
        class PerformanceMonitor:
            def __init__(self):
                self.start_time = None
                self.end_time = None
                self.peak_memory = 0
                self.peak_cpu = 0
                self.monitoring = False
                self.monitor_thread = None
            
            def start_monitoring(self):
                """Start performance monitoring."""
                self.start_time = time.time()
                self.monitoring = True
                self.monitor_thread = threading.Thread(target=self._monitor_loop)
                self.monitor_thread.daemon = True
                self.monitor_thread.start()
            
            def stop_monitoring(self):
                """Stop performance monitoring."""
                self.monitoring = False
                self.end_time = time.time()
                if self.monitor_thread:
                    self.monitor_thread.join(timeout=1)
            
            def _monitor_loop(self):
                """Monitor system resources."""
                while self.monitoring:
                    try:
                        # Memory usage
                        memory = psutil.virtual_memory()
                        self.peak_memory = max(self.peak_memory, memory.percent)
                        
                        # CPU usage
                        cpu = psutil.cpu_percent(interval=0.1)
                        self.peak_cpu = max(self.peak_cpu, cpu)
                        
                        time.sleep(0.1)
                    except Exception:
                        break
            
            def get_metrics(self):
                """Get performance metrics."""
                duration = (self.end_time or time.time()) - (self.start_time or time.time())
                return {
                    "duration": duration,
                    "peak_memory_percent": self.peak_memory,
                    "peak_cpu_percent": self.peak_cpu,
                    "memory_efficiency": "good" if self.peak_memory < 70 else "moderate" if self.peak_memory < 85 else "poor",
                    "cpu_efficiency": "good" if self.peak_cpu < 50 else "moderate" if self.peak_cpu < 75 else "poor"
                }
        
        return PerformanceMonitor()

    @pytest.mark.asyncio
    async def test_vision_agent_performance(self, performance_monitor):
        """Test Vision Agent performance under load."""
        print("🔍 Testing Vision Agent performance...")
        
        # Mock vision operations for consistent testing
        with patch.object(VisionAgent, 'parse_screen_elements') as mock_parse:
            mock_parse.return_value = {
                "elements": [{"id": f"element_{i}", "type": "button", "content": f"Button {i}"} for i in range(10)]
            }
            
            with patch.object(VisionAgent, '_capture_screen_base64') as mock_capture:
                mock_capture.return_value = "fake_screenshot_data"
                
                performance_monitor.start_monitoring()
                
                # Test multiple concurrent vision operations
                vision_agent = VisionAgent()
                tasks = []
                
                # Create 50 concurrent vision tasks
                for i in range(50):
                    task = vision_agent.parse_screen_elements()
                    tasks.append(task)
                
                # Execute all tasks
                start_time = time.time()
                results = await asyncio.gather(*tasks)
                duration = time.time() - start_time
                
                performance_monitor.stop_monitoring()
                metrics = performance_monitor.get_metrics()
                
                # Performance assertions
                assert len(results) == 50
                assert duration < 10.0, f"Vision operations took too long: {duration:.2f}s"
                assert all(len(result["elements"]) == 10 for result in results)
                
                print(f"  ✅ Completed 50 vision operations in {duration:.2f}s")
                print(f"  📊 Peak memory: {metrics['peak_memory_percent']:.1f}%")
                print(f"  📊 Peak CPU: {metrics['peak_cpu_percent']:.1f}%")

    @pytest.mark.asyncio
    async def test_memory_system_stress(self, performance_monitor):
        """Test Memory system under stress."""
        print("🧠 Testing Memory system stress...")
        
        with patch.object(memory_manager, 'store_memory') as mock_store:
            mock_store.return_value = True
            
            with patch.object(memory_manager, 'search_memories') as mock_search:
                mock_search.return_value = [
                    {"content": f"Memory {i}", "timestamp": datetime.now().isoformat()}
                    for i in range(10)
                ]
                
                performance_monitor.start_monitoring()
                
                # Stress test with 1000 memory operations
                store_tasks = []
                search_tasks = []
                
                # Create storage tasks
                for i in range(500):
                    task = memory_manager.store_memory(
                        content=f"Stress test memory {i}",
                        interaction_type="stress_test",
                        context="performance_testing",
                        tags="stress,test,performance"
                    )
                    store_tasks.append(task)
                
                # Create search tasks
                for i in range(500):
                    task = memory_manager.search_memories(f"query {i}")
                    search_tasks.append(task)
                
                # Execute all tasks
                start_time = time.time()
                store_results = await asyncio.gather(*store_tasks)
                search_results = await asyncio.gather(*search_tasks)
                duration = time.time() - start_time
                
                performance_monitor.stop_monitoring()
                metrics = performance_monitor.get_metrics()
                
                # Performance assertions
                assert len(store_results) == 500
                assert len(search_results) == 500
                assert duration < 15.0, f"Memory operations took too long: {duration:.2f}s"
                assert all(store_results)  # All stores should succeed
                
                print(f"  ✅ Completed 1000 memory operations in {duration:.2f}s")
                print(f"  📊 Peak memory: {metrics['peak_memory_percent']:.1f}%")
                print(f"  📊 Peak CPU: {metrics['peak_cpu_percent']:.1f}%")

    @pytest.mark.asyncio
    async def test_tts_performance_benchmark(self, performance_monitor):
        """Test TTS performance under load."""
        print("🎵 Testing TTS performance benchmark...")
        
        with patch.object(KokoroTTS, 'synthesize_speech') as mock_synthesize:
            # Mock different audio sizes for realistic testing
            def mock_synth(text, **kwargs):
                # Simulate processing time based on text length
                processing_time = len(text) * 0.01  # 10ms per character
                time.sleep(processing_time)
                return b"mock_audio_data_" + text.encode()
            
            mock_synthesize.side_effect = mock_synth
            
            performance_monitor.start_monitoring()
            
            # Test with various text lengths
            test_texts = [
                "Short",  # 5 chars
                "Medium length text for testing",  # 30 chars
                "This is a very long text that simulates a real response from the AI assistant with multiple sentences and detailed information",  # 150 chars
                "Extremely long text that contains multiple paragraphs and detailed explanations about various topics to test the performance limits of the TTS system under heavy load conditions" * 2  # 300+ chars
            ]
            
            # Create concurrent TTS tasks
            tts = KokoroTTS()
            tasks = []
            
            # Create 100 TTS tasks with varying text lengths
            for i in range(100):
                text = test_texts[i % len(test_texts)]
                task = tts.synthesize_speech(f"Test text {i}: {text}")
                tasks.append(task)
            
            # Execute all tasks
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            duration = time.time() - start_time
            
            performance_monitor.stop_monitoring()
            metrics = performance_monitor.get_metrics()
            
            # Performance assertions
            assert len(results) == 100
            assert duration < 30.0, f"TTS operations took too long: {duration:.2f}s"
            assert all(isinstance(result, bytes) for result in results)
            
            # Calculate average processing time
            avg_time_per_request = duration / 100
            print(f"  ✅ Completed 100 TTS operations in {duration:.2f}s")
            print(f"  ⏱️  Average time per request: {avg_time_per_request:.3f}s")
            print(f"  📊 Peak memory: {metrics['peak_memory_percent']:.1f}%")
            print(f"  📊 Peak CPU: {metrics['peak_cpu_percent']:.1f}%")

    @pytest.mark.asyncio
    async def test_research_system_load(self, performance_monitor):
        """Test Research system under load."""
        print("🔍 Testing Research system load...")
        
        with patch.object(web_search_handler, 'search') as mock_search:
            mock_search.return_value = [
                {"title": f"Result {i}", "url": f"https://example.com/{i}", "snippet": f"Snippet {i}"}
                for i in range(5)
            ]
            
            with patch.object(research_handler, 'scrape_url') as mock_scrape:
                mock_scrape.return_value = Mock(
                    success=True,
                    cleaned_content=f"Content for URL",
                    markdown="# Content\n\nTest content"
                )
                
                performance_monitor.start_monitoring()
                
                # Stress test with concurrent research operations
                tasks = []
                
                # Create 50 concurrent research workflows
                for i in range(50):
                    # Each workflow includes search and scraping
                    search_task = web_search_handler.search(f"query {i}")
                    scrape_task = research_handler.scrape_url(f"https://example.com/{i}")
                    tasks.extend([search_task, scrape_task])
                
                # Execute all tasks
                start_time = time.time()
                results = await asyncio.gather(*tasks)
                duration = time.time() - start_time
                
                performance_monitor.stop_monitoring()
                metrics = performance_monitor.get_metrics()
                
                # Performance assertions
                assert len(results) == 100  # 50 searches + 50 scrapes
                assert duration < 20.0, f"Research operations took too long: {duration:.2f}s"
                
                print(f"  ✅ Completed 100 research operations in {duration:.2f}s")
                print(f"  📊 Peak memory: {metrics['peak_memory_percent']:.1f}%")
                print(f"  📊 Peak CPU: {metrics['peak_cpu_percent']:.1f}%")

    @pytest.mark.asyncio
    async def test_bug_watcher_continuous_monitoring(self, performance_monitor):
        """Test Bug Watcher continuous monitoring performance."""
        print("🐛 Testing Bug Watcher continuous monitoring...")
        
        with patch.object(bug_watcher, 'scan_for_errors') as mock_scan:
            # Simulate periodic error detection
            call_count = 0
            def scan_side_effect():
                nonlocal call_count
                call_count += 1
                # Simulate finding errors occasionally
                if call_count % 10 == 0:
                    return [{"text": "Test error", "confidence": 0.8}]
                return []
            
            mock_scan.side_effect = scan_side_effect
            
            performance_monitor.start_monitoring()
            
            # Simulate 30 seconds of continuous monitoring
            start_time = time.time()
            monitoring_tasks = []
            
            # Create monitoring tasks that run concurrently
            for _ in range(10):  # 10 concurrent monitoring loops
                task = self._simulate_monitoring_loop(bug_watcher, duration=3.0)
                monitoring_tasks.append(task)
            
            results = await asyncio.gather(*monitoring_tasks)
            duration = time.time() - start_time
            
            performance_monitor.stop_monitoring()
            metrics = performance_monitor.get_metrics()
            
            # Performance assertions
            assert duration < 10.0, f"Monitoring took too long: {duration:.2f}s"
            assert call_count > 0  # Should have made several scans
            
            total_scans = sum(results)
            print(f"  ✅ Completed {total_scans} error scans in {duration:.2f}s")
            print(f"  📊 Peak memory: {metrics['peak_memory_percent']:.1f}%")
            print(f"  📊 Peak CPU: {metrics['peak_cpu_percent']:.1f}%")

    async def _simulate_monitoring_loop(self, bug_watcher, duration):
        """Simulate a monitoring loop for testing."""
        start_time = time.time()
        scan_count = 0
        
        while time.time() - start_time < duration:
            await bug_watcher.scan_for_errors()
            scan_count += 1
            await asyncio.sleep(0.1)  # 100ms between scans
        
        return scan_count

    @pytest.mark.asyncio
    async def test_system_wide_stress_test(self, performance_monitor):
        """Test entire system under maximum stress."""
        print("🚀 Testing system-wide stress test...")
        
        # Mock all modules for system-wide testing
        with patch.object(web_search_handler, 'search') as mock_search:
            mock_search.return_value = [{"title": "Test", "url": "test.com", "snippet": "test"}]
            
            with patch.object(research_handler, 'scrape_url') as mock_scrape:
                mock_scrape.return_value = Mock(success=True, cleaned_content="test")
                
                with patch.object(KokoroTTS, 'synthesize_speech') as mock_tts:
                    mock_tts.return_value = b"test_audio"
                    
                    with patch.object(memory_manager, 'store_memory') as mock_memory:
                        mock_memory.return_value = True
                        
                        with patch.object(VisionAgent, 'parse_screen_elements') as mock_vision:
                            mock_vision.return_value = {"elements": [{"id": "test", "type": "button"}]}
                            
                            performance_monitor.start_monitoring()
                            
                            # Create massive concurrent workload
                            tasks = []
                            
                            # Add 20 tasks for each module type
                            for i in range(20):
                                tasks.extend([
                                    web_search_handler.search(f"query {i}"),
                                    research_handler.scrape_url(f"https://test{i}.com"),
                                    KokoroTTS().synthesize_speech(f"Test text {i}"),
                                    memory_manager.store_memory(f"Memory {i}", "test", "test"),
                                    VisionAgent().parse_screen_elements()
                                ])
                            
                            # Execute all tasks
                            start_time = time.time()
                            results = await asyncio.gather(*tasks, return_exceptions=True)
                            duration = time.time() - start_time
                            
                            performance_monitor.stop_monitoring()
                            metrics = performance_monitor.get_metrics()
                            
                            # Count successful operations
                            successful_ops = sum(1 for r in results if not isinstance(r, Exception))
                            
                            # Performance assertions
                            assert successful_ops >= 90, f"Too many failed operations: {len(results) - successful_ops}"
                            assert duration < 30.0, f"System stress test took too long: {duration:.2f}s"
                            
                            print(f"  ✅ Completed {successful_ops}/{len(tasks)} operations in {duration:.2f}s")
                            print(f"  📊 Peak memory: {metrics['peak_memory_percent']:.1f}%")
                            print(f"  📊 Peak CPU: {metrics['peak_cpu_percent']:.1f}%")
                            print(f"  🏗️  System efficiency: {metrics['memory_efficiency']} memory, {metrics['cpu_efficiency']} CPU")

    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, performance_monitor):
        """Test for memory leaks during extended operation."""
        print("🔍 Testing for memory leaks...")
        
        # Get initial memory state
        gc.collect()  # Force garbage collection
        initial_memory = psutil.Process().memory_info().rss
        
        with patch.object(memory_manager, 'store_memory') as mock_store:
            mock_store.return_value = True
            
            # Run many operations and check memory growth
            for batch in range(10):
                tasks = []
                for i in range(100):
                    task = memory_manager.store_memory(f"Leak test {batch}_{i}", "test", "test")
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
                
                # Force garbage collection
                gc.collect()
                
                # Check memory usage
                current_memory = psutil.Process().memory_info().rss
                memory_growth = (current_memory - initial_memory) / 1024 / 1024  # MB
                
                print(f"  Batch {batch + 1}: Memory growth: {memory_growth:.1f} MB")
                
                # Memory growth should be reasonable (less than 100MB per batch)
                assert memory_growth < 100, f"Potential memory leak detected: {memory_growth:.1f} MB growth"

    @pytest.mark.asyncio
    async def test_resource_cleanup(self, performance_monitor):
        """Test proper resource cleanup after operations."""
        print("🧹 Testing resource cleanup...")
        
        # Monitor file descriptors and memory
        initial_fds = len(psutil.Process().open_files())
        initial_memory = psutil.Process().memory_info().rss
        
        # Perform intensive operations
        with patch.object(KokoroTTS, 'synthesize_speech') as mock_tts:
            mock_tts.return_value = b"cleanup_test_audio"
            
            # Create and destroy many TTS instances
            for i in range(50):
                tts = KokoroTTS()
                await tts.synthesize_speech(f"Cleanup test {i}")
                del tts  # Explicitly delete instance
                
                if i % 10 == 0:
                    gc.collect()  # Periodic cleanup
        
        # Final cleanup
        gc.collect()
        
        # Check resource cleanup
        final_fds = len(psutil.Process().open_files())
        final_memory = psutil.Process().memory_info().rss
        
        fd_growth = final_fds - initial_fds
        memory_growth = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        print(f"  📁 File descriptor growth: {fd_growth}")
        print(f"  💾 Memory growth: {memory_growth:.1f} MB")
        
        # Resources should be properly cleaned up
        assert fd_growth < 10, f"File descriptor leak detected: {fd_growth} new descriptors"
        assert memory_growth < 50, f"Memory cleanup failed: {memory_growth:.1f} MB growth"

# Load Testing
@pytest.mark.skipif(not PERFORMANCE_AVAILABLE, reason="Performance modules not available")
@pytest.mark.slow
class TestLoadTesting:
    """Load testing for sustained operations."""

    @pytest.mark.asyncio
    async def test_sustained_load_vision(self):
        """Test sustained vision processing load."""
        print("🔄 Testing sustained vision load...")
        
        with patch.object(VisionAgent, 'parse_screen_elements') as mock_parse:
            mock_parse.return_value = {"elements": [{"id": "test", "type": "button"}]}
            
            # Run sustained load for 30 seconds
            start_time = time.time()
            operation_count = 0
            
            while time.time() - start_time < 30:  # 30 seconds of sustained load
                # Create batch of operations
                tasks = [VisionAgent().parse_screen_elements() for _ in range(10)]
                await asyncio.gather(*tasks)
                operation_count += 10
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
            
            duration = time.time() - start_time
            ops_per_second = operation_count / duration
            
            print(f"  ✅ Completed {operation_count} operations in {duration:.1f}s")
            print(f"  ⚡ Operations per second: {ops_per_second:.1f}")
            
            # Should maintain reasonable performance
            assert ops_per_second > 50, f"Performance degraded too much: {ops_per_second:.1f} ops/s"

    @pytest.mark.asyncio
    async def test_sustained_load_memory(self):
        """Test sustained memory operations load."""
        print("🧠 Testing sustained memory load...")
        
        with patch.object(memory_manager, 'store_memory') as mock_store:
            mock_store.return_value = True
            
            # Run sustained load for 30 seconds
            start_time = time.time()
            operation_count = 0
            
            while time.time() - start_time < 30:  # 30 seconds of sustained load
                # Create batch of operations
                tasks = [
                    memory_manager.store_memory(f"Sustained test {operation_count + i}", "test", "test")
                    for i in range(20)
                ]
                await asyncio.gather(*tasks)
                operation_count += 20
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.05)
            
            duration = time.time() - start_time
            ops_per_second = operation_count / duration
            
            print(f"  ✅ Completed {operation_count} operations in {duration:.1f}s")
            print(f"  ⚡ Operations per second: {ops_per_second:.1f}")
            
            # Should maintain reasonable performance
            assert ops_per_second > 200, f"Memory performance degraded: {ops_per_second:.1f} ops/s"

if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_performance_stress.py -v -s
    pytest.main([__file__, "-v", "-s"])
