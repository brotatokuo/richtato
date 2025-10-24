FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
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

# Copy pyproject.toml first for better caching
COPY pyproject.toml /app/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy the rest of the project
COPY . /app/

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media

# Expose port
EXPOSE 8000

# Default command
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
