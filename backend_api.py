import asyncio
import os
import sqlite3
import shutil
import psutil  
import requests  
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  
from fastapi import HTTPException  
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.responses import FileResponse  
from pydantic import BaseModel  
from typing import Optional, Dict, List, Any, cast
from core.voice_assistant import voice_assistant  
from core.function_executor import executor as function_executor  
from core.database import db  
from core.receptionist import receptionist  
from core.settings_store import settings as settings_store  
from config import VOICE_ASSISTANT_ENABLED, OLLAMA_URL, LOCAL_ROUTER_PATH, CUSTOM_PPN_PATH  

app = FastAPI(title="Wolf AI Backend API")

# Setup CORS to allow the frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint for startup script."""
    return {"status": "healthy", "service": "Wolf AI Backend"}

@app.get("/api/status")
async def get_system_status():
    """Get system status for startup script."""
    return system_status

@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html."""
    frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
    index_file = os.path.join(frontend_dist, "index.html")
    
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        return {"message": "Frontend not built. Run 'cd frontend && npm run build'"}

# Global status tracking dictionary mimicking actual backend state
system_status = {
    "isListening": False,
    "Voice Core": "ACTIVE" if VOICE_ASSISTANT_ENABLED else "OFFLINE",
    "System Control": "READY",
    "Neural Sonic": "STANDBY",
    "Dev Agent": "IDLE"
}

from typing import Optional, Dict, List, Any

diagnostics_state: Dict[str, Dict[str, Any]] = {
    "router_api": {"key": "router_api", "title": "Router API", "desc": "Test local LLM and Ollama bindings", "status": "READY", "ok": None, "detail": "Awaiting test run", "checked_at": None},
    "local_database": {"key": "local_database", "title": "Local Database", "desc": "Verify SQLite read/write access", "status": "READY", "ok": None, "detail": "Awaiting test run", "checked_at": None},
    "tts_engine": {"key": "tts_engine", "title": "TTS Engine", "desc": "Check Piper speech synthesis binaries", "status": "READY", "ok": None, "detail": "Awaiting test run", "checked_at": None},
    "kokoro_tts": {"key": "kokoro_tts", "title": "Kokoro TTS", "desc": "Check Kokoro neural TTS model", "status": "READY", "ok": None, "detail": "Awaiting test run", "checked_at": None},
    "stt_engine": {"key": "stt_engine", "title": "STT Engine", "desc": "Validate Transcription vs Porcupine engine", "status": "READY", "ok": None, "detail": "Awaiting test run", "checked_at": None},
    "pc_control": {"key": "pc_control", "title": "PC Control", "desc": "Check screen control and system permissions", "status": "READY", "ok": None, "detail": "Awaiting test run", "checked_at": None},
    "phone_gateway": {"key": "phone_gateway", "title": "Phone Gateway", "desc": "Validate SIP/GSM hardware connection", "status": "READY", "ok": None, "detail": "Awaiting test run", "checked_at": None},
    "ocr_vision": {"key": "ocr_vision", "title": "OCR Vision", "desc": "Detect Tesseract engine for Bug Watcher", "status": "READY", "ok": None, "detail": "Awaiting test run", "checked_at": None},
    "omni_parser": {"key": "omni_parser", "title": "OmniParser", "desc": "Check UI parsing and grounding system", "status": "READY", "ok": None, "detail": "Awaiting test run", "checked_at": None},
    "memory_system": {"key": "memory_system", "title": "Memory System", "desc": "Verify memory storage and recall functions", "status": "READY", "ok": None, "detail": "Awaiting test run", "checked_at": None},
    "gpu_acceleration": {"key": "gpu_acceleration", "title": "GPU Acceleration", "desc": "Check CUDA and GPU availability", "status": "READY", "ok": None, "detail": "Awaiting test run", "checked_at": None},
    "voice_assistant": {"key": "voice_assistant", "title": "Voice Assistant", "desc": "Check voice assistant initialization", "status": "READY", "ok": None, "detail": "Awaiting test run", "checked_at": None},
}


def _diagnostic_result(ok: bool, detail: str):
    return ok, detail


def _check_router_api():
    base = OLLAMA_URL.replace("/api", "")
    try:
        resp = requests.get(f"{base}/api/tags", timeout=4)
        if resp.status_code == 200:
            model_files_ok = os.path.isdir(LOCAL_ROUTER_PATH)
            model_note = "router model dir found" if model_files_ok else "router model dir missing"
            return _diagnostic_result(True, f"Ollama reachable (200), {model_note}")
        return _diagnostic_result(False, f"Ollama returned status {resp.status_code}")
    except Exception as e:
        return _diagnostic_result(False, f"Ollama unreachable: {e}")


def _check_local_database():
    try:
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("SELECT 1")
        return _diagnostic_result(True, f"SQLite reachable at {db.db_path}")
    except Exception as e:
        return _diagnostic_result(False, f"Database error: {e}")


def _check_tts_engine():
    voice_dir = os.path.join("models", "piper", "voices")
    fallback_voice = os.path.join("voices", "en_GB-northern_english_male-medium.onnx")
    has_voice_dir = os.path.isdir(voice_dir)
    has_fallback = os.path.exists(fallback_voice)
    if has_voice_dir or has_fallback:
        where = voice_dir if has_voice_dir else fallback_voice
        return _diagnostic_result(True, f"Piper assets found at {where}")
    return _diagnostic_result(False, "Piper voice assets not found")


def _check_stt_engine():
    try:
        from RealtimeSTT import AudioToTextRecorder   # noqa: F401
        ppn_ok = os.path.exists(CUSTOM_PPN_PATH)
        suffix = "custom wakeword found" if ppn_ok else "custom wakeword file missing"
        return _diagnostic_result(True, f"RealtimeSTT import ok, {suffix}")
    except Exception as e:
        return _diagnostic_result(False, f"RealtimeSTT import failed: {e}")


def _check_pc_control():
    try:
        has_code = shutil.which("code") is not None
        has_ps = shutil.which("powershell") is not None
        if has_ps:
            note = "PowerShell available"
            if has_code:
                note += ", VS Code CLI available"
            return _diagnostic_result(True, note)
        return _diagnostic_result(False, "PowerShell executable not found")
    except Exception as e:
        return _diagnostic_result(False, f"PC control precheck failed: {e}")


def _check_phone_gateway():
    try:
        from core.gsm_gateway import gsm_gateway  
        status = "connected" if gsm_gateway.is_connected else "not connected"
        return _diagnostic_result(True, f"GSM gateway loaded, current status: {status}")
    except Exception as e:
        return _diagnostic_result(False, f"GSM gateway unavailable: {e}")


def _check_ocr_vision():
    tesseract_default = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    if os.path.exists(tesseract_default):
        return _diagnostic_result(True, f"Tesseract found at {tesseract_default}")
    return _diagnostic_result(False, "Tesseract executable not found at default path")


def _check_kokoro_tts():
    """Check Kokoro TTS model availability."""
    try:
        kokoro_path = os.path.join("models", "kokoro", "kokoro-v0_19.pth")
        if os.path.exists(kokoro_path):
            return _diagnostic_result(True, f"Kokoro model found at {kokoro_path}")
        else:
            return _diagnostic_result(False, f"Kokoro model not found at {kokoro_path}")
    except Exception as e:
        return _diagnostic_result(False, f"Kokoro TTS check failed: {e}")


def _check_omni_parser():
    """Check OmniParser availability."""
    try:
        omni_path = os.path.join("engines", "omni_parser")
        if os.path.exists(omni_path):
            return _diagnostic_result(True, f"OmniParser found at {omni_path}")
        else:
            return _diagnostic_result(False, f"OmniParser not found at {omni_path}")
    except Exception as e:
        return _diagnostic_result(False, f"OmniParser check failed: {e}")


def _check_memory_system():
    """Check memory system functionality."""
    try:
        memory_dir = "data/memory"
        if os.path.exists(memory_dir):
            files = os.listdir(memory_dir)
            return _diagnostic_result(True, f"Memory directory found with {len(files)} files")
        else:
            return _diagnostic_result(False, f"Memory directory not found at {memory_dir}")
    except Exception as e:
        return _diagnostic_result(False, f"Memory system check failed: {e}")


def _check_gpu_acceleration():
    """Check GPU and CUDA availability."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
            return _diagnostic_result(True, f"CUDA available with {gpu_count} GPU(s): {gpu_name}")
        else:
            return _diagnostic_result(False, "CUDA not available, using CPU")
    except Exception as e:
        return _diagnostic_result(False, f"GPU check failed: {e}")


