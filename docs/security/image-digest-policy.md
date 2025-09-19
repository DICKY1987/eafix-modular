# Container Image Digest Pinning Policy

## Overview

This document establishes the mandatory security policy for container image usage within the EAFIX Trading System to ensure supply chain integrity and reproducible builds.

## Policy Statement

**All container images MUST be pinned to specific SHA256 digests. The use of `latest`, floating tags, or unpinned images is strictly prohibited in production and CI/CD environments.**

## Rationale

### Security Benefits
- **Supply Chain Integrity**: Prevents tag manipulation attacks where malicious images are pushed with legitimate tags
- **Reproducible Builds**: Ensures identical container execution across environments
- **Vulnerability Management**: Provides precise tracking of image versions for security scanning
- **Rollback Safety**: Guarantees ability to revert to known-good image versions

### Trading System Requirements
- **Market Hours Uptime**: Critical for 99.9% availability SLO during market hours (6 AM - 6 PM EST)
- **Deterministic Behavior**: Essential for trading signal reproducibility and audit compliance
- **Zero-Downtime Deployments**: Requires predictable container behavior

## Implementation Requirements

### 1. Base Images (Application Services)
All Dockerfiles MUST specify base images with SHA256 digests:

```dockerfile
# ✅ CORRECT - Pinned digest
FROM python:3.11-slim@sha256:f52d14c7d0e87b6be38fdf5a5f6c7ae19a04e95e7dfd8cad073ad5063d80d3d0

# ❌ PROHIBITED - Floating tag
FROM python:3.11-slim
FROM python:latest
```

### 2. Infrastructure Images (Docker Compose)
All Docker Compose services MUST use pinned digests:

```yaml
# ✅ CORRECT - Infrastructure with digest
services:
  redis:
    image: redis:7-alpine@sha256:de13e74e14b98eb96bdf886791ae47686c3c5d29f9d5f85ea55206843e3fce26
  
  postgres:
    image: postgres:15-alpine@sha256:c5b2b4b97db8cc4fa4a6aba8e5d4e0d67db1e96a7d8d1e4c37a7f7f90c0a5b10
```

### 3. CI/CD Images
GitHub Actions and CI/CD pipelines MUST pin all container images:

```yaml
# ✅ CORRECT - CI image with digest
- name: Security Scan
  uses: docker://aquasec/trivy:0.48.3@sha256:727403307a3d14e3f7ade204ee2f2883bb52ede2b8b95ce6e4dc05de781b7a6f
```

## Enforcement Mechanisms

### 1. Pre-commit Hooks
Automated validation prevents commits with unpinned images:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: check-docker-digest
      name: Check Docker image digests
      entry: scripts/check-docker-digests.sh
      language: script
      files: '(Dockerfile|docker-compose\.yml|\.github/workflows/.*\.yml)$'
```

### 2. CI/CD Gates
Pipeline jobs MUST fail if unpinned images are detected:

```yaml
# .github/workflows/security.yml
- name: Validate Image Digests
  run: |
    if grep -r "FROM.*:latest\|image:.*:latest" .; then
      echo "❌ Latest tags detected - all images must use SHA256 digests"
      exit 1
    fi
```

### 3. Dependabot Integration
Automated digest updates through security dependency management:

```yaml
# .github/dependabot.yml
updates:
  - package-ecosystem: "docker"
    directory: "/services/data-ingestor"
    schedule:
      interval: "weekly"
```

## Digest Update Procedures

### 1. Regular Updates
- **Frequency**: Weekly security scans for new digests
- **Process**: Dependabot PRs → Security review → Automated testing → Deployment
- **Rollback**: Immediate revert to previous digest if issues detected

### 2. Emergency Updates
- **Trigger**: Critical CVE affecting pinned images
- **SLA**: 4-hour response time for security patches
- **Validation**: Expedited testing focused on security validation

### 3. Audit Trail
All digest changes MUST include:
- **Security scan results** before/after update
- **CVE impact assessment** for changed images
- **Testing validation** confirming no breaking changes
- **Approval record** from security team

## Current Pinned Images

### Application Base Images
- **python:3.11-slim**: `sha256:f52d14c7d0e87b6be38fdf5a5f6c7ae19a04e95e7dfd8cad073ad5063d80d3d0`

### Infrastructure Images
- **redis:7-alpine**: `sha256:de13e74e14b98eb96bdf886791ae47686c3c5d29f9d5f85ea55206843e3fce26`
- **postgres:15-alpine**: `sha256:c5b2b4b97db8cc4fa4a6aba8e5d4e0d67db1e96a7d8d1e4c37a7f7f90c0a5b10`
- **prom/prometheus:v2.48.1**: `sha256:f6639335d34a77d9d9db382b92eeb7fc00934be8eae81dbc03b31cfe90411a05`
- **grafana/grafana:10.2.3**: `sha256:195f23f4ea0a0c76ade82f4d6d81abec6b2cdb6fc4b6c94b79a0c4b8aaffe0c7`

## Exceptions

### Development Environment
- **Local development** MAY use floating tags for rapid iteration
- **Docker Compose override** files can specify `image: redis:latest` for dev convenience
- **Production parity** MUST be validated before deployment

### Testing Scenarios
- **Unit tests** MAY use test-specific images without digests
- **Integration tests** MUST use production-equivalent pinned images
- **Contract tests** MUST use exact production image digests

## Compliance Verification

### Weekly Audit
```bash
# Check for unpinned images across the repository
find . -name "Dockerfile" -o -name "docker-compose*.yml" -o -name "*.github/workflows/*.yml" | \
xargs grep -l "FROM\|image:" | \
xargs grep -E "(FROM|image:).*:(latest|[0-9]+\.[0-9]+)$" || echo "✅ All images properly pinned"
```

### Monthly Security Review
- **Vulnerability scanning** of all pinned images
- **Digest freshness** assessment (images older than 90 days)
- **Supply chain analysis** using OpenSSF Scorecards
- **Compliance reporting** to security team

## Incident Response

### Compromised Image Detection
1. **Immediate Action**: Stop affected services
2. **Investigation**: Identify scope of potential compromise
3. **Containment**: Update to known-good digest
4. **Recovery**: Full security validation before restart
5. **Post-Mortem**: Update procedures to prevent recurrence

### Emergency Rollback
- **RTO**: 15 minutes for critical trading services
- **RPO**: Zero data loss requirement
- **Procedure**: Automated digest rollback via CI/CD pipeline
- **Validation**: Health checks and integration tests before traffic restoration

## Tools and Resources

### Digest Lookup
```bash
# Get current digest for an image
docker inspect --format='{{index .RepoDigests 0}}' redis:7-alpine

# Pull and verify digest
docker pull redis:7-alpine@sha256:de13e74e14b98eb96bdf886791ae47686c3c5d29f9d5f85ea55206843e3fce26
```

### Security Scanning
```bash
# Scan pinned image for vulnerabilities
trivy image redis:7-alpine@sha256:de13e74e14b98eb96bdf886791ae47686c3c5d29f9d5f85ea55206843e3fce26
```

---

**Policy Version**: 1.0  
**Effective Date**: 2025-01-15  
**Next Review**: 2025-04-15  
**Owner**: Security Team  
**Approver**: CTO