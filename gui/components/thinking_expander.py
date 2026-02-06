"""
ThinkingExpander component - Gemini-style collapsible thinking UI for PySide6.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QSizePolicy, QWidget
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QRectF, QPointF
from PySide6.QtGui import QFont, QPainter, QColor

# --- jarvis Knight Theme Constants ---
THEME_GLASS_DARK = "rgba(10, 15, 25, 0.4)" 
THEME_BORDER = "rgba(76, 201, 240, 0.3)" 
THEME_ACCENT = "#4cc9f0"
THEME_TEXT_SUB = "#94a3b8"

class RotatingSpinner(QWidget):
    """A widget that displays a rotating text character."""

    def __init__(self, text="⟳", color=THEME_ACCENT, font_size=12, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self._text = text
        self._color = QColor(color)
        self._font = QFont("Segoe UI", font_size)
        self._angle = 0
        self._animation = None
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def get_angle(self):
        return self._angle

    def set_angle(self, angle):
        self._angle = angle
        self.update()

    angle = Property(float, get_angle, set_angle)

    def start_animation(self):
        if not self._animation:
            self._animation = QPropertyAnimation(self, b"angle", self)
            self._animation.setDuration(1000)
            self._animation.setStartValue(0)
            self._animation.setEndValue(360)
            self._animation.setLoopCount(-1)  # Infinite loop
            self._animation.start()

    def stop_animation(self):
        if self._animation:
            self._animation.stop()
            self._animation = None
        self._angle = 0
        self.update()

    def set_complete(self):
        self.stop_animation()
        self._text = "✓"
        self._color = QColor("#4CAF50")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)
        
        painter.setPen(self._color)
        painter.setFont(self._font)
        
        # Center the text
        rect = QRectF(-self.width() / 2, -self.height() / 2, self.width(), self.height())
        painter.drawText(rect, Qt.AlignCenter, self._text)


class ThinkingExpander(QFrame):
    """Gemini-style collapsible thinking UI."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("thinkingExpander")
        # Default to expanded
        self._is_expanded = True
        self._animation = None
        self._content_height = 0
        
        # Match MessageBubble width constraints
        self.setMaximumWidth(600)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        
        self._setup_ui()
        self._apply_style()
        
        # Start rotating immediately
        self.spinner.start_animation()
        
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header (clickable to expand/collapse)
        self.header = QFrame()
        self.header.setObjectName("thinkingHeader")
        self.header.setCursor(Qt.PointingHandCursor)
        header_layout = QHBoxLayout(self.header)
        # Condensed margins
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(6)
        
        # Rotating Spinner
        self.spinner = RotatingSpinner()
        header_layout.addWidget(self.spinner)
        
        # Title
        self.title_label = QLabel("Thinking...")
        self.title_label.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 11px;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Expand/Collapse arrow
        # Default to expanded arrow
        self.arrow_label = QLabel("▼")
        self.arrow_label.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 9px;")
        header_layout.addWidget(self.arrow_label)
        
        self.main_layout.addWidget(self.header)
        
        # Content container (collapsible)
        self.content_container = QWidget()
        # Default to expanded height
        self.content_container.setMaximumHeight(170)
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(8, 0, 8, 8)
        
        # Thinking log text
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMinimumHeight(60)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(10, 15, 25, 0.4);
                color: {THEME_TEXT_SUB};
                border: 1px solid {THEME_BORDER};
                border-radius: 4px;
                padding: 6px;
                line-height: 120%;
            }}
        """)
        content_layout.addWidget(self.log_text)
        
        self.main_layout.addWidget(self.content_container)
        
        # Connect click event
        self.header.mousePressEvent = self._on_header_click
        
    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#thinkingExpander {{
                background-color: {THEME_GLASS_DARK};
                border: 1px solid {THEME_BORDER};
                border-radius: 6px;
                margin-bottom: 4px;
                margin-top: 4px;
            }}
            QFrame#thinkingHeader {{
                background-color: transparent;
                border-radius: 6px;
                border: none;
            }}
            QFrame#thinkingHeader:hover {{
                background-color: rgba(76, 201, 240, 0.1);
            }}
        """)
        
    def _on_header_click(self, event):
        self.toggle_expanded()
        
    def toggle_expanded(self):
        """Toggle the expanded/collapsed state with animation."""
        self._is_expanded = not self._is_expanded
        
        # Update arrow
        self.arrow_label.setText("▼" if self._is_expanded else "▶")
        
        # Animate content height
        target_height = 170 if self._is_expanded else 0
        
        if self._animation:
            self._animation.stop()
            
        self._animation = QPropertyAnimation(self.content_container, b"maximumHeight", self)
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.setStartValue(self.content_container.maximumHeight())
        self._animation.setEndValue(target_height)
        self._animation.start()
        
    def add_text(self, text: str):
        """Add text to the thinking log."""
        self.log_text.insertPlainText(text)
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def complete(self):
        """Mark thinking as complete."""
        self.spinner.set_complete()
        self.title_label.setText("Thinking Processed")
        self.title_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
