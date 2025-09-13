"""
Self-Healing Manager for CLI Multi-Rapid Enterprise Orchestration Platform

Integrates the comprehensive self-healing system with the existing framework,
providing automated error recovery and operational resilience.
"""

import os
import time
import yaml
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass


class ErrorCode(Enum):
    """Standard error codes for self-healing system"""
    ERR_ELEVATION_REQUIRED = "ERR_ELEVATION_REQUIRED"
    ERR_TOOLCHAIN_MISSING = "ERR_TOOLCHAIN_MISSING"
    ERR_AV_BLOCK = "ERR_AV_BLOCK"
    ERR_CLOCK_SKEW = "ERR_CLOCK_SKEW"
    ERR_PATH_DENIED = "ERR_PATH_DENIED"
    ERR_PATH_NOT_FOUND = "ERR_PATH_NOT_FOUND"
    ERR_PATH_UNICODE = "ERR_PATH_UNICODE"
    ERR_RESERVED_NAME = "ERR_RESERVED_NAME"
    ERR_ZONE_IDENTIFIER = "ERR_ZONE_IDENTIFIER"
    ERR_READONLY_ATTR = "ERR_READONLY_ATTR"
    ERR_FILE_LOCKED = "ERR_FILE_LOCKED"
    ERR_YAML_JSON_PARSE = "ERR_YAML_JSON_PARSE"
    ERR_SCHEMA = "ERR_SCHEMA"
    ERR_SCHEMA_EVOLUTION = "ERR_SCHEMA_EVOLUTION"
    ERR_ARCHIVE_CORRUPT = "ERR_ARCHIVE_CORRUPT"
    ERR_CHECKSUM = "ERR_CHECKSUM"
    ERR_SIG_INVALID = "ERR_SIG_INVALID"
    ERR_CONFLICTS = "ERR_CONFLICTS"
    ERR_DISK_SPACE = "ERR_DISK_SPACE"
    ERR_STATE_DRIFT = "ERR_STATE_DRIFT"
    ERR_VERSION_CONSTRAINTS = "ERR_VERSION_CONSTRAINTS"
    ERR_SNAPSHOT_FAIL = "ERR_SNAPSHOT_FAIL"
    ERR_BACKUP_INTEGRITY = "ERR_BACKUP_INTEGRITY"
    ERR_PARTIAL_APPLY = "ERR_PARTIAL_APPLY"
    ERR_MIGRATION_DEPENDENCY = "ERR_MIGRATION_DEPENDENCY"
    ERR_RESOURCE_STARVE = "ERR_RESOURCE_STARVE"
    ERR_HEALTH_FLAKY = "ERR_HEALTH_FLAKY"
    ERR_PORT_BIND = "ERR_PORT_BIND"
    ERR_CONFIG_REGRESSION = "ERR_CONFIG_REGRESSION"
    ERR_ROLLBACK_FAIL = "ERR_ROLLBACK_FAIL"
    ERR_POST_ROLLBACK_DRIFT = "ERR_POST_ROLLBACK_DRIFT"
    ERR_REENTRANT_RUN = "ERR_REENTRANT_RUN"
    ERR_POLICY_VIOLATION = "ERR_POLICY_VIOLATION"
    ERR_AUDIT_WRITE_FAIL = "ERR_AUDIT_WRITE_FAIL"
    ERR_METRICS_EXPORT = "ERR_METRICS_EXPORT"


@dataclass
class SelfHealingResult:
    """Result of a self-healing attempt"""
    success: bool
    error_code: Optional[ErrorCode]
    applied_fixes: List[str]
    attempts: int
    total_time: float
    message: str


