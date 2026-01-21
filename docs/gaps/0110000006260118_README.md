---
doc_id: DOC-DOC-0010
---

# Production Readiness Gap Analysis

This directory contains production readiness documentation for the EAFIX modular trading system.

## 📋 Documentation Structure

### Core Documents
- **[GAP_REGISTER.md](GAP_REGISTER.md)** - Active gap tracking with Risk Priority Numbers (RPN)
- **[slo/SLOs.md](slo/SLOs.md)** - Service Level Objectives and alerting configuration
- **[fmea/FMEA.md](fmea/FMEA.md)** - Failure Mode and Effects Analysis
- **[invariants/INVARIANTS.md](invariants/INVARIANTS.md)** - Executable system invariants

### Operational Templates
- **[INCIDENT_TEMPLATE.md](INCIDENT_TEMPLATE.md)** - Incident response template
- **[POSTMORTEM_TEMPLATE.md](POSTMORTEM_TEMPLATE.md)** - Post-incident analysis template
- **[game_day.md](game_day.md)** - Game day runbook and disaster recovery procedures

## 🎯 Using This Documentation

### Regular Gap Review (Weekly)
```bash
# Review current gaps and priorities
make gaps-check
```

### Pre-Release Checklist
1. Review and update GAP_REGISTER.md
2. Validate all SLOs are being monitored
3. Run FMEA review for new features
4. Verify invariants are tested

### Incident Response
1. Use INCIDENT_TEMPLATE.md during incidents
2. Follow up with POSTMORTEM_TEMPLATE.md
3. Update GAP_REGISTER.md with findings
4. Update FMEA with new failure modes

## 📊 Gap Priority (RPN Score)
- **High Priority**: RPN > 80 (immediate attention)
- **Medium Priority**: RPN 40-80 (next sprint)
- **Low Priority**: RPN < 40 (backlog)

Current high-priority gaps:
- G-003: Position reconciliation (RPN: 105)
- G-001: Signal TTL enforcement (RPN: 96)

## 🔧 Automation Integration

### CI/CD Integration
- Gap documentation is checked in CI via `.github/workflows/`
- Schema compatibility is validated automatically
- Smoke tests verify SLO compliance

### Monitoring Integration
- SLO metrics are exported to Prometheus
- Invariant violations trigger alerts
- FMEA failure modes have corresponding monitoring

## 🎯 Next Steps

1. **Implement High-Priority Gaps**: Focus on G-003 and G-001
2. **Automate SLO Monitoring**: Set up Prometheus alerts for all SLOs
3. **Invariant Testing**: Implement automated tests for each invariant
4. **Game Day Testing**: Schedule quarterly disaster recovery exercises

---

For questions about production readiness or gap analysis, contact the system owners listed in [CODEOWNERS](../../.github/CODEOWNERS).