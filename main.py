"""
Wolf AI - Backend Entry Point
"""

import warnings
import sys
import os
import time
import threading

# Suppress ALL warnings globally before any other imports
warnings.simplefilter("ignore")
os.environ["QT_API"] = "" # Disable any qt bindings

# Force UTF-8 encoding for console output to handle emojis on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from core.llm import preload_models
from core.voice_assistant import voice_assistant
from core.tts import tts
from core.settings_store import settings
from config import VOICE_ASSISTANT_ENABLED, GREEN, RESET
from core.model_manager import unload_all_models
from core.calendar_manager import calendar_manager

class BackendServer:
    def __init__(self):
        print("\n" + bytes.fromhex("4d6164652042792051616469726461642d4b617a6920506f7274666f6c696f206c696e6b2071616469726461646b617a692e636f6d").decode() + "\n")
        print(f"{GREEN}[System] Initializing Wolf AI Backend Engine...{RESET}")

    def _preload_models(self):
        threading.Thread(target=preload_models, daemon=True).start()

    def _init_god_mode(self):
        # Start bug watcher if enabled
        if settings.get("bug_watcher.enabled", False):
            try:
                from core.bug_watcher import bug_watcher
                bug_watcher.start()
                print("[System] Bug watcher started")
            except ImportError:
                print("[System] Bug watcher not available.")
        
        # We removed HUD rendering to decouple the backend from PySide
        if settings.get("hud.enabled", False):
            print("[System] Note: HUD is disabled in headless backend mode.")
    
    def _init_voice_assistant(self):
        print(f"[App] Initializing voice assistant (enabled={VOICE_ASSISTANT_ENABLED})...")
        if VOICE_ASSISTANT_ENABLED:
            def init_va():
                print(f"[App] Background thread: Initializing voice assistant components...")
                if voice_assistant.initialize():
                    print(f"[App] ✓ Voice assistant initialized")
                    tts.toggle(True)
                    print(f"[App] Starting voice assistant engine...")
                    voice_assistant.start()
                    print(f"[App] ✓ Voice assistant is fully active and listening.")
                else:
                    print(f"[App] ✗ Failed to initialize voice assistant")
            
            # Start background thread to load AI models and STT
            threading.Thread(target=init_va, daemon=True).start()
        else:
            print(f"[App] Voice assistant disabled in config")
            
    def run_forever(self):
        try:
            # Setup and initialize all core engines
            self._preload_models()
            self._init_god_mode()
            self._init_voice_assistant()
            
            # Start calendar manager locally
            calendar_manager.start()
            print("[System] Calendar manager started")
            # Start FastAPI backend server using Uvicorn
            import uvicorn
            print(f"{GREEN}[System] Booting FastAPI WebSocket Server on ws://localhost:8000{RESET}")
            uvicorn.run("backend_api:app", host="0.0.0.0", port=8000, log_level="warning")
            
        except KeyboardInterrupt:
            print("\n[System] Interrupted! Shutting down gracefully...")
            if VOICE_ASSISTANT_ENABLED:
                voice_assistant.stop()
            unload_all_models(sync=True)
            print("[System] Backend stopped.")
            sys.exit(0)

if __name__ == "__main__":
    server = BackendServer()
    server.run_forever()
