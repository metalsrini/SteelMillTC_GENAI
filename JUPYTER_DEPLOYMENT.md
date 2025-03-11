# Deploying Mill Test Certificate Analyzer with Jupyter

This guide explains how to deploy and use the Mill Test Certificate Analyzer application using Jupyter Lab or Jupyter Notebook for a more interactive experience.

## Why Use Jupyter?

Jupyter provides several advantages for working with the MTC Analyzer:

1. **Interactive Development**: Make changes to the code and see results in real-time
2. **Documentation & Visualization**: Combine code, visualizations, and narrative text in a single document
3. **Experimentation**: Test new features or analyze results within the notebook
4. **Education**: Use as a teaching tool for others learning to use the application
5. **Remote Access**: Access the application remotely when deployed on a server with Jupyter

## Prerequisites

Before starting, make sure you have:

- Python 3.8 or newer
- The Mill Test Certificate Analyzer code
- Basic familiarity with Jupyter notebooks

## Installation

### 1. Install Jupyter

If you don't already have Jupyter Lab or Notebook installed, you can install it using pip:

```bash
# For Jupyter Lab (recommended)
pip install jupyterlab

# Or for Jupyter Notebook
pip install notebook
```

### 2. Set Up Your Project Environment

Make sure all the Mill Test Certificate Analyzer dependencies are installed:

```bash
pip install -r requirements.txt
```

## Deployment Methods

There are two main ways to deploy the MTC Analyzer with Jupyter:

1. Using the provided notebook `run_mtc_analyzer.ipynb`
2. Creating a custom deployment notebook

### Method 1: Using the Provided Notebook

The Mill Test Certificate Analyzer comes with a pre-configured Jupyter notebook for easy deployment:

1. Start Jupyter Lab or Notebook in your project directory:
   ```bash
   # For Jupyter Lab
   jupyter lab
   
   # For Jupyter Notebook
   jupyter notebook
   ```

2. Open the `run_mtc_analyzer.ipynb` notebook

3. Execute each cell in sequence by clicking the "Run" button or pressing Shift+Enter

4. When you reach the cell that starts the server, you'll see a clickable link to open the application

5. When you're done, run the final cell to shut down the server properly

### Method 2: Creating a Custom Deployment Notebook

You can create your own notebook for custom deployment:

1. Start Jupyter Lab or Notebook and create a new notebook

2. Add the following code to import necessary libraries:
   ```python
   import os
   import subprocess
   import time
   import webbrowser
   from IPython.display import display, HTML
   ```

3. Set up environment variables:
   ```python
   # Set environment variables required for the application
   os.environ["FLASK_APP"] = "app.py"
   os.environ["FLASK_ENV"] = "development"
   
   # If you need to set an OpenAI API key
   os.environ["OPENAI_API_KEY"] = "your_openai_api_key"
   ```

4. Start the Flask server:
   ```python
   # Start the Flask application in the background
   print("Starting Mill Test Certificate Analyzer...")
   flask_process = subprocess.Popen(["python", "app.py"])
   
   # Give the server a moment to start up
   time.sleep(2)
   
   # Display the application URL with a clickable link
   app_url = "http://127.0.0.1:8080"
   print(f"Mill Test Certificate Analyzer is running at: {app_url}")
   display(HTML(f'<a href="{app_url}" target="_blank">Open Mill Test Certificate Analyzer</a>'))
   ```

5. Add a cell to shut down the server when you're done:
   ```python
   # Terminate the Flask server process
   if 'flask_process' in globals():
       print("Shutting down the Mill Test Certificate Analyzer...")
       flask_process.terminate()
       flask_process.wait()
       print("Server has been shut down.")
   else:
       print("No Flask server is currently running.")
   ```

## Advanced Usage: Interacting with the Application Programmatically

Jupyter allows you to interact with the application programmatically in the same notebook. Here are some examples:

### Making HTTP Requests to the Application API

```python
import requests

# Define the base URL
base_url = "http://127.0.0.1:8080"

# Example: Get the list of previously processed certificates
response = requests.get(f"{base_url}/list_jobs")
jobs = response.json()
print(f"Found {len(jobs)} processed certificates:")
for job in jobs:
    print(f"- {job['filename']} (Job ID: {job['job_id']})")

# Example: Get raw text of a specific job
job_id = jobs[0]['job_id']  # Use the first job
response = requests.get(f"{base_url}/raw_text/{job_id}")
raw_text = response.text
print(f"First 500 characters of raw text: {raw_text[:500]}...")
```

