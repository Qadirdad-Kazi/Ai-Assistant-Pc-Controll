"""
FunctionGemma Router - Routes user prompts to appropriate functions.
Supports 9 functions: 6 actions, 1 context, 2 passthrough.
"""

import os
import warnings

# Suppress transformers warnings before importing
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore", message=".*generation flags are not valid.*")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, logging as transformers_logging
from transformers.utils import get_json_schema
from typing import Literal, Tuple, Dict, Any
import time
import re
import json
from huggingface_hub import snapshot_download

# Suppress transformers logging
transformers_logging.set_verbosity_error()

from config import LOCAL_ROUTER_PATH, HF_ROUTER_REPO

# Debug flag - set to True to see Gemma's raw response
DEBUG_ROUTER = False


# --- Tool Definitions (God-Mode essentials) ---
def pc_control(action: str, target: str = None):
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

# Pre-compute tool schemas
TOOLS = [
    get_json_schema(pc_control),
    get_json_schema(play_music),
    get_json_schema(thinking),
    get_json_schema(nonthinking),
    get_json_schema(scaffold_website),
    get_json_schema(set_call_directive)
]

# All valid function names
VALID_FUNCTIONS = {
    "pc_control", "play_music", "thinking", "nonthinking", "scaffold_website", "set_call_directive"
}


def ensure_model_available(model_path: str = LOCAL_ROUTER_PATH) -> str:
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
        from huggingface_hub import snapshot_download
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
        """Use the main LLM (Ollama) to perform routing via prompting."""
        from config import OLLAMA_URL, RESPONDER_MODEL
        import requests
        
        fallback_prompt = f"""
        You are the neural mission router for Wolf AI.
        Determine which holographic action to trigger for the user's prompt.
        
        Available functions:
        - pc_control(action, target): Execute system commands. [action: 'open_app', 'close_app', 'volume', 'lock', 'shutdown', 'restart', 'sleep', 'empty_trash', 'minimize_all', 'screenshot', 'mute', 'media']
        - play_music(query, service): Search and play music. [service: 'youtube', 'spotify']
        - scaffold_website(prompt, framework): Build an entire website/app. [framework: 'react', 'nextjs', 'html', 'python']
        - set_call_directive(caller_name, instructions): Delegate an upcoming phone call.
        - thinking(prompt): Multi-step reasoning, math, code, or complexity.
        - nonthinking(prompt): Simple greetings, chitchat, or direct facts.

        Output ONLY the function call in this syntax: call:function_name{{arg1:value1,arg2:value2}}
        Example 1: Tasking to turn on kitchen lights -> call:control_light{{action:on,room:kitchen}}
        Example 2: User says hello -> call:nonthinking{{prompt:hello}}
        Example 3: Complex math -> call:thinking{{prompt:calculate 2+2}}
        Example 4: Rafay will call, ask about the meeting -> call:set_call_directive{{caller_name:Rafay,instructions:ask about the meeting}}

        User Prompt: {user_prompt}
        Decision:"""

        try:
            response = requests.post(f"{OLLAMA_URL}/generate", json={
                "model": RESPONDER_MODEL,
                "prompt": fallback_prompt,
                "stream": False,
                "options": {"num_predict": 50, "temperature": 0.1}
            }, timeout=10).json()
            
            return response.get("response", "").strip()
        except Exception as e:
            print(f"[Router Fallback Error] {e}")
            return f"call:nonthinking{{prompt:<escape>{user_prompt}<escape>}}"

    @torch.inference_mode()
    def route(self, user_prompt: str) -> Tuple[str, Dict[str, Any]]:
        """
        Route a user prompt to the appropriate function.
        
        Returns:
            Tuple of (function_name, arguments_dict)
        """
        if self.use_ollama_fallback:
            response = self._ollama_route(user_prompt)
            return self._parse_function_call(response, user_prompt)

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
    
    def _parse_function_call(self, response: str, user_prompt: str) -> Tuple[str, Dict[str, Any]]:
        """Parse the model's response to extract function name and arguments."""
        
        # Try to find function call pattern: call:function_name
        for func_name in VALID_FUNCTIONS:
            if f"call:{func_name}" in response:
                # Try to extract arguments
                args = self._extract_arguments(response, func_name, user_prompt)
                return func_name, args
        
        # Fallback to nonthinking if no function found
        return "nonthinking", {"prompt": user_prompt}
    
    def _extract_arguments(self, response: str, func_name: str, user_prompt: str) -> Dict[str, Any]:
        """Extract arguments from the response."""
        
        # Default arguments for passthrough functions
        if func_name in ("thinking", "nonthinking"):
            return {"prompt": user_prompt}
        
        
        # Parse the model's custom format: {key:<escape>value<escape>,key2:<escape>value2<escape>}
        # Find the arguments block after the function name
        pattern = rf"call:{func_name}\{{([^}}]+)\}}"
        match = re.search(pattern, response)
        
        if match:
            args_str = match.group(1)
            args = {}
            
            # Split by comma, but handle values with commas inside <escape> tags
            # Pattern: key:<escape>value<escape> OR key:value (for ints/bools)
            # We look for key followed by either <escape>...<escape> OR anything until comma/end
            arg_pattern = r'(\w+):(?:<escape>([^<]*)<escape>|([^,]+))'
            for arg_match in re.finditer(arg_pattern, args_str):
                key = arg_match.group(1)
                # group(2) is escaped value, group(3) is unescaped value
                val_escaped = arg_match.group(2)
                val_unescaped = arg_match.group(3)
                
                value = val_escaped if val_escaped is not None else val_unescaped
                
                # Try to convert to appropriate type
                if value.isdigit():
                    args[key] = int(value)
                elif value.lower() in ('true', 'false'):
                    args[key] = value.lower() == 'true'
                else:
                    args[key] = value
            
            if args:
                return args
        
        if func_name == "pc_control":
            return {"action": "open_app", "target": user_prompt}
        elif func_name == "play_music": # Added play_music fallback
            return {"query": user_prompt}
        elif func_name == "scaffold_website":
            return {"prompt": user_prompt, "framework": "html"}
        elif func_name == "set_call_directive":
            return {"caller_name": "Unknown", "instructions": user_prompt}
        
        return {}
    
    def route_with_timing(self, user_prompt: str) -> Tuple[Tuple[str, Dict], float]:
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
    
    total_time = 0
    correct = 0
    
    for prompt, expected in test_prompts:
        (func_name, args), elapsed = router.route_with_timing(prompt)
        total_time += elapsed
        match = "✓" if func_name == expected else "✗"
        if func_name == expected:
            correct += 1
        
        print(f"\n[{match}] {prompt}")
        print(f"    → {func_name}({args}) [{elapsed*1000:.0f}ms]")
    
    avg_time = total_time / len(test_prompts)
    print(f"\n{'='*70}")
    print(f"Accuracy: {correct}/{len(test_prompts)} ({100*correct/len(test_prompts):.0f}%)")
    print(f"Average routing time: {avg_time*1000:.0f}ms per prompt")
    print(f"Total time: {total_time:.2f}s for {len(test_prompts)} prompts")
