# Deployment & Rollback Runbook

## 🚀 Deployment Overview

This runbook covers deployment procedures, rollback strategies, and release management for the EAFIX trading system. All deployments must follow the procedures outlined here to ensure trading system stability.

## 📋 Pre-Deployment Checklist

### Development Environment Validation
```bash
# 1. All tests pass
make test-all
make contracts-test

# 2. Code quality checks pass
make lint
make format

# 3. Security scans pass
make security-scan

# 4. Performance benchmarks meet SLAs
make performance-test

# 5. Contract validation passes
make contracts-validate-full
```

### Staging Environment Validation
```bash
# 1. Deploy to staging
make deploy-staging

# 2. Smoke tests pass
make smoke-staging

# 3. Integration tests pass
make integration-test-staging

# 4. Load tests meet requirements
make load-test-staging --target-rps=100 --duration=300s
```

### Production Readiness
```bash
# 1. Database migrations tested
make db-migration-dry-run

# 2. Configuration validated
make validate-prod-config

# 3. Monitoring alerts configured
make validate-alerts

# 4. Rollback plan prepared
make prepare-rollback-plan
```

## 🔄 Deployment Strategies

### Blue-Green Deployment (Recommended)
Blue-Green deployment ensures zero-downtime deployments by maintaining two identical production environments.

```bash
# 1. Deploy to green environment
make deploy-green

# 2. Validate green environment
make validate-green-deployment

# 3. Switch traffic to green
make switch-to-green

# 4. Monitor for issues (15-minute observation period)
make monitor-deployment --duration=15m

# 5. Decommission blue environment (after 24h stability)
make decommission-blue
```

### Rolling Deployment
For updates that don't require database changes:

```bash
# 1. Rolling update with health checks
make rolling-deploy --max-unavailable=1 --health-check-timeout=60s

# 2. Validate each service as it comes online
make validate-rolling-deployment
```

### Canary Deployment
For high-risk changes:

```bash
# 1. Deploy to 10% of traffic
make canary-deploy --traffic-percentage=10

# 2. Monitor key metrics for 2 hours
make monitor-canary --duration=2h --metrics=latency,error_rate,trading_pnl

# 3. Gradually increase traffic
make canary-promote --traffic-percentage=50
make canary-promote --traffic-percentage=100
```

## 🐳 Docker Deployment

### Container Image Management
```bash
# 1. Build all service images
make docker-build-all

# 2. Tag images with version
docker tag eafix/data-ingestor:latest eafix/data-ingestor:v1.2.3
docker tag eafix/signal-generator:latest eafix/signal-generator:v1.2.3

# 3. Push to registry
make docker-push-all --version=v1.2.3

# 4. Update docker-compose.yml with specific versions
sed -i 's/:latest/:v1.2.3/g' deploy/compose/docker-compose.yml
```

### Service-by-Service Deployment
```bash
# Deploy individual services with zero downtime
make deploy-service SERVICE=data-ingestor VERSION=v1.2.3

# Validation after each service deployment
curl http://localhost:8081/healthz
make validate-service SERVICE=data-ingestor
```

## ☸️ Kubernetes Deployment

### Helm Chart Deployment
```bash
# 1. Update Helm values for production
helm upgrade --install eafix-prod ./deploy/helm/eafix \
  --namespace=eafix-prod \
  --values=deploy/helm/values-prod.yaml \
  --atomic \
  --timeout=600s

# 2. Validate deployment
kubectl rollout status deployment/data-ingestor -n eafix-prod
kubectl rollout status deployment/signal-generator -n eafix-prod

# 3. Run smoke tests
kubectl run smoke-test --image=eafix/smoke-test:latest --rm -it -n eafix-prod
```

### Service Mesh Deployment (Istio)
```bash
# 1. Deploy with traffic splitting
kubectl apply -f deploy/k8s/istio-virtual-service.yaml

# 2. Gradually shift traffic
kubectl patch virtualservice eafix-vs -n eafix-prod --type=json \
  -p='[{"op": "replace", "path": "/spec/http/0/match/0/weight", "value": 50}]'

# 3. Monitor service mesh metrics
kubectl port-forward -n istio-system svc/kiali 20001:20001
```

## 🗄️ Database Migrations

