"""
Flow Orchestrator Core

Implements runtime flow orchestration for event-driven data pipelines,
coordinating data flows between EAFIX services and managing execution state.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

import redis.asyncio as redis
import httpx
import structlog

logger = structlog.get_logger(__name__)


class FlowStatus(Enum):
    """Flow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class StepStatus(Enum):
    """Flow step execution status.""" 
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"


@dataclass
class FlowStepExecution:
    """Individual flow step execution state."""
    
    step_id: str
    service_name: str
    action: str
    status: StepStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    retry_count: int = 0
    output_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data


@dataclass 
class FlowExecution:
    """Complete flow execution state."""
    
    flow_id: str
    flow_name: str
    trigger_event: Optional[str]
    trigger_data: Optional[Dict[str, Any]]
    status: FlowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    steps: List[FlowStepExecution] = None
    error: Optional[str] = None
    success_rate: float = 0.0
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        data['steps'] = [step.to_dict() for step in self.steps]
        return data


class CircuitBreaker:
    """Circuit breaker for service calls."""
    
    def __init__(self, failure_threshold: int, timeout_seconds: int):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.is_open = False
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.is_open:
            if self._should_attempt_reset():
                logger.info("Circuit breaker attempting reset")
                self.is_open = False
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.timeout_seconds
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.is_open = False
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(
                "Circuit breaker opened",
                failure_count=self.failure_count,
                threshold=self.failure_threshold
            )


