import importlib
import sqlite3
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


class _Signal:
    def __init__(self):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args, **kwargs):
        for callback in list(self._callbacks):
            callback(*args, **kwargs)


class _VoiceAssistantStub:
    def __init__(self):
        self.wake_word_detected = _Signal()
        self.processing_finished = _Signal()
        self.messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi commander", "metadata": {"stages": []}},
        ]
        self.current_user_prompt = ""
        self.current_stream = ""
        self.current_metadata = {}
        self.is_initialized = True

    def _on_speech(self, text):
        self.messages.append({"role": "user", "content": f"User asked: {text}\n\nRespond naturally"})
        self.messages.append(
            {
                "role": "assistant",
                "content": f"Processed: {text}",
                "metadata": {"stages": [{"name": "parse", "content": "ok"}]},
            }
        )


class _FunctionExecutorStub:
    def __init__(self):
        self.tasks = [
            {
                "id": "task_seed",
                "title": "Seed Task",
                "description": "Initial task",
                "status": "pending",
            }
        ]
        self._execution_events = [
            {
                "id": 1,
                "timestamp": "2026-04-18T12:00:00",
                "type": "info",
                "message": "Executor online",
            }
        ]
        self._event_counter = 1
        self._media_state = {
            "isPlaying": False,
            "service": "auto",
            "source": "none",
            "trackTitle": "Idle",
            "trackArtist": "Wolf AI",
            "durationSec": 0,
            "positionSec": 0,
            "volume": 70,
            "streamUrl": "",
        }
        self._local_map = {}

    def get_execution_events(self, after_id=0, limit=200):
        return [e for e in self._execution_events if e.get("id", 0) > after_id][:limit]

    def get_media_state(self):
        return dict(self._media_state)

    def control_media(self, action, **kwargs):
        if action == "play":
            self._media_state.update({"isPlaying": True, "trackTitle": kwargs.get("query", "music")})
        elif action == "pause":
            self._media_state.update({"isPlaying": False})
        elif action == "set_volume":
            self._media_state.update({"volume": int(kwargs.get("volume", 70))})
        return {"success": True, "message": f"media {action}", "data": {"state": self.get_media_state()}}

    def get_local_song_path(self, song_id):
        return self._local_map.get(song_id, "")

    def _save_tasks(self):
        return True

    def execute(self, func_name, params):
        if func_name == "create_task":
            task = {
                "id": f"task_{len(self.tasks) + 1}",
                "title": params.get("title", "Untitled"),
                "description": params.get("description", ""),
                "status": "pending",
            }
            self.tasks.append(task)
            return {"success": True, "message": "task created", "data": {"task": task}}

        if func_name == "edit_task":
            task_id = params.get("task_id")
            for task in self.tasks:
                if task["id"] == task_id:
                    task["title"] = params.get("title", task["title"])
                    task["description"] = params.get("description", task["description"])
                    return {"success": True, "message": "task updated", "data": {"task": task}}
            return {"success": False, "message": "task not found"}

        if func_name == "execute_task":
            task_id = params.get("task_id")
            self._event_counter += 1
            self._execution_events.append(
                {
                    "id": self._event_counter,
                    "timestamp": "2026-04-18T12:00:01",
                    "type": "task",
                    "message": "Executed task",
                    "task_id": task_id,
                }
            )
            for task in self.tasks:
                if task["id"] == task_id:
                    task["status"] = "completed"
            return {"success": True, "message": "executed", "data": {"result": {"task_id": task_id}}}

        return {"success": True, "message": f"executed {func_name}"}


class _SettingsStoreStub:
    def __init__(self):
        self._defaults = {
            "theme": "Dark",
            "general": {"max_history": 20},
            "models": {"chat": "llama3.2:3b", "router": "./merged_model"},
            "ollama_url": "http://localhost:11434",
            "tts": {"engine": "kokoro", "voice": "af_heart"},
            "wake_word": {"keyword": "wolf", "sensitivity": 0.6, "confirmation_count": 1},
            "picovoice": {"enabled": False, "key": "", "ppn_path": "resources/wakewords/hey_wolf.ppn"},
            "phone": {"connection_mode": "None"},
            "gsm": {"port": "COM3"},
            "sip": {"server_ip": "0.0.0.0"},
            "bug_watcher": {"enabled": False},
            "hud": {"enabled": False},
            "spotify": {"client_id": "", "client_secret": ""},
        }
        self._data = self._deep_copy(self._defaults)

    def _deep_copy(self, obj):
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        return obj

    def get_all(self):
        return self._deep_copy(self._data)

    def reset_to_defaults(self):
        self._data = self._deep_copy(self._defaults)

    def get(self, key_path, default=None):
        node = self._data
        for key in key_path.split("."):
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def set(self, key_path, value):
        node = self._data
        parts = key_path.split(".")
        for key in parts[:-1]:
            node = node.setdefault(key, {})
        node[parts[-1]] = value


