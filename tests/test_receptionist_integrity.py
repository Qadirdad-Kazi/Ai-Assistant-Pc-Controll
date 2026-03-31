import sys
import os
import time
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.receptionist import receptionist
from core.gsm_gateway import gsm_gateway
from core.audio_bridge import audio_bridge
from core.database import db

def test_full_call_cycle():
    """
    Simulates a full call cycle to verify all professional modules are wired.
    This test mocks the hardware but executes the real logic.
    """
    print("\n--- [Integrity Test] Starting Professional Call Cycle Verification ---")
    
    # 1. Setup Directive
    print("[Test] Step 1: Setting up directive...")
    receptionist.add_directive("Amazon", "Tell them to leave the package at the front door.")
    
    # 2. Simulate Incoming Call
    print("[Test] Step 2: Simulating incoming call from +123456789 (Amazon)...")
    
    # Mocking the interaction inputs
    # In a real test, we would mock stt.recorder.text()
    
    def run_receptionist():
        receptionist.handle_incoming_call("+123456789")

    call_thread = threading.Thread(target=run_receptionist)
    call_thread.start()
    
    time.sleep(2)
    print(f"[Test] Current Call Status: {db.get_call_logs(limit=1)[0]['status'] if db.get_call_logs() else 'Pending'}")
    
    # 3. Simulate Hangup
    print("[Test] Step 3: Simulating modem hangup...")
    gsm_gateway.is_connected = True # Mock connection
    gsm_gateway.hangup_call()
    
    print("[Test] Step 4: Verifying database logs...")
    logs = db.get_call_logs(limit=1)
    if logs:
        print(f"✅ Success: Call logged with status '{logs[0]['status']}'")
    else:
        print("❌ Failure: Call was not logged in database.")

if __name__ == "__main__":
    test_full_call_cycle()
