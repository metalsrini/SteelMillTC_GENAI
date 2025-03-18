#!/usr/bin/env python3
"""
Simple script to run the Mill Test Certificate Analyzer application
"""

import os
import sys

def main():
    print("Starting Mill Test Certificate Analyzer application...")
    
    # Ensure the required directories exist
    for directory in ['processed_files']:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created {directory} directory")
    
    # Run the Flask application
    os.system('python app.py')

if __name__ == "__main__":
    main() 