# DOC_ID: DOC-SERVICE-0097
"""
CSV Router

Routes validated CSV files to appropriate downstream services
based on file type and configured routing rules.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)


class CSVRouter:
    """Routes CSV files to downstream services."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # HTTP clients for downstream services
        self.http_clients: Dict[str, httpx.AsyncClient] = {}
        
        # Routing state
        self.recent_routes: List[Dict[str, Any]] = []
        self._routes_lock = asyncio.Lock()
        
        # Service health tracking
        self.service_health: Dict[str, Dict[str, Any]] = {}
        
        self.running = False
    
    async def start(self) -> None:
        """Start the router."""
        # Initialize HTTP clients for downstream services
        timeout = httpx.Timeout(self.settings.service_timeout_seconds)
        
        for service_name, endpoint in self.settings.service_endpoints.items():
            self.http_clients[service_name] = httpx.AsyncClient(
                base_url=endpoint,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
        
        # Initialize service health tracking
        for service_name in self.settings.service_endpoints:
            self.service_health[service_name] = {
                "healthy": True,
                "last_check": datetime.utcnow(),
                "consecutive_failures": 0
            }
        
        self.running = True
        logger.info(
            "CSV router started",
            downstream_services=list(self.settings.service_endpoints.keys())
        )
    
    async def stop(self) -> None:
        """Stop the router."""
        # Close all HTTP clients
        for client in self.http_clients.values():
            await client.aclose()
        
        self.http_clients.clear()
        self.running = False
        logger.info("CSV router stopped")
    
    async def route_file(self, file_path: Path, file_type: str) -> Dict[str, Any]:
        """
        Route a CSV file to appropriate downstream services.
        
        Args:
            file_path: Path to CSV file
            file_type: Type of CSV file (contract type)
            
        Returns:
            Routing result with details of attempted deliveries
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(
                "Routing file",
                file_path=str(file_path),
                file_type=file_type
            )
            
            # Get destination services for this file type
            destinations = self._get_destinations_for_type(file_type)
            if not destinations:
                logger.warning(
                    "No routing destinations for file type",
                    file_type=file_type
                )
                return {
                    "success": False,
                    "error": f"No routing rules for file type: {file_type}",
                    "file_path": str(file_path),
                    "file_type": file_type
                }
            
            # Route to all destinations
            routing_result = await self.route_file_to_services(
                file_path, file_type, destinations
            )
            
            # Track recent route
            await self._track_recent_route(file_path, file_type, routing_result)
            
            # Record metrics
            routing_time = asyncio.get_event_loop().time() - start_time
            self.metrics.record_file_routing(routing_time, routing_result["success"])
            
            return routing_result
            
        except Exception as e:
            routing_time = asyncio.get_event_loop().time() - start_time
            logger.error(
                "File routing error",
                file_path=str(file_path),
                error=str(e),
                exc_info=True
            )
            
            self.metrics.record_file_routing(routing_time, False)
            self.metrics.record_error("routing_error")
            
            return {
                "success": False,
                "error": str(e),
                "file_path": str(file_path),
                "file_type": file_type
            }
    
    async def route_file_to_services(self, file_path: Path, file_type: str, 
                                   destination_services: List[str]) -> Dict[str, Any]:
        """Route file to specific list of services."""
        start_time = asyncio.get_event_loop().time()
        
        results = {}
        successful_routes = 0
        
        # Route to each destination service
        for service_name in destination_services:
            if service_name not in self.http_clients:
                logger.warning(
                    "Unknown destination service",
                    service=service_name,
                    available_services=list(self.http_clients.keys())
                )
                results[service_name] = {
                    "success": False,
                    "error": "Unknown service"
                }
                continue
            
            # Check service health
            if not await self._is_service_healthy(service_name):
                logger.warning(
                    "Skipping unhealthy service",
                    service=service_name
                )
                results[service_name] = {
                    "success": False,
                    "error": "Service unhealthy"
                }
                continue
            
            # Attempt routing
            route_result = await self._route_to_service(
                file_path, file_type, service_name
            )
            results[service_name] = route_result
            
            if route_result["success"]:
                successful_routes += 1
        
        routing_time = asyncio.get_event_loop().time() - start_time
        overall_success = successful_routes > 0
        
        return {
            "success": overall_success,
            "file_path": str(file_path),
            "file_type": file_type,
            "destinations": destination_services,
            "successful_routes": successful_routes,
            "total_destinations": len(destination_services),
            "results": results,
            "routing_time_seconds": routing_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _route_to_service(self, file_path: Path, file_type: str, 
                              service_name: str) -> Dict[str, Any]:
        """Route file to a specific service."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            client = self.http_clients[service_name]
            
            # Prepare routing payload
            payload = {
                "file_path": str(file_path),
                "file_type": file_type,
                "timestamp": datetime.utcnow().isoformat(),
                "source_service": "transport-router"
            }
            
            # Determine endpoint based on service type and file type
            endpoint = self._get_service_endpoint(service_name, file_type)
            
            # Make HTTP request
            response = await client.post(endpoint, json=payload)
            
            response_time = asyncio.get_event_loop().time() - start_time
            
            if response.status_code in [200, 201, 202]:
                # Success
                await self._update_service_health(service_name, True)
                
                self.metrics.record_service_delivery(
                    service_name, response_time, True
                )
                
                logger.info(
                    "File routed successfully",
                    service=service_name,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    response_time_ms=response_time * 1000
                )
                
                return {
                    "success": True,
                    "service": service_name,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "response_time_seconds": response_time
                }
            else:
                # HTTP error
                await self._update_service_health(service_name, False)
                
                self.metrics.record_service_delivery(
                    service_name, response_time, False
                )
                
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get("detail", "")
                    if error_detail:
                        error_msg = f"{error_msg}: {error_detail}"
                except Exception:
                    pass
                
                logger.error(
                    "File routing failed",
                    service=service_name,
                    status_code=response.status_code,
                    error=error_msg
                )
                
                return {
                    "success": False,
                    "service": service_name,
                    "error": error_msg,
                    "status_code": response.status_code,
                    "response_time_seconds": response_time
                }
                
        except httpx.TimeoutException:
            response_time = asyncio.get_event_loop().time() - start_time
            await self._update_service_health(service_name, False)
            
            self.metrics.record_service_delivery(service_name, response_time, False)
            
            logger.error(
                "Service routing timeout",
                service=service_name,
                timeout_seconds=self.settings.service_timeout_seconds
            )
            
            return {
                "success": False,
                "service": service_name,
                "error": "Timeout",
                "response_time_seconds": response_time
            }
            
        except Exception as e:
            response_time = asyncio.get_event_loop().time() - start_time
            await self._update_service_health(service_name, False)
            
            self.metrics.record_service_delivery(service_name, response_time, False)
            
            logger.error(
                "Service routing error",
                service=service_name,
                error=str(e)
            )
            
            return {
                "success": False,
                "service": service_name,
                "error": str(e),
                "response_time_seconds": response_time
            }
    
    def _get_destinations_for_type(self, file_type: str) -> List[str]:
        """Get destination services for a file type."""
        return self.settings.default_routing_rules.get(file_type, [])
    
    def _get_service_endpoint(self, service_name: str, file_type: str) -> str:
        """Get appropriate endpoint for service and file type."""
        # Default endpoints for different services
        endpoint_mapping = {
            "signal-analyzer": "/analyze/file",
            "risk-manager": "/risk/process-file", 
            "execution-engine": "/execution/ingest-file",
            "reporter": "/reports/ingest",
            "reentry-engine": "/reentry/process",
            "telemetry-daemon": "/telemetry/ingest"
        }
        
        return endpoint_mapping.get(service_name, "/ingest")
    
    async def _is_service_healthy(self, service_name: str) -> bool:
        """Check if service is considered healthy."""
        health_info = self.service_health.get(service_name, {})
        
        # Service is unhealthy if it has too many consecutive failures
        max_failures = 3
        if health_info.get("consecutive_failures", 0) >= max_failures:
            return False
        
        # Check if we need to update health status
        last_check = health_info.get("last_check", datetime.utcnow())
        if (datetime.utcnow() - last_check).seconds > 60:  # Check every minute
            await self._check_service_health(service_name)
        
        return self.service_health[service_name].get("healthy", False)
    
    async def _check_service_health(self, service_name: str) -> None:
        """Check actual health of a service."""
        try:
            client = self.http_clients[service_name]
            response = await client.get("/healthz", timeout=5.0)
            
            healthy = response.status_code == 200
            await self._update_service_health(service_name, healthy)
            
        except Exception:
            await self._update_service_health(service_name, False)
    
    async def _update_service_health(self, service_name: str, healthy: bool) -> None:
        """Update health status of a service."""
        if service_name not in self.service_health:
            self.service_health[service_name] = {
                "healthy": True,
                "last_check": datetime.utcnow(),
                "consecutive_failures": 0
            }
        
        health_info = self.service_health[service_name]
        health_info["last_check"] = datetime.utcnow()
        
        if healthy:
            health_info["healthy"] = True
            health_info["consecutive_failures"] = 0
        else:
            health_info["healthy"] = False
            health_info["consecutive_failures"] = health_info.get("consecutive_failures", 0) + 1
    
    async def _track_recent_route(self, file_path: Path, file_type: str, 
                                 routing_result: Dict[str, Any]) -> None:
        """Track recent routing for status reporting."""
        async with self._routes_lock:
            route_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "file_path": str(file_path),
                "file_type": file_type,
                "success": routing_result["success"],
                "successful_routes": routing_result.get("successful_routes", 0),
                "total_destinations": routing_result.get("total_destinations", 0)
            }
            
            self.recent_routes.append(route_record)
            
            # Keep only last 100 routes
            if len(self.recent_routes) > 100:
                self.recent_routes = self.recent_routes[-100:]
    
    async def get_recent_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently routed files."""
        async with self._routes_lock:
            return self.recent_routes[-limit:] if limit > 0 else self.recent_routes
    
    async def get_routing_rules(self) -> Dict[str, Any]:
        """Get current routing rules."""
        return {
            "enabled": self.settings.routing_enabled,
            "rules": self.settings.default_routing_rules,
            "service_endpoints": self.settings.service_endpoints,
            "timeout_seconds": self.settings.service_timeout_seconds
        }
    
    async def get_service_health_status(self) -> Dict[str, Any]:
        """Get health status of all downstream services."""
        # Update health for all services
        for service_name in self.service_health:
            await self._check_service_health(service_name)
        
        return dict(self.service_health)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get router status."""
        service_health = await self.get_service_health_status()
        healthy_services = sum(1 for info in service_health.values() if info["healthy"])
        
        return {
            "running": self.running,
            "routing_enabled": self.settings.routing_enabled,
            "downstream_services": len(self.http_clients),
            "healthy_services": healthy_services,
            "unhealthy_services": len(self.service_health) - healthy_services,
            "recent_routes_count": len(self.recent_routes),
            "service_health": service_health
        }