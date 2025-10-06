#!/bin/bash
# JARIS Web GUI Launcher Script

echo "🚀 Starting JARIS Web GUI..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python3 setup.py"
    exit 1
fi

# Activate virtual environment and run JARIS Web GUI
source venv/bin/activate
python3 jaris_web_gui.py
