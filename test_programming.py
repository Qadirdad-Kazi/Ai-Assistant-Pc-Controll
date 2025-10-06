#!/usr/bin/env python3
"""
Test Programming Functionality
Demonstrates the AI Agent's programming capabilities
"""

import os
import sys
import time
import subprocess
from jaris_ai_agent import JARISAIAgent

def test_programming_commands():
    """Test various programming commands"""
    print("🧪 Testing JARIS AI Agent Programming Functionality")
    print("=" * 60)
    
    # Initialize the AI Agent
    agent = JARISAIAgent()
    
    # Test commands
    test_commands = [
        "Create a simple HTML contact form",
        "Generate an HTML login form with CSS styling",
        "Make a React login component",
        "Create a Python Flask API endpoint"
    ]
    
    print("🎯 Available Test Commands:")
    for i, cmd in enumerate(test_commands, 1):
        print(f"  {i}. {cmd}")
    
    print("\n💡 Choose a command to test (1-4) or 'all' for all commands:")
    choice = input("Enter choice: ").strip()
    
    if choice.lower() == 'all':
        # Test all commands
        for i, command in enumerate(test_commands, 1):
            print(f"\n{'='*60}")
            print(f"🧪 Test {i}: {command}")
            print(f"{'='*60}")
            
            try:
                success = agent.process_command(command)
                if success:
                    print(f"✅ Test {i} completed successfully!")
                else:
                    print(f"❌ Test {i} failed!")
            except Exception as e:
                print(f"❌ Test {i} error: {e}")
            
            print("\n⏳ Waiting 3 seconds before next test...")
            time.sleep(3)
    
    elif choice.isdigit() and 1 <= int(choice) <= len(test_commands):
        # Test specific command
        command = test_commands[int(choice) - 1]
        print(f"\n🧪 Testing: {command}")
        print("=" * 60)
        
        try:
            success = agent.process_command(command)
            if success:
                print("✅ Test completed successfully!")
            else:
                print("❌ Test failed!")
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    else:
        print("❌ Invalid choice. Please run again and choose 1-4 or 'all'")

def test_web_gui_programming():
    """Test programming functionality through the web GUI"""
    print("\n🌐 Testing Programming via Web GUI")
    print("=" * 40)
    
    print("📋 Steps to test programming in Web GUI:")
    print("1. Open browser to: http://localhost:8080")
    print("2. Go to '💻 PC Control' tab")
    print("3. Try these commands:")
    print("   - 'create folder MyProject'")
    print("   - 'create file hello.html with <h1>Hello World</h1>'")
    print("   - 'list files'")
    print("   - 'open downloads'")
    print("4. Use voice commands with 🎤 button")
    print("5. Try continuous listening with 🔄 button")
    
    print("\n🎯 Programming-specific commands to try:")
    programming_commands = [
        "create folder ReactProject",
        "create file index.html with <!DOCTYPE html><html><head><title>My App</title></head><body><h1>Hello World</h1></body></html>",
        "create file style.css with body { font-family: Arial; margin: 20px; }",
        "list files",
        "open downloads",
        "screenshot"
    ]
    
    for i, cmd in enumerate(programming_commands, 1):
        print(f"  {i}. {cmd}")

def main():
    """Main test function"""
    print("🤖 JARIS Programming Functionality Test")
    print("=" * 50)
    
    print("Choose test method:")
    print("1. Test AI Agent directly")
    print("2. Test via Web GUI")
    print("3. Show both methods")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        test_programming_commands()
    elif choice == "2":
        test_web_gui_programming()
    elif choice == "3":
        test_programming_commands()
        test_web_gui_programming()
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
