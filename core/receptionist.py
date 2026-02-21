"""
Receptionist Module - Handles incoming GSM calls and expected directives.
"""
from typing import Dict, Any
import requests
import time
from config import OLLAMA_URL, RESPONDER_MODEL
from core.tts import tts

class Receptionist:
    def __init__(self):
        # Dictionary mapping caller_name or phone number to specific instructions
        self.expected_calls: Dict[str, str] = {}
        # Transcripts of calls processed
        self.call_logs = []

    def add_directive(self, caller_name: str, instructions: str) -> Dict[str, Any]:
        """Save a directive for an expected caller."""
        caller_key = caller_name.strip().lower()
        self.expected_calls[caller_key] = instructions
        
        message = f"Directive saved: I will handle the call from {caller_name}. Instructions: {instructions}"
        print(f"[Receptionist] {message}")
        
        return {
            "success": True,
            "message": message,
            "data": {"caller": caller_name, "instructions": instructions}
        }

    def handle_incoming_call(self, caller_id: str, mock_caller_speech: str = None, mock_user_response: str = None):
        """Called by GSM Gateway when a call comes in."""
        print(f"[Receptionist] Incoming call from {caller_id}")
        
        # Check if we have a directive that matches this caller
        # For a full implementation, this should fuzzy match or use a contacts database.
        # For now, we do a simple substring match on keys.
        
        matched_instructions = None
        matched_caller = "Unknown"
        
        for key, instr in self.expected_calls.items():
            if key in caller_id.lower() or caller_id.lower() in key:
                matched_instructions = instr
                matched_caller = key
                break
                
        if matched_instructions:
            print(f"[Receptionist] Found directive for {matched_caller}: {matched_instructions}")
            # Step 1: Answer Call (via gsm_gateway)
            from core.gsm_gateway import gsm_gateway
            from core.audio_bridge import audio_bridge
            
            gsm_gateway.answer_call()
            audio_bridge.link_call()
            
            # Step 2: Generate greeting based on instructions
            prompt = f"You are Wolf AI, a phone assistant. You just answered a call from {matched_caller}. Your instructions from the boss are: {matched_instructions}. Keep your response to a single short sentence to start the conversation."
            
            greeting = self._generate_response(prompt)
            print(f"[Receptionist] Saying: {greeting}")
            
            # Step 3: Speak greeting via TTS
            tts.toggle(True)
            tts.queue_sentence(greeting)
            
            # Step 4: Simulate STT Listening
            print("[Receptionist] Listening to caller... (STT pipeline placeholder)")
            # In full dev mode, here is where RealTimeSTT listens via linked bridge.
            
            # Let's mock the caller's response
            caller_speech = mock_caller_speech if mock_caller_speech else "(silence)"
            print(f"[Caller]: {caller_speech}")
            
            transcript_log = f"Wolf: {greeting}\nCaller: {caller_speech}"
            
            if "talk to qadirdad" in caller_speech.lower() or "speak to qadirdad" in caller_speech.lower():
                print("[Receptionist] Intent detected: Handover to Boss.")
                handover_msg = "Please hold for a moment, I am putting Qadirdad on the line."
                print(f"[Receptionist] Saying: {handover_msg}")
                tts.queue_sentence(handover_msg)
                
                # Wait for TTS to finish (mocked by sleep)
                time.sleep(2)
                
                audio_bridge.hold_call()
                audio_bridge.announce_to_user(f"Qadirdad, {matched_caller} wants to talk to you.")
                
                # Mock user interaction in console for demonstration
                # In full GUI, this would be a prompt on the HUD or verbal wake word command
                print("[Proactive Layer] Waiting for user approval... (Type 'ok' or 'no' in terminal)")
                
                # Use a background thread or a short wait to simulate user input if running headless
                if mock_user_response is not None:
                    user_response = mock_user_response.lower()
                    print(f"Qadirdad's response (ok/no): {user_response}")
                else:
                    user_response = input("Qadirdad's response (ok/no): ").strip().lower()
                
                if user_response == 'ok':
                    audio_bridge.handover_to_user()
                    transcript_log += f"\n[Handover accepted by user. Agent sleeping.]"
                    print("[Receptionist] Call handed over. Exiting AI loop.")
                    
                    # We leave the call active. The user hangs up mechanically.
                else:
                    audio_bridge.link_call() # Un-hold
                    rejection_msg = "I'm sorry, he is currently unavailable. I will let him know you called."
                    print(f"[Receptionist] Saying: {rejection_msg}")
                    tts.queue_sentence(rejection_msg)
                    time.sleep(2)
                    gsm_gateway.hangup_call()
                    audio_bridge.sever_call()
                    transcript_log += f"\nWolf: {rejection_msg}\n[Call Terminated]"
            else:
                # No handover needed
                time.sleep(2) 
                # Step 5: Hangup and unbridge
                print("[Receptionist] Call ended.")
                gsm_gateway.hangup_call()
                audio_bridge.sever_call()

            # Step 6: Log transcript
            log_entry = {
                "caller": matched_caller,
                "instructions": matched_instructions,
                "transcript": transcript_log,
                "status": "Completed" if not ("talk to qadirdad" in caller_speech.lower() and user_response == 'ok') else "Handed Over"
            }
            self.call_logs.append(log_entry)
            
            # Remove directive after processing
            del self.expected_calls[matched_caller]

    def _generate_response(self, prompt: str) -> str:
        """Call Ollama locally to generate the dialogue."""
        try:
            response = requests.post(f"{OLLAMA_URL}/generate", json={
                "model": RESPONDER_MODEL,
                "prompt": prompt,
                "stream": False
            }, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            else:
                return "Hello. My systems are currently offline."
        except Exception as e:
            print(f"[Receptionist] LLM Error: {e}")
            return "Hello. Let me note that down."

# Singleton instance
receptionist = Receptionist()
