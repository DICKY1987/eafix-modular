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

# Create data directory
RUN mkdir -p data/reentry-engine

# Expose service port (8089 for reentry-engine)
EXPOSE 8089

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8089/healthz || exit 1

# Run the service
CMD ["python", "-m", "src.main"]