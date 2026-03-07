"""
Tasks Tab - Create and manage tasks using plain English descriptions.
Supports both manual prompts and voice commands for task execution.
"""

import json
import threading
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QListWidgetItem, QSizePolicy, QMenu, QMessageBox, QTextEdit,
    QDialog
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
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        # Header with title and status
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        self.title_label = SubtitleLabel(self.task_data.get('title', 'Untitled Task'))
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(40)
        
        self.status_badge = QLabel(self.task_data.get('status', 'pending'))
        self.status_badge.setStyleSheet("""
            QLabel {
                background-color: rgba(76, 201, 240, 0.2);
                color: #4cc9f0;
                border: 1px solid rgba(76, 201, 240, 0.3);
                border-radius: 8px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
                min-width: 60px;
                max-width: 80px;
            }
        """)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(self.title_label, 1)  # Take available space
        header_layout.addWidget(self.status_badge, 0)  # Fixed size
        
        # Description
        self.description_label = BodyLabel(self.task_data.get('description', ''))
        self.description_label.setWordWrap(True)
        self.description_label.setMaximumHeight(50)
        self.description_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # Action buttons - make them more compact
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(4)
        actions_layout.setContentsMargins(0, 4, 0, 0)
        
        self.execute_btn = PrimaryPushButton("Execute")
        self.execute_btn.setIcon(FIF.PLAY)
        self.execute_btn.setFixedHeight(28)
        self.execute_btn.setMinimumWidth(70)
        self.execute_btn.clicked.connect(lambda: self.execute_requested.emit(self.task_data['id']))
        
        self.edit_btn = PushButton("Edit")
        self.edit_btn.setIcon(FIF.EDIT)
        self.edit_btn.setFixedHeight(28)
        self.edit_btn.setMinimumWidth(60)
        self.edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.task_data['id']))
        
        self.delete_btn = PushButton("Delete")
        self.delete_btn.setIcon(FIF.DELETE)
        self.delete_btn.setFixedHeight(28)
        self.delete_btn.setMinimumWidth(60)
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.task_data['id']))
        
        actions_layout.addWidget(self.execute_btn)
        actions_layout.addWidget(self.edit_btn)
        actions_layout.addWidget(self.delete_btn)
        actions_layout.addStretch()
        
        # Add all to main layout
        layout.addLayout(header_layout)
        layout.addWidget(self.description_label)
        layout.addLayout(actions_layout)
        
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

