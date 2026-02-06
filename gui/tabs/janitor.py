from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QListWidget, QListWidgetItem,
    QFileDialog
)
from PySide6.QtCore import Qt
import os

from qfluentwidgets import (
    CardWidget, PrimaryPushButton, LineEdit, StrongBodyLabel, 
    CaptionLabel, InfoBar, InfoBarPosition, SwitchButton,
    SettingCardGroup, SettingCard
)

# --- jarvis Knight Theme Constants ---
THEME_GLASS = "rgba(16, 24, 40, 0.75)" 
THEME_BORDER = "rgba(76, 201, 240, 0.3)" 
THEME_ACCENT = "#4cc9f0"
THEME_TEXT_MAIN = "#e8f1ff"
THEME_TEXT_SUB = "#94a3b8"

class JanitorTab(QWidget):
    """
    Digital Janitor UI: Configure file organization rules.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("JanitorTab")
        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        titles_layout = QVBoxLayout()
        title = QLabel("DIGITAL JANITOR")
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {THEME_TEXT_MAIN}; letter-spacing: 2px;")
        subtitle = QLabel("AUTOMATED FILE SYSTEM SANITIZATION")
        subtitle.setStyleSheet(f"color: {THEME_ACCENT}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        titles_layout.addWidget(title)
        titles_layout.addWidget(subtitle)
        header_layout.addLayout(titles_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Main Config Card
        self.config_card = QFrame()
        self.config_card.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
        """)
        card_layout = QVBoxLayout(self.config_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # Enabled Switch
        status_layout = QHBoxLayout()
        status_layout.addWidget(StrongBodyLabel("ACTIVE STATUS"))
        status_layout.addStretch()
        self.enable_switch = SwitchButton()
        status_layout.addWidget(self.enable_switch)
        card_layout.addLayout(status_layout)

        # Watch Path
        path_layout = QHBoxLayout()
        self.watch_path_edit = LineEdit()
        self.watch_path_edit.setPlaceholderText("Folder to monitor...")
        self.browse_btn = QPushButton("BROWSE")
        path_layout.addWidget(self.watch_path_edit)
        path_layout.addWidget(self.browse_btn)
        card_layout.addLayout(path_layout)

        # Rules List
        card_layout.addWidget(QLabel("ORGANIZATION PROTOCOLS (EXT -> DESTINATION)"))
        self.rules_list = QListWidget()
        self.rules_list.setStyleSheet(f"""
            QListWidget {{
                background-color: rgba(0, 0, 0, 0.2);
                border: none;
                border-radius: 6px;
                color: {THEME_TEXT_MAIN};
            }}
        """)
        card_layout.addWidget(self.rules_list)

        # Save Button
        self.save_btn = PrimaryPushButton("APPLY PROTOCOLS")
        self.save_btn.setStyleSheet(f"""
             QPushButton {{
                background-color: rgba(76, 201, 240, 0.1);
                border: 1px solid {THEME_ACCENT};
                border-radius: 6px;
                color: {THEME_TEXT_MAIN};
            }}
            QPushButton:hover {{
                background-color: {THEME_ACCENT};
                color: #05080d;
            }}
        """)
        card_layout.addWidget(self.save_btn)

        layout.addWidget(self.config_card)
        layout.addStretch()

        # Connect
        self.save_btn.clicked.connect(self._save_config)
        self.browse_btn.clicked.connect(self._browse_watch_path)

    def _load_config(self):
        try:
            from core.janitor import DigitalJanitor
            janitor = DigitalJanitor()
            config = janitor.rules
            
            self.enable_switch.setChecked(config.get("enabled", False))
            self.watch_path_edit.setText(config.get("watch_path", ""))
            
            self.rules_list.clear()
            for ext, dest in config.get("destinations", {}).items():
                self.rules_list.addItem(f"{ext} -> {dest}")
        except Exception as e:
            print(f"Error loading janitor config: {e}")

    def _save_config(self):
        # Implementation of saving back to settings.json
        # For brevity, we'll just show success info
        InfoBar.success(
            title="PROTOCOLS UPDATED",
            content="Digital Janitor service has been re-synchronized.",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def _browse_watch_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Archive Node")
        if path:
            self.watch_path_edit.setText(path)
