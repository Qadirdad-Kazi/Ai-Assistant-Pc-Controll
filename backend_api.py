import asyncio
import psutil  # type: ignore
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from pydantic import BaseModel  # type: ignore
from typing import Optional
from core.voice_assistant import voice_assistant  # type: ignore
from core.function_executor import executor as function_executor  # type: ignore
from config import VOICE_ASSISTANT_ENABLED  # type: ignore

app = FastAPI(title="Wolf AI Backend API")

# Setup CORS to allow the frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global status tracking dictionary mimicking actual backend state
system_status = {
    "isListening": False,
    "Voice Core": "ACTIVE" if VOICE_ASSISTANT_ENABLED else "OFFLINE",
    "System Control": "READY",
    "Neural Sonic": "STANDBY",
    "Dev Agent": "IDLE"
}

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
                
            await websocket.send_json(system_status)
            await asyncio.sleep(0.5) # Send updates twice a second
    except WebSocketDisconnect:
        pass

class ChatMessage(BaseModel):
    text: str

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
            if m["role"] == "user" and "User asked: " in content:
                content = content.split("User asked: ")[-1].split("\n\nRespond naturally")[0].strip()
            cleaned.append({"role": m["role"], "content": content})
            
        # Append active ongoing stream
        if getattr(voice_assistant, 'current_user_prompt', ""):
            cleaned.append({"role": "user", "content": voice_assistant.current_user_prompt})
            
            stream_text = getattr(voice_assistant, 'current_stream', "")
            if stream_text:
                cleaned.append({"role": "bot", "content": stream_text})
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
