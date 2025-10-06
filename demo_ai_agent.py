#!/usr/bin/env python3
"""
JARIS AI Agent Demo
Demonstrates desktop automation capabilities
"""

import os
import sys
import time
import subprocess
import platform

def demo_automation():
    """Demo the automation capabilities"""
    print("🤖 JARIS AI Agent Demo")
    print("=" * 50)
    
    print("🎯 Capabilities:")
    print("• Natural language command interpretation")
    print("• Automatic VS Code opening")
    print("• File creation with visible typing")
    print("• Code generation with AI")
    print("• Terminal command execution")
    print("• Visual feedback for all actions")
    
    print("\n📋 Example Commands:")
    examples = [
        "Create a React login form with modern styling",
        "Generate an HTML contact form with validation",
        "Make a Python Flask API with user authentication",
        "Create a Node.js Express server with MongoDB",
        "Build a Vue.js dashboard with charts",
        "Generate a Python data analysis script"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"  {i}. {example}")
    
    print("\n🔧 Technical Features:")
    print("• AI-powered command interpretation")
    print("• PyAutoGUI for desktop automation")
    print("• Real-time code typing simulation")
    print("• Framework-specific project setup")
    print("• Production-ready code generation")
    print("• Visual progress indicators")
    
    print("\n🚀 How it works:")
    print("1. User gives natural language command")
    print("2. AI interprets command and generates plan")
    print("3. Opens VS Code automatically")
    print("4. Creates project structure")
    print("5. Types code character by character")
    print("6. Runs setup commands")
    print("7. Shows completion status")
    
    print("\n💡 Ready to test!")
    print("Run: python3 jaris_ai_agent.py")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'requests', 'pyautogui', 'pyperclip', 'pynput'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements_automation.txt")
        return False
    else:
        print("\n✅ All dependencies available!")
        return True

def test_vscode():
    """Test VS Code availability"""
    print("\n🔍 Checking VS Code...")
    
    if platform.system() == "Darwin":  # macOS
        vscode_path = "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
        if os.path.exists(vscode_path):
            print("✅ VS Code found")
            return True
        else:
            print("❌ VS Code not found")
            return False
    else:
        # Try to run 'code' command
        try:
            subprocess.run(["code", "--version"], check=True, capture_output=True)
            print("✅ VS Code available")
            return True
        except:
            print("❌ VS Code not in PATH")
            return False

def main():
    """Main demo function"""
    print("🎬 JARIS AI Agent Demo")
    print("=" * 60)
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Check VS Code
    vscode_ok = test_vscode()
    
    # Show demo
    demo_automation()
    
    print("\n📊 Status:")
    print(f"• Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"• VS Code: {'✅' if vscode_ok else '❌'}")
    
    if deps_ok and vscode_ok:
        print("\n🚀 Ready to run JARIS AI Agent!")
        print("Execute: python3 jaris_ai_agent.py")
    else:
        print("\n⚠️ Please install missing dependencies first")
        print("Run: pip install -r requirements_automation.txt")

if __name__ == "__main__":
    main()
