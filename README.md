# Vehicle Management System Setup Guide

This document provides step-by-step instructions for setting up the Vehicle Management System Django application on a new device.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Git (optional, for cloning the repository)

## Setup Steps

### 1. Install Required Software

Ensure your system has the necessary software installed:

```bash
# For macOS (using Homebrew)
brew install python postgresql

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
pip install django psycopg2-binary Pillow
```

### 4. Configure PostgreSQL

Set up the PostgreSQL database:

```bash
# Connect to PostgreSQL command line
# For Linux/macOS:
sudo -u postgres psql
# For Windows (after adding PostgreSQL bin to PATH):
psql -U postgres
```

Execute the following SQL commands:

```sql
-- Create a database user
CREATE USER pmc_user WITH PASSWORD '12345678';

-- Create the database
CREATE DATABASE pmc_database;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE pmc_database TO pmc_user;

-- Exit PostgreSQL
\q
```

### 5. Update Django Settings (if needed)

If your PostgreSQL configuration differs, update the `settings.py` file:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'pmc_database',
        'USER': 'pmc_user',
        'PASSWORD': '12345678',
        'HOST': '127.0.0.1',  # Use 127.0.0.1 instead of 'localhost'
        'PORT': '5432',
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

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL service is running
- Verify database credentials in settings.py
- Check that the database and user exist with proper permissions

### Migration Errors
- If you encounter migration errors, try:
  ```bash
  python manage.py migrate --fake-initial
  ```

### Static Files Not Loading
- Run `python manage.py collectstatic`
- Ensure STATIC_URL and STATIC_ROOT are correctly set in settings.py

## Backup and Restore

### Creating a Database Backup
```bash
pg_dump -U pmc_user -d pmc_database > backup.sql
```

### Restoring from Backup
```bash
psql -U pmc_user -d pmc_database < backup.sql
```