# Vehicle Management System Setup Guide

This document provides step-by-step instructions for setting up the Vehicle Management System Django application on a new device.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git (optional, for cloning the repository)

## Quick Setup

The easiest way to set up the project is using the automated setup scripts:

### For Linux/macOS:
```bash
chmod +x setup_venv.sh
./setup_venv.sh
```

### For Windows:
```bash
setup_venv.bat
```

These scripts will:
1. Create a virtual environment
2. Install all required dependencies
3. Attempt to set up the PostgreSQL database automatically
4. Guide you through the next steps

## Manual Setup

If you prefer to set up manually or the automated scripts don't work for your environment:

### 1. Install Required Software

```bash
# For macOS (using Homebrew)
brew install python postgresql
```

### 2. Clone/Copy the Project

```bash
# Using Git
git clone [repository-url]

# Navigate to the project directory
cd BAD_PMC
```

### 3. Create and Activate Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install django psycopg2-binary Pillow reportlab
```

### 4. Set Up PostgreSQL Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql  # Linux/macOS
psql -U postgres       # Windows

# Run these SQL commands:
CREATE USER pmc_user WITH PASSWORD '12345678';
CREATE DATABASE pmc_database;
GRANT ALL PRIVILEGES ON DATABASE pmc_database TO pmc_user;
\q
```

### 5. Configure Django Settings

Make sure your `settings.py` contains:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'pmc_database',
        'USER': 'pmc_user',
        'PASSWORD': '12345678',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

### 6. Final Setup Steps

```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create media directory for uploads
mkdir media

# Run the server
python manage.py runserver
```

Access the application at [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## User Roles and Access

The system supports three user roles:
- **Warehouse Personnel**: Manage inspection reports
- **Operations Team**: View vehicles and reports
- **Vehicle Management Team**: Full access to manage vehicles, users, and reports

## Backup and Restore

```bash
# Create backup
pg_dump -U pmc_user -d pmc_database > backup.sql

# Restore from backup
psql -U pmc_user -d pmc_database < backup.sql
```