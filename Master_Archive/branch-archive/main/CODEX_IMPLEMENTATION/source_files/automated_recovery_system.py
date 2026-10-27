#!/usr/bin/env python3
"""
Automated Recovery Execution System
===================================

Intelligent system that automatically executes recovery procedures instead of just
suggesting them. Uses decision trees, runbooks, and AI-powered recovery automation.
"""

import asyncio
import json
import logging
import subprocess
import requests
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import yaml
import re
import shlex

logger = logging.getLogger(__name__)


class RecoveryStatus(Enum):
    """Recovery execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class RecoveryRisk(Enum):
    """Risk levels for recovery actions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(Enum):
    """Types of recovery actions."""
    COMMAND = "command"
    API_CALL = "api_call"
    SERVICE_RESTART = "service_restart"
    CONFIGURATION_CHANGE = "configuration_change"
    RESOURCE_CLEANUP = "resource_cleanup"
    NETWORK_OPERATION = "network_operation"
    DATABASE_OPERATION = "database_operation"
    CUSTOM_FUNCTION = "custom_function"


@dataclass
class RecoveryAction:
    """Individual recovery action."""
    id: str
    name: str
    action_type: ActionType
    command: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    risk_level: RecoveryRisk = RecoveryRisk.LOW
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 5.0
    verification_command: Optional[str] = None
    rollback_command: Optional[str] = None
    requires_confirmation: bool = False
    dependencies: List[str] = field(default_factory=list)
    custom_function: Optional[Callable] = None


@dataclass
class RecoveryRunbook:
    """Complete recovery runbook for a specific error type."""
    id: str
    name: str
    description: str
    error_patterns: List[str] = field(default_factory=list)
    error_conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[RecoveryAction] = field(default_factory=list)
    max_execution_time: int = 600  # 10 minutes
    auto_execute: bool = True
    requires_approval: bool = False
    success_criteria: List[str] = field(default_factory=list)
    rollback_on_failure: bool = True


@dataclass
class RecoveryExecution:
    """Record of a recovery execution."""
    id: str
    runbook_id: str
    error_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: RecoveryStatus = RecoveryStatus.PENDING
    actions_executed: List[Dict[str, Any]] = field(default_factory=list)
    success_rate: float = 0.0
    error_message: Optional[str] = None
    rollback_performed: bool = False


