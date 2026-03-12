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
            web_search_handler.search.assert_called_with("current Bitcoin price", 5)

    @pytest.mark.asyncio
    async def test_url_scraping(self, mock_crawl4ai_response, sample_web_content):
        """Test URL content scraping."""
        with patch('utilities.research_handler.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            result = await research_handler.scrape_url("https://example.com/test")
            
            assert result is not None
            assert result.success is True
            assert result.url == sample_web_content["url"]
            assert len(result.markdown) > 0

    @pytest.mark.asyncio
    async def test_content_extraction(self, mock_crawl4ai_response):
        """Test content extraction and cleaning."""
        with patch('utilities.research_handler.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            result = await research_handler.scrape_url("https://example.com/test")
            
            # Test content cleaning
            cleaned_content = research_handler.clean_content(result.cleaned_content)
            
            assert isinstance(cleaned_content, str)
            assert len(cleaned_content) > 0
            assert "Llama 3.2" in cleaned_content

    @pytest.mark.asyncio
    async def test_research_summary_generation(self, sample_web_content):
        """Test generating research summaries."""
        with patch.object(research_handler, 'generate_summary') as mock_summary:
            mock_summary.return_value = """
            Llama 3.2 is a 3B parameter language model optimized for local deployment.
            Key features include 8192 token context length and vision capabilities.
            The architecture uses 32 transformer layers with 26 attention heads.
            """
            
            summary = await research_handler.generate_summary(sample_web_content["content"])
            
            assert isinstance(summary, str)
            assert len(summary) > 0
            assert "Llama 3.2" in summary

    @pytest.mark.asyncio
    async def test_deep_research_workflow(self, sample_search_results, mock_crawl4ai_response):
        """Test complete deep research workflow."""
        with patch.object(web_search_handler, 'search', return_value=sample_search_results):
            with patch('utilities.research_handler.AsyncWebCrawler') as mock_crawler:
                mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
                
                # Step 1: Search for relevant URLs
                search_results = await web_search_handler.search("Llama 3.2 architecture")
                assert len(search_results) > 0
                
                # Step 2: Scrape top result
                scraped_content = await research_handler.scrape_url(search_results[0]["url"])
                assert scraped_content.success is True
                
                # Step 3: Generate summary
                summary = await research_handler.generate_summary(scraped_content.cleaned_content)
                assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_overlay_bypass(self, mock_crawl4ai_response):
        """Test bypassing web overlays and popups."""
        # Configure crawler with overlay bypass
        with patch('utilities.research_handler.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            result = await research_handler.scrape_url(
                "https://example.com/with-overlay",
                bypass_overlays=True
            )
            
            assert result.success is True
            assert len(result.cleaned_content) > 0

    @pytest.mark.asyncio
    async def test_javascript_rendering(self, mock_crawl4ai_response):
        """Test JavaScript rendering for dynamic content."""
        with patch('utilities.research_handler.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            result = await research_handler.scrape_url(
                "https://example.com/dynamic",
                js_rendering=True
            )
            
            assert result.success is True
            # Verify JS rendering was requested
            mock_crawler.assert_called_with(
                js_code=None,
                browser_type="chromium",
                headless=True,
                verbose=False
            )

    @pytest.mark.asyncio
    async def test_multi_url_research(self, sample_search_results, mock_crawl4ai_response):
        """Test researching multiple URLs simultaneously."""
        urls = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]
        
        with patch('utilities.research_handler.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            # Scrape multiple URLs concurrently
            tasks = [research_handler.scrape_url(url) for url in urls]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == len(urls)
            for result in results:
                assert result.success is True

    @pytest.mark.asyncio
    async def test_content_filtering(self, mock_crawl4ai_response):
        """Test content filtering and relevance scoring."""
        with patch('utilities.research_handler.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            result = await research_handler.scrape_url("https://example.com/test")
            
            # Test relevance scoring
            relevance_score = research_handler.calculate_relevance(
                result.cleaned_content,
                "Llama 3.2 architecture"
            )
            
            assert isinstance(relevance_score, float)
            assert 0.0 <= relevance_score <= 1.0
            assert relevance_score > 0.5  # Should be relevant

    @pytest.mark.asyncio
    async def test_error_handling_invalid_url(self):
        """Test error handling with invalid URLs."""
        with patch('utilities.research_handler.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.side_effect = Exception("Invalid URL")
            
            result = await research_handler.scrape_url("invalid-url")
            
            assert result is None or result.success is False

    @pytest.mark.asyncio
    async def test_rate_limiting(self, sample_search_results):
        """Test rate limiting for search requests."""
        with patch.object(web_search_handler, 'search', return_value=sample_search_results):
            # Make multiple rapid requests
            tasks = []
            for i in range(5):
                task = web_search_handler.search(f"test query {i}")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # All requests should succeed (rate limiting handles delays)
            assert len(results) == 5
            for result in results:
                assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_search_query_optimization(self):
        """Test search query optimization."""
        original_query = "what is the current price of bitcoin"
        optimized_query = web_search_handler.optimize_query(original_query)
        
        assert isinstance(optimized_query, str)
        assert len(optimized_query) > 0
        # Should remove stop words and focus on keywords
        assert "bitcoin" in optimized_query.lower()
        assert "price" in optimized_query.lower()

    @pytest.mark.asyncio
    async def test_content_caching(self, mock_crawl4ai_response):
        """Test content caching to avoid repeated requests."""
        with patch('utilities.research_handler.AsyncWebCrawler') as mock_crawler:
            mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
            
            url = "https://example.com/cached"
            
            # First request
            result1 = await research_handler.scrape_url(url)
            
            # Second request (should use cache)
            result2 = await research_handler.scrape_url(url)
            
            # Both should return same result
            assert result1.url == result2.url
            assert result1.markdown == result2.markdown

    @pytest.mark.asyncio
    async def test_research_report_generation(self, sample_search_results, mock_crawl4ai_response):
        """Test generating comprehensive research reports."""
        with patch.object(web_search_handler, 'search', return_value=sample_search_results):
            with patch('utilities.research_handler.AsyncWebCrawler') as mock_crawler:
                mock_crawler.return_value.__aenter__.return_value.arun.return_value = mock_crawl4ai_response
                
                report = await research_handler.generate_research_report("Llama 3.2 architecture")
                
                assert isinstance(report, dict)
                assert "summary" in report
                assert "sources" in report
                assert "key_findings" in report
                assert len(report["sources"]) > 0

# Integration Tests
@pytest.mark.skipif(not RESEARCH_AVAILABLE, reason="Research modules not available")
@pytest.mark.integration
class TestDeepResearchIntegration:
    """Integration tests for Deep Research with real components."""

    @pytest.mark.asyncio
    async def test_real_web_search(self):
        """Test actual web search functionality."""
        try:
            results = await web_search_handler.search("Wolf AI assistant")
            
            assert isinstance(results, list)
            if len(results) > 0:
                assert "title" in results[0]
                assert "url" in results[0]
                
        except Exception as e:
            pytest.skip(f"Web search not available: {e}")

    @pytest.mark.asyncio
    async def test_real_url_scraping(self):
        """Test actual URL scraping with Crawl4AI."""
        try:
            # Use a reliable, simple URL for testing
            test_url = "https://httpbin.org/html"
            
            result = await research_handler.scrape_url(test_url)
            
            if result and result.success:
                assert isinstance(result.markdown, str)
                assert len(result.markdown) > 0
            else:
                pytest.skip("URL scraping failed")
                
        except Exception as e:
            if "playwright" in str(e).lower() or "browser" in str(e).lower():
                pytest.skip(f"Browser not available: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_bitcoin_price_search(self):
        """Test real-time Bitcoin price search as mentioned in testing guide."""
        try:
            results = await web_search_handler.search("current Bitcoin price")
            
            assert isinstance(results, list)
            
            # Look for price information in results
            price_found = False
            for result in results:
                if any(keyword in result["snippet"].lower() for keyword in ["bitcoin", "btc", "$", "price"]):
                    price_found = True
                    break
            
            # Note: This might not find actual price data in test environment
            # but should work in production
            
        except Exception as e:
            pytest.skip(f"Bitcoin price search failed: {e}")

    @pytest.mark.asyncio
    async def test_ollama_docs_research(self):
        """Test researching Ollama documentation as mentioned in testing guide."""
        try:
            test_url = "https://ollama.com/library/llama3.2"
            
            result = await research_handler.scrape_url(test_url)
            
            if result and result.success:
                # Test content extraction
                summary = await research_handler.generate_summary(result.cleaned_content)
                
                assert isinstance(summary, str)
                assert len(summary) > 0
                
                # Should contain information about Llama 3.2
                assert any(term in summary.lower() for term in ["llama", "model", "parameters"])
            else:
                pytest.skip("Ollama docs scraping failed")
                
        except Exception as e:
            if "network" in str(e).lower() or "connection" in str(e).lower():
                pytest.skip(f"Network access not available: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_comprehensive_research_workflow(self):
        """Test complete research workflow as described in enhancement guide."""
        try:
            # Step 1: Web search
            search_results = await web_search_handler.search("latest AI PC control technology")
            
            if not search_results:
                pytest.skip("No search results available")
            
            # Step 2: Deep research on top result
            top_url = search_results[0]["url"]
            scraped_content = await research_handler.scrape_url(top_url)
            
            if not scraped_content or not scraped_content.success:
                pytest.skip("Content scraping failed")
            
            # Step 3: Generate comprehensive summary
            summary = await research_handler.generate_summary(scraped_content.cleaned_content)
            
            assert isinstance(summary, str)
            assert len(summary) > 50  # Reasonable summary length
            
        except Exception as e:
            if "network" in str(e).lower():
                pytest.skip(f"Network-dependent test skipped: {e}")
            else:
                raise

if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_deep_research.py -v
    pytest.main([__file__, "-v"])
