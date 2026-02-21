# 🧪 Wolf AI 2.0 Testing Guide

This guide details exactly how to run through and verify the new "God-Mode" features integrated into Wolf AI. 

## 1. 💻 Testing the Dev Agent (Autonomous Web Scaffolding)

The Dev Agent is no longer a mock script; it uses Vite and local LLMs to generate real code.

### Instructions:
1. Start the application by running `python main.py` in your terminal.
2. In the Chat interface, say or type a vague prompt like:  
   **"Wolf, build a website."**
3. **Expected Behavior:** Wolf will realize the prompt is vague and ask a clarifying question like: *"What framework would you like to use, and what should the website do?"*
4. Reply with specifics:  
   **"I want a React app using Vite to track my daily habits. Make it a dark mode UI."**
5. **Expected Behavior:** Wolf will acknowledge the request, run the `create-vite` CLI commands in the background (within the `workspace/` folder), and use the local LLaMA model to rewrite `App.jsx` with a fully functional UI.
6. **Verification:** Navigate to the `workspace/wolf_project` directory on your PC. You should see a standard Vite React project structure. Run `npm install` and `npm run dev` to see the AI-generated code live in your browser!

---

## 2. 📱 Testing the Phone Handover Protocol (Receptionist AI)

This tests the logic loop of delegating a call, the AI answering, and properly bridging audio when a caller wants to talk directly to you.

### Instructions:
1. In the Chat interface, issue a directive:  
   **"Wolf, Rafay will call soon. Ask him what time our meeting is."**
2. **Expected Behavior:** Wolf confirms the directive is saved.
3. *Since you might not have a physical GSM modem hooked up at this exact second, this logic runs inside the `core/receptionist.py`. To test the live GUI, wait for an expected call. Or for dev testing, use the mock scripts we ran earlier.*
4. When "Rafay" calls, Wolf answers and says: *"Hello Rafay, this is Wolf AI. What's the schedule for our meeting today?"*
5. If Rafay replies with **"I want to talk to Qadirdad"**, Wolf will:
   - Put Rafay on hold.
   - Speak out of your Desktop Speakers: *"Qadirdad, Rafay wants to talk to you."*
   - A prompt will await your approval. 
6. **Verification:** If you approve, Wolf exits the execution loop and bridges your microphone to the phone line, allowing you to seamlessly take over the call. Check the **Receptionist Logs** tab in the GUI to see the full transcript and the final status marked as `Handed Over`.

---

## 3. ⚙️ Testing God-Mode GUI Settings

This verifies that the new dynamic UI controls actually interact with the background Python threads.

### Instructions:
1. Open the Wolf AI application.
2. Navigate to the **Settings** tab.
3. Scroll down to the **God-Mode Integrations** section.
4. **Test the HUD:** Toggle the **"Transparent Desktop HUD"** switch.
   - **Expected Behavior:** A borderless, slightly transparent window should appear locked to the top-right corner of your screen. Toggle it off, and it should vanish immediately. 
5. **Test the Bug Watcher:** Toggle the **"Proactive Bug Watcher"** switch.
   - **Expected Behavior:** Check your terminal output. You should see logs indicating: `[Proactive Layer] Bug Watcher started. Polling screen...`. Toggle it off, and the thread gracefully terminates.
6. **Test the COM Port:** Edit the text box for the **GSM Gateway COM Port**. This preference handles persistence without needing code modifications.

---

## 4. 👁️ Testing the Bug Watcher (OCR Screencap)

This tests the system's ability to watch your screen and detect application crashes proactively.

### Instructions:
1. In the **Settings** tab, ensure the **Proactive Bug Watcher** switch is **ON**.
2. Open a random Notepad file, a blank web page, or an IDE.
3. Type the word `Traceback (most recent call last)` or `Fatal Error:` in large font on the screen, mimicking a Python crash or general system failure.
4. Keep that window in plain sight on your monitor.
5. **Expected Behavior:** Within 10 seconds, the background Tesseract OCR engine will scan the screen, identify the crash signature, and output a severe warning to your terminal: `[Proactive Layer] 🔥 CRASH DETECTED ON SCREEN: TRACEBACK (MOST RECENT CALL LAST)`. 
6. *Note:* If you have the Glass HUD enabled, it will also push a visual alert to the dynamic overlay!

---
*Happy Testing! Consult the main README if dependencies like Tesseract OCR or Vite are not installed.*
