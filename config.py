"""
Centralized configuration for Wolf AI.
"""

# --- Model Configuration ---
RESPONDER_MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api"
LOCAL_ROUTER_PATH = "./merged_model"
HF_ROUTER_REPO = "nlouis/wolf-ai-router"  # Hugging Face repo for auto-download
MAX_HISTORY = 20

# --- TTS Configuration ---
# Available voices: "Male (Northern)", "Female (Alba)"
TTS_VOICE_MODEL = "Male (Northern)"
TTS_MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx"
TTS_CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json"

# --- STT Configuration ---
# Using RealTimeSTT for real-time speech-to-text
STT_MODEL_PATH = None  # Not used with RealTimeSTT (kept for compatibility)
STT_USE_WHISPER = False  # Not used with RealTimeSTT (kept for compatibility)
WHISPER_MODEL_SIZE = "base"  # Not used with RealTimeSTT (kept for compatibility)
WAKE_WORD_DETECTION_METHOD = "transcription"  # RealTimeSTT uses transcription-based detection
REALTIMESTT_MODEL = "small"  # Upgraded from 'base' for better wake word detection accuracy
USE_PORCUPINE_WAKE_WORD = False  # Use Porcupine for wake word detection (more accurate, requires API key)
PORCUPINE_ACCESS_KEY = None  # Get from https://console.picovoice.ai/ (optional, for better wake word detection)
WAKE_WORD = "wolf"
WAKE_WORD_SENSITIVITY = 0.6  # Increased for better custom word detection
WAKE_WORD_CONFIRMATION_COUNT = 1  # Require multiple detections before triggering (reduces false positives)
STT_SAMPLE_RATE = 16000
STT_CHUNK_SIZE = 4096
STT_RECORD_TIMEOUT = 5.0  # Maximum seconds to record after wake word

# --- Voice Assistant Configuration ---
VOICE_ASSISTANT_ENABLED = True
LLM_TIMEOUT_SECONDS = 300  # 5 minutes of inactivity before sleep
LLM_KEEP_ALIVE = "5m"  # Keep in memory for 5 minutes after last use

# --- Router Keywords ---
# REMOVED: ROUTER_KEYWORDS - All queries now go through Function Gemma router
# The router handles all routing decisions, so keyword-based bypass is no longer needed

# --- Function Definitions (Simplified for PC Control & Brain) ---
FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "pc_control",
            "description": "Execute system-level commands like controlling volume, opening apps, or locking the PC.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "The system action: open_app, close_app, volume, lock, etc."},
                    "target": {"type": "string", "description": "The app name or specific value (e.g., 'Spotify', '50')"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_music",
            "description": "Play a song, artist, or playlist via YouTube or Spotify.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The song title or artist"},
                    "service": {"type": "string", "enum": ["youtube", "spotify"], "description": "Preferred service"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "passthrough",
            "description": "DEFAULT - Use for greetings, chitchat, and general knowledge questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thinking": {"type": "boolean", "description": "True for complex logic, False for simple chat."}
                },
                "required": ["thinking"]
            }
        }
    }
]

# --- Console Colors ---
GRAY = "\033[90m"
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"

# --- Spotify Configuration ---
# Get these from https://developer.spotify.com/dashboard
SPOTIPY_CLIENT_ID = None
SPOTIPY_CLIENT_SECRET = None
SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback"
