@echo off
echo Starting JARIS Web GUI...

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Please run setup first:
    echo    python setup.py
    pause
    exit /b 1
)

REM Activate virtual environment and run JARIS Web GUI
call venv\Scripts\activate.bat
python jaris_web_gui.py
pause
