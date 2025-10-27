FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY src/ src/

# Copy shared library (relative to build context)
COPY ../../shared/ /app/shared/

# Copy contracts (relative to build context)  
COPY ../../contracts/ /app/contracts/

# Create data and config directories
RUN mkdir -p data/reentry config

# Create default parameter sets directory
RUN mkdir -p config

# Expose service port (8087 for reentry-matrix-svc)
EXPOSE 8087

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8087/healthz || exit 1

# Run the service
CMD ["python", "-m", "src.main"]