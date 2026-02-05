# 🛠️ Wolf AI - Development Tools

This directory contains development tools, demos, and experimental features for Wolf AI.

## 📁 Files

### 🎭 `demo.py` - Standalone Voice Assistant Demo
**Purpose**: Complete voice-controlled AI assistant in a single script

#### What it is:
- 🎤 **Voice-First Interface** - No GUI, just voice interaction
- 🧠 **Full AI Brain** - Same intelligence as main app
- 🔊 **Voice Output** - Speaks responses back to you
- ⚡ **Lightweight** - Minimal dependencies, fast startup

#### Features:
- 🗣️ **Wake Word Detection** - Say "Jarvis" to activate
- 💬 **Natural Conversation** - Chat like with a real assistant
- 🏠 **Smart Home Control** - "Turn on the lights"
- ⏰ **Timer & Alarms** - "Set timer for 10 minutes"
- 📅 **Calendar Management** - "Add meeting tomorrow at 2pm"
- 🔍 **Web Search** - "Search for Python tutorials"
- 🌤️ **Weather Updates** - "What's the weather like?"

#### How to Use:
```bash
# Run the voice assistant demo
python development/demo.py

# You'll see:
# 🎙️ Wolf AI Voice Assistant Demo
# 📍 Say "Jarvis" to wake up the assistant
# 🔄 Listening for wake word...

# Then say:
# "Jarvis, what time is it?"
# "Jarvis, turn on the office lights"
# "Jarvis, set a timer for 5 minutes"
```

#### Demo Controls:
- **🎤 Wake Word**: Say "Jarvis" to start listening
- **🛑 Stop**: Say "goodbye" or press Ctrl+C
- **🔊 Volume**: Adjust system volume for TTS
- **🎙️ Microphone**: Ensure mic permissions are granted

#### What to Expect:
```
🎙️ Wolf AI Voice Assistant Demo
📍 Say "Jarvis" to wake up the assistant
🔄 Listening for wake word...

✅ Wake word detected! Listening for command...
🎤 You said: "What time is it?"
🧠 Processing...
🔊 Speaking: The current time is 3:45 PM.

🔄 Listening for wake word...
```

---

## 🎯 Development Use Cases

### 1. **Voice Testing**
Test voice recognition and TTS without GUI:
```bash
python development/demo.py
# Test various voice commands and accents
```

### 2. **Quick Prototyping**
Test new features before adding to main app:
```bash
# Edit demo.py to add your new feature
# Test with voice commands
# Once working, integrate into main app
```

### 3. **Performance Testing**
Measure voice response times:
```bash
python development/demo.py
# Time from wake word to response
# Check memory usage
# Test with background noise
```

### 4. **Accessibility Testing**
Test voice-only interaction:
```bash
# Can users navigate without screen?
# Is voice feedback clear?
# Are commands intuitive?
```

---

## 🧪 Demo vs Main App

| Feature | Demo | Main App |
|---------|------|----------|
| **Voice Control** | ✅ Full | ✅ Full |
| **GUI Interface** | ❌ None | ✅ Complete |
| **Chat History** | ❌ None | ✅ Saved |
| **Settings** | ❌ Fixed | ✅ Customizable |
| **Web Browser** | ❌ None | ✅ Available |
| **System Resources** | 🟢 Low | 🟡 Higher |
| **Startup Time** | ⚡ Fast | 🐌 Slower |

---

## 🔧 Customizing the Demo

### Adding New Commands:
```python
# In demo.py, add to the command handler
elif "weather" in text:
    response = get_weather()
elif "news" in text:
    response = get_latest_news()
```

### Changing Wake Word:
```python
# In config.py:
WAKE_WORD = "computer"  # Instead of "jarvis"
```

### Custom Voice:
```python
# In config.py:
TTS_VOICE_MODEL = "en_US-lessac-medium"  # Different voice
```

---

## 🐛 Demo Troubleshooting

### Common Issues:

#### 🔴 "Wake word not detected"
**Solution**: 
- Check microphone permissions
- Try adjusting `WAKE_WORD_SENSITIVITY` in config.py
- Ensure quiet environment

#### 🔴 "Voice sounds robotic"
**Solution**:
- Try different TTS voice model
- Check system audio settings
- Ensure good internet connection

#### 🔴 "Commands not recognized"
**Solution**:
- Speak clearly and naturally
- Check STT model is loaded
- Try simpler commands first

#### 🔴 "No response from AI"
**Solution**:
- Check Ollama is running: `ollama serve`
- Verify model is installed: `ollama list`
- Check network connection

---

## 🚀 Demo Development

### Adding New Features:
1. **Create Function**:
```python
def my_new_feature(command_text):
    # Process the command
    return "Feature result"
```

2. **Add to Handler**:
```python
elif "my command" in text:
    response = my_new_feature(text)
```

3. **Test It**:
```bash
python development/demo.py
# Say: "Jarvis, my command"
```

### Debugging Voice Issues:
```python
# Add debug prints to see what's happening
print(f"STT detected: {text}")
print(f"Router classified: {function_name}")
print(f"LLM response: {response}")
```

### Performance Optimization:
```python
# Add timing measurements
import time
start = time.time()
# ... process command
end = time.time()
print(f"Response time: {end-start:.2f}s")
```

---

## 📊 Demo Performance

### Expected Performance:
- **Wake Word Detection**: <500ms
- **STT Processing**: <1s
- **AI Response**: <2s
- **TTS Generation**: <1s
- **Total Response**: <4s

### System Requirements:
- **RAM**: 4GB minimum
- **CPU**: Any modern processor
- **Microphone**: Built-in or USB
- **Speakers**: Built-in or external
- **Network**: For AI model access

---

## 🎯 Demo Use Cases

### 1. **Voice Assistant Testing**
```bash
# Test how well voice commands work
# Check accuracy in different environments
# Test with different accents
```

### 2. **Feature Development**
```bash
# Quickly test new AI features
# Prototype new command types
# Test model performance
```

### 3. **Accessibility Demo**
```bash
# Show voice-only interaction
# Test hands-free operation
# Demonstrate accessibility features
```

### 4. **Performance Benchmarking**
```bash
# Measure response times
# Test resource usage
# Compare different models
```

---

## 🎪 Demo Fun Commands

Try these fun commands with the demo:

```bash
# Fun interactions
"Jarvis, tell me a joke"
"Jarvis, what's the meaning of life?"
"Jarvis, sing me a song"
"Jarvis, do you like robots?"

# Practical commands
"Jarvis, what time is it?"
"Jarvis, how's the weather?"
"Jarvis, set a timer for 1 minute"
"Jarvis, remind me to buy milk"

# Complex commands
"Jarvis, turn on the living room lights to 50%"
"Jarvis, search for the best pizza places nearby"
"Jarvis, add a meeting to my calendar for tomorrow at 3pm"
```

---

The demo is your playground for experimenting with Wolf AI's voice capabilities! Perfect for testing, development, and showing off what your AI assistant can do. 🎙️🐺
