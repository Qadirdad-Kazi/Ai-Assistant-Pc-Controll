from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QListWidgetItem, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from qfluentwidgets import (
    ListWidget, ScrollArea, FluentIcon as FIF, PrimaryPushButton,
    StrongBodyLabel, CaptionLabel
)

THEME_GLASS = "rgba(10, 15, 30, 0.8)"
THEME_BORDER = "rgba(76, 201, 240, 0.3)"
THEME_TEXT_MAIN = "#e8eaed"
THEME_TEXT_SUB = "#8b9bb4"

class CallLogsTab(QWidget):
    """
    Call Logs Tab: Tracks intercepts, phone calls, and transcripts via GSM/SIP.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CallLogsInterface")
        self._setup_ui()

    def _setup_ui(self):
        grid = QVBoxLayout(self)
        grid.setContentsMargins(40, 40, 40, 40)
        grid.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        titles_layout = QVBoxLayout()
        title = QLabel("RECEPTIONIST LOGS")
        title.setStyleSheet(f"font-size: 28px; font-weight: 900; color: {THEME_TEXT_MAIN}; letter-spacing: 4px;")
        subtitle = QLabel("GSM INTERCEPTS & COMMUNICATION TRANSCRIPTS")
        subtitle.setStyleSheet("color: #4cc9f0; font-size: 11px; font-weight: bold; letter-spacing: 2px;")
        titles_layout.addWidget(title)
        titles_layout.addWidget(subtitle)
        header_layout.addLayout(titles_layout)
        header_layout.addStretch()

        self.btn_refresh = PrimaryPushButton(FIF.SYNC, "REFRESH LOGS")
        self.btn_refresh.setFixedSize(160, 36)
        header_layout.addWidget(self.btn_refresh)
        
        grid.addLayout(header_layout)

        # Main Log View container
        log_panel = QFrame()
        log_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(76, 201, 240, 30))
        shadow.setOffset(0,0)
        log_panel.setGraphicsEffect(shadow)

        panel_layout = QVBoxLayout(log_panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        
        # Placeholder for logs
        self.log_list = ListWidget()
        self.log_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                color: {THEME_TEXT_MAIN};
            }}
            QListWidget::item {{
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 5px;
            }}
            QListWidget::item:hover {{
                background: rgba(76, 201, 240, 0.1);
                border-left: 3px solid #4cc9f0;
            }}
        """)
        
        # Add a dummy log
        dummy_item = QListWidgetItem()
        self.log_list.addItem(dummy_item)
        
        dummy_widget = QWidget()
        dummy_layout = QVBoxLayout(dummy_widget)
        dummy_layout.setContentsMargins(0, 0, 0, 0)
        dummy_title = StrongBodyLabel("[GSM GATEWAY] Incoming Call from +923001234567")
        dummy_time = CaptionLabel("Today at 10:45 AM | Duration: 4m 12s | Status: Answered")
        dummy_transcript = CaptionLabel("Transcript: Hello, I would like to book an appointment...")
        dummy_transcript.setStyleSheet(f"color: {THEME_TEXT_SUB};")
        
        dummy_layout.addWidget(dummy_title)
        dummy_layout.addWidget(dummy_time)
        dummy_layout.addWidget(dummy_transcript)
        
        dummy_item.setSizeHint(dummy_widget.sizeHint())
        self.log_list.setItemWidget(dummy_item, dummy_widget)

        panel_layout.addWidget(self.log_list)
        grid.addWidget(log_panel)

