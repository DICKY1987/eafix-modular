# Multi-stage build for data-ingestor service
# Pin to specific digest for security (updated as of 2025-01-15)
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
      org.opencontainers.image.title="Data Ingestor Service" \
      org.opencontainers.image.description="Normalizes broker price feeds from MT4/DDE"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies with security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libc6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim@sha256:f52d14c7d0e87b6be38fdf5a5f6c7ae19a04e95e7dfd8cad073ad5063d80d3d0 as production

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
      org.opencontainers.image.title="Data Ingestor Service" \
      org.opencontainers.image.description="Normalizes broker price feeds from MT4/DDE"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies with security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        dumb-init \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user with specific UID/GID for security
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --shell /bin/sh --create-home appuser

# Create app directory
WORKDIR /app

# Copy application code with proper ownership
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser adapters/ ./adapters/
COPY --chown=appuser:appuser __init__.py .

# Security hardening - set proper file permissions
RUN chmod -R 755 /app && \
    find /app -type f -name "*.py" -exec chmod 644 {} \; && \
    find /app -type d -exec chmod 755 {} \; && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (documented but not privileged)
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
