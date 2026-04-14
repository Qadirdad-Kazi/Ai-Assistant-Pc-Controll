#!/usr/bin/env python3
"""
Wolf AI 2.0 Startup Script
Launches both backend API and frontend UI with voice assistant.
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path
import webbrowser
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Force UTF-8 encoding for console output to handle emojis on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class WolfAILauncher:
    """Launches Wolf AI backend and frontend."""
    
    def __init__(self):
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.project_root = project_root
        
    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        print("[CHECK] Checking dependencies...")
        
        # Check Python dependencies
        try:
            import uvicorn
            import fastapi
            import requests
            import sounddevice
            import numpy
            import serial # pyserial
            import kokoro
            from RealtimeSTT import AudioToTextRecorder
            print("[OK] Professional-grade dependencies available")
        except ImportError as e:
            print(f"❌ Missing Python dependency: {e}")
            print("Run: pip install uvicorn fastapi requests sounddevice numpy pyserial RealtimeSTT kokoro")
            return False
        
        # Check Node.js for frontend
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("[OK] Node.js available")
            else:
                print("Node.js not found, checking for alternative...")
                # Try alternative Node.js paths
                node_paths = [
                    r"C:\Program Files\nodejs\node.exe",
                    r"C:\Program Files (x86)\nodejs\node.exe",
                    r"C:\Program Files\nodejs\node.cmd",
                    r"C:\Program Files (x86)\nodejs\node.cmd"
                ]
                
                node_found = False
                for node_path in node_paths:
                    if Path(node_path).exists():
                        print(f"[OK] Node.js found at: {node_path}")
                        node_found = True
                        break
                
                if not node_found:
                    print("❌ Node.js not found")
                    print("Please install Node.js from https://nodejs.org/")
                    return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Node.js not found")
            print("Please install Node.js from https://nodejs.org/")
            return False
        
        # Check for pre-built frontend
        dist_dir = self.project_root / "frontend" / "dist"
        if dist_dir.exists() and (dist_dir / "index.html").exists():
            print("[OK] Production frontend build found")
            self.frontend_port = 8000
        else:
            print("[INFO] Production build not found - using development mode (Port 5173)")
            self.frontend_port = 5173
        
        return True
    
    def start_backend(self) -> bool:
        """Start the backend API server."""
        print("[LAUNCH] Starting backend API server...")
        
        try:
            # Change to project root
            os.chdir(self.project_root)
            
            # Start backend server
            # We don't pipe stdout/stderr so the user can see CUDA/VA logs in the terminal
            self.backend_process = subprocess.Popen([
                sys.executable, 'main.py'
            ])
            
            # Wait a moment for server to start
            time.sleep(3)
            
            # Check if backend is running
            if self.backend_process.poll() is None:
                print("[OK] Backend server started on http://localhost:8000")
                return True
            else:
                print("❌ Backend server failed to start")
                stdout, stderr = self.backend_process.communicate()
                print(f"Error: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False
    
    def start_frontend(self) -> bool:
        """Start the frontend development server."""
        print("[THEME] Starting frontend development server...")
        
        try:
            frontend_dir = self.project_root / "frontend"
            
            # Check if frontend is built
            dist_dir = frontend_dir / "dist"
            if dist_dir.exists():
                print("[OK] Frontend build found, serving static files...")
                # Backend will serve the static files
                return True
            
            # Start development server
            os.chdir(frontend_dir)
            
            self.frontend_process = subprocess.Popen([
                'npm', 'run', 'dev'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            
            # Wait for frontend to start
            time.sleep(5)
            
            # Check if frontend is running
            if self.frontend_process.poll() is None:
                print("[OK] Frontend started on http://localhost:5173")
                return True
            else:
                print("❌ Frontend failed to start")
                stdout, stderr = self.frontend_process.communicate()
                print(f"Error: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")
            return False
    
    def check_backend_health(self) -> bool:
        """Check if backend is healthy."""
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_frontend_health(self) -> bool:
        """Check if frontend is accessible."""
        try:
            import requests
            response = requests.get("http://localhost:5173", timeout=5)
            return response.status_code == 200
        except:
            # If frontend dev server is not running, check if backend serves frontend
            try:
                response = requests.get("http://localhost:8000", timeout=5)
                return response.status_code == 200
            except:
                return False
    
    def open_browser(self, url: str):
        """Open browser to specified URL."""
        try:
            webbrowser.open(url)
            print(f"[WEB] Opened browser to {url}")
        except Exception as e:
            print(f"[WARN] Could not open browser: {e}")
    
    def run(self, open_browser: bool = True):
        """Run the complete Wolf AI system."""
        print("[WOLF] Wolf AI 2.0 Startup")
        print("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Start backend
        if not self.start_backend():
            return False
        
        # Wait for backend to be healthy
        print(f"[WAIT] Waiting for backend to be healthy (timeout: 60s)...")
        for i in range(60):
            if self.check_backend_health():
                print("[OK] Backend is healthy!")
                break
            time.sleep(1)
        else:
            print("❌ Backend failed to become healthy")
            return False
        
        # Start frontend
        if not self.start_frontend():
            return False
        
        # Check services
        print("\n[CHECK] Checking services...")
        
        backend_healthy = self.check_backend_health()
        frontend_healthy = self.check_frontend_health()
        
        print(f"Backend API: {'[OK] Healthy' if backend_healthy else '[ERR] Unhealthy'}")
        print(f"Frontend UI: {'[OK] Healthy' if frontend_healthy else '[ERR] Unhealthy'}")
        
        if backend_healthy and frontend_healthy:
            print("\n[SUCCESS] Wolf AI 2.0 is running!")
            print("\n[LIST] Services:")
            print(f"   • Backend API: http://localhost:8000")
            print(f"   • Frontend UI: http://localhost:{self.frontend_port}")
            print(f"   • API Docs: http://localhost:8000/docs")
            print(f"   • WebSocket: ws://localhost:8000/ws/status")
            
            if open_browser:
                ui_url = f"http://localhost:{self.frontend_port}"
                self.open_browser(ui_url)
            
            print("\n[VOICE]  Voice Assistant:")
            print("   • Say 'Hey Wolf' to activate")
            print("   • Press Ctrl+C to stop")
            
            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
                    
                    # Check if processes are still running
                    if self.backend_process and self.backend_process.poll() is not None:
                        print("❌ Backend stopped unexpectedly")
                        break
                        
                    if self.frontend_process and self.frontend_process.poll() is not None:
                        print("❌ Frontend stopped unexpectedly")
                        break
                        
            except KeyboardInterrupt:
                print("\n[STOP] Stopping Wolf AI...")
                
        else:
            print("❌ Some services failed to start")
            return False
        
        # Cleanup
        self.stop()
        return True
    
    def stop(self):
        """Stop all processes."""
        print("[STOP] Stopping services...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("[OK] Backend stopped")
            except:
                self.backend_process.kill()
                print("[OK] Backend killed")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print("[OK] Frontend stopped")
            except:
                self.frontend_process.kill()
                print("[OK] Frontend killed")
        
        print("👋 Wolf AI stopped. Goodbye!")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start Wolf AI 2.0")
    parser.add_argument("--no-browser", action="store_true", 
                       help="Don't open browser automatically")
    parser.add_argument("--backend-only", action="store_true",
                       help="Start only backend API")
    parser.add_argument("--frontend-only", action="store_true", 
                       help="Start only frontend UI")
    
    args = parser.parse_args()
    
    launcher = WolfAILauncher()
    
    if args.backend_only:
        success = launcher.start_backend()
        if success:
            print("✅ Backend running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                launcher.stop()
    elif args.frontend_only:
        success = launcher.start_frontend()
        if success:
            print("✅ Frontend running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                launcher.stop()
    else:
        launcher.run(open_browser=not args.no_browser)

if __name__ == "__main__":
    main()
