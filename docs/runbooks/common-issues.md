---
doc_id: DOC-CONFIG-0085
---

# Common Issues & Solutions

## 🔧 Quick Troubleshooting Guide

This runbook contains solutions for the most frequently encountered issues in the EAFIX trading system. Issues are organized by category and include step-by-step resolution procedures.

## 🚨 Service Health Issues

### Service Won't Start
**Symptoms:**
- Service fails to start via Docker Compose
- Health check endpoint returns 500/503
- Container exits immediately after start

**Diagnosis:**
```bash
# Check container status
docker compose ps

# Check container logs
docker compose logs <service-name> --tail=50

# Check resource availability
df -h  # Disk space
free -h  # Memory
docker system df  # Docker space usage
```

**Solutions:**

**1. Insufficient Resources:**
```bash
# Clean up disk space
docker system prune -af
docker volume prune -f

# Check and free memory
sudo systemctl restart docker  # If safe to do so
```

**2. Configuration Issues:**
```bash
# Validate Docker Compose configuration
docker compose config --quiet

# Check environment variables
docker compose config | grep -A 10 -B 10 environment

# Reset to known good configuration
git checkout HEAD -- deploy/compose/docker-compose.yml
```

**3. Database Connection Issues:**
```bash
# Test database connectivity
psql -h localhost -p 5432 -U eafix -d eafix_prod -c "SELECT 1;"

# Check database container
docker compose logs postgres

# Restart database if needed
docker compose restart postgres
sleep 10  # Wait for startup
```

### High Memory Usage
**Symptoms:**
- Docker containers using >80% of allocated memory
- System becomes unresponsive
- Out of memory errors in logs

**Diagnosis:**
```bash
# Check container memory usage
docker stats --no-stream

# Check system memory
free -h

# Find memory-hungry processes
ps aux --sort=-%mem | head -10
```

**Solutions:**

**1. Restart Memory-Heavy Services:**
```bash
# Identify high-memory containers
docker stats --no-stream | awk 'NR>1 && $7+0 > 80 {print $2}' | while read container; do
    echo "Restarting high-memory container: $container"
    docker restart $container
    sleep 30  # Allow startup
done
```

**2. Tune Memory Limits:**
```bash
# Edit docker-compose.yml to adjust memory limits
# For signal-generator (example):
# mem_limit: 512m  # Increase from 256m
docker compose up -d --no-deps signal-generator
```

## 📊 Data Quality Issues

### Stale Market Data
**Symptoms:**
- Price timestamps are >5 minutes old
- No new price updates for major currency pairs
- Data ingestor showing connectivity errors

**Diagnosis:**
```bash
# Check data freshness
curl http://localhost:8081/api/latest-prices | jq '.[] | {symbol, timestamp, age: (now - (.timestamp | fromdateiso8601))}'

# Check data source connectivity
curl http://localhost:8081/api/data-sources

# Check ingestor logs
docker compose logs data-ingestor --tail=20
```

**Solutions:**

**1. Restart Data Feeds:**
```bash
# Restart data ingestor
docker compose restart data-ingestor

# Wait for reconnection
sleep 30

# Test data flow
curl -X POST http://localhost:8081/test/inject-tick \
  -H "Content-Type: application/json" \
  -d '{"symbol": "EURUSD", "bid": 1.0850, "ask": 1.0852}'
```

**2. Switch to Backup Feed:**
```bash
# If primary feed fails, switch to backup (example configuration)
curl -X POST http://localhost:8081/api/data-sources/switch \
  -H "Content-Type: application/json" \
  -d '{"source": "backup_feed", "reason": "primary_feed_failure"}'
```

### Signal Generation Stopped
**Symptoms:**
- No new signals generated for >15 minutes
- Signal confidence scores all showing 0.0
- Indicator data appears stale

**Diagnosis:**
```bash
# Check recent signals
curl http://localhost:8083/api/signals?limit=5

# Check indicator engine health
curl http://localhost:8082/healthz

# Check data dependency
curl http://localhost:8082/api/indicators/EURUSD | jq '.timestamp'

# Test signal generation
curl -X POST http://localhost:8083/test/generate-signal \
  -H "Content-Type: application/json" \
  -d '{"symbol": "EURUSD", "test_mode": true}'
```

