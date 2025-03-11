# Mill Test Certificate Analyzer - Quick Start Guide

This guide will help you get the Mill Test Certificate Analyzer up and running quickly.

## Prerequisites

- Python 3.8 or newer
- pip (Python package installer)
- A valid OpenAI API key

## Installation (5 Minutes)

### Option 1: Using the run.sh Script (Recommended for Unix/Mac)

1. Open a terminal in the project directory
2. Make the script executable (if needed):
   ```bash
   chmod +x run.sh
   ```
3. Run the script:
   ```bash
   ./run.sh
   ```
4. Follow the prompts to set up your environment

The script will:
- Check your Python installation
- Create and activate a virtual environment
- Install all dependencies
- Create necessary directories
- Set up environment variables
- Start the application

### Option 2: Manual Setup

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On Unix or MacOS:
     ```bash
     source venv/bin/activate
     ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   FLASK_APP=app.py
   FLASK_ENV=development
   ```

5. Start the application:
   ```bash
   python app.py
   ```

6. Open a web browser and navigate to:
   ```
   http://127.0.0.1:8080
   ```

## Using the Application

### 1. Upload a Certificate

1. On the home page, click the "Upload Mill Test Certificate" button
2. Select a PDF file containing a Mill Test Certificate
3. Click "Upload" to process the certificate

### 2. View Analysis

After uploading, you'll be redirected to the analysis page showing:
- Certificate Summary - Overview and compliance status
- Chemical Composition - Material chemical properties
- Mechanical Properties - Strength and hardness data
- Additional Information - Other relevant data

### 3. Query the Certificate

1. On the analysis page, locate the query box
2. Type a natural language question (e.g., "Is the carbon content within specification?")
3. View the response based on the certificate data

## Example Certificates

If you don't have a Mill Test Certificate for testing, you can use the sample provided:
- `AA1060_Aluminum Alloy Sheet.pdf` - An aluminum alloy certificate

## Troubleshooting

### Common Issues

1. **Application won't start**
   - Check that port 8080 is not already in use
   - Ensure all dependencies are installed properly
   - Verify your .env file has the correct API key

2. **Certificate upload fails**
   - Ensure the file is a valid PDF
   - Check that the PDF is not password-protected
   - Verify that the file size is under 10MB

3. **Analysis shows limited information**
   - Some certificates may have formats that are harder to extract data from
   - Try a different certificate to compare results

### Getting Help

If you encounter persistent issues:
1. Check the console output for error messages
2. Review the README.md file for more detailed documentation
3. Check the JUPYTER_DEPLOYMENT.md if you're using Jupyter

## Next Steps

- Try uploading different types of certificates
- Experiment with the query functionality
- Review the full documentation for detailed information
- Explore integration with your existing systems

## Quick Reference

- Application URL: http://127.0.0.1:8080
- Default port: 8080
- Data storage location: ./processed_jobs/
- Template location: ./templates/
- Configuration: .env file

Happy analyzing! 