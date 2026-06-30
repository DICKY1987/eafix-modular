"""
PTY Backend Implementation
Cross-platform PTY/ConPTY support for Windows and Unix systems
"""

import os
import sys
import time
import signal
import struct
import threading
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QThread
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal, QThread
    PYQT_VERSION = 5

# Windows-specific imports
if sys.platform == 'win32':
    try:
        import winpty
        WINDOWS_PTY_AVAILABLE = True
    except ImportError:
        WINDOWS_PTY_AVAILABLE = False
else:
    import pty
    import select

logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """Command execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass
class CommandResult:
    """Command execution result with metadata"""
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    execution_time: float = 0.0
    memory_used_mb: float = 0.0
    status: CommandStatus = CommandStatus.COMPLETED
    process_id: Optional[int] = None


class ANSIProcessor:
    """ANSI escape sequence processor for terminal output formatting"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset terminal state"""
        self.cursor_row = 0
        self.cursor_col = 0
        self.saved_cursor_row = 0
        self.saved_cursor_col = 0
        self.current_attrs = {}
        self.screen_buffer = []

    def process_ansi(self, text: str) -> str:
        """Process ANSI escape sequences and return formatted text"""
        # Handle carriage return (overwrite line)
        if '\r' in text and '\n' not in text:
            parts = text.split('\r')
            if len(parts) > 1:
                return parts[-1]  # Return last part after CR

        # For now, return text as-is (full ANSI processing can be added later)
        return text


class PTYWorker(QThread):
    """Worker thread for PTY process execution"""

    data_received = pyqtSignal(str)
    process_finished = pyqtSignal(CommandResult)
    error_occurred = pyqtSignal(str)

    def __init__(self, command: str, args: list, cwd: str, env: Dict[str, str]):
        super().__init__()
        self.command = command
        self.args = args
        self.cwd = cwd
        self.env = env
        self.should_stop = False
        self.process = None
        self.pty_fd = None
        self.process_id = None
        self.start_time = None
        self.ansi_processor = ANSIProcessor()

    def run(self):
        """Main thread execution"""
        try:
            self.start_time = time.time()

            if sys.platform == 'win32':
                self._run_windows()
            else:
                self._run_unix()

        except Exception as e:
            logger.exception(f"PTY worker error: {e}")
            self.error_occurred.emit(str(e))

    def _run_windows(self):
        """Run PTY process on Windows using winpty"""
        if not WINDOWS_PTY_AVAILABLE:
            self.error_occurred.emit("winpty not available. Install with: pip install pywinpty")
            return

        try:
            # Create winpty process
            self.process = winpty.PtyProcess.spawn(
                [self.command] + self.args,
                cwd=self.cwd,
                env=self.env
            )

            self.process_id = self.process.pid
            self._read_pty_output_windows()

        except Exception as e:
            logger.exception(f"Windows PTY error: {e}")
            self.error_occurred.emit(f"Failed to start Windows PTY: {e}")

    def _run_unix(self):
        """Run PTY process on Unix systems"""
        try:
            # Create PTY
            master_fd, slave_fd = pty.openpty()

            # Fork process
            pid = os.fork()

            if pid == 0:
                # Child process
                os.close(master_fd)
                os.setsid()
                os.dup2(slave_fd, 0)
                os.dup2(slave_fd, 1)
                os.dup2(slave_fd, 2)
                os.close(slave_fd)

                # Change directory and environment
                os.chdir(self.cwd)
                for key, value in self.env.items():
                    os.environ[key] = value

                # Execute command
                try:
                    os.execvp(self.command, [self.command] + self.args)
                except OSError:
                    sys.exit(127)

            else:
                # Parent process
                os.close(slave_fd)
                self.pty_fd = master_fd
                self.process_id = pid
                self._read_pty_output_unix()

        except Exception as e:
            logger.exception(f"Unix PTY error: {e}")
            self.error_occurred.emit(f"Failed to start Unix PTY: {e}")

    def _read_pty_output_unix(self):
        """Read PTY output on Unix systems"""
        stdout_data = []

        try:
            while not self.should_stop:
                # Check if data is available
                ready, _, _ = select.select([self.pty_fd], [], [], 0.1)

                if ready:
                    try:
                        data = os.read(self.pty_fd, 1024)
                        if not data:
                            break

                        text = data.decode('utf-8', errors='replace')
                        processed_text = self.ansi_processor.process_ansi(text)
                        stdout_data.append(processed_text)
                        self.data_received.emit(processed_text)

                    except OSError:
                        break

                # Check if process is still running
                try:
                    pid, exit_code = os.waitpid(self.process_id, os.WNOHANG)
                    if pid > 0:
                        break
                except OSError:
                    break

            # Get final exit code
            try:
                _, exit_code = os.waitpid(self.process_id, 0)
                exit_code = os.WEXITSTATUS(exit_code)
            except OSError:
                exit_code = -1

        except Exception as e:
            logger.exception(f"Error reading Unix PTY output: {e}")
            exit_code = -1

        finally:
            if self.pty_fd:
                os.close(self.pty_fd)

        # Calculate execution metrics
        execution_time = time.time() - self.start_time if self.start_time else 0

        result = CommandResult(
            exit_code=exit_code,
            stdout=''.join(stdout_data),
            execution_time=execution_time,
            status=CommandStatus.COMPLETED if exit_code == 0 else CommandStatus.FAILED,
            process_id=self.process_id
        )

        self.process_finished.emit(result)

    def _read_pty_output_windows(self):
        """Read PTY output on Windows systems"""
        stdout_data = []

        try:
            while not self.should_stop:
                # Check if process is alive
                if not self.process.isalive():
                    break

                try:
                    # Read available data
                    data = self.process.read(1024, blocking=False)
                    if data:
                        text = data.decode('utf-8', errors='replace')
                        processed_text = self.ansi_processor.process_ansi(text)
                        stdout_data.append(processed_text)
                        self.data_received.emit(processed_text)
                    else:
                        time.sleep(0.01)  # Small delay to prevent CPU spinning
                except:
                    break

            # Wait for process completion
            exit_code = self.process.wait()

        except Exception as e:
            logger.exception(f"Error reading Windows PTY output: {e}")
            exit_code = -1

        # Calculate execution metrics
        execution_time = time.time() - self.start_time if self.start_time else 0

        result = CommandResult(
            exit_code=exit_code,
            stdout=''.join(stdout_data),
            execution_time=execution_time,
            status=CommandStatus.COMPLETED if exit_code == 0 else CommandStatus.FAILED,
            process_id=self.process_id
        )

        self.process_finished.emit(result)

    def send_input(self, text: str):
        """Send input to the PTY"""
        try:
            if sys.platform == 'win32' and self.process:
                self.process.write(text.encode('utf-8'))
            elif self.pty_fd:
                os.write(self.pty_fd, text.encode('utf-8'))
        except Exception as e:
            logger.warning(f"Failed to send input: {e}")

    def send_signal(self, sig: signal.Signals):
        """Send signal to the process"""
        try:
            if sys.platform == 'win32':
                self._send_signal_windows(sig)
            else:
                self._send_signal_unix(sig)
        except Exception as e:
            logger.warning(f"Failed to send signal {sig}: {e}")

    def _send_signal_unix(self, sig: signal.Signals):
        """Send signal on Unix systems"""
        if self.process_id:
            os.killpg(self.process_id, sig)

    def _send_signal_windows(self, sig: signal.Signals):
        """Send signal on Windows systems"""
        if sig == signal.SIGINT:
            # Try to send Ctrl+C
            if self.process:
                try:
                    # Send Ctrl+C character to PTY
                    self.process.write(b'\x03')
                except:
                    # Fallback: terminate process
                    if hasattr(self.process, 'terminate'):
                        self.process.terminate()
        elif sig == signal.SIGTERM:
            if self.process and hasattr(self.process, 'terminate'):
                self.process.terminate()

    def resize_pty(self, cols: int, rows: int):
        """Resize the PTY"""
        try:
            if sys.platform != 'win32' and self.pty_fd:
                import fcntl
                import termios
                s = struct.pack('HHHH', rows, cols, 0, 0)
                fcntl.ioctl(self.pty_fd, termios.TIOCSWINSZ, s)
            elif sys.platform == 'win32' and self.process:
                # Windows PTY resize (if supported by winpty)
                if hasattr(self.process, 'set_size'):
                    self.process.set_size(cols, rows)
        except Exception as e:
            logger.warning(f"Failed to resize PTY: {e}")

    def stop(self):
        """Stop the PTY worker"""
        self.should_stop = True
        if self.process:
            try:
                self.send_signal(signal.SIGTERM)
                time.sleep(0.1)
                if sys.platform != 'win32' and hasattr(self.process, 'poll') and self.process.poll() is None:
                    self.send_signal(signal.SIGKILL)
            except:
                pass


