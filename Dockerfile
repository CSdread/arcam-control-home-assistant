# Multi-stage build for efficient image size
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml ./
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r homeassistant && useradd -r -g homeassistant homeassistant

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY homeassistant/ ./homeassistant/
COPY docs/ ./docs/
COPY tests/ ./tests/
COPY pyproject.toml requirements.txt ./

# Create necessary directories and set permissions
RUN mkdir -p /config /data && \
    chown -R homeassistant:homeassistant /app /config /data

# Switch to non-root user
USER homeassistant

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV HOME_ASSISTANT_CONFIG_DIR=/config

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8123/api/ || exit 1

# Expose Home Assistant port
EXPOSE 8123

# Volume mounts for persistent data
VOLUME ["/config", "/data"]

# Default command to run Home Assistant
CMD ["python", "-m", "homeassistant", "--config", "/config"]
