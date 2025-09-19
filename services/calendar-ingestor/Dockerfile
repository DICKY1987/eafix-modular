FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY src/ src/

# Create data directory
RUN mkdir -p data/calendar

# Expose service port (8086 for calendar-ingestor)
EXPOSE 8086

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8086/healthz || exit 1

# Run the service
CMD ["python", "-m", "src.main"]