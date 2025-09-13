"""
Integration tests for the self-healing system with CLI Multi-Rapid platform.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cli_multi_rapid.self_healing_manager import (
    SelfHealingManager, 
    ErrorCode, 
    SelfHealingResult,
    get_self_healing_manager
)


class TestSelfHealingIntegration:
    """Test self-healing system integration with the platform"""
    
    def test_self_healing_manager_initialization(self):
        """Test that self-healing manager can be initialized"""
        manager = SelfHealingManager()
        assert manager is not None
        assert hasattr(manager, 'config')
        assert hasattr(manager, 'fixers')
        
    def test_config_loading(self):
        """Test configuration loading from YAML"""
        manager = SelfHealingManager()
        config = manager.config
        
        assert 'self_healing' in config
        sh_config = config['self_healing']
        
        # Verify required keys exist
        required_keys = ['max_attempts', 'base_backoff_seconds', 'fixers']
        for key in required_keys:
            assert key in sh_config, f"Missing required key: {key}"
            
    def test_error_code_enum(self):
        """Test that all error codes are properly defined"""
        # Test a few key error codes
        assert ErrorCode.ERR_DISK_SPACE.value == "ERR_DISK_SPACE"
        assert ErrorCode.ERR_FILE_LOCKED.value == "ERR_FILE_LOCKED"
        assert ErrorCode.ERR_PORT_BIND.value == "ERR_PORT_BIND"
        
        # Test that all error codes follow naming convention
        for error_code in ErrorCode:
            assert error_code.value.startswith("ERR_")
            assert error_code.value.replace("ERR_", "").replace("_", "").isalnum()
            
    def test_fixer_registration(self):
        """Test that fixers are properly registered"""
        manager = SelfHealingManager()
        
        # Check that some fixers are registered
        assert len(manager.fixers) > 0
        
        # Check specific error codes have fixers
        expected_fixers = [
            ErrorCode.ERR_DISK_SPACE,
            ErrorCode.ERR_PATH_DENIED,
            ErrorCode.ERR_FILE_LOCKED,
        ]
        
        for error_code in expected_fixers:
            assert error_code in manager.fixers
            assert len(manager.fixers[error_code]) > 0
            
    def test_healing_attempt_with_security_hard_fail(self):
        """Test that security hard fail errors are not healed"""
        manager = SelfHealingManager()
        
        # Test security hard fail
        result = manager.attempt_healing(ErrorCode.ERR_SIG_INVALID)
        
        assert result.success is False
        assert result.attempts == 0
        assert "Security hard fail" in result.message
        assert result.applied_fixes == []
        
    def test_healing_attempt_with_no_fixers(self):
        """Test healing attempt for error code with no registered fixers"""
        manager = SelfHealingManager()
        
        # Clear fixers for test error code to simulate no fixers available
        test_error = ErrorCode.ERR_METRICS_EXPORT
        original_fixers = manager.fixers.get(test_error, [])
        manager.fixers[test_error] = []
        
        try:
            result = manager.attempt_healing(test_error)
            
            assert result.success is False
            assert result.attempts == 0
            assert "No fixers available" in result.message
            assert result.applied_fixes == []
        finally:
            # Restore original fixers
            if original_fixers:
                manager.fixers[test_error] = original_fixers
            elif test_error in manager.fixers:
                del manager.fixers[test_error]
                
    @patch('time.sleep')  # Speed up test by mocking sleep
    def test_healing_attempt_with_retry_logic(self, mock_sleep):
        """Test healing attempt with retry and exponential backoff"""
        manager = SelfHealingManager()
        
        # Mock a fixer that always fails
        def failing_fixer(context):
            return False
            
        # Register failing fixer for test
        test_error = ErrorCode.ERR_RESOURCE_STARVE
        manager.fixers[test_error] = [failing_fixer]
        
        result = manager.attempt_healing(test_error)
        
        # Should fail after max attempts
        max_attempts = manager.config.get('self_healing', {}).get('max_attempts', 3)
        assert result.success is False
        assert result.attempts == max_attempts
        assert len(result.applied_fixes) == max_attempts  # One failed attempt per retry
        
        # Verify sleep was called for backoff (except on last attempt)
        assert mock_sleep.call_count == max_attempts - 1
        
    def test_custom_fixer_registration(self):
        """Test registering custom fixers"""
        manager = SelfHealingManager()
        
        def custom_fixer(context):
            return True
            
        test_error = ErrorCode.ERR_CONFIG_REGRESSION
        original_count = len(manager.fixers.get(test_error, []))
        
        manager.register_custom_fixer(test_error, custom_fixer)
        
        new_count = len(manager.fixers.get(test_error, []))
        assert new_count == original_count + 1
        assert custom_fixer in manager.fixers[test_error]
        
    def test_global_manager_instance(self):
        """Test that global manager instance works correctly"""
        manager1 = get_self_healing_manager()
        manager2 = get_self_healing_manager()
        
        # Should return the same instance
        assert manager1 is manager2
        
    def test_healing_result_structure(self):
        """Test that SelfHealingResult has correct structure"""
        result = SelfHealingResult(
            success=True,
            error_code=ErrorCode.ERR_DISK_SPACE,
            applied_fixes=['fix1', 'fix2'],
            attempts=2,
            total_time=1.5,
            message="Test message"
        )
        
        assert result.success is True
        assert result.error_code == ErrorCode.ERR_DISK_SPACE
        assert result.applied_fixes == ['fix1', 'fix2']
        assert result.attempts == 2
        assert result.total_time == 1.5
        assert result.message == "Test message"
        
    def test_path_creation_fixer(self):
        """Test the path creation fixer"""
        import tempfile
        import shutil
        
        manager = SelfHealingManager()
        
        # Create a temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        try:
            test_path = os.path.join(temp_dir, 'nonexistent', 'nested', 'path', 'file.txt')
            context = {'path': test_path}
            
            # Test the path creation fixer
            result = manager._fix_create_missing_path(context)
            
            # Check if parent directories were created
            parent_dir = Path(test_path).parent
            assert parent_dir.exists()
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.integration
class TestSelfHealingCLIIntegration:
    """Test self-healing integration with CLI commands"""
    
    def test_cli_self_healing_import(self):
        """Test that CLI can import self-healing components"""
        try:
            from cli_multi_rapid.cli import main, parse_args
            from cli_multi_rapid.self_healing_manager import get_self_healing_manager
            
            # Should not raise any import errors
            assert True
        except ImportError as e:
            pytest.fail(f"CLI import failed: {e}")
            
    def test_cli_self_healing_status_command(self):
        """Test self-healing status command parsing"""
        from cli_multi_rapid.cli import parse_args
        
        args = parse_args(['self-healing', 'status'])
        
        assert args.command == 'self-healing'
        assert args.healing_cmd == 'status'
        
    def test_cli_self_healing_test_command(self):
        """Test self-healing test command parsing"""
        from cli_multi_rapid.cli import parse_args
        
        args = parse_args(['self-healing', 'test', 'ERR_DISK_SPACE'])
        
        assert args.command == 'self-healing'
        assert args.healing_cmd == 'test'
        assert args.error_code == 'ERR_DISK_SPACE'
        
    def test_cli_self_healing_config_command(self):
        """Test self-healing config command parsing"""
        from cli_multi_rapid.cli import parse_args
        
        args = parse_args(['self-healing', 'config'])
        
        assert args.command == 'self-healing'
        assert args.healing_cmd == 'config'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])