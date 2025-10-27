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

# Create data directories
RUN mkdir -p data/transport-router data/transport-router/dead-letters

# Expose service port (8090 for transport-router)
EXPOSE 8090

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8090/healthz || exit 1

# Run the service
CMD ["python", "-m", "src.main"]