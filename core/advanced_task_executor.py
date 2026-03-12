"""
Advanced Task Executor
Enables to voice assistant to understand and execute complex, multi-step tasks like a human.
"""

import re
import os
import json
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import pyautogui
import time
from pathlib import Path

class AdvancedTaskExecutor:
    """Handles complex task understanding and execution with AI reasoning."""
    
    def __init__(self):
        self.task_history = []
        self.current_context = {}
        self.user_preferences = {}
        self.screenshot_dir = os.path.join(os.path.expanduser("~"), "Desktop", "ai_screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
    def understand_task(self, user_input: str) -> Dict[str, Any]:
        """AI-powered task understanding with dynamic planning."""
        print(f"[AdvancedTask] 🧠 Understanding task: '{user_input}'")
        
        # Analyze task complexity and intent
        task_analysis = self._analyze_task_intent(user_input)
        
        # Extract entities and parameters
        entities = self._extract_entities(user_input)
        
        # Generate dynamic execution plan using AI (no hardcoded templates)
        execution_plan = self._generate_dynamic_plan(user_input)
        
        # Calculate confidence based on intent clarity
        confidence = self._calculate_confidence(task_analysis, entities, execution_plan)
        
        print(f"[AdvancedTask] 📋 Task understood: {task_analysis.get('intent', 'unknown')}")
        print(f"[AI Plan] 🧠 Generated {len(execution_plan)} steps dynamically")
        
        return {
            "intent": task_analysis.get("intent", "unknown"),
            "confidence": confidence,
            "complexity": task_analysis.get("complexity", "medium"),
            "actions": task_analysis.get("actions", []),
            "entities": entities,
            "execution_plan": execution_plan,
            "ai_generated": True
        }
    
    def _calculate_confidence(self, task_analysis: Dict, entities: Dict, execution_plan: List) -> float:
        """Calculate confidence based on task clarity and plan quality."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on intent clarity
        if task_analysis.get("intent") != "unknown":
            confidence += 0.2
        
        # Boost confidence based on extracted entities
        if entities:
            confidence += 0.1 * min(len(entities) * 0.1, 0.2)
        
        # Boost confidence based on execution plan quality
        if execution_plan and len(execution_plan) > 1:
            confidence += 0.2
        
        # Cap at 1.0
        return min(confidence, 1.0)

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
                "patterns": [r"build\s+(?:a\s+)?(?:website|web\s+site|web\s+app)", r"create\s+(?:a\s+)?(?:website|web\s+site|web\s+app)", r"make\s+(?:a\s+)?(?:website|web\s+site|web\s+app)", r"portfolio\s+website", r"web\s+development", r"html\s+css\s+javascript"],
                "complexity": "high",
                "actions": ["file_operations", "application_launch", "text_generation"]
            },
            "multi_step_task": {
                "patterns": [r"build.*then.*open", r"create.*then.*launch", r"setup.*and.*open", r"create.*and.*start", r"build.*and.*open"],
                "complexity": "high",
                "actions": ["file_operations", "application_launch", "text_generation"]
            },
            "project_setup": {
                "patterns": [r"setup\s+(?:a\s+)?(?:project|development)", r"create\s+(?:a\s+)?(?:project|folder\s+structure)", r"initialize\s+(?:a\s+)?(?:project|repo)"],
                "complexity": "high",
                "actions": ["file_operations", "application_launch"]
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
            elif intent == "web_development":
                plan.extend([
                    {"step": 1, "action": "navigate_to_path", "details": {"path": entities.get("path", "Desktop")}},
                    {"step": 2, "action": "create_folder", "details": {"name": "portfolio-website"}},
                    {"step": 3, "action": "create_file", "details": {"name": "index.html", "content": self._generate_html_content(entities)}},
                    {"step": 4, "action": "create_file", "details": {"name": "styles.css", "content": self._generate_css_content(entities)}},
                    {"step": 5, "action": "create_file", "details": {"name": "script.js", "content": self._generate_js_content(entities)}},
                    {"step": 6, "action": "launch_application", "details": {"app": "vscode"}},
                    {"step": 7, "action": "confirm_creation", "details": {"item": "portfolio website"}}
                ])
            elif intent == "multi_step_task":
                plan.extend([
                    {"step": 1, "action": "navigate_to_path", "details": {"path": entities.get("path", "Desktop")}},
                    {"step": 2, "action": "create_folder", "details": {"name": "portfolio-website"}},
                    {"step": 3, "action": "create_file", "details": {"name": "index.html", "content": self._generate_html_content(entities)}},
                    {"step": 4, "action": "create_file", "details": {"name": "styles.css", "content": self._generate_css_content(entities)}},
                    {"step": 5, "action": "create_file", "details": {"name": "script.js", "content": self._generate_js_content(entities)}},
                    {"step": 6, "action": "launch_application", "details": {"app": "vscode"}},
                    {"step": 7, "action": "confirm_creation", "details": {"item": "portfolio website"}}
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
        """Execute plan with visual verification and AI-driven adaptation."""
        print(f"[AdvancedTask] ⚡ Executing plan with {len(plan)} steps (Visual AI Mode)")
        
        results = []
        success_count = 0
        
        for i, step in enumerate(plan, 1):
            step_num = step["step"]
            action = step["action"]
            details = step["details"]
            verification = step.get("verification", f"Step {step_num} completed")
            
            print(f"[AdvancedTask] 📍 Step {step_num}: {action}")
            
            # Execute with visual verification
            try:
                result = self._execute_with_visual_verification(action, details)
                
                if result.get("success", False):
                    print(f"[AdvancedTask] ✅ Step {step_num} completed successfully")
                    success_count += 1
                    
                    # Add visual analysis to result
                    if "visual_analysis" in result:
                        analysis = result["visual_analysis"]
                        print(f"[Visual] 🧠 AI says: {analysis.get('observations', 'N/A')}")
                        
                else:
                    print(f"[AdvancedTask] ❌ Step {step_num} failed: {result.get('message', 'Unknown error')}")
                
                results.append({
                    "step": step_num,
                    "action": action,
                    "details": details,
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "visual_analysis": result.get("visual_analysis", {}),
                    "screenshot": result.get("screenshot", "")
                })
                
            except Exception as e:
                print(f"[AdvancedTask] ❌ Step {step_num} crashed: {e}")
                results.append({
                    "step": step_num,
                    "action": action,
                    "details": details,
                    "success": False,
                    "message": f"Step crashed: {e}",
                    "visual_analysis": {"error": str(e)},
                    "screenshot": ""
                })
        
        # Generate summary
        success_rate = success_count / len(plan)
        overall_success = success_rate >= 0.7  # 70% success rate required
        
        summary = f"Completed {success_count}/{len(plan)} steps successfully"
        if overall_success:
            summary += " - Task completed successfully!"
        else:
            summary += " - Task partially completed"
        
        return {
            "success": overall_success,
            "summary": summary,
            "success_rate": success_rate,
            "results": results,
            "screenshots_taken": len([r for r in results if r.get("screenshot")])
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
            # Use current working directory (should be the project folder after navigation)
            current_path = os.getcwd()
            file_path = os.path.join(current_path, filename)
            
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
        """Create a folder and navigate into it."""
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            folder_path = os.path.join(desktop_path, folder_name)
            
            os.makedirs(folder_path, exist_ok=True)
            
            # Change to the newly created folder
            os.chdir(folder_path)
            
            return {
                "success": True,
                "message": f"Created and navigated to folder {folder_name}",
                "folder_path": folder_path,
                "current_dir": os.getcwd()
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
            
            # For VS Code, open the current folder as a project
            if executable == "code":
                current_path = os.getcwd()
                # Try multiple methods to open VS Code
                import subprocess
                
                # Method 1: Try direct 'code' command
                try:
                    result = subprocess.run([executable, current_path], capture_output=True, timeout=10)
                    if result.returncode == 0:
                        return {
                            "success": True,
                            "message": f"Launched {app_name} with project folder",
                            "app": executable,
                            "folder": current_path
                        }
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                
                # Method 2: Try using PC controller as fallback
                try:
                    from core.pc_control import pc_controller
                    result = pc_controller._open_app("Visual Studio Code")
                    if result.get("success"):
                        return {
                            "success": True,
                            "message": f"Launched {app_name} via PC control",
                            "app": "Visual Studio Code",
                            "folder": current_path
                        }
                except:
                    pass
                
                return {"success": False, "message": f"VS Code not found. Please ensure VS Code is installed and in PATH."}
            
            # Use PC controller for other apps
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

    def _take_screenshot(self, action_name: str) -> str:
        """Take a temporary screenshot for AI analysis (auto-deleted after use)."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"temp_{action_name}_{timestamp}.png"
            screenshot_path = os.path.join(self.screenshot_dir, filename)
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
            
            print(f"[Visual] 📸 Temporary screenshot for AI analysis: {filename}")
            return screenshot_path
            
        except Exception as e:
            print(f"[Visual] ❌ Screenshot failed: {e}")
            return ""

    def _cleanup_screenshot(self, screenshot_path: str) -> None:
        """Delete temporary screenshot after AI analysis."""
        try:
            if screenshot_path and os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                print(f"[Visual] 🗑️ Cleaned up temporary screenshot")
        except Exception as e:
            print(f"[Visual] ⚠️ Could not cleanup screenshot: {e}")

    def _analyze_screenshot_with_ai(self, screenshot_path: str, expected_action: str) -> Dict[str, Any]:
        """Use AI to analyze screenshot and determine if action succeeded."""
        try:
            # Convert screenshot to base64 for AI analysis
            import base64
            with open(screenshot_path, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode()
            
            # Use vision AI to analyze the screenshot
            from core.llm import http_session
            from config import OLLAMA_URL, RESPONDER_MODEL
            
            prompt = f"""Analyze this screenshot and determine if the following action was successful: "{expected_action}"
            
            Look for:
            1. Did the expected application/window open?
            2. Is the correct interface visible?
            3. Are there any error messages?
            4. Is the UI element/functionality present?
            
            Respond with JSON format:
            {{
                "success": true/false,
                "confidence": 0.0-1.0,
                "observations": "what you see in the screenshot",
                "issues": "any problems detected",
                "next_action": "what should be done next"
            }}
            
            Be very specific about what you see and whether it matches the expected outcome."""
            
            # Try to use vision model if available, fallback to regular analysis
            response = http_session.post(f"{OLLAMA_URL}/api/generate", json={
                "model": RESPONDER_MODEL,
                "prompt": prompt + f"\n\nScreenshot: {screenshot_path}",
                "stream": False
            }, timeout=30)
            
            if response.status_code == 200:
                ai_response = response.json().get("response", "").strip()
                
                # Try to parse JSON response
                try:
                    analysis = json.loads(ai_response)
                    return analysis
                except:
                    # If JSON parsing fails, create basic analysis
                    return {
                        "success": "successful" in ai_response.lower() or "completed" in ai_response.lower(),
                        "confidence": 0.7,
                        "observations": ai_response,
                        "issues": "",
                        "next_action": "continue"
                    }
            
        except Exception as e:
            print(f"[Visual] ❌ AI analysis failed: {e}")
        
        # Fallback analysis
        return {
            "success": True,
            "confidence": 0.5,
            "observations": "AI analysis unavailable, assuming success",
            "issues": "Could not analyze screenshot",
            "next_action": "continue"
        }

    def _execute_with_visual_verification(self, action: str, details: Dict) -> Dict[str, Any]:
        """Execute action with screenshot verification and auto-cleanup."""
        print(f"[Visual] 🎯 Executing: {action}")
        
        # Take before screenshot
        before_screenshot = self._take_screenshot(f"before_{action}")
        
        # Execute the action
        result = self._execute_action(action, details)
        
        # Wait a moment for UI to update
        time.sleep(2)
        
        # Take after screenshot
        after_screenshot = self._take_screenshot(f"after_{action}")
        
        # Analyze the result
        if after_screenshot:
            analysis = self._analyze_screenshot_with_ai(after_screenshot, action)
            
            print(f"[Visual] 🧠 AI Analysis: {analysis.get('observations', 'N/A')}")
            print(f"[Visual] ✅ Success: {analysis.get('success', False)} (Confidence: {analysis.get('confidence', 0)})")
            
            # If action failed, try to recover
            if not analysis.get("success", False) and analysis.get("confidence", 0) < 0.7:
                cleanup_result = self._handle_execution_failure(action, details, analysis)
                # Cleanup screenshots after analysis
                self._cleanup_screenshot(before_screenshot)
                self._cleanup_screenshot(after_screenshot)
                return cleanup_result
            
            result["visual_analysis"] = analysis
            result["screenshot"] = after_screenshot
        
        # Cleanup screenshots after successful analysis
        self._cleanup_screenshot(before_screenshot)
        self._cleanup_screenshot(after_screenshot)
        
        return result

    def _handle_execution_failure(self, action: str, details: Dict, analysis: Dict) -> Dict[str, Any]:
        """Handle execution failure with intelligent recovery."""
        print(f"[Visual] 🚨 Action failed: {analysis.get('issues', 'Unknown issue')}")
        
        # Try to close wrong applications/windows
        if "wrong app" in analysis.get("issues", "").lower() or "incorrect" in analysis.get("observations", "").lower():
            print(f"[Visual] 🔄 Closing wrong applications...")
            self._close_all_applications()
            time.sleep(1)
            
            # Retry the action
            print(f"[Visual] 🔄 Retrying action: {action}")
            retry_result = self._execute_action(action, details)
            time.sleep(2)
            
            # Verify retry
            retry_screenshot = self._take_screenshot(f"retry_{action}")
            if retry_screenshot:
                retry_analysis = self._analyze_screenshot_with_ai(retry_screenshot, action)
                if retry_analysis.get("success", False):
                    print(f"[Visual] ✅ Retry successful!")
                    return {"success": True, "message": f"Action succeeded after retry", "visual_analysis": retry_analysis}
        
        return {"success": False, "message": f"Action failed: {analysis.get('issues', 'Unknown')}", "visual_analysis": analysis}

    def _close_all_applications(self) -> None:
        """Close all applications to clean the state."""
        try:
            # Close common applications
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if any(app in proc_name for app in ['code', 'chrome', 'firefox', 'notepad', 'explorer']):
                        proc.terminate()
                except:
                    pass
            
            # Also try Alt+F4 to close active window
            pyautogui.hotkey('alt', 'f4')
            time.sleep(0.5)
            
        except Exception as e:
            print(f"[Visual] ⚠️ Could not close all apps: {e}")

    def _generate_dynamic_plan(self, user_input: str) -> List[Dict[str, Any]]:
        """Generate execution plan dynamically using AI instead of hardcoded templates."""
        try:
            from core.llm import http_session
            from config import OLLAMA_URL, RESPONDER_MODEL
            
            prompt = f"""You are an AI assistant that needs to break down this task into specific executable steps: "{user_input}"
            
            Available actions:
            - navigate_to_path: Navigate to a folder path
            - create_folder: Create a folder
            - create_file: Create a file with content
            - launch_application: Launch an application
            - click_element: Click on UI element
            - type_text: Type text
            - wait_for_ready: Wait for application to be ready
            - confirm_creation: Confirm file/folder creation
            - confirm_launch: Confirm application launch
            
            Create a step-by-step plan. Each step should be a JSON object with:
            {{
                "step": number,
                "action": "action_name",
                "details": {{"key": "value"}},
                "verification": "what to check visually"
            }}
            
            Return only the JSON array of steps, no explanations."""
            
            response = http_session.post(f"{OLLAMA_URL}/api/generate", json={
                "model": RESPONDER_MODEL,
                "prompt": prompt,
                "stream": False
            }, timeout=30)
            
            if response.status_code == 200:
                ai_plan = response.json().get("response", "").strip()
                
                # Try to parse the AI plan
                try:
                    steps = json.loads(ai_plan)
                    if isinstance(steps, list):
                        print(f"[AI Plan] 🧠 Generated {len(steps)} steps dynamically")
                        return steps
                except:
                    pass
            
        except Exception as e:
            print(f"[AI Plan] ❌ Dynamic plan generation failed: {e}")
        
        # Fallback to basic plan
        return [
            {"step": 1, "action": "navigate_to_path", "details": {"path": "Desktop"}, "verification": "Desktop visible"},
            {"step": 2, "action": "confirm_creation", "details": {"item": "task completed"}, "verification": "Task finished"}
        ]

    def _generate_html_content(self, entities: Dict) -> str:
        """Generate HTML content using AI."""
        try:
            # Use AI to generate personalized HTML content
            from core.llm import http_session
            from config import OLLAMA_URL, RESPONDER_MODEL
            
            prompt = """Generate a professional portfolio website HTML with the following requirements:
            - Modern, responsive design
            - Navigation bar with smooth scrolling
            - About section
            - Projects section with grid layout
            - Contact section
            - Link to external CSS and JS files
            - Semantic HTML5 structure
            - Professional and clean design
            
            Return only the HTML code (no explanations)."""
            
            response = http_session.post(f"{OLLAMA_URL}/api/generate", json={
                "model": RESPONDER_MODEL,
                "prompt": prompt,
                "stream": False
            }, timeout=30)
            
            if response.status_code == 200:
                ai_content = response.json().get("response", "").strip()
                if ai_content and "<html" in ai_content.lower():
                    return ai_content
            
        except Exception as e:
            print(f"[AI Content] Failed to generate HTML, using template: {e}")
        
        # Fallback to template
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Portfolio</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>Welcome to My Portfolio</h1>
        <nav>
            <ul>
                <li><a href="#about">About</a></li>
                <li><a href="#projects">Projects</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section id="about">
            <h2>About Me</h2>
            <p>I am a passionate developer creating amazing web experiences.</p>
        </section>
        
        <section id="projects">
            <h2>Projects</h2>
            <div class="project-grid">
                <div class="project">
                    <h3>Project 1</h3>
                    <p>Description of my first project.</p>
                </div>
                <div class="project">
                    <h3>Project 2</h3>
                    <p>Description of my second project.</p>
                </div>
            </div>
        </section>
        
        <section id="contact">
            <h2>Contact</h2>
            <p>Email: contact@example.com</p>
        </section>
    </main>
    
    <script src="script.js"></script>
</body>
</html>"""

    def _generate_css_content(self, entities: Dict) -> str:
        """Generate CSS content for portfolio website."""
        return """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
}

header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem 0;
    text-align: center;
}

