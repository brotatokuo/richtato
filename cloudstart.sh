#!/usr/bin/env bash
set -euo pipefail

# Start Nginx and Django (Gunicorn) inside the container

envsubst < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

service nginx start

cd /app/backend
python manage.py collectstatic --noinput

exec gunicorn richtato.wsgi:application \
  --bind 0.0.0.0:${PORT:-10000} \
  --workers 3 \
  --timeout 120
