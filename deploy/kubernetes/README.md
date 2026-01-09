---
doc_id: DOC-DOC-0009
---

# EAFIX Trading System - Kubernetes Deployment

This directory contains comprehensive Kubernetes manifests for deploying the EAFIX trading system in production environments with enterprise-grade security, observability, and resilience features.

## Architecture Overview

The EAFIX trading system is deployed as a collection of microservices with the following components:

### Core Trading Services
- **data-ingestor** (8081): Price feed normalization from MT4/DDE
- **indicator-engine** (8082): Technical indicator computation
- **signal-generator** (8083): Trading signal generation
- **risk-manager** (8084): Risk validation and position sizing
- **execution-engine** (8085): Broker order execution
- **calendar-ingestor** (8086): Economic calendar processing
- **reentry-matrix-svc** (8087): Re-entry decision logic
- **reporter** (8088): Metrics and P&L analysis
- **gui-gateway** (8080): API gateway for operator UI
- **compliance-monitor** (9201): Regulatory compliance monitoring

### Infrastructure Services
- **Redis** (6379): Message bus for event-driven communication
- **PostgreSQL** (5432): Persistent data storage
- **Prometheus** (9090): Metrics collection
- **Grafana** (3000): Monitoring dashboards

## Directory Structure

```
deploy/kubernetes/
├── namespaces/             # Namespace definitions
├── secrets/               # Secret templates (use external secret management)
├── configmaps/            # Configuration maps
├── storage/               # Persistent volumes and storage classes
├── deployments/           # Application deployments
├── services/              # Kubernetes services
├── ingress/               # Ingress controllers and routing
├── monitoring/            # Monitoring stack configurations
├── istio/                # Service mesh configurations
│   ├── gateways/         # Istio gateways
│   ├── virtual-services/ # Traffic routing rules
│   ├── destination-rules/# Load balancing and circuit breakers
│   ├── peer-authentication/ # mTLS configuration
│   └── authorization-policies/ # Security policies
└── README.md             # This file
```

## Prerequisites

Before deploying, ensure you have:

1. **Kubernetes Cluster**: v1.24+ with sufficient resources
2. **kubectl**: Configured to access your cluster
3. **Istio Service Mesh**: v1.18+ installed (optional but recommended)
4. **Cert-Manager**: For automatic TLS certificate management
5. **Ingress Controller**: NGINX Ingress Controller recommended
6. **External Secret Management**: Vault, AWS Secrets Manager, or similar

### Resource Requirements

**Minimum Production Requirements**:
- **CPU**: 12 cores total
- **Memory**: 24GB total  
- **Storage**: 150GB persistent storage
- **Network**: Low latency between nodes

**Recommended Production Requirements**:
- **CPU**: 24 cores total
- **Memory**: 48GB total
- **Storage**: 500GB persistent storage with SSD
- **Network**: Dedicated VLAN with sub-millisecond latency

## Quick Start

### 1. Basic Deployment (Without Istio)

```bash
# Create namespace
kubectl apply -f namespaces/

# Create storage resources
kubectl apply -f storage/

# Create secrets (replace with your secret management system)
kubectl apply -f secrets/

# Create configuration maps
kubectl apply -f configmaps/

# Deploy infrastructure services
kubectl apply -f deployments/infrastructure.yml
kubectl apply -f services/infrastructure-services.yml

# Wait for infrastructure to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n eafix-trading --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgres -n eafix-trading --timeout=300s

# Deploy trading services
kubectl apply -f deployments/trading-services.yml
kubectl apply -f deployments/supporting-services.yml
kubectl apply -f services/trading-services.yml

# Create ingress
kubectl apply -f ingress/

# Verify deployment
kubectl get pods -n eafix-trading
kubectl get services -n eafix-trading
```

### 2. Advanced Deployment (With Istio Service Mesh)

```bash
# Ensure Istio is installed
istioctl install --set values.defaultRevision=default

# Label namespace for Istio injection
kubectl label namespace eafix-trading istio-injection=enabled

# Deploy base resources
kubectl apply -f namespaces/
kubectl apply -f storage/
kubectl apply -f secrets/
kubectl apply -f configmaps/

# Deploy infrastructure
kubectl apply -f deployments/infrastructure.yml
kubectl apply -f services/infrastructure-services.yml

# Wait for infrastructure
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n eafix-trading --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgres -n eafix-trading --timeout=300s

# Deploy trading services
kubectl apply -f deployments/trading-services.yml
kubectl apply -f deployments/supporting-services.yml
kubectl apply -f services/trading-services.yml

# Configure Istio service mesh
kubectl apply -f istio/gateways/
kubectl apply -f istio/virtual-services/
kubectl apply -f istio/destination-rules/
kubectl apply -f istio/peer-authentication/
kubectl apply -f istio/authorization-policies/

# Verify Istio configuration
istioctl analyze -n eafix-trading
```

