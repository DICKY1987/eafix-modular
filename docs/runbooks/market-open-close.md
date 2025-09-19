# Market Open/Close Procedures

## 🌅 Pre-Market Preparation (5:00 - 9:30 AM EST)

### Daily System Health Check
```bash
# Complete system validation before market open
echo "=== Pre-Market System Validation ===" | tee pre_market_$(date +%Y%m%d).log

# 1. Core system health
make smoke 2>&1 | tee -a pre_market_$(date +%Y%m%d).log

# 2. Service connectivity
for port in 8080 8081 8082 8083 8084 8085 8086 8087 8088; do
    echo "Testing port $port..." | tee -a pre_market_$(date +%Y%m%d).log
    curl -s -o /dev/null -w "Port $port: %{http_code} (%{time_total}s)\n" http://localhost:$port/healthz 2>&1 | tee -a pre_market_$(date +%Y%m%d).log
done

# 3. Contract validation
make contracts-validate 2>&1 | tee -a pre_market_$(date +%Y%m%d).log

# 4. Database connectivity and performance
echo "Database validation:" | tee -a pre_market_$(date +%Y%m%d).log
psql -h localhost -U eafix -d eafix_prod -c "
    SELECT 
        'Connection OK' as status,
        version() as version,
        now() as timestamp;
" 2>&1 | tee -a pre_market_$(date +%Y%m%d).log
```

### Market Data Feed Validation
```bash
# Verify market data connectivity
curl http://localhost:8081/api/data-sources | jq '.[] | {source, status, last_update}' | tee -a pre_market_$(date +%Y%m%d).log

# Test major currency pairs availability
for symbol in EURUSD GBPUSD USDJPY AUDUSD USDCAD; do
    echo "Testing $symbol data feed..." | tee -a pre_market_$(date +%Y%m%d).log
    curl -s "http://localhost:8081/api/latest-prices?symbol=$symbol" | jq -r ".timestamp // \"No data\"" | tee -a pre_market_$(date +%Y%m%d).log
done

# Verify data freshness (should be within last 5 minutes)
python -c "
import json, requests, datetime
response = requests.get('http://localhost:8081/api/latest-prices')
if response.status_code == 200:
    data = response.json()
    for tick in data[:5]:  # Check first 5 symbols
        timestamp = datetime.datetime.fromisoformat(tick['timestamp'].replace('Z', '+00:00'))
        age_minutes = (datetime.datetime.now(datetime.timezone.utc) - timestamp).total_seconds() / 60
        print(f'{tick[\"symbol\"]}: {age_minutes:.1f} minutes old')
        if age_minutes > 5:
            print(f'WARNING: {tick[\"symbol\"]} data is stale!')
" 2>&1 | tee -a pre_market_$(date +%Y%m%d).log
```

### Trading System Configuration
```bash
# Verify risk parameters are set for the day
curl http://localhost:8084/api/risk-limits | jq '{
    max_daily_loss: .account_limits.max_daily_loss,
    max_position_size: .account_limits.max_position_size,
    max_correlation_exposure: .correlation_limits.max_correlation_exposure
}' | tee -a pre_market_$(date +%Y%m%d).log

# Check calendar events for today
curl "http://localhost:8086/api/events?date=$(date +%Y-%m-%d)&impact=high" | jq '.events[] | {time: .scheduled_time, currency: .currency, title: .title}' | tee -a pre_market_$(date +%Y%m%d).log

# Validate signal generation is ready
curl -X POST http://localhost:8083/test/generate-signal \
    -H "Content-Type: application/json" \
    -d '{"symbol": "EURUSD", "test_mode": true}' | jq '.status' | tee -a pre_market_$(date +%Y%m%d).log
```

### Pre-Market Checklist
- [ ] All services healthy (9/9 services responding)
- [ ] Database connectivity confirmed
- [ ] Market data feeds active and fresh (<5 min old)
- [ ] Risk parameters configured for the day
- [ ] High-impact calendar events reviewed
- [ ] Signal generation tested successfully
- [ ] Trading desk notified of system status
- [ ] Backup systems validated
- [ ] On-call engineer identified and available

