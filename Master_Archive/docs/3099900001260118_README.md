---
doc_id: DOC-DOC-0002
---

# EAFIX Trading System Documentation

This directory contains comprehensive documentation for the EAFIX Trading System microservices architecture.

## Documentation Structure

### Architecture & Design

- **[adr/](adr/)**: Architecture Decision Records (ADRs)
  - Decision rationale for major architectural choices
  - Service decomposition strategies
  - Technology selection justifications

- **[modernization/](modernization/)**: Modernization Documentation  
  - Service catalog with SLOs and ownership
  - Migration guides from legacy to microservices
  - Performance benchmarks and optimization guides

### Operations & Production

- **[runbooks/](runbooks/)**: Operational Runbooks
  - Per-service operational procedures
  - Incident response playbooks
  - Troubleshooting guides
  - Emergency procedures

- **[gaps/](gaps/)**: Production Readiness
  - Gap register with risk assessments
  - Service Level Objectives (SLOs)
  - FMEA analysis and mitigation strategies
  - System invariants and monitoring

## Documentation Guidelines

### For Developers

When adding new services or features:

1. **ADRs**: Create ADR for significant architectural decisions
2. **Service Docs**: Update service catalog in `modernization/`
3. **Runbooks**: Create operational procedures in `runbooks/`
4. **Gap Analysis**: Assess production readiness gaps

### For Operations Teams

For incident response and day-to-day operations:

1. **Start with Runbooks**: Service-specific procedures and troubleshooting
2. **Check SLOs**: Understand performance expectations and alert thresholds
3. **Gap Register**: Understand known limitations and workarounds
4. **Incident Templates**: Use structured templates in `.github/ISSUE_TEMPLATE/`

## Key Documents

### Quick References

- **[Service Catalog](modernization/01_service_catalog.md)**: Complete service inventory with ports, SLOs, and ownership
- **[Gap Register](gaps/GAP_REGISTER.md)**: Active production readiness tracking
- **[System SLOs](gaps/slo/SLOs.md)**: Performance targets and monitoring

### Architecture Decisions

- **[ADR-0001](adr/ADR-0001-service-decomposition.md)**: Service decomposition strategy
- Additional ADRs document major technical decisions

### Emergency Procedures

- **Incident Response**: See `.github/ISSUE_TEMPLATE/incident_report.md`
- **Service Runbooks**: Individual service procedures in `runbooks/`
- **System Recovery**: Emergency procedures documented per service

## Contributing to Documentation

### Documentation Standards

- **Markdown**: Use standard markdown formatting
- **Structure**: Follow existing directory structure
- **Cross-references**: Link related documents
- **Date Stamps**: Include "Last Updated" dates
- **Ownership**: Identify document owners/maintainers

### Review Process

- All documentation changes go through PR review
- Architecture changes require ADR updates
- Operational changes require runbook updates
- New services require complete documentation package

### Templates

Use these templates for new documentation:

- **ADR Template**: Follow existing ADR structure
- **Runbook Template**: Include standard sections (overview, procedures, troubleshooting)
- **Service Docs**: Include SLOs, architecture, dependencies, APIs

## Documentation Maintenance

### Regular Reviews

- **Monthly**: Review gap register and update risk assessments
- **Quarterly**: Update SLOs based on actual performance
- **Per Release**: Update service documentation and runbooks
- **Post-Incident**: Update procedures based on lessons learned

### Metrics

Track documentation health:
- Coverage: All services have complete documentation
- Freshness: Documents updated within last 90 days
- Usage: Documentation referenced in incident response
- Accuracy: Procedures successfully followed during incidents

## Additional Resources

### External References

- **GitHub Repository**: Main codebase and issues
- **Contract Registry**: `../contracts/` for API and event schemas  
- **Shared Libraries**: `../shared/` for common components
- **Deployment**: `../deploy/` for infrastructure as code

### Support Channels

- **Issues**: Use GitHub issues with appropriate templates
- **Architecture Questions**: Reference ADRs and create new ones for decisions
- **Operational Issues**: Follow runbook procedures and escalation paths

---

*This documentation follows the principle of "docs as code" - all documentation is versioned, reviewed, and maintained alongside the codebase.*