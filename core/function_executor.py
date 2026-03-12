"""
Simplified Function Executor for Wolf AI.
"""

from core.llm import route_query, should_bypass_router, http_session  
from core.pc_control import pc_controller  
from core.vision_agent import vision_agent  
from core.dev_agent import dev_agent  
from core.receptionist import receptionist  
from core.memory import memory_manager  
from core.enhanced_thinking import enhanced_thinking_router  
from core.settings_store import settings  
from core.tts import tts  
from config import OLLAMA_URL, RESPONDER_MODEL, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI  
import json
import re
import requests  
import threading
import time
import os
import hashlib
import psutil  
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from utilities.youtube_handler import YouTubeHandler  
from utilities.spotify_handler import SpotifyHandler  
from utilities.research_handler import research_handler  
from utilities.search_handler import web_search_handler  

class FunctionExecutor:
    """Central executor for simplified core functions."""
    
    def __init__(self):
        # Placeholder for managers if needed later
        self.tasks_file = "tasks.json"
        self.tasks = self._load_tasks()
        self._event_lock = threading.Lock()
        self._event_counter = 0
        self._execution_events: List[Dict[str, Any]] = []
        self._media_lock = threading.Lock()
        self._media_state: Dict[str, Any] = {
            "isPlaying": False,
            "service": "auto",
            "source": "none",
            "trackTitle": "Idle",
            "trackArtist": "Wolf AI",
            "durationSec": 0,
            "positionSec": 0,
            "volume": 70,
            "streamUrl": "",
            "localSongId": "",
            "updatedAt": time.time()
        }
        self.youtube_handler = YouTubeHandler()
        self.spotify_handler = SpotifyHandler(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
        )
        self.spotify_ready = False
        self._local_song_map: Dict[str, str] = {}
        self._local_song_catalog: List[Dict[str, Any]] = []
        self._last_app_open_ts: Dict[str, float] = {}
        self._reindex_local_songs()
        self.app_map = {
            "visual studio code": "C:\\Users\\User\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
            "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            "edge": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            "safari": "C:\\Program Files\\Safari\\Application\\safari.exe",
            "notepad": "C:\\Windows\\notepad.exe",
            "word": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
            "excel": "C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE",
            "powerpoint": "C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE",
            "spotify": "C:\\Users\\User\\AppData\\Roaming\\Spotify\\spotify.exe",
            "vlc": "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
            "telegram": "C:\\Users\\User\\AppData\\Roaming\\Telegram Desktop\\Telegram.exe",
            "discord": "C:\\Users\\User\\AppData\\Local\\Discord\\app-1.0.9003\\Discord.exe",
            "slack": "C:\\Users\\User\\AppData\\Local\\slack\\app-4.23.0\\slack.exe"
        }

    def _emit_execution_event(self, event_type: str, message: str, **extra: Any) -> None:
        """Store a structured execution event for live frontend streaming."""
        with self._event_lock:
            self._event_counter += 1
            event = {
                "id": self._event_counter,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "type": event_type,
                "message": message,
            }
            event.update(extra)
            self._execution_events.append(event)

            # Keep memory bounded.
            if len(self._execution_events) > 1000:
                self._execution_events = list(self._execution_events[-1000:]) 

    def get_execution_events(self, after_id: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Return execution events newer than the provided event id."""
        with self._event_lock:
            new_events = [e for e in self._execution_events if e.get("id", 0) > after_id]
            return new_events[:limit] 

    def _reindex_local_songs(self) -> None:
        """Index local audio files from common folders for fallback playback."""
        search_roots = [
            Path.cwd() / "music",
            Path.cwd() / "Music",
            Path.home() / "Music",
            Path.home() / "Downloads",
        ]
        exts = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}

        catalog: List[Dict[str, Any]] = []
        id_map: Dict[str, str] = {}

        for root in search_roots:
            if not root.exists() or not root.is_dir():
                continue
            try:
                for file in root.rglob("*"):
                    if not file.is_file() or file.suffix.lower() not in exts:
                        continue
                    sid = hashlib.sha1(str(file).encode("utf-8")).hexdigest()[:16] 
                    title = file.stem.replace("_", " ").replace("-", " ").strip()
                    rec = {
                        "id": sid,
                        "title": title,
                        "artist": file.parent.name,
                        "path": str(file),
                    }
                    catalog.append(rec)
                    id_map[sid] = str(file)
            except Exception:
                continue

        self._local_song_catalog = catalog
        self._local_song_map = id_map

    def get_local_song_path(self, song_id: str) -> str:
        """Resolve a local song id to absolute path."""
        return self._local_song_map.get(song_id, "")

    def _search_local_song(self, query: str) -> Dict[str, Any]:
        """Best-effort local song matcher by filename tokens."""
        if not self._local_song_catalog:
            self._reindex_local_songs()
        if not self._local_song_catalog:
            return {}

        q = (query or "").lower().strip()
        tokens = [t for t in re.split(r"\s+", q) if t]

        scored: List[Dict[str, Any]] = []
        for item in self._local_song_catalog:
            hay = f"{item.get('title','')} {item.get('artist','')}".lower()
            if not tokens:
                score = 1
            else:
                score = sum(1 for t in tokens if t in hay)
            if score > 0:
                scored.append({"score": score, "item": item})

        if not scored:
            return {}
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[0]["item"]

    def _ensure_spotify_ready(self) -> bool:
        """Initialize Spotify auth once if API credentials are available."""
        if self.spotify_ready:
            return True
        ok, _msg = self.spotify_handler.authenticate()
        self.spotify_ready = bool(ok)
        return self.spotify_ready

    def _attempt_spotify_play(self, query: str) -> Dict[str, Any]:
        """Try playing through Spotify API. Returns source payload or empty dict on failure."""
        if not self._ensure_spotify_ready():
            return {}

        track = self.spotify_handler.search_track_info(query)
        if not track:
            return {}

        played = self.spotify_handler.play_track_uri(track.get("uri", ""))
        if not played:
            return {}

        self._pc_control({"action": "open_app", "target": "spotify"})
        return {
            "source": "spotify",
            "service": "spotify",
            "trackTitle": track.get("title", query.title()),
            "trackArtist": track.get("artist", "Spotify"),
            "durationSec": int(track.get("duration_ms", 0) / 1000) if track.get("duration_ms") else 0,
            "streamUrl": track.get("preview_url") or "",
            "localSongId": "",
        }

    def _attempt_spotify_desktop_play(self, query: str) -> Dict[str, Any]:
        """Fallback for local Spotify app control without Spotify API credentials."""
        now = time.time()
        if (now - float(self._last_app_open_ts.get("spotify", 0.0))) < 8.0:
            # Spotify was just opened by a previous action in this same command chain.
            spotify_running = True
        else:
            spotify_running = False

        try:
            if not spotify_running:
                for proc in psutil.process_iter(["name"]):
                    name = (proc.info.get("name") or "").lower()
                    if name == "spotify.exe" or name == "spotify":
                        spotify_running = True
                        break
        except Exception:
            if not spotify_running:
                spotify_running = False

        if not spotify_running:
            open_result = self._pc_control({"action": "open_app", "target": "spotify"})
            if not open_result.get("success"):
                return {}

        # Best effort: toggle system media playback to start/resume Spotify.
        self._pc_control({"action": "media", "target": "playpause"})

        return {
            "source": "spotify_desktop",
            "service": "spotify",
            "trackTitle": query.title() if query else "Spotify Playback",
            "trackArtist": "Spotify",
            "durationSec": 0,
            "streamUrl": "",
            "localSongId": "",
        }

    def _attempt_local_play(self, query: str) -> Dict[str, Any]:
        """Try local file playback and return a browser-playable backend URL."""
        song = self._search_local_song(query)
        if not song:
            return {}
        return {
            "source": "local",
            "service": "local",
            "trackTitle": song.get("title", query.title()),
            "trackArtist": song.get("artist", "Local Library"),
            "durationSec": 0,
            "streamUrl": f"/api/media/local/{song.get('id','')}",
            "localSongId": song.get("id", ""),
        }

    def _attempt_youtube_play(self, query: str) -> Dict[str, Any]:
        """Try YouTube search + direct stream URL fallback."""
        results = self.youtube_handler.search(query, limit=1)
        if not results:
            return {}
        first = results[0]
        stream_url = self.youtube_handler.get_stream_url(first.get("url", "")) or ""
        if not stream_url:
            return {}
        self._pc_control({"action": "open_app", "target": "chrome"})
        return {
            "source": "youtube",
            "service": "youtube",
            "trackTitle": first.get("title", query.title()),
            "trackArtist": first.get("uploader", "YouTube"),
            "durationSec": int(first.get("duration", 0) or 0),
            "streamUrl": stream_url,
            "localSongId": "",
        }
    
    def execute(self, func_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function and return result."""
        try:
            if func_name == "pc_control":
                return self._pc_control(params)
            elif func_name == "play_music":
                return self._play_music(params)
            elif func_name == "scaffold_website":
                return self._scaffold_website(params)
            elif func_name == "set_call_directive":
                return self._set_call_directive(params)
            elif func_name == "visual_agent":
                return self._visual_agent(params)
            elif func_name == "create_task":
                return self._create_task(params)
            elif func_name == "edit_task":
                return self._edit_task(params)
            elif func_name == "list_tasks":
                return self._list_tasks(params)
            elif func_name == "execute_task":
                return self._execute_task(params)
            elif func_name == "research_web":
                return self._research_web(params)
            elif func_name == "web_search":
                return self._web_search(params)
            elif func_name == "recall_memory":
                return self._recall_memory(params)
            elif func_name == "remember":
                return self._remember_preference(params)
            elif func_name in ("thinking", "nonthinking"):
                prompt = params.get("prompt", "")
                # Check if this is a capability question
                if self._is_capability_question(prompt):
                    return self._capability_overview()
                elif func_name == "thinking":
                    # Use enhanced thinking router for complex reasoning
                    return self._enhanced_thinking(prompt, params)
                else:
                    return {"success": True, "message": "Direct LLM response."}
            else:
                return {"success": False, "message": f"Unknown function: {func_name}"}
        except Exception as e:
            return {"success": False, "message": f"Execution error: {str(e)}"}
    
    def _is_capability_question(self, prompt: str) -> bool:
        """Check if the prompt is asking about capabilities."""
        capability_keywords = [
            "tell me about yourself", "what can you do", "who are you", "what are you",
            "your capabilities", "what do you do", "help", "abilities", "features",
            "what are your features", "introduction", "introduce yourself"
        ]
        
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in capability_keywords)
    
    def _is_app_opening_command(self, prompt: str) -> bool:
        """Check if prompt is trying to open an app but was misrouted."""
        # More aggressive detection for app opening commands
        prompt_lower = prompt.lower()
        
        # Direct app opening patterns
        open_patterns = [
            r"open\s+(\w+)",
            r"launch\s+(\w+)", 
            r"start\s+(\w+)",
            r"run\s+(\w+)"
        ]
        
        # Check for direct patterns first
        for pattern in open_patterns:
            if re.search(pattern, prompt_lower):
                print(f"[FunctionExecutor] Found app opening pattern: {pattern}")
                return True
        
        # Check for UI-related terms that indicate complex commands
        ui_terms = ["select", "choose", "profile", "search", "find", "click", "type", "navigate", "scroll", "wait"]
        
        # If any UI term is found, it's likely a complex command
        if any(term in prompt_lower for term in ui_terms):
            print(f"[FunctionExecutor] Detected UI-related command: '{prompt}'")
            return True
        
        # Check for app names in the prompt
        app_keywords = [
            "chrome", "firefox", "edge", "safari", "visual studio", "vs code", 
            "visualstudio", "notepad", "word", "excel", "powerpoint", 
            "spotify", "vlc", "telegram", "discord", "slack"
        ]
        
        # If any app name is mentioned, treat as app command
        if any(app in prompt_lower for app in app_keywords):
            print(f"[FunctionExecutor] Found app keyword in: '{prompt}'")
            return True
            
        return False
    
    def _capability_overview(self) -> Dict[str, Any]:
        """Return an overview of Wolf AI's capabilities."""
        capabilities = """I'm Wolf AI, your voice assistant! I can control your computer, manage tasks, play music, and help with complex problems.

Here's what I can do:
• Open apps like Visual Studio, Chrome, or Spotify
• Control volume, take screenshots, lock your screen
• Create and manage tasks with plain English descriptions
• Play music on YouTube or Spotify
• Find and click elements on your screen using visual AI
• Solve complex problems through reasoning
• Build websites and applications
• Have natural conversations

Just say "Hey Wolf" followed by any command. For example: "Hey Wolf, open Visual Studio" or "Hey Wolf, what can you do?"

Say "stop" or "quit" at any time to interrupt me."""
        
        return {
            "success": True,
            "message": capabilities.strip(),
            "data": {"type": "capability_overview"}
        }

    def _enhanced_thinking(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute enhanced thinking with structured reasoning stages."""
        print(f"[FunctionExecutor] Enhanced Thinking Mode: {prompt}")

        # If this is an actionable computer-ops prompt, execute it instead of only reasoning.
        if self._is_actionable_computer_task(prompt):
            print("[FunctionExecutor] Thinking prompt is actionable. Delegating to autonomous task executor...")
            delegated = self._execute_task({
                "description": prompt,
                "max_steps": params.get("max_steps", 15)
            })
            # Ensure we handle the result safely for type-checking
            final_res = {} if not isinstance(delegated, dict) else delegated
            inner_data = final_res.get("data", {})
            if not isinstance(inner_data, dict):
                inner_data = {}
            
            # Explicitly cast or use type ignore for Pyre2
            inner_data["type"] = "autonomous_execution" 
            inner_data["routed_from"] = "thinking" 
            
            final_res["data"] = inner_data 
            return final_res
        
        # Determine reasoning depth from params
        depth = params.get("depth", "medium")  # shallow, medium, deep
        
        # Route through enhanced thinking
        try:
            thinking_result = enhanced_thinking_router.route_thinking_query(prompt, depth=depth)
            
            return {
                "success": True,
                "message": thinking_result.get("reasoning", "Reasoning complete."),
                "data": {
                    "type": "enhanced_thinking",
                    "strategy": thinking_result.get("strategy", "unknown"),
                    "depth": thinking_result.get("depth", depth),
                    "stages": thinking_result.get("stages", []),
                    "full_result": thinking_result
                }
            }
        
        except Exception as e:
            print(f"[FunctionExecutor] Error in enhanced thinking: {e}")
            return {
                "success": False,
                "message": f"Thinking error: {str(e)}",
                "data": {}
            }

    def _is_actionable_computer_task(self, prompt: str) -> bool:
        """Heuristic detector for prompts that should execute on the PC instead of pure reasoning."""
        if not prompt:
            return False

        text = prompt.lower()

        action_verbs = [
            "open", "launch", "start", "run", "create", "make", "delete", "remove",
            "rename", "move", "copy", "write", "save", "install", "uninstall"
        ]
        computer_objects = [
            "file", "folder", "directory", "desktop", "downloads", "documents", "vscode",
            "vs code", "visual studio code", "terminal", "powershell", "cmd", ".html", ".py", ".txt"
        ]
        execution_markers = ["then", "after that", "step", "and then", "on my pc", "on my computer"]

        has_action = any(v in text for v in action_verbs)
        has_object = any(o in text for o in computer_objects)
        has_exec_marker = any(m in text for m in execution_markers)

        return (has_action and has_object) or (has_action and has_exec_marker)

    def _pc_control(self, params: Dict):
        """Handle system level commands."""
        action = params.get("action", "unknown")
        target = params.get("target", "")
        
        print(f"[FunctionExecutor] PC Control: action='{action}', target='{target}'")
        
        try:
            result = pc_controller.execute(action, target)
            result["data"] = {"action": action, "target": target}

            if action == "open_app" and result.get("success"):
                app_key = str(target or "").strip().lower()
                if app_key:
                    self._last_app_open_ts[app_key] = time.time()

            print(f"[FunctionExecutor] PC Control result: {result}")
            return result
        except Exception as e:
            print(f"[FunctionExecutor] PC Control error: {e}")
            return {"success": False, "message": f"PC Control error: {str(e)}"}

    def _research_web(self, params: Dict):
        """Perform deep web research using Crawl4AI."""
        url = params.get("url")
        if not url:
            return {"success": False, "message": "No URL provided for research."}
        
        self._emit_execution_event("research_start", f"Performing deep research on: {url}", url=url)
        result = research_handler.scrape_url_sync(url)
        
        if result.get("success"):
            self._emit_execution_event("research_complete", f"Successfully researched: {result.get('title')}", title=result.get("title"))
        else:
            self._emit_execution_event("research_error", f"Research failed: {result.get('message')}")
            
        return result

    def _web_search(self, params: Dict):
        """Perform a web search using DuckDuckGo."""
        query = params.get("query")
        if not query:
            return {"success": False, "message": "No search query provided."}
            
        self._emit_execution_event("search_start", f"Searching web for: {query}", query=query)
        results = web_search_handler.search(query, limit=params.get("limit", 5))
        
        if results:
            self._emit_execution_event("search_complete", f"Found {len(results)} search results.", count=len(results))
            return {
                "success": True, 
                "message": f"Found {len(results)} results for '{query}'.",
                "data": {"results": results}
            }
        else:
            return {"success": False, "message": f"No results found for '{query}'."}

    def _recall_memory(self, params: Dict):
        """Recall information from past interactions and logs."""
        query = params.get("query", "")
        if not query:
            return {"success": False, "message": "No recall query provided."}
            
        print(f"[FunctionExecutor] Recalling memory for: {query}")
        
        # 1. Check reasoning logs
        reasoning = memory_manager.get_similar_reasoning(query, limit=3)
        
        # 2. Check interaction history
        # We need a search method for interaction history, but let's use recent context for now
        # Or we can just build a summary
        history = memory_manager.get_conversation_context(limit=10)
        
        # 3. Check patterns
        patterns = memory_manager.get_learned_patterns()
        relevant_patterns = []
        for name, data in patterns.items():
            if query.lower() in name.lower() or query.lower() in str(data).lower():
                relevant_patterns.append({"name": name, "data": data})
                
        message = f"Memory recall for '{query}':\n"
        if reasoning:
            message += f"\nRelevant past reasoning:\n"
            for r in reasoning:
                message += f"- Query: {r.get('query')}\n  Action: {r.get('action_taken')}\n"
        
        if relevant_patterns:
            message += f"\nLearned patterns:\n"
            for p in relevant_patterns:
                message += f"- {p['name']}: {p['data'].get('data', {}).get('description', 'N/A')}\n"
        else:
            message += f"\nNo specific memories found about '{query}'."
                
        return {
            "success": True,
            "message": message,
            "data": {
                "reasoning": reasoning,
                "patterns": relevant_patterns,
                "history": history
            }
        }

    def _remember_preference(self, params: Dict):
        """Store user preferences in memory."""
        preference = params.get("preference", "")
        if not preference:
            return {"success": False, "message": "No preference provided to remember."}
            
        print(f"[FunctionExecutor] Storing preference: {preference}")
        
        # Store in user preferences
        try:
            # Extract key information
            preference_data = {
                "preference": preference,
                "timestamp": datetime.now().isoformat(),
                "category": "user_preference"
            }
            
            # Save to memory
            memory_manager.save_user_preference("general_preference", preference_data)
            
            return {
                "success": True, 
                "message": f"I'll remember that: {preference}"
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to store preference: {str(e)}"}

    def _play_music(self, params: Dict):
        """Handle music commands with source fallback: spotify -> local -> youtube."""
        query = str(params.get("query", "music") or "music").strip()
        preferred_service = str(params.get("service", "auto") or "auto").lower().strip()

        source_payload: Dict[str, Any] = {}
        attempts: List[str] = []

        if preferred_service in ("auto", "spotify"):
            attempts.append("spotify")
            source_payload = self._attempt_spotify_play(query)
            if not source_payload:
                attempts.append("spotify_desktop")
                source_payload = self._attempt_spotify_desktop_play(query)

        if not source_payload and preferred_service in ("auto", "local"):
            attempts.append("local")
            source_payload = self._attempt_local_play(query)

        if not source_payload and preferred_service in ("auto", "youtube"):
            attempts.append("youtube")
            source_payload = self._attempt_youtube_play(query)

        if not source_payload:
            self._emit_execution_event(
                "media_error",
                f"Playback failed for '{query}'. Tried: {', '.join(attempts) if attempts else 'none'}"
            )
            return {
                "success": False,
                "message": f"Could not play '{query}'. Spotify/local/YouTube were unavailable.",
                "data": {"query": query, "attempts": attempts, "state": self.get_media_state()}
            }

        with self._media_lock:
            self._media_state.update({
                "isPlaying": True,
                "service": source_payload.get("service", "auto"),
                "source": source_payload.get("source", "unknown"),
                "trackTitle": source_payload.get("trackTitle", query.title()),
                "trackArtist": source_payload.get("trackArtist", "Unknown Artist"),
                "durationSec": int(source_payload.get("durationSec", 0) or 0),
                "positionSec": 0,
                "streamUrl": source_payload.get("streamUrl", ""),
                "localSongId": source_payload.get("localSongId", ""),
                "updatedAt": time.time(),
            })

        state = self.get_media_state()
        self._emit_execution_event(
            "media_play",
            f"Now playing {state.get('trackTitle')} via {state.get('source')}",
            media_state=state,
            attempts=attempts,
        )

        return {
            "success": True,
            "message": f"Now playing {state.get('trackTitle')} via {state.get('source')}.",
            "data": {"query": query, "service": preferred_service, "state": state, "attempts": attempts}
        }

    def get_media_state(self) -> Dict[str, Any]:
        """Return media state with real-time progress interpolation."""
        with self._media_lock:
            now = time.time()
            state = dict(self._media_state)

            if state.get("isPlaying") and state.get("durationSec", 0) > 0:
                elapsed = max(0, int(now - state.get("updatedAt", now)))
                state["positionSec"] = min(state.get("positionSec", 0) + elapsed, state.get("durationSec", 0))

                if state["positionSec"] >= state.get("durationSec", 0):
                    state["isPlaying"] = False
                    self._media_state.update({
                        "isPlaying": False,
                        "positionSec": state["positionSec"],
                        "updatedAt": now
                    })
                else:
                    self._media_state.update({
                        "positionSec": state["positionSec"],
                        "updatedAt": now
                    })

            return state

    def control_media(self, action: str, **kwargs: Any) -> Dict[str, Any]:
        """Control media state and mirror media-key actions where possible."""
        action = (action or "").lower().strip()
        now = time.time()

        if action == "play":
            query = kwargs.get("query") or self._media_state.get("trackTitle") or "music"
            service = kwargs.get("service") or self._media_state.get("service") or "youtube"
            return self._play_music({"query": query, "service": service})

        if action in ("pause", "toggle"):
            # Trigger OS media key for active player.
            self._pc_control({"action": "media", "target": "playpause"})
            current = self.get_media_state()
            with self._media_lock:
                self._media_state.update({
                    "isPlaying": not current.get("isPlaying", False),
                    "updatedAt": now
                })

        elif action in ("next", "prev", "previous"):
            media_target = "next" if action == "next" else "prev"
            self._pc_control({"action": "media", "target": media_target})
            with self._media_lock:
                self._media_state.update({
                    "positionSec": 0,
                    "updatedAt": now
                })

        elif action == "seek":
            target_sec = int(kwargs.get("positionSec", 0) or 0)
            with self._media_lock:
                duration = int(self._media_state.get("durationSec", 0) or 0)
                if duration > 0:
                    target_sec = max(0, min(target_sec, duration))
                self._media_state.update({
                    "positionSec": target_sec,
                    "updatedAt": now
                })

        elif action == "set_volume":
            volume = int(kwargs.get("volume", 70) or 70)
            volume = max(0, min(volume, 100))
            self._pc_control({"action": "volume", "target": str(volume)})
            with self._media_lock:
                self._media_state.update({
                    "volume": volume,
                    "updatedAt": now
                })
        else:
            return {"success": False, "message": f"Unsupported media action: {action}", "data": {"state": self.get_media_state()}}

        state = self.get_media_state()
        self._emit_execution_event("media_control", f"Media action executed: {action}", action=action, media_state=state)
        return {"success": True, "message": f"Media action executed: {action}", "data": {"state": state}}

    def _scaffold_website(self, params: Dict):
        """Handle website scaffolding."""
        prompt = params.get("prompt", "")
        framework = params.get("framework", "html")
        
        return dev_agent.scaffold_project(prompt, framework)

    def _set_call_directive(self, params: Dict):
        """Handle expecting an incoming call."""
        caller = params.get("caller_name", "Unknown caller")
        instructions = params.get("instructions", "Say hello")
        return receptionist.add_directive(caller, instructions)

    def _visual_agent(self, params: Dict):
        """Handle visual UI interactions using VisionAgent."""
        task = params.get("task", "click on something")
        action = params.get("action", "click")
        
        if action == "type":
            return vision_agent._find_and_type_text(task)
        elif action == "scroll":
            return vision_agent._scroll_screen(task)
        elif action == "describe":
            msg = vision_agent._describe_screen()
            return {"success": True, "message": msg}
        else:
            return vision_agent._find_and_click_element(task)

    def _load_tasks(self):
        """Load tasks from JSON file."""
        try:
            with open(self.tasks_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_tasks(self):
        """Save tasks to JSON file."""
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(self.tasks, f, indent=2)
            return True
        except Exception as e:
            print(f"[FunctionExecutor] Error saving tasks: {e}")
            return False

    def _create_task(self, params: Dict):
        """Create a new task."""
        title = params.get("title", "Untitled Task")
        description = params.get("description", "")
        
        task = {
            "id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": title,
            "description": description,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.tasks.append(task)
        if self._save_tasks():
            return {
                "success": True, 
                "message": f"Task '{title}' created successfully.", 
                "data": {"task_id": task["id"], "task": task}
            }
        else:
            return {"success": False, "message": "Failed to save task."}

    def _edit_task(self, params: Dict):
        """Edit an existing task."""
        task_id = params.get("task_id")
        title = params.get("title")
        description = params.get("description")
        
        for task in self.tasks:
            if task.get("id") == task_id:
                if title:
                    task["title"] = title
                if description:
                    task["description"] = description
                task["updated_at"] = datetime.now().isoformat()
                
                if self._save_tasks():
                    return {"success": True, "message": f"Task '{task_id}' updated successfully.", "data": {"task": task}}
                else:
                    return {"success": False, "message": "Failed to save updated task."}
                    
        return {"success": False, "message": f"Task '{task_id}' not found."}

    def _list_tasks(self, params: Dict):
        """List all tasks."""
        status_filter = params.get("status", None)
        
        if status_filter:
            filtered_tasks = [t for t in self.tasks if t.get("status") == status_filter]
        else:
            filtered_tasks = self.tasks
        
        return {
            "message": f"Found {len(filtered_tasks)} tasks.",
            "data": {"tasks": filtered_tasks, "count": len(filtered_tasks)}
        }

    def _create_simple_task(self, task_id: str, description: str, max_steps: int) -> Dict[str, Any]:
        """Fallback to simple task execution for low confidence tasks."""
        print(f"[FunctionExecutor] Using simple execution for: {description}")
        
        if "create" in description.lower():
            return self._create_simple_file_task(task_id, description)
        elif "open" in description.lower():
            return self._open_simple_app_task(task_id, description)
        else:
            return {"success": False, "message": f"Simple task not supported: {description}"}
    
    def _create_simple_file_task(self, task_id: str, description: str) -> Dict[str, Any]:
        """Create a simple file task."""
        # Extract file name from description
        import re
        match = re.search(r"create(?: file)?\s+(?:called\s+)?[\"']?([^\"'\s]+)[\"']?", description, re.IGNORECASE)
        if match:
            filename = match.group(1).strip()
        else:
            filename = "new_file.txt"
        
        # Create file
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            file_path = os.path.join(desktop_path, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Created file: {description}")
            
            # Update task status
            task = next((t for t in self.tasks if t.get('id') == task_id), None)
            if task:
                task['status'] = 'completed'
                task['result'] = f"Created {filename}"
            
            return {"success": True, "message": f"Created {filename}", "file_path": file_path}
        except Exception as e:
            return {"success": False, "message": f"File creation failed: {e}"}
    
    def _open_simple_app_task(self, task_id: str, description: str) -> Dict[str, Any]:
        """Open a simple application task."""
        # Extract app name from description
        import re
        match = re.search(r"open\s+(?:visual\s+studio\s+code|vs\s+code|chrome|firefox|notepad|calculator)", description, re.IGNORECASE)
        if match:
            app_name = match.group(0).strip()
        else:
            app_name = description.strip()
        
        # Launch application
        try:
            from core.pc_control import pc_controller
            result = pc_controller._open_app(app_name)
            
            # Update task status
            task = next((t for t in self.tasks if t.get('id') == task_id), None)
            if task:
                task['status'] = 'completed'
                task['result'] = f"Opened {app_name}"
            
            return result
        except Exception as e:
            return {"success": False, "message": f"Application launch failed: {e}"}
    
    def _execute_task(self, params: Dict):
        """Execute a task using AI intelligence to understand and complete it."""
        
        task_id = params.get("task_id")
        description = params.get("description")
        
        if task_id:
            # Find task by ID
            task = next((t for t in self.tasks if t.get('id') == task_id), None)
            if not task:
                return {"success": False, "message": f"Task with ID '{task_id}' not found."}
            description = task.get('description', '')
        
        if not description:
            return {"success": False, "message": "No task description provided."}
        
        max_steps = int(params.get("max_steps", 10)) or 10
        
        # Use advanced AI for task understanding and execution
        from core.advanced_task_executor import advanced_executor
        
        # First, try to understand the task using AI
        task_understanding = advanced_executor.understand_task(description)
        
        if task_understanding["confidence"] < 0.3:
            # Low confidence, fall back to simple execution
            return self._create_simple_task(task_id, description, max_steps)
        
        # High confidence, use advanced multi-step execution
        execution_plan = task_understanding["execution_plan"]
        execution_result = advanced_executor.execute_plan(execution_plan)
        
        # Generate response based on execution results
        if execution_result["success"]:
            response = f"Task completed successfully! {execution_result['summary']}"
        else:
            failed_steps = [r for r in execution_result["results"] if not r["success"]]
            response = f"Task partially completed. {execution_result['summary']}. Failed steps: {len(failed_steps)}"
        
        # Emit execution events for real-time feedback
        self._emit_execution_event(
            "task_start",
            f"Starting advanced task: {description}",
            task_id=task_id,
            description=description,
            max_steps=max_steps,
        )
        
        try:
            print(f"[FunctionExecutor] Executing advanced task: '{description}'")
            
            # Execute each step with real-time feedback
            for i, step in enumerate(execution_result["results"], 1):
                step_num = step["step"]
                action = step["action"]
                details = step["details"]
                
                self._emit_execution_event(
                    "step_progress",
                    f"Step {step_num}: {action}",
                    task_id=task_id,
                    step=step_num,
                    action=action,
                    details=details
                )
                
                # Extract function call from step details
                calls = step.get("calls", [])
                if calls:
                    try:
                        func_name, route_params = calls[0] # Take strictly the first call
                        
                        if func_name == "task_complete":
                            final_message = route_params.get("message", "Task completed via agent logic.")
                            success = True
                            self._emit_execution_event( 
                                "task_complete",
                                final_message,
                                task_id=task_id,
                                step=step + 1,
                            )
                            break
                            
                        print(f"[AgentLoop] Step {step+1}: Executing {func_name} with {route_params}")
                        self._emit_execution_event( 
                            "step_execute",
                            f"Executing {func_name}",
                            task_id=task_id,
                            step=step + 1,
                            function=func_name,
                            params=route_params,
                        )
                        executed_funcs.append(func_name)
                            
                        # Execute the function
                        result = self.execute(func_name, route_params)  
                        results.append(result)
                        
                        # Update history
                        res_msg = result.get("message", "No message")
                        self._emit_execution_event( 
                            "step_result",
                            res_msg,
                            task_id=task_id,
                            step=step + 1,
                            function=func_name,
                            success=result.get("success", False),
                        )
                        history_str += f"\n- Step: call:{func_name}{route_params}\n- Result: {res_msg}\n"
                        
                        print(f"[AgentLoop] Step {step+1} Result: {res_msg}")
                            
                    except Exception as e:
                        print(f"[AgentLoop] Error in LLM step: {e}")
                        success = False
                        final_message = f"Error communicating with AI: {e}"
                        self._emit_execution_event( 
                            "step_error",
                            final_message,
                            task_id=task_id,
                            step=step + 1,
                        )
                        break
            
            if not success and final_message == "Task stopped.":
                final_message = f"Reached maximum steps ({max_steps}) without calling task_complete."
                self._emit_execution_event( 
                    "task_timeout",
                    final_message,
                    task_id=task_id,
                    max_steps=max_steps,
                )
            
            # Update task status if we have a task_id
            if task_id:
                for task in self.tasks:
                    if task.get('id') == task_id:
                        task["status"] = "completed" if success else "failed"
                        task["updated_at"] = datetime.now().isoformat()
                        break
                self._save_tasks()
            
            result_data = {
                "success": success,
                "message": f"Agent finished! Goal: '{description}'. Result: {final_message}",
                "data": {
                    "original_task": description,
                    "ai_reasoning": history_str,
                    "executed_functions": executed_funcs,
                    "result": results[-1] if results else {}
                }
            }
            self._emit_execution_event(
                "task_end",
                final_message,
                task_id=task_id,
                success=success,
            )
            return result_data
                
        except Exception as e:
            print(f"[FunctionExecutor] Error executing task: {e}")
            self._emit_execution_event(
                "task_error",
                f"Task execution crashed: {str(e)}",
                task_id=task_id,
            )
            return {"success": False, "message": f"Error executing task: {str(e)}"}

# Global instance
executor = FunctionExecutor()
