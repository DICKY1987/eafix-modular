"""
Telemetry Daemon Service

Centralized telemetry collection and health monitoring for all EAFIX services.
Aggregates health metrics, provides system-wide monitoring, alerting capabilities,
and unified observability dashboard.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import redis.asyncio as redis
import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import httpx

from .config import Settings
from .health import HealthChecker
from .metrics import MetricsCollector
from .collector import HealthMetricsCollector
from .aggregator import SystemHealthAggregator
from .alerting import AlertManager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if __debug__ else structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class ServiceHealthRequest(BaseModel):
    """Request for specific service health check."""
    
    service_name: str


class SystemHealthThreshold(BaseModel):
    """Request to update system health thresholds."""
    
    service_name: str
    metric_name: str
    threshold_type: str  # "critical", "warning", "info"
    threshold_value: float


class TelemetryDaemonService:
    """Core telemetry daemon service."""
    
    def __init__(self, settings: Settings, metrics: MetricsCollector, health_checker: HealthChecker):
        self.settings = settings
        self.metrics = metrics
        self.health_checker = health_checker
        
        self.redis_client: Optional[redis.Redis] = None
        self.health_collector = HealthMetricsCollector(settings, metrics)
        self.system_aggregator = SystemHealthAggregator(settings, metrics)
        self.alert_manager = AlertManager(settings, metrics)
        
        self.running = False
        self.collection_task: Optional[asyncio.Task] = None
        self.aggregation_task: Optional[asyncio.Task] = None
        self.alerting_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the telemetry daemon service."""
        if self.running:
            return
        
        logger.info("Starting Telemetry Daemon Service", port=self.settings.service_port)
        
        # Initialize Redis connection
        self.redis_client = redis.from_url(self.settings.redis_url)
        await self.redis_client.ping()
        logger.info("Connected to Redis", url=self.settings.redis_url)
        
        # Start components
        await self.health_collector.start()
        await self.system_aggregator.start()
        await self.alert_manager.start()
        
        # Start background tasks
        if self.settings.health_collection_enabled:
            self.collection_task = asyncio.create_task(self._run_health_collection())
        
        if self.settings.system_aggregation_enabled:
            self.aggregation_task = asyncio.create_task(self._run_system_aggregation())
        
        if self.settings.alerting_enabled:
            self.alerting_task = asyncio.create_task(self._run_alerting())
        
        self.running = True
        self.metrics.increment_counter("service_starts")
        
        logger.info("Telemetry Daemon Service started successfully")
    
    async def stop(self) -> None:
        """Stop the telemetry daemon service."""
        if not self.running:
            return
        
        logger.info("Stopping Telemetry Daemon Service")
        
        # Stop background tasks
        for task in [self.collection_task, self.aggregation_task, self.alerting_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Stop components
        await self.alert_manager.stop()
        await self.system_aggregator.stop()
        await self.health_collector.stop()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        self.running = False
        logger.info("Telemetry Daemon Service stopped")
    
    async def _run_health_collection(self) -> None:
        """Run health metrics collection loop."""
        try:
            while self.running:
                try:
                    await self.health_collector.collect_all_service_health()
                    self.metrics.increment_counter("health_collection_cycles")
                    
                    await asyncio.sleep(self.settings.health_collection_interval_seconds)
                    
                except Exception as e:
                    logger.error("Health collection cycle failed", error=str(e))
                    self.metrics.record_error("health_collection_error")
                    await asyncio.sleep(5)  # Short delay before retry
                    
        except asyncio.CancelledError:
            logger.info("Health collection task cancelled")
        except Exception as e:
            logger.error("Health collection task failed", error=str(e))
    
    async def _run_system_aggregation(self) -> None:
        """Run system health aggregation loop."""
        try:
            while self.running:
                try:
                    await self.system_aggregator.aggregate_system_health()
                    self.metrics.increment_counter("aggregation_cycles")
                    
                    await asyncio.sleep(self.settings.aggregation_interval_seconds)
                    
                except Exception as e:
                    logger.error("System aggregation cycle failed", error=str(e))
                    self.metrics.record_error("aggregation_error")
                    await asyncio.sleep(10)  # Delay before retry
                    
        except asyncio.CancelledError:
            logger.info("System aggregation task cancelled")
        except Exception as e:
            logger.error("System aggregation task failed", error=str(e))
    
    async def _run_alerting(self) -> None:
        """Run alerting loop."""
        try:
            while self.running:
                try:
                    await self.alert_manager.process_alerts()
                    self.metrics.increment_counter("alerting_cycles")
                    
                    await asyncio.sleep(self.settings.alerting_check_interval_seconds)
                    
                except Exception as e:
                    logger.error("Alerting cycle failed", error=str(e))
                    self.metrics.record_error("alerting_error")
                    await asyncio.sleep(15)  # Delay before retry
                    
        except asyncio.CancelledError:
            logger.info("Alerting task cancelled")
        except Exception as e:
            logger.error("Alerting task failed", error=str(e))
    
    async def get_system_health_overview(self) -> Dict[str, Any]:
        """Get comprehensive system health overview."""
        return await self.system_aggregator.get_system_health_overview()
    
    async def get_service_health_details(self, service_name: str) -> Dict[str, Any]:
        """Get detailed health information for a specific service."""
        return await self.health_collector.get_service_health_details(service_name)
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts."""
        return await self.alert_manager.get_active_alerts()
    
    async def update_health_threshold(self, service_name: str, metric_name: str, 
                                    threshold_type: str, threshold_value: float) -> Dict[str, Any]:
        """Update health threshold for a service metric."""
        return await self.alert_manager.update_threshold(
            service_name, metric_name, threshold_type, threshold_value
        )
    
    async def get_telemetry_status(self) -> Dict[str, Any]:
        """Get telemetry daemon status."""
        collector_status = await self.health_collector.get_status()
        aggregator_status = await self.system_aggregator.get_status()
        alert_manager_status = await self.alert_manager.get_status()
        
        return {
            "service": "telemetry-daemon",
            "running": self.running,
            "collection_active": self.collection_task is not None and not self.collection_task.done(),
            "aggregation_active": self.aggregation_task is not None and not self.aggregation_task.done(),
            "alerting_active": self.alerting_task is not None and not self.alerting_task.done(),
            "health_collector": collector_status,
            "system_aggregator": aggregator_status,
            "alert_manager": alert_manager_status,
            "metrics": self.metrics.get_metrics_summary()
        }


# Global service instance
service_instance: Optional[TelemetryDaemonService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle."""
    global service_instance
    
    # Startup
    settings = Settings()
    metrics = MetricsCollector()
    health_checker = HealthChecker(settings, metrics)
    
    service_instance = TelemetryDaemonService(settings, metrics, health_checker)
    
    try:
        await service_instance.start()
        yield
    finally:
        # Shutdown
        if service_instance:
            await service_instance.stop()


# Create FastAPI application
app = FastAPI(
    title="Telemetry Daemon Service",
    description="Centralized health monitoring and alerting for EAFIX trading system",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/healthz")
async def health_check():
    """Liveness probe endpoint."""
    if not service_instance or not service_instance.running:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "healthy", "service": "telemetry-daemon"}


@app.get("/readyz")
async def readiness_check():
    """Readiness probe endpoint."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    health_status = await service_instance.health_checker.get_health_status()
    
    if health_status["overall_status"] != "healthy":
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return health_status


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return service_instance.metrics.get_metrics_summary()


@app.get("/telemetry/system-health")
async def get_system_health():
    """Get comprehensive system health overview."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.get_system_health_overview()


@app.get("/telemetry/service-health/{service_name}")
async def get_service_health(service_name: str):
    """Get detailed health information for a specific service."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await service_instance.get_service_health_details(service_name)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Service not found: {service_name}")
    
    return result


@app.get("/telemetry/alerts")
async def get_active_alerts():
    """Get list of active alerts."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.get_active_alerts()


@app.post("/telemetry/alerts/threshold")
async def update_health_threshold(request: SystemHealthThreshold):
    """Update health threshold for a service metric."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await service_instance.update_health_threshold(
        request.service_name,
        request.metric_name,
        request.threshold_type,
        request.threshold_value
    )
    
    return result


@app.get("/telemetry/dashboard")
async def get_monitoring_dashboard():
    """Get monitoring dashboard data."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    # Get comprehensive dashboard data
    system_health = await service_instance.get_system_health_overview()
    active_alerts = await service_instance.get_active_alerts()
    telemetry_status = await service_instance.get_telemetry_status()
    
    return {
        "dashboard": {
            "timestamp": datetime.utcnow().isoformat(),
            "system_health": system_health,
            "active_alerts": active_alerts,
            "alert_summary": {
                "total_alerts": len(active_alerts),
                "critical_alerts": len([a for a in active_alerts if a.get("severity") == "critical"]),
                "warning_alerts": len([a for a in active_alerts if a.get("severity") == "warning"])
            },
            "telemetry_status": telemetry_status
        }
    }


@app.get("/telemetry/status")
async def get_telemetry_status():
    """Get detailed telemetry daemon status."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.get_telemetry_status()


@app.post("/telemetry/ingest")
async def ingest_health_metric(health_data: Dict[str, Any]):
    """Manually ingest health metric data."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        await service_instance.health_collector.ingest_health_data(health_data)
        return {"status": "success", "message": "Health data ingested"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to ingest health data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    settings = Settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        log_level=settings.log_level.lower(),
        reload=settings.debug_mode
    )