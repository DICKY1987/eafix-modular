"""
Flow Orchestrator Health Checker

Health checking for flow orchestrator service, including Redis connectivity,
service registry health, and flow execution monitoring.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import redis.asyncio as redis
import httpx
import psutil
import structlog

logger = structlog.get_logger(__name__)


class HealthChecker:
    """Health checker for flow orchestrator service."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # HTTP client for service health checks
        self.http_client: Optional[httpx.AsyncClient] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Health state tracking
        self.last_health_check = None
        self.health_history: List[Dict[str, Any]] = []
        self._health_lock = asyncio.Lock()
        
        # System monitoring
        self.process = psutil.Process()
        
        self.running = False
    
    async def start(self) -> None:
        """Start the health checker."""
        # Initialize HTTP client
        timeout = httpx.Timeout(self.settings.service_timeout_seconds)
        self.http_client = httpx.AsyncClient(timeout=timeout)
        
        # Initialize Redis client
        self.redis_client = redis.from_url(self.settings.redis_url)
        
        self.running = True
        logger.info("Flow orchestrator health checker started")
    
    async def stop(self) -> None:
        """Stop the health checker."""
        # Close HTTP client
        if self.http_client:
            await self.http_client.aclose()
        
        # Close Redis client
        if self.redis_client:
            await self.redis_client.close()
        
        self.running = False
        logger.info("Flow orchestrator health checker stopped")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        start_time = time.time()
        
        try:
            logger.debug("Starting flow orchestrator health check")
            
            # Run health checks in parallel
            checks = await asyncio.gather(
                self._check_redis_health(),
                self._check_service_registry_health(),
                self._check_flow_system_health(),
                self._check_system_resources(),
                self._check_orchestrator_components(),
                return_exceptions=True
            )
            
            # Process results
            redis_health, registry_health, flow_health, system_health, components_health = checks
            
            # Handle exceptions
            for i, result in enumerate(checks):
                if isinstance(result, Exception):
                    check_names = ["redis", "registry", "flows", "system", "components"]
                    logger.error(f"Health check failed: {check_names[i]}", error=str(result))
                    checks[i] = {"healthy": False, "error": str(result)}
            
            # Calculate overall health
            overall_healthy = all([
                self._is_check_healthy(redis_health),
                self._is_check_healthy(registry_health),
                self._is_check_healthy(flow_health),
                self._is_check_healthy(system_health),
                self._is_check_healthy(components_health)
            ])
            
            health_score = self._calculate_health_score([
                redis_health, registry_health, flow_health,
                system_health, components_health
            ])
            
            check_duration = time.time() - start_time
            
            health_status = {
                "service": "flow-orchestrator",
                "overall_status": "healthy" if overall_healthy else "unhealthy",
                "overall_healthy": overall_healthy,
                "health_score": health_score,
                "timestamp": datetime.utcnow().isoformat(),
                "check_duration_seconds": check_duration,
                
                # Individual checks
                "redis": redis_health,
                "service_registry": registry_health,
                "flow_system": flow_health,
                "system_resources": system_health,
                "orchestrator_components": components_health,
                
                # Meta information
                "orchestrator_info": {
                    "running": self.running,
                    "uptime_seconds": self._get_uptime_seconds(),
                    "process_id": self.process.pid,
                    "service_port": self.settings.service_port
                }
            }
            
            # Store in history
            await self._store_health_result(health_status)
            
            # Record metrics
            self.metrics.record_health_check(check_duration, overall_healthy)
            
            self.last_health_check = datetime.utcnow()
            
            logger.info(
                "Flow orchestrator health check completed",
                overall_status=health_status["overall_status"],
                health_score=health_score,
                duration_seconds=check_duration
            )
            
            return health_status
            
        except Exception as e:
            check_duration = time.time() - start_time
            logger.error("Flow orchestrator health check failed", error=str(e), exc_info=True)
            
            self.metrics.record_health_check(check_duration, False)
            
            return {
                "service": "flow-orchestrator",
                "overall_status": "unhealthy",
                "overall_healthy": False,
                "health_score": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "check_duration_seconds": check_duration
            }
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity and pub/sub functionality."""
        try:
            if not self.redis_client:
                return {"healthy": False, "error": "Redis client not initialized"}
            
            start_time = time.time()
            
            # Test basic connectivity
            await self.redis_client.ping()
            ping_time = (time.time() - start_time) * 1000
            
            # Test pub/sub functionality (critical for flow orchestration)
            pubsub = self.redis_client.pubsub()
            test_topic = "eafix.orchestrator.health.test"
            await pubsub.subscribe(test_topic)
            
            # Publish test message
            await self.redis_client.publish(test_topic, "health_check")
            
            # Try to receive the message (with timeout)
            message_received = False
            try:
                async with asyncio.timeout(2.0):
                    async for message in pubsub.listen():
                        if message["type"] == "message":
                            message_received = True
                            break
            except asyncio.TimeoutError:
                pass
            
            await pubsub.unsubscribe(test_topic)
            await pubsub.close()
            
            # Get Redis info
            redis_info = await self.redis_client.info()
            
            return {
                "healthy": True,
                "ping_time_ms": ping_time,
                "pubsub_working": message_received,
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory_human": redis_info.get("used_memory_human", "unknown"),
                "redis_version": redis_info.get("redis_version", "unknown"),
                "uptime_in_seconds": redis_info.get("uptime_in_seconds", 0),
                "pubsub_channels": redis_info.get("pubsub_channels", 0),
                "pubsub_patterns": redis_info.get("pubsub_patterns", 0)
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "redis_url": self.settings.redis_url
            }
    
    async def _check_service_registry_health(self) -> Dict[str, Any]:
        """Check health of all registered services."""
        try:
            if not self.http_client:
                return {"healthy": False, "error": "HTTP client not initialized"}
            
            service_results = {}
            healthy_services = 0
            total_services = len(self.settings.service_registry)
            
            # Check each registered service
            for service_name, service_info in self.settings.service_registry.items():
                try:
                    endpoint = service_info["endpoint"]
                    health_path = service_info.get("health_path", "/healthz")
                    health_url = f"{endpoint}{health_path}"
                    
                    start_time = time.time()
                    response = await self.http_client.get(health_url)
                    response_time = (time.time() - start_time) * 1000
                    
                    service_healthy = response.status_code == 200
                    if service_healthy:
                        healthy_services += 1
                    
                    service_results[service_name] = {
                        "healthy": service_healthy,
                        "status_code": response.status_code,
                        "response_time_ms": response_time,
                        "endpoint": endpoint,
                        "role": service_info.get("role", "unknown"),
                        "priority": service_info.get("priority", 0)
                    }
                    
                except Exception as e:
                    service_results[service_name] = {
                        "healthy": False,
                        "error": str(e),
                        "endpoint": service_info["endpoint"],
                        "role": service_info.get("role", "unknown")
                    }
            
            # Calculate health based on service criticality
            critical_services = [
                name for name, info in self.settings.service_registry.items()
                if info.get("role") in ["data_source", "processor", "validator"]
            ]
            
            critical_healthy = sum(
                1 for name in critical_services 
                if service_results.get(name, {}).get("healthy", False)
            )
            
            # Registry is healthy if at least 80% of services are up and all critical services are up
            registry_healthy = (
                healthy_services >= (total_services * 0.8) and
                critical_healthy == len(critical_services)
            )
            
            return {
                "healthy": registry_healthy,
                "total_services": total_services,
                "healthy_services": healthy_services,
                "unhealthy_services": total_services - healthy_services,
                "health_percentage": (healthy_services / total_services) * 100,
                "critical_services": len(critical_services),
                "critical_healthy": critical_healthy,
                "services": service_results
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_flow_system_health(self) -> Dict[str, Any]:
        """Check flow orchestration system health."""
        try:
            # Check flow configuration validity
            config_errors = self.settings.validate_flow_definitions()
            config_healthy = len(config_errors) == 0
            
            # Check enabled flows
            enabled_flows = self.settings.get_enabled_flows()
            total_flows = len(self.settings.flow_definitions)
            
            # Check event routing
            routing_rules = self.settings.event_routing_rules
            routing_healthy = len(routing_rules) > 0
            
            # Simulate flow metrics (would be real in production)
            flow_metrics_healthy = True  # Placeholder
            
            overall_healthy = (
                config_healthy and
                len(enabled_flows) > 0 and
                routing_healthy and
                flow_metrics_healthy
            )
            
            return {
                "healthy": overall_healthy,
                "configuration": {
                    "valid": config_healthy,
                    "errors": config_errors
                },
                "flows": {
                    "total_defined": total_flows,
                    "enabled": len(enabled_flows),
                    "disabled": total_flows - len(enabled_flows)
                },
                "event_routing": {
                    "rules_configured": len(routing_rules),
                    "healthy": routing_healthy
                },
                "orchestration": {
                    "enabled": self.settings.flow_orchestration_enabled,
                    "monitoring_enabled": self.settings.flow_monitoring_enabled
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Process-specific metrics
            process_memory = self.process.memory_info()
            process_cpu = self.process.cpu_percent()
            
            # Thread and connection counts
            thread_count = self.process.num_threads()
            
            # File descriptors (Unix-like systems)
            try:
                fd_count = self.process.num_fds()
            except AttributeError:
                fd_count = None  # Windows doesn't have file descriptors
            
            # Network connections
            try:
                connections = self.process.connections()
                connection_count = len(connections)
                established_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
            except (psutil.AccessDenied, AttributeError):
                connection_count = None
                established_connections = None
            
            # Determine health based on thresholds
            cpu_healthy = cpu_percent < 85.0
            memory_healthy = memory.percent < 90.0
            process_memory_healthy = process_memory.rss < (2 * 1024 * 1024 * 1024)  # 2GB
            
            overall_healthy = cpu_healthy and memory_healthy and process_memory_healthy
            
            return {
                "healthy": overall_healthy,
                "system": {
                    "cpu_percent": cpu_percent,
                    "cpu_healthy": cpu_healthy,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024 ** 3),
                    "memory_healthy": memory_healthy
                },
                "process": {
                    "pid": self.process.pid,
                    "cpu_percent": process_cpu,
                    "memory_rss_mb": process_memory.rss / (1024 * 1024),
                    "memory_vms_mb": process_memory.vms / (1024 * 1024),
                    "memory_healthy": process_memory_healthy,
                    "thread_count": thread_count,
                    "fd_count": fd_count,
                    "connection_count": connection_count,
                    "established_connections": established_connections,
                    "status": self.process.status()
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_orchestrator_components(self) -> Dict[str, Any]:
        """Check orchestrator-specific components."""
        try:
            # Check output directory
            output_dir = self.settings.get_output_path()
            output_dir_healthy = True
            
            try:
                if not output_dir.exists():
                    output_dir.mkdir(parents=True, exist_ok=True)
                output_dir_accessible = output_dir.is_dir()
            except Exception as e:
                output_dir_accessible = False
                output_dir_healthy = False
            
            # Check contracts directory
            contracts_dir = self.settings.get_contracts_path()
            contracts_accessible = contracts_dir.exists() and contracts_dir.is_dir()
            
            # Check configuration consistency
            config_issues = []
            
            # Validate service registry
            if not self.settings.service_registry:
                config_issues.append("No services registered")
            
            # Validate flow definitions
            config_errors = self.settings.validate_flow_definitions()
            config_issues.extend(config_errors)
            
            # Validate event routing
            if not self.settings.event_routing_rules:
                config_issues.append("No event routing rules configured")
            
            config_healthy = len(config_issues) == 0
            
            # Check feature flags
            features = {
                "flow_orchestration": self.settings.flow_orchestration_enabled,
                "flow_monitoring": self.settings.flow_monitoring_enabled,
                "circuit_breaker": self.settings.circuit_breaker_enabled,
                "event_publishing": self.settings.publish_flow_events
            }
            
            overall_healthy = (
                output_dir_healthy and
                contracts_accessible and
                config_healthy
            )
            
            return {
                "healthy": overall_healthy,
                "directories": {
                    "output": {
                        "path": str(output_dir),
                        "exists": output_dir.exists() if output_dir else False,
                        "accessible": output_dir_accessible
                    },
                    "contracts": {
                        "path": str(contracts_dir),
                        "exists": contracts_dir.exists() if contracts_dir else False,
                        "accessible": contracts_accessible
                    }
                },
                "configuration": {
                    "healthy": config_healthy,
                    "issues": config_issues
                },
                "features": features,
                "settings": {
                    "max_concurrent_flows": self.settings.max_concurrent_flows,
                    "flow_timeout_seconds": self.settings.flow_timeout_seconds,
                    "monitoring_interval": self.settings.flow_monitoring_interval_seconds
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def _is_check_healthy(self, check_result: Dict[str, Any]) -> bool:
        """Determine if a health check result is healthy."""
        return check_result.get("healthy", False)
    
    def _calculate_health_score(self, check_results: List[Dict[str, Any]]) -> float:
        """Calculate overall health score from individual checks."""
        if not check_results:
            return 0.0
        
        # Assign weights to different checks
        weights = {
            0: 0.30,  # Redis (critical for flow orchestration)
            1: 0.25,  # Service registry (important for coordination)
            2: 0.20,  # Flow system (core functionality)
            3: 0.15,  # System resources (important for stability)
            4: 0.10   # Orchestrator components (important for configuration)
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for i, result in enumerate(check_results):
            weight = weights.get(i, 0.1)
            total_weight += weight
            
            if self._is_check_healthy(result):
                total_score += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _get_uptime_seconds(self) -> float:
        """Get service uptime in seconds."""
        try:
            create_time = self.process.create_time()
            return time.time() - create_time
        except Exception:
            return 0.0
    
    async def _store_health_result(self, health_result: Dict[str, Any]) -> None:
        """Store health check result in history."""
        async with self._health_lock:
            # Add to history
            self.health_history.append({
                "timestamp": health_result["timestamp"],
                "overall_healthy": health_result["overall_healthy"],
                "health_score": health_result["health_score"],
                "check_duration": health_result["check_duration_seconds"]
            })
            
            # Keep only recent history (last 1000 checks)
            if len(self.health_history) > 1000:
                self.health_history = self.health_history[-1000:]
    
    async def get_health_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent health check history."""
        async with self._health_lock:
            return self.health_history[-limit:]
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary statistics."""
        async with self._health_lock:
            if not self.health_history:
                return {
                    "available": False,
                    "message": "No health history available"
                }
            
            recent_checks = self.health_history[-50:]  # Last 50 checks
            
            healthy_count = sum(1 for check in recent_checks if check["overall_healthy"])
            avg_health_score = sum(check["health_score"] for check in recent_checks) / len(recent_checks)
            avg_check_duration = sum(check["check_duration"] for check in recent_checks) / len(recent_checks)
            
            return {
                "available": True,
                "total_checks": len(self.health_history),
                "recent_checks": len(recent_checks),
                "health_percentage": (healthy_count / len(recent_checks)) * 100,
                "average_health_score": avg_health_score,
                "average_check_duration_seconds": avg_check_duration,
                "last_check": recent_checks[-1]["timestamp"] if recent_checks else None
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get health checker status."""
        return {
            "running": self.running,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_history_count": len(self.health_history),
            "monitored_services_count": len(self.settings.service_registry),
            "orchestration_enabled": self.settings.flow_orchestration_enabled
        }