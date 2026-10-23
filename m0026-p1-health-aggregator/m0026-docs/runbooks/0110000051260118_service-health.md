---
doc_id: DOC-CONFIG-0091
---

# Service Health & Monitoring Runbook

## 🏥 Health Check Overview

This runbook provides procedures for monitoring, diagnosing, and maintaining the health of all EAFIX trading system services.

## 🔍 Service Health Checks

### Automated Health Monitoring
```bash
# Complete system health check
make smoke

# Individual service health checks
curl http://localhost:8080/healthz | jq .  # GUI Gateway
curl http://localhost:8081/healthz | jq .  # Data Ingestor
curl http://localhost:8082/healthz | jq .  # Indicator Engine
curl http://localhost:8083/healthz | jq .  # Signal Generator
curl http://localhost:8084/healthz | jq .  # Risk Manager
curl http://localhost:8085/healthz | jq .  # Execution Engine
curl http://localhost:8086/healthz | jq .  # Calendar Ingestor
curl http://localhost:8087/healthz | jq .  # Reentry Matrix Service
curl http://localhost:8088/healthz | jq .  # Reporter
```

### Infrastructure Health Checks
```bash
# Redis (Message Bus)
redis-cli -h localhost -p 6379 ping
redis-cli -h localhost -p 6379 info replication

# PostgreSQL (Database)
psql -h localhost -p 5432 -U eafix -d eafix_prod -c "SELECT version();"
psql -h localhost -p 5432 -U eafix -d eafix_prod -c "SELECT count(*) FROM pg_stat_activity;"

# Docker Container Status
docker compose -f deploy/compose/docker-compose.yml ps
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```

## 📊 Monitoring Dashboard Access

### Grafana Dashboards
- **URL**: http://localhost:3000
- **Credentials**: admin/admin (default)
- **Key Dashboards**:
  - EAFIX System Overview
  - Trading Performance Metrics
  - Service Health Status
  - Infrastructure Monitoring

### Prometheus Metrics
- **URL**: http://localhost:9090
- **Key Metrics**:
  - `up{job="eafix-services"}` - Service availability
  - `http_requests_duration_seconds` - Request latency
  - `trading_signals_generated_total` - Signal generation rate
  - `trading_orders_executed_total` - Order execution rate

## 🚨 Alert Definitions & Thresholds

### Critical Alerts (P0)
```yaml
# Service Down
- alert: ServiceDown
  expr: up{job="eafix-services"} == 0
  for: 30s
  severity: critical

# High Error Rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 2m
  severity: critical

# Trading Path Broken
- alert: TradingPathBroken
  expr: rate(trading_signals_generated_total[5m]) == 0
  for: 5m
  severity: critical
```

### Warning Alerts (P1)
```yaml
# High Latency
- alert: HighLatency
  expr: histogram_quantile(0.95, http_request_duration_seconds) > 1.0
  for: 5m
  severity: warning

# High Memory Usage
- alert: HighMemoryUsage
  expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8
  for: 10m
  severity: warning
```

## 🔧 Service-Specific Health Procedures

### Data Ingestor (Port 8081)
**Health Indicators:**
- Recent price tick timestamps
- Data feed connectivity
- Processing latency

**Health Check Commands:**
```bash
# Check recent data ingestion
curl http://localhost:8081/api/latest-prices | jq '.[] | {symbol, timestamp, age: (now - (.timestamp | fromdateiso8601))}'

# Check data processing rate
curl http://localhost:8081/metrics | grep "price_ticks_processed_total"

# Check data feed connectivity
curl http://localhost:8081/api/feed-status

# Manual data injection test
curl -X POST http://localhost:8081/test/inject-tick \
  -H "Content-Type: application/json" \
  -d '{"symbol": "EURUSD", "bid": 1.0850, "ask": 1.0852, "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'
```

**Troubleshooting:**
- **Stale Data**: Check external data feed connectivity
- **High Latency**: Check Redis connection and processing queue
- **Missing Symbols**: Verify symbol configuration and data subscriptions

### Indicator Engine (Port 8082)
**Health Indicators:**
- Indicator calculation latency
- Data dependency availability
- Calculation accuracy

**Health Check Commands:**
```bash
# Check recent indicator calculations
curl http://localhost:8082/api/indicators/EURUSD | jq '.timestamp, .indicators | keys'

# Check calculation performance
curl http://localhost:8082/metrics | grep "indicator_calculation_duration_seconds"

# Test indicator calculation
curl -X POST http://localhost:8082/test/calculate \
  -H "Content-Type: application/json" \
  -d '{"symbol": "EURUSD", "indicators": ["sma_20", "rsi_14", "macd"]}'
```

