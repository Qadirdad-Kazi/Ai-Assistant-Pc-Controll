"""
Holographic System Dashboard for Wolf AI (Simplified God-Mode).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGraphicsDropShadowEffect, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QDate, QTime, Signal, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap

from qfluentwidgets import (
    StrongBodyLabel, FluentIcon as FIF, IconWidget, CardWidget
)

from datetime import datetime

# --- Theme Constants ---
THEME_BG = "#05080d"
THEME_GLASS = "rgba(16, 24, 40, 0.70)"
THEME_BORDER = "rgba(76, 201, 240, 0.3)"
THEME_ACCENT = "#4cc9f0"
THEME_TEXT_MAIN = "#e8f1ff"
THEME_TEXT_SUB = "#94a3b8"
THEME_LISTENING = "#ff007b" # Vibrant pink/red when listening

class GlowEffect(QGraphicsDropShadowEffect):
    def __init__(self, color=THEME_ACCENT, blur=15, parent=None):
        super().__init__(parent)
        self.setBlurRadius(blur)
        self.setColor(QColor(color))
        self.setOffset(0, 0)

class GreetingsHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 20)
        
        text_container = QFrame()
        tc_layout = QVBoxLayout(text_container)
        tc_layout.setContentsMargins(0,0,0,0)
        tc_layout.setSpacing(0)
        
        self.status_lbl = QLabel("// SYSTEM ONLINE")
        self.status_lbl.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 14px; letter-spacing: 2px; color: {THEME_ACCENT}; font-weight: bold;")
        
        self.main_title = QLabel("COMMANDER")
        self.main_title.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 48px; font-weight: 800; color: {THEME_TEXT_MAIN};")
        self.main_title.setGraphicsEffect(GlowEffect(THEME_ACCENT, 20))
        
        self.date_lbl = QLabel()
        self.date_lbl.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 16px; font-family: 'Consolas', monospace;")
        
        tc_layout.addWidget(self.status_lbl)
        tc_layout.addWidget(self.main_title)
        tc_layout.addWidget(self.date_lbl)
        
        self.layout.addWidget(text_container)
        self.layout.addStretch()
        
        # Clock Section
        self.clock_lbl = QLabel("--:--")
        self.clock_lbl.setStyleSheet(f"font-family: 'Consolas', monospace; font-size: 32px; font-weight: bold; color: {THEME_TEXT_MAIN};")
        self.layout.addWidget(self.clock_lbl)

        self._update_time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)

    def _update_time(self):
        now = datetime.now()
        self.date_lbl.setText(QDate.currentDate().toString("yyyy.MM.dd | dddd").upper())
        self.clock_lbl.setText(QTime.currentTime().toString("HH:mm:ss"))
        
        hour = now.hour
        if 5 <= hour < 12: greeting = "MORNING ADVISOR"
        elif 12 <= hour < 18: greeting = "AFTERNOON PROTOCOL"
        else: greeting = "EVENING SECURITY"
        self.status_lbl.setText(f"// {greeting} ACTIVE")

class StatusCard(CardWidget):
    def __init__(self, icon, title, status, color=THEME_ACCENT, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 100)
        self.setStyleSheet(f"""
            CardWidget {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        
        iw = IconWidget(icon)
        iw.setFixedSize(32, 32)
        layout.addWidget(iw)
        
        info = QVBoxLayout()
        t = StrongBodyLabel(title.upper())
        t.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 10px; letter-spacing: 1px;")
        self.s = QLabel(status)
        self.s.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        
        info.addWidget(t)
        info.addWidget(self.s)
        layout.addLayout(info)
        layout.addStretch()

    def set_status(self, text):
        self.s.setText(text)

class DashboardView(QWidget):
    navigate_to = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardInterface")
        
        # Load the generated background image
        import os
        bg_path = os.path.join(os.getcwd(), "dashboard_bg.png")
        self.bg_pixmap = QPixmap(bg_path)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        self.header = GreetingsHeader()
        main_layout.addWidget(self.header)
        
        # Status Grid
        grid = QGridLayout()
        grid.setSpacing(20)
        
        self.voice_card = StatusCard(FIF.MICROPHONE, "Voice Core", "LISTENING", THEME_ACCENT)
        self.pc_card = StatusCard(FIF.LAYOUT, "System Control", "READY", "#00ff9d")
        self.media_card = StatusCard(FIF.MUSIC, "Neural Sonic", "STANDBY", "#ff007b")
        self.dev_card = StatusCard(FIF.CODE, "Dev Agent", "IDLE", "#7d2ae8")
        
        grid.addWidget(self.voice_card, 0, 0)
        grid.addWidget(self.pc_card, 0, 1)
        grid.addWidget(self.media_card, 1, 0)
        grid.addWidget(self.dev_card, 1, 1)
        
        main_layout.addLayout(grid)
        
        # Large Mission Message / Listening UI Container
        self.center_container = QWidget()
        self.center_layout = QVBoxLayout(self.center_container)
        
        self.mission_lbl = QLabel("WOLF AI IS READY FOR ASSIGNMENT.")
        self.mission_lbl.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 18px; color: {THEME_TEXT_SUB}; font-style: italic;")
        self.mission_lbl.setAlignment(Qt.AlignCenter)
        
        self.listening_lbl = QLabel("🎙️ LISTENING...")
        self.listening_lbl.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 42px; font-weight: 900; color: {THEME_LISTENING}; letter-spacing: 12px;")
        self.listening_lbl.setAlignment(Qt.AlignCenter)
        self.listening_lbl.hide()
        
        # Audio Pulse Glow Effect
        self.listening_glow = GlowEffect(THEME_LISTENING, 40)
        self.listening_lbl.setGraphicsEffect(self.listening_glow)
        
        self.center_layout.addWidget(self.mission_lbl)
        self.center_layout.addWidget(self.listening_lbl)
        
        main_layout.addStretch()
        main_layout.addWidget(self.center_container)
        main_layout.addStretch()

    def set_listening(self, is_listening: bool):
        """Toggle the central dashboard listening mode UI."""
        if is_listening:
            self.mission_lbl.hide()
            self.listening_lbl.show()
            self.voice_card.set_status("ACTIVE")
            self.voice_card.s.setStyleSheet(f"color: {THEME_LISTENING}; font-size: 18px; font-weight: bold;")
        else:
            self.listening_lbl.hide()
            self.mission_lbl.show()
            self.voice_card.set_status("LISTENING")
            self.voice_card.s.setStyleSheet(f"color: {THEME_ACCENT}; font-size: 18px; font-weight: bold;")

    def paintEvent(self, event):
        """Draw the generated Wolf Couples image in the background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        if not hasattr(self, 'bg_pixmap') or self.bg_pixmap.isNull():
            return
            
        scaled_pixmap = self.bg_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        x = (self.width() - scaled_pixmap.width()) // 2
        y = (self.height() - scaled_pixmap.height()) // 2
        
        # Make it subtle so it feels immersive but professional
        painter.setOpacity(0.35) 
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.setOpacity(1.0)
