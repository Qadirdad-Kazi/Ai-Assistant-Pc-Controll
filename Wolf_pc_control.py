#!/usr/bin/env python3
"""
Wolf PC Control Module
Handles system automation and PC control commands
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
from pathlib import Path
from typing import Dict, List, Any, Optional
import webbrowser
import shutil

class WolfPCControl:
    def __init__(self):
        """Initialize PC Control module"""
        self.system_info = {
            "os": platform.system(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
        
        # Configure PyAutoGUI for safety
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # Application mappings
        self.app_commands = {
            "calculator": ["Calculator", "calc"],
            "notepad": ["TextEdit", "notepad"],
            "terminal": ["Terminal", "cmd"],
            "browser": ["Safari", "chrome", "firefox"],
            "finder": ["Finder", "explorer"],
            "vscode": ["Visual Studio Code", "code"],
            "vs code": ["Visual Studio Code", "code"],
            "notes": ["Notes", "notepad"],
            "spotify": ["Spotify", "spotify"],
            "music": ["Music", "wmplayer"]
        }
        
        # Command Registry: Map keywords to handler methods
        self.command_map = {
            "system_info": ["system info", "computer info", "hardware info", "diagnostic", "status"],
            "files_create": ["create folder", "make directory", "new folder", "mkdir"],
            "files_list": ["list files", "show files", "directory contents", "ls"],
            "files_delete": ["delete file", "remove file", "delete folder", "rm"],
            "files_copy": ["copy file", "duplicate file", "cp"],
            "files_move": ["move file", "rename file", "mv"],
            "web_open": ["open website", "browse to", "visit site", "go to"],
            "web_search": ["search google", "google search", "lookup"],
            "app_open": ["open application", "launch app", "start program", "open "],
            "app_close": ["close application", "quit app", "kill process", "stop app"],
            "screen_shot": ["take screenshot", "capture screen", "snapshot"],
            "window_min": ["minimize window", "minimize all", "hide windows"],
            "window_max": ["maximize window", "fullscreen"],
            "clip_copy": ["copy text", "clipboard copy", "copy to clipboard"],
            "clip_paste": ["paste text", "clipboard paste", "paste from clipboard"],
            "clip_show": ["show clipboard", "get clipboard"],
            "audio_vol_up": ["volume up", "increase volume", "louder"],
            "audio_vol_down": ["volume down", "decrease volume", "quieter"],
            "audio_mute": ["mute", "unmute", "silence"],
            "media_toggle": ["play music", "pause music", "play/pause", "media play", "resume"],
            "media_next": ["next track", "next song", "skip song"],
            "media_prev": ["previous track", "previous song", "last song", "back track"],
            "monitor_proc": ["running processes", "task list", "top processes"],
            "monitor_mem": ["memory usage", "ram usage", "memory status"],
            "monitor_cpu": ["cpu usage", "processor load", "cpu status"]
        }
        
        print(f"🖥️ Wolf PC Control initialized for {self.system_info['os']}")
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute PC control command based on natural language input"""
        cmd_input = command.lower().strip()
        
        # 1. Try exact keyword matching via dispatcher
        for action, keywords in self.command_map.items():
            if any(k in cmd_input for k in keywords):
                handler = getattr(self, f"_handle_{action}", None)
                if handler:
                    return handler(command)
        
        # 2. Check for naked application names (e.g., "open calculator")
        if cmd_input.startswith("open ") or cmd_input in self.app_commands:
            return self._handle_app_open(command)
            
        return {
            "success": False,
            "error": f"Protocol unrecognized: '{command}'",
            "available_commands": self.get_available_commands()
        }

    # Handler Methods (Internal)
    def _handle_system_info(self, cmd): return self.get_system_info()
    def _handle_files_create(self, cmd): return self.create_folder_from_command(cmd)
    def _handle_files_list(self, cmd): return self.list_files_from_command(cmd)
    def _handle_files_delete(self, cmd): return self.delete_file_from_command(cmd)
    def _handle_files_copy(self, cmd): return self.copy_file_from_command(cmd)
    def _handle_files_move(self, cmd): return self.move_file_from_command(cmd)
    def _handle_web_open(self, cmd): return self.open_website_from_command(cmd)
    def _handle_web_search(self, cmd): return self.google_search_from_command(cmd)
    def _handle_app_open(self, cmd): return self.open_application_from_command(cmd)
    def _handle_app_close(self, cmd): return self.close_application_from_command(cmd)
    def _handle_screen_shot(self, cmd): return self.take_screenshot()
    def _handle_window_min(self, cmd): return self.minimize_windows()
    def _handle_window_max(self, cmd): return self.maximize_window()
    def _handle_clip_copy(self, cmd): return self.copy_to_clipboard_from_command(cmd)
    def _handle_clip_paste(self, cmd): return self.paste_from_clipboard()
    def _handle_clip_show(self, cmd): return self.get_clipboard_content()
    def _handle_audio_vol_up(self, cmd): return self.volume_up()
    def _handle_audio_vol_down(self, cmd): return self.volume_down()
    def _handle_audio_mute(self, cmd): return self.toggle_mute()
    def _handle_media_toggle(self, cmd): return self.media_play_pause()
    def _handle_media_next(self, cmd): return self.media_next()
    def _handle_media_prev(self, cmd): return self.media_previous()
    def _handle_monitor_proc(self, cmd): return self.list_running_processes()
    def _handle_monitor_mem(self, cmd): return self.get_memory_usage()
    def _handle_monitor_cpu(self, cmd): return self.get_cpu_usage()
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            info = {
                "success": True,
                "system": {
                    "os": self.system_info["os"],
                    "version": self.system_info["version"],
                    "machine": self.system_info["machine"],
                    "processor": self.system_info["processor"],
                    "cpu_cores": psutil.cpu_count(logical=False),
                    "logical_cores": psutil.cpu_count(logical=True),
                    "cpu_usage": f"{cpu_percent}%"
                },
                "memory": {
                    "total": f"{memory.total // (1024**3)} GB",
                    "available": f"{memory.available // (1024**3)} GB",
                    "used": f"{memory.used // (1024**3)} GB",
                    "percentage": f"{memory.percent}%"
                },
                "disk": {
                    "total": f"{disk.total // (1024**3)} GB",
                    "free": f"{disk.free // (1024**3)} GB",
                    "used": f"{disk.used // (1024**3)} GB",
                    "percentage": f"{(disk.used/disk.total)*100:.1f}%"
                }
            }
            return info
        except Exception as e:
            return {"success": False, "error": f"Failed to get system info: {str(e)}"}
    
    def create_folder_from_command(self, command: str) -> Dict[str, Any]:
        """Create folder from natural language command with precise name extraction"""
        try:
            command_lower = command.lower()
            words = command.split()
            
            # Determine target parent directory
            target_parent = Path.home()
            if "desktop" in command_lower:
                target_parent = Path.home() / "Desktop"
            elif "downloads" in command_lower:
                target_parent = Path.home() / "Downloads"
            elif "documents" in command_lower:
                target_parent = Path.home() / "Documents"
            
            # Fallback to home if specialized folder doesn't exist
            if not target_parent.exists():
                target_parent = Path.home()

            folder_name = ""
            
            # Pattern 1: "... named [Name]" or "... called [Name]"
            if "named " in command_lower:
                idx = command_lower.rfind("named ") + 6
                folder_name = command[idx:].strip()
            elif "called " in command_lower:
                idx = command_lower.rfind("called ") + 7
                folder_name = command[idx:].strip()
            
            # Pattern 2: "create folder [Name] on ..." or "create [Name] folder"
            if not folder_name:
                # Look for text between 'folder' and 'on' OR after 'folder'
                if "folder" in command_lower:
                    parts = command_lower.split("folder")
                    after_folder = command[len(parts[0])+6:].strip()
                    
                    if " on " in after_folder.lower():
                        folder_name = after_folder[:after_folder.lower().find(" on ")].strip()
                    else:
                        folder_name = after_folder
            
            # Clean up punctuation from the end (common in speech)
            if folder_name.endswith(('.', '!', '?')):
                folder_name = folder_name[:-1]
            
            if not folder_name or folder_name.lower() in ["desktop", "downloads", "documents"]:
                folder_name = "NewFolder"
            
            folder_path = target_parent / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "message": f"Successfully initialized protocol: Folder '{folder_name}' created at {target_parent}.",
                "path": str(folder_path),
                "folder_name": folder_name
            }
        except Exception as e:
            return {"success": False, "error": f"Folder creation protocol failed: {str(e)}"}
    
    def list_files_from_command(self, command: str) -> Dict[str, Any]:
        """List files in directory from command"""
        try:
            # Determine which directory to list
            if "desktop" in command.lower():
                path = Path.home() / "Desktop"
            elif "downloads" in command.lower():
                path = Path.home() / "Downloads"
            elif "documents" in command.lower():
                path = Path.home() / "Documents"
            else:
                path = Path.cwd()  # Current directory
            
            if not path.exists():
                return {"success": False, "error": f"Directory not found: {path}"}
            
            files = []
            folders = []
            
            for item in path.iterdir():
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "size": item.stat().st_size,
                        "type": "file"
                    })
                elif item.is_dir():
                    folders.append({
                        "name": item.name,
                        "type": "folder"
                    })
            
            return {
                "success": True,
                "path": str(path),
                "folders": folders,
                "files": files,
                "total_items": len(files) + len(folders)
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to list files: {str(e)}"}
    
    def open_application_from_command(self, command: str) -> Dict[str, Any]:
        """Open application from natural language command"""
        try:
            command_lower = command.lower()
            words = command.split()
            app_name = ""
            
            # Extract application name
            if "open" in command_lower:
                idx = command_lower.split().index("open")
                app_name = " ".join(words[idx+1:])
            elif "launch" in command_lower:
                idx = command_lower.split().index("launch")
                app_name = " ".join(words[idx+1:])
            elif "start" in command_lower:
                idx = command_lower.split().index("start")
                app_name = " ".join(words[idx+1:])
            
            # Clean up app name
            if app_name.lower().startswith("the "):
                app_name = app_name[4:]
            
            if app_name.lower().startswith("application "):
                app_name = app_name[12:]
            elif app_name.lower().startswith("app "):
                app_name = app_name[4:]
            elif app_name.lower().startswith("program "):
                app_name = app_name[8:]
            
            if not app_name:
                return {"success": False, "error": "No application name specified"}
            
            app_to_launch = app_name.strip()
            found_in_map = False
            
            for key, commands in self.app_commands.items():
                if key in app_name.lower():
                    if platform.system() == "Darwin":  # macOS
                        app_to_launch = commands[0]
                    else:
                        app_to_launch = commands[1] if len(commands) > 1 else commands[0]
                    found_in_map = True
                    break
            
            # If not found in map, try to use the name as is (capitalized for macOS)
            if not found_in_map and platform.system() == "Darwin":
                # Capitalize first letter of each word for better chance of matching
                app_to_launch = app_name.title()
            
            if platform.system() == "Darwin":
                subprocess.run(["open", "-a", app_to_launch], check=True)
            elif platform.system() == "Windows":
                subprocess.run(["start", app_to_launch], shell=True, check=True)
            else:  # Linux
                subprocess.run([app_to_launch], check=True)
            
            return {
                "success": True,
                "message": f"Opened {app_to_launch}",
                "application": app_to_launch
            }
        except subprocess.CalledProcessError:
            return {"success": False, "error": f"Failed to open application: {app_name}"}
        except Exception as e:
            return {"success": False, "error": f"Error opening application: {str(e)}"}
    
    def take_screenshot(self) -> Dict[str, Any]:
        """Take a screenshot and save it"""
        try:
            desktop_path = Path.home() / "Desktop"
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            screenshot_path = desktop_path / f"screenshot_{timestamp}.png"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
            
            return {
                "success": True,
                "message": f"Screenshot saved to {screenshot_path}",
                "path": str(screenshot_path)
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to take screenshot: {str(e)}"}
    
    def open_website_from_command(self, command: str) -> Dict[str, Any]:
        """Open website from natural language command"""
        try:
            # Extract URL from command
            words = command.split()
            url = ""
            
            for word in words:
                if "." in word and any(tld in word for tld in [".com", ".org", ".net", ".edu", ".gov"]):
                    url = word
                    break
            
            if not url:
                return {"success": False, "error": "No valid URL found in command"}
            
            # Add https:// if not present
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            
            webbrowser.open(url)
            
            return {
                "success": True,
                "message": f"Opened website: {url}",
                "url": url
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to open website: {str(e)}"}
    
    def google_search_from_command(self, command: str) -> Dict[str, Any]:
        """Perform Google search from command"""
        try:
            # Extract search query
            command_lower = command.lower()
            if "search google for" in command_lower:
                query = command[command_lower.find("search google for") + 17:].strip()
            elif "google search" in command_lower:
                query = command[command_lower.find("google search") + 13:].strip()
            else:
                return {"success": False, "error": "No search query found"}
            
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            
            return {
                "success": True,
                "message": f"Searching Google for: {query}",
                "query": query,
                "url": search_url
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to perform Google search: {str(e)}"}
    
    def copy_to_clipboard_from_command(self, command: str) -> Dict[str, Any]:
        """Copy text to clipboard from command"""
        try:
            # Extract text after "copy"
            words = command.split()
            if "copy" in [w.lower() for w in words]:
                idx = next(i for i, w in enumerate(words) if w.lower() == "copy")
                text_to_copy = " ".join(words[idx+1:])
            else:
                text_to_copy = command
            
            pyperclip.copy(text_to_copy)
            
            return {
                "success": True,
                "message": f"Copied to clipboard: {text_to_copy}",
                "text": text_to_copy
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to copy to clipboard: {str(e)}"}
    
    def paste_from_clipboard(self) -> Dict[str, Any]:
        """Paste from clipboard"""
        try:
            clipboard_content = pyperclip.paste()
            pyautogui.hotkey('cmd', 'v') if platform.system() == "Darwin" else pyautogui.hotkey('ctrl', 'v')
            
            return {
                "success": True,
                "message": "Pasted from clipboard",
                "content": clipboard_content
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to paste from clipboard: {str(e)}"}
    
    def get_clipboard_content(self) -> Dict[str, Any]:
        """Get current clipboard content"""
        try:
            content = pyperclip.paste()
            return {
                "success": True,
                "content": content,
                "length": len(content)
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get clipboard content: {str(e)}"}
    
    def volume_up(self) -> Dict[str, Any]:
        """Increase system volume"""
        try:
            if platform.system() == "Darwin":
                # Use AppleScript for macOS
                script = "set volume output volume (output volume of (get volume settings) + 10)"
                subprocess.run(["osascript", "-e", script])
            elif platform.system() == "Windows":
                pyautogui.press('volumeup')
            else:
                subprocess.run(["amixer", "set", "Master", "5%+"], check=True)
            
            return {"success": True, "message": "Volume increased"}
        except Exception as e:
            return {"success": False, "error": f"Failed to increase volume: {str(e)}"}
    
    def volume_down(self) -> Dict[str, Any]:
        """Decrease system volume"""
        try:
            if platform.system() == "Darwin":
                # Use AppleScript for macOS
                script = "set volume output volume (output volume of (get volume settings) - 10)"
                subprocess.run(["osascript", "-e", script])
            elif platform.system() == "Windows":
                pyautogui.press('volumedown')
            else:
                subprocess.run(["amixer", "set", "Master", "5%-"], check=True)
            
            return {"success": True, "message": "Volume decreased"}
        except Exception as e:
            return {"success": False, "error": f"Failed to decrease volume: {str(e)}"}
    
    def toggle_mute(self) -> Dict[str, Any]:
        """Toggle system mute"""
        try:
            if platform.system() == "Darwin":
                # Use AppleScript for macOS
                script = "set volume output muted not (output muted of (get volume settings))"
                subprocess.run(["osascript", "-e", script])
            elif platform.system() == "Windows":
                pyautogui.press('volumemute')
            else:
                subprocess.run(["amixer", "set", "Master", "toggle"], check=True)
            
            return {"success": True, "message": "Volume mute toggled"}
        except Exception as e:
            return {"success": False, "error": f"Failed to toggle mute: {str(e)}"}

    def media_play_pause(self) -> Dict[str, Any]:
        """Toggle media play/pause"""
        try:
            if platform.system() == "Darwin":
                # Use AppleScript key code 100 (F8/Play/Pause)
                subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 100'])
            else:
                pyautogui.press('playpause')
            return {"success": True, "message": "Toggled media play/pause"}
        except Exception as e:
            return {"success": False, "error": f"Failed to toggle media: {str(e)}"}

    def media_next(self) -> Dict[str, Any]:
        """Skip to next track"""
        try:
            if platform.system() == "Darwin":
                # Use AppleScript key code 101 (F9/Next)
                subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 101'])
            else:
                pyautogui.press('nexttrack')
            return {"success": True, "message": "Skipped to next track"}
        except Exception as e:
            return {"success": False, "error": f"Failed to skip track: {str(e)}"}

    def media_previous(self) -> Dict[str, Any]:
        """Go to previous track"""
        try:
            if platform.system() == "Darwin":
                # Use AppleScript key code 98 (F7/Previous)
                subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 98'])
            else:
                pyautogui.press('prevtrack')
            return {"success": True, "message": "Went to previous track"}
        except Exception as e:
            return {"success": False, "error": f"Failed to go to previous track: {str(e)}"}
    
    def list_running_processes(self) -> Dict[str, Any]:
        """List currently running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage
            processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:10]
            
            return {
                "success": True,
                "processes": processes,
                "total_processes": len(processes)
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to list processes: {str(e)}"}
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage"""
        try:
            memory = psutil.virtual_memory()
            return {
                "success": True,
                "memory": {
                    "total": f"{memory.total // (1024**3)} GB",
                    "available": f"{memory.available // (1024**3)} GB",
                    "used": f"{memory.used // (1024**3)} GB",
                    "percentage": f"{memory.percent}%"
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get memory usage: {str(e)}"}
    
    def get_cpu_usage(self) -> Dict[str, Any]:
        """Get current CPU usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            avg_cpu = sum(cpu_percent) / len(cpu_percent)
            
            return {
                "success": True,
                "cpu": {
                    "average": f"{avg_cpu:.1f}%",
                    "per_core": [f"{cpu:.1f}%" for cpu in cpu_percent],
                    "cores": len(cpu_percent)
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get CPU usage: {str(e)}"}
    
    def minimize_windows(self) -> Dict[str, Any]:
        """Minimize current window"""
        try:
            if platform.system() == "Darwin":
                # Use AppleScript to minimize the frontmost window
                script = '''
                tell application "System Events"
                    set frontProcess to first process whose frontmost is true
                    tell frontProcess
                        set value of attribute "AXMinimized" of window 1 to true
                    end tell
                end tell
                '''
                subprocess.run(["osascript", "-e", script])
            elif platform.system() == "Windows":
                pyautogui.hotkey('win', 'down') # Minimize current window
            else:
                pyautogui.hotkey('ctrl', 'alt', 'd')
            
            return {"success": True, "message": "Minimized window"}
        except Exception as e:
            return {"success": False, "error": f"Failed to minimize window: {str(e)}"}
    
    def maximize_window(self) -> Dict[str, Any]:
        """Maximize current window"""
        try:
            if platform.system() == "Darwin":
                # Use AppleScript to toggle Full Screen
                script = '''
                tell application "System Events"
                    set frontProcess to first process whose frontmost is true
                    tell frontProcess
                        set value of attribute "AXFullScreen" of window 1 to not (value of attribute "AXFullScreen" of window 1)
                    end tell
                end tell
                '''
                subprocess.run(["osascript", "-e", script])
            elif platform.system() == "Windows":
                pyautogui.hotkey('win', 'up')
            else:
                pyautogui.hotkey('alt', 'f10')
            
            return {"success": True, "message": "Maximized window"}
        except Exception as e:
            return {"success": False, "error": f"Failed to maximize window: {str(e)}"}
    
    def delete_file_from_command(self, command: str) -> Dict[str, Any]:
        """Delete file from natural language command"""
        try:
            # Extract filename from command
            words = command.split()
            filename = ""
            
            if "delete" in [w.lower() for w in words]:
                idx = next(i for i, w in enumerate(words) if w.lower() == "delete")
                filename = " ".join(words[idx+1:])
            elif "remove" in [w.lower() for w in words]:
                idx = next(i for i, w in enumerate(words) if w.lower() == "remove")
                filename = " ".join(words[idx+1:])
            
            # Remove "file" if it's the first word of filename
            if filename.lower().startswith("file "):
                filename = filename[5:]
            
            if not filename:
                return {"success": False, "error": "No filename specified"}
            
            # Look for file in common locations
            search_paths = [
                Path.home() / "Desktop",
                Path.home() / "Downloads",
                Path.home() / "Documents",
                Path.cwd()
            ]
            
            file_path = None
            for search_path in search_paths:
                potential_path = search_path / filename
                if potential_path.exists():
                    file_path = potential_path
                    break
            
            if not file_path:
                return {"success": False, "error": f"File not found: {filename}"}
            
            file_path.unlink()  # Delete the file
            
            return {
                "success": True,
                "message": f"Deleted file: {file_path}",
                "path": str(file_path)
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to delete file: {str(e)}"}
    
    def copy_file_from_command(self, command: str) -> Dict[str, Any]:
        """Copy file from natural language command"""
        try:
            # This is a simplified implementation
            # In a real scenario, you'd want more sophisticated parsing
            words = command.split()
            if len(words) < 3:
                return {"success": False, "error": "Copy command requires source and destination"}
            
            # Extract source and destination
            copy_idx = next(i for i, w in enumerate(words) if w.lower() == "copy")
            source = words[copy_idx + 1] if len(words) > copy_idx + 1 else ""
            dest = words[copy_idx + 2] if len(words) > copy_idx + 2 else ""
            
            if not source or not dest:
                return {"success": False, "error": "Source or destination not specified"}
            
            shutil.copy2(source, dest)
            
            return {
                "success": True,
                "message": f"Copied {source} to {dest}",
                "source": source,
                "destination": dest
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to copy file: {str(e)}"}
    
    def move_file_from_command(self, command: str) -> Dict[str, Any]:
        """Move/rename file from natural language command"""
        try:
            words = command.split()
            if len(words) < 3:
                return {"success": False, "error": "Move command requires source and destination"}
            
            # Extract source and destination
            move_idx = next(i for i, w in enumerate(words) if w.lower() in ["move", "rename"])
            source = words[move_idx + 1] if len(words) > move_idx + 1 else ""
            dest = words[move_idx + 2] if len(words) > move_idx + 2 else ""
            
            if not source or not dest:
                return {"success": False, "error": "Source or destination not specified"}
            
            shutil.move(source, dest)
            
            return {
                "success": True,
                "message": f"Moved {source} to {dest}",
                "source": source,
                "destination": dest
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to move file: {str(e)}"}
    
    def close_application_from_command(self, command: str) -> Dict[str, Any]:
        """Close application from natural language command"""
        try:
            # Extract application name
            words = command.split()
            app_name = ""
            
            if "close" in [w.lower() for w in words]:
                idx = next(i for i, w in enumerate(words) if w.lower() == "close")
                app_name = " ".join(words[idx+1:])
            
            if not app_name:
                return {"success": False, "error": "No application name specified"}
            
            # Find and terminate process
            killed_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if app_name.lower() in proc.info['name'].lower():
                        proc.terminate()
                        killed_processes.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if killed_processes:
                return {
                    "success": True,
                    "message": f"Closed applications: {', '.join(killed_processes)}",
                    "closed_apps": killed_processes
                }
            else:
                return {"success": False, "error": f"Application not found: {app_name}"}
                
        except Exception as e:
            return {"success": False, "error": f"Failed to close application: {str(e)}"}
    
    def get_available_commands(self) -> List[str]:
        """Get list of available PC control commands"""
        return [
            "System Information: 'system info', 'computer info', 'hardware info'",
            "File Operations: 'create folder [name]', 'list files', 'delete file [name]'",
            "Applications: 'open [app]', 'close [app]'", 
            "Web Browsing: 'open website [url]', 'search google for [query]'",
            "Screenshots: 'take screenshot', 'capture screen'",
            "Window Control: 'minimize window', 'maximize window'",
            "Clipboard: 'copy text [text]', 'paste text', 'show clipboard'",
            "Volume Control: 'volume up', 'volume down', 'mute'",
            "Media Control: 'play music', 'next track', 'previous track'",
            "System Monitoring: 'running processes', 'memory usage', 'cpu usage'"
        ]