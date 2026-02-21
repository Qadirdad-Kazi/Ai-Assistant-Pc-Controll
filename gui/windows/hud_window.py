from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter

class TransparentHUD(QWidget):
    """
    A transparent overlay UI that lives on top of the screen.
    Displays Proactive alerts and Visual Feedback (e.g. Ghostly highlights).
    """
    def __init__(self):
        super().__init__()
        # Set window flags for transparent, always-on-top, click-through overlay
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool | 
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Determine screen geometry to cover the whole screen
        self.setGeometry(0, 0, 1920, 1080) # Normally use desktop() geometry
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Test Alert Label
        self.alert_label = QLabel("PROACTIVE LAYER: NO ISSUES")
        self.alert_label.setStyleSheet("color: rgba(76, 201, 240, 0.8); font-size: 24px; font-weight: bold; background: rgba(10, 15, 30, 0.5); border-radius: 8px; padding: 10px;")
        self.alert_label.setAlignment(Qt.AlignTop | Qt.AlignRight)
        
        layout.addWidget(self.alert_label, alignment=Qt.AlignTop | Qt.AlignRight)
        
        # Fade out timer placeholder
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self._fade_out)
        self.opacity = 1.0

    def show_alert(self, text: str):
        self.alert_label.setText(text)
        self.opacity = 1.0
        self.alert_label.setStyleSheet("color: rgba(255, 50, 50, 0.9); font-size: 24px; font-weight: bold; background: rgba(20, 0, 0, 0.6); border-radius: 8px; padding: 10px;")
        self.show()
        # Ensure it stats on top
        self.raise_()
        self.fade_timer.start(5000) # Hide after 5 seconds
        
    def _fade_out(self):
        self.hide()
        self.fade_timer.stop()
        
# Global reference to HUD
hud_window = None

def init_hud():
    global hud_window
    if hud_window is None:
        hud_window = TransparentHUD()
        hud_window.show()
