"""
Calendar Manager - Integration with macOS Calendar.app via AppleScript.
Polls for upcoming 'Call' events and prepares the Receptionist.
"""
import subprocess
import threading
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from core.receptionist import receptionist  
from core.tts import tts  
from config import CYAN, RESET, GREEN, YELLOW

# --- Configuration ---
POLL_INTERVAL_SECONDS = 300 # 5 minutes
REMINDER_LEAD_TIME_MINUTES = 10 
CALENDAR_KEYWORDS = ["call", "phone", "zoom", "meeting with", "interview"]

class CalendarManager:
    def __init__(self):
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._processed_event_ids = set() # Prevent duplicate reminders
        
    def start(self):
        """Start the background polling loop."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print(f"{CYAN}[CalendarManager] Started background sync loop.{RESET}")

    def stop(self):
        self.running = False

    def _poll_loop(self):
        while self.running:
            try:
                self.sync_now()
            except Exception as e:
                print(f"{YELLOW}[CalendarManager] Error during sync: {e}{RESET}")
            time.sleep(POLL_INTERVAL_SECONDS)

    def sync_now(self):
        """Manual sync of calendar events."""
        print(f"{CYAN}[CalendarManager] Syncing with macOS Calendar...{RESET}")
        events = self._fetch_calendar_events()
        
        for event in events:
            self._process_event(event)

    def _fetch_calendar_events(self) -> List[Dict[str, Any]]:
        """Execute AppleScript to get today's events."""
        script = """
        set today to current date
        set time of today to 0
        set tomorrow to today + 86400
        set results to {}
        tell application "Calendar"
            repeat with aCal in calendars
                set theEvents to (every event of aCal whose start date is greater than or equal to today and start date is less than tomorrow)
                repeat with anEvent in theEvents
                    set end of results to (uid of anEvent & "|" & summary of anEvent & "|" & (get start date of anEvent as string) & "|" & description of anEvent)
                end repeat
            end repeat
        end tell
        return results
        """
        try:
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print(f"{YELLOW}[CalendarManager] osascript error: {result.stderr}{RESET}")
                return []
            
            raw_output = result.stdout.strip()
            if not raw_output:
                return []
            
            # Split by comma-space which osascript uses for list returns
            raw_events = raw_output.split(", ")
            parsed_events = []
            
            for raw in raw_events:
                parts = raw.split("|")
                if len(parts) >= 3:
                    parsed_events.append({
                        "uid": parts[0],
                        "summary": parts[1],
                        "start_str": parts[2],
                        "description": parts[3] if len(parts) > 3 else ""
                    })
            return parsed_events
            
        except Exception as e:
            print(f"[CalendarManager] Failed to fetch events: {e}")
            return []

    def _process_event(self, event: Dict[str, Any]):
        summary = event["summary"].lower()
        uid = event["uid"]
        
        # 1. Filter for Call-related events
        is_call = any(kw in summary for kw in CALENDAR_KEYWORDS)
        if not is_call:
            return
            
        # 2. Prevent duplicate processing
        if uid in self._processed_event_ids:
            return
            
        # 3. Check for specific instructions in description
        instructions = event["description"] or f"Autonomous call handling for {event['summary']}"
        
        # 4. Detect approximate start time
        # Note: Parsing AppleScript dates is locale-dependent, but we'll try a common one
        # "Tuesday, March 31, 2026 at 7:50:00 AM"
        
        # 5. Extract Caller Name from summary (e.g., "Call with Amazon" -> "Amazon")
        caller_name = event["summary"]
        if "with " in summary:
            caller_name = event["summary"].split("with ")[1]
        elif "call " in summary:
            caller_name = event["summary"].split("call ")[1]
            
        # 6. Add to Receptionist immediately
        receptionist.add_directive(caller_name, instructions)
        print(f"{GREEN}[CalendarManager] Added auto-directive for: {caller_name}{RESET}")
        
        # 7. Logic for "Starting Soon" Reminder (Visual & Audible)
        # We broadcast this to the frontend via the backend_api
        try:
            from backend_api import safety_manager # Reuse safety_manager for broadcasts
            import asyncio
            
            # Audible reminder
            tts.speak(f"Qadirdad, I've detected a scheduled call with {caller_name} in your calendar. I'm preparing to handle it.")
            
            # Visual broadcast
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    safety_manager.broadcast({
                        "type": "CALENDAR_REMINDER",
                        "caller": caller_name,
                        "time": event["start_str"],
                        "instructions": instructions
                    }),
                    loop
                )
        except Exception as e:
            print(f"[CalendarManager] Failed to broadcast reminder: {e}")

        self._processed_event_ids.add(uid)

# Global instance
calendar_manager = CalendarManager()
