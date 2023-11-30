FROM python:3.11.4-slim

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=PosteBackend.settings

WORKDIR /usr/src/app

COPY . .

RUN apt-get update && apt-get install -y libpq-dev gcc && apt-get clean

RUN pip install --upgrade pip && pip install -r requirements.txt

RUN apt-get remove -y libpq-dev gcc && apt-get autoremove -y

RUN python manage.py collectstatic --noinput

RUN chmod +x /usr/src/app/deploy/entrypoint.sh

ENTRYPOINT ["/usr/src/app/deploy/entrypoint.sh"]