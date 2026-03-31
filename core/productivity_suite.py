"""
Productivity Suite - Automates post-call actions:
- Sentiment Analysis (LLM)
- Email Follow-ups (AppleScript/Mail.app)
- Document Generation (Proposals/Contracts)
- Task Creation (Trello/Notion Mock)
"""
import os
import subprocess
import json
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from config import OLLAMA_URL, RESPONDER_MODEL, CYAN, RESET, GREEN, YELLOW
from core.database import db

class ProductivitySuite:
    def __init__(self):
        self.doc_dir = Path("data/documents/proposals")
        self.doc_dir.mkdir(parents=True, exist_ok=True)

    def process_call_outcome(self, call_id: int, caller: str, transcript: str):
        """Orchestrate the post-call productivity flow."""
        print(f"{CYAN}[Productivity] Processing outcome for call {call_id} (+{caller})...{RESET}")
        
        # 1. Sentiment Analysis
        sentiment_data = self.analyze_sentiment(transcript)
        
        # 2. Document Generation
        doc_path = self.generate_call_document(caller, transcript, sentiment_data)
        
        # 3. Task Creation
        self.create_automated_tasks(call_id, caller, transcript, sentiment_data)
        
        # 4. Email Drafting
        self.draft_follow_up_email(caller, transcript, sentiment_data)
        
        # 5. Update Database with sentiment results
        try:
            # We need to update the existing log entry
            import sqlite3
            with sqlite3.connect(db.db_path) as conn:
                conn.execute(
                    "UPDATE call_logs SET sentiment_score = ?, client_mood = ?, estimated_deal_size = ?, document_path = ? WHERE id = ?",
                    (sentiment_data['score'], sentiment_data['mood'], sentiment_data.get('deal_size', 0.0), str(doc_path), call_id)
                )
                conn.commit()
            print(f"{GREEN}[Productivity] Call {call_id} enriched. Deal Size: ${sentiment_data.get('deal_size', 0.0)}{RESET}")
        except Exception as e:
            print(f"{YELLOW}[Productivity] Failed to update call log: {e}{RESET}")

        # 6. Automated Scheduling
        if sentiment_data['mood'] == 'Frustrated' or 'callback' in transcript.lower():
            self.schedule_callback(caller, sentiment_data)

    def analyze_sentiment(self, transcript: str) -> Dict[str, Any]:
        """Use local LLM to gauge mood and urgency."""
        prompt = f"""
        Analyze this phone call transcript and return a JSON object with:
        1. 'mood': (Positive, Neutral, Negative, or Frustrated)
        2. 'score': (1 to 10, where 10 is very positive)
        3. 'deal_size': (Estimated monetary value in USD, extract numbers only. 0.0 if not found)
        4. 'summary': (One sentence summary)
        5. 'next_steps': (List of 2-3 specific action items)
        
        Transcript:
        {transcript}
        """
        
        try:
            response = requests.post(
                f"{OLLAMA_URL}/generate",
                json={
                    "model": RESPONDER_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            if response.status_code == 200:
                data = json.loads(response.json().get("response", "{}"))
                return {
                    "mood": data.get("mood", "Neutral"),
                    "score": data.get("score", 5),
                    "deal_size": data.get("deal_size", 0.0),
                    "summary": data.get("summary", "Call completed."),
                    "next_steps": data.get("next_steps", ["Follow up with client"])
                }
        except Exception as e:
            print(f"[Productivity] Sentiment Error: {e}")
            
        return {"mood": "Neutral", "score": 5, "summary": "Call completed.", "next_steps": ["Follow up"]}

    def generate_call_document(self, caller: str, transcript: str, sentiment: Dict[str, Any]) -> Path:
        """Create a professional Markdown proposal/summary."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        file_name = f"Proposal_{caller}_{timestamp}.md"
        file_path = self.doc_dir / file_name
        
        content = f"""# Call Summary & Proposal: {caller}
**Date:** {datetime.datetime.now().strftime("%B %d, %Y")}
**Client Mood:** {sentiment['mood']} ({sentiment['score']}/10)

## Executive Summary
{sentiment['summary']}

## Proposed Next Steps
"""
        for step in sentiment['next_steps']:
            content += f"- [ ] {step}\n"
            
        content += f"\n## Full Transcript Reference\n\n{transcript}\n"
        
        with open(file_path, "w") as f:
            f.write(content)
            
        return file_path

    def create_automated_tasks(self, call_id: int, caller: str, transcript: str, sentiment: Dict[str, Any]):
        """Populate the local task manager."""
        for step in sentiment['next_steps']:
            priority = "High" if sentiment['score'] < 4 else "Medium"
            db.add_task(
                title=f"{step} ({caller})",
                description=f"Action item generated from call {call_id}.",
                priority=priority,
                related_call_id=call_id
            )

    def draft_follow_up_email(self, caller: str, transcript: str, sentiment: Dict[str, Any]):
        """Draft a follow-up via macOS Mail.app."""
        subject = f"Follow-up: Our conversation today ({caller})"
        body = f"Hi {caller},\n\nThank you for speaking with us today. Following up on our discussion:\n\n"
        for step in sentiment['next_steps']:
            body += f"- {step}\n"
        body += "\nBest regards,\nQadirdad & Wolf AI"
        
        # Escaping quotes for AppleScript
        safe_body = body.replace('"', '\\"')
        safe_subject = subject.replace('"', '\\"')
        
        applescript = f'''
        tell application "Mail"
            set newMessage to make new outgoing message with properties {{subject:"{safe_subject}", content:"{safe_body}", visible:true}}
            activate
        end tell
        '''
        
        try:
            subprocess.run(['osascript', '-e', applescript], check=True)
            print(f"[Productivity] Email draft created for {caller}")
        except Exception as e:
            print(f"[Productivity] Failed to draft email: {e}")

    def schedule_callback(self, caller: str, sentiment: Dict[str, Any]):
        """Integration with macOS Calendar for follow-up scheduling."""
        try:
            from core.calendar_manager import calendar_manager
            # Create a mock directive for the manager to handle
            print(f"{CYAN}[Productivity] Automatically scheduling follow-up for {caller}...{RESET}")
            
            # Use AppleScript to add an event for tomorrow at 10 AM
            script = f'''
            set tomorrow to (current date) + 86400
            set time of tomorrow to (10 * 3600)
            tell application "Calendar"
                tell calendar "Work"
                    make new event with properties {{summary:"Follow up with {caller} (Wolf AI)", start date:tomorrow, description:"Automatic follow-up for {sentiment['summary']}"}}
                end tell
            end tell
            '''
            subprocess.run(['osascript', '-e', script])
            
        except Exception as e:
            print(f"[Productivity] Failed to schedule callback: {e}")

# Global instance
productivity_suite = ProductivitySuite()
