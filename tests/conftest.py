"""
PyTest configuration and fixtures for Wolf AI testing.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)

@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response for testing."""
    return {
        "model": "llama3.2:3b",
        "created_at": "2024-01-01T00:00:00.000000Z",
        "response": "Test response from Wolf AI",
        "done": True,
        "total_duration": 1000000,
        "load_duration": 500000,
        "prompt_eval_count": 10,
        "prompt_eval_duration": 300000,
        "eval_count": 5,
        "eval_duration": 200000
    }

@pytest.fixture
def mock_omni_parser_response():
    """Mock OmniParser response for vision testing."""
    return {
        "elements": [
            {
                "id": "element_1",
                "type": "button",
                "content": "Search",
                "bbox": [100, 200, 300, 250],
                "confidence": 0.95
            },
            {
                "id": "element_2", 
                "type": "input",
                "content": "search_bar",
                "bbox": [50, 180, 320, 220],
                "confidence": 0.88
            }
        ],
        "image_size": [1920, 1080]
    }

@pytest.fixture
def mock_screen_capture():
    """Mock screen capture for vision testing."""
    # This would be a base64 encoded PNG in real usage
    return b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

@pytest.fixture
def test_config():
    """Test configuration settings."""
    return {
        "ollama_url": "http://localhost:11434/api",
        "visual_model": "llava-phi3",
        "responder_model": "llama3.2:3b",
        "tts_engine": "kokoro",
        "stt_engine": "realtimestt",
        "omni_parser_url": "http://localhost:8001",
        "test_timeout": 30
    }

@pytest.fixture
def disable_voice_assistant():
    """Temporarily disable voice assistant for testing."""
    with patch.dict(os.environ, {'VOICE_ASSISTANT_ENABLED': 'False'}):
        yield

@pytest.fixture
def bug_watcher():
    """Bug watcher fixture for testing."""
    from core.bug_watcher import BugWatcher
    return BugWatcher()
