#!/bin/bash

# Mill Test Certificate Analyzer Runner Script
# This script helps set up and run the MTC Analyzer application

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}===${NC} $1 ${BLUE}===${NC}\n"
}

# Check if Python is installed
check_python() {
    print_header "Checking Python Installation"
    if command -v python3 &>/dev/null; then
        PYTHON="python3"
    elif command -v python &>/dev/null; then
        PYTHON="python"
    else
        echo -e "${RED}Python is not installed! Please install Python 3.8 or newer.${NC}"
        exit 1
    fi
    
    # Check Python version
    PY_VERSION=$($PYTHON --version 2>&1 | cut -d' ' -f2)
    echo -e "Found Python version: ${GREEN}$PY_VERSION${NC}"
    
    # Parse version number and check if it's 3.8+
    PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
    PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)
    
    if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]); then
        echo -e "${YELLOW}Warning: Python version 3.8+ is recommended for this application.${NC}"
    fi
}

# Setup virtual environment
setup_venv() {
    print_header "Setting Up Virtual Environment"
    
    if [ -d "venv" ]; then
        echo "Virtual environment already exists."
    else
        echo "Creating new virtual environment..."
        $PYTHON -m venv venv
    fi
    
    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        echo "Activating virtual environment (Windows)..."
        source venv/Scripts/activate
    else
        # Unix-like
        echo "Activating virtual environment..."
        source venv/bin/activate
    fi
    
    echo -e "${GREEN}Virtual environment activated!${NC}"
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    echo "Installing required packages from requirements.txt..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}All dependencies installed successfully!${NC}"
    else
        echo -e "${RED}Error installing dependencies. Please check the error messages above.${NC}"
        exit 1
    fi
}

# Setup environment variables
setup_env() {
    print_header "Setting Up Environment Variables"
    
    if [ ! -f ".env" ]; then
        echo "Creating .env file..."
        echo "FLASK_APP=app.py" > .env
        echo "FLASK_ENV=development" >> .env
        
        echo -e "${YELLOW}Please edit the .env file to add your OpenAI API key:${NC}"
        echo -e "${YELLOW}OPENAI_API_KEY=your_api_key_here${NC}"
    else
        echo ".env file already exists."
    fi
}

# Create required directories
create_dirs() {
    print_header "Creating Required Directories"
    
    if [ ! -d "processed_jobs" ]; then
        echo "Creating processed_jobs directory..."
        mkdir -p processed_jobs/temp
    fi
    
    if [ ! -d "processed_jobs/temp" ]; then
        echo "Creating temp directory..."
        mkdir -p processed_jobs/temp
    fi
    
    echo -e "${GREEN}Directories created/verified!${NC}"
}

# Run the application
run_app() {
    print_header "Starting Mill Test Certificate Analyzer"
    echo -e "The application will be available at ${GREEN}http://127.0.0.1:8080${NC}"
    echo -e "Press ${BLUE}Ctrl+C${NC} to stop the server."
    echo ""
    
    $PYTHON app.py
}

# Main execution
main() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${GREEN}           Mill Test Certificate Analyzer Setup               ${NC}"
    echo -e "${BLUE}================================================================${NC}"
    
    check_python
    setup_venv
    install_dependencies
    setup_env
    create_dirs
    run_app
}

# Run the main function
main 