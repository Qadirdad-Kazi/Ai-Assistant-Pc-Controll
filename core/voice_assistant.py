"""
Voice Assistant - Main orchestrator for Alexa-like voice interaction.
Manages: STT → Function Gemma → Qwen → TTS pipeline.
"""

import threading
import json
import requests
from typing import Optional
from PySide6.QtCore import QObject, Signal

from config import (
    RESPONDER_MODEL, OLLAMA_URL, MAX_HISTORY, GRAY, RESET, CYAN, GREEN, WAKE_WORD, YELLOW
)
from core.stt import STTListener
from core.llm import route_query, should_bypass_router, http_session
from core.model_persistence import ensure_llama_loaded, mark_llama_used, unload_llama
from core.tts import tts, SentenceBuffer
from core.function_executor import executor as function_executor
from core.reasoning import reasoning_engine
from core.self_reflection import self_reflection_engine
from core.memory import memory_manager
from core.multi_model import multi_model_reasoner
from core.uncertainty import quantify_and_disclose_uncertainty, uncertainty_analyzer

# Functions that are actions (not passthrough)
ACTION_FUNCTIONS = {
    "control_light", "set_timer", "set_alarm", 
    "create_calendar_event", "add_task", "web_search", "pc_control",
    "play_music", "scaffold_website", "set_call_directive", "visual_agent",
    "create_task", "list_tasks", "execute_task"
}


