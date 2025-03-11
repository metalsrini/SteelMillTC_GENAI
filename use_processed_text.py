#!/usr/bin/env python3
"""
Example script to demonstrate how to use the processed certificate text with an LLM.
This is a simplified example and would need to be adapted to work with your specific LLM provider.
"""

import json
import os
import sys

# Function to load the processed text
def load_processed_text(file_path):
    """Load the processed text from a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract the text from the appropriate field based on the response format
        if 'extraction' in data and 'result_text' in data['extraction']:
            return data['extraction']['result_text']
        elif 'extracted_text' in data:
            return data['extracted_text']
        else:
            print("Error: No extracted text found in the file.")
            return None
    except Exception as e:
        print(f"Error loading processed text: {e}")
        return None

# Example function to send text to an LLM (this is a placeholder)
def query_llm(text, prompt=""):
    """
    Example function to query an LLM with the processed text.
    This is just a placeholder - you would replace this with your actual LLM API call.
    """
    print("Sending processed text to LLM...")
    print(f"Text length: {len(text)} characters")
    
    # Here you would add your LLM API integration code
    # For example, for OpenAI:
    """
    import openai
    
    openai.api_key = "your-api-key"
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are analyzing a steel mill test certificate."},
            {"role": "user", "content": prompt + "\n\n" + text}
        ]
    )
    
    return response.choices[0].message.content
    """
    
    # For demonstration purposes, we'll just return a sample response
    print("\nSample prompt that would be sent to the LLM:")
    print("-------------------")
    print(prompt)
    print("\nWith the extracted text from the PDF")
    print("-------------------")
    
    return """
Based on the steel mill test certificate, here are the answers to your questions:

1. Material Grade: AA1060 (Aluminum Alloy)

2. Key Chemical Composition Elements:
   - Aluminum (Al): 99.60% (minimum)
   - Silicon (Si): 0.25% (maximum)
   - Iron (Fe): 0.35% (maximum)
   - Copper (Cu): 0.05% (maximum)
   - Manganese (Mn): 0.03% (maximum)
   - Magnesium (Mg): 0.03% (maximum)
   - Zinc (Zn): 0.05% (maximum)
   - Titanium (Ti): 0.03% (maximum)
   - Other elements: each 0.03% maximum, total 0.03% maximum

3. Mechanical Properties:
   - Temper: H24 FINISH
   - The certificate indicates this is in accordance with ASTM standards

4. Compliance with Industry Standards:
   - Yes, the material complies with ASTM standards (specifically mentioned in the certificate)
   - The certificate is issued by YIEH CORPORATION LIMITED, which appears to be the manufacturer

This is a mill test certificate for AA1060 aluminum alloy sheet, which is a high-purity aluminum grade (minimum 99.60% aluminum content) with H24 temper, indicating it has been strain-hardened and partially annealed.
"""

def main():
    # Check if the processed file exists
    processed_file = "processed_certificate.json"
    if not os.path.exists(processed_file):
        print(f"Error: Processed file '{processed_file}' not found.")
        print("Please run 'process_certificate.py' first to generate the processed file.")
        sys.exit(1)
    
    # Load the processed text
    text = load_processed_text(processed_file)
    if not text:
        sys.exit(1)
    
    # Example: Query the LLM with some specific questions about the certificate
    prompt = """
    Analyze this steel mill test certificate and answer the following questions:
    1. What is the material grade?
    2. What are the key chemical composition elements?
    3. What are the mechanical properties?
    4. Is this material compliant with industry standards?
    """
    
    # Get response from LLM
    response = query_llm(text, prompt)
    
    # Print the response
    print("\n=== LLM Analysis ===")
    print(response)
    print("=====================")

if __name__ == "__main__":
    main() 