### Pre-Migration Validation
```bash
# 1. Create database backup
pg_dump -h prod-db -U eafix eafix_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Test migration on staging
psql -h staging-db -U eafix -d eafix_staging -f migrations/v1.2.3.sql

# 3. Validate migration rollback
psql -h staging-db -U eafix -d eafix_staging -f migrations/rollback_v1.2.3.sql
```

### Production Migration
```bash
# 1. Enable maintenance mode (if required)
curl -X POST http://localhost:8080/maintenance/enable

# 2. Run migration with monitoring
psql -h prod-db -U eafix -d eafix_prod -f migrations/v1.2.3.sql

# 3. Validate data integrity
python scripts/validation/validate-migration.py --version=v1.2.3

# 4. Disable maintenance mode
curl -X POST http://localhost:8080/maintenance/disable
```

## 🔄 Configuration Management

### Environment-Specific Configurations
```bash
# 1. Validate configuration files
make validate-config ENV=production

# 2. Deploy configurations
kubectl create configmap eafix-config \
  --from-file=config/production/ \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Restart services to pick up new config
kubectl rollout restart deployment/signal-generator -n eafix-prod
```

### Secret Management
```bash
# 1. Update secrets in vault/k8s secrets
kubectl create secret generic eafix-secrets \
  --from-literal=db-password='new-secure-password' \
  --from-literal=api-key='new-api-key' \
  --dry-run=client -o yaml | kubectl apply -f -

# 2. Restart affected services
kubectl rollout restart deployment --selector=app=eafix -n eafix-prod
```

## 🔙 Rollback Procedures

### Immediate Rollback (Emergency)
```bash
# 1. Immediate rollback to previous version
make emergency-rollback

# 2. Verify rollback successful
make validate-rollback

# 3. Notify stakeholders
make notify-emergency-rollback --reason="Critical issue in v1.2.3"
```

### Docker Rollback
```bash
# 1. Identify previous working version
docker images eafix/signal-generator --format "table {{.Tag}}\t{{.CreatedAt}}"

# 2. Update docker-compose to previous version
sed -i 's/:v1.2.3/:v1.2.2/g' deploy/compose/docker-compose.yml

# 3. Rolling restart with previous version
docker compose up -d --no-deps signal-generator

# 4. Validate rollback
curl http://localhost:8083/healthz
```

### Kubernetes Rollback
```bash
# 1. Check rollout history
kubectl rollout history deployment/signal-generator -n eafix-prod

# 2. Rollback to previous version
kubectl rollout undo deployment/signal-generator -n eafix-prod

# 3. Rollback to specific revision
kubectl rollout undo deployment/signal-generator --to-revision=2 -n eafix-prod

# 4. Validate rollback
kubectl rollout status deployment/signal-generator -n eafix-prod
```

### Database Rollback
```bash
# 1. Stop application writes
curl -X POST http://localhost:8080/maintenance/enable

# 2. Restore database from backup
pg_restore -h prod-db -U eafix -d eafix_prod backup_20241201_143022.sql

# 3. Run rollback migration if needed
psql -h prod-db -U eafix -d eafix_prod -f migrations/rollback_v1.2.3.sql

# 4. Re-enable application
curl -X POST http://localhost:8080/maintenance/disable
```

## 📊 Deployment Monitoring

### Key Metrics to Monitor
```bash
# 1. Service availability
watch -n 10 'curl -s http://localhost:8080/health | jq .status'

# 2. Response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8083/api/signals

# 3. Error rates
curl http://localhost:9090/api/v1/query?query='rate(http_requests_total{status=~"5.."}[5m])'

# 4. Trading-specific metrics
curl http://localhost:8083/metrics | grep signals_generated_total
```

### Automated Deployment Validation
```bash
#!/bin/bash
# deployment-validation.sh

VERSION=$1
TIMEOUT=300

echo "Validating deployment version $VERSION..."

# Wait for all services to be healthy
for i in {1..10}; do
    if make smoke; then
        echo "All services healthy"
        break
    fi
    sleep 30
done

# Run integration tests
if make integration-test; then
    echo "Integration tests passed"
else
    echo "Integration tests failed - triggering rollback"
    make emergency-rollback
    exit 1
fi

# Monitor for 5 minutes
python scripts/monitoring/deployment-monitor.py --duration=300 --threshold=error_rate:0.05,latency_p95:1000ms

echo "Deployment validation completed successfully"
```

