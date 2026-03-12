# 🚀 Wolf AI 2.0: Ultimate Enhancement Testing Guide

This guide covers the testing procedures for the latest high-performance modules: **OmniParser Vision**, **Neural Sonic (Kokoro) TTS**, **Deep Research**, and **Autonomous Web Intelligence**.

---

## 🏗️ 1. Required Setup (Apps & APIs)

Before testing, ensures you have the following "God-Mode" engines running:

### A. Vision Engine (Microsoft OmniParser)
The Vision Agent now uses **OmniParser** for pixel-perfect grounding. We have integrated it directly into the codebase.
1. **Weights Setup**: Run the download script to fetch the model files:
   ```bash
   python engines/omni_parser/download_weights.py
   ```
2. **Start the Server**: Run our custom REST API:
   ```bash
   python engines/omni_parser/omni_server.py
   ```
3. **Default Port**: Ensure it is accessible at `http://localhost:8001`.
4. **Ollama Model**: Run `ollama pull llava-phi3` to handle the visual reasoning.

### B. Deep Research (Crawl4AI)
1. **Hardware Setup**: Run `playwright install` in your terminal to ensure the research browser is ready.
2. **No API Key needed**: This runs entirely locally.

### C. Neural Sonic (Kokoro TTS)
1. **Model Weights**: The `kokoro` library will download its ~80MB model on first run. Ensure you have an active internet connection for the very first "Speak" command.

---

## 👁️ 2. Testing the Vision Agent (UI Grounding)

This tests the assistant's ability to "see" and "click" specific UI elements using OmniParser.

### Instructions:
1. Open a browser or any application (e.g., Spotify or Notepad).
2. In the Wolf AI Chat, say: **"Wolf, click on the Search bar in Chrome."**
3. **Expected Behavior**:
   - The terminal should log `[OmniParser] Screen parsed... Found X elements`.
   - You should see `[VisionAgent] Grounded action to OmniParser element`.
   - Your mouse cursor will physically move to the Search bar and click it.
4. **Try "Describe"**: Say **"Wolf, describe what you see on my screen."**
   - **Expected Behavior**: Wolf will analyze the screenshot and provide a detailed Markdown description of your open windows and active programs.

---

## 🧠 3. Testing Memory Recall (Autonomous History)

Verify the assistant's ability to browse its own past experiences.

### Instructions:
1. Issue a command: **"Wolf, remember that I like my habbit tracker apps in dark mode."**
2. Then ask: **"Wolf, what are my style preferences for apps?"**
3. **Expected Behavior**:
   - Wolf will trigger the `recall_memory` tool.
   - It will search past interaction logs and return: *"You previously mentioned that you prefer your habit tracker apps to have a dark mode UI."*

---

## 🎵 4. Testing Neural Sonic (Kokoro TTS)

Verify the ultra-human, low-latency speech synthesis.

### Instructions:
1. Go to the **Settings** tab in the Wolf AI UI.
2. Under **TTS Settings**, change the **Engine** to `kokoro`.
3. Go back to the **Chat** and say: **"Wolf, tell me a short story about a digital wolf."**
4. **Expected Behavior**:
   - Wolf will begin speaking almost instantly with the high-fidelity Kokoro voice.
   - The **Neural Sonic** status card on the Dashboard should switch from `STANDBY` to `PLAYING` in real-time.
   - The **Neural Frequency Visualizer** in the Media tab should react to the AI's voice if bridged through system audio.

---

## 🔍 5. Testing Deep Research & Web Intelligence

Test the assistant's ability to browse the live web and extract deep knowledge.

### Instructions:
1. **Web Search**: Ask a real-time question: **"Wolf, what is the current price of Bitcoin?"**
   - **Expected Behavior**: Wolf will trigger the `web_search` tool using DuckDuckGo and provide the latest data.
2. **Deep Research**: Provide a specific URL: **"Wolf, research the latest technical docs at https://ollama.com/library/llama3.2 and summarize the architecture."**
   - **Expected Behavior**:
     - The terminal logs `[Research] Deep scraping URL...`.
     - Wolf uses Crawl4AI to bypass overlays and extract clean Markdown.
     - You get a comprehensive summary based on the actual live website content.

---

## 👁️‍🗨️ 6. Testing Proactive Vision (Bug Watcher)

Test how the assistant uses Vision to analyze system errors autonomously.

### Instructions:
1. Create a "fake error" by typing `Fatal Error: System Core Dumped` in a large Notepad window.
2. Ensure **Proactive Bug Watcher** is enabled in Settings.
3. **Expected Behavior**:
   - The Bug Watcher (OCR) detects the text.
   - It automatically triggers the **Vision Agent** (`_analyze_screen`) to confirm if it's a real crash.
   - Wolf speaks: *"Alert. I've detected a system error in your application window..."*
   - A visual alert appears on your **Glass HUD**.

---

*Happy Testing! These features represent the cutting edge of local AI PC Control.*
