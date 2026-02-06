import os
import shutil
import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PySide6.QtCore import QObject, Signal

class JanitorHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            self.callback(event.src_path)

class DigitalJanitor(QObject):
    """
    Digital Janitor: Background agent that organizes files.
    """
    file_organized = Signal(str, str) # Original path, New path
    
    def __init__(self, settings_file="data/janitor_settings.json"):
        super().__init__()
        self.settings_file = settings_file
        self.rules = self._load_settings()
        self.observer = None
        self.running = False

    def _load_settings(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    return json.load(f)
            except:
                pass
        
        # Default rules
        return {
            "watch_path": os.path.expanduser("~/Downloads"),
            "destinations": {
                ".pdf": os.path.expanduser("~/Documents/PDFs"),
                ".zip": os.path.expanduser("~/Downloads/Archives"),
                ".exe": os.path.expanduser("~/Downloads/Installers"),
                ".msi": os.path.expanduser("~/Downloads/Installers"),
                ".py": os.path.expanduser("~/Development/Scripts"),
                ".jpg": os.path.expanduser("~/Pictures/Saved"),
                ".png": os.path.expanduser("~/Pictures/Saved")
            },
            "enabled": False
        }

    def save_settings(self, rules):
        self.rules = rules
        with open(self.settings_file, "w") as f:
            json.dump(rules, f, indent=4)
        if self.running:
            self.stop()
            self.start()

    def start(self):
        if not self.rules.get("enabled"):
            return
            
        watch_path = self.rules.get("watch_path")
        if not os.path.exists(watch_path):
            return

        self.observer = Observer()
        self.observer.schedule(JanitorHandler(self.handle_file), watch_path, recursive=False)
        self.observer.start()
        self.running = True
        print(f"[Janitor] Started watching: {watch_path}")

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.running = False
        print("[Janitor] Stopped.")

    def handle_file(self, src_path):
        """Analyze and move file."""
        # Wait a bit for the file write to complete
        time.sleep(1)
        
        ext = os.path.splitext(src_path)[1].lower()
        dest_dir = self.rules.get("destinations", {}).get(ext)
        
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
            filename = os.path.basename(src_path)
            dest_path = os.path.join(dest_dir, filename)
            
            try:
                # Use shutil.move
                shutil.move(src_path, dest_path)
                self.file_organized.emit(src_path, dest_path)
                print(f"[Janitor] Moved {filename} to {dest_dir}")
            except Exception as e:
                print(f"[Janitor] Error moving {src_path}: {e}")
