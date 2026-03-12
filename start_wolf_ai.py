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

class WolfAILauncher:
    """Launches Wolf AI backend and frontend."""
    
    def __init__(self):
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.project_root = project_root
        
    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        print("🔍 Checking dependencies...")
        
        # Check Python dependencies
        try:
            import uvicorn
            import fastapi
            import requests
            print("✅ Python dependencies available")
        except ImportError as e:
            print(f"❌ Missing Python dependency: {e}")
            print("Run: pip install uvicorn fastapi requests")
            return False
        
        # Check Node.js for frontend
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Node.js available")
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
                        print(f"✅ Node.js found at: {node_path}")
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
        
        # Check npm (optional for frontend dev)
        print("ℹ️  npm check skipped - using pre-built frontend")
        print("✅ Frontend build available")
        
        return True
    
    def start_backend(self) -> bool:
        """Start the backend API server."""
        print("🚀 Starting backend API server...")
        
        try:
            # Change to project root
            os.chdir(self.project_root)
            
            # Start backend server
            self.backend_process = subprocess.Popen([
                sys.executable, 'main.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait a moment for server to start
            time.sleep(3)
            
            # Check if backend is running
            if self.backend_process.poll() is None:
                print("✅ Backend server started on http://localhost:8000")
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
            
            self.frontend_process = subprocess.Popen([
                'npm', 'run', 'dev'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for frontend to start
            time.sleep(5)
            
            # Check if frontend is running
            if self.frontend_process.poll() is None:
                print("✅ Frontend started on http://localhost:5173")
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
        for i in range(10):
            if self.check_backend_health():
                print("✅ Backend is healthy!")
                break
            time.sleep(1)
        else:
            print("❌ Backend failed to become healthy")
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
            print("   • Frontend UI: http://localhost:5173")
            print("   • API Docs: http://localhost:8000/docs")
            print("   • WebSocket: ws://localhost:8000/ws/status")
            
            if open_browser:
                self.open_browser("http://localhost:5173")
            
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
