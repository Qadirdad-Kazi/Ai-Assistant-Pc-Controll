"""
Dev Agent - Autonomous developer assistant.
Handles interactive project scaffolding and actual code generation using Ollama.
"""

import os
import subprocess
import requests
import re
from typing import Dict, Any
from config import OLLAMA_URL, RESPONDER_MODEL

class DevAgent:
    def __init__(self, workspace_dir: str = "./workspace"):
        self.workspace_dir = os.path.abspath(workspace_dir)
        os.makedirs(self.workspace_dir, exist_ok=True)
        self.active_session = False
        self.collected_requirements = ""
        self.project_name = "wolf_project"
        
    def scaffold_project(self, prompt: str, framework: str = "html") -> Dict[str, Any]:
        """
        Interactively scaffolds a project. Asks questions if details are sparse.
        """
        # Append the new prompt to our running requirements
        if self.collected_requirements:
            self.collected_requirements += "\\n" + prompt
        else:
            self.collected_requirements = prompt
            
        print(f"[DevAgent] Current Requirements: {self.collected_requirements}")
        
        # Step 1: Ask LLM if we have enough info to build
        eval_prompt = f"""
        You are Wolf AI's elite Developer Agent. The user wants to build a software project.
        Current accumulated requirements from user: "{self.collected_requirements}"
        
        Evaluate these requirements. 
        If the requirements are very vague (e.g., "build a web", "make an app"), ask exactly ONE natural follow-up question to clarify (e.g., "What framework would you like to use, like React or NextJS, and what is the main purpose of the app?"). Do not say anything else.
        If the requirements are sufficiently detailed (contains a framework like html, react, or python, AND a specific purpose/app idea), reply with EXACTLY the word "READY_TO_BUILD".
        """
        
        try:
            response = requests.post(f"{OLLAMA_URL}/generate", json={
                "model": RESPONDER_MODEL,
                "prompt": eval_prompt,
                "stream": False
            }, timeout=30)
            
            if response.status_code == 200:
                answer = response.json().get("response", "").strip()
            else:
                answer = "READY_TO_BUILD" # Fallback
                
        except Exception as e:
            print(f"[DevAgent] LLM connection error: {e}")
            return {"success": False, "message": f"Dev Agent Error: {e}"}

        # Step 2: Handle LLM Decision
        if "READY_TO_BUILD" not in answer.upper():
            # The LLM asked a question! Return it to the chat loop.
            return {
                "success": True,
                "message": f"🤖 **Dev Agent:** {answer}",
                "data": {"status": "gathering_info"}
            }
            
        # Step 3: We are ready! Reset session and actually build it
        final_reqs = self.collected_requirements
        self.collected_requirements = "" # Reset for next time
        
        build_msg = f"🚀 **Dev Agent initializing build sequence...**\\nBuilding based on: *{final_reqs}*\\nPlease wait..."
        
        # We will attempt to run the build in the background or block.
        # For this demo, let's execute CLI commands sequentially.
        try:
            target_dir = os.path.join(self.workspace_dir, self.project_name)
            
            # Determine actual framework intended (LLM could do this, but we fallback to substring)
            if "react" in final_reqs.lower() or "vite" in final_reqs.lower():
                actual_fw = "react"
            elif "python" in final_reqs.lower() or "api" in final_reqs.lower():
                actual_fw = "python"
            else:
                actual_fw = "html"

            if actual_fw == "react":
                print("[DevAgent] Using Vite to scaffold React app...")
                # Run Vite (requires npm/npx)
                # Shell=True is necessary on Windows for npx
                subprocess.run(
                    f"npx -y create-vite@latest {self.project_name} --template react", 
                    cwd=self.workspace_dir, 
                    shell=True, 
                    check=False
                )
                
                # Further, we could use LLM to write the App.jsx
                self._generate_and_write_file(
                    final_reqs, 
                    os.path.join(target_dir, "src", "App.jsx"),
                    "We have a React+Vite app. Write the complete, beautiful CSS/React content for src/App.jsx. Return ONLY the raw code."
                )
                
                final_status = f"✅ **React App Scaffolded!**\\nYour project is ready at: `{target_dir}`\\nRun `cd workspace/{self.project_name}` then `npm install` and `npm run dev`."
                
            elif actual_fw == "python":
                print("[DevAgent] Scaffolding Python app...")
                os.makedirs(os.path.join(target_dir, "src"), exist_ok=True)
                
                self._generate_and_write_file(
                    final_reqs,
                    os.path.join(target_dir, "src", "main.py"),
                    "Write a complete, documented Python script/app meeting these requirements. Output ONLY the raw Python code."
                )
                with open(os.path.join(target_dir, "requirements.txt"), "w") as f:
                    f.write("# Add your python dependencies here\\n")
                    
                final_status = f"✅ **Python App Scaffolded!**\\nYour script is ready at: `{target_dir}/src/main.py`"
                
            else:
                # Default HTML
                print("[DevAgent] Scaffolding HTML app...")
                os.makedirs(target_dir, exist_ok=True)
                
                self._generate_and_write_file(
                    final_reqs,
                    os.path.join(target_dir, "index.html"),
                    "Write a beautiful, modern standalone HTML file containing CSS and JS to meet these requirements. Make it look super premium. Output ONLY the raw HTML code."
                )
                
                final_status = f"✅ **HTML/JS App Scaffolded!**\\nYour webpage is ready at: `{target_dir}/index.html`"

            return {
                "success": True,
                "message": final_status,
                "data": {"path": target_dir, "framework": actual_fw}
            }

        except Exception as e:
            return {"success": False, "message": f"Dev Agent Build Error: {e}"}

    def _generate_and_write_file(self, reqs: str, filepath: str, instruction: str):
        """Uses local LLM to generate the actual code and writes it to disk."""
        print(f"[DevAgent] Generating code for nearest file: {filepath}...")
        prompt = f"{instruction}\\n\\nRequirements: {reqs}\\n\\nEnsure your response contains NO formatting blocks like ```html, ONLY the raw text that goes straight into the file."
        
        try:
            response = requests.post(f"{OLLAMA_URL}/generate", json={
                "model": RESPONDER_MODEL,
                "prompt": prompt,
                "stream": False
            }, timeout=60)
            
            if response.status_code == 200:
                code_content = response.json().get("response", "").strip()
                # Clean up potential markdown blocks if LLM disobeyed
                code_content = re.sub(r"^```[a-zA-Z]*\\n", "", code_content, flags=re.MULTILINE)
                code_content = re.sub(r"\\n```$", "", code_content, flags=re.MULTILINE)
                code_content = code_content.strip("`")
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(code_content)
                print(f"[DevAgent] ✓ Wrote {filepath}")
        except Exception as e:
            print(f"[DevAgent] Code generation failed for {filepath}: {e}")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"// Failed to generate code: {e}")

# Global instance
dev_agent = DevAgent()
