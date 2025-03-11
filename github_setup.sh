#!/bin/bash

# Mill Test Certificate Analyzer GitHub Setup Script
# This script helps set up and configure a GitHub repository for the MTC Analyzer

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

# Check if Git is installed
check_git() {
    print_header "Checking Git Installation"
    if ! command -v git &>/dev/null; then
        echo -e "${RED}Git is not installed! Please install Git first.${NC}"
        echo -e "Visit https://git-scm.com/downloads for installation instructions."
        exit 1
    fi
    
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    echo -e "Found Git version: ${GREEN}$GIT_VERSION${NC}"
}

# Initialize Git repository
init_repo() {
    print_header "Initializing Git Repository"
    
    if [ -d ".git" ]; then
        echo -e "${YELLOW}Git repository already initialized.${NC}"
        
        # Check if remote already exists
        if git remote -v | grep -q origin; then
            echo -e "Remote 'origin' already configured:"
            git remote -v
            
            read -p "Do you want to update the remote URL? (y/n): " update_remote
            if [[ $update_remote == "y" || $update_remote == "Y" ]]; then
                configure_remote
            fi
        else
            configure_remote
        fi
    else
        echo "Initializing new Git repository..."
        git init
        echo -e "${GREEN}Git repository initialized!${NC}"
        configure_remote
    fi
}

# Configure remote repository
configure_remote() {
    print_header "Configuring Remote Repository"
    
    echo -e "${YELLOW}Enter your GitHub repository URL${NC}"
    echo "Example: https://github.com/username/mill-test-certificate-analyzer.git"
    read -p "Repository URL: " repo_url
    
    if [ -z "$repo_url" ]; then
        echo -e "${RED}Repository URL cannot be empty.${NC}"
        return
    fi
    
    # Check if remote already exists and update it
    if git remote -v | grep -q origin; then
        git remote set-url origin "$repo_url"
        echo -e "Updated remote 'origin' URL to: ${GREEN}$repo_url${NC}"
    else
        git remote add origin "$repo_url"
        echo -e "Added remote 'origin' with URL: ${GREEN}$repo_url${NC}"
    fi
}

# Initial commit
make_initial_commit() {
    print_header "Making Initial Commit"
    
    # Check if there are uncommitted changes
    if ! git diff --quiet HEAD || git diff --staged --quiet; then
        git add .
        git status
        
        read -p "Enter a commit message (default: 'Initial commit of Mill Test Certificate Analyzer'): " commit_message
        if [ -z "$commit_message" ]; then
            commit_message="Initial commit of Mill Test Certificate Analyzer"
        fi
        
        git commit -m "$commit_message"
        echo -e "${GREEN}Changes committed with message: '$commit_message'${NC}"
    else
        echo -e "${YELLOW}No changes to commit.${NC}"
    fi
}

# Push to remote
push_to_remote() {
    print_header "Pushing to Remote Repository"
    
    # Determine the current branch
    current_branch=$(git symbolic-ref --short HEAD 2>/dev/null)
    if [ -z "$current_branch" ]; then
        current_branch="main"
    fi
    
    echo -e "Current branch: ${GREEN}$current_branch${NC}"
    read -p "Push to this branch? (y/n): " confirm_push
    
    if [[ $confirm_push == "y" || $confirm_push == "Y" ]]; then
        echo "Pushing to remote repository..."
        git push -u origin "$current_branch"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Successfully pushed to remote repository!${NC}"
        else
            echo -e "${RED}Failed to push to remote repository.${NC}"
            echo "Please check your repository URL and credentials."
        fi
    else
        echo "Push cancelled."
    fi
}

# Configure GitHub Actions
configure_actions() {
    print_header "Configuring GitHub Actions"
    
    read -p "Do you want to set up GitHub Actions for CI/CD? (y/n): " setup_actions
    
    if [[ $setup_actions == "y" || $setup_actions == "Y" ]]; then
        # Create workflows directory if it doesn't exist
        mkdir -p .github/workflows
        
        # Create GitHub Actions workflow file
        cat > .github/workflows/python-app.yml << 'EOF'
name: Mill Test Certificate Analyzer CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 pytest
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    - name: Lint with flake8
      run: |
        # stop the build if there are Python syntax errors or undefined names
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    - name: Test with pytest
      run: |
        pytest
EOF
        
        git add .github/workflows/python-app.yml
        git commit -m "Add GitHub Actions workflow"
        
        echo -e "${GREEN}GitHub Actions workflow configured!${NC}"
        echo "After pushing to GitHub, CI/CD will be automatically set up."
    else
        echo "Skipping GitHub Actions setup."
    fi
}

# Display success message
show_success() {
    print_header "Setup Complete"
    
    echo -e "${GREEN}Your Mill Test Certificate Analyzer is now set up with GitHub!${NC}"
    echo -e "\nNext steps:"
    echo -e "1. Visit your GitHub repository to see your code"
    echo -e "2. Set up any required GitHub Secrets for your workflow"
    echo -e "3. Share your repository with collaborators"
    echo -e "\nRepository URL: $(git remote get-url origin)"
}

# Main execution
main() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${GREEN}       Mill Test Certificate Analyzer GitHub Setup           ${NC}"
    echo -e "${BLUE}================================================================${NC}"
    
    check_git
    init_repo
    make_initial_commit
    push_to_remote
    configure_actions
    show_success
}

# Run the main function
main 