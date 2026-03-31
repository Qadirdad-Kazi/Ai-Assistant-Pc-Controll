import subprocess
import os
import sys
import time

def start_vision_server():
    """Starts the OmniParser server using its dedicated venv."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    engine_dir = os.path.join(root_dir, "engines", "omni_parser")
    venv_python = "/Users/qadirdadkazi/Desktop/Github Clones/Ai-Assistant-Pc-Controll/engines/omni_parser/venv/bin/python3"
    server_script = "/Users/qadirdadkazi/Desktop/Github Clones/Ai-Assistant-Pc-Controll/engines/omni_parser/omnitool/omniparserserver/omniparserserver.py"

    if not os.path.exists(venv_python):
        print(f"[!] Error: Vision Venv not found at {venv_python}")
        return False

    print(f"[*] Starting OmniParser Vision Server on Port 8001...")
    
    # We use a subprocess.Popen to let it run in the background if called from another script
    # or just run it directly if called manually
    try:
        # Note: We need to set the PYTHONPATH to include the omni_parser root so it can find its utils
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{engine_dir}:{env.get('PYTHONPATH', '')}"
        
        process = subprocess.Popen(
            [venv_python, server_script],
            cwd=engine_dir,  # Run from the engine dir for internal relative imports
            env=env
        )
        
        print(f"[*] Vision Server PID: {process.pid}")
        print("[*] Waiting for heartbeat on http://localhost:8001...")
        return True
    except Exception as e:
        print(f"[!] Critical Error starting Vision Server: {e}")
        return False

if __name__ == "__main__":
    start_vision_server()
    # Keep the main thread alive if run directly
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down Vision Server...")
