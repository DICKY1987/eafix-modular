---
doc_id: DOC-DOC-0008
---

# EAFIX Trading System - Helm Chart

This Helm chart deploys the EAFIX trading system with comprehensive production-ready configurations including security, observability, and scalability features.

## Overview

The EAFIX trading system is a microservices-based financial trading platform that processes real-time market data, generates trading signals, manages risk, and executes trades through broker interfaces.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- Persistent storage support
- Ingress controller (NGINX recommended)
- Cert-manager (for TLS certificates)

## Installing the Chart

### Quick Start

```bash
# Add required repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install with default values
helm install eafix-trading ./eafix-trading \
  --namespace eafix-trading \
  --create-namespace
```

### Production Installation

```bash
# Create custom values file
cat > production-values.yaml <<EOF
environment:
  name: "production"
  logLevel: "WARN"

services:
  dataIngestor:
    replicas: 3
  signalGenerator:
    replicas: 3
  riskManager:
    replicas: 3

ingress:
  enabled: true
  hosts:
    - host: trading.yourcompany.com
      paths:
        - path: /
          service: gui-gateway
          port: 8080

monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 20

redis:
  auth:
    password: "your-secure-redis-password"

postgresql:
  auth:
    postgresPassword: "your-secure-postgres-password"
EOF

# Install with production configuration
helm install eafix-trading ./eafix-trading \
  --namespace eafix-trading \
  --create-namespace \
  --values production-values.yaml \
  --set global.imageRegistry=ghcr.io \
  --set image.tag=v0.1.0
```

## Configuration

### Global Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.imageRegistry` | Global Docker registry | `ghcr.io` |
| `global.imagePullSecrets` | Global image pull secrets | `[]` |
| `global.storageClass` | Global storage class | `""` |

### Image Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.registry` | Image registry | `ghcr.io` |
| `image.repository` | Image repository | `dicky1987/eafix-modular` |
| `image.tag` | Image tag | `v0.1.0` |
| `image.pullPolicy` | Image pull policy | `Always` |

### Service Configuration

Each trading service can be configured with:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `services.<serviceName>.enabled` | Enable/disable service | `true` |
| `services.<serviceName>.replicas` | Number of replicas | Varies by service |
| `services.<serviceName>.resources` | Resource requests/limits | See values.yaml |

#### Available Services

- `dataIngestor`: Price feed ingestion (port 8081)
- `indicatorEngine`: Technical indicators (port 8082)  
- `signalGenerator`: Trading signals (port 8083)
- `riskManager`: Risk management (port 8084)
- `executionEngine`: Order execution (port 8085)
- `calendarIngestor`: Economic calendar (port 8086)
- `reentryMatrixSvc`: Re-entry decisions (port 8087)
- `reporter`: Analytics and reporting (port 8088)
- `guiGateway`: API gateway (port 8080)
- `complianceMonitor`: Compliance monitoring (port 8080, metrics 9201)

### Infrastructure Services

#### Redis Configuration

```yaml
redis:
  enabled: true
  architecture: standalone
  auth:
    enabled: true
    password: "secure-password"  # Use external secrets in production
  master:
    persistence:
      enabled: true
      size: 20Gi
    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "1"
```

#### PostgreSQL Configuration

```yaml
postgresql:
  enabled: true
  auth:
    postgresPassword: "secure-password"  # Use external secrets in production
    database: "eafix_trading"
  primary:
    persistence:
      enabled: true
      size: 100Gi
    resources:
      requests:
        memory: "2Gi"
        cpu: "1"
      limits:
        memory: "4Gi"
        cpu: "2"
```

### Security Configuration

#### Service Account

```yaml
serviceAccount:
  create: true
  name: ""
  annotations: {}
```

#### Security Context

```yaml
podSecurityContext:
  fsGroup: 1000
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000
```

#### Network Policies

```yaml
networkPolicy:
  enabled: true
  ingress: []
  egress: []
```

### Ingress Configuration

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: trading.eafix.com
      paths:
        - path: /
          pathType: Prefix
          service: gui-gateway
          port: 8080
  tls:
    - secretName: trading-eafix-tls
      hosts:
        - trading.eafix.com
```

### Monitoring Configuration

```yaml
monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true
  alertmanager:
    enabled: true
