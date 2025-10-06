#!/usr/bin/env python3
"""
JARIS Setup Script
Installs dependencies and sets up the environment
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"   Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def create_virtual_environment():
    """Create a virtual environment"""
    venv_path = "venv"
    if os.path.exists(venv_path):
        print("✅ Virtual environment already exists")
        return True
    
    return run_command(f"{sys.executable} -m venv {venv_path}", "Creating virtual environment")

def install_requirements():
    """Install Python requirements in virtual environment"""
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        return False
    
    # Determine the correct pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = "venv/Scripts/pip"
    else:  # Unix/Linux/macOS
        pip_path = "venv/bin/pip"
    
    return run_command(f"{pip_path} install -r requirements.txt", "Installing Python dependencies")

def check_ollama():
    """Check if Ollama is available"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            return True
    except:
        pass
    
    print("⚠️  Ollama is not running")
    print("   To use AI features, please:")
    print("   1. Install Ollama from https://ollama.ai/")
    print("   2. Start Ollama: ollama serve")
    print("   3. Pull a model: ollama pull llama3.2:latest")
    return False

def create_launcher_script():
    """Create a simple launcher script"""
    launcher_content = '''#!/bin/bash
# JARIS Launcher Script

echo "🚀 Starting JARIS..."
python3 jaris_ai_assistant.py
'''
    
    with open("start_jaris.sh", "w") as f:
        f.write(launcher_content)
    
    # Make it executable
    os.chmod("start_jaris.sh", 0o755)
    print("✅ Created launcher script: start_jaris.sh")

def main():
    """Main setup function"""
    print("🔧 JARIS Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        print("❌ Setup failed during virtual environment creation")
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Check Ollama
    print("\n🔍 Checking Ollama...")
    check_ollama()
    
    # Create launcher script
    print("\n📝 Creating launcher script...")
    create_launcher_script()
    
    print("\n🎉 Setup completed!")
    print("\nTo run JARIS:")
    print("  # Activate virtual environment first:")
    if os.name == 'nt':  # Windows
        print("  venv\\Scripts\\activate")
        print("  python jaris_ai_assistant.py")
    else:  # Unix/Linux/macOS
        print("  source venv/bin/activate")
        print("  python jaris_ai_assistant.py")
    print("  or")
    print("  ./start_jaris.sh")
    print("\nFor voice features, make sure your microphone is working.")
    print("For AI features, make sure Ollama is running.")

if __name__ == "__main__":
    main()
