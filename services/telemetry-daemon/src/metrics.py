# DOC_ID: DOC-SERVICE-0091
"""
Metrics Collection System

Prometheus-compatible metrics collection for telemetry daemon performance,
health check statistics, and system monitoring metrics.
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
import threading

import structlog

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Collects and manages metrics for telemetry daemon."""
    
    def __init__(self):
        # Metrics storage
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Timing metrics
        self.timing_metrics: Dict[str, List[float]] = defaultdict(list)
        
        # Service-specific metrics
        self.service_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Start time for uptime calculation
        self.start_time = time.time()
        
        logger.info("Metrics collector initialized")
    
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
    
    # Telemetry-specific metric recording methods
    
    def record_health_collection(self, duration: float, successful_collections: int) -> None:
        """Record health collection cycle metrics."""
        self.increment_counter("health_collection_cycles_total")
        self.record_timing("health_collection_duration_seconds", duration)
        self.set_gauge("successful_health_collections", float(successful_collections))
        
        if successful_collections > 0:
            self.increment_counter("health_collection_success_total")
        else:
            self.increment_counter("health_collection_failure_total")
    
    def record_service_health_check(self, service_name: str, duration: float, success: bool) -> None:
        """Record individual service health check metrics."""
        labels = {"service": service_name}
        
        self.increment_counter("service_health_checks_total", labels=labels)
        self.record_timing("service_health_check_duration_seconds", duration, labels)
        
        if success:
            self.increment_counter("service_health_check_success_total", labels=labels)
            self.set_gauge("service_health_status", 1.0, labels)
        else:
            self.increment_counter("service_health_check_failure_total", labels=labels)
            self.set_gauge("service_health_status", 0.0, labels)
    
    def record_aggregation(self, duration: float) -> None:
        """Record system aggregation metrics."""
        self.increment_counter("system_aggregation_cycles_total")
        self.record_timing("system_aggregation_duration_seconds", duration)
    
    def record_health_check(self, duration: float, success: bool) -> None:
        """Record telemetry daemon health check metrics."""
        self.increment_counter("telemetry_health_checks_total")
        self.record_timing("telemetry_health_check_duration_seconds", duration)
        
        if success:
            self.increment_counter("telemetry_health_check_success_total")
            self.set_gauge("telemetry_health_status", 1.0)
        else:
            self.increment_counter("telemetry_health_check_failure_total")
            self.set_gauge("telemetry_health_status", 0.0)
    
    def record_service_delivery(self, service_name: str, duration: float, success: bool) -> None:
        """Record service delivery metrics."""
        labels = {"service": service_name}
        
        self.increment_counter("service_deliveries_total", labels=labels)
        self.record_timing("service_delivery_duration_seconds", duration, labels)
        
        if success:
            self.increment_counter("service_delivery_success_total", labels=labels)
        else:
            self.increment_counter("service_delivery_failure_total", labels=labels)
    
    def record_file_validation(self, duration: float, success: bool, file_type: str) -> None:
        """Record file validation metrics."""
        labels = {"file_type": file_type}
        
        self.increment_counter("file_validations_total", labels=labels)
        self.record_timing("file_validation_duration_seconds", duration, labels)
        
        if success:
            self.increment_counter("file_validation_success_total", labels=labels)
        else:
            self.increment_counter("file_validation_failure_total", labels=labels)
    
    def record_file_routing(self, duration: float, success: bool, file_type: str) -> None:
        """Record file routing metrics."""
        labels = {"file_type": file_type}
        
        self.increment_counter("file_routing_attempts_total", labels=labels)
        self.record_timing("file_routing_duration_seconds", duration, labels)
        
        if success:
            self.increment_counter("file_routing_success_total", labels=labels)
        else:
            self.increment_counter("file_routing_failure_total", labels=labels)
    
    def record_error(self, error_type: str, service: Optional[str] = None) -> None:
        """Record error occurrence."""
        labels = {"error_type": error_type}
        if service:
            labels["service"] = service
        
        self.increment_counter("errors_total", labels=labels)
    
    def record_csv_write(self, file_type: str, success: bool, duration: Optional[float] = None) -> None:
        """Record CSV write operation metrics."""
        labels = {"file_type": file_type}
        
        self.increment_counter("csv_writes_total", labels=labels)
        
        if success:
            self.increment_counter("csv_write_success_total", labels=labels)
        else:
            self.increment_counter("csv_write_failure_total", labels=labels)
        
        if duration is not None:
            self.record_timing("csv_write_duration_seconds", duration, labels)
    
    def record_alert_generated(self, severity: str, service: str) -> None:
        """Record alert generation metrics."""
        labels = {"severity": severity, "service": service}
        
        self.increment_counter("alerts_generated_total", labels=labels)
        self.increment_counter(f"alerts_{severity}_total")
    
    def record_alert_resolved(self, severity: str, service: str, resolution_time: float) -> None:
        """Record alert resolution metrics."""
        labels = {"severity": severity, "service": service}
        
        self.increment_counter("alerts_resolved_total", labels=labels)
        self.record_timing("alert_resolution_time_seconds", resolution_time, labels)
    
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
    
    def get_service_metrics_summary(self, service_name: str) -> Dict[str, Any]:
        """Get metrics summary for a specific service."""
        health_check_stats = self.get_timing_stats(
            "service_health_check_duration_seconds",
            {"service": service_name}
        )
        
        return {
            "service": service_name,
            "health_checks": {
                "total": self.get_counter_value("service_health_checks_total", {"service": service_name}),
                "successful": self.get_counter_value("service_health_check_success_total", {"service": service_name}),
                "failed": self.get_counter_value("service_health_check_failure_total", {"service": service_name}),
                "timing": health_check_stats
            },
            "current_status": self.get_gauge_value("service_health_status", {"service": service_name}),
            "deliveries": {
                "total": self.get_counter_value("service_deliveries_total", {"service": service_name}),
                "successful": self.get_counter_value("service_delivery_success_total", {"service": service_name}),
                "failed": self.get_counter_value("service_delivery_failure_total", {"service": service_name})
            }
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # System metrics
        system_metrics = {
            "uptime_seconds": uptime,
            "health_checks": {
                "telemetry_total": self.get_counter_value("telemetry_health_checks_total"),
                "telemetry_successful": self.get_counter_value("telemetry_health_check_success_total"),
                "telemetry_failed": self.get_counter_value("telemetry_health_check_failure_total"),
                "service_total": self.get_counter_value("service_health_checks_total"),
                "service_successful": self.get_counter_value("service_health_check_success_total"),
                "service_failed": self.get_counter_value("service_health_check_failure_total")
            }
        }
        
        # Health collection metrics
        health_collection_timing = self.get_timing_stats("health_collection_duration_seconds")
        health_collection_metrics = {
            "cycles_total": self.get_counter_value("health_collection_cycles_total"),
            "cycles_successful": self.get_counter_value("health_collection_success_total"),
            "cycles_failed": self.get_counter_value("health_collection_failure_total"),
            "timing": health_collection_timing
        }
        
        # Aggregation metrics
        aggregation_timing = self.get_timing_stats("system_aggregation_duration_seconds")
        aggregation_metrics = {
            "cycles_total": self.get_counter_value("system_aggregation_cycles_total"),
            "timing": aggregation_timing
        }
        
        # File processing metrics
        file_processing_metrics = {
            "validations": {
                "total": self.get_counter_value("file_validations_total"),
                "successful": self.get_counter_value("file_validation_success_total"),
                "failed": self.get_counter_value("file_validation_failure_total")
            },
            "routing": {
                "attempts": self.get_counter_value("file_routing_attempts_total"),
                "successful": self.get_counter_value("file_routing_success_total"),
                "failed": self.get_counter_value("file_routing_failure_total")
            },
            "csv_writes": {
                "total": self.get_counter_value("csv_writes_total"),
                "successful": self.get_counter_value("csv_write_success_total"),
                "failed": self.get_counter_value("csv_write_failure_total")
            }
        }
        
        # Alert metrics
        alert_metrics = {
            "generated": self.get_counter_value("alerts_generated_total"),
            "resolved": self.get_counter_value("alerts_resolved_total"),
            "by_severity": {
                "critical": self.get_counter_value("alerts_critical_total"),
                "warning": self.get_counter_value("alerts_warning_total"),
                "info": self.get_counter_value("alerts_info_total")
            }
        }
        
        # Error metrics
        error_metrics = {
            "total": self.get_counter_value("errors_total")
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_metrics,
            "health_collection": health_collection_metrics,
            "aggregation": aggregation_metrics,
            "file_processing": file_processing_metrics,
            "alerts": alert_metrics,
            "errors": error_metrics,
            "telemetry_status": self.get_gauge_value("telemetry_health_status")
        }
    
    def get_prometheus_metrics(self) -> str:
        """Generate Prometheus-format metrics."""
        lines = []
        
        # Add help and type information
        lines.append("# HELP telemetry_uptime_seconds Telemetry daemon uptime in seconds")
        lines.append("# TYPE telemetry_uptime_seconds gauge")
        lines.append(f"telemetry_uptime_seconds {time.time() - self.start_time}")
        
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
            self.service_metrics.clear()
            self.start_time = time.time()
        
        logger.info("Metrics reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get metrics collector status."""
        with self._lock:
            counter_count = len(self.counters)
            gauge_count = len(self.gauges)
            histogram_count = len(self.histograms)
            timing_count = len(self.timing_metrics)
        
        return {
            "metrics_collected": {
                "counters": counter_count,
                "gauges": gauge_count,
                "histograms": histogram_count,
                "timings": timing_count
            },
            "uptime_seconds": time.time() - self.start_time,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat()
        }