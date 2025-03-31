#!/bin/bash

# Script to set up a Python virtual environment for the Vehicle Management System

# Define colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up virtual environment for Vehicle Management System...${NC}"

# Check if Python 3 is installed
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    # Check if this is Python 3
    PY_VERSION=$(python --version 2>&1)
    if [[ $PY_VERSION == *"Python 3"* ]]; then
        PYTHON=python
    else
        echo "Python 3 is required but not found. Please install Python 3 and try again."
        exit 1
    fi
else
    echo "Python 3 is required but not found. Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment
echo -e "${GREEN}Creating virtual environment...${NC}"
$PYTHON -m venv venv

# Determine the activate script based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    ACTIVATE="venv/Scripts/activate"
else
    # Unix/Linux/MacOS
    ACTIVATE="venv/bin/activate"
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source $ACTIVATE

# Upgrade pip
echo -e "${GREEN}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install django
pip install pillow  # For ImageField support
pip install reportlab  # For PDF generation

# Create requirements.txt
echo -e "${GREEN}Creating requirements.txt...${NC}"
pip freeze > requirements.txt

echo -e "${YELLOW}Installation complete!${NC}"
echo -e "To activate the virtual environment, run: ${GREEN}source $ACTIVATE${NC}"
echo -e "To deactivate the virtual environment when done, run: ${GREEN}deactivate${NC}"
echo -e "\nRequirements have been saved to requirements.txt"