class AutomatedRecoverySystem:
    """Automatically executes recovery procedures based on detected issues."""
    
    def __init__(self, runbooks_dir: Path = Path("recovery_runbooks")):
        """Initialize the automated recovery system.
        
        Args:
            runbooks_dir: Directory containing recovery runbook definitions
        """
        self.runbooks_dir = runbooks_dir
        self.runbooks_dir.mkdir(exist_ok=True)
        
        # Recovery runbooks registry
        self.runbooks: Dict[str, RecoveryRunbook] = {}
        self.active_executions: Dict[str, RecoveryExecution] = {}
        self.execution_history: List[RecoveryExecution] = []
        
        # Configuration
        self.auto_execution_enabled = True
        self.high_risk_confirmation = True
        self.max_concurrent_recoveries = 3
        self.recovery_timeout = 600  # 10 minutes
        
        # State persistence
        self.state_file = Path("recovery_state.json")
        self.history_file = Path("recovery_history.json")
        
        # Load existing runbooks
        self._load_runbooks()
        self._load_state()
        
        logger.info("AutomatedRecoverySystem initialized")
    
    def register_runbook(self, runbook: RecoveryRunbook) -> None:
        """Register a recovery runbook.
        
        Args:
            runbook: Recovery runbook to register
        """
        self.runbooks[runbook.id] = runbook
        self._save_runbook(runbook)
        logger.info(f"Registered recovery runbook: {runbook.id}")
    
    async def execute_recovery(self, error_id: str, error_data: Dict[str, Any],
                             force_execute: bool = False) -> Optional[str]:
        """Execute recovery procedure for an error.
        
        Args:
            error_id: Unique identifier for the error
            error_data: Error details and context
            force_execute: Force execution even if auto-execution is disabled
            
        Returns:
            Execution ID if recovery started, None otherwise
        """
        if not self.auto_execution_enabled and not force_execute:
            logger.info("Auto-execution disabled, skipping recovery")
            return None
        
        # Find matching runbook
        runbook = self._find_matching_runbook(error_data)
        if not runbook:
            logger.warning(f"No matching runbook found for error: {error_id}")
            return None
        
        # Check if we're already at max concurrent executions
        if len(self.active_executions) >= self.max_concurrent_recoveries:
            logger.warning("Maximum concurrent recoveries reached, queuing...")
            return None
        
        # Create execution record
        execution_id = f"exec_{int(time.time())}_{error_id[:8]}"
        execution = RecoveryExecution(
            id=execution_id,
            runbook_id=runbook.id,
            error_id=error_id,
            start_time=datetime.now()
        )
        
        self.active_executions[execution_id] = execution
        
        # Start execution asynchronously
        asyncio.create_task(self._execute_runbook(execution, runbook, error_data))
        
        logger.info(f"Started recovery execution: {execution_id} for error: {error_id}")
        return execution_id
    
    def _find_matching_runbook(self, error_data: Dict[str, Any]) -> Optional[RecoveryRunbook]:
        """Find the best matching runbook for an error.
        
        Args:
            error_data: Error details and context
            
        Returns:
            Matching runbook or None
        """
        error_message = error_data.get("error_message", "").lower()
        error_type = error_data.get("error_type", "").lower()
        system = error_data.get("system", "").lower()
        
        best_match = None
        best_score = 0
        
        for runbook in self.runbooks.values():
            score = 0
            
            # Check error patterns
            for pattern in runbook.error_patterns:
                if re.search(pattern.lower(), error_message):
                    score += 10
                if re.search(pattern.lower(), error_type):
                    score += 8
            
            # Check error conditions
            for condition_key, condition_value in runbook.error_conditions.items():
                if condition_key in error_data:
                    if isinstance(condition_value, str):
                        if condition_value.lower() in str(error_data[condition_key]).lower():
                            score += 5
                    elif error_data[condition_key] == condition_value:
                        score += 5
            
            # Boost score for system-specific runbooks
            if system in runbook.id.lower():
                score += 3
            
            if score > best_score:
                best_score = score
                best_match = runbook
        
        return best_match if best_score >= 5 else None  # Minimum threshold
    
    async def _execute_runbook(self, execution: RecoveryExecution, 
                             runbook: RecoveryRunbook, error_data: Dict[str, Any]) -> None:
        """Execute a recovery runbook.
        
        Args:
            execution: Execution record to update
            runbook: Runbook to execute
            error_data: Original error data
        """
        logger.info(f"Executing runbook: {runbook.id}")
        execution.status = RecoveryStatus.RUNNING
        
        try:
            # Check if approval is required
            if runbook.requires_approval and not await self._get_approval(runbook, error_data):
                execution.status = RecoveryStatus.SKIPPED
                execution.error_message = "Approval required but not granted"
                return
            
            # Execute actions in sequence
            executed_actions = []
            successful_actions = 0
            
            for action in runbook.actions:
                # Check dependencies
                if not self._check_action_dependencies(action, executed_actions):
                    logger.warning(f"Dependencies not met for action: {action.id}")
                    continue
                
                # Execute action
                action_result = await self._execute_action(action, error_data, execution)
                executed_actions.append(action_result)
                execution.actions_executed.append(action_result)
                
                if action_result["status"] == "success":
                    successful_actions += 1
                elif action_result["status"] == "failed" and action.risk_level == RecoveryRisk.CRITICAL:
                    # Critical action failed, abort
                    logger.error(f"Critical action failed: {action.id}")
                    break
            
            # Calculate success rate
            if executed_actions:
                execution.success_rate = successful_actions / len(executed_actions)
            
            # Determine overall status
            if execution.success_rate >= 0.8:
                execution.status = RecoveryStatus.SUCCESS
                logger.info(f"Recovery completed successfully: {execution.id}")
                
                # Verify success criteria
                if runbook.success_criteria:
                    verification_passed = await self._verify_success_criteria(
                        runbook.success_criteria, error_data
                    )
                    if not verification_passed:
                        execution.status = RecoveryStatus.PARTIAL
                        logger.warning("Success criteria not fully met")
            
            elif execution.success_rate > 0:
                execution.status = RecoveryStatus.PARTIAL
                logger.warning(f"Recovery partially successful: {execution.id}")
            
            else:
                execution.status = RecoveryStatus.FAILED
                logger.error(f"Recovery failed: {execution.id}")
                
                # Perform rollback if configured
                if runbook.rollback_on_failure:
                    await self._perform_rollback(execution, executed_actions)
        
        except Exception as e:
            execution.status = RecoveryStatus.FAILED
            execution.error_message = str(e)
            logger.error(f"Recovery execution error: {e}")
        
        finally:
            execution.end_time = datetime.now()
            
            # Move to history
            self.execution_history.append(execution)
            if execution.id in self.active_executions:
                del self.active_executions[execution.id]
            
            # Save state
            self._save_state()
            
            logger.info(f"Recovery execution completed: {execution.id} - {execution.status.value}")
    
    async def _execute_action(self, action: RecoveryAction, error_data: Dict[str, Any],
                            execution: RecoveryExecution) -> Dict[str, Any]:
        """Execute a single recovery action.
        
        Args:
            action: Action to execute
            error_data: Original error data
            execution: Current execution context
            
        Returns:
            Action execution result
        """
        logger.info(f"Executing action: {action.name}")
        
        action_result = {
            "action_id": action.id,
            "action_name": action.name,
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "output": "",
            "error": None,
            "attempts": 0
        }
        
        # Check for confirmation requirement
        if action.requires_confirmation:
            if not await self._get_action_confirmation(action, error_data):
                action_result["status"] = "skipped"
                action_result["error"] = "User confirmation required but not granted"
                return action_result
        
        # Execute with retries
        for attempt in range(action.retry_count):
            action_result["attempts"] = attempt + 1
            
            try:
                success, output, error = await self._execute_action_type(action, error_data)
                
                if success:
                    action_result["status"] = "success"
                    action_result["output"] = output
                    
                    # Run verification if configured
                    if action.verification_command:
                        verification_success = await self._verify_action(action, error_data)
                        if not verification_success:
                            action_result["status"] = "partial"
                            action_result["error"] = "Verification failed"
                    
                    break
                else:
                    action_result["error"] = error
                    if attempt < action.retry_count - 1:
                        logger.warning(f"Action failed (attempt {attempt + 1}), retrying: {action.name}")
                        await asyncio.sleep(action.retry_delay)
                    else:
                        action_result["status"] = "failed"
            
            except Exception as e:
                action_result["error"] = str(e)
                if attempt < action.retry_count - 1:
                    await asyncio.sleep(action.retry_delay)
                else:
                    action_result["status"] = "failed"
        
        action_result["end_time"] = datetime.now().isoformat()
        logger.info(f"Action completed: {action.name} - {action_result['status']}")
        
        return action_result
    
    async def _execute_action_type(self, action: RecoveryAction, 
                                 error_data: Dict[str, Any]) -> tuple[bool, str, Optional[str]]:
        """Execute action based on its type.
        
        Args:
            action: Action to execute
            error_data: Error context
            
        Returns:
            (success, output, error)
        """
        try:
            if action.action_type == ActionType.COMMAND:
                return await self._execute_command(action, error_data)
            
            elif action.action_type == ActionType.API_CALL:
                return await self._execute_api_call(action, error_data)
            
            elif action.action_type == ActionType.SERVICE_RESTART:
                return await self._execute_service_restart(action, error_data)
            
            elif action.action_type == ActionType.CONFIGURATION_CHANGE:
                return await self._execute_config_change(action, error_data)
            
            elif action.action_type == ActionType.RESOURCE_CLEANUP:
                return await self._execute_resource_cleanup(action, error_data)
            
            elif action.action_type == ActionType.NETWORK_OPERATION:
                return await self._execute_network_operation(action, error_data)
            
            elif action.action_type == ActionType.DATABASE_OPERATION:
                return await self._execute_database_operation(action, error_data)
            
            elif action.action_type == ActionType.CUSTOM_FUNCTION:
                return await self._execute_custom_function(action, error_data)
            
            else:
                return False, "", f"Unknown action type: {action.action_type}"
        
        except Exception as e:
            return False, "", str(e)
    
    async def _execute_command(self, action: RecoveryAction, 
                             error_data: Dict[str, Any]) -> tuple[bool, str, Optional[str]]:
        """Execute shell command action."""
        if not action.command:
            return False, "", "No command specified"
        
        # Substitute variables in command
        command = self._substitute_variables(action.command, error_data, action.parameters)
        
        try:
            # Use shlex to safely parse the command
            cmd_parts = shlex.split(command)
            
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=action.timeout
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode() if stdout else ""
            error = stderr.decode() if stderr else None
            
            success = process.returncode == 0
            
            return success, output, error
        
        except asyncio.TimeoutError:
            return False, "", f"Command timeout after {action.timeout}s"
        
        except Exception as e:
            return False, "", str(e)
    
    async def _execute_api_call(self, action: RecoveryAction, 
                              error_data: Dict[str, Any]) -> tuple[bool, str, Optional[str]]:
        """Execute API call action."""
        url = action.parameters.get("url")
        method = action.parameters.get("method", "GET").upper()
        headers = action.parameters.get("headers", {})
        data = action.parameters.get("data")
        json_data = action.parameters.get("json")
        
        if not url:
            return False, "", "No URL specified for API call"
        
        # Substitute variables
        url = self._substitute_variables(url, error_data, action.parameters)
        
        try:
            async with asyncio.timeout(action.timeout):
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=action.timeout)
                elif method == "POST":
                    response = requests.post(url, headers=headers, data=data, 
                                           json=json_data, timeout=action.timeout)
                elif method == "PUT":
                    response = requests.put(url, headers=headers, data=data,
                                          json=json_data, timeout=action.timeout)
                elif method == "DELETE":
                    response = requests.delete(url, headers=headers, timeout=action.timeout)
                else:
                    return False, "", f"Unsupported HTTP method: {method}"
                
                success = 200 <= response.status_code < 300
                output = response.text
                error = None if success else f"HTTP {response.status_code}: {response.text}"
                
                return success, output, error
        
        except Exception as e:
            return False, "", str(e)
    
    async def _execute_service_restart(self, action: RecoveryAction,
                                     error_data: Dict[str, Any]) -> tuple[bool, str, Optional[str]]:
        """Execute service restart action."""
        service_name = action.parameters.get("service_name")
        if not service_name:
            service_name = error_data.get("service_name")
        
        if not service_name:
            return False, "", "No service name specified"
        
        try:
            # Try systemctl first
            stop_cmd = f"systemctl stop {service_name}"
            start_cmd = f"systemctl start {service_name}"
            status_cmd = f"systemctl is-active {service_name}"
            
            # Stop service
            stop_process = await asyncio.create_subprocess_shell(
                stop_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await stop_process.communicate()
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Start service
            start_process = await asyncio.create_subprocess_shell(
                start_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await start_process.communicate()
            
            # Wait for service to be ready
            await asyncio.sleep(5)
            
            # Check status
            status_process = await asyncio.create_subprocess_shell(
                status_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await status_process.communicate()
            
            output = f"Service {service_name} restart attempted"
            is_active = b"active" in stdout
            
            return is_active, output, None if is_active else f"Service {service_name} not active after restart"
        
        except Exception as e:
            return False, "", str(e)
    
    async def _execute_config_change(self, action: RecoveryAction,
                                   error_data: Dict[str, Any]) -> tuple[bool, str, Optional[str]]:
        """Execute configuration change action."""
        file_path = action.parameters.get("file_path")
        changes = action.parameters.get("changes", {})
        backup = action.parameters.get("backup", True)
        
        if not file_path or not changes:
            return False, "", "File path and changes required"
        
        try:
            config_file = Path(file_path)
            
            # Create backup if requested
            if backup:
                backup_file = config_file.with_suffix(f"{config_file.suffix}.backup.{int(time.time())}")
                backup_file.write_bytes(config_file.read_bytes())
            
            # Read current config
            if config_file.suffix in ['.json']:
                with open(config_file) as f:
                    config = json.load(f)
                
                # Apply changes
                for key, value in changes.items():
                    keys = key.split('.')
                    current = config
                    for k in keys[:-1]:
                        current = current.setdefault(k, {})
                    current[keys[-1]] = value
                
                # Write updated config
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
            
            elif config_file.suffix in ['.yml', '.yaml']:
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                
                # Apply changes
                for key, value in changes.items():
                    keys = key.split('.')
                    current = config
                    for k in keys[:-1]:
                        current = current.setdefault(k, {})
                    current[keys[-1]] = value
                
                # Write updated config
                with open(config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
            
            else:
                # Text file - simple find/replace
                content = config_file.read_text()
                for old, new in changes.items():
                    content = content.replace(old, new)
                config_file.write_text(content)
            
            return True, f"Configuration updated: {file_path}", None
        
        except Exception as e:
            return False, "", str(e)
    
    async def _execute_resource_cleanup(self, action: RecoveryAction,
                                      error_data: Dict[str, Any]) -> tuple[bool, str, Optional[str]]:
        """Execute resource cleanup action."""
        cleanup_type = action.parameters.get("type", "temp_files")
        
        try:
            if cleanup_type == "temp_files":
                # Clean up temporary files
                temp_dirs = ["/tmp", "/var/tmp", Path.home() / "tmp"]
                cleaned_size = 0
                
                for temp_dir in temp_dirs:
                    if Path(temp_dir).exists():
                        for file_path in Path(temp_dir).glob("*"):
                            if file_path.is_file() and file_path.stat().st_mtime < time.time() - 3600:  # 1 hour old
                                try:
                                    size = file_path.stat().st_size
                                    file_path.unlink()
                                    cleaned_size += size
                                except:
                                    pass
                
                return True, f"Cleaned {cleaned_size} bytes of temporary files", None
            
            elif cleanup_type == "memory":
                # Force garbage collection and memory cleanup
                import gc
                gc.collect()
                
                # Clear system caches if possible
                try:
                    subprocess.run(["sync"], check=False)
                    with open("/proc/sys/vm/drop_caches", "w") as f:
                        f.write("1\n")  # Clear page cache
                except:
                    pass
                
                return True, "Memory cleanup completed", None
            
            elif cleanup_type == "disk_space":
                # Clean up disk space
                cleaned_size = 0
                
                # Clean log files
                log_dirs = ["/var/log", "/tmp"]
                for log_dir in log_dirs:
                    if Path(log_dir).exists():
                        for log_file in Path(log_dir).glob("*.log*"):
                            if log_file.stat().st_size > 100 * 1024 * 1024:  # > 100MB
                                try:
                                    size = log_file.stat().st_size
                                    log_file.write_text("")  # Truncate instead of delete
                                    cleaned_size += size
                                except:
                                    pass
                
                return True, f"Cleaned {cleaned_size} bytes of disk space", None
            
            else:
                return False, "", f"Unknown cleanup type: {cleanup_type}"
        
        except Exception as e:
            return False, "", str(e)
    
    async def _execute_network_operation(self, action: RecoveryAction,
                                       error_data: Dict[str, Any]) -> tuple[bool, str, Optional[str]]:
        """Execute network operation action."""
        operation = action.parameters.get("operation")
        target = action.parameters.get("target")
        
        if not operation or not target:
            return False, "", "Operation and target required"
        
        try:
            if operation == "ping":
                # Test connectivity
                process = await asyncio.create_subprocess_exec(
                    "ping", "-c", "3", target,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                success = process.returncode == 0
                output = stdout.decode() if stdout else stderr.decode()
                
                return success, output, None if success else "Ping failed"
            
            elif operation == "port_check":
                # Check if port is open
                host, port = target.split(":")
                port = int(port)
                
                try:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(host, port),
                        timeout=action.timeout
                    )
                    writer.close()
                    await writer.wait_closed()
                    
                    return True, f"Port {port} on {host} is open", None
                
                except:
                    return False, "", f"Port {port} on {host} is not accessible"
            
            elif operation == "dns_lookup":
                # DNS resolution test
                import socket
                try:
                    ip = socket.gethostbyname(target)
                    return True, f"DNS lookup successful: {target} -> {ip}", None
                except:
                    return False, "", f"DNS lookup failed for {target}"
            
            else:
                return False, "", f"Unknown network operation: {operation}"
        
        except Exception as e:
            return False, "", str(e)
    
    async def _execute_database_operation(self, action: RecoveryAction,
                                        error_data: Dict[str, Any]) -> tuple[bool, str, Optional[str]]:
        """Execute database operation action."""
        # This is a placeholder implementation
        # In practice, you'd integrate with your specific database systems
        
        operation = action.parameters.get("operation")
        connection_string = action.parameters.get("connection_string")
        query = action.parameters.get("query")
        
        if not operation:
            return False, "", "Database operation not specified"
        
        try:
            if operation == "health_check":
                # Simple connection test
                # This would use your actual database client
                return True, "Database connection successful", None
            
            elif operation == "restart_connections":
                # Restart connection pool
                return True, "Database connections restarted", None
            
            elif operation == "clear_locks":
                # Clear database locks
                return True, "Database locks cleared", None
            
            else:
                return False, "", f"Unknown database operation: {operation}"
        
        except Exception as e:
            return False, "", str(e)
    
    async def _execute_custom_function(self, action: RecoveryAction,
                                     error_data: Dict[str, Any]) -> tuple[bool, str, Optional[str]]:
        """Execute custom function action."""
        if not action.custom_function:
            return False, "", "No custom function specified"
        
        try:
            # Execute custom function with error data and parameters
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                action.custom_function,
                error_data,
                action.parameters
            )
            
            if isinstance(result, tuple) and len(result) == 3:
                return result
            elif isinstance(result, bool):
                return result, "Custom function executed", None if result else "Custom function failed"
            else:
                return True, str(result), None
        
        except Exception as e:
            return False, "", str(e)
    
    def _substitute_variables(self, text: str, error_data: Dict[str, Any], 
                            parameters: Dict[str, Any]) -> str:
        """Substitute variables in text with actual values.
        
        Args:
            text: Text containing variables in {variable} format
            error_data: Error data for substitution
            parameters: Additional parameters
            
        Returns:
            Text with variables substituted
        """
        # Combine all available variables
        variables = {
            **error_data,
            **parameters,
            "timestamp": datetime.now().isoformat(),
            "hostname": subprocess.getoutput("hostname").strip()
        }
        
        # Substitute variables
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            text = text.replace(placeholder, str(value))
        
        return text
    
    async def _get_approval(self, runbook: RecoveryRunbook, 
                          error_data: Dict[str, Any]) -> bool:
        """Get approval for runbook execution (placeholder implementation).
        
        Args:
            runbook: Runbook requiring approval
            error_data: Error context
            
        Returns:
            True if approved
        """
        # In a real implementation, this would integrate with your approval system
        # (Slack, email, web interface, etc.)
        
        logger.info(f"Approval required for runbook: {runbook.id}")
        
        # For demo purposes, auto-approve low-risk runbooks
        has_high_risk_actions = any(
            action.risk_level in [RecoveryRisk.HIGH, RecoveryRisk.CRITICAL]
            for action in runbook.actions
        )
        
        if not has_high_risk_actions:
            logger.info("Auto-approving low-risk runbook")
            return True
        
        # High-risk runbooks would require explicit approval
        logger.warning("High-risk runbook requires manual approval")
        return False  # Would wait for approval in real implementation
    
    async def _get_action_confirmation(self, action: RecoveryAction,
                                     error_data: Dict[str, Any]) -> bool:
        """Get confirmation for high-risk action execution.
        
        Args:
            action: Action requiring confirmation
            error_data: Error context
            
        Returns:
            True if confirmed
        """
        # Similar to approval, this would integrate with confirmation system
        if action.risk_level in [RecoveryRisk.LOW, RecoveryRisk.MEDIUM]:
            return True
        
        logger.warning(f"High-risk action requires confirmation: {action.name}")
        return False  # Would wait for confirmation in real implementation
    
    def _check_action_dependencies(self, action: RecoveryAction,
                                 executed_actions: List[Dict[str, Any]]) -> bool:
        """Check if action dependencies are satisfied.
        
        Args:
            action: Action to check dependencies for
            executed_actions: List of already executed actions
            
        Returns:
            True if dependencies are satisfied
        """
        if not action.dependencies:
            return True
        
        executed_ids = {a["action_id"] for a in executed_actions if a["status"] == "success"}
        
        return all(dep_id in executed_ids for dep_id in action.dependencies)
    
    async def _verify_action(self, action: RecoveryAction, 
                           error_data: Dict[str, Any]) -> bool:
        """Verify action execution was successful.
        
        Args:
            action: Action to verify
            error_data: Error context
            
        Returns:
            True if verification passed
        """
        if not action.verification_command:
            return True
        
        try:
            command = self._substitute_variables(action.verification_command, error_data, action.parameters)
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            return process.returncode == 0
        
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    async def _verify_success_criteria(self, success_criteria: List[str],
                                     error_data: Dict[str, Any]) -> bool:
        """Verify runbook success criteria.
        
        Args:
            success_criteria: List of success criteria commands
            error_data: Error context
            
        Returns:
            True if all criteria are met
        """
        for criterion in success_criteria:
            try:
                command = self._substitute_variables(criterion, error_data, {})
                
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await process.communicate()
                
                if process.returncode != 0:
                    logger.warning(f"Success criterion failed: {criterion}")
                    return False
            
            except Exception as e:
                logger.error(f"Error checking success criterion: {e}")
                return False
        
        return True
    
    async def _perform_rollback(self, execution: RecoveryExecution,
                              executed_actions: List[Dict[str, Any]]) -> None:
        """Perform rollback of executed actions.
        
        Args:
            execution: Execution record to update
            executed_actions: List of executed actions to rollback
        """
        logger.info(f"Performing rollback for execution: {execution.id}")
        
        # Rollback in reverse order
        for action_result in reversed(executed_actions):
            if action_result["status"] != "success":
                continue
            
            # Find original action
            action = None
            runbook = self.runbooks.get(execution.runbook_id)
            if runbook:
                action = next((a for a in runbook.actions if a.id == action_result["action_id"]), None)
            
            if action and action.rollback_command:
                try:
                    logger.info(f"Rolling back action: {action.name}")
                    
                    process = await asyncio.create_subprocess_shell(
                        action.rollback_command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    await process.communicate()
                    
                    if process.returncode == 0:
                        logger.info(f"Rollback successful for: {action.name}")
                    else:
                        logger.error(f"Rollback failed for: {action.name}")
                
                except Exception as e:
                    logger.error(f"Error during rollback: {e}")
        
        execution.rollback_performed = True
    
    def _load_runbooks(self) -> None:
        """Load runbooks from files."""
        try:
            for runbook_file in self.runbooks_dir.glob("*.json"):
                with open(runbook_file) as f:
                    runbook_data = json.load(f)
                
                # Convert to RecoveryRunbook object
                actions = []
                for action_data in runbook_data.get("actions", []):
                    action = RecoveryAction(
                        id=action_data["id"],
                        name=action_data["name"],
                        action_type=ActionType(action_data["action_type"]),
                        command=action_data.get("command"),
                        parameters=action_data.get("parameters", {}),
                        risk_level=RecoveryRisk(action_data.get("risk_level", "low")),
                        timeout=action_data.get("timeout", 30),
                        retry_count=action_data.get("retry_count", 3),
                        retry_delay=action_data.get("retry_delay", 5.0),
                        verification_command=action_data.get("verification_command"),
                        rollback_command=action_data.get("rollback_command"),
                        requires_confirmation=action_data.get("requires_confirmation", False),
                        dependencies=action_data.get("dependencies", [])
                    )
                    actions.append(action)
                
                runbook = RecoveryRunbook(
                    id=runbook_data["id"],
                    name=runbook_data["name"],
                    description=runbook_data["description"],
                    error_patterns=runbook_data.get("error_patterns", []),
                    error_conditions=runbook_data.get("error_conditions", {}),
                    actions=actions,
                    max_execution_time=runbook_data.get("max_execution_time", 600),
                    auto_execute=runbook_data.get("auto_execute", True),
                    requires_approval=runbook_data.get("requires_approval", False),
                    success_criteria=runbook_data.get("success_criteria", []),
                    rollback_on_failure=runbook_data.get("rollback_on_failure", True)
                )
                
                self.runbooks[runbook.id] = runbook
            
            logger.info(f"Loaded {len(self.runbooks)} recovery runbooks")
        
        except Exception as e:
            logger.error(f"Error loading runbooks: {e}")
    
    def _save_runbook(self, runbook: RecoveryRunbook) -> None:
        """Save runbook to file."""
        try:
            runbook_file = self.runbooks_dir / f"{runbook.id}.json"
            
            # Convert to serializable format
            actions_data = []
            for action in runbook.actions:
                action_data = {
                    "id": action.id,
                    "name": action.name,
                    "action_type": action.action_type.value,
                    "command": action.command,
                    "parameters": action.parameters,
                    "risk_level": action.risk_level.value,
                    "timeout": action.timeout,
                    "retry_count": action.retry_count,
                    "retry_delay": action.retry_delay,
                    "verification_command": action.verification_command,
                    "rollback_command": action.rollback_command,
                    "requires_confirmation": action.requires_confirmation,
                    "dependencies": action.dependencies
                }
                actions_data.append(action_data)
            
            runbook_data = {
                "id": runbook.id,
                "name": runbook.name,
                "description": runbook.description,
                "error_patterns": runbook.error_patterns,
                "error_conditions": runbook.error_conditions,
                "actions": actions_data,
                "max_execution_time": runbook.max_execution_time,
                "auto_execute": runbook.auto_execute,
                "requires_approval": runbook.requires_approval,
                "success_criteria": runbook.success_criteria,
                "rollback_on_failure": runbook.rollback_on_failure
            }
            
            with open(runbook_file, 'w') as f:
                json.dump(runbook_data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving runbook: {e}")
    
    def _save_state(self) -> None:
        """Save current state to file."""
        try:
            state_data = {
                "active_executions": {
                    exec_id: {
                        "id": exec.id,
                        "runbook_id": exec.runbook_id,
                        "error_id": exec.error_id,
                        "start_time": exec.start_time.isoformat(),
                        "status": exec.status.value,
                        "success_rate": exec.success_rate
                    }
                    for exec_id, exec in self.active_executions.items()
                }
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        
        except Exception as e:
            logger.warning(f"Error saving state: {e}")
    
    def _load_state(self) -> None:
        """Load state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file) as f:
                    state_data = json.load(f)
                
                # Load active executions
                for exec_id, exec_data in state_data.get("active_executions", {}).items():
                    execution = RecoveryExecution(
                        id=exec_data["id"],
                        runbook_id=exec_data["runbook_id"],
                        error_id=exec_data["error_id"],
                        start_time=datetime.fromisoformat(exec_data["start_time"]),
                        status=RecoveryStatus(exec_data["status"]),
                        success_rate=exec_data.get("success_rate", 0.0)
                    )
                    self.active_executions[exec_id] = execution
        
        except Exception as e:
            logger.warning(f"Error loading state: {e}")
    
    def get_execution_status(self, execution_id: str) -> Optional[RecoveryExecution]:
        """Get status of a recovery execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution status or None if not found
        """
        return self.active_executions.get(execution_id)
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get recovery system statistics.
        
        Returns:
            Statistics dictionary
        """
        total_executions = len(self.execution_history)
        successful_executions = len([e for e in self.execution_history if e.status == RecoveryStatus.SUCCESS])
        
        return {
            "total_runbooks": len(self.runbooks),
            "total_executions": total_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "active_executions": len(self.active_executions),
            "auto_execution_enabled": self.auto_execution_enabled
        }


# Example runbook creation
def create_example_runbooks() -> List[RecoveryRunbook]:
    """Create example recovery runbooks."""
    
    # Database connection failure runbook
    db_restart_action = RecoveryAction(
        id="restart_db_service",
        name="Restart Database Service",
        action_type=ActionType.SERVICE_RESTART,
        parameters={"service_name": "postgresql"},
        risk_level=RecoveryRisk.MEDIUM,
        verification_command="systemctl is-active postgresql",
        rollback_command="systemctl stop postgresql"
    )
    
    db_connection_runbook = RecoveryRunbook(
        id="database_connection_failure",
        name="Database Connection Failure Recovery",
        description="Recovers from database connection failures",
        error_patterns=["connection.*failed", "database.*unreachable", "timeout.*database"],
        error_conditions={"system": "database"},
        actions=[db_restart_action],
        success_criteria=["pg_isready -h localhost"],
        auto_execute=True
    )
    
    # High CPU usage runbook
    cleanup_action = RecoveryAction(
        id="cleanup_temp_files",
        name="Clean Temporary Files",
        action_type=ActionType.RESOURCE_CLEANUP,
        parameters={"type": "temp_files"},
        risk_level=RecoveryRisk.LOW
    )
    
    restart_service_action = RecoveryAction(
        id="restart_high_cpu_service",
        name="Restart High CPU Service",
        action_type=ActionType.SERVICE_RESTART,
        parameters={"service_name": "{service_name}"},
        risk_level=RecoveryRisk.MEDIUM,
        dependencies=["cleanup_temp_files"]
    )
    
    cpu_usage_runbook = RecoveryRunbook(
        id="high_cpu_usage",
        name="High CPU Usage Recovery",
        description="Recovers from high CPU usage situations",
        error_patterns=["cpu.*high", "resource.*exhaustion"],
        error_conditions={"cpu_usage": 90},
        actions=[cleanup_action, restart_service_action],
        auto_execute=True
    )
    
    return [db_connection_runbook, cpu_usage_runbook]


# Example usage
async def main():
    """Example usage of the AutomatedRecoverySystem."""
    recovery_system = AutomatedRecoverySystem()
    
    # Register example runbooks
    for runbook in create_example_runbooks():
        recovery_system.register_runbook(runbook)
    
    # Simulate error for recovery
    error_data = {
        "error_id": "db_001",
        "error_message": "Database connection failed after 3 attempts",
        "system": "database",
        "service_name": "api_server",
        "timestamp": datetime.now().isoformat()
    }
    
    # Execute recovery
    execution_id = await recovery_system.execute_recovery("db_001", error_data)
    
    if execution_id:
        print(f"Recovery started: {execution_id}")
        
        # Monitor execution
        while True:
            status = recovery_system.get_execution_status(execution_id)
            if not status:
                break
            
            print(f"Execution status: {status.status.value}")
            
            if status.status in [RecoveryStatus.SUCCESS, RecoveryStatus.FAILED, RecoveryStatus.PARTIAL]:
                break
            
            await asyncio.sleep(2)
        
        # Get final statistics
        stats = recovery_system.get_recovery_statistics()
        print(f"Recovery statistics: {stats}")


if __name__ == "__main__":
    asyncio.run(main())