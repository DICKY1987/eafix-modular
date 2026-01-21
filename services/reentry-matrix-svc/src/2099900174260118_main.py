# doc_id: DOC-SERVICE-0166
# DOC_ID: DOC-SERVICE-0080
"""
Re-entry Matrix Service

Provides tiered re-entry decision logic using the shared library for hybrid ID
management and vocabulary validation. Implements the matrix mapping resolver
for parameter sets with fallback tiers.
"""

import asyncio
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Dict, Any

import redis.asyncio as redis
import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import Settings
from .health import HealthChecker
from .metrics import MetricsCollector
from .resolver import TieredParameterResolver
from .processor import ReentryProcessor

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


class ReentryRequest(BaseModel):
    """Request for re-entry decision."""
    
    trade_id: str
    symbol: str
    outcome_class: str  # WIN, LOSS, BREAKEVEN
    duration_class: str  # FLASH, QUICK, LONG, EXTENDED
    proximity_state: str  # PRE_1H, AT_EVENT, POST_30M
    calendar_id: str  # CAL8_*, CAL5_*, NONE
    direction: str  # LONG, SHORT
    generation: int  # 1, 2, 3
    current_lot_size: float
    profit_loss_pips: float


class ReentryResponse(BaseModel):
    """Response with re-entry decision."""
    
    status: str
    hybrid_id: str
    reentry_action: str  # R1, R2, HOLD, NO_REENTRY
    parameter_set_id: str
    resolved_tier: str  # EXACT, TIER1, TIER2, TIER3, GLOBAL
    chain_position: str  # O, R1, R2
    lot_size: float
    stop_loss: float
    take_profit: float
    confidence_score: float


class ReentryMatrixService:
    """Core re-entry matrix service."""
    
    def __init__(self, settings: Settings, metrics: MetricsCollector, health_checker: HealthChecker):
        self.settings = settings
        self.metrics = metrics
        self.health_checker = health_checker
        
        self.redis_client: Optional[redis.Redis] = None
        self.resolver = TieredParameterResolver(settings)
        self.processor = ReentryProcessor(settings, metrics)
        
        self.running = False
    
    async def start(self) -> None:
        """Start the service."""
        if self.running:
            return
        
        logger.info("Starting Re-entry Matrix Service", port=self.settings.service_port)
        
        # Initialize Redis connection
        self.redis_client = redis.from_url(self.settings.redis_url)
        
        # Test connections
        await self.redis_client.ping()
        logger.info("Connected to Redis", url=self.settings.redis_url)
        
        # Load parameter sets
        await self.resolver.load_parameter_sets()
        
        # Mark as running
        self.running = True
        self.metrics.increment_counter("service_starts")
        
        logger.info("Re-entry Matrix Service started successfully")
    
    async def stop(self) -> None:
        """Stop the service."""
        if not self.running:
            return
        
        logger.info("Stopping Re-entry Matrix Service")
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        self.running = False
        logger.info("Re-entry Matrix Service stopped")
    
    async def process_reentry_request(self, request: ReentryRequest) -> ReentryResponse:
        """Process a re-entry decision request using tiered resolver."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(
                "Processing re-entry request",
                trade_id=request.trade_id,
                symbol=request.symbol,
                outcome=request.outcome_class,
                duration=request.duration_class,
                generation=request.generation
            )
            
            # Use the processor to handle the logic
            decision = await self.processor.process_reentry_decision(request)
            
            # Record metrics
            processing_time = asyncio.get_event_loop().time() - start_time
            self.metrics.record_reentry_processed(processing_time)
            self.metrics.increment_counter("reentry_decisions_total")
            
            # Publish event if configured
            if self.redis_client and self.settings.publish_events:
                await self._publish_reentry_decision(decision)
            
            return ReentryResponse(
                status="success",
                hybrid_id=decision["hybrid_id"],
                reentry_action=decision["reentry_action"],
                parameter_set_id=decision["parameter_set_id"],
                resolved_tier=decision["resolved_tier"],
                chain_position=decision["chain_position"],
                lot_size=decision["lot_size"],
                stop_loss=decision["stop_loss"],
                take_profit=decision["take_profit"],
                confidence_score=decision["confidence_score"]
            )
            
        except Exception as e:
            logger.error(
                "Failed to process re-entry request",
                trade_id=request.trade_id,
                error=str(e),
                exc_info=True
            )
            self.metrics.record_error("processing_error")
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    async def _publish_reentry_decision(self, decision: Dict[str, Any]) -> None:
        """Publish re-entry decision event to Redis."""
        try:
            event = {
                "event_type": "reentry_decision",
                "timestamp": datetime.utcnow().isoformat(),
                "data": decision
            }
            
            await self.redis_client.publish(
                self.settings.reentry_decisions_topic,
                json.dumps(event)
            )
            
        except Exception as e:
            logger.warning("Failed to publish reentry decision event", error=str(e))


# Global service instance
service_instance: Optional[ReentryMatrixService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle."""
    global service_instance
    
    # Startup
    settings = Settings()
    metrics = MetricsCollector()
    health_checker = HealthChecker(settings, metrics)
    
    service_instance = ReentryMatrixService(settings, metrics, health_checker)
    
    try:
        await service_instance.start()
        yield
    finally:
        # Shutdown
        if service_instance:
            await service_instance.stop()


# Create FastAPI application
app = FastAPI(
    title="Re-entry Matrix Service",
    description="Tiered re-entry decision logic with hybrid ID management",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/healthz")
async def health_check():
    """Liveness probe endpoint."""
    if not service_instance or not service_instance.running:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "healthy", "service": "reentry-matrix-svc"}


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


@app.post("/reentry/decide", response_model=ReentryResponse)
async def decide_reentry(request: ReentryRequest):
    """Process re-entry decision request."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.process_reentry_request(request)


@app.get("/reentry/parameters/{tier}")
async def get_parameter_sets(tier: str):
    """Get parameter sets for a specific tier."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    parameter_sets = await service_instance.resolver.get_parameter_sets_for_tier(tier)
    return {"tier": tier, "parameter_sets": parameter_sets}


@app.get("/reentry/status")
async def get_service_status():
    """Get detailed service status."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    resolver_status = await service_instance.resolver.get_status()
    processor_status = await service_instance.processor.get_status()
    
    return {
        "service": "reentry-matrix-svc",
        "running": service_instance.running,
        "resolver": resolver_status,
        "processor": processor_status,
        "metrics": service_instance.metrics.get_metrics_summary()
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