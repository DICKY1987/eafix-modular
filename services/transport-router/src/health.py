# DOC_ID: DOC-SERVICE-0094
"""
Health Check System for Transport Router Service

Comprehensive health checking including file system monitoring,
downstream service connectivity, validation capabilities, and routing status.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

import redis.asyncio as redis
import httpx
import structlog

logger = structlog.get_logger(__name__)


class HealthChecker:
    """Comprehensive health checker for transport router service."""
    
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
        
        # File system check
        filesystem_result = await self._check_filesystem()
        checks["filesystem"] = filesystem_result
        if filesystem_result["status"] != "healthy":
            overall_healthy = False
        
        # Watched directories check
        directories_result = await self._check_watched_directories()
        checks["watched_directories"] = directories_result
        if directories_result["status"] != "healthy":
            overall_healthy = False
        
        # Downstream services check
        services_result = await self._check_downstream_services()
        checks["downstream_services"] = services_result
        # Don't fail overall health if some services are down - this is expected
        
        # Contract system check
        contracts_result = await self._check_contract_system()
        checks["contract_system"] = contracts_result
        if contracts_result["status"] != "healthy":
            overall_healthy = False
        
        # Configuration check
        config_result = await self._check_configuration()
        checks["configuration"] = config_result
        if config_result["status"] != "healthy":
            overall_healthy = False
        
        return {
            "service": "transport-router",
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
                socket_timeout=5.0
            )
            
            # Test basic operations
            await redis_client.ping()
            
            # Test publishing capability if enabled
            if self.settings.publish_file_events:
                test_message = {"test": "health_check", "timestamp": datetime.utcnow().isoformat()}
                await redis_client.publish("health_check_test", json.dumps(test_message))
                publish_tested = True
            else:
                publish_tested = False
            
            await redis_client.close()
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "url": self.settings.redis_url,
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
    
    async def _check_filesystem(self) -> Dict[str, Any]:
        """Check file system access and permissions."""
        try:
            output_path = self.settings.get_output_path()
            dead_letter_path = self.settings.get_dead_letter_path()
            
            issues = []
            
            # Check output directory
            if not output_path.exists():
                try:
                    output_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create output directory {output_path}: {e}")
            
            if output_path.exists() and not output_path.is_dir():
                issues.append(f"Output path is not a directory: {output_path}")
            
            # Test write permissions on output directory
            if output_path.exists() and output_path.is_dir():
                test_file = output_path / "health_check_test.tmp"
                try:
                    test_file.write_text("health check test")
                    test_file.unlink()
                    output_writable = True
                except Exception:
                    output_writable = False
                    issues.append(f"Output directory not writable: {output_path}")
            else:
                output_writable = False
            
            # Check dead letter directory
            if not dead_letter_path.exists():
                try:
                    dead_letter_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create dead letter directory {dead_letter_path}: {e}")
            
            # Check disk space
            import shutil
            disk_usage = shutil.disk_usage(output_path if output_path.exists() else Path.cwd())
            free_space_mb = disk_usage.free // (1024 * 1024)
            free_space_gb = free_space_mb // 1024
            
            if free_space_gb < 1:  # Less than 1GB free
                issues.append(f"Low disk space: {free_space_gb}GB free")
            
            return {
                "status": "healthy" if not issues else "unhealthy",
                "output_directory": str(output_path),
                "output_writable": output_writable,
                "dead_letter_directory": str(dead_letter_path),
                "free_space_mb": free_space_mb,
                "free_space_gb": free_space_gb,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_watched_directories(self) -> Dict[str, Any]:
        """Check watched directories status."""
        try:
            watched_paths = self.settings.get_watched_paths()
            directory_status = []
            accessible_dirs = 0
            total_csv_files = 0
            
            for path in watched_paths:
                dir_info = {
                    "path": str(path),
                    "exists": path.exists(),
                    "is_directory": path.is_dir() if path.exists() else False,
                    "readable": False,
                    "csv_file_count": 0
                }
                
                if path.exists() and path.is_dir():
                    try:
                        # Test readability
                        list(path.iterdir())
                        dir_info["readable"] = True
                        accessible_dirs += 1
                        
                        # Count CSV files
                        if self.settings.watch_recursive:
                            csv_files = list(path.rglob("*.csv"))
                        else:
                            csv_files = list(path.glob("*.csv"))
                        
                        dir_info["csv_file_count"] = len(csv_files)
                        total_csv_files += len(csv_files)
                        
                    except Exception as e:
                        dir_info["error"] = str(e)
                
                directory_status.append(dir_info)
            
            # Determine overall status
            if self.settings.file_watching_enabled:
                if accessible_dirs == 0:
                    status = "unhealthy"
                elif accessible_dirs < len(watched_paths) / 2:  # Less than half accessible
                    status = "degraded"
                else:
                    status = "healthy"
            else:
                status = "healthy"  # Not enabled, so don't fail
            
            return {
                "status": status,
                "file_watching_enabled": self.settings.file_watching_enabled,
                "total_directories": len(watched_paths),
                "accessible_directories": accessible_dirs,
                "total_csv_files": total_csv_files,
                "recursive_watching": self.settings.watch_recursive,
                "directory_details": directory_status
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_downstream_services(self) -> Dict[str, Any]:
        """Check downstream service connectivity."""
        if not self.settings.downstream_health_check_enabled:
            return {
                "status": "skipped",
                "reason": "downstream health checks disabled"
            }
        
        try:
            service_results = {}
            healthy_services = 0
            total_services = len(self.settings.service_endpoints)
            
            # Check each downstream service
            timeout = httpx.Timeout(5.0)
            
            for service_name, endpoint in self.settings.service_endpoints.items():
                start_time = asyncio.get_event_loop().time()
                
                try:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await client.get(f"{endpoint}/healthz")
                        response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                        
                        if response.status_code == 200:
                            service_results[service_name] = {
                                "status": "healthy",
                                "endpoint": endpoint,
                                "response_time_ms": round(response_time, 2)
                            }
                            healthy_services += 1
                        else:
                            service_results[service_name] = {
                                "status": "unhealthy",
                                "endpoint": endpoint,
                                "error": f"HTTP {response.status_code}",
                                "response_time_ms": round(response_time, 2)
                            }
                            
                except Exception as e:
                    response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                    service_results[service_name] = {
                        "status": "unhealthy",
                        "endpoint": endpoint,
                        "error": str(e),
                        "response_time_ms": round(response_time, 2)
                    }
            
            # Overall status based on service health
            if healthy_services == total_services:
                overall_status = "healthy"
            elif healthy_services > total_services / 2:
                overall_status = "degraded"
            else:
                overall_status = "unhealthy"
            
            return {
                "status": overall_status,
                "total_services": total_services,
                "healthy_services": healthy_services,
                "unhealthy_services": total_services - healthy_services,
                "service_details": service_results
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_contract_system(self) -> Dict[str, Any]:
        """Check contract system availability."""
        try:
            contracts_path = self.settings.get_contracts_path()
            shared_lib_path = self.settings.get_shared_library_path()
            
            issues = []
            
            # Check contracts directory
            if not contracts_path.exists():
                issues.append(f"Contracts directory not found: {contracts_path}")
            
            # Check shared library
            if not shared_lib_path.exists():
                issues.append(f"Shared library not found: {shared_lib_path}")
            
            # Test contract model imports
            try:
                import sys
                if str(contracts_path) not in sys.path:
                    sys.path.insert(0, str(contracts_path))
                
                from contracts.models import ActiveCalendarSignal, ReentryDecision
                contract_imports_ok = True
            except Exception as e:
                issues.append(f"Contract imports failed: {e}")
                contract_imports_ok = False
            
            return {
                "status": "healthy" if not issues else "unhealthy",
                "contracts_path": str(contracts_path),
                "shared_library_path": str(shared_lib_path),
                "contract_imports_ok": contract_imports_ok,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration validity."""
        try:
            # Validate paths
            path_errors = self.settings.validate_paths()
            
            # Check critical settings
            issues = []
            
            if self.settings.service_port < 1024 or self.settings.service_port > 65535:
                issues.append("Invalid service port range")
            
            if self.settings.service_timeout_seconds <= 0:
                issues.append("Invalid service timeout")
            
            if self.settings.max_file_size_mb <= 0:
                issues.append("Invalid max file size")
            
            if not self.settings.service_endpoints:
                issues.append("No downstream service endpoints configured")
            
            if self.settings.file_watching_enabled and not self.settings.watched_directories:
                issues.append("File watching enabled but no directories configured")
            
            all_issues = path_errors + issues
            
            return {
                "status": "healthy" if not all_issues else "unhealthy",
                "configuration_valid": len(all_issues) == 0,
                "issues": all_issues,
                "service_port": self.settings.service_port,
                "file_watching_enabled": self.settings.file_watching_enabled,
                "routing_enabled": self.settings.routing_enabled,
                "validation_enabled": {
                    "checksums": self.settings.checksum_validation_enabled,
                    "sequences": self.settings.sequence_validation_enabled,
                    "schemas": self.settings.schema_validation_enabled
                }
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
        """Get readiness status (more strict than health)."""
        health_status = await self.get_health_status()
        
        # For readiness, require core systems to be healthy
        critical_checks = ["redis", "filesystem", "contract_system", "configuration"]
        
        readiness_healthy = True
        for check_name in critical_checks:
            if check_name in health_status["checks"]:
                if health_status["checks"][check_name]["status"] != "healthy":
                    readiness_healthy = False
                    break
        
        return {
            "service": "transport-router",
            "timestamp": datetime.utcnow().isoformat(),
            "ready": readiness_healthy,
            "critical_checks": {
                check: health_status["checks"].get(check, {"status": "unknown"})
                for check in critical_checks
            }
        }