## 🔐 Security Considerations

### Pre-Deployment Security Checks
```bash
# 1. Container image vulnerability scanning
trivy image eafix/signal-generator:v1.2.3

# 2. Configuration security validation
make security-config-scan

# 3. Secret rotation (if needed)
make rotate-secrets --dry-run

# 4. Network policy validation
kubectl auth can-i '*' '*' --as=system:serviceaccount:eafix-prod:eafix-service
```

### Post-Deployment Security Validation
```bash
# 1. Service mesh security policies
kubectl get peerauthentication -n eafix-prod

# 2. RBAC validation
kubectl auth can-i list pods --as=system:serviceaccount:eafix-prod:eafix-service

# 3. Network connectivity test
kubectl exec -n eafix-prod deploy/signal-generator -- nc -zv data-ingestor 8081
```

## 📈 Performance Validation

### Post-Deployment Performance Tests
```bash
# 1. Latency benchmark
python scripts/performance/latency-benchmark.py --duration=300 --target-p95=500ms

# 2. Throughput test
python scripts/performance/throughput-test.py --duration=300 --target-rps=100

# 3. Load test
python scripts/load-test/gradual-load.py --max-rps=200 --ramp-duration=300

# 4. Trading flow validation
python scripts/e2e/trading-flow-test.py --iterations=100
```

### Performance Regression Detection
```bash
# Compare performance before and after deployment
python scripts/performance/regression-detector.py \
  --baseline-version=v1.2.2 \
  --current-version=v1.2.3 \
  --threshold=10  # 10% regression threshold
```

## 🚨 Deployment Alerts

### Alert Configuration
```yaml
# deployment-alerts.yaml
groups:
  - name: deployment
    rules:
      - alert: DeploymentFailed
        expr: kube_deployment_status_replicas_unavailable > 0
        for: 5m
        severity: critical

      - alert: HighErrorRateAfterDeployment
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        severity: critical

      - alert: PerformanceRegression
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1.0
        for: 5m
        severity: warning
```

### Automated Rollback Triggers
```bash
# Configure automatic rollback on critical alerts
kubectl create configmap rollback-config \
  --from-literal=error-rate-threshold=0.05 \
  --from-literal=latency-threshold=2.0 \
  --from-literal=rollback-enabled=true \
  -n eafix-prod
```

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing in CI/CD
- [ ] Staging environment validated
- [ ] Database migration tested
- [ ] Rollback plan prepared
- [ ] Monitoring alerts configured
- [ ] Change request approved
- [ ] Deployment window scheduled
- [ ] Team notifications sent

### During Deployment
- [ ] Maintenance mode enabled (if required)
- [ ] Database backup created
- [ ] Services deployed in correct order
- [ ] Health checks passing
- [ ] Smoke tests executed
- [ ] Performance validation completed
- [ ] Security validation completed

### Post-Deployment
- [ ] All services healthy
- [ ] Integration tests passing
- [ ] Trading flow validated
- [ ] Performance within SLAs
- [ ] Monitoring showing green
- [ ] Documentation updated
- [ ] Team notifications sent
- [ ] Change request closed

## 🔄 Continuous Deployment (CD)

### GitOps Workflow
```bash
# 1. Code merged to main triggers CD pipeline
git push origin main

# 2. Automated testing and building
# (Handled by GitHub Actions)

# 3. Automatic deployment to staging
# (Triggered by successful tests)

# 4. Manual approval for production
# (GitHub Environment Protection Rules)

# 5. Automatic deployment to production
# (After approval)
```

### ArgoCD Configuration
```yaml
# argocd-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: eafix-prod
spec:
  source:
    repoURL: https://github.com/company/eafix-modular
    path: deploy/k8s
    targetRevision: main
  destination:
    server: https://kubernetes.default.svc
    namespace: eafix-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

---

**Document Owner**: Platform Engineering Team  
**Last Updated**: December 2024  
**Next Review**: January 2025  
**Deployment Approvers**: Engineering Manager, Trading Operations Lead