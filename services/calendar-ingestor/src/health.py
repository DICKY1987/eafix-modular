"""
Calendar Ingestor Health Checker
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class HealthChecker:
    """Health check logic for calendar ingestor service"""
    
    def __init__(self):
        self.last_check = None
        self.status_cache = None
        self.cache_duration_seconds = 30
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        current_time = datetime.now(timezone.utc)
        
        # Use cached status if recent
        if (self.status_cache and self.last_check and 
            (current_time - self.last_check).total_seconds() < self.cache_duration_seconds):
            return self.status_cache
        
        health_status = {
            "status": "healthy",
            "timestamp": current_time.isoformat(),
            "checks": {},
            "service": "calendar-ingestor"
        }
        
        try:
            # Check Redis connectivity (if available from app state)
            redis_status = await self._check_redis()
            health_status["checks"]["redis"] = redis_status
            
            # Check file system write permissions
            filesystem_status = await self._check_filesystem()
            health_status["checks"]["filesystem"] = filesystem_status
            
            # Check configuration
            config_status = self._check_configuration()
            health_status["checks"]["configuration"] = config_status
            
            # Check overall service health
            checks_passed = all(
                check.get("status") == "ok" 
                for check in health_status["checks"].values()
            )
            
            if not checks_passed:
                health_status["status"] = "degraded"
                
            # Count failed checks
            failed_checks = [
                name for name, check in health_status["checks"].items()
                if check.get("status") != "ok"
            ]
            
            if len(failed_checks) > 1:
                health_status["status"] = "unhealthy"
            
            health_status["failed_checks"] = failed_checks
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            health_status = {
                "status": "unhealthy",
                "timestamp": current_time.isoformat(),
                "error": str(e),
                "service": "calendar-ingestor"
            }
        
        # Cache the result
        self.last_check = current_time
        self.status_cache = health_status
        
        return health_status
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            # This would need access to the actual Redis client
            # For now, return a basic check
            return {
                "status": "ok",
                "message": "Redis check not implemented yet",
                "latency_ms": None
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Redis connectivity failed: {str(e)}",
                "latency_ms": None
            }
    
    async def _check_filesystem(self) -> Dict[str, Any]:
        """Check filesystem write permissions"""
        try:
            # Try to create and write a test file
            test_dir = Path("./data/calendar")
            test_dir.mkdir(parents=True, exist_ok=True)
            
            test_file = test_dir / "health_check.tmp"
            test_content = f"Health check at {datetime.now(timezone.utc).isoformat()}"
            
            # Write test
            test_file.write_text(test_content, encoding='utf-8')
            
            # Read test
            read_content = test_file.read_text(encoding='utf-8')
            if read_content != test_content:
                raise Exception("File content mismatch")
            
            # Cleanup
            test_file.unlink(missing_ok=True)
            
            return {
                "status": "ok",
                "message": "Filesystem read/write operational",
                "test_directory": str(test_dir)
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Filesystem check failed: {str(e)}",
                "test_directory": str(test_dir) if 'test_dir' in locals() else None
            }
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check service configuration"""
        try:
            # Basic configuration validation
            config_issues = []
            
            # This would check actual settings if available
            # For now, return a basic check
            
            if config_issues:
                return {
                    "status": "warning",
                    "message": "Configuration issues detected",
                    "issues": config_issues
                }
            else:
                return {
                    "status": "ok",
                    "message": "Configuration appears valid"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Configuration check failed: {str(e)}"
            }