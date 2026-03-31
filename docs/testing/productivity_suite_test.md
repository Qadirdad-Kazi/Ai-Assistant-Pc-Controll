# Test Case: Executive Productivity & Document Generation

## 1. Purpose
To verify that Wolf AI 2.0 can autonomously handle post-call business operations, including drafting context-aware follow-up emails, generating professional Markdown proposals, and synchronizing entries into the CRM database.

## 2. Preconditions
- **OS**: macOS (for AppleScript email drafting).
- **App**: Apple Mail must be configured with an active account.
- **Environment**: Productivity suite must have write access to the project's `proposals/` directory.

## 3. Execution Steps

### Automated Test
1.  Open terminal in project root.
2.  Run: `python3 tests/test_productivity_suite.py`
3.  Confirm that `test_proposal.md` was created, contained the correct client data, and was successfully cleaned up.

### Manual Verification
1.  **Command**: "Wolf, draft a follow-up email to `client@example.com` about the 5,000 dollar project we just discussed."
2.  **Observation**: 
    - The Apple Mail app should open a new message window.
    - **Verification**: Check if the body contains references to "5,000 dollars" and "mobile app project."
3.  **Command**: "Wolf, generate a project proposal for `Vertex Solutions` for an AI migration worth 15,000 dollars."
4.  **Observation**: 
    - A new `.md` file should appear in your `proposals/` folder.
    - **Verification**: Review the document to confirm it uses a professional tone and correct financial figures.

## 4. Expected Results
- **Email Accuracy**: The AppleScript must correctly populate `recipient`, `subject`, and `content`.
- **Document Quality**: Proposals must be generated in clean Markdown format with professional headers.
- **Task Logging**: Every document generation must be recorded in the [Receptionist Dashboard](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/frontend/src/pages/CallLogs.jsx) as a completed action.
