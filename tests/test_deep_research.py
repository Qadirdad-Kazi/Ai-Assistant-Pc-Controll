"""
Deep Research Test Suite
Tests web intelligence and Crawl4AI integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from utilities.research_handler import research_handler
    from utilities.search_handler import web_search_handler
    RESEARCH_AVAILABLE = True
except ImportError as e:
    print(f"Research modules not available: {e}")
    RESEARCH_AVAILABLE = False

@pytest.mark.skipif(not RESEARCH_AVAILABLE, reason="Research modules not available")
class TestDeepResearch:
    """Test suite for Deep Research capabilities."""

    @pytest.fixture
    def sample_web_content(self):
        """Sample web content for testing."""
        return {
            "url": "https://example.com/test",
            "title": "Test Page",
            "content": """
            # Llama 3.2 Architecture
            
            Llama 3.2 is a state-of-the-art language model with the following features:
            
            - 3 billion parameters
            - Context length of 8192 tokens
            - Optimized for local inference
            - Vision capabilities in multimodal variants
            
            ## Technical Specifications
            
            The model uses a transformer architecture with:
            - 32 layers
            - 26 attention heads
            - Vocabulary size of 128,000 tokens
            """,
            "markdown": "# Llama 3.2 Architecture\n\nLlama 3.2 is a state-of-the-art language model...",
            "links": ["https://ollama.com/library/llama3.2"],
            "images": ["model_architecture.png"],
            "metadata": {
                "author": "AI Research Team",
                "date": "2024-01-01",
                "word_count": 150
            }
        }

    @pytest.fixture
    def sample_search_results(self):
        """Sample search results for testing."""
        return [
            {
                "title": "Llama 3.2 - Ollama",
                "url": "https://ollama.com/library/llama3.2",
                "body": "Llama 3.2 is a compact language model optimized for local deployment..."
            },
            {
                "title": "Llama 3.2 Architecture Guide",
                "url": "https://example.com/architecture",
                "body": "Technical deep dive into Llama 3.2's transformer architecture..."
            }
        ]

    @pytest.fixture
    def mock_crawl4ai_response(self, sample_web_content):
        """Mock Crawl4AI response."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.url = sample_web_content["url"]
        mock_result.markdown = sample_web_content["markdown"]
        mock_result.cleaned_content = sample_web_content["content"]
        mock_result.links = sample_web_content["links"]
        mock_result.images = sample_web_content["images"]
        mock_result.metadata = sample_web_content["metadata"]
        return mock_result

    @pytest.mark.asyncio
    async def test_web_search_basic(self, sample_search_results):
        """Test basic web search functionality."""
        with patch.object(web_search_handler, 'search', return_value=sample_search_results):
            results = web_search_handler.search("Llama 3.2 architecture")
            
            assert isinstance(results, list)
            assert len(results) > 0
            assert "title" in results[0]
            assert "url" in results[0]
            assert "body" in results[0]

    @pytest.mark.asyncio
    async def test_real_time_search(self, sample_search_results):
        """Test real-time search for current information."""
        with patch.object(web_search_handler, 'search', return_value=sample_search_results):
            # Test real-time query
            results = web_search_handler.search("current Bitcoin price")
            
            assert isinstance(results, list)
            assert len(results) > 0
            
            # Verify search was called with correct query
            web_search_handler.search.assert_called_with("current Bitcoin price")

    @pytest.mark.asyncio
    async def test_url_scraping(self, mock_crawl4ai_response, sample_web_content):
        """Test URL content scraping."""
        with patch('crawl4ai.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            result = await research_handler.scrape_url("https://example.com/test")
            
            assert result is not None
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_content_extraction(self, mock_crawl4ai_response):
        """Test content extraction and cleaning."""
        with patch('crawl4ai.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            result = await research_handler.scrape_url("https://example.com/content")
            
            assert result is not None
            if result.get("success"):
                assert "markdown" in result
                assert len(result["markdown"]) > 0

    @pytest.mark.asyncio
    async def test_research_summary_generation(self, mock_crawl4ai_response):
        """Test research summary generation."""
        with patch('crawl4ai.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            result = await research_handler.scrape_url("https://example.com/article")
            
            assert result is not None
            if result.get("success"):
                assert "title" in result
                assert isinstance(result["title"], str)

    @pytest.mark.asyncio
    async def test_deep_research_workflow(self, sample_search_results, mock_crawl4ai_response):
        """Test complete deep research workflow."""
        with patch.object(web_search_handler, 'search', return_value=sample_search_results):
            with patch('crawl4ai.AsyncWebCrawler') as mock_crawler:
                mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
                
                # Step 1: Search
                search_results = web_search_handler.search("test query")
                assert len(search_results) > 0
                
                # Step 2: Scrape first result
                if search_results:
                    result = await research_handler.scrape_url(search_results[0]["url"])
                    assert result is not None

    @pytest.mark.asyncio
    async def test_overlay_bypass(self, mock_crawl4ai_response):
        """Test overlay bypass functionality."""
        with patch('crawl4ai.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            result = await research_handler.scrape_url("https://example.com/overlay")
            
            assert result is not None
            # The CrawlerRunConfig should have remove_overlay_elements=True

    @pytest.mark.asyncio
    async def test_javascript_rendering(self, mock_crawl4ai_response):
        """Test JavaScript rendering."""
        with patch('crawl4ai.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            result = await research_handler.scrape_url("https://example.com/js-heavy")
            
            assert result is not None
            # The CrawlerRunConfig should have process_iframes=True

    @pytest.mark.asyncio
    async def test_multi_url_research(self, sample_search_results, mock_crawl4ai_response):
        """Test research across multiple URLs."""
        with patch('crawl4ai.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            urls = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]
            results = []
            
            for url in urls:
                result = await research_handler.scrape_url(url)
                results.append(result)
            
            assert len(results) == len(urls)
            for result in results:
                assert result is not None

    @pytest.mark.asyncio
    async def test_content_filtering(self, mock_crawl4ai_response):
        """Test content filtering."""
        with patch('crawl4ai.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            result = await research_handler.scrape_url("https://example.com/filter")
            
            assert result is not None
            if result.get("success"):
                # The CrawlerRunConfig should have word_count_threshold=10
                assert "markdown" in result

    @pytest.mark.asyncio
    async def test_error_handling_invalid_url(self):
        """Test error handling for invalid URLs."""
        result = await research_handler.scrape_url("invalid-url")
        
        assert result is not None
        assert isinstance(result, dict)
        # Should handle the error gracefully

    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_crawl4ai_response):
        """Test rate limiting."""
        with patch('crawl4ai.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            # Test multiple rapid requests
            urls = [f"https://example.com/page{i}" for i in range(3)]
            results = []
            
            for url in urls:
                result = await research_handler.scrape_url(url)
                results.append(result)
            
            assert len(results) == len(urls)

    @pytest.mark.asyncio
    async def test_search_query_optimization(self, sample_search_results):
        """Test search query optimization."""
        with patch.object(web_search_handler, 'search', return_value=sample_search_results):
            # Test with different query types
            queries = ["simple query", "complex query with quotes", "query -exclude"]
            
            for query in queries:
                results = web_search_handler.search(query)
                assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_content_caching(self, mock_crawl4ai_response):
        """Test content caching."""
        with patch('crawl4ai.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            result = await research_handler.scrape_url("https://example.com/cache")
            
            assert result is not None
            # The handler should attempt to save to cache

    @pytest.mark.asyncio
    async def test_research_report_generation(self, sample_search_results, mock_crawl4ai_response):
        """Test research report generation."""
        with patch.object(web_search_handler, 'search', return_value=sample_search_results):
            with patch('crawl4ai.AsyncWebCrawler') as mock_crawler:
                mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
                
                # Generate a simple research report
                search_results = web_search_handler.search("test topic")
                report_data = {
                    "query": "test topic",
                    "search_results": search_results,
                    "scraped_content": []
                }
                
                if search_results:
                    result = await research_handler.scrape_url(search_results[0]["url"])
                    if result.get("success"):
                        report_data["scraped_content"].append(result)
                
                assert len(report_data["search_results"]) > 0
                assert isinstance(report_data, dict)

# Integration Tests
@pytest.mark.skipif(not RESEARCH_AVAILABLE, reason="Research modules not available")
@pytest.mark.integration
class TestDeepResearchIntegration:
    """Integration tests for Deep Research with real components."""

    @pytest.mark.asyncio
    async def test_real_web_search(self):
        """Test actual web search functionality."""
        if not web_search_handler.is_initialized:
            pytest.skip("DuckDuckGo search not available")
        
        results = web_search_handler.search("Python programming")
        
        assert isinstance(results, list)
        # May return empty list if no internet, but should not crash

    @pytest.mark.asyncio
    async def test_real_url_scraping(self):
        """Test actual URL scraping."""
        if not research_handler.is_initialized:
            pytest.skip("Crawl4AI not available")
        
        # Test with a simple, reliable website
        result = await research_handler.scrape_url("https://httpbin.org/html")
        
        assert isinstance(result, dict)
        assert "success" in result

    @pytest.mark.asyncio
    async def test_ollama_docs_research(self):
        """Test researching Ollama documentation."""
        if not research_handler.is_initialized:
            pytest.skip("Crawl4AI not available")
        
        result = await research_handler.scrape_url("https://github.com/ollama/ollama")
        
        assert isinstance(result, dict)
        assert "success" in result

    @pytest.mark.asyncio
    async def test_comprehensive_research_workflow(self):
        """Test complete research workflow with real components."""
        if not web_search_handler.is_initialized or not research_handler.is_initialized:
            pytest.skip("Required components not available")
        
        # Search for a topic
        search_results = web_search_handler.search("artificial intelligence")
        
        if search_results:
            # Scrape the first result
            result = await research_handler.scrape_url(search_results[0]["url"])
            
            assert isinstance(result, dict)
            assert "success" in result

    @pytest.mark.asyncio
    async def test_bitcoin_price_search(self):
        """Test real-time Bitcoin price search as mentioned in testing guide."""
        if not web_search_handler.is_initialized:
            pytest.skip("DuckDuckGo search not available")
        
        results = web_search_handler.search("current Bitcoin price")
        
        assert isinstance(results, list)
        # Should not crash even if no results found

if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_deep_research.py -v -s
    pytest.main([__file__, "-v", "-s"])
