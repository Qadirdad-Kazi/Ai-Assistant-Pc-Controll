# PC Controller Module Documentation

## Overview
The `PCController` class is a powerful system control module that provides an interface for interacting with the operating system, managing applications, and controlling input devices. It's designed to be cross-platform, with special handling for Windows, macOS, and Linux systems.

## Features

### System Control
- Launch applications
- Open URLs in default browser
- Manage windows (minimize, maximize, close)
- Control system volume
- Take screenshots
- Perform OCR on screen content
- Get active window information
- Control system power (shutdown, restart, sleep)

### Input Device Control
- Move mouse cursor
- Click mouse buttons (left, right, middle)
- Type text
- Press special keys and key combinations
- Control media playback

### AI Integration
- Execute AI-powered tasks
- Handle natural language commands
- Generate and execute code
- Process screen content with OCR

## Installation

### Prerequisites
- Python 3.7+
- Required packages (install via `pip install -r requirements.txt`):
  - `pyautogui`
  - `keyboard`
  - `psutil`
  - `pytesseract` (for OCR)
  - `Pillow` (for image processing)
  - `requests` (for web requests)

## Usage

### Initialization
```python
from pc_controller import PCController

# Create a new controller instance
controller = PCController()
```

### Basic Commands

#### Launch Applications
```python
# Launch an application by name
result = controller.execute_command("open chrome")
print(result['message'])
```

#### Control Windows
```python
# Minimize current window
result = controller.execute_command("minimize window")

# Maximize window
result = controller.execute_command("maximize window")

# Close current window
result = controller.execute_command("close window")
```

#### Mouse Control
```python
# Move mouse to coordinates (x, y)
controller.move_mouse_to_coordinates(100, 200)

# Left click at current position
controller.click_mouse_button(button='left')

# Right click at specific coordinates
controller.click_mouse_button(x=150, y=300, button='right')

# Double click
controller.click_mouse_button(clicks=2)
```

#### Keyboard Control
```python
# Type text
controller.type_keyboard_input("Hello, World!")

# Press special keys
controller.press_special_keys(['ctrl', 'c'])  # Copy
controller.press_special_keys(['alt', 'tab'])  # Switch windows
controller.press_special_keys('volumedown')   # Media control
```

#### System Control
```python
# Take a screenshot
screenshot = controller.take_screenshot()
print(f"Screenshot saved to: {screenshot['filepath']}")

# Get active window info
window_info = controller.get_active_window_info()
print(f"Active window: {window_info.get('title')}")

# Shutdown system (requires confirmation)
# controller.execute_command("shutdown computer")
```

## Advanced Usage

### AI-Powered Tasks
```python
# Execute a task using AI
task_result = controller.execute_ai_task(
    "Create a simple calculator in Python"
)
print(task_result['message'])
```

### Screen Content Analysis
```python
# Get text from screen using OCR
scan_result = controller.scan_screen(ocr=True)
if scan_result['success'] and 'text' in scan_result:
    print("Detected text:", scan_result['text'])
```

## Error Handling
All methods return a dictionary with a `success` boolean and a `message` string. In case of errors, additional details are available in the `details` key.

```python
result = controller.execute_command("open nonexistent_app")
if not result['success']:
    print(f"Error: {result['message']}")
    if 'details' in result:
        print("Error details:", result['details'])
```

## Security Considerations
- The controller has access to system functions; use with caution
- Some operations may require elevated privileges
- Be cautious when executing AI-generated code or commands
- The screen reader feature may capture sensitive information

## Troubleshooting
- If mouse/keyboard control doesn't work, check if the application has the necessary permissions
- For OCR functionality, ensure Tesseract OCR is installed and in your system PATH
- On macOS, you may need to grant "Accessibility" and "Screen Recording" permissions

## License
[Specify your license here]
