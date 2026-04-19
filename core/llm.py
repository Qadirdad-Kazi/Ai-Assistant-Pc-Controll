"""
LLM interaction and function execution.
"""

import requests  
import json
import re
import threading
from typing import Dict, Any, Optional
from config import (  
    OLLAMA_URL, LOCAL_ROUTER_PATH, GREEN, CYAN, YELLOW, GRAY, RESET, RESPONDER_MODEL
)
from core.privacy_tracker import privacy_tracker
from core.database import db

# Persistent Session for faster HTTP
http_session = requests.Session()

# Global Router Instance
router = None


def is_router_loaded():
    """Check if the local router model is loaded in memory."""
    return router is not None


def should_bypass_router(text):
    """Return True if text definitely doesn't need routing."""
    # All queries now go through Function Gemma router
    # This function is kept for compatibility but always returns False
    return False


def route_query(user_input):
    """Route user query using local FunctionGemmaRouter. Checks learned heuristics first."""
    global router
    
    # Check for learned heuristics (Personalized corrections)
    learned_plan = db.get_learned_heuristic(user_input)
    if learned_plan:
        print(f"{CYAN}[System] Using learned heuristic for: '{user_input}'{RESET}")
        return [("learned_heuristic", {"plan": learned_plan, "query": user_input})]

    # Lazy Initialization of Router
    if not router:
        try:
            from core.router import FunctionGemmaRouter  
            # We load without compilation for faster initialization and stability
            router = FunctionGemmaRouter(model_path=LOCAL_ROUTER_PATH, compile_model=False)
        except Exception as e:
            print(f"{GRAY}[Router Init Error: {e}]{RESET}")
            return [("nonthinking", {"prompt": user_input})]

    try:
        # Route using the fine-tuned model - returns List[(func_name, params)]
        calls, elapsed = router.route_with_timing(user_input)
        return calls
            
    except Exception as e:
        print(f"{GRAY}[Router Error: {e}]{RESET}")
        return [("nonthinking", {"prompt": user_input})]


def execute_function(name, params):
    """Execute function and return response string."""
    if name == "pc_control":
        action = params.get("action", "unknown")
        target = params.get("target", "")
        return f"🖥️ System execution: {action} {target}"
    
    elif name == "play_music":
        query = params.get("query", "")
        return f"🎵 Now playing: {query}"
    
    else:
        return f"Unknown function: {name}"


def preload_models():
    """Client-side preload to ensure models are in memory before user interaction. Sequential to save memory."""
    from core.router import FunctionGemmaRouter  
    from core.tts import tts
    
    global router
    
    print(f"{GRAY}[System] Preloading models sequentially to conserve memory...{RESET}")
    
    # 1. Load Voice (usually lightest if using Piper)
    try:
        print(f"{GRAY}[System] Phase 1/3: Loading voice model...{RESET}")
        tts.initialize()
    except Exception as e:
        print(f"{GRAY}[System] Voice load warning: {e}{RESET}")

    # 2. Load Responder (Ollama - mostly off-process memory)
    try:
        print(f"{GRAY}[System] Phase 2/3: Loading responder model ({RESPONDER_MODEL})...{RESET}")
        payload = {
            "model": RESPONDER_MODEL, 
            "prompt": "hi",
            "stream": False,
            "keep_alive": "30m",
            "options": {"num_predict": 1}
        }
        privacy_tracker.log_event("Ollama", "SENT", "Model Load/Heartbeat", f"Loading {RESPONDER_MODEL}", len(json.dumps(payload)))
        response = http_session.post(f"{OLLAMA_URL}/generate", json=payload, timeout=120)
        privacy_tracker.log_event("Ollama", "RECEIVED", "Model Status", f"Response: {response.status_code}", len(response.content))
        if response.status_code == 200:
            print(f"{GRAY}[System] Responder model loaded successfully.{RESET}")
    except Exception as e:
        print(f"{GRAY}[System] Responder load warning: {e}{RESET}")

    # 3. Load Router (Heaviest - load last)
    try:
        print(f"{GRAY}[System] Phase 3/3: Loading local router model...{RESET}")
        if not router:
            router = FunctionGemmaRouter(model_path=LOCAL_ROUTER_PATH, compile_model=False)
        print(f"{GRAY}[System] Router model loaded successfully.{RESET}")
    except Exception as e:
        print(f"{GRAY}[Router] Failed to load local model: {e}{RESET}")

    print(f"{GRAY}[System] Models warm and ready.{RESET}")
