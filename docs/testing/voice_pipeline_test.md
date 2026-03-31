# Test Case: Voice Command Pipeline & Intent Mapping

## 1. Purpose
To verify the entire audio-to-action lifecycle: from local Wake Word detection (Porcupine) to high-speed STT (Faster-Whisper) and precise Intent Routing (Function Gemma).

## 2. Preconditions
- **Audio**: Working Microphone (System Default).
- **Wake Word**: `wolf` Access Key must be valid in `config.py`.
- **Services**: Ollama must be running with the `function_gemma` or `qwen2:7b` model loaded.
- **Environment**: Silence or low background noise for high-confidence STT.

## 3. Execution Steps

### Automated Test
1.  Open terminal in project root.
2.  Run: `python3 tests/test_voice_pipeline.py`
3.  Confirm that complex multi-sentence queries are correctly decomposed into a list of tuples (e.g., `[("pc_control", ...), ("pc_control", ...)]`).

### Manual Verification
1.  **Wake up**: Say "Wolf." 
    - **Observation**: The [Voice Core](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/frontend/src/App.jsx) HUD should pulse cyan, indicating it's listening.
2.  **Intent Test**: Say "Wolf, create a project folder on my desktop and open Visual Studio Code."
3.  **Observation**: 
    - STT should transcribe the request in the console.
    - Wolf should announce: *"Starting step 1: create folder..."*
    - **Verification**: Check your desktop for the new folder.

## 4. Expected Results
- **Latency**: STT transcription should complete in under 500ms for short phrases.
- **Routing Accuracy**: Intent mapping must correctly distinguish between conversational talk ("How are you?") and system commands ("Lock PC").
- **Parameter Extraction**: The `target` and `action` parameters must accurately reflect the specific app or directory names spoken.