class FlowOrchestrator:
    """Core flow orchestration engine."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # Redis client for event messaging
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        
        # HTTP client for service calls
        self.http_client: Optional[httpx.AsyncClient] = None
        
        # Active flow executions
        self.active_flows: Dict[str, FlowExecution] = {}
        self.flow_history: List[FlowExecution] = []
        self._flows_lock = asyncio.Lock()
        
        # Service circuit breakers
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Flow monitoring
        self.flow_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None
        
        self.running = False
    
    async def start(self) -> None:
        """Start the flow orchestrator."""
        if self.running:
            return
        
        logger.info("Starting Flow Orchestrator")
        
        # Initialize Redis connection
        self.redis_client = redis.from_url(self.settings.redis_url)
        await self.redis_client.ping()
        logger.info("Connected to Redis", url=self.settings.redis_url)
        
        # Initialize HTTP client
        timeout = httpx.Timeout(self.settings.service_timeout_seconds)
        self.http_client = httpx.AsyncClient(timeout=timeout)
        
        # Initialize circuit breakers for all services
        if self.settings.circuit_breaker_enabled:
            cb_config = self.settings.get_circuit_breaker_config()
            for service_name in self.settings.service_registry.keys():
                self.circuit_breakers[service_name] = CircuitBreaker(
                    cb_config["failure_threshold"],
                    cb_config["timeout_seconds"]
                )
        
        # Start background tasks
        if self.settings.flow_monitoring_enabled:
            self.monitoring_task = asyncio.create_task(self._run_flow_monitoring())
        
        self.health_check_task = asyncio.create_task(self._run_health_checks())
        
        # Subscribe to trigger events
        await self._setup_event_subscriptions()
        
        self.running = True
        logger.info("Flow Orchestrator started successfully")
    
    async def stop(self) -> None:
        """Stop the flow orchestrator."""
        if not self.running:
            return
        
        logger.info("Stopping Flow Orchestrator")
        
        # Cancel background tasks
        for task in [self.monitoring_task, self.health_check_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close pubsub
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        # Close HTTP client
        if self.http_client:
            await self.http_client.aclose()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        self.running = False
        logger.info("Flow Orchestrator stopped")
    
    async def _setup_event_subscriptions(self) -> None:
        """Setup Redis pub/sub subscriptions for flow triggers."""
        if not self.redis_client:
            return
        
        self.pubsub = self.redis_client.pubsub()
        
        # Subscribe to all event topics that can trigger flows
        trigger_topics = set()
        for flow_name, flow_def in self.settings.get_enabled_flows().items():
            trigger_events = flow_def.get("trigger_events", [])
            for event_type in trigger_events:
                if event_type != "periodic":  # Handle periodic separately
                    topics = self.settings.get_event_topics(event_type)
                    trigger_topics.update(topics)
        
        if trigger_topics:
            await self.pubsub.subscribe(*trigger_topics)
            logger.info("Subscribed to trigger topics", topics=list(trigger_topics))
            
            # Start message processing task
            asyncio.create_task(self._process_trigger_messages())
    
    async def _process_trigger_messages(self) -> None:
        """Process incoming trigger messages from Redis."""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        await self._handle_trigger_message(
                            message["channel"].decode(),
                            message["data"].decode()
                        )
                    except Exception as e:
                        logger.error(
                            "Error processing trigger message",
                            channel=message["channel"].decode(),
                            error=str(e)
                        )
                        
        except asyncio.CancelledError:
            logger.info("Trigger message processing cancelled")
        except Exception as e:
            logger.error("Trigger message processing failed", error=str(e))
    
    async def _handle_trigger_message(self, channel: str, data: str) -> None:
        """Handle a trigger message from Redis."""
        try:
            # Parse message data
            message_data = json.loads(data)
            event_type = message_data.get("event_type", "unknown")
            
            logger.debug("Received trigger message", channel=channel, event_type=event_type)
            
            # Find flows that should be triggered by this event
            triggered_flows = []
            for flow_name, flow_def in self.settings.get_enabled_flows().items():
                trigger_events = flow_def.get("trigger_events", [])
                
                # Check if this event type triggers the flow
                for trigger_event in trigger_events:
                    if trigger_event == event_type:
                        triggered_flows.append((flow_name, flow_def))
                        break
                    
                    # Also check if channel matches expected topics
                    topics = self.settings.get_event_topics(trigger_event)
                    if channel in topics:
                        triggered_flows.append((flow_name, flow_def))
                        break
            
            # Execute triggered flows
            for flow_name, flow_def in triggered_flows:
                await self.execute_flow(flow_name, event_type, message_data)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in trigger message", channel=channel, data=data)
        except Exception as e:
            logger.error("Error handling trigger message", error=str(e), exc_info=True)
    
    async def execute_flow(self, flow_name: str, trigger_event: Optional[str] = None,
                          trigger_data: Optional[Dict[str, Any]] = None) -> FlowExecution:
        """Execute a flow by name."""
        flow_def = self.settings.get_flow_definition(flow_name)
        if not flow_def:
            raise ValueError(f"Unknown flow: {flow_name}")
        
        if not flow_def.get("enabled", False):
            raise ValueError(f"Flow disabled: {flow_name}")
        
        # Create flow execution
        flow_id = str(uuid.uuid4())
        flow_execution = FlowExecution(
            flow_id=flow_id,
            flow_name=flow_name,
            trigger_event=trigger_event,
            trigger_data=trigger_data,
            status=FlowStatus.PENDING,
            start_time=datetime.utcnow()
        )
        
        logger.info(
            "Starting flow execution",
            flow_id=flow_id,
            flow_name=flow_name,
            trigger_event=trigger_event
        )
        
        # Store active flow
        async with self._flows_lock:
            self.active_flows[flow_id] = flow_execution
        
        try:
            # Execute flow steps
            flow_execution.status = FlowStatus.RUNNING
            await self._execute_flow_steps(flow_execution, flow_def)
            
            # Calculate success rate
            completed_steps = sum(1 for step in flow_execution.steps 
                                if step.status == StepStatus.COMPLETED)
            flow_execution.success_rate = completed_steps / len(flow_execution.steps) if flow_execution.steps else 0.0
            
            # Determine final status
            if all(step.status == StepStatus.COMPLETED for step in flow_execution.steps):
                flow_execution.status = FlowStatus.COMPLETED
            elif any(step.status == StepStatus.FAILED for step in flow_execution.steps):
                flow_execution.status = FlowStatus.FAILED
            else:
                flow_execution.status = FlowStatus.COMPLETED  # Partial success
            
            flow_execution.end_time = datetime.utcnow()
            flow_execution.duration_ms = (flow_execution.end_time - flow_execution.start_time).total_seconds() * 1000
            
            logger.info(
                "Flow execution completed",
                flow_id=flow_id,
                flow_name=flow_name,
                status=flow_execution.status.value,
                duration_ms=flow_execution.duration_ms,
                success_rate=flow_execution.success_rate
            )
            
            # Record metrics
            self.metrics.record_flow_execution(
                flow_name, 
                flow_execution.duration_ms / 1000,
                flow_execution.status == FlowStatus.COMPLETED
            )
            
            # Publish flow completion event
            if self.settings.publish_flow_events:
                await self._publish_flow_event(flow_execution, "flow_completed")
            
        except Exception as e:
            flow_execution.status = FlowStatus.FAILED
            flow_execution.error = str(e)
            flow_execution.end_time = datetime.utcnow()
            flow_execution.duration_ms = (flow_execution.end_time - flow_execution.start_time).total_seconds() * 1000
            
            logger.error(
                "Flow execution failed",
                flow_id=flow_id,
                flow_name=flow_name,
                error=str(e),
                exc_info=True
            )
            
            self.metrics.record_flow_execution(
                flow_name,
                flow_execution.duration_ms / 1000,
                False
            )
            
            # Publish flow failure event
            if self.settings.publish_flow_events:
                await self._publish_flow_event(flow_execution, "flow_failed")
        
        finally:
            # Move to history and remove from active
            async with self._flows_lock:
                self.flow_history.append(flow_execution)
                if flow_id in self.active_flows:
                    del self.active_flows[flow_id]
                
                # Keep history manageable
                if len(self.flow_history) > 1000:
                    self.flow_history = self.flow_history[-1000:]
        
        return flow_execution
    
    async def _execute_flow_steps(self, flow_execution: FlowExecution, flow_def: Dict[str, Any]) -> None:
        """Execute individual steps of a flow."""
        steps_config = flow_def.get("steps", [])
        
        for i, step_config in enumerate(steps_config):
            step_id = f"{flow_execution.flow_name}.step[{i}]"
            service_name = step_config["service"]
            action = step_config["action"]
            
            # Create step execution
            step_execution = FlowStepExecution(
                step_id=step_id,
                service_name=service_name,
                action=action,
                status=StepStatus.PENDING
            )
            flow_execution.steps.append(step_execution)
            
            logger.debug(
                "Executing flow step",
                flow_id=flow_execution.flow_id,
                step_id=step_id,
                service=service_name,
                action=action
            )
            
            # Execute step with retries
            await self._execute_step_with_retries(step_execution, step_config, flow_execution)
    
    async def _execute_step_with_retries(self, step_execution: FlowStepExecution, 
                                       step_config: Dict[str, Any], 
                                       flow_execution: FlowExecution) -> None:
        """Execute a step with retry logic."""
        max_retries = self.settings.flow_retry_attempts
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                step_execution.status = StepStatus.RETRY
                step_execution.retry_count = attempt
                logger.info(
                    "Retrying flow step",
                    step_id=step_execution.step_id,
                    attempt=attempt,
                    max_retries=max_retries
                )
            
            try:
                step_execution.status = StepStatus.RUNNING
                step_execution.start_time = datetime.utcnow()
                
                # Execute the actual step
                await self._execute_single_step(step_execution, step_config, flow_execution)
                
                step_execution.end_time = datetime.utcnow()
                step_execution.duration_ms = (step_execution.end_time - step_execution.start_time).total_seconds() * 1000
                step_execution.status = StepStatus.COMPLETED
                
                logger.debug(
                    "Flow step completed",
                    step_id=step_execution.step_id,
                    duration_ms=step_execution.duration_ms
                )
                
                return  # Success, no need to retry
                
            except Exception as e:
                step_execution.error = str(e)
                
                if attempt < max_retries:
                    logger.warning(
                        "Flow step failed, will retry",
                        step_id=step_execution.step_id,
                        attempt=attempt,
                        error=str(e)
                    )
                    await asyncio.sleep(min(2 ** attempt, 10))  # Exponential backoff
                else:
                    step_execution.status = StepStatus.FAILED
                    step_execution.end_time = datetime.utcnow()
                    step_execution.duration_ms = (step_execution.end_time - step_execution.start_time).total_seconds() * 1000
                    
                    logger.error(
                        "Flow step failed after retries",
                        step_id=step_execution.step_id,
                        attempts=max_retries + 1,
                        error=str(e)
                    )
                    
                    self.metrics.record_error("flow_step_error", step_execution.service_name)
                    break
    
    async def _execute_single_step(self, step_execution: FlowStepExecution,
                                 step_config: Dict[str, Any],
                                 flow_execution: FlowExecution) -> None:
        """Execute a single flow step."""
        service_name = step_execution.service_name
        action = step_execution.action
        
        # Get service info
        service_info = self.settings.get_service_info(service_name)
        if not service_info:
            raise ValueError(f"Unknown service: {service_name}")
        
        # Execute action based on type
        if action == "publish":
            await self._execute_publish_action(step_execution, step_config, flow_execution)
        elif action == "consume_and_process":
            await self._execute_process_action(step_execution, step_config, flow_execution)
        elif action == "validate":
            await self._execute_validate_action(step_execution, step_config, flow_execution)
        elif action == "execute":
            await self._execute_execute_action(step_execution, step_config, flow_execution)
        elif action == "route":
            await self._execute_route_action(step_execution, step_config, flow_execution)
        elif action == "collect_health":
            await self._execute_health_collection_action(step_execution, step_config, flow_execution)
        elif action == "aggregate_and_alert":
            await self._execute_aggregation_action(step_execution, step_config, flow_execution)
        else:
            await self._execute_generic_action(step_execution, step_config, flow_execution)
    
    async def _execute_publish_action(self, step_execution: FlowStepExecution,
                                    step_config: Dict[str, Any],
                                    flow_execution: FlowExecution) -> None:
        """Execute a publish action."""
        # This would typically involve triggering data ingestion/publishing
        # For now, simulate by checking service health
        await self._call_service_health_check(step_execution.service_name)
        
        # Simulate publishing event data
        if "topics" in step_config and self.redis_client:
            event_data = {
                "event_type": step_config.get("event", "unknown"),
                "flow_id": flow_execution.flow_id,
                "service": step_execution.service_name,
                "timestamp": datetime.utcnow().isoformat(),
                "trigger_data": flow_execution.trigger_data
            }
            
            for topic in step_config["topics"]:
                await self.redis_client.publish(topic, json.dumps(event_data))
    
    async def _execute_process_action(self, step_execution: FlowStepExecution,
                                    step_config: Dict[str, Any],
                                    flow_execution: FlowExecution) -> None:
        """Execute a process action."""
        # Call service processing endpoint
        service_info = self.settings.get_service_info(step_execution.service_name)
        endpoint = service_info["endpoint"]
        
        # Determine processing endpoint based on service
        if step_execution.service_name == "indicator-engine":
            process_url = f"{endpoint}/indicators/compute"
        elif step_execution.service_name == "signal-generator":
            process_url = f"{endpoint}/signals/generate"
        else:
            process_url = f"{endpoint}/process"
        
        # Call service
        await self._call_service_api(step_execution.service_name, "POST", process_url, 
                                   {"trigger_data": flow_execution.trigger_data})
    
    async def _execute_validate_action(self, step_execution: FlowStepExecution,
                                     step_config: Dict[str, Any],
                                     flow_execution: FlowExecution) -> None:
        """Execute a validate action."""
        # Call risk manager validation
        service_info = self.settings.get_service_info(step_execution.service_name)
        endpoint = service_info["endpoint"]
        validate_url = f"{endpoint}/risk/validate"
        
        await self._call_service_api(step_execution.service_name, "POST", validate_url,
                                   {"signal_data": flow_execution.trigger_data})
    
    async def _execute_execute_action(self, step_execution: FlowStepExecution,
                                    step_config: Dict[str, Any],
                                    flow_execution: FlowExecution) -> None:
        """Execute an execute action."""
        # Call execution engine
        service_info = self.settings.get_service_info(step_execution.service_name)
        endpoint = service_info["endpoint"]
        execute_url = f"{endpoint}/orders/execute"
        
        await self._call_service_api(step_execution.service_name, "POST", execute_url,
                                   {"order_data": flow_execution.trigger_data})
    
    async def _execute_route_action(self, step_execution: FlowStepExecution,
                                  step_config: Dict[str, Any],
                                  flow_execution: FlowExecution) -> None:
        """Execute a route action."""
        # Call transport router
        service_info = self.settings.get_service_info(step_execution.service_name)
        endpoint = service_info["endpoint"]
        route_url = f"{endpoint}/route/data"
        
        await self._call_service_api(step_execution.service_name, "POST", route_url,
                                   {"route_data": flow_execution.trigger_data,
                                    "destinations": step_config.get("destinations", [])})
    
    async def _execute_health_collection_action(self, step_execution: FlowStepExecution,
                                              step_config: Dict[str, Any],
                                              flow_execution: FlowExecution) -> None:
        """Execute health collection action."""
        # Call telemetry daemon health collection
        service_info = self.settings.get_service_info(step_execution.service_name)
        endpoint = service_info["endpoint"]
        collect_url = f"{endpoint}/telemetry/collect"
        
        await self._call_service_api(step_execution.service_name, "POST", collect_url, {})
    
    async def _execute_aggregation_action(self, step_execution: FlowStepExecution,
                                        step_config: Dict[str, Any],
                                        flow_execution: FlowExecution) -> None:
        """Execute aggregation and alerting action."""
        # Call telemetry daemon aggregation
        service_info = self.settings.get_service_info(step_execution.service_name)
        endpoint = service_info["endpoint"]
        aggregate_url = f"{endpoint}/telemetry/aggregate"
        
        await self._call_service_api(step_execution.service_name, "POST", aggregate_url, {})
    
    async def _execute_generic_action(self, step_execution: FlowStepExecution,
                                    step_config: Dict[str, Any],
                                    flow_execution: FlowExecution) -> None:
        """Execute a generic action (fallback)."""
        # Generic health check as fallback
        await self._call_service_health_check(step_execution.service_name)
    
    async def _call_service_api(self, service_name: str, method: str, url: str,
                              data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a service API with circuit breaker protection."""
        if not self.http_client:
            raise RuntimeError("HTTP client not initialized")
        
        async def api_call():
            if method.upper() == "GET":
                response = await self.http_client.get(url)
            elif method.upper() == "POST":
                response = await self.http_client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        # Use circuit breaker if enabled
        if service_name in self.circuit_breakers:
            result = await self.circuit_breakers[service_name].call(api_call)
        else:
            result = await api_call()
        
        return result
    
    async def _call_service_health_check(self, service_name: str) -> Dict[str, Any]:
        """Call service health check endpoint."""
        service_info = self.settings.get_service_info(service_name)
        if not service_info:
            raise ValueError(f"Unknown service: {service_name}")
        
        endpoint = service_info["endpoint"]
        health_path = service_info.get("health_path", "/healthz")
        health_url = f"{endpoint}{health_path}"
        
        return await self._call_service_api(service_name, "GET", health_url)
    
    async def _publish_flow_event(self, flow_execution: FlowExecution, event_type: str) -> None:
        """Publish flow execution event to Redis."""
        if not self.redis_client:
            return
        
        try:
            event_data = {
                "event_type": event_type,
                "flow_execution": flow_execution.to_dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.publish(
                self.settings.flow_events_topic,
                json.dumps(event_data)
            )
            
        except Exception as e:
            logger.error("Failed to publish flow event", error=str(e))
    
    async def _run_flow_monitoring(self) -> None:
        """Run flow monitoring loop."""
        try:
            while self.running:
                try:
                    await self._monitor_active_flows()
                    await self._update_flow_metrics()
                    
                    await asyncio.sleep(self.settings.flow_monitoring_interval_seconds)
                    
                except Exception as e:
                    logger.error("Flow monitoring cycle failed", error=str(e))
                    await asyncio.sleep(5)
                    
        except asyncio.CancelledError:
            logger.info("Flow monitoring cancelled")
        except Exception as e:
            logger.error("Flow monitoring failed", error=str(e))
    
    async def _monitor_active_flows(self) -> None:
        """Monitor active flows for timeouts and issues."""
        current_time = datetime.utcnow()
        timeout_threshold = timedelta(seconds=self.settings.flow_timeout_seconds)
        
        async with self._flows_lock:
            timed_out_flows = []
            
            for flow_id, flow_execution in self.active_flows.items():
                if current_time - flow_execution.start_time > timeout_threshold:
                    timed_out_flows.append(flow_id)
            
            # Handle timed out flows
            for flow_id in timed_out_flows:
                flow_execution = self.active_flows[flow_id]
                flow_execution.status = FlowStatus.TIMEOUT
                flow_execution.end_time = current_time
                flow_execution.error = "Flow execution timeout"
                
                logger.warning(
                    "Flow execution timed out",
                    flow_id=flow_id,
                    flow_name=flow_execution.flow_name,
                    timeout_seconds=self.settings.flow_timeout_seconds
                )
                
                # Move to history
                self.flow_history.append(flow_execution)
                del self.active_flows[flow_id]
    
    async def _update_flow_metrics(self) -> None:
        """Update flow performance metrics."""
        # Calculate metrics from recent flow history
        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_flows = [f for f in self.flow_history if f.start_time > recent_cutoff]
        
        if recent_flows:
            # Group by flow name
            flow_groups = {}
            for flow in recent_flows:
                if flow.flow_name not in flow_groups:
                    flow_groups[flow.flow_name] = []
                flow_groups[flow.flow_name].append(flow)
            
            # Calculate metrics per flow type
            for flow_name, flows in flow_groups.items():
                success_count = sum(1 for f in flows if f.status == FlowStatus.COMPLETED)
                avg_duration = sum(f.duration_ms or 0 for f in flows) / len(flows)
                success_rate = success_count / len(flows)
                
                self.flow_metrics[flow_name] = {
                    "total_executions": len(flows),
                    "successful_executions": success_count,
                    "success_rate": success_rate,
                    "average_duration_ms": avg_duration,
                    "last_updated": datetime.utcnow().isoformat()
                }
    
    async def _run_health_checks(self) -> None:
        """Run periodic health checks of services."""
        try:
            while self.running:
                try:
                    await self._check_all_services_health()
                    await asyncio.sleep(self.settings.service_health_check_interval_seconds)
                    
                except Exception as e:
                    logger.error("Service health check cycle failed", error=str(e))
                    await asyncio.sleep(10)
                    
        except asyncio.CancelledError:
            logger.info("Service health checks cancelled")
        except Exception as e:
            logger.error("Service health checks failed", error=str(e))
    
    async def _check_all_services_health(self) -> None:
        """Check health of all registered services."""
        health_results = {}
        
        for service_name, service_info in self.settings.service_registry.items():
            try:
                result = await self._call_service_health_check(service_name)
                health_results[service_name] = {"healthy": True, "response": result}
                self.metrics.record_service_health_check(service_name, 0.1, True)
                
            except Exception as e:
                health_results[service_name] = {"healthy": False, "error": str(e)}
                self.metrics.record_service_health_check(service_name, 0.1, False)
                logger.warning(
                    "Service health check failed",
                    service=service_name,
                    error=str(e)
                )
        
        # Update service health metrics
        healthy_services = sum(1 for result in health_results.values() if result["healthy"])
        total_services = len(health_results)
        
        self.metrics.set_gauge("orchestrator_healthy_services", float(healthy_services))
        self.metrics.set_gauge("orchestrator_total_services", float(total_services))
        self.metrics.set_gauge("orchestrator_service_health_rate", healthy_services / total_services if total_services > 0 else 0.0)
    
    # Public API methods
    
    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get list of currently active flows."""
        async with self._flows_lock:
            return [flow.to_dict() for flow in self.active_flows.values()]
    
    async def get_flow_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent flow execution history."""
        async with self._flows_lock:
            return [flow.to_dict() for flow in self.flow_history[-limit:]]
    
    async def get_flow_metrics(self) -> Dict[str, Any]:
        """Get flow performance metrics."""
        async with self._flows_lock:
            active_count = len(self.active_flows)
            total_history = len(self.flow_history)
        
        return {
            "active_flows": active_count,
            "total_executions": total_history,
            "flow_metrics": self.flow_metrics.copy(),
            "circuit_breakers": {
                name: {
                    "is_open": cb.is_open,
                    "failure_count": cb.failure_count,
                    "last_failure": cb.last_failure_time.isoformat() if cb.last_failure_time else None
                }
                for name, cb in self.circuit_breakers.items()
            }
        }
    
    async def trigger_flow_manually(self, flow_name: str, 
                                   trigger_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manually trigger a flow execution."""
        try:
            flow_execution = await self.execute_flow(flow_name, "manual", trigger_data)
            return {
                "success": True,
                "flow_id": flow_execution.flow_id,
                "status": flow_execution.status.value
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cancel_flow(self, flow_id: str) -> Dict[str, Any]:
        """Cancel an active flow execution."""
        async with self._flows_lock:
            if flow_id not in self.active_flows:
                return {"success": False, "error": "Flow not found"}
            
            flow_execution = self.active_flows[flow_id]
            flow_execution.status = FlowStatus.CANCELLED
            flow_execution.end_time = datetime.utcnow()
            
            # Move to history
            self.flow_history.append(flow_execution)
            del self.active_flows[flow_id]
            
            logger.info("Flow cancelled", flow_id=flow_id, flow_name=flow_execution.flow_name)
            
            return {"success": True, "flow_id": flow_id}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        async with self._flows_lock:
            active_count = len(self.active_flows)
            history_count = len(self.flow_history)
        
        return {
            "running": self.running,
            "active_flows": active_count,
            "flow_history_count": history_count,
            "enabled_flows": len(self.settings.get_enabled_flows()),
            "circuit_breakers_enabled": self.settings.circuit_breaker_enabled,
            "monitoring_enabled": self.settings.flow_monitoring_enabled,
            "service_health_checks": len(self.settings.service_registry)
        }