# DOC_ID: DOC-SERVICE-0095
"""
Transport Router Service

Handles CSV file routing, integrity validation, and downstream service coordination.
Monitors CSV outputs from various services, validates checksums, sequences, and routes
data to appropriate downstream consumers with integrity guarantees.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

import redis.asyncio as redis
import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import aiofiles
import watchfiles

from .config import Settings
from .health import HealthChecker
from .metrics import MetricsCollector
from .router import CSVRouter
from .validator import IntegrityValidator
from .watcher import FileWatcher

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


class FileValidationRequest(BaseModel):
    """Request for manual file validation."""
    
    file_path: str
    expected_type: str  # "ActiveCalendarSignal", "ReentryDecision", etc.


class RouteRequest(BaseModel):
    """Request for manual file routing."""
    
    file_path: str
    destination_services: List[str]
    validate_integrity: bool = True


class TransportRouterService:
    """Core transport router service."""
    
    def __init__(self, settings: Settings, metrics: MetricsCollector, health_checker: HealthChecker):
        self.settings = settings
        self.metrics = metrics
        self.health_checker = health_checker
        
        self.redis_client: Optional[redis.Redis] = None
        self.router = CSVRouter(settings, metrics)
        self.validator = IntegrityValidator(settings, metrics)
        self.file_watcher = FileWatcher(settings, metrics)
        
        self.running = False
        self.watcher_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the transport router service."""
        if self.running:
            return
        
        logger.info("Starting Transport Router Service", port=self.settings.service_port)
        
        # Initialize Redis connection
        self.redis_client = redis.from_url(self.settings.redis_url)
        await self.redis_client.ping()
        logger.info("Connected to Redis", url=self.settings.redis_url)
        
        # Start components
        await self.router.start()
        await self.validator.start()
        
        # Start file watcher if enabled
        if self.settings.file_watching_enabled:
            await self.file_watcher.start()
            self.watcher_task = asyncio.create_task(self._run_file_watcher())
        
        self.running = True
        self.metrics.increment_counter("service_starts")
        
        logger.info("Transport Router Service started successfully")
    
    async def stop(self) -> None:
        """Stop the transport router service."""
        if not self.running:
            return
        
        logger.info("Stopping Transport Router Service")
        
        # Stop file watcher
        if self.watcher_task:
            self.watcher_task.cancel()
            try:
                await self.watcher_task
            except asyncio.CancelledError:
                pass
        
        # Stop components
        await self.file_watcher.stop()
        await self.validator.stop()
        await self.router.stop()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        self.running = False
        logger.info("Transport Router Service stopped")
    
    async def _run_file_watcher(self) -> None:
        """Run file watcher in background."""
        try:
            async for file_event in self.file_watcher.watch_directories():
                if file_event["event_type"] in ["created", "modified"]:
                    await self._handle_file_event(file_event)
                    
        except Exception as e:
            logger.error("File watcher failed", error=str(e))
            self.metrics.record_error("file_watcher_error")
    
    async def _handle_file_event(self, file_event: Dict[str, Any]) -> None:
        """Handle file system events."""
        try:
            file_path = Path(file_event["path"])
            
            # Only process CSV files
            if not file_path.suffix.lower() == '.csv':
                return
            
            # Skip temporary files
            if file_path.name.endswith('.tmp'):
                return
            
            logger.info(
                "Processing file event",
                event_type=file_event["event_type"],
                file_path=str(file_path)
            )
            
            # Determine file type from filename pattern
            file_type = self._determine_file_type(file_path)
            if not file_type:
                logger.warning("Unknown file type", file_path=str(file_path))
                return
            
            # Validate integrity
            if self.settings.validate_all_files:
                validation_result = await self.validator.validate_file(file_path, file_type)
                if not validation_result["valid"]:
                    logger.error(
                        "File validation failed",
                        file_path=str(file_path),
                        errors=validation_result["errors"]
                    )
                    self.metrics.record_error("file_validation_error")
                    return
            
            # Route to appropriate destinations
            routing_result = await self.router.route_file(file_path, file_type)
            
            # Publish event if configured
            if self.redis_client and self.settings.publish_file_events:
                await self._publish_file_processed_event(file_path, file_type, routing_result)
            
            self.metrics.increment_counter("files_processed")
            
        except Exception as e:
            logger.error("Failed to handle file event", error=str(e), file_path=file_event.get("path"))
            self.metrics.record_error("file_handling_error")
    
    def _determine_file_type(self, file_path: Path) -> Optional[str]:
        """Determine file type from filename pattern."""
        filename = file_path.name.lower()
        
        if filename.startswith("active_calendar_signals_"):
            return "ActiveCalendarSignal"
        elif filename.startswith("reentry_decisions_"):
            return "ReentryDecision"
        elif filename.startswith("trade_results_"):
            return "TradeResult"
        elif filename.startswith("health_metrics_"):
            return "HealthMetric"
        else:
            return None
    
    async def _publish_file_processed_event(self, file_path: Path, file_type: str, 
                                          routing_result: Dict[str, Any]) -> None:
        """Publish file processed event to Redis."""
        try:
            event = {
                "event_type": "file_processed",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "file_path": str(file_path),
                    "file_type": file_type,
                    "routing_result": routing_result,
                    "service": "transport-router"
                }
            }
            
            await self.redis_client.publish(
                self.settings.file_events_topic,
                json.dumps(event)
            )
            
            self.metrics.increment_counter("events_published")
            
        except Exception as e:
            logger.warning("Failed to publish file processed event", error=str(e))
    
    async def validate_file_manual(self, file_path: str, expected_type: str) -> Dict[str, Any]:
        """Manually validate a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"valid": False, "error": "File does not exist"}
            
            return await self.validator.validate_file(path, expected_type)
            
        except Exception as e:
            logger.error("Manual file validation failed", error=str(e))
            return {"valid": False, "error": str(e)}
    
    async def route_file_manual(self, file_path: str, destination_services: List[str], 
                              validate_integrity: bool = True) -> Dict[str, Any]:
        """Manually route a file to destination services."""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": "File does not exist"}
            
            file_type = self._determine_file_type(path)
            if not file_type:
                return {"success": False, "error": "Unknown file type"}
            
            # Validate if requested
            if validate_integrity:
                validation_result = await self.validator.validate_file(path, file_type)
                if not validation_result["valid"]:
                    return {
                        "success": False, 
                        "error": "File validation failed",
                        "validation_errors": validation_result["errors"]
                    }
            
            # Route to specified destinations
            routing_result = await self.router.route_file_to_services(
                path, file_type, destination_services
            )
            
            return {"success": True, "routing_result": routing_result}
            
        except Exception as e:
            logger.error("Manual file routing failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def get_router_status(self) -> Dict[str, Any]:
        """Get transport router status."""
        router_status = await self.router.get_status()
        validator_status = await self.validator.get_status()
        watcher_status = await self.file_watcher.get_status()
        
        return {
            "service": "transport-router",
            "running": self.running,
            "watcher_active": self.watcher_task is not None and not self.watcher_task.done(),
            "router": router_status,
            "validator": validator_status,
            "file_watcher": watcher_status,
            "metrics": self.metrics.get_metrics_summary()
        }


# Global service instance
service_instance: Optional[TransportRouterService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle."""
    global service_instance
    
    # Startup
    settings = Settings()
    metrics = MetricsCollector()
    health_checker = HealthChecker(settings, metrics)
    
    service_instance = TransportRouterService(settings, metrics, health_checker)
    
    try:
        await service_instance.start()
        yield
    finally:
        # Shutdown
        if service_instance:
            await service_instance.stop()


