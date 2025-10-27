# Multi-stage build for security and size optimization
# Use specific Python version with digest pinning (to be updated with actual digests)
FROM python:3.11-slim@sha256:f52d14c7d0e87b6be38fdf5a5f6c7ae19a04e95e7dfd8cad073ad5063d80d3d0 as builder

# Set build arguments for security scanning
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION
LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.url="https://github.com/DICKY1987/eafix-modular" \
      org.opencontainers.image.source="https://github.com/DICKY1987/eafix-modular" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="EAFIX Trading System" \
      org.opencontainers.image.title="GUI Gateway Service" \
      org.opencontainers.image.description="API Gateway for EAFIX Trading System Operator Interface"

# Install security updates and build dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create application user and group
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --shell /bin/sh --create-home appuser

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt* pyproject.toml* poetry.lock* ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        fastapi==0.104.1 \
        uvicorn[standard]==0.24.0 \
        pydantic==2.5.0 \
        structlog==23.2.0 \
        redis==5.0.1 \
        httpx==0.25.2 && \
    pip list --format=json > /app/installed-packages.json

# Production stage
FROM python:3.11-slim@sha256:f52d14c7d0e87b6be38fdf5a5f6c7ae19a04e95e7dfd8cad073ad5063d80d3d0 as production

# Set build arguments for labels
ARG BUILD_DATE
ARG VCS_REF  
ARG VERSION
LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.url="https://github.com/DICKY1987/eafix-modular" \
      org.opencontainers.image.source="https://github.com/DICKY1987/eafix-modular" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="EAFIX Trading System" \
      org.opencontainers.image.title="GUI Gateway Service" \
      org.opencontainers.image.description="API Gateway for EAFIX Trading System Operator Interface"

# Install security updates and minimal runtime dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        dumb-init \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Create non-root user and group  
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --shell /bin/sh --create-home appuser

# Copy Python installation and packages from builder
COPY --from=builder --chown=root:root /usr/local /usr/local
COPY --from=builder --chown=root:root /app/installed-packages.json /app/

# Set working directory and ownership
WORKDIR /app
RUN chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser *.py ./

# Security hardening
RUN chmod -R 755 /app && \
    find /app -type f -name "*.py" -exec chmod 644 {} \; && \
    find /app -type d -exec chmod 755 {} \;

# Switch to non-root user
USER appuser

# Set security-focused environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

# Expose port
EXPOSE 8080

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Run the application with proper process management
CMD ["python", "-m", "uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "1", \
     "--access-log", \
     "--log-level", "info"]