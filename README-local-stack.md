# CLI Multi-Rapid Local Development Stack

## Overview

Enterprise-grade local development environment with comprehensive services for the CLI Multi-Rapid platform.

## Services Included

### **Core Application Stack**
- **FastAPI API** (`localhost:8000`) - Main application with health checks and metrics
- **PostgreSQL + pgvector** (`localhost:5432`) - Database with vector search capabilities  
- **Redis** (`localhost:6379`) - Caching and quota tracking
- **MinIO** (`localhost:9000`) - S3-compatible artifact storage

### **Development Tools**
- **Adminer** (`localhost:8080`) - Database administration interface
- **MinIO Console** (`localhost:9001`) - Object storage management

### **Observability Stack**
- **Prometheus** (`localhost:9090`) - Metrics collection
- **Grafana** (`localhost:3000`) - Dashboards and visualization

## Quick Start

### 1. Setup Environment
```bash
# Copy environment template
cp local/.env.example local/.env

# Edit configuration if needed
code local/.env
```

### 2. Start Services
```bash
# Start all services
docker compose -f local/docker-compose.yml up -d

# Check service status
docker compose -f local/docker-compose.yml ps
```

### 3. Verify Health
```bash
# API health check
curl http://localhost:8000/healthz

# System status (all dependencies)
curl http://localhost:8000/system-status

# Database connectivity
curl http://localhost:8000/db-ping

# Redis connectivity  
curl http://localhost:8000/redis-ping
```

## Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| API Health | http://localhost:8000/healthz | Container health check |
| System Status | http://localhost:8000/system-status | Comprehensive health |
| Adminer | http://localhost:8080 | Database management |
| MinIO Console | http://localhost:9001 | Object storage UI |
| Prometheus | http://localhost:9090 | Metrics collection |
| Grafana | http://localhost:3000 | Monitoring dashboards |

## Default Credentials

### Database (PostgreSQL)
- **User**: `postgres`
- **Password**: `postgres` 
- **Database**: `cli_multi_rapid`

### MinIO
- **Access Key**: `minioadmin`
- **Secret Key**: `minioadmin`

### Grafana
- **Username**: `admin`
- **Password**: `admin`

## VS Code Integration

### Available Tasks
```bash
# Via Command Palette (Ctrl+Shift+P) → "Tasks: Run Task"
- "Local Stack: Start Services"
- "Local Stack: Stop Services" 
- "Local Stack: View Logs"
- "Local Stack: Health Check"
```

### Debug Configuration
Pre-configured launch settings for debugging the FastAPI application with full stack integration.

## Development Workflow

### 1. Code Changes
- FastAPI app code is mounted as volume (`local/app:/app`)
- Changes trigger auto-reload in development mode
- Logs visible via `docker compose logs -f api`

### 2. Database Schema
```bash
# Run migrations (when implemented)
docker compose exec api alembic upgrade head

# Access database directly
docker compose exec postgres psql -U postgres -d cli_multi_rapid
```

### 3. Artifact Storage
- Shared volume: `./artifacts` ↔ `/app/artifacts`
- MinIO buckets: `artifacts`, `workflows`, `backups`
- Access via API: `GET /artifacts`

### 4. Monitoring
- Application metrics: `http://localhost:8000/metrics`
- Prometheus targets: `http://localhost:9090/targets`
- Grafana dashboards: `http://localhost:3000`

## Troubleshooting

### Port Conflicts
If default ports are in use, modify `local/.env`:
```bash
API_PORT=8001
POSTGRES_PORT=5433
# etc.
```

### Service Dependencies
Services start in dependency order:
```
postgres, redis, minio → api → monitoring
```

### Health Checks
All services include health checks. View status:
```bash
docker compose -f local/docker-compose.yml ps
```

### Reset Environment
```bash
# Stop and remove all containers/volumes
docker compose -f local/docker-compose.yml down -v

# Restart fresh
docker compose -f local/docker-compose.yml up -d
```

## Integration with CLI Multi-Rapid

The local stack integrates seamlessly with:
- **Agentic Framework v3** - API endpoints for task execution
- **Workflow Orchestrator** - Artifact storage and retrieval  
- **Cross-language Bridge** - Health monitoring and status
- **VS Code Workflow System** - Debug and development tasks

## Production Readiness

This local stack mirrors the production architecture:
- Container-based deployment
- Health checks and monitoring
- Structured logging and metrics
- Secret management patterns
- Service mesh communication

Use this environment to develop and test features before deploying to production Kubernetes environments.