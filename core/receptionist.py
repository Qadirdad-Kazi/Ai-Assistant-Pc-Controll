"""
Receptionist Module - Handles incoming GSM calls and expected directives.
"""
from typing import Dict, Any, Optional
import requests  
import json
import time
import datetime
from config import OLLAMA_URL, RESPONDER_MODEL  
from core.tts import tts  
from core.database import db  
from backend_api import sync_request_confirmation

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

    def handle_incoming_call(self, caller_id: str, mock_caller_speech: Optional[str] = None, mock_user_response: Optional[str] = None):
        """Called by GSM Gateway when a call comes in."""
        print(f"[Receptionist] Incoming call from {caller_id}")
        
        try:
            from backend_api import system_status
            system_status["Call Status"] = "RINGING"
        except ImportError:
            system_status = None
            
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
            
            if system_status:
                system_status["Call Status"] = f"ACTIVE ({matched_caller})"
            
            gsm_gateway.answer_call()
            audio_bridge.link_call()
            
            # Step 2: Generate greeting based on instructions
            prompt = f"You are Wolf AI, a phone assistant. You just answered a call from {matched_caller}. Your instructions from the boss are: {matched_instructions}. Keep your response to a single short sentence to start the conversation."
            
            greeting = self._generate_response(prompt)
            print(f"[Receptionist] Saying: {greeting}")
            
            # Step 3: Speak greeting via TTS
            tts.toggle(True)
            tts.queue_sentence(greeting)
            
            # Step 4: Real-Time Interaction Loop
            print("[Receptionist] Monitoring call audio...")
            from core.voice_assistant import voice_assistant
            stt = voice_assistant.stt_listener
            
            transcript_log = ""
            
            # Use a slightly longer timeout for phone responses
            call_timeout = 300 # 5 minutes max
            start_time = time.time()
            
            # Initial Greeting already done. Now listen for caller.
            while time.time() - start_time < call_timeout:
                if not gsm_gateway.is_connected:
                    break
                
                # Listen for speech from the caller
                caller_speech = stt.recorder.text() if stt and stt.recorder else "(silence)"
                if not caller_speech or caller_speech.strip() == "":
                    time.sleep(0.5)
                    continue
                
                print(f"[Caller]: {caller_speech}")
                transcript_log += f"Caller: {caller_speech}\n"
                
                # Check for Handover Intent
                if any(phrase in caller_speech.lower() for phrase in ["talk to", "speak to", "with qadirdad", "boss"]):
                    print("[Receptionist] Handover requested.")
                    tts.queue_sentence("One moment please, I'll see if he's available.")
                    
                    audio_bridge.hold_call()
                    audio_bridge.announce_to_user(f"{matched_caller} is asking to speak with you on the GSM line.")
                    
                    # USE SAFETY BRIDGE INSTEAD OF TERMINAL INPUT
                    approved = sync_request_confirmation(
                        action=f"Incoming Call Handover: {matched_caller}",
                        details=f"Caller said: '{caller_speech}'\nDo you want to take over the call?"
                    )
                    
                    if approved:
                        if system_status: system_status["Call Status"] = "USER ACTIVE"
                        audio_bridge.handover_to_user()
                        transcript_log += "[Call Handed Over to User]\n"
                        # Exit loop, call is active but AI is disengaged
                        return
                    else:
                        audio_bridge.link_call() # Return audio to AI
                        if system_status: system_status["Call Status"] = f"ACTIVE ({matched_caller})"
                        reject = "I'm sorry, he's unable to take the call right now. Can I take a message?"
                        tts.queue_sentence(reject)
                        transcript_log += f"Wolf: {reject}\n"
                else:
                    # Generate autonomous LLM response
                    prompt = f"Caller said: '{caller_speech}'. Your instructions: {matched_instructions}. Respond naturally as Wolf AI."
                    ai_reply = self._generate_response(prompt)
                    print(f"Wolf: {ai_reply}")
                    tts.queue_sentence(ai_reply)
                    transcript_log += f"Wolf: {ai_reply}\n"
                    
                # Check for hangup in next loop
                time.sleep(0.2)
            
            if system_status: system_status["Call Status"] = "IDLE"

            # Step 6: Log transcript
            log_entry = {
                "caller": matched_caller,
                "instructions": matched_instructions,
                "transcript": transcript_log,
                "status": "Completed" if not ("talk to qadirdad" in caller_speech.lower() and user_response == 'ok') else "Handed Over",  
                "timestamp": datetime.datetime.now().isoformat(timespec="seconds")
            }
            self.call_logs.append(log_entry)

            # Persist to sqlite so logs survive restarts and are available via backend APIs.
            try:
                call_id = db.log_call(
                    caller_id=matched_caller,
                    status=log_entry["status"],
                    intent=matched_instructions,
                    transcript=transcript_log,
                )
                
                # TRIGGER PRODUCTIVITY SUITE
                # Run in a background thread to avoid blocking the caller's disconnection
                from core.productivity_suite import productivity_suite
                import threading
                threading.Thread(
                    target=productivity_suite.process_call_outcome, 
                    args=(call_id, matched_caller, transcript_log), 
                    daemon=True
                ).start()
                
            except Exception as e:
                print(f"[Receptionist] Failed to persist call log or trigger productivity: {e}")
            
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
