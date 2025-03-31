# Vehicle Management System Setup Guide

This document provides step-by-step instructions for setting up the Vehicle Management System Django application on a new device.

## Prerequisites

- Python 3.8 or higher
- Git (optional, for cloning the repository)

## Setup Steps

### 1. Install Required Software

Ensure your system has the necessary software installed:

```bash
# For macOS (using Homebrew)
brew install python
```

### 2. Clone/Copy the Project

Transfer the project files to your new device:

```bash
# Using Git
git clone [repository-url]

# Or copy the files manually to your device
```

Navigate to the project directory:

```bash
cd BAD_PMC
```

### 3. Install Python Dependencies

Create and activate a virtual environment, then install required packages:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Django and other dependencies
pip install django Pillow reportlab
```

### 4. Configure SQLite Database

The project uses SQLite by default, which doesn't require additional setup. The database file will be created automatically in your project directory.

### 5. Update Django Settings (if needed)

The `settings.py` file should already be configured to use SQLite:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 6. Create Database Tables

Run migrations to set up the database schema:

```bash
python manage.py makemigrations VehicleManagementSystem
python manage.py migrate
```

### 7. Create a Superuser

Create an administrative user:

```bash
python manage.py createsuperuser
```

Follow the prompts to enter employee ID, name, and password.

### 8. Create Media Directory

Create a directory for file uploads:

```bash
mkdir media
```

### 9. Run the Development Server

Start the Django development server:

```bash
python manage.py runserver
```

Access the application by visiting [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your web browser.

## User Roles and Access

The system supports three user roles:
- **Warehouse Personnel**: Manage inspection reports
- **Operations Team**: View vehicles and reports
- **Vehicle Management Team**: Full access to manage vehicles, users, and reports