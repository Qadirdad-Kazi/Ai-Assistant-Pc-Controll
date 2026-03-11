"""
TTS (Text-to-Speech) module using Piper TTS executable.
Provides streaming sentence-based synthesis with interrupt support.
"""

import io
import os
import queue
import threading
import time
import json
import re
import base64
import zipfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from config import OLLAMA_URL, GREEN, CYAN, YELLOW, GRAY, RESET
import requests
import sounddevice as sd  # type: ignore

# ANSI colors for console output
GRAY = "\033[90m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"

# HTTP session for downloads
http_session = requests.Session()

PIPER_VOICES = {
    "Male (Northern)": {
        "model": "en_GB-northern_english_male-medium",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx",
        "config": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json"
    },
    "Female (Alba)": {
        "model": "en_GB-alba-medium",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx",
        "config": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx.json"
    }
}


class SentenceBuffer:
    """Buffers streaming text and extracts complete sentences."""
    
    SENTENCE_ENDINGS = re.compile(r'([.!?])\s+|([.!?])$')
    
    def __init__(self):
        self.buffer = ""
    
    def add(self, text):
        """Add text chunk and return any complete sentences."""
        self.buffer += text
        sentences = []
        
        while True:
            match = self.SENTENCE_ENDINGS.search(self.buffer)
            if match:
                end_pos = match.end()
                sentence = self.buffer[:end_pos].strip()
                if sentence:
                    sentences.append(sentence)
                self.buffer = self.buffer[end_pos:]
            else:
                break
        
        return sentences
    
    def flush(self):
        """Return any remaining text as a final sentence."""
        remaining = self.buffer.strip()
        self.buffer = ""
        return remaining if remaining else None


