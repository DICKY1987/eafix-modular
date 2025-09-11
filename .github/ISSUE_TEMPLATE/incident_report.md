---
name: Incident Report
about: Report a trading system incident or outage
title: '[INCIDENT] '
labels: 'incident'
assignees: ''

---

**Incident Summary**
Brief description of what happened.

**Incident Timeline**
- **Start Time**: [YYYY-MM-DD HH:MM:SS UTC]
- **Detection Time**: [YYYY-MM-DD HH:MM:SS UTC] 
- **Resolution Time**: [YYYY-MM-DD HH:MM:SS UTC]

**Impact Assessment**
- [ ] **SEV-1**: Complete trading system outage, financial impact
- [ ] **SEV-2**: Major service degradation, partial trading impact
- [ ] **SEV-3**: Minor service issues, minimal trading impact
- [ ] **SEV-4**: Isolated issues, no trading impact

**Financial Impact**
- Estimated P&L impact: [$ amount or "None"]
- Missed trading opportunities: [Description]
- Execution delays: [Duration and impact]

**Affected Services**
- [ ] data-ingestor (price feeds)
- [ ] indicator-engine (technical analysis)
- [ ] signal-generator (trading signals)
- [ ] risk-manager (position limits)
- [ ] execution-engine (order placement)
- [ ] calendar-ingestor (economic events)
- [ ] reentry-matrix-svc (re-entry logic)
- [ ] reporter (metrics/reporting)
- [ ] gui-gateway (user interface)
- [ ] Redis (message bus)
- [ ] PostgreSQL (database)

**Root Cause Analysis**
What was the underlying cause of the incident?

**Contributing Factors**
What factors made this incident worse or longer?

**Detection Method**
How was this incident discovered?
- [ ] Automated monitoring alert
- [ ] User report
- [ ] Routine check
- [ ] Other: [describe]

**Resolution Steps**
What steps were taken to resolve the incident?
1. [First action]
2. [Second action]
3. [etc.]

**Prevention Measures**
What can be done to prevent this incident from happening again?

**Monitoring Gaps**
What monitoring or alerting would have helped detect this sooner?

**Documentation Updates**
What runbooks, procedures, or documentation need to be updated?

**Follow-up Actions**
- [ ] Create tickets for prevention measures
- [ ] Update runbooks
- [ ] Improve monitoring
- [ ] Review and update incident response procedures
- [ ] Schedule post-mortem meeting

**Logs and Evidence**
```
Paste relevant log entries, error messages, or monitoring data here
```

**Additional Notes**
Any other relevant information about the incident.