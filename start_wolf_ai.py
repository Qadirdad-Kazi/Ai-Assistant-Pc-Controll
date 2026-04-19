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
import shutil
from pathlib import Path
import webbrowser
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class WolfAILauncher:
    """Launches Wolf AI backend and frontend."""
    
    def __init__(self):
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.backend_log_handle = None
        self.frontend_log_handle = None
        self.node_cmd: Optional[str] = None
        self.npm_cmd: Optional[str] = None
        self.project_root = project_root
        self.logs_dir = self.project_root / "logs"

    def _resolve_executable(self, names, fallback_paths=None) -> Optional[str]:
        """Find an executable in PATH or known Windows install locations."""
        fallback_paths = fallback_paths or []

        for name in names:
            resolved = shutil.which(name)
            if resolved:
                return resolved

        for candidate in fallback_paths:
            if Path(candidate).exists():
                return candidate

        return None

    def _tail_log(self, file_path: Path, lines: int = 30) -> str:
        """Return the tail of a log file for debugging startup failures."""
        try:
            if not file_path.exists():
                return "(log file not found)"
            content = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            return "\n".join(content[-lines:]) if content else "(log file is empty)"
        except Exception as e:
            return f"(failed to read log: {e})"
        
    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        print("🔍 Checking dependencies...")
        
        # Check Python dependencies
        try:
            import uvicorn
            import fastapi
            import requests
            import sounddevice
            import numpy
            import serial # pyserial
            from RealtimeSTT import AudioToTextRecorder
            print("✅ Professional-grade dependencies available")
        except ImportError as e:
            print(f"❌ Missing Python dependency: {e}")
            print("Run: pip install uvicorn fastapi requests sounddevice numpy pyserial RealtimeSTT")
            return False
        
        # Check Node.js for frontend
        node_fallbacks = [
            r"C:\Program Files\nodejs\node.exe",
            r"C:\Program Files (x86)\nodejs\node.exe",
            r"C:\Program Files\nodejs\node.cmd",
            r"C:\Program Files (x86)\nodejs\node.cmd",
        ]
        self.node_cmd = self._resolve_executable(["node", "node.exe", "node.cmd"], node_fallbacks)

        if not self.node_cmd:
            print("❌ Node.js not found")
            print("Please install Node.js from https://nodejs.org/")
            return False
        print(f"✅ Node.js available ({self.node_cmd})")
        
        frontend_dir = self.project_root / "frontend"
        dist_dir = frontend_dir / "dist"

        npm_fallbacks = [
            r"C:\Program Files\nodejs\npm.cmd",
            r"C:\Program Files (x86)\nodejs\npm.cmd",
            r"C:\Program Files\nodejs\npm.exe",
            r"C:\Program Files (x86)\nodejs\npm.exe",
        ]

        # If node was found in a known location, prefer sibling npm.cmd.
        if self.node_cmd:
            node_path = Path(self.node_cmd)
            sibling_npm_cmd = node_path.parent / "npm.cmd"
            sibling_npm_exe = node_path.parent / "npm.exe"
            npm_fallbacks = [str(sibling_npm_cmd), str(sibling_npm_exe)] + npm_fallbacks

        self.npm_cmd = self._resolve_executable(["npm", "npm.cmd", "npm.exe"], npm_fallbacks)

        if dist_dir.exists():
            print("✅ Frontend build available")
        elif self.npm_cmd:
            print(f"✅ npm available for frontend dev server ({self.npm_cmd})")
        else:
            print("❌ Frontend build missing and npm not found")
            print("Install npm/Node.js or build frontend (frontend/dist) before launching.")
            return False
        
        return True
    
    def start_backend(self) -> bool:
        """Start the backend API server."""
        print("🚀 Starting backend API server...")
        
        try:
            # Change to project root
            os.chdir(self.project_root)

            self.logs_dir.mkdir(parents=True, exist_ok=True)
            backend_log = self.logs_dir / "backend_startup.log"
            self.backend_log_handle = open(backend_log, "w", encoding="utf-8", buffering=1)
            
            # Start backend server
            self.backend_process = subprocess.Popen([
                sys.executable, 'main.py'
            ], stdout=self.backend_log_handle, stderr=subprocess.STDOUT, text=True)
            
            # Wait a moment for server to start
            time.sleep(3)
            
            # Check if backend is running
            if self.backend_process.poll() is None:
                print("✅ Backend server started on http://localhost:8000")
                print(f"📝 Backend logs: {backend_log}")
                return True
            else:
                print("❌ Backend server failed to start")
                print(self._tail_log(backend_log))
                return False
                
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False
    
    def start_frontend(self) -> bool:
        """Start the frontend development server."""
        print("🎨 Starting frontend development server...")
        
        try:
            frontend_dir = self.project_root / "frontend"
            
            # Check if frontend is built
            dist_dir = frontend_dir / "dist"
            if dist_dir.exists():
                print("📦 Frontend build found, serving static files...")
                # Backend will serve the static files
                return True
            
            # Start development server
            os.chdir(frontend_dir)

            self.logs_dir.mkdir(parents=True, exist_ok=True)
            frontend_log = self.logs_dir / "frontend_startup.log"
            self.frontend_log_handle = open(frontend_log, "w", encoding="utf-8", buffering=1)

            npm_cmd = self.npm_cmd or self._resolve_executable(
                ["npm", "npm.cmd", "npm.exe"],
                [
                    r"C:\Program Files\nodejs\npm.cmd",
                    r"C:\Program Files (x86)\nodejs\npm.cmd",
                ],
            )
            if not npm_cmd:
                print("❌ Could not locate npm executable to start frontend dev server")
                return False
            
            self.frontend_process = subprocess.Popen([
                npm_cmd, 'run', 'dev'
            ], stdout=self.frontend_log_handle, stderr=subprocess.STDOUT, text=True)
            
            # Wait for frontend to start
            time.sleep(5)
            
            # Check if frontend is running
            if self.frontend_process.poll() is None:
                print("✅ Frontend started on http://localhost:5173")
                print(f"📝 Frontend logs: {frontend_log}")
                return True
            else:
                print("❌ Frontend failed to start")
                print(self._tail_log(frontend_log))
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
            print(f"🌐 Opened browser to {url}")
        except Exception as e:
            print(f"⚠️  Could not open browser: {e}")
    
    def run(self, open_browser: bool = True):
        """Run the complete Wolf AI system."""
        print("🐺 Wolf AI 2.0 Startup")
        print("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Start backend
        if not self.start_backend():
            return False
        
        # Wait for backend to be healthy
        print("⏳ Waiting for backend to be healthy...")
        max_wait_seconds = 45
        for i in range(max_wait_seconds):
            if self.backend_process and self.backend_process.poll() is not None:
                print("❌ Backend process exited before becoming healthy")
                print(self._tail_log(self.logs_dir / "backend_startup.log"))
                return False
            if self.check_backend_health():
                print("✅ Backend is healthy!")
                break
            time.sleep(1)
        else:
            print("❌ Backend failed to become healthy")
            print(self._tail_log(self.logs_dir / "backend_startup.log"))
            return False
        
        # Start frontend
        if not self.start_frontend():
            return False
        
        # Check services
        print("\n🔍 Checking services...")
        
        backend_healthy = self.check_backend_health()
        frontend_healthy = self.check_frontend_health()
        
        print(f"Backend API: {'✅ Healthy' if backend_healthy else '❌ Unhealthy'}")
        print(f"Frontend UI: {'✅ Healthy' if frontend_healthy else '❌ Unhealthy'}")
        
        if backend_healthy and frontend_healthy:
            print("\n🎉 Wolf AI 2.0 is running!")
            print("\n📋 Services:")
            print("   • Backend API: http://localhost:8000")
            print("   • Frontend UI: http://localhost:8000 (served by backend)")
            print("   • API Docs: http://localhost:8000/docs")
            print("   • WebSocket: ws://localhost:8000/ws/status")
            
            if open_browser:
                self.open_browser("http://localhost:8000")
            
            print("\n🎙️  Voice Assistant:")
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
                print("\n🛑 Stopping Wolf AI...")
                
        else:
            print("❌ Some services failed to start")
            return False
        
        # Cleanup
        self.stop()
        return True
    
    def stop(self):
        """Stop all processes."""
        print("🛑 Stopping services...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("✅ Backend stopped")
            except:
                self.backend_process.kill()
                print("✅ Backend killed")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print("✅ Frontend stopped")
            except:
                self.frontend_process.kill()
                print("✅ Frontend killed")

        if self.backend_log_handle:
            try:
                self.backend_log_handle.close()
            except Exception:
                pass
            self.backend_log_handle = None

        if self.frontend_log_handle:
            try:
                self.frontend_log_handle.close()
            except Exception:
                pass
            self.frontend_log_handle = None
        
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
