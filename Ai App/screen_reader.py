"""
Screen Reader Module
Handles continuous screen reading and content analysis
"""
import time
import threading
import pytesseract
from PIL import ImageGrab
from queue import Queue

class ScreenReader:
    def __init__(self, update_interval=2.0):
        """
        Initialize the screen reader
        
        Args:
            update_interval (float): How often to read the screen (in seconds)
        """
        self.update_interval = update_interval
        self.is_running = False
        self.is_paused = False
        self.last_content = ""
        self.callback = None
        self.thread = None
        self.content_queue = Queue()
        
        # Configure Tesseract path if needed (for Windows)
        if platform.system() == 'Windows':
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def start(self, callback=None):
        """
        Start the screen reader
        
        Args:
            callback (callable): Function to call with screen content updates
        """
        if self.is_running:
            return False
            
        self.callback = callback
        self.is_running = True
        self.is_paused = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return True
    
    def pause(self):
        """Pause the screen reader"""
        self.is_paused = True
    
    def resume(self):
        """Resume the screen reader"""
        self.is_paused = False
    
    def stop(self):
        """Stop the screen reader"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
    
    def _run(self):
        """Main screen reading loop"""
        while self.is_running:
            if not self.is_paused:
                try:
                    # Capture screen and extract text
                    screenshot = ImageGrab.grab()
                    text = pytesseract.image_to_string(screenshot)
                    text = text.strip()
                    
                    # Only process if content changed
                    if text and text != self.last_content:
                        self.last_content = text
                        if self.callback:
                            self.callback({
                                'content': text,
                                'timestamp': time.time(),
                                'type': 'screen_content'
                            })
                except Exception as e:
                    print(f"Screen reading error: {e}")
            
            # Wait for the next update interval
            time.sleep(self.update_interval)
    
    def get_latest_content(self):
        """Get the most recent screen content"""
        return self.last_content
    
    def is_active(self):
        """Check if the screen reader is running and not paused"""
        return self.is_running and not self.is_paused