# Create FastAPI application
app = FastAPI(
    title="Transport Router Service",
    description="CSV file routing with integrity validation and downstream coordination",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/healthz")
async def health_check():
    """Liveness probe endpoint."""
    if not service_instance or not service_instance.running:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "healthy", "service": "transport-router"}


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


@app.post("/transport/validate")
async def validate_file(request: FileValidationRequest):
    """Manually validate a CSV file."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await service_instance.validate_file_manual(
        request.file_path, 
        request.expected_type
    )
    
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Validation failed"))
    
    return result


@app.post("/transport/route")
async def route_file(request: RouteRequest):
    """Manually route a CSV file to destination services."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    result = await service_instance.route_file_manual(
        request.file_path,
        request.destination_services,
        request.validate_integrity
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Routing failed"))
    
    return result


@app.get("/transport/status")
async def get_router_status():
    """Get detailed transport router status."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.get_router_status()


@app.get("/transport/watched-directories")
async def get_watched_directories():
    """Get list of directories being watched."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.file_watcher.get_watched_directories()


@app.get("/transport/routing-rules")
async def get_routing_rules():
    """Get current routing rules."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.router.get_routing_rules()


@app.get("/transport/recent-files")
async def get_recent_files(limit: int = 10):
    """Get recently processed files."""
    if not service_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await service_instance.router.get_recent_files(limit)


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