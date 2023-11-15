#!/bin/sh

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Creating superuser..."
python manage.py createsuperuser --noinput \
  --username $DJANGO_USER \
  --email $DJANGO_EMAIL

# Set the password for the superuser.
echo "Setting superuser password..."
python -c "import os; \
import django; \
os.environ.setdefault('DJANGO_SETTINGS_MODULE', ''); \
django.setup(); \
from django.contrib.auth import get_user_model; \
User = get_user_model(); \
user = User.objects.get(username=os.environ.get('DJANGO_USER')); \
user.set_password(os.environ.get('DJANGO_PASSWORD')); \
user.save()"


echo "Starting server..."
exec gunicorn PosteBackend.wsgi:application --bind 0.0.0.0:8000 --workers 4