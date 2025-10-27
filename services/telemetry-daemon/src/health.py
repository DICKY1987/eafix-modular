"""
Health Check System

Comprehensive health checking for the telemetry daemon service itself,
including dependency health, data freshness, and system resource monitoring.
"""

import asyncio
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

import redis.asyncio as redis
import httpx
import structlog

logger = structlog.get_logger(__name__)


class HealthChecker:
    """Comprehensive health checker for telemetry daemon."""
    
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
        
        # System resource monitoring
        self.process = psutil.Process()
        
        self.running = False
    
    async def start(self) -> None:
        """Start the health checker."""
        # Initialize HTTP client
        timeout = httpx.Timeout(5.0)
        self.http_client = httpx.AsyncClient(timeout=timeout)
        
        # Initialize Redis client
        self.redis_client = redis.from_url(self.settings.redis_url)
        
        self.running = True
        logger.info("Health checker started")
    
    async def stop(self) -> None:
        """Stop the health checker."""
        # Close HTTP client
        if self.http_client:
            await self.http_client.aclose()
        
        # Close Redis client
        if self.redis_client:
            await self.redis_client.close()
        
        self.running = False
        logger.info("Health checker stopped")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        start_time = time.time()
        
        try:
            logger.debug("Starting comprehensive health check")
            
            # Run health checks in parallel
            checks = await asyncio.gather(
                self._check_redis_health(),
                self._check_monitored_services_health(),
                self._check_system_resources(),
                self._check_data_freshness(),
                self._check_disk_space(),
                self._check_telemetry_components(),
                return_exceptions=True
            )
            
            # Process results
            redis_health, services_health, system_health, data_freshness, disk_health, components_health = checks
            
            # Handle exceptions
            for i, result in enumerate(checks):
                if isinstance(result, Exception):
                    check_names = ["redis", "services", "system", "data_freshness", "disk", "components"]
                    logger.error(f"Health check failed: {check_names[i]}", error=str(result))
                    checks[i] = {"healthy": False, "error": str(result)}
            
            # Calculate overall health
            overall_healthy = all([
                self._is_check_healthy(redis_health),
                self._is_check_healthy(services_health),
                self._is_check_healthy(system_health),
                self._is_check_healthy(data_freshness),
                self._is_check_healthy(disk_health),
                self._is_check_healthy(components_health)
            ])
            
            health_score = self._calculate_health_score([
                redis_health, services_health, system_health,
                data_freshness, disk_health, components_health
            ])
            
            check_duration = time.time() - start_time
            
            health_status = {
                "service": "telemetry-daemon",
                "overall_status": "healthy" if overall_healthy else "unhealthy",
                "overall_healthy": overall_healthy,
                "health_score": health_score,
                "timestamp": datetime.utcnow().isoformat(),
                "check_duration_seconds": check_duration,
                
                # Individual checks
                "redis": redis_health,
                "monitored_services": services_health,
                "system_resources": system_health,
                "data_freshness": data_freshness,
                "disk_space": disk_health,
                "telemetry_components": components_health,
                
                # Meta information
                "telemetry_service_info": {
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
                "Health check completed",
                overall_status=health_status["overall_status"],
                health_score=health_score,
                duration_seconds=check_duration
            )
            
            return health_status
            
        except Exception as e:
            check_duration = time.time() - start_time
            logger.error("Health check failed", error=str(e), exc_info=True)
            
            self.metrics.record_health_check(check_duration, False)
            
            return {
                "service": "telemetry-daemon",
                "overall_status": "unhealthy",
                "overall_healthy": False,
                "health_score": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "check_duration_seconds": check_duration
            }
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            if not self.redis_client:
                return {"healthy": False, "error": "Redis client not initialized"}
            
            start_time = time.time()
            
            # Test basic connectivity
            await self.redis_client.ping()
            ping_time = (time.time() - start_time) * 1000
            
            # Test pub/sub functionality
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe("test_channel")
            await pubsub.unsubscribe("test_channel")
            await pubsub.close()
            
            # Get Redis info
            redis_info = await self.redis_client.info()
            
            return {
                "healthy": True,
                "ping_time_ms": ping_time,
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory_human": redis_info.get("used_memory_human", "unknown"),
                "redis_version": redis_info.get("redis_version", "unknown"),
                "uptime_in_seconds": redis_info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "redis_url": self.settings.redis_url
            }
    
    async def _check_monitored_services_health(self) -> Dict[str, Any]:
        """Check health of monitored services."""
        try:
            if not self.http_client:
                return {"healthy": False, "error": "HTTP client not initialized"}
            
            service_results = {}
            healthy_services = 0
            total_services = len(self.settings.monitored_services)
            
            # Check each monitored service
            for service_name, endpoint in self.settings.monitored_services.items():
                try:
                    start_time = time.time()
                    response = await self.http_client.get(f"{endpoint}/healthz")
                    response_time = (time.time() - start_time) * 1000
                    
                    service_healthy = response.status_code == 200
                    if service_healthy:
                        healthy_services += 1
                    
                    service_results[service_name] = {
                        "healthy": service_healthy,
                        "status_code": response.status_code,
                        "response_time_ms": response_time,
                        "endpoint": endpoint
                    }
                    
                except Exception as e:
                    service_results[service_name] = {
                        "healthy": False,
                        "error": str(e),
                        "endpoint": endpoint
                    }
            
            overall_healthy = healthy_services >= (total_services * 0.8)  # 80% threshold
            
            return {
                "healthy": overall_healthy,
                "total_services": total_services,
                "healthy_services": healthy_services,
                "unhealthy_services": total_services - healthy_services,
                "health_percentage": (healthy_services / total_services) * 100,
                "services": service_results
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
            
            # File descriptors (Unix-like systems)
            try:
                fd_count = self.process.num_fds()
            except AttributeError:
                fd_count = None  # Windows doesn't have file descriptors
            
            # Thread count
            thread_count = self.process.num_threads()
            
            # Determine health based on thresholds
            cpu_healthy = cpu_percent < 80.0
            memory_healthy = memory.percent < 85.0
            process_memory_healthy = process_memory.rss < (1024 * 1024 * 1024)  # 1GB
            
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
                    "status": self.process.status()
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_data_freshness(self) -> Dict[str, Any]:
        """Check data freshness and collection status."""
        try:
            # Check if health collection is recent
            collection_healthy = True
            collection_age_minutes = 0
            
            if self.last_health_check:
                age = datetime.utcnow() - self.last_health_check
                collection_age_minutes = age.total_seconds() / 60
                
                # Health data should be fresh (within 5 minutes)
                collection_healthy = collection_age_minutes < 5.0
            
            # Check output directory accessibility
            output_dir = self.settings.get_output_path()
            output_dir_healthy = output_dir.exists() and output_dir.is_dir()
            
            # Check for recent CSV files if CSV output is enabled
            csv_files_healthy = True
            recent_csv_files = 0
            
            if self.settings.csv_output_enabled and output_dir_healthy:
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                
                for csv_file in output_dir.glob("*.csv"):
                    file_time = datetime.fromtimestamp(csv_file.stat().st_mtime)
                    if file_time > cutoff_time:
                        recent_csv_files += 1
                
                # Should have at least some CSV activity in the last hour
                csv_files_healthy = recent_csv_files > 0
            
            overall_healthy = collection_healthy and output_dir_healthy and csv_files_healthy
            
            return {
                "healthy": overall_healthy,
                "health_collection": {
                    "last_check": self.last_health_check.isoformat() if self.last_health_check else None,
                    "age_minutes": collection_age_minutes,
                    "healthy": collection_healthy
                },
                "output_directory": {
                    "path": str(output_dir),
                    "exists": output_dir.exists() if output_dir else False,
                    "accessible": output_dir_healthy
                },
                "csv_files": {
                    "enabled": self.settings.csv_output_enabled,
                    "recent_files": recent_csv_files,
                    "healthy": csv_files_healthy
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space for output directories."""
        try:
            output_dir = self.settings.get_output_path()
            
            # Get disk usage for output directory
            if output_dir.exists():
                disk_usage = psutil.disk_usage(str(output_dir))
                
                free_gb = disk_usage.free / (1024 ** 3)
                total_gb = disk_usage.total / (1024 ** 3)
                used_percent = (disk_usage.used / disk_usage.total) * 100
                
                # Disk healthy if more than 1GB free and less than 90% used
                disk_healthy = free_gb > 1.0 and used_percent < 90.0
                
                return {
                    "healthy": disk_healthy,
                    "output_directory": str(output_dir),
                    "total_gb": round(total_gb, 2),
                    "free_gb": round(free_gb, 2),
                    "used_percent": round(used_percent, 2),
                    "threshold_warnings": {
                        "low_space": free_gb < 1.0,
                        "high_usage": used_percent > 90.0
                    }
                }
            else:
                return {
                    "healthy": False,
                    "error": "Output directory does not exist",
                    "output_directory": str(output_dir)
                }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_telemetry_components(self) -> Dict[str, Any]:
        """Check internal telemetry daemon components."""
        try:
            # This would typically check the health of internal components
            # For now, we'll check basic component states
            
            components = {
                "health_collection_enabled": self.settings.health_collection_enabled,
                "system_aggregation_enabled": self.settings.system_aggregation_enabled,
                "alerting_enabled": self.settings.alerting_enabled,
                "csv_output_enabled": self.settings.csv_output_enabled,
                "publish_health_events": self.settings.publish_health_events
            }
            
            # Check configuration consistency
            config_healthy = True
            config_issues = []
            
            # Validate monitored services configuration
            if not self.settings.monitored_services:
                config_issues.append("No services configured for monitoring")
                config_healthy = False
            
            # Validate output directory
            try:
                output_dir = self.settings.get_output_path()
                if not output_dir.exists():
                    output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                config_issues.append(f"Cannot create output directory: {e}")
                config_healthy = False
            
            # Check interval configurations
            if self.settings.health_collection_interval_seconds <= 0:
                config_issues.append("Invalid health collection interval")
                config_healthy = False
            
            overall_healthy = config_healthy
            
            result = {
                "healthy": overall_healthy,
                "components": components,
                "configuration": {
                    "healthy": config_healthy,
                    "monitored_services_count": len(self.settings.monitored_services),
                    "issues": config_issues
                }
            }
            
            return result
            
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
            0: 0.25,  # Redis (critical for functionality)
            1: 0.20,  # Monitored services (important for purpose)
            2: 0.15,  # System resources (important for stability)
            3: 0.15,  # Data freshness (important for accuracy)
            4: 0.10,  # Disk space (important for operations)
            5: 0.15   # Telemetry components (important for configuration)
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
            "monitored_services_count": len(self.settings.monitored_services),
            "health_collection_enabled": self.settings.health_collection_enabled
        }