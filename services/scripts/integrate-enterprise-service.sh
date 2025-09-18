#!/bin/bash
# services/scripts/integrate-enterprise-service.sh
# Usage: ./integrate-enterprise-service.sh data-ingestor 8001

SERVICE_NAME=$1
SERVICE_PORT=$2

if [ -z "$SERVICE_NAME" ] || [ -z "$SERVICE_PORT" ]; then
    echo "Usage: $0 <service-name> <service-port>"
    echo "Example: $0 data-ingestor 8001"
    exit 1
fi

echo "Integrating enterprise capabilities for $SERVICE_NAME..."

# Check if service directory exists
SERVICE_DIR="services/$SERVICE_NAME"
if [ ! -d "$SERVICE_DIR" ]; then
    echo "Error: Service directory $SERVICE_DIR does not exist"
    exit 1
fi

# 1. Update service main.py (automated) - backup first
MAIN_FILE="$SERVICE_DIR/src/${SERVICE_NAME//-/_}/main.py"
if [ -f "$MAIN_FILE" ]; then
    echo "Backing up original main.py..."
    cp "$MAIN_FILE" "$MAIN_FILE.backup"

    echo "Adding enterprise import to $MAIN_FILE..."
    # Add import at the top (after existing imports)
    sed -i '1i from services.common.base_service import BaseEnterpriseService' "$MAIN_FILE"
else
    echo "Warning: Main file $MAIN_FILE not found"
fi

# 2. Copy test template
echo "Setting up test templates..."
TEST_DIR="$SERVICE_DIR/tests/unit"
mkdir -p "$TEST_DIR"

cp "services/common/test_service_template.py" \
   "$TEST_DIR/test_${SERVICE_NAME//-/_}_service.py" 2>/dev/null || \
   echo "Warning: Test template not found, will create basic one"

# 3. Update Docker configuration
echo "Updating Docker configuration..."
DOCKERFILE="$SERVICE_DIR/Dockerfile"
if [ -f "$DOCKERFILE" ]; then
    # Add metrics port exposure
    if ! grep -q "EXPOSE.*$(($SERVICE_PORT + 1000))" "$DOCKERFILE"; then
        cat >> "$DOCKERFILE" << EOF

# Enterprise capabilities
EXPOSE $SERVICE_PORT
EXPOSE $(($SERVICE_PORT + 1000))
EOF
    fi
fi

# 4. Create environment template
echo "Creating environment template..."
cat > "$SERVICE_DIR/.env.template" << EOF
# Service Configuration
SERVICE_NAME=$SERVICE_NAME
SERVICE_PORT=$SERVICE_PORT
LOG_LEVEL=INFO

# Enterprise Feature Flags
FEATURE_ENHANCED_MONITORING=false
FEATURE_DETAILED_LOGGING=false
FEATURE_CIRCUIT_BREAKER=false

# Infrastructure
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://eafix:eafix_password@localhost:5432/eafix_trading
EOF

# 5. Validation
echo "Running validation suite for $SERVICE_NAME..."
if [ -d "$SERVICE_DIR/tests" ]; then
    cd "$SERVICE_DIR"
    if command -v pytest &> /dev/null; then
        pytest tests/ -v || echo "Tests failed - please review"
    else
        echo "pytest not available, skipping test validation"
    fi
    cd - > /dev/null
fi

echo "Integration complete for $SERVICE_NAME"
echo ""
echo "Next steps:"
echo "1. Update the service class to inherit from BaseEnterpriseService"
echo "2. Implement the required abstract methods (startup, shutdown, check_health)"
echo "3. Test service locally: docker-compose up $SERVICE_NAME"
echo "4. Verify metrics at localhost:$(($SERVICE_PORT + 1000))"
echo "5. Check health endpoint: curl localhost:$SERVICE_PORT/health"
echo ""
echo "Manual changes required in $MAIN_FILE:"
echo "- Change class to inherit from BaseEnterpriseService"
echo "- Call super().__init__('$SERVICE_NAME', $SERVICE_PORT) in constructor"
echo "- Implement startup(), shutdown(), and check_health() methods"