### 3. Helm Deployment (Recommended)

```bash
# Add required Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install the EAFIX trading system
cd ../helm/
helm install eafix-trading ./eafix-trading \
  --namespace eafix-trading \
  --create-namespace \
  --values values.yaml \
  --set global.imageRegistry=ghcr.io \
  --set image.tag=v0.1.0

# Monitor deployment
helm status eafix-trading -n eafix-trading
kubectl get pods -n eafix-trading -w
```

## Configuration

### Environment Variables

Key environment variables for trading services:

```yaml
# Redis Configuration
SERVICE_REDIS_URL: "redis://redis:6379"
REDIS_PASSWORD: "<from-secret>"

# Database Configuration  
SERVICE_POSTGRES_URL: "postgresql://username:password@postgres:5432/eafix_trading"

# Service Discovery
SERVICE_RISK_MANAGER_URL: "http://risk-manager:8084"
SERVICE_EXECUTION_ENGINE_URL: "http://execution-engine:8085"

# Logging
SERVICE_LOG_LEVEL: "INFO"
```

### Resource Allocation

Services are configured with the following resource allocations:

| Service | CPU Request | Memory Request | CPU Limit | Memory Limit |
|---------|-------------|----------------|-----------|--------------|
| data-ingestor | 200m | 256Mi | 500m | 512Mi |
| indicator-engine | 300m | 512Mi | 700m | 1Gi |
| signal-generator | 200m | 256Mi | 500m | 512Mi |
| risk-manager | 300m | 512Mi | 700m | 1Gi |
| execution-engine | 200m | 256Mi | 500m | 512Mi |
| gui-gateway | 200m | 256Mi | 500m | 512Mi |

### Health Checks

All services implement comprehensive health checks:

- **Liveness Probe**: HTTP GET `/healthz` (30s initial delay, 10s period)
- **Readiness Probe**: HTTP GET `/healthz` (5s initial delay, 5s period)

## Security

### Secret Management

**IMPORTANT**: Never commit actual secrets to version control. Use one of these approaches:

#### Option 1: External Secret Operator (Recommended)
```bash
# Install External Secrets Operator
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace

# Create SecretStore and ExternalSecret resources
kubectl apply -f secrets/external-secret-store.yml
```

#### Option 2: Sealed Secrets
```bash
# Install Sealed Secrets
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml

# Encrypt your secrets
kubeseal --format=yaml < secrets/trading-secrets.yml > secrets/sealed-trading-secrets.yml
```

### Network Security

The deployment includes comprehensive network security:

1. **Network Policies**: Restrict traffic between pods
2. **Istio mTLS**: Mutual TLS for all service communication
3. **Authorization Policies**: Fine-grained access control
4. **Ingress Security**: Rate limiting and security headers

### Pod Security

- **Security Context**: Non-root containers with read-only root filesystems
- **Resource Limits**: Prevent resource exhaustion attacks
- **Network Policies**: Restrict network access
- **Pod Security Standards**: Enforced at namespace level

## Monitoring

### Prometheus Metrics

All services expose metrics at `/metrics` endpoint:

```bash
# Check service metrics
kubectl port-forward svc/data-ingestor 8081:8081 -n eafix-trading
curl http://localhost:8081/metrics
```

### Grafana Dashboards

Import the provided Grafana dashboards from `../observability/grafana/dashboards/`.

### Alerting

Alerts are configured in `../observability/alertmanager.yml` with:
- Critical trading system alerts
- SLO violation notifications  
- Compliance monitoring alerts
- Infrastructure health alerts

## Troubleshooting

### Common Issues

#### 1. Pods in CrashLoopBackOff
```bash
# Check pod logs
kubectl logs <pod-name> -n eafix-trading
kubectl describe pod <pod-name> -n eafix-trading

# Check events
kubectl get events -n eafix-trading --sort-by=.metadata.creationTimestamp
```

