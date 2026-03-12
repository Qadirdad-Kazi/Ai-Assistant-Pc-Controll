import os
import time
import threading
import queue
import numpy as np # type: ignore
import sounddevice as sd # type: ignore
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from kokoro import KModel, KPipeline # type: ignore
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False

class KokoroTTS:
    """
    Next-generation local TTS using Kokoro-82M.
    Provides human-like quality with low latency.
    """
    
    def __init__(self, model_path: str = "models/kokoro/kokoro-v0_19.pth"):
        self.model_path = model_path
        self.pipeline = None
        self.is_initialized = False
        self.speech_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread: Optional[threading.Thread] = None
        
    def initialize(self):
        """Load the model and pipeline."""
        if not KOKORO_AVAILABLE:
            print("[KokoroTTS] Library not installed. Run 'pip install kokoro'.")
            return False
            
        if self.is_initialized:
            return True
            
        try:
            print(f"[KokoroTTS] Initializing Kokoro from {self.model_path}...")
            # Note: Kokoro requires 'onnxruntime' or 'torch'
            # This is a simplified initialization assuming the user has the model
            self.pipeline = KPipeline(lang_code='a') # 'a' for American English
            self.is_initialized = True
            
            # Start worker thread
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            if self.worker_thread:
                self.worker_thread.start()
            return True
        except Exception as e:
            print(f"[KokoroTTS] Initialization failed: {e}")
            return False

    def speak(self, text: str):
        """Queue text for speech."""
        if not self.is_initialized:
            if not self.initialize():
                return
                
        from core.settings_store import settings
        raw_v = settings.get("tts.voice", "af_heart")
        
        # Voice mapping: Map Piper/human-readable names to Kokoro internal names
        voice_map = {
            "Male (Northern)": "am_adam",   # Close enough male voice
            "Female (Alba)": "af_heart",    # Close enough female voice
            "af_heart": "af_heart",
            "am_adam": "am_adam",
            "af_sky": "af_sky",
            "bf_emma": "bf_emma",
            "bm_george": "bm_george"
        }
        
        v = voice_map.get(raw_v, "af_heart")
        
        # Auto-switch pipeline language if voice starts with 'b' (British)
        target_lang = 'b' if v.startswith('b') else 'a'
        if self.pipeline and self.pipeline.lang_code != target_lang:
            print(f"[KokoroTTS] Switching language to {target_lang}")
            self.pipeline = KPipeline(lang_code=target_lang)
            
        s = settings.get("tts.speed", 1.0)
        self.speech_queue.put({"text": text, "voice": v, "speed": s})

    def wait_for_completion(self):
        """Wait for queue to clear."""
        self.speech_queue.join()

    def stop(self):
        """Stop current playback and clear queue."""
        self.stop_event.set()
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
        self.stop_event.clear()

    def _worker(self):
        """Process speech requests in the background."""
        while True:
            try:
                item = self.speech_queue.get(timeout=1)
                text = item["text"]
                voice = item.get("voice", "af_heart")
                speed = item.get("speed", 1.0)
                
                print(f"[KokoroTTS] Generating: {text[:50]}...") # type: ignore
                
                # Kokoro generation
                generator = self.pipeline(text, voice=voice, speed=speed) # type: ignore
                
                for gs, ps, audio in generator:
                    if self.stop_event.is_set():
                        break
                    
                    # Play audio using sounddevice
                    sd.play(audio, 24000) # Kokoro uses 24kHz
                    sd.wait()
                
                self.speech_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[KokoroTTS] Worker error: {e}")
                time.sleep(1)

# Global instance
kokoro_tts = KokoroTTS()
