import asyncio
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

# Try to import crawl4ai, but provide a mock/fallback if not installed yet
try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode 
    from crawl4ai.extraction_strategy import LLMExtractionStrategy 
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False

class ResearchHandler:
    """
    Handles deep web research using Crawl4AI for high-fidelity markdown extraction.
    This is the 'God-Mode' reader for Wolf AI.
    """
    
    def __init__(self):
        self.output_dir = Path("data/research")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.is_initialized = CRAWL4AI_AVAILABLE

    async def scrape_url(self, url: str, extract_blocks: bool = True) -> Dict[str, Any]:
        """
        Deep scrape a URL and return clean markdown and metadata.
        """
        if not self.is_initialized:
            return {
                "success": False,
                "message": "Crawl4AI is not installed. Run 'pip install crawl4ai' to enable deep research."
            }

        print(f"[Research] Deep scraping URL: {url}")
        
        try:
            async with AsyncWebCrawler() as crawler:
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    word_count_threshold=10,
                    remove_overlay_elements=True,
                    process_iframes=True
                )
                
                result = await crawler.arun(url=url, config=config)
                
                if result.success:
                    # Save a local cache of the research
                    url_part = url[:50]
                    safe_name = "".join([c if c.isalnum() else "_" for c in url_part])
                    output_path = self.output_dir / f"{safe_name}.md"
                    
                    try:
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(result.markdown)
                    except Exception as e:
                        print(f"[Research] Error saving cache: {e}")

                    return {
                        "success": True,
                        "markdown": result.markdown[:5000],
                        "title": result.metadata.get("title", "Unknown Page"),
                        "links": result.metadata.get("links", []),
                        "saved_at": str(output_path)
                    }
                else:
                    return {"success": False, "message": f"Scrape failed: {result.error_message}"}
                
        except Exception as e:
            return {"success": False, "message": f"Research error: {str(e)}"}

    def scrape_url_sync(self, url: str) -> Dict[str, Any]:
        """Synchronous wrapper for standard function executor."""
        try:
            return asyncio.run(self.scrape_url(url))
        except Exception as e:
            return {"success": False, "message": f"Sync loop error: {str(e)}"}

# Global instance
research_handler = ResearchHandler()
