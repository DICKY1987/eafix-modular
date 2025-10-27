#!/usr/bin/env python3
"""
Dashboard Backend Service - Enterprise Edition
Scalable trading dashboard with BaseEnterpriseService integration
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json

from services.common.base_service import BaseEnterpriseService
from .dashboard_backend import DashboardDataManager
from .advanced_indicators import AdvancedIndicatorEngine


class DashboardBackendService(BaseEnterpriseService):
    """Enterprise dashboard backend with real-time data streaming"""

    def __init__(self):
        super().__init__(service_name="dashboard-backend")
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.data_manager = None
        self.indicator_engine = None
        self.active_connections: List[WebSocket] = []

        # Configuration
        self.update_interval = 1.0  # 1 second updates
        self.max_connections = 100

    async def startup(self):
        """Initialize dashboard backend service"""
        try:
            self.logger.info("Starting dashboard backend service...")

            # Initialize data manager
            self.data_manager = DashboardDataManager(
                database_path="data/dashboard.sqlite",
                redis_url="redis://localhost:6379"
            )
            await self.data_manager.initialize()

            # Initialize advanced indicator engine
            self.indicator_engine = AdvancedIndicatorEngine()

            # Start real-time data streaming
            asyncio.create_task(self._data_streaming_loop())

            self.logger.info("Dashboard backend service started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start dashboard backend: {e}")
            raise

    async def shutdown(self):
        """Graceful shutdown of dashboard backend service"""
        try:
            self.logger.info("Shutting down dashboard backend service...")

            # Close all WebSocket connections
            for connection in self.active_connections[:]:
                try:
                    await connection.close()
                except Exception:
                    pass

            # Shutdown data manager
            if self.data_manager:
                await self.data_manager.cleanup()

            self.logger.info("Dashboard backend service shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Health check for dashboard backend service"""
        return {
            "service": "dashboard-backend",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "data_manager": "healthy" if self.data_manager else "unhealthy",
                "indicator_engine": "healthy" if self.indicator_engine else "unhealthy",
                "active_connections": len(self.active_connections),
                "max_connections": self.max_connections
            },
            "metrics": {
                "update_interval": self.update_interval,
                "websocket_connections": len(self.active_connections)
            }
        }

    async def connect_websocket(self, websocket: WebSocket):
        """Accept and manage WebSocket connection"""
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(code=1008, reason="Too many connections")
            return

        await websocket.accept()
        self.active_connections.append(websocket)

        self.logger.info(f"New WebSocket connection: {len(self.active_connections)} total")

        try:
            # Send initial data
            initial_data = await self._get_dashboard_data()
            await websocket.send_json(initial_data)

            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for messages (for interactive features)
                    message = await websocket.receive_text()
                    await self._handle_websocket_message(websocket, message)
                except WebSocketDisconnect:
                    break

        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}")
        finally:
            # Clean up connection
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            self.logger.info(f"WebSocket disconnected: {len(self.active_connections)} remaining")

    async def _handle_websocket_message(self, websocket: WebSocket, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "subscribe":
                # Handle subscription to specific data streams
                symbols = data.get("symbols", [])
                await self._subscribe_to_symbols(websocket, symbols)

            elif message_type == "unsubscribe":
                # Handle unsubscription
                symbols = data.get("symbols", [])
                await self._unsubscribe_from_symbols(websocket, symbols)

            elif message_type == "get_history":
                # Send historical data
                symbol = data.get("symbol")
                timeframe = data.get("timeframe", "1H")
                history = await self._get_historical_data(symbol, timeframe)
                await websocket.send_json({
                    "type": "history",
                    "symbol": symbol,
                    "data": history
                })

        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")

    async def _data_streaming_loop(self):
        """Real-time data streaming to connected clients"""
        while True:
            try:
                if self.active_connections:
                    # Get latest dashboard data
                    dashboard_data = await self._get_dashboard_data()

                    # Broadcast to all connected clients
                    disconnected = []
                    for connection in self.active_connections:
                        try:
                            await connection.send_json({
                                "type": "update",
                                "timestamp": datetime.utcnow().isoformat(),
                                "data": dashboard_data
                            })
                        except Exception:
                            disconnected.append(connection)

                    # Remove disconnected clients
                    for connection in disconnected:
                        if connection in self.active_connections:
                            self.active_connections.remove(connection)

                await asyncio.sleep(self.update_interval)

            except Exception as e:
                self.logger.error(f"Error in data streaming loop: {e}")
                await asyncio.sleep(5)  # Wait before retry

    async def _get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Get latest market data
            market_data = await self.data_manager.get_latest_market_data()

            # Calculate indicators
            indicators = await self.indicator_engine.calculate_all_indicators(market_data)

            # Get trading signals
            signals = await self.data_manager.get_active_signals()

            # Get portfolio status
            portfolio = await self.data_manager.get_portfolio_status()

            return {
                "market_data": market_data,
                "indicators": indicators,
                "signals": signals,
                "portfolio": portfolio,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _subscribe_to_symbols(self, websocket: WebSocket, symbols: List[str]):
        """Subscribe WebSocket to specific trading symbols"""
        # Implementation would depend on specific requirements
        self.logger.info(f"WebSocket subscribed to symbols: {symbols}")

    async def _unsubscribe_from_symbols(self, websocket: WebSocket, symbols: List[str]):
        """Unsubscribe WebSocket from trading symbols"""
        self.logger.info(f"WebSocket unsubscribed from symbols: {symbols}")

    async def _get_historical_data(self, symbol: str, timeframe: str) -> List[Dict]:
        """Get historical data for a trading symbol"""
        if self.data_manager:
            return await self.data_manager.get_historical_data(symbol, timeframe)
        return []


# FastAPI application setup
app = FastAPI(
    title="EAFIX Dashboard Backend",
    description="Real-time trading dashboard with WebSocket streaming",
    version="1.0.0"
)

# Initialize service
dashboard_service = DashboardBackendService()

# Add enterprise endpoints
app.add_api_route("/healthz", dashboard_service.health_check)
app.add_api_route("/readyz", dashboard_service.health_check)
app.add_api_route("/metrics", dashboard_service.get_metrics)

@app.on_event("startup")
async def startup_event():
    await dashboard_service.startup()

@app.on_event("shutdown")
async def shutdown_event():
    await dashboard_service.shutdown()

# WebSocket endpoint for real-time data
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await dashboard_service.connect_websocket(websocket)

# REST API endpoints
@app.get("/api/dashboard/data")
async def get_dashboard_data():
    """Get current dashboard data via REST API"""
    try:
        data = await dashboard_service._get_dashboard_data()
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/indicators/list")
async def get_available_indicators():
    """Get list of available indicators"""
    if dashboard_service.indicator_engine:
        return {"indicators": dashboard_service.indicator_engine.get_available_indicators()}
    return {"indicators": []}

@app.post("/api/indicators/calculate")
async def calculate_indicators(request: Dict[str, Any]):
    """Calculate specific indicators for given data"""
    try:
        if not dashboard_service.indicator_engine:
            raise HTTPException(status_code=503, detail="Indicator engine not available")

        symbol = request.get("symbol")
        indicators = request.get("indicators", [])
        timeframe = request.get("timeframe", "1H")

        # Get market data
        market_data = await dashboard_service.data_manager.get_market_data(symbol, timeframe)

        # Calculate requested indicators
        results = await dashboard_service.indicator_engine.calculate_indicators(
            market_data, indicators
        )

        return {"success": True, "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files for GUI (if needed)
# app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)