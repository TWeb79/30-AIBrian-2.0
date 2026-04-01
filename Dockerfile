# BRAIN 2.0 - Dockerfile
# Multi-stage build for production

# ─────────────────────────────────────────────────────────────────────────────
# Base Stage: Python
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ─────────────────────────────────────────────────────────────────────────────
# Development Stage
# ─────────────────────────────────────────────────────────────────────────────
FROM base AS development

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose API port
EXPOSE 8000

# Run development server with hot reload
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ─────────────────────────────────────────────────────────────────────────────
# Production Stage
# ─────────────────────────────────────────────────────────────────────────────
FROM base AS production

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy compiled Python files only (no source for smaller image)
# In a real build, you'd use a multi-stage build with compile step
COPY api ./api
COPY brain ./brain
COPY codec ./codec
COPY config.py .
COPY self ./self
COPY emotion ./emotion
COPY drives ./drives
COPY persistence ./persistence

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BRAIN_SCALE=0.01
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Expose API port
EXPOSE 8000

# Change to non-root user
USER appuser

# Run production server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ─────────────────────────────────────────────────────────────────────────────
# Build Commands
# ─────────────────────────────────────────────────────────────────────────────
# Build development image:
#   docker build -t brain2:dev --target development .
#
# Build production image:
#   docker build -t brain2:prod --target production .
#
# Run development:
#   docker run -p 8000:8000 -v $(pwd)/brain_state:/app/brain_state brain2:dev
#
# Run production:
#   docker run -p 8000:8000 -v brain2_data:/app/brain_state brain2:prod
#
# Docker Compose for local development:
#   docker-compose up --build
