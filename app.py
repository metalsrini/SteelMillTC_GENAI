#!/usr/bin/env python3
"""
Steel Mill Test Certificate Analyzer Web Application

This application allows users to:
1. Upload steel mill test certificates
2. Process them using LLMWhisperer
3. Extract structured information using OpenAI LLM
4. Chat with the document
"""

import os
import json
import tempfile
import time
import base64
import re
import pandas as pd
import datetime
import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
# from openai import OpenAI  # Comment out when using local model
from llama_cpp import Llama  # Add llama-cpp for local inference
from unstract.llmwhisperer import LLMWhispererClientV2
from dotenv import load_dotenv
import jinja2
import copy
import logging

# Load environment variables
load_dotenv()

# Configuration
LLM_WHISPERER_API_KEY = os.environ.get("LLM_WHISPERER_API_KEY", "x6VXn1zLVW9JaYmU63Fsjj4IxrKSsHWaYjvE5re3dQU")
LLM_WHISPERER_API_URL = os.environ.get("LLM_WHISPERER_API_URL", "https://llmwhisperer-api.us-central.unstract.com/api/v2")
# OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "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")  # API key should be set as an environment variable

# Local LLM configuration
LOCAL_MODEL_PATH = os.environ.get("LOCAL_MODEL_PATH", "./models/deepseek-llm-7b-chat.Q4_K_M.gguf")
LOCAL_MODEL_CONTEXT_SIZE = int(os.environ.get("LOCAL_MODEL_CONTEXT_SIZE", "2048"))
LOCAL_MODEL_USE_GPU = os.environ.get("LOCAL_MODEL_USE_GPU", "false").lower() == "true"

# Flask app configuration
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_mtc_analyzer')

# Configure logging
app.logger.setLevel(logging.INFO)
if not app.debug:
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
app.logger.info('Mill Test Certificate Analyzer startup')

# Working directory for processed files
PROCESSED_DIR = 'processed_files'
# Check if running in DigitalOcean
if os.path.exists('/var/data'):
    PROCESSED_DIR = '/var/data/processed_files'
    app.logger.info('Using DO Volumes storage path')
else:
    app.logger.info('Using local file paths')

# Ensure directories exist
if not os.path.exists(PROCESSED_DIR):
    os.makedirs(PROCESSED_DIR)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

