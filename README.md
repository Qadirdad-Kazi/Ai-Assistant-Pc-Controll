# VoiceCompanion: AI-Powered Voice Assistant

VoiceCompanion is an intelligent voice assistant application built with Electron and Python. It allows users to interact with their computer using voice commands, switch between an AI conversational mode and a direct PC control mode, and also supports text-based commands.

## Features

*   **Dual Mode Operation:**
    *   **AI Mode:** Engage in natural conversations with an AI (powered by Ollama) for information, questions, and general assistance.
    *   **PC Control Mode:** Execute direct commands to control your PC, such as opening applications, taking screenshots, and more.
*   **Voice and Text Input:** Interact via voice commands or type commands directly into the application.
*   **Wake Word Detection:** (If currently active and reliable) Activate the assistant using a customizable wake word.
*   **Real-time Transcription & TTS:** See your spoken words transcribed and hear responses spoken back.
*   **Customizable Settings:** (If settings UI is fully functional) Adjust voice gender, language, theme, etc.
*   **Cross-Platform:** Built with Electron for potential cross-platform compatibility (currently developed on macOS).

## Available PC Control Commands

In **PC Control Mode**, you can use the following voice or text commands:

### Application Control
- "Open [application name]" - Launches the specified application (e.g., "Open Chrome", "Open Safari")
- "Close [application name]" - Closes the specified application
- "Switch to [application name]" - Brings the specified application to the front

### System Operations
- "Take a screenshot" - Captures the screen and saves it with a timestamp
- "Volume up/down" - Adjusts system volume
- "Mute/Unmute" - Toggles system mute
- "Lock screen" - Locks your computer
- "Shut down" - Shuts down the computer
- "Restart" - Restarts the computer
- "Sleep" - Puts the computer to sleep

### Media Control
- "Play/Pause" - Toggles play/pause for media players
- "Next track" - Skips to the next track
- "Previous track" - Goes back to the previous track
- "Volume up/down" - Adjusts media volume

### Window Management
- "Maximize window" - Maximizes the current window
- "Minimize window" - Minimizes the current window
- "Close window" - Closes the current window
- "Switch window" - Cycles through open windows

### Web Browsing
- "Search [query]" - Performs a web search with the default browser
- "Go to [website]" - Opens the specified website in your default browser

### System Information
- "What time is it?" - Tells the current time
- "What's the date?" - Tells the current date
- "System status" - Provides system information

Note: Some commands may require specific applications to be installed or may work differently across operating systems.

## Tech Stack

*   **Frontend:**
    *   Electron
    *   HTML5
    *   CSS3
    *   JavaScript
*   **Backend:**
    *   Python
    *   `websockets` library (for WebSocket communication)
    *   `Ollama` (for AI model interaction, e.g., Llama 3.2)
*   **Voice & PC Control:**
    *   `speech_recognition` (for converting speech to text)
    *   `pyttsx3` (for text-to-speech)
    *   `PyAudio` (for microphone access)
    *   `pyautogui` (for PC automation tasks)
*   **Development:**
    *   Node.js & npm

## Prerequisites

*   **Node.js and npm:** Download and install from [nodejs.org](https://nodejs.org/).
*   **Python:** Version 3.8 or higher recommended. Download from [python.org](https://python.org/).
*   **Ollama:** Installed and running with a suitable model (e.g., `ollama pull llama3.2`). See [ollama.ai](https://ollama.ai/) for instructions.
*   **PortAudio:** Required by PyAudio.
    *   On macOS: `brew install portaudio`
    *   On Debian/Ubuntu: `sudo apt-get install libasound2-dev portaudio19-dev libportaudiocpp0`
    *   On Windows: Often bundled with PyAudio wheels, but ensure microphone drivers are working.

## Setup and Installation

1.  **Clone the Repository / Download Files:**
    ```bash
    # If it's a git repository
    # git clone <repository-url>
    # cd VoiceCompanion
    ```
    (Or simply navigate to your project directory if you have the files locally)

2.  **Install Node.js Dependencies:**
    Open a terminal in the project's root directory (`VoiceCompanion`) and run:
    ```bash
    npm install
    ```

3.  **Set Up Python Virtual Environment:**
    In the same terminal (project root):
    ```bash
    # Create a virtual environment
    python3 -m venv venv

    # Activate the virtual environment
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows (Git Bash or WSL):
    # source venv/Scripts/activate
    # On Windows (Command Prompt/PowerShell):
    # venv\Scripts\activate
    ```

4.  **Install Python Dependencies:**
    Ensure your virtual environment is activated. The `requirements.txt` file in the project is quite extensive. For the core functionality we've recently developed, the essential packages are:
    ```
    websockets
    requests
    SpeechRecognition
    PyAudio
    pyttsx3
    pyautogui
    # python-dotenv (recommended for managing environment variables)
    ```
    You can install these specific packages or use the existing `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Consider creating a streamlined `requirements_core.txt` for easier setup of essential features.)*

## Running the Application

1.  **Ensure Ollama is Running:** Start your Ollama server and make sure the desired model is available.
2.  **Start VoiceCompanion:**
    With the Python virtual environment activated, run the following command from the project's root directory:
    ```bash
    npm start
    ```
    This will launch the Electron application and start the Python backend server.

## Usage

*   **Mode Toggling:** Use the "AI Mode" and "PC Control Mode" buttons in the UI to switch between functionalities.
    *   **AI Mode:** Voice input is sent to the Ollama AI for conversational responses. Text input is typically disabled.
    *   **PC Control Mode:** Voice and text commands are interpreted for direct computer actions (e.g., "open Chrome", "take a screenshot").
*   **Voice Input:** Click the microphone icon (or use wake word if active) to speak your command/query.
*   **Text Input:** In PC Control Mode, type your command into the input field and press Enter or click the send button.

## Troubleshooting

*   **Microphone Access:** Ensure the application has permission to access your microphone. Check your OS settings.
*   **Python Errors:** If you encounter Python errors on startup, ensure the virtual environment is activated and all dependencies from `requirements.txt` (or the core list) are installed correctly.
*   **Ollama Connection:** Verify that your Ollama server is running and accessible (default: `http://localhost:11434`).
*   **`No module named 'tkinter'` (on some Linux for `pyautogui`):** You might need to install it, e.g., `sudo apt-get install python3-tk`.

---

*(Consider adding sections for Project Structure, Contributing, or License if desired.)*
