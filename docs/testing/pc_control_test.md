# Test Case: PC Control & Workspace Orchestration

## 1. Purpose
To verify that Wolf AI 2.0 can autonomously manage the macOS desktop environment, including proportionate window tiling, dynamic application launching, and system-level parameter control (volume, power states).

## 2. Preconditions
- **OS**: macOS (for AppleScript tiling tests).
- **Permissions**: Accessibility permissions must be granted to the terminal or IDE running the tests (System Settings > Privacy & Security > Accessibility).
- **Libraries**: `pyautogui` must be installed.
- **Tools**: VS Code, Google Chrome, and Finder should be open for live tiling verification.

## 3. Execution Steps

### Automated Test
1.  Open terminal in project root.
2.  Run: `python3 tests/test_pc_control.py`
3.  Verify all unit tests pass (especially `test_window_tiling_macos`).

### Manual Verification
1.  **Command**: "Wolf, open Visual Studio Code and tile my windows."
2.  **Observation**: 
    - VS Code should snap to the left 60% of the screen.
    - Finder and Chrome should split the right 40%.
3.  **Command**: "Wolf, set volume to 50%."
4.  **Observation**: The system volume HUD should appear and adjust to the specified level.

## 4. Expected Results
- **Automated**: Subprocess mock calls for `osascript` must contain the correct bounds logic: `{0, 0, screen_width * 0.6, screen_height}`.
- **Manual**: Apps must reposition instantly without manual dragging.
- **Success Criteria**: Every command triggers a verbal confirmation and an entry in the [Action Log](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/frontend/src/pages/Activity.jsx).
