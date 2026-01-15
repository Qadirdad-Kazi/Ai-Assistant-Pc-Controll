#!/bin/bash

# Wolf Desktop App Launcher
# This script starts the Wolf AI Assistant desktop application

echo "🤖 Starting Wolf AI Desktop Assistant..."

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if virtual environment exists
if [ ! -d "$DIR/venv" ]; then
    echo "❌ Virtual environment not found. Please run the setup first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$DIR/venv/bin/activate"

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python -c "import eel, speech_recognition, pyttsx3, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install eel speech_recognition pyttsx3 requests pyaudio
fi

# Check if Ollama is running
echo "🔍 Checking Ollama status..."
curl -s http://localhost:11434/api/version > /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Ollama is not running on localhost:11434"
    echo "   Please start Ollama or the AI features won't work."
    echo "   You can still use the application, but responses will be limited."
    echo ""
fi

# Start the desktop application
echo "🚀 Launching Wolf Desktop App..."
python "$DIR/Wolf_desktop_app.py"

echo "👋 Wolf Desktop App has closed."