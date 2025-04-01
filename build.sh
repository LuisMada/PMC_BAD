#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting build process..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Create superuser automatically if not exists
echo "Creating superuser if needed..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BAD_PMC.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(employee_id=os.environ.get('DJANGO_SUPERUSER_EMPLOYEE_ID', 'ADMIN001')).exists():
    User.objects.create_superuser(
        employee_id=os.environ.get('DJANGO_SUPERUSER_EMPLOYEE_ID', 'ADMIN001'),
        name=os.environ.get('DJANGO_SUPERUSER_NAME', 'Admin User'),
        password=os.environ.get('DJANGO_SUPERUSER_PASSWORD', '00000000')
    )
    print('Superuser created.')
else:
    print('Superuser already exists.')
"

echo "Build completed successfully!"