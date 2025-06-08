# Wolf AI Assistant - Complete Setup Guide

## Quick Start

1. **Install Ollama** (if not already installed):
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Download a model**:
   ```bash
   ollama pull llama2
   ```

3. **Start Ollama service**:
   ```bash
   ollama serve
   ```

4. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env file with your preferred settings
   ```

5. **Run Wolf AI Assistant**:
   ```bash
   python app.py
   ```

6. **Access the web interface**:
   Open http://localhost:5000 in your browser

## Environment Configuration

Create a `.env` file in your project directory:

```env
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Database
DATABASE_PATH=./data/wolf_ai.db

# Audio (for environments with hardware)
ENABLE_TTS=true
ENABLE_VOICE_INPUT=true
```

## Wake Word Detection

Wolf AI Assistant includes "Hey Wolf" wake word detection that works automatically when:
- Microphone hardware is available
- Audio system is properly configured
- Background listening is enabled

### Wake Word Commands:
- "Hey Wolf" - Primary wake word
- "Hi Wolf" - Alternative wake word  
- "Hello Wolf" - Alternative wake word
- "Ok Wolf" - Alternative wake word

### API Endpoints for Wake Word Control:
- `POST /api/wake-word/start` - Start background listening
- `POST /api/wake-word/stop` - Stop background listening
- `GET /api/wake-word/status` - Check if wake word detection is active

## Ollama Models Comparison

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| orca-mini | 3GB | Fast | Good | Quick responses |
| llama2 | 7GB | Medium | Excellent | General conversation |
| mistral | 7GB | Fast | Excellent | Balanced performance |
| codellama | 7GB | Medium | Excellent | Programming tasks |
| dolphin-mistral | 7GB | Medium | Excellent | Instruction following |

## Features Available

### Text-Based Interaction
- Type commands in the web interface
- Real-time AI conversations
- System command execution
- Settings management

### Voice Features (Hardware Dependent)
- Wake word detection ("Hey Wolf")
- Voice command recognition
- Text-to-speech responses
- Background listening

### PC Control Commands
- `"What time is it?"` - Get current time/date
- `"Open Chrome"` - Launch applications
- `"Take a screenshot"` - Capture screen (GUI environments)
- `"Tell me a joke"` - AI conversation
- `"Hello Wolf"` - General greeting

### System Integration
- SQLite database for conversation history
- Settings persistence
- Dark/light theme support
- Responsive web interface

## Troubleshooting

### Ollama Not Working
1. Check if Ollama is running: `ollama list`
2. Verify the model is downloaded: `ollama pull llama2`
3. Test connection: Visit `/api/test-ollama` endpoint
4. Check environment variables in `.env` file

### Voice Features Not Available
- This is normal in cloud/server environments
- Use text input instead of voice commands
- All functionality works via text interface

### Performance Issues
- Try a smaller model like `orca-mini`
- Reduce response length in settings
- Check available system memory

## Development

### Running in Development Mode
```bash
export FLASK_ENV=development
python app.py
```

### API Testing
```bash
# Test Ollama connection
curl http://localhost:5000/api/test-ollama

# Send text command
curl -X POST http://localhost:5000/api/command \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello Wolf"}'

# Check wake word status
curl http://localhost:5000/api/wake-word/status
```

## Architecture

- **Frontend**: Modern web interface with HTML/CSS/JavaScript
- **Backend**: Python Flask server
- **AI**: Ollama for language model inference
- **Database**: SQLite for data persistence
- **Voice**: SpeechRecognition + pyttsx3 (when available)
- **PC Control**: Cross-platform system commands

## Security Notes

- Ollama runs locally - no data sent to external servers
- All conversations stored locally in SQLite database
- PC control commands have safety restrictions
- No external dependencies for core functionality