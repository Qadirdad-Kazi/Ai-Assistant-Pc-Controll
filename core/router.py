"""
FunctionGemma Router - Routes user prompts to appropriate functions.
Supports 9 functions: 6 actions, 1 context, 2 passthrough.
"""

import os
import warnings
import requests  # type: ignore

# Suppress transformers warnings before importing
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore", message=".*generation flags are not valid.*")

import torch  # type: ignore
from transformers import AutoTokenizer, AutoModelForCausalLM, logging as transformers_logging  # type: ignore
from transformers.utils import get_json_schema  # type: ignore
from typing import Literal, Tuple, Dict, Any, Optional
import time
import re
import json
from huggingface_hub import snapshot_download  # type: ignore

# Suppress transformers logging
transformers_logging.set_verbosity_error()

from config import LOCAL_ROUTER_PATH, HF_ROUTER_REPO, OLLAMA_URL, RESPONDER_MODEL  # type: ignore

# Debug flag - set to True to see Gemma's raw response
DEBUG_ROUTER = False


# --- Tool Definitions (God-Mode essentials) ---
def pc_control(action: str, target: Optional[str] = None):
    """
    Execute system-level commands like controlling volume, opening apps, or locking the PC.
    
    Args:
        action: The system action: open_app, close_app, volume, lock, etc.
        target: The app name or specific value (e.g., 'Spotify', '50')
    """
    pass

def play_music(query: str, service: str = "youtube"):
    """
    Search and play music using YouTube or sync with Spotify.
    
    Args:
        query: Song name, artist, or music genre to play.
        service: 'youtube' to search and play a stream, or 'spotify' to sync/play via Spotify.
    """
    pass

def thinking(prompt: str):
    """
    Use for complex queries requiring reasoning, math, coding, or multi-step analysis.
    
    Args:
        prompt: The user's original prompt
    """
    pass

def nonthinking(prompt: str):
    """
    Use for simple queries, greetings, chitchat, and general knowledge.
    
    Args:
        prompt: The user's original prompt
    """
    pass


def scaffold_website(prompt: str, framework: str = "html"):
    """
    Build an entire React/Next.js/Python project or website from a prompt.
    
    Args:
        prompt: The user's description of what to build
        framework: react, nextjs, python, html
    """
    pass

def set_call_directive(caller_name: str, instructions: str):
    """
    Instruct the AI to handle an expected incoming phone call on your behalf.
    
    Args:
        caller_name: Name or number of the person expected to call
        instructions: Detailed instructions on what to ask or say to the caller
    """
    pass

def visual_agent(task: str):
    """
    Use the visual AI to look at the screen, find an element, icon, or button on the screen, and click it.
    
    Args:
        task: What to find and click on (e.g., 'the Spotify icon on desktop', 'the submit button').
    """
    pass

def create_task(title: str, description: str):
    """
    Create a new task with a title and plain English description.
    
    Args:
        title: Brief title for the task
        description: Detailed description of what to do in plain English
    """
    pass

def list_tasks(status: Optional[str] = None):
    """
    List all tasks, optionally filtered by status.
    
    Args:
        status: Filter by status ('pending', 'completed', 'failed'). If None, shows all tasks.
    """
    pass

def execute_task(task_id: Optional[str] = None, description: Optional[str] = None):
    """
    Execute a task either by ID or by providing a description.
    
    Args:
        task_id: ID of an existing task to execute
        description: Plain English description of what to execute (used if task_id not provided)
    """
    pass

# Pre-compute tool schemas
TOOLS = [
    get_json_schema(pc_control),
    get_json_schema(play_music),
    get_json_schema(thinking),
    get_json_schema(nonthinking),
    get_json_schema(scaffold_website),
    get_json_schema(set_call_directive),
    get_json_schema(visual_agent),
    get_json_schema(create_task),
    get_json_schema(list_tasks),
    get_json_schema(execute_task)
]

# All valid function names
VALID_FUNCTIONS = {
    "pc_control", "play_music", "thinking", "nonthinking", "scaffold_website", 
    "set_call_directive", "visual_agent", "create_task", "list_tasks", "execute_task", "task_complete"
}


