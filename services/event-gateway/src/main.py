"""
Event Gateway Service

Main FastAPI service for event-driven messaging, Redis pub/sub management,
and event routing between EAFIX services.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Dict, Any, List

import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from .config import Settings
from .gateway import EventGateway
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


class EventPublishRequest(BaseModel):
    """Request to publish an event."""
    
    event_type: str
    schema_version: str = "1.0"
    payload: Dict[str, Any]
    topic: Optional[str] = None
    producer: Optional[str] = None
    trace_id: Optional[str] = None


class TopicSubscribeRequest(BaseModel):
    """Request to subscribe to topics."""
    
    topics: List[str]
    consumer_id: str


class EventGatewayService:
    """Core event gateway service."""
    
    def __init__(self, settings: Settings, metrics: MetricsCollector, health_checker: HealthChecker):
        self.settings = settings
        self.metrics = metrics
        self.health_checker = health_checker
        
        self.gateway = EventGateway(settings, metrics)
        
        self.running = False
    
    async def start(self) -> None:
        """Start the event gateway service."""
        if self.running:
            return
        
        logger.info("Starting Event Gateway Service", port=self.settings.service_port)
        
        # Start gateway
        await self.gateway.start()
        
        self.running = True
        self.metrics.increment_counter("service_starts")
        
        logger.info("Event Gateway Service started successfully")
    
    async def stop(self) -> None:
        """Stop the event gateway service."""
        if not self.running:
            return
        
        logger.info("Stopping Event Gateway Service")
        
        # Stop gateway
        await self.gateway.stop()
        
        self.running = False
        logger.info("Event Gateway Service stopped")
    
    async def publish_event(self, event_type: str, schema_version: str, payload: Dict[str, Any],
                           topic: Optional[str] = None, producer: Optional[str] = None,
                           trace_id: Optional[str] = None) -> Dict[str, Any]:
        """Publish an event through the gateway."""
        return await self.gateway.publish_event(
            event_type, schema_version, payload, topic, producer, trace_id
        )
    
    async def get_topic_metrics(self, topic: str) -> Dict[str, Any]:
        """Get metrics for a topic."""
        return await self.gateway.get_topic_metrics(topic)
    
    async def get_gateway_status(self) -> Dict[str, Any]:
        """Get comprehensive gateway status."""
        gateway_status = await self.gateway.get_status()
        
        return {
            "service": "event-gateway",
            "running": self.running,
            "gateway": gateway_status,
            "topics": {
                "configured": len(self.settings.event_topics),
                "total_with_dlq": len(self.settings.get_all_topics())
            },
            "features": {
                "routing_enabled": self.settings.event_routing_enabled,
                "validation_enabled": self.settings.event_validation_enabled,
                "transformation_enabled": self.settings.event_transformation_enabled,
                "filtering_enabled": self.settings.event_filtering_enabled,
                "dead_letter_enabled": self.settings.dead_letter_enabled
            }
        }


# Global service instance
service_instance: Optional[EventGatewayService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle."""
    global service_instance
    
    # Startup
    settings = Settings()
    metrics = MetricsCollector()
    health_checker = HealthChecker(settings, metrics)
    
    service_instance = EventGatewayService(settings, metrics, health_checker)
    
    try:
        await service_instance.start()
        yield
    finally:
        # Shutdown
        if service_instance:
            await service_instance.stop()


# Create FastAPI application
app = FastAPI(
    title="Event Gateway Service",
    description="Event-driven messaging and routing for EAFIX microservices",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/healthz")
async def health_check():
    """Liveness probe endpoint."""
    if not service_instance or not service_instance.running:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "healthy", "service": "event-gateway"}


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


@app.get("/gateway/status")
async def get_gateway_status():
    """Get comprehensive gateway status."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.get_gateway_status()


@app.post("/events/publish")
async def publish_event(request: EventPublishRequest):
    """Publish an event to the gateway."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await service_instance.publish_event(
        request.event_type,
        request.schema_version,
        request.payload,
        request.topic,
        request.producer,
        request.trace_id
    )
    
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "Event publish failed"))
    
    return result


@app.get("/topics")
async def get_all_topics():
    """Get all configured topics."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "topics": list(service_instance.settings.get_all_topics()),
        "configured_topics": service_instance.settings.event_topics,
        "routing_rules": service_instance.settings.event_routing_rules
    }


@app.get("/topics/{topic_name}/metrics")
async def get_topic_metrics(topic_name: str):
    """Get metrics for a specific topic."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if topic_name not in service_instance.settings.get_all_topics():
        raise HTTPException(status_code=404, detail=f"Topic not found: {topic_name}")
    
    return await service_instance.get_topic_metrics(topic_name)


@app.get("/topics/{topic_name}/config")
async def get_topic_config(topic_name: str):
    """Get configuration for a specific topic."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    config = service_instance.settings.get_topic_config(topic_name)
    if not config:
        raise HTTPException(status_code=404, detail=f"Topic not found: {topic_name}")
    
    return {"topic": topic_name, "config": config}


@app.get("/events/dead-letter")
async def get_dead_letter_messages(limit: int = 100):
    """Get dead letter messages."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if limit <= 0 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    
    return await service_instance.gateway.get_dead_letter_messages(limit)


@app.get("/events/routing-rules")
async def get_routing_rules():
    """Get event routing rules."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return service_instance.settings.event_routing_rules


@app.get("/events/filters")
async def get_event_filters():
    """Get event filtering configuration."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return service_instance.settings.event_filters


@app.get("/dashboard")
async def get_gateway_dashboard():
    """Get gateway dashboard data."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    status = await service_instance.get_gateway_status()
    dead_letters = await service_instance.gateway.get_dead_letter_messages(50)
    
    # Get metrics for all topics
    topic_metrics = {}
    for topic in service_instance.settings.event_topics.keys():
        topic_metrics[topic] = await service_instance.get_topic_metrics(topic)
    
    return {
        "dashboard": {
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "topic_metrics": topic_metrics,
            "dead_letter_summary": {
                "total_messages": len(dead_letters),
                "recent_messages": dead_letters[:10]  # Show most recent 10
            },
            "configuration": {
                "total_topics": len(service_instance.settings.event_topics),
                "routing_rules": len(service_instance.settings.event_routing_rules),
                "event_filters": len(service_instance.settings.event_filters)
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