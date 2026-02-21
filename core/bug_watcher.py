"""
Bug Watcher logic - The Proactive Layer.
Watches the screen in a background thread for application crashes or terminal errors.
"""
import time
import threading
try:
    import pyautogui
except ImportError:
    pyautogui = None

class BugWatcher:
    """Watches the screen asynchronously via OCR/VLM to pre-emptively detect bugs."""
    def __init__(self):
        self.interval = 10 # Scan every 10 seconds
        self.running = False
        self._thread = None
        
    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._scan_loop, daemon=True)
            self._thread.start()
            print("[Proactive Layer] Bug Watcher started. Polling screen...")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
            print("[Proactive Layer] Bug Watcher stopped.")

    def _scan_loop(self):
        while self.running:
            # Logic representing capturing a screenshot in the background
            # Next phase would integrate pytesseract or LLaVA for multi-modal analysis
            if pyautogui:
                # img = pyautogui.screenshot()
                # Run img through OCR or lightweight Vision model
                # if "Exception" in ocr_text or "Error" in ocr_text:
                #     trigger_hud_alert("Potential crash detected.")
                pass
            time.sleep(self.interval)

# Singleton
bug_watcher = BugWatcher()