class TaskDialog(QDialog):
    """Dialog for creating/editing tasks."""
    
    task_saved = Signal(dict)  # task_data
    
    def __init__(self, parent=None, task_data=None):
        super().__init__(parent)
        self.task_data = task_data or {}
        self.setModal(True)
        self.setWindowTitle("Create New Task" if not self.task_data else "Edit Task")
        self.setMinimumSize(500, 400)
        self.resize(500, 400)
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
        
        # Sidebar (task list) - make it responsive
        sidebar = QFrame()
        sidebar.setMinimumWidth(300)
        sidebar.setMaximumWidth(500)
        sidebar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(8)
        
        # Sidebar header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 8)  # Add bottom margin
        
        self.title_label = SubtitleLabel("Tasks")
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        self.add_task_btn = PrimaryPushButton("Add Task")
        self.add_task_btn.setIcon(FIF.ADD)
        self.add_task_btn.setFixedHeight(32)
        self.add_task_btn.setMinimumWidth(80)
        self.add_task_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.add_task_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_task_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Connect button with multiple methods for debugging
        self.add_task_btn.clicked.connect(self._create_task)
        self.add_task_btn.pressed.connect(lambda: print("[TasksTab] Button pressed!"))
        self.add_task_btn.released.connect(lambda: print("[TasksTab] Button released!"))
        
        header_layout.addWidget(self.title_label, 1)  # Take available space
        header_layout.addWidget(self.add_task_btn, 0)  # Fixed size
        
        # Task list with better scrolling
        self.task_list = ListWidget()
        self.task_list.setSpacing(4)
        self.task_list.setStyleSheet("""
            ListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            ListWidget::item {
                background-color: transparent;
                border: none;
                padding: 2px;
                margin: 1px;
            }
            ListWidget::item:selected {
                background-color: rgba(76, 201, 240, 0.1);
                border: 1px solid rgba(76, 201, 240, 0.3);
                border-radius: 6px;
            }
        """)
        
        sidebar_layout.addLayout(header_layout)
        sidebar_layout.addWidget(self.task_list)
        
        # Main content area - make it responsive
        content_area = QFrame()
        content_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)
        
        # Content header
        self.content_title = SubtitleLabel("Select a task to view details")
        self.content_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.content_title.setWordWrap(True)
        
        self.content_description = BodyLabel("Choose a task from the list to execute, edit, or view details.")
        self.content_description.setWordWrap(True)
        
        # Task details area
        self.task_details = ScrollArea()
        self.task_details.setWidgetResizable(True)
        self.task_details.setWidgetResizable(True)
        self.task_details.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.task_details.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.task_details_widget = QWidget()
        self.task_details_layout = QVBoxLayout(self.task_details_widget)
        self.task_details_layout.setContentsMargins(8, 8, 8, 8)
        self.task_details.setWidget(self.task_details_widget)
        
        # Execution log
        self.execution_log = QTextEdit()
        self.execution_log.setPlaceholderText("Task execution results will appear here...")
        self.execution_log.setMaximumHeight(180)
        self.execution_log.setMinimumHeight(120)
        self.execution_log.setReadOnly(True)
        
        content_layout.addWidget(self.content_title)
        content_layout.addWidget(self.content_description)
        content_layout.addWidget(self.task_details)
        content_layout.addWidget(QLabel("Execution Log:"))
        content_layout.addWidget(self.execution_log)
        
        # Add to main layout with responsive sizing
        main_layout.addWidget(sidebar, 0)  # Sidebar takes minimal space
        main_layout.addWidget(content_area, 1)  # Content takes remaining space
    
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
            # Load tasks from the function executor's tasks file
            from core.function_executor import executor as function_executor
            self.tasks = function_executor.tasks.copy()
            self._refresh_task_list()
            print(f"[TasksTab] Loaded {len(self.tasks)} tasks from database")
        except Exception as e:
            print(f"[TasksTab] Error loading tasks: {e}")
            self.tasks = []
            self._refresh_task_list()
    
    def _refresh_task_list(self):
        """Refresh the task list display."""
        self.task_list.clear()
        
        for task in self.tasks:
            item = QListWidgetItem(self.task_list)
            task_widget = TaskItem(task)
            task_widget.execute_requested.connect(self._execute_task)
            task_widget.delete_requested.connect(self._delete_task)
            task_widget.edit_requested.connect(self._edit_task)
            
            # Calculate proper size hint based on content
            task_widget.adjustSize()
            size_hint = task_widget.sizeHint()
            # Ensure minimum height but allow expansion for long content
            size_hint.setHeight(max(size_hint.height(), 120))
            # Limit maximum width to prevent overflow
            size_hint.setWidth(min(size_hint.width(), self.task_list.width() - 20))
            
            item.setSizeHint(size_hint)
            self.task_list.setItemWidget(item, task_widget)
    
    def _create_task(self):
        """Create a new task."""
        print("[TasksTab] Add Task button clicked!")  # Debug print
        try:
            dialog = TaskDialog(self)
            dialog.task_saved.connect(self._save_task)
            result = dialog.exec()  # Use exec() for modal dialog
            print(f"[TasksTab] Dialog closed with result: {result}")
        except Exception as e:
            print(f"[TasksTab] Error creating task dialog: {e}")
            import traceback
            traceback.print_exc()
    
    def _edit_task(self, task_id):
        """Edit an existing task."""
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        if task:
            dialog = TaskDialog(self, task)
            dialog.task_saved.connect(self._save_task)
            dialog.exec()  # Use exec() for modal dialog
    
    def _save_task(self, task_data):
        """Save a task (create or update)."""
        try:
            # Save to function executor's tasks
            from core.function_executor import executor as function_executor
            
            existing_index = next((i for i, t in enumerate(function_executor.tasks) if t['id'] == task_data['id']), None)
            
            if existing_index is not None:
                function_executor.tasks[existing_index] = task_data
            else:
                function_executor.tasks.append(task_data)
            
            # Save to file
            function_executor._save_tasks()
            
            # Update local copy and refresh
            self.tasks = function_executor.tasks.copy()
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
        except Exception as e:
            print(f"[TasksTab] Error saving task: {e}")
            InfoBar.error(
                title="Save Failed",
                content=f"Failed to save task: {str(e)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
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
            try:
                # Delete from function executor's tasks
                from core.function_executor import executor as function_executor
                
                function_executor.tasks = [t for t in function_executor.tasks if t['id'] != task_id]
                function_executor._save_tasks()
                
                # Update local copy and refresh
                self.tasks = function_executor.tasks.copy()
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
            except Exception as e:
                print(f"[TasksTab] Error deleting task: {e}")
                InfoBar.error(
                    title="Delete Failed",
                    content=f"Failed to delete task: {str(e)}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
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
