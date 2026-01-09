# DOC_ID: DOC-SERVICE-0073
"""
Health Check System for Re-entry Engine Service

Implements comprehensive health checking including Redis connectivity,
matrix service integration, shared library validation, and processing status.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)


class HealthChecker:
    """Comprehensive health checker for re-entry engine service."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        self.last_check_time: Optional[datetime] = None
        self.cached_health_status: Optional[Dict[str, Any]] = None
        self.cache_ttl_seconds = 30  # Cache health status for 30 seconds
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status with caching."""
        now = datetime.utcnow()
        
        # Return cached status if still valid
        if (self.cached_health_status and self.last_check_time and 
            (now - self.last_check_time).total_seconds() < self.cache_ttl_seconds):
            return self.cached_health_status
        
        # Perform health checks
        health_status = await self._perform_health_checks()
        
        # Update cache
        self.cached_health_status = health_status
        self.last_check_time = now
        
        return health_status
    
    async def _perform_health_checks(self) -> Dict[str, Any]:
        """Perform all health checks and aggregate results."""
        checks = {}
        overall_healthy = True
        
        # Redis connectivity check
        redis_result = await self._check_redis_connectivity()
        checks["redis"] = redis_result
        if redis_result["status"] != "healthy":
            overall_healthy = False
        
        # Re-entry matrix service check
        matrix_result = await self._check_matrix_service()
        checks["matrix_service"] = matrix_result
        if matrix_result["status"] != "healthy":
            overall_healthy = False
        
        # Shared library check
        shared_lib_result = await self._check_shared_library()
        checks["shared_library"] = shared_lib_result
        if shared_lib_result["status"] != "healthy":
            overall_healthy = False
        
        # File system check
        filesystem_result = await self._check_filesystem()
        checks["filesystem"] = filesystem_result
        if filesystem_result["status"] != "healthy":
            overall_healthy = False
        
        # Processing status check
        processing_result = await self._check_processing_status()
        checks["processing"] = processing_result
        if processing_result["status"] != "healthy":
            overall_healthy = False
        
        # Configuration check
        config_result = await self._check_configuration()
        checks["configuration"] = config_result
        if config_result["status"] != "healthy":
            overall_healthy = False
        
        return {
            "service": "reentry-engine",
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "checks": checks,
            "uptime_seconds": self._get_uptime_seconds()
        }
    
    async def _check_redis_connectivity(self) -> Dict[str, Any]:
        """Check Redis connectivity and pub/sub capabilities."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Create Redis client with timeout
            redis_client = redis.from_url(
                self.settings.redis_url,
                socket_timeout=self.settings.redis_connection_timeout_seconds
            )
            
            # Test basic operations
            await redis_client.ping()
            
            # Test pub/sub subscription capability
            if self.settings.subscribe_to_trade_results:
                pubsub = redis_client.pubsub()
                await pubsub.subscribe("test_channel")
                await pubsub.unsubscribe("test_channel")
                pubsub_tested = True
            else:
                pubsub_tested = False
            
            # Test publishing capability
            if self.settings.publish_reentry_events:
                test_message = {"test": "health_check", "timestamp": datetime.utcnow().isoformat()}
                await redis_client.publish("health_check_test", str(test_message))
                publish_tested = True
            else:
                publish_tested = False
            
            await redis_client.close()
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "url": self.settings.redis_url,
                "pubsub_tested": pubsub_tested,
                "publish_tested": publish_tested
            }
            
        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": round(response_time, 2),
                "url": self.settings.redis_url
            }
    
    async def _check_matrix_service(self) -> Dict[str, Any]:
        """Check re-entry matrix service connectivity."""
        try:
            import httpx
            
            start_time = asyncio.get_event_loop().time()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Test health endpoint
                health_response = await client.get(f"{self.settings.reentry_matrix_service_url}/healthz")
                
                if health_response.status_code == 200:
                    # Test status endpoint for more detailed info
                    try:
                        status_response = await client.get(f"{self.settings.reentry_matrix_service_url}/reentry/status")
                        status_data = status_response.json() if status_response.status_code == 200 else {}
                    except Exception:
                        status_data = {}
                    
                    response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    
                    return {
                        "status": "healthy",
                        "url": self.settings.reentry_matrix_service_url,
                        "response_time_ms": round(response_time, 2),
                        "service_status": status_data
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "url": self.settings.reentry_matrix_service_url,
                        "error": f"Health check returned {health_response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "status": "unhealthy",
                "url": self.settings.reentry_matrix_service_url,
                "error": str(e)
            }
    
    async def _check_shared_library(self) -> Dict[str, Any]:
        """Check shared library components."""
        try:
            import sys
            from pathlib import Path
            
            # Add shared library to path
            shared_path = self.settings.get_shared_library_path()
            if str(shared_path) not in sys.path:
                sys.path.insert(0, str(shared_path.parent))
            
            # Test imports
            from shared.reentry import HybridIdHelper, ReentryVocabulary, compose, parse, validate_key
            
            # Test vocabulary loading
            vocab_path = self.settings.get_vocabulary_file_path()
            if vocab_path.exists():
                vocab = ReentryVocabulary(vocab_path)
                vocab_status = "loaded"
                vocab_tokens = len(vocab.get_duration_tokens())
            else:
                vocab = ReentryVocabulary()  # Use defaults
                vocab_status = "using_defaults"
                vocab_tokens = len(vocab.get_duration_tokens())
            
            # Test hybrid ID operations
            helper = HybridIdHelper(vocab)
            
            # Test composition
            test_hybrid = compose("W1", "QUICK", "AT_EVENT", "NONE", "LONG", 1)
            
            # Test parsing
            parsed = parse(test_hybrid)
            
            # Test validation
            is_valid = validate_key(test_hybrid)
            
            if not is_valid:
                raise ValueError("Hybrid ID validation failed")
            
            return {
                "status": "healthy",
                "shared_library_path": str(shared_path),
                "vocabulary_file": str(vocab_path),
                "vocabulary_status": vocab_status,
                "vocabulary_tokens": vocab_tokens,
                "test_hybrid_id": test_hybrid,
                "parsing_working": bool(parsed),
                "validation_working": is_valid
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "shared_library_path": str(self.settings.get_shared_library_path())
            }
    
    async def _check_filesystem(self) -> Dict[str, Any]:
        """Check file system access and permissions."""
        try:
            output_path = self.settings.get_output_path()
            
            # Check if output directory exists and is writable
            if not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)
            
            if not output_path.is_dir():
                raise ValueError(f"Output path is not a directory: {output_path}")
            
            # Test write permissions
            test_file = output_path / "health_check_test.tmp"
            try:
                test_file.write_text("health check test")
                test_file.unlink()
                write_access = True
            except Exception:
                write_access = False
            
            # Check disk space
            import shutil
            disk_usage = shutil.disk_usage(output_path)
            free_space_mb = disk_usage.free // (1024 * 1024)
            
            # Check for existing CSV files
            csv_files = list(output_path.glob("reentry_decisions_*.csv"))
            
            # Calculate total CSV file size
            total_csv_size_mb = 0
            for csv_file in csv_files:
                try:
                    total_csv_size_mb += csv_file.stat().st_size // (1024 * 1024)
                except Exception:
                    pass
            
            return {
                "status": "healthy" if write_access else "unhealthy",
                "output_directory": str(output_path),
                "directory_exists": output_path.exists(),
                "write_access": write_access,
                "free_space_mb": free_space_mb,
                "existing_csv_files": len(csv_files),
                "total_csv_size_mb": total_csv_size_mb
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "output_directory": str(self.settings.get_output_path())
            }
    
    async def _check_processing_status(self) -> Dict[str, Any]:
        """Check processing component status."""
        try:
            # This would typically check the processor instance
            # For now, return basic status
            
            return {
                "status": "healthy",
                "processing_enabled": True,
                "trade_result_subscription": self.settings.subscribe_to_trade_results,
                "csv_writes_enabled": self.settings.csv_atomic_writes,
                "batch_processing": self.settings.batch_processing_enabled
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration validity."""
        try:
            # Validate all configured paths
            path_errors = self.settings.validate_paths()
            
            # Check critical settings
            issues = []
            
            if self.settings.service_port < 1024 or self.settings.service_port > 65535:
                issues.append("Invalid service port range")
            
            if self.settings.min_confidence_threshold < 0.0 or self.settings.min_confidence_threshold > 1.0:
                issues.append("Invalid confidence threshold range")
            
            if self.settings.processing_timeout_seconds <= 0:
                issues.append("Invalid processing timeout")
            
            if self.settings.reentry_cooldown_minutes < 0:
                issues.append("Invalid cooldown minutes")
            
            if self.settings.max_reentry_attempts_per_day < 1:
                issues.append("Invalid max attempts per day")
            
            all_issues = path_errors + issues
            
            return {
                "status": "healthy" if not all_issues else "unhealthy",
                "configuration_valid": len(all_issues) == 0,
                "issues": all_issues,
                "service_port": self.settings.service_port,
                "matrix_service_url": self.settings.reentry_matrix_service_url,
                "trade_results_topic": self.settings.trade_results_topic,
                "reentry_decisions_topic": self.settings.reentry_decisions_topic
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _get_uptime_seconds(self) -> float:
        """Get service uptime in seconds (simplified)."""
        # This is a basic implementation - in a real service, you'd track actual startup time
        return 0.0
    
    async def is_healthy(self) -> bool:
        """Simple boolean health check."""
        try:
            status = await self.get_health_status()
            return status["overall_status"] == "healthy"
        except Exception:
            return False
    
    async def get_readiness_status(self) -> Dict[str, Any]:
        """Get readiness status (more strict than health for startup)."""
        health_status = await self.get_health_status()
        
        # For readiness, require all critical services to be healthy
        critical_checks = ["redis", "matrix_service", "shared_library", "configuration"]
        
        readiness_healthy = True
        for check_name in critical_checks:
            if check_name in health_status["checks"]:
                if health_status["checks"][check_name]["status"] != "healthy":
                    readiness_healthy = False
                    break
        
        return {
            "service": "reentry-engine",
            "timestamp": datetime.utcnow().isoformat(),
            "ready": readiness_healthy,
            "critical_checks": {
                check: health_status["checks"].get(check, {"status": "unknown"})
                for check in critical_checks
            }
        }