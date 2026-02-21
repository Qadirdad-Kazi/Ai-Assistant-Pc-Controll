# 🎙️ Professional Wake Word Setup (Porcupine)

By default, Wolf AI acts as its own wake word detector by transcribing every noise in your room using the CPU. This is free but can cause massive CPU spikes and audio driver lag on systems without powerful NVIDIA graphics cards.

To achieve **zero latency** and **0.1% CPU usage**, Wolf has been natively integrated with **Picovoice Porcupine**, the enterprise industry standard for wake word detection. 

Here is exactly how to create your own professional `wolf.ppn` file and link it to the app:

---

## 🏗️ Step 1: Generate your Wake Word File

1. Go to the [Picovoice Console](https://console.picovoice.ai/).
2. Create a free account and log in.
3. On your dashboard dashboard, find and copy your **AccessKey**. Keep this handy.
4. Navigate to the **Porcupine** section in the sidebar.
5. You will see a text box to design a Custom Wake Word. Type `Wolf` or `Hey Wolf`.
6. **CRITICAL:** Under the "Platform" dropdown, you MUST select **Windows (x86_64, arm64)**. *(If you select Web/Linux/Android, the file will crash Windows).*
7. Click **Train**. The server will take a few seconds to compile the neural network.
8. Click the download button to save the `.zip` file to your PC.
9. Extract the `.zip` and locate the `.ppn` file inside (e.g., `hey_wolf_windows.ppn`).

---

## ⚙️ Step 2: Link into Wolf AI 

You no longer have to edit any Python code to swap out the AI engines. It is fully integrated into the Wolf GUI.

1. Launch Wolf AI.
2. Click on the **Settings** tab.
3. Scroll down to the **Wake Word Engine** section.
4. **Picovoice Access Key:** Paste the long AccessKey you copied from the website in Step 1.
5. **Custom .ppn File Path:** Paste the absolute path to where you saved the `.ppn` file on your computer (e.g., `C:\Users\YourName\Downloads\hey_wolf_windows.ppn`).

---

## 🚀 Step 3: Restart and Observe

1. Close the Wolf AI window entirely.
2. Open your terminal and run `python main.py` again.

**What changes?**
When you look at your terminal during the boot-up sequence, you will now see:
`[STT] 🦔 Access Key found. Switching to high-performance Porcupine engine...`

Wolf is no longer using the heavy Whisper AI just to listen for its name. Your CPU usage will instantly drop back to normal levels, and uttering *"Wolf"* will trigger a reaction instantaneously!
