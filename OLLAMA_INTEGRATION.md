# Wolf AI Assistant - Ollama Integration Guide

## Overview
Wolf AI Assistant uses Ollama to provide intelligent conversational AI responses. This guide explains how to set up and configure Ollama integration.

## Prerequisites
- Ollama installed on your system
- At least one language model downloaded (e.g., llama2, mistral, codellama)

## Installation & Setup

### 1. Install Ollama
```bash
# Download and install Ollama from https://ollama.ai
curl -fsSL https://ollama.ai/install.sh | sh

# Or download directly from GitHub releases
# https://github.com/jmorganca/ollama/releases
```

### 2. Download a Model
```bash
# Download the default model (llama2)
ollama pull llama2

# Or download other models
ollama pull mistral
ollama pull codellama
ollama pull orca-mini
```

### 3. Start Ollama Service
```bash
# Start Ollama server (runs on localhost:11434 by default)
ollama serve

# Or run in background
nohup ollama serve &
```

## Environment Configuration

Create a `.env` file in your Wolf AI Assistant directory:

```env
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Alternative models you can use:
# OLLAMA_MODEL=mistral
# OLLAMA_MODEL=codellama
# OLLAMA_MODEL=orca-mini

# For remote Ollama instance:
# OLLAMA_URL=http://your-server:11434
```

## Configuration Options

### Available Models
- **llama2**: General purpose conversational AI (recommended)
- **mistral**: Fast and efficient model
- **codellama**: Specialized for coding tasks
- **orca-mini**: Smaller, faster model
- **dolphin-mistral**: Enhanced instruction following

### Model Parameters
You can customize the AI behavior by modifying these parameters in `ollama_client.py`:

```python
"options": {
    "temperature": 0.7,    # Creativity (0.0-1.0)
    "top_p": 0.9,         # Nucleus sampling
    "max_tokens": 200,    # Response length
    "stop": ["User:", "System:"]  # Stop sequences
}
```

## Testing Ollama Connection

### 1. Check if Ollama is Running
```bash
curl http://localhost:11434/api/tags
```

### 2. Test Model Response
```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Hello, how are you?",
    "stream": false
  }'
```

### 3. Use Wolf AI Test Endpoint
Access: `http://localhost:5000/api/test-ollama`

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Ensure Ollama service is running: `ollama serve`
   - Check the URL in your environment variables
   - Verify firewall settings

2. **Model Not Found**
   - Download the model: `ollama pull llama2`
   - Check available models: `ollama list`

3. **Slow Responses**
   - Try a smaller model like `orca-mini`
   - Reduce `max_tokens` parameter
   - Check system resources (RAM/CPU)

4. **Out of Memory**
   - Use a smaller model
   - Reduce context window
   - Close other applications

### Performance Optimization

1. **For Better Speed:**
   ```env
   OLLAMA_MODEL=orca-mini
   ```

2. **For Better Quality:**
   ```env
   OLLAMA_MODEL=mistral
   ```

3. **For Coding Tasks:**
   ```env
   OLLAMA_MODEL=codellama
   ```

## Fallback Mode

If Ollama is not available, Wolf AI Assistant automatically falls back to:
- Pre-programmed responses for common queries
- Basic system command execution
- Time/date information

## Remote Ollama Setup

To use a remote Ollama instance:

1. **Server Setup:**
   ```bash
   # On the server
   OLLAMA_HOST=0.0.0.0 ollama serve
   ```

2. **Client Configuration:**
   ```env
   OLLAMA_URL=http://your-server-ip:11434
   ```

## Model Management

### List Available Models
```bash
ollama list
```

### Remove a Model
```bash
ollama rm llama2
```

### Update a Model
```bash
ollama pull llama2
```

## Security Considerations

1. **Local Use Only**: Keep Ollama on localhost for security
2. **Firewall**: Don't expose port 11434 to the internet
3. **Model Content**: Be aware that models may generate inappropriate content
4. **Data Privacy**: Conversations are not sent to external servers when using local Ollama

## Advanced Configuration

### Custom System Prompts
Modify the system prompts in `ollama_client.py` to change Wolf AI's personality:

```python
self.system_prompts = {
    'en': "You are Wolf, a helpful and friendly AI assistant...",
    'ur': "آپ Wolf ہیں، ایک مددگار اور دوستانہ AI اسسٹنٹ..."
}
```

### Multi-language Support
Wolf AI supports multiple languages. Configure the model for your preferred language:

```env
OLLAMA_MODEL=llama2  # Supports multiple languages
```

## Support

For Ollama-specific issues:
- Visit: https://github.com/jmorganca/ollama
- Documentation: https://ollama.ai/docs

For Wolf AI integration issues:
- Check the console logs
- Test the `/api/test-ollama` endpoint
- Verify your environment configuration