class SelfHealingManager:
    """
    Manages self-healing operations for the CLI Multi-Rapid platform.
    
    Provides automated error recovery, retry logic with exponential backoff,
    and integration with the existing orchestration framework.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the self-healing manager"""
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 
                'config', 'self_healing', 'self_healing.yaml'
            )
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize fixer registry
        self.fixers: Dict[ErrorCode, List[Callable]] = {}
        self._register_builtin_fixers()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load self-healing configuration from YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.logger.info(f"Loaded self-healing config from {self.config_path}")
                return config
        except Exception as e:
            self.logger.error(f"Failed to load self-healing config: {e}")
            # Return minimal default config
            return {
                'self_healing': {
                    'max_attempts': 3,
                    'base_backoff_seconds': 10,
                    'max_backoff_seconds': 300,
                    'security_hard_fail': ['ERR_SIG_INVALID'],
                    'fixers': {}
                }
            }
    
    def _register_builtin_fixers(self):
        """Register built-in fixer functions"""
        # Path and file system fixers
        self.fixers[ErrorCode.ERR_PATH_DENIED] = [
            self._fix_acquire_acl,
            self._fix_expand_tilde_env
        ]
        
        self.fixers[ErrorCode.ERR_PATH_NOT_FOUND] = [
            self._fix_expand_tilde_env,
            self._fix_create_missing_path
        ]
        
        self.fixers[ErrorCode.ERR_READONLY_ATTR] = [
            self._fix_clear_readonly,
            self._fix_stop_owning_service
        ]
        
        self.fixers[ErrorCode.ERR_FILE_LOCKED] = [
            self._fix_stop_owning_service,
            self._fix_lock_breaker
        ]
        
        # Disk space and resource fixers
        self.fixers[ErrorCode.ERR_DISK_SPACE] = [
            self._fix_purge_caches,
            self._fix_rotate_logs,
            self._fix_use_staging_volume
        ]
        
        self.fixers[ErrorCode.ERR_RESOURCE_STARVE] = [
            self._fix_throttle,
            self._fix_spill_to_volume,
            self._fix_rotate_logs
        ]
        
        # Configuration and state fixers
        self.fixers[ErrorCode.ERR_CONFIG_REGRESSION] = [
            self._fix_revert_config
        ]
        
        self.fixers[ErrorCode.ERR_STATE_DRIFT] = [
            self._fix_re_plan_with_snapshot
        ]
        
        # Port and service fixers
        self.fixers[ErrorCode.ERR_PORT_BIND] = [
            self._fix_alt_port,
            self._fix_service_order
        ]
        
    def attempt_healing(self, error_code: ErrorCode, context: Dict[str, Any] = None) -> SelfHealingResult:
        """
        Attempt to heal from the specified error code.
        
        Args:
            error_code: The error that occurred
            context: Additional context information for healing
            
        Returns:
            SelfHealingResult with healing attempt details
        """
        if context is None:
            context = {}
            
        start_time = time.time()
        applied_fixes = []
        
        # Check for security hard fail
        sh_config = self.config.get('self_healing', {})
        security_hard_fail = sh_config.get('security_hard_fail', [])
        if error_code.value in security_hard_fail:
            return SelfHealingResult(
                success=False,
                error_code=error_code,
                applied_fixes=[],
                attempts=0,
                total_time=time.time() - start_time,
                message=f"Security hard fail for {error_code.value} - no healing attempted"
            )
        
        max_attempts = sh_config.get('max_attempts', 3)
        base_backoff = sh_config.get('base_backoff_seconds', 10)
        max_backoff = sh_config.get('max_backoff_seconds', 300)
        
        # Get fixers for this error code
        fixers = self.fixers.get(error_code, [])
        if not fixers:
            self.logger.warning(f"No fixers registered for {error_code.value}")
            return SelfHealingResult(
                success=False,
                error_code=error_code,
                applied_fixes=[],
                attempts=0,
                total_time=time.time() - start_time,
                message=f"No fixers available for {error_code.value}"
            )
        
        # Attempt healing with exponential backoff
        for attempt in range(1, max_attempts + 1):
            self.logger.info(f"Healing attempt {attempt}/{max_attempts} for {error_code.value}")
            
            # Try each fixer
            for fixer in fixers:
                try:
                    fixer_name = fixer.__name__
                    self.logger.debug(f"Applying fixer: {fixer_name}")
                    
                    success = fixer(context)
                    applied_fixes.append(fixer_name)
                    
                    if success:
                        return SelfHealingResult(
                            success=True,
                            error_code=error_code,
                            applied_fixes=applied_fixes,
                            attempts=attempt,
                            total_time=time.time() - start_time,
                            message=f"Successfully healed {error_code.value} with {fixer_name}"
                        )
                        
                except Exception as e:
                    self.logger.error(f"Fixer {fixer.__name__} failed: {e}")
                    continue
            
            # Exponential backoff before next attempt
            if attempt < max_attempts:
                backoff_time = min(base_backoff * (2 ** (attempt - 1)), max_backoff)
                self.logger.info(f"Waiting {backoff_time}s before next attempt")
                time.sleep(backoff_time)
        
        return SelfHealingResult(
            success=False,
            error_code=error_code,
            applied_fixes=applied_fixes,
            attempts=max_attempts,
            total_time=time.time() - start_time,
            message=f"All healing attempts failed for {error_code.value}"
        )
    
    def register_custom_fixer(self, error_code: ErrorCode, fixer: Callable):
        """Register a custom fixer function for an error code"""
        if error_code not in self.fixers:
            self.fixers[error_code] = []
        self.fixers[error_code].append(fixer)
        self.logger.info(f"Registered custom fixer {fixer.__name__} for {error_code.value}")
    
    # Built-in fixer implementations
    def _fix_acquire_acl(self, context: Dict[str, Any]) -> bool:
        """Attempt to acquire appropriate ACL permissions"""
        self.logger.info("Attempting to acquire ACL permissions")
        # Implementation would depend on platform and specific requirements
        return False  # Placeholder
    
    def _fix_expand_tilde_env(self, context: Dict[str, Any]) -> bool:
        """Expand tilde and environment variables in paths"""
        self.logger.info("Expanding tilde and environment variables")
        # Implementation would handle path expansion
        return False  # Placeholder
    
    def _fix_create_missing_path(self, context: Dict[str, Any]) -> bool:
        """Create missing directory paths"""
        path = context.get('path')
        if path:
            try:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created missing path: {path}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to create path {path}: {e}")
        return False
    
    def _fix_clear_readonly(self, context: Dict[str, Any]) -> bool:
        """Clear readonly attributes from files"""
        self.logger.info("Clearing readonly attributes")
        # Implementation would clear readonly flags
        return False  # Placeholder
    
    def _fix_stop_owning_service(self, context: Dict[str, Any]) -> bool:
        """Stop services that might be locking files"""
        self.logger.info("Stopping owning services")
        # Implementation would identify and stop relevant services
        return False  # Placeholder
    
    def _fix_lock_breaker(self, context: Dict[str, Any]) -> bool:
        """Break file locks using platform-specific methods"""
        self.logger.info("Breaking file locks")
        # Implementation would use handle.exe or similar tools
        return False  # Placeholder
    
    def _fix_purge_caches(self, context: Dict[str, Any]) -> bool:
        """Purge various cache directories to free disk space"""
        self.logger.info("Purging cache directories")
        # Implementation would clean temp dirs, build caches, etc.
        return False  # Placeholder
    
    def _fix_rotate_logs(self, context: Dict[str, Any]) -> bool:
        """Rotate and compress log files to save space"""
        self.logger.info("Rotating log files")
        # Implementation would handle log rotation
        return False  # Placeholder
    
    def _fix_use_staging_volume(self, context: Dict[str, Any]) -> bool:
        """Switch operations to a staging volume with more space"""
        self.logger.info("Switching to staging volume")
        # Implementation would redirect operations to alternate volume
        return False  # Placeholder
    
    def _fix_throttle(self, context: Dict[str, Any]) -> bool:
        """Throttle resource-intensive operations"""
        self.logger.info("Throttling resource usage")
        # Implementation would reduce operation intensity
        return False  # Placeholder
    
    def _fix_spill_to_volume(self, context: Dict[str, Any]) -> bool:
        """Spill operations to secondary storage"""
        self.logger.info("Spilling to secondary volume")
        # Implementation would move data to alternate storage
        return False  # Placeholder
    
    def _fix_revert_config(self, context: Dict[str, Any]) -> bool:
        """Revert configuration to last known good state"""
        self.logger.info("Reverting configuration")
        # Implementation would restore previous config
        return False  # Placeholder
    
    def _fix_re_plan_with_snapshot(self, context: Dict[str, Any]) -> bool:
        """Re-plan operations using snapshot data"""
        self.logger.info("Re-planning with snapshot")
        # Implementation would re-analyze state from snapshots
        return False  # Placeholder
    
    def _fix_alt_port(self, context: Dict[str, Any]) -> bool:
        """Use alternative port for service binding"""
        self.logger.info("Switching to alternative port")
        # Implementation would find and use available port
        return False  # Placeholder
    
    def _fix_service_order(self, context: Dict[str, Any]) -> bool:
        """Adjust service startup order to resolve conflicts"""
        self.logger.info("Adjusting service startup order")
        # Implementation would reorder service dependencies
        return False  # Placeholder


# Global instance for easy access
_self_healing_manager = None

def get_self_healing_manager() -> SelfHealingManager:
    """Get the global self-healing manager instance"""
    global _self_healing_manager
    if _self_healing_manager is None:
        _self_healing_manager = SelfHealingManager()
    return _self_healing_manager