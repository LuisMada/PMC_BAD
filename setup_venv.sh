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
pip install psycopg2-binary  # For PostgreSQL support

# Try to detect if PostgreSQL is installed
if command -v psql &>/dev/null; then
    echo -e "${GREEN}PostgreSQL detected. Attempting to set up database...${NC}"
    
    # Check if we can connect to PostgreSQL
    if psql -U postgres -c '\q' 2>/dev/null; then
        # Try to create database and user automatically
        echo -e "${GREEN}Creating database and user...${NC}"
        psql -U postgres -c "CREATE USER pmc_user WITH PASSWORD '12345678';" 2>/dev/null
        psql -U postgres -c "CREATE DATABASE pmc_database;" 2>/dev/null
        psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE pmc_database TO pmc_user;" 2>/dev/null
        
        echo -e "${GREEN}Database setup complete. If you didn't see any error messages, the setup was successful.${NC}"
    else
        echo -e "${YELLOW}Could not connect to PostgreSQL as user 'postgres'. You may need to set up the database manually.${NC}"
        echo -e "Please run the following commands in PostgreSQL:"
        echo -e "CREATE USER pmc_user WITH PASSWORD '12345678';"
        echo -e "CREATE DATABASE pmc_database;"
        echo -e "GRANT ALL PRIVILEGES ON DATABASE pmc_database TO pmc_user;"
    fi
else
    echo -e "${YELLOW}PostgreSQL not detected. Please install PostgreSQL and set up the database manually.${NC}"
fi

# Create requirements.txt
echo -e "${GREEN}Creating requirements.txt...${NC}"
pip freeze > requirements.txt

echo -e "${YELLOW}Installation complete!${NC}"
echo -e "To activate the virtual environment, run: ${GREEN}source $ACTIVATE${NC}"
echo -e "To deactivate the virtual environment when done, run: ${GREEN}deactivate${NC}"

echo -e "\nNext steps:"
echo -e "1. Apply migrations: ${GREEN}python manage.py migrate${NC}"
echo -e "2. Create a superuser: ${GREEN}python manage.py createsuperuser${NC}"
echo -e "3. Run the server: ${GREEN}python manage.py runserver${NC}"

echo -e "\nRequirements have been saved to requirements.txt"