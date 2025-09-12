"""
Cross-Language Error Handler
============================

Unified error handling and logging across Python, MQL4, and PowerShell systems.
Provides standardized error reporting and recovery mechanisms.
"""

import logging
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high" 
    CRITICAL = "critical"


class LanguageSystem(Enum):
    """Supported language systems."""
    PYTHON = "python"
    MQL4 = "mql4"
    POWERSHELL = "powershell"
    BRIDGE = "bridge"


class CrossLanguageErrorHandler:
    """Handles errors across all language systems with unified reporting."""
    
    def __init__(self, log_directory: Optional[Path] = None):
        """Initialize cross-language error handler.
        
        Args:
            log_directory: Directory for error log files
        """
        self.log_directory = log_directory or Path("logs")
        self.log_directory.mkdir(exist_ok=True)
        
        # Error log files for each system
        self.error_logs = {
            LanguageSystem.PYTHON: self.log_directory / "python_errors.log",
            LanguageSystem.MQL4: self.log_directory / "mql4_errors.log", 
            LanguageSystem.POWERSHELL: self.log_directory / "powershell_errors.log",
            LanguageSystem.BRIDGE: self.log_directory / "bridge_errors.log"
        }
        
        # Central error registry
        self.error_registry_file = self.log_directory / "error_registry.json"
        self.error_registry = self._load_error_registry()
        
        logger.info(f"CrossLanguageErrorHandler initialized with log directory: {self.log_directory}")
    
    def handle_python_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                           severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> str:
        """Handle Python error with context and logging.
        
        Args:
            error: The Python exception
            context: Additional context information
            severity: Error severity level
            
        Returns:
            Error ID for tracking
        """
        error_info = {
            "system": LanguageSystem.PYTHON.value,
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "severity": severity.value,
            "context": context or {}
        }
        
        error_id = self._register_error(error_info)
        self._log_to_file(LanguageSystem.PYTHON, error_info, error_id)
        
        logger.error(f"Python error [{error_id}]: {error_info['error_type']} - {error_info['error_message']}")
        
        return error_id
    
    def handle_mql4_error(self, error_code: int, error_message: str, 
                         context: Optional[Dict[str, Any]] = None,
                         severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> str:
        """Handle MQL4 error with context and logging.
        
        Args:
            error_code: MQL4 error code
            error_message: Error message from MQL4
            context: Additional context information
            severity: Error severity level
            
        Returns:
            Error ID for tracking
        """
        error_info = {
            "system": LanguageSystem.MQL4.value,
            "timestamp": datetime.now().isoformat(),
            "error_type": "MQL4Error",
            "error_code": error_code,
            "error_message": error_message,
            "severity": severity.value,
            "context": context or {}
        }
        
        error_id = self._register_error(error_info)
        self._log_to_file(LanguageSystem.MQL4, error_info, error_id)
        
        logger.error(f"MQL4 error [{error_id}]: Code {error_code} - {error_message}")
        
        return error_id
    
    def handle_powershell_error(self, error_message: str, exit_code: Optional[int] = None,
                               context: Optional[Dict[str, Any]] = None,
                               severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> str:
        """Handle PowerShell error with context and logging.
        
        Args:
            error_message: Error message from PowerShell
            exit_code: PowerShell exit code
            context: Additional context information
            severity: Error severity level
            
        Returns:
            Error ID for tracking
        """
        error_info = {
            "system": LanguageSystem.POWERSHELL.value,
            "timestamp": datetime.now().isoformat(),
            "error_type": "PowerShellError",
            "error_message": error_message,
            "exit_code": exit_code,
            "severity": severity.value,
            "context": context or {}
        }
        
        error_id = self._register_error(error_info)
        self._log_to_file(LanguageSystem.POWERSHELL, error_info, error_id)
        
        logger.error(f"PowerShell error [{error_id}]: {error_message} (exit code: {exit_code})")
        
        return error_id
    
    def handle_bridge_error(self, error_message: str, source_system: Optional[LanguageSystem] = None,
                           target_system: Optional[LanguageSystem] = None,
                           context: Optional[Dict[str, Any]] = None,
                           severity: ErrorSeverity = ErrorSeverity.HIGH) -> str:
        """Handle cross-language bridge error.
        
        Args:
            error_message: Bridge error message
            source_system: Source language system
            target_system: Target language system
            context: Additional context information
            severity: Error severity level
            
        Returns:
            Error ID for tracking
        """
        error_info = {
            "system": LanguageSystem.BRIDGE.value,
            "timestamp": datetime.now().isoformat(),
            "error_type": "BridgeError",
            "error_message": error_message,
            "source_system": source_system.value if source_system else None,
            "target_system": target_system.value if target_system else None,
            "severity": severity.value,
            "context": context or {}
        }
        
        error_id = self._register_error(error_info)
        self._log_to_file(LanguageSystem.BRIDGE, error_info, error_id)
        
        logger.error(f"Bridge error [{error_id}]: {error_message}")
        
        return error_id
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics across all systems.
        
        Returns:
            Dictionary with error statistics
        """
        stats = {
            "total_errors": len(self.error_registry),
            "by_system": {},
            "by_severity": {},
            "recent_errors": []
        }
        
        # Count by system
        for error_id, error_info in self.error_registry.items():
            system = error_info.get("system", "unknown")
            stats["by_system"][system] = stats["by_system"].get(system, 0) + 1
        
        # Count by severity
        for error_id, error_info in self.error_registry.items():
            severity = error_info.get("severity", "unknown")
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
        
        # Get recent errors (last 10)
        sorted_errors = sorted(
            self.error_registry.items(),
            key=lambda x: x[1].get("timestamp", ""),
            reverse=True
        )
        stats["recent_errors"] = [
            {
                "error_id": error_id,
                "system": error_info.get("system"),
                "error_type": error_info.get("error_type"),
                "error_message": error_info.get("error_message", "")[:100],  # Truncate long messages
                "severity": error_info.get("severity"),
                "timestamp": error_info.get("timestamp")
            }
            for error_id, error_info in sorted_errors[:10]
        ]
        
        return stats
    
    def get_error_report(self, system: Optional[LanguageSystem] = None,
                        severity: Optional[ErrorSeverity] = None,
                        limit: int = 50) -> List[Dict[str, Any]]:
        """Get filtered error report.
        
        Args:
            system: Filter by language system
            severity: Filter by error severity
            limit: Maximum number of errors to return
            
        Returns:
            List of error information dictionaries
        """
        filtered_errors = []
        
        for error_id, error_info in self.error_registry.items():
            # Apply filters
            if system and error_info.get("system") != system.value:
                continue
            if severity and error_info.get("severity") != severity.value:
                continue
            
            error_report = {
                "error_id": error_id,
                **error_info
            }
            filtered_errors.append(error_report)
        
        # Sort by timestamp (most recent first) and limit
        filtered_errors.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return filtered_errors[:limit]
    
    def clear_old_errors(self, days_old: int = 30) -> int:
        """Clear errors older than specified days.
        
        Args:
            days_old: Number of days to keep errors
            
        Returns:
            Number of errors cleared
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cutoff_iso = cutoff_date.isoformat()
        
        errors_to_remove = []
        for error_id, error_info in self.error_registry.items():
            error_timestamp = error_info.get("timestamp", "")
            if error_timestamp < cutoff_iso:
                errors_to_remove.append(error_id)
        
        # Remove old errors
        for error_id in errors_to_remove:
            del self.error_registry[error_id]
        
        # Save updated registry
        self._save_error_registry()
        
        logger.info(f"Cleared {len(errors_to_remove)} errors older than {days_old} days")
        
        return len(errors_to_remove)
    
    def suggest_remediation(self, error_id: str) -> List[str]:
        """Suggest remediation steps for a specific error.
        
        Args:
            error_id: Error ID to get suggestions for
            
        Returns:
            List of suggested remediation steps
        """
        if error_id not in self.error_registry:
            return ["Error not found in registry"]
        
        error_info = self.error_registry[error_id]
        system = error_info.get("system")
        error_type = error_info.get("error_type", "")
        error_message = error_info.get("error_message", "")
        
        suggestions = []
        
        # System-specific suggestions
        if system == LanguageSystem.PYTHON.value:
            suggestions.extend(self._get_python_remediation_suggestions(error_type, error_message))
        elif system == LanguageSystem.MQL4.value:
            suggestions.extend(self._get_mql4_remediation_suggestions(error_info.get("error_code"), error_message))
        elif system == LanguageSystem.POWERSHELL.value:
            suggestions.extend(self._get_powershell_remediation_suggestions(error_message, error_info.get("exit_code")))
        elif system == LanguageSystem.BRIDGE.value:
            suggestions.extend(self._get_bridge_remediation_suggestions(error_message))
        
        # General suggestions
        suggestions.extend([
            "Check system logs for additional context",
            "Verify configuration files are correct",
            "Ensure all required dependencies are installed",
            "Check network connectivity if applicable"
        ])
        
        return suggestions[:10]  # Limit to top 10 suggestions
    
    def _register_error(self, error_info: Dict[str, Any]) -> str:
        """Register error in central registry.
        
        Args:
            error_info: Error information dictionary
            
        Returns:
            Generated error ID
        """
        import hashlib
        
        # Generate error ID based on timestamp and error content
        error_content = f"{error_info['timestamp']}{error_info['system']}{error_info['error_message']}"
        error_id = hashlib.md5(error_content.encode()).hexdigest()[:8]
        
        # Ensure unique ID
        base_id = error_id
        counter = 1
        while error_id in self.error_registry:
            error_id = f"{base_id}_{counter}"
            counter += 1
        
        self.error_registry[error_id] = error_info
        self._save_error_registry()
        
        return error_id
    
    def _log_to_file(self, system: LanguageSystem, error_info: Dict[str, Any], error_id: str) -> None:
        """Log error to system-specific log file.
        
        Args:
            system: Language system
            error_info: Error information
            error_id: Error ID
        """
        try:
            log_file = self.error_logs[system]
            
            with open(log_file, 'a', encoding='utf-8') as f:
                timestamp = error_info.get('timestamp', '')
                severity = error_info.get('severity', 'unknown')
                error_type = error_info.get('error_type', 'Unknown')
                error_message = error_info.get('error_message', '')
                
                f.write(f"[{timestamp}] [{error_id}] [{severity.upper()}] {error_type}: {error_message}\n")
                
                # Add additional details for some systems
                if system == LanguageSystem.PYTHON and 'traceback' in error_info:
                    f.write(f"Traceback:\n{error_info['traceback']}\n")
                elif system == LanguageSystem.MQL4 and 'error_code' in error_info:
                    f.write(f"MQL4 Error Code: {error_info['error_code']}\n")
                elif system == LanguageSystem.POWERSHELL and 'exit_code' in error_info:
                    f.write(f"Exit Code: {error_info['exit_code']}\n")
                
                f.write("---\n")
        
        except Exception as exc:
            logger.warning(f"Failed to write to log file {log_file}: {exc}")
    
    def _load_error_registry(self) -> Dict[str, Any]:
        """Load error registry from file.
        
        Returns:
            Error registry dictionary
        """
        if not self.error_registry_file.exists():
            return {}
        
        try:
            with open(self.error_registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as exc:
            logger.warning(f"Failed to load error registry: {exc}")
            return {}
    
    def _save_error_registry(self) -> None:
        """Save error registry to file."""
        try:
            with open(self.error_registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.error_registry, f, indent=2)
        except Exception as exc:
            logger.warning(f"Failed to save error registry: {exc}")
    
    def _get_python_remediation_suggestions(self, error_type: str, error_message: str) -> List[str]:
        """Get Python-specific remediation suggestions."""
        suggestions = []
        
        if "ImportError" in error_type or "ModuleNotFoundError" in error_type:
            suggestions.extend([
                "Install missing Python module using pip",
                "Check if module name is spelled correctly",
                "Verify Python environment and PATH"
            ])
        elif "FileNotFoundError" in error_type:
            suggestions.extend([
                "Verify file path exists and is accessible",
                "Check file permissions",
                "Ensure working directory is correct"
            ])
        elif "ConnectionError" in error_type or "timeout" in error_message.lower():
            suggestions.extend([
                "Check network connectivity",
                "Verify service is running and accessible",
                "Increase timeout values if necessary"
            ])
        
        return suggestions
    
    def _get_mql4_remediation_suggestions(self, error_code: Optional[int], error_message: str) -> List[str]:
        """Get MQL4-specific remediation suggestions."""
        suggestions = []
        
        if error_code:
            # Common MQL4 error codes
            if error_code == 1:
                suggestions.append("Check MQL4 syntax and compilation errors")
            elif error_code == 2:
                suggestions.append("Verify array bounds and indices")
            elif error_code == 4:
                suggestions.append("Check server connection and trading permissions")
            elif error_code in [130, 131, 132]:
                suggestions.append("Verify trading parameters (stops, lots, prices)")
        
        if "terminal" in error_message.lower():
            suggestions.extend([
                "Check MetaTrader 4 installation",
                "Verify terminal is running and logged in",
                "Check DDE connection settings"
            ])
        
        return suggestions
    
    def _get_powershell_remediation_suggestions(self, error_message: str, exit_code: Optional[int]) -> List[str]:
        """Get PowerShell-specific remediation suggestions."""
        suggestions = []
        
        if exit_code:
            if exit_code == 1:
                suggestions.append("Check PowerShell script syntax and parameters")
            elif exit_code == -1:
                suggestions.append("Verify PowerShell execution policy allows script execution")
        
        if "execution policy" in error_message.lower():
            suggestions.extend([
                "Set PowerShell execution policy to RemoteSigned or Unrestricted",
                "Use Set-ExecutionPolicy cmdlet with appropriate scope"
            ])
        elif "not found" in error_message.lower():
            suggestions.extend([
                "Verify PowerShell is installed and in PATH", 
                "Check if required PowerShell modules are available"
            ])
        
        return suggestions
    
    def _get_bridge_remediation_suggestions(self, error_message: str) -> List[str]:
        """Get bridge-specific remediation suggestions."""
        suggestions = []
        
        if "configuration" in error_message.lower():
            suggestions.extend([
                "Verify unified configuration is properly propagated",
                "Check configuration file permissions and accessibility",
                "Ensure all required configuration sections are present"
            ])
        elif "communication" in error_message.lower():
            suggestions.extend([
                "Check network connectivity between systems",
                "Verify API endpoints are accessible",
                "Check firewall and port configurations"
            ])
        elif "timeout" in error_message.lower():
            suggestions.extend([
                "Increase timeout values in configuration",
                "Check system performance and resource usage",
                "Verify target system is responsive"
            ])
        
        return suggestions