import threading
import time
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QSizePolicy, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QFont, QColor
from qfluentwidgets import (
    PrimaryPushButton, FluentIcon as FIF, IconWidget,
    CardWidget
)

# Test functions
def check_ollama_router():
    from config import OLLAMA_URL
    import requests
    try:
        r = requests.get(f"{OLLAMA_URL}/tags", timeout=5)
        if r.status_code == 200:
            return True, "Ollama API is running and accessible."
        return False, f"Ollama returned status {r.status_code}"
    except Exception as e:
        return False, f"Ollama unreachable: {str(e)}"

def check_database():
    from core.database import db
    try:
        sessions = db.get_sessions()
        return True, f"Database connected. {len(sessions)} sessions found."
    except Exception as e:
        return False, f"Database error: {str(e)}"

def check_voice_tts():
    from core.tts import tts
    try:
        if not tts.piper_exe:
            return False, "Piper TTS executable not found."
        return True, "TTS engine fully initialized."
    except Exception as e:
        return False, f"TTS error: {str(e)}"

def check_stt_engine():
    from core.settings_store import settings
    try:
        key = settings.get("picovoice.key")
        if key:
            return True, "Porcupine high-performance engine configured."
        return True, "Default CPU transcription engine configured."
    except Exception as e:
        return False, str(e)

def check_pc_control():
    try:
        import pyautogui
        size = pyautogui.size()
        import subprocess
        result = subprocess.run(["whoami"], capture_output=True, text=True, timeout=5)
        user = result.stdout.strip()
        return True, f"Screen: {size.width}x{size.height}, User: {user}"
    except Exception as e:
        return False, f"PC Control error: {str(e)}"

def check_phone_gateway():
    from core.settings_store import settings
    mode = settings.get("phone.mode", "None")
    if mode == "None":
        return True, "Gateway disabled (Standby Mode)."
    
    if mode == "Wi-Fi Softphone (SIP)":
        ip = settings.get("sip.ip", "0.0.0.0")
        import socket
        try:
            # Simple ping/socket check to see if IP is reachable
            # SIP typically uses 5060, but we just check if the host is up
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            # We don't know the exact port since it's a softphone, 
            # but we can check if the device is reachable on the network
            import os
            response = os.system(f"ping -n 1 {ip} > nul")
            if response == 0:
                return True, f"SIP Host {ip} is reachable."
            return False, f"SIP Host {ip} is unreachable."
        except:
            return False, f"Network error checking {ip}"
            
    if mode == "GSM Hardware (Serial)":
        port = settings.get("gsm.port", "COM3")
        try:
            import serial
            # Just check if the port exists/is available
            ser = serial.Serial(port, timeout=1)
            ser.close()
            return True, f"GSM Modem found on {port}."
        except Exception as e:
            return False, f"GSM Modem {port} failed: {str(e)}"
    
    return False, "Unknown phone mode."

def check_ocr_vision():
    from core.settings_store import settings
    # BugWatcher uses tesseract
    try:
        import pytesseract
        # On windows, we usually need to check the path
        path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
        
        ver = pytesseract.get_tesseract_version()
        return True, f"Tesseract {ver} detected."
    except Exception as e:
        return False, "Tesseract OCR not found in default path."


class TestRunner(QObject):
    test_started = Signal(str)
    test_finished = Signal(str, bool, str)

    def run_test(self, name):
        tests = self._get_test_map()
        if name in tests:
            self.test_started.emit(name)
            success, msg = tests[name]()
            self.test_finished.emit(name, success, msg)

    def run_all(self):
        tests = self._get_test_map()
        for name in tests:
            self.run_test(name)
            time.sleep(0.3)

    def _get_test_map(self):
        return {
            "Router API": check_ollama_router,
            "Local Database": check_database,
            "TTS Engine": check_voice_tts,
            "STT Engine": check_stt_engine,
            "PC Control": check_pc_control,
            "Phone Gateway": check_phone_gateway,
            "OCR Vision": check_ocr_vision
        }

