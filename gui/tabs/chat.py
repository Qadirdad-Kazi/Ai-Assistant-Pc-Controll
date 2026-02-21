from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QListWidgetItem, QSizePolicy, QMenu, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QColor

from qfluentwidgets import (
    PrimaryPushButton, PushButton, TransparentToolButton,
    LineEdit, SwitchButton, ListWidget, ScrollArea,
    FluentIcon as FIF, Action, RoundMenu
)

from gui.components.message_bubble import MessageBubble
from gui.components import ThinkingExpander
from core.database import db

# --- Theme Constants ---
THEME_GLASS_SIDEBAR = "rgba(5, 8, 13, 0.6)"
THEME_BORDER = "rgba(76, 201, 240, 0.3)" # Neon Cyan
THEME_HIGHLIGHT = "rgba(76, 201, 240, 0.1)"
THEME_TEXT_MAIN = "#e8eaed"
THEME_TEXT_SUB = "#8b9bb4"

class ChatTab(QWidget):
    """
    Chat Tab Component - Wolf Knight Theme.
    """
    
    # Signals
    send_message_requested = Signal(str)
    stop_generation_requested = Signal()
    tts_toggled = Signal(bool)
    new_chat_requested = Signal()
    session_selected = Signal(str)
    session_pin_requested = Signal(str)
    session_rename_requested = Signal(str, str)
    session_delete_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("ChatTab")
        self._setup_ui()
        self._connect_internal_signals()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Sidebar (Glass Panel) ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(280)
        self.sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {THEME_GLASS_SIDEBAR};
                border-right: 1px solid {THEME_BORDER};
            }}
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(15)
        
        # Header Label for Sidebar
        sb_label = QLabel("MISSION LOGS")
        sb_label.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 10px; font-weight: bold; letter-spacing: 2px;")
        sidebar_layout.addWidget(sb_label)

        # New Chat Button (Styled as Command Key)
        self.new_chat_btn = PushButton(FIF.ADD, "NEW PROTOCOL")
        self.new_chat_btn.setFixedHeight(40)
        self.new_chat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(76, 201, 240, 0.1);
                border: 1px solid {THEME_BORDER};
                color: {THEME_TEXT_MAIN};
                border-radius: 6px;
                font-weight: bold;
                text-align: left;
                padding-left: 15px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{
                background-color: rgba(76, 201, 240, 0.2);
                border: 1px solid #4cc9f0;
            }}
        """)
        sidebar_layout.addWidget(self.new_chat_btn)

        # Session List
        self.session_list = ListWidget()
        self.session_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self._show_session_context_menu)
        self.session_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background: transparent;
                color: {THEME_TEXT_SUB};
                padding: 10px;
                border-radius: 6px;
                margin-bottom: 4px;
            }}
            QListWidget::item:hover {{
                background-color: {THEME_HIGHLIGHT};
                color: {THEME_TEXT_MAIN};
            }}
            QListWidget::item:selected {{
                background-color: rgba(76, 201, 240, 0.15);
                color: #4cc9f0;
                border-left: 2px solid #4cc9f0;
            }}
        """)
        sidebar_layout.addWidget(self.session_list)
        
        layout.addWidget(self.sidebar)

        # --- Chat Content Area ---
        self.chat_content = QFrame()
        self.chat_content.setObjectName("chatContent")
        self.chat_content.setStyleSheet("background-color: transparent;")
        chat_layout = QVBoxLayout(self.chat_content)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Header (Floating HUD Strip)
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("background: transparent;") # Keep transparent to show window bg
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)
        
        self.status_icon =  QLabel("●")
        self.status_icon.setStyleSheet("color: #4cc9f0; font-size: 10px;")
        
        self.status_label = QLabel("SYSTEM READY")
        self.status_label.setStyleSheet("color: #4cc9f0; font-size: 12px; font-weight: bold; letter-spacing: 1px;")
        
        header_layout.addWidget(self.status_icon)
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()

        # TTS Toggle custom style
        self.tts_toggle = SwitchButton()
        self.tts_toggle.setOnText("VOICE")
        self.tts_toggle.setOffText("SILENT")
        # Fluent switch is hard to style deeply without sub-classing, but it usually adapts to theme
        header_layout.addWidget(self.tts_toggle)

        chat_layout.addWidget(header)

        # Chat Scroll Area
        self.chat_scroll = ScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("background: transparent; border: none;")
        self.chat_scroll.viewport().setStyleSheet("background: transparent;")
        
        # Custom Scrollbar style moved to global styles usually, but ensuring it here:
        self.chat_scroll.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical { background: transparent; width: 6px; margin: 0; }
            QScrollBar::handle:vertical { background: rgba(76, 201, 240, 0.2); border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: rgba(76, 201, 240, 0.5); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_container_layout = QVBoxLayout(self.chat_container)
        self.chat_container_layout.setContentsMargins(40, 10, 40, 20)
        self.chat_container_layout.setSpacing(20)
        self.chat_container_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_container)
        chat_layout.addWidget(self.chat_scroll)

        # Input Bar (Floating Glass Dock)
        input_container = QFrame()
        input_container.setStyleSheet("background: transparent;")
        ic_layout = QVBoxLayout(input_container)
        ic_layout.setContentsMargins(40, 0, 40, 30)
        
        self.input_bar = QFrame()
        self.input_bar.setFixedHeight(60)
        self.input_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(10, 15, 30, 0.8);
                border: 1px solid {THEME_BORDER};
                border-radius: 30px;
            }}
        """)
        # Add glow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(76, 201, 240, 50))
        shadow.setOffset(0,0)
        self.input_bar.setGraphicsEffect(shadow)
        
        input_layout = QHBoxLayout(self.input_bar)
        input_layout.setContentsMargins(20, 5, 10, 5)
        input_layout.setSpacing(10)

        self.user_input = LineEdit()
        self.user_input.setPlaceholderText("Enter command sequence...")
        self.user_input.setClearButtonEnabled(True)
        self.user_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #e8eaed;
                font-size: 14px;
            }
        """)
        input_layout.addWidget(self.user_input, 1)

        self.stop_btn = PrimaryPushButton(FIF.CLOSE, "ABORT")
        self.stop_btn.setVisible(False)
        self.stop_btn.setFixedSize(90, 36)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 59, 48, 0.2);
                border: 1px solid #ff3b30;
                color: #ff3b30;
                border-radius: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(255, 59, 48, 0.4); }
        """)
        input_layout.addWidget(self.stop_btn)

        self.send_btn = PrimaryPushButton(FIF.SEND, "EXECUTE")
        self.send_btn.setFixedSize(110, 36)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 201, 240, 0.2);
                border: 1px solid #4cc9f0;
                color: #4cc9f0;
                border-radius: 18px;
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 1px;
            }
            QPushButton:hover { background-color: rgba(76, 201, 240, 0.4); color: white; }
        """)
        input_layout.addWidget(self.send_btn)
        
        ic_layout.addWidget(self.input_bar)
        chat_layout.addWidget(input_container)

        layout.addWidget(self.chat_content)

    def _connect_internal_signals(self):
        """Connect internal UI events to public signals."""
        self.new_chat_btn.clicked.connect(self.new_chat_requested.emit)
        self.send_btn.clicked.connect(self._on_send_clicked)
        self.user_input.returnPressed.connect(self._on_send_clicked)
        self.stop_btn.clicked.connect(self.stop_generation_requested.emit)
        self.tts_toggle.checkedChanged.connect(self.tts_toggled.emit)
        self.session_list.itemClicked.connect(self._on_session_clicked)

    def _on_send_clicked(self):
        text = self.user_input.text()
        if text.strip():
            self.send_message_requested.emit(text)

    def _on_session_clicked(self, item: QListWidgetItem):
        session_id = item.data(Qt.UserRole)
        if session_id:
            self.session_selected.emit(session_id)

    # --- Public API for Controller/MainWindow ---

    def set_status(self, text: str):
        """Update status label."""
        QTimer.singleShot(0, lambda: self.status_label.setText(text.upper()))

    def clear_input(self):
        self.user_input.clear()

    def set_generating_state(self, is_generating: bool):
         """Switch states."""
         self.send_btn.setVisible(not is_generating)
         self.stop_btn.setVisible(is_generating)
         self.user_input.setEnabled(not is_generating)
         if not is_generating:
             self.user_input.setFocus()
         
         # Pulse effect for status icon?
         self.status_icon.setStyleSheet(f"color: {'#ff3b30' if is_generating else '#4cc9f0'}; font-size: 10px;")

    def add_message_bubble(self, role: str, text: str, is_thinking: bool = False):
        """Add a bubble."""
        bubble = MessageBubble(role, text, is_thinking)
        
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper_layout = QHBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        
        if role == "user":
            wrapper_layout.addStretch()
            wrapper_layout.addWidget(bubble)
        else:
            wrapper_layout.addWidget(bubble)
            wrapper_layout.addStretch()
        
        count = self.chat_container_layout.count()
        self.chat_container_layout.insertWidget(count - 1, wrapper)
        
        QTimer.singleShot(50, self.scroll_to_bottom)

    def add_streaming_widgets(self, thinking_ui, search_indicator, response_bubble):
        """Add streaming widgets."""
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(8)
        
        wrapper_layout.addWidget(thinking_ui)
        wrapper_layout.addWidget(search_indicator)
        
        bubble_wrapper = QWidget()
        bubble_wrapper.setStyleSheet("background: transparent;")
        bubble_layout = QHBoxLayout(bubble_wrapper)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.addWidget(response_bubble)
        bubble_layout.addStretch()
        wrapper_layout.addWidget(bubble_wrapper)
        
        count = self.chat_container_layout.count()
        self.chat_container_layout.insertWidget(count - 1, wrapper)
        
        QTimer.singleShot(50, self.scroll_to_bottom)

    def clear_chat_display(self):
        """Clear chat."""
        while self.chat_container_layout.count() > 1:
            item = self.chat_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def scroll_to_bottom(self):
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def refresh_sidebar(self, current_session_id: str = None):
        """Refresh sidebar list."""
        self.session_list.clear()
        sessions = db.get_sessions()
        
        for sess in sessions:
            title = sess['title']
            sid = sess['id']
            is_pinned = sess.get('pinned', False)
            is_current = sid == current_session_id
            
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, sid)
            
            if is_pinned:
                item.setIcon(FIF.PIN.icon())
            else:
                item.setIcon(FIF.CHAT.icon())
                
            self.session_list.addItem(item)
            if is_current:
                self.session_list.setCurrentItem(item)

    def _show_session_context_menu(self, position):
        item = self.session_list.itemAt(position)
        if not item: return
        session_id = item.data(Qt.UserRole)
        if not session_id: return

        menu = RoundMenu(parent=self)
        
        menu.addAction(Action(FIF.PIN, "Pin/Unpin", triggered=lambda: self.session_pin_requested.emit(session_id)))
        menu.addAction(Action(FIF.EDIT, "Rename", triggered=lambda: self._prompt_rename(session_id)))
        menu.addSeparator()
        menu.addAction(Action(FIF.DELETE, "Delete", triggered=lambda: self.session_delete_requested.emit(session_id)))
        
        menu.exec(self.session_list.mapToGlobal(position))

    def _prompt_rename(self, session_id):
        from PySide6.QtWidgets import QInputDialog
        new_title, ok = QInputDialog.getText(self, "Protocol Rename", "Enter new designation:")
        if ok and new_title.strip():
            self.session_rename_requested.emit(session_id, new_title.strip())