def ensure_model_available(model_path: str = LOCAL_ROUTER_PATH) -> Optional[str]:
    """
    Ensure the router model is available locally.
    Downloads from Hugging Face if not found.
    
    Returns:
        str or None: Path to the model, or None if download fails
    """
    if os.path.exists(model_path) and os.path.isdir(model_path):
        # Check for essential files
        if os.path.exists(os.path.join(model_path, "model.safetensors")):
            return model_path
    
    # Download from Hugging Face
    if not HF_ROUTER_REPO:
        print(f"[Router] Model not found locally. Proceeding with Ollama Fallback...")
        return None
        
    print(f"[Router] Attempting download from Hugging Face: {HF_ROUTER_REPO}...")
    
    try:
        from huggingface_hub import snapshot_download  # type: ignore
        downloaded_path = snapshot_download(
            repo_id=HF_ROUTER_REPO,
            local_dir=model_path,
            local_dir_use_symlinks=False
        )
        print(f"[Router] ✓ Model downloaded to {downloaded_path}")
        return downloaded_path
    except Exception as e:
        print(f"[Router] ERROR: Failed to download model from {HF_ROUTER_REPO}: {e}")
        print(f"[Router] Falling back to Ollama-based routing.")
        return None


class FunctionGemmaRouter:
    """Routes user prompts to appropriate functions using fine-tuned FunctionGemma or Ollama fallback."""
    
    def __init__(self, model_path: str = LOCAL_ROUTER_PATH, compile_model: bool = False):
        # Ensure model is available (download from HF if needed)
        self.model_path = ensure_model_available(model_path)
        self.use_ollama_fallback = self.model_path is None
        
        if not self.use_ollama_fallback:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Loading FunctionGemma Router on {device.upper()}...")
            start = time.time()
            
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                
                # CPU often doesn't support bfloat16 natively
                dtype = torch.bfloat16 if device == "cuda" else torch.float32
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    torch_dtype=dtype,
                    device_map=device,
                )
                self.model.eval()

                # Compile for speed (PyTorch 2.0+)
                if compile_model:
                    try:
                        self.model = torch.compile(self.model, mode="reduce-overhead")
                        print("Model compiled with torch.compile()")
                    except Exception as e:
                        print(f"torch.compile() not available: {e}")
                
                print(f"Router loaded in {time.time() - start:.2f}s")
                print(f"Device: {self.model.device}, Dtype: {self.model.dtype}")
            except Exception as e:
                print(f"[Router] Failed to load local model: {e}")
                print(f"[Router] Switching to Ollama-based routing.")
                self.use_ollama_fallback = True
                self.model = None
                self.tokenizer = None
        else:
            self.model = None
            self.tokenizer = None
            print("[Router] Initialized in Ollama Fallback mode.")
    
    def _ollama_route(self, user_prompt: str) -> str:
        """Fallback routing using Ollama."""
        print(f"[Router] Using Ollama fallback for: '{user_prompt}'")
        
        fallback_prompt = f"""
        You are the neural mission router for Wolf AI.
        Determine which holographic action to trigger for the user's prompt.
        
        Available functions:
        - pc_control(action, target): Execute system commands. [action: 'open_app', 'close_app', 'volume', 'lock', 'shutdown', 'restart', 'sleep', 'empty_trash', 'minimize_all', 'screenshot', 'mute', 'media', 'command'] -> for 'command', set target to the exact terminal/powershell command to run.
        - play_music(query, service): Search and play music. [service: 'youtube', 'spotify']
        - scaffold_website(prompt, framework): Build an entire website/app. [framework: 'react', 'nextjs', 'html', 'python']
        - set_call_directive(caller_name, instructions): Delegate an upcoming phone call.
        - visual_agent(task): Use visual AI to find and click elements on screen.
        - create_task(title, description): Create a new task with plain English description.
        - list_tasks(status): List tasks, optionally filtered by status.
        - execute_task(task_id, description): Execute a task by ID or description.
        - thinking(prompt): Multi-step reasoning, math, code, or complexity.
        - nonthinking(prompt): Simple greetings, chitchat, or direct facts.

        IMPORTANT ROUTING RULES:
        1. ANY request to open/close applications, control volume, shutdown, restart, or system control -> use pc_control
        2. App names like "visual studio", "chrome", "spotify", "notepad", "vs code", "visualstudio" -> use pc_control with action: 'open_app'. NEVER include the rest of the sentence in the target!
        3. System commands like "volume up", "mute", "lock screen" -> use pc_control
        4. Keywords "open", "launch", "start", "run" followed by app name -> use pc_control
        5. Complex multi-step tasks -> OUTPUT MULTIPLE FUNCTION CALLS, one per line!
        6. Task execution commands like "create a presentation", "organize my files", "research topic" -> use thinking
        7. Questions about capabilities, "tell me about yourself", "what can you do", "who are you" -> use nonthinking with capability overview
        8. Only use nonthinking for greetings, goodbyes, simple questions, and casual chat
        9. Only use thinking for complex problems, math, coding, or multi-step reasoning
        10. If the user asks you to create files, folders, or run system scripts, use pc_control with action: 'command' and target as the exact Powershell command to run!

        Output function calls in this syntax: call:function_name{{arg1:value1,arg2:value2}}
        If the user asks multiple things, output MULTIPLE lines:
        call:function1{{...}}
        call:function2{{...}}
        
        Example 1: "open visual studio" -> call:pc_control{{action:open_app,target:visual studio}}
        Example 2: "open visualstudio code" -> call:pc_control{{action:open_app,target:visual studio code}}
        Example 3: "open chrome then create a react app" -> 
        call:pc_control{{action:open_app,target:chrome}}
        call:scaffold_website{{prompt:create a react app,framework:react}}
        Example 4: "turn off pc" -> call:pc_control{{action:shutdown,target:}}
        Example 5: "hello" -> call:nonthinking{{prompt:hello}}
        Example 6: "calculate 2+2" -> call:thinking{{prompt:calculate 2+2}}
        Example 7: "play music on spotify" -> call:play_music{{query:music,service:spotify}}
        Example 8: "open chrome" -> call:pc_control{{action:open_app,target:chrome}}
        Example 9: "open vs code then open desktop in it and make an html file" -> 
        call:pc_control{{action:open_app,target:vs code}}
        call:thinking{{prompt:open desktop in vs code and make an html file}}
        Example 10: "create a presentation about marketing" -> call:thinking{{prompt:create a presentation about marketing}}

        User Prompt: {user_prompt}
        Decision:"""

        try:
            response = requests.post(f"{OLLAMA_URL}/generate", json={
                "model": RESPONDER_MODEL,
                "prompt": fallback_prompt,
                "stream": False,
                "options": {"num_predict": 150, "temperature": 0.1}
            }, timeout=10).json()
            
            raw_response = response.get("response", "").strip()
            print(f"[Router] Ollama raw response: '{raw_response}'")
            return raw_response
        except Exception as e:
            print(f"[Router Fallback Error] {e}")
            return f"call:nonthinking{{prompt:<escape>{user_prompt}<escape>}}"

    @torch.inference_mode()
    def route(self, user_prompt: str) -> list[Tuple[str, Dict[str, Any]]]:
        """
        Route a user prompt to the appropriate function.
        
        Returns:
            List of Tuples of (function_name, arguments_dict)
        """
        if self.use_ollama_fallback:
            response = self._ollama_route(user_prompt)
            return self._parse_function_call(response, user_prompt)

        # Define system message
        SYSTEM_MSG = "You are a helpful AI routing assistant. You must map the user's request to the correct function."
        
        # Build messages
        messages = [
            {"role": "developer", "content": SYSTEM_MSG},
            {"role": "user", "content": user_prompt},
        ]
        
        # Apply chat template
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tools=TOOLS,
            add_generation_prompt=True,
            tokenize=False
        )
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        # Generate with minimal settings for speed
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=100,  # Increased for function args
            do_sample=False,
            use_cache=True,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        
        # Decode new tokens only
        new_tokens = outputs[0][inputs['input_ids'].shape[1]:]
        response = self.tokenizer.decode(new_tokens, skip_special_tokens=False)
        
        # Debug: Print raw Gemma response
        if DEBUG_ROUTER:
            print(f"\n{'='*50}")
            print(f"[Router DEBUG] User prompt: {user_prompt}")
            print(f"[Router DEBUG] Raw Gemma response:")
            print(f"  {repr(response)}")
            print(f"{'='*50}")
        
        # Parse function call
        return self._parse_function_call(response, user_prompt)
    
    def _parse_function_call(self, response: str, user_prompt: str) -> list[Tuple[str, Dict[str, Any]]]:
        """Parse model's response to extract function name and arguments."""
        
        print(f"[Router] Parsing response: '{response}'")
        calls = []
        
        # Check for both formats: call:func{...} and func(...)
        for func_name in VALID_FUNCTIONS:
            # Pattern 1: call:func_name{...} (allow newlines inside)
            pattern1 = rf"call:{func_name}\{{([^}}]*)\}}"
            for match in re.finditer(pattern1, response, re.DOTALL):
                args_str = match.group(1)
                full_match = match.group(0)
                print(f"[Router] Found function: {func_name} (Format 1)")
                args = self._extract_arguments(full_match, func_name, user_prompt)
                print(f"[Router] Extracted args: {args}")
                calls.append((func_name, args))
                
            # Pattern 2: func_name(...) (allow newlines inside)
            pattern2 = rf"{func_name}\((.*?)\)"
            for match in re.finditer(pattern2, response, re.DOTALL):
                # Ensure it's not preceded by 'def ' or similar python keywords 
                args_str = match.group(1)
                full_match = match.group(0)
                print(f"[Router] Found function: {func_name} (Format 2)")
                args = self._extract_arguments(full_match, func_name, user_prompt)
                print(f"[Router] Extracted args: {args}")
                calls.append((func_name, args))
        
        # Fallback to nonthinking if no function found
        if not calls:
            print(f"[Router] No function found, falling back to nonthinking")
            return [("nonthinking", {"prompt": user_prompt})]
            
        return calls
    
    def _extract_arguments(self, response: str, func_name: str, user_prompt: str) -> Dict[str, Any]:
        """Extract arguments from the response."""
        
        # Default arguments for passthrough functions
        if func_name in ("thinking", "nonthinking"):
            return {"prompt": user_prompt}
        
        
        # New robust parsing logic
        
        # 1) Try standard call:func{...} regex
        pattern = rf"call:{func_name}\{{([^}}]+)\}}"
        match = re.search(pattern, response)
        
        args: Dict[str, Any] = {}
        if match:
            args_str = match.group(1)
            
            # Simple key-value parser recognizing both standard and <escape> formats
            # Key can be wrapped in quotes
            key_val_pairs = re.findall(r'[\'"]?(\w+)[\'"]?\s*:\s*(?:<escape>(.*?)<escape>|[\'"](.*?)[\'"]|([^,]+))', args_str)
            for k_v_match in key_val_pairs:
                key = k_v_match[0]
                # Coalesce the matched value groups
                value = next((v for v in k_v_match[1:] if v), "").strip()
                
                if value.isdigit():
                    args[key] = int(value)
                elif value.lower() in ('true', 'false'):
                    args[key] = value.lower() == 'true'
                else:
                    args[key] = value
                    
            if args:
                return args
                
        # 2) Try functional syntax func(kwarg=val)
        pattern_func = rf"{func_name}\((.*?)\)"
        match_func = re.search(pattern_func, response)
        if match_func:
            args_str = match_func.group(1)
            # Find kwargs: key='value' or key="value" or key=value
            kwarg_pairs = re.findall(r'(\w+)\s*=\s*(?:[\'"](.*?)[\'"]|([^,]+))', args_str)
            for k_v_match in kwarg_pairs:
                key = k_v_match[0]
                value = k_v_match[1] if k_v_match[1] else k_v_match[2]
                args[key] = value.strip()
                
            if args:
                return args
        
        # If we reach here and couldn't parse the dictionary, return a default safe empty dict
        # DO NOT fallback to opening the whole user_prompt as an app, because if the AI writes a bad syntax, it will bug out.
        if func_name == "pc_control":
            # Just do nothing safely
            return {"action": "unknown", "target": ""}
        elif func_name == "play_music":
            return {"query": user_prompt}
        elif func_name == "scaffold_website":
            return {"prompt": user_prompt, "framework": "html"}
        elif func_name == "set_call_directive":
            return {"caller_name": "Unknown", "instructions": user_prompt}
        
        return {}
    
    def route_with_timing(self, user_prompt: str) -> Tuple[list[Tuple[str, Dict[str, Any]]], float]:
        """Route with timing info."""
        start = time.time()
        result = self.route(user_prompt)
        elapsed = time.time() - start
        return result, elapsed


