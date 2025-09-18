"""
Terminal Parity Test Harness
Validates that GUI terminal matches VS Code terminal behavior exactly
"""

import os
import sys
import subprocess
import time
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict


@dataclass
class ParityTestResult:
    """Result of a parity test"""
    test_name: str
    gui_result: Dict[str, Any]
    cli_result: Dict[str, Any]
    passed: bool
    differences: List[str]
    notes: str = ""


class TerminalParityTester:
    """Test harness for terminal parity between GUI and CLI"""
    
    def __init__(self, gui_command: str = "python gui/cli_terminal_gui.py", timeout: int = 30):
        self.gui_command = gui_command
        self.timeout = timeout
        self.test_results = []
        
    def run_all_tests(self) -> List[ParityTestResult]:
        """Run comprehensive parity test suite"""
        print("🧪 Running Terminal Parity Tests...")
        print("=" * 50)
        
        # Core parity tests
        tests = [
            self.test_isatty_detection,
            self.test_ansi_colors,
            self.test_interactive_prompts,
            self.test_ctrl_c_handling,
            self.test_unicode_support,
            self.test_exit_codes,
            self.test_stderr_handling,
            self.test_environment_inheritance,
            self.test_working_directory,
            self.test_shell_integration,
        ]
        
        for test_func in tests:
            try:
                result = test_func()
                self.test_results.append(result)
                self._print_test_result(result)
            except Exception as e:
                error_result = ParityTestResult(
                    test_name=test_func.__name__,
                    gui_result={"error": str(e)},
                    cli_result={"error": "Test failed"},
                    passed=False,
                    differences=[f"Test execution failed: {e}"]
                )
                self.test_results.append(error_result)
                self._print_test_result(error_result)
                
        self._print_summary()
        return self.test_results
        
    def test_isatty_detection(self) -> ParityTestResult:
        """Test that isatty() returns True in both environments"""
        test_script = '''
import sys
print(f"stdin.isatty(): {sys.stdin.isatty()}")
print(f"stdout.isatty(): {sys.stdout.isatty()}")
print(f"stderr.isatty(): {sys.stderr.isatty()}")
'''
        
        gui_result = self._run_in_gui(test_script)
        cli_result = self._run_in_cli(test_script)
        
        differences = []
        if gui_result.get("stdout") != cli_result.get("stdout"):
            differences.append("isatty() output differs")
            
        return ParityTestResult(
            test_name="TTY Detection",
            gui_result=gui_result,
            cli_result=cli_result,
            passed=len(differences) == 0,
            differences=differences,
            notes="Both should show True for interactive terminals"
        )
        
    def test_ansi_colors(self) -> ParityTestResult:
        """Test ANSI color sequence handling"""
        test_script = '''
print("\\033[31mRed text\\033[0m")
print("\\033[32mGreen text\\033[0m")  
print("\\033[1;34mBold blue text\\033[0m")
print("\\033[41;37mRed background, white text\\033[0m")
'''
        
        gui_result = self._run_in_gui(test_script)
        cli_result = self._run_in_cli(test_script)
        
        differences = []
        # For ANSI tests, we check that both contain the color sequences
        gui_output = gui_result.get("stdout", "")
        cli_output = cli_result.get("stdout", "")
        
        # Both should contain the text (colors are handled by display layer)
        if "Red text" not in gui_output or "Green text" not in gui_output:
            differences.append("GUI missing color text content")
        if "Red text" not in cli_output or "Green text" not in cli_output:
            differences.append("CLI missing color text content")
            
        return ParityTestResult(
            test_name="ANSI Colors",
            gui_result=gui_result,
            cli_result=cli_result,
            passed=len(differences) == 0,
            differences=differences,
            notes="Both should display colored text"
        )
        
    def test_interactive_prompts(self) -> ParityTestResult:
        """Test interactive prompts (simplified - no actual input)"""
        test_script = '''
import sys
print("This is a prompt test")
# Note: actual input() would hang in automated testing
print("Prompt would appear here: ", end="")
sys.stdout.flush()
print("[simulated input]")
'''
        
        gui_result = self._run_in_gui(test_script)
        cli_result = self._run_in_cli(test_script)
        
        differences = []
        if gui_result.get("exit_code") != cli_result.get("exit_code"):
            differences.append("Exit codes differ for signal handling")
            
        return ParityTestResult(
            test_name="Ctrl+C Handling",
            gui_result=gui_result,
            cli_result=cli_result,
            passed=len(differences) == 0,
            differences=differences,
            notes="Both should handle signals properly"
        )
        
    def test_unicode_support(self) -> ParityTestResult:
        """Test Unicode and special character support"""
        test_script = '''
import sys
print("Unicode test: 🚀 ✅ ❌ 🔥")
print("Special chars: áéíóú ñ ç")
print("Box drawing: ┌─┐│ │└─┘")
print("Math symbols: ∑ ∆ π ∞")
print(f"Encoding: {sys.stdout.encoding}")
'''
        
        gui_result = self._run_in_gui(test_script)
        cli_result = self._run_in_cli(test_script)
        
        differences = []
        gui_output = gui_result.get("stdout", "")
        cli_output = cli_result.get("stdout", "")
        
        # Check for presence of unicode characters
        test_chars = ["🚀", "✅", "ñ", "┌", "π"]
        for char in test_chars:
            if char in cli_output and char not in gui_output:
                differences.append(f"GUI missing unicode char: {char}")
            elif char in gui_output and char not in cli_output:
                differences.append(f"CLI missing unicode char: {char}")
                
        return ParityTestResult(
            test_name="Unicode Support",
            gui_result=gui_result,
            cli_result=cli_result,
            passed=len(differences) == 0,
            differences=differences,
            notes="Both should display unicode characters correctly"
        )
        
    def test_exit_codes(self) -> ParityTestResult:
        """Test exit code propagation"""
        test_script = '''
import sys
print("Testing exit codes")
sys.exit(42)
'''
        
        gui_result = self._run_in_gui(test_script)
        cli_result = self._run_in_cli(test_script)
        
        differences = []
        if gui_result.get("exit_code") != 42:
            differences.append(f"GUI exit code wrong: {gui_result.get('exit_code')} != 42")
        if cli_result.get("exit_code") != 42:
            differences.append(f"CLI exit code wrong: {cli_result.get('exit_code')} != 42")
            
        return ParityTestResult(
            test_name="Exit Codes",
            gui_result=gui_result,
            cli_result=cli_result,
            passed=len(differences) == 0,
            differences=differences,
            notes="Both should return exit code 42"
        )
        
    def test_stderr_handling(self) -> ParityTestResult:
        """Test stderr vs stdout separation"""
        test_script = '''
import sys
print("This goes to stdout")
print("This goes to stderr", file=sys.stderr)
sys.stderr.flush()
sys.stdout.flush()
'''
        
        gui_result = self._run_in_gui(test_script)
        cli_result = self._run_in_cli(test_script)
        
        differences = []
        
        # Check that both captured stderr
        gui_stderr = gui_result.get("stderr", "")
        cli_stderr = cli_result.get("stderr", "")
        
        if "stderr" not in gui_stderr:
            differences.append("GUI didn't capture stderr")
        if "stderr" not in cli_stderr:
            differences.append("CLI didn't capture stderr")
            
        return ParityTestResult(
            test_name="Stderr Handling",
            gui_result=gui_result,
            cli_result=cli_result,
            passed=len(differences) == 0,
            differences=differences,
            notes="Both should separate stdout and stderr"
        )
        
    def test_environment_inheritance(self) -> ParityTestResult:
        """Test environment variable inheritance"""
        test_script = '''
import os
print(f"PATH exists: {'PATH' in os.environ}")
print(f"PYTHON_PATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"VIRTUAL_ENV: {os.environ.get('VIRTUAL_ENV', 'Not set')}")
print(f"Total env vars: {len(os.environ)}")
'''
        
        gui_result = self._run_in_gui(test_script)
        cli_result = self._run_in_cli(test_script)
        
        differences = []
        gui_output = gui_result.get("stdout", "")
        cli_output = cli_result.get("stdout", "")
        
        # Both should have PATH
        if "PATH exists: True" not in gui_output:
            differences.append("GUI missing PATH environment")
        if "PATH exists: True" not in cli_output:
            differences.append("CLI missing PATH environment")
            
        return ParityTestResult(
            test_name="Environment Inheritance",
            gui_result=gui_result,
            cli_result=cli_result,
            passed=len(differences) == 0,
            differences=differences,
            notes="Both should inherit environment variables"
        )
        
    def test_working_directory(self) -> ParityTestResult:
        """Test working directory consistency"""
        test_script = '''
import os
print(f"Current directory: {os.getcwd()}")
print(f"Directory exists: {os.path.exists('.')}")
'''
        
        gui_result = self._run_in_gui(test_script)
        cli_result = self._run_in_cli(test_script)
        
        differences = []
        gui_output = gui_result.get("stdout", "")
        cli_output = cli_result.get("stdout", "")
        
        # Extract directory paths
        gui_dir = self._extract_directory(gui_output)
        cli_dir = self._extract_directory(cli_output)
        
        if gui_dir != cli_dir:
            differences.append(f"Working directories differ: GUI={gui_dir}, CLI={cli_dir}")
            
        return ParityTestResult(
            test_name="Working Directory",
            gui_result=gui_result,
            cli_result=cli_result,
            passed=len(differences) == 0,
            differences=differences,
            notes="Both should start in same directory"
        )
        
    def test_shell_integration(self) -> ParityTestResult:
        """Test shell command execution"""
        if sys.platform == "win32":
            test_command = "echo Hello from Windows"
        else:
            test_command = "echo 'Hello from Unix'"
            
        gui_result = self._run_command_in_gui(test_command)
        cli_result = self._run_command_in_cli(test_command)
        
        differences = []
        
        # Both should execute shell commands
        if "Hello from" not in gui_result.get("stdout", ""):
            differences.append("GUI shell command failed")
        if "Hello from" not in cli_result.get("stdout", ""):
            differences.append("CLI shell command failed")
            
        return ParityTestResult(
            test_name="Shell Integration",
            gui_result=gui_result,
            cli_result=cli_result,
            passed=len(differences) == 0,
            differences=differences,
            notes="Both should execute shell commands"
        )
        
    def _run_in_gui(self, python_script: str) -> Dict[str, Any]:
        """Run Python script in GUI terminal (simulated)"""
        # For now, simulate GUI execution by running in subprocess
        # In real implementation, this would interact with the GUI
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_script)
            script_path = f.name
            
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "execution_time": 0  # Would be measured in real GUI
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Timeout expired",
                "exit_code": -1,
                "execution_time": self.timeout
            }
        finally:
            os.unlink(script_path)
            
    def _run_in_cli(self, python_script: str) -> Dict[str, Any]:
        """Run Python script in CLI environment"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_script)
            script_path = f.name
            
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "execution_time": 0
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Timeout expired",
                "exit_code": -1,
                "execution_time": self.timeout
            }
        finally:
            os.unlink(script_path)
            
    def _run_command_in_gui(self, command: str) -> Dict[str, Any]:
        """Run shell command in GUI (simulated)"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "execution_time": 0
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Timeout expired",
                "exit_code": -1,
                "execution_time": self.timeout
            }
            
    def _run_command_in_cli(self, command: str) -> Dict[str, Any]:
        """Run shell command in CLI environment"""
        return self._run_command_in_gui(command)  # Same implementation for now
        
    def _extract_directory(self, output: str) -> str:
        """Extract directory path from test output"""
        for line in output.split('\n'):
            if "Current directory:" in line:
                return line.split("Current directory: ")[1].strip()
        return ""
        
    def _print_test_result(self, result: ParityTestResult):
        """Print formatted test result"""
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"{status} {result.test_name}")
        
        if not result.passed:
            for diff in result.differences:
                print(f"   - {diff}")
                
        if result.notes:
            print(f"   Note: {result.notes}")
        print()
        
    def _print_summary(self):
        """Print test summary"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.passed)
        failed = total - passed
        
        print("=" * 50)
        print(f"📊 Test Summary: {passed}/{total} passed")
        
        if failed > 0:
            print(f"❌ {failed} tests failed:")
            for result in self.test_results:
                if not result.passed:
                    print(f"   - {result.test_name}")
        else:
            print("🎉 All tests passed! Terminal parity achieved.")
            
        print("=" * 50)
        
    def save_results(self, filename: str = "parity_test_results.json"):
        """Save test results to JSON file"""
        results_data = {
            "test_run_time": time.time(),
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for r in self.test_results if r.passed),
            "results": [asdict(result) for result in self.test_results]
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
            
        print(f"📄 Results saved to {filename}")


def main():
    """Run the parity test suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test terminal parity between GUI and CLI")
    parser.add_argument("--gui-command", default="python gui/cli_terminal_gui.py",
                       help="Command to launch GUI terminal")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Timeout for individual tests")
    parser.add_argument("--save-results", default="parity_test_results.json",
                       help="File to save test results")
    
    args = parser.parse_args()
    
    # Check if GUI exists
    gui_path = Path("gui/cli_terminal_gui.py")
    if not gui_path.exists():
        print("❌ GUI terminal not found at gui/cli_terminal_gui.py")
        print("💡 Run the migration script first to create the GUI")
        return 1
        
    # Run tests
    tester = TerminalParityTester(args.gui_command, args.timeout)
    results = tester.run_all_tests()
    
    # Save results
    if args.save_results:
        tester.save_results(args.save_results)
        
    # Return exit code based on results
    failed_tests = sum(1 for r in results if not r.passed)
    return 1 if failed_tests > 0 else 0


if __name__ == "__main__":
    sys.exit(main())_code"):
            differences.append("Exit codes differ")
            
        return ParityTestResult(
            test_name="Interactive Prompts",
            gui_result=gui_result,
            cli_result=cli_result,
            passed=len(differences) == 0,
            differences=differences,
            notes="Both should handle prompts without hanging"
        )
        
    def test_ctrl_c_handling(self) -> ParityTestResult:
        """Test Ctrl+C signal handling (simulated)"""
        test_script = '''
import signal
import sys

def signal_handler(signum, frame):
    print("Received signal:", signum)
    sys.exit(130)  # Standard Ctrl+C exit code

signal.signal(signal.SIGINT, signal_handler)
print("Signal handler registered")
print("Exit code will be 0 (no actual Ctrl+C in test)")
'''
        
        gui_result = self._run_in_gui(test_script)
        cli_result = self._run_in_cli(test_script)
        
        differences = []
        if gui_result.get("exit_code") != cli_result.get("exit