### File Upload using Python

```python
import requests

# Define the base URL
base_url = "http://127.0.0.1:8080"

# Path to a certificate file
cert_file_path = "path/to/your/certificate.pdf"

# Upload the file
with open(cert_file_path, 'rb') as file:
    files = {'file': file}
    response = requests.post(f"{base_url}/upload_file", files=files)

if response.status_code == 200:
    result = response.json()
    print(f"File uploaded successfully! Job ID: {result['job_id']}")
    # Redirect to the analysis page
    display(HTML(f'<a href="{base_url}/analysis/{result["job_id"]}" target="_blank">View Analysis</a>'))
else:
    print(f"Error uploading file: {response.text}")
```

### Analyzing Results with Pandas

You can also analyze the structured data extracted from certificates:

```python
import pandas as pd
import json
import requests

# Define the base URL
base_url = "http://127.0.0.1:8080"

# Get job ID (assuming you have already uploaded a file)
job_id = "your_job_id"  # Replace with actual job ID

# Get the structured data
response = requests.get(f"{base_url}/job/{job_id}/structured_data.json")
data = response.json()

# Convert chemical composition to a DataFrame
if 'chemical_composition' in data:
    chem_df = pd.DataFrame(data['chemical_composition'])
    display(chem_df)
    
    # Create a bar chart of chemical composition
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 6))
    for element in chem_df.columns:
        if element not in ['test_id', 'product']:  # Skip non-chemical properties
            try:
                plt.bar(element, float(chem_df[element].iloc[0]))
            except (ValueError, TypeError):
                pass  # Skip if not a number
    plt.title('Chemical Composition')
    plt.ylabel('Percentage')
    plt.show()
```

## Customizing the Analyzer from Jupyter

You can also modify the application code directly from Jupyter:

```python
# First, stop the server if it's running
if 'flask_process' in globals():
    flask_process.terminate()
    flask_process.wait()
    print("Server has been shut down.")

# Modify a file, e.g., to customize the analysis page template
with open('templates/analysis.html', 'r') as file:
    content = file.read()

# Make modifications to the content
modified_content = content.replace('Mill Test Certificate Analysis', 'Custom MTC Analysis')

# Write the changes back
with open('templates/analysis.html', 'w') as file:
    file.write(modified_content)
    
print("Modified the analysis template")

# Restart the server with the changes
flask_process = subprocess.Popen(["python", "app.py"])
time.sleep(2)
print("Server restarted with changes")
display(HTML(f'<a href="http://127.0.0.1:8080" target="_blank">Open Modified Application</a>'))
```

## Deploying in a Remote Jupyter Environment

If you want to deploy the MTC Analyzer on a remote server with Jupyter:

1. Set up Jupyter with password protection on your server
   ```bash
   jupyter notebook password
   ```

2. Configure Jupyter to listen on a specific port and allow remote connections
   ```bash
   jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser
   ```

3. Set up port forwarding or a proper reverse proxy (like Nginx) for security

4. Connect to the remote Jupyter instance and follow the deployment steps above

5. Note that when running on a remote server, you'll need to change the application URL from localhost to your server's address

## Troubleshooting

If you encounter issues:

1. **Application doesn't start**: Check for error messages in the notebook cell output
   
2. **Cannot connect to the application**: Verify the port (8080) is not in use by another process

3. **Changes don't appear**: Make sure you've restarted the Flask server after making changes

4. **Server crash**: Check Flask error logs and ensure all dependencies are correctly installed

5. **Jupyter kernel dies**: This usually indicates a memory issue - try restarting with fewer processes running

## Conclusion

Using Jupyter with the Mill Test Certificate Analyzer provides a flexible environment for both end-users and developers. It allows for interactive use of the application while also enabling customization and analysis of results in a single interface.

For more information about Jupyter, visit:
- [Jupyter Lab Documentation](https://jupyterlab.readthedocs.io/)
- [Jupyter Notebook Documentation](https://jupyter-notebook.readthedocs.io/) 