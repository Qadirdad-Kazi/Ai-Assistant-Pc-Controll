"""
Voice Listening Indicator - Visual cue when wake word is detected and AI is listening.
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QPoint
from PySide6.QtGui import QFont, QPainter, QColor, QBrush, QPen


class VoiceIndicator(QWidget):
    """Animated voice listening indicator that appears when wake word is detected."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.is_listening = False
        self.pulse_animation = None
        self.opacity_effect = None
        
        self._setup_ui()
        self._setup_animations()
        self.hide()
    
    def _setup_ui(self):
        """Setup the indicator UI."""
        self.setFixedSize(200, 200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        # Main container widget for custom painting
        self.container = QWidget(self)
        self.container.setFixedSize(200, 200)
        layout.addWidget(self.container)
        
        # Text label
        self.text_label = QLabel("Listening...", self)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.text_label.setStyleSheet("""
            QLabel {
                color: #33b5e5;
                background: transparent;
                padding: 8px;
                margin-top: 10px;
            }
        """)
        layout.addWidget(self.text_label)
        
        # Set overall styling
        self.setStyleSheet("""
            VoiceIndicator {
                background: transparent;
            }
        """)
    
    def _setup_animations(self):
        """Setup pulse and fade animations."""
        # Opacity effect for fade in/out
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Fade in animation
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)
        
        # Fade out animation
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out.finished.connect(self._on_fade_out_finished)
        
        # Pulse animation for the circle
        self.pulse_value = 0.0
        self.pulse_animation = QPropertyAnimation(self, b"pulseValue")
        self.pulse_animation.setDuration(1500)
        self.pulse_animation.setStartValue(0.0)
        self.pulse_animation.setEndValue(1.0)
        self.pulse_animation.setLoopCount(-1)  # Infinite loop
        self.pulse_animation.setEasingCurve(QEasingCurve.InOutSine)
    
    def paintEvent(self, event):
        """Custom paint event to draw animated pulsing circle."""
        if not self.is_listening:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate pulse size
        base_size = 80
        pulse_size = base_size + (self.pulse_value * 40)  # Pulse from 80 to 120
        
        # Calculate center
        center_x = self.width() // 2
        center_y = self.container.height() // 2
        
        # Draw outer pulse ring (fading)
        pulse_alpha = int(255 * (1 - self.pulse_value))
        pulse_color = QColor(51, 181, 229, pulse_alpha)  # #33b5e5 with alpha
        painter.setPen(QPen(pulse_color, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(
            QPoint(center_x, center_y),
            int(pulse_size // 2),
            int(pulse_size // 2)
        )
        
        # Draw main circle (solid)
        main_color = QColor(51, 181, 229, 200)  # #33b5e5 with some transparency
        painter.setPen(QPen(main_color, 4))
        painter.setBrush(QBrush(main_color, Qt.SolidPattern))
        painter.drawEllipse(
            QPoint(center_x, center_y),
            int(base_size // 2),
            int(base_size // 2)
        )
        
        # Draw inner dot (microphone icon representation)
        inner_color = QColor(51, 181, 229, 255)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(inner_color, Qt.SolidPattern))
        painter.drawEllipse(
            QPoint(center_x, center_y),
            8,
            8
        )
    
    def get_pulse_value(self):
        """Getter for pulse animation property."""
        return self.pulse_value
    
    def set_pulse_value(self, value):
        """Setter for pulse animation property."""
        self.pulse_value = value
        self.update()  # Trigger repaint
    
    # Create property for animation
    pulseValue = property(get_pulse_value, set_pulse_value)
    
    def show_listening(self):
        """Show the listening indicator."""
        print(f"[VoiceIndicator] show_listening() called, current state: is_listening={self.is_listening}")
        if self.is_listening:
            print(f"[VoiceIndicator] Already listening, skipping")
            return
        
        print(f"[VoiceIndicator] Setting is_listening=True")
        self.is_listening = True
        self._position_window()
        print(f"[VoiceIndicator] Showing widget and starting animations")
        self.show()
        self.fade_in.start()
        if self.pulse_animation:
            self.pulse_animation.start()
        print(f"[VoiceIndicator] ✓ Indicator should now be visible")
    
    def hide_listening(self, delay_ms: int = 500):
        """Hide the listening indicator with optional delay."""
        if not self.is_listening:
            return
        
        # Add a small delay before hiding to make it more visible
        if delay_ms > 0:
            QTimer.singleShot(delay_ms, self._do_hide)
        else:
            self._do_hide()
    
    def _do_hide(self):
        """Actually hide the indicator."""
        if not self.is_listening:
            return
        
        self.is_listening = False
        if self.pulse_animation:
            self.pulse_animation.stop()
        self.fade_out.start()
    
    def _on_fade_out_finished(self):
        """Called when fade out animation completes."""
        self.hide()
        self.pulse_value = 0.0
    
    def _position_window(self):
        """Position the indicator in the center of the parent window."""
        if not self.parent():
            return
        
        parent_rect = self.parent().rect()
        x = (parent_rect.width() - self.width()) // 2
        y = (parent_rect.height() - self.height()) // 2 - 50  # Slightly above center
        self.move(x, y)
    
    def showEvent(self, event):
        """Position window on show."""
        super().showEvent(event)
        self._position_window()
