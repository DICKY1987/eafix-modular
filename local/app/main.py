"""
CLI Multi-Rapid Local Development FastAPI Application
"""
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

import redis
import asyncpg
import structlog
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('cli_multi_rapid_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('cli_multi_rapid_request_duration_seconds', 'Request duration')

# Pydantic models
class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    environment: str = "local"

class DatabaseStatus(BaseModel):
    connected: bool
    version: Optional[str] = None
    error: Optional[str] = None

class RedisStatus(BaseModel):
    connected: bool
    version: Optional[str] = None
    error: Optional[str] = None

class SystemStatus(BaseModel):
    database: DatabaseStatus
    redis: RedisStatus
    uptime: float

# FastAPI application
app = FastAPI(
    title="CLI Multi-Rapid Local Development API",
    description="Enterprise orchestration platform local development interface",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
start_time = datetime.now()

# Dependency functions
async def get_redis() -> redis.Redis:
    """Get Redis connection."""
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    return redis.from_url(redis_url, decode_responses=True)

async def get_database():
    """Get database connection."""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/cli_multi_rapid")
    return await asyncpg.connect(db_url)

# Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    REQUEST_COUNT.labels(method="GET", endpoint="/").inc()
    return {
        "service": "CLI Multi-Rapid Local Development API",
        "status": "running",
        "docs": "/docs",
        "health": "/healthz"
    }

@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for container orchestration."""
    REQUEST_COUNT.labels(method="GET", endpoint="/healthz").inc()
    
    with REQUEST_DURATION.time():
        logger.info("Health check requested")
        return HealthResponse()

@app.get("/system-status", response_model=SystemStatus)
async def system_status():
    """Comprehensive system status including all dependencies."""
    REQUEST_COUNT.labels(method="GET", endpoint="/system-status").inc()
    
    # Check database
    db_status = DatabaseStatus(connected=False)
    try:
        conn = await get_database()
        version_result = await conn.fetchval("SELECT version()")
        await conn.close()
        db_status.connected = True
        db_status.version = version_result
        logger.info("Database connection successful", version=version_result)
    except Exception as e:
        db_status.error = str(e)
        logger.error("Database connection failed", error=str(e))

    # Check Redis
    redis_status = RedisStatus(connected=False)
    try:
        r = await get_redis()
        info = r.info()
        redis_status.connected = True
        redis_status.version = info.get("redis_version")
        logger.info("Redis connection successful", version=redis_status.version)
    except Exception as e:
        redis_status.error = str(e)
        logger.error("Redis connection failed", error=str(e))

    uptime = (datetime.now() - start_time).total_seconds()
    
    return SystemStatus(
        database=db_status,
        redis=redis_status,
        uptime=uptime
    )

@app.get("/db-ping")
async def database_ping():
    """Simple database connectivity test."""
    REQUEST_COUNT.labels(method="GET", endpoint="/db-ping").inc()
    
    try:
        conn = await get_database()
        result = await conn.fetchval("SELECT NOW()")
        await conn.close()
        
        return {
            "status": "connected",
            "timestamp": result,
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error("Database ping failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@app.get("/redis-ping")
async def redis_ping():
    """Simple Redis connectivity test."""
    REQUEST_COUNT.labels(method="GET", endpoint="/redis-ping").inc()
    
    try:
        r = await get_redis()
        result = r.ping()
        
        return {
            "status": "connected",
            "ping": result,
            "message": "Redis connection successful"
        }
    except Exception as e:
        logger.error("Redis ping failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"Redis connection failed: {str(e)}")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/artifacts")
async def list_artifacts():
    """List available artifacts from the shared volume."""
    artifacts_dir = "/app/artifacts"
    
    if not os.path.exists(artifacts_dir):
        return {"artifacts": [], "message": "No artifacts directory found"}
    
    try:
        files = []
        for root, dirs, filenames in os.walk(artifacts_dir):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                stat = os.stat(filepath)
                files.append({
                    "name": filename,
                    "path": os.path.relpath(filepath, artifacts_dir),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return {"artifacts": files, "count": len(files)}
    except Exception as e:
        logger.error("Error listing artifacts", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error listing artifacts: {str(e)}")

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with structured logging."""
    logger.error("Unhandled exception", 
                path=request.url.path,
                method=request.method,
                error=str(exc),
                exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)