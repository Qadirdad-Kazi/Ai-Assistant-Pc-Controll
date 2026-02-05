import requests
import json
import sys
import os
import re
import wave
import threading
import queue
import time
import logging
import sounddevice as sd
import numpy as np
from pathlib import Path

# RealtimeSTT for wake word and speech recognition
try:
    from RealtimeSTT import AudioToTextRecorder
    REALTIMESTT_AVAILABLE = True
except ImportError:
    REALTIMESTT_AVAILABLE = False

# VRAM Monitoring
try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False


class VRAMMonitor:
    """Background thread that monitors and displays GPU VRAM usage."""
    
    def __init__(self, interval=5.0):
        self.interval = interval
        self.running = False
        self.thread = None
        
        if PYNVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.device_count = pynvml.nvmlDeviceGetCount()
                self.handles = [pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(self.device_count)]
            except Exception as e:
                print(f"[VRAM Monitor] Failed to initialize: {e}")
                self.device_count = 0
                self.handles = []
        else:
            self.device_count = 0
            self.handles = []
    
    def get_vram_usage(self):
        """Get VRAM usage for all GPUs."""
        if not PYNVML_AVAILABLE or not self.handles:
            return None
        
        usage = []
        for i, handle in enumerate(self.handles):
            try:
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                used_gb = info.used / (1024 ** 3)
                total_gb = info.total / (1024 ** 3)
                percent = (info.used / info.total) * 100
                usage.append((i, used_gb, total_gb, percent))
            except:
                pass
        return usage
    
    def print_usage(self):
        """Print current VRAM usage."""
        usage = self.get_vram_usage()
        if usage:
            for gpu_id, used, total, percent in usage:
                print(f"\r\033[90m[VRAM GPU{gpu_id}] {used:.2f}/{total:.2f} GB ({percent:.1f}%)\033[0m", end="", flush=True)
            print()  # New line
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.running:
            self.print_usage()
            time.sleep(self.interval)
    
    def start(self):
        """Start background VRAM monitoring."""
        if not PYNVML_AVAILABLE or not self.handles:
            print("[VRAM Monitor] Not available (pynvml not installed or no GPU)")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"[VRAM Monitor] Started (interval: {self.interval}s)")
    
    def stop(self):
        """Stop background monitoring."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
    
    def shutdown(self):
        """Clean up pynvml."""
        self.stop()
        if PYNVML_AVAILABLE:
            try:
                pynvml.nvmlShutdown()
            except:
                pass


# Global VRAM monitor
vram_monitor = VRAMMonitor(interval=10.0)


def check_device_status():
    """Check and print the device status for all components."""
    print(f"\n{BOLD}{'='*50}{RESET}")
    print(f"{BOLD}Device Status Check{RESET}")
    print(f"{'='*50}")
    
    # Check PyTorch CUDA availability
    import torch
    cuda_available = torch.cuda.is_available()
    print(f"  PyTorch CUDA Available: {GREEN if cuda_available else YELLOW}{cuda_available}{RESET}")
    
    if cuda_available:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_count = torch.cuda.device_count()
        print(f"  GPU: {gpu_name}")
        print(f"  GPU Count: {gpu_count}")
    else:
        print(f"  {YELLOW}WARNING: CUDA not available - models will use CPU{RESET}")
    
    # Check Router device
    if router:
        router_device = str(router.model.device)
        router_dtype = str(router.model.dtype)
        is_gpu = "cuda" in router_device
        print(f"  Router Model: {GREEN if is_gpu else YELLOW}{router_device}{RESET} ({router_dtype})")
    else:
        print(f"  Router Model: {GRAY}Not loaded{RESET}")
    
    # Check TTS engine
    if tts.piper_exe:
        print(f"  TTS Engine: PiperTTS ({tts.VOICE_MODEL})")
        print(f"  TTS Device: CPU (ONNX)")
    else:
        print(f"  TTS Engine: {GRAY}Not loaded{RESET}")
    
    # Summary
    print(f"{'='*50}")
    if vram_monitor.handles:
        vram_monitor.print_usage()
    print()


# ANSI Escape Codes for coloring output
GRAY = "\033[90m"
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"

# --- Model Configuration ---
RESPONDER_MODEL = "qwen3:0.6b"       # Conversational responses
OLLAMA_URL = "http://localhost:11434/api"
LOCAL_ROUTER_PATH = "./merged_model"

# Persistent Session for faster HTTP
http_session = requests.Session()

try:
    from core.router import FunctionGemmaRouter
except ImportError:
    print(f"{GRAY}[System] FunctionGemmaRouter not found.{RESET}")
    sys.exit(1)

# Global Router Instance
router = None

# --- Function Definitions (Official JSON Schema) ---
# The fine-tuned function gemma model routes ALL inputs and determines
# whether to use thinking mode or non-thinking mode for the qwen3 responder.
# All user inputs pass through function gemma first, which analyzes the query
# and returns either "thinking" (for complex queries) or "nonthinking" (for simple ones).
FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "control_light",
            "description": "Controls smart lights - turn on, off, or dim lights in a room",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "The action to perform: on, off, or dim"},
                    "room": {"type": "string", "description": "The room name where the light is located"}
                },
                "required": ["action", "room"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Searches the web for information using Google",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_timer",
            "description": "Sets a countdown timer for a specified duration",
            "parameters": {
                "type": "object",
                "properties": {
                    "duration": {"type": "string", "description": "Time duration like 5 minutes or 1 hour"},
                    "label": {"type": "string", "description": "Optional timer name or label"}
                },
                "required": ["duration"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Creates a new calendar event or appointment",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The event title"},
                    "date": {"type": "string", "description": "The date of the event"},
                    "time": {"type": "string", "description": "The time of the event"},
                    "description": {"type": "string", "description": "Optional event details"}
                },
                "required": ["title", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_calendar",
            "description": "Reads and retrieves calendar events for a date or time range",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "The date or date range to check"},
                    "filter": {"type": "string", "description": "Optional filter like meetings or appointments"}
                },
                "required": ["date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "passthrough",
            "description": "DEFAULT FUNCTION - Use this whenever no other function is clearly needed. This is the fallback for: greetings (hello, hi, good morning), chitchat (how are you, what's your name), general knowledge questions, explanations, conversations, and ANY query that does NOT explicitly require controlling lights, setting timers, searching the web, or managing calendar events. When in doubt, use passthrough.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thinking": {"type": "boolean", "description": "Set to true for complex reasoning/math/logic, false for simple greetings and chitchat."}
                },
                "required": ["thinking"]
            }
        }
    }
]

def route_query(user_input):
    """Route user query using local FunctionGemmaRouter."""
    global router
    if not router:
        return "passthrough", {"thinking": False}

    try:
        # Route using the fine-tuned model (thinking vs nonthinking)
        # route_with_timing returns: ((function_name, args_dict), elapsed_time)
        result, elapsed = router.route_with_timing(user_input)
        func_name, args = result
        
        # Function gemma returns either "thinking" or "nonthinking" as the function name
        if func_name == "thinking":
            return "passthrough", {"thinking": True, "router_latency": elapsed}
        elif func_name == "nonthinking":
            return "passthrough", {"thinking": False, "router_latency": elapsed}
        else:
            # If it returns any other function, treat as non-thinking for now
            return "passthrough", {"thinking": False, "router_latency": elapsed}
            
    except Exception as e:
        print(f"{GRAY}[Router Error: {e}]{RESET}")
        return "passthrough", {"thinking": False, "router_latency": 0.0}

# --- Function Execution Stubs ---
def execute_function(name, params):
    """Execute function and return response string."""
    if name == "control_light":
        action = params.get("action", "toggle")
        room = params.get("room", "room")
        if action == "on":
            return f"💡 Turned on the {room} lights."
        elif action == "off":
            return f"💡 Turned off the {room} lights."
        elif action == "dim":
            return f"💡 Dimmed the {room} lights."
        else:
            return f"💡 {action.capitalize()} the {room} lights."
    
    elif name == "web_search":
        query = params.get("query", "")
        return f"🔍 Searching the web for: {query}"
    
    elif name == "set_timer":
        duration = params.get("duration", "")
        label = params.get("label", "Timer")
        return f"⏱️ Timer set for {duration}" + (f" ({label})" if label else "")
    
    elif name == "create_calendar_event":
        title = params.get("title", "Event")
        date = params.get("date", "")
        time = params.get("time", "")
        return f"📅 Created event: {title} on {date}" + (f" at {time}" if time else "")
    
    elif name == "read_calendar":
        date = params.get("date", "today")
        return f"📆 Checking calendar for {date}..."
    
    else:
        return f"Unknown function: {name}"


# --- Direct Piper TTS Integration ---
class PiperTTS:
    """Direct Piper TTS wrapper with streaming sentence support."""
    
    VOICE_MODEL = "en_GB-northern_english_male-medium"
    MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx"
    CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json"
    
    def __init__(self):
        self.enabled = False
        self.voice = None
        self.speech_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        self.interrupt_event = threading.Event()
        self.models_dir = Path.home() / ".local" / "share" / "piper" / "voices"
        self.current_stream = None
        
        try:
            from piper import PiperVoice
            self.PiperVoice = PiperVoice
            self.available = True
        except ImportError:
            self.available = False
            print(f"{GRAY}[TTS] piper-tts not installed. Run: pip install piper-tts{RESET}")
    
    def download_model(self):
        """Download voice model if not present."""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        model_path = self.models_dir / f"{self.VOICE_MODEL}.onnx"
        config_path = self.models_dir / f"{self.VOICE_MODEL}.onnx.json"
        
        if not model_path.exists():
            print(f"{CYAN}[TTS] Downloading voice model ({self.VOICE_MODEL})...{RESET}")
            r = http_session.get(self.MODEL_URL, stream=True)
            r.raise_for_status()
            with open(model_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            r = http_session.get(self.CONFIG_URL)
            r.raise_for_status()
            with open(config_path, 'wb') as f:
                f.write(r.content)
            print(f"{GREEN}[TTS] ✓ Model downloaded!{RESET}")
        
        return str(model_path), str(config_path)
    
    def initialize(self):
        """Load the voice model."""
        if not self.available:
            print(f"{YELLOW}[TTS] piper-tts not available{RESET}")
            return False
        
        try:
            print(f"{CYAN}[TTS] Loading Piper voice model...{RESET}")
            model_path, config_path = self.download_model()
            self.voice = self.PiperVoice.load(model_path, config_path)
            self.running = True
            self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self.worker_thread.start()
            print(f"{GREEN}[TTS] ✓ Piper TTS ready ({self.VOICE_MODEL}){RESET}")
            return True
        except Exception as e:
            print(f"{YELLOW}[TTS] Failed to initialize: {e}{RESET}")
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
        """Synthesize and play text using sounddevice streaming."""
        if not self.voice or not text.strip():
            return
        
        try:
            sample_rate = self.voice.config.sample_rate
            
            with sd.OutputStream(samplerate=sample_rate, channels=1, dtype='int16', latency='low') as stream:
                self.current_stream = stream
                for audio_chunk in self.voice.synthesize(text):
                    if self.interrupt_event.is_set():
                        stream.abort()
                        break
                    data = np.frombuffer(audio_chunk.audio_int16_bytes, dtype=np.int16)
                    stream.write(data)
                self.current_stream = None
                    
        except Exception as e:
            print(f"{GRAY}[TTS Error]: {e}{RESET}")
    
    def queue_sentence(self, sentence):
        """Add a sentence to the speech queue."""
        if self.enabled and self.voice and sentence.strip():
            self.speech_queue.put(sentence)
    
    def stop(self):
        """Interrupt current speech and clear queue."""
        self.interrupt_event.set()
        with self.speech_queue.mutex:
            self.speech_queue.queue.clear()
        if self.current_stream:
            try:
                self.current_stream.abort()
            except:
                pass
            
    def wait_for_completion(self):
        """Wait for all queued speech to finish."""
        if self.enabled:
            self.speech_queue.join()
    
    def toggle(self, enable):
        """Enable/disable TTS."""
        if enable and not self.voice:
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


# --- Voice Input with RealtimeSTT ---
class VoiceInput:
    """Voice input handler with wake word detection using RealtimeSTT."""
    
    def __init__(self, wake_word="jarvis", on_text_callback=None):
        self.enabled = False
        self.recorder = None
        self.wake_word = wake_word
        self.on_text_callback = on_text_callback
        self.listening = False
        self.available = REALTIMESTT_AVAILABLE
        
        if not self.available:
            print(f"{GRAY}[Voice] RealtimeSTT not available. Install with: pip install RealtimeSTT{RESET}")
    
    def _on_recording_start(self):
        """Callback when recording starts."""
        self.listening = True
        print(f"\n{GREEN}🎤 Listening...{RESET}", end=" ", flush=True)
    
    def _on_recording_stop(self):
        """Callback when recording stops."""
        self.listening = False
        print(f"{GRAY}Processing...{RESET}")
    
    def _on_wakeword_detected(self):
        """Callback when wake word is detected."""
        print(f"\n{CYAN}👂 Wake word '{self.wake_word}' detected!{RESET}")
    
    def initialize(self):
        """Initialize the voice recorder with wake word detection."""
        if not self.available:
            return False
        
        try:
            print(f"{CYAN}[Voice] Initializing RealtimeSTT with wake word '{self.wake_word}'...{RESET}")
            
            # Initialize recorder with wake word and callbacks
            # Use pvporcupine as the wake word backend (already installed)
            self.recorder = AudioToTextRecorder(
                wake_words=self.wake_word,
                wakeword_backend="pvporcupine",  # Specify which wake word engine to use
                on_recording_start=self._on_recording_start,
                on_recording_stop=self._on_recording_stop,
                on_wakeword_detected=self._on_wakeword_detected,
                spinner=False  # Disable spinner for cleaner output
            )
            
            print(f"{GREEN}[Voice] ✓ Ready! Say '{self.wake_word}' to activate.{RESET}")
            return True
            
        except Exception as e:
            print(f"{YELLOW}[Voice] Failed to initialize: {e}{RESET}")
            print(f"{GRAY}[Voice] Try: pip install pvporcupine{RESET}")
            return False
    
    def listen_once(self):
        """Listen for wake word, then capture spoken command."""
        if not self.recorder:
            return None
        
        try:
            # This will block until wake word is detected, then record speech
            text = self.recorder.text()
            return text.strip() if text else None
        except Exception as e:
            print(f"{GRAY}[Voice Error]: {e}{RESET}")
            return None
    
    def toggle(self, enable):
        """Enable/disable voice input."""
        if enable and not self.recorder:
            if self.initialize():
                self.enabled = True
                return True
            return False
        self.enabled = enable
        return True
    
    def shutdown(self):
        """Clean up resources."""
        if self.recorder:
            try:
                self.recorder.shutdown()
            except:
                pass


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


# Global TTS instance
tts = PiperTTS()

# Global Voice Input instance
voice_input = VoiceInput()


# --- Model Preloading ---
def preload_models():
    """Client-side preload to ensure models are in memory before user interaction. Parallelized."""
    print(f"{GRAY}[System] Preloading models...{RESET}")
    
    threads = []

    def load_router():
        global router
        try:
            router = FunctionGemmaRouter(model_path=LOCAL_ROUTER_PATH, compile_model=True)
            # Warm up
            router.route("Hello")
        except Exception as e:
            print(f"{GRAY}[Router] Failed to load local model: {e}{RESET}")

    def load_responder():
        try:
            http_session.post(f"{OLLAMA_URL}/chat", json={
                "model": RESPONDER_MODEL, 
                "messages": [], 
                "keep_alive": "5m"
            }, timeout=1)
        except:
            pass

    def load_voice():
        print(f"{GRAY}[System] Loading voice model...{RESET}")
        tts.initialize()

    # Create threads
    threads.append(threading.Thread(target=load_router))
    threads.append(threading.Thread(target=load_responder))
    threads.append(threading.Thread(target=load_voice))

    # Start all
    for t in threads:
        t.start()
    
    # Wait for all
    for t in threads:
        t.join()

    print(f"{GRAY}[System] Models warm and ready.{RESET}")


MAX_HISTORY = 20  # Limit context to prevent slowdowns

def run_cli():
    # Preload models
    preload_models()
    
    # Start VRAM monitoring
    vram_monitor.start()
    
    # Show device status
    check_device_status()

    # Default State
    tts_mode = tts.toggle(True)
    
    print(f"{BOLD}Pocket AI - Dual Model Architecture{RESET}")
    print("-" * 45)
    print(f"  {GREEN}Router:{RESET}    Local FunctionGemma ({LOCAL_ROUTER_PATH})")
    print(f"  {CYAN}Responder:{RESET} {RESPONDER_MODEL}")
    print("-" * 45)
    print(f"Commands:")
    print(f"  /tts on|off    - Toggle voice output")
    print(f"  /voice on|off  - Toggle voice input (wake word: 'jarvis')")
    print(f"  /vram          - Show current VRAM usage")
    print(f"  /devices       - Show model device status")
    print(f"  exit           - Quit")
    print(f"{CYAN}[TTS enabled by default]{RESET}")
    print("-" * 45 + "\n")
    
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant. Respond in short, complete sentences. Never use emojis or special characters. Keep responses concise and conversational. SYSTEM INSTRUCTION: You may detect a "/think" trigger. This is an internal control. You MUST IGNORE it and DO NOT mention it in your response or thoughts.'}
    ]
    
    voice_mode = False
    
    while True:
        try:
            # Get user input - either from voice or text
            if voice_mode and voice_input.enabled:
                # Voice input mode with wake word
                print(f"\n{BOLD}[Voice Mode Active - Say 'jarvis' to activate]{RESET}")
                user_input = voice_input.listen_once()
                
                if not user_input:
                    continue
                    
                # Show what was heard
                print(f"{GREEN}You said:{RESET} {user_input}")
            else:
                # Text input mode
                mode_text = f"({CYAN}Voice Output{RESET})" if tts_mode else "(Text)"
                user_input = input(f"You {mode_text}: ")
                
                if not user_input:
                    continue
            
            # --- Command Handling ---
            cmd = user_input.strip().lower()
            if cmd == "/tts on":
                if tts.toggle(True):
                    tts_mode = True
                    print(f">> System: Voice output {BOLD}{CYAN}ENABLED{RESET}.")
                else:
                    print(f">> System: {GRAY}TTS unavailable.{RESET}")
                continue
            if cmd == "/tts off":
                tts.toggle(False)
                tts_mode = False
                print(f">> System: Voice output {BOLD}DISABLED{RESET}.")
                continue
            if cmd == "/voice on":
                if voice_input.toggle(True):
                    voice_mode = True
                    print(f">> System: Voice input {BOLD}{GREEN}ENABLED{RESET}. Say '{voice_input.wake_word}' to activate.")
                else:
                    print(f">> System: {GRAY}Voice input unavailable.{RESET}")
                continue
            if cmd == "/voice off":
                voice_input.toggle(False)
                voice_mode = False
                print(f">> System: Voice input {BOLD}DISABLED{RESET}.")
                continue
            if cmd == "/vram":
                vram_monitor.print_usage()
                continue
            if cmd == "/devices":
                check_device_status()
                continue
            if cmd in ['exit', 'quit']:
                vram_monitor.shutdown()
                tts.shutdown()
                voice_input.shutdown()
                print("Goodbye!")
                break
            
            # --- Step 1: Route through Function Gemma ---
            # All inputs are routed through the trained function gemma model
            # which determines whether to use thinking or non-thinking mode
            print(f"{GRAY}[Routing...]{RESET}", end=" ", flush=True)
            func_name, params = route_query(user_input)
            print(f"{GREEN}→ {func_name}{RESET} {GRAY}(thinking={params.get('thinking', False)}){RESET}")
            
            # --- Step 2: Handle based on function ---
            if func_name == "passthrough":
                # Manage context window
                if len(messages) > MAX_HISTORY:
                    # Keep system message [0] + last MAX_HISTORY messages
                    messages = [messages[0]] + messages[-(MAX_HISTORY-1):]

                # Use Qwen for conversational response
                messages.append({'role': 'user', 'content': user_input})
                
                # Enable thinking only when functiongemma explicitly requests it
                enable_thinking = params.get("thinking", False)
                
                payload = {
                    "model": RESPONDER_MODEL,
                    "messages": messages,
                    "stream": True,
                    "think": enable_thinking
                }
                
                print("AI: ", end='', flush=True)
                
                full_response = ""
                has_printed_thought = False
                sentence_buffer = SentenceBuffer() if tts_mode else None
                
                start_responder = time.time()
                with http_session.post(f"{OLLAMA_URL}/chat", json=payload, stream=True) as r:
                    r.raise_for_status()
                    
                    for line in r.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                msg = chunk.get('message', {})
                                
                                if 'thinking' in msg and msg['thinking']:
                                    print(f"{GRAY}{msg['thinking']}{RESET}", end='', flush=True)
                                    has_printed_thought = True

                                if 'content' in msg and msg['content']:
                                    if has_printed_thought:
                                        print(f"{RESET}\n\n", end='', flush=True)
                                        has_printed_thought = False
                                    
                                    content = msg['content']
                                    print(content, end='', flush=True)
                                    full_response += content
                                    
                                    # Queue complete sentences for TTS
                                    if tts_mode and sentence_buffer:
                                        sentences = sentence_buffer.add(content)
                                        for sentence in sentences:
                                            tts.queue_sentence(sentence)
                                    
                            except json.JSONDecodeError:
                                continue
                
                # Flush any remaining text
                if tts_mode and sentence_buffer:
                    remaining = sentence_buffer.flush()
                    if remaining:
                        tts.queue_sentence(remaining)
                
                total_responder_time = time.time() - start_responder
                router_time = params.get("router_latency", 0.0)
                
                # Print Timing Stats
                print(f"\n{GRAY}[Router: {router_time:.2f}s | Responder: {total_responder_time:.2f}s]{RESET}")
                
                # Wait for TTS to finish
                if tts_mode:
                    tts.wait_for_completion()
                
                print()
                messages.append({'role': 'assistant', 'content': full_response})
            
            else:
                # Execute the function locally
                result = execute_function(func_name, params)
                print(f"AI: {result}")
                
                if tts_mode:
                    # Remove emoji for TTS
                    clean_result = re.sub(r'[^\w\s.,!?-]', '', result)
                    tts.queue_sentence(clean_result)
                    tts.wait_for_completion()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    run_cli()