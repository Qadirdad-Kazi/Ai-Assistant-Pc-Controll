# 🏗️ Wolf AI 2.0: System Architecture

Wolf AI 2.0 is built on a **Layered Agentic Architecture**, designed for high-performance PC orchestration and autonomous business intelligence. Unlike standard chatbots, Wolf AI integrates directly with pixel-level vision and machine-level serial communication.

---

## 1. Core Orchestration Engine

The heart of the system is the **[`AdvancedTaskExecutor`](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/core/advanced_task_executor.py)**. 

### Multi-Step Chaining
Wolf AI doesn't just execute single actions; it builds **Chain-of-Command** sequences.
- **Example**: *"Create a project folder and open Visual Studio Code."*
- **Logic**: The executor builds a sequence: `[create_folder] -> [open_app] -> [tile_windows]`.
- **Progress Tracking**: Real-time progress is broadcasted to the **[Workflow HUD](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/frontend/src/App.jsx)** on the frontend.

---

## 2. The Synaptic Layer (Continual Learning)

Wolf AI 2.0 features a **Neural Experience Database** that allows it to evolve through user interaction.

### How it Works:
1. **Failure Monitoring**: If a standard command (e.g., *"Open Spotify"*) fails, the executor marks a failure event.
2. **Correction Capture**: If the user provides a series of manual corrective steps, the AI autonomously bundles them.
3. **Synaptic Persistence**: These instructions are saved to the **[`learned_heuristics`](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/core/database.py)** table.
4. **Adaptive Priority**: In future interactions, the **[Direct Router](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/core/llm.py)** intercepts the query before it hits the LLM, executing the learned "Synaptic Path" instantly.

---

## 3. Vision-Grounded Actions (OmniParser)

The **[`VisionAgent`](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/core/vision_agent.py)** provides pixel-perfect grounding for UI interactions.
- **Technology**: Uses **Microsoft's OmniParser** to convert screen pixels into a structured list of UI elements (buttons, inputs, menus).
- **Coordinate Mapping**: Automatically maps AI intent to exact screen coordinates for `pyautogui` clicks and typing.

---

## 4. Hardware/Audio Integration

### GSM Modem (SIM800L)
Integrates via Serial (UART) to provide local cellular capabilities:
- **Receptionist Mode**: Autonomously answers calls, transcribes them, and performs post-call sentiment analysis.
- **Audio Bridge**: Cross-routes cellular audio to the PC's STT and TTS engines using virtual or physical audio cables.

---

## 5. Technology Stack Summary
- **Languages**: Python (Core), React (Frontend).
- **Inference**: Local Ollama (FunctionGemma, Qwen2, LLaVA).
- **Speech**: Faster-Whisper (STT), Neural Sonic/Kokoro (TTS).
- **Automation**: PyAutoGUI, AppleScript (macOS), Tesseract (OCR).
- **Persistence**: SQLite (Audit Logs, Synaptic Memory, CRM).