**Solutions:**

**1. Restart Signal Generation Chain:**
```bash
# Restart in dependency order
docker compose restart data-ingestor
sleep 10
docker compose restart indicator-engine
sleep 10  
docker compose restart signal-generator

# Validate chain is working
make smoke
```

**2. Clear Signal Cache:**
```bash
# Clear any corrupted signal cache
redis-cli -h localhost -p 6379 FLUSHDB

# Restart signal generator
docker compose restart signal-generator
```

## 🔄 Performance Issues

### High Latency
**Symptoms:**
- Response times >1 second
- Signal generation taking >10 seconds
- Order execution delays >5 seconds

**Diagnosis:**
```bash
# Test response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8083/api/signals

# Check system load
uptime

# Check database performance
psql -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check container resource usage
docker stats --no-stream
```

**Solutions:**

**1. Database Optimization:**
```bash
# Run database maintenance
psql -h localhost -U eafix -d eafix_prod -c "
    VACUUM ANALYZE;
    REINDEX SYSTEM eafix_prod;
"

# Check for blocking queries
psql -c "SELECT pid, query_start, state, query FROM pg_stat_activity WHERE state = 'active';"
```

**2. Service Optimization:**
```bash
# Restart services to clear memory leaks
docker compose restart indicator-engine signal-generator

# Check for resource constraints
docker compose up -d --scale signal-generator=2  # Scale if needed
```

### Database Connection Pool Exhaustion
**Symptoms:**
- "too many connections" errors
- Services unable to connect to database
- Database queries timing out

**Diagnosis:**
```bash
# Check connection count
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check connection limits
psql -c "SHOW max_connections;"

# Check active queries
psql -c "SELECT pid, usename, application_name, state, query_start FROM pg_stat_activity WHERE state != 'idle';"
```

**Solutions:**

**1. Kill Idle Connections:**
```bash
# Kill idle connections older than 1 hour
psql -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity 
WHERE state = 'idle' 
  AND query_start < now() - interval '1 hour'
  AND pid <> pg_backend_pid();
"
```

**2. Restart Services:**
```bash
# Restart services to reset connection pools
docker compose restart signal-generator risk-manager execution-engine
```

## 🎯 Trading-Specific Issues

### Position Reconciliation Failure
**Symptoms:**
- Position counts don't match between systems
- Unrealized P&L calculations incorrect
- Risk calculations showing wrong exposure

**Diagnosis:**
```bash
# Check position reconciliation status
curl http://localhost:8080/api/reconcile/positions | jq '{
    system_positions: .system_count,
    broker_positions: .broker_count,
    discrepancy: .total_discrepancy_value
}'

# Check recent trades
curl http://localhost:8085/api/executions?limit=10 | jq '.[] | {order_id, status, quantity, timestamp}'

# Check position manager logs
docker compose logs reporter --tail=20
```

**Solutions:**

**1. Manual Reconciliation:**
```bash
# Force full position reconciliation
curl -X POST http://localhost:8080/api/reconcile/force-full \
  -H "Content-Type: application/json" \
  -d '{"reason": "manual_fix", "operator": "'$USER'"}'

# Wait for completion and check results
sleep 30
curl http://localhost:8080/api/reconcile/status
```

**2. Position Reset (EXTREME MEASURE):**
```bash
# Only in case of critical discrepancies
# This should be approved by trading desk first
curl -X POST http://localhost:8080/emergency/reset-positions \
  -H "Content-Type: application/json" \
  -d '{"confirm": true, "reason": "critical_discrepancy", "operator": "'$USER'"}'
```

### Orders Not Executing
**Symptoms:**
- Orders stuck in "pending" state
- High rejection rate from broker
- Execution engine showing connection errors

