# Test Case: Call Assistant & GSM Integration

## 1. Purpose
To verify that Wolf AI 2.0 can autonomously handle incoming GSM calls via the SIM800L modem, transcribe conversations, detect business intent (deal size), and log sentiment analysis to the [Receptionist Dashboard](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/frontend/src/pages/CallLogs.jsx).

## 2. Preconditions
- **Hardware**: SIM800L GSM Module, 5V / 2A Power Supply, Active SIM Card.
- **Wiring**: TX/RX pins correctly mapped to the host machine's UART/Serial port.
- **Environment**: SIM800L must have a cellular signal (verified via blinking LED).
- **Services**: Ollama must be running for transcript summarization.

## 3. Execution Steps

### Automated Test
1.  Open terminal in project root.
2.  Run: `python3 tests/test_receptionist.py`
3.  Verify the `call_logs` table reflects the mocked transcript entries with positive sentiment.

### Manual Verification
1.  **Action**: Call the SIM number from your mobile phone.
2.  **Action**: Say: "Hello, I'd like to talk about a software project worth 10,000 dollars."
3.  **Observation**: 
    - Wolf should autonomously answer the call.
    - Check the [Strategy Dashboard](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/frontend/src/pages/Analytics.jsx) - the project value should be added to the "Total Pipeline" metric.
4.  **Verification**: Confirm a follow-up email draft appears in the [Tasks](file:///Users/qadirdadkazi/Desktop/Github%20Clones/Ai-Assistant-Pc-Controll/frontend/src/pages/Tasks.jsx) menu.

## 4. Expected Results
- **Transcript Accuracy**: The CRM entry matches the spoken words within a 90% confidence interval.
- **BI Extraction**: The "Deal Size" field in the database should show `10000.0`.
- **Mood Detection**: The sentiment analysis must correctly identify "Positive" or "Interested" based on the transcript.
