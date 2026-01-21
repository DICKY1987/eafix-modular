---
doc_id: DOC-CONFIG-0089
---

# EAFIX Runbooks Index

## 📚 Complete Runbook Library

This is the comprehensive index of all operational runbooks for the EAFIX trading system. Use this index to quickly find the appropriate runbook for your situation.

## 🚨 Emergency Response

### Primary Response Runbooks
- **[incident-response.md](incident-response.md)** - Main incident response procedures (START HERE)
- **[trading-incidents.md](trading-incidents.md)** - Trading-specific incident handling
- **[escalation-procedures.md](escalation-procedures.md)** - Contact info and escalation matrix
- **[on-call/README.md](../on-call/README.md)** - Complete on-call guide

### Quick Reference
```bash
# Emergency Commands
curl -X POST http://localhost:8080/emergency/stop-trading
make emergency-restart
make smoke
```

## 🔧 System Operations

### Core Operations
- **[service-health.md](service-health.md)** - Health monitoring and diagnostics
- **[deployment.md](deployment.md)** - Deployment and rollback procedures
- **[market-open-close.md](market-open-close.md)** - Daily market operations
- **[common-issues.md](common-issues.md)** - Troubleshooting guide

### Specialized Procedures
- **[backup-recovery.md](backup-recovery.md)** - Data backup and recovery
- **[security-incidents.md](security-incidents.md)** - Security incident response
- **[performance-issues.md](performance-issues.md)** - Performance troubleshooting
- **[capacity-management.md](capacity-management.md)** - Capacity planning and scaling

## 📊 By Urgency Level

### P0 - Critical (Immediate)
1. **[incident-response.md](incident-response.md)** - Primary response procedures
2. **[trading-incidents.md](trading-incidents.md)** - Trading system failures
3. **[escalation-procedures.md](escalation-procedures.md)** - Emergency contacts

### P1 - High (15 minutes)
1. **[service-health.md](service-health.md)** - Service diagnostics
2. **[common-issues.md](common-issues.md)** - Known problem solutions
3. **[performance-issues.md](performance-issues.md)** - Performance degradation

### P2 - Medium (1 hour)
1. **[deployment.md](deployment.md)** - Deployment issues
2. **[backup-recovery.md](backup-recovery.md)** - Data recovery
3. **[capacity-management.md](capacity-management.md)** - Resource issues

### P3 - Low (Next business day)
1. **[scheduled-maintenance.md](scheduled-maintenance.md)** - Planned maintenance
2. **[database-maintenance.md](database-maintenance.md)** - DB maintenance
3. **[log-rotation.md](log-rotation.md)** - Log management

## 🎯 By Service Component

### Trading Core Services
| Service | Port | Primary Runbooks |
|---------|------|------------------|
| GUI Gateway | 8080 | [service-health.md](service-health.md), [common-issues.md](common-issues.md) |
| Data Ingestor | 8081 | [trading-incidents.md](trading-incidents.md), [market-open-close.md](market-open-close.md) |
| Indicator Engine | 8082 | [performance-issues.md](performance-issues.md), [common-issues.md](common-issues.md) |
| Signal Generator | 8083 | [trading-incidents.md](trading-incidents.md), [performance-issues.md](performance-issues.md) |
| Risk Manager | 8084 | [trading-incidents.md](trading-incidents.md), [common-issues.md](common-issues.md) |
| Execution Engine | 8085 | [trading-incidents.md](trading-incidents.md), [common-issues.md](common-issues.md) |
| Calendar Ingestor | 8086 | [service-health.md](service-health.md) |
| Reentry Matrix | 8087 | [service-health.md](service-health.md) |
| Reporter | 8088 | [service-health.md](service-health.md), [backup-recovery.md](backup-recovery.md) |

### Infrastructure Components
| Component | Primary Runbooks |
|-----------|------------------|
| Redis | [common-issues.md](common-issues.md), [performance-issues.md](performance-issues.md) |
| PostgreSQL | [database-maintenance.md](database-maintenance.md), [backup-recovery.md](backup-recovery.md) |
| Docker | [deployment.md](deployment.md), [common-issues.md](common-issues.md) |
| Kubernetes | [deployment.md](deployment.md), [capacity-management.md](capacity-management.md) |

## ⏰ By Time of Day

### Pre-Market (5:00-9:30 AM EST)
- **[market-open-close.md](market-open-close.md)** - Pre-market procedures
- **[service-health.md](service-health.md)** - System validation
- **[backup-recovery.md](backup-recovery.md)** - Data integrity checks

### Market Hours (9:30 AM-4:00 PM EST)
- **[incident-response.md](incident-response.md)** - Primary response
- **[trading-incidents.md](trading-incidents.md)** - Trading issues
- **[escalation-procedures.md](escalation-procedures.md)** - Fast escalation

### After Hours (4:00 PM-6:00 AM EST)
- **[market-open-close.md](market-open-close.md)** - End-of-day procedures
- **[scheduled-maintenance.md](scheduled-maintenance.md)** - Maintenance window
- **[database-maintenance.md](database-maintenance.md)** - DB maintenance

### Weekends
- **[scheduled-maintenance.md](scheduled-maintenance.md)** - Extended maintenance
- **[capacity-management.md](capacity-management.md)** - Planning activities
- **[backup-recovery.md](backup-recovery.md)** - Full system backups

