# Multi-stage Dockerfile for Toonora Pipeline
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    inkscape \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-enhanced.txt requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-enhanced.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p assets/characters assets/backgrounds assets/audio assets/stock_videos \
    output temp logs

# Default command
CMD ["python", "enhanced_pipeline.py", "--week=1"]