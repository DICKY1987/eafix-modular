# Multi-stage build for calendar-downloader service
FROM python:3.11-slim@sha256:f52d14c7d0e87b6be38fdf5a5f6c7ae19a04e95e7dfd8cad073ad5063d80d3d0 as builder

# Build arguments for security labeling
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Security labels
LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.url="https://github.com/DICKY1987/eafix-modular" \
      org.opencontainers.image.source="https://github.com/DICKY1987/eafix-modular" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="EAFIX Trading System" \
      org.opencontainers.image.title="Calendar Downloader Service" \
      org.opencontainers.image.description="Automated ForexFactory calendar downloader with enterprise monitoring"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies and dumb-init
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r eafix && useradd -r -g eafix -d /app -s /bin/bash eafix

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim@sha256:f52d14c7d0e87b6be38fdf5a5f6c7ae19a04e95e7dfd8cad073ad5063d80d3d0

# Copy built dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/bin/dumb-init /usr/bin/dumb-init
COPY --from=builder /usr/bin/curl /usr/bin/curl

# Create non-root user
RUN groupadd -r eafix && useradd -r -g eafix -d /app -s /bin/bash eafix

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY --from=builder /app/requirements.txt ./

# Create data directory for calendars
RUN mkdir -p data/calendars && chown -R eafix:eafix /app

# Switch to non-root user
USER eafix

# Expose ports
EXPOSE 8080

# Enhanced health check with proper timeout
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

# Use dumb-init for proper signal handling and PID 1 management
ENTRYPOINT ["dumb-init", "--"]

# Enhanced command with better process management
CMD ["python", "-m", "uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "1", \
     "--access-log", \
     "--log-level", "info"]

# Enterprise capabilities - additional port for enterprise features
EXPOSE 8001