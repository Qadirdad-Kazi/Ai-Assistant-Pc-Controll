from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget, QHBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor, QFont

class NewsCard(QFrame):
    """
    A card widget representing a single news story.
    Styling optimized for Aura Theme (Dark Navy).
    """
    def __init__(self, article, parent=None):
        super().__init__(parent)
        self.article = article
        self.url = article.get('url')
        
        self.setObjectName("newsCard")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(140) # Slightly more compact
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Image placeholder (Left side)
        self.image_area = QLabel()
        self.image_area.setFixedSize(60, 60)
        self.image_area.setAlignment(Qt.AlignCenter)
        # Use semi-transparent background for icon
        self.image_area.setStyleSheet(f"""
            background-color: {self._get_category_color(article.get('category'))}20; 
            border: 1px solid {self._get_category_color(article.get('category'))}40;
            border-radius: 10px;
            font-size: 28px;
        """)
        self.image_area.setText(self._get_category_icon(article.get('category')))
        layout.addWidget(self.image_area)
        
        # Content (Right side)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        content_layout.setAlignment(Qt.AlignVCenter)
        
        # Headline
        headline = QLabel(article.get('title', 'No Title'))
        headline.setWordWrap(True)
        # Explicit white color for visibility
        headline.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 600; font-family: 'Segoe UI';")
        content_layout.addWidget(headline)
        
        # Metadata Row
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(10)
        
        # Source
        source = QLabel(article.get('source', 'Unknown'))
        source.setStyleSheet("color: #33b5e5; font-weight: bold; font-size: 12px;") # Cyan accent
        meta_layout.addWidget(source)
        
        # Divider
        div = QLabel("•")
        div.setStyleSheet("color: #555;")
        meta_layout.addWidget(div)
        
        # Time
        date = QLabel(article.get('date', 'Just now'))
        date.setStyleSheet("color: #8a8a8a; font-size: 12px;")
        meta_layout.addWidget(date)
        
        meta_layout.addStretch()
        content_layout.addLayout(meta_layout)
        
        layout.addLayout(content_layout)
        
        # Styling using ID selector
        # We ensure background is visible against the dark window
        self.setStyleSheet("""
            QFrame#newsCard {
                background-color: #111625; /* Slightly lighter than window #05080d */
                border: 1px solid #1a2236;
                border-radius: 12px;
            }
            QFrame#newsCard:hover {
                background-color: #1a2236;
                border: 1px solid #33b5e5; /* Cyan hover border */
            }
        """)

    def _get_category_color(self, category):
        """Return color based on category."""
        cat = str(category).lower()
        if "tech" in cat: return "#33b5e5" # Cyan
        if "market" in cat or "finance" in cat: return "#00c853" # Green
        if "science" in cat: return "#aa66cc" # Purple
        if "culture" in cat: return "#ff4444" # Red
        return "#ffbb33" # Orange/Yellow default

    def _get_category_icon(self, category):
        cat = str(category).lower()
        if "tech" in cat: return "💻"
        if "market" in cat: return "📈"
        if "science" in cat: return "🧬"
        if "culture" in cat: return "🎭" 
        return "📰"
    
    def mousePressEvent(self, event):
        """Open URL on click."""
        import webbrowser
        if self.url:
            webbrowser.open(self.url)
