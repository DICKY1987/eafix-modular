"""
Dependency-Aware Execution Scheduler (MOD-006)
Execute phases in parallel where possible while respecting depends_on; surface readiness on the bus.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Set, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, deque
import networkx as nx

logger = logging.getLogger(__name__)

class PhaseStatus(Enum):
    """Phase execution status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"

@dataclass
class Phase:
    """Represents a workflow phase."""
    phase_id: str
    name: str
    description: str = ""
    dependencies: List[str] = None
    tools: List[str] = None
    timeout_seconds: int = 300
    retry_count: int = 3
    critical: bool = False
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tools is None:
            self.tools = []

@dataclass 
class PhaseExecution:
    """Represents the execution state of a phase."""
    phase: Phase
    status: PhaseStatus = PhaseStatus.PENDING
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: float = 0.0
    attempts: int = 0
    error_message: Optional[str] = None
    result_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.result_data is None:
            self.result_data = {}

class DependencyAwareScheduler:
    """Schedules and executes phases based on dependency graph."""
    
    def __init__(self, event_bus_callback: Optional[Callable] = None):
        self.phases: Dict[str, Phase] = {}
        self.executions: Dict[str, PhaseExecution] = {}
        self.dependency_graph = nx.DiGraph()
        self.event_bus_callback = event_bus_callback
        self.execution_tasks: Dict[str, asyncio.Task] = {}
        
        # Deadlock detection
        self.max_deadlock_wait_seconds = 300  # 5 minutes
        
    def add_phase(self, phase: Phase) -> None:
        """Add a phase to the scheduler."""
        self.phases[phase.phase_id] = phase
        self.executions[phase.phase_id] = PhaseExecution(phase=phase)
        
        # Add to dependency graph
        self.dependency_graph.add_node(phase.phase_id)
        for dep in phase.dependencies:
            self.dependency_graph.add_edge(dep, phase.phase_id)
        
        logger.info(f"Added phase: {phase.phase_id} (deps: {phase.dependencies})")
    
    def add_phases(self, phases: List[Phase]) -> None:
        """Add multiple phases at once."""
        for phase in phases:
            self.add_phase(phase)
    
    def validate_dependencies(self) -> Dict[str, Any]:
        """Validate the dependency graph for cycles and missing dependencies."""
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            if cycles:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Circular dependencies detected: {cycles}")
        except nx.NetworkXError as e:
            validation_result['errors'].append(f"Graph validation error: {str(e)}")
        
        # Check for missing dependencies
        for phase_id, phase in self.phases.items():
            for dep in phase.dependencies:
                if dep not in self.phases:
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Phase {phase_id} depends on unknown phase: {dep}")
        
        # Check for orphaned phases (no path from any root)
        try:
            roots = [n for n in self.dependency_graph.nodes() if self.dependency_graph.in_degree(n) == 0]
            if not roots:
                validation_result['warnings'].append("No root phases found (all phases have dependencies)")
            else:
                reachable = set()
                for root in roots:
                    reachable.update(nx.descendants(self.dependency_graph, root))
                    reachable.add(root)
                
                orphaned = set(self.dependency_graph.nodes()) - reachable
                if orphaned:
                    validation_result['warnings'].append(f"Unreachable phases: {list(orphaned)}")
                    
        except Exception as e:
            validation_result['warnings'].append(f"Reachability check failed: {str(e)}")
        
        return validation_result
    
    def get_ready_phases(self) -> List[str]:
        """Get phases that are ready to execute (dependencies satisfied)."""
        
        ready_phases = []
        
        for phase_id, execution in self.executions.items():
            if execution.status == PhaseStatus.PENDING:
                # Check if all dependencies are completed
                phase = execution.phase
                deps_satisfied = all(
                    self.executions.get(dep_id, {}).status == PhaseStatus.COMPLETED
                    for dep_id in phase.dependencies
                )
                
                if deps_satisfied:
                    ready_phases.append(phase_id)
                    # Update status to ready
                    execution.status = PhaseStatus.READY
        
        return ready_phases
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit event to event bus if callback is provided."""
        if self.event_bus_callback:
            try:
                event = {
                    'event_type': event_type,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'data': data
                }
                self.event_bus_callback(event)
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
    
    async def _execute_phase(self, phase_id: str, executor_func: Callable) -> Dict[str, Any]:
        """Execute a single phase."""
        
        execution = self.executions[phase_id]
        phase = execution.phase
        
        execution.status = PhaseStatus.RUNNING
        execution.start_time = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Starting phase execution: {phase_id}")
        
        # Emit phase started event
        self._emit_event('phase_started', {
            'phase_id': phase_id,
            'phase_name': phase.name,
            'dependencies': phase.dependencies,
            'tools': phase.tools
        })
        
        try:
            # Execute phase with timeout and retries
            for attempt in range(phase.retry_count + 1):
                execution.attempts = attempt + 1
                
                try:
                    # Call the executor function with timeout
                    result = await asyncio.wait_for(
                        executor_func(phase),
                        timeout=phase.timeout_seconds
                    )
                    
                    # Success - update execution state
                    execution.status = PhaseStatus.COMPLETED
                    execution.end_time = datetime.now(timezone.utc).isoformat()
                    execution.duration_seconds = time.time() - time.mktime(
                        datetime.fromisoformat(execution.start_time.replace('Z', '+00:00')).timetuple()
                    )
                    execution.result_data = result or {}
                    
                    logger.info(f"✅ Phase {phase_id} completed successfully (attempt {attempt + 1})")
                    
                    # Emit phase completed event
                    self._emit_event('phase_completed', {
                        'phase_id': phase_id,
                        'phase_name': phase.name,
                        'status': 'completed',
                        'duration_seconds': execution.duration_seconds,
                        'attempts': execution.attempts,
                        'result': execution.result_data
                    })
                    
                    return execution.result_data
                    
                except asyncio.TimeoutError:
                    error_msg = f"Phase {phase_id} timed out after {phase.timeout_seconds} seconds"
                    logger.warning(f"⏰ {error_msg} (attempt {attempt + 1})")
                    
                    if attempt == phase.retry_count:  # Last attempt
                        execution.status = PhaseStatus.TIMEOUT
                        execution.error_message = error_msg
                        break
                    else:
                        # Wait before retry
                        await asyncio.sleep(min(2 ** attempt, 10))  # Exponential backoff, max 10s
                
                except Exception as e:
                    error_msg = f"Phase {phase_id} failed: {str(e)}"
                    logger.warning(f"❌ {error_msg} (attempt {attempt + 1})")
                    
                    if attempt == phase.retry_count:  # Last attempt
                        execution.status = PhaseStatus.FAILED
                        execution.error_message = error_msg
                        break
                    else:
                        # Wait before retry
                        await asyncio.sleep(min(2 ** attempt, 10))  # Exponential backoff
        
        except Exception as e:
            # Unexpected error in retry loop
            execution.status = PhaseStatus.FAILED
            execution.error_message = f"Unexpected error in phase {phase_id}: {str(e)}"
            logger.error(execution.error_message)
        
        finally:
            # Ensure end time is set
            if not execution.end_time:
                execution.end_time = datetime.now(timezone.utc).isoformat()
            
            # Emit phase failed/timeout event
            if execution.status in [PhaseStatus.FAILED, PhaseStatus.TIMEOUT]:
                self._emit_event('phase_failed', {
                    'phase_id': phase_id,
                    'phase_name': phase.name,
                    'status': execution.status.value,
                    'error_message': execution.error_message,
                    'attempts': execution.attempts,
                    'duration_seconds': execution.duration_seconds
                })
        
        return execution.result_data
    
    async def execute_workflow(self, executor_func: Callable, 
                              max_parallel_phases: int = 5) -> Dict[str, Any]:
        """Execute all phases in dependency order with parallelization."""
        
        # Validate dependencies first
        validation = self.validate_dependencies()
        if not validation['valid']:
            return {
                'status': 'failed',
                'message': 'Dependency validation failed',
                'errors': validation['errors'],
                'validation': validation
            }
        
        logger.info(f"Starting workflow execution with {len(self.phases)} phases")
        
        # Emit workflow started event
        self._emit_event('workflow_started', {
            'total_phases': len(self.phases),
            'phases': [p.phase_id for p in self.phases.values()],
            'max_parallel': max_parallel_phases
        })
        
        start_time = time.time()
        completed_phases = 0
        failed_phases = 0
        
        try:
            # Main execution loop
            while completed_phases + failed_phases < len(self.phases):
                # Get phases ready to execute
                ready_phases = self.get_ready_phases()
                
                if not ready_phases and not self.execution_tasks:
                    # No ready phases and no running tasks - deadlock or completion
                    remaining_phases = [
                        p_id for p_id, exec in self.executions.items() 
                        if exec.status == PhaseStatus.PENDING
                    ]
                    
                    if remaining_phases:
                        # Deadlock detected
                        error_msg = f"Deadlock detected. Remaining phases: {remaining_phases}"
                        logger.error(error_msg)
                        
                        self._emit_event('workflow_failed', {
                            'error': 'deadlock',
                            'message': error_msg,
                            'remaining_phases': remaining_phases
                        })
                        
                        return {
                            'status': 'failed',
                            'message': error_msg,
                            'completed_phases': completed_phases,
                            'failed_phases': failed_phases,
                            'remaining_phases': remaining_phases
                        }
                    break  # All phases completed
                
                # Start new phases (up to parallel limit)
                available_slots = max_parallel_phases - len(self.execution_tasks)
                phases_to_start = ready_phases[:available_slots]
                
                for phase_id in phases_to_start:
                    task = asyncio.create_task(self._execute_phase(phase_id, executor_func))
                    self.execution_tasks[phase_id] = task
                    
                    # Update status
                    self.executions[phase_id].status = PhaseStatus.RUNNING
                
                # Wait for at least one task to complete
                if self.execution_tasks:
                    done_tasks, pending_tasks = await asyncio.wait(
                        self.execution_tasks.values(),
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Process completed tasks
                    for task in done_tasks:
                        # Find phase_id for this task
                        phase_id = None
                        for p_id, p_task in self.execution_tasks.items():
                            if p_task == task:
                                phase_id = p_id
                                break
                        
                        if phase_id:
                            # Remove from active tasks
                            del self.execution_tasks[phase_id]
                            
                            # Update counters
                            execution = self.executions[phase_id]
                            if execution.status == PhaseStatus.COMPLETED:
                                completed_phases += 1
                                logger.info(f"Phase {phase_id} completed ({completed_phases}/{len(self.phases)})")
                            else:
                                failed_phases += 1
                                logger.error(f"Phase {phase_id} failed ({failed_phases} total failures)")
                                
                                # Check if this was a critical phase
                                if execution.phase.critical:
                                    logger.error(f"Critical phase {phase_id} failed - stopping workflow")
                                    
                                    # Cancel remaining tasks
                                    for remaining_task in self.execution_tasks.values():
                                        remaining_task.cancel()
                                    
                                    self._emit_event('workflow_failed', {
                                        'error': 'critical_phase_failed',
                                        'failed_phase': phase_id,
                                        'message': f"Critical phase {phase_id} failed"
                                    })
                                    
                                    return {
                                        'status': 'failed',
                                        'message': f'Critical phase {phase_id} failed',
                                        'completed_phases': completed_phases,
                                        'failed_phases': failed_phases
                                    }
                
                # Emit progress update
                progress_percent = (completed_phases + failed_phases) / len(self.phases) * 100
                self._emit_event('workflow_progress', {
                    'completed_phases': completed_phases,
                    'failed_phases': failed_phases,
                    'total_phases': len(self.phases),
                    'progress_percent': round(progress_percent, 1),
                    'running_phases': len(self.execution_tasks)
                })
        
        except Exception as e:
            error_msg = f"Workflow execution error: {str(e)}"
            logger.error(error_msg)
            
            self._emit_event('workflow_failed', {
                'error': 'execution_error',
                'message': error_msg
            })
            
            return {
                'status': 'failed', 
                'message': error_msg,
                'completed_phases': completed_phases,
                'failed_phases': failed_phases
            }
        
        # Workflow completed
        total_duration = time.time() - start_time
        
        if failed_phases == 0:
            status = 'completed'
            message = f'All {len(self.phases)} phases completed successfully'
            logger.info(f"✅ Workflow completed successfully in {total_duration:.1f}s")
        else:
            status = 'completed_with_failures'
            message = f'{completed_phases} phases completed, {failed_phases} phases failed'
            logger.warning(f"⚠️ Workflow completed with failures in {total_duration:.1f}s")
        
        self._emit_event('workflow_completed', {
            'status': status,
            'completed_phases': completed_phases,
            'failed_phases': failed_phases,
            'total_phases': len(self.phases),
            'duration_seconds': total_duration
        })
        
        return {
            'status': status,
            'message': message,
            'completed_phases': completed_phases,
            'failed_phases': failed_phases,
            'total_phases': len(self.phases),
            'duration_seconds': total_duration,
            'execution_summary': {
                phase_id: {
                    'status': exec.status.value,
                    'duration': exec.duration_seconds,
                    'attempts': exec.attempts,
                    'error': exec.error_message
                }
                for phase_id, exec in self.executions.items()
            }
        }
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status of all phases."""
        
        status_counts = defaultdict(int)
        phase_statuses = {}
        
        for phase_id, execution in self.executions.items():
            status = execution.status.value
            status_counts[status] += 1
            
            phase_statuses[phase_id] = {
                'status': status,
                'phase_name': execution.phase.name,
                'dependencies': execution.phase.dependencies,
                'start_time': execution.start_time,
                'end_time': execution.end_time,
                'duration_seconds': execution.duration_seconds,
                'attempts': execution.attempts,
                'error_message': execution.error_message
            }
        
        return {
            'total_phases': len(self.phases),
            'status_counts': dict(status_counts),
            'phase_statuses': phase_statuses,
            'active_tasks': len(self.execution_tasks)
        }

def main():
    """CLI interface for the scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dependency-Aware Execution Scheduler")
    parser.add_argument("command", choices=["validate", "status"], help="Command to run")
    parser.add_argument("--phases-file", help="JSON file containing phase definitions")
    
    args = parser.parse_args()
    
    scheduler = DependencyAwareScheduler()
    
    # Load phases if file provided
    if args.phases_file:
        try:
            with open(args.phases_file, 'r') as f:
                phases_data = json.load(f)
                
            phases = []
            for phase_data in phases_data:
                phase = Phase(**phase_data)
                phases.append(phase)
            
            scheduler.add_phases(phases)
        except Exception as e:
            print(f"Error loading phases file: {e}", file=sys.stderr)
            sys.exit(1)
    
    if args.command == "validate":
        validation = scheduler.validate_dependencies()
        print(json.dumps(validation, indent=2))
        sys.exit(0 if validation['valid'] else 1)
        
    elif args.command == "status":
        status = scheduler.get_execution_status()
        print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()