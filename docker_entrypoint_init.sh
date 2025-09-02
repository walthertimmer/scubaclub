#!/bin/sh
set -e

echo "Running Django setup commands..."

# Database setup
echo "python manage.py ensure_schema"
python manage.py ensure_schema

echo "python manage.py migrate"
python manage.py migrate

echo "python manage.py compilemessages"
python manage.py compilemessages

echo "python manage.py create_superuser"
python manage.py create_superuser

# Static files
echo "python manage.py collectstatic --noinput"
python manage.py collectstatic --noinput

echo "Setup completed successfully"