## 🔔 Market Open (9:30 AM EST)

### Market Open Validation (First 15 minutes)
```bash
# Monitor initial market activity
echo "=== Market Open Monitoring ===" | tee market_open_$(date +%Y%m%d_%H%M).log

# 1. Verify increased data flow
echo "Data ingestion rate check:" | tee -a market_open_$(date +%Y%m%d_%H%M).log
curl http://localhost:8081/metrics | grep "price_ticks_processed_total" | tee -a market_open_$(date +%Y%m%d_%H%M).log

# 2. Monitor signal generation
echo "Signal generation check:" | tee -a market_open_$(date +%Y%m%d_%H%M).log
curl http://localhost:8083/api/signals?limit=5 | jq '.[] | {timestamp, symbol, confidence}' | tee -a market_open_$(date +%Y%m%d_%H%M).log

# 3. Check execution engine readiness
echo "Execution engine status:" | tee -a market_open_$(date +%Y%m%d_%H%M).log
curl http://localhost:8085/test/broker-connectivity | jq '.status' | tee -a market_open_$(date +%Y%m%d_%H%M).log

# 4. Monitor system performance
echo "System performance:" | tee -a market_open_$(date +%Y%m%d_%H%M).log
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | tee -a market_open_$(date +%Y%m%d_%H%M).log
```

### Real-Time Monitoring Setup
```bash
# Start real-time monitoring dashboard (run in background)
python scripts/monitoring/market-hours-monitor.py --start-time="09:30" --log-file="market_activity_$(date +%Y%m%d).log" &

# Monitor key trading metrics
watch -n 30 '
echo "=== $(date) ==="
echo "Active Signals: $(curl -s http://localhost:8083/api/signals?status=active | jq length)"
echo "Open Positions: $(curl -s http://localhost:8080/api/positions?status=open | jq length)"
echo "System Health: $(curl -s http://localhost:8080/health | jq -r .status)"
echo "Last Data Update: $(curl -s http://localhost:8081/api/latest-prices | jq -r ".[0].timestamp")"
'
```

## 📈 Market Hours Monitoring (9:30 AM - 4:00 PM EST)

### Continuous Health Monitoring
```bash
# Automated monitoring script (run continuously during market hours)
#!/bin/bash
# market-hours-monitoring.sh

LOG_FILE="market_hours_$(date +%Y%m%d).log"
ALERT_THRESHOLD_LATENCY=1000  # milliseconds
ALERT_THRESHOLD_ERROR_RATE=0.05  # 5%

while [ "$(date +%H%M)" -lt "1600" ]; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Check service health
    UNHEALTHY_SERVICES=0
    for port in 8080 8081 8082 8083 8084 8085 8086 8087 8088; do
        if ! curl -s -f "http://localhost:$port/healthz" > /dev/null; then
            echo "$TIMESTAMP WARNING: Service on port $port is unhealthy" | tee -a $LOG_FILE
            UNHEALTHY_SERVICES=$((UNHEALTHY_SERVICES + 1))
        fi
    done
    
    # Check trading metrics
    SIGNAL_COUNT=$(curl -s "http://localhost:8083/api/signals?since=10m" | jq length)
    if [ "$SIGNAL_COUNT" -eq 0 ]; then
        echo "$TIMESTAMP WARNING: No signals generated in last 10 minutes" | tee -a $LOG_FILE
    fi
    
    # Check position reconciliation
    POSITION_DISCREPANCY=$(curl -s "http://localhost:8080/api/reconcile/positions" | jq '.total_discrepancy_value')
    if [ "$(echo "$POSITION_DISCREPANCY > 1000" | bc)" -eq 1 ]; then
        echo "$TIMESTAMP WARNING: Position discrepancy > $1000: $POSITION_DISCREPANCY" | tee -a $LOG_FILE
    fi
    
    # Log status every 15 minutes
    if [ "$(date +%M | sed 's/^0//')" -eq 0 ] || [ "$(date +%M | sed 's/^0//')" -eq 15 ] || [ "$(date +%M | sed 's/^0//')" -eq 30 ] || [ "$(date +%M | sed 's/^0//')" -eq 45 ]; then
        echo "$TIMESTAMP INFO: System healthy - $SIGNAL_COUNT signals, $UNHEALTHY_SERVICES unhealthy services" | tee -a $LOG_FILE
    fi
    
    sleep 60  # Check every minute
done
```