class _PrivacyTrackerStub:
    def get_logs(self):
        return [
            {
                "id": 1,
                "timestamp": "2026-04-18T12:00:00",
                "service": "Ollama",
                "direction": "SENT",
                "type": "chat",
                "summary": "Prompt sent",
                "size": 128,
            }
        ]


class _ReceptionistStub:
    def __init__(self):
        self.call_logs = [
            {
                "id": "call_1",
                "caller": "Amazon",
                "status": "handled",
                "instructions": "Pitch premium",
                "transcript": "hello from amazon",
                "timestamp": "2026-04-18T11:58:00",
                "document_path": "data/documents/proposals/demo.md",
                "client_mood": "Positive",
            }
        ]


class _AnalyticsEngineStub:
    def get_summary_metrics(self):
        return {"pipeline_value": 5000, "total_calls": 3, "total_tasks": 7, "success_rate": 92}

    def get_top_clients(self):
        return [{"caller_id": "Amazon", "call_count": 2, "total_value": 4000, "avg_sentiment": 8.4}]

    def get_deal_heatmap(self):
        return [{"mood": "Positive", "value": 4000}, {"mood": "Neutral", "value": 1000}]


class _DBStub:
    def __init__(self, db_path):
        self.db_path = str(db_path)

    def get_action_logs(self, limit=50):
        return [
            {
                "id": 1,
                "action_name": "open_app",
                "status": "success",
                "details": "Opened VS Code",
                "timestamp": "2026-04-18T12:00:00",
            }
        ][:limit]

    def get_call_logs(self, limit=50):
        return [
            {
                "id": "call_1",
                "caller": "Amazon",
                "status": "handled",
                "instructions": "Pitch premium",
                "transcript": "hello from amazon",
                "timestamp": "2026-04-18T11:58:00",
                "document_path": "data/documents/proposals/demo.md",
                "client_mood": "Positive",
            }
        ][:limit]


def _install_module(name, attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


@pytest.fixture(scope="session")
def app_module(tmp_path_factory):
    tmp_root = tmp_path_factory.mktemp("wolf_test_data")
    db_path = tmp_root / "wolf_core.db"

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS learned_heuristics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT UNIQUE,
                learned_plan TEXT,
                success_count INTEGER DEFAULT 0,
                timestamp TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO learned_heuristics (query, learned_plan, success_count, timestamp) VALUES (?, ?, ?, ?)",
            ("follow up email", "[]", 2, "2026-04-18T12:00:00"),
        )
        conn.commit()

    voice_assistant = _VoiceAssistantStub()
    function_executor = _FunctionExecutorStub()
    settings_store = _SettingsStoreStub()

    _install_module("core.voice_assistant", {"voice_assistant": voice_assistant})
    _install_module("core.function_executor", {"executor": function_executor})
    _install_module("core.productivity_suite", {"productivity_suite": object()})
    _install_module("core.analytics_engine", {"analytics_engine": _AnalyticsEngineStub()})
    _install_module("core.model_manager", {"model_manager": object()})
    _install_module("core.database", {"db": _DBStub(db_path)})
    _install_module("core.receptionist", {"receptionist": _ReceptionistStub()})
    _install_module("core.settings_store", {"settings": settings_store})
    _install_module("core.privacy_tracker", {"privacy_tracker": _PrivacyTrackerStub()})
    _install_module(
        "core.pc_control",
        {
            "pc_controller": types.SimpleNamespace(
                confirmation_callback=None,
                clarification_callback=None,
            )
        },
    )
    _install_module(
        "core.gsm_gateway",
        {"gsm_gateway": types.SimpleNamespace(is_connected=False, on_call_incoming=None, connect=lambda: True)},
    )
    _install_module(
        "config",
        {
            "VOICE_ASSISTANT_ENABLED": True,
            "OLLAMA_URL": "http://fake-ollama:11434",
            "LOCAL_ROUTER_PATH": str(tmp_root),
            "CUSTOM_PPN_PATH": str(tmp_root / "wakeword.ppn"),
        },
    )

    if "backend_api" in sys.modules:
        del sys.modules["backend_api"]

    module = importlib.import_module("backend_api")

    class _Response:
        status_code = 200

    module.requests.get = lambda *args, **kwargs: _Response()
    return module


@pytest.fixture()
def client(app_module):
    with TestClient(app_module.app) as test_client:
        yield test_client


@pytest.fixture()
def backend_state(app_module):
    return app_module


@pytest.fixture()
def repo_root():
    return Path(__file__).resolve().parents[1]