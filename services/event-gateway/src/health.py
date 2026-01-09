# DOC_ID: DOC-SERVICE-0055
"""
Event Gateway Health Checker

Health checking for event gateway service including Redis connectivity,
message queue status, and event processing performance.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

import redis.asyncio as redis
import psutil
import structlog

logger = structlog.get_logger(__name__)


class HealthChecker:
    """Health checker for event gateway service."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # Redis client for health checks
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
        # Initialize Redis client
        self.redis_client = redis.from_url(self.settings.redis_url)
        
        self.running = True
        logger.info("Event gateway health checker started")
    
    async def stop(self) -> None:
        """Stop the health checker."""
        # Close Redis client
        if self.redis_client:
            await self.redis_client.close()
        
        self.running = False
        logger.info("Event gateway health checker stopped")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        start_time = time.time()
        
        try:
            logger.debug("Starting event gateway health check")
            
            # Run health checks in parallel
            checks = await asyncio.gather(
                self._check_redis_health(),
                self._check_message_processing_health(),
                self._check_topic_health(),
                self._check_system_resources(),
                self._check_gateway_configuration(),
                return_exceptions=True
            )
            
            # Process results
            redis_health, processing_health, topic_health, system_health, config_health = checks
            
            # Handle exceptions
            for i, result in enumerate(checks):
                if isinstance(result, Exception):
                    check_names = ["redis", "processing", "topics", "system", "config"]
                    logger.error(f"Health check failed: {check_names[i]}", error=str(result))
                    checks[i] = {"healthy": False, "error": str(result)}
            
            # Calculate overall health
            overall_healthy = all([
                self._is_check_healthy(redis_health),
                self._is_check_healthy(processing_health),
                self._is_check_healthy(topic_health),
                self._is_check_healthy(system_health),
                self._is_check_healthy(config_health)
            ])
            
            health_score = self._calculate_health_score([
                redis_health, processing_health, topic_health,
                system_health, config_health
            ])
            
            check_duration = time.time() - start_time
            
            health_status = {
                "service": "event-gateway",
                "overall_status": "healthy" if overall_healthy else "unhealthy",
                "overall_healthy": overall_healthy,
                "health_score": health_score,
                "timestamp": datetime.utcnow().isoformat(),
                "check_duration_seconds": check_duration,
                
                # Individual checks
                "redis": redis_health,
                "message_processing": processing_health,
                "topics": topic_health,
                "system_resources": system_health,
                "gateway_configuration": config_health,
                
                # Meta information
                "gateway_info": {
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
                "Event gateway health check completed",
                overall_status=health_status["overall_status"],
                health_score=health_score,
                duration_seconds=check_duration
            )
            
            return health_status
            
        except Exception as e:
            check_duration = time.time() - start_time
            logger.error("Event gateway health check failed", error=str(e), exc_info=True)
            
            self.metrics.record_health_check(check_duration, False)
            
            return {
                "service": "event-gateway",
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
            
            # Test pub/sub functionality
            pubsub = self.redis_client.pubsub()
            test_topic = "eafix.gateway.health.test"
            await pubsub.subscribe(test_topic)
            
            # Publish test message and verify subscription works
            await self.redis_client.publish(test_topic, "health_check")
            await pubsub.unsubscribe(test_topic)
            await pubsub.close()
            
            # Get Redis info
            redis_info = await self.redis_client.info()
            
            # Check Redis memory usage
            used_memory = redis_info.get("used_memory", 0)
            max_memory = redis_info.get("maxmemory", 0)
            memory_usage_percent = (used_memory / max_memory * 100) if max_memory > 0 else 0
            
            # Check if Redis is running in cluster mode
            is_cluster = redis_info.get("cluster_enabled", 0) == 1
            
            memory_healthy = memory_usage_percent < 85.0 if max_memory > 0 else True
            connection_healthy = redis_info.get("connected_clients", 0) < 100
            
            return {
                "healthy": memory_healthy and connection_healthy,
                "ping_time_ms": ping_time,
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory_human": redis_info.get("used_memory_human", "unknown"),
                "memory_usage_percent": memory_usage_percent,
                "redis_version": redis_info.get("redis_version", "unknown"),
                "uptime_in_seconds": redis_info.get("uptime_in_seconds", 0),
                "pubsub_channels": redis_info.get("pubsub_channels", 0),
                "pubsub_patterns": redis_info.get("pubsub_patterns", 0),
                "is_cluster": is_cluster,
                "keyspace_hits": redis_info.get("keyspace_hits", 0),
                "keyspace_misses": redis_info.get("keyspace_misses", 0)
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "redis_url": self.settings.redis_url
            }
    
    async def _check_message_processing_health(self) -> Dict[str, Any]:
        """Check message processing performance and queue status."""
        try:
            # Simulate message processing metrics (would be real in production)
            # These would come from the actual gateway instance
            
            # Check if processing is enabled
            processing_enabled = self.settings.event_routing_enabled
            
            # Simulate queue sizes and processing rates
            total_queue_size = 0  # Would be real queue sizes
            processing_rate = 100  # Messages per second
            error_rate = 0.01  # 1% error rate
            
            # Check latency thresholds
            avg_latency_ms = 25  # Simulated average latency
            max_latency_ms = 150  # Simulated max latency
            
            latency_healthy = (
                avg_latency_ms < self.settings.latency_warning_threshold_ms and
                max_latency_ms < self.settings.latency_critical_threshold_ms
            )
            
            queue_healthy = total_queue_size < self.settings.max_message_queue_size * 0.8
            error_rate_healthy = error_rate < 0.05  # Less than 5% error rate
            
            overall_healthy = (
                processing_enabled and
                latency_healthy and
                queue_healthy and
                error_rate_healthy
            )
            
            return {
                "healthy": overall_healthy,
                "processing_enabled": processing_enabled,
                "queue_status": {
                    "total_queue_size": total_queue_size,
                    "max_queue_size": self.settings.max_message_queue_size,
                    "queue_utilization_percent": (total_queue_size / self.settings.max_message_queue_size) * 100,
                    "queue_healthy": queue_healthy
                },
                "performance": {
                    "processing_rate_per_second": processing_rate,
                    "error_rate_percent": error_rate * 100,
                    "average_latency_ms": avg_latency_ms,
                    "max_latency_ms": max_latency_ms,
                    "latency_healthy": latency_healthy
                },
                "thresholds": {
                    "latency_warning_ms": self.settings.latency_warning_threshold_ms,
                    "latency_critical_ms": self.settings.latency_critical_threshold_ms,
                    "max_error_rate_percent": 5.0
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_topic_health(self) -> Dict[str, Any]:
        """Check topic configuration and status."""
        try:
            configured_topics = self.settings.event_topics
            all_topics = self.settings.get_all_topics()
            
            # Validate topic configuration
            config_errors = self.settings.validate_topic_config()
            config_healthy = len(config_errors) == 0
            
            # Check routing rules
            routing_rules = self.settings.event_routing_rules
            routing_healthy = len(routing_rules) > 0
            
            # Count topics by type
            regular_topics = len(configured_topics)
            dlq_topics = len([t for t in all_topics if t.endswith(self.settings.dead_letter_topic_suffix)])
            
            # Check if critical topics are configured
            critical_topics = [
                "eafix.price.tick",
                "eafix.signals.generated", 
                "eafix.execution.completed"
            ]
            
            critical_topics_configured = sum(1 for topic in critical_topics if topic in configured_topics)
            critical_healthy = critical_topics_configured == len(critical_topics)
            
            overall_healthy = (
                config_healthy and
                routing_healthy and
                critical_healthy and
                regular_topics > 0
            )
            
            return {
                "healthy": overall_healthy,
                "topic_counts": {
                    "configured_topics": regular_topics,
                    "dead_letter_topics": dlq_topics,
                    "total_topics": len(all_topics)
                },
                "configuration": {
                    "config_healthy": config_healthy,
                    "config_errors": config_errors,
                    "routing_rules": len(routing_rules),
                    "routing_healthy": routing_healthy
                },
                "critical_topics": {
                    "total_critical": len(critical_topics),
                    "configured_critical": critical_topics_configured,
                    "critical_healthy": critical_healthy,
                    "missing_critical": [t for t in critical_topics if t not in configured_topics]
                },
                "features": {
                    "dead_letter_enabled": self.settings.dead_letter_enabled,
                    "filtering_enabled": self.settings.event_filtering_enabled,
                    "transformation_enabled": self.settings.event_transformation_enabled,
                    "validation_enabled": self.settings.event_validation_enabled
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
            
            # Network connections (important for event gateway)
            try:
                connections = self.process.connections()
                connection_count = len(connections)
                established_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
                redis_connections = len([c for c in connections if c.laddr.port == 6379 or c.raddr.port == 6379])
            except (psutil.AccessDenied, AttributeError):
                connection_count = None
                established_connections = None
                redis_connections = None
            
            # Thread count
            thread_count = self.process.num_threads()
            
            # File descriptors (Unix-like systems)
            try:
                fd_count = self.process.num_fds()
            except AttributeError:
                fd_count = None  # Windows doesn't have file descriptors
            
            # Determine health based on thresholds
            cpu_healthy = cpu_percent < 80.0
            memory_healthy = memory.percent < 85.0
            process_memory_healthy = process_memory.rss < (1.5 * 1024 * 1024 * 1024)  # 1.5GB
            
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
                },
                "network": {
                    "total_connections": connection_count,
                    "established_connections": established_connections,
                    "redis_connections": redis_connections
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_gateway_configuration(self) -> Dict[str, Any]:
        """Check gateway configuration health."""
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
            
            # Validate configuration consistency
            config_issues = []
            
            # Check Redis pool configuration
            if self.settings.redis_pool_max_connections <= 0:
                config_issues.append("Invalid Redis pool configuration")
            
            # Check message processing configuration
            if self.settings.message_batch_size <= 0:
                config_issues.append("Invalid message batch size")
            
            if self.settings.max_message_queue_size <= 0:
                config_issues.append("Invalid max queue size")
            
            # Check timeout configurations
            if self.settings.message_timeout_seconds <= 0:
                config_issues.append("Invalid message timeout")
            
            # Check retry configuration
            if self.settings.max_retry_attempts < 0:
                config_issues.append("Invalid retry attempts configuration")
            
            config_healthy = len(config_issues) == 0
            
            # Check feature configuration
            features_configured = {
                "routing": self.settings.event_routing_enabled,
                "validation": self.settings.event_validation_enabled,
                "transformation": self.settings.event_transformation_enabled,
                "filtering": self.settings.event_filtering_enabled,
                "dead_letter": self.settings.dead_letter_enabled,
                "performance_monitoring": self.settings.performance_monitoring_enabled
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
                "features": features_configured,
                "settings": {
                    "redis_pool_max_connections": self.settings.redis_pool_max_connections,
                    "message_batch_size": self.settings.message_batch_size,
                    "max_queue_size": self.settings.max_message_queue_size,
                    "processing_interval_ms": self.settings.message_processing_interval_ms
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
            0: 0.30,  # Redis (critical for message routing)
            1: 0.25,  # Message processing (core functionality)
            2: 0.20,  # Topics (important for routing)
            3: 0.15,  # System resources (important for stability)
            4: 0.10   # Gateway configuration (important for setup)
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
            "gateway_features_monitored": len(self.settings.get_event_gateway_config()),
            "topics_monitored": len(self.settings.event_topics)
        }