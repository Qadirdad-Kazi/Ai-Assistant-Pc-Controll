import time
from core.function_executor import executor
from core.receptionist import receptionist
from config import RESPONDER_MODEL

print("Setting directive through executor...")
print(executor.execute("set_call_directive", {"caller_name": "Rafay", "instructions": "Ask him what time the meeting is."}))

print("\nSimulating incoming call from Rafay (+923001234567)...")
receptionist.handle_incoming_call("+923001234567")

print("\n--- Call Logs ---")
for log in receptionist.call_logs:
    print(log)
