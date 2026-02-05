"""
Global stylesheet for the Wolf AI application (Aura AI Theme).
"""


# Wolf Knight Theme Colors
# Background: #05080d
# Surface: rgba(16, 24, 40, 0.70)
# Border: rgba(76, 201, 240, 0.3)
# Accent: #4cc9f0
# Text: #e8f1ff

AURA_STYLESHEET = """
/* Global Window Background */
FluentWindow {
    background-color: #05080d;
    color: #e8f1ff;
}

/* Stacked Widget Background (Content Area) */
StackedWidget {
    background-color: transparent;
    border: none;
}

/* Navigation Interface (Sidebar) */
NavigationInterface {
    background-color: #05080d;
    border-right: 1px solid rgba(76, 201, 240, 0.3);
}

/* Cards (Surface) */
CardWidget, SettingCard, SettingCardGroup {
    background-color: rgba(16, 24, 40, 0.70);
    border: 1px solid rgba(76, 201, 240, 0.3);
    border-radius: 12px;
}

/* Labels */
TitleLabel, SubtitleLabel, StrongBodyLabel {
    color: #e8f1ff;
    font-weight: bold;
}

BodyLabel, CaptionLabel {
    color: #94a3b8;
}

/* Standard QWidget used as containers */
QWidget#chatContent, QWidget#plannerPanel, QFrame#homeAutomationView, QWidget#settingsInterface, QWidget#scrollWidget {
    background-color: transparent;
}

/* List Items (Session List) */
ListWidget {
    background-color: transparent;
    border: none;
}

ListWidget::item {
    color: #94a3b8;
    border-radius: 6px;
    padding: 8px;
    margin: 2px;
}

ListWidget::item:hover {
    background-color: rgba(76, 201, 240, 0.15);
    color: #e8f1ff;
    border: 1px solid rgba(76, 201, 240, 0.3);
}

ListWidget::item:selected {
    background-color: rgba(76, 201, 240, 0.25);
    color: #4cc9f0;
    border-left: 2px solid #4cc9f0;
}

/* Input Fields */
LineEdit, TextEdit, PlainTextEdit, ComboBox {
    background-color: rgba(20, 30, 50, 0.6);
    border: 1px solid rgba(76, 201, 240, 0.3);
    border-radius: 8px;
    color: #e8f1ff;
    selection-background-color: #4cc9f0;
    padding: 5px;
}

LineEdit:focus, TextEdit:focus, PlainTextEdit:focus, ComboBox:focus {
    border: 1px solid #4cc9f0;
    background-color: rgba(30, 40, 60, 0.8);
}

/* Buttons */
QPushButton {
    background-color: rgba(76, 201, 240, 0.1);
    border: 1px solid rgba(76, 201, 240, 0.3);
    border-radius: 6px;
    color: #e8f1ff;
    padding: 6px 16px;
}

QPushButton:hover {
    background-color: rgba(76, 201, 240, 0.3);
    border: 1px solid #4cc9f0;
}

QPushButton:pressed {
    background-color: rgba(76, 201, 240, 0.5);
}

PrimaryPushButton {
    background-color: rgba(76, 201, 240, 0.2);
    border: 1px solid #4cc9f0;
    color: #e8f1ff;
}

PrimaryPushButton:hover {
    background-color: #4cc9f0;
    color: #05080d;
}

/* ScrollBars */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(76, 201, 240, 0.2);
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #4cc9f0;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
