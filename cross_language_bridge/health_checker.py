"""
Cross-System Health Checker
===========================

Validates health and connectivity across Python, MQL4, and PowerShell systems.
Provides unified health checking and monitoring capabilities.
"""

import subprocess
import socket
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
import json

logger = logging.getLogger(__name__)


class CrossSystemHealthChecker:
    """Checks health and connectivity across all language systems."""
    
    def __init__(self, config_manager=None):
        """Initialize cross-system health checker.
        
        Args:
            config_manager: UnifiedConfigManager instance
        """
        self.config_manager = config_manager
        self.health_results = {}
        
        logger.info("CrossSystemHealthChecker initialized")
    
    def check_python_health(self) -> Dict[str, Any]:
        """Check Python system health.
        
        Returns:
            Dictionary with Python health status
        """
        health_status = {
            "system": "python",
            "status": "unknown",
            "checks": [],
            "timestamp": time.time()
        }
        
        try:
            # Check Python interpreter
            import sys
            python_version = sys.version
            health_status["checks"].append({
                "name": "python_interpreter",
                "status": "healthy",
                "details": f"Python {python_version.split()[0]}"
            })
            
            # Check required modules
            required_modules = ["json", "pathlib", "subprocess", "socket"]
            for module_name in required_modules:
                try:
                    __import__(module_name)
                    health_status["checks"].append({
                        "name": f"module_{module_name}",
                        "status": "healthy",
                        "details": f"Module {module_name} available"
                    })
                except ImportError:
                    health_status["checks"].append({
                        "name": f"module_{module_name}",
                        "status": "unhealthy",
                        "details": f"Module {module_name} not available"
                    })
            
            # Check workflow orchestrator
            try:
                from workflows.orchestrator import WorkflowOrchestrator
                health_status["checks"].append({
                    "name": "workflow_orchestrator",
                    "status": "healthy",
                    "details": "Workflow orchestrator available"
                })
            except ImportError as exc:
                health_status["checks"].append({
                    "name": "workflow_orchestrator", 
                    "status": "warning",
                    "details": f"Workflow orchestrator unavailable: {exc}"
                })
            
            # Overall Python health
            unhealthy_checks = [c for c in health_status["checks"] if c["status"] == "unhealthy"]
            if unhealthy_checks:
                health_status["status"] = "unhealthy"
            else:
                health_status["status"] = "healthy"
            
            logger.info("Python health check completed successfully")
            
        except Exception as exc:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(exc)
            logger.error(f"Python health check failed: {exc}")
        
        return health_status
    
    def check_mql4_health(self) -> Dict[str, Any]:
        """Check MQL4 system health.
        
        Returns:
            Dictionary with MQL4 health status
        """
        health_status = {
            "system": "mql4",
            "status": "unknown", 
            "checks": [],
            "timestamp": time.time()
        }
        
        try:
            # Check for MQL4 configuration file
            config_file = Path("config/mql4_config.mqh")
            if config_file.exists():
                health_status["checks"].append({
                    "name": "mql4_config",
                    "status": "healthy",
                    "details": "MQL4 configuration file exists"
                })
            else:
                health_status["checks"].append({
                    "name": "mql4_config",
                    "status": "warning",
                    "details": "MQL4 configuration file not found"
                })
            
            # Check for MetaTrader installation (Windows-specific)
            try:
                mt4_paths = [
                    Path("C:/Program Files (x86)/MetaTrader 4/terminal.exe"),
                    Path("C:/Program Files/MetaTrader 4/terminal.exe"),
                    Path(os.environ.get("MT4_PATH", "")) / "terminal.exe" if os.environ.get("MT4_PATH") else None
                ]
                
                mt4_found = False
                for mt4_path in mt4_paths:
                    if mt4_path and mt4_path.exists():
                        health_status["checks"].append({
                            "name": "metatrader4",
                            "status": "healthy",
                            "details": f"MetaTrader 4 found at {mt4_path}"
                        })
                        mt4_found = True
                        break
                
                if not mt4_found:
                    health_status["checks"].append({
                        "name": "metatrader4",
                        "status": "warning",
                        "details": "MetaTrader 4 installation not found"
                    })
            
            except Exception:
                health_status["checks"].append({
                    "name": "metatrader4",
                    "status": "warning", 
                    "details": "Could not check MetaTrader 4 installation"
                })
            
            # Check DDE connection capabilities (Windows-specific)
            try:
                import pywin32  # noqa
                health_status["checks"].append({
                    "name": "dde_support",
                    "status": "healthy",
                    "details": "DDE support available (pywin32 installed)"
                })
            except ImportError:
                health_status["checks"].append({
                    "name": "dde_support",
                    "status": "warning",
                    "details": "DDE support not available (pywin32 not installed)"
                })
            
            # Overall MQL4 health
            unhealthy_checks = [c for c in health_status["checks"] if c["status"] == "unhealthy"]
            warning_checks = [c for c in health_status["checks"] if c["status"] == "warning"]
            
            if unhealthy_checks:
                health_status["status"] = "unhealthy"
            elif warning_checks:
                health_status["status"] = "degraded"
            else:
                health_status["status"] = "healthy"
            
            logger.info("MQL4 health check completed")
            
        except Exception as exc:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(exc)
            logger.error(f"MQL4 health check failed: {exc}")
        
        return health_status
    
    def check_powershell_health(self) -> Dict[str, Any]:
        """Check PowerShell system health.
        
        Returns:
            Dictionary with PowerShell health status
        """
        health_status = {
            "system": "powershell",
            "status": "unknown",
            "checks": [],
            "timestamp": time.time()
        }
        
        try:
            # Check PowerShell availability
            try:
                result = subprocess.run(
                    ["powershell", "-Command", "$PSVersionTable.PSVersion.Major"],
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                if result.returncode == 0:
                    ps_version = result.stdout.strip()
                    health_status["checks"].append({
                        "name": "powershell_interpreter",
                        "status": "healthy",
                        "details": f"PowerShell version {ps_version} available"
                    })
                else:
                    health_status["checks"].append({
                        "name": "powershell_interpreter",
                        "status": "unhealthy",
                        "details": "PowerShell not available or not executable"
                    })
            
            except subprocess.TimeoutExpired:
                health_status["checks"].append({
                    "name": "powershell_interpreter",
                    "status": "unhealthy", 
                    "details": "PowerShell command timed out"
                })
            except FileNotFoundError:
                health_status["checks"].append({
                    "name": "powershell_interpreter",
                    "status": "unhealthy",
                    "details": "PowerShell executable not found"
                })
            
            # Check PowerShell configuration file
            config_file = Path("config/powershell_config.ps1")
            if config_file.exists():
                health_status["checks"].append({
                    "name": "powershell_config",
                    "status": "healthy",
                    "details": "PowerShell configuration file exists"
                })
            else:
                health_status["checks"].append({
                    "name": "powershell_config",
                    "status": "warning",
                    "details": "PowerShell configuration file not found"
                })
            
            # Check execution policy (Windows-specific)
            try:
                result = subprocess.run(
                    ["powershell", "-Command", "Get-ExecutionPolicy"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    execution_policy = result.stdout.strip()
                    if execution_policy in ["RemoteSigned", "Unrestricted", "Bypass"]:
                        health_status["checks"].append({
                            "name": "execution_policy",
                            "status": "healthy",
                            "details": f"Execution policy: {execution_policy}"
                        })
                    else:
                        health_status["checks"].append({
                            "name": "execution_policy",
                            "status": "warning",
                            "details": f"Restrictive execution policy: {execution_policy}"
                        })
            
            except Exception:
                health_status["checks"].append({
                    "name": "execution_policy",
                    "status": "warning",
                    "details": "Could not check PowerShell execution policy"
                })
            
            # Overall PowerShell health
            unhealthy_checks = [c for c in health_status["checks"] if c["status"] == "unhealthy"]
            warning_checks = [c for c in health_status["checks"] if c["status"] == "warning"]
            
            if unhealthy_checks:
                health_status["status"] = "unhealthy"
            elif warning_checks:
                health_status["status"] = "degraded"
            else:
                health_status["status"] = "healthy"
            
            logger.info("PowerShell health check completed")
            
        except Exception as exc:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(exc)
            logger.error(f"PowerShell health check failed: {exc}")
        
        return health_status
    
    def check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity for cross-system communication.
        
        Returns:
            Dictionary with network connectivity status
        """
        health_status = {
            "system": "network",
            "status": "unknown",
            "checks": [],
            "timestamp": time.time()
        }
        
        try:
            # Check localhost connectivity
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(('localhost', 80))
                sock.close()
                
                if result == 0:
                    health_status["checks"].append({
                        "name": "localhost_connectivity",
                        "status": "healthy",
                        "details": "Localhost connectivity available"
                    })
                else:
                    health_status["checks"].append({
                        "name": "localhost_connectivity",
                        "status": "warning",
                        "details": "Localhost port 80 not reachable"
                    })
            
            except Exception:
                health_status["checks"].append({
                    "name": "localhost_connectivity",
                    "status": "warning",
                    "details": "Could not test localhost connectivity"
                })
            
            # Check API port availability (if configured)
            if self.config_manager:
                config = self.config_manager.load_unified_config()
                api_port = config.get("api", {}).get("port", 8000)
                
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex(('localhost', api_port))
                    sock.close()
                    
                    if result == 0:
                        health_status["checks"].append({
                            "name": f"api_port_{api_port}",
                            "status": "healthy",
                            "details": f"API port {api_port} is reachable"
                        })
                    else:
                        health_status["checks"].append({
                            "name": f"api_port_{api_port}",
                            "status": "warning", 
                            "details": f"API port {api_port} is not reachable"
                        })
                
                except Exception:
                    health_status["checks"].append({
                        "name": f"api_port_{api_port}",
                        "status": "warning",
                        "details": f"Could not test API port {api_port}"
                    })
            
            # Overall network health
            unhealthy_checks = [c for c in health_status["checks"] if c["status"] == "unhealthy"]
            warning_checks = [c for c in health_status["checks"] if c["status"] == "warning"]
            
            if unhealthy_checks:
                health_status["status"] = "unhealthy"
            elif warning_checks:
                health_status["status"] = "degraded"
            else:
                health_status["status"] = "healthy"
            
            logger.info("Network connectivity check completed")
            
        except Exception as exc:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(exc)
            logger.error(f"Network connectivity check failed: {exc}")
        
        return health_status
    
    def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check across all systems.
        
        Returns:
            Dictionary with comprehensive health status
        """
        logger.info("Starting comprehensive cross-system health check")
        
        health_results = {
            "timestamp": time.time(),
            "overall_status": "unknown",
            "systems": {}
        }
        
        # Check all systems
        system_checks = [
            ("python", self.check_python_health),
            ("mql4", self.check_mql4_health), 
            ("powershell", self.check_powershell_health),
            ("network", self.check_network_connectivity)
        ]
        
        for system_name, check_func in system_checks:
            try:
                health_results["systems"][system_name] = check_func()
            except Exception as exc:
                health_results["systems"][system_name] = {
                    "system": system_name,
                    "status": "unhealthy",
                    "error": str(exc),
                    "timestamp": time.time()
                }
                logger.error(f"{system_name} health check failed: {exc}")
        
        # Calculate overall status
        system_statuses = [s["status"] for s in health_results["systems"].values()]
        
        if "unhealthy" in system_statuses:
            health_results["overall_status"] = "unhealthy"
        elif "degraded" in system_statuses:
            health_results["overall_status"] = "degraded"
        elif "warning" in system_statuses:
            health_results["overall_status"] = "warning"
        else:
            health_results["overall_status"] = "healthy"
        
        # Store results
        self.health_results = health_results
        
        logger.info(f"Comprehensive health check completed. Overall status: {health_results['overall_status']}")
        
        return health_results
    
    def get_health_summary(self) -> str:
        """Get a formatted summary of the latest health check results.
        
        Returns:
            Formatted health summary string
        """
        if not self.health_results:
            return "No health check results available. Run run_comprehensive_health_check() first."
        
        summary = ["=== Cross-System Health Summary ==="]
        summary.append(f"Overall Status: {self.health_results['overall_status'].upper()}")
        summary.append(f"Check Time: {time.ctime(self.health_results['timestamp'])}")
        summary.append("")
        
        for system_name, system_health in self.health_results["systems"].items():
            summary.append(f"{system_name.upper()} System: {system_health['status'].upper()}")
            
            if "checks" in system_health:
                for check in system_health["checks"]:
                    status_symbol = {"healthy": "✓", "warning": "⚠", "unhealthy": "✗"}.get(check["status"], "?")
                    summary.append(f"  {status_symbol} {check['name']}: {check['details']}")
            
            if "error" in system_health:
                summary.append(f"  ✗ Error: {system_health['error']}")
            
            summary.append("")
        
        return "\n".join(summary)