#!/bin/sh
set -e

echo "Running Django setup commands..."

# Database setup
echo "python manage.py ensure_schema"
python manage.py ensure_schema

echo "python manage.py migrate"
python manage.py migrate

echo "python manage.py create_superuser"
python manage.py create_superuser

echo "python manage.py create_languages"
python manage.py create_languages

echo "python manage.py create_countries"
python manage.py create_countries

# Static files
echo "python manage.py collectstatic --noinput"
python manage.py collectstatic --noinput

echo "Setup completed successfully"