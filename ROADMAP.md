# 🐺 Wolf AI — The "God-Mode" Roadmap

> **Vision:** To build the ultimate local, privacy-first AI agent that commands the PC, handles the phone, and masters the developer workflow.

---

## 📋 Table of Contents

1. [🏛️ Core Architecture (Wolf 2.0)](#️-core-architecture-wolf-20)
2. [🖥️ Full PC Control & OS Integration](#️-full-pc-control--os-integration)
3. [💻 AI Developer Workflow (The "Dev Agent")](#-ai-developer-workflow-the-dev-agent)
4. [📞 AI Phone Assistant (Receptionist Mode)](#-ai-phone-assistant-receptionist-mode)
5. [🧠 Cognitive Memory & Proactive Layer](#-cognitive-memory--proactive-layer)
6. [🎨 UI/UX: The "Glass" HUD](#-uiux-the-glass-hud)
7. [📱 Mobile-to-PC Bridge](#-mobile-to-pc-bridge)
8. [🚀 Implementation Phases](#-implementation-phases)
9. [📦 Strategic Tech Stack](#-strategic-tech-stack)
10. [🐛 Known Issues & Optimization](#-known-issues--optimization)

---

## 🏛️ Core Architecture (Wolf 2.0)
*Moving from a monolithic script to a high-performance modular system.*

- **Wolf-Brain (Python):** Central orchestration, Routing, and RAG logic.
- **Wolf-Voice (C++/Rust):** Ultra-low latency audio processing for "Instant Response" feel.
- **Wolf-Executor (Rust/Python):** The high-speed "hands" that control the OS, mouse, and keyboard.
- **Wolf-UI (PySide6/Electron):** A sleek, modern interface with hardware acceleration.

---

## 🖥️ Full PC Control & OS Integration
*Complete command of the Windows environment.*

### System Actions
- **Process Stealth:** Terminate background bloatware or high-CPU tasks automatically.
- **Security:** Auto-lock PC when you walk away; Master PIN for destructive actions.
- **Hardware Orchestration:** Control brightness, volume, fan speeds, and RGB via voice.
- **File Commander:** Advanced file movement, bulk renaming, and intelligent folder organization.

### Desktop Agent (VLM-Powered)
- **Visual Task Loop:** Screenshot → VLM analysis → `pyautogui` action → Repeat.
- **OCR Integration:** Read any text on screen, including locked documents or videos.
- **UI Navigation:** *"Wolf, click the export button in Premiere Pro"* — Wolf finds the pixel coordinates and clicks.

---

## 💻 AI Developer Workflow (The "Dev Agent")
*A senior developer living inside your machine.*

- **Autonomous Scaffolding:** Build entire React/Next.js/Python projects from a single prompt.
- **Terminal Master:** Wolf runs its own terminal, installs `npm/pip` packages, and fixes its own build errors.
- **VS Code Integration:** Deep integration to edit files, refactor code, and write unit tests.
- **Pre-emptive Debugging:** Wolf watches your screen and suggests fixes for errors *before* you ask.

---

## 📞 AI Phone Assistant (Receptionist Mode)
*Your personal assistant on the phone line.*

- **Local GSM / SIP Bridge:** Handle real-time phone calls via a Physical GSM Gateway (e.g., SIM module via AT commands), a SIP/VOIP line from a local Pakistani telecom, or an Android auto-responder bridge. (Twilio/VAPI is not supported locally).
- **Hybrid TTS:** Socially-tuned, emotional voices for calls (ElevenLabs) vs. fast local voices (Piper) for utility.
- **Real-time Research:** If a caller asks for a price or date, Wolf searches the web *live* and answers them.
- **Call Archives:** Full transcripts, summaries, and sentiment analysis for every incoming call.

---

## 🧠 Cognitive Memory & Proactive Layer
*Moving from Reactive to Proactive.*

- **Long-Term Vector Memory:** Wolf remembers details from conversations 6 months ago using ChromaDB.
- **The Proactive Layer:** Wolf monitors system health, calendar conflicts, and project deadlines to notify you *before* problems occur.
- **Shadow Files:** A local database of your preferences, coding style, and habits.

---

## 🎨 UI/UX: The "Glass" HUD
*Interfaces inspired by Jarvis and futuristic OS design.*

- **HUD Mode:** A transparent overlay that lives on top of your screen.
- **Visual Feedback:** Ghostly highlights on buttons when Wolf is about to click them for you.
- **Sonic Interface:** Real-time frequency visualizers and "living" UI animations that react to your voice.

---

## 📱 Mobile-to-PC Bridge
*Control your PC from anywhere.*

- **Mobile App/Web UI:** A secure React Native app to send commands to Wolf from your phone.
- **Remote Execution:** *"Wolf, turn on the heater (Kasa) and start my build server."*
- **Notifications:** Get a ping on your phone when a long-running task finishes on your PC.

---

## 🚀 Implementation Phases

### Phase 1: PC Control & Dev Agent (Completed)
- [x] Build `core/pc_control.py` (The "Hands").
  - *Completed: Built core OS automation methods using subprocess and pyautogui.*
  - *How to test: Run the app and type "Lock the PC" or "Open Calculator".*
- [x] Add 15+ System Actions (Volume, Apps, Windows).
  - *Completed: Added 15+ varied system commands including sleep, restart, screenshots, mute, and media controls.*
  - *How to test: Type "Take a screenshot" or "Mute the volume".*
- [x] Implement the first "Website Scaffolder" command.
  - *Completed: Implemented core/dev_agent.py with autonomous project generation.*
  - *How to test: Type "Build a React app for a todo list".*

### Phase 2: Phone Integration (The "voice" via Local Carrier) (Completed)
- [x] Configure Physical GSM Gateway (AT commands over Serial) or setup SIP/VOIP.
  - *Completed: Built core/gsm_gateway.py to handle PySerial AT commands for devices like SIM800L.*
  - *How to test: Run a dummy script or interact with `gsm_gateway.connect()` via the Python console.*
- [x] Build the local Python audio bridge to handle streams from the GSM/SIP endpoint.
  - *Completed: Built core/audio_bridge.py for isolating STT/TTS channels.*
  - *How to test: Review `audio_bridge.py` logic to see the virtual audio cable mappings being maintained during a call link.*
- [x] Implement ElevenLabs emotional TTS (or Piper equivalent) for phone calls.
  - *Completed: Connected the ultra-fast local `PiperTTS` for all voice responses to handle real-time SIP/GSM conversations locally.*
  - *How to test: Type a command via voice prompt and observe Piper responding rapidly.*
- [x] Create the "Call Logs" GUI tab for logging intercepts and transcripts.
  - *Completed: Created the Receptionist Logs tab UI and imported it into the Main Sidebar replacing older features.*
  - *How to test: Launch `python main.py` and click the Phone icon on the sidebar.*

### Phase 3: The HUD & Proactive Layer
- [ ] Build the transparent overlay UI.
- [ ] Implement the screen-watching "Bug Watcher" logic.

---

## 📦 Strategic Tech Stack

- **Brain:** Python 3.11 + Ollama (Llama 3.2 / Qwen 2.5).
- **Automation:** PyAutoGUI + PyGetWindow + Playwright.
- **Performance:** Rust extensions (via PyO3) for screen capture and UI events.
- **Storage:** SQLite (History) + ChromaDB (Vector Knowledge).
- **Communication:** GSM Gateway / SIP (Phone) + FastAPI (Mobile Bridge).

---

## 🐛 Known Issues & Optimization
*Top priority fixes for stability.*

1. **Dependency Hell:** Fix `requirements.txt` to include `langchain`, `watchdog`, and `pywin32`.
2. **Startup Lag:** Move `KnowledgeBase` initialization to a truly lazy background thread.
3. **Path Stability:** Convert all hardcoded strings into `Path()` objects.

---

<p align="center">
  <strong>The Wolf is evolving.</strong><br>
  Maintained by <a href="https://qadirdadkazi.com">Qadirdad-Kazi</a>
</p>