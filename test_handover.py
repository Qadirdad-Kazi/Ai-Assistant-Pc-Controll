import time
from core.function_executor import executor
from core.receptionist import receptionist

# Set directive
print("Setting directive through executor...")
executor.execute("set_call_directive", {"caller_name": "Rafay", "instructions": "Ask him what time the meeting is."})

print("\n--- SIMULATION 1: Handover Request (Approved) ---")
print("Simulating incoming call from Rafay (+923001234567)...")
receptionist.handle_incoming_call("Rafay Khwaja (+923001234567)", mock_caller_speech="I want to talk to Qadirdad right now.", mock_user_response="ok")

print("\n--- Call Logs ---")
for log in receptionist.call_logs:
    print(log)
