"""Debug script to see raw model output."""
import torch
from core.router import FunctionGemmaRouter, TOOLS

router = FunctionGemmaRouter(compile_model=False)

SYSTEM_MSG = "You are a model that can do function calling with the following functions"

test_prompts = [
    "Turn on the living room lights",
    "Set a timer for 10 minutes",
    "Add buy groceries to my list",
]

for user_prompt in test_prompts:
    messages = [
        {"role": "developer", "content": SYSTEM_MSG},
        {"role": "user", "content": user_prompt},
    ]
    
    prompt = router.tokenizer.apply_chat_template(
        messages, tools=TOOLS, add_generation_prompt=True, tokenize=False
    )
    inputs = router.tokenizer(prompt, return_tensors="pt").to(router.model.device)
    
    with torch.inference_mode():
        outputs = router.model.generate(
            **inputs, 
            max_new_tokens=150, 
            do_sample=False, 
            use_cache=True, 
            pad_token_id=router.tokenizer.pad_token_id
        )
    
    new_tokens = outputs[0][inputs['input_ids'].shape[1]:]
    response = router.tokenizer.decode(new_tokens, skip_special_tokens=False)
    
    print(f"\n{'='*60}")
    print(f"PROMPT: {user_prompt}")
    print(f"RAW OUTPUT: {repr(response)}")
    print(f"{'='*60}")