**Troubleshooting:**
- **Calculation Errors**: Check input data quality and mathematical libraries
- **High Memory Usage**: Review indicator history retention and caching
- **Slow Calculations**: Optimize algorithms or increase processing power

### Signal Generator (Port 8083)
**Health Indicators:**
- Signal generation rate
- Signal confidence distribution
- Signal accuracy metrics

**Health Check Commands:**
```bash
# Check recent signals
curl http://localhost:8083/api/signals?limit=5 | jq '.[] | {id, symbol, confidence, timestamp}'

# Check signal generation rate
curl http://localhost:8083/metrics | grep "signals_generated_total"

# Test signal generation
curl -X POST http://localhost:8083/test/generate \
  -H "Content-Type: application/json" \
  -d '{"symbol": "EURUSD", "test_mode": true}'

# Check signal accuracy
curl http://localhost:8083/api/metrics/accuracy?period=24h
```

**Troubleshooting:**
- **No Signals**: Check indicator data availability and signal criteria
- **Low Confidence**: Review signal algorithms and market conditions
- **Poor Accuracy**: Validate backtesting and adjust parameters

### Risk Manager (Port 8084)
**Health Indicators:**
- Risk validation response time
- Position limit compliance
- Account balance accuracy

**Health Check Commands:**
```bash
# Check risk validation performance
curl http://localhost:8084/metrics | grep "risk_validation_duration_seconds"

# Check current risk metrics
curl http://localhost:8084/api/risk-metrics/current

# Test risk validation
curl -X POST http://localhost:8084/test/validate \
  -H "Content-Type: application/json" \
  -d '{"signal_id": "test", "symbol": "EURUSD", "confidence": 0.8, "position_size": 0.1}'

# Check risk limits
curl http://localhost:8084/api/risk-limits
```

**Troubleshooting:**
- **All Signals Rejected**: Check risk limits and account balance
- **Slow Validation**: Review risk calculation algorithms
- **Incorrect Limits**: Validate risk configuration and position data

### Execution Engine (Port 8085)
**Health Indicators:**
- Order execution latency
- Fill rate percentage
- Broker connectivity

**Health Check Commands:**
```bash
# Check execution performance
curl http://localhost:8085/metrics | grep "order_execution_duration_seconds"

# Check recent executions
curl http://localhost:8085/api/executions?limit=5 | jq '.[] | {order_id, status, execution_time}'

# Test broker connectivity
curl http://localhost:8085/test/broker-connectivity

# Check fill rates
curl http://localhost:8085/api/metrics/fill-rate?period=1h
```

**Troubleshooting:**
- **Slow Execution**: Check broker API latency and network connectivity
- **Low Fill Rate**: Review order types and market conditions
- **Connection Issues**: Validate broker credentials and API endpoints

## 📈 Performance Monitoring

### Key Performance Indicators (KPIs)
```bash
# End-to-end trading latency (target: <500ms)
python scripts/performance/e2e-latency.py --duration=300

# Signal generation rate (target: >10/hour during active markets)
curl http://localhost:8083/metrics | grep "signals_generated_total" | awk '{print $2}'

# Order execution success rate (target: >95%)
python scripts/performance/execution-success-rate.py --period=24h

# System uptime (target: >99.9%)
python scripts/monitoring/uptime-calculator.py --period=30d
```

### Resource Utilization Monitoring
```bash
# CPU usage per service
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}"

# Memory usage per service
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Disk usage
df -h

# Network I/O
docker stats --no-stream --format "table {{.Container}}\t{{.NetIO}}"
```

### Database Performance Monitoring
```bash
# Connection count
psql -c "SELECT count(*) as connections FROM pg_stat_activity;"

# Slow queries
psql -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Database size
psql -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) as size FROM pg_database;"

# Lock monitoring
psql -c "SELECT * FROM pg_locks WHERE NOT granted;"
```

## 🔄 Automated Remediation

### Auto-Restart Procedures
```bash
#!/bin/bash
# automated-service-restart.sh

SERVICE_NAME=$1
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:808x/healthz > /dev/null 2>&1; then
        echo "Service $SERVICE_NAME is healthy"
        exit 0
    else
        echo "Service $SERVICE_NAME unhealthy, restarting..."
        docker compose restart $SERVICE_NAME
        sleep 30
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

echo "Service $SERVICE_NAME failed to recover after $MAX_RETRIES attempts"
exit 1
```

