# doc_id: DOC-SERVICE-0221
# DOC_ID: DOC-SERVICE-0062
"""
Flow Orchestrator Service

Main FastAPI service for runtime flow orchestration, coordinating event-driven
data pipelines and managing inter-service communication flows.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Dict, Any, List

import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from .config import Settings
from .orchestrator import FlowOrchestrator
from .metrics import MetricsCollector
from .health import HealthChecker

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


class FlowTriggerRequest(BaseModel):
    """Request to manually trigger a flow."""
    
    flow_name: str
    trigger_data: Optional[Dict[str, Any]] = None


class FlowCancelRequest(BaseModel):
    """Request to cancel a flow."""
    
    flow_id: str


class EventInjectRequest(BaseModel):
    """Request to inject an event into the flow system."""
    
    event_type: str
    event_data: Dict[str, Any]
    target_topic: Optional[str] = None


class FlowOrchestratorService:
    """Core flow orchestrator service."""
    
    def __init__(self, settings: Settings, metrics: MetricsCollector, health_checker: HealthChecker):
        self.settings = settings
        self.metrics = metrics
        self.health_checker = health_checker
        
        self.orchestrator = FlowOrchestrator(settings, metrics)
        
        self.running = False
    
    async def start(self) -> None:
        """Start the flow orchestrator service."""
        if self.running:
            return
        
        logger.info("Starting Flow Orchestrator Service", port=self.settings.service_port)
        
        # Validate configuration
        config_errors = self.settings.validate_flow_definitions()
        if config_errors:
            logger.error("Flow configuration errors", errors=config_errors)
            raise RuntimeError(f"Invalid flow configuration: {config_errors}")
        
        # Start orchestrator
        await self.orchestrator.start()
        
        self.running = True
        self.metrics.increment_counter("service_starts")
        
        logger.info("Flow Orchestrator Service started successfully")
    
    async def stop(self) -> None:
        """Stop the flow orchestrator service."""
        if not self.running:
            return
        
        logger.info("Stopping Flow Orchestrator Service")
        
        # Stop orchestrator
        await self.orchestrator.stop()
        
        self.running = False
        logger.info("Flow Orchestrator Service stopped")
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator status."""
        orchestrator_status = await self.orchestrator.get_status()
        flow_metrics = await self.orchestrator.get_flow_metrics()
        
        return {
            "service": "flow-orchestrator",
            "running": self.running,
            "orchestrator": orchestrator_status,
            "metrics": flow_metrics,
            "configuration": {
                "enabled_flows": len(self.settings.get_enabled_flows()),
                "monitored_services": len(self.settings.service_registry),
                "flow_monitoring_enabled": self.settings.flow_monitoring_enabled,
                "circuit_breaker_enabled": self.settings.circuit_breaker_enabled
            }
        }
    
    async def trigger_flow(self, flow_name: str, trigger_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger a flow execution."""
        return await self.orchestrator.trigger_flow_manually(flow_name, trigger_data)
    
    async def cancel_flow(self, flow_id: str) -> Dict[str, Any]:
        """Cancel a flow execution."""
        return await self.orchestrator.cancel_flow(flow_id)
    
    async def inject_event(self, event_type: str, event_data: Dict[str, Any], 
                          target_topic: Optional[str] = None) -> Dict[str, Any]:
        """Inject an event into the flow system."""
        if not self.orchestrator.redis_client:
            return {"success": False, "error": "Redis client not available"}
        
        try:
            # Determine target topic
            if target_topic:
                topics = [target_topic]
            else:
                topics = self.settings.get_event_topics(event_type)
                if not topics:
                    return {"success": False, "error": f"No topics configured for event type: {event_type}"}
            
            # Prepare event message
            event_message = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "injected": True,
                "data": event_data
            }
            
            # Publish to topics
            published_topics = []
            for topic in topics:
                await self.orchestrator.redis_client.publish(topic, json.dumps(event_message))
                published_topics.append(topic)
            
            logger.info(
                "Event injected",
                event_type=event_type,
                topics=published_topics
            )
            
            return {
                "success": True,
                "event_type": event_type,
                "published_topics": published_topics,
                "timestamp": event_message["timestamp"]
            }
            
        except Exception as e:
            logger.error("Failed to inject event", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get active flows."""
        return await self.orchestrator.get_active_flows()
    
    async def get_flow_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get flow execution history."""
        return await self.orchestrator.get_flow_history(limit)
    
    async def get_flow_metrics(self) -> Dict[str, Any]:
        """Get flow performance metrics."""
        return await self.orchestrator.get_flow_metrics()


# Global service instance
service_instance: Optional[FlowOrchestratorService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle."""
    global service_instance
    
    # Startup
    settings = Settings()
    metrics = MetricsCollector()
    health_checker = HealthChecker(settings, metrics)
    
    service_instance = FlowOrchestratorService(settings, metrics, health_checker)
    
    try:
        await service_instance.start()
        yield
    finally:
        # Shutdown
        if service_instance:
            await service_instance.stop()


# Create FastAPI application
app = FastAPI(
    title="Flow Orchestrator Service",
    description="Runtime flow orchestration for EAFIX event-driven data pipelines",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/healthz")
async def health_check():
    """Liveness probe endpoint."""
    if not service_instance or not service_instance.running:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "healthy", "service": "flow-orchestrator"}


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


@app.get("/orchestrator/status")
async def get_orchestrator_status():
    """Get comprehensive orchestrator status."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.get_orchestrator_status()


@app.get("/orchestrator/flows/active")
async def get_active_flows():
    """Get list of currently active flows."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.get_active_flows()


@app.get("/orchestrator/flows/history")
async def get_flow_history(limit: int = 100):
    """Get flow execution history."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    
    return await service_instance.get_flow_history(limit)


@app.get("/orchestrator/flows/metrics")
async def get_flow_metrics():
    """Get flow performance metrics."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.get_flow_metrics()


@app.post("/orchestrator/flows/trigger")
async def trigger_flow(request: FlowTriggerRequest):
    """Manually trigger a flow execution."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await service_instance.trigger_flow(request.flow_name, request.trigger_data)
    
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "Flow trigger failed"))
    
    return result


@app.post("/orchestrator/flows/cancel")
async def cancel_flow(request: FlowCancelRequest):
    """Cancel a flow execution."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await service_instance.cancel_flow(request.flow_id)
    
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "Flow cancel failed"))
    
    return result


