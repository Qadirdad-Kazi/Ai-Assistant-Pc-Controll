# Test Case: Continual Learning & Heuristic Evolution

## 1. Purpose
To verify that Wolf AI 2.0 can autonomously learn from "Experience" when a standard command fails, capture a user-provided correction as a permanent heuristic, and prioritize that learned path in future interactions.

## 2. Preconditions
- **Database**: SQLite `wolf_core.db` must have the `learned_heuristics` table (automatically created on startup).
- **Services**: Ollama must be active for intent detection.

## 3. Execution Steps

### Automated Test
1.  Open terminal in project root.
2.  Run: `python3 tests/test_learning_loop.py`
3.  Verify the "Synaptic reinforcement" test successfully increments the `success_count`.

### Manual Verification
1.  **Simulate Failure**: 
    - Ask: "Wolf, open Spotify." 
    - (Assuming Spotify isn't in your standard Path/Apps) Wolf should report a failure.
2.  **Provide Correction**: 
    - Ask: "Wolf, click the Windows icon, type 'Spotify', and press enter."
    - Wolf should execute these steps and announce: *"I have successfully learned how to handle 'Open Spotify' for next time."*
3.  **Verify Evolution**:
    - Ask: "Wolf, open Spotify."
    - **Observation**: Wolf should immediately execute the learned "click/type/enter" sequence instead of trying the default launch logic.
4.  **Confirm HUD**: 
    - Check the [Knowledge Base](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/frontend/src/pages/KnowledgeBase.jsx).
    - The entry for "Open Spotify" should show `Use Count: 1`.

## 4. Expected Results
- **Memory Persistence**: The learned workflow resides in the `learned_heuristics` table after a restart.
- **Adaptive Priority**: The [Adaptive Router](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/core/llm.py) must intercept the query *before* the LLM and trigger the "Synaptic Path."
- **Transparency**: Every step of the learned macro is audible and logged in the [System Activity](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/frontend/src/pages/Activity.jsx).
