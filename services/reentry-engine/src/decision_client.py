# DOC_ID: DOC-SERVICE-0072
"""
Re-entry Matrix Service Client

HTTP client for communicating with the re-entry matrix service
to request re-entry decisions based on trade outcomes.
"""

import asyncio
from typing import Dict, Any, Optional
import structlog
import httpx

logger = structlog.get_logger(__name__)


class ReentryMatrixClient:
    """Client for re-entry matrix service."""
    
    def __init__(self, settings):
        self.settings = settings
        self.base_url = settings.reentry_matrix_service_url
        self.timeout = settings.reentry_matrix_timeout_seconds
        
        self.client: Optional[httpx.AsyncClient] = None
        self.running = False
    
    async def start(self) -> None:
        """Start the client."""
        if self.running:
            return
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            headers={"Content-Type": "application/json"}
        )
        
        # Test connectivity
        try:
            response = await self.client.get("/healthz")
            if response.status_code == 200:
                logger.info("Connected to re-entry matrix service", url=self.base_url)
                self.running = True
            else:
                raise httpx.HTTPStatusError(
                    f"Health check failed: {response.status_code}", 
                    request=response.request, 
                    response=response
                )
        except Exception as e:
            logger.error("Failed to connect to re-entry matrix service", error=str(e))
            if self.client:
                await self.client.aclose()
                self.client = None
            raise
    
    async def stop(self) -> None:
        """Stop the client."""
        if not self.running:
            return
        
        if self.client:
            await self.client.aclose()
            self.client = None
        
        self.running = False
        logger.info("Re-entry matrix client stopped")
    
    async def request_reentry_decision(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request a re-entry decision from the matrix service.
        
        Args:
            request_data: Re-entry request data
            
        Returns:
            Re-entry decision response
            
        Raises:
            httpx.HTTPError: If request fails
        """
        if not self.running or not self.client:
            raise RuntimeError("Re-entry matrix client not started")
        
        try:
            logger.info(
                "Requesting re-entry decision",
                trade_id=request_data.get("trade_id"),
                symbol=request_data.get("symbol"),
                outcome=request_data.get("outcome_class")
            )
            
            response = await self.client.post(
                "/reentry/decide",
                json=request_data
            )
            
            response.raise_for_status()
            
            decision_data = response.json()
            
            logger.info(
                "Received re-entry decision",
                trade_id=request_data.get("trade_id"),
                reentry_action=decision_data.get("reentry_action"),
                resolved_tier=decision_data.get("resolved_tier"),
                confidence_score=decision_data.get("confidence_score")
            )
            
            return decision_data
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "Re-entry decision request failed",
                status_code=e.response.status_code,
                error=str(e)
            )
            raise
        except Exception as e:
            logger.error("Re-entry decision request error", error=str(e))
            raise
    
    async def get_matrix_status(self) -> Dict[str, Any]:
        """Get re-entry matrix service status."""
        if not self.running or not self.client:
            return {"status": "disconnected", "error": "Client not started"}
        
        try:
            response = await self.client.get("/reentry/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Failed to get matrix service status", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def get_parameter_sets(self, tier: str) -> Dict[str, Any]:
        """Get parameter sets for a specific tier."""
        if not self.running or not self.client:
            raise RuntimeError("Re-entry matrix client not started")
        
        try:
            response = await self.client.get(f"/reentry/parameters/{tier}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Failed to get parameter sets", tier=tier, error=str(e))
            raise
    
    async def health_check(self) -> bool:
        """Check if matrix service is healthy."""
        try:
            if not self.running or not self.client:
                return False
            
            response = await self.client.get("/healthz")
            return response.status_code == 200
        except Exception:
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get client status."""
        health_ok = await self.health_check()
        
        return {
            "running": self.running,
            "base_url": self.base_url,
            "timeout_seconds": self.timeout,
            "matrix_service_healthy": health_ok,
            "connected": self.client is not None and self.running
        }