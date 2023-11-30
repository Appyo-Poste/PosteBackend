#!/bin/sh

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Creating superuser..."
python manage.py createsuperuser --noinput

echo "Starting server..."
exec gunicorn PosteBackend.wsgi:application --bind 0.0.0.0:8000 --workers 4