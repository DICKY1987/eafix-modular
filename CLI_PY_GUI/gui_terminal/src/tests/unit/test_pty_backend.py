"""
Unit tests for PTY Backend
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from gui_terminal.core.pty_backend import PTYBackend, PTYWorker, CommandResult, CommandStatus


class TestPTYBackend:
    """Test PTY backend functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.pty_backend = PTYBackend()

    def test_initialization(self):
        """Test PTY backend initialization"""
        assert self.pty_backend.current_worker is None
        assert self.pty_backend.default_shell is not None
        assert isinstance(self.pty_backend.default_env, dict)

    def test_get_default_shell(self):
        """Test default shell detection"""
        shell = self.pty_backend._get_default_shell()
        assert shell is not None
        assert isinstance(shell, str)
        assert len(shell) > 0

    @patch('gui_terminal.core.pty_backend.PTYWorker')
    def test_start_session(self, mock_worker_class):
        """Test starting a PTY session"""
        mock_worker = Mock()
        mock_worker_class.return_value = mock_worker

        # Start session
        self.pty_backend.start_session("bash", ["-l"], "/home/user", {"TEST": "value"})

        # Verify worker created and started
        mock_worker_class.assert_called_once()
        mock_worker.start.assert_called_once()
        assert self.pty_backend.current_worker == mock_worker

    def test_start_session_defaults(self):
        """Test starting session with default parameters"""
        with patch('gui_terminal.core.pty_backend.PTYWorker') as mock_worker_class:
            mock_worker = Mock()
            mock_worker_class.return_value = mock_worker

            self.pty_backend.start_session()

            mock_worker_class.assert_called_once()
            args = mock_worker_class.call_args[0]
            assert args[0] == self.pty_backend.default_shell  # command
            assert args[1] == []  # args
            assert args[3] == self.pty_backend.default_env  # env

    def test_send_input_no_worker(self):
        """Test sending input without active worker"""
        # Should not raise exception
        self.pty_backend.send_input("test\n")

    def test_send_input_with_worker(self):
        """Test sending input with active worker"""
        mock_worker = Mock()
        self.pty_backend.current_worker = mock_worker

        self.pty_backend.send_input("test\n")
        mock_worker.send_input.assert_called_once_with("test\n")

    def test_stop_session(self):
        """Test stopping session"""
        mock_worker = Mock()
        self.pty_backend.current_worker = mock_worker

        self.pty_backend.stop_session()

        mock_worker.stop.assert_called_once()
        mock_worker.wait.assert_called_once()
        assert self.pty_backend.current_worker is None

    def test_is_session_active(self):
        """Test session activity check"""
        # No active session
        assert not self.pty_backend.is_session_active()

        # Mock active session
        mock_worker = Mock()
        mock_worker.isRunning.return_value = True
        self.pty_backend.current_worker = mock_worker

        assert self.pty_backend.is_session_active()

        # Mock inactive session
        mock_worker.isRunning.return_value = False
        assert not self.pty_backend.is_session_active()


class TestCommandResult:
    """Test CommandResult data class"""

    def test_creation(self):
        """Test CommandResult creation"""
        result = CommandResult(
            exit_code=0,
            stdout="test output",
            stderr="",
            execution_time=1.5,
            status=CommandStatus.COMPLETED
        )

        assert result.exit_code == 0
        assert result.stdout == "test output"
        assert result.stderr == ""
        assert result.execution_time == 1.5
        assert result.status == CommandStatus.COMPLETED

    def test_defaults(self):
        """Test CommandResult default values"""
        result = CommandResult(exit_code=0)

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.execution_time == 0.0
        assert result.status == CommandStatus.COMPLETED
        assert result.process_id is None


@pytest.mark.integration
class TestPTYWorkerIntegration:
    """Integration tests for PTY worker"""

    @pytest.mark.skipif(
        not hasattr(pytest, 'qt_api'),
        reason="Requires Qt for signal testing"
    )
    def test_pty_worker_signals(self, qtbot):
        """Test PTY worker signal emissions"""
        worker = PTYWorker("echo", ["test"], "/tmp", {})

        # Connect signal spy
        with qtbot.waitSignal(worker.process_finished, timeout=5000) as blocker:
            worker.start()

        # Check result
        result = blocker.args[0]
        assert isinstance(result, CommandResult)
        assert result.exit_code == 0
        assert "test" in result.stdout

    @pytest.mark.expensive
    def test_pty_worker_long_running(self, qtbot):
        """Test PTY worker with long-running command"""
        worker = PTYWorker("sleep", ["1"], "/tmp", {})

        start_time = time.time()
        with qtbot.waitSignal(worker.process_finished, timeout=3000) as blocker:
            worker.start()

        end_time = time.time()
        result = blocker.args[0]

        assert isinstance(result, CommandResult)
        assert result.exit_code == 0
        assert end_time - start_time >= 1.0  # At least 1 second

    def test_pty_worker_error_command(self, qtbot):
        """Test PTY worker with error command"""
        worker = PTYWorker("nonexistent_command_12345", [], "/tmp", {})

        with qtbot.waitSignal(worker.error_occurred, timeout=2000) as blocker:
            worker.start()

        error_message = blocker.args[0]
        assert isinstance(error_message, str)
        assert len(error_message) > 0