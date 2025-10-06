#!/usr/bin/env python3
"""
AI Agent - Desktop Automation Assistant
Interprets natural language commands and performs visible actions on PC
"""

import os
import sys
import time
import subprocess
import platform
import json
import requests
from typing import Dict, List, Any
import pyautogui
import pyperclip
from pathlib import Path

class AIAgent:
    def __init__(self):
        """Initialize the AI Agent"""
        self.settings = {
            "ai_model": "gpt-3.5-turbo",
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "vscode_path": self._find_vscode_path(),
            "typing_speed": 0.05,  # seconds between keystrokes
            "action_delay": 1.0,   # delay between actions
        }
        
        # Configure PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        print("🤖 AI Agent initialized")
        print(f"📁 VS Code path: {self.settings['vscode_path']}")
    
    def _find_vscode_path(self) -> str:
        """Find VS Code installation path"""
        if platform.system() == "Darwin":  # macOS
            return "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
        elif platform.system() == "Windows":
            return "code"  # Usually in PATH
        else:  # Linux
            return "code"
    
    def interpret_command(self, command: str) -> Dict[str, Any]:
        """Interpret natural language command using AI"""
        if not self.settings['openai_api_key']:
            return self._fallback_interpretation(command)
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings['openai_api_key']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.settings['ai_model'],
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a desktop automation assistant. Interpret natural language commands and return a JSON response with:
                            {
                                "action": "create_project|create_file|type_code|run_command|open_ide",
                                "framework": "react|html|python|node|etc",
                                "project_name": "name",
                                "files": [{"name": "filename", "content": "code"}],
                                "commands": ["command1", "command2"],
                                "description": "what you're doing"
                            }"""
                        },
                        {
                            "role": "user",
                            "content": command
                        }
                    ]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                return json.loads(content)
            else:
                return self._fallback_interpretation(command)
                
        except Exception as e:
            print(f"AI interpretation error: {e}")
            return self._fallback_interpretation(command)
    
    def _fallback_interpretation(self, command: str) -> Dict[str, Any]:
        """Fallback interpretation without AI"""
        command_lower = command.lower()
        
        if "react" in command_lower:
            return {
                "action": "create_project",
                "framework": "react",
                "project_name": "my-react-app",
                "files": [],
                "commands": ["npx create-react-app my-react-app"],
                "description": "Creating React project"
            }
        elif "html" in command_lower and "form" in command_lower:
            return {
                "action": "create_file",
                "framework": "html",
                "project_name": "html-form",
                "files": [
                    {
                        "name": "index.html",
                        "content": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Form</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 50px; }
        .form-container { max-width: 400px; margin: 0 auto; }
        input, button { width: 100%; padding: 10px; margin: 5px 0; }
        button { background: #007bff; color: white; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="form-container">
        <h2>Login Form</h2>
        <form>
            <input type="text" placeholder="Username" required>
            <input type="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>"""
                    }
                ],
                "commands": [],
                "description": "Creating HTML login form"
            }
        else:
            return {
                "action": "create_file",
                "framework": "generic",
                "project_name": "project",
                "files": [],
                "commands": [],
                "description": "Processing command"
            }
    
    def execute_plan(self, plan: Dict[str, Any]) -> bool:
        """Execute the interpreted plan"""
        try:
            print(f"🎯 {plan.get('description', 'Executing plan')}")
            
            # Step 1: Open VS Code
            if plan.get('action') in ['create_project', 'create_file', 'type_code']:
                self._open_vscode()
                time.sleep(3)
            
            # Step 2: Create project structure
            if plan.get('action') == 'create_project':
                self._create_project(plan)
            
            # Step 3: Create files
            if plan.get('files'):
                self._create_files(plan['files'])
            
            # Step 4: Run commands
            if plan.get('commands'):
                self._run_commands(plan['commands'])
            
            print("✅ Plan executed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Execution error: {e}")
            return False
    
    def _open_vscode(self):
        """Open VS Code"""
        print("📂 Opening VS Code...")
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run([self.settings['vscode_path'], "."], check=True)
            else:
                subprocess.run([self.settings['vscode_path'], "."], check=True)
        except Exception as e:
            print(f"Error opening VS Code: {e}")
    
    def _create_project(self, plan: Dict[str, Any]):
        """Create project structure"""
        project_name = plan.get('project_name', 'project')
        framework = plan.get('framework', 'generic')
        
        print(f"📁 Creating {framework} project: {project_name}")
        
        # Create project directory
        os.makedirs(project_name, exist_ok=True)
        os.chdir(project_name)
        
        # Run framework-specific commands
        if framework == 'react':
            print("⚛️ Setting up React project...")
            subprocess.run(["npx", "create-react-app", project_name], check=True)
        elif framework == 'node':
            print("🟢 Setting up Node.js project...")
            subprocess.run(["npm", "init", "-y"], check=True)
        elif framework == 'python':
            print("🐍 Setting up Python project...")
            with open("requirements.txt", "w") as f:
                f.write("flask\nrequests\n")
    
    def _create_files(self, files: List[Dict[str, str]]):
        """Create files with content"""
        for file_info in files:
            filename = file_info['name']
            content = file_info['content']
            
            print(f"📝 Creating {filename}...")
            
            # Create file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Simulate typing in VS Code
            self._simulate_typing_in_vscode(filename, content)
    
    def _simulate_typing_in_vscode(self, filename: str, content: str):
        """Simulate typing code in VS Code"""
        print(f"⌨️ Typing {filename} in VS Code...")
        
        # Open file in VS Code (Ctrl+O)
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'o')
        time.sleep(1)
        pyautogui.typewrite(filename)
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(2)
        
        # Clear existing content and type new content
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        
        # Type content character by character
        for char in content:
            if char == '\n':
                pyautogui.press('enter')
            else:
                pyautogui.typewrite(char)
            time.sleep(self.settings['typing_speed'])
        
        # Save file
        pyautogui.hotkey('ctrl', 's')
        time.sleep(1)
    
    def _run_commands(self, commands: List[str]):
        """Run terminal commands"""
        for command in commands:
            print(f"💻 Running: {command}")
            
            # Open terminal in VS Code
            pyautogui.hotkey('ctrl', '`')
            time.sleep(1)
            
            # Type command
            pyautogui.typewrite(command)
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(2)
    
    def process_command(self, command: str) -> bool:
        """Main method to process natural language commands"""
        print(f"🧠 Interpreting: '{command}'")
        
        # Step 1: Interpret command
        plan = self.interpret_command(command)
        print(f"📋 Plan: {json.dumps(plan, indent=2)}")
        
        # Step 2: Execute plan
        return self.execute_plan(plan)

def main():
    """Main function"""
    print("🤖 AI Agent - Desktop Automation Assistant")
    print("=" * 60)
    
    agent = AIAgent()
    
    # Example commands to test
    test_commands = [
        "Create a login form in HTML and CSS",
        "Make a React project called Portfolio with a navbar and hero section",
        "Generate a Python Flask API with user authentication",
        "Create a Node.js Express server with MongoDB"
    ]
    
    print("\n🎯 Available test commands:")
    for i, cmd in enumerate(test_commands, 1):
        print(f"{i}. {cmd}")
    
    print("\n💡 Enter a command or press Enter to run test:")
    user_input = input("> ").strip()
    
    if user_input:
        agent.process_command(user_input)
    else:
        # Run test command
        print("\n🧪 Running test: Creating HTML login form...")
        agent.process_command("Create a login form in HTML and CSS")
    
    print("\n✅ Cursor AI Agent completed!")

if __name__ == "__main__":
    main()