def _check_voice_assistant():
    """Check voice assistant initialization."""
    try:
        from core.voice_assistant import voice_assistant  
        if hasattr(voice_assistant, 'is_initialized') and voice_assistant.is_initialized:
            return _diagnostic_result(True, "Voice assistant initialized")
        else:
            return _diagnostic_result(False, "Voice assistant not initialized")
    except Exception as e:
        return _diagnostic_result(False, f"Voice assistant check failed: {e}")


diagnostic_checkers = {
    "router_api": _check_router_api,
    "local_database": _check_local_database,
    "tts_engine": _check_tts_engine,
    "kokoro_tts": _check_kokoro_tts,
    "stt_engine": _check_stt_engine,
    "pc_control": _check_pc_control,
    "phone_gateway": _check_phone_gateway,
    "ocr_vision": _check_ocr_vision,
    "omni_parser": _check_omni_parser,
    "memory_system": _check_memory_system,
    "gpu_acceleration": _check_gpu_acceleration,
    "voice_assistant": _check_voice_assistant,
}


def run_single_diagnostic(key: str):
    if key not in diagnostics_state or key not in diagnostic_checkers:
        raise HTTPException(status_code=404, detail=f"Unknown diagnostic: {key}")

    diagnostics_state[key]["status"] = "RUNNING"
    ok, detail = diagnostic_checkers[key]()
    diagnostics_state[key]["ok"] = bool(ok)
    diagnostics_state[key]["detail"] = str(detail)
    diagnostics_state[key]["status"] = "PASS" if ok else "FAIL"
    diagnostics_state[key]["checked_at"] = float(asyncio.get_event_loop().time())
    return diagnostics_state[key]


