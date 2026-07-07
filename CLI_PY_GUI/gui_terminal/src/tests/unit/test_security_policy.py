"""
Unit tests for Security Policy Manager
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from gui_terminal.security.policy_manager import (
    SecurityPolicyManager,
    SecurityViolation,
    ViolationType,
    ThreatLevel
)


class TestSecurityPolicyManager:
    """Test Security Policy Manager functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.temp_policy_file = None

    def teardown_method(self):
        """Cleanup test fixtures"""
        if self.temp_policy_file and Path(self.temp_policy_file).exists():
            Path(self.temp_policy_file).unlink()

    def create_test_policy_file(self, policy_data: dict) -> str:
        """Create temporary policy file"""
        import yaml

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(policy_data, f)
            self.temp_policy_file = f.name
            return f.name

    def test_initialization_with_policy_file(self):
        """Test initialization with custom policy file"""
        policy_data = {
            "command_filtering": {
                "mode": "whitelist",
                "allowed_commands": ["ls", "pwd"],
                "blocked_commands": ["rm", "del"]
            }
        }

        policy_file = self.create_test_policy_file(policy_data)
        manager = SecurityPolicyManager(policy_path=policy_file)

        assert manager.command_mode == "whitelist"
        assert "ls" in manager.allowed_commands
        assert "pwd" in manager.allowed_commands
        assert "rm" in manager.blocked_commands

    def test_validate_command_whitelist_allowed(self):
        """Test command validation with whitelist - allowed command"""
        policy_data = {
            "command_filtering": {
                "mode": "whitelist",
                "allowed_commands": ["ls", "pwd"],
                "blocked_commands": []
            }
        }

        policy_file = self.create_test_policy_file(policy_data)
        manager = SecurityPolicyManager(policy_path=policy_file)

        is_valid, violations = manager.validate_command("ls", ["-la"], "/tmp")
        assert is_valid is True
        assert len(violations) == 0

    def test_validate_command_whitelist_blocked(self):
        """Test command validation with whitelist - blocked command"""
        policy_data = {
            "command_filtering": {
                "mode": "whitelist",
                "allowed_commands": ["ls", "pwd"],
                "blocked_commands": []
            }
        }

        policy_file = self.create_test_policy_file(policy_data)
        manager = SecurityPolicyManager(policy_path=policy_file)

        is_valid, violations = manager.validate_command("rm", ["-rf", "/"], "/tmp")
        assert is_valid is False
        assert len(violations) > 0
        assert "not in allowed list" in violations[0]

    def test_validate_command_blacklist(self):
        """Test command validation with blacklist"""
        policy_data = {
            "command_filtering": {
                "mode": "blacklist",
                "allowed_commands": [],
                "blocked_commands": ["rm", "del"]
            }
        }

        policy_file = self.create_test_policy_file(policy_data)
        manager = SecurityPolicyManager(policy_path=policy_file)

        is_valid, violations = manager.validate_command("rm", ["-rf"], "/tmp")
        assert is_valid is False
        assert len(violations) > 0
        assert "is blocked" in violations[0]

    def test_validate_command_dangerous_patterns(self):
        """Test command validation with dangerous patterns"""
        manager = SecurityPolicyManager()

        # Test shell metacharacters
        is_valid, violations = manager.validate_command("ls", ["; rm -rf /"], "/tmp")
        assert is_valid is False
        assert len(violations) > 0

        # Test directory traversal
        is_valid, violations = manager.validate_command("cat", ["../../../etc/passwd"], "/tmp")
        assert is_valid is False
        assert len(violations) > 0

    def test_validate_command_path_validation(self):
        """Test command validation with path validation"""
        manager = SecurityPolicyManager()

        # Non-existent directory
        is_valid, violations = manager.validate_command("ls", [], "/nonexistent/path")
        assert is_valid is False
        assert any("does not exist" in v for v in violations)

    def test_sanitize_command(self):
        """Test command sanitization"""
        manager = SecurityPolicyManager()

        command, args = manager.sanitize_command("ls", ["; rm -rf /", "test\x00file"])

        assert command == "ls"  # Command should be clean
        assert "rm -rf /" in args[0]  # Semicolon removed but content preserved
        assert "testfile" == args[1]  # Null byte removed

    def test_compliance_rules(self):
        """Test compliance rules validation"""
        policy_data = {
            "compliance_rules": {
                "prevent_privilege_escalation": {
                    "enabled": True,
                    "patterns": ["sudo", "su"],
                    "severity": "critical",
                    "action": "block"
                }
            }
        }

        policy_file = self.create_test_policy_file(policy_data)
        manager = SecurityPolicyManager(policy_path=policy_file)

        is_valid, violations = manager.validate_command("sudo", ["ls"], "/tmp")
        assert is_valid is False
        assert len(violations) > 0
        assert "prevent_privilege_escalation" in violations[0]

    def test_resource_limits_validation(self):
        """Test resource limits validation"""
        manager = SecurityPolicyManager()

        # Test memory limit
        is_valid, violations = manager.validate_resource_usage(
            memory_mb=1000,  # Exceeds default 512MB
            cpu_percent=25,
            execution_time=30
        )
        assert is_valid is False
        assert any("Memory usage" in v for v in violations)

        # Test CPU limit
        is_valid, violations = manager.validate_resource_usage(
            memory_mb=100,
            cpu_percent=75,  # Exceeds default 50%
            execution_time=30
        )
        assert is_valid is False
        assert any("CPU usage" in v for v in violations)

        # Test execution time limit
        is_valid, violations = manager.validate_resource_usage(
            memory_mb=100,
            cpu_percent=25,
            execution_time=400  # Exceeds default 300s
        )
        assert is_valid is False
        assert any("Execution time" in v for v in violations)

    def test_violation_logging(self):
        """Test security violation logging"""
        manager = SecurityPolicyManager()

        # Trigger a violation
        manager.validate_command("rm", ["-rf", "/"], "/tmp", "test_user", "test_session")

        # Check violations were logged
        assert len(manager.violations_log) > 0
        violation = manager.violations_log[0]
        assert isinstance(violation, SecurityViolation)
        assert violation.user_id == "test_user"
        assert violation.session_id == "test_session"
        assert "rm -rf /" in violation.command

    def test_get_violation_summary(self):
        """Test violation summary generation"""
        manager = SecurityPolicyManager()

        # Add some violations
        manager.validate_command("rm", ["-rf"], "/tmp")
        manager.validate_command("sudo", ["ls"], "/tmp")

        summary = manager.get_violation_summary()
        assert summary["total"] >= 2
        assert isinstance(summary["by_type"], dict)
        assert isinstance(summary["recent"], list)

    def test_policy_update(self):
        """Test policy updates"""
        manager = SecurityPolicyManager()

        # Update command mode
        manager.update_policy("command_filtering", "mode", "blacklist")
        assert manager.command_mode == "blacklist"

        # Update resource limits
        manager.update_policy("resource_limits", "max_memory_mb", 1024)
        assert manager.process_limits.max_memory_mb == 1024

    def test_get_policy_status(self):
        """Test policy status retrieval"""
        manager = SecurityPolicyManager()

        status = manager.get_policy_status()
        assert isinstance(status, dict)
        assert "policy_file" in status
        assert "command_mode" in status
        assert "allowed_commands_count" in status
        assert "violations_count" in status


class TestSecurityViolation:
    """Test SecurityViolation data class"""

    def test_creation(self):
        """Test SecurityViolation creation"""
        violation = SecurityViolation(
            violation_type=ViolationType.COMMAND_BLOCKED,
            threat_level=ThreatLevel.HIGH,
            command="rm -rf /",
            description="Dangerous command blocked"
        )

        assert violation.violation_type == ViolationType.COMMAND_BLOCKED
        assert violation.threat_level == ThreatLevel.HIGH
        assert violation.command == "rm -rf /"
        assert violation.description == "Dangerous command blocked"
        assert violation.blocked is True

    def test_defaults(self):
        """Test SecurityViolation default values"""
        violation = SecurityViolation(
            violation_type=ViolationType.SUSPICIOUS_ACTIVITY,
            threat_level=ThreatLevel.MEDIUM,
            command="test",
            description="test"
        )

        assert violation.user_id == "unknown"
        assert violation.session_id == "unknown"
        assert violation.remediation is None
        assert violation.blocked is True
        assert violation.timestamp > 0