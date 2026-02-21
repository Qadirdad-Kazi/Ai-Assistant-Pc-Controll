# 🐺 Wolf AI 2.0 — The "God-Mode" Agent

<p align="center">
  <img src="wolf_avatar.png" alt="Wolf AI Logo" width="120" height="120">
</p>

**Wolf AI 2.0** is the ultimate local, privacy-first AI agent designed to command your PC, handle your mobile phone calls via GSM, and master your developer workflow. Moving beyond a simple chatbot, Wolf is a high-performance modular system running entirely on YOUR machine.

> 🔒 **God-Mode, Offline.** No cloud dependencies. No mandatory API keys. Absolute control over your Windows OS and telephony.

---

## ✨ Key Features (Wolf 2.0)

| Feature | Description |
|---------|-------------|
| 🖥️ **PC Commander** | Full OS integration. Control volume, power states, manage windows, and take screenshots via natural language. |
| 💻 **Dev Agent** | Autonomous scaffolding. Ask Wolf to build a React app; it interactively gathers requirements, executes Vite/CLI commands in the background, and uses Ollama to dynamically generate the functional source code (e.g., `App.jsx`). |
| 📞 **Receptionist Mode** | Local GSM/SIP bridge. Connect a SIM800L module to intercept calls. Features a full **Handover Protocol**: puts callers on hold, announces them through your desktop speakers, and bridges your mic if you accept. |
| 🎨 **Glass HUD** | Transparent, click-through overlay interface that floats above all apps to deliver proactive system alerts. Switchable via Settings. |
| 🧠 **Proactive Layer** | Background "Bug Watcher" thread that monitors your screen state via OCR and logs crashes or errors pre-emptively. Switchable via Settings. |
| 🎵 **Sonic Interface** | Futuristic media controller featuring a neural frequency visualizer that mathematically syncs to BPM and audio energy. |
| ⚙️ **God-Mode Settings** | Dedicated GUI tab to dynamically configure COM Ports for GSM modems and toggle background automation threads (HUD/Bug Watcher). |
| 🎤 **Ultra-Low Latency Voice** | Streamlined audio pipelines bridging `RealTimeSTT` with `PiperTTS` executable for near-instant conversational responses. |

---

## 🏛️ Core Architecture

Wolf 2.0 transitions from a monolithic script into a segmented, high-performance capability stack:

- **Brain (Python):** Central orchestration handled by `FunctionGemma` and `Ollama` (`llama3.2:3b`).
- **Hands (OS/Dev Agent):** PyAutoGUI, Subprocess, and custom OS hooks to command the system and scaffold code.
- **Voice (Audio Bridge):** Advanced hardware routing pushing TTS directly to a GSM Modem's Line-Out while isolating the desktop.
- **UI (PySide6):** Hardware-accelerated components, blur effects, and borderless HUD overlays.

---

## 📋 Prerequisites

### Required Software

| Software | Purpose | Download |
|----------|---------|----------|
| **Miniconda** | Python environment manager | [miniconda.io](https://docs.anaconda.com/miniconda/) |
| **Ollama** | Local AI model server | [ollama.com](https://ollama.com/download) |
| **NVIDIA GPU** (Recommended) | Faster AI inference for local models | GPU with 4GB+ VRAM |

### Hardware Recommendations

- **Minimum**: 8GB RAM, any modern CPU
- **Recommended**: 16GB RAM, NVIDIA GPU with 6GB+ VRAM
- *(Optional)*: Hardware GSM Modem (e.g., SIM800L) connected via USB UART for Phone Integration.

---

## 🚀 Quick Start Guide

### Step 1: Install Ollama & Pull the Model

Ensure Ollama is installed and running in the background.

```bash
# Recommended Model for routing and chatting
ollama pull llama3.2:3b
```

### Step 2: Set Up the Project

```bash
# Clone the repository
git clone https://github.com/your-username/wolf-ai.git
cd wolf-ai

# Create a conda environment
conda create -n wolfai python=3.11 -y
conda activate wolfai

# Install dependencies
pip install -r requirements.txt
```

*(NVIDIA users should install PyTorch with CUDA support for significantly faster STT/TTS and inference).*

### Step 3: Run the Application

```bash
python main.py
```

---

## 🎙️ Operating Wolf

Wolf AI is natively listening. Say the wake word **"wolf"** and speak your command naturally.

### Example Commands

- **PC Control:** *"Wolf, lower the volume to 20"* or *"Wolf, take a screenshot"* or *"Wolf, lock the computer"*
- **Dev Agent:** *"Wolf, build a quick React app for a todo list"*
- **Media:** *"Wolf, play some lo-fi music"*
- **Knowledge:** *"Wolf, explain quantum computing"*

---

## 📞 Phone Integration (Receptionist Mode) Setup

Unlike standard web-based VoIP, Wolf 2.0 connects directly to local Pakistani cellular networks (or any generic GSM) via physical AT commands. 

1. Connect your GSM modem (e.g., SIM800L) to a USB Serial adapter and plug it into your PC.
2. Open the **Settings** tab in the Wolf UI and navigate to the **God-Mode Integrations** section.
3. Enter your assigned COM Port (e.g., `COM3`).
4. Ensure the Audio Line-Out of the modem is routed to a PC Line-In, and the PC Line-Out is routed to the Modem Line-In.
5. Open the **Receptionist Logs** tab in the GUI. You can now delegate calls, have the AI answer, or utilize the hold-and-announce handover protocol!

---

## 🛠️ Configuration

All configuration is centralized in `config.py`.

```python
# The main chat model
RESPONDER_MODEL = "llama3.2:3b"

# Enable/disable voice assistant
VOICE_ASSISTANT_ENABLED = True

# Change wake word
WAKE_WORD = "wolf"
```

---

## 🤝 Contributing

We welcome contributions to expand the "God-Mode" capabilities, especially around integrating robust Vision Language Models (VLMs) into the Proactive Bug Watcher layer.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/advanced-vlm`
3. Commit your changes
4. Submit a pull request

<p align="center">
  <strong>The Wolf is evolving.</strong><br>
  Made with ❤️ for local AI enthusiasts
</p>
