# doc_id: DOC-DOC-0020
# DOC_ID: DOC-SERVICE-0001
# services/common/base_enterprise_service.py

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

import uvloop
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import structlog

from .service_config import ServiceConfig
from .health_checks import HealthCheckManager
from .metrics import MetricsCollector
from .circuit_breaker import CircuitBreaker


@dataclass
class ServiceMetadata:
    """Service identification and configuration"""
    name: str
    version: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    health_check_interval: int = 30
    circuit_breaker_enabled: bool = True
    metrics_enabled: bool = True


class BaseEnterpriseService(ABC):
    """
    Enterprise service foundation providing:
    - Automatic health checks
    - Prometheus metrics
    - Circuit breaker pattern
    - Structured logging
    - Graceful shutdown
    
    Usage: Inherit and implement service_logic()
    """
    
    def __init__(self, metadata: ServiceMetadata, config: ServiceConfig):
        self.metadata = metadata
        self.config = config
        self.logger = structlog.get_logger(service=metadata.name)
        
        # Core components
        self.app = FastAPI(
            title=metadata.name,
            description=metadata.description,
            version=metadata.version
        )
        
        self.health_manager = HealthCheckManager(self)
        self.metrics = MetricsCollector(metadata.name) if metadata.metrics_enabled else None
        self.circuit_breaker = CircuitBreaker() if metadata.circuit_breaker_enabled else None
        
        # Service state
        self._is_ready = False
        self._is_healthy = True
        self._shutdown_event = asyncio.Event()
        
        self._setup_middleware()
        self._setup_routes()
        
    def _setup_middleware(self):
        """Configure middleware for observability and security"""
        
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Request timing middleware
        @self.app.middleware("http")
        async def timing_middleware(request: Request, call_next):
            start_time = time.time()
            
            if self.metrics:
                self.metrics.requests_total.inc()
                
            try:
                response = await call_next(request)
                duration = time.time() - start_time
                
                if self.metrics:
                    self.metrics.request_duration.observe(duration)
                    
                self.logger.info(
                    "request_completed",
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration=duration
                )
                
                return response
                
            except Exception as e:
                duration = time.time() - start_time
                
                if self.metrics:
                    self.metrics.request_errors.inc()
                    
                self.logger.error(
                    "request_failed",
                    method=request.method,
                    path=request.url.path,
                    duration=duration,
                    error=str(e)
                )
                raise
    
    def _setup_routes(self):
        """Setup standard enterprise endpoints"""
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            if not self._is_healthy:
                raise HTTPException(status_code=503, detail="Service unhealthy")
            return {"status": "healthy", "service": self.metadata.name}
        
        @self.app.get("/ready")
        async def ready():
            """Readiness check endpoint"""
            if not self._is_ready:
                raise HTTPException(status_code=503, detail="Service not ready")
            return {"status": "ready", "service": self.metadata.name}
        
        @self.app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint"""
            if not self.metrics:
                return {"message": "Metrics disabled"}
            return generate_latest()
        
        @self.app.get("/info")
        async def info():
            """Service information endpoint"""
            return {
                "name": self.metadata.name,
                "version": self.metadata.version,
                "description": self.metadata.description,
                "dependencies": self.metadata.dependencies,
                "uptime": time.time() - self._start_time if hasattr(self, '_start_time') else 0
            }
    
    @abstractmethod
    async def service_logic(self):
        """
        Implement your service's core logic here.
        This method will be called during startup.
        """
        pass
    
    @abstractmethod
    async def cleanup(self):
        """
        Cleanup resources when service shuts down.
        Override to implement custom cleanup logic.
        """
        pass
    
    async def startup(self):
        """Service startup sequence"""
        self._start_time = time.time()
        
        self.logger.info("service_starting", version=self.metadata.version)
        
        try:
            # Initialize health checks
            await self.health_manager.start()
            
            # Run service-specific logic
            await self.service_logic()
            
            # Mark as ready
            self._is_ready = True
            
            self.logger.info("service_started", startup_time=time.time() - self._start_time)
            
        except Exception as e:
            self.logger.error("service_startup_failed", error=str(e))
            self._is_healthy = False
            raise
    
    async def shutdown(self):
        """Graceful shutdown sequence"""
        self.logger.info("service_shutting_down")
        
        try:
            # Mark as not ready
            self._is_ready = False
            
            # Stop accepting new work
            self._shutdown_event.set()
            
            # Run cleanup
            await self.cleanup()
            
            # Stop health checks
            await self.health_manager.stop()
            
            self.logger.info("service_shutdown_complete")
            
        except Exception as e:
            self.logger.error("service_shutdown_error", error=str(e))
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """FastAPI lifespan manager"""
        await self.startup()
        yield
        await self.shutdown()
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the service with uvicorn"""
        import uvicorn
        
        # Use uvloop for better performance
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        
        # Apply lifespan to app
        self.app.router.lifespan_context = self.lifespan
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_config=None,  # Use structlog
            access_log=False  # We handle logging in middleware
        )
    
    @property
    def is_ready(self) -> bool:
        return self._is_ready
    
    @property
    def is_healthy(self) -> bool:
        return self._is_healthy
    
    def mark_unhealthy(self, reason: str = ""):
        """Mark service as unhealthy"""
        self._is_healthy = False
        self.logger.warning("service_marked_unhealthy", reason=reason)