class PTYBackend(QObject):
    """PTY backend manager for cross-platform terminal support"""

    output_received = pyqtSignal(str)
    process_finished = pyqtSignal(CommandResult)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_worker = None
        self.default_shell = self._get_default_shell()
        self.default_env = dict(os.environ)

    def _get_default_shell(self) -> str:
        """Get default system shell"""
        if sys.platform == 'win32':
            return os.environ.get('COMSPEC', 'cmd.exe')
        else:
            return os.environ.get('SHELL', '/bin/bash')

    def start_session(self, command: Optional[str] = None, args: Optional[list] = None,
                     cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None):
        """Start a new PTY session"""
        # Stop existing session
        self.stop_session()

        # Set defaults
        if command is None:
            command = self.default_shell
        if args is None:
            args = []
        if cwd is None:
            cwd = os.getcwd()
        if env is None:
            env = self.default_env

        # Create and start worker
        self.current_worker = PTYWorker(command, args, cwd, env)
        self.current_worker.data_received.connect(self.output_received)
        self.current_worker.process_finished.connect(self.process_finished)
        self.current_worker.error_occurred.connect(self.error_occurred)

        self.current_worker.start()
        logger.info(f"Started PTY session: {command} {' '.join(args)}")

    def send_input(self, text: str):
        """Send input to current PTY session"""
        if self.current_worker:
            self.current_worker.send_input(text)

    def send_signal(self, sig: signal.Signals):
        """Send signal to current PTY session"""
        if self.current_worker:
            self.current_worker.send_signal(sig)

    def resize_terminal(self, cols: int, rows: int):
        """Resize current PTY session"""
        if self.current_worker:
            self.current_worker.resize_pty(cols, rows)

    def stop_session(self):
        """Stop current PTY session"""
        if self.current_worker:
            self.current_worker.stop()
            self.current_worker.wait()
            self.current_worker = None
            logger.info("PTY session stopped")

    def is_session_active(self) -> bool:
        """Check if PTY session is active"""
        return self.current_worker is not None and self.current_worker.isRunning()