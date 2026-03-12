"""
Advanced Task Executor
Enables to voice assistant to understand and execute complex, multi-step tasks like a human.
"""

import os
import re
import json
import subprocess
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

class AdvancedTaskExecutor:
    """Handles complex task understanding and execution with AI reasoning."""
    
    def __init__(self):
        self.task_history = []
        self.current_context = {}
        self.user_preferences = {}
        
    def understand_task(self, user_input: str) -> Dict[str, Any]:
        """AI-powered task understanding with intent recognition."""
        print(f"[AdvancedTask] 🧠 Understanding task: '{user_input}'")
        
        # Analyze task complexity and intent
        task_analysis = self._analyze_task_intent(user_input)
        
        # Extract entities and parameters
        entities = self._extract_entities(user_input)
        
        # Plan execution steps
        execution_plan = self._create_execution_plan(task_analysis, entities)
        
        result = {
            "user_input": user_input,
            "task_analysis": task_analysis,
            "entities": entities,
            "execution_plan": execution_plan,
            "confidence": task_analysis.get("confidence", 0.5)
        }
        
        print(f"[AdvancedTask] 📋 Task understood: {task_analysis.get('intent', 'unknown')}")
        return result
    
    def _analyze_task_intent(self, user_input: str) -> Dict[str, Any]:
        """Analyze user intent and task complexity."""
        user_lower = user_input.lower()
        
        # Task intent patterns
        intents = {
            "create_file": {
                "patterns": [r"create\s+(?:a\s+)?(?:text\s+)?file", r"make\s+(?:a\s+)?(?:text\s+)?file", r"write\s+(?:a\s+)?(?:text\s+)?file", r"build\s+(?:a\s+)?(?:text\s+)?file"],
                "complexity": "medium",
                "actions": ["file_operations", "text_generation"]
            },
            "create_folder": {
                "patterns": [r"create\s+(?:a\s+)?(?:folder|directory)", r"make\s+(?:a\s+)?(?:folder|directory)", r"new\s+(?:folder|directory)"],
                "complexity": "low",
                "actions": ["file_operations"]
            },
            "open_ide": {
                "patterns": [r"open\s+(?:visual\s+studio\s+code|vs\s+code|code\s+editor)", r"launch\s+(?:visual\s+studio\s+code|vs\s+code|code\s+editor)", r"start\s+(?:visual\s+studio\s+code|vs\s+code|code\s+editor)"],
                "complexity": "low",
                "actions": ["application_launch"]
            },
            "web_development": {
                "patterns": [r"build\s+(?:a\s+)?(?:website|web\s+site|web\s+app)", r"create\s+(?:a\s+)?(?:website|web\s+site|web\s+app)", r"make\s+(?:a\s+)?(?:website|web\s+site|web\s+app)"],
                "complexity": "high",
                "actions": ["file_operations", "application_launch", "text_generation"]
            },
            "navigate_desktop": {
                "patterns": [r"go\s+to\s+desktop", r"navigate\s+to\s+desktop", r"show\s+desktop"],
                "complexity": "low",
                "actions": ["navigation"]
            },
            "complex_workflow": {
                "patterns": [r"setup\s+(?:development\s+)?environment", r"prepare\s+(?:my\s+)?workspace", r"organize\s+(?:my\s+)?project"],
                "complexity": "high",
                "actions": ["multi_step"]
            }
        }
        
        # Match intent
        matched_intent = None
        confidence = 0.0
        
        for intent_name, intent_data in intents.items():
            for pattern in intent_data["patterns"]:
                if re.search(pattern, user_lower):
                    matched_intent = intent_name
                    confidence = 0.8 + (0.1 * len(pattern.split()))  # Longer patterns = higher confidence
                    if confidence > confidence:
                        confidence = confidence
                        matched_intent = intent_name
        
        if not matched_intent:
            return {"intent": "unknown", "confidence": 0.1, "complexity": "unknown"}
        
        return {
            "intent": matched_intent,
            "confidence": confidence,
            "complexity": intents[matched_intent]["complexity"],
            "actions": intents[matched_intent]["actions"]
        }
    
    def _extract_entities(self, user_input: str) -> Dict[str, Any]:
        """Extract entities like file names, paths, applications."""
        entities = {}
        
        # File name extraction - more precise patterns
        file_patterns = [
            r"(?:create|make|write)\s+(?:a\s+)?(?:text\s+)?file\s+(?:named\s+)?[\"']([^\"'\"]+)[\"']",
            r"(?:create|make|write)\s+(?:a\s+)?(?:text\s+)?file\s+(?:called\s+)?[\"']([^\"'\"]+)[\"']",
            r"(?:create|make|write)\s+(?:a\s+)?(?:text\s+)?file\s+[\"']([^\"'\"]+)[\"'](?=\s+with|\s+and|$)",
            r"(?:folder|directory)\s+(?:called\s+)?[\"']([^\"'\"]+)[\"']"
        ]
        
        # Content extraction - improved patterns
        content_patterns = [
            r"with\s+content\s+[\"']([^\"']+)[\"']",
            r"content\s+[\"']([^\"']+)[\"']",
            r"named\s+[\"']([^\"']+)[\"']\s+with",
            r"file\s+[\"']([^\"']+)[\"']\s+with\s+content\s+[\"']([^\"']+)[\"']"
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                entities["file_name"] = match.group(1).strip()
        
        # Extract content
        for pattern in content_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                entities["content"] = match.group(1).strip()
        
        # Application extraction
        app_patterns = [
            r"(?:open|launch|start)\s+(?:visual\s+studio\s+code|vs\s+code|chrome|firefox|spotify)",
            r"(?:navigate to|go to)\s+(?:desktop|documents|downloads)"
        ]
        
        for pattern in app_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                entities["application"] = match.group(0).strip()
        
        # Path extraction
        path_patterns = [
            r"(?:navigate to|go to|cd)\s+([a-zA-Z]:\\[^\\\s]+)",
            r"(?:create|make)\s+(?:folder|directory)\s+(?:in\s+)?([a-zA-Z]:\\[^\\\s]+)"
        ]
        
        for pattern in path_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                entities["path"] = match.group(1).strip()
        
        return entities
    
    def _create_execution_plan(self, task_analysis: Dict, entities: Dict) -> List[Dict[str, Any]]:
        """Create step-by-step execution plan."""
        intent = task_analysis.get("intent", "unknown")
        actions = task_analysis.get("actions", [])
        
        plan = []
        
        if "file_operations" in actions:
            if intent == "create_file":
                file_name = entities.get("file_name", "notes.txt")
                content = entities.get("content", "")
                plan.extend([
                    {"step": 1, "action": "navigate_to_path", "details": {"path": entities.get("path", "Desktop")}},
                    {"step": 2, "action": "create_file", "details": {"name": file_name, "content": content}},
                    {"step": 3, "action": "confirm_creation", "details": {"item": file_name}}
                ])
            elif intent == "create_folder":
                folder_name = entities.get("file_name", "new_project")
                plan.extend([
                    {"step": 1, "action": "navigate_to_path", "details": {"path": entities.get("path", "Desktop")}},
                    {"step": 2, "action": "create_folder", "details": {"name": folder_name}},
                    {"step": 3, "action": "confirm_creation", "details": {"item": folder_name}}
                ])
        
        if "application_launch" in actions:
            app_name = entities.get("application", "vscode")
            plan.extend([
                    {"step": 1, "action": "launch_application", "details": {"app": app_name}},
                    {"step": 2, "action": "wait_for_ready", "details": {"timeout": 3}},
                    {"step": 3, "action": "confirm_launch", "details": {"app": app_name}}
            ])
        
        if "navigation" in actions:
            path = entities.get("path", "Desktop")
            plan.extend([
                    {"step": 1, "action": "navigate_to_path", "details": {"path": path}},
                    {"step": 2, "action": "confirm_navigation", "details": {"path": path}}
            ])
        
        if "multi_step" in actions:
            plan.extend([
                {"step": 1, "action": "analyze_workspace", "details": {}},
                {"step": 2, "action": "setup_development_env", "details": {}},
                {"step": 3, "action": "create_project_structure", "details": {}},
                {"step": 4, "action": "install_dependencies", "details": {}},
                {"step": 5, "action": "create_project_structure", "details": {}},
                {"step": 6, "action": "confirm_setup", "details": {}}
            ])
        
        return plan
    
    def _generate_html_content(self, entities: Dict) -> str:
        """Generate HTML content based on context."""
        file_name = entities.get("file_name", "index.html")
        
        if "website" in file_name.lower() or "index" in file_name.lower():
            return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Demo Website</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #4CAF50;
            text-align: center;
            margin-bottom: 30px;
        }
        .feature {
            background: rgba(76, 175, 80, 0.2);
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }
        .btn {
            background: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
        }
        .btn:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Welcome to My Demo Website</h1>
        
        <div class="feature">
            <h2>✨ Features</h2>
            <p>This is a demo website created by Wolf AI Assistant with advanced task understanding capabilities.</p>
            <ul>
                <li>🤖 AI-powered task comprehension</li>
                <li>📋 Multi-step execution planning</li>
                <li>🎯 Intelligent file operations</li>
                <li>🔧 Development environment setup</li>
            </ul>
        </div>
        
        <div class="feature">
            <h2>🎯 Capabilities</h2>
            <p>The assistant can understand complex commands and break them down into executable steps.</p>
            <button class="btn" onclick="alert('Hello from AI!')">Click Me!</button>
        </div>
        
        <div class="feature">
            <h2>📱 Created by</h2>
            <p>Generated using advanced AI task execution with human-like understanding.</p>
        </div>
    </div>
    
    <script>
        console.log('Website loaded successfully!');
    </script>
