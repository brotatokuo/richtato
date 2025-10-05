#!/usr/bin/env bash
set -euo pipefail

export DEPLOY_STAGE=${DEPLOY_STAGE:-PROD}
export PYTHONUNBUFFERED=1
export PORT=${PORT:-10000}

cd /app/backend

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Start Gunicorn on 8000 in background
(gunicorn richtato.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 120 &)

# Render Nginx config from template with current $PORT
envsubst '$PORT' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# Start Nginx in foreground
exec nginx -g 'daemon off;'
