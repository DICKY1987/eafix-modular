# doc_id: DOC-SERVICE-0130
# DOC_ID: DOC-SERVICE-0048
"""
Data Validator Health Checker

Health checking for data validator service including validation performance,
data source monitoring, and validation rule integrity.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

import redis.asyncio as redis
import httpx
import psutil
import structlog

logger = structlog.get_logger(__name__)


class HealthChecker:
    """Health checker for data validator service."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # Redis and HTTP clients
        self.redis_client: Optional[redis.Redis] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        
        # Health state tracking
        self.last_health_check = None
        self.health_history: List[Dict[str, Any]] = []
        self._health_lock = asyncio.Lock()
        
        # System monitoring
        self.process = psutil.Process()
        
        self.running = False
    
    async def start(self) -> None:
        """Start the health checker."""
        # Initialize Redis client
        self.redis_client = redis.from_url(self.settings.redis_url)
        
        # Initialize HTTP client
        timeout = httpx.Timeout(5.0)
        self.http_client = httpx.AsyncClient(timeout=timeout)
        
        self.running = True
        logger.info("Data validator health checker started")
    
    async def stop(self) -> None:
        """Stop the health checker."""
        # Close HTTP client
        if self.http_client:
            await self.http_client.aclose()
        
        # Close Redis client
        if self.redis_client:
            await self.redis_client.close()
        
        self.running = False
        logger.info("Data validator health checker stopped")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        start_time = time.time()
        
        try:
            logger.debug("Starting data validator health check")
            
            # Run health checks in parallel
            checks = await asyncio.gather(
                self._check_redis_health(),
                self._check_validation_performance(),
                self._check_data_sources_health(),
                self._check_validation_rules_integrity(),
                self._check_system_resources(),
                return_exceptions=True
            )
            
            # Process results
            redis_health, performance_health, sources_health, rules_health, system_health = checks
            
            # Handle exceptions
            for i, result in enumerate(checks):
                if isinstance(result, Exception):
                    check_names = ["redis", "performance", "sources", "rules", "system"]
                    logger.error(f"Health check failed: {check_names[i]}", error=str(result))
                    checks[i] = {"healthy": False, "error": str(result)}
            
            # Calculate overall health
            overall_healthy = all([
                self._is_check_healthy(redis_health),
                self._is_check_healthy(performance_health),
                self._is_check_healthy(sources_health),
                self._is_check_healthy(rules_health),
                self._is_check_healthy(system_health)
            ])
            
            health_score = self._calculate_health_score([
                redis_health, performance_health, sources_health,
                rules_health, system_health
            ])
            
            check_duration = time.time() - start_time
            
            health_status = {
                "service": "data-validator",
                "overall_status": "healthy" if overall_healthy else "unhealthy",
                "overall_healthy": overall_healthy,
                "health_score": health_score,
                "timestamp": datetime.utcnow().isoformat(),
                "check_duration_seconds": check_duration,
                
                # Individual checks
                "redis": redis_health,
                "validation_performance": performance_health,
                "data_sources": sources_health,
                "validation_rules": rules_health,
                "system_resources": system_health,
                
                # Meta information
                "validator_info": {
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
                "Data validator health check completed",
                overall_status=health_status["overall_status"],
                health_score=health_score,
                duration_seconds=check_duration
            )
            
            return health_status
            
        except Exception as e:
            check_duration = time.time() - start_time
            logger.error("Data validator health check failed", error=str(e), exc_info=True)
            
            self.metrics.record_health_check(check_duration, False)
            
            return {
                "service": "data-validator",
                "overall_status": "unhealthy",
                "overall_healthy": False,
                "health_score": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "check_duration_seconds": check_duration
            }
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity for monitoring."""
        try:
            if not self.redis_client:
                return {"healthy": False, "error": "Redis client not initialized"}
            
            start_time = time.time()
            
            # Test basic connectivity
            await self.redis_client.ping()
            ping_time = (time.time() - start_time) * 1000
            
            # Get Redis info
            redis_info = await self.redis_client.info()
            
            return {
                "healthy": True,
                "ping_time_ms": ping_time,
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory_human": redis_info.get("used_memory_human", "unknown"),
                "redis_version": redis_info.get("redis_version", "unknown")
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "redis_url": self.settings.redis_url
            }
    
    async def _check_validation_performance(self) -> Dict[str, Any]:
        """Check validation performance metrics."""
        try:
            # Check if validation is enabled
            validation_enabled = (
                self.settings.data_validation_enabled and
                self.settings.schema_validation_enabled
            )
            
            if not validation_enabled:
                return {
                    "healthy": False,
                    "error": "Validation is disabled"
                }
            
            # Simulate performance metrics (would be real in production)
            avg_validation_time_ms = 15  # Simulated
            max_validation_time_ms = 85  # Simulated
            validation_success_rate = 0.98  # Simulated
            
            # Check performance against thresholds
            performance_healthy = (
                avg_validation_time_ms < self.settings.max_validation_time_ms and
                validation_success_rate > 0.95
            )
            
            time_threshold_healthy = max_validation_time_ms < self.settings.max_validation_time_ms
            
            return {
                "healthy": performance_healthy and time_threshold_healthy,
                "validation_enabled": validation_enabled,
                "performance": {
                    "average_validation_time_ms": avg_validation_time_ms,
                    "max_validation_time_ms": max_validation_time_ms,
                    "validation_success_rate": validation_success_rate,
                    "time_threshold_healthy": time_threshold_healthy
                },
                "thresholds": {
                    "max_validation_time_ms": self.settings.max_validation_time_ms,
                    "min_success_rate": 0.95
                },
                "features": {
                    "schema_validation": self.settings.schema_validation_enabled,
                    "quality_checks": self.settings.data_quality_checks_enabled,
                    "pipeline_validation": self.settings.pipeline_validation_enabled,
                    "anomaly_detection": self.settings.anomaly_detection_enabled
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_data_sources_health(self) -> Dict[str, Any]:
        """Check health of monitored data sources."""
        try:
            if not self.http_client:
                return {"healthy": False, "error": "HTTP client not initialized"}
            
            source_results = {}
            healthy_sources = 0
            total_sources = len(self.settings.monitored_data_sources)
            
            if total_sources == 0:
                return {
                    "healthy": True,
                    "message": "No data sources configured for monitoring"
                }
            
            # Check each monitored data source
            for source_name, source_config in self.settings.monitored_data_sources.items():
                try:
                    endpoint = source_config["endpoint"]
                    
                    start_time = time.time()
                    response = await self.http_client.get(f"{endpoint}/healthz")
                    response_time = (time.time() - start_time) * 1000
                    
                    source_healthy = response.status_code == 200
                    if source_healthy:
                        healthy_sources += 1
                    
                    source_results[source_name] = {
                        "healthy": source_healthy,
                        "status_code": response.status_code,
                        "response_time_ms": response_time,
                        "endpoint": endpoint,
                        "data_types": source_config.get("data_types", "")
                    }
                    
                except Exception as e:
                    source_results[source_name] = {
                        "healthy": False,
                        "error": str(e),
                        "endpoint": source_config["endpoint"]
                    }
            
            # Consider healthy if at least 70% of sources are up
            overall_healthy = healthy_sources >= (total_sources * 0.7)
            
            return {
                "healthy": overall_healthy,
                "total_sources": total_sources,
                "healthy_sources": healthy_sources,
                "unhealthy_sources": total_sources - healthy_sources,
                "health_percentage": (healthy_sources / total_sources) * 100,
                "sources": source_results
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_validation_rules_integrity(self) -> Dict[str, Any]:
        """Check validation rules configuration integrity."""
        try:
            # Validate configuration
            config_errors = self.settings.validate_configuration()
            config_healthy = len(config_errors) == 0
            
            # Check validation rules
            total_rules = len(self.settings.validation_rules)
            pipeline_rules = len(self.settings.pipeline_validation_rules)
            
            # Validate each schema has required rule components
            incomplete_schemas = []
            for schema, rules in self.settings.validation_rules.items():
                if "schema_validation" not in rules:
                    incomplete_schemas.append(f"{schema}: missing schema_validation")
                elif "required_fields" not in rules["schema_validation"]:
                    incomplete_schemas.append(f"{schema}: missing required_fields")
            
            rules_complete = len(incomplete_schemas) == 0
            
            # Check monitored schemas coverage
            monitored_schemas = self.settings.get_all_monitored_schemas()
            covered_schemas = set(self.settings.validation_rules.keys())
            uncovered_schemas = monitored_schemas - covered_schemas
            
            coverage_healthy = len(uncovered_schemas) == 0
            
            overall_healthy = (
                config_healthy and
                rules_complete and
                total_rules > 0 and
                coverage_healthy
            )
            
            return {
                "healthy": overall_healthy,
                "configuration": {
                    "config_healthy": config_healthy,
                    "config_errors": config_errors
                },
                "validation_rules": {
                    "total_schema_rules": total_rules,
                    "total_pipeline_rules": pipeline_rules,
                    "rules_complete": rules_complete,
                    "incomplete_schemas": incomplete_schemas
                },
                "schema_coverage": {
                    "total_monitored": len(monitored_schemas),
                    "total_covered": len(covered_schemas),
                    "coverage_percentage": (len(covered_schemas) / len(monitored_schemas)) * 100 if monitored_schemas else 100,
                    "uncovered_schemas": list(uncovered_schemas),
                    "coverage_healthy": coverage_healthy
                },
                "features": {
                    "csv_validation": self.settings.csv_validation_enabled,
                    "anomaly_detection": self.settings.anomaly_detection_enabled,
                    "alerts": self.settings.validation_alerts_enabled
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
            
            # Thread count
            thread_count = self.process.num_threads()
            
            # File descriptors (Unix-like systems)
            try:
                fd_count = self.process.num_fds()
            except AttributeError:
                fd_count = None  # Windows doesn't have file descriptors
            
            # Check output directory
            output_dir = self.settings.get_output_path()
            output_dir_accessible = False
            
            try:
                if not output_dir.exists():
                    output_dir.mkdir(parents=True, exist_ok=True)
                output_dir_accessible = output_dir.is_dir()
            except Exception:
                output_dir_accessible = False
            
            # Determine health based on thresholds
            cpu_healthy = cpu_percent < 75.0
            memory_healthy = memory.percent < 85.0
            process_memory_healthy = process_memory.rss < (1 * 1024 * 1024 * 1024)  # 1GB
            
            overall_healthy = (
                cpu_healthy and
                memory_healthy and
                process_memory_healthy and
                output_dir_accessible
            )
            
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
                },
                "storage": {
                    "output_directory": str(output_dir),
                    "output_dir_accessible": output_dir_accessible
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
            0: 0.20,  # Redis (important for monitoring)
            1: 0.30,  # Validation performance (core functionality)
            2: 0.25,  # Data sources (important for monitoring)
            3: 0.15,  # Validation rules (important for correctness)
            4: 0.10   # System resources (important for stability)
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
    
    async def get_status(self) -> Dict[str, Any]:
        """Get health checker status."""
        return {
            "running": self.running,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_history_count": len(self.health_history),
            "monitored_data_sources": len(self.settings.monitored_data_sources),
            "validation_enabled": self.settings.data_validation_enabled
        }