## 🔍 By Problem Type

### Service Failures
1. **[common-issues.md](common-issues.md)** - Service won't start, crashes
2. **[service-health.md](service-health.md)** - Health check failures
3. **[deployment.md](deployment.md)** - Deployment-related failures

### Performance Issues
1. **[performance-issues.md](performance-issues.md)** - Latency, throughput
2. **[capacity-management.md](capacity-management.md)** - Resource constraints
3. **[database-maintenance.md](database-maintenance.md)** - Database performance

### Data Issues
1. **[trading-incidents.md](trading-incidents.md)** - Market data problems
2. **[backup-recovery.md](backup-recovery.md)** - Data corruption/loss
3. **[data-quality.md](data-quality.md)** - Data integrity issues

### Security Issues
1. **[security-incidents.md](security-incidents.md)** - Security breaches
2. **[incident-response.md](incident-response.md)** - General security response
3. **[escalation-procedures.md](escalation-procedures.md)** - Security escalation

### Network Issues
1. **[connectivity-issues.md](connectivity-issues.md)** - Network connectivity
2. **[common-issues.md](common-issues.md)** - Redis, database connections
3. **[trading-incidents.md](trading-incidents.md)** - Broker API issues

## 📱 Mobile Quick Reference

### Emergency Numbers
- **Primary On-Call**: +1-555-0123
- **Trading Desk**: +1-555-0200 (market hours)
- **Security Team**: +1-555-0300 (24/7)

### Essential Commands
```bash
# System status
make smoke

# Emergency stop
curl -X POST http://localhost:8080/emergency/stop-trading

# Service restart
docker compose restart <service>

# Check logs
docker compose logs <service> --tail=50
```

### Critical URLs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Health Dashboard**: http://localhost:8080/health
- **Prometheus**: http://localhost:9090

## 🎯 Runbook Selection Guide

### "The system is completely down!"
→ **[incident-response.md](incident-response.md)** (Section: Emergency Response)

### "Trading is not working!"
→ **[trading-incidents.md](trading-incidents.md)** (Trading Emergency Procedures)

### "A service is failing health checks"
→ **[service-health.md](service-health.md)** or **[common-issues.md](common-issues.md)**

### "Everything is slow"
→ **[performance-issues.md](performance-issues.md)**

### "I need to deploy a fix"
→ **[deployment.md](deployment.md)**

### "Data looks wrong"
→ **[trading-incidents.md](trading-incidents.md)** (Data Validation section)

### "It's market open and something's wrong"
→ **[market-open-close.md](market-open-close.md)** + **[trading-incidents.md](trading-incidents.md)**

### "I don't know what's wrong"
→ **[incident-response.md](incident-response.md)** (Investigation Phase)

### "Should I escalate this?"
→ **[escalation-procedures.md](escalation-procedures.md)** (Escalation Decision Tree)

## 📊 Runbook Metrics & Maintenance

### Usage Tracking
Track which runbooks are used most frequently to identify:
- Common failure patterns
- Training opportunities
- Documentation gaps

### Update Schedule
- **Monthly**: Review incident-driven updates
- **Quarterly**: Full runbook review cycle
- **Semi-annually**: Contact information verification
- **Annually**: Complete process review

### Quality Metrics
- Incident resolution time improvement
- Escalation rate reduction
- First-time fix rate
- Runbook accuracy feedback

## 🎓 Training & Certification

### Required Reading (All Team Members)
1. **[incident-response.md](incident-response.md)** - Core incident response
2. **[escalation-procedures.md](escalation-procedures.md)** - Escalation matrix
3. **[on-call/README.md](../on-call/README.md)** - On-call procedures

### Role-Specific Training

**On-Call Engineers:**
- All emergency response runbooks
- Service-specific troubleshooting guides
- Performance and capacity management

**Trading Operations:**
- **[trading-incidents.md](trading-incidents.md)**
- **[market-open-close.md](market-open-close.md)**
- Trading-specific procedures

**Platform Engineers:**
- **[deployment.md](deployment.md)**
- **[service-health.md](service-health.md)**
- **[capacity-management.md](capacity-management.md)**

## 🔄 Continuous Improvement

### Feedback Collection
After each incident, evaluate:
- Was the correct runbook used?
- Was information accurate and complete?
- What information was missing?
- How can response time be improved?

### Runbook Evolution
- Update runbooks based on incident learnings
- Add new scenarios encountered
- Remove obsolete procedures
- Improve clarity and usability

### Testing & Validation
- **Game Day Exercises**: Test runbooks in simulated incidents
- **Walkthrough Reviews**: Regular team reviews of procedures
- **Automation Opportunities**: Identify manual steps for automation

---

**Quick Access Links:**
- 🚨 [Emergency Response](incident-response.md) | 📞 [Escalation](escalation-procedures.md) | 💰 [Trading Issues](trading-incidents.md)
- 🔧 [Common Issues](common-issues.md) | 📊 [Service Health](service-health.md) | 🚀 [Deployment](deployment.md)

**Document Owner**: Platform Engineering Team  
**Last Updated**: December 2024  
**Next Review**: January 2025