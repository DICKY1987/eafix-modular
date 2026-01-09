---
doc_id: DOC-CONFIG-0094
---

# OpenSSF Scorecards Security Policy

## Overview

This document defines the security policy and minimum requirements for the EAFIX Trading System based on OpenSSF Scorecards supply chain security assessment framework.

## Policy Statement

**The EAFIX trading system MUST maintain a minimum OpenSSF Scorecard score of 7.0/10 with no more than 5 high-priority security findings to ensure adequate supply chain security for financial trading operations.**

## Rationale

### Trading System Context
- **Financial Exposure**: Direct market access with real monetary risk
- **Regulatory Requirements**: Must meet financial industry security standards (SOX, PCI DSS)  
- **Operational Criticality**: 99.9% uptime SLO during market hours (6 AM - 6 PM EST)
- **Data Sensitivity**: Trade signals, positions, and P&L data require highest protection
- **Supply Chain Risk**: Dependencies could introduce vulnerabilities affecting trading logic

### Security Framework Benefits
- **Standardized Assessment**: Industry-recognized security evaluation framework
- **Continuous Monitoring**: Weekly automated security posture assessment
- **Compliance Evidence**: Auditable security controls for regulatory review
- **Risk Reduction**: Proactive identification of supply chain vulnerabilities

## Security Controls Matrix

### Required Controls (Score Weight: High)

#### Branch Protection (10% weight)
- **Requirement**: Main branch MUST be protected
- **Implementation**: 
  - Required pull request reviews (minimum 1)
  - Dismiss stale reviews on new commits
  - Require status checks to pass
  - Restrict pushes to main branch
  - No force pushes allowed
- **Trading System Impact**: Prevents unauthorized trading logic changes

#### Code Review (10% weight)  
- **Requirement**: All changes MUST be reviewed by qualified personnel
- **Implementation**:
  - Required reviewers with trading system knowledge
  - CODEOWNERS file defining review responsibilities
  - No self-approval of changes
- **Trading System Impact**: Ensures trading algorithms are validated before deployment

#### Static Application Security Testing (10% weight)
- **Requirement**: SAST tools MUST be integrated into CI/CD pipeline
- **Implementation**:
  - CodeQL analysis for Python codebase
  - Security-focused pre-commit hooks
  - Automated vulnerability scanning
- **Trading System Impact**: Detects security flaws in trading logic and data handling

#### Dependency Management (10% weight)
- **Requirement**: Dependencies MUST be pinned and regularly updated
- **Implementation**:
  - Docker image digest pinning policy enforced
  - Dependabot automated updates enabled
  - Vulnerability scanning of all dependencies
- **Trading System Impact**: Prevents supply chain attacks on trading infrastructure

#### Vulnerability Management (10% weight)
- **Requirement**: Known vulnerabilities MUST be addressed within SLA
- **Implementation**:
  - Automated vulnerability scanning
  - 4-hour response time for critical CVEs
  - Security advisory monitoring
- **Trading System Impact**: Maintains trading system security posture

### Important Controls (Score Weight: Medium)

#### Security Policy (8% weight)
- **Requirement**: SECURITY.md file MUST define vulnerability reporting process
- **Current Status**: ✅ Implemented
- **Location**: `/SECURITY.md`

#### License Compliance (8% weight)
- **Requirement**: Valid SPDX license identifier MUST be present
- **Current Status**: ✅ MIT License implemented
- **Location**: `/LICENSE`

#### Signed Releases (8% weight)
- **Requirement**: Releases MUST be cryptographically signed
- **Implementation**: Cosign integration for container signing
- **Trading System Impact**: Ensures deployment integrity

#### CI Testing (8% weight)
- **Requirement**: Comprehensive automated testing MUST be present
- **Implementation**: 
  - Unit tests for all services
  - Integration tests for trading pipeline
  - Contract tests for event schemas
- **Trading System Impact**: Validates trading logic correctness

### Standard Controls (Score Weight: Low)

#### Token Permissions (6% weight)
- **Requirement**: GitHub Actions MUST use minimal necessary permissions
- **Implementation**: Explicit permission declarations in all workflows

#### Maintained Project (6% weight)
- **Requirement**: Regular development activity MUST be demonstrated
- **Monitoring**: Automated tracking of commit frequency and contributor activity

#### Contributors (6% weight)
- **Requirement**: Contributors MUST have verified GitHub identities
- **Implementation**: Contributor verification process

#### Binary Artifacts (6% weight)
- **Requirement**: Source code MUST NOT contain binary artifacts
- **Implementation**: Automated scanning for binary files in commits

#### Packaging (6% weight)
- **Requirement**: Secure package publishing practices MUST be followed
- **Implementation**: Automated Docker image builds with security scanning

#### Pinned Dependencies (6% weight)
- **Requirement**: Production dependencies MUST be pinned to specific versions
- **Implementation**: Digest pinning policy for all container images

## Minimum Score Requirements

