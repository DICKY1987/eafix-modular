# doc_id: DOC-SERVICE-0159
# DOC_ID: DOC-SERVICE-0074
"""
Re-entry Engine Service

Central re-entry processing engine that consumes TradeResult events,
analyzes outcomes using the shared library, calls the reentry-matrix-svc
for decisions, and produces ReentryDecision events with atomic CSV writes.
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
from .processor import TradeResultProcessor
from .decision_client import ReentryMatrixClient

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


class TradeResultEvent(BaseModel):
    """Trade result event from execution engine."""
    
    event_type: str
    timestamp: str
    data: Dict[str, Any]


class ReentryEngineService:
    """Core re-entry engine service."""
    
    def __init__(self, settings: Settings, metrics: MetricsCollector, health_checker: HealthChecker):
        self.settings = settings
        self.metrics = metrics
        self.health_checker = health_checker
        
        self.redis_client: Optional[redis.Redis] = None
        self.processor = TradeResultProcessor(settings, metrics)
        self.matrix_client = ReentryMatrixClient(settings)
        
        self.running = False
        self.subscriber_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the re-entry engine service."""
        if self.running:
            return
        
        logger.info("Starting Re-entry Engine Service", port=self.settings.service_port)
        
        # Initialize Redis connection
        self.redis_client = redis.from_url(self.settings.redis_url)
        await self.redis_client.ping()
        logger.info("Connected to Redis", url=self.settings.redis_url)
        
        # Start processor
        await self.processor.start()
        
        # Start matrix client
        await self.matrix_client.start()
        
        # Start trade result subscriber if enabled
        if self.settings.subscribe_to_trade_results:
            self.subscriber_task = asyncio.create_task(self._subscribe_to_trade_results())
        
        self.running = True
        self.metrics.increment_counter("service_starts")
        
        logger.info("Re-entry Engine Service started successfully")
    
    async def stop(self) -> None:
        """Stop the re-entry engine service."""
        if not self.running:
            return
        
        logger.info("Stopping Re-entry Engine Service")
        
        # Stop subscriber
        if self.subscriber_task:
            self.subscriber_task.cancel()
            try:
                await self.subscriber_task
            except asyncio.CancelledError:
                pass
        
        # Stop components
        await self.processor.stop()
        await self.matrix_client.stop()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        self.running = False
        logger.info("Re-entry Engine Service stopped")
    
    async def _subscribe_to_trade_results(self) -> None:
        """Subscribe to trade result events from Redis."""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(self.settings.trade_results_topic)
            
            logger.info("Subscribed to trade results", topic=self.settings.trade_results_topic)
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        await self._process_trade_result_event(message["data"])
                        self.metrics.increment_counter("trade_results_processed")
                    except Exception as e:
                        logger.error("Failed to process trade result event", error=str(e))
                        self.metrics.record_error("trade_result_processing_error")
                        
        except Exception as e:
            logger.error("Trade result subscriber failed", error=str(e))
            self.metrics.record_error("subscriber_error")
    
    async def _process_trade_result_event(self, message_data: bytes) -> None:
        """Process a single trade result event."""
        try:
            # Parse event
            event_data = json.loads(message_data.decode())
            trade_result = event_data.get("data", {})
            
            logger.info(
                "Processing trade result",
                trade_id=trade_result.get("trade_id"),
                symbol=trade_result.get("symbol"),
                profit_loss=trade_result.get("profit_loss")
            )
            
            # Process with re-entry logic
            await self.processor.process_trade_result(trade_result)
            
        except Exception as e:
            logger.error("Failed to process trade result event", error=str(e))
            raise
    
    async def process_trade_result_manual(self, trade_result: Dict[str, Any]) -> Dict[str, Any]:
        """Manually process a trade result (for testing/debugging)."""
        return await self.processor.process_trade_result(trade_result)
    
    async def get_reentry_status(self) -> Dict[str, Any]:
        """Get re-entry engine status."""
        processor_status = await self.processor.get_status()
        matrix_client_status = await self.matrix_client.get_status()
        
        return {
            "service": "reentry-engine",
            "running": self.running,
            "subscriber_active": self.subscriber_task is not None and not self.subscriber_task.done(),
            "processor": processor_status,
            "matrix_client": matrix_client_status,
            "metrics": self.metrics.get_metrics_summary()
        }


# Global service instance
service_instance: Optional[ReentryEngineService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle."""
    global service_instance
    
    # Startup
    settings = Settings()
    metrics = MetricsCollector()
    health_checker = HealthChecker(settings, metrics)
    
    service_instance = ReentryEngineService(settings, metrics, health_checker)
    
    try:
        await service_instance.start()
        yield
    finally:
        # Shutdown
        if service_instance:
            await service_instance.stop()


# Create FastAPI application
app = FastAPI(
    title="Re-entry Engine Service",
    description="Central re-entry processing with atomic CSV writes",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/healthz")
async def health_check():
    """Liveness probe endpoint."""
    if not service_instance or not service_instance.running:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "healthy", "service": "reentry-engine"}


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


@app.post("/reentry/process")
async def process_trade_result(trade_result: Dict[str, Any], background_tasks: BackgroundTasks):
    """Manually process a trade result for re-entry analysis."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        result = await service_instance.process_trade_result_manual(trade_result)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/reentry/status")
async def get_reentry_status():
    """Get detailed re-entry engine status."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.get_reentry_status()


@app.get("/reentry/recent-decisions")
async def get_recent_decisions(limit: int = 10):
    """Get recent re-entry decisions."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.processor.get_recent_decisions(limit)


@app.get("/reentry/stats")
async def get_reentry_stats():
    """Get re-entry processing statistics."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.processor.get_processing_stats()


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