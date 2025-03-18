# Mill Test Certificate Analyzer

A simple Flask web application that analyzes Mill Test Certificates (MTCs) to extract and structure data, and provides a natural language querying interface.

## Features

- **Document Processing**: Upload and process mill test certificates in PDF, JPG, or PNG format
- **Text Extraction**: Extract text from certificates using LLMWhisperer's advanced OCR
- **Structured Data**: Extract key information like chemical composition and mechanical properties
- **Natural Language Query**: Ask questions about the certificate in plain English
- **Data Organization**: Save and browse previously processed certificates

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository or download the code

2. Install the required dependencies
```bash
pip install -r requirements.txt
```

### Running the Application

1. Start the Flask server
```bash
python run.py
```

2. Open a web browser and navigate to `http://127.0.0.1:8080`

## Usage

### Uploading a Certificate

1. Navigate to the home page
2. Click on the "Upload Mill Test Certificate" button
3. Select a PDF or image file containing a Mill Test Certificate
4. Click "Upload" to process the certificate

### Querying Data

You can query the extracted data using natural language:
1. Navigate to the analysis page for a certificate
2. Enter your question in the query box (e.g., "What is the carbon content?")
3. View the response based on the certificate data

## Directory Structure

```
├── app.py                   # Main Flask application
├── run.py                   # Script to run the application
├── requirements.txt         # Python dependencies
├── examples/                # Example certificate files
├── static/                  # Static files (CSS/JS)
├── templates/               # HTML templates
├── processed_files/         # Directory for processed certificate data
└── unstract/                # Custom LLMWhisperer module
```

## Development

### Adding New Features

To add new features:

1. Create a feature branch
```bash
git checkout -b feature/your-feature-name
```

2. Implement your changes
3. Test thoroughly
4. Submit a pull request

### Running Tests

```bash
pytest tests/
```

## Local Development

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`
4. Access the application at [http://localhost:8080](http://localhost:8080) 