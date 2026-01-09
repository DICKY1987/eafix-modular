# DOC_ID: DOC-SERVICE-0063
"""
Flow Orchestrator Metrics Collection

Prometheus-compatible metrics for flow orchestration performance,
service health tracking, and flow execution analytics.
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
import threading

import structlog

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Collects and manages metrics for flow orchestrator."""
    
    def __init__(self):
        # Metrics storage
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Timing metrics
        self.timing_metrics: Dict[str, List[float]] = defaultdict(list)
        
        # Flow-specific metrics
        self.flow_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Service health tracking
        self.service_health_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Start time for uptime calculation
        self.start_time = time.time()
        
        logger.info("Flow orchestrator metrics collector initialized")
    
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            metric_name = self._format_metric_name(name, labels)
            self.counters[metric_name] += value
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        with self._lock:
            metric_name = self._format_metric_name(name, labels)
            self.gauges[metric_name] = value
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram observation."""
        with self._lock:
            metric_name = self._format_metric_name(name, labels)
            self.histograms[metric_name].append(value)
    
    def record_timing(self, name: str, duration: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record timing metric."""
        with self._lock:
            metric_name = self._format_metric_name(name, labels)
            self.timing_metrics[metric_name].append(duration)
            
            # Keep only recent timings (last 1000)
            if len(self.timing_metrics[metric_name]) > 1000:
                self.timing_metrics[metric_name] = self.timing_metrics[metric_name][-1000:]
    
    def _format_metric_name(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Format metric name with labels."""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    # Flow orchestration specific metrics
    
    def record_flow_execution(self, flow_name: str, duration: float, success: bool) -> None:
        """Record flow execution metrics."""
        labels = {"flow": flow_name}
        
        self.increment_counter("flow_executions_total", labels=labels)
        self.record_timing("flow_execution_duration_seconds", duration, labels)
        
        if success:
            self.increment_counter("flow_executions_success_total", labels=labels)
        else:
            self.increment_counter("flow_executions_failed_total", labels=labels)
        
        # Update flow-specific metrics
        with self._lock:
            if flow_name not in self.flow_metrics:
                self.flow_metrics[flow_name] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "total_duration": 0.0,
                    "last_execution": None
                }
            
            metrics = self.flow_metrics[flow_name]
            metrics["total_executions"] += 1
            metrics["total_duration"] += duration
            metrics["last_execution"] = datetime.utcnow().isoformat()
            
            if success:
                metrics["successful_executions"] += 1
            else:
                metrics["failed_executions"] += 1
    
    def record_flow_step_execution(self, flow_name: str, step_name: str, service: str, 
                                 duration: float, success: bool) -> None:
        """Record flow step execution metrics."""
        labels = {"flow": flow_name, "step": step_name, "service": service}
        
        self.increment_counter("flow_step_executions_total", labels=labels)
        self.record_timing("flow_step_duration_seconds", duration, labels)
        
        if success:
            self.increment_counter("flow_step_success_total", labels=labels)
        else:
            self.increment_counter("flow_step_failed_total", labels=labels)
    
    def record_event_processing(self, event_type: str, processing_time: float, success: bool) -> None:
        """Record event processing metrics."""
        labels = {"event_type": event_type}
        
        self.increment_counter("events_processed_total", labels=labels)
        self.record_timing("event_processing_duration_seconds", processing_time, labels)
        
        if success:
            self.increment_counter("events_processed_success_total", labels=labels)
        else:
            self.increment_counter("events_processed_failed_total", labels=labels)
    
    def record_service_health_check(self, service_name: str, duration: float, success: bool) -> None:
        """Record service health check metrics."""
        labels = {"service": service_name}
        
        self.increment_counter("service_health_checks_total", labels=labels)
        self.record_timing("service_health_check_duration_seconds", duration, labels)
        
        if success:
            self.increment_counter("service_health_checks_success_total", labels=labels)
            self.set_gauge("service_health_status", 1.0, labels)
        else:
            self.increment_counter("service_health_checks_failed_total", labels=labels)
            self.set_gauge("service_health_status", 0.0, labels)
        
        # Update service health tracking
        with self._lock:
            if service_name not in self.service_health_metrics:
                self.service_health_metrics[service_name] = {
                    "last_check": None,
                    "consecutive_failures": 0,
                    "consecutive_successes": 0,
                    "total_checks": 0,
                    "successful_checks": 0
                }
            
            metrics = self.service_health_metrics[service_name]
            metrics["last_check"] = datetime.utcnow().isoformat()
            metrics["total_checks"] += 1
            
            if success:
                metrics["successful_checks"] += 1
                metrics["consecutive_successes"] += 1
                metrics["consecutive_failures"] = 0
            else:
                metrics["consecutive_failures"] += 1
                metrics["consecutive_successes"] = 0
    
    def record_circuit_breaker_state(self, service_name: str, is_open: bool, failure_count: int) -> None:
        """Record circuit breaker state metrics."""
        labels = {"service": service_name}
        
        self.set_gauge("circuit_breaker_open", 1.0 if is_open else 0.0, labels)
        self.set_gauge("circuit_breaker_failure_count", float(failure_count), labels)
        
        if is_open:
            self.increment_counter("circuit_breaker_opened_total", labels=labels)
    
    def record_redis_operation(self, operation: str, success: bool, duration: float) -> None:
        """Record Redis operation metrics."""
        labels = {"operation": operation}
        
        self.increment_counter("redis_operations_total", labels=labels)
        self.record_timing("redis_operation_duration_seconds", duration, labels)
        
        if success:
            self.increment_counter("redis_operations_success_total", labels=labels)
        else:
            self.increment_counter("redis_operations_failed_total", labels=labels)
    
    def record_health_check(self, duration: float, success: bool) -> None:
        """Record orchestrator health check metrics."""
        self.increment_counter("orchestrator_health_checks_total")
        self.record_timing("orchestrator_health_check_duration_seconds", duration)
        
        if success:
            self.increment_counter("orchestrator_health_checks_success_total")
            self.set_gauge("orchestrator_health_status", 1.0)
        else:
            self.increment_counter("orchestrator_health_checks_failed_total")
            self.set_gauge("orchestrator_health_status", 0.0)
    
    def record_error(self, error_type: str, context: Optional[str] = None) -> None:
        """Record error occurrence."""
        labels = {"error_type": error_type}
        if context:
            labels["context"] = context
        
        self.increment_counter("errors_total", labels=labels)
    
    def update_active_flows_gauge(self, count: int) -> None:
        """Update active flows gauge."""
        self.set_gauge("active_flows", float(count))
    
    def update_flow_queue_size(self, size: int) -> None:
        """Update flow queue size gauge."""
        self.set_gauge("flow_queue_size", float(size))
    
    # Metric query methods
    
    def get_counter_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value."""
        metric_name = self._format_metric_name(name, labels)
        with self._lock:
            return self.counters.get(metric_name, 0)
    
    def get_gauge_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value."""
        metric_name = self._format_metric_name(name, labels)
        with self._lock:
            return self.gauges.get(metric_name, 0.0)
    
    def get_histogram_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics."""
        metric_name = self._format_metric_name(name, labels)
        with self._lock:
            values = list(self.histograms.get(metric_name, []))
        
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        
        values.sort()
        count = len(values)
        
        return {
            "count": count,
            "min": values[0],
            "max": values[-1],
            "avg": sum(values) / count,
            "p50": values[int(count * 0.5)],
            "p95": values[int(count * 0.95)],
            "p99": values[int(count * 0.99)]
        }
    
    def get_timing_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get timing statistics."""
        metric_name = self._format_metric_name(name, labels)
        with self._lock:
            values = list(self.timing_metrics.get(metric_name, []))
        
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        
        values.sort()
        count = len(values)
        
        return {
            "count": count,
            "min": values[0],
            "max": values[-1],
            "avg": sum(values) / count,
            "p50": values[int(count * 0.5)] if count > 0 else 0,
            "p95": values[int(count * 0.95)] if count > 0 else 0,
            "p99": values[int(count * 0.99)] if count > 0 else 0
        }
    
    def get_flow_metrics_summary(self, flow_name: str) -> Dict[str, Any]:
        """Get metrics summary for a specific flow."""
        execution_stats = self.get_timing_stats(
            "flow_execution_duration_seconds",
            {"flow": flow_name}
        )
        
        with self._lock:
            flow_specific = self.flow_metrics.get(flow_name, {})
        
        return {
            "flow": flow_name,
            "executions": {
                "total": self.get_counter_value("flow_executions_total", {"flow": flow_name}),
                "successful": self.get_counter_value("flow_executions_success_total", {"flow": flow_name}),
                "failed": self.get_counter_value("flow_executions_failed_total", {"flow": flow_name}),
                "timing": execution_stats
            },
            "flow_specific": flow_specific
        }
    
    def get_service_metrics_summary(self, service_name: str) -> Dict[str, Any]:
        """Get metrics summary for a specific service."""
        health_check_stats = self.get_timing_stats(
            "service_health_check_duration_seconds",
            {"service": service_name}
        )
        
        with self._lock:
            health_tracking = self.service_health_metrics.get(service_name, {})
        
        return {
            "service": service_name,
            "health_checks": {
                "total": self.get_counter_value("service_health_checks_total", {"service": service_name}),
                "successful": self.get_counter_value("service_health_checks_success_total", {"service": service_name}),
                "failed": self.get_counter_value("service_health_checks_failed_total", {"service": service_name}),
                "timing": health_check_stats
            },
            "current_status": self.get_gauge_value("service_health_status", {"service": service_name}),
            "circuit_breaker": {
                "is_open": self.get_gauge_value("circuit_breaker_open", {"service": service_name}) > 0,
                "failure_count": self.get_gauge_value("circuit_breaker_failure_count", {"service": service_name})
            },
            "health_tracking": health_tracking
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # System metrics
        system_metrics = {
            "uptime_seconds": uptime,
            "health_checks": {
                "orchestrator_total": self.get_counter_value("orchestrator_health_checks_total"),
                "orchestrator_successful": self.get_counter_value("orchestrator_health_checks_success_total"),
                "orchestrator_failed": self.get_counter_value("orchestrator_health_checks_failed_total"),
                "service_total": self.get_counter_value("service_health_checks_total"),
                "service_successful": self.get_counter_value("service_health_checks_success_total"),
                "service_failed": self.get_counter_value("service_health_checks_failed_total")
            }
        }
        
        # Flow execution metrics
        flow_execution_timing = self.get_timing_stats("flow_execution_duration_seconds")
        flow_execution_metrics = {
            "executions_total": self.get_counter_value("flow_executions_total"),
            "executions_successful": self.get_counter_value("flow_executions_success_total"),
            "executions_failed": self.get_counter_value("flow_executions_failed_total"),
            "active_flows": self.get_gauge_value("active_flows"),
            "queue_size": self.get_gauge_value("flow_queue_size"),
            "timing": flow_execution_timing
        }
        
        # Event processing metrics
        event_processing_timing = self.get_timing_stats("event_processing_duration_seconds")
        event_metrics = {
            "events_processed_total": self.get_counter_value("events_processed_total"),
            "events_successful": self.get_counter_value("events_processed_success_total"),
            "events_failed": self.get_counter_value("events_processed_failed_total"),
            "timing": event_processing_timing
        }
        
        # Redis metrics
        redis_timing = self.get_timing_stats("redis_operation_duration_seconds")
        redis_metrics = {
            "operations_total": self.get_counter_value("redis_operations_total"),
            "operations_successful": self.get_counter_value("redis_operations_success_total"),
            "operations_failed": self.get_counter_value("redis_operations_failed_total"),
            "timing": redis_timing
        }
        
        # Error metrics
        error_metrics = {
            "total": self.get_counter_value("errors_total")
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_metrics,
            "flow_execution": flow_execution_metrics,
            "event_processing": event_metrics,
            "redis": redis_metrics,
            "errors": error_metrics,
            "orchestrator_status": self.get_gauge_value("orchestrator_health_status")
        }
    
    def get_all_flow_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all flows."""
        with self._lock:
            flow_names = set(self.flow_metrics.keys())
        
        # Also get flow names from counter metrics
        for metric_name in self.counters.keys():
            if "flow_executions_total" in metric_name and "{flow=" in metric_name:
                # Extract flow name from metric label
                start = metric_name.find("flow=") + 5
                end = metric_name.find(",", start)
                if end == -1:
                    end = metric_name.find("}", start)
                if start > 4 and end > start:
                    flow_name = metric_name[start:end]
                    flow_names.add(flow_name)
        
        return {
            flow_name: self.get_flow_metrics_summary(flow_name)
            for flow_name in flow_names
        }
    
    def get_all_service_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all services."""
        with self._lock:
            service_names = set(self.service_health_metrics.keys())
        
        # Also get service names from gauge metrics
        for metric_name in self.gauges.keys():
            if "service_health_status" in metric_name and "{service=" in metric_name:
                # Extract service name from metric label
                start = metric_name.find("service=") + 8
                end = metric_name.find(",", start)
                if end == -1:
                    end = metric_name.find("}", start)
                if start > 7 and end > start:
                    service_name = metric_name[start:end]
                    service_names.add(service_name)
        
        return {
            service_name: self.get_service_metrics_summary(service_name)
            for service_name in service_names
        }
    
    def get_prometheus_metrics(self) -> str:
        """Generate Prometheus-format metrics."""
        lines = []
        
        # Add help and type information
        lines.append("# HELP orchestrator_uptime_seconds Flow orchestrator uptime in seconds")
        lines.append("# TYPE orchestrator_uptime_seconds gauge")
        lines.append(f"orchestrator_uptime_seconds {time.time() - self.start_time}")
        
        lines.append("")
        
        # Export counters
        with self._lock:
            for metric_name, value in self.counters.items():
                # Parse labels from metric name
                if "{" in metric_name:
                    base_name, label_part = metric_name.split("{", 1)
                    labels = "{" + label_part
                else:
                    base_name = metric_name
                    labels = ""
                
                lines.append(f"# TYPE {base_name} counter")
                lines.append(f"{base_name}{labels} {value}")
        
        lines.append("")
        
        # Export gauges
        with self._lock:
            for metric_name, value in self.gauges.items():
                if "{" in metric_name:
                    base_name, label_part = metric_name.split("{", 1)
                    labels = "{" + label_part
                else:
                    base_name = metric_name
                    labels = ""
                
                lines.append(f"# TYPE {base_name} gauge")
                lines.append(f"{base_name}{labels} {value}")
        
        return "\n".join(lines)
    
    def reset_metrics(self) -> None:
        """Reset all metrics (for testing)."""
        with self._lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.timing_metrics.clear()
            self.flow_metrics.clear()
            self.service_health_metrics.clear()
            self.start_time = time.time()
        
        logger.info("Flow orchestrator metrics reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get metrics collector status."""
        with self._lock:
            counter_count = len(self.counters)
            gauge_count = len(self.gauges)
            histogram_count = len(self.histograms)
            timing_count = len(self.timing_metrics)
            flow_count = len(self.flow_metrics)
            service_count = len(self.service_health_metrics)
        
        return {
            "metrics_collected": {
                "counters": counter_count,
                "gauges": gauge_count,
                "histograms": histogram_count,
                "timings": timing_count,
                "flows": flow_count,
                "services": service_count
            },
            "uptime_seconds": time.time() - self.start_time,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat()
        }