class VoiceAssistant(QObject):
    """Main voice assistant orchestrator."""
    
    # Signals for UI updates (optional)
    wake_word_detected = Signal()
    speech_recognized = Signal(str)
    processing_started = Signal()
    processing_finished = Signal()
    error_occurred = Signal(str)
    # GUI update signals
    timer_set = Signal(int, str)  # seconds, label
    alarm_added = Signal()
    calendar_updated = Signal()
    task_added = Signal()
    
    def __init__(self):
        super().__init__()
        self.stt_listener: Optional[STTListener] = None
        self.running = False
        self.messages = [
            {
                'role': 'system', 
                'content': 'You are a helpful assistant. Respond in short, complete sentences. Never use emojis or special characters. Keep responses concise and conversational.'
            }
        ]
        self.current_session_id = None
        self.current_stop_event = None
        self.current_user_prompt = ""
        self.current_stream = ""
        
    def initialize(self) -> bool:
        """Initialize voice assistant components."""
        try:
            print(f"{CYAN}[VoiceAssistant] Initializing voice assistant components...{RESET}")
            # Initialize STT listener
            print(f"{CYAN}[VoiceAssistant] Creating STT listener...{RESET}")
            self.stt_listener = STTListener(
                wake_word_callback=self._on_wake_word,
                speech_callback=self._on_speech,
                stop_callback=self._on_stop
            )
            print(f"{CYAN}[VoiceAssistant] ✓ STT listener created{RESET}")
            
            print(f"{CYAN}[VoiceAssistant] Initializing STT models...{RESET}")
            if not self.stt_listener.initialize():
                print(f"{GRAY}[VoiceAssistant] ✗ Failed to initialize STT.{RESET}")
                return False
            print(f"{CYAN}[VoiceAssistant] ✓ STT initialized{RESET}")
            
            # Ensure TTS is initialized
            if not tts.piper_exe:
                print(f"{CYAN}[VoiceAssistant] Initializing TTS...{RESET}")
                tts.initialize()
                print(f"{CYAN}[VoiceAssistant] ✓ TTS initialized{RESET}")
            
            print(f"{CYAN}[VoiceAssistant] ✓ Voice assistant initialized successfully{RESET}")
            return True
        except Exception as e:
            print(f"{GRAY}[VoiceAssistant] ✗ Initialization error: {e}{RESET}")
            import traceback
            traceback.print_exc()
            return False
    
    def start(self):
        """Start the voice assistant."""
        if self.running:
            return
        
        if not self.stt_listener:
            if not self.initialize():
                return
        
        self.running = True
        self.stt_listener.start()
        print(f"{CYAN}[VoiceAssistant] Voice assistant started. Say '{GREEN}{WAKE_WORD}{RESET}{CYAN}' to activate.{RESET}")
    
    def stop(self):
        """Stop the voice assistant."""
        if not self.running:
            return
        
        self.running = False
        if self.stt_listener:
            self.stt_listener.stop()
        print(f"{GRAY}[VoiceAssistant] Voice assistant stopped.{RESET}")
    
    def _on_stop(self):
        """Handle 'stop' voice command — interrupt TTS immediately."""
        print(f"{YELLOW}[VoiceAssistant] 🛑 Stop command received! Interrupting TTS and LLM.{RESET}")
        if self.current_stop_event:
            self.current_stop_event.set()
        tts.stop()
    
    def _on_wake_word(self):
        """Handle wake word detection."""
        print(f"{GREEN}[VoiceAssistant] ✓ Wake word callback received!{RESET}")
        print(f"{GREEN}[VoiceAssistant] Emitting wake_word_detected signal...{RESET}")
        self.wake_word_detected.emit()
        print(f"{GREEN}[VoiceAssistant] ✓ Signal emitted. Listening for speech...{RESET}")

    def _on_speech(self, text: str):
        """Handle recognized speech. STT already stripped the wake word."""
        if not text.strip():
            return

        self.speech_recognized.emit(text)
        self.processing_started.emit()
        print(f"{CYAN}[VoiceAssistant] Processing: {text}{RESET}")

        # Interrupt any ongoing TTS before processing the new query
        if self.current_stop_event:
            self.current_stop_event.set()
        tts.stop()

        self.current_user_prompt = text
        self.current_stream = ""

        local_stop = threading.Event()
        self.current_stop_event = local_stop

        thread = threading.Thread(target=self._process_query, args=(text, local_stop), daemon=True)
        thread.start()
    
    def _process_query(self, user_text: str, stop_event: threading.Event):
        """Process user query through the pipeline with Chain-of-Thought reasoning."""
        try:
            # Step 0: Chain-of-Thought Reasoning - Think before routing
            print(f"{CYAN}[VoiceAssistant] Engaging chain-of-thought reasoning...{RESET}")
            reasoning_result = reasoning_engine.think_step_by_step(user_text)
            thinking_context = reasoning_result.get("thinking", {}).get("raw_thinking", "")
            reasoning_steps = reasoning_result.get("steps", [])
            
            print(f"{CYAN}[VoiceAssistant] Reasoning context: {len(reasoning_steps)} steps identified{RESET}")
            
            # Step 1: Route through Function Gemma (with reasoning context)
            if should_bypass_router(user_text):
                calls = [("nonthinking", {"prompt": user_text})]
            else:
                calls = route_query(user_text)
            
            print(f"{GRAY}[VoiceAssistant] Routed to: {[c[0] for c in calls]}{RESET}")
            
            # Step 2: Handle based on function type. 
            # Iterate through all detected functions.
            for i, (func_name, params) in enumerate(calls):
                if stop_event.is_set(): break
                
                # If there are multiple actions, only the LAST action generates a verbal response,
                # unless a prior action failed.
                is_last_action = i == len(calls) - 1
                
                if func_name in ACTION_FUNCTIONS:
                    # Execute action function
                    result = function_executor.execute(func_name, params)
                    response_text = result.get("message", "Done.")
                    print(f"[Function Result] {response_text}")
                    
                    # Verify result using reasoning
                    evaluation = reasoning_engine.reason_about_result(
                        user_text, 
                        f"{func_name}({params})", 
                        result,
                        thinking_context
                    )
                    result_confidence = evaluation.get("confidence", 5)
                    result_complete = evaluation.get("is_complete", True)
                    
                    print(f"{CYAN}[Verification] Confidence: {result_confidence}/10, Complete: {result_complete}{RESET}")
                    
                    # Emit GUI update signals for specific actions
                    if func_name == "set_timer" and result.get("success"):
                        seconds = result.get("data", {}).get("seconds", 0)
                        label = result.get("data", {}).get("label", "Timer")
                        self.timer_set.emit(seconds, label)
                    elif func_name == "set_alarm" and result.get("success"):
                        self.alarm_added.emit()
                    elif func_name == "create_calendar_event" and result.get("success"):
                        self.calendar_updated.emit()
                    elif func_name == "add_task" and result.get("success"):
                        self.task_added.emit()
                    
                    failed_action = not result.get("success", False)
                    
                    if is_last_action or failed_action:
                        self._generate_response_with_context(func_name, result, user_text, stop_event, enable_thinking=failed_action)
                    
                    # For successful PC control actions, also ensure conversation mode is activated
                    if func_name == "pc_control" and not failed_action:
                        if self.stt_listener:
                            self.stt_listener.enter_conversation_mode()
                    
                    if failed_action:
                        break # Stop pipeline if an action fails
                        
                elif func_name == "visual_agent":
                    # Handle visual tasks specifically (so the AI announces what it's doing)
                    tts.speak("Looking at your screen right now...")
                    result = function_executor.execute(func_name, params)
                    if is_last_action or not result.get("success", False):
                        self._generate_response_with_context(func_name, result, user_text, stop_event, enable_thinking=False)
                    
                elif func_name == "get_system_info":
                    # Get system info
                    result = function_executor.execute(func_name, params)
                    if is_last_action:
                        self._generate_response_with_context(func_name, result, user_text, stop_event, enable_thinking=True)
                    
                elif func_name in ("thinking", "nonthinking"):
                    # Direct Qwen passthrough
                    if is_last_action:
                        enable_thinking = (func_name == "thinking")
                        self._stream_qwen_response(user_text, stop_event, enable_thinking)
                
                else:
                    # Fallback to nonthinking
                    if is_last_action:
                        self._stream_qwen_response(user_text, stop_event, False)
                
        except Exception as e:
            error_msg = f"Error processing query: {e}"
            print(f"{GRAY}[VoiceAssistant] {error_msg}{RESET}")
            self.error_occurred.emit(error_msg)
            self.processing_finished.emit()
    
    def _generate_response_with_context(self, func_name: str, result: dict, user_text: str, stop_event: threading.Event, enable_thinking: bool = False):
        """Generate Llama response with function execution context."""
        try:
            # Ensure Llama is loaded
            if not ensure_llama_loaded():
                print(f"{GRAY}[VoiceAssistant] Failed to load Llama model.{RESET}")
                self.processing_finished.emit()
                return
            
            mark_llama_used()
            
            # Build context message
            success = result.get("success", False)
            message = result.get("message", "")
            
            # Enhanced context for get_system_info
            if func_name == "get_system_info" and success:
                data = result.get("data", {})
                context_parts = []
                if data.get("timers"):
                    context_parts.append(f"Active timers: {data['timers']}")
                if data.get("alarms"):
                    context_parts.append(f"Alarms: {data['alarms']}")
                if data.get("calendar_today"):
                    context_parts.append(f"Today's events: {data['calendar_today']}")
                if data.get("tasks"):
                    pending = [t for t in data['tasks'] if not t.get('completed')]
                    context_parts.append(f"Pending tasks: {len(pending)} items")
                if data.get("smart_devices"):
                    on_devices = [d['name'] for d in data['smart_devices'] if d.get('is_on')]
                    context_parts.append(f"Devices on: {on_devices if on_devices else 'none'}")
                if data.get("weather"):
                    w = data['weather']
                    context_parts.append(f"Weather: {w.get('temp')}°F, {w.get('condition')}")
                if data.get("news"):
                    news_items = data['news']
                    if news_items:
                        news_titles = [item.get('title', '')[:50] for item in news_items[:3]]
                        context_parts.append(f"Top news: {', '.join(news_titles)}")
                context_msg = "SYSTEM CONTEXT:\n" + "\n".join(context_parts) if context_parts else "No system information available."
            elif func_name == "visual_agent":
                context_msg = f"Visual Agent Task executed. Success: {success}. Result/Thought: {message}"
            else:
                context_msg = f"Function {func_name} executed. Success: {success}. Result: {message}. If success is False or the app was missing, you must ask the user a follow-up question (e.g. asking if they want help downloading it)."
            
            # Manage context window
            max_hist = MAX_HISTORY
            if len(self.messages) > max_hist:
                self.messages = [self.messages[0]] + self.messages[-(max_hist-1):]
            
            # Add context as user message
            context_prompt = f"{context_msg}\n\nUser asked: {user_text}\n\nRespond naturally and concisely."
            self.messages.append({'role': 'user', 'content': context_prompt})
            
            # Prepare payload
            payload = {
                "model": RESPONDER_MODEL,
                "messages": self.messages,
                "stream": True,
                "think": enable_thinking,
                "keep_alive": "5m"
            }
            
            sentence_buffer = SentenceBuffer()
            full_response = ""
            
            # Stream response
            with http_session.post(f"{OLLAMA_URL}/chat", json=payload, stream=True, timeout=60) as r:
                r.raise_for_status()
                
                for line in r.iter_lines():
                    if stop_event.is_set():
                        break
                    
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            msg = chunk.get('message', {})
                            
                            if 'content' in msg and msg['content']:
                                content = msg['content']
                                full_response += content
                                self.current_stream = full_response
                                
                                # Queue for TTS
                                sentences = sentence_buffer.add(content)
                                for s in sentences:
                                    tts.queue_sentence(s)
                        except:
                            continue
            
            # Flush remaining
            if not stop_event.is_set():
                rem = sentence_buffer.flush()
                if rem:
                    tts.queue_sentence(rem)
            
            # Self-Reflection: Verify response quality before finalizing
            print(f"{CYAN}[VoiceAssistant] Applying self-reflection to verify response...{RESET}")
            quality_report = self_reflection_engine.rate_response_quality(
                full_response, 
                user_text, 
                context=func_name
            )
            
            quality_level = quality_report.get("quality_level", "Medium")
            overall_score = quality_report.get("overall_score", 5)
            
            if overall_score < 6:
                # Low quality - attempt correction
                print(f"{YELLOW}[VoiceAssistant] Low quality response detected (score: {overall_score:.1f}), attempting correction...{RESET}")
                correction = self_reflection_engine.self_correct(
                    user_text,
                    full_response,
                    ["Low quality response"],
                    func_name
                )
                
                if correction.get("success"):
                    corrected = correction.get("corrected_response", full_response)
                    print(f"{GREEN}[VoiceAssistant] Response corrected.{RESET}")
                    full_response = corrected
            else:
                print(f"{GREEN}[VoiceAssistant] Response quality verified (score: {overall_score:.1f}, level: {quality_level}){RESET}")
            
            # Uncertainty Quantification: Analyze confidence in response
            print(f"{CYAN}[VoiceAssistant] Analyzing uncertainty in response...{RESET}")
            uncertainty_result = quantify_and_disclose_uncertainty(full_response)
            confidence_disclosure = uncertainty_result.get("confidence_disclosure", "")
            confidence_score = uncertainty_result["uncertainty_data"]["confidence_score"]
            
            print(f"{CYAN}[UncertaintyAnalyzer] Confidence: {confidence_score}% - {uncertainty_result['uncertainty_data']['confidence_level'].upper()}{RESET}")
            
            # If confidence is low, consider what to add
            if confidence_score < 50:
                print(f"{YELLOW}[VoiceAssistant] Low confidence detected, including uncertainty disclosure${RESET}")
                full_response = uncertainty_result.get("adjusted_response", full_response)
            
            # Update messages
            self.messages.append({'role': 'assistant', 'content': full_response})
            self.current_user_prompt = ""
            self.current_stream = ""
            
            # Log interaction to memory
            memory_manager.log_interaction(
                user_input=user_text,
                ai_response=full_response,
                interaction_type=func_name,
                metadata={
                    "quality_score": overall_score,
                    "quality_level": quality_level,
                    "reasoning_steps": reasoning_steps,
                    "verification_confidence": result_confidence,
                    "response_confidence": confidence_score,
                    "confidence_level": uncertainty_result["uncertainty_data"]["confidence_level"],
                    "uncertainty_indicators": uncertainty_result["uncertainty_data"]["uncertainty_indicators"]
                }
            )
            
            # Log reasoning for future reference
            memory_manager.log_reasoning(
                query=user_text,
                reasoning_steps=reasoning_steps,
                action_taken=func_name,
                result={"message": result.get("message", ""), "success": result.get("success", False)},
                confidence=result_confidence
            )
            
            mark_llama_used()  # Update usage time
            
            print(f"{GREEN}[VoiceAssistant] Response generated and logged to memory.{RESET}")
            self.processing_finished.emit()
            # Keep mic open for follow-up without re-saying the wake word
            if self.stt_listener:
                self.stt_listener.enter_conversation_mode()
            
        except Exception as e:
            print(f"{GRAY}[VoiceAssistant] Error generating response: {e}{RESET}")
            self.processing_finished.emit()
    
    def _stream_qwen_response(self, user_text: str, stop_event: threading.Event, enable_thinking: bool):
        """Stream direct Llama response with intelligent model selection."""
        try:
            # Ensure Llama is loaded
            if not ensure_llama_loaded():
                print(f"{GRAY}[VoiceAssistant] Failed to load Llama model.{RESET}")
                self.processing_finished.emit()
                return
            
            mark_llama_used()
            
            # Multi-Model: Select optimal model for this query
            model_selection = multi_model_reasoner.adaptive_model_selection(user_text)
            selected_model = model_selection.get("model", RESPONDER_MODEL)
            model_info = model_selection.get("model_info", {})
            
            print(f"{CYAN}[MultiModel] Using {selected_model} (Reasoning Depth: {model_info.get('reasoning_depth', 'unknown')}){RESET}")
            
            # Manage context window
            max_hist = MAX_HISTORY
            if len(self.messages) > max_hist:
                self.messages = [self.messages[0]] + self.messages[-(max_hist-1):]
            
            self.messages.append({'role': 'user', 'content': user_text})
            
            # Prepare payload with selected model
            payload = {
                "model": selected_model,
                "messages": self.messages,
                "stream": True,
                "think": enable_thinking,
                "keep_alive": "5m"
            }
            
            sentence_buffer = SentenceBuffer()
            full_response = ""
            
            # Define completion callback for TTS
            def on_tts_complete():
                print(f"{CYAN}[VoiceAssistant] TTS finished, activating conversation mode.{RESET}")
                if self.stt_listener:
                    self.stt_listener.enter_conversation_mode()
            
            # Set completion callback
            tts.set_completion_callback(on_tts_complete)
            
            # Stream response
            with http_session.post(f"{OLLAMA_URL}/chat", json=payload, stream=True, timeout=60) as r:
                r.raise_for_status()
                
                for line in r.iter_lines():
                    if stop_event.is_set():
                        break
                    
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            msg = chunk.get('message', {})
                            
                            if 'content' in msg and msg['content']:
                                content = msg['content']
                                full_response += content
                                
                                # Queue for TTS
                                sentences = sentence_buffer.add(content)
                                for s in sentences:
                                    tts.queue_sentence(s)
                        except:
                            continue
            
            # Flush remaining
            if not stop_event.is_set():
                rem = sentence_buffer.flush()
                if rem:
                    tts.queue_sentence(rem)
            
            # Update messages
            self.messages.append({'role': 'assistant', 'content': full_response})
            self.current_user_prompt = ""
            self.current_stream = ""
            
            mark_llama_used()  # Update usage time
            
            print(f"{GREEN}[VoiceAssistant] Response generated.{RESET}")
            self.processing_finished.emit()
            
            # Wait for TTS to complete before enabling conversation mode
            tts.wait_for_completion()
            
        except Exception as e:
            print(f"{GRAY}[VoiceAssistant] Error streaming response: {e}{RESET}")
            self.processing_finished.emit()


# Global voice assistant instance
voice_assistant = VoiceAssistant()