### Circuit Breaker Monitoring
```bash
# Check circuit breaker states
curl http://localhost:8080/api/circuit-breakers | jq '.[] | {service, state, failure_count}'

# Reset circuit breaker (manual intervention)
curl -X POST http://localhost:8080/api/circuit-breakers/reset \
  -H "Content-Type: application/json" \
  -d '{"service": "risk-manager"}'
```

## 📊 Health Reporting

### Daily Health Report Generation
```bash
#!/bin/bash
# generate-daily-health-report.sh

DATE=$(date +%Y-%m-%d)
REPORT_FILE="health-report-$DATE.json"

{
  echo "{"
  echo "  \"date\": \"$DATE\","
  echo "  \"services\": ["
  
  # Check each service
  for port in 8080 8081 8082 8083 8084 8085 8086 8087 8088; do
    response=$(curl -s http://localhost:$port/healthz)
    echo "    $response,"
  done
  
  echo "  ],"
  echo "  \"infrastructure\": {"
  echo "    \"redis\": \"$(redis-cli ping 2>/dev/null || echo 'DOWN')\","
  echo "    \"postgres\": \"$(psql -c 'SELECT 1' 2>/dev/null && echo 'UP' || echo 'DOWN')\""
  echo "  },"
  echo "  \"performance_metrics\": {"
  echo "    \"avg_latency\": \"$(python scripts/performance/avg-latency.py)\","
  echo "    \"success_rate\": \"$(python scripts/performance/success-rate.py)\""
  echo "  }"
  echo "}"
} > $REPORT_FILE

echo "Health report generated: $REPORT_FILE"
```

### Weekly Health Summary
```bash
# Generate weekly summary
python scripts/reporting/weekly-health-summary.py --week $(date +%Y-W%U)

# Send summary email
python scripts/notifications/send-health-summary.py --recipients ops-team@company.com
```

## 🔍 Diagnostic Tools

### Service Dependency Graph
```bash
# Generate service dependency visualization
python scripts/tools/service-dependency-graph.py --output=deps.png

# Check service communication patterns
python scripts/tools/service-communication-analyzer.py --period=24h
```

### Log Analysis Tools
```bash
# Error pattern analysis
python scripts/logs/error-pattern-analyzer.py --since=24h

# Performance bottleneck detection
python scripts/logs/bottleneck-detector.py --service=all --period=1h

# Anomaly detection in logs
python scripts/logs/anomaly-detector.py --baseline=7d --check=1h
```

### Configuration Drift Detection
```bash
# Check for configuration changes
python scripts/tools/config-drift-detector.py --baseline=production

# Validate service configurations
python scripts/tools/config-validator.py --environment=production
```

## 📋 Health Check Schedules

### Continuous Monitoring (Real-time)
- Service health endpoints (every 30 seconds)
- Infrastructure health (every 1 minute)
- Performance metrics (every 5 minutes)
- Alert rule evaluation (every 1 minute)

### Periodic Checks (Scheduled)
- **Every 5 minutes**: Trading path validation
- **Every 15 minutes**: Position reconciliation
- **Every 1 hour**: Performance benchmark tests
- **Every 4 hours**: Configuration drift detection
- **Daily**: Comprehensive health report
- **Weekly**: Capacity planning review
- **Monthly**: Service dependency audit

### Game Day Exercises
- **Monthly**: Service failover testing
- **Quarterly**: Disaster recovery simulation
- **Semi-annually**: Capacity stress testing
- **Annually**: Business continuity testing

## 🚀 Optimization Recommendations

### Performance Tuning
```bash
# Database query optimization
python scripts/optimization/db-query-analyzer.py --slow-threshold=1000ms

# Service resource optimization
python scripts/optimization/resource-optimizer.py --target-utilization=70

# Cache hit rate optimization
python scripts/optimization/cache-optimizer.py --service=all
```

### Capacity Planning
```bash
# Resource usage trending
python scripts/capacity/resource-trends.py --period=30d

# Growth projection
python scripts/capacity/growth-projector.py --horizon=90d

# Scaling recommendations
python scripts/capacity/scaling-advisor.py --service=signal-generator
```

---

**Document Owner**: Platform Engineering Team  
**Last Updated**: December 2024  
**Next Review**: January 2025  
**On-Call Contact**: [PagerDuty Integration]