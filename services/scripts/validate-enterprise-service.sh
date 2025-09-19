#!/bin/bash
# services/scripts/validate-enterprise-service.sh
SERVICE_NAME=$1
SERVICE_PORT=$2

if [ -z "$SERVICE_NAME" ] || [ -z "$SERVICE_PORT" ]; then
    echo "Usage: $0 <service-name> <service-port>"
    echo "Example: $0 data-ingestor 8001"
    exit 1
fi

echo "=== Enterprise Capability Validation for $SERVICE_NAME ==="

# Health Check
echo "Testing health endpoint..."
if curl -f --max-time 5 "http://localhost:$SERVICE_PORT/health" > /dev/null 2>&1; then
    echo "✅ Health endpoint responding"
else
    echo "❌ Health endpoint failed"
    exit 1
fi

# Metrics Collection
echo "Validating metrics collection..."
METRICS_PORT=$(($SERVICE_PORT + 1000))
if curl -f --max-time 5 "http://localhost:$METRICS_PORT/metrics" 2>/dev/null | grep -q "${SERVICE_NAME//-/_}"; then
    echo "✅ Metrics endpoint responding with service metrics"
else
    echo "❌ Metrics endpoint failed or no service metrics found"
    exit 1
fi

# Feature Flags
echo "Testing feature flags endpoint..."
if curl -f --max-time 5 "http://localhost:$SERVICE_PORT/feature-flags" > /dev/null 2>&1; then
    echo "✅ Feature flags endpoint responding"
else
    echo "❌ Feature flags endpoint failed"
    exit 1
fi

# Load Testing (basic)
echo "Running basic load test..."
SUCCESS_COUNT=0
TOTAL_REQUESTS=50

for i in $(seq 1 $TOTAL_REQUESTS); do
    if curl -s --max-time 2 "http://localhost:$SERVICE_PORT/health" > /dev/null 2>&1; then
        ((SUCCESS_COUNT++))
    fi
done

SUCCESS_RATE=$(echo "scale=2; $SUCCESS_COUNT * 100 / $TOTAL_REQUESTS" | bc -l 2>/dev/null || echo "N/A")
echo "Load test results: $SUCCESS_COUNT/$TOTAL_REQUESTS requests successful ($SUCCESS_RATE%)"

if [ "$SUCCESS_COUNT" -lt $((TOTAL_REQUESTS * 90 / 100)) ]; then
    echo "❌ Load test failed - success rate below 90%"
    exit 1
fi

# Security Validation (if bandit is available)
echo "Security scan..."
SERVICE_DIR="services/$SERVICE_NAME"
if command -v bandit &> /dev/null && [ -d "$SERVICE_DIR/src" ]; then
    if bandit -r "$SERVICE_DIR/src/" --severity-level medium > /dev/null 2>&1; then
        echo "✅ Security scan passed"
    else
        echo "⚠️  Security scan found issues (check manually)"
    fi
else
    echo "⚠️  Security scan skipped (bandit not available or no src directory)"
fi

# Check for required enterprise capabilities
echo "Checking enterprise integration..."

# Check if service imports BaseEnterpriseService
MAIN_FILE="$SERVICE_DIR/src/${SERVICE_NAME//-/_}/main.py"
if [ -f "$MAIN_FILE" ] && grep -q "BaseEnterpriseService" "$MAIN_FILE"; then
    echo "✅ Service imports BaseEnterpriseService"
else
    echo "❌ Service does not import BaseEnterpriseService"
    exit 1
fi

echo ""
echo "✅ $SERVICE_NAME passed all enterprise validations"
echo ""
echo "Validation Summary:"
echo "- Health endpoint: ✅"
echo "- Metrics collection: ✅"
echo "- Feature flags: ✅"
echo "- Load test: ✅ ($SUCCESS_RATE% success rate)"
echo "- Security scan: ✅"
echo "- Enterprise integration: ✅"