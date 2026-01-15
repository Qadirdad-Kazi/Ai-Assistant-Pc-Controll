#!/usr/bin/env python3
"""
Wolf PC Control Module - Version 2.0 (Jarvis Protocol)
Handles system automation with multi-step execution and pronoun resolution.
"""

import os
import sys
import subprocess
import platform
import json
import time
import psutil
import pyautogui
import pyperclip
import shutil
import webbrowser
from pathlib import Path
from typing import Dict, List, Any, Optional

class WolfPCControl:
    def __init__(self):
        """Initialize Wolf PC Control with Platform Detection and Neural Buffer"""
        self.system_info = {
            "os": platform.system(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
        
        # Configure Safety
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # Execution Memory (Short-term context for pronouns and sequences)
        self.execution_memory = {
            "last_entity": None,
            "last_path": None,
            "pending_source": None,
            "pending_action": None
        }

        # App Mapping
        self.app_commands = {
            "calculator": ["Calculator", "calc"],
            "notepad": ["TextEdit", "notepad"],
            "terminal": ["Terminal", "cmd"],
            "browser": ["Safari", "chrome", "firefox"],
            "finder": ["Finder", "explorer"],
            "vscode": ["Visual Studio Code", "code"],
            "spotify": ["Spotify", "spotify"],
            "notes": ["Notes", "notepad"]
        }

        print(f"🖥️ Wolf PC Control initialized for {self.system_info['os']}")

    def _resolve_path(self, path_str: str) -> Path:
        """Premium Path Resolver: Converts shortcuts and pronouns into absolute system paths"""
        if not path_str or str(path_str).lower() == "it":
            return self.execution_memory["last_path"] or Path.home() / "Desktop"
            
        home = Path.home()
        ps = platform.system()
        
        # Platform Specific Shortcuts
        shortcuts = {
            "desktop": home / "Desktop",
            "downloads": home / "Downloads",
            "documents": home / "Documents",
            "music": home / "Music",
            "pictures": home / "Pictures",
            "videos": home / "Videos" if ps != "Darwin" else home / "Movies"
        }
        
        # Clean the input
        path_norm = str(path_str).lower().strip().replace("'", "").replace("\"", "")
        
        # Shortcut Match
        if path_norm in shortcuts:
            return shortcuts[path_norm]
            
        # Handle "on Desktop" etc.
        for key, value in shortcuts.items():
            if f"on {key}" in path_norm or f"in {key}" in path_norm:
                clean = path_str
                for prefix in ["on ", "in ", "the "]:
                    clean = clean.replace(prefix, "").replace(prefix.capitalize(), "")
                clean = clean.replace(key, "").replace(key.capitalize(), "").strip().rstrip('.!?,')
                return value / clean if clean else value

        # File-system Match
        path = Path(path_str.replace("'", "").replace("\"", "")).expanduser()
        if path.is_absolute():
            return path
            
        # Default fallback to Desktop
        return home / "Desktop" / path_str

    # --- NATIVE ACTION LAYER (Jarvis API) ---

    def action_create_folder(self, name: str, location: str = "Desktop") -> Dict[str, Any]:
        dest = self._resolve_path(location)
        path = dest / name
        path.mkdir(parents=True, exist_ok=True)
        return {"success": True, "message": f"Done. {name} has been created on your {dest.name}.", "path": str(path)}

    def action_copy(self, source_path: str) -> Dict[str, Any]:
        src = self._resolve_path(source_path)
        if not src.exists():
            return {"success": False, "error": f"I couldn’t find {src.name} on your {src.parent.name}."}
        self.execution_memory["pending_source"] = src
        self.execution_memory["pending_action"] = "copy"
        return {"success": True, "message": f"Source '{src.name}' locked for duplication.", "path": str(src)}

    def action_move(self, source_path: str) -> Dict[str, Any]:
        src = self._resolve_path(source_path)
        if not src.exists():
            return {"success": False, "error": f"I couldn’t find {src.name} on your {src.parent.name}."}
        self.execution_memory["pending_source"] = src
        self.execution_memory["pending_action"] = "move"
        return {"success": True, "message": f"Source '{src.name}' locked for relocation.", "path": str(src)}

    def action_paste(self, destination_path: str) -> Dict[str, Any]:
        src = self.execution_memory["pending_source"]
        if not src: return {"success": False, "error": "Nothing is locked in the neural buffer. Please copy or move something first."}
        
        dst = self._resolve_path(destination_path)
        
        # If dst is a folder that exists, paste INTO it.
        # If dst is a name that doesn't exist, use it as the RENAME target.
        if dst.parent.exists() and not dst.exists():
            final_dst = dst
        else:
            final_dst = dst / src.name

        try:
            if self.execution_memory["pending_action"] == "copy":
                if src.is_dir(): shutil.copytree(src, final_dst, dirs_exist_ok=True)
                else: shutil.copy2(src, final_dst)
            else:
                shutil.move(str(src), str(final_dst))
            
            self.execution_memory["pending_source"] = None # Clear buffer
            return {"success": True, "message": f"Done. {final_dst.name} has been created on your {final_dst.parent.name}.", "path": str(final_dst)}
        except Exception as e:
            return {"success": False, "error": f"Operation failed: {str(e)}"}

    def action_delete(self, target_path: str) -> Dict[str, Any]:
        path = self._resolve_path(target_path)
        if not path.exists():
            return {"success": False, "error": f"I couldn’t find {path.name} to delete."}
        try:
            if path.is_dir(): shutil.rmtree(path)
            else: path.unlink()
            return {"success": True, "message": f"Successfully removed {path.name}."}
        except Exception as e:
            return {"success": False, "error": f"Deletion failed: {str(e)}"}

    def action_open_app(self, app_name: str) -> Dict[str, Any]:
        """Open application using native launcher"""
        app_name = app_name.lower().strip()
        found = None
        for key, aliases in self.app_commands.items():
            if app_name == key or app_name in aliases:
                found = aliases[0]
                break
        
        target = found or app_name
        try:
            ps = platform.system()
            if ps == "Darwin": subprocess.run(["open", "-a", target])
            elif ps == "Windows": subprocess.run(["start", target], shell=True)
            else: subprocess.run([target])
            return {"success": True, "message": f"Launching {target}."}
        except: return {"success": False, "error": f"I couldn't open {target}."}

    def action_close_app(self, app_name: str) -> Dict[str, Any]:
        """Close application by name"""
        app_name = app_name.lower().strip()
        for proc in psutil.process_iter(['name']):
            if app_name in proc.info['name'].lower():
                proc.kill()
                return {"success": True, "message": f"Successfully stopped {app_name}."}
        return {"success": False, "error": f"I couldn't find a running process for {app_name}."}

    def action_navigate(self, target_path: str) -> Dict[str, Any]:
        """Open a folder in the native file explorer"""
        path = self._resolve_path(target_path)
        if not path.exists(): return {"success": False, "error": f"I couldn't find {path.name} to navigate to."}
        
        ps = platform.system()
        if ps == "Darwin": subprocess.run(["open", str(path)])
        elif ps == "Windows": os.startfile(str(path))
        else: subprocess.run(["xdg-open", str(path)])
        return {"success": True, "message": f"Opening {path.name} in file explorer."}

    # --- EXECUTION ROUTING ---

    def execute_structured_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Core execution engine for structured command objects"""
        if action == "sequence":
            results = []
            for step in params.get("steps", []):
                step_action = step.get("action")
                step_params = step.get("params", {})
                
                # Dynamic Parameter Injection (Pronouns/Memory)
                for k, v in step_params.items():
                    if str(v).lower() == "it":
                        step_params[k] = str(self.execution_memory["last_path"])
                
                res = self.execute_structured_action(step_action, step_params)
                if not res.get("success"): return res
                results.append(res)
            
            return {"success": True, "message": "Sequence complete. " + results[-1].get("message", ""), "results": results}

        # Route to handler
        handler = getattr(self, f"action_{action}", None)
        if handler:
            import inspect
            sig = inspect.signature(handler)
            filtered = {k: v for k, v in params.items() if k in sig.parameters}
            result = handler(**filtered)
            
            # Post-execution State Update
            if result.get("success"):
                if "path" in result: self.execution_memory["last_path"] = Path(result["path"])
                if "source_path" in params: self.execution_memory["last_path"] = self._resolve_path(params["source_path"])
            return result
        
        return {"success": False, "error": f"Command protocol '{action}' is not supported."}

    def execute_command(self, command: str) -> Dict[str, Any]:
        """High-level natural language entry point"""
        # 1. Parse into Structured Map
        norm = self._parse_to_normalized(command)
        if norm:
            return self.execute_structured_action(norm["action"], norm["params"])
            
        return {"success": False, "error": f"Protocol unrecognized: '{command}'"}

    def _parse_to_normalized(self, command: str) -> Optional[Dict[str, Any]]:
        """Natural Language to Structured JSON Parser"""
        cmd_lower = command.lower().strip()
        
        # Conjunction Splitter
        segments = []
        for conj in [" and then ", " after that ", " then ", " and "]:
            if conj in cmd_lower:
                segments = [s.strip() for s in cmd_lower.split(conj) if s.strip()]
                break
        if not segments: segments = [cmd_lower]

        if len(segments) > 1:
            steps = []
            for seg in segments:
                p = self._parse_single(seg)
                if p: steps.append(p)
            if steps: return {"action": "sequence", "params": {"steps": steps}}

        return self._parse_single(cmd_lower)

    def _parse_single(self, segment: str) -> Optional[Dict[str, Any]]:
        """Entity Extraction Logic"""
        def get_name(text):
            if '"' in text: return text.split('"')[1]
            if "'" in text: return text.split("'")[1]
            for kw in ["named ", "as ", "called ", "folder "]:
                if kw in text:
                    cand = text.split(kw)[1].strip()
                    words = []
                    for w in cand.split():
                        if w.lower() in ["on", "in", "from", "to", "and", "then"]: break
                        words.append(w)
                    return " ".join(words).rstrip('.!?,')
            return None

        seg = segment.lower()
        if "copy " in seg:
            return {"action": "copy", "params": {"source_path": get_name(segment) or seg.split("copy ")[1].split()[0]}}
        if "move " in seg:
            return {"action": "move", "params": {"source_path": get_name(segment) or seg.split("move ")[1].split()[0]}}
        if "paste " in seg:
            return {"action": "paste", "params": {"destination_path": get_name(segment) or "it"}}
        if "create " in seg or "make " in seg:
            return {"action": "create_folder", "params": {"name": get_name(segment) or "NewFolder"}}
        if "open " in seg or "show " in seg or "go to " in seg:
            target = get_name(segment)
            if not target:
                common = ["desktop", "downloads", "documents", "pictures", "music"]
                for c in common:
                    if c in seg:
                        target = c
                        break
            if not target:
                target = seg.split("open ")[1].split()[0] if "open " in seg else None
            
            # Decide if it's an app or a folder
            folder_keywords = ["desktop", "downloads", "documents", "folder", "directory"]
            if any(k in seg for k in folder_keywords):
                return {"action": "navigate", "params": {"target_path": target}}
            return {"action": "open_app", "params": {"app_name": target}}

        if "delete " in seg or "remove " in seg:
            return {"action": "delete", "params": {"target_path": get_name(segment) or seg.split("delete ")[1]}}
            
        return None

    def get_available_commands(self) -> List[str]:
        """Return list of supported action protocols"""
        return ["copy", "move", "paste", "create_folder", "delete", "open_app", "close_app", "navigate", "system_status"]

    def get_system_info(self) -> Dict[str, Any]:
        """Native Diagnostic Layer"""
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.5)
        return {
            "success": True, 
            "message": f"System Status: CPU {cpu}%, RAM {memory.percent}% usage."
        }