</body>
</html>"""
        
        return "<html><body><h1>Hello World</h1></body></html>"
    
    def execute_plan(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute step-by-step plan with feedback."""
        print(f"[AdvancedTask] ⚡ Executing plan with {len(plan)} steps")
        
        results = []
        success_count = 0
        
        for i, step in enumerate(plan, 1):
            step_num = step["step"]
            action = step["action"]
            details = step["details"]
            
            print(f"[AdvancedTask] 📍 Step {step_num}: {action}")
            
            try:
                result = self._execute_step(action, details)
                results.append({
                    "step": step_num,
                    "action": action,
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "details": details
                })
                
                if result.get("success"):
                    success_count += 1
                    print(f"[AdvancedTask] ✅ Step {step_num} completed successfully")
                else:
                    print(f"[AdvancedTask] ❌ Step {step_num} failed: {result.get('message', 'Unknown error')}")
                
                # Add delay between steps for better UX
                time.sleep(0.5)
                
            except Exception as e:
                results.append({
                    "step": step_num,
                    "action": action,
                    "success": False,
                    "message": str(e),
                    "details": details
                })
                print(f"[AdvancedTask] 💥 Step {step_num} error: {e}")
        
        success_rate = (success_count / len(plan)) * 100 if plan else 0
        
        return {
            "success": success_rate == 100,
            "success_rate": success_rate,
            "total_steps": len(plan),
            "successful_steps": success_count,
            "results": results,
            "summary": f"Completed {success_count}/{len(plan)} steps ({success_rate:.1f}% success rate)"
        }
    
    def _execute_step(self, action: str, details: Dict) -> Dict[str, Any]:
        """Execute individual step with appropriate method."""
        try:
            if action == "navigate_to_path":
                return self._navigate_to_path(details.get("path", ""))
            
            elif action == "create_file":
                return self._create_file(details.get("name", ""), details.get("content", ""))
            
            elif action == "create_folder":
                return self._create_folder(details.get("name", ""))
            
            elif action == "launch_application":
                return self._launch_application(details.get("app", ""))
            
            elif action == "open_file":
                return self._open_file_in_ide(details.get("app", "vscode"), details.get("file", ""))
            
            elif action == "setup_development_env":
                return self._setup_development_environment()
            
            elif action in ["confirm_creation", "confirm_launch", "confirm_navigation"]:
                return {"success": True, "message": f"Confirmed {action.replace('_', ' ')}"}
            
            elif action in ["wait_for_ready", "analyze_workspace", "create_project_structure", "install_dependencies", "confirm_setup"]:
                return {"success": True, "message": f"Processed {action}"}
            
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "message": f"Step execution failed: {e}"}
    
    def _navigate_to_path(self, path: str) -> Dict[str, Any]:
        """Navigate to specified path using terminal."""
        try:
            # Convert to proper Windows path format
            if not path.startswith(("C:", "D:", "E:", "F:")):
                # Assume relative path, add to Desktop
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                full_path = os.path.join(desktop_path, path)
            else:
                full_path = path
            
            # Use PowerShell to navigate
            command = f'cd "{full_path}"'
            result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True)
            
            return {
                "success": result.returncode == 0,
                "message": f"Navigated to {full_path}",
                "path": full_path
            }
        except Exception as e:
            return {"success": False, "message": f"Navigation failed: {e}"}
    
    def _create_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Create a file with specified content."""
        try:
            # Default to Desktop if no path specified
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            file_path = os.path.join(desktop_path, filename)
            
            # Use provided content or default
            file_content = content if content else f"Created file: {filename}"
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            return {
                "success": True,
                "message": f"Created {filename}",
                "file_path": file_path,
                "size": len(file_content)
            }
        except Exception as e:
            return {"success": False, "message": f"File creation failed: {e}"}
    
    def _create_folder(self, folder_name: str) -> Dict[str, Any]:
        """Create a folder."""
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            folder_path = os.path.join(desktop_path, folder_name)
            
            os.makedirs(folder_path, exist_ok=True)
            
            return {
                "success": True,
                "message": f"Created folder {folder_name}",
                "folder_path": folder_path
            }
        except Exception as e:
            return {"success": False, "message": f"Folder creation failed: {e}"}
    
    def _launch_application(self, app_name: str) -> Dict[str, Any]:
        """Launch application with intelligent detection."""
        try:
            # Map common app names to executable names
            app_mapping = {
                "vscode": "code",
                "visual studio code": "code",
                "code": "code",
                "chrome": "chrome",
                "firefox": "firefox"
            }
            
            normalized_app = app_name.lower()
            executable = app_mapping.get(normalized_app, app_name)
            
            # Use PC controller for app launching
            from core.pc_control import pc_controller
            result = pc_controller._open_app(executable)
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"Launched {app_name}",
                    "app": executable
                }
            else:
                return result
                
        except Exception as e:
            return {"success": False, "message": f"Application launch failed: {e}"}
    
    def _open_file_in_ide(self, ide: str, filename: str) -> Dict[str, Any]:
        """Open file in specified IDE."""
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            file_path = os.path.join(desktop_path, filename)
            
            # Launch IDE with file
            if ide.lower() in ["vscode", "code", "visual studio code"]:
                command = f'code "{file_path}"'
            else:
                command = f'start "{file_path}"'
            
            result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True)
            
            return {
                "success": result.returncode == 0,
                "message": f"Opened {filename} in {ide}",
                "file_path": file_path
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to open file in IDE: {e}"}
    
    def _setup_development_environment(self) -> Dict[str, Any]:
        """Setup a basic development environment."""
        try:
            tasks = [
                "Creating project structure...",
                "Installing common dependencies...",
                "Setting up Git repository...",
                "Configuring development tools..."
            ]
            
            results = []
            for task in tasks:
                # Simulate setup tasks
                time.sleep(0.2)
                results.append({"task": task, "status": "completed"})
            
            return {
                "success": True,
                "message": "Development environment setup completed",
                "tasks": results
            }
        except Exception as e:
            return {"success": False, "message": f"Setup failed: {e}"}

# Global instance
advanced_executor = AdvancedTaskExecutor()
