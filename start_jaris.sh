#!/bin/bash
# JARIS Launcher Script

echo "🚀 Starting JARIS..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python3 setup.py"
    exit 1
fi

# Activate virtual environment and run JARIS
source venv/bin/activate
python jaris_ai_assistant.py
