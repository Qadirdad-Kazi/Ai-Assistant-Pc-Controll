"""
Upload the FunctionGemma router model to Hugging Face Hub.

Usage:
    1. Login to Hugging Face: huggingface-cli login
    2. Run: python upload_model.py
"""

from huggingface_hub import HfApi, create_repo
from config import LOCAL_ROUTER_PATH, HF_ROUTER_REPO
import os

def upload_model():
    """Upload the merged model to Hugging Face Hub."""
    
    if not os.path.exists(LOCAL_ROUTER_PATH):
        print(f"Error: Model not found at {LOCAL_ROUTER_PATH}")
        print("Train the model first using: python train_function_gemma.py")
        return
    
    api = HfApi()
    
    # Create repo if it doesn't exist
    try:
        create_repo(HF_ROUTER_REPO, repo_type="model", exist_ok=True)
        print(f"Repository ready: https://huggingface.co/{HF_ROUTER_REPO}")
    except Exception as e:
        print(f"Repo creation note: {e}")
    
    # Upload all files from merged_model folder
    print(f"Uploading model from {LOCAL_ROUTER_PATH}...")
    
    api.upload_folder(
        folder_path=LOCAL_ROUTER_PATH,
        repo_id=HF_ROUTER_REPO,
        repo_type="model",
        commit_message="Upload FunctionGemma router model"
    )
    
    print(f"\n✓ Model uploaded successfully!")
    print(f"  View at: https://huggingface.co/{HF_ROUTER_REPO}")

if __name__ == "__main__":
    upload_model()