**Diagnosis:**
```bash
# Check execution engine health
curl http://localhost:8085/healthz

# Check pending orders
curl http://localhost:8085/api/orders?status=pending

# Test broker connectivity
curl http://localhost:8085/test/broker-connectivity

# Check broker API limits
curl http://localhost:8085/api/broker-limits
```

**Solutions:**

**1. Restart Execution Engine:**
```bash
# Restart execution engine
docker compose restart execution-engine

# Wait for reconnection
sleep 30

# Test with small order
curl -X POST http://localhost:8085/test/dry-run-order \
  -H "Content-Type: application/json" \
  -d '{"symbol": "EURUSD", "quantity": 0.01, "side": "buy"}'
```

**2. Check Account Status:**
```bash
# Verify account balance and permissions
curl http://localhost:8085/api/account-status

# Check trading permissions
curl http://localhost:8085/api/trading-permissions
```

### Risk Manager Rejecting All Signals
**Symptoms:**
- 100% signal rejection rate
- Risk scores all showing maximum values
- Position sizing returning zero

**Diagnosis:**
```bash
# Check risk limits
curl http://localhost:8084/api/risk-limits

# Check account balance
curl http://localhost:8084/api/account-status

# Test risk validation
curl -X POST http://localhost:8084/test/validate-signal \
  -H "Content-Type: application/json" \
  -d '{"signal_id": "test", "symbol": "EURUSD", "confidence": 0.8, "position_size": 0.01}'

# Check recent risk assessments
curl http://localhost:8084/api/risk-assessments?limit=5
```

**Solutions:**

**1. Reset Risk Parameters:**
```bash
# Check if risk limits are too restrictive
curl http://localhost:8084/api/risk-limits | jq '{
    max_daily_loss: .account_limits.max_daily_loss,
    current_daily_loss: .current_usage.daily_loss,
    remaining: (.account_limits.max_daily_loss - .current_usage.daily_loss)
}'

# If needed, adjust risk parameters (requires approval)
curl -X POST http://localhost:8084/api/risk-limits/adjust \
  -H "Content-Type: application/json" \
  -d '{
    "max_daily_loss": 1000,
    "reason": "conservative_limits_causing_rejections",
    "operator": "'$USER'"
  }'
```

**2. Check Data Quality:**
```bash
# Verify position data accuracy
curl http://localhost:8084/api/positions/validate

# Refresh account balance data
curl -X POST http://localhost:8084/api/account/refresh
```

## 🌐 Network & Connectivity Issues

### Redis Connection Failures
**Symptoms:**
- Services unable to publish/subscribe to messages
- Message queue depths showing zero
- Event-driven communication broken

**Diagnosis:**
```bash
# Test Redis connectivity
redis-cli -h localhost -p 6379 ping

# Check Redis logs
docker compose logs redis --tail=20

# Check message queues
redis-cli -h localhost -p 6379 info keyspace

# Test pub/sub
redis-cli -h localhost -p 6379 publish test_channel "test_message"
```

**Solutions:**

**1. Restart Redis:**
```bash
# Restart Redis container
docker compose restart redis

# Wait for startup
sleep 10

# Test connectivity
redis-cli -h localhost -p 6379 ping

# Restart dependent services
docker compose restart signal-generator execution-engine reporter
```

**2. Clear Redis Data (if corrupted):**
```bash
# Flush all Redis data (CAUTION: loses all cached data)
redis-cli -h localhost -p 6379 FLUSHALL

# Restart all services to repopulate
docker compose restart
```

### External API Connectivity Issues
**Symptoms:**
- Broker API calls failing
- Market data feed interruptions
- Third-party service timeouts

**Diagnosis:**
```bash
# Test external connectivity
curl -I https://api.broker.com/health

# Check DNS resolution
nslookup api.broker.com

# Test from within container
docker exec -it eafix-execution-engine curl -I https://api.broker.com/health

# Check firewall/proxy settings
curl -v --proxy http://proxy.company.com:8080 https://api.broker.com/health
```

**Solutions:**

**1. Network Troubleshooting:**
```bash
# Test basic connectivity
ping api.broker.com

# Check routing
traceroute api.broker.com

# Test different DNS servers
nslookup api.broker.com 8.8.8.8
```

