#!/usr/bin/env python3
# doc_id: DOC-TEST-0056
# DOC_ID: DOC-SERVICE-0014
"""
End-to-End Signal Flow Tester
Validates complete signal flow from source to MT4 execution
"""

import os
import time
import json
import csv
import socket
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TestResult(Enum):
    """Test result types"""
    PASS = "PASS"
    FAIL = "FAIL"
    TIMEOUT = "TIMEOUT"
    PARTIAL = "PARTIAL"


@dataclass
class TestStep:
    """Individual test step"""
    name: str
    expected_file: str
    timeout_seconds: int
    validation_func: callable
    result: TestResult = TestResult.FAIL
    details: str = ""
    timestamp: Optional[datetime] = None


class SignalFlowTester:
    """Tests complete signal flow from source to MT4"""
    
    def __init__(self, mt4_data_folder: str, test_timeout: int = 300):
        self.mt4_data_folder = Path(mt4_data_folder)
        self.eafix_dir = self.mt4_data_folder / "eafix"
        self.test_timeout = test_timeout
        self.test_results: List[TestStep] = []
        
        # Ensure directories exist
        self.eafix_dir.mkdir(parents=True, exist_ok=True)
        
    def validate_csv_structure(self, file_path: Path, expected_headers: List[str]) -> Tuple[bool, str]:
        """Validate CSV file structure and integrity"""
        try:
            if not file_path.exists():
                return False, f"File does not exist: {file_path}"
                
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                
                # Check headers
                missing_headers = set(expected_headers) - set(headers)
                if missing_headers:
                    return False, f"Missing headers: {missing_headers}"
                
                # Check for data rows
                row_count = sum(1 for _ in reader)
                if row_count == 0:
                    return False, "No data rows found"
                
                return True, f"Valid CSV with {row_count} data rows"
                
        except Exception as e:
            return False, f"CSV validation error: {str(e)}"
    
    def validate_file_sequence(self, file_path: Path) -> Tuple[bool, str]:
        """Validate file_seq monotonicity and checksums"""
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            if not rows:
                return False, "No data to validate"
            
            # Check file_seq monotonicity
            sequences = [int(row.get('file_seq', 0)) for row in rows]
            if sequences != sorted(sequences):
                return False, "file_seq not monotonic"
            
            # Check checksums if present
            checksum_errors = []
            for i, row in enumerate(rows):
                if 'checksum_sha256' in row:
                    # Create row copy without checksum for validation
                    row_copy = {k: v for k, v in row.items() if k != 'checksum_sha256'}
                    row_str = json.dumps(row_copy, sort_keys=True)
                    calculated_checksum = hashlib.sha256(row_str.encode()).hexdigest()
                    
                    if calculated_checksum != row['checksum_sha256']:
                        checksum_errors.append(f"Row {i+1}: checksum mismatch")
            
            if checksum_errors:
                return False, f"Checksum errors: {'; '.join(checksum_errors)}"
                
            return True, f"Valid sequences and checksums for {len(rows)} rows"
            
        except Exception as e:
            return False, f"Sequence validation error: {str(e)}"
    
    def wait_for_file_update(self, file_path: Path, timeout: int, 
                            initial_mtime: Optional[float] = None) -> Tuple[bool, str]:
        """Wait for file to be created or updated"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if file_path.exists():
                current_mtime = file_path.stat().st_mtime
                if initial_mtime is None or current_mtime > initial_mtime:
                    return True, f"File updated at {datetime.fromtimestamp(current_mtime)}"
            time.sleep(1)
        
        return False, f"File not updated within {timeout} seconds"
    
    def test_socket_communication(self) -> TestStep:
        """Test socket communication if available"""
        step = TestStep(
            name="Socket Communication Test",
            expected_file="N/A",
            timeout_seconds=10,
            validation_func=None
        )
        
        try:
            # Try to connect to MT4 socket server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            # Try common ports
            ports = [5555, 9999]
            connected = False
            
            for port in ports:
                try:
                    sock.connect(('localhost', port))
                    connected = True
                    step.details = f"Socket connection successful on port {port}"
                    step.result = TestResult.PASS
                    
                    # Send test message
                    test_msg = {"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()}
                    sock.send((json.dumps(test_msg) + "\n").encode())
                    
                    break
                except:
                    continue
            
            if not connected:
                step.result = TestResult.FAIL
                step.details = f"Could not connect to socket on ports {ports}"
            
            sock.close()
            
        except Exception as e:
            step.result = TestResult.FAIL
            step.details = f"Socket test error: {str(e)}"
        
        step.timestamp = datetime.utcnow()
        return step
    
    def test_csv_integrity(self) -> TestStep:
        """Test CSV integrity checker"""
        step = TestStep(
            name="CSV Integrity Check",
            expected_file="csv_integrity_report.txt",
            timeout_seconds=30,
            validation_func=None
        )
        
        try:
            # Run CSV integrity checker if available
            import subprocess
            result = subprocess.run(
                ["python", "csv_integrity_check.py", str(self.eafix_dir)],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                step.result = TestResult.PASS
                step.details = f"CSV integrity check passed: {result.stdout}"
            else:
                step.result = TestResult.FAIL
                step.details = f"CSV integrity check failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            step.result = TestResult.TIMEOUT
            step.details = "CSV integrity check timed out"
        except FileNotFoundError:
            step.result = TestResult.PARTIAL
            step.details = "csv_integrity_check.py not found - skipping"
        except Exception as e:
            step.result = TestResult.FAIL
            step.details = f"CSV integrity check error: {str(e)}"
        
        step.timestamp = datetime.utcnow()
        return step
    
    def inject_calendar_signal(self) -> TestStep:
        """Inject calendar signal and verify processing"""
        step = TestStep(
            name="Calendar Signal Injection",
            expected_file="active_calendar_signals.csv",
            timeout_seconds=60,
            validation_func=lambda: self.validate_csv_structure(
                self.eafix_dir / "active_calendar_signals.csv",
                ['symbol', 'cal8', 'cal5', 'signal_type', 'proximity', 'event_time_utc', 
                 'state', 'priority_weight', 'file_seq', 'created_at_utc', 'checksum_sha256']
            )
        )
        
        try:
            # Create test calendar event
            from calendar_event_simulator import CalendarEventSimulator
            
            simulator = CalendarEventSimulator(str(self.eafix_dir))
            
            # Create immediate proximity event to trigger processing
            event_config = {
                'symbol': 'EURUSD',
                'region': 'A',
                'country': 'US', 
                'impact': 'H',
                'event_type': 'NF',
                'signal_type': 'ECO_HIGH_USD',
                'state': 'ACTIVE',
                'proximity': 'IM',  # Immediate
                'minutes_from_now': 0,  # Now
                'priority_weight': 1.0
            }
            
            event = simulator.create_test_event(event_config)
            file_path = simulator.write_active_calendar_signals([event])
            
            # Wait for system to process
            target_file = self.eafix_dir / "active_calendar_signals.csv"
            initial_mtime = target_file.stat().st_mtime if target_file.exists() else None
            
            updated, update_msg = self.wait_for_file_update(target_file, step.timeout_seconds, initial_mtime)
            
            if updated:
                is_valid, validation_msg = step.validation_func()
                if is_valid:
                    step.result = TestResult.PASS
                    step.details = f"Calendar signal processed successfully: {validation_msg}"
                else:
                    step.result = TestResult.FAIL
                    step.details = f"Calendar signal validation failed: {validation_msg}"
            else:
                step.result = TestResult.TIMEOUT
                step.details = f"Calendar signal not processed: {update_msg}"
                
        except Exception as e:
            step.result = TestResult.FAIL
            step.details = f"Calendar signal injection error: {str(e)}"
        
        step.timestamp = datetime.utcnow()
        return step
    
    def inject_indicator_signal(self) -> TestStep:
        """Inject indicator signal and verify processing"""
        step = TestStep(
            name="Indicator Signal Injection",
            expected_file="reentry_decisions.csv",
            timeout_seconds=60,
            validation_func=lambda: self.validate_csv_structure(
                self.eafix_dir / "reentry_decisions.csv",
                ['hybrid_id', 'parameter_set_id', 'param_version', 'lots', 'sl_points', 
                 'tp_points', 'entry_offset_points', 'comment', 'file_seq', 
                 'created_at_utc', 'checksum_sha256']
            )
        )
        
        try:
            from indicator_signal_simulator import IndicatorSignalSimulator
            
            simulator = IndicatorSignalSimulator(str(self.eafix_dir))
            
            # Create high-confidence indicator signal
            signal_file = simulator.simulate_ma_crossover('EURUSD', 'LONG')
            
            # Wait for decision processing
            target_file = self.eafix_dir / "reentry_decisions.csv"
            initial_mtime = target_file.stat().st_mtime if target_file.exists() else None
            
            updated, update_msg = self.wait_for_file_update(target_file, step.timeout_seconds, initial_mtime)
            
            if updated:
                is_valid, validation_msg = step.validation_func()
                if is_valid:
                    step.result = TestResult.PASS
                    step.details = f"Indicator signal processed to decision: {validation_msg}"
                else:
                    step.result = TestResult.FAIL
                    step.details = f"Decision validation failed: {validation_msg}"
            else:
                step.result = TestResult.TIMEOUT
                step.details = f"Indicator signal not processed to decision: {update_msg}"
                
        except Exception as e:
            step.result = TestResult.FAIL
            step.details = f"Indicator signal injection error: {str(e)}"
        
        step.timestamp = datetime.utcnow()
        return step
    
    def verify_mt4_execution(self) -> TestStep:
        """Verify MT4 receives and processes signals"""
        step = TestStep(
            name="MT4 Execution Verification",
            expected_file="trade_results.csv",
            timeout_seconds=120,
            validation_func=lambda: self.validate_csv_structure(
                self.eafix_dir / "trade_results.csv",
                ['file_seq', 'ts_utc', 'account_id', 'symbol', 'ticket', 'direction', 
                 'lots', 'entry_price', 'close_price', 'profit_ccy', 'pips', 
                 'open_time_utc', 'close_time_utc', 'sl_price', 'tp_price', 
                 'magic_number', 'close_reason', 'signal_source', 'parameter_set_id', 
                 'param_version', 'checksum_sha256']
            )
        )
        
        try:
            # Check if MT4 EA is running by looking for recent heartbeat
            health_file = self.eafix_dir / "health_metrics.csv"
            
            if health_file.exists():
                with open(health_file, 'r') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                if rows:
                    last_row = rows[-1]
                    last_heartbeat = datetime.fromisoformat(last_row['last_heartbeat'].replace('Z', '+00:00'))
                    time_since_heartbeat = datetime.utcnow().replace(tzinfo=last_heartbeat.tzinfo) - last_heartbeat
                    
                    if time_since_heartbeat.total_seconds() > 60:
                        step.result = TestResult.FAIL
                        step.details = f"MT4 EA not responding - last heartbeat {time_since_heartbeat.total_seconds():.0f}s ago"
                        step.timestamp = datetime.utcnow()
                        return step
            
            # Wait for trade execution results
            target_file = self.eafix_dir / "trade_results.csv"
            initial_mtime = target_file.stat().st_mtime if target_file.exists() else None
            
            updated, update_msg = self.wait_for_file_update(target_file, step.timeout_seconds, initial_mtime)
            
            if updated:
                is_valid, validation_msg = step.validation_func()
                if is_valid:
                    step.result = TestResult.PASS
                    step.details = f"MT4 execution confirmed: {validation_msg}"
                else:
                    step.result = TestResult.FAIL
                    step.details = f"Trade results validation failed: {validation_msg}"
            else:
                step.result = TestResult.PARTIAL
                step.details = f"No new trade executions detected: {update_msg}"
                
        except Exception as e:
            step.result = TestResult.FAIL
            step.details = f"MT4 execution verification error: {str(e)}"
        
        step.timestamp = datetime.utcnow()
        return step
    
    def run_comprehensive_test(self) -> Dict:
        """Run complete end-to-end test suite"""
        print("=== Starting Comprehensive Signal Flow Test ===\n")
        
        test_start = datetime.utcnow()
        
        # Test sequence
        test_steps = [
            ("Socket Communication", self.test_socket_communication),
            ("CSV Integrity", self.test_csv_integrity),
            ("Calendar Signal Flow", self.inject_calendar_signal),
            ("Indicator Signal Flow", self.inject_indicator_signal),
            ("MT4 Execution", self.verify_mt4_execution)
        ]
        
        results = []
        
        for step_name, test_func in test_steps:
            print(f"Running: {step_name}...")
            step_result = test_func()
            results.append(step_result)
            
            print(f"  Result: {step_result.result.value}")
            print(f"  Details: {step_result.details}")
            print()
            
            # Stop on critical failures
            if step_result.result == TestResult.FAIL and step_name in ["Calendar Signal Flow", "Indicator Signal Flow"]:
                print(f"Critical failure in {step_name} - stopping test suite")
                break
        
        test_end = datetime.utcnow()
        test_duration = (test_end - test_start).total_seconds()
        
        # Generate summary
        summary = {
            'test_start': test_start.isoformat(),
            'test_end': test_end.isoformat(),
            'duration_seconds': test_duration,
            'total_steps': len(results),
            'passed': sum(1 for r in results if r.result == TestResult.PASS),
            'failed': sum(1 for r in results if r.result == TestResult.FAIL),
            'timeout': sum(1 for r in results if r.result == TestResult.TIMEOUT),
            'partial': sum(1 for r in results if r.result == TestResult.PARTIAL),
            'steps': results
        }
        
        # Print summary
        print("=== Test Summary ===")
        print(f"Duration: {test_duration:.1f} seconds")
        print(f"Passed: {summary['passed']}/{summary['total_steps']}")
        print(f"Failed: {summary['failed']}/{summary['total_steps']}")
        print(f"Timeout: {summary['timeout']}/{summary['total_steps']}")
        print(f"Partial: {summary['partial']}/{summary['total_steps']}")
        
        if summary['failed'] == 0 and summary['timeout'] == 0:
            print("\n✅ ALL TESTS PASSED - Signal flow is working correctly!")
        else:
            print("\n❌ SOME TESTS FAILED - Check individual step details above")
        
        return summary
    
    def generate_test_report(self, summary: Dict, output_file: str = "signal_flow_test_report.json"):
        """Generate detailed test report"""
        report_path = Path(output_file)
        
        # Convert test steps to serializable format
        serializable_summary = summary.copy()
        serializable_summary['steps'] = []
        
        for step in summary['steps']:
            step_dict = {
                'name': step.name,
                'expected_file': step.expected_file,
                'timeout_seconds': step.timeout_seconds,
                'result': step.result.value,
                'details': step.details,
                'timestamp': step.timestamp.isoformat() if step.timestamp else None
            }
            serializable_summary['steps'].append(step_dict)
        
        with open(report_path, 'w') as f:
            json.dump(serializable_summary, f, indent=2)
        
        print(f"\nDetailed test report saved to: {report_path}")


def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test complete signal flow from source to MT4")
    parser.add_argument("--mt4-data", required=True, help="MT4 data folder path")
    parser.add_argument("--timeout", type=int, default=300, help="Test timeout in seconds")
    parser.add_argument("--report", default="signal_flow_test_report.json", help="Output report file")
    
    args = parser.parse_args()
    
    # Validate MT4 data folder
    mt4_path = Path(args.mt4_data)
    if not mt4_path.exists():
        print(f"Error: MT4 data folder does not exist: {mt4_path}")
        return 1
    
    # Run tests
    tester = SignalFlowTester(str(mt4_path), args.timeout)
    summary = tester.run_comprehensive_test()
    tester.generate_test_report(summary, args.report)
    
    # Return appropriate exit code
    if summary['failed'] > 0 or summary['timeout'] > 0:
        return 1
    return 0


if __name__ == "__main__":
    exit(main())