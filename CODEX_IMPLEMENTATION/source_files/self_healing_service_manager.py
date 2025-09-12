#!/usr/bin/env python3
"""
Self-Healing Service Manager
============================

Automatic service restart, recovery, and health management system.
Provides intelligent service lifecycle management with automatic failure recovery.
"""

import asyncio
import psutil
import subprocess
import time
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
import signal
import os

logger = logging.getLogger(__name__)


class ServiceState(Enum):
    """Service states."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    RECOVERING = "recovering"


class RestartPolicy(Enum):
    """Service restart policies."""
    NEVER = "never"
    ON_FAILURE = "on_failure"
    ALWAYS = "always"
    UNLESS_STOPPED = "unless_stopped"


@dataclass
class ServiceDefinition:
    """Service definition with configuration."""
    name: str
    command: List[str]
    working_dir: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    restart_policy: RestartPolicy = RestartPolicy.ON_FAILURE
    max_restarts: int = 5
    restart_delay: float = 5.0
    health_check: Optional[Callable] = None
    health_check_interval: float = 30.0
    health_check_timeout: float = 10.0
    health_check_retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    graceful_shutdown_timeout: float = 30.0
    required_resources: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceStatus:
    """Current service status."""
    name: str
    state: ServiceState
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    exit_code: Optional[int] = None
    error_message: Optional[str] = None


class SelfHealingServiceManager:
    """Manages services with automatic restart and healing capabilities."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """Initialize service manager.
        
        Args:
            config_file: Path to service configuration file
        """
        self.services: Dict[str, ServiceDefinition] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Configuration
        self.config_file = config_file or Path("service_config.json")
        self.state_file = Path("service_state.json")
        
        # Recovery settings
        self.global_restart_limit = 10
        self.global_restart_window = timedelta(hours=1)
        self.restart_history: Dict[str, List[datetime]] = {}
        
        logger.info("SelfHealingServiceManager initialized")
    
    def register_service(self, service: ServiceDefinition) -> None:
        """Register a service for management.
        
        Args:
            service: Service definition to register
        """
        self.services[service.name] = service
        self.service_status[service.name] = ServiceStatus(
            name=service.name,
            state=ServiceState.STOPPED
        )
        self.restart_history[service.name] = []
        
        logger.info(f"Registered service: {service.name}")
    
    async def start_service(self, service_name: str) -> bool:
        """Start a specific service.
        
        Args:
            service_name: Name of service to start
            
        Returns:
            True if service started successfully
        """
        if service_name not in self.services:
            logger.error(f"Service not found: {service_name}")
            return False
        
        service = self.services[service_name]
        status = self.service_status[service_name]
        
        if status.state in [ServiceState.RUNNING, ServiceState.STARTING]:
            logger.warning(f"Service {service_name} already running/starting")
            return True
        
        # Check dependencies
        for dep in service.dependencies:
            if dep not in self.service_status:
                logger.error(f"Dependency {dep} not registered for {service_name}")
                return False
            
            dep_status = self.service_status[dep]
            if dep_status.state != ServiceState.RUNNING:
                logger.error(f"Dependency {dep} not running for {service_name}")
                return False
        
        # Check resource requirements
        if not self._check_resource_requirements(service):
            logger.error(f"Resource requirements not met for {service_name}")
            return False
        
        try:
            status.state = ServiceState.STARTING
            
            # Prepare environment
            env = os.environ.copy()
            env.update(service.environment)
            
            # Start process
            process = subprocess.Popen(
                service.command,
                cwd=service.working_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            self.processes[service_name] = process
            status.pid = process.pid
            status.start_time = datetime.now()
            status.state = ServiceState.RUNNING
            status.error_message = None
            
            logger.info(f"Started service {service_name} (PID: {process.pid})")
            
            # Save state
            self._save_state()
            
            return True
            
        except Exception as e:
            status.state = ServiceState.FAILED
            status.error_message = str(e)
            logger.error(f"Failed to start service {service_name}: {e}")
            return False
    
    async def stop_service(self, service_name: str, graceful: bool = True) -> bool:
        """Stop a specific service.
        
        Args:
            service_name: Name of service to stop
            graceful: Whether to attempt graceful shutdown
            
        Returns:
            True if service stopped successfully
        """
        if service_name not in self.services:
            logger.error(f"Service not found: {service_name}")
            return False
        
        service = self.services[service_name]
        status = self.service_status[service_name]
        
        if status.state != ServiceState.RUNNING:
            logger.warning(f"Service {service_name} not running")
            return True
        
        try:
            status.state = ServiceState.STOPPING
            process = self.processes.get(service_name)
            
            if not process:
                status.state = ServiceState.STOPPED
                return True
            
            if graceful:
                # Try graceful shutdown first
                if hasattr(signal, 'SIGTERM'):
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                
                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(
                        self._wait_for_process_exit(process),
                        timeout=service.graceful_shutdown_timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Graceful shutdown timeout for {service_name}, forcing")
                    if hasattr(signal, 'SIGKILL'):
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    else:
                        process.kill()
            else:
                # Force shutdown
                if hasattr(signal, 'SIGKILL'):
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
            
            # Clean up
            if service_name in self.processes:
                del self.processes[service_name]
            
            status.state = ServiceState.STOPPED
            status.pid = None
            status.exit_code = process.returncode
            
            logger.info(f"Stopped service {service_name}")
            self._save_state()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop service {service_name}: {e}")
            return False
    
    async def restart_service(self, service_name: str, reason: str = "manual") -> bool:
        """Restart a service with restart limit checking.
        
        Args:
            service_name: Name of service to restart
            reason: Reason for restart (for logging)
            
        Returns:
            True if service restarted successfully
        """
        if service_name not in self.services:
            logger.error(f"Service not found: {service_name}")
            return False
        
        service = self.services[service_name]
        status = self.service_status[service_name]
        
        # Check restart limits
        if not self._can_restart_service(service_name):
            logger.error(f"Restart limit exceeded for {service_name}")
            status.state = ServiceState.FAILED
            return False
        
        logger.info(f"Restarting service {service_name} (reason: {reason})")
        
        # Record restart
        now = datetime.now()
        self.restart_history[service_name].append(now)
        status.restart_count += 1
        status.last_restart = now
        status.state = ServiceState.RECOVERING
        
        # Stop service
        await self.stop_service(service_name, graceful=True)
        
        # Wait before restart
        await asyncio.sleep(service.restart_delay)
        
        # Start service
        success = await self.start_service(service_name)
        
        if success:
            logger.info(f"Successfully restarted service {service_name}")
        else:
            logger.error(f"Failed to restart service {service_name}")
            status.state = ServiceState.FAILED
        
        return success
    
    async def start_monitoring(self) -> None:
        """Start service monitoring loop."""
        if self.running:
            logger.warning("Monitoring already running")
            return
        
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Started service monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop service monitoring loop."""
        if not self.running:
            return
        
        self.running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped service monitoring")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.running:
            try:
                # Check all services
                for service_name in list(self.services.keys()):
                    await self._check_service_health(service_name)
                
                # Clean up old restart history
                self._cleanup_restart_history()
                
                # Save state periodically
                self._save_state()
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _check_service_health(self, service_name: str) -> None:
        """Check health of a specific service.
        
        Args:
            service_name: Name of service to check
        """
        if service_name not in self.services:
            return
        
        service = self.services[service_name]
        status = self.service_status[service_name]
        
        # Check if process is still running
        process = self.processes.get(service_name)
        
        if status.state == ServiceState.RUNNING:
            if not process or process.poll() is not None:
                # Process died
                exit_code = process.returncode if process else None
                logger.warning(f"Service {service_name} died unexpectedly (exit code: {exit_code})")
                
                status.state = ServiceState.FAILED
                status.exit_code = exit_code
                
                # Handle restart policy
                if service.restart_policy in [RestartPolicy.ALWAYS, RestartPolicy.ON_FAILURE]:
                    await self.restart_service(service_name, reason="process_died")
                
                return
            
            # Update resource usage
            try:
                proc = psutil.Process(process.pid)
                status.cpu_usage = proc.cpu_percent()
                status.memory_usage = proc.memory_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            # Run health check if configured
            if service.health_check and status.last_health_check:
                time_since_check = datetime.now() - status.last_health_check
                if time_since_check.total_seconds() >= service.health_check_interval:
                    await self._run_health_check(service_name)
            elif service.health_check and not status.last_health_check:
                await self._run_health_check(service_name)
    
    async def _run_health_check(self, service_name: str) -> None:
        """Run health check for a service.
        
        Args:
            service_name: Name of service to check
        """
        service = self.services[service_name]
        status = self.service_status[service_name]
        
        if not service.health_check:
            return
        
        try:
            # Run health check with timeout
            health_result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, service.health_check
                ),
                timeout=service.health_check_timeout
            )
            
            status.last_health_check = datetime.now()
            
            if health_result:
                status.health_status = "healthy"
            else:
                status.health_status = "unhealthy"
                logger.warning(f"Health check failed for {service_name}")
                
                # Consider restart if consistently failing
                if service.restart_policy != RestartPolicy.NEVER:
                    await self.restart_service(service_name, reason="health_check_failed")
        
        except asyncio.TimeoutError:
            status.health_status = "timeout"
            logger.warning(f"Health check timeout for {service_name}")
        
        except Exception as e:
            status.health_status = "error"
            logger.error(f"Health check error for {service_name}: {e}")
    
    def _can_restart_service(self, service_name: str) -> bool:
        """Check if service can be restarted based on limits.
        
        Args:
            service_name: Name of service to check
            
        Returns:
            True if service can be restarted
        """
        service = self.services[service_name]
        status = self.service_status[service_name]
        
        # Check service-specific restart limit
        if status.restart_count >= service.max_restarts:
            return False
        
        # Check global restart limit within time window
        now = datetime.now()
        recent_restarts = [
            restart_time for restart_time in self.restart_history[service_name]
            if now - restart_time <= self.global_restart_window
        ]
        
        return len(recent_restarts) < self.global_restart_limit
    
    def _check_resource_requirements(self, service: ServiceDefinition) -> bool:
        """Check if resource requirements are met.
        
        Args:
            service: Service definition to check
            
        Returns:
            True if requirements are met
        """
        if not service.required_resources:
            return True
        
        # Check memory requirement
        if "memory_mb" in service.required_resources:
            required_memory = service.required_resources["memory_mb"]
            available_memory = psutil.virtual_memory().available / (1024 * 1024)
            if available_memory < required_memory:
                return False
        
        # Check CPU requirement
        if "cpu_percent" in service.required_resources:
            required_cpu = service.required_resources["cpu_percent"]
            cpu_usage = psutil.cpu_percent(interval=1)
            available_cpu = 100 - cpu_usage
            if available_cpu < required_cpu:
                return False
        
        # Check disk space requirement
        if "disk_mb" in service.required_resources:
            required_disk = service.required_resources["disk_mb"]
            disk_usage = psutil.disk_usage('/')
            available_disk = disk_usage.free / (1024 * 1024)
            if available_disk < required_disk:
                return False
        
        return True
    
    def _cleanup_restart_history(self) -> None:
        """Clean up old restart history entries."""
        cutoff = datetime.now() - self.global_restart_window
        
        for service_name in self.restart_history:
            self.restart_history[service_name] = [
                restart_time for restart_time in self.restart_history[service_name]
                if restart_time > cutoff
            ]
    
    async def _wait_for_process_exit(self, process: subprocess.Popen) -> None:
        """Wait for process to exit asynchronously.
        
        Args:
            process: Process to wait for
        """
        while process.poll() is None:
            await asyncio.sleep(0.1)
    
    def _save_state(self) -> None:
        """Save service state to file."""
        try:
            state_data = {
                "services": {
                    name: {
                        "state": status.state.value,
                        "pid": status.pid,
                        "start_time": status.start_time.isoformat() if status.start_time else None,
                        "restart_count": status.restart_count,
                        "last_restart": status.last_restart.isoformat() if status.last_restart else None,
                        "health_status": status.health_status,
                        "cpu_usage": status.cpu_usage,
                        "memory_usage": status.memory_usage,
                        "exit_code": status.exit_code,
                        "error_message": status.error_message
                    }
                    for name, status in self.service_status.items()
                },
                "restart_history": {
                    name: [t.isoformat() for t in times]
                    for name, times in self.restart_history.items()
                }
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")
    
    def _load_state(self) -> None:
        """Load service state from file."""
        try:
            if not self.state_file.exists():
                return
            
            with open(self.state_file, 'r') as f:
                state_data = json.load(f)
            
            # Restore service status
            for name, status_data in state_data.get("services", {}).items():
                if name in self.service_status:
                    status = self.service_status[name]
                    status.state = ServiceState(status_data["state"])
                    status.pid = status_data.get("pid")
                    status.start_time = datetime.fromisoformat(status_data["start_time"]) if status_data.get("start_time") else None
                    status.restart_count = status_data.get("restart_count", 0)
                    status.last_restart = datetime.fromisoformat(status_data["last_restart"]) if status_data.get("last_restart") else None
                    status.health_status = status_data.get("health_status", "unknown")
                    status.cpu_usage = status_data.get("cpu_usage", 0.0)
                    status.memory_usage = status_data.get("memory_usage", 0.0)
                    status.exit_code = status_data.get("exit_code")
                    status.error_message = status_data.get("error_message")
            
            # Restore restart history
            for name, times in state_data.get("restart_history", {}).items():
                if name in self.restart_history:
                    self.restart_history[name] = [datetime.fromisoformat(t) for t in times]
        
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
    
    def get_service_status(self, service_name: str) -> Optional[ServiceStatus]:
        """Get status of a specific service.
        
        Args:
            service_name: Name of service
            
        Returns:
            Service status or None if not found
        """
        return self.service_status.get(service_name)
    
    def get_all_services_status(self) -> Dict[str, ServiceStatus]:
        """Get status of all services.
        
        Returns:
            Dictionary of service statuses
        """
        return self.service_status.copy()
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary.
        
        Returns:
            System health summary
        """
        total_services = len(self.services)
        running_services = len([s for s in self.service_status.values() if s.state == ServiceState.RUNNING])
        failed_services = len([s for s in self.service_status.values() if s.state == ServiceState.FAILED])
        
        return {
            "total_services": total_services,
            "running_services": running_services,
            "failed_services": failed_services,
            "overall_health": "healthy" if failed_services == 0 else "degraded" if running_services > 0 else "critical",
            "uptime_percentage": (running_services / total_services * 100) if total_services > 0 else 100
        }


# Example usage and service definitions
async def main():
    """Example usage of the SelfHealingServiceManager."""
    manager = SelfHealingServiceManager()
    
    # Example health check function
    def api_health_check() -> bool:
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    # Register services
    api_service = ServiceDefinition(
        name="api_server",
        command=["python", "server.py"],
        working_dir="/path/to/api",
        restart_policy=RestartPolicy.ALWAYS,
        max_restarts=10,
        health_check=api_health_check,
        health_check_interval=30.0,
        required_resources={"memory_mb": 512, "cpu_percent": 10}
    )
    
    worker_service = ServiceDefinition(
        name="background_worker",
        command=["python", "worker.py"],
        working_dir="/path/to/worker",
        restart_policy=RestartPolicy.ON_FAILURE,
        dependencies=["api_server"]
    )
    
    manager.register_service(api_service)
    manager.register_service(worker_service)
    
    # Start services
    await manager.start_service("api_server")
    await manager.start_service("background_worker")
    
    # Start monitoring
    await manager.start_monitoring()
    
    try:
        # Keep running
        while True:
            status = manager.get_system_health_summary()
            print(f"System Health: {status}")
            await asyncio.sleep(30)
    
    except KeyboardInterrupt:
        await manager.stop_monitoring()
        
        # Stop all services
        for service_name in manager.services:
            await manager.stop_service(service_name)


if __name__ == "__main__":
    asyncio.run(main())