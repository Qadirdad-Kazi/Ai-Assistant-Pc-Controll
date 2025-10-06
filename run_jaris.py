#!/usr/bin/env python3
"""
JARIS Launcher Script
This script checks dependencies and launches JARIS
"""

import sys
import subprocess
import importlib.util

def check_dependency(module_name, package_name=None):
    """Check if a Python module is available"""
    if package_name is None:
        package_name = module_name
    
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        print(f"❌ Missing dependency: {package_name}")
        print(f"   Install with: pip install {package_name}")
        return False
    return True

def check_ollama():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            return True
    except:
        pass
    
    print("❌ Ollama is not running")
    print("   Please start Ollama: ollama serve")
    print("   Or install Ollama from: https://ollama.ai/")
    return False

def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    
    print("Creating virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install missing dependencies in virtual environment"""
    if not os.path.exists("venv"):
        if not create_virtual_environment():
            return False
    
    # Determine the correct pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:  # Unix/Linux/macOS
        pip_path = os.path.join("venv", "bin", "pip")
    
    print("Installing dependencies...")
    try:
        subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main launcher function"""
    print("🚀 JARIS Launcher")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Check dependencies
    dependencies = [
        ("requests", "requests"),
        ("speech_recognition", "speechrecognition"),
        ("pyttsx3", "pyttsx3"),
    ]
    
    missing_deps = []
    for module, package in dependencies:
        if not check_dependency(module, package):
            missing_deps.append(package)
    
    if missing_deps:
        print(f"\n📦 Installing missing dependencies: {', '.join(missing_deps)}")
        if not install_dependencies():
            print("❌ Failed to install dependencies. Please install manually:")
            print(f"   pip install {' '.join(missing_deps)}")
            sys.exit(1)
    
    # Check Ollama
    print("\n🔍 Checking Ollama...")
    if not check_ollama():
        print("\n⚠️  Ollama is not running, but you can still use JARIS")
        print("   Some features may not work without Ollama")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Launch JARIS
    print("\n🎯 Launching JARIS...")
    try:
        # Determine the correct python path based on OS
        if os.name == 'nt':  # Windows
            python_path = os.path.join("venv", "Scripts", "python")
        else:  # Unix/Linux/macOS
            python_path = os.path.join("venv", "bin", "python")
        
        # Run JARIS using the virtual environment
        subprocess.run([python_path, "jaris_ai_assistant.py"])
    except Exception as e:
        print(f"❌ Error launching JARIS: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
