#!/bin/bash

# services/scripts/integrate-enterprise-service.sh
# Automated script to integrate enterprise capabilities into any EAFIX service
# Usage: ./integrate-enterprise-service.sh <service-name> <service-port>

set -euo pipefail

SERVICE_NAME="${1:-}"
SERVICE_PORT="${2:-8000}"

if [[ -z "$SERVICE_NAME" ]]; then
    echo "Usage: $0 <service-name> [port]"
    echo "Example: $0 data-ingestor 8001"
    exit 1
fi

SERVICE_DIR="services/${SERVICE_NAME}"
SRC_DIR="${SERVICE_DIR}/src/${SERVICE_NAME//-/_}"

echo "🚀 Integrating enterprise capabilities for service: $SERVICE_NAME"

# Validate service directory exists
if [[ ! -d "$SERVICE_DIR" ]]; then
    echo "❌ Service directory not found: $SERVICE_DIR"
    exit 1
fi

# Step 1: Create enterprise main.py
echo "📝 Creating enterprise main.py..."
cat > "${SRC_DIR}/main_enterprise.py" << 'EOF'
"""
Enterprise-enabled main entry point for {SERVICE_NAME}
Provides full enterprise capabilities with 2-line integration
"""

import asyncio
import os
from pathlib import Path

from services.common.base_enterprise_service import BaseEnterpriseService, ServiceMetadata
from services.common.service_config import ServiceConfig
from .core import {SERVICE_CLASS_NAME}  # Import your service logic


class {SERVICE_CLASS_NAME}Enterprise(BaseEnterpriseService):
    """Enterprise wrapper for {SERVICE_NAME} service"""
    
    def __init__(self):
        # Service metadata
        metadata = ServiceMetadata(
            name="{SERVICE_NAME}",
            version="1.0.0",
            description="{SERVICE_DESCRIPTION}",
            dependencies=[],  # Add your dependencies
            health_check_interval=30,
            circuit_breaker_enabled=True,
            metrics_enabled=True
        )
        
        # Load configuration
        config = ServiceConfig.from_env()
        
        # Initialize enterprise service
        super().__init__(metadata, config)
        
        # Initialize your service logic
        self.service_impl = {SERVICE_CLASS_NAME}()
    
    async def service_logic(self):
        """Implement your core service logic here"""
        # Start your service's main loop
        await self.service_impl.start()
        
        # Setup your routes
        self._setup_service_routes()
    
    async def cleanup(self):
        """Cleanup resources when shutting down"""
        if hasattr(self.service_impl, 'stop'):
            await self.service_impl.stop()
    
    def _setup_service_routes(self):
        """Setup service-specific routes"""
        
        @self.app.get("/api/v1/status")
        async def get_status():
            """Service-specific status endpoint"""
            return await self.service_impl.get_status()
        
        # Add more routes as needed
        # @self.app.post("/api/v1/your-endpoint")
        # async def your_endpoint(data: YourModel):
        #     return await self.service_impl.handle_request(data)


def main():
    """Main entry point"""
    service = {SERVICE_CLASS_NAME}Enterprise()
    service.run(
        host="0.0.0.0",
        port={SERVICE_PORT}
    )


if __name__ == "__main__":
    main()
EOF

# Replace placeholders
SERVICE_CLASS_NAME=$(echo "$SERVICE_NAME" | sed 's/-/_/g' | sed 's/\b\w/\u&/g' | sed 's/_//g')
SERVICE_DESCRIPTION="Enterprise-enabled $SERVICE_NAME service for EAFIX trading system"

sed -i "s/{SERVICE_NAME}/$SERVICE_NAME/g" "${SRC_DIR}/main_enterprise.py"
sed -i "s/{SERVICE_CLASS_NAME}/$SERVICE_CLASS_NAME/g" "${SRC_DIR}/main_enterprise.py"
sed -i "s/{SERVICE_DESCRIPTION}/$SERVICE_DESCRIPTION/g" "${SRC_DIR}/main_enterprise.py"
sed -i "s/{SERVICE_PORT}/$SERVICE_PORT/g" "${SRC_DIR}/main_enterprise.py"

# Step 2: Update Dockerfile for enterprise capabilities
echo "🐳 Updating Dockerfile..."
if [[ -f "${SERVICE_DIR}/Dockerfile" ]]; then
    # Add enterprise ports to existing Dockerfile
    if ! grep -q "EXPOSE.*$SERVICE_PORT" "${SERVICE_DIR}/Dockerfile"; then
        cat >> "${SERVICE_DIR}/Dockerfile" << EOF

# Enterprise service ports
EXPOSE $SERVICE_PORT
EXPOSE $((SERVICE_PORT + 1000))  # Health check port

# Enterprise entry point
CMD ["python", "-m", "${SERVICE_NAME//-/_}.main_enterprise"]
EOF
    fi
else
    # Create new Dockerfile
    cat > "${SERVICE_DIR}/Dockerfile" << EOF
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY services/common/ ./services/common/

# Enterprise service ports
EXPOSE $SERVICE_PORT
EXPOSE $((SERVICE_PORT + 1000))  # Health check port

# Set Python path
ENV PYTHONPATH=/app/src

# Enterprise entry point
CMD ["python", "-m", "${SERVICE_NAME//-/_}.main_enterprise"]
EOF
fi

