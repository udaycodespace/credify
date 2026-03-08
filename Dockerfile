# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and use a virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Runtime ---
FROM python:3.11-slim

WORKDIR /app

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000 \
    FLASK_ENV=production \
    PATH="/opt/venv/bin:$PATH"

# Install minimal runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libfreetype6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Create persistent data volumes with correct permissions
RUN mkdir -p data logs static/uploads \
    && useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

# Ensure appuser can write to the data directories
RUN chmod -R 755 data logs static/uploads

USER appuser

# Health check using curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

EXPOSE 5000

# Entry point
CMD ["python", "main.py"]
