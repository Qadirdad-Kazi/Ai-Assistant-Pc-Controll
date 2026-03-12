# 🎙️ UI & Voice Integration Guide

## 📋 Overview

Wolf AI 2.0 features a complete integration between:
- **Frontend UI** (React-based web interface)
- **Backend API** (FastAPI with WebSocket support)
- **Voice Assistant** (Speech-to-text and text-to-speech)
- **AI Modules** (Vision, Memory, Research, Bug Watcher)

## 🚀 Quick Start

### Method 1: Use the Startup Script (Recommended)
```bash
# Start both backend and frontend
python start_wolf_ai.py

# Start only backend
python start_wolf_ai.py --backend-only

# Start only frontend
python start_wolf_ai.py --frontend-only

# Don't open browser automatically
python start_wolf_ai.py --no-browser
```

### Method 2: Manual Startup
```bash
# Terminal 1: Start Backend
python main.py

# Terminal 2: Start Frontend (if needed)
cd frontend
npm run dev
```

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend UI** | http://localhost:5173 | Main React interface |
| **Backend API** | http://localhost:8000 | REST API and WebSocket |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **WebSocket** | ws://localhost:8000/ws/status | Real-time status updates |

## 🎙️ Frontend Features

### Core Components
- **Dashboard**: System overview and status monitoring
- **Chat Interface**: Voice assistant interaction
- **Settings**: Configuration management
- **Diagnostics**: System health checks
- **Media**: Audio playback and management
- **Tasks**: Task management and tracking

### Real-time Features
- **WebSocket Integration**: Live status updates
- **Voice Activity Indicator**: Shows when listening/speaking
- **System Monitor**: CPU, memory, and performance metrics
- **Status Cards**: Component health indicators

## 🎤 Voice Assistant Features

### Voice Input (STT)
- **Wake Word Detection**: "Hey Wolf" activation
- **Continuous Listening**: Background audio processing
- **Command Recognition**: Natural language understanding
- **Noise Reduction**: Audio filtering and enhancement

### Voice Output (TTS)
- **Multiple Voices**: Male/Female options
- **Speech Speed Control**: Adjustable playback rate
- **Audio Streaming**: Real-time synthesis
- **Interrupt Support**: Stop current speech immediately

### Voice Commands
```bash
# System Control
"Hey Wolf, turn on the lights"
"Hey Wolf, open browser"
"Hey Wolf, what time is it?"

# Information
"Hey Wolf, search for Bitcoin price"
"Hey Wolf, tell me about AI"
"Hey Wolf, research latest news"

# PC Control
"Hey Wolf, click the start button"
"Hey Wolf, type hello world"
"Hey Wolf, scroll down"
```

## 🔗 Integration Architecture

### Backend API Endpoints
```python
# Health Check
GET /health

# System Status
GET /api/status

# Diagnostics
GET /api/diagnostics

# Settings
GET/POST /api/settings

# WebSocket Status
WS /ws/status
```

### WebSocket Communication
```javascript
// Frontend WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/status');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    setIsListening(data.isListening);
    setStatuses(data);
};
```

### Voice Assistant Integration
```python
# Voice Assistant State Management
system_status = {
    "isListening": False,
    "Voice Core": "ACTIVE",
    "System Control": "READY", 
    "Neural Sonic": "STANDBY",
    "Dev Agent": "IDLE"
}
```

## 🧪 Testing Integration

### Run Integration Tests
```bash
# Test UI and Voice integration
python -m pytest tests/test_ui_voice_integration.py -v

# Test specific components
python -m pytest tests/test_ui_voice_integration.py::TestUIVoiceIntegration::test_voice_assistant_initialization -v
python -m pytest tests/test_ui_voice_integration.py::TestUIVoiceIntegration::test_frontend_build_exists -v
```

### Test Coverage
- ✅ Frontend build verification
- ✅ Backend API health checks
- ✅ Voice assistant initialization
- ✅ TTS/STT integration
- ✅ WebSocket communication
- ✅ Component integration
- ✅ Error handling
- ✅ Configuration management

## 🔧 Configuration

### Backend Configuration (`config.py`)
```python
# Voice Assistant Settings
VOICE_ASSISTANT_ENABLED = True
WAKE_WORD = "Hey Wolf"

# API Settings
OLLAMA_URL = "http://localhost:11434"
BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = 8000

# TTS Settings
TTS_ENGINE = "kokoro"  # or "piper"
VOICE_SPEED = 1.0
```

### Frontend Configuration
```javascript
// WebSocket connection
const WS_URL = 'ws://localhost:8000/ws/status';

// API base URL
const API_BASE_URL = 'http://localhost:8000/api';
```

