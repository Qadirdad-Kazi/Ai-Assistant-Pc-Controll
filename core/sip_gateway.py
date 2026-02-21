"""
Local SIP Gateway Module
Allows Wolf AI to act as a softphone over Wi-Fi, intercepting calls from an Android SIP Server
without requiring physical GSM hardware.
"""

import threading
import time
from typing import Callable
from core.settings_store import settings

try:
    from pyvoip.SIP import SIPApp, CallState
except ImportError:
    SIPApp = None
    CallState = None

class SIPGateway:
    def __init__(self):
        self.sip_app = None
        self.running = False
        self._thread = None
        self.current_call = None
        
        # Callback for when a call is received
        self.on_incoming_call: Callable[[str], None] = None
        
    def start(self):
        """Initializes the SIP listener using settings from the GUI."""
        if not SIPApp:
            print("[SIP Gateway] pyvoip not found. SIP functionality disabled.")
            return
            
        if self.running:
            print("[SIP Gateway] Already running.")
            return

        sip_ip = settings.get("sip.ip", "0.0.0.0")
        sip_port = int(settings.get("sip.port", 5060))
        sip_user = settings.get("sip.username", "wolf")
        sip_pass = settings.get("sip.password", "password")
        
        try:
            # Initialize SIP application to listen for incoming connections
            # In a real deployed environment, this connects to the Android SIP Server
            self.sip_app = SIPApp(sip_ip, sip_port, sip_user, sip_pass)
            self.running = True
            
            print(f"[SIP Gateway] Started listening aggressively on {sip_ip}:{sip_port} (User: {sip_user})")
            
            # Start the background polling thread to handle call states
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()
            
        except Exception as e:
            print(f"[SIP Gateway] Failed to start: {e}")
            self.running = False

    def _poll_loop(self):
        """Background thread checking for incoming SIP packets."""
        while self.running and self.sip_app:
            try:
                # Check for calls in 'RINGING' state
                calls = self.sip_app.get_calls()
                for call in calls:
                    if call.state == CallState.RINGING and self.current_call is None:
                        self.current_call = call
                        caller_id = call.request.headers.get("From", "Unknown SIP Caller")
                        
                        # Clean up SIP caller URI formatting if needed
                        if "<sip:" in caller_id:
                            caller_id = caller_id.split("<sip:")[1].split("@")[0]
                            
                        print(f"[SIP Gateway] Incoming VoWIFI Call Detected from: {caller_id}")
                        
                        # Route to Receptionist logic
                        if self.on_incoming_call:
                            # Start a thread so we don't block the SIP poll loop
                            threading.Thread(target=self.on_incoming_call, args=(caller_id,), daemon=True).start()
                            
            except Exception as e:
                print(f"[SIP Gateway] Polling error: {e}")
                
            time.sleep(1) # Poll every second

    def answer_call(self):
        """Instructs the SIP protocol to pick up the ringing call."""
        if self.current_call and self.current_call.state == CallState.RINGING:
            print("[SIP Gateway] Answering call over Wi-Fi...")
            self.current_call.answer()
            
            # Here we would normally bind the pyvoip audio stream
            # to our audio_bridge for STT/TTS interaction.
            # self.current_call.read_audio() / write_audio()
        else:
            print("[SIP Gateway] No active call to answer.")

    def hangup_call(self):
        """Instructs the SIP protocol to sever the active connection."""
        if self.current_call:
            print("[SIP Gateway] Hanging up SIP connection...")
            try:
                self.current_call.hangup()
            except Exception as e:
                print(f"[SIP Gateway] Hangup error: {e}")
            finally:
                self.current_call = None
        else:
            print("[SIP Gateway] No active call to hang up.")

    def stop(self):
        """Shuts down the SIP listener socket."""
        self.running = False
        if self.sip_app:
            print("[SIP Gateway] Stopping SIP listener...")
            self.sip_app.stop()
            self.sip_app = None

# Singleton instance
sip_gateway = SIPGateway()