**2. Proxy Configuration:**
```bash
# If behind corporate proxy, update service configuration
# Add to docker-compose.yml environment:
# HTTP_PROXY: http://proxy.company.com:8080
# HTTPS_PROXY: http://proxy.company.com:8080
# NO_PROXY: localhost,127.0.0.1,redis,postgres

docker compose up -d --no-deps execution-engine
```

## 📝 Configuration Issues

### Environment Variable Problems
**Symptoms:**
- Services failing with "configuration missing" errors
- Database connection strings incorrect
- API keys not found

**Diagnosis:**
```bash
# Check environment variables in running containers
docker exec -it eafix-signal-generator env | grep -E "(REDIS|DB|API)"

# Validate docker-compose environment section
docker compose config | grep -A 20 environment

# Check .env files
ls -la .env*
cat .env 2>/dev/null || echo "No .env file found"
```

**Solutions:**

**1. Recreate Environment Configuration:**
```bash
# Create missing .env file
cat > .env << EOF
REDIS_URL=redis://redis:6379
DATABASE_URL=postgresql://eafix:password@postgres:5432/eafix_prod
LOG_LEVEL=INFO
EOF

# Restart services to pick up changes
docker compose up -d --no-deps signal-generator
```

**2. Reset to Default Configuration:**
```bash
# Reset configuration to repository defaults
git checkout HEAD -- deploy/compose/.env*
git checkout HEAD -- deploy/compose/docker-compose.yml

# Restart all services
docker compose down && docker compose up -d
```

### Docker Compose Issues
**Symptoms:**
- Services unable to communicate with each other
- Port conflicts
- Volume mount failures

**Diagnosis:**
```bash
# Validate compose file
docker compose config --quiet

# Check port conflicts
netstat -tulpn | grep :8080

# Check volume mounts
docker compose ps --services --filter "status=exited"
```

**Solutions:**

**1. Network Issues:**
```bash
# Recreate Docker network
docker compose down
docker network prune -f
docker compose up -d
```

**2. Port Conflicts:**
```bash
# Find and kill processes using conflicting ports
sudo lsof -ti:8080 | xargs -r kill -9

# Or change ports in docker-compose.yml
# ports:
#   - "8090:8080"  # Change external port
```

## 🔧 Quick Reference Commands

### Health Check All Services
```bash
#!/bin/bash
for port in 8080 8081 8082 8083 8084 8085 8086 8087 8088; do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/healthz)
    if [ "$status" = "200" ]; then
        echo "Port $port: ✅ Healthy"
    else
        echo "Port $port: ❌ Unhealthy ($status)"
    fi
done
```

### Emergency System Restart
```bash
#!/bin/bash
echo "🚨 Emergency system restart initiated"
docker compose down
sleep 10
docker compose up -d
sleep 30
make smoke
echo "✅ Emergency restart completed"
```

### Quick Performance Check
```bash
#!/bin/bash
echo "=== Quick Performance Check ==="
echo "System Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Memory: $(free -h | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo "Disk: $(df -h / | awk 'NR==2{print $5}')"
echo "Docker Stats:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}"
```

## 📞 When to Escalate

### Immediate Escalation (P0)
- Complete system outage during market hours
- Data corruption affecting positions
- Security breach indicators
- Multiple cascading failures

### 15-Minute Escalation (P1)
- Single service outage affecting trading
- Performance degradation >5s latency
- Position reconciliation failures
- Database connectivity issues

### 1-Hour Escalation (P2)
- Non-critical service outages
- Performance issues 1-5s latency
- Data quality issues not affecting trading
- Monitoring system failures

### Contact Information
- **On-Call Engineer**: Check PagerDuty or Slack
- **Trading Desk**: +1-555-0200 (market hours only)
- **Platform Engineering**: #eafix-dev Slack channel
- **Emergency**: Follow escalation procedures in escalation-procedures.md

---

**Document Owner**: Platform Engineering Team  
**Last Updated**: December 2024  
**Next Review**: January 2025  
**Contributors**: All team members based on incident learnings