### Performance Tracking
```bash
# Track key performance metrics during market hours
python -c "
import requests, json, time
from datetime import datetime

metrics_log = f'performance_metrics_{datetime.now().strftime(\"%Y%m%d\")}.json'
metrics = []

while datetime.now().hour < 16:  # Until 4 PM
    timestamp = datetime.now().isoformat()
    
    # Collect metrics
    try:
        # Signal generation latency
        signal_resp = requests.get('http://localhost:8083/metrics')
        # Execution latency  
        exec_resp = requests.get('http://localhost:8085/metrics')
        # Data ingestion latency
        data_resp = requests.get('http://localhost:8081/metrics')
        
        metric_data = {
            'timestamp': timestamp,
            'signal_latency': 'extracted_from_metrics',
            'execution_latency': 'extracted_from_metrics', 
            'data_latency': 'extracted_from_metrics'
        }
        
        metrics.append(metric_data)
        
        # Save every 15 minutes
        if len(metrics) % 15 == 0:
            with open(metrics_log, 'w') as f:
                json.dump(metrics, f, indent=2)
                
    except Exception as e:
        print(f'Error collecting metrics: {e}')
    
    time.sleep(60)  # Collect every minute
"
```

## 🌆 Market Close (4:00 PM EST)

### End-of-Day Procedures
```bash
echo "=== Market Close Procedures ===" | tee market_close_$(date +%Y%m%d).log

# 1. Final position reconciliation
echo "Final position reconciliation:" | tee -a market_close_$(date +%Y%m%d).log
curl -X POST http://localhost:8080/api/reconcile/end-of-day | jq '{
    total_positions: .summary.total_positions,
    total_unrealized_pnl: .summary.total_unrealized_pnl,
    discrepancies: .summary.discrepancy_count
}' | tee -a market_close_$(date +%Y%m%d).log

# 2. Daily P&L calculation
echo "Daily P&L summary:" | tee -a market_close_$(date +%Y%m%d).log
curl "http://localhost:8088/api/reports/daily-pnl?date=$(date +%Y-%m-%d)" | jq '{
    realized_pnl: .realized_pnl,
    unrealized_pnl: .unrealized_pnl,
    total_pnl: .total_pnl,
    total_trades: .total_trades
}' | tee -a market_close_$(date +%Y%m%d).log

# 3. Trading statistics for the day
echo "Trading statistics:" | tee -a market_close_$(date +%Y%m%d).log
curl "http://localhost:8083/api/metrics/daily-summary?date=$(date +%Y-%m-%d)" | jq '{
    signals_generated: .signals_generated,
    signals_executed: .signals_executed,
    win_rate: .win_rate,
    avg_signal_confidence: .avg_confidence
}' | tee -a market_close_$(date +%Y%m%d).log

# 4. System performance summary
echo "System performance summary:" | tee -a market_close_$(date +%Y%m%d).log
python scripts/reporting/daily-performance-summary.py --date=$(date +%Y-%m-%d) | tee -a market_close_$(date +%Y%m%d).log
```

