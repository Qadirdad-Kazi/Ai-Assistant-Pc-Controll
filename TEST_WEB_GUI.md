# 🧪 JARIS Web GUI Test Guide

## 🚀 **How to Start the Web GUI**

### **Method 1: Using the Launcher Script**
```bash
# Unix/macOS
./start_web_gui.sh

# Windows
start_web_gui.bat
```

### **Method 2: Manual Start**
```bash
# Activate virtual environment
source venv/bin/activate

# Start the web GUI
python3 jaris_web_gui.py
```

### **Method 3: Direct Python**
```bash
python3 jaris_web_gui.py
```

## 🌐 **Access the Web GUI**
- **URL:** http://localhost:8080
- **Auto-opens:** Browser should open automatically
- **Manual:** Open any browser and go to the URL above

## 🧪 **What You Can Test**

### **💬 AI Chat Tab**
**Test Commands:**
- "Hello JARIS, how are you?"
- "What's the weather like?"
- "Tell me a joke"
- "What can you do?"
- "Help me with Python programming"

**Voice Features:**
- Click 🎤 button to speak
- Click 🔄 button for continuous listening
- Responses are automatically spoken

### **💻 PC Control Tab**
**File Operations:**
- `create folder MyProject`
- `create folder TestFolder in desktop`
- `create file hello.txt with Hello World`
- `list files`
- `list files downloads`
- `open downloads`
- `open desktop`
- `open documents`

**System Control:**
- `screenshot`
- `system info`
- `volume up`
- `volume down`
- `mute`
- `brightness up`
- `brightness down`

**Application Control:**
- `start app Safari`
- `start app Terminal`
- `start app Calculator`
- `launch Chrome`

**Network Control:**
- `wifi on`
- `wifi off`
- `bluetooth on`
- `bluetooth off`

**System Commands:**
- `execute python --version`
- `execute ls -la`
- `execute ps aux`

### **🎤 Voice Control**
**Voice Commands to Try:**
- "Create folder MyProject"
- "List files"
- "Take a screenshot"
- "Volume up"
- "System info"
- "Open downloads"

## 🔧 **Troubleshooting**

### **If Web GUI Won't Start:**
```bash
# Check if port 8080 is free
lsof -i :8080

# Try different port (edit jaris_web_gui.py line 1551)
# Change: port = 8080
# To: port = 8081
```

### **If Ollama Connection Fails:**
```bash
# Start Ollama
ollama serve

# Pull a model
ollama pull llama3.2:latest

# Check if running
curl http://localhost:11434/api/tags
```

### **If Voice Doesn't Work:**
```bash
# Install audio dependencies
pip install pyaudio

# On macOS, you might need:
brew install portaudio
```

## 📊 **Expected Results**

### **✅ Working Features:**
- Web interface loads at http://localhost:8080
- AI chat responds to messages
- PC control executes commands
- Voice input works (click 🎤)
- Voice output works (responses are spoken)
- Continuous listening works (click 🔄)

### **❌ Common Issues:**
- "Cannot connect to AI service" → Ollama not running
- "Voice input error" → Microphone permissions
- "Port already in use" → Change port in code
- "Module not found" → Install dependencies

## 🎯 **Quick Test Sequence**

1. **Start the GUI:**
   ```bash
   python3 jaris_web_gui.py
   ```

2. **Open Browser:**
   - Go to http://localhost:8080

3. **Test AI Chat:**
   - Type: "Hello JARIS"
   - Click 🎤 and say: "What can you do?"

4. **Test PC Control:**
   - Switch to "💻 PC Control" tab
   - Type: "list files"
   - Click 🎤 and say: "create folder TestFolder"

5. **Test Voice Features:**
   - Click 🔄 for continuous listening
   - Say: "take a screenshot"
   - Say: "system info"

## 🚀 **Advanced Testing**

### **Test All Voice Commands:**
- "Create folder MyProject in desktop"
- "List files downloads"
- "Open downloads"
- "Take a screenshot"
- "System info"
- "Volume up"
- "Brightness down"

### **Test Continuous Listening:**
1. Click 🔄 button
2. Wait for it to turn green
3. Say any command
4. Watch it execute automatically

### **Test Error Handling:**
- Try invalid commands
- Test with Ollama stopped
- Test with microphone disabled

## 📝 **Test Results Log**

**Date:** ___________
**System:** ___________
**Browser:** ___________

**✅ Working:**
- [ ] Web GUI loads
- [ ] AI Chat responds
- [ ] PC Control works
- [ ] Voice input works
- [ ] Voice output works
- [ ] Continuous listening works

**❌ Issues:**
- [ ] Web GUI won't start
- [ ] AI Chat not responding
- [ ] PC Control not working
- [ ] Voice input not working
- [ ] Voice output not working
- [ ] Continuous listening not working

**Notes:**
_________________________________
_________________________________

---

**🎉 Ready to test your JARIS Web GUI!**
