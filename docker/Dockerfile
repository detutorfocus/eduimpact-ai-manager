# ─────────────────────────────────────────────
# EduImpact AI Manager v1 — Dockerfile
# ─────────────────────────────────────────────

FROM python:3.11-slim

# System dependencies for Pillow, psycopg2, and lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/media/quote_cards \
             /app/staticfiles \
             /app/logs \
             /app/assets/fonts

# Set permissions
RUN chmod +x manage.py

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings

# Expose port
EXPOSE 8000

# Default command (overridden in docker-compose per service)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
