import json
from typing import List, Dict, Any
try:
    from duckduckgo_search import DDGS # type: ignore
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

class SearchHandler:
    """Handles web searching using DuckDuckGo."""
    
    def __init__(self):
        self.is_initialized = DDGS_AVAILABLE

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search the web and return results."""
        if not self.is_initialized:
            print("[SearchHandler] duckduckgo-search not installed.")
            return []

        print(f"[SearchHandler] Searching for: {query}")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=limit))
                return [
                    {
                        "title": r.get("title"),
                        "url": r.get("href"),
                        "body": r.get("body")
                    }
                    for r in results
                ]
        except Exception as e:
            print(f"[SearchHandler] Search error: {e}")
            return []

# Global instance
web_search_handler = SearchHandler()
