"""
Train FunctionGemma for function calling with 9 tools.
Based on Google's official documentation.
"""

import torch
import json
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig, PeftModel

# Configuration
MODEL_ID = "google/functiongemma-270m-it"
OUTPUT_DIR = "functiongemma-270m-ft"
MERGED_OUTPUT_DIR = "merged_model"
DATA_FILE = "training_dataset_functions.jsonl"  # New dataset with 9 functions

# --- Tool Definitions (all 9 functions) ---

def control_light(action: str, device_name: str = None, brightness: int = None, color: str = None) -> str:
    """
    Control smart lights - turn on, off, dim, or change color.
    
    Args:
        action: Action to perform: on, off, dim, toggle
        device_name: Name of the light or room
        brightness: Brightness level 0-100
        color: Color name or hex code
    """
    return "result"

def set_timer(duration: str, label: str = None) -> str:
    """
    Set a countdown timer.
    
    Args:
        duration: Duration like '5 minutes' or '1 hour'
        label: Optional label for the timer
    """
    return "result"

def set_alarm(time: str, label: str = None) -> str:
    """
    Set an alarm for a specific time.
    
    Args:
        time: Time for alarm like '7am' or '14:30'
        label: Optional label
    """
    return "result"

def create_calendar_event(title: str, date: str = None, time: str = None, duration: int = None) -> str:
    """
    Create a calendar event.
    
    Args:
        title: Event title
        date: Date like 'tomorrow' or '2024-01-15'
        time: Time like '3pm'
        duration: Duration in minutes
    """
    return "result"

def add_task(text: str, priority: str = None) -> str:
    """
    Add a task to the to-do list.
    
    Args:
        text: Task description
        priority: Priority level
    """
    return "result"

def web_search(query: str) -> str:
    """
    Search the web for information.
    
    Args:
        query: Search query
    """
    return "result"

def get_system_info() -> str:
    """
    Get current system state including timers, calendar, tasks, devices, and weather.
    """
    return "result"

def thinking(prompt: str) -> str:
    """
    Use for complex queries requiring reasoning, math, coding, or multi-step analysis.
    
    Args:
        prompt: The user's original prompt
    """
    return "result"

def nonthinking(prompt: str) -> str:
    """
    Use for simple queries, greetings, factual questions not requiring deep reasoning.
    
    Args:
        prompt: The user's original prompt
    """
    return "result"


# Generate tool schemas
from transformers.utils import get_json_schema
TOOLS = [
    get_json_schema(control_light),
    get_json_schema(set_timer),
    get_json_schema(set_alarm),
    get_json_schema(create_calendar_event),
    get_json_schema(add_task),
    get_json_schema(web_search),
    get_json_schema(get_system_info),
    get_json_schema(thinking),
    get_json_schema(nonthinking),
]

DEFAULT_SYSTEM_MSG = "You are a model that can do function calling with the following functions"


def rebuild_with_proper_schema(sample):
    """Rebuild sample with properly formatted tool schemas."""
    messages = sample["messages"]
    
    # Find the tool call
    tool_name = None
    tool_args = None
    user_content = None
    
    for msg in messages:
        if msg["role"] == "user":
            user_content = msg["content"]
        elif msg["role"] == "assistant" and "tool_calls" in msg:
            tc = msg["tool_calls"][0]["function"]
            tool_name = tc["name"]
            tool_args = tc["arguments"]
    
    if not all([user_content, tool_name]):
        return sample
    
    # Handle empty args for get_system_info
    if tool_args is None:
        tool_args = {}
    
    return {
        "messages": [
            {"role": "developer", "content": DEFAULT_SYSTEM_MSG},
            {"role": "user", "content": user_content},
            {"role": "assistant", "tool_calls": [{"type": "function", "function": {"name": tool_name, "arguments": tool_args}}]},
        ],
        "tools": TOOLS
    }


def train():
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    
    print(f"Loading dataset from {DATA_FILE}...")
    raw_dataset = load_dataset("json", data_files=DATA_FILE, split="train")
    print(f"Dataset size: {len(raw_dataset)}")
    
    # Rebuild with proper tool schemas
    print("Rebuilding with proper tool schemas...")
    dataset = raw_dataset.map(rebuild_with_proper_schema, remove_columns=raw_dataset.column_names)
    
    # Debug: show formatted prompt
    print("\n--- Sample dataset entry ---")
    sample = dataset[0]
    print(f"User: {sample['messages'][1]['content']}")
    print(f"Function: {sample['messages'][2]['tool_calls'][0]['function']['name']}")
    print(f"Args: {sample['messages'][2]['tool_calls'][0]['function']['arguments']}")
    
    debug_msg = tokenizer.apply_chat_template(
        sample["messages"], 
        tools=sample["tools"], 
        add_generation_prompt=False, 
        tokenize=False
    )
    print(f"\n--- Tokenized length: {len(tokenizer.encode(debug_msg))} tokens ---\n")
    
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="eager"
    )
    
    print(f"Device: {model.device}")
    print(f"DType: {model.dtype}")
    
    # LoRA config
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM",
    )
    
    # Training config - optimized for 8GB VRAM
    args = SFTConfig(
        output_dir=OUTPUT_DIR,
        max_length=768, 
        packing=False,
        num_train_epochs=8,
        per_device_train_batch_size=1,  # Reduced for 8GB GPU
        gradient_accumulation_steps=4,  # Effective batch size = 4
        gradient_checkpointing=True,  # Save memory
        optim="adamw_torch_fused",
        logging_steps=10,
        save_strategy="epoch",
        learning_rate=2e-5,
        bf16=True,
        lr_scheduler_type="constant",
        overwrite_output_dir=True,
    )
    
    # Create trainer
    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=dataset,
        peft_config=peft_config,
        processing_class=tokenizer,
    )
    
    print(f"\nStarting training on {len(dataset)} examples...")
    print(f"Functions: control_light, set_timer, set_alarm, create_calendar_event,")
    print(f"           add_task, web_search, get_system_info, thinking, nonthinking")
    print("=" * 60)
    
    trainer.train()
    
    print("Saving adapter...")
    trainer.save_model(OUTPUT_DIR)
    
    # Free memory
    del model
    del trainer
    torch.cuda.empty_cache()
    
    # Merge
    print("\nMerging adapter into base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    
    merged_model = PeftModel.from_pretrained(base_model, OUTPUT_DIR)
    merged_model = merged_model.merge_and_unload()
    
    print(f"Saving merged model to: {MERGED_OUTPUT_DIR}")
    merged_model.save_pretrained(MERGED_OUTPUT_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_OUTPUT_DIR)
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print(f"Merged model saved to: {MERGED_OUTPUT_DIR}")
    print("\nTo test the model, run:")
    print("  python -m core.router")


if __name__ == "__main__":
    train()
