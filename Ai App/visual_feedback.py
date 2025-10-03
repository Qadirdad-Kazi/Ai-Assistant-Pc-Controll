"""
Visual Feedback Module
Handles on-screen visual feedback for user actions
"""
import os
import time
import tempfile
import subprocess
import platform
import threading
from PIL import Image, ImageDraw, ImageFont

try:
    import pyautogui
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

class VisualFeedback:
    def __init__(self, enabled=True):
        """
        Initialize the visual feedback system
        
        Args:
            enabled (bool): Whether visual feedback is enabled
        """
        self.enabled = enabled and GUI_AVAILABLE
        self.feedback_thread = None
    
    def show_message(self, message, duration=2):
        """
        Show a visual feedback message on screen
        
        Args:
            message (str): Message to display
            duration (int): How long to show the message in seconds
        """
        if not self.enabled:
            return
            
        def show():
            try:
                # Create a semi-transparent overlay
                screen_width, screen_height = pyautogui.size()
                img = Image.new('RGBA', (screen_width, 100), (0, 0, 0, 180))
                draw = ImageDraw.Draw(img)
                
                # Try to use a nice font, fall back to default if not available
                try:
                    font = ImageFont.truetype("Arial", 24)
                except:
                    font = ImageFont.load_default()
                
                # Calculate text size and position
                text_bbox = draw.textbbox((0, 0), message, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                x = (screen_width - text_width) // 2
                y = (100 - text_height) // 2
                
                # Draw text with a slight shadow for better visibility
                draw.text((x+1, y+1), message, fill=(0, 0, 0), font=font)
                draw.text((x, y), message, fill=(255, 255, 255), font=font)
                
                # Save to a temporary file and display
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    img_path = tmp.name
                    img.save(img_path)
                    
                    # Show the image using the default image viewer
                    if platform.system() == 'Darwin':  # macOS
                        subprocess.run(['open', img_path])
                    elif platform.system() == 'Windows':
                        os.startfile(img_path)
                    else:  # Linux and others
                        subprocess.run(['xdg-open', img_path])
                    
                    # Schedule removal of the temp file
                    def remove_temp():
                        time.sleep(duration)
                        try:
                            if os.path.exists(img_path):
                                os.remove(img_path)
                        except:
                            pass
                    
                    threading.Thread(target=remove_temp, daemon=True).start()
                    
            except Exception as e:
                print(f"Error showing visual feedback: {e}")
        
        # Run in a separate thread to not block
        self.feedback_thread = threading.Thread(target=show, daemon=True)
        self.feedback_thread.start()
        
    def set_enabled(self, enabled):
        """Enable or disable visual feedback"""
        self.enabled = enabled and GUI_AVAILABLE
