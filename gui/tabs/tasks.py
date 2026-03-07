"""
Tasks Tab - Create and manage tasks using plain English descriptions.
Supports both manual prompts and voice commands for task execution.
"""

import json
import threading
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QListWidgetItem, QSizePolicy, QMenu, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QColor

from qfluentwidgets import (
    PrimaryPushButton, PushButton, TransparentToolButton,
    LineEdit, SwitchButton, ListWidget, ScrollArea, CardWidget,
    FluentIcon as FIF, Action, RoundMenu, InfoBar, InfoBarPosition,
    SubtitleLabel, BodyLabel, CaptionLabel, ProgressBar, CheckBox
)

from core.database import db
from core.function_executor import executor as function_executor
from core.llm import route_query
from gui.components.message_bubble import MessageBubble

# --- Theme Constants ---
THEME_GLASS_SIDEBAR = "rgba(5, 8, 13, 0.6)"
THEME_BORDER = "rgba(76, 201, 240, 0.3)" # Neon Cyan
THEME_HIGHLIGHT = "rgba(76, 201, 240, 0.1)"
THEME_TEXT_MAIN = "#e8eaed"
THEME_TEXT_SUB = "#8b9bb4"

class TaskItem(CardWidget):
    """Individual task item widget."""
    
    execute_requested = Signal(str)  # task_id
    delete_requested = Signal(str)   # task_id
    edit_requested = Signal(str)     # task_id
    
    def __init__(self, task_data):
        super().__init__()
        self.task_data = task_data
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header with title and status
        header_layout = QHBoxLayout()
        
        self.title_label = SubtitleLabel(self.task_data.get('title', 'Untitled Task'))
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        
        self.status_badge = QLabel(self.task_data.get('status', 'pending'))
        self.status_badge.setStyleSheet("""
            QLabel {
                background-color: rgba(76, 201, 240, 0.2);
                color: #4cc9f0;
                border: 1px solid rgba(76, 201, 240, 0.3);
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_badge)
        
        # Description
        self.description_label = BodyLabel(self.task_data.get('description', ''))
        self.description_label.setWordWrap(True)
        self.description_label.setMaximumHeight(60)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.execute_btn = PrimaryPushButton("Execute")
        self.execute_btn.setIcon(FIF.PLAY)
        self.execute_btn.clicked.connect(lambda: self.execute_requested.emit(self.task_data['id']))
        
        self.edit_btn = PushButton("Edit")
        self.edit_btn.setIcon(FIF.EDIT)
        self.edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.task_data['id']))
        
        self.delete_btn = PushButton("Delete")
        self.delete_btn.setIcon(FIF.DELETE)
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.task_data['id']))
        
        actions_layout.addWidget(self.execute_btn)
        actions_layout.addWidget(self.edit_btn)
        actions_layout.addWidget(self.delete_btn)
        actions_layout.addStretch()
        
        # Add all to main layout
        layout.addLayout(header_layout)
        layout.addWidget(self.description_label)
        layout.addLayout(actions_layout)
        
        # Update status appearance
        self._update_status_appearance()
    
    def _apply_styles(self):
        self.setStyleSheet("""
            CardWidget {
                background-color: rgba(5, 8, 13, 0.8);
                border: 1px solid rgba(76, 201, 240, 0.2);
                border-radius: 8px;
                margin: 4px;
            }
            CardWidget:hover {
                border: 1px solid rgba(76, 201, 240, 0.4);
                background-color: rgba(76, 201, 240, 0.05);
            }
        """)
    
    def _update_status_appearance(self):
        status = self.task_data.get('status', 'pending')
        if status == 'completed':
            self.status_badge.setText("✓ Completed")
            self.status_badge.setStyleSheet("""
                QLabel {
                    background-color: rgba(76, 240, 140, 0.2);
                    color: #4cf08c;
                    border: 1px solid rgba(76, 240, 140, 0.3);
                    border-radius: 12px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            self.execute_btn.setEnabled(False)
        elif status == 'failed':
            self.status_badge.setText("✗ Failed")
            self.status_badge.setStyleSheet("""
                QLabel {
                    background-color: rgba(240, 76, 76, 0.2);
                    color: #f04c4c;
                    border: 1px solid rgba(240, 76, 76, 0.3);
                    border-radius: 12px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
    
    def update_status(self, status):
        self.task_data['status'] = status
        self._update_status_appearance()

class TaskDialog(QWidget):
    """Dialog for creating/editing tasks."""
    
    task_saved = Signal(dict)  # task_data
    
    def __init__(self, parent=None, task_data=None):
        super().__init__(parent)
        self.task_data = task_data or {}
        self._setup_ui()
        self._apply_styles()
        self._load_data()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title
        self.title_label = SubtitleLabel("Create New Task" if not self.task_data else "Edit Task")
        layout.addWidget(self.title_label)
        
        # Task title
        title_layout = QVBoxLayout()
        title_label = BodyLabel("Task Title:")
        self.title_input = LineEdit()
        self.title_input.setPlaceholderText("e.g., Open Visual Studio Code and create new project")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)
        layout.addLayout(title_layout)
        
        # Task description
        desc_layout = QVBoxLayout()
        desc_label = BodyLabel("Description (Plain English):")
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText(
            "Describe what you want to do in plain English. Examples:\n"
            "• 'Open Spotify and play my workout playlist'\n"
            "• 'Increase volume to 50%'\n"
            "• 'Open Chrome and go to youtube.com'\n"
            "• 'Lock the computer after 5 minutes'"
        )
        self.desc_input.setMaximumHeight(120)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = PrimaryPushButton("Save Task")
        self.save_btn.setIcon(FIF.SAVE)
        self.save_btn.clicked.connect(self._save_task)
        
        self.cancel_btn = PushButton("Cancel")
        self.cancel_btn.setIcon(FIF.CANCEL)
        self.cancel_btn.clicked.connect(self.close)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)
        layout.addLayout(buttons_layout)
    
    def _apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(5, 8, 13, 0.95);
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
            QLineEdit, QTextEdit {{
                background-color: rgba(76, 201, 240, 0.05);
                border: 1px solid {THEME_BORDER};
                border-radius: 6px;
                padding: 8px;
                color: {THEME_TEXT_MAIN};
                font-size: 13px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 1px solid #4cc9f0;
                background-color: rgba(76, 201, 240, 0.1);
            }}
        """)
    
    def _load_data(self):
        if self.task_data:
            self.title_input.setText(self.task_data.get('title', ''))
            self.desc_input.setPlainText(self.task_data.get('description', ''))
    
    def _save_task(self):
        title = self.title_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        
        if not title or not description:
            InfoBar.warning(
                title="Missing Information",
                content="Please fill in both title and description.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        task_data = {
            'id': self.task_data.get('id', f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            'title': title,
            'description': description,
            'status': self.task_data.get('status', 'pending'),
            'created_at': self.task_data.get('created_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat()
        }
        
        self.task_saved.emit(task_data)
        self.close()

class TasksTab(QWidget):
    """Tasks Tab - Create and manage tasks."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("tasksInterface")
        self.tasks = []
        self._setup_ui()
        self._apply_styles()
        self._load_tasks()
    
    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar (task list)
        sidebar = QFrame()
        sidebar.setMaximumWidth(400)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        
        # Sidebar header
        header_layout = QHBoxLayout()
        self.title_label = SubtitleLabel("Tasks")
        self.title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        
        self.add_task_btn = PrimaryPushButton("Add Task")
        self.add_task_btn.setIcon(FIF.ADD)
        self.add_task_btn.clicked.connect(self._create_task)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_task_btn)
        
        # Task list
        self.task_list = ListWidget()
        self.task_list.setStyleSheet("""
            ListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            ListWidget::item {
                background-color: transparent;
                border: none;
                padding: 4px;
            }
            ListWidget::item:selected {
                background-color: rgba(76, 201, 240, 0.1);
                border: 1px solid rgba(76, 201, 240, 0.3);
                border-radius: 6px;
            }
        """)
        
        sidebar_layout.addLayout(header_layout)
        sidebar_layout.addWidget(self.task_list)
        
        # Main content area
        content_area = QFrame()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(24, 24, 24, 24)
        
        # Content header
        self.content_title = SubtitleLabel("Select a task to view details")
        self.content_description = BodyLabel("Choose a task from the list to execute, edit, or view details.")
        
        # Task details area
        self.task_details = ScrollArea()
        self.task_details.setWidgetResizable(True)
        self.task_details_widget = QWidget()
        self.task_details_layout = QVBoxLayout(self.task_details_widget)
        self.task_details.setWidget(self.task_details_widget)
        
        # Execution log
        self.execution_log = QTextEdit()
        self.execution_log.setPlaceholderText("Task execution results will appear here...")
        self.execution_log.setMaximumHeight(200)
        self.execution_log.setReadOnly(True)
        
        content_layout.addWidget(self.content_title)
        content_layout.addWidget(self.content_description)
        content_layout.addWidget(self.task_details)
        content_layout.addWidget(QLabel("Execution Log:"))
        content_layout.addWidget(self.execution_log)
        
        # Add to main layout
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_area)
        
        # Set stretch factors
        main_layout.setStretchFactor(sidebar, 0)
        main_layout.setStretchFactor(content_area, 1)
    
    def _apply_styles(self):
        self.setStyleSheet(f"""
            TasksTab {{
                background-color: transparent;
            }}
            QFrame {{
                background-color: rgba(5, 8, 13, 0.6);
                border: 1px solid {THEME_BORDER};
                border-radius: 8px;
            }}
            QTextEdit {{
                background-color: rgba(76, 201, 240, 0.05);
                border: 1px solid {THEME_BORDER};
                border-radius: 6px;
                padding: 8px;
                color: {THEME_TEXT_MAIN};
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }}
        """)
    
    def _load_tasks(self):
        """Load tasks from database."""
        try:
            # For now, create some example tasks
            # In a real implementation, this would load from a database
            self.tasks = [
                {
                    'id': 'task_001',
                    'title': 'Open Development Environment',
                    'description': 'Open Visual Studio Code and create a new Python project',
                    'status': 'pending',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                },
                {
                    'id': 'task_002', 
                    'title': 'Music Setup',
                    'description': 'Open Spotify and play my workout playlist',
                    'status': 'pending',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            ]
            self._refresh_task_list()
        except Exception as e:
            print(f"[TasksTab] Error loading tasks: {e}")
    
    def _refresh_task_list(self):
        """Refresh the task list display."""
        self.task_list.clear()
        
        for task in self.tasks:
            item = QListWidgetItem(self.task_list)
            task_widget = TaskItem(task)
            task_widget.execute_requested.connect(self._execute_task)
            task_widget.delete_requested.connect(self._delete_task)
            task_widget.edit_requested.connect(self._edit_task)
            
            item.setSizeHint(task_widget.sizeHint())
            self.task_list.setItemWidget(item, task_widget)
    
    def _create_task(self):
        """Create a new task."""
        dialog = TaskDialog(self)
        dialog.task_saved.connect(self._save_task)
        dialog.show()
    
    def _edit_task(self, task_id):
        """Edit an existing task."""
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        if task:
            dialog = TaskDialog(self, task)
            dialog.task_saved.connect(self._save_task)
            dialog.show()
    
    def _save_task(self, task_data):
        """Save a task (create or update)."""
        existing_index = next((i for i, t in enumerate(self.tasks) if t['id'] == task_data['id']), None)
        
        if existing_index is not None:
            self.tasks[existing_index] = task_data
        else:
            self.tasks.append(task_data)
        
        self._refresh_task_list()
        
        InfoBar.success(
            title="Task Saved",
            content=f"Task '{task_data['title']}' has been saved successfully.",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
    
    def _delete_task(self, task_id):
        """Delete a task."""
        reply = QMessageBox.question(
            self, 'Delete Task', 'Are you sure you want to delete this task?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.tasks = [t for t in self.tasks if t['id'] != task_id]
            self._refresh_task_list()
            
            InfoBar.success(
                title="Task Deleted",
                content="The task has been deleted successfully.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def _execute_task(self, task_id):
        """Execute a task."""
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        if not task:
            return
        
        # Update UI to show execution
        self.content_title.setText(f"Executing: {task['title']}")
        self.content_description.setText("Processing task...")
        self.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting task execution...")
        
        # Execute in background thread
        thread = threading.Thread(target=self._execute_task_thread, args=(task,), daemon=True)
        thread.start()
    
    def _execute_task_thread(self, task):
        """Execute task in background thread."""
        try:
            description = task['description']
            
            # Route the task description through the existing system
            func_name, params = route_query(description)
            
            # Log the routing result
            self.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Routed to: {func_name}")
            self.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Parameters: {params}")
            
            # Execute the function
            result = function_executor.execute(func_name, params)
            
            # Update task status based on result
            if result.get('success', False):
                task['status'] = 'completed'
                self.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Task completed successfully")
                self.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Result: {result.get('message', 'Success')}")
            else:
                task['status'] = 'failed'
                self.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Task failed")
                self.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {result.get('message', 'Unknown error')}")
            
            task['updated_at'] = datetime.now().isoformat()
            
            # Update UI in main thread
            QTimer.singleShot(0, lambda: self._task_execution_complete(task, result))
            
        except Exception as e:
            task['status'] = 'failed'
            task['updated_at'] = datetime.now().isoformat()
            
            self.execution_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Exception during execution: {str(e)}")
            QTimer.singleShot(0, lambda: self._task_execution_complete(task, {'success': False, 'message': str(e)}))
    
    def _task_execution_complete(self, task, result):
        """Handle task execution completion."""
        # Update task in list
        for i, t in enumerate(self.tasks):
            if t['id'] == task['id']:
                self.tasks[i] = task
                break
        
        self._refresh_task_list()
        
        # Update content area
        if result.get('success', False):
            self.content_title.setText(f"✓ Completed: {task['title']}")
            self.content_description.setText("Task executed successfully!")
        else:
            self.content_title.setText(f"✗ Failed: {task['title']}")
            self.content_description.setText(f"Task failed: {result.get('message', 'Unknown error')}")
        
        # Show notification
        if result.get('success', False):
            InfoBar.success(
                title="Task Completed",
                content=f"Task '{task['title']}' executed successfully.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.error(
                title="Task Failed",
                content=f"Task '{task['title']}' failed to execute.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