class PiperTTS:
    """Piper TTS wrapper using pre-built executable for Windows compatibility."""
    
    # Piper Windows executable
    PIPER_VERSION = "2023.11.14-2"
    PIPER_RELEASE_URL = f"https://github.com/rhasspy/piper/releases/download/{PIPER_VERSION}/piper_windows_amd64.zip"
    
    def __init__(self, model_name="lessac", voice_key="lessac"):
        self.model_name = model_name
        self.voice_key = voice_key
        self.piper_dir = Path("models/piper")
        self.models_dir = Path("models/voices")
        self.piper_exe = None
        self.model_path = None
        self.enabled = False  # Initialize enabled state
        self.sentence_buffer = SentenceBuffer()
        self.speech_worker = None
        self.speech_queue = queue.Queue()
        self.stop_speech = threading.Event()
        self.interrupt_event = threading.Event()
        self.current_process = None
        self.running = False
        self._init_lock = threading.RLock()
        self.available = False
        self.worker_thread = None
        self.completion_callback = None
        
        # Delay heavy initialization until first use to improve startup time.
        self.enabled = False

    def _find_piper_executable(self) -> Optional[str]:
        """Find Piper executable across known extraction layouts."""
        candidates = [
            self.piper_dir / "piper.exe",
            self.piper_dir / "piper" / "piper.exe",
            self.piper_dir / "piper_windows" / "piper.exe",
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return str(candidate.resolve())
        return None
    
    def _initialize_piper(self) -> bool:
        """Initialize Piper TTS executable."""
        try:
            # Check if Piper executable already exists in any known layout.
            existing_exe = self._find_piper_executable()

            if existing_exe:
                self.piper_exe = existing_exe
                print(f"{GREEN}[TTS] ✓ Piper executable found: {self.piper_exe}{RESET}")
                return True
            else:
                # Try to download Piper executable
                print(f"{CYAN}[TTS] Piper executable not found. Downloading...{RESET}")
                downloaded_exe = self._download_piper_executable()
                if downloaded_exe and Path(downloaded_exe).exists():
                    self.piper_exe = str(Path(downloaded_exe).resolve())
                    print(f"{GREEN}[TTS] ✓ Piper executable ready: {self.piper_exe}{RESET}")
                    return True
                else:
                    print(f"{YELLOW}[TTS] ⚠️ Could not download Piper executable{RESET}")
                    return False
                    
        except Exception as e:
            print(f"{YELLOW}[TTS] Failed to initialize Piper: {e}{RESET}")
            return False
    
    def _load_voice_model(self):
        """Load the voice model for the current voice key."""
        try:
            model_path = self._download_model(self.voice_key)
            self.model_path = model_path
            print(f"{GREEN}[TTS] ✓ Voice model loaded: {self.voice_key}{RESET}")
        except Exception as e:
            print(f"{GRAY}[TTS] Failed to load voice model: {e}{RESET}")
            self.model_path = None
    
    def _download_piper_executable(self) -> Optional[str]:
        try:
            # Create piper directory if it doesn't exist
            self.piper_dir.mkdir(parents=True, exist_ok=True)
            print(f"{CYAN}[TTS] Downloading Piper executable...{RESET}")
            
            # Download URL for Windows
            piper_url = f"https://github.com/rhasspy/piper/releases/download/{self.PIPER_VERSION}/piper_windows_amd64.zip"
            
            # Download to memory
            response = requests.get(piper_url, timeout=30)
            response.raise_for_status()
            
            if response.status_code == 200:
                # Extract to memory
                import zipfile
                with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                    zip_ref.extractall(self.piper_dir)
                    print(f"{GREEN}[TTS] ✓ Piper executable downloaded and extracted{RESET}")
                    detected_exe = self._find_piper_executable()
                    if detected_exe:
                        return detected_exe
                    print(f"{YELLOW}[TTS] Piper extracted, but executable path was not found{RESET}")
                    return None
            else:
                print(f"{GRAY}[TTS] Failed to download Piper. Status: {response.status_code}{RESET}")
                return None
                
        except Exception as e:
            print(f"{YELLOW}[TTS] Failed to download Piper: {e}{RESET}")
            return None
    
    def _download_model(self, voice_key: str) -> Optional[str]:
        """Download voice model if not present."""
        voice_data = PIPER_VOICES.get(voice_key, PIPER_VOICES["Male (Northern)"])
        model_name = voice_data["model"]
        model_url = voice_data["url"]
        config_url = voice_data["config"]
        
        self.models_dir.mkdir(parents=True, exist_ok=True)
        model_path = self.models_dir / f"{model_name}.onnx"
        config_path = self.models_dir / f"{model_name}.onnx.json"
        
        if not model_path.exists():
            print(f"{CYAN}[TTS] Downloading voice model ({model_name})...{RESET}")
            r = http_session.get(model_url, stream=True)
            r.raise_for_status()
            with open(model_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            r = http_session.get(config_url)
            r.raise_for_status()
            with open(config_path, 'wb') as f:
                f.write(r.content)
            print(f"{GREEN}[TTS] ✓ Model downloaded!{RESET}")
        
        return str(model_path)
    
    def initialize(self):
        """Set up Piper executable and initial voice model."""
        with self._init_lock:
            if self.enabled and self.piper_exe and self.model_path and self.running:
                return True

            try:
                from core.settings_store import settings
                current_voice = settings.get("tts.voice", "Male (Northern)")

                print(f"{CYAN}[TTS] Initializing Piper TTS (executable mode)...{RESET}")

                # Check if Piper executable already exists in any known layout.
                existing_exe = self._find_piper_executable()
                if existing_exe:
                    self.piper_exe = existing_exe
                    print(f"{GREEN}[TTS] ✓ Piper executable found: {self.piper_exe}{RESET}")
                else:
                    print(f"{CYAN}[TTS] Piper executable not found. Downloading...{RESET}")
                    self.piper_exe = self._download_piper_executable()
                    if not self.piper_exe or not Path(self.piper_exe).exists():
                        print(f"{YELLOW}[TTS] Could not set up Piper executable{RESET}")
                        self.available = False
                        return False

                # Download/find voice model
                self.model_path = self._download_model(current_voice)
                if self.model_path:
                    self.model_path = str(Path(self.model_path).resolve())

                # Test the executable
                try:
                    if not self.piper_exe or not Path(self.piper_exe).exists():
                        raise FileNotFoundError(f"Piper executable not found at: {self.piper_exe}")
                    result = subprocess.run(
                        [self.piper_exe, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=str(Path(self.piper_exe).parent)
                    )
                    print(f"{CYAN}[TTS] Piper version: {result.stdout.strip()}{RESET}")
                except Exception as e:
                    print(f"{YELLOW}[TTS] Warning: Could not get Piper version: {e}{RESET}")

                # Start the worker thread
                if not self.running:
                    self.running = True
                    self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
                    self.worker_thread.start()
                self.enabled = True
                self.available = True

                print(f"{GREEN}[TTS] [OK] Piper TTS ready ({current_voice}){RESET}")
                return True

            except Exception as e:
                print(f"{YELLOW}[TTS] Failed to initialize: {e}{RESET}")
                import traceback
                traceback.print_exc()
                return False
    
    def _speech_worker(self):
        """Background thread that plays queued sentences."""
        while self.running:
            try:
                if self.interrupt_event.is_set():
                    self.interrupt_event.clear()
                
                text = self.speech_queue.get(timeout=0.5)
                if text is None:
                    break
                
                if self.interrupt_event.is_set():
                    self.speech_queue.task_done()
                    continue

                self._speak_text(text)
                self.speech_queue.task_done()
            except queue.Empty:
                continue
    
    def _speak_text(self, text):
        """Synthesize text to WAV file then play. Avoids audio device conflicts with STT."""
        if not self.piper_exe or not self.model_path or not text.strip():
            return
        
        import tempfile
        import soundfile as sf
        
        tmp_wav = None
        try:
            # Write output to a temp WAV file — Piper never touches the audio device this way,
            # preventing the 0xC0000409 crash caused by audio driver conflicts with open STT streams.
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp_wav = f.name
            
            cmd = [
                str(self.piper_exe),
                "--model", str(self.model_path),
                "--output_file", tmp_wav,
                "--quiet"
            ]
            
            self.current_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                cwd=str(Path(self.piper_exe).parent),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            _, stderr = self.current_process.communicate(
                input=(text.strip() + "\n").encode('utf-8'),
                timeout=30
            )
            
            if self.interrupt_event.is_set():
                if self.current_process: self.current_process.kill()
                self.current_process = None
                return
            
            if self.current_process.returncode != 0:
                err_msg = stderr.decode('utf-8', errors='ignore').strip()
                print(f"{YELLOW}[TTS] Piper error (code {self.current_process.returncode}): {err_msg}{RESET}")
                self.current_process = None
                return
            
            self.current_process = None
            
            # Play the WAV file
            if tmp_wav and os.path.exists(tmp_wav) and not self.interrupt_event.is_set():
                data, samplerate = sf.read(tmp_wav, dtype='int16')
                if len(data) > 0:
                    sd.play(data, samplerate=samplerate, blocking=True)
                
        except subprocess.TimeoutExpired:
            print(f"{YELLOW}[TTS] Synthesis timeout{RESET}")
            if self.current_process:
                self.current_process.kill()
                self.current_process = None
        except Exception as e:
            print(f"{YELLOW}[TTS Error]: {e}{RESET}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up temp file
            if tmp_wav and os.path.exists(tmp_wav):
                try:
                    os.remove(tmp_wav)
                except:
                    pass
    
    def queue_sentence(self, sentence):
        """Add a sentence to the speech queue."""
        if self.enabled and self.piper_exe and sentence.strip():
            self.speech_queue.put(sentence)

    def speak(self, text: str) -> bool:
        """Backward-compatible synchronous speak API used by older call sites."""
        if not text or not text.strip():
            return False

        if not self.enabled:
            if not self.initialize():
                return False

        self.queue_sentence(text)
        self.wait_for_completion()
        return True
    
    def stop(self):
        """Interrupt current speech and clear queue."""
        self.interrupt_event.set()
        with self.speech_queue.mutex:
            self.speech_queue.queue.clear()
        
        # Stop current playback
        try:
            sd.stop()
        except:
            pass
        
        # Kill current piper process if running
        if self.current_process:
            try:
                self.current_process.kill()
            except:
                pass
            
    def set_completion_callback(self, callback):
        """Set callback to be called when speech finishes."""
        self.completion_callback = callback
    
    def wait_for_completion(self):
        """Wait for all queued speech to finish."""
        if self.enabled:
            self.speech_queue.join()
            # Call completion callback if set
            if self.completion_callback:
                self.completion_callback()
    
    def update_voice(self, voice_key: str):
        """Switch to a different voice model."""
        if voice_key in PIPER_VOICES:
            self.model_path = self._download_model(voice_key)
            print(f"{GREEN}[TTS] ✓ Switched to voice: {voice_key}{RESET}")

    def toggle(self, enable):
        """Enable/disable TTS."""
        if enable and not self.piper_exe:
            if self.initialize():
                self.enabled = True
                return True
            return False
        self.enabled = enable
        return True
    
    def shutdown(self):
        """Clean up resources."""
        self.running = False
        self.stop()
        self.speech_queue.put(None)


# Global TTS instance
tts = PiperTTS()
