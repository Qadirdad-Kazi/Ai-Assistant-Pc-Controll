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

try:
    import pytesseract
    from PIL import Image
    # Windows default Tesseract path (user may need to install tesseract-ocr)
    pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
except ImportError:
    pytesseract = None

class BugWatcher:
    """Watches the screen asynchronously via OCR to pre-emptively detect bugs."""
    def __init__(self):
        self.interval = 10 # Scan every 10 seconds
        self.running = False
        self._thread = None
        
        # Keywords to look for
        self.alert_keywords = ["exception", "traceback (most recent call last)", "fatal error", "syntaxerror", "referenceerror", "typeerror"]
        
        # To avoid spamming the same error
        self.last_alerted_text = ""
        
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
            if pyautogui and pytesseract:
                try:
                    # 1. Capture the screen
                    screenshot = pyautogui.screenshot()
                    
                    # 2. Extract text (using fast/sparse OCR parameters)
                    # --psm 11 looks for sparse text, which is faster than full page layouts
                    ocr_text = pytesseract.image_to_string(screenshot, config='--psm 11').lower()
                    
                    # 3. Analyze text for crash signatures
                    detected_error = None
                    for keyword in self.alert_keywords:
                        if keyword in ocr_text:
                            detected_error = keyword
                            break
                    
                    if detected_error:
                        # Extract a snippet around the error to show in HUD
                        start_idx = ocr_text.find(detected_error)
                        snippet = ocr_text[max(0, start_idx-20):min(len(ocr_text), start_idx+60)].replace('\\n', ' ').strip()
                        
                        if snippet != self.last_alerted_text:
                            self.last_alerted_text = snippet
                            print(f"[Proactive Layer] 🔥 CRASH DETECTED ON SCREEN: {detected_error.upper()}")
                            print(f"Context: {snippet}")
                            
                            # Trigger HUD if initialized
                            try:
                                from gui.windows.hud_window import hud_window
                                if hud_window:
                                    hud_window.show_alert(f"BUG DETECTED: {detected_error.upper()}")
                            except Exception:
                                pass
                            
                except Exception as e:
                    # Might happen if Tesseract isn't installed properly in Windows
                    print(f"[Proactive Layer] OCR Error: {e}")
                    time.sleep(30) # Wait longer before trying again if broken
            
            time.sleep(self.interval)

# Singleton
bug_watcher = BugWatcher()