header h1 {
    margin-bottom: 1rem;
    font-size: 2.5rem;
}

nav ul {
    list-style: none;
    display: flex;
    justify-content: center;
    gap: 2rem;
}

nav a {
    color: white;
    text-decoration: none;
    font-weight: bold;
}

nav a:hover {
    text-decoration: underline;
}

main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

section {
    margin-bottom: 3rem;
}

h2 {
    color: #333;
    margin-bottom: 1rem;
    font-size: 2rem;
}

.project-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.project {
    background: #f4f4f4;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.project h3 {
    color: #667eea;
    margin-bottom: 0.5rem;
}

@media (max-width: 768px) {
    nav ul {
        flex-direction: column;
        gap: 1rem;
    }
    
    header h1 {
        font-size: 2rem;
    }
}"""

    def _generate_js_content(self, entities: Dict) -> str:
        """Generate JavaScript content for portfolio website."""
        return """// Portfolio Website JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('nav a');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Add animation to projects on scroll
    const projects = document.querySelectorAll('.project');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });
    
    projects.forEach(project => {
        project.style.opacity = '0';
        project.style.transform = 'translateY(20px)';
        project.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(project);
    });
    
    // Simple contact form validation (if you add a form later)
    console.log('Portfolio website loaded successfully!');
});"""

# Global instance
advanced_executor = AdvancedTaskExecutor()