# Step 3: Create environment template
echo "⚙️  Creating environment template..."
cat > "${SERVICE_DIR}/.env.template" << 'EOF'
# Enterprise Service Configuration
SERVICE_NAME={SERVICE_NAME}
SERVICE_PORT={SERVICE_PORT}
LOG_LEVEL=INFO

# Feature Flags
ENTERPRISE_FEATURES_ENABLED=true
HEALTH_CHECKS_ENABLED=true
METRICS_ENABLED=true
CIRCUIT_BREAKER_ENABLED=true

# Database (if needed)
DATABASE_URL=postgresql://user:pass@localhost:5432/eafix

# Redis (if needed)
REDIS_URL=redis://localhost:6379

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Monitoring
PROMETHEUS_ENABLED=true
JAEGER_ENABLED=false

# Security
JWT_SECRET_KEY=your-secret-key-here
API_KEY_HEADER=X-API-Key
EOF

sed -i "s/{SERVICE_NAME}/$SERVICE_NAME/g" "${SERVICE_DIR}/.env.template"
sed -i "s/{SERVICE_PORT}/$SERVICE_PORT/g" "${SERVICE_DIR}/.env.template"

# Step 4: Create test template
echo "🧪 Creating test template..."
mkdir -p "${SERVICE_DIR}/tests/unit"
cat > "${SERVICE_DIR}/tests/unit/test_${SERVICE_NAME//-/_}_enterprise.py" << 'EOF'
"""
Enterprise capability tests for {SERVICE_NAME}
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from {SERVICE_MODULE}.main_enterprise import {SERVICE_CLASS_NAME}Enterprise


@pytest.fixture
async def service():
    """Create test service instance"""
    service = {SERVICE_CLASS_NAME}Enterprise()
    yield service
    await service.cleanup()


@pytest.fixture
def client(service):
    """Create test client"""
    return TestClient(service.app)


class TestEnterpriseCapabilities:
    """Test enterprise capabilities"""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "{SERVICE_NAME}"
    
    def test_ready_endpoint_not_ready(self, client):
        """Test readiness when service not ready"""
        response = client.get("/ready")
        assert response.status_code == 503
    
    def test_info_endpoint(self, client):
        """Test service info endpoint"""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "{SERVICE_NAME}"
        assert data["version"] == "1.0.0"
        assert "uptime" in data
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_service_lifecycle(self, service):
        """Test service startup and shutdown"""
        # Mock the service implementation
        service.service_impl = AsyncMock()
        service.service_impl.start = AsyncMock()
        service.service_impl.stop = AsyncMock()
        service.service_impl.get_status = AsyncMock(return_value={"status": "ok"})
        
        # Test startup
        await service.startup()
        assert service.is_ready
        assert service.is_healthy
        service.service_impl.start.assert_called_once()
        
        # Test shutdown
        await service.shutdown()
        assert not service.is_ready
        service.service_impl.stop.assert_called_once()


class TestServiceSpecific:
    """Test service-specific functionality"""
    
    def test_status_endpoint(self, client):
        """Test service status endpoint"""
        with patch.object(client.app, 'service_impl') as mock_impl:
            mock_impl.get_status.return_value = {"status": "operational"}
            response = client.get("/api/v1/status")
            assert response.status_code == 200
    
    # Add more service-specific tests here
EOF

sed -i "s/{SERVICE_NAME}/$SERVICE_NAME/g" "${SERVICE_DIR}/tests/unit/test_${SERVICE_NAME//-/_}_enterprise.py"
sed -i "s/{SERVICE_CLASS_NAME}/$SERVICE_CLASS_NAME/g" "${SERVICE_DIR}/tests/unit/test_${SERVICE_NAME//-/_}_enterprise.py"
sed -i "s/{SERVICE_MODULE}/${SERVICE_NAME//-/_}/g" "${SERVICE_DIR}/tests/unit/test_${SERVICE_NAME//-/_}_enterprise.py"

# Step 5: Update docker-compose.yml entry
echo "🔧 Updating docker-compose.yml..."
if [[ -f "docker-compose.yml" ]]; then
    # Check if service already exists in compose file
    if ! grep -q "${SERVICE_NAME}:" docker-compose.yml; then
        cat >> docker-compose.yml << EOF

  ${SERVICE_NAME}:
    build: ./services/${SERVICE_NAME}
    ports:
      - "${SERVICE_PORT}:${SERVICE_PORT}"
      - "$((SERVICE_PORT + 1000)):$((SERVICE_PORT + 1000))"
    environment:
      - SERVICE_NAME=${SERVICE_NAME}
      - SERVICE_PORT=${SERVICE_PORT}
      - ENTERPRISE_FEATURES_ENABLED=true
    volumes:
      - ./services/common:/app/services/common
    depends_on:
      - redis
      - postgres
    networks:
      - eafix-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${SERVICE_PORT}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF
    fi
fi

echo "✅ Enterprise integration complete for $SERVICE_NAME!"
echo ""
echo "Next steps:"
echo "1. Review and customize ${SRC_DIR}/main_enterprise.py"
echo "2. Copy .env.template to .env and configure"
echo "3. Run tests: pytest ${SERVICE_DIR}/tests/"
echo "4. Build and run: docker-compose up ${SERVICE_NAME}"
echo ""
echo "Enterprise capabilities now available:"
echo "- Health checks: http://localhost:${SERVICE_PORT}/health"
echo "- Readiness: http://localhost:${SERVICE_PORT}/ready"
echo "- Metrics: http://localhost:${SERVICE_PORT}/metrics"
echo "- Service info: http://localhost:${SERVICE_PORT}/info"