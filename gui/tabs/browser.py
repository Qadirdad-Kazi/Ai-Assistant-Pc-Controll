from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QFrame, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QThread, Slot, Signal
from PySide6.QtGui import QPixmap, QImage, QColor

from qfluentwidgets import (
    PrimaryPushButton, LineEdit, StrongBodyLabel, CaptionLabel,
    ScrollArea, CardWidget
)

from gui.components.thinking_expander import ThinkingExpander
from core.agent import BrowserAgent

# --- jarvis Knight Theme Constants ---
THEME_GLASS = "rgba(16, 24, 40, 0.70)" 
THEME_BORDER = "rgba(76, 201, 240, 0.3)" # Neon Cyan
THEME_ACCENT = "#4cc9f0"
THEME_TEXT_MAIN = "#e8f1ff"
THEME_TEXT_SUB = "#94a3b8"
THEME_GLOW = "rgba(76, 201, 240, 0.15)"

class GlowEffect(QGraphicsDropShadowEffect):
    def __init__(self, color=THEME_ACCENT, blur=15, parent=None):
        super().__init__(parent)
        self.setBlurRadius(blur)
        self.setColor(QColor(color))
        self.setOffset(0, 0)

class BrowserTab(QWidget):
    """
    Tab for controlling the AI Browser Agent.
    jarvis Knight Theme.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BrowserTab")
        
        # Agent Threading
        self.agent_thread = QThread()
        self.agent = None # Will instantiate when needed
        
        self._setup_ui()
        self._setup_agent()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        # Left Column: Browser Viewport (Custom Glass Frame)
        viewport_container = QFrame()
        viewport_container.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
        """)
        viewport_container.setGraphicsEffect(GlowEffect(THEME_ACCENT, 10))
        
        viewport_layout = QVBoxLayout(viewport_container)
        viewport_layout.setContentsMargins(15, 15, 15, 15)
        viewport_layout.setSpacing(10)
        
        v_header = QLabel("NEURAL VISION VIEWPORT")
        v_header.setStyleSheet(f"color: {THEME_ACCENT}; font-size: 11px; font-weight: bold; letter-spacing: 2px; border: none; background: transparent;")
        viewport_layout.addWidget(v_header)
        
        self.image_label = QLabel("AWAITING TARGET...")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(5, 10, 15, 0.6); 
                color: {THEME_TEXT_SUB};
                border: 1px dashed {THEME_BORDER};
                border-radius: 8px;
                font-family: 'Consolas';
                letter-spacing: 1px;
            }}
        """)
        self.image_label.setMinimumSize(640, 360)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        viewport_layout.addWidget(self.image_label)
        
        layout.addWidget(viewport_container, stretch=3)

        # Right Column: Controls & Logs (Glass Frame)
        controls_container = QFrame()
        controls_container.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
        """)
        
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(15)

        # Status
        self.status_label = QLabel("STATUS: IDLE")
        self.status_label.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 10px; font-weight: bold; letter-spacing: 1px; border: none; background: transparent;")
        controls_layout.addWidget(self.status_label)

        # Thinking Stream
        # Note: ThinkingExpander might have its own internal styling, but we wrap it here.
        # Ideally, update ThinkingExpander too, but for now we contain it.
        self.thinking_expander = ThinkingExpander(self)
        controls_layout.addWidget(self.thinking_expander)

        # Action Log
        log_label = QLabel("EXECUTION LOG")
        log_label.setStyleSheet(f"color: {THEME_ACCENT}; font-size: 11px; font-weight: bold; letter-spacing: 2px; border: none; background: transparent;")
        controls_layout.addWidget(log_label)
        
        self.action_log = QTextEdit()
        self.action_log.setReadOnly(True)
        self.action_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(0, 0, 0, 0.4);
                border: 1px solid {THEME_BORDER};
                border-radius: 6px;
                color: {THEME_TEXT_MAIN};
                font-family: 'Consolas'; 
                font-size: 11px;
                padding: 10px;
            }}
        """)
        controls_layout.addWidget(self.action_log)

        # Input Area
        input_layout = QHBoxLayout()
        self.url_input = LineEdit()
        self.url_input.setPlaceholderText("Enter mission directive...")
        self.url_input.setFixedHeight(36)
        # Apply custom style to override default fluent LineEdit if needed
        self.url_input.setStyleSheet(f"""
            LineEdit {{
                background: rgba(0,0,0,0.3);
                border: 1px solid {THEME_BORDER};
                color: {THEME_TEXT_MAIN};
                border-radius: 4px;
            }}
            LineEdit:focus {{
                border: 1px solid {THEME_ACCENT};
                background: rgba(0,0,0,0.5);
            }}
        """)
        input_layout.addWidget(self.url_input)
        
        self.go_btn = PrimaryPushButton("ENGAGE")
        self.go_btn.setFixedSize(90, 36)
        self.go_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(76, 201, 240, 0.2);
                border: 1px solid {THEME_ACCENT};
                color: {THEME_TEXT_MAIN};
                border-radius: 4px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {THEME_ACCENT};
                color: #05080d;
            }}
        """)
        self.go_btn.clicked.connect(self._on_execute)
        input_layout.addWidget(self.go_btn)
        
        controls_layout.addLayout(input_layout)
        
        layout.addWidget(controls_container, stretch=2)

    def _setup_agent(self):
        # Instantiate agent - model comes from settings now
        try:
            from core.settings_store import settings
            model_name = settings.get("models.web_agent", "qwen3-vl:4b")
            self.agent = BrowserAgent(model_name=model_name) 
            self.agent.moveToThread(self.agent_thread)
            
            # Connect signals
            self.agent.screenshot_updated.connect(self._update_screenshot)
            self.agent.thinking_update.connect(self._update_thinking)
            self.agent.action_updated.connect(self._log_action)
            self.agent.finished.connect(self._on_finished)
            self.agent.error_occurred.connect(self._on_error)
            
            # Connect start signal
            self.run_signal.connect(self.agent.start_task)
            
            # Start thread
            self.agent_thread.start()
        except: pass

    def _on_execute(self):
        instruction = self.url_input.text()
        if not instruction.strip():
            return
            
        self.status_label.setText("STATUS: OPERATIONAL")
        self.status_label.setStyleSheet(f"color: {THEME_ACCENT}; font-size: 10px; font-weight: bold; letter-spacing: 1px; border: none; background: transparent;")
        self.go_btn.setEnabled(False)
        self.action_log.clear()
        
        self.run_signal.emit(instruction)

    # Signal to bridge GUI -> Worker
    run_signal = Signal(str)

    def closeEvent(self, event):
        if self.agent:
            try:
                self.agent.stop()
                self.agent.cleanup()
            except: pass
        self.agent_thread.quit()
        self.agent_thread.wait()
        super().closeEvent(event)

    # Slots
    @Slot(QImage)
    def _update_screenshot(self, image):
        # Scale to fit label
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    @Slot(str)
    def _update_thinking(self, text):
        self.thinking_expander.add_text(text)

    @Slot(str)
    def _log_action(self, text):
        self.action_log.append(text)

    @Slot()
    def _on_finished(self):
        self.status_label.setText("STATUS: COMPLETE")
        self.status_label.setStyleSheet(f"color: #a0ffa0; font-size: 10px; font-weight: bold; letter-spacing: 1px; border: none; background: transparent;")
        self.go_btn.setEnabled(True)
        self.thinking_expander.complete()

    @Slot(str)
    def _on_error(self, err):
        self.status_label.setText(f"STATUS: ERROR")
        self.status_label.setStyleSheet(f"color: #ff5555; font-size: 10px; font-weight: bold; letter-spacing: 1px; border: none; background: transparent;")
        self.action_log.append(f"ERROR: {err}")
        self.go_btn.setEnabled(True)

