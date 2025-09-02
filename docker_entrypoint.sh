#!/bin/sh
set -e

echo "Starting Django application..."

# Collect static files if in development mode
if [ "$ENVIRONMENT" = "dev" ]; then
    echo "Collecting static files for development..."
    python manage.py collectstatic --noinput

    # Use Django's development server which serves static files automatically
    echo "Starting Django development server..."
    exec python manage.py runserver 0.0.0.0:${PORT:-8000}
else
    echo "running with gunicorn"
    # Production mode - use Gunicorn
    exec gunicorn scubaclub.wsgi:application \
        --bind 0.0.0.0:${PORT:-8000} \
        --workers=1 --threads=4 --timeout=60
fi