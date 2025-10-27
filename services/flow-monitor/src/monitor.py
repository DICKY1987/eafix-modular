"""
Flow Monitor Core

Implements end-to-end flow monitoring, tracing, and performance analysis
across the entire EAFIX trading system pipeline.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

import redis.asyncio as redis
import httpx
import structlog

logger = structlog.get_logger(__name__)


class FlowStatus(Enum):
    """Flow execution status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    PARTIAL = "partial"


class StageStatus(Enum):
    """Individual stage status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class FlowStageTrace:
    """Individual stage trace information."""
    
    stage_id: str
    service_name: str
    event_type: str
    status: StageStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    expected_latency_ms: float = 0
    critical_latency_ms: float = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data
    
    def is_latency_critical(self) -> bool:
        """Check if stage latency is critical."""
        return self.duration_ms is not None and self.duration_ms > self.critical_latency_ms
    
    def is_latency_warning(self) -> bool:
        """Check if stage latency is a warning."""
        return (self.duration_ms is not None and 
                self.duration_ms > self.expected_latency_ms and 
                not self.is_latency_critical())


@dataclass
class FlowTrace:
    """Complete flow trace information."""
    
    trace_id: str
    flow_name: str
    status: FlowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    stages: List[FlowStageTrace] = None
    trigger_event: Optional[Dict[str, Any]] = None
    expected_total_latency_ms: float = 0
    critical_total_latency_ms: float = 0
    success_rate_threshold: float = 0.95
    
    def __post_init__(self):
        if self.stages is None:
            self.stages = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        data['stages'] = [stage.to_dict() for stage in self.stages]
        return data
    
    def get_completed_stages(self) -> List[FlowStageTrace]:
        """Get list of completed stages."""
        return [stage for stage in self.stages if stage.status == StageStatus.COMPLETED]
    
    def get_failed_stages(self) -> List[FlowStageTrace]:
        """Get list of failed stages."""
        return [stage for stage in self.stages if stage.status == StageStatus.FAILED]
    
    def calculate_success_rate(self) -> float:
        """Calculate success rate for completed stages."""
        if not self.stages:
            return 0.0
        
        completed_stages = len(self.get_completed_stages())
        return completed_stages / len(self.stages)
    
    def is_performance_degraded(self) -> bool:
        """Check if flow performance is degraded."""
        return (self.total_duration_ms is not None and 
                self.total_duration_ms > self.expected_total_latency_ms * 1.5)
    
    def is_critical_latency(self) -> bool:
        """Check if flow has critical latency."""
        return (self.total_duration_ms is not None and 
                self.total_duration_ms > self.critical_total_latency_ms)


@dataclass
class FlowPerformanceMetrics:
    """Flow performance metrics over a time window."""
    
    flow_name: str
    time_window_start: datetime
    time_window_end: datetime
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_duration_ms: float = 0.0
    median_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    success_rate: float = 0.0
    performance_degradation_detected: bool = False
    critical_latency_violations: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['time_window_start'] = self.time_window_start.isoformat()
        data['time_window_end'] = self.time_window_end.isoformat()
        return data


class FlowMonitor:
    """Core flow monitoring engine."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # Redis client for event monitoring
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        
        # HTTP client for service monitoring
        self.http_client: Optional[httpx.AsyncClient] = None
        
        # Active flow traces
        self.active_traces: Dict[str, FlowTrace] = {}
        self.completed_traces: List[FlowTrace] = []
        self._traces_lock = asyncio.Lock()
        
        # Performance metrics storage
        self.performance_metrics: Dict[str, List[FlowPerformanceMetrics]] = {}
        self._metrics_lock = asyncio.Lock()
        
        # Background monitoring tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # Event correlation for flow tracing
        self.event_correlation: Dict[str, Dict[str, Any]] = {}
        
        self.running = False
    
    async def start(self) -> None:
        """Start the flow monitor."""
        if self.running:
            return
        
        logger.info("Starting Flow Monitor")
        
        # Validate configuration
        config_errors = self.settings.validate_flow_config()
        if config_errors:
            raise RuntimeError(f"Invalid flow configuration: {config_errors}")
        
        # Initialize Redis connection
        self.redis_client = redis.from_url(self.settings.redis_url)
        await self.redis_client.ping()
        logger.info("Connected to Redis", url=self.settings.redis_url)
        
        # Initialize HTTP client
        timeout = httpx.Timeout(10.0)
        self.http_client = httpx.AsyncClient(timeout=timeout)
        
        # Start event monitoring
        if self.settings.end_to_end_tracing_enabled:
            self.monitoring_tasks.append(
                asyncio.create_task(self._start_event_monitoring())
            )
        
        # Start performance analysis
        if self.settings.performance_analysis_enabled:
            self.monitoring_tasks.append(
                asyncio.create_task(self._run_performance_analysis())
            )
        
        # Start service health monitoring
        self.monitoring_tasks.append(
            asyncio.create_task(self._monitor_service_health())
        )
        
        self.running = True
        logger.info("Flow Monitor started successfully")
    
    async def stop(self) -> None:
        """Stop the flow monitor."""
        if not self.running:
            return
        
        logger.info("Stopping Flow Monitor")
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
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
        logger.info("Flow Monitor stopped")
    
    async def _start_event_monitoring(self) -> None:
        """Start Redis event monitoring for flow tracing."""
        try:
            self.pubsub = self.redis_client.pubsub()
            
            # Subscribe to monitored topics
            if self.settings.monitored_topics:
                await self.pubsub.subscribe(*self.settings.monitored_topics)
                logger.info("Subscribed to flow monitoring topics", topics=self.settings.monitored_topics)
            
            # Process events
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        await self._handle_flow_event(
                            message["channel"].decode(),
                            message["data"].decode()
                        )
                    except Exception as e:
                        logger.error(
                            "Error processing flow event",
                            channel=message["channel"].decode(),
                            error=str(e)
                        )
                        
        except asyncio.CancelledError:
            logger.info("Event monitoring cancelled")
        except Exception as e:
            logger.error("Event monitoring failed", error=str(e))
    
    async def _handle_flow_event(self, channel: str, data: str) -> None:
        """Handle flow event for tracing."""
        try:
            # Parse event data
            event_data = json.loads(data)
            event_type = event_data.get("event_type", "unknown")
            timestamp = datetime.fromisoformat(event_data.get("timestamp", datetime.utcnow().isoformat()))
            
            logger.debug("Processing flow event", channel=channel, event_type=event_type)
            
            # Check if this event should trigger or continue a flow trace
            await self._process_flow_event(channel, event_type, event_data, timestamp)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in flow event", channel=channel, data=data[:100])
        except Exception as e:
            logger.error("Error handling flow event", error=str(e), exc_info=True)
    
    async def _process_flow_event(self, channel: str, event_type: str, 
                                 event_data: Dict[str, Any], timestamp: datetime) -> None:
        """Process flow event for tracing and monitoring."""
        # Determine which flows this event might be part of
        relevant_flows = await self._find_relevant_flows(event_type, event_data)
        
        for flow_name in relevant_flows:
            await self._update_flow_trace(flow_name, event_type, event_data, timestamp, channel)
    
    async def _find_relevant_flows(self, event_type: str, event_data: Dict[str, Any]) -> List[str]:
        """Find flows that are relevant to this event."""
        relevant_flows = []
        
        for flow_name, flow_config in self.settings.get_enabled_flows().items():
            stages = flow_config.get("stages", [])
            
            for stage in stages:
                if stage.get("event_type") == event_type:
                    relevant_flows.append(flow_name)
                    break
        
        return relevant_flows
    
    async def _update_flow_trace(self, flow_name: str, event_type: str, 
                                event_data: Dict[str, Any], timestamp: datetime, channel: str) -> None:
        """Update flow trace with new event."""
        async with self._traces_lock:
            # Check if this is the start of a new flow or continuation of existing
            trace_id = await self._get_or_create_trace_id(flow_name, event_type, event_data)
            
            if trace_id not in self.active_traces:
                # Start new trace
                await self._start_new_trace(trace_id, flow_name, event_type, event_data, timestamp)
            else:
                # Update existing trace
                await self._update_existing_trace(trace_id, event_type, event_data, timestamp)
    
    async def _get_or_create_trace_id(self, flow_name: str, event_type: str, 
                                    event_data: Dict[str, Any]) -> str:
        """Get existing trace ID or create new one."""
        # Try to correlate with existing traces based on common identifiers
        correlation_keys = ["trace_id", "correlation_id", "signal_id", "order_id", "execution_id"]
        
        for key in correlation_keys:
            if key in event_data:
                correlation_value = event_data[key]
                
                # Look for existing traces with this correlation
                for trace_id, trace in self.active_traces.items():
                    if (trace.flow_name == flow_name and 
                        trace.trigger_event and
                        trace.trigger_event.get(key) == correlation_value):
                        return trace_id
        
        # No existing trace found, create new trace ID
        return f"{flow_name}_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    async def _start_new_trace(self, trace_id: str, flow_name: str, event_type: str,
                             event_data: Dict[str, Any], timestamp: datetime) -> None:
        """Start a new flow trace."""
        flow_config = self.settings.get_flow_config(flow_name)
        if not flow_config:
            return
        
        # Create new trace
        trace = FlowTrace(
            trace_id=trace_id,
            flow_name=flow_name,
            status=FlowStatus.ACTIVE,
            start_time=timestamp,
            trigger_event=event_data,
            expected_total_latency_ms=flow_config.get("total_expected_latency_ms", 0),
            critical_total_latency_ms=flow_config.get("total_critical_latency_ms", 0),
            success_rate_threshold=flow_config.get("success_rate_threshold", 0.95)
        )
        
        # Initialize stages
        stages = flow_config.get("stages", [])
        for stage_config in stages:
            stage_trace = FlowStageTrace(
                stage_id=stage_config["stage_id"],
                service_name=stage_config["service"],
                event_type=stage_config["event_type"],
                status=StageStatus.PENDING,
                expected_latency_ms=stage_config.get("expected_latency_ms", 0),
                critical_latency_ms=stage_config.get("critical_latency_ms", 0)
            )
            trace.stages.append(stage_trace)
        
        # Mark first relevant stage as processing
        for stage in trace.stages:
            if stage.event_type == event_type:
                stage.status = StageStatus.PROCESSING
                stage.start_time = timestamp
                break
        
        self.active_traces[trace_id] = trace
        
        logger.info(
            "Started new flow trace",
            trace_id=trace_id,
            flow_name=flow_name,
            event_type=event_type
        )
        
        # Record metrics
        self.metrics.record_flow_trace_started(flow_name)
    
    async def _update_existing_trace(self, trace_id: str, event_type: str,
                                   event_data: Dict[str, Any], timestamp: datetime) -> None:
        """Update existing flow trace with new event."""
        trace = self.active_traces[trace_id]
        
        # Find the stage that corresponds to this event
        stage_updated = False
        for stage in trace.stages:
            if (stage.event_type == event_type and 
                stage.status in [StageStatus.PENDING, StageStatus.PROCESSING]):
                
                # Update stage completion
                if stage.status == StageStatus.PROCESSING:
                    stage.status = StageStatus.COMPLETED
                    stage.end_time = timestamp
                    if stage.start_time:
                        stage.duration_ms = (timestamp - stage.start_time).total_seconds() * 1000
                else:
                    # Stage was pending, now processing
                    stage.status = StageStatus.PROCESSING
                    stage.start_time = timestamp
                
                stage_updated = True
                break
        
        if stage_updated:
            # Check if flow is complete
            await self._check_flow_completion(trace_id, timestamp)
            
            logger.debug(
                "Updated flow trace stage",
                trace_id=trace_id,
                flow_name=trace.flow_name,
                event_type=event_type
            )
        else:
            logger.debug(
                "No matching stage found for event",
                trace_id=trace_id,
                event_type=event_type
            )
    
    async def _check_flow_completion(self, trace_id: str, timestamp: datetime) -> None:
        """Check if flow trace is complete and finalize it."""
        trace = self.active_traces[trace_id]
        
        # Count stage statuses
        completed_stages = len(trace.get_completed_stages())
        failed_stages = len(trace.get_failed_stages())
        total_stages = len(trace.stages)
        
        flow_complete = False
        
        if completed_stages == total_stages:
            # All stages completed successfully
            trace.status = FlowStatus.COMPLETED
            flow_complete = True
        elif failed_stages > 0 and (completed_stages + failed_stages) == total_stages:
            # Some stages failed, but all stages are done
            trace.status = FlowStatus.FAILED
            flow_complete = True
        elif (timestamp - trace.start_time).total_seconds() > (self.settings.max_trace_duration_minutes * 60):
            # Flow timed out
            trace.status = FlowStatus.TIMEOUT
            flow_complete = True
        
        if flow_complete:
            trace.end_time = timestamp
            trace.total_duration_ms = (timestamp - trace.start_time).total_seconds() * 1000
            
            # Move to completed traces
            self.completed_traces.append(trace)
            del self.active_traces[trace_id]
            
            # Keep only recent completed traces
            if len(self.completed_traces) > 10000:
                self.completed_traces = self.completed_traces[-10000:]
            
            logger.info(
                "Flow trace completed",
                trace_id=trace_id,
                flow_name=trace.flow_name,
                status=trace.status.value,
                duration_ms=trace.total_duration_ms,
                success_rate=trace.calculate_success_rate()
            )
            
            # Record metrics
            self.metrics.record_flow_trace_completed(
                trace.flow_name,
                trace.total_duration_ms / 1000,
                trace.status == FlowStatus.COMPLETED,
                trace.calculate_success_rate()
            )
            
            # Check for alerts
            await self._check_flow_alerts(trace)
    
    async def _check_flow_alerts(self, trace: FlowTrace) -> None:
        """Check if flow trace should trigger alerts."""
        if not self.settings.flow_alerting_enabled:
            return
        
        alerts = []
        
        # Check success rate
        success_rate = trace.calculate_success_rate()
        if success_rate < self.settings.success_rate_alert_threshold:
            alerts.append({
                "type": "low_success_rate",
                "message": f"Flow {trace.flow_name} success rate is low: {success_rate:.2%}",
                "severity": "high"
            })
        
        # Check overall latency
        if trace.is_critical_latency():
            alerts.append({
                "type": "critical_latency",
                "message": f"Flow {trace.flow_name} has critical latency: {trace.total_duration_ms:.0f}ms",
                "severity": "critical"
            })
        elif trace.is_performance_degraded():
            alerts.append({
                "type": "performance_degradation",
                "message": f"Flow {trace.flow_name} performance degraded: {trace.total_duration_ms:.0f}ms",
                "severity": "medium"
            })
        
        # Check individual stage latencies
        for stage in trace.stages:
            if stage.is_latency_critical():
                alerts.append({
                    "type": "stage_critical_latency",
                    "message": f"Stage {stage.stage_id} has critical latency: {stage.duration_ms:.0f}ms",
                    "severity": "high"
                })
        
        # Send alerts
        for alert in alerts:
            await self._send_flow_alert(trace, alert)
    
    async def _send_flow_alert(self, trace: FlowTrace, alert: Dict[str, Any]) -> None:
        """Send flow monitoring alert."""
        alert_data = {
            "alert_type": "flow_monitoring",
            "trace_id": trace.trace_id,
            "flow_name": trace.flow_name,
            "timestamp": datetime.utcnow().isoformat(),
            "alert": alert
        }
        
        logger.warning(
            "Flow monitoring alert",
            trace_id=trace.trace_id,
            flow_name=trace.flow_name,
            alert_type=alert["type"],
            message=alert["message"]
        )
        
        # Publish alert to Redis
        try:
            await self.redis_client.publish(
                "eafix.flow.alerts",
                json.dumps(alert_data)
            )
        except Exception as e:
            logger.error("Failed to publish flow alert", error=str(e))
        
        self.metrics.record_flow_alert(trace.flow_name, alert["type"])
    
    async def _run_performance_analysis(self) -> None:
        """Run periodic performance analysis."""
        try:
            while self.running:
                try:
                    await self._analyze_flow_performance()
                    await asyncio.sleep(self.settings.trace_analysis_interval_seconds)
                    
                except Exception as e:
                    logger.error("Performance analysis cycle failed", error=str(e))
                    await asyncio.sleep(30)
                    
        except asyncio.CancelledError:
            logger.info("Performance analysis cancelled")
        except Exception as e:
            logger.error("Performance analysis failed", error=str(e))
    
    async def _analyze_flow_performance(self) -> None:
        """Analyze flow performance over the configured window."""
        window_end = datetime.utcnow()
        window_start = window_end - timedelta(minutes=self.settings.performance_window_minutes)
        
        async with self._traces_lock:
            # Get traces in the analysis window
            window_traces = [
                trace for trace in self.completed_traces
                if window_start <= trace.start_time <= window_end
            ]
        
        # Analyze each flow
        for flow_name in self.settings.get_enabled_flows().keys():
            flow_traces = [t for t in window_traces if t.flow_name == flow_name]
            
            if flow_traces:
                metrics = await self._calculate_flow_metrics(flow_name, flow_traces, window_start, window_end)
                
                async with self._metrics_lock:
                    if flow_name not in self.performance_metrics:
                        self.performance_metrics[flow_name] = []
                    
                    self.performance_metrics[flow_name].append(metrics)
                    
                    # Keep only recent metrics (last 24 hours of windows)
                    cutoff_time = window_end - timedelta(hours=24)
                    self.performance_metrics[flow_name] = [
                        m for m in self.performance_metrics[flow_name]
                        if m.time_window_start > cutoff_time
                    ]
                
                logger.debug(
                    "Analyzed flow performance",
                    flow_name=flow_name,
                    executions=metrics.total_executions,
                    success_rate=metrics.success_rate,
                    avg_duration_ms=metrics.avg_duration_ms
                )
    
    async def _calculate_flow_metrics(self, flow_name: str, traces: List[FlowTrace],
                                    window_start: datetime, window_end: datetime) -> FlowPerformanceMetrics:
        """Calculate performance metrics for a flow."""
        if not traces:
            return FlowPerformanceMetrics(
                flow_name=flow_name,
                time_window_start=window_start,
                time_window_end=window_end
            )
        
        # Calculate basic metrics
        total_executions = len(traces)
        successful_executions = len([t for t in traces if t.status == FlowStatus.COMPLETED])
        failed_executions = total_executions - successful_executions
        success_rate = successful_executions / total_executions
        
        # Calculate duration metrics
        durations = [t.total_duration_ms for t in traces if t.total_duration_ms is not None]
        
        if durations:
            durations.sort()
            avg_duration_ms = statistics.mean(durations)
            median_duration_ms = statistics.median(durations)
            min_duration_ms = min(durations)
            max_duration_ms = max(durations)
            
            # Calculate percentiles
            p95_index = int(len(durations) * 0.95)
            p99_index = int(len(durations) * 0.99)
            p95_duration_ms = durations[p95_index] if p95_index < len(durations) else max_duration_ms
            p99_duration_ms = durations[p99_index] if p99_index < len(durations) else max_duration_ms
        else:
            avg_duration_ms = median_duration_ms = min_duration_ms = max_duration_ms = 0.0
            p95_duration_ms = p99_duration_ms = 0.0
        
        # Check for performance degradation
        flow_config = self.settings.get_flow_config(flow_name)
        expected_latency = flow_config.get("total_expected_latency_ms", 0) if flow_config else 0
        performance_degradation_detected = avg_duration_ms > expected_latency * (1 + self.settings.performance_degradation_threshold)
        
        # Count critical latency violations
        critical_latency_violations = len([t for t in traces if t.is_critical_latency()])
        
        return FlowPerformanceMetrics(
            flow_name=flow_name,
            time_window_start=window_start,
            time_window_end=window_end,
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            avg_duration_ms=avg_duration_ms,
            median_duration_ms=median_duration_ms,
            p95_duration_ms=p95_duration_ms,
            p99_duration_ms=p99_duration_ms,
            min_duration_ms=min_duration_ms,
            max_duration_ms=max_duration_ms,
            success_rate=success_rate,
            performance_degradation_detected=performance_degradation_detected,
            critical_latency_violations=critical_latency_violations
        )
    
    async def _monitor_service_health(self) -> None:
        """Monitor health of services involved in flows."""
        try:
            while self.running:
                try:
                    await self._check_service_health()
                    await asyncio.sleep(self.settings.flow_monitoring_interval_seconds)
                    
                except Exception as e:
                    logger.error("Service health monitoring failed", error=str(e))
                    await asyncio.sleep(30)
                    
        except asyncio.CancelledError:
            logger.info("Service health monitoring cancelled")
        except Exception as e:
            logger.error("Service health monitoring failed", error=str(e))
    
    async def _check_service_health(self) -> None:
        """Check health of all monitored services."""
        for service_name, service_config in self.settings.monitored_services.items():
            try:
                endpoint = service_config["endpoint"]
                health_path = service_config.get("health_path", "/healthz")
                health_url = f"{endpoint}{health_path}"
                
                start_time = time.time()
                response = await self.http_client.get(health_url)
                response_time = (time.time() - start_time) * 1000
                
                is_healthy = response.status_code == 200
                
                self.metrics.record_service_health_check(service_name, response_time / 1000, is_healthy)
                
                if not is_healthy:
                    logger.warning(
                        "Service health check failed",
                        service=service_name,
                        status_code=response.status_code,
                        response_time_ms=response_time
                    )
                
            except Exception as e:
                self.metrics.record_service_health_check(service_name, 0, False)
                logger.error(
                    "Service health check error",
                    service=service_name,
                    error=str(e)
                )
    
    # Public API methods
    
    async def get_active_traces(self) -> List[Dict[str, Any]]:
        """Get currently active flow traces."""
        async with self._traces_lock:
            return [trace.to_dict() for trace in self.active_traces.values()]
    
    async def get_completed_traces(self, limit: int = 100, flow_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get completed flow traces."""
        async with self._traces_lock:
            traces = self.completed_traces[-limit:]
            
            if flow_name:
                traces = [t for t in traces if t.flow_name == flow_name]
            
            return [trace.to_dict() for trace in traces]
    
    async def get_flow_performance_metrics(self, flow_name: str, hours: int = 1) -> List[Dict[str, Any]]:
        """Get performance metrics for a flow."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        async with self._metrics_lock:
            flow_metrics = self.performance_metrics.get(flow_name, [])
            recent_metrics = [
                m for m in flow_metrics
                if m.time_window_start > cutoff_time
            ]
            
            return [metrics.to_dict() for metrics in recent_metrics]
    
    async def get_flow_summary(self) -> Dict[str, Any]:
        """Get flow monitoring summary."""
        async with self._traces_lock:
            active_count = len(self.active_traces)
            completed_count = len(self.completed_traces)
        
        # Calculate success rates by flow
        flow_success_rates = {}
        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        
        async with self._traces_lock:
            recent_traces = [t for t in self.completed_traces if t.start_time > recent_cutoff]
        
        for flow_name in self.settings.get_enabled_flows().keys():
            flow_traces = [t for t in recent_traces if t.flow_name == flow_name]
            if flow_traces:
                successful = len([t for t in flow_traces if t.status == FlowStatus.COMPLETED])
                flow_success_rates[flow_name] = successful / len(flow_traces)
            else:
                flow_success_rates[flow_name] = 0.0
        
        return {
            "active_traces": active_count,
            "completed_traces_total": completed_count,
            "recent_traces_1h": len(recent_traces),
            "flow_success_rates": flow_success_rates,
            "monitored_flows": len(self.settings.get_enabled_flows()),
            "monitored_services": len(self.settings.monitored_services)
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get flow monitor status."""
        return {
            "running": self.running,
            "monitoring_config": self.settings.get_monitoring_config(),
            "active_tasks": len(self.monitoring_tasks),
            "redis_connected": self.redis_client is not None,
            "pubsub_subscribed": self.pubsub is not None
        }