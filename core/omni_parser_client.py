import requests
import json
import base64
import time
from typing import List, Dict, Any, Optional
from core.privacy_tracker import privacy_tracker

class OmniParserClient:
    """
    Client for Microsoft OmniParser. 
    Assumes OmniParser is running as a local REST service (standard port 8001).
    """
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url

    def is_available(self) -> bool:
        """Check if the OmniParser service is reachable."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def parse_screen(self, img_base64: str) -> Dict[str, Any]:
        """
        Send screenshot to OmniParser and get structured UI elements.
        Returns:
            {
                "elements": [{"box": [x, y, w, h], "label": "button", "text": "Login", "score": 0.9}, ...],
                "parsed_image": "base64..." (image with bounding box labels)
            }
        """
        if not self.is_available():
            return {"success": False, "message": "OmniParser service not reachable."}

        try:
            start_time = time.time()
            # Privacy Log: Send
            privacy_tracker.log_event("OmniParser", "SENT", "Image Analysis", f"Parsing screen for UI elements", len(img_base64))
            
            response = requests.post(
                f"{self.base_url}/parse",
                json={"image": img_base64},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Privacy Log: Receive
            privacy_tracker.log_event("OmniParser", "RECEIVED", "UI Elements", f"Found {len(data.get('elements', []))} elements", len(response.content))
            
            latency = time.time() - start_time
            print(f"[OmniParser] Screen parsed in {latency:.2f}s. Found {len(data.get('elements', []))} elements.")
            
            return {
                "success": True,
                "elements": data.get("elements", []),
                "parsed_image": data.get("parsed_image", ""),
                "latency": latency
            }
        except Exception as e:
            return {"success": False, "message": f"OmniParser error: {str(e)}"}

    def find_element_by_description(self, elements: List[Dict[str, Any]], query: str) -> Optional[Dict[str, Any]]:
        """
        Heuristic to find an element from the parsed list matching the query.
        """
        query = query.lower()
        best_match = None
        highest_score = 0.0

        for el in elements:
            text = str(el.get("text", "")).lower()
            label = str(el.get("label", "")).lower()
            
            # Simple keyword matching
            score = 0.0
            if query in text:
                score += 0.8
            if query in label:
                score += 0.2
            
            if score > highest_score:
                highest_score = score
                best_match = el
        
        return best_match if highest_score > 0 else None

# Global instance
omni_parser = OmniParserClient()
