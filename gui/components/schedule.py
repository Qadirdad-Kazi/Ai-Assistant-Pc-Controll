from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton
)
from PySide6.QtCore import Qt, QDate, QTime, QDateTime, Signal
from PySide6.QtGui import QColor

from qfluentwidgets import (
    PushButton, PrimaryPushButton, LineEdit, 
    ComboBox, MessageBoxBase, SubtitleLabel
)
from qfluentwidgets.components.date_time.fast_calendar_view import FastCalendarView as CalendarView
from qfluentwidgets.components.date_time.calendar_picker import CalendarPicker
from qfluentwidgets.components.date_time.time_picker import TimePicker

from core.calendar_manager import calendar_manager
from datetime import datetime

class AddEventDialog(MessageBoxBase):
    """Custom Dialog for adding events using Fluent Widgets."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Add Event", self)
        
        # UI Setup
        self.viewLayout.addWidget(self.titleLabel)
        
        # Title Input
        self.titleEdit = LineEdit(self)
        self.titleEdit.setPlaceholderText("Event Title")
        self.viewLayout.addWidget(self.titleEdit)
        
        # Date Picker
        self.datePicker = CalendarPicker(self)
        self.datePicker.setDate(QDate.currentDate())
        self.viewLayout.addWidget(self.datePicker)
        
        # Time Picker
        self.timePicker = TimePicker(self)
        self.timePicker.setTime(QTime.currentTime())
        # Use 24h format or AM/PM? TimePicker defaults to system or 24h usually.
        self.viewLayout.addWidget(self.timePicker)
        
        # Category
        self.catCombo = ComboBox(self)
        self.catCombo.addItems(["WORK", "PERSONAL", "OTHER"])
        self.viewLayout.addWidget(self.catCombo)
        
        # Buttons are handled by MessageBoxBase (yesButton, cancelButton)
        self.yesButton.setText("Save")
        self.cancelButton.setText("Cancel")
        
        self.widget.setMinimumWidth(350)
        
    def get_data(self):
        title = self.titleEdit.text()
        date = self.datePicker.date
        time = self.timePicker.time
        cat = self.catCombo.text()
        
        dt = QDateTime(date, time)
        start = dt.toString("yyyy-MM-dd HH:mm:ss")
        end = dt.addSecs(3600).toString("yyyy-MM-dd HH:mm:ss")
        
        return title, start, end, cat

class ScheduleComponent(QWidget):
    """Component for displaying daily schedule and calendar. Fluent Version."""
    
    def __init__(self):
        super().__init__()
        self.selected_date = QDate.currentDate()
        self._setup_ui()
        self.refresh_events()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # --- Timeline Section ---
        timeline_container = QFrame()
        timeline_container.setStyleSheet("background: transparent;")
        timeline_layout = QVBoxLayout(timeline_container)
        
        # Header
        header_layout = QHBoxLayout()
        self.date_label = QLabel(self.selected_date.toString("dddd, MMMM d"))
        self.date_label.setStyleSheet("color: #e8eaed; font-size: 16px; font-weight: bold; background: transparent;")
        header_layout.addWidget(self.date_label)
        header_layout.addStretch()
        
        add_btn = PushButton("+")
        add_btn.setFixedSize(32, 32)
        add_btn.setCursor(Qt.PointingHandCursor)
        # Custom styling for round button
        add_btn.setStyleSheet("""
            QPushButton { 
                background: rgba(51, 181, 229, 0.1); 
                color: #33b5e5; 
                border-radius: 16px; 
                border: 1px solid #33b5e5; 
                font-size: 18px; 
                font-weight: bold;
            }
            QPushButton:hover { 
                background: rgba(51, 181, 229, 0.2); 
            }
        """)
        add_btn.clicked.connect(self._show_add_event_dialog)
        header_layout.addWidget(add_btn)
        
        timeline_layout.addLayout(header_layout)
        
        # Scrollable Timeline
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.timeline_content = QWidget()
        self.timeline_content.setStyleSheet("background: transparent;")
        self.timeline_layout = QVBoxLayout(self.timeline_content)
        self.timeline_layout.setSpacing(12)
        self.timeline_layout.addStretch()
        
        scroll.setWidget(self.timeline_content)
        timeline_layout.addWidget(scroll, 2) 
        
        layout.addWidget(timeline_container, 2)
        
        # --- Fluent Calendar View ---
        self.calendar = CalendarView()
        # Prevent auto-hide (it assumes popup behavior)
        self.calendar.hide = lambda: None
        self.calendar.close = lambda: None
        
        # Connect date changed signal
        self.calendar.dateChanged.connect(self._on_date_selected)
        
        # Style overrides usually handled by global theme, but we can enforce some if needed
        # Fluent CalendarView generally looks good in dark mode.
        
        layout.addWidget(self.calendar, 1)

    def _on_date_selected(self, date):
        self.selected_date = date
        self.date_label.setText(date.toString("dddd, MMMM d"))
        self.refresh_events()
        
    def refresh_events(self):
        """Clear timeline and load events for selected date."""
        while self.timeline_layout.count() > 1: # Keep stretch
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        date_str = self.selected_date.toString("yyyy-MM-dd")
        events = calendar_manager.get_events(date_str)
        
        if not events:
            empty = QLabel("No events scheduled")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #8b9bb4; padding: 20px; font-style: italic;")
            self.timeline_layout.insertWidget(0, empty)
        else:
            for event in events:
                self._add_event_card(event)

    def _add_event_card(self, event):
        card = QFrame()
        card.setCursor(Qt.PointingHandCursor)
        
        cat = event['category']
        accent_color = "#33b5e5" if "WORK" in cat else "#00c853" if "PERSONAL" in cat else "#aa66cc"
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #111625;
                border-radius: 8px;
                border: 1px solid #1a2236;
                border-left: 3px solid {accent_color};
            }}
            QFrame:hover {{ 
                background-color: #1a2236;
                border: 1px solid {accent_color};
            }}
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Time
        start_dt = datetime.strptime(event['start_time'], "%Y-%m-%d %H:%M:%S")
        time_str = start_dt.strftime("%I:%M %p").lstrip("0")
        
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet(f"color: {accent_color}; font-weight: bold; font-size: 13px; background: transparent; border: none;")
        time_lbl.setFixedWidth(65)
        layout.addWidget(time_lbl)
        
        # Details
        details = QVBoxLayout()
        details.setSpacing(4)
        
        title_lbl = QLabel(event['title'])
        title_lbl.setStyleSheet("color: #e8eaed; font-weight: 500; font-size: 14px; background: transparent; border: none;")
        details.addWidget(title_lbl)
        
        cat_lbl = QLabel(cat)
        cat_lbl.setStyleSheet(f"color: {accent_color}; font-size: 10px; background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px; border: none;")
        cat_lbl.setFixedWidth(cat_lbl.sizeHint().width() + 15)
        details.addWidget(cat_lbl)
        
        layout.addLayout(details)
        layout.addStretch()
        
        # Delete button
        del_btn = QPushButton("×")
        del_btn.setFixedSize(24, 24)
        del_btn.setStyleSheet("""
            QPushButton { color: #6e6e6e; background: transparent; font-size: 18px; border: none; border-radius: 12px; }
            QPushButton:hover { background: rgba(239, 83, 80, 0.2); color: #ef5350; }
        """)
        del_btn.clicked.connect(lambda: self._delete_event(event['id']))
        layout.addWidget(del_btn)
        
        self.timeline_layout.insertWidget(self.timeline_layout.count()-1, card)

    def _delete_event(self, event_id):
        calendar_manager.delete_event(event_id)
        self.refresh_events()
        
    def _show_add_event_dialog(self):
        """Show dialog to create a new event."""
        w = AddEventDialog(self.window())
        if w.exec():
            title, start, end, cat = w.get_data()
            if title:
                calendar_manager.add_event(title, start, end, cat)
                self.refresh_events()