def get_diagnostics_payload():
    return {"diagnostics": list(diagnostics_state.values())}

# Connect to the voice assistant's signals to dynamically update state
if VOICE_ASSISTANT_ENABLED:
    def on_wake_word():
        system_status["isListening"] = True
    def on_processing_finished():
        system_status["isListening"] = False

    voice_assistant.wake_word_detected.connect(on_wake_word)
    voice_assistant.processing_finished.connect(on_processing_finished)

# Track previous network stats for bandwidth calculation
last_net_io = psutil.net_io_counters()
last_net_time = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0

@app.websocket("/ws/system")
async def websocket_system_monitor(websocket: WebSocket):
    global last_net_io, last_net_time
    await websocket.accept()
    
    if not last_net_time:
        last_net_time = asyncio.get_event_loop().time()
        
    try:
        while True:
            # CPU & RAM
            cpu_percent = psutil.cpu_percent(interval=0)
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            
            # Network Calculation (Mbps)
            current_net_io = psutil.net_io_counters()
            current_time = asyncio.get_event_loop().time()
            time_delta = current_time - last_net_time
            
            if time_delta > 0:
                bytes_sent = current_net_io.bytes_sent - last_net_io.bytes_sent
                bytes_recv = current_net_io.bytes_recv - last_net_io.bytes_recv
                
                # Convert bytes/sec to Mbps
                net_up = (bytes_sent * 8) / (1024 * 1024) / time_delta
                net_down = (bytes_recv * 8) / (1024 * 1024) / time_delta
            else:
                net_up = 0.0
                net_down = 0.0
                
            last_net_io = current_net_io
            last_net_time = current_time

            data = {
                "cpu": int(cpu_percent),
                "ram": int(ram_percent),
                "netUp": float(f"{net_up:.1f}"),
                "netDown": float(f"{net_down:.1f}")
            }
            await websocket.send_json(data)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass

@app.websocket("/ws/status")
async def websocket_system_status(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Sync the Voice Core status based on the boolean
            if VOICE_ASSISTANT_ENABLED:
                system_status["Voice Core"] = "LISTENING" if system_status["isListening"] else "ACTIVE"
            
            # Neural Sonic status is already set by TTS in system_status
            # Don't override it with media state which is for music playback
                
            await websocket.send_json(system_status)
            await asyncio.sleep(0.5) # Send updates twice a second
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/diagnostics")
async def websocket_diagnostics(websocket: WebSocket):
    await websocket.accept()
    try:
        last_hash = ""
        while True:
            payload = get_diagnostics_payload()
            payload_hash = str(payload)
            if payload_hash != last_hash:
                await websocket.send_json(payload)
                last_hash = payload_hash
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass

class ChatMessage(BaseModel):
    text: str

class MediaControlRequest(BaseModel):
    action: str
    query: Optional[str] = None
    service: Optional[str] = None
    volume: Optional[int] = None
    positionSec: Optional[int] = None


class DiagnosticsRunRequest(BaseModel):
    key: Optional[str] = None


class SettingsUpdateRequest(BaseModel):
    settings: dict


def _flatten_settings(data: dict, prefix: str = ""):
    flat = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten_settings(value, path))
        else:
            flat[path] = value
    return flat


