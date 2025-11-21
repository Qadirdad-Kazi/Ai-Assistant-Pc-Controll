# 🤖 AiNest - AI Desktop Assistant

**J**ust **A**nother **R**eally **I**ntelligent **S**ystem

A modern, intelligent desktop AI assistant that combines the power of Ollama local AI models with intuitive voice interaction and automated PC control capabilities.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Ollama](https://img.shields.io/badge/Ollama-Compatible-green.svg)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### 🎯 **Core Capabilities**
- **🗣️ Natural Voice Interaction** - Speak naturally with your AI assistant
- **💬 Intelligent Chat Interface** - Modern, responsive desktop chat application
- **🤖 Local AI Processing** - Powered by Ollama (completely offline)
- **🔧 Auto Model Detection** - Automatically discovers and uses available Ollama models
- **🎤 Voice Recognition** - Advanced speech-to-text capabilities
- **🔊 Text-to-Speech** - Natural voice responses from your assistant

### 🛠️ **Smart Features**
- **🔄 Automatic Model Switching** - Seamlessly handles model updates and changes
- **⚙️ Intuitive Settings Panel** - Easy configuration and customization
- **📊 Real-time Status Monitoring** - System health and connection status
- **💾 Conversation Memory** - Maintains context throughout your session
- **🎨 Modern UI Design** - Beautiful, responsive desktop interface

### 🔮 **Extensible Architecture**
- **🚀 Desktop-First Design** - Built with Eel for native desktop experience
- **📱 Web Technology Stack** - HTML5, CSS3, JavaScript frontend
- **🐍 Python Backend** - Robust, maintainable server architecture
- **🔌 Modular Components** - Easy to extend and customize

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed on your system
2. **Ollama** installed and running
3. **At least one AI model** downloaded via Ollama

### 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Qadirdad-Kazi/Ai-Assistant-Pc-Controll.git
   cd Ai-Assistant-Pc-Controll
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Ollama and download a model**
   ```bash
   # Install Ollama (macOS)
   brew install ollama
   
   # Start Ollama service
   ollama serve
   
   # Download a model (in another terminal)
   ollama pull llama3.2:latest
   # or try: ollama pull llama2, ollama pull mistral, etc.
   ```

5. **Launch AiNest**
   ```bash
   ./start_desktop_app.sh
   ```

## 🎮 Usage

### 🗣️ **Voice Interaction**
1. Click the **🎤 Voice** button
2. Speak naturally when prompted
3. Your speech will be converted to text automatically
4. The AI will respond both in text and speech (if enabled)

### 💬 **Text Chat**
1. Type your message in the input field
2. Press **Enter** to send (Shift+Enter for new line)
3. Enjoy natural conversation with your AI assistant

### ⚙️ **Settings Configuration**
- **Ollama URL**: Default `http://localhost:11434`
- **AI Model**: Auto-detected from available models
- **Voice Input**: Enable/disable speech recognition
- **Auto-speak**: Toggle automatic voice responses
- **TTS Volume**: Adjust text-to-speech volume

## 🏗️ Architecture

### 📁 **Project Structure**
```
Ai-Assistant-Pc-Controll/
├── AiNest_desktop_app.py      # Main desktop application (Eel-based)
├── AiNest_ai_agent.py         # Core AI agent logic
├── desktop_app/
│   └── index.html           # Frontend UI (HTML/CSS/JS)
├── start_desktop_app.sh     # Application launcher
├── requirements.txt         # Python dependencies
├── requirements_automation.txt  # Automation dependencies
└── venv/                    # Virtual environment
```

### 🔧 **Technology Stack**

**Backend (Python)**
- **Eel** - Desktop app framework (web technologies in native window)
- **requests** - HTTP client for Ollama API communication
- **speech_recognition** - Voice input processing
- **pyttsx3** - Text-to-speech engine
- **threading** - Concurrent voice processing

**Frontend (Web Technologies)**
- **HTML5** - Modern semantic markup
- **CSS3** - Responsive design with gradients and animations
- **JavaScript (ES6+)** - Interactive UI and Eel communication
- **WebRTC** - Audio processing support

**AI Integration**
- **Ollama** - Local LLM inference engine
- **REST API** - HTTP-based model communication
- **JSON** - Structured data exchange format

## 🤖 Supported AI Models

AiNest automatically detects and works with any Ollama-compatible model:

### 🌟 **Recommended Models**
- **llama3.2:latest** - Latest Llama model (default preference)
- **llama3.1:latest** - Previous Llama version
- **llama2:latest** - Stable and reliable
- **mistral:latest** - Fast and efficient
- **codellama:latest** - Code-focused assistant

### 🔄 **Auto-Detection Priority**
1. `llama3.2:latest` (highest priority)
2. `llama3.1:latest`
3. `llama3:latest`
4. `llama2:latest`
5. `mistral:latest`
6. `codellama:latest`
7. Any other available model (fallback)

## 🛠️ Troubleshooting

### 🚨 **Common Issues**

**"Ollama not running"**
```bash
# Start Ollama service
ollama serve

# Verify it's running
curl http://localhost:11434/api/version
```

**"No models available"**
```bash
# List installed models
ollama list

# Install a model if none exist
ollama pull llama3.2:latest
```

**"Microphone not working"**
- Check system microphone permissions
- Ensure no other apps are using the microphone
- Try restarting the application

**"TTS not working"**
- Verify system audio output
- Check TTS volume settings in the app
- Restart the application

### 🔍 **Debug Mode**
Run with verbose output to see detailed logs:
```bash
python AiNest_desktop_app.py
```

## 🎤 Voice Commands Examples

### **General Conversation**
- "Hello AiNest, how are you today?"
- "What can you help me with?"
- "Tell me about artificial intelligence"
- "What's the meaning of life?"

### **Technical Assistance**
- "Explain Python decorators"
- "How do I create a REST API?"
- "What's the difference between Git and GitHub?"
- "Help me debug this code"

### **Creative Tasks**
- "Write a poem about technology"
- "Create a story about robots"
- "Suggest names for my new project"
- "Help me brainstorm ideas"

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### 📋 **Development Guidelines**
- Follow PEP 8 coding standards
- Add docstrings to all functions
- Include error handling for external dependencies
- Test with multiple Ollama models
- Update documentation for new features

## 🔮 Roadmap

### **Planned Features**
- 🔧 **PC Control Integration** - System automation capabilities
- 📊 **Analytics Dashboard** - Usage statistics and insights
- 🎨 **Theme Customization** - Multiple UI themes
- 📱 **Mobile Companion** - Cross-platform synchronization
- 🔌 **Plugin System** - Extensible functionality
- 🌍 **Multi-language Support** - International localization

### **Future Enhancements**
- Integration with more AI providers
- Advanced voice recognition features
- Custom wake word detection
- Cloud synchronization options
- Advanced automation scripting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama Team** - For the amazing local AI inference engine
- **Python Community** - For the incredible ecosystem of libraries
- **Eel Framework** - For making desktop apps with web technologies seamless
- **Open Source Contributors** - For the tools that make this project possible

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Qadirdad-Kazi/Ai-Assistant-Pc-Controll/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Qadirdad-Kazi/Ai-Assistant-Pc-Controll/discussions)

---

**Made with ❤️ by the AiNest Team**

*Transform your computer into an intelligent assistant with the power of local AI!*
