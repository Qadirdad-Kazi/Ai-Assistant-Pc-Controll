from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QListWidget, QListWidgetItem,
    QProgressBar, QFrame, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QIcon, QColor

from qfluentwidgets import (
    CardWidget, PrimaryPushButton, LineEdit, StrongBodyLabel, 
    CaptionLabel, InfoBar, InfoBarPosition, ProgressBar
)

# --- jarvis Knight Theme Constants ---
THEME_GLASS = "rgba(16, 24, 40, 0.70)" 
THEME_BORDER = "rgba(76, 201, 240, 0.3)" # Neon Cyan
THEME_ACCENT = "#4cc9f0"
THEME_TEXT_MAIN = "#e8f1ff"
THEME_TEXT_SUB = "#94a3b8"

class GrimoireTab(QWidget):
    """
    Grimoire: Local Knowledge Base & Document Management.
    jarvis Knight Theme.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GrimoireTab")
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        
        titles_layout = QVBoxLayout()
        title = QLabel("GRIMOIRE ARCHIVES")
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {THEME_TEXT_MAIN}; letter-spacing: 2px;")
        subtitle = QLabel("LOCAL KNOWLEDGE VECTOR STORE")
        subtitle.setStyleSheet(f"color: {THEME_ACCENT}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        titles_layout.addWidget(title)
        titles_layout.addWidget(subtitle)
        
        header_layout.addLayout(titles_layout)
        header_layout.addStretch()
        
        # Stats Bubble
        stats_bubble = QLabel("• 0 FRAGMENTS INDEXED")
        stats_bubble.setObjectName("statsBubble") 
        stats_bubble.setStyleSheet(f"""
            background-color: rgba(13, 18, 29, 0.6); 
            color: {THEME_ACCENT}; 
            border: 1px solid {THEME_BORDER}; 
            border-radius: 14px; 
            padding: 6px 15px; 
            font-weight: bold;
            font-size: 10px;
        """)
        header_layout.addWidget(stats_bubble)
        
        layout.addLayout(header_layout)

        # Main Content Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {THEME_BORDER};
            }}
        """)

        # Left Panel: Document List & Import
        left_panel = QFrame()
        left_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        doc_header = QLabel("SCROLL COLLECTION")
        doc_header.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 11px; font-weight: bold;")
        left_layout.addWidget(doc_header)
        
        self.doc_list = QListWidget()
        self.doc_list.setStyleSheet(f"""
            QListWidget {{
                background-color: rgba(0, 0, 0, 0.2);
                border: none;
                border-radius: 6px;
                color: {THEME_TEXT_MAIN};
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }}
            QListWidget::item:selected {{
                background-color: rgba(76, 201, 240, 0.15);
                color: {THEME_ACCENT};
            }}
            QListWidget::item:hover {{
                background-color: rgba(255, 255, 255, 0.05);
            }}
        """)
        left_layout.addWidget(self.doc_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = PrimaryPushButton("INGEST DOCUMENT")
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(76, 201, 240, 0.2);
                border: 1px solid {THEME_ACCENT};
                color: {THEME_TEXT_MAIN};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {THEME_ACCENT};
                color: #05080d;
            }}
        """)
        # self.add_btn.clicked.connect(self._import_document) 
        
        self.clear_btn = QPushButton("PURGE")
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 85, 85, 0.1);
                border: 1px solid rgba(255, 85, 85, 0.4);
                color: #ff5555;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 85, 85, 0.3);
            }}
        """)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.clear_btn)
        left_layout.addLayout(btn_layout)
        
        # Progress Bar
        self.progress = ProgressBar()
        self.progress.setValue(0)
        self.progress.hide()
        left_layout.addWidget(self.progress)
        
        splitter.addWidget(left_panel)

        # Right Panel: Preview / Details
        right_panel = QFrame()
        right_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        preview_header = QLabel("GLYPH INSPECTION")
        preview_header.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 11px; font-weight: bold;")
        right_layout.addWidget(preview_header)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Select a document to inspect contents or query results...")
        self.preview_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: rgba(0, 0, 0, 0.2);
                border: none;
                border-radius: 6px;
                color: {THEME_TEXT_MAIN};
                font-family: 'Consolas';
                font-size: 12px;
                padding: 10px;
            }}
        """)
        right_layout.addWidget(self.preview_text)
        
        # Query Test Area
        query_layout = QHBoxLayout()
        self.query_input = LineEdit()
        self.query_input.setPlaceholderText("Test query against Grimoire...")
        self.query_input.setStyleSheet(f"""
            LineEdit {{
                background-color: rgba(0, 0, 0, 0.2);
                border: 1px solid {THEME_BORDER};
                border-radius: 6px;
                color: {THEME_TEXT_MAIN};
                padding: 5px;
            }}
        """)
        
        self.query_btn = QPushButton("CONSULT")
        self.query_btn.setFixedSize(80, 32)
        self.query_btn.setStyleSheet(f"""
             QPushButton {{
                background-color: rgba(76, 201, 240, 0.1);
                border: 1px solid {THEME_ACCENT};
                border-radius: 6px;
                color: {THEME_ACCENT};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {THEME_ACCENT};
                color: #05080d;
            }}
        """)
        
        query_layout.addWidget(self.query_input)
        query_layout.addWidget(self.query_btn)
        right_layout.addLayout(query_layout)
        
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        
        # Connect Signals
        self.add_btn.clicked.connect(self._import_document)
        self.clear_btn.clicked.connect(self._purge_db)
        self.query_btn.clicked.connect(self._run_query)
        self.query_input.returnPressed.connect(self._run_query)
        
        # Initial Load
        QTimer.singleShot(1000, self._refresh_stats)

    def _refresh_stats(self):
        """Refresh the document list and fragment count."""
        try:
            from core.knowledge_base import knowledge_base
            
            # Update Sources
            self.doc_list.clear()
            sources = knowledge_base.get_all_sources()
            for source in sources:
                self.doc_list.addItem(source)
                
            # Update Count
            stats = knowledge_base.get_stats()
            count = stats.get("count", 0)
            
            # Update bubble via findChild if proper object name used, or store ref
            # We stored reference as local var 'stats_bubble' in init, which is lost. 
            # Let's fix _setup_ui to verify object name or store self.stats_bubble
            bubble = self.findChild(QLabel, "statsBubble")
            if bubble:
                bubble.setText(f"• {count} FRAGMENTS INDEXED")
                
        except Exception as e:
            print(f"[Grimoire] Stats Refresh Error: {e}")

    def _import_document(self):
        """Open file dialog and ingest."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Ingest Scroll", "", "Documents (*.pdf *.txt *.md *.py *.json *.log)"
        )
        if not path:
            return
            
        self.add_btn.setEnabled(False)
        self.add_btn.setText("INGESTING...")
        self.progress.show()
        self.progress.setRange(0, 0) # Infinite
        
        # Run in thread
        self.worker = IngestWorker(path)
        self.worker.finished.connect(self._on_ingest_finished)
        self.worker.error.connect(self._on_ingest_error)
        self.worker.start()

    def _on_ingest_finished(self, msg):
        self.add_btn.setEnabled(True)
        self.add_btn.setText("INGEST DOCUMENT")
        self.progress.hide()
        
        # Show success in preview
        self.preview_text.append(f"\n[SYSTEM] {msg}")
        self._refresh_stats()

    def _on_ingest_error(self, err):
        self.add_btn.setEnabled(True)
        self.add_btn.setText("INGEST DOCUMENT")
        self.progress.hide()
        self.preview_text.append(f"\n[ERROR] Ingestion Failed: {err}")

    def _purge_db(self):
        from core.knowledge_base import knowledge_base
        knowledge_base.clear()
        self._refresh_stats()
        self.preview_text.setText("[SYSTEM] Archives purged.")

    def _run_query(self):
        text = self.query_input.text().strip()
        if not text:
            return
            
        self.preview_text.append(f"\n[QUERY] {text}")
        self.query_input.clear()
        
        try:
            from core.knowledge_base import knowledge_base
            results = knowledge_base.query(text)
            
            if not results:
                self.preview_text.append("[SYSTEM] No relevant matches found in archives.")
            else:
                for i, res in enumerate(results):
                    content = res['content']
                    source = res['source']
                    score = res['score'] 
                    # Score is distance? Chroma default is L2 distance usually? 
                    # Smaller is better. 
                    
                    self.preview_text.append(f"\n--- MATCH {i+1} (Source: {source}) ---")
                    self.preview_text.append(f"{content[:500]}...")
        except Exception as e:
            self.preview_text.append(f"[ERROR] Query failed: {e}")


class IngestWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, path):
        super().__init__()
        self.path = path
        
    def run(self):
        try:
            from core.knowledge_base import knowledge_base
            msg = knowledge_base.ingest_document(self.path)
            self.finished.emit(msg)
        except Exception as e:
            self.error.emit(str(e))