def _apply_runtime_setting(key_path: str, value):
    """Apply a subset of settings immediately to running modules when safe."""
    try:
        if key_path == "gsm.port":
            from core.gsm_gateway import gsm_gateway  
            gsm_gateway.port = str(value)
        elif key_path == "bug_watcher.enabled":
            from core.bug_watcher import bug_watcher  
            if bool(value):
                bug_watcher.start()
            else:
                bug_watcher.stop()
        elif key_path == "tts.engine":
            from core.tts import tts 
            tts.engine = str(value).lower()
            tts.initialize()
    except Exception as e:
        print(f"[Settings Runtime Apply] Failed to apply {key_path}: {e}")

def _get_call_logs(limit: int = 100):
    """Get call logs from database and fallback to in-memory receptionist logs."""
    logs = []
    try:
        logs = db.get_call_logs(limit=limit)
    except Exception:
        logs = []

    if not logs:
        raw = receptionist.call_logs[-limit:] if getattr(receptionist, "call_logs", None) else []
        logs = list(reversed(raw))

    normalized = []
    for idx, item in enumerate(logs):
        ts = item.get("timestamp", "")
        normalized.append({
            "id": item.get("id") or f"call_{idx}_{hash(str(item)) & 0xffff}",
            "caller": item.get("caller", "Unknown"),
            "status": item.get("status", "Unknown"),
            "instructions": item.get("instructions", item.get("intent_executed", "No instructions")),
            "transcript": item.get("transcript", ""),
            "timestamp": ts,
        })
    return normalized

@app.post("/api/chat")
async def send_chat(message: ChatMessage):
    if VOICE_ASSISTANT_ENABLED:
        # Simulate voice input with text
        voice_assistant._on_speech(message.text)
    return {"status": "processing"}

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    def get_clean_messages():
        if not VOICE_ASSISTANT_ENABLED:
            return []
        cleaned = []
        for m in voice_assistant.messages:
            if m["role"] == "system": 
                continue
            content = m["content"]
            metadata = m.get("metadata", {})
            
            if m["role"] == "user" and "User asked: " in content:
                content = content.split("User asked: ")[-1].split("\n\nRespond naturally")[0].strip()
            
            cleaned.append({
                "role": m["role"], 
                "content": content,
                "metadata": metadata
            })
            
        # Append active ongoing stream
        if getattr(voice_assistant, 'current_user_prompt', ""):
            cleaned.append({"role": "user", "content": voice_assistant.current_user_prompt})
            
            stream_text = getattr(voice_assistant, 'current_stream', "")
            if stream_text:
                cleaned.append({
                    "role": "bot", 
                    "content": stream_text,
                    "metadata": getattr(voice_assistant, 'current_metadata', {})
                })
            else:
                cleaned.append({"role": "bot", "content": "Processing..."})
                
        return cleaned

    try:
        last_hash = ""
        while True:
            if VOICE_ASSISTANT_ENABLED:
                messages = get_clean_messages()
                messages_hash = str(messages)
                if messages_hash != last_hash:
                    await websocket.send_json({"messages": messages})
                    last_hash = messages_hash
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass

@app.websocket("/ws/media")
async def websocket_media(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"state": function_executor.get_media_state()})
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass

@app.websocket("/ws/call-logs")
async def websocket_call_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        last_hash = ""
        while True:
            logs = _get_call_logs(limit=200)
            payload_hash = str(logs)
            if payload_hash != last_hash:
                await websocket.send_json({"logs": logs})
                last_hash = payload_hash
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass

@app.websocket("/ws/execution")
async def websocket_execution(websocket: WebSocket):
    await websocket.accept()
    last_event_id = 0
    try:
        while True:
            events = function_executor.get_execution_events(after_id=last_event_id, limit=200)
            if events:
                last_event_id = events[-1].get("id", last_event_id)
                await websocket.send_json({"events": events})
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        pass

@app.get("/api/media/state")
async def get_media_state():
    return {"state": function_executor.get_media_state()}