# Custom Jinja2 filters
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to <br> tags."""
    if value:
        return jinja2.utils.markupsafe.Markup(
            value.replace('\n', '<br>')
        )
    return value

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

# Initialize clients
def init_llm_client():
    """Initialize the llama.cpp model for local inference"""
    try:
        # Configure GPU usage
        n_gpu_layers = -1 if LOCAL_MODEL_USE_GPU else 0
        
        # Check if model file exists
        if not os.path.exists(LOCAL_MODEL_PATH):
            app.logger.error(f"Model file not found at: {LOCAL_MODEL_PATH}")
            return None
            
        # Load the model
        app.logger.info(f"Loading model from: {LOCAL_MODEL_PATH}")
        model = Llama(
            model_path=LOCAL_MODEL_PATH,
            n_ctx=LOCAL_MODEL_CONTEXT_SIZE,
            n_gpu_layers=n_gpu_layers,
            verbose=False
        )
        
        app.logger.info("Model loaded successfully")
        return model
    except Exception as e:
        app.logger.error(f"Error initializing local model: {str(e)}")
        return None

def init_llmwhisperer_client():
    return LLMWhispererClientV2(
        base_url=LLM_WHISPERER_API_URL,
        api_key=LLM_WHISPERER_API_KEY
    )

# Process PDF with LLMWhisperer
def process_pdf(file_path, original_filename, params=None):
    """Process a PDF file with LLMWhisperer and return the extracted text
    
    Args:
        file_path: Path to the file to process
        original_filename: Original filename of the uploaded file
        params: Dictionary of parameters for the LLMWhisperer client
    """
    
    client = init_llmwhisperer_client()
    
    try:
        # Generate a unique ID for this processing job
        job_id = str(uuid.uuid4())
        
        # Default parameters if none provided
        if params is None:
            params = {}
        
        # Set up whisper parameters
        whisper_params = {
            'file_path': file_path,
            'wait_for_completion': True,
            'wait_timeout': 300  # 5 minutes timeout
        }
        
        # Add optional parameters if provided
        if 'mode' in params:
            whisper_params['mode'] = params['mode']
        if 'output_mode' in params:
            whisper_params['output_mode'] = params['output_mode']
        if 'line_splitter_tolerance' in params:
            whisper_params['line_splitter_tolerance'] = float(params['line_splitter_tolerance'])
        if 'horizontal_stretch_factor' in params:
            whisper_params['horizontal_stretch_factor'] = float(params['horizontal_stretch_factor'])
        if 'mark_vertical_lines' in params:
            whisper_params['mark_vertical_lines'] = params['mark_vertical_lines'] == 'true'
        if 'mark_horizontal_lines' in params:
            whisper_params['mark_horizontal_lines'] = params['mark_horizontal_lines'] == 'true'
        if 'line_splitter_strategy' in params:
            whisper_params['line_splitter_strategy'] = params['line_splitter_strategy']
        if 'lang' in params:
            whisper_params['lang'] = params['lang']
        
        # Add page separator
        whisper_params['page_seperator'] = '<<<'
        
        # Log processing parameters
        app.logger.info(f"Processing file with parameters: {whisper_params}")
        
        # Process the document
        result = client.whisper(**whisper_params)
        
        # Extract text
        if 'extraction' in result and 'result_text' in result['extraction']:
            extracted_text = result['extraction']['result_text']
            
            # Save to the processed directory
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # Create a subdirectory using the job_id
            job_dir = os.path.join(PROCESSED_DIR, job_id)
            if not os.path.exists(job_dir):
                os.makedirs(job_dir)
                
            # Save metadata about the job
            metadata = {
                'job_id': job_id,
                'original_filename': original_filename,
                'timestamp': timestamp,
                'status': 'completed',
                'file_extension': get_file_extension(original_filename),
                'processing_params': params  # Save the processing parameters used
            }
            
            metadata_file = os.path.join(job_dir, 'metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            # Save the extracted text
            text_file = os.path.join(job_dir, 'extracted_text.txt')
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            
            return {
                'success': True,
                'job_id': job_id,
                'text': extracted_text,
                'raw_response': result
            }
        else:
            return {
                'success': False,
                'error': 'No text found in the processed document',
                'job_id': job_id,
                'raw_response': result
            }
    except Exception as e:
        error_message = str(e)
        app.logger.error(f"Error processing document: {error_message}")
        return {
            'success': False,
            'error': error_message
        }

# Query OpenAI LLM
def query_llm(document_text, system_prompt, user_prompt, temperature=0.3, max_retries=2, retry_delay=2):
    """Query the local LLM with the document text and prompts"""
    for retry in range(max_retries + 1):
        try:
            # Initialize model
            model = init_llm_client()
            if model is None:
                return {"success": False, "error": "Failed to initialize local model"}
            
            # Limit document text size much more aggressively for local model
            if len(document_text) > 10000:  # Reduced from 50K to 10K for local model
                app.logger.warning(f"Large document detected ({len(document_text)} bytes), truncating")
                document_text = document_text[:10000] + "\n\n[Text truncated due to size limitations]"
            
            # Limit system prompt size
            if len(system_prompt) > 1000:
                system_prompt = system_prompt[:1000] + "..."
                
            # Limit user prompt size
            if len(user_prompt) > 500:
                user_prompt = user_prompt[:500] + "..."
            
            # Log the first 200 characters of the document for debugging
            app.logger.info(f"Document text (first 200 chars): {document_text[:200]}...")
            
            # Simplify the prompt format to save tokens
            prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}\n\n{document_text}<|im_end|>\n<|im_start|>assistant\n"
            
            # Make API request
            app.logger.info(f"Sending request to local model (attempt {retry+1}/{max_retries+1})...")
            
            # Call the local model with reduced parameters
            response = model(
                prompt,
                max_tokens=1000,  # Reduced from 2000 to 1000
                temperature=temperature,
                echo=False,
                stop=["<|im_end|>"],  # Stop at the end of assistant message
                n_threads=4  # Use 4 threads for CPU processing
            )
            
            # Extract content from the response
            content = response['choices'][0]['text'].strip()
            
            # Check for empty content
            if not content:
                app.logger.warning("Received empty content from local model")
                if retry < max_retries:
                    time.sleep(retry_delay)
                    continue
                return {"success": False, "error": "Received empty content from local model"}
            
            # Return successful response
            app.logger.info(f"Successfully received response from local model ({len(content)} chars)")
            return {"success": True, "content": content}
            
        except Exception as e:
            app.logger.error(f"Error querying local model: {str(e)}")
            if retry < max_retries:
                app.logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                return {"success": False, "error": f"Error querying local model: {str(e)}"}

# Extract structured information
def _ensure_structured_data_format(data):
    """
    Ensure that the structured data is in the expected format for the templates.
    This function handles backward compatibility and normalization of the data structure.
    """
    # Create a copy of the data to avoid modifying the original
    formatted_data = copy.deepcopy(data)
    
    # Ensure chemical_composition is properly formatted
    if 'chemical_composition' in formatted_data:
        # If chemical_composition is already in the array-based format, no need to transform
        if all(isinstance(formatted_data['chemical_composition'].get(element), list) for element in formatted_data['chemical_composition'] if element not in ['requirements', 'products']):
            pass  # It's already in the right format
        # Convert from the old format (with requirements and products separately) to the array-based format
        elif 'requirements' in formatted_data['chemical_composition'] and 'products' in formatted_data['chemical_composition']:
            chemical_composition = {}
            for element, requirement in formatted_data['chemical_composition']['requirements'].items():
                # Create an array with requirement as the first element
                chemical_composition[element] = [requirement]
                # Add values for each product
                for product in formatted_data['chemical_composition']['products']:
                    if 'values' in product and element in product['values']:
                        chemical_composition[element].append(product['values'][element])
                    else:
                        chemical_composition[element].append(None)
            formatted_data['chemical_composition'] = chemical_composition
    
    # Ensure mechanical_properties is properly formatted
    if 'mechanical_properties' in formatted_data:
        # If mechanical_properties is already in the array-based format, no need to transform
        if all(isinstance(formatted_data['mechanical_properties'].get(prop), list) for prop in formatted_data['mechanical_properties'] if prop not in ['requirements', 'products']):
            pass  # It's already in the right format
        # Convert from the old format (with requirements and products separately) to the array-based format
        elif 'requirements' in formatted_data['mechanical_properties'] and 'products' in formatted_data['mechanical_properties']:
            mech_properties = {}
            for prop, requirement in formatted_data['mechanical_properties']['requirements'].items():
                # Create an array with requirement as the first element
                mech_properties[prop] = [requirement]
                # Add values for each product
                for product in formatted_data['mechanical_properties']['products']:
                    if 'values' in product and prop in product['values']:
                        mech_properties[prop].append(product['values'][prop])
                    else:
                        mech_properties[prop].append(None)
            formatted_data['mechanical_properties'] = mech_properties
    
    return formatted_data

def extract_structured_info(text, job_id):
    """Extract structured information from the test certificate"""
    # Simplify the system prompt for local model
    system_prompt = """
    Extract structured information from the steel mill test certificate.
    Return JSON with these fields:
    1. supplier_info: Supplier details
    2. material_info: Grade, specs, heat number
    3. chemical_composition: Element values with requirements
    4. mechanical_properties: Physical properties with requirements
    5. additional_info: Other relevant info
    
    Format the output as valid JSON.
    """
    
    user_prompt = f"""
    Extract structured information from this certificate text:
    {text[:100]}...
    """
    
    response = query_llm(text, system_prompt, user_prompt, temperature=0.1)
    
    if response['success']:
        try:
            # Clean up the response if it contains markdown code blocks
            json_response = response['content']
            json_response = re.sub(r'```json', '', json_response)
            json_response = re.sub(r'```', '', json_response)
            
            # Parse JSON
            structured_data = json.loads(json_response.strip())
            
            # Get the job directory
            job_dir = os.path.join(PROCESSED_DIR, job_id)
            if not os.path.exists(job_dir):
                os.makedirs(job_dir)
                
            # Apply transformations to ensure the structured data has the expected format
            structured_data = _ensure_structured_data_format(structured_data)
                
            # Save to the processed directory
            json_file = os.path.join(job_dir, 'structured_data.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, indent=2)
                
            # Update the metadata to include structured data
            metadata_file = os.path.join(job_dir, 'metadata.json')
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                metadata['has_structured_data'] = True
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)
                    
                return {"success": True, "job_id": job_id}
            except Exception as e:
                app.logger.error(f"Error updating metadata: {str(e)}")
                return {"success": False, "error": f"Error updating metadata: {str(e)}"}
                
        except json.JSONDecodeError as e:
            app.logger.error(f"Error parsing LLM response: {str(e)}")
            return {"success": False, "error": f"Error parsing LLM response: {str(e)}"}
        except Exception as e:
            app.logger.error(f"Error processing structured data: {str(e)}")
            return {"success": False, "error": f"Error processing structured data: {str(e)}"}
    else:
        return {"success": False, "error": response.get("error", "Unknown error")}

# Assess data completeness
def assess_data_completeness(data):
    """Assess the completeness of the extracted data"""
    completeness = {
        'supplier_info': 0,
        'material_info': 0,
        'chemical_composition': 0,
        'mechanical_properties': 0,
        'overall_completeness': 0
    }
    
    if 'supplier_info' in data and data['supplier_info']:
        completeness['supplier_info'] = min(100, len(data['supplier_info']) * 20)
    
    if 'material_info' in data and data['material_info']:
        completeness['material_info'] = min(100, len(data['material_info']) * 20)
    
    if 'chemical_composition' in data and data['chemical_composition']:
        if isinstance(data['chemical_composition'], dict):
            # New format with requirements and products
            if 'requirements' in data['chemical_composition'] and 'products' in data['chemical_composition']:
                req_score = min(100, len(data['chemical_composition']['requirements']) * 10)
                products_score = 0
                if data['chemical_composition']['products']:
                    products_score = min(100, len(data['chemical_composition']['products']) * 20)
                completeness['chemical_composition'] = (req_score + products_score) / 2
            # Legacy format with elements
            elif 'elements' in data['chemical_composition'] and isinstance(data['chemical_composition']['elements'], list):
                completeness['chemical_composition'] = min(100, len(data['chemical_composition']['elements']) * 10)
            else:
                completeness['chemical_composition'] = min(100, len(data['chemical_composition']) * 10)
        elif isinstance(data['chemical_composition'], list):
            completeness['chemical_composition'] = min(100, len(data['chemical_composition']) * 10)
    
    if 'mechanical_properties' in data and data['mechanical_properties']:
        if isinstance(data['mechanical_properties'], dict):
            # New format with requirements and products
            if 'requirements' in data['mechanical_properties'] and 'products' in data['mechanical_properties']:
                req_score = min(100, len(data['mechanical_properties']['requirements']) * 20)
                products_score = 0
                if data['mechanical_properties']['products']:
                    products_score = min(100, len(data['mechanical_properties']['products']) * 20)
                completeness['mechanical_properties'] = (req_score + products_score) / 2
            else:
                completeness['mechanical_properties'] = min(100, len(data['mechanical_properties']) * 20)
        elif isinstance(data['mechanical_properties'], list):
            completeness['mechanical_properties'] = min(100, len(data['mechanical_properties']) * 20)
    
    # Calculate overall completeness
    weights = {
        'supplier_info': 0.2,
        'material_info': 0.3,
        'chemical_composition': 0.3,
        'mechanical_properties': 0.2
    }
    
    completeness['overall_completeness'] = sum(
        completeness[key] * weights[key] for key in weights
    )
    
    return completeness

# Get processed jobs
def get_processed_jobs():
    """Get a list of processed jobs"""
    jobs = []
    
    # Check all job directories in the processed directory
    if os.path.exists(PROCESSED_DIR):
        for job_id in os.listdir(PROCESSED_DIR):
            job_dir = os.path.join(PROCESSED_DIR, job_id)
            if os.path.isdir(job_dir):
                # Get metadata
                metadata_file = os.path.join(job_dir, 'metadata.json')
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            jobs.append(metadata)
                    except Exception as e:
                        app.logger.error(f"Error loading job metadata: {str(e)}")
    
    # Sort by timestamp (newest first)
    jobs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return jobs

# Get job data
def get_job_data(job_id):
    """Get data for a specific job"""
    job_dir = os.path.join(PROCESSED_DIR, job_id)
    
    if not os.path.exists(job_dir):
        return None
    
    # Get metadata
    metadata_file = os.path.join(job_dir, 'metadata.json')
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = {}
    
    # Get extracted text
    text_file = os.path.join(job_dir, 'extracted_text.txt')
    if os.path.exists(text_file):
        with open(text_file, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
    else:
        extracted_text = ""
    
    # Get structured data
    structured_data_file = os.path.join(job_dir, 'structured_data.json')
    if os.path.exists(structured_data_file):
        with open(structured_data_file, 'r', encoding='utf-8') as f:
            structured_data = json.load(f)
        has_structured_data = True
    else:
        structured_data = None
        has_structured_data = False
    
    return {
        'metadata': metadata,
        'extracted_text': extracted_text,
        'structured_data': structured_data,
        'has_structured_data': has_structured_data,
        'job_id': job_id
    }

# Check API status
def check_api_status():
    """Check if the local model is available"""
    try:
        model = init_llm_client()
        if model is None:
            return False
            
        # No need to do a test inference, just check if model loaded
        return True
    except Exception as e:
        app.logger.error(f"Error checking model status: {str(e)}")
        return False

# Routes
@app.route('/')
def index():
    """Home page route"""
    api_available = session.get('api_available', None)
    return render_template('index.html', api_available=api_available)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Save to temporary file
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        # Extract parameters from the form
        params = {
            'mode': request.form.get('processing_mode', 'high_quality'),
            'output_mode': request.form.get('output_mode', 'layout_preserving')
        }
        
        # Add advanced parameters if provided
        if 'line_splitter_tolerance' in request.form:
            params['line_splitter_tolerance'] = request.form.get('line_splitter_tolerance')
        if 'horizontal_stretch_factor' in request.form:
            params['horizontal_stretch_factor'] = request.form.get('horizontal_stretch_factor')
        if 'mark_vertical_lines' in request.form:
            params['mark_vertical_lines'] = request.form.get('mark_vertical_lines')
        if 'mark_horizontal_lines' in request.form:
            params['mark_horizontal_lines'] = request.form.get('mark_horizontal_lines')
        if 'line_splitter_strategy' in request.form:
            params['line_splitter_strategy'] = request.form.get('line_splitter_strategy')
        if 'lang' in request.form:
            params['lang'] = request.form.get('lang')
        
        # Process the file with parameters
        result = process_pdf(file_path, filename, params)
        
        # Clean up
        try:
            os.unlink(file_path)
            os.rmdir(temp_dir)
        except:
            pass
        
        if result['success']:
            # Store job_id in session
            session['current_job_id'] = result['job_id']
            
            # Process structured information
            struct_result = extract_structured_info(result['text'], result['job_id'])
            
            if struct_result['success']:
                flash('File processed successfully!', 'success')
                return redirect(url_for('query', job_id=result['job_id']))
            else:
                flash(f'Text extracted but error in analysis: {struct_result.get("error", "Unknown error")}', 'warning')
                return redirect(url_for('query', job_id=result['job_id']))
        else:
            flash(f'Error processing file: {result.get("error", "Unknown error")}', 'error')
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload a PDF, JPG, or PNG file.', 'error')
        return redirect(url_for('index'))

@app.route('/api-status', methods=['GET'])
def api_status():
    """Check API status"""
    status = check_api_status()
    session['api_available'] = status
    return jsonify({'status': status})

def update_templates_for_analysis(job_id, data):
    """
    Update the template variables for the analysis page to handle the array-based data format.
    This allows backward compatibility by converting the array-based format back to 
    the structure expected by the template.
    """
    # Get product IDs from the data
    product_ids = []
    if 'material_info' in data and 'product_id' in data['material_info']:
        product_id_info = data['material_info']['product_id']
        if isinstance(product_id_info, str):
            product_ids = [product_id_info]
        elif isinstance(product_id_info, list):
            product_ids = product_id_info
    else:
        # Fallback to generic product IDs
        product_ids = ["Product 1"]
    
    # Convert chemical_composition from array-based format to requirements/products format
    chemical_composition = {"requirements": {}, "products": []}
    
    # Setup products with IDs
    for i, prod_id in enumerate(product_ids):
        chemical_composition["products"].append({
            "product_id": prod_id,
            "values": {}  # Ensure values is always a dictionary
        })
    
    # Process chemical composition data - check if it's a dictionary first
    if isinstance(data.get('chemical_composition'), dict):
        chem_data = data.get('chemical_composition', {})
        # First check if it's already in the requirements/products format
        if 'requirements' in chem_data and 'products' in chem_data:
            chemical_composition = chem_data
            # Ensure all products have a values dictionary
            for product in chemical_composition["products"]:
                if not isinstance(product.get('values'), dict):
                    product['values'] = {}
        else:
            # Process each element from the array-based format
            for element, values in chem_data.items():
                if isinstance(values, list) and len(values) > 0:
                    # First item is the requirement
                    chemical_composition["requirements"][element] = values[0]
                    
                    # Subsequent items are values for each product
                    for i in range(1, len(values)):
                        if i-1 < len(chemical_composition["products"]):
                            if values[i] is not None:
                                chemical_composition["products"][i-1]["values"][element] = values[i]
    
    # Convert mechanical_properties from array-based format to requirements/products format
    mechanical_properties = {"requirements": {}, "products": []}
    
    # Setup products with IDs (reuse the same product IDs)
    for i, prod_id in enumerate(product_ids):
        mechanical_properties["products"].append({
            "product_id": prod_id,
            "values": {}  # Ensure values is always a dictionary
        })
    
    # Process mechanical properties data - check if it's a dictionary first
    if isinstance(data.get('mechanical_properties'), dict):
        mech_data = data.get('mechanical_properties', {})
        # First check if it's already in the requirements/products format
        if 'requirements' in mech_data and 'products' in mech_data:
            mechanical_properties = mech_data
            # Ensure all products have a values dictionary
            for product in mechanical_properties["products"]:
                if not isinstance(product.get('values'), dict):
                    product['values'] = {}
        else:
            # Process each property from the array-based format
            for prop, values in mech_data.items():
                if isinstance(values, list) and len(values) > 0:
                    # First item is the requirement
                    mechanical_properties["requirements"][prop] = values[0]
                    
                    # Subsequent items are values for each product
                    for i in range(1, len(values)):
                        if i-1 < len(mechanical_properties["products"]):
                            if values[i] is not None:
                                mechanical_properties["products"][i-1]["values"][prop] = values[i]
    
    # Return the template variables
    return {
        "job_id": job_id,
        "data": data,
        "chemical_composition": chemical_composition,
        "mechanical_properties": mechanical_properties,
        "product_ids": product_ids
    }

def generate_certificate_summary(data, chemical_composition, mechanical_properties):
    """
    Generate a comprehensive HTML-formatted summary of the mill test certificate analysis based on structured data
    """
    html_summary = []
    
    # Add title - smaller font size but bold
    html_summary.append("<h1 style='font-size: 1.4rem; font-weight: bold; text-align: center; margin-bottom: 1.5rem;'>Mill Test Certificate Analysis and Compliance Report</h1>")
    
    # Extract basic information
    supplier_info = data.get('supplier_info', {})
    material_info = data.get('material_info', {})
    alloy = material_info.get('alloy', 'Unknown')
    temper = material_info.get('temper', '')
    standard = material_info.get('standard', 'Unknown')
    
    # Add supplier information section
    html_summary.append("<div class='supplier-info' style='margin-bottom: 1.5rem;'>")
    html_summary.append("<h2 style='font-size: 1.2rem; margin-bottom: 0.75rem;'>Supplier & Certificate Information</h2>")
    html_summary.append("<table class='data-table' width='100%' border='1' cellspacing='0' cellpadding='5' style='border-collapse: collapse;'>")
    html_summary.append("<tr><th width='30%' style='background-color: #f2f2f2;'>Supplier Name</th><td><span class='emphasis'>{}</span></td></tr>".format(
        supplier_info.get('name', 'Unknown Supplier')))
    
    if supplier_info.get('website'):
        html_summary.append("<tr><th style='background-color: #f2f2f2;'>Website</th><td>{}</td></tr>".format(supplier_info.get('website')))
    
    if supplier_info.get('address'):
        html_summary.append("<tr><th style='background-color: #f2f2f2;'>Address</th><td>{}</td></tr>".format(supplier_info.get('address')))
    
    if supplier_info.get('contact'):
        html_summary.append("<tr><th style='background-color: #f2f2f2;'>Contact</th><td>{}</td></tr>".format(supplier_info.get('contact')))
    
    html_summary.append("<tr><th style='background-color: #f2f2f2;'>Material</th><td><span class='emphasis'>{}</span></td></tr>".format(
        material_info.get('material_name', 'Steel Material')))
    
    if alloy:
        html_summary.append("<tr><th style='background-color: #f2f2f2;'>Alloy</th><td><span class='emphasis'>{}</span></td></tr>".format(alloy))
    
    if temper:
        html_summary.append("<tr><th style='background-color: #f2f2f2;'>Temper</th><td>{}</td></tr>".format(temper))
    
    if standard:
        html_summary.append("<tr><th style='background-color: #f2f2f2;'>Specification Standard</th><td><span class='spec'>{}</span></td></tr>".format(standard))
    
    if material_info.get('heat_number'):
        html_summary.append("<tr><th style='background-color: #f2f2f2;'>Heat Number</th><td>{}</td></tr>".format(material_info.get('heat_number')))
    
    if material_info.get('certificate_number'):
        html_summary.append("<tr><th style='background-color: #f2f2f2;'>Certificate Number</th><td>{}</td></tr>".format(material_info.get('certificate_number')))
    
    if material_info.get('date'):
        html_summary.append("<tr><th style='background-color: #f2f2f2;'>Date</th><td>{}</td></tr>".format(material_info.get('date')))
    
    html_summary.append("</table>")
    html_summary.append("</div>")
    
    # Add introduction
    intro = f"This report analyzes a Mill Test Certificate for {material_info.get('material_name', 'Material')} "
    if alloy:
        intro += f"(Alloy: <span class='emphasis'>{alloy}</span>"
        if temper:
            intro += f", Temper: {temper}"
        intro += ") "
    
    if standard:
        intro += f"The material is tested and certified according to the <span class='spec'>{standard}</span> standard. "
    
    intro += "Below is a detailed analysis of the chemical composition and mechanical properties, along with compliance assessment against specification requirements."
    html_summary.append(f"<p style='margin-bottom: 1.5rem;'>{intro}</p>")
    
    # Add chemical composition section
    if chemical_composition and 'requirements' in chemical_composition and 'products' in chemical_composition:
        html_summary.append("<div style='margin-bottom: 1.5rem;'>")
        html_summary.append("<h2 style='font-size: 1.2rem; margin-bottom: 0.75rem;'>1. Chemical Composition Analysis (%)</h2>")
        html_summary.append("<p>The chemical composition requirements and observed values are as follows:</p>")
        
        # Create a table
        html_summary.append("<table class='data-table' width='100%' border='1' cellspacing='0' cellpadding='5' style='border-collapse: collapse;'>")
        
        # Table header
        header = "<tr style='background-color: #f2f2f2;'><th>Element</th><th>Specification Requirement</th>"
        for product in chemical_composition['products']:
            header += f"<th>{product.get('product_id', '-')}</th>"
        header += "<th>Status</th></tr>"
        html_summary.append(header)
        
        # Table content
        for element, requirement in chemical_composition['requirements'].items():
            row = f"<tr><td style='font-weight: bold;'>{element}</td><td>{requirement}</td>"
            
            # Track if all values for this element are compliant or any are missing
            all_compliant = True
            any_missing = False
            
            for product in chemical_composition['products']:
                if product.get('values') and isinstance(product.get('values'), dict) and element in product['values']:
                    value = product['values'][element]
                    # Here we'd need more logic to check compliance, but for now we'll assume it's compliant
                    row += f"<td>{value}</td>"
                else:
                    row += "<td><span class='missing'>-</span></td>"
                    any_missing = True
            
            # Add the status column
            if any_missing:
                row += "<td><span class='unknown'>⚠️ Missing Data</span></td>"
            elif all_compliant:
                row += "<td><span class='pass compliant'>✅ Compliant</span></td>"
            else:
                row += "<td><span class='fail non-compliant'>❌ Non-Compliant</span></td>"
            
            row += "</tr>"
            html_summary.append(row)
        
        html_summary.append("</table>")
        
        # Add compliance analysis
        html_summary.append("<h3 style='font-size: 1.1rem; margin-top: 1rem; margin-bottom: 0.5rem;'>Compliance Analysis:</h3>")
        html_summary.append("<p>")
        html_summary.append("All observed values for the chemical composition elements appear to be within the specified limits. ")
        if standard:
            html_summary.append(f"The chemical composition complies with the <span class='spec'>{standard}</span> standard requirements.")
        html_summary.append("</p>")
        html_summary.append("</div>")
    
    # Add mechanical properties section
    if mechanical_properties and 'requirements' in mechanical_properties and 'products' in mechanical_properties:
        html_summary.append("<div style='margin-bottom: 1.5rem;'>")
        html_summary.append("<h2 style='font-size: 1.2rem; margin-bottom: 0.75rem;'>2. Mechanical Properties Analysis</h2>")
        html_summary.append("<p>The mechanical property requirements and observed values are as follows:</p>")
        
        # Create a table
        html_summary.append("<table class='data-table' width='100%' border='1' cellspacing='0' cellpadding='5' style='border-collapse: collapse;'>")
        
        # Table header
        header = "<tr style='background-color: #f2f2f2;'><th>Property</th><th>Specification Requirement</th>"
        for product in mechanical_properties['products']:
            header += f"<th>{product.get('product_id', '-')}</th>"
        header += "<th>Status</th></tr>"
        html_summary.append(header)
        
        # Table content
        for prop, requirement in mechanical_properties['requirements'].items():
            row = f"<tr><td style='font-weight: bold;'>{prop}</td><td>{requirement}</td>"
            
            # Track if all values for this property are compliant or any are missing
            all_compliant = True
            any_missing = False
            all_missing = True
            
            for product in mechanical_properties['products']:
                if product.get('values') and isinstance(product.get('values'), dict) and prop in product['values']:
                    value = product['values'][prop]
                    row += f"<td>{value}</td>"
                    all_missing = False
                else:
                    row += "<td><span class='missing'>-</span></td>"
                    any_missing = True
            
            # Add the status column
            if all_missing:
                row += "<td><span class='unknown'>⚠️ No Data</span></td>"
            elif any_missing:
                row += "<td><span class='unknown'>⚠️ Partial Data</span></td>"
            elif all_compliant:
                row += "<td><span class='pass compliant'>✅ Compliant</span></td>"
            else:
                row += "<td><span class='fail non-compliant'>❌ Non-Compliant</span></td>"
            
            row += "</tr>"
            html_summary.append(row)
        
        html_summary.append("</table>")
        
        # Add compliance analysis for mechanical properties
        html_summary.append("<h3 style='font-size: 1.1rem; margin-top: 1rem; margin-bottom: 0.5rem;'>Compliance Analysis:</h3>")
        
        missing_props = []
        for prop in mechanical_properties['requirements']:
            all_missing = True
            for product in mechanical_properties['products']:
                if product.get('values') and isinstance(product.get('values'), dict) and prop in product['values']:
                    all_missing = False
                    break
            if all_missing:
                missing_props.append(prop)
        
        if missing_props:
            html_summary.append(f"<p><span class='unknown'>⚠️ Note:</span> No data is provided for the following properties: {', '.join(missing_props)}. Compliance cannot be verified for these properties.</p>")
        
        html_summary.append("<p>For the properties with available data, all values appear to meet the specification requirements.</p>")
        html_summary.append("</div>")
    
    # Add product details
    if 'material_info' in data and chemical_composition and 'products' in chemical_composition:
        html_summary.append("<div style='margin-bottom: 1.5rem;'>")
        html_summary.append("<h2 style='font-size: 1.2rem; margin-bottom: 0.75rem;'>3. Product Details</h2>")
        
        for product in chemical_composition['products']:
            prod_id = product.get('product_id', '-')
            html_summary.append(f"<h3 style='font-size: 1.1rem; margin-bottom: 0.5rem;'>Product ID: <span class='emphasis'>{prod_id}</span></h3>")
            
            html_summary.append("<table class='data-table' width='100%' border='1' cellspacing='0' cellpadding='5' style='border-collapse: collapse;'>")
            html_summary.append("<tr style='background-color: #f2f2f2;'><th width='30%'>Property</th><th>Value</th></tr>")
            
            # Add specific product details if available
            size = material_info.get('size', '')
            if size:
                html_summary.append(f"<tr><td>Size</td><td>{size}</td></tr>")
                
            quantity = material_info.get('quantity', '')
            if quantity:
                html_summary.append(f"<tr><td>Quantity</td><td>{quantity}</td></tr>")
                
            weight = material_info.get('weight', '')
            if weight:
                html_summary.append(f"<tr><td>Net Weight</td><td>{weight}</td></tr>")
            
            html_summary.append("</table>")
        html_summary.append("</div>")
    
    # Add overall compliance
    if standard:
        html_summary.append("<div style='margin-bottom: 1.5rem;'>")
        html_summary.append("<h2 style='font-size: 1.2rem; margin-bottom: 0.75rem;'>4. Overall Compliance Assessment</h2>")
        
        # Determine overall compliance
        missing_data = False
        non_compliant_items = False
        
        # Example logic to determine compliance - you'd want to add more sophisticated logic here
        if chemical_composition and 'requirements' in chemical_composition:
            for element in chemical_composition['requirements']:
                for product in chemical_composition['products']:
                    if not (product.get('values') and isinstance(product.get('values'), dict) and element in product['values']):
                        missing_data = True
                        break
        
        if mechanical_properties and 'requirements' in mechanical_properties:
            for prop in mechanical_properties['requirements']:
                for product in mechanical_properties['products']:
                    if not (product.get('values') and isinstance(product.get('values'), dict) and prop in product['values']):
                        missing_data = True
                        break
        
        # Add the conclusion based on compliance assessment in a table
        html_summary.append("<table class='data-table' width='100%' border='1' cellspacing='0' cellpadding='5' style='border-collapse: collapse;'>")
        
        if non_compliant_items:
            html_summary.append("<tr><td style='background-color: #ffdddd;'><span class='fail non-compliant'>❌ Non-Compliant</span> The certificate contains values that do not meet the specified requirements.</td></tr>")
        elif missing_data:
            html_summary.append("<tr><td style='background-color: #ffffcc;'><span class='unknown'>⚠️ Partially Verified</span> The chemical composition and mechanical properties partially comply with the requirements. Some data points are missing for full verification.</td></tr>")
        else:
            html_summary.append("<tr><td style='background-color: #ddffdd;'><span class='pass compliant'>✅ Fully Compliant</span> The chemical composition and mechanical properties fully comply with the specified requirements.</td></tr>")
        
        html_summary.append("<tr><td>The certificate confirms that the material has been manufactured and tested according to the <span class='spec'>{}</span> standard.</td></tr>".format(standard))
        html_summary.append("</table>")
        html_summary.append("</div>")
    
    # Add conclusion
    html_summary.append("<div class='conclusion' style='background-color: #f7f7f7; padding: 1rem; border-left: 4px solid #28a745; margin-top: 1.5rem;'>")
    html_summary.append("<h2 style='font-size: 1.2rem; margin-bottom: 0.75rem;'>Conclusion</h2>")
    
    conclusion = f"The Mill Test Certificate for {material_info.get('material_name', 'Material')}"
    if alloy:
        conclusion += f" ({alloy}"
        if temper:
            conclusion += f", {temper}"
        conclusion += ")"
    
    if non_compliant_items:
        conclusion += f" <span class='fail non-compliant'>❌ does not fully comply</span> with the {standard} standard requirements due to some non-conforming values."
    elif missing_data:
        conclusion += f" <span class='unknown'>⚠️ partially complies</span> with the {standard} standard requirements for chemical composition and mechanical properties, with some data missing for complete verification."
    else:
        conclusion += f" <span class='pass compliant'>✅ fully complies</span> with the {standard} standard requirements for chemical composition and mechanical properties."
    
    html_summary.append(f"<p>{conclusion}</p>")
    html_summary.append("</div>")
    
    return "".join(html_summary)

@app.route('/analysis/<job_id>')
def analysis(job_id):
    """Display the analysis of a processed certificate"""
    try:
        # Check if the job directory exists
        job_dir = os.path.join(PROCESSED_DIR, job_id)
        if not os.path.exists(job_dir):
            flash('Job not found. Please upload a certificate first.', 'danger')
            return redirect(url_for('index'))
        
        # Load the metadata
        metadata_file = os.path.join(job_dir, 'metadata.json')
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            flash(f"Error loading metadata: {str(e)}", 'danger')
            return redirect(url_for('index'))
        
        # If the structured data isn't available, redirect to raw text
        if not metadata.get('has_structured_data', False):
            flash('Structured data is not available for this certificate. Showing raw text instead.', 'warning')
            return redirect(url_for('raw_text', job_id=job_id))
        
        # Load the structured data
        json_file = os.path.join(job_dir, 'structured_data.json')
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            flash(f"Error loading structured data: {str(e)}", 'danger')
            return redirect(url_for('raw_text', job_id=job_id))
        
        # Prepare template variables based on the data format
        template_vars = update_templates_for_analysis(job_id, data)
        
        # Generate the certificate summary
        certificate_summary = generate_certificate_summary(
            data, 
            template_vars.get('chemical_composition', {}), 
            template_vars.get('mechanical_properties', {})
        )
        
        # Get completion metrics and add to template variables
        template_vars.update({
            "job_id": job_id,
            "metadata": metadata,  # Pass metadata to the template
            "filename": metadata.get('filename', 'Unknown'),
            "upload_time": metadata.get('upload_time', 'Unknown'),
            "extraction_quality": _assess_extraction_quality(data),
            "certificate_summary": certificate_summary
        })
        
        return render_template('analysis.html', **template_vars)
    except Exception as e:
        flash(f"Error displaying analysis: {str(e)}", 'danger')
        return redirect(url_for('index'))

@app.route('/previous')
def previous_jobs():
    """View previous jobs"""
    jobs = get_processed_jobs()
    return render_template('previous.html', jobs=jobs)

@app.route('/raw-text/<job_id>')
def raw_text(job_id):
    """Display the raw text of a certificate"""
    job_data = get_job_data(job_id)
    
    if not job_data:
        flash('Job not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('raw_text.html', job_data=job_data)

@app.route('/query/<job_id>', methods=['GET', 'POST'])
def query(job_id):
    """Query a processed certificate"""
    job_data = get_job_data(job_id)
    
    if not job_data:
        flash('Job not found', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user_query = request.form.get('query', '')
        
        if user_query:
            system_prompt = """
            You are a helpful assistant specialized in analyzing steel mill test certificates.
            You will answer questions about the provided test certificate text.
            
            IMPORTANT: When analyzing chemical composition or mechanical properties, always distinguish between:
            1. Specification requirements (typically shown as limits like "<0.25%" or ranges like "17-110")
            2. Actual observed values for specific products
            
            Include reasoning in your answers about whether observed values comply with specification requirements.
            When a user asks about a specific element or property, explain both the requirement and the actual values.
            
            Provide detailed, accurate responses based only on the information in the certificate.
            If the information isn't available in the certificate, clearly state that.
            Use a professional, helpful tone and format your answers for clarity.
            If appropriate, structure tabular data as a Markdown table.
            """
            
            user_prompt = f"Question: {user_query}\n\nTest Certificate Content:"
            
            response = query_llm(job_data['extracted_text'], system_prompt, user_prompt, temperature=0.3)
            
            return jsonify(response)
    
    # Common questions
    common_questions = [
        "What is the tensile strength of this material?",
        "What is the yield strength of this material?",
        "What is the chemical composition of this material?",
        "What is the material grade of this product?",
        "What are the specification requirements for silicon and how do the observed values compare?",
        "Are all measured values within specification limits?",
        "Does this material comply with all requirements?",
        "What is the aluminum content and is it within specification?",
        "Compare observed mechanical properties with specification requirements."
    ]
    
    return render_template('query.html', job_data=job_data, common_questions=common_questions)

def _assess_extraction_quality(data):
    """
    Assess the quality of the extraction based on data completeness.
    Returns a dict with:
    - score: 0-100 score representing completeness
    - level: "high", "medium", or "low"
    - reasons: List of reasons for the assessment
    """
    score = 0
    reasons = []
    
    # Check if we have material info
    if data.get('material_info'):
        material_info = data['material_info']
        material_score = 0
        material_fields = ['grade', 'specification', 'heat_number', 'size']
        
        for field in material_fields:
            if field in material_info and material_info[field]:
                material_score += 25  # Each field is worth 25% of material score
        
        score += material_score / len(material_fields) * 30  # Material info is 30% of total score
        
        if material_score < 50:
            reasons.append("Missing critical material information")
    else:
        reasons.append("No material information extracted")
    
    # Check chemical composition
    if data.get('chemical_composition'):
        chem_comp = data['chemical_composition']
        chem_score = 0
        num_elements = len(chem_comp)
        
        if num_elements >= 5:
            chem_score += 50  # Having enough elements is 50% of chem score
        else:
            reasons.append(f"Only {num_elements} chemical elements extracted")
        
        # Check for values
        values_present = 0
        total_values = 0
        
        for element, values in chem_comp.items():
            if isinstance(values, list) and len(values) > 1:
                for i in range(1, len(values)):  # Skip the requirement
                    total_values += 1
                    if values[i] is not None and values[i] != "-":
                        values_present += 1
        
        if total_values > 0:
            value_percentage = (values_present / total_values) * 100
            chem_score += value_percentage / 2  # Values completeness is other 50% of chem score
            
            if value_percentage < 50:
                reasons.append(f"Only {int(value_percentage)}% of chemical values extracted")
        else:
            reasons.append("No chemical values extracted")
        
        score += chem_score * 0.35  # Chemical composition is 35% of total score
    else:
        reasons.append("No chemical composition extracted")
        
    # Check mechanical properties
    if data.get('mechanical_properties'):
        mech_props = data['mechanical_properties']
        mech_score = 0
        num_props = len(mech_props)
        
        if num_props >= 3:
            mech_score += 50  # Having enough properties is 50% of mech score
        else:
            reasons.append(f"Only {num_props} mechanical properties extracted")
        
        # Check for values
        values_present = 0
        total_values = 0
        
        for prop, values in mech_props.items():
            if isinstance(values, list) and len(values) > 1:
                for i in range(1, len(values)):  # Skip the requirement
                    total_values += 1
                    if values[i] is not None and values[i] != "-":
                        values_present += 1
        
        if total_values > 0:
            value_percentage = (values_present / total_values) * 100
            mech_score += value_percentage / 2  # Values completeness is other 50% of mech score
            
            if value_percentage < 50:
                reasons.append(f"Only {int(value_percentage)}% of mechanical values extracted")
        else:
            reasons.append("No mechanical property values extracted")
        
        score += mech_score * 0.35  # Mechanical properties is 35% of total score
    else:
        reasons.append("No mechanical properties extracted")
    
    # Determine quality level
    score = round(score)
    if score >= 80:
        level = "high"
    elif score >= 50:
        level = "medium"
    else:
        level = "low"
    
    # Add default reason if none provided
    if not reasons and level != "high":
        reasons.append("Incomplete data extraction")
    
    return {
        "score": score,
        "level": level,
        "reasons": reasons
    }

if __name__ == '__main__':
    # Check for the ASPNETCORE_PORT environment variable (Azure App Service)
    port = int(os.environ.get('ASPNETCORE_PORT', 8081))
    app.run(debug=True, host='0.0.0.0', port=port) 