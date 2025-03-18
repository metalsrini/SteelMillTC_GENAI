#!/usr/bin/env python3
"""
Download DeepSeek model in GGUF format for local inference

This script downloads the DeepSeek model in GGUF format from Hugging Face
and saves it to the models directory.
"""

import os
import sys
import requests
import time
from tqdm import tqdm

# Configuration
MODEL_REPO = "TheBloke/deepseek-llm-7b-chat-GGUF"
MODEL_FILE = "deepseek-llm-7b-chat.Q4_K_M.gguf"  # Q4_K_M is a good balance of quality and size
MODELS_DIR = "./models"
HF_API_TOKEN = os.environ.get("HF_TOKEN", "")  # Optional: Your Hugging Face token

def download_file(url, destination, token=None):
    """Download a file with progress bar"""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    print(f"Downloading {url} to {destination}")
    
    response = requests.get(url, headers=headers, stream=True)
    
    if response.status_code != 200:
        print(f"Error downloading file: {response.status_code} {response.reason}")
        print(response.text)
        return False
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024  # 1MB
    
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    with open(destination, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=MODEL_FILE) as pbar:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    
    print(f"Download completed: {destination}")
    return True

def main():
    """Main function"""
    print("Preparing to download DeepSeek model for local inference")
    
    # Create models directory if it doesn't exist
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Full path to the model file
    model_path = os.path.join(MODELS_DIR, MODEL_FILE)
    
    # Check if model already exists
    if os.path.exists(model_path):
        print(f"Model already exists at {model_path}")
        print("Do you want to download it again? (y/n)")
        
        choice = input().strip().lower()
        if choice != 'y':
            print("Download cancelled")
            return
    
    # Hugging Face download URL
    hf_url = f"https://huggingface.co/{MODEL_REPO}/resolve/main/{MODEL_FILE}"
    
    print(f"Starting download of DeepSeek model (~4GB)...")
    print(f"This may take a while depending on your internet connection.")
    
    success = download_file(hf_url, model_path, HF_API_TOKEN)
    
    if success:
        print("\n--------------------------------------------------")
        print(f"✅ Model downloaded successfully to: {model_path}")
        print("--------------------------------------------------")
        print("You can now run the application with:")
        print("python run.py")
        print("\nMake sure to set the environment variable:")
        print(f"LOCAL_MODEL_PATH={model_path}")
        print("--------------------------------------------------")
    else:
        print("\n❌ Model download failed.")
        print("Please check your internet connection and try again.")
        print("If you have a Hugging Face account, set the HF_TOKEN environment variable.")

if __name__ == "__main__":
    main() 