### Risk Management Review
```bash
# End-of-day risk assessment
echo "Risk management review:" | tee -a market_close_$(date +%Y%m%d).log

# 1. Risk limit utilization
curl http://localhost:8084/api/risk-metrics/daily-utilization | jq '{
    max_daily_loss_used: .max_daily_loss_percentage,
    position_concentration: .max_position_concentration,
    correlation_exposure: .correlation_exposure_percentage
}' | tee -a market_close_$(date +%Y%m%d).log

# 2. VaR calculation for overnight positions
curl http://localhost:8084/api/risk-metrics/var?horizon=1d | jq '{
    portfolio_var: .portfolio_var,
    expected_shortfall: .expected_shortfall,
    confidence_level: .confidence_level
}' | tee -a market_close_$(date +%Y%m%d).log

# 3. Check for any risk breaches during the day
curl "http://localhost:8084/api/risk-breaches?date=$(date +%Y-%m-%d)" | jq 'length' | tee -a market_close_$(date +%Y%m%d).log
```

## 🌙 After-Hours Maintenance (4:00 PM - 6:00 AM EST)

### System Maintenance Window
```bash
# After-hours maintenance procedures
echo "=== After-Hours Maintenance ===" | tee after_hours_$(date +%Y%m%d).log

# 1. Log rotation and cleanup
echo "Log rotation and cleanup:" | tee -a after_hours_$(date +%Y%m%d).log
find /var/log -name "*.log" -mtime +7 -delete 2>&1 | tee -a after_hours_$(date +%Y%m%d).log
docker system prune -f 2>&1 | tee -a after_hours_$(date +%Y%m%d).log

# 2. Database maintenance
echo "Database maintenance:" | tee -a after_hours_$(date +%Y%m%d).log
psql -h localhost -U eafix -d eafix_prod -c "
    VACUUM ANALYZE;
    REINDEX SYSTEM eafix_prod;
    SELECT relname, n_tup_ins, n_tup_upd, n_tup_del 
    FROM pg_stat_user_tables 
    ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC 
    LIMIT 10;
" 2>&1 | tee -a after_hours_$(date +%Y%m%d).log

# 3. Backup procedures
echo "Backup procedures:" | tee -a after_hours_$(date +%Y%m%d).log
pg_dump -h localhost -U eafix eafix_prod | gzip > "backup_$(date +%Y%m%d_%H%M%S).sql.gz"
echo "Database backup completed: backup_$(date +%Y%m%d_%H%M%S).sql.gz" | tee -a after_hours_$(date +%Y%m%d).log

# 4. System health optimization
echo "System optimization:" | tee -a after_hours_$(date +%Y%m%d).log
# Restart services with high memory usage
docker stats --no-stream | awk 'NR>1 && $7+0 > 80 {print $2}' | while read container; do
    echo "Restarting high-memory container: $container" | tee -a after_hours_$(date +%Y%m%d).log
    docker restart $container
done
```

### Daily Reports Generation
```bash
# Generate comprehensive daily reports
python scripts/reporting/generate-daily-report.py \
    --date $(date +%Y-%m-%d) \
    --output-dir "/reports/daily/$(date +%Y/%m)" \
    --include-charts \
    --send-email "trading-ops@company.com,risk-management@company.com"

# Generate trading performance report
python scripts/reporting/trading-performance-report.py \
    --date $(date +%Y-%m-%d) \
    --benchmark SP500 \
    --output "/reports/daily/$(date +%Y/%m)/trading_performance_$(date +%Y%m%d).pdf"
```

## 🎯 Weekend Procedures

