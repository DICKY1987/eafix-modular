#!/usr/bin/env python3
# doc_id: DOC-SERVICE-0137
# DOC_ID: DOC-SERVICE-0033
"""
Calendar Ingestor Service - Main Entry Point
Processes economic calendar events and generates ActiveCalendarSignal CSV files
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response

from .ingestor import CalendarIngestor
from .config import Settings
from .health import HealthChecker
from .metrics import MetricsCollector


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.LoggerFactory(),
    logger_factory=structlog.stdlib.LoggerFactory(),
    context_class=dict,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management"""
    logger.info("Starting Calendar Ingestor service")
    
    # Initialize components
    settings = Settings()
    metrics = MetricsCollector()
    health_checker = HealthChecker()
    ingestor = CalendarIngestor(settings, metrics)
    
    # Store in app state
    app.state.settings = settings
    app.state.metrics = metrics
    app.state.health_checker = health_checker
    app.state.ingestor = ingestor
    
    # Start the ingestor
    await ingestor.start()
    
    try:
        yield
    finally:
        logger.info("Shutting down Calendar Ingestor service")
        await ingestor.stop()


app = FastAPI(
    title="EAFIX Calendar Ingestor",
    description="Processes economic calendar events and generates active signals",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    try:
        health_status = await app.state.health_checker.check_health()
        if health_status["status"] == "healthy":
            return JSONResponse(content=health_status, status_code=200)
        else:
            return JSONResponse(content=health_status, status_code=503)
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            content={"status": "unhealthy", "error": str(e)}, 
            status_code=503
        )


@app.get("/readyz")
async def readiness_check():
    """Readiness check endpoint"""
    try:
        uptime = app.state.metrics.get_uptime()
        ready = uptime > 2.0
        return JSONResponse(
            content={"ready": ready, "uptime": uptime},
            status_code=200 if ready else 503
        )
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            content={"ready": False, "error": str(e)},
            status_code=503
        )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/status")
async def service_status():
    """Service status information"""
    return {
        "service": "calendar-ingestor",
        "version": "1.0.0",
        "status": "running",
        "config": {
            "redis_url": app.state.settings.redis_url,
            "log_level": app.state.settings.log_level,
            "output_directory": app.state.settings.output_directory
        }
    }


@app.post("/ingest/manual")
async def manual_calendar_ingest(calendar_data: dict):
    """Manual calendar event ingestion endpoint for testing"""
    try:
        result = await app.state.ingestor.process_calendar_event(calendar_data)
        return {"status": "success", "message": "Calendar event processed", "result": result}
    except Exception as e:
        logger.error("Manual calendar ingestion failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/signals/active")
async def get_active_signals():
    """Get current active calendar signals"""
    try:
        signals = await app.state.ingestor.get_active_signals()
        return {"status": "success", "active_signals": signals}
    except Exception as e:
        logger.error("Failed to retrieve active signals", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Main entry point"""
    # Configure logging level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level))
    
    # Start the server
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8086,  # Calendar ingestor runs on port 8086
        reload=False,
        access_log=True
    )


if __name__ == "__main__":
    main()