### Overall Score Thresholds
- **Production Release**: Minimum 7.0/10 (70th percentile)
- **Development Branch**: Minimum 6.0/10 (60th percentile)  
- **Feature Branches**: No minimum (advisory only)

### High-Priority Finding Limits
- **Production Release**: Maximum 5 high-priority findings
- **Development Branch**: Maximum 10 high-priority findings
- **Feature Branches**: No limit (advisory only)

### Critical Control Requirements
These controls MUST pass regardless of overall score:
- Branch Protection enabled
- Code Review required
- SAST enabled
- No known high/critical CVEs
- Security Policy present

## Monitoring and Compliance

### Automated Assessment
- **Frequency**: Weekly scheduled assessment every Monday at 4 AM UTC
- **Triggers**: 
  - Changes to security configurations
  - Updates to branch protection rules
  - Modifications to CI/CD workflows
  - Security policy changes
- **Integration**: Results uploaded to GitHub Security tab for visibility

### Manual Review Process
- **Monthly Security Review**: Detailed analysis of scorecard trends and recommendations
- **Quarterly Assessment**: Comprehensive security posture evaluation with stakeholders
- **Annual Audit**: External security assessment including Scorecards results

### Compliance Reporting
- **Real-time Dashboard**: GitHub Security tab with current scorecard status
- **Weekly Reports**: Automated email summary of security posture changes
- **Monthly Metrics**: Security KPIs including score trends and remediation velocity
- **Quarterly Reviews**: Executive summary for leadership and compliance teams

## Remediation Procedures

### Score Below Threshold
1. **Immediate Actions**:
   - Halt production deployments
   - Conduct emergency security assessment
   - Identify root cause of score degradation

2. **Remediation Process**:
   - Create remediation plan with timeline
   - Implement security improvements
   - Re-run assessment to validate fixes
   - Document lessons learned

3. **Return to Service**:
   - Validate score meets minimum threshold
   - Conduct integration testing
   - Obtain security team approval
   - Resume normal operations

### High-Priority Findings
1. **Immediate Response** (within 4 hours):
   - Assess finding severity and impact
   - Determine if immediate action required
   - Create incident ticket and assign owner

2. **Investigation** (within 24 hours):
   - Root cause analysis
   - Impact assessment on trading operations
   - Development of remediation plan

3. **Resolution** (within SLA):
   - Critical findings: 24 hours
   - High findings: 72 hours  
   - Medium findings: 7 days
   - Low findings: 30 days

## Integration with CI/CD

### Pull Request Checks
- **Required Status Check**: Scorecards assessment MUST pass before merge
- **Automated Comments**: PR comments with security score and recommendations
- **Blocking Conditions**: PRs blocked if introducing high-priority findings

### Release Gates
- **Pre-release Validation**: Scorecards score verified before release tagging
- **Deployment Pipeline**: Production deployment blocked if minimum score not met
- **Emergency Override**: CTO approval required for emergency deployments bypassing security gates

### Development Workflow
- **Feature Branch Analysis**: Advisory scorecards assessment on feature branches
- **Security Feedback**: Developers receive immediate feedback on security implications
- **Training Integration**: Links to security training based on identified gaps

## Exceptions and Waivers

### Emergency Trading Operations
- **Market Crisis**: Security gates MAY be temporarily bypassed with CTO approval
- **Critical Bug Fix**: Expedited security review process for critical trading issues  
- **Time-sensitive Opportunities**: Risk/reward assessment for urgent trading feature deployments

### Waiver Process
1. **Request Submission**: Document business justification and risk assessment
2. **Security Review**: Security team evaluates risk and mitigation options
3. **Approval Authority**: 
   - Low risk: Security Team Lead
   - Medium risk: CISO approval
   - High risk: CTO and CISO approval
4. **Documentation**: All waivers logged with expiration dates and review triggers

### Compensating Controls
When waivers are granted, compensating controls MUST be implemented:
- Additional monitoring and alerting
- Manual security reviews
- Reduced deployment frequency
- Enhanced logging and audit trails

## Key Performance Indicators (KPIs)

### Security Metrics
- **Overall Score Trend**: Monthly average scorecard score
- **High Finding Velocity**: Mean time to resolve high-priority findings
- **Control Coverage**: Percentage of controls meeting minimum requirements
- **Regression Rate**: Frequency of score decreases after releases

### Business Metrics  
- **Deployment Frequency**: Impact of security gates on release velocity
- **Mean Time to Production**: Security review impact on deployment timeline
- **Security Incident Rate**: Correlation between scorecard score and security incidents
- **Compliance Cost**: Resource allocation for maintaining security posture

### Trading System Metrics
- **Uptime Impact**: Security-related downtime during market hours
- **Performance Impact**: Latency introduced by security controls
- **Data Integrity**: Security control effectiveness for trading data protection
- **Audit Readiness**: Compliance preparation time and success rate

---

**Policy Version**: 1.0  
**Effective Date**: 2025-01-15  
**Next Review**: 2025-04-15  
**Owner**: Security Team  
**Approver**: CISO and CTO