@app.get("/api/diagnostics")
async def get_diagnostics():
    return get_diagnostics_payload()


@app.post("/api/diagnostics/run")
async def run_diagnostics(req: DiagnosticsRunRequest):
    if req.key and isinstance(req.key, str):
        key_val = cast(str, req.key)
        result = run_single_diagnostic(key_val)
        return {"result": result, "diagnostics": list(diagnostics_state.values())}

    for key_str in diagnostics_state.keys():
        run_single_diagnostic(key_str)
    return {"diagnostics": list(diagnostics_state.values())}


@app.get("/api/settings")
async def get_settings():
    return {"settings": settings_store.get_all()}


@app.put("/api/settings")
async def update_settings(req: SettingsUpdateRequest):
    incoming = req.settings or {}
    flat = _flatten_settings(incoming)

    changed = []
    restart_required_keys = [
        "ollama_url", "models.chat", "models.web_agent", "tts.voice",
        "wake_word.keyword", "wake_word.sensitivity", "wake_word.confirmation_count",
        "picovoice.enabled", "picovoice.key", "picovoice.ppn_path"
    ]
    restart_required = False

    for key_path, value in flat.items():
        settings_store.set(key_path, value)
        _apply_runtime_setting(key_path, value)
        changed.append(key_path)
        if key_path in restart_required_keys:
            restart_required = True

    return {
        "success": True,
        "message": "Settings saved.",
        "changed_keys": changed,
        "restart_required": restart_required,
        "settings": settings_store.get_all(),
    }


@app.post("/api/settings/reset")
async def reset_settings():
    settings_store.reset_to_defaults()
    return {"success": True, "message": "Settings reset to defaults.", "settings": settings_store.get_all()}


@app.get("/api/settings/validate")
async def validate_settings():
    cfg = settings_store.get_all()
    ollama_url = cfg.get("ollama_url", "http://localhost:11434")
    base = str(ollama_url).rstrip("/")

    checks = {
        "ollama": {"ok": False, "detail": "Not checked"},
        "spotify_credentials": {"ok": False, "detail": "Not set"},
    }

    try:
        resp = requests.get(f"{base}/api/tags", timeout=4)
        checks["ollama"] = {"ok": resp.status_code == 200, "detail": f"HTTP {resp.status_code}"}
    except Exception as e:
        checks["ollama"] = {"ok": False, "detail": str(e)}

    spotify_id = cfg.get("spotify", {}).get("client_id")
    spotify_secret = cfg.get("spotify", {}).get("client_secret")
    if spotify_id and spotify_secret:
        checks["spotify_credentials"] = {"ok": True, "detail": "Client ID/Secret present"}

    return {"checks": checks}

@app.get("/api/call-logs")
async def get_call_logs(limit: int = 100):
    safe_limit = max(1, min(limit, 500))
    return {"logs": _get_call_logs(limit=safe_limit), "count": safe_limit}

@app.post("/api/media/control")
async def control_media(req: MediaControlRequest):
    result = function_executor.control_media(
        action=req.action,
        query=req.query,
        service=req.service,
        volume=req.volume,
        positionSec=req.positionSec,
    )
    return result

@app.get("/api/media/local/{song_id}")
async def stream_local_song(song_id: str):
    file_path = function_executor.get_local_song_path(song_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="Song not found")
    return FileResponse(file_path, media_type="audio/mpeg")

# --- Tasks API ---
class TaskData(BaseModel):
    title: str
    description: str

@app.get("/api/tasks")
async def get_tasks():
    return {"tasks": function_executor.tasks}

@app.post("/api/tasks")
async def create_task(task: TaskData):
    result = function_executor.execute("create_task", {"title": task.title, "description": task.description})
    return result

@app.put("/api/tasks/{task_id}")
async def edit_task(task_id: str, task: TaskData):
    result = function_executor.execute("edit_task", {"task_id": task_id, "title": task.title, "description": task.description})
    return result

@app.post("/api/tasks/{task_id}/execute")
async def execute_task(task_id: str):
    result = function_executor.execute("execute_task", {"task_id": task_id})
    return result

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    tasks = function_executor.tasks
    original_len = len(tasks)
    function_executor.tasks = [t for t in tasks if t.get("id") != task_id]
    if len(function_executor.tasks) < original_len:
        function_executor._save_tasks()
        return {"success": True, "message": "Task deleted."}
    return {"success": False, "message": "Task not found."}
