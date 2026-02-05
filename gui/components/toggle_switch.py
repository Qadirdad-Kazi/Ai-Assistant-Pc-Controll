"""
ToggleSwitch component - Custom iOS-style toggle switch for PySide6.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QPainter, QColor, QPen


class ToggleSwitch(QWidget):
    """Custom toggle switch widget."""
    
    toggled = Signal(bool)
    
    def __init__(self, label: str = "", checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._thumb_position = 1.0 if checked else 0.0
        self._label = label
        
        self.setFixedSize(80 if label else 50, 28)
        self.setCursor(Qt.PointingHandCursor)
        
        self._animation = QPropertyAnimation(self, b"thumb_position")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def get_thumb_position(self):
        return self._thumb_position
    
    def set_thumb_position(self, pos):
        self._thumb_position = pos
        self.update()
    
    thumb_position = Property(float, get_thumb_position, set_thumb_position)
    
    def isChecked(self):
        return self._checked
    
    def setChecked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self._animate_thumb()
            self.toggled.emit(self._checked)
    
    def _animate_thumb(self):
        self._animation.stop()
        self._animation.setStartValue(self._thumb_position)
        self._animation.setEndValue(1.0 if self._checked else 0.0)
        self._animation.start()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dimensions
        track_width = 44
        track_height = 24
        thumb_size = 20
        padding = 2
        
        # Draw label if present
        label_offset = 0
        if self._label:
            painter.setPen(QColor("#9e9e9e"))
            painter.drawText(0, 0, 30, 28, Qt.AlignVCenter | Qt.AlignLeft, self._label)
            label_offset = 35
        
        # Track colors
        track_off_color = QColor("#3d3d3d")
        track_on_color = QColor("#4F8EF7")
        
        # Interpolate color based on position
        r = int(track_off_color.red() + (track_on_color.red() - track_off_color.red()) * self._thumb_position)
        g = int(track_off_color.green() + (track_on_color.green() - track_off_color.green()) * self._thumb_position)
        b = int(track_off_color.blue() + (track_on_color.blue() - track_off_color.blue()) * self._thumb_position)
        track_color = QColor(r, g, b)
        
        # Draw track
        track_rect = QRectF(label_offset, 2, track_width, track_height)
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, track_height / 2, track_height / 2)
        
        # Draw thumb
        thumb_x = label_offset + padding + (track_width - thumb_size - padding * 2) * self._thumb_position
        thumb_y = 2 + padding
        thumb_rect = QRectF(thumb_x, thumb_y, thumb_size, thumb_size)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(thumb_rect)
