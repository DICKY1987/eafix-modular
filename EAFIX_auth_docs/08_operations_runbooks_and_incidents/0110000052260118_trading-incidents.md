---
doc_id: DOC-CONFIG-0092
---

# Trading-Specific Incident Response

## 🎯 Trading System Critical Path

Understanding the critical trading path is essential for proper incident response:

```
Market Data → Data Ingestor → Indicator Engine → Signal Generator → Risk Manager → Execution Engine → Broker
```

Any failure in this path during market hours is considered **P0** and requires immediate response.

## 🚨 Trading Emergency Procedures

### Immediate Trading Halt
```bash
# EMERGENCY: Stop all trading immediately
curl -X POST http://localhost:8080/emergency/stop-trading \
  -H "Content-Type: application/json" \
  -d '{"reason": "incident_response", "operator": "'$USER'"}'

# Verify trading stopped
curl http://localhost:8080/api/trading-status
```

### Position Protection
```bash
# Check all open positions
curl http://localhost:8080/api/positions?status=open | jq '.[] | {symbol, quantity, unrealized_pnl, entry_price}'

# Emergency close all positions (EXTREME MEASURE)
curl -X POST http://localhost:8080/emergency/close-all-positions \
  -H "Content-Type: application/json" \
  -d '{"reason": "risk_management", "operator": "'$USER'"}'

# Set emergency stop losses (safer approach)
curl -X POST http://localhost:8080/emergency/set-stop-losses \
  -H "Content-Type: application/json" \
  -d '{"percentage": 2.0, "operator": "'$USER'"}'
```

## 📊 Trading-Specific Incident Types

### Signal Generation Failure

**Symptoms:**
- No new signals for >15 minutes during active market
- Signal confidence scores all 0.0
- Signal generation latency >10 seconds

**Immediate Response:**
```bash
# 1. Check signal generator health
curl http://localhost:8083/healthz

# 2. Check recent signals
curl http://localhost:8083/api/signals?limit=10 | jq '.[] | {id, symbol, confidence, timestamp}'

# 3. Check indicator engine dependency
curl http://localhost:8082/healthz

# 4. Manual signal generation test
curl -X POST http://localhost:8083/test/generate-signal \
  -H "Content-Type: application/json" \
  -d '{"symbol": "EURUSD", "test_mode": true}'
```

**Recovery Actions:**
1. Restart signal-generator service
2. Verify indicator data flow
3. Check for configuration changes
4. Validate signal generation algorithms

### Market Data Feed Issues

**Symptoms:**
- Stale price data (>30 seconds old)
- Missing price updates for major pairs
- Price data with impossible values

**Immediate Response:**
```bash
# 1. Check data ingestor health
curl http://localhost:8081/healthz

# 2. Check recent price data
curl http://localhost:8081/api/latest-prices | jq '.[] | {symbol, bid, ask, timestamp}'

# 3. Check data age
curl http://localhost:8081/api/data-freshness

# 4. Test manual price injection
curl -X POST http://localhost:8081/test/inject-price \
  -H "Content-Type: application/json" \
  -d '{"symbol": "EURUSD", "bid": 1.0850, "ask": 1.0852}'
```

**Recovery Actions:**
1. Restart data-ingestor service
2. Check external data feed connectivity
3. Validate price data sources
4. Switch to backup data feed if available

### Order Execution Failures

**Symptoms:**
- Orders stuck in pending state
- High execution latency (>5 seconds)
- Execution rejections increasing

**Immediate Response:**
```bash
# 1. Check execution engine health
curl http://localhost:8085/healthz

# 2. Check pending orders
curl http://localhost:8085/api/orders?status=pending

# 3. Check recent execution results
curl http://localhost:8085/api/executions?limit=10 | jq '.[] | {order_id, status, execution_time}'

# 4. Test broker connectivity
curl http://localhost:8085/test/broker-connectivity
```

**Recovery Actions:**
1. Restart execution-engine service
2. Check broker API connectivity
3. Validate order routing configuration
4. Check account margin and permissions

### Risk Management System Failure

**Symptoms:**
- All signals being rejected
- Position size calculations showing 0
- Risk scores not updating

**Immediate Response:**
```bash
# 1. Check risk manager health
curl http://localhost:8084/healthz

# 2. Check recent risk assessments
curl http://localhost:8084/api/risk-assessments?limit=10

# 3. Test risk validation
curl -X POST http://localhost:8084/test/validate-signal \
  -H "Content-Type: application/json" \
  -d '{"signal_id": "test_123", "symbol": "EURUSD", "confidence": 0.8}'

# 4. Check risk limits configuration
curl http://localhost:8084/api/risk-limits
```

**Recovery Actions:**
1. Restart risk-manager service
2. Validate risk configuration
3. Check position reconciliation
4. Verify account balance data

## 🔍 Trading Data Validation

### Position Reconciliation
```bash
# 1. Get system positions
curl http://localhost:8080/api/positions > system_positions.json

# 2. Get broker positions (if available)
curl http://localhost:8085/api/broker-positions > broker_positions.json

# 3. Compare positions
python scripts/reconciliation/compare_positions.py system_positions.json broker_positions.json

# 4. Manual reconciliation report
curl -X POST http://localhost:8080/api/reconcile/generate-report
```

### Signal Quality Validation
```bash
# 1. Check signal accuracy metrics
curl http://localhost:8083/api/metrics/signal-accuracy

# 2. Validate recent signal outcomes
curl http://localhost:8083/api/signals/validate-recent

# 3. Check signal distribution
curl http://localhost:8083/api/metrics/signal-distribution | jq '.'
```