## 🎯 Voice-to-UI Workflow

1. **User Speaks**: "Hey Wolf, what's the weather?"
2. **STT Processing**: Audio → Text conversion
3. **Command Recognition**: Natural language understanding
4. **API Processing**: Execute request (web search, etc.)
5. **Response Generation**: Create appropriate response
6. **TTS Synthesis**: Text → Audio conversion
7. **Audio Playback**: Speak response to user
8. **UI Update**: Show status changes in real-time

## 🔄 UI-to-Voice Workflow

1. **UI Action**: User clicks "Voice" button
2. **WebSocket Message**: Send activation command
3. **Voice Assistant**: Start listening mode
4. **UI Update**: Show listening indicator
5. **Audio Capture**: Record user speech
6. **Processing**: Convert and process command
7. **Response**: Execute and speak response
8. **UI Update**: Update status and results

## 🚨 Troubleshooting

### Common Issues

#### Backend Not Starting
```bash
# Check dependencies
pip install uvicorn fastapi requests

# Check port availability
netstat -an | grep 8000

# Check logs
python main.py
```

#### Frontend Not Loading
```bash
# Install Node.js dependencies
cd frontend
npm install

# Build frontend
npm run build

# Start dev server
npm run dev
```

#### Voice Assistant Not Working
```bash
# Check microphone permissions
# Windows: Allow app access to microphone
# Linux/macOS: Check system privacy settings

# Check audio devices
python -c "import sounddevice as sd; print(sd.default.device)"

# Test TTS
python -c "from core.tts import tts; tts.speak('test')"
```

### Debug Mode
```bash
# Enable verbose logging
python main.py --debug

# Check component status
curl http://localhost:8000/api/status

# Test WebSocket
wscat -c ws://localhost:8000/ws/status
```

## 🎛️ Customization

### Adding New Voice Commands
```python
# In core/function_executor.py
def custom_command(params):
    # Implement your custom logic
    return {"success": True, "message": "Command executed"}

# Register the command
ACTION_FUNCTIONS["custom_command"] = "custom_command"
```

### Adding New UI Components
```jsx
// In frontend/src/components/
import React from 'react';

function CustomComponent() {
    return (
        <div className="custom-component">
            <h2>Custom Feature</h2>
            {/* Your component logic */}
        </div>
    );
}

export default CustomComponent;
```

### Custom WebSocket Events
```python
# In backend_api.py
@router.websocket("/ws/custom")
async def custom_websocket(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        try:
            data = await websocket.receive_text()
            # Process custom data
            await websocket.send_json({"status": "received"})
        except WebSocketDisconnect:
            break
```

## 📊 Performance Optimization

### Backend Optimization
- **Async Processing**: Use async/await for I/O operations
- **Connection Pooling**: Reuse database connections
- **Caching**: Cache frequent API responses
- **Rate Limiting**: Prevent API abuse

### Frontend Optimization
- **Code Splitting**: Load components on demand
- **Lazy Loading**: Defer heavy component loading
- **WebSocket Optimization**: Batch status updates
- **Audio Streaming**: Use Web Audio API for better performance

### Voice Optimization
- **Audio Buffering**: Optimize audio chunk sizes
- **Noise Reduction**: Pre-process audio input
- **Model Caching**: Keep AI models in memory
- **Parallel Processing**: Handle multiple audio streams

## 🔒 Security Considerations

### API Security
- **CORS Configuration**: Properly configure cross-origin requests
- **Authentication**: Add API keys/tokens if needed
- **Input Validation**: Sanitize all user inputs
- **Rate Limiting**: Prevent API abuse

### Voice Security
- **Privacy**: Handle sensitive audio data carefully
- **Local Processing**: Process audio locally when possible
- **Encryption**: Encrypt audio transmissions
- **User Consent**: Get permission for audio recording

## 🎉 Conclusion

Wolf AI 2.0 provides a complete integration between UI and voice capabilities:

- **✅ Seamless Voice Control**: Natural language interaction
- **✅ Real-time UI Updates**: Live status and feedback
- **✅ Modular Architecture**: Easy to extend and customize
- **✅ Robust Testing**: Comprehensive test coverage
- **✅ Production Ready**: Optimized for real-world use

The system is designed to be intuitive, responsive, and reliable, providing users with a powerful voice-controlled AI assistant experience through a modern web interface.

---

**Next Steps:**
1. Run `python start_wolf_ai.py` to start the system
2. Open http://localhost:5173 in your browser
3. Say "Hey Wolf" to activate voice assistant
4. Explore the features and capabilities

🚀 **Enjoy your AI-powered voice assistant!**
