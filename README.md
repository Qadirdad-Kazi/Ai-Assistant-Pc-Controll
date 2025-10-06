# 🤖 JARIS AI Assistant

**Just A Rather Intelligent System** - A powerful AI assistant with voice control and PC automation.

## ✨ Features

- **💬 AI Chat** - Intelligent conversations with Ollama
- **🎤 Voice Control** - Speech recognition and text-to-speech
- **💻 PC Control** - Complete system automation
- **🌐 Web GUI** - Modern browser-based interface
- **🔄 Continuous Listening** - Always-on voice activation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama installed and running

### Installation
   ```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama (if not running)
ollama serve

# 3. Pull a model
ollama pull llama3.2:latest

# 4. Run JARIS
python3 jaris_web_gui.py
```

### Access
Open your browser and go to: **http://localhost:8080**

## 🎯 Usage

### AI Chat
- Type messages to chat with AI
- Click 🎤 for voice input
- Responses are automatically spoken

### PC Control
- Execute system commands
- Create/manage files and folders
- Control system settings
- Use voice commands with 🎤

### Voice Features
- **🎤 Voice Input** - Click microphone to speak
- **🔄 Continuous Listening** - Always-on voice activation
- **🔊 Voice Output** - Automatic speech responses

## 📁 Project Structure

```
├── jaris_web_gui.py          # Main web application
├── requirements.txt         # Python dependencies
├── start_web_gui.sh         # Unix launcher
├── start_web_gui.bat        # Windows launcher
├── templates/
│   └── index.html          # Web interface
└── venv/                   # Virtual environment
```

## 🎤 Voice Commands

**AI Chat:**
- "Hello JARIS, how are you?"
- "What's the weather like?"
- "Tell me a joke"

**PC Control:**
- "Create folder MyProject"
- "List files"
- "Open downloads"
- "Take a screenshot"
- "System info"

## 🔧 Troubleshooting

**"Cannot connect to AI service"**
- Make sure Ollama is running: `ollama serve`

**Voice not working**
- Check microphone permissions
- Install audio drivers: `pip install pyaudio`

**Port already in use**
- Change port in `jaris_web_gui.py` (line with `app.run`)

## 📞 Support

- Check that Ollama is running on localhost:11434
- Ensure all dependencies are installed
- Web GUI works in any modern browser

---

**🎉 Enjoy your AI assistant!**