@app.post("/orchestrator/events/inject")
async def inject_event(request: EventInjectRequest):
    """Inject an event into the flow system for testing."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await service_instance.inject_event(
        request.event_type, 
        request.event_data, 
        request.target_topic
    )
    
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "Event injection failed"))
    
    return result


@app.get("/orchestrator/configuration/flows")
async def get_flow_definitions():
    """Get configured flow definitions."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "enabled_flows": service_instance.settings.get_enabled_flows(),
        "all_flows": service_instance.settings.flow_definitions
    }


@app.get("/orchestrator/configuration/services")
async def get_service_registry():
    """Get service registry configuration."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return service_instance.settings.service_registry


@app.get("/orchestrator/configuration/events")
async def get_event_routing():
    """Get event routing configuration."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return service_instance.settings.event_routing_rules


@app.get("/orchestrator/dashboard")
async def get_orchestrator_dashboard():
    """Get orchestrator dashboard data."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    status = await service_instance.get_orchestrator_status()
    active_flows = await service_instance.get_active_flows()
    flow_metrics = await service_instance.get_flow_metrics()
    
    return {
        "dashboard": {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "active_flows": active_flows,
            "active_flows_count": len(active_flows),
            "flow_performance": flow_metrics,
            "service_health": {
                "total_services": len(service_instance.settings.service_registry),
                "monitored_services": len(service_instance.settings.service_registry)
            }
        }
    }


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