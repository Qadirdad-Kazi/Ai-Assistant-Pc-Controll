import sys
import os
import time
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.calendar_manager import calendar_manager
from core.receptionist import receptionist

def test_calendar_detection():
    print("\n--- [System Test] Calendar Sync Verification ---")
    
    # Mock an event that looks like it came from AppleScript
    mock_event = {
        "uid": "test-123",
        "summary": "Call with Steve Jobs",
        "start_str": "Tuesday, March 31, 2026 at 10:00 AM",
        "description": "Discuss future silicon strategy. Wolf should handle initial pleasantries."
    }
    
    print(f"[Test] Injecting mock event: {mock_event['summary']}")
    
    # Manually trigger processing
    calendar_manager._process_event(mock_event)
    
    # 1. Check if Receptionist got it
    caller_key = "steve jobs"
    if caller_key in receptionist.expected_calls:
        print(f"✅ Success: Receptionist directive added for '{caller_key}'")
        print(f"   Instructions: {receptionist.expected_calls[caller_key]}")
    else:
        print(f"❌ Failure: Receptionist did not receive directive.")

if __name__ == "__main__":
    test_calendar_detection()
    # Give a moment for the async task to (potentially) run if backend_api was imported
    time.sleep(1)
