"""
Global stylesheet for the Wolf AI application (Aura AI Theme).
"""

# Aura Theme Colors
# Background: #05080d (Deepest Navy)
# Surface: #0f1524 (Dark Navy)
# Accent: #33b5e5 (Cyan)
# Text: #e8eaed

AURA_STYLESHEET = """
/* Global Window Background */
FluentWindow {
    background-color: #05080d;
    color: #e8eaed;
}

/* Stacked Widget Background (Content Area) */
StackedWidget {
    background-color: #05080d;
    border: none;
}

/* Navigation Interface (Sidebar) */
NavigationInterface {
    background-color: #05080d;
    border-right: 1px solid #1a2236;
}

/* Cards (Surface) */
CardWidget {
    background-color: #0f1524;
    border: 1px solid #1a2236;
    border-radius: 10px;
}

/* Labels */
TitleLabel, SubtitleLabel, StrongBodyLabel {
    color: #e8eaed;
}

BodyLabel, CaptionLabel {
    color: #8b9bb4;
}

/* Standard QWidget used as containers */
QWidget#chatContent, QWidget#plannerPanel, QWidget#briefingView, QFrame#homeAutomationView {
    background-color: transparent;
}

/* List Items (Session List) */
ListWidget {
    background-color: transparent;
    border: none;
}

ListWidget::item {
    color: #8b9bb4;
    border-radius: 6px;
    padding: 8px;
    margin: 2px;
}

ListWidget::item:hover {
    background-color: rgba(51, 181, 229, 0.1); /* Cyan tint */
    color: #e8eaed;
}

ListWidget::item:selected {
    background-color: rgba(51, 181, 229, 0.2);
    color: #33b5e5;
    border-left: 2px solid #33b5e5;
}

/* Input Fields */
LineEdit, TextEdit, PlainTextEdit {
    background-color: #0f1524;
    border: 1px solid #1a2236;
    border-radius: 8px;
    color: #e8eaed;
    selection-background-color: #33b5e5;
}

LineEdit:focus, TextEdit:focus {
    border: 1px solid #33b5e5;
    background-color: #141c2f;
}

/* ScrollBars */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #1a2236;
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #33b5e5;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
