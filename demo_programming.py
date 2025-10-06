#!/usr/bin/env python3
"""
Demo Programming Functionality
Shows what the AI Agent can do for programming
"""

def demo_programming_capabilities():
    """Demo the programming capabilities"""
    print("🤖 JARIS AI Agent - Programming Capabilities Demo")
    print("=" * 60)
    
    print("🎯 What JARIS AI Agent Can Do:")
    print("• Natural language programming commands")
    print("• Automatic VS Code opening")
    print("• File creation with visible typing")
    print("• Code generation with AI")
    print("• Project setup and configuration")
    print("• Framework-specific scaffolding")
    
    print("\n📋 Example Commands You Can Try:")
    
    # HTML/CSS Examples
    print("\n🌐 HTML/CSS Development:")
    html_examples = [
        "Create a simple HTML contact form",
        "Generate an HTML login form with CSS styling",
        "Make a responsive landing page",
        "Create an HTML portfolio website",
        "Build an HTML5 game interface"
    ]
    for i, example in enumerate(html_examples, 1):
        print(f"  {i}. {example}")
    
    # React Examples
    print("\n⚛️ React Development:")
    react_examples = [
        "Create a React login form with modern styling",
        "Make a React dashboard with charts",
        "Generate a React Native signup screen",
        "Build a React portfolio with animations",
        "Create a React todo app with state management"
    ]
    for i, example in enumerate(react_examples, 1):
        print(f"  {i}. {example}")
    
    # Backend Examples
    print("\n🟢 Backend Development:")
    backend_examples = [
        "Create a Python Flask API with authentication",
        "Generate a Node.js Express server with MongoDB",
        "Make a Python Django blog with admin panel",
        "Build a REST API with documentation",
        "Create a Python data analysis script"
    ]
    for i, example in enumerate(backend_examples, 1):
        print(f"  {i}. {example}")
    
    # Full-Stack Examples
    print("\n🚀 Full-Stack Development:")
    fullstack_examples = [
        "Create a MERN stack e-commerce site",
        "Generate a Vue.js dashboard with backend",
        "Make a Python Django blog with React frontend",
        "Build a React Native mobile app",
        "Create a Next.js full-stack application"
    ]
    for i, example in enumerate(fullstack_examples, 1):
        print(f"  {i}. {example}")
    
    print("\n🔧 How to Test:")
    print("1. Run: python3 jaris_ai_agent.py")
    print("2. Give any of the commands above")
    print("3. Watch it open VS Code and type code!")
    
    print("\n🌐 Or Test via Web GUI:")
    print("1. Go to: http://localhost:8080")
    print("2. Use '💻 PC Control' tab")
    print("3. Try commands like:")
    print("   - 'create folder MyProject'")
    print("   - 'create file hello.html with <h1>Hello</h1>'")
    print("   - 'list files'")
    print("   - 'open downloads'")

def show_web_gui_commands():
    """Show specific commands for web GUI testing"""
    print("\n🌐 Web GUI Programming Commands:")
    print("=" * 40)
    
    print("📋 Commands to try in the Web GUI (PC Control tab):")
    
    # File Operations
    print("\n📁 File Operations:")
    file_commands = [
        "create folder MyProject",
        "create folder ReactApp in desktop",
        "create file index.html with <!DOCTYPE html><html><head><title>My App</title></head><body><h1>Hello World</h1></body></html>",
        "create file style.css with body { font-family: Arial; margin: 20px; }",
        "list files",
        "list files desktop",
        "open downloads",
        "open desktop"
    ]
    for i, cmd in enumerate(file_commands, 1):
        print(f"  {i}. {cmd}")
    
    # System Commands
    print("\n💻 System Commands:")
    system_commands = [
        "screenshot",
        "system info",
        "volume up",
        "volume down",
        "brightness up",
        "brightness down",
        "execute python --version",
        "execute ls -la"
    ]
    for i, cmd in enumerate(system_commands, 1):
        print(f"  {i}. {cmd}")
    
    # Voice Commands
    print("\n🎤 Voice Commands (click 🎤 button):")
    voice_commands = [
        "Create folder MyProject",
        "List files",
        "Take a screenshot",
        "Open downloads",
        "System information",
        "Volume up",
        "Create file hello.txt"
    ]
    for i, cmd in enumerate(voice_commands, 1):
        print(f"  {i}. {cmd}")

def main():
    """Main demo function"""
    demo_programming_capabilities()
    show_web_gui_commands()
    
    print("\n🎊 Ready to test programming functionality!")
    print("Choose your method:")
    print("• Direct AI Agent: python3 jaris_ai_agent.py")
    print("• Web GUI: http://localhost:8080")
    print("• Test Script: python3 test_programming.py")

if __name__ == "__main__":
    main()
