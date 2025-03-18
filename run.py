#!/usr/bin/env python3
"""
Simple script to run the Mill Test Certificate Analyzer application
"""

import os
import sys

def main():
    print("Starting Mill Test Certificate Analyzer application...")
    
    # Ensure the required directories exist
    for directory in ['processed_files', 'models']:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created {directory} directory")
    
    # Check if using local model
    model_path = os.environ.get("LOCAL_MODEL_PATH", "./models/deepseek-llm-7b-chat.Q4_K_M.gguf")
    if not os.path.exists(model_path):
        print(f"WARNING: Model file not found at: {model_path}")
        print("You need to download the model first to use local inference.")
        print("Run: python download_model.py")
        print("Or set LOCAL_MODEL_PATH environment variable to point to your model file.")
        print("Continuing without local model capability...")
    else:
        print(f"Using local model at: {model_path}")
    
    # Run the Flask application
    os.system('python app.py')

if __name__ == "__main__":
    main() 