# 🤖 JARIS AI Agent

**Desktop Automation Assistant for Natural Language Programming**

Transform natural language commands into real-time visible programming actions on your PC.

## ✨ **What It Does**

### **🎯 Core Capabilities**
- **Natural Language Interpretation** - Understands commands like "Create a React login form"
- **Automatic IDE Control** - Opens VS Code and navigates files
- **Visible Code Typing** - Types code character by character, visibly to user
- **AI Code Generation** - Generates production-ready, well-commented code
- **Project Setup** - Creates folder structures and runs setup commands
- **Visual Feedback** - Shows progress and completion status

### **🔧 Technical Features**
- **PyAutoGUI Integration** - Desktop automation and control
- **AI-Powered Interpretation** - Uses JARIS AI for command understanding
- **Real-time Typing Simulation** - Types code at realistic speeds
- **Framework Support** - React, HTML, Python, Node.js, Vue.js, etc.
- **Cross-platform** - Works on Windows, macOS, and Linux

## 🚀 **Quick Start**

### **1. Install Dependencies**
```bash
# Install automation packages
pip install -r requirements_automation.txt

# Or install individually
pip install pyautogui pyperclip pynput requests
```

### **2. Run the Agent**
```bash
# Start the AI Agent
python3 jaris_ai_agent.py

# Or run the basic version
python3 ai_agent.py
```

### **3. Give Commands**
```
> Create a React login form with modern styling
> Generate an HTML contact form with validation
> Make a Python Flask API with user authentication
```

## 🎯 **Example Commands**

### **React Development**
```
"Create a React login form with modern styling"
"Make a React dashboard with charts and tables"
"Generate a React Native signup screen"
"Build a React portfolio with animations"
```

### **HTML/CSS**
```
"Create an HTML contact form with validation"
"Make a responsive landing page"
"Generate a modern navigation menu"
"Build an HTML5 game interface"
```

### **Backend Development**
```
"Create a Python Flask API with authentication"
"Generate a Node.js Express server with MongoDB"
"Make a Python data analysis script"
"Build a REST API with documentation"
```

### **Full-Stack Projects**
```
"Create a MERN stack e-commerce site"
"Generate a Vue.js dashboard with backend"
"Make a Python Django blog with admin panel"
"Build a React Native mobile app"
```

## 🔧 **How It Works**

### **Step 1: Command Interpretation**
- User gives natural language command
- AI analyzes the request using JARIS
- Generates structured plan with files and commands

### **Step 2: IDE Automation**
- Opens VS Code automatically
- Creates project structure
- Navigates to appropriate directories

### **Step 3: Code Generation**
- Generates production-ready code
- Types code character by character
- Adds proper comments and structure

### **Step 4: Project Setup**
- Runs framework-specific commands
- Installs dependencies
- Sets up development environment

### **Step 5: Visual Feedback**
- Shows progress indicators
- Displays completion status
- Provides error handling

## 📁 **Project Structure**

```
├── jaris_ai_agent.py          # Main AI Agent
├── ai_agent.py                # Basic automation agent
├── demo_ai_agent.py           # Demo and testing
├── requirements_automation.txt # Automation dependencies
└── README_AI_AGENT.md         # This documentation
```

## 🎬 **Demo Commands**

### **Test the System**
```bash
# Check dependencies and VS Code
python3 demo_ai_agent.py

# Run interactive mode
python3 jaris_ai_agent.py
```

### **Example Session**
```
🤖 JARIS AI Agent - Desktop Automation
============================================================

💡 Enter a programming command (or 'quit' to exit):
Examples:
  - Create a React login form
  - Make an HTML contact form
  - Generate a Python Flask API
  - Create a Node.js Express server

> Create a React login form

🧠 Interpreting: 'Create a React login form'
📋 Plan: {
  "action": "create_project",
  "framework": "react",
  "project_name": "react-login",
  "files": [...],
  "commands": ["npm install", "npm start"],
  "description": "Creating React login form with modern styling"
}

🎯 Creating React login form with modern styling
📋 Steps:
   1. Create React project structure
   2. Generate LoginForm component
   3. Add CSS styling
   4. Install dependencies
   5. Start development server

📂 Opening VS Code...
✅ VS Code opened
📁 Creating react project: react-login
⚛️ Setting up React project...
📝 Creating component: src/components/LoginForm.js
⌨️ Typing src/components/LoginForm.js in VS Code...
✅ src/components/LoginForm.js created and saved
💻 Running: npm install
💻 Running: npm start
✅ Plan executed successfully!
```

## 🔧 **Configuration**

### **Settings (in jaris_cursor_agent.py)**
```python
self.settings = {
    "ollama_url": "http://localhost:11434",
    "model": "llama3.2:latest",
    "vscode_path": "/Applications/Visual Studio Code.app/...",
    "typing_speed": 0.03,  # seconds between keystrokes
    "action_delay": 1.0,   # delay between actions
}
```

### **Customization**
- **Typing Speed** - Adjust `typing_speed` for faster/slower typing
- **VS Code Path** - Set correct path for your system
- **AI Model** - Change model in settings
- **Frameworks** - Add support for new frameworks

## 🛠️ **Troubleshooting**

### **Common Issues**

**"ModuleNotFoundError: No module named 'pyautogui'"**
```bash
pip install pyautogui pyperclip pynput
```

**"VS Code not found"**
- Install VS Code
- Add to PATH or update `vscode_path` in settings

**"AI interpretation error"**
- Make sure Ollama is running
- Check `ollama_url` in settings

**"PyAutoGUI failsafe triggered"**
- Move mouse to corner to disable failsafe
- Adjust `pyautogui.FAILSAFE` setting

### **Platform-Specific Issues**

**macOS:**
- Grant accessibility permissions to Terminal/Python
- System Preferences → Security & Privacy → Accessibility

**Windows:**
- Run as administrator if needed
- Check antivirus software interference

**Linux:**
- Install required system packages
- Check display server compatibility

## 🎯 **Advanced Usage**

### **Custom Commands**
Add new command patterns in `_basic_interpretation()` method:

```python
elif "vue" in command_lower and "dashboard" in command_lower:
    return {
        "action": "create_project",
        "framework": "vue",
        "project_name": "vue-dashboard",
        "files": [...],
        "commands": [...],
        "description": "Creating Vue.js dashboard"
    }
```

### **Framework Extensions**
Add support for new frameworks by extending the interpretation logic and adding framework-specific setup commands.

### **Integration with JARIS**
The Cursor AI Agent integrates with JARIS for enhanced AI capabilities and can be controlled via voice commands.

## 🎊 **Features Summary**

✅ **Natural Language Processing** - Understands complex programming requests
✅ **Visual Automation** - See code being typed in real-time
✅ **AI Code Generation** - Production-ready, well-commented code
✅ **Framework Support** - React, HTML, Python, Node.js, Vue.js, etc.
✅ **Project Setup** - Automatic dependency installation and configuration
✅ **Cross-platform** - Works on Windows, macOS, and Linux
✅ **JARIS Integration** - Enhanced AI capabilities and voice control
✅ **Error Handling** - Robust error handling and user feedback

---

**🤖 Transform your natural language into visible programming actions with JARIS AI Agent!**
