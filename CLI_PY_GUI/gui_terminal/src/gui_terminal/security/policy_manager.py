"""
Security Policy Manager
Enterprise-grade security policy enforcement and compliance monitoring
"""

import os
import re
import time
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Security threat level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViolationType(Enum):
    """Security violation types"""
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


class SecurityPolicyManager:
    """
    Centralized security policy enforcement and compliance monitoring
    """

    def __init__(self, policy_path: Optional[str] = None):
        self.policy_path = policy_path or self._get_default_policy_path()
        self.violations_log = []
        self.compliance_rules = {}
        self.process_limits = ProcessLimits()

        # Command filtering
        self.command_mode = "whitelist"  # whitelist, blacklist, or disabled
        self.allowed_commands = set()
        self.blocked_commands = set()
        self.dangerous_patterns = []

        # Load policies
        self.load_policies()

    def _get_default_policy_path(self) -> str:
        """Get default security policy file path"""
        config_dir = Path.home() / ".gui_terminal"
        config_dir.mkdir(exist_ok=True)
        policy_file = config_dir / "security_policies.yaml"

        if not policy_file.exists():
            self._create_default_policy(policy_file)

        return str(policy_file)

    def _create_default_policy(self, policy_file: Path):
        """Create default security policy file"""
        default_policy = {
            "command_filtering": {
                "mode": "whitelist",
                "allowed_commands": [
                    "ls", "dir", "pwd", "cd", "echo", "cat", "type", "grep", "find",
                    "python", "pip", "git", "node", "npm", "docker", "kubectl",
                    "cli-multi-rapid"
                ],
                "blocked_commands": [
                    "rm", "del", "format", "fdisk", "dd", "mkfs", "sudo", "su",
                    "chmod 777", "chown", "passwd"
                ]
            },
            "resource_limits": {
                "enforce": True,
                "max_processes": 10,
                "max_memory_mb": 512,
                "max_cpu_percent": 50,
                "max_execution_time": 300,
                "max_file_size_mb": 100
            },
            "audit_logging": {
                "enabled": True,
                "log_commands": True,
                "log_file_access": True,
                "log_network_access": True,
                "integrity_check": True
            },
            "network_access": {
                "allowed_domains": [
                    "github.com", "pypi.org", "npmjs.com"
                ],
                "blocked_domains": [],
                "allow_localhost": True
            },
            "file_system": {
                "restricted_paths": [
                    "/etc/passwd", "/etc/shadow", "C:\\Windows\\System32"
                ],
                "allowed_paths": [
                    "/home", "/tmp", "C:\\Users"
                ]
            },
            "compliance_rules": {
                "prevent_privilege_escalation": {
                    "enabled": True,
                    "patterns": ["sudo", "su", "runas"],
                    "severity": "critical",
                    "action": "block"
                },
                "prevent_destructive_commands": {
                    "enabled": True,
                    "patterns": ["rm -rf", "del /f /s /q", "format", "fdisk"],
                    "severity": "high",
                    "action": "block"
                }
            }
        }

        try:
            with open(policy_file, 'w') as f:
                yaml.dump(default_policy, f, default_flow_style=False, indent=2)
            logger.info(f"Created default security policy: {policy_file}")
        except Exception as e:
            logger.error(f"Failed to create default policy: {e}")

    def load_policies(self):
        """Load security policies from file"""
        try:
            if not Path(self.policy_path).exists():
                logger.warning(f"Policy file not found: {self.policy_path}")
                return

            with open(self.policy_path, 'r') as f:
                policies = yaml.safe_load(f)

            # Load command filtering
            cmd_filter = policies.get('command_filtering', {})
            self.command_mode = cmd_filter.get('mode', 'whitelist')
            self.allowed_commands = set(cmd_filter.get('allowed_commands', []))
            self.blocked_commands = set(cmd_filter.get('blocked_commands', []))

            # Load resource limits
            limits = policies.get('resource_limits', {})
            self.process_limits = ProcessLimits(
                max_memory_mb=limits.get('max_memory_mb', 512),
                max_cpu_percent=limits.get('max_cpu_percent', 50),
                max_execution_time=limits.get('max_execution_time', 300),
                max_processes=limits.get('max_processes', 10)
            )

            # Load compliance rules
            rules = policies.get('compliance_rules', {})
            for rule_id, rule_data in rules.items():
                self.compliance_rules[rule_id] = ComplianceRule(
                    rule_id=rule_id,
                    name=rule_data.get('name', rule_id),
                    description=rule_data.get('description', ''),
                    enabled=rule_data.get('enabled', True),
                    violation_patterns=rule_data.get('patterns', []),
                    severity=ThreatLevel(rule_data.get('severity', 'medium')),
                    action=rule_data.get('action', 'block')
                )

            # Setup dangerous patterns
            self.dangerous_patterns = [
                r'[;&|`$()]',  # Shell metacharacters
                r'\.\./.*',    # Directory traversal
                r'--?password', # Password arguments
                r'sudo|su|runas',    # Privilege escalation
                r'rm\s+-rf',   # Dangerous rm
                r'del\s+/[fqsr]',  # Dangerous del
            ]

            logger.info(f"Security policies loaded from: {self.policy_path}")

        except Exception as e:
            logger.error(f"Failed to load security policies: {e}")

    def validate_command(self, command: str, args: List[str], cwd: str,
                        user_id: str = "default", session_id: str = "default") -> Tuple[bool, List[str]]:
        """Validate command against security policies"""
        violations = []
        full_command = f"{command} {' '.join(args)}".strip()

        # Command whitelist/blacklist validation
        if self.command_mode == "whitelist":
            if command not in self.allowed_commands:
                violation = SecurityViolation(
                    violation_type=ViolationType.COMMAND_BLOCKED,
                    threat_level=ThreatLevel.MEDIUM,
                    command=full_command,
                    description=f"Command '{command}' not in allowed list",
                    user_id=user_id,
                    session_id=session_id
                )
                self.violations_log.append(violation)
                violations.append(violation.description)

        if command in self.blocked_commands:
            violation = SecurityViolation(
                violation_type=ViolationType.COMMAND_BLOCKED,
                threat_level=ThreatLevel.HIGH,
                command=full_command,
                description=f"Command '{command}' is blocked",
                user_id=user_id,
                session_id=session_id
            )
            self.violations_log.append(violation)
            violations.append(violation.description)

        # Pattern validation
        for pattern in self.dangerous_patterns:
            if re.search(pattern, full_command, re.IGNORECASE):
                violation = SecurityViolation(
                    violation_type=ViolationType.PATTERN_DETECTED,
                    threat_level=ThreatLevel.HIGH,
                    command=full_command,
                    description=f"Dangerous pattern detected: {pattern}",
                    user_id=user_id,
                    session_id=session_id
                )
                self.violations_log.append(violation)
                violations.append(violation.description)

        # Compliance rules validation
        for rule_id, rule in self.compliance_rules.items():
            if rule.enabled:
                for pattern in rule.violation_patterns:
                    if re.search(pattern, full_command, re.IGNORECASE):
                        violation = SecurityViolation(
                            violation_type=ViolationType.SUSPICIOUS_ACTIVITY,
                            threat_level=rule.severity,
                            command=full_command,
                            description=f"Compliance violation ({rule_id}): {rule.description}",
                            user_id=user_id,
                            session_id=session_id,
                            blocked=rule.action == "block"
                        )
                        self.violations_log.append(violation)
                        if rule.action == "block":
                            violations.append(violation.description)

        # Path validation
        try:
            if not os.path.exists(cwd):
                violation = SecurityViolation(
                    violation_type=ViolationType.PATH_TRAVERSAL,
                    threat_level=ThreatLevel.MEDIUM,
                    command=full_command,
                    description=f"Working directory does not exist: {cwd}",
                    user_id=user_id,
                    session_id=session_id
                )
                self.violations_log.append(violation)
                violations.append(violation.description)
        except Exception as e:
            logger.warning(f"Path validation error: {e}")

        # Log audit event
        self._log_audit_event(full_command, cwd, user_id, session_id, violations)

        return len(violations) == 0, violations

    def validate_resource_usage(self, memory_mb: float, cpu_percent: float,
                              execution_time: float) -> Tuple[bool, List[str]]:
        """Validate resource usage against limits"""
        violations = []

        if memory_mb > self.process_limits.max_memory_mb:
            violations.append(f"Memory usage ({memory_mb:.1f}MB) exceeds limit ({self.process_limits.max_memory_mb}MB)")

        if cpu_percent > self.process_limits.max_cpu_percent:
            violations.append(f"CPU usage ({cpu_percent:.1f}%) exceeds limit ({self.process_limits.max_cpu_percent}%)")

        if execution_time > self.process_limits.max_execution_time:
            violations.append(f"Execution time ({execution_time:.1f}s) exceeds limit ({self.process_limits.max_execution_time}s)")

        return len(violations) == 0, violations

    def sanitize_command(self, command: str, args: List[str]) -> Tuple[str, List[str]]:
        """Sanitize command arguments"""
        # Remove dangerous characters from command
        sanitized_command = re.sub(r'[;\|\&`$()]', '', command)

        # Remove dangerous characters from arguments
        sanitized_args = []
        for arg in args:
            # Remove null bytes and control characters
            sanitized_arg = re.sub(r'[\x00-\x1f\x7f]', '', arg)
            # Remove dangerous shell metacharacters
            sanitized_arg = re.sub(r'[;\|\&`$()]', '', sanitized_arg)
            sanitized_args.append(sanitized_arg)

        return sanitized_command, sanitized_args

    def is_path_allowed(self, path: str) -> bool:
        """Check if path access is allowed"""
        try:
            abs_path = os.path.abspath(path)

            # Check against restricted paths
            # This would be loaded from policy file
            restricted_paths = [
                "/etc/passwd", "/etc/shadow",
                "C:\\Windows\\System32", "C:\\Windows\\SysWOW64"
            ]

            for restricted in restricted_paths:
                if abs_path.startswith(restricted):
                    return False

            return True
        except Exception:
            return False

    def get_violation_summary(self) -> Dict[str, Any]:
        """Get summary of security violations"""
        if not self.violations_log:
            return {"total": 0, "by_type": {}, "recent": []}

        # Count violations by type
        by_type = {}
        for violation in self.violations_log:
            vtype = violation.violation_type.value
            by_type[vtype] = by_type.get(vtype, 0) + 1

        # Get recent violations (last 10)
        recent = []
        for violation in self.violations_log[-10:]:
            recent.append({
                "type": violation.violation_type.value,
                "command": violation.command,
                "description": violation.description,
                "timestamp": violation.timestamp,
                "blocked": violation.blocked
            })

        return {
            "total": len(self.violations_log),
            "by_type": by_type,
            "recent": recent
        }

    def _log_audit_event(self, command: str, cwd: str, user_id: str,
                        session_id: str, violations: List[str]):
        """Log audit event for compliance"""
        audit_entry = {
            "timestamp": time.time(),
            "event_type": "command_validation",
            "user_id": user_id,
            "session_id": session_id,
            "command": command,
            "working_directory": cwd,
            "violations_count": len(violations),
            "violations": violations,
            "allowed": len(violations) == 0
        }

        # Log to audit logger (would be handled by AuditLogger class)
        logger.info(f"Audit: {audit_entry}")

    def update_policy(self, section: str, key: str, value: Any):
        """Update security policy setting"""
        try:
            if section == "command_filtering":
                if key == "mode":
                    self.command_mode = value
                elif key == "allowed_commands":
                    self.allowed_commands = set(value)
                elif key == "blocked_commands":
                    self.blocked_commands = set(value)

            elif section == "resource_limits":
                if hasattr(self.process_limits, key):
                    setattr(self.process_limits, key, value)

            logger.info(f"Updated security policy: {section}.{key} = {value}")

        except Exception as e:
            logger.error(f"Failed to update policy: {e}")

    def reload_policies(self):
        """Reload policies from file"""
        try:
            self.load_policies()
            logger.info("Security policies reloaded")
        except Exception as e:
            logger.error(f"Failed to reload policies: {e}")

    def export_violations(self, export_path: str):
        """Export violations log for compliance reporting"""
        try:
            violations_data = []
            for violation in self.violations_log:
                violations_data.append({
                    "violation_type": violation.violation_type.value,
                    "threat_level": violation.threat_level.value,
                    "command": violation.command,
                    "description": violation.description,
                    "timestamp": violation.timestamp,
                    "user_id": violation.user_id,
                    "session_id": violation.session_id,
                    "blocked": violation.blocked
                })

            with open(export_path, 'w') as f:
                yaml.dump(violations_data, f, default_flow_style=False, indent=2)

            logger.info(f"Violations exported to: {export_path}")

        except Exception as e:
            logger.error(f"Failed to export violations: {e}")

    def get_policy_status(self) -> Dict[str, Any]:
        """Get current policy status for monitoring"""
        return {
            "policy_file": self.policy_path,
            "command_mode": self.command_mode,
            "allowed_commands_count": len(self.allowed_commands),
            "blocked_commands_count": len(self.blocked_commands),
            "compliance_rules_count": len(self.compliance_rules),
            "violations_count": len(self.violations_log),
            "resource_limits": {
                "max_memory_mb": self.process_limits.max_memory_mb,
                "max_cpu_percent": self.process_limits.max_cpu_percent,
                "max_execution_time": self.process_limits.max_execution_time
            }
        }