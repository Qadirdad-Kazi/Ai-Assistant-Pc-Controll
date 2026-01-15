#!/usr/bin/env python3
"""
Wolf AI Agent - Enhanced Desktop Automation
Integrates with Wolf for natural language programming automation
"""

import os
import sys
import time
import subprocess
import platform
import json
import requests
import pyautogui
import pyperclip
from pathlib import Path
from typing import Dict, List, Any

class WolfAIAgent:
    def __init__(self):
        """Initialize Wolf AI Agent"""
        self.settings = {
            "ollama_url": "http://localhost:11434",
            "model": "llama3.2:latest",
            "vscode_path": self._find_vscode_path(),
            "typing_speed": 0.03,
            "action_delay": 1.0,
        }
        
        # Configure PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        print("🤖 Wolf AI Agent initialized")
        print(f"📁 VS Code path: {self.settings['vscode_path']}")
    
    def _find_vscode_path(self) -> str:
        """Find VS Code installation path"""
        if platform.system() == "Darwin":
            return "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
        elif platform.system() == "Windows":
            return "code"
        else:
            return "code"
    
    def interpret_with_ai(self, command: str) -> Dict[str, Any]:
        """Use Wolf AI to interpret commands"""
        try:
            system_prompt = """You are a desktop automation assistant. Interpret natural language programming commands and return JSON with:
            {
                "action": "create_project|create_file|type_code|run_command|open_ide",
                "framework": "react|html|python|node|vue|angular|etc",
                "project_name": "name",
                "files": [{"name": "filename", "content": "code", "type": "component|page|utility"}],
                "commands": ["command1", "command2"],
                "description": "what you're doing",
                "steps": ["step1", "step2"]
            }
            
            Generate production-ready, well-commented code. Follow best practices."""
            
            response = requests.post(
                f"{self.settings['ollama_url']}/api/chat",
                json={
                    "model": self.settings['model'],
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": command}
                    ],
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('message', {}).get('content', '{}')
                
                # Try to extract JSON from the response
                try:
                    # Look for JSON in the response
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start != -1 and end != -1:
                        json_str = content[start:end]
                        return json.loads(json_str)
                except:
                    pass
                
                # Fallback to basic interpretation
                return self._basic_interpretation(command)
            else:
                return self._basic_interpretation(command)
                
        except Exception as e:
            print(f"AI interpretation error: {e}")
            return self._basic_interpretation(command)
    
    def _basic_interpretation(self, command: str) -> Dict[str, Any]:
        """Basic command interpretation"""
        command_lower = command.lower()
        
        if "react" in command_lower and "login" in command_lower:
            return {
                "action": "create_project",
                "framework": "react",
                "project_name": "react-login",
                "files": [
                    {
                        "name": "src/components/LoginForm.js",
                        "content": """import React, { useState } from 'react';
import './LoginForm.css';

const LoginForm = () => {
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        console.log('Login attempt:', formData);
        // Add authentication logic here
    };

    return (
        <div className="login-container">
            <form className="login-form" onSubmit={handleSubmit}>
                <h2>Login</h2>
                <div className="form-group">
                    <input
                        type="email"
                        name="email"
                        placeholder="Email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                    />
                </div>
                <div className="form-group">
                    <input
                        type="password"
                        name="password"
                        placeholder="Password"
                        value={formData.password}
                        onChange={handleChange}
                        required
                    />
                </div>
                <button type="submit" className="login-btn">
                    Login
                </button>
            </form>
        </div>
    );
};

export default LoginForm;""",
                        "type": "component"
                    },
                    {
                        "name": "src/components/LoginForm.css",
                        "content": """.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-form {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    width: 100%;
    max-width: 400px;
}

.login-form h2 {
    text-align: center;
    margin-bottom: 1.5rem;
    color: #333;
}

.form-group {
    margin-bottom: 1rem;
}

.form-group input {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 16px;
    box-sizing: border-box;
}

.form-group input:focus {
    outline: none;
    border-color: #667eea;
}

.login-btn {
    width: 100%;
    padding: 12px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 16px;
    cursor: pointer;
    transition: transform 0.2s;
}

.login-btn:hover {
    transform: translateY(-2px);
}""",
                        "type": "style"
                    }
                ],
                "commands": ["npm install", "npm start"],
                "description": "Creating React login form with modern styling",
                "steps": [
                    "Create React project structure",
                    "Generate LoginForm component",
                    "Add CSS styling",
                    "Install dependencies",
                    "Start development server"
                ]
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
    <title>Login Form</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .form-container {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        
        .form-container h2 {
            text-align: center;
            margin-bottom: 1.5rem;
            color: #333;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="form-container">
        <h2>Login Form</h2>
        <form>
            <div class="form-group">
                <input type="email" placeholder="Email" required>
            </div>
            <div class="form-group">
                <input type="password" placeholder="Password" required>
            </div>
            <button type="submit" class="btn">Login</button>
        </form>
    </div>
</body>
</html>""",
                        "type": "page"
                    }
                ],
                "commands": [],
                "description": "Creating HTML login form with modern styling",
                "steps": [
                    "Create HTML file",
                    "Add CSS styling",
                    "Implement form structure"
                ]
            }
        else:
            return {
                "action": "create_file",
                "framework": "generic",
                "project_name": "project",
                "files": [],
                "commands": [],
                "description": "Processing command",
                "steps": ["Analyzing command"]
            }
    
    def execute_plan(self, plan: Dict[str, Any]) -> bool:
        """Execute the interpreted plan with visual feedback"""
        try:
            print(f"🎯 {plan.get('description', 'Executing plan')}")
            
            # Show steps
            if plan.get('steps'):
                print("📋 Steps:")
                for i, step in enumerate(plan['steps'], 1):
                    print(f"   {i}. {step}")
            
            # Step 1: Open VS Code
            if plan.get('action') in ['create_project', 'create_file', 'type_code']:
                self._open_vscode()
                time.sleep(3)
            
            # Step 2: Create project structure
            if plan.get('action') == 'create_project':
                self._create_project(plan)
            
            # Step 3: Create files with visual typing
            if plan.get('files'):
                self._create_files_with_typing(plan['files'])
            
            # Step 4: Run commands
            if plan.get('commands'):
                self._run_commands_with_feedback(plan['commands'])
            
            print("✅ Plan executed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Execution error: {e}")
            return False
    
    def _open_vscode(self):
        """Open VS Code with visual feedback"""
        print("📂 Opening VS Code...")
        try:
            subprocess.run([self.settings['vscode_path'], "."], check=True)
            print("✅ VS Code opened")
        except Exception as e:
            print(f"❌ Error opening VS Code: {e}")
    
    def _create_project(self, plan: Dict[str, Any]):
        """Create project structure"""
        project_name = plan.get('project_name', 'project')
        framework = plan.get('framework', 'generic')
        
        print(f"📁 Creating {framework} project: {project_name}")
        
        # Create project directory
        os.makedirs(project_name, exist_ok=True)
        os.chdir(project_name)
        
        # Framework-specific setup
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
    
    def _create_files_with_typing(self, files: List[Dict[str, str]]):
        """Create files with visible typing simulation"""
        for file_info in files:
            filename = file_info['name']
            content = file_info['content']
            file_type = file_info.get('type', 'file')
            
            print(f"📝 Creating {file_type}: {filename}")
            
            # Create directory if needed
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Create file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Simulate typing in VS Code
            self._simulate_typing_in_vscode(filename, content)
    
    def _simulate_typing_in_vscode(self, filename: str, content: str):
        """Simulate typing code in VS Code with visual feedback"""
        print(f"⌨️ Typing {filename} in VS Code...")
        
        # Open file in VS Code
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'o')
        time.sleep(1)
        pyautogui.typewrite(filename)
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(2)
        
        # Clear and type content
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        
        # Type content with realistic speed
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if i > 0:
                pyautogui.press('enter')
            for char in line:
                pyautogui.typewrite(char)
                time.sleep(self.settings['typing_speed'])
        
        # Save file
        pyautogui.hotkey('ctrl', 's')
        time.sleep(1)
        print(f"✅ {filename} created and saved")
    
    def _run_commands_with_feedback(self, commands: List[str]):
        """Run terminal commands with visual feedback"""
        for command in commands:
            print(f"💻 Running: {command}")
            
            # Open terminal
            pyautogui.hotkey('ctrl', '`')
            time.sleep(1)
            
            # Type and execute command
            pyautogui.typewrite(command)
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(3)
    
    def process_command(self, command: str) -> bool:
        """Main method to process natural language commands"""
        print(f"🧠 Interpreting: '{command}'")
        
        # Interpret command
        plan = self.interpret_with_ai(command)
        print(f"📋 Plan: {json.dumps(plan, indent=2)}")
        
        # Execute plan
        return self.execute_plan(plan)

def main():
    """Main function"""
    print("🤖 Wolf AI Agent - Desktop Automation")
    print("=" * 60)
    
    agent = WolfAIAgent()
    
    # Interactive mode
    while True:
        print("\n💡 Enter a programming command (or 'quit' to exit):")
        print("Examples:")
        print("  - Create a React login form")
        print("  - Make an HTML contact form")
        print("  - Generate a Python Flask API")
        print("  - Create a Node.js Express server")
        
        user_input = input("\n> ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if user_input:
            agent.process_command(user_input)
        else:
            print("Please enter a command")

if __name__ == "__main__":
    main()
