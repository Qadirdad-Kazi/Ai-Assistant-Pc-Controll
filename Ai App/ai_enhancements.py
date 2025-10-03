import os
import sys
import json
import time
import psutil
import platform
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
import pyautogui
import pygetwindow as gw
from PIL import ImageGrab, Image, ImageOps, ImageEnhance
import pytesseract
import openai
import numpy as np
from pathlib import Path

class AIEnhancements:
    def __init__(self, config: Optional[Dict] = None):
        """Initialize AI enhancements with configuration."""
        self.config = config or {}
        self.system_info = self._get_system_info()
        self.setup_ai()
        self.screen_width, self.screen_height = pyautogui.size()
        
    def setup_ai(self) -> None:
        """Initialize AI components."""
        try:
            # Initialize OpenAI with config if available
            if hasattr(self.config, 'OPENAI_API_KEY'):
                openai.api_key = self.config.OPENAI_API_KEY
            if hasattr(self.config, 'OLLAMA_API_BASE'):
                openai.api_base = self.config.OLLAMA_API_BASE
        except Exception as e:
            print(f"AI setup error: {e}")

    def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'cpu_cores': os.cpu_count(),
            'memory': psutil.virtual_memory().total,
            'boot_time': psutil.boot_time(),
            'users': [user.name for user in psutil.users()],
            'python_version': platform.python_version()
        }

    # System Controls
    def system_health_check(self) -> Dict[str, Any]:
        """Check system health metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'cores': psutil.cpu_count(),
                'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            },
            'boot_time': psutil.boot_time(),
            'uptime': time.time() - psutil.boot_time(),
            'process_count': len(psutil.pids())
        }

    def optimize_system(self) -> Dict[str, Any]:
        """Run system optimization routines."""
        results = {'actions': [], 'success': True}
        
        try:
            # Clear system cache
            if platform.system() == 'Windows':
                os.system('ipconfig /flushdns')
                results['actions'].append('Flushed DNS cache')
            elif platform.system() == 'Darwin':  # macOS
                os.system('sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder')
                results['actions'].append('Flushed DNS cache')
            
            # Clear temporary files
            temp_dir = '/tmp' if platform.system() != 'Windows' else os.environ.get('TEMP', 'C:\\Windows\\Temp')
            temp_files = self._clear_temp_files(temp_dir)
            results['temp_files_cleared'] = temp_files
            
            results['status'] = 'Optimization completed successfully'
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            
        return results

    def _clear_temp_files(self, temp_dir: str) -> int:
        """Clear temporary files from the specified directory."""
        count = 0
        try:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        # Skip files that are in use or can't be deleted
                        if os.access(file_path, os.W_OK):
                            os.unlink(file_path)
                            count += 1
                    except (OSError, PermissionError):
                        continue
        except Exception:
            pass
        return count

    # AI-Powered Features
    def analyze_screen_content(self, region: tuple = None) -> Dict[str, Any]:
        """Analyze screen content using OCR and AI."""
        try:
            # Capture screen
            screenshot = self._capture_screen(region)
            
            # Use OCR to extract text
            text = pytesseract.image_to_string(screenshot)
            
            # Analyze with AI
            analysis = self._analyze_with_ai({
                'text': text,
                'context': 'screen_analysis',
                'system_info': self.system_info
            })
            
            return {
                'success': True,
                'text': text,
                'analysis': analysis,
                'screenshot_size': screenshot.size
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def predict_user_intent(self, command: str, context: Dict = None) -> Dict[str, Any]:
        """Predict user intent using AI."""
        try:
            # Prepare context for AI
            context = context or {}
            context.update({
                'command': command,
                'timestamp': datetime.now().isoformat(),
                'active_window': self._get_active_window_info(),
                'system_status': self.system_health_check()
            })
            
            # Get AI prediction
            response = self._analyze_with_ai({
                'command': command,
                'context': context,
                'task': 'predict_intent'
            })
            
            return {
                'success': True,
                'intent': response.get('intent', 'unknown'),
                'confidence': response.get('confidence', 0),
                'action': response.get('action', {}),
                'context': context
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def smart_automation(self, task_description: str) -> Dict[str, Any]:
        """Perform smart automation based on task description."""
        try:
            # Get AI plan for the task
            plan = self._analyze_with_ai({
                'task': task_description,
                'context': {
                    'system_info': self.system_info,
                    'current_state': self._get_system_state()
                },
                'action': 'create_automation_plan'
            })
            
            # Execute the plan
            results = []
            for step in plan.get('steps', []):
                try:
                    result = self._execute_automation_step(step)
                    results.append({
                        'step': step.get('action'),
                        'success': result.get('success', False),
                        'result': result
                    })
                except Exception as e:
                    results.append({
                        'step': step.get('action'),
                        'success': False,
                        'error': str(e)
                    })
            
            return {
                'success': all(r.get('success', False) for r in results),
                'results': results,
                'task_completed': plan.get('task_completed', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    # Helper Methods
    def _capture_screen(self, region: tuple = None) -> Image.Image:
        """Capture screen or region of the screen."""
        if region:
            return ImageGrab.grab(bbox=region)
        return ImageGrab.grab()

    def _get_active_window_info(self) -> Dict[str, Any]:
        """Get information about the currently active window."""
        try:
            window = gw.getActiveWindow()
            if window:
                return {
                    'title': window.title,
                    'size': window.size,
                    'position': window.topleft,
                    'is_maximized': window.isMaximized,
                    'is_minimized': window.isMinimized
                }
            return {}
        except Exception:
            return {}

    def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state snapshot."""
        return {
            'time': datetime.now().isoformat(),
            'active_app': self._get_active_window_info(),
            'system_load': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
            'memory': dict(psutil.virtual_memory()._asdict()),
            'cpu': psutil.cpu_percent(percpu=True),
            'disk': dict(psutil.disk_usage('/')._asdict())
        }

    def _analyze_with_ai(self, data: Dict) -> Dict:
        """Send data to AI for analysis."""
        try:
            # This is a placeholder for actual AI integration
            # In a real implementation, you would call an AI API here
            # For now, we'll return a mock response
            
            # Example of how you might structure an AI API call:
            """
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": json.dumps(data)}
                ]
            )
            return json.loads(response.choices[0].message.content)
            """
            
            # Mock response for development
            if data.get('task') == 'predict_intent':
                return {
                    'intent': 'execute_command',
                    'confidence': 0.95,
                    'action': {
                        'type': 'run_command',
                        'command': data.get('command', '')
                    }
                }
            elif data.get('action') == 'create_automation_plan':
                return {
                    'steps': [
                        {'action': 'analyze_task', 'details': 'Understanding the task'},
                        {'action': 'execute_commands', 'details': 'Performing the task'}
                    ],
                    'task_completed': True
                }
            else:
                return {'status': 'analysis_complete', 'details': 'Sample analysis'}
                
        except Exception as e:
            return {'error': str(e)}

    def _execute_automation_step(self, step: Dict) -> Dict:
        """Execute a single automation step."""
        action = step.get('action', '').lower()
        
        try:
            if action == 'type_text':
                pyautogui.write(step.get('text', ''), interval=0.1)
                return {'success': True}
                
            elif action == 'press_keys':
                keys = step.get('keys', [])
                if isinstance(keys, str):
                    keys = [keys]
                pyautogui.hotkey(*keys)
                return {'success': True}
                
            elif action == 'click':
                x = step.get('x')
                y = step.get('y')
                button = step.get('button', 'left')
                clicks = step.get('clicks', 1)
                
                if x is not None and y is not None:
                    pyautogui.click(x, y, button=button, clicks=clicks)
                else:
                    pyautogui.click(button=button, clicks=clicks)
                return {'success': True}
                
            elif action == 'wait':
                time.sleep(step.get('seconds', 1))
                return {'success': True}
                
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'step': step
            }

# Example usage
if __name__ == "__main__":
    # Initialize with config
    config = {
        'OPENAI_API_KEY': 'your-api-key-here',  # Optional
        'OLLAMA_API_BASE': 'http://localhost:11434/v1'  # Optional
    }
    
    ai = AIEnhancements(config)
    
    # Example: Check system health
    print("System Health:", json.dumps(ai.system_health_check(), indent=2))
    
    # Example: Analyze screen content
    # analysis = ai.analyze_screen_content()
    # print("Screen Analysis:", json.dumps(analysis, indent=2))
    
    # Example: Predict user intent
    intent = ai.predict_user_intent("Open Chrome and search for AI news")
    print("Predicted Intent:", json.dumps(intent, indent=2))
