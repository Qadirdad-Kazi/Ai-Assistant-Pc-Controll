"""
Voice Assistant - Main orchestrator for Alexa-like voice interaction.
Manages: STT → Function Gemma → Qwen → TTS pipeline.
"""

import threading
import json
import requests
import re
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
from core.emotional_intelligence import emotional_analyzer
from core.intuition import intuition_engine
from core.curiosity import curiosity_engine
from core.personalization import adaptive_personalizer
from core.attention import attention_manager
from core.personality import personality_system
from core.fatigue import energy_manager
from core.metacognition import metacognition_engine

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

    def _is_pc_capability_query(self, user_text: str) -> bool:
        """Detect capability checks that should get deterministic assistant grounding."""
        txt = user_text.lower().strip()
        asks_capability = bool(re.search(r"\b(can you|do you|are you able to|do u)\b", txt))
        mentions_pc = bool(re.search(r"\b(pc|computer|desktop|laptop|system)\b", txt))
        mentions_control = bool(re.search(r"\b(control|open|close|volume|shutdown|restart|lock|launch|manage)\b", txt))
        return asks_capability and (mentions_pc or mentions_control)
    
    def _process_query(self, user_text: str, stop_event: threading.Event):
        """Process user query through the pipeline with Chain-of-Thought reasoning and human-like thinking."""
        try:
            if self._is_pc_capability_query(user_text):
                capability_answer = (
                    "Yes. I can control your PC directly when you ask commands like "
                    "open apps, close apps, adjust volume, lock, shutdown, restart, "
                    "take screenshots, and basic media controls."
                )
                print(f"{CYAN}[VoiceAssistant] Capability query detected. Sending direct capability response...{RESET}")
                spoke_ok = False
                try:
                    spoke_ok = bool(tts.speak(capability_answer))
                except Exception as tts_err:
                    print(f"{YELLOW}[VoiceAssistant] Capability TTS fallback triggered: {tts_err}{RESET}")

                if not spoke_ok:
                    tts.queue_sentence(capability_answer)
                    tts.wait_for_completion()
                self.messages.append({'role': 'user', 'content': user_text})
                self.messages.append({'role': 'assistant', 'content': capability_answer})
                self.processing_finished.emit()
                if self.stt_listener:
                    self.stt_listener.enter_conversation_mode()
                return

            # Step 0a: EMOTIONAL INTELLIGENCE - Detect user emotion
            print(f"{CYAN}[VoiceAssistant] Analyzing user emotional state...{RESET}")
            emotion_analysis = emotional_analyzer.detect_user_emotion(user_text)
            detected_emotion = emotion_analysis.get("primary_emotion", "neutral")
            emotion_intensity = str(emotion_analysis.get("intensity", "medium"))
            print(f"{CYAN}[EmotionalIntelligence] Detected: {detected_emotion} (intensity: {emotion_intensity}){RESET}")
            
            # Step 0b: ATTENTION MANAGER - Check if can handle new task
            print(f"{CYAN}[VoiceAssistant] Assessing attention state...{RESET}")
            attention_result = attention_manager.process_query(user_text, task_id=f"query_{id(user_text)}", task_priority=5)
            can_process = attention_result.get("can_process", True)
            distraction_level = attention_result.get("distraction_level", 0)
            print(f"{CYAN}[AttentionManager] Can process: {can_process}, Distraction: {distraction_level:.2f}{RESET}")
            
            if not can_process:
                # Overwhelmed - suggest simpler task or break
                should_break, break_reason = attention_manager.should_take_break()
                if should_break:
                    tts.speak(f"I'm feeling overwhelmed right now. {break_reason} Let me take a moment.")
                    print(f"{YELLOW}[AttentionManager] {break_reason}{RESET}")
                    self.processing_finished.emit()
                    return
            
            # Step 0c: INTUITION ENGINE - Quick response for common patterns
            print(f"{CYAN}[VoiceAssistant] Checking intuition for instant response...{RESET}")
            intuition_response = intuition_engine.make_quick_decision(user_text)
            if intuition_response and intuition_response.get("should_respond_quickly"):
                quick_response = intuition_response.get("response", "")
                confidence = intuition_response.get("confidence", 0.5)
                if confidence > 0.75:
                    print(f"{GREEN}[IntuitiveEngine] Using intuitive response (confidence: {confidence:.2f}){RESET}")
                    # Consume minimal energy for quick response
                    energy_manager.consume_energy("simple_query", "simple")
                    tts.speak(quick_response)
                    self.messages.append({'role': 'user', 'content': user_text})
                    self.messages.append({'role': 'assistant', 'content': quick_response})
                    memory_manager.log_interaction(user_text, quick_response, "intuition_fast_response")
                    self.processing_finished.emit()
                    if self.stt_listener:
                        self.stt_listener.enter_conversation_mode()
                    return
            
            # Step 0d: ENERGY MANAGER - Track energy for this complex operation
            energy_cost = energy_manager.consume_energy("reasoning_step", "complex")
            print(f"{CYAN}[EnergyManager] Consumed {energy_cost:.1f} energy. Status: {energy_manager.get_energy_status()['degradation_level']}{RESET}")
            
            # Step 0e: Check if should refuse complex task due to fatigue
            refuse_complex, refuse_reason = energy_manager.should_refuse_complex_task()
            if refuse_complex:
                print(f"{YELLOW}[EnergyManager] {refuse_reason}{RESET}")
                tts.speak(refuse_reason)
                self.processing_finished.emit()
                return
            
            # Step 0f: Chain-of-Thought Reasoning - Think before routing
            print(f"{CYAN}[VoiceAssistant] Engaging chain-of-thought reasoning...{RESET}")
            reasoning_result = reasoning_engine.think_step_by_step(user_text)
            thinking_context = reasoning_result.get("thinking", {}).get("raw_thinking", "")
            reasoning_steps = reasoning_result.get("steps", [])
            
            print(f"{CYAN}[VoiceAssistant] Reasoning context: {len(reasoning_steps)} steps identified{RESET}")
            
            # Step 1: CURIOSITY MODULE - Detect ambiguities and generate clarifying questions
            print(f"{CYAN}[VoiceAssistant] Checking for ambiguous queries...{RESET}")
            ambiguities = curiosity_engine.identify_ambiguities(user_text)
            if ambiguities:
                print(f"{CYAN}[CuriosityEngine] Ambiguities detected: {ambiguities}{RESET}")
                clarifying_questions = curiosity_engine.generate_clarifying_questions(user_text, ambiguities)
                if clarifying_questions:
                    print(f"{CYAN}[CuriosityEngine] Generated clarifying questions: {clarifying_questions[:2]}{RESET}")
            
            # Step 2: Route through Function Gemma (with reasoning context)
            if should_bypass_router(user_text):
                calls = [("nonthinking", {"prompt": user_text})]
            else:
                calls = route_query(user_text)
            
            print(f"{GRAY}[VoiceAssistant] Routed to: {[c[0] for c in calls]}{RESET}")
            
            # Step 3: Handle based on function type. 
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
                    if is_last_action:
                        if func_name == "thinking":
                            # First try executable thinking (autonomous computer actions when prompt is actionable).
                            result = function_executor.execute(func_name, params)
                            result_type = result.get("data", {}).get("type", "") if isinstance(result, dict) else ""

                            if result_type in ("autonomous_execution", "enhanced_thinking"):
                                self._generate_response_with_context(func_name, result, user_text, stop_event, enable_thinking=False)
                            else:
                                self._stream_qwen_response(user_text, stop_event, True)
                        else:
                            # nonthinking remains direct conversational passthrough
                            self._stream_qwen_response(user_text, stop_event, False)
                
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
            
            # PERSONALITY SYSTEM: Apply personality traits to response
            print(f"{CYAN}[PersonalitySystem] Applying personality traits...{RESET}")
            full_response = personality_system.apply_all_trait_modifications(full_response)
            
            # PERSONALIZATION: Adapt response to user preferences and style
            print(f"{CYAN}[Personalization] Adapting response to user profile...{RESET}")
            user_id = "default_user"  # In production, would use actual user ID
            full_response = adaptive_personalizer.personalize_response(full_response, user_id)
            if hasattr(adaptive_personalizer, "adapt_communication_style"):
                full_response = adaptive_personalizer.adapt_communication_style(full_response, user_id)
            else:
                full_response = adaptive_personalizer.personalize_response(full_response, user_id)
            
            # EMOTIONAL INTELLIGENCE: Generate empathetic response envelope if needed
            if detected_emotion != "neutral":
                print(f"{CYAN}[EmotionalIntelligence] Adding empathetic response for {detected_emotion}...{RESET}")
                empathetic_response = emotional_analyzer.generate_empathetic_response(detected_emotion, emotion_intensity)
                if empathetic_response:
                    full_response = f"{empathetic_response}\n\n{full_response}"
            
            # METACOGNITION ENGINE: Add thinking-about-thinking to response
            print(f"{CYAN}[MetacognitionEngine] Adding metacognitive awareness...{RESET}")
            metacognitive_result = metacognition_engine.process_with_metacognition(
                query=user_text,
                response=full_response,
                reasoning_steps=reasoning_steps,
                confidence=confidence_score / 100.0  # Convert to 0-1 scale
            )
            full_response = metacognitive_result.get("final_response", full_response)
            has_warning = metacognitive_result.get("has_warning", False)
            warning_msg = metacognitive_result.get("warning_message", "")
            
            if has_warning:
                print(f"{YELLOW}[MetacognitionEngine] Warning issued: {warning_msg}{RESET}")
            
            # ENERGY MANAGER: Track energy recovery and fatigue effects
            energy_status = energy_manager.get_energy_status()
            if energy_status.get("should_take_break"):
                break_recommendation = energy_manager.get_estimated_break_needed()
                print(f"{YELLOW}[EnergyManager] Break needed: {break_recommendation}{RESET}")
            
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
            try:
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
                            except Exception:
                                continue
            except requests.HTTPError as chat_error:
                # Fallback path for old Ollama builds or missing chat-model endpoints.
                print(f"{YELLOW}[VoiceAssistant] /chat streaming failed ({chat_error}). Falling back to /generate with responder model.{RESET}")
                fallback_payload = {
                    "model": RESPONDER_MODEL,
                    "prompt": user_text,
                    "stream": False,
                    "keep_alive": "5m"
                }
                fallback_resp = http_session.post(f"{OLLAMA_URL}/generate", json=fallback_payload, timeout=60)
                if fallback_resp.status_code == 200:
                    full_response = fallback_resp.json().get("response", "")
                    if full_response:
                        tts.queue_sentence(full_response)
                else:
                    raise
            
            # Flush remaining
            if not stop_event.is_set():
                rem = sentence_buffer.flush()
                if rem:
                    tts.queue_sentence(rem)
            
            # PERSONALITY SYSTEM: Apply personality traits
            print(f"{CYAN}[PersonalitySystem] Applying personality traits...{RESET}")
            full_response = personality_system.apply_all_trait_modifications(full_response)
            
            # PERSONALIZATION: Adapt response to user
            print(f"{CYAN}[Personalization] Personalizing response...{RESET}")
            user_id = "default_user"
            full_response = adaptive_personalizer.personalize_response(full_response, user_id)
            if hasattr(adaptive_personalizer, "adapt_communication_style"):
                full_response = adaptive_personalizer.adapt_communication_style(full_response, user_id)
            else:
                full_response = adaptive_personalizer.personalize_response(full_response, user_id)
            
            # METACOGNITION ENGINE: Add self-reflection
            print(f"{CYAN}[MetacognitionEngine] Adding metacognitive elements...{RESET}")
            metacognitive_result = metacognition_engine.process_with_metacognition(
                query=user_text,
                response=full_response,
                reasoning_steps=[],
                confidence=0.7
            )
            full_response = metacognitive_result.get("final_response", full_response)
            
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