if __name__ == "__main__":
    router = FunctionGemmaRouter(compile_model=False)
    
    test_prompts = [
        # Action functions
        ("Open Spotify", "pc_control"),
        ("Lower the volume to 20", "pc_control"),
        ("Lock the computer", "pc_control"),
        ("Play some lo-fi music", "play_music"),
        ("Build a quick react app for a todo list", "scaffold_website"),
        ("Rafay will call you soon, ask him what time the meeting is", "set_call_directive"),
        
        # Passthrough functions
        ("Explain quantum computing", "thinking"),
        ("Write a Python function to sort a list", "thinking"),
        ("Hello there!", "nonthinking"),
        ("What's the capital of France?", "nonthinking"),
    ]
    
    print("\n" + "="*70)
    print("FUNCTION CALLING ROUTER TEST")
    print("="*70)
    
    total_time: float = 0.0
    correct: int = 0
    
    for prompt, expected in test_prompts:
        calls, elapsed = router.route_with_timing(prompt)
        func_name, args = calls[0] if calls else ("unknown", {})
        total_time += elapsed
        match = "✓" if func_name == expected else "✗"
        if func_name == expected:
            correct += 1  # type: ignore
        
        print(f"\n[{match}] {prompt}")
        print(f"    → {func_name}({args}) [{elapsed*1000:.0f}ms]")
    
    avg_time = total_time / len(test_prompts)
    print(f"\n{'='*70}")
    print(f"Accuracy: {correct}/{len(test_prompts)} ({100*correct/len(test_prompts):.0f}%)")  # type: ignore
    print(f"Average routing time: {avg_time*1000:.0f}ms per prompt")
    print(f"Total time: {total_time:.2f}s for {len(test_prompts)} prompts")