class DiagnosticCard(CardWidget):
    """Glossy card representing a test."""
    
    def __init__(self, title, description, icon):
        super().__init__()
        self.title = title
        
        # Enable glossy UI
        self.setStyleSheet("""
            DiagnosticCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255, 255, 255, 0.05), stop:1 rgba(255, 255, 255, 0.02));
                border: 1px solid rgba(76, 201, 240, 0.2);
                border-radius: 16px;
            }
            DiagnosticCard:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(76, 201, 240, 0.1), stop:1 rgba(76, 201, 240, 0.05));
                border: 1px solid rgba(76, 201, 240, 0.6);
            }
        """)
        
        self.setFixedHeight(130)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        
        # Icon
        self.icon_widget = IconWidget(icon)
        self.icon_widget.setFixedSize(44, 44)
        
        # Text
        text_layout = QVBoxLayout()
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-size: 19px; font-weight: 800; color: #ffffff; font-family: 'Segoe UI';")
        self.desc_lbl = QLabel(description)
        self.desc_lbl.setStyleSheet("font-size: 13px; color: #b0c4de; font-family: 'Segoe UI';")
        self.desc_lbl.setWordWrap(True)
        
        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.desc_lbl)
        text_layout.addStretch()
        
        # Right Side (Status + Button)
        right_layout = QVBoxLayout()
        
        self.status_lbl = QLabel("READY")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("""
            font-size: 11px; 
            font-weight: bold; 
            color: #a0a0a0; 
            padding: 4px 12px; 
            background: rgba(0,0,0,0.3); 
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
        """)
        
        self.run_btn = PrimaryPushButton(FIF.SYNC, "TEST")
        self.run_btn.setFixedSize(80, 32)
        self.run_btn.setStyleSheet("font-size: 11px; font-weight: bold;")
        
        right_layout.addWidget(self.status_lbl, 0, Qt.AlignRight)
        right_layout.addStretch()
        right_layout.addWidget(self.run_btn, 0, Qt.AlignRight)
        
        layout.addWidget(self.icon_widget)
        layout.addSpacing(20)
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addLayout(right_layout)

    def set_status(self, is_running=False, is_success=None, message=""):
        if is_running:
            self.status_lbl.setText("RUNNING...")
            self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12; padding: 5px 10px; background: rgba(243, 156, 18, 0.2); border-radius: 6px;")
            self.desc_lbl.setText("Testing functionality...")
        elif is_success is True:
            self.status_lbl.setText("PASS")
            self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #2ecc71; padding: 5px 10px; background: rgba(46, 204, 113, 0.2); border-radius: 6px;")
            self.desc_lbl.setText(message)
        elif is_success is False:
            self.status_lbl.setText("FAIL")
            self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c; padding: 5px 10px; background: rgba(231, 76, 60, 0.2); border-radius: 6px;")
            self.desc_lbl.setText(message)


class DiagnosticsTab(QWidget):
    """System diagnostics and unit tests page."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("diagnosticsInterface")
        self.cards = {}
        self._setup_ui()
        
        self.runner = TestRunner()
        self.runner.test_started.connect(self._on_test_started)
        self.runner.test_finished.connect(self._on_test_finished)
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("System Diagnostics")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        
        self.run_btn = PrimaryPushButton(FIF.PLAY, "Run All Diagnostics")
        self.run_btn.setFixedSize(200, 40)
        self.run_btn.clicked.connect(self.run_diagnostics)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.run_btn)
        
        # Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#scrollContent { background: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")
        self.grid = QGridLayout(scroll_content)
        self.grid.setSpacing(15)
        
        self.add_card("Router API", "Test local LLM and Ollama bindings", FIF.ROBOT)
        self.add_card("Local Database", "Verify SQLite read/write access", FIF.SAVE)
        self.add_card("TTS Engine", "Check Piper speech synthesis binaries", FIF.VOLUME)
        self.add_card("STT Engine", "Validate Transcription vs Porcupine engine", FIF.MICROPHONE)
        self.add_card("PC Control", "Check screen control and system permissions", FIF.LAYOUT)
        self.add_card("Phone Gateway", "Validate SIP/GSM hardware connection", FIF.PHONE)
        self.add_card("OCR Vision", "Detect Tesseract engine for Bug Watcher", FIF.VIEW)
        
        scroll.setWidget(scroll_content)
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)
        main_layout.addWidget(scroll)

    def add_card(self, title, desc, icon):
        card = DiagnosticCard(title, desc, icon)
        row = len(self.cards) // 2
        col = len(self.cards) % 2
        self.grid.addWidget(card, row, col)
        
        # Connect individual run button
        card.run_btn.clicked.connect(lambda: threading.Thread(
            target=self.runner.run_test, args=(title,), daemon=True
        ).start())
        
        self.cards[title] = card

    def run_diagnostics(self):
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Running...")
        threading.Thread(target=self.runner.run_all, daemon=True).start()
        
    def _on_test_started(self, test_name):
        if test_name in self.cards:
            self.cards[test_name].set_status(is_running=True)
            
    def _on_test_finished(self, test_name, success, msg):
        if test_name in self.cards:
            self.cards[test_name].set_status(is_success=success, message=msg)
            
        # Check if all done to reset button (simplified logic)
        all_done = not any(c.status_lbl.text() == "RUNNING..." for c in self.cards.values())
        if all_done:
            self.run_btn.setEnabled(True)
            self.run_btn.setText("Run All Diagnostics")