```

### Autoscaling Configuration

```yaml
autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

### Service Mesh (Istio) Configuration

```yaml
serviceMesh:
  enabled: false
  istio:
    sidecarInjection: true
    virtualServices:
      enabled: true
    destinationRules:
      enabled: true
    peerAuthentication:
      enabled: true
      mtlsMode: STRICT
```

## Upgrading

### Minor Version Upgrade

```bash
# Update image tag
helm upgrade eafix-trading ./eafix-trading \
  --namespace eafix-trading \
  --set image.tag=v0.1.1 \
  --reuse-values
```

### Major Version Upgrade

```bash
# Backup current configuration
helm get values eafix-trading -n eafix-trading > current-values.yaml

# Upgrade with new chart version
helm upgrade eafix-trading ./eafix-trading \
  --namespace eafix-trading \
  --values current-values.yaml \
  --set image.tag=v0.2.0
```

### Rolling Back

```bash
# List revisions
helm history eafix-trading -n eafix-trading

# Rollback to previous version
helm rollback eafix-trading 1 -n eafix-trading
```

## Scaling

### Manual Scaling

```bash
# Scale individual service
helm upgrade eafix-trading ./eafix-trading \
  --set services.signalGenerator.replicas=5 \
  --reuse-values
```

### Auto Scaling

Enable Horizontal Pod Autoscaler:

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
```

## Monitoring and Observability

### Prometheus Metrics

All services expose metrics at `/metrics`:

```bash
# Port forward to access metrics
kubectl port-forward svc/data-ingestor 8081:8081 -n eafix-trading
curl http://localhost:8081/metrics
```

### Grafana Dashboards

The chart includes predefined Grafana dashboards for:
- Trading system overview
- Service performance metrics
- Infrastructure monitoring
- Business KPIs

### Health Checks

All services include:
- Liveness probes: `/healthz`
- Readiness probes: `/healthz`
- Startup probes for slower starting services

## Troubleshooting

### Common Issues

#### 1. ImagePullBackOff

```bash
# Check image registry credentials
kubectl get pods -n eafix-trading
kubectl describe pod <pod-name> -n eafix-trading

# Update image pull secrets
helm upgrade eafix-trading ./eafix-trading \
  --set global.imagePullSecrets[0].name=my-registry-secret \
  --reuse-values
```

#### 2. PersistentVolume Issues

```bash
# Check PVC status
kubectl get pvc -n eafix-trading

# Update storage class
helm upgrade eafix-trading ./eafix-trading \
  --set global.storageClass=fast-ssd \
  --reuse-values
```

#### 3. Service Communication Issues

```bash
# Test service connectivity
helm test eafix-trading -n eafix-trading

# Check service endpoints
kubectl get endpoints -n eafix-trading
```

### Debug Commands

```bash
# View all resources
kubectl get all -n eafix-trading

# Check Helm release status
helm status eafix-trading -n eafix-trading

# View rendered templates
helm template eafix-trading ./eafix-trading --debug
```

## Security Best Practices

### Secret Management

Never store secrets in values files. Use external secret management:

```yaml
secrets:
  create: false
  external:
    enabled: true
    backendType: vault
    secretStore: "vault-backend"
```

### Resource Limits

Always set resource limits:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Security Context

Use non-root containers:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
```

## Testing

### Helm Tests

Run included tests:

```bash
helm test eafix-trading -n eafix-trading
```

### Integration Tests

```bash
# Port forward to GUI gateway
kubectl port-forward svc/gui-gateway 8080:8080 -n eafix-trading

# Test API endpoints
curl http://localhost:8080/healthz
curl http://localhost:8080/api/v1/system/status
```

## Uninstalling

```bash
# Uninstall release
helm uninstall eafix-trading -n eafix-trading

# Clean up namespace (if desired)
kubectl delete namespace eafix-trading
```

## Values Reference

For a complete list of configurable values, see:
- `values.yaml`: Default configuration
- `values-production.yaml`: Production-optimized settings
- `values-development.yaml`: Development-friendly settings

## Support

- **Documentation**: See `deploy/kubernetes/README.md` for detailed Kubernetes deployment guide
- **Issues**: Report issues in the GitHub repository
- **Emergency**: trading-ops@eafix.com