### Risk Metrics Validation
```bash
# 1. Current risk exposure
curl http://localhost:8084/api/risk-metrics/current

# 2. Risk limit utilization
curl http://localhost:8084/api/risk-metrics/utilization

# 3. Value at Risk calculation
curl http://localhost:8084/api/risk-metrics/var
```

## 📈 Market Hours Considerations

### Pre-Market (6:00-9:30 AM EST)
**Priorities:**
1. System health verification
2. Data feed connectivity
3. Signal generation testing
4. Risk parameter validation

**Procedures:**
```bash
# Pre-market checklist
make smoke
make contracts-validate
curl http://localhost:8080/api/pre-market-checklist
```

### Market Open (9:30 AM - 4:00 PM EST)
**Priorities:**
1. Immediate incident response (<5 minutes)
2. Trading continuity maintenance
3. Position protection
4. Risk monitoring

**Critical Response Times:**
- Signal generation: <1 minute recovery
- Order execution: <2 minute recovery
- Market data: <30 second recovery

### After Hours (4:00 PM - 6:00 AM EST)
**Priorities:**
1. Position reconciliation
2. System maintenance windows
3. Incident post-mortem
4. Preventive maintenance

## 🎯 Trading Performance Metrics

### Latency Monitoring
```bash
# End-to-end latency test
python scripts/performance/trading-latency.py --duration=60

# Service-specific latency
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8083/api/signals/latest
```

### Execution Quality Metrics
```bash
# Slippage analysis
curl http://localhost:8085/api/metrics/slippage?period=1h

# Fill rate analysis
curl http://localhost:8085/api/metrics/fill-rate?period=1h

# Execution time distribution
curl http://localhost:8085/api/metrics/execution-times?period=1h
```

### Signal Quality Metrics
```bash
# Signal generation rate
curl http://localhost:8083/api/metrics/signal-rate?period=1h

# Signal confidence distribution
curl http://localhost:8083/api/metrics/confidence-distribution?period=1h

# Signal accuracy tracking
curl http://localhost:8083/api/metrics/accuracy?period=24h
```

## 🛡️ Risk Management During Incidents

### Emergency Risk Controls
```bash
# Reduce position sizes by 50%
curl -X POST http://localhost:8084/emergency/reduce-position-sizes \
  -d '{"reduction_factor": 0.5, "reason": "incident_response"}'

# Tighten risk limits temporarily
curl -X POST http://localhost:8084/emergency/tighten-limits \
  -d '{"factor": 0.7, "duration_minutes": 60}'

# Stop new position opening
curl -X POST http://localhost:8084/emergency/stop-new-positions \
  -d '{"reason": "system_instability"}'
```

### Position Monitoring
```bash
# Monitor position P&L in real-time
while true; do
  curl -s http://localhost:8080/api/positions/summary | jq '.total_unrealized_pnl'
  sleep 10
done

# Alert on large position moves
python scripts/monitoring/position-alerts.py --threshold=1000
```

## 📞 Trading Desk Communication

### Critical Incident Notification
**Immediate Phone Call Required For:**
- System outage during market hours
- Position reconciliation discrepancies >$10k
- Risk management system failures
- Order execution issues affecting >$50k

**Phone Call Script:**
```
"This is [Your Name] from Platform Engineering. 
We have a [P0/P1] incident affecting [System Component].
Trading impact: [Description]
Current status: [Status]
Estimated resolution: [Time]
Actions needed from trading desk: [Actions]"
```

### Regular Updates During Incidents
- Every 15 minutes for P0 incidents
- Every 30 minutes for P1 incidents
- Include: Status, Impact, ETA, Actions needed

### Resolution Confirmation
- Confirm trading operations restored
- Verify position integrity
- Get approval to resume normal operations

## 📋 Trading Incident Checklist

### During Market Hours
- [ ] Stop trading if critical path affected
- [ ] Notify trading desk within 5 minutes
- [ ] Protect open positions
- [ ] Identify root cause
- [ ] Implement temporary fix
- [ ] Resume trading operations
- [ ] Monitor for stability
- [ ] Position reconciliation
- [ ] Incident documentation

### After Market Hours
- [ ] Assess impact on next session
- [ ] Implement permanent fix
- [ ] System validation
- [ ] Update monitoring
- [ ] Incident post-mortem
- [ ] Runbook updates

## 🔧 Recovery Validation

### Trading System Recovery Checklist
```bash
# 1. Service health
make smoke

# 2. Data flow validation
curl http://localhost:8081/api/latest-prices | jq '.[] | .timestamp' | head -5

# 3. Signal generation
curl http://localhost:8083/api/signals?limit=3 | jq '.[] | {timestamp, symbol, confidence}'

# 4. Risk validation
curl -X POST http://localhost:8084/test/validate-test-signal

# 5. Execution test
curl -X POST http://localhost:8085/test/dry-run-order

# 6. End-to-end test
python scripts/e2e/trading-flow-test.py --duration=60
```

### Performance Validation
```bash
# Latency test
python scripts/performance/latency-benchmark.py --target-latency=500ms

# Throughput test  
python scripts/performance/throughput-test.py --target-tps=100

# Load test
python scripts/load-test/trading-load.py --duration=300 --ramp-up=60
```

---

**Document Owner**: Trading Operations Team  
**Technical Owner**: Platform Engineering Team  
**Last Updated**: December 2024  
**Next Review**: January 2025