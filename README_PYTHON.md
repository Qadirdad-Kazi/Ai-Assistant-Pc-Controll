# JARIS - Just A Rather Intelligent System (Python Version)

JARIS is a Python-based AI assistant with voice control and PC management capabilities. It provides a desktop GUI application for natural language interaction with your computer.

## ✨ Features

- **AI-Powered Chat**: Natural language processing using Ollama
- **Voice Control**: Speech-to-text and text-to-speech capabilities
- **System Commands**: Execute system commands through natural language
- **File Operations**: Create, read, and manage files and directories
- **Desktop GUI**: Modern interface built with tkinter
- **Settings Management**: Configurable voice, AI, and appearance settings

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Ollama installed and running (https://ollama.ai/)
- Microphone and speakers for voice features

### Installation

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd Ai-Assistant-Pc-Controll
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and start Ollama**
   - Download from https://ollama.ai/
   - Install Ollama
   - Pull a model (e.g., `ollama pull llama3.2:latest`)

4. **Run JARIS**
   ```bash
   python jaris_ai_assistant.py
   ```

## 🛠️ Usage

### AI Mode
- Type messages in the input field or use voice input
- JARIS will respond using the configured Ollama model
- Voice responses can be enabled in settings

### PC Control Mode
- Execute system commands using natural language
- Examples:
  - "create folder MyProject"
  - "create file app.py with print('Hello World')"
  - "list files"
  - "navigate to Documents"
  - "open downloads"
  - "execute python --version"

### Settings
- Configure voice settings (enable/disable, volume, sensitivity)
- Set AI model and Ollama URL
- Customize appearance (theme, font size)

## 🔧 Configuration

### Settings File
Settings are automatically saved to `settings.json` in the application directory.

### Supported Commands
- **File Operations**: create folder, create file, list files
- **Navigation**: navigate to [directory]
- **System**: open [application/path], execute [command]
- **General**: Any shell command

### Voice Features
- Speech recognition using Google's speech API
- Text-to-speech using pyttsx3
- Adjustable microphone sensitivity
- Volume control

## 🐛 Troubleshooting

### Common Issues

**"Cannot connect to AI service"**
- Make sure Ollama is running: `ollama serve`
- Check if the model is installed: `ollama list`
- Verify the Ollama URL in settings

**Voice recognition not working**
- Check microphone permissions
- Adjust microphone sensitivity in settings
- Ensure internet connection for Google speech recognition

**TTS not working**
- Install audio drivers
- Check system volume settings
- Try different TTS engines in the code

**PyAudio installation issues**
- On Windows: `pip install pipwin && pipwin install pyaudio`
- On macOS: `brew install portaudio && pip install pyaudio`
- On Linux: `sudo apt-get install python3-pyaudio`

## 📁 Project Structure

```
Ai-Assistant-Pc-Controll/
├── jaris_ai_assistant.py    # Main application
├── requirements.txt         # Python dependencies
├── settings.json           # User settings (auto-generated)
└── README_PYTHON.md        # This file
```

## 🔧 Development

### Adding New Commands
Extend the `execute_command` method in the `JarvisAI` class:

```python
elif command.startswith("your_command"):
    # Your command logic here
    return True, "Success message"
```

### Customizing the GUI
Modify the `setup_*_tab` methods in the `JarvisGUI` class to add new interface elements.

### Adding New AI Models
Update the model selection in the settings tab and ensure the model is available in Ollama.

## 📝 License

This project is open source. Feel free to modify and distribute.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Verify Ollama is running correctly
3. Check Python dependencies are installed
4. Review error messages in the console
