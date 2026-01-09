# DOC_ID: DOC-SERVICE-0024
"""
Enterprise base service providing monitoring, health checks, and feature flags.
Inherit once, get all enterprise capabilities.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

import structlog
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager


class EnterpriseMetrics:
    """RED Metrics + Business KPIs for any service"""

    def __init__(self, service_name: str):
        self.service_name = service_name

        # RED Metrics (Rate, Errors, Duration)
        self.request_count = Counter(
            f'{service_name}_requests_total',
            'Total requests processed',
            ['method', 'endpoint', 'status']
        )

        self.request_duration = Histogram(
            f'{service_name}_request_duration_seconds',
            'Request processing time',
            ['method', 'endpoint']
        )

        self.error_count = Counter(
            f'{service_name}_errors_total',
            'Total errors encountered',
            ['error_type', 'severity']
        )

        # Business Metrics
        self.business_events = Counter(
            f'{service_name}_business_events_total',
            'Business events processed',
            ['event_type', 'outcome']
        )

        # Health Metrics
        self.health_status = Gauge(
            f'{service_name}_health_status',
            'Service health status (1=healthy, 0=unhealthy)'
        )


class FeatureFlags:
    """Environment-based feature flags with audit logging"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = structlog.get_logger(service=service_name, component="feature_flags")

    def is_enabled(self, flag_name: str, default: bool = False) -> bool:
        """Check if feature flag is enabled with audit logging"""
        env_var = f"FEATURE_{flag_name.upper()}"
        raw_value = os.getenv(env_var, str(default).lower())
        enabled = raw_value.lower() in ('true', '1', 'yes', 'on')

        # Audit log every flag check
        self.logger.info(
            "feature_flag_checked",
            flag_name=flag_name,
            enabled=enabled,
            source=env_var,
            raw_value=raw_value
        )

        return enabled


class BaseEnterpriseService(ABC):
    """
    Base class providing enterprise capabilities to all services.

    Inherit from this class and get:
    - Structured logging with correlation IDs
    - Prometheus metrics (RED + business)
    - Feature flags with audit trails
    - Health checks with dependencies
    - Graceful shutdown handling
    """

    def __init__(self, service_name: str, port: int = 8000):
        self.service_name = service_name
        self.port = port

        # Enterprise capabilities
        self.metrics = EnterpriseMetrics(service_name)
        self.flags = FeatureFlags(service_name)
        self.logger = structlog.get_logger(service=service_name)

        # Health tracking
        self.dependencies_healthy = True
        self.startup_complete = False

        # FastAPI app with monitoring
        self.app = FastAPI(
            title=f"{service_name.title()} Service",
            description=f"Enterprise {service_name} microservice",
            lifespan=self.lifespan
        )

        self._setup_monitoring_endpoints()
        self._setup_middleware()

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Application lifecycle with proper startup/shutdown"""
        try:
            # Startup
            self.logger.info("service_starting", service=self.service_name)
            await self.startup()
            self.startup_complete = True
            self.metrics.health_status.set(1)

            # Start Prometheus metrics server
            start_http_server(self.port + 1000)  # Metrics on port+1000
            self.logger.info("service_started",
                           service=self.service_name,
                           metrics_port=self.port + 1000)

            yield

        finally:
            # Shutdown
            self.logger.info("service_stopping", service=self.service_name)
            await self.shutdown()
            self.metrics.health_status.set(0)
            self.logger.info("service_stopped", service=self.service_name)

    def _setup_monitoring_endpoints(self):
        """Standard monitoring endpoints for all services"""

        @self.app.get("/health")
        async def health_check():
            """Kubernetes health check endpoint"""
            is_healthy = (
                self.startup_complete and
                self.dependencies_healthy and
                await self.check_health()
            )

            status_code = 200 if is_healthy else 503
            self.metrics.health_status.set(1 if is_healthy else 0)

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "service": self.service_name,
                "startup_complete": self.startup_complete,
                "dependencies_healthy": self.dependencies_healthy
            }

        @self.app.get("/feature-flags")
        async def list_feature_flags():
            """Debug endpoint to see all feature flags"""
            flags = {}
            for key, value in os.environ.items():
                if key.startswith('FEATURE_'):
                    flag_name = key[8:].lower()  # Remove FEATURE_ prefix
                    flags[flag_name] = value.lower() in ('true', '1', 'yes', 'on')

            return {"service": self.service_name, "flags": flags}

        @self.app.get("/metrics-summary")
        async def metrics_summary():
            """Human-readable metrics summary"""
            return {
                "service": self.service_name,
                "note": f"Prometheus metrics available at port {self.port + 1000}"
            }

    def _setup_middleware(self):
        """Request/response middleware for automatic metrics"""

        @self.app.middleware("http")
        async def metrics_middleware(request, call_next):
            # Start timing
            with self.metrics.request_duration.labels(
                method=request.method,
                endpoint=request.url.path
            ).time():

                # Process request
                try:
                    response = await call_next(request)
                    status = "success"

                except Exception as e:
                    self.metrics.error_count.labels(
                        error_type=type(e).__name__,
                        severity="error"
                    ).inc()
                    self.logger.error("request_failed",
                                    error=str(e),
                                    path=request.url.path,
                                    method=request.method)
                    raise

                finally:
                    # Record request
                    self.metrics.request_count.labels(
                        method=request.method,
                        endpoint=request.url.path,
                        status=getattr(response, 'status_code', 'error') if 'response' in locals() else 'error'
                    ).inc()

                return response

    # Abstract methods - implement in concrete services
    @abstractmethod
    async def startup(self):
        """Service-specific startup logic"""
        pass

    @abstractmethod
    async def shutdown(self):
        """Service-specific shutdown logic"""
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """Service-specific health check logic"""
        pass

    # Helper methods
    def track_business_event(self, event_type: str, outcome: str = "success"):
        """Track business KPIs"""
        self.metrics.business_events.labels(
            event_type=event_type,
            outcome=outcome
        ).inc()

        self.logger.info("business_event",
                        event_type=event_type,
                        outcome=outcome)