### Saturday Maintenance
```bash
# Extended maintenance window
echo "=== Saturday Maintenance ===" | tee saturday_maintenance_$(date +%Y%m%d).log

# 1. Full system backup
echo "Full system backup:" | tee -a saturday_maintenance_$(date +%Y%m%d).log
docker compose -f deploy/compose/docker-compose.yml down
tar -czf "system_backup_$(date +%Y%m%d).tar.gz" /var/lib/docker/volumes/
docker compose -f deploy/compose/docker-compose.yml up -d

# 2. Security updates
echo "Security updates:" | tee -a saturday_maintenance_$(date +%Y%m%d).log
apt list --upgradable | grep security 2>&1 | tee -a saturday_maintenance_$(date +%Y%m%d).log

# 3. Performance analysis
echo "Performance analysis:" | tee -a saturday_maintenance_$(date +%Y%m%d).log
python scripts/analysis/weekly-performance-analysis.py --week $(date +%Y-W%U) 2>&1 | tee -a saturday_maintenance_$(date +%Y%m%d).log

# 4. Capacity planning review
echo "Capacity planning:" | tee -a saturday_maintenance_$(date +%Y%m%d).log
python scripts/capacity/weekly-capacity-review.py 2>&1 | tee -a saturday_maintenance_$(date +%Y%m%d).log
```

### Sunday System Preparation
```bash
# Prepare system for the upcoming week
echo "=== Sunday System Preparation ===" | tee sunday_prep_$(date +%Y%m%d).log

# 1. Update market calendar for the week
echo "Updating market calendar:" | tee -a sunday_prep_$(date +%Y%m%d).log
python scripts/calendar/update-weekly-calendar.py --start-date $(date -d "tomorrow" +%Y-%m-%d) 2>&1 | tee -a sunday_prep_$(date +%Y%m%d).log

# 2. Review and update risk parameters
echo "Risk parameters review:" | tee -a sunday_prep_$(date +%Y%m%d).log
python scripts/risk/weekly-risk-review.py 2>&1 | tee -a sunday_prep_$(date +%Y%m%d).log

# 3. System validation for Monday open
echo "Pre-Monday validation:" | tee -a sunday_prep_$(date +%Y%m%d).log
make smoke 2>&1 | tee -a sunday_prep_$(date +%Y%m%d).log
make contracts-validate-full 2>&1 | tee -a sunday_prep_$(date +%Y%m%d).log

# 4. Generate weekly summary report
echo "Weekly summary report:" | tee -a sunday_prep_$(date +%Y%m%d).log
python scripts/reporting/weekly-summary-report.py --week $(date +%Y-W%U) \
    --send-to "management@company.com" 2>&1 | tee -a sunday_prep_$(date +%Y%m%d).log
```

## 📋 Market Session Checklists

### Pre-Market Checklist (Daily)
- [ ] System health check completed (all 9 services healthy)
- [ ] Market data feeds validated and fresh
- [ ] Database connectivity confirmed
- [ ] Risk parameters set for the day
- [ ] High-impact calendar events reviewed
- [ ] Signal generation tested
- [ ] Execution engine broker connectivity confirmed
- [ ] Position reconciliation from previous day completed
- [ ] On-call engineer notified and available
- [ ] Trading desk informed of system status

### Market Open Checklist (9:30 AM)
- [ ] Increased data flow confirmed
- [ ] Signal generation active
- [ ] First signals of the day validated
- [ ] System performance within normal ranges
- [ ] Real-time monitoring activated
- [ ] Trading desk has system dashboard access
- [ ] Backup procedures verified

### Market Close Checklist (4:00 PM)
- [ ] Final position reconciliation completed
- [ ] Daily P&L calculated and verified
- [ ] Trading statistics compiled
- [ ] End-of-day risk assessment completed
- [ ] All open positions documented
- [ ] System performance summary generated
- [ ] Daily reports sent to stakeholders
- [ ] After-hours maintenance scheduled

### Weekend Checklist
- [ ] Full system backup completed
- [ ] Security updates reviewed and applied
- [ ] Weekly performance analysis completed
- [ ] Capacity planning review conducted
- [ ] Next week's calendar events loaded
- [ ] Risk parameters reviewed for next week
- [ ] Weekly summary report generated
- [ ] System validated for Monday open

---

**Document Owner**: Trading Operations Team  
**Technical Owner**: Platform Engineering Team  
**Last Updated**: December 2024  
**Next Review**: January 2025