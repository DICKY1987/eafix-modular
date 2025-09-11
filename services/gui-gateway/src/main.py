"""
GUI Gateway Service - API Gateway for Operator Interface

This service provides the API gateway for the trading system operator interface,
aggregating data from all microservices into a unified API for the frontend.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseSettings, BaseModel
import httpx
import structlog

from .config import Settings
from .models import (
    SystemStatus, ServiceHealth, TradingDashboard, 
    PositionSummary, SignalFeed, OrderHistory
)
from .aggregator import DataAggregator
from .health import HealthChecker


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

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting GUI Gateway service")
    
    # Initialize dependencies
    settings = Settings()
    health_checker = HealthChecker(settings)
    data_aggregator = DataAggregator(settings)
    
    # Store in app state
    app.state.settings = settings
    app.state.health_checker = health_checker
    app.state.data_aggregator = data_aggregator
    
    # Start background tasks
    await data_aggregator.start()
    
    yield
    
    # Cleanup
    logger.info("Shutting down GUI Gateway service")
    await data_aggregator.stop()


# Create FastAPI app
app = FastAPI(
    title="EAFIX GUI Gateway",
    description="API Gateway for Trading System Operator Interface",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_settings() -> Settings:
    """Get application settings."""
    return app.state.settings


def get_health_checker() -> HealthChecker:
    """Get health checker."""
    return app.state.health_checker


def get_data_aggregator() -> DataAggregator:
    """Get data aggregator."""
    return app.state.data_aggregator


@app.get("/healthz")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "gui-gateway"}


@app.get("/readyz")
async def readiness_check(health_checker: HealthChecker = Depends(get_health_checker)):
    """Readiness check - verify all dependencies are available."""
    try:
        status = await health_checker.check_all_services()
        if not all(service["healthy"] for service in status.values()):
            raise HTTPException(status_code=503, detail="Some services are unhealthy")
        return {"status": "ready", "services": status}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/api/v1/system/status", response_model=SystemStatus)
async def get_system_status(
    health_checker: HealthChecker = Depends(get_health_checker),
    data_aggregator: DataAggregator = Depends(get_data_aggregator)
):
    """Get overall system status and health."""
    try:
        # Get service health status
        service_health = await health_checker.check_all_services()
        
        # Get system metrics
        system_metrics = await data_aggregator.get_system_metrics()
        
        return SystemStatus(
            overall_status="healthy" if all(s["healthy"] for s in service_health.values()) else "degraded",
            services=service_health,
            metrics=system_metrics,
            timestamp=data_aggregator.current_time()
        )
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")


@app.get("/api/v1/dashboard", response_model=TradingDashboard)
async def get_trading_dashboard(
    data_aggregator: DataAggregator = Depends(get_data_aggregator)
):
    """Get comprehensive trading dashboard data."""
    try:
        dashboard = await data_aggregator.get_dashboard_data()
        return dashboard
    except Exception as e:
        logger.error("Failed to get dashboard data", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@app.get("/api/v1/positions", response_model=List[PositionSummary])
async def get_positions(
    data_aggregator: DataAggregator = Depends(get_data_aggregator)
):
    """Get current position summary."""
    try:
        positions = await data_aggregator.get_positions()
        return positions
    except Exception as e:
        logger.error("Failed to get positions", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve positions")


@app.get("/api/v1/signals/live", response_model=List[SignalFeed])
async def get_live_signals(
    limit: int = 50,
    data_aggregator: DataAggregator = Depends(get_data_aggregator)
):
    """Get live trading signals feed."""
    try:
        signals = await data_aggregator.get_live_signals(limit)
        return signals
    except Exception as e:
        logger.error("Failed to get live signals", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve signals")


@app.get("/api/v1/orders/history", response_model=List[OrderHistory])
async def get_order_history(
    limit: int = 100,
    symbol: str = None,
    data_aggregator: DataAggregator = Depends(get_data_aggregator)
):
    """Get order execution history."""
    try:
        orders = await data_aggregator.get_order_history(limit, symbol)
        return orders
    except Exception as e:
        logger.error("Failed to get order history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve order history")


@app.get("/api/v1/calendar/events")
async def get_calendar_events(
    hours_ahead: int = 24,
    data_aggregator: DataAggregator = Depends(get_data_aggregator)
):
    """Get upcoming economic calendar events."""
    try:
        events = await data_aggregator.get_calendar_events(hours_ahead)
        return events
    except Exception as e:
        logger.error("Failed to get calendar events", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve calendar events")


@app.post("/api/v1/trading/pause")
async def pause_trading(
    data_aggregator: DataAggregator = Depends(get_data_aggregator)
):
    """Emergency pause all trading activity."""
    try:
        result = await data_aggregator.pause_trading()
        logger.warning("Trading paused via GUI", result=result)
        return {"status": "success", "message": "Trading paused", "result": result}
    except Exception as e:
        logger.error("Failed to pause trading", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to pause trading")


@app.post("/api/v1/trading/resume")
async def resume_trading(
    data_aggregator: DataAggregator = Depends(get_data_aggregator)
):
    """Resume trading activity."""
    try:
        result = await data_aggregator.resume_trading()
        logger.info("Trading resumed via GUI", result=result)
        return {"status": "success", "message": "Trading resumed", "result": result}
    except Exception as e:
        logger.error("Failed to resume trading", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to resume trading")


@app.get("/api/v1/metrics/performance")
async def get_performance_metrics(
    period: str = "1d",  # 1h, 1d, 1w, 1m
    data_aggregator: DataAggregator = Depends(get_data_aggregator)
):
    """Get system performance metrics."""
    try:
        metrics = await data_aggregator.get_performance_metrics(period)
        return metrics
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


if __name__ == "__main__":
    import uvicorn
    
    settings = Settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )