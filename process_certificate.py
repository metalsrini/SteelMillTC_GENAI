#!/usr/bin/env python3
"""
Process a steel mill test certificate PDF using LLMWhisperer.
This script extracts the text from the PDF in a format optimized for LLM consumption.
"""

import os
import sys
import json
import time
from dotenv import load_dotenv
from unstract.llmwhisperer import LLMWhispererClientV2

# Load environment variables
load_dotenv()

# API configuration
API_KEY = "x6VXn1zLVW9JaYmU63Fsjj4IxrKSsHWaYjvE5re3dQU"
API_BASE_URL = "https://llmwhisperer-api.us-central.unstract.com/api/v2"

def process_pdf(file_path, wait_for_completion=False):
    """
    Process a PDF file using LLMWhisperer and return the extracted text.
    
    Args:
        file_path (str): Path to the PDF file
        wait_for_completion (bool): Whether to wait for processing to complete
        
    Returns:
        dict: The response from LLMWhisperer
    """
    print(f"Processing file: {file_path}")
    
    # Create an instance of the LLMWhisperer client
    client = LLMWhispererClientV2(
        base_url=API_BASE_URL,
        api_key=API_KEY
    )
    
    try:
        if wait_for_completion:
            # Synchronous mode - wait for processing to complete
            print("Using synchronous mode - waiting for processing to complete...")
            result = client.whisper(
                file_path=file_path,
                wait_for_completion=True,
                wait_timeout=200  # Timeout in seconds
            )
            print("Processing complete!")
            return result
        else:
            # Asynchronous mode - submit for processing and poll for status
            print("Using asynchronous mode - submitting for processing...")
            result = client.whisper(file_path=file_path)
            
            if result["status_code"] == 202:
                print(f"Document submitted successfully. Whisper hash: {result['whisper_hash']}")
                
                # Poll for status until processing is complete
                while True:
                    print("Checking processing status...")
                    status = client.whisper_status(whisper_hash=result["whisper_hash"])
                    
                    if status["status"] == "processing":
                        print("Status: Still processing...")
                    elif status["status"] == "delivered":
                        print("Status: Already delivered!")
                        break
                    elif status["status"] == "unknown":
                        print("Status: Unknown")
                        break
                    elif status["status"] == "processed":
                        print("Status: Processing complete!")
                        # Retrieve the result
                        final_result = client.whisper_retrieve(whisper_hash=result["whisper_hash"])
                        return final_result
                    
                    # Wait before polling again
                    time.sleep(5)
            else:
                print(f"Error submitting document. Status code: {result['status_code']}")
                sys.exit(1)
                
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

def save_results(response, output_file, text_file):
    """
    Save the processing results to JSON and text files.
    
    Args:
        response (dict): The response from LLMWhisperer
        output_file (str): Path to save the JSON output
        text_file (str): Path to save the raw text output
    """
    # Save full JSON response
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(response, f, indent=2)
    
    print(f"Results saved to: {output_file}")
    
    # Extract and save just the text content
    extracted_text = None
    
    # Check for the text in the expected locations based on API response format
    if 'extraction' in response and 'result_text' in response['extraction']:
        extracted_text = response['extraction']['result_text']
    elif 'extracted_text' in response:
        extracted_text = response['extracted_text']
    
    if extracted_text:
        # Save extracted text to a separate text file
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
            
        print(f"Raw text saved to: {text_file}")
        
        # Print text preview
        print("\nExtracted Text Preview:")
        # Print first 500 characters as a preview
        preview = extracted_text[:500]
        print(f"{preview}...")
    else:
        print("No extracted text found in the response")

def main():
    """Main function to process the PDF file"""
    # Default file name - the one we have in the repository
    file_path = "AA1060_Aluminum Alloy Sheet.pdf"
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    
    # Process the file - using synchronous mode for simplicity
    result = process_pdf(file_path, wait_for_completion=True)
    
    # Save the results
    output_file = "processed_certificate.json"
    text_file = "processed_certificate.txt"
    save_results(result, output_file, text_file)
    
    print("\nProcessing complete! You can now use the extracted text for further LLM inputs.")
    print(f"The full extracted text is available in the '{text_file}' file.")

if __name__ == "__main__":
    main() 