#### 2. Service Communication Issues
```bash
# Test service connectivity
kubectl exec -it <source-pod> -n eafix-trading -- curl http://target-service:port/healthz

# Check DNS resolution
kubectl exec -it <pod> -n eafix-trading -- nslookup target-service
```

#### 3. Istio Configuration Issues
```bash
# Analyze Istio configuration
istioctl analyze -n eafix-trading

# Check proxy configuration
istioctl proxy-config cluster <pod-name> -n eafix-trading
istioctl proxy-config routes <pod-name> -n eafix-trading
```

#### 4. Redis Connection Issues
```bash
# Test Redis connectivity
kubectl exec -it redis-0 -n eafix-trading -- redis-cli ping

# Check Redis authentication
kubectl exec -it redis-0 -n eafix-trading -- redis-cli -a $(kubectl get secret trading-secrets -o jsonpath='{.data.REDIS_PASSWORD}' | base64 -d) ping
```

#### 5. Database Connection Issues
```bash
# Test PostgreSQL connectivity
kubectl exec -it postgres-0 -n eafix-trading -- psql -U $(kubectl get secret trading-secrets -o jsonpath='{.data.POSTGRES_USER}' | base64 -d) -d eafix_trading -c "\l"
```

### Debug Commands

```bash
# View all resources in namespace
kubectl get all -n eafix-trading

# Check resource utilization
kubectl top pods -n eafix-trading
kubectl top nodes

# View service mesh status
istioctl proxy-status -n eafix-trading

# Check certificate status (with cert-manager)
kubectl get certificates -n eafix-trading
kubectl describe certificate trading-eafix-tls -n eafix-trading
```

### Performance Tuning

#### JVM Services
```yaml
env:
- name: JAVA_OPTS
  value: "-Xms512m -Xmx1g -XX:+UseG1GC -XX:MaxGCPauseMillis=100"
```

#### Redis Tuning
```yaml
# In redis ConfigMap
data:
  redis.conf: |
    maxmemory-policy allkeys-lru
    tcp-keepalive 300
    save 900 1
```

#### PostgreSQL Tuning
```yaml
env:
- name: POSTGRES_INITDB_ARGS
  value: "--data-checksums"
- name: POSTGRESQL_SHARED_PRELOAD_LIBRARIES
  value: "pg_stat_statements"
```

## Backup and Recovery

### Database Backup
```bash
# Create database backup
kubectl exec -it postgres-0 -n eafix-trading -- pg_dump -U $(kubectl get secret trading-secrets -o jsonpath='{.data.POSTGRES_USER}' | base64 -d) eafix_trading > backup.sql

# Restore from backup
kubectl exec -i postgres-0 -n eafix-trading -- psql -U $(kubectl get secret trading-secrets -o jsonpath='{.data.POSTGRES_USER}' | base64 -d) eafix_trading < backup.sql
```

### Redis Backup
```bash
# Create Redis backup
kubectl exec -it redis-0 -n eafix-trading -- redis-cli -a $(kubectl get secret trading-secrets -o jsonpath='{.data.REDIS_PASSWORD}' | base64 -d) --rdb dump.rdb
```

## Scaling

### Horizontal Pod Autoscaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: signal-generator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: signal-generator
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Manual Scaling
```bash
# Scale deployment
kubectl scale deployment signal-generator --replicas=5 -n eafix-trading

# Scale with Helm
helm upgrade eafix-trading ./eafix-trading --set services.signalGenerator.replicas=5
```

## Maintenance

### Rolling Updates
```bash
# Update image version
kubectl set image deployment/data-ingestor data-ingestor=ghcr.io/dicky1987/eafix-modular/data-ingestor:v0.1.1 -n eafix-trading

# Monitor rollout
kubectl rollout status deployment/data-ingestor -n eafix-trading

# Rollback if necessary
kubectl rollout undo deployment/data-ingestor -n eafix-trading
```

### Cluster Upgrade
```bash
# Drain nodes safely
kubectl cordon <node-name>
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Verify deployment after upgrade
kubectl get pods -n eafix-trading
helm test eafix-trading -n eafix-trading
```

## Support

For production deployment support:
- **Emergency Issues**: trading-ops@eafix.com
- **General Support**: support@eafix.com  
- **Security Issues**: security@eafix.com

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Istio Documentation](https://istio.io/latest/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [EAFIX Trading System Architecture](../../docs/architecture/README.md)