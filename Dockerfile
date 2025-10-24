# Multi-stage build: build React frontend, then run Django + Gunicorn behind Nginx

# 1) Build frontend
FROM node:20-bullseye-slim AS frontend
WORKDIR /frontend

# Install deps first (better layer caching)
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile

# Allow Vite base API URL to be injected at build time
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Build
COPY frontend ./
RUN yarn build


# 2) Final runtime: Python + Nginx
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ARG DEBIAN_FRONTEND=noninteractive

# System packages for Django, Gunicorn, OCR/HEIF requirements, and Nginx
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        nginx \
        gettext-base \
        postgresql-client \
        build-essential \
        libpq-dev \
        tesseract-ocr \
        tesseract-ocr-eng \
        ocrmypdf \
        ghostscript \
        libheif-dev \
        libheif1 \
        libffi-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libwebp-dev \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 \
        libgomp1 \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies from backend's pyproject
COPY backend/pyproject.toml /app/backend/pyproject.toml
WORKDIR /app/backend
RUN pip install --no-cache-dir -e .

# Copy backend source
COPY backend /app/backend

# Copy built frontend into Nginx html directory
COPY --from=frontend /frontend/dist /usr/share/nginx/html

# Ensure static/media directories exist
RUN mkdir -p /app/backend/staticfiles /app/backend/media

# Copy Nginx template and startup script
WORKDIR /app
COPY nginx.template.conf /etc/nginx/templates/default.conf.template
COPY cloudstart.sh /app/start.sh
RUN chmod +x /app/start.sh \
    && rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf || true

# Render sets $PORT for the web service
ENV PORT=10000
EXPOSE 10000

CMD ["/app/start.sh"]
