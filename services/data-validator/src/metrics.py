"""
Data Validator Metrics Collection

Prometheus-compatible metrics for data validation performance,
quality monitoring, and validation rule effectiveness.
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
import threading

import structlog

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Collects and manages metrics for data validator."""
    
    def __init__(self):
        # Metrics storage
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Timing metrics
        self.timing_metrics: Dict[str, List[float]] = defaultdict(list)
        
        # Validation-specific metrics
        self.validation_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.quality_scores: Dict[str, List[float]] = defaultdict(list)
        
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Start time for uptime calculation
        self.start_time = time.time()
        
        logger.info("Data validator metrics collector initialized")
    
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
    
    # Data validation specific metrics
    
    def record_data_validation(self, schema: str, duration: float, success: bool, quality_score: float) -> None:
        """Record data validation metrics."""
        labels = {"schema": schema}
        
        self.increment_counter("data_validations_total", labels=labels)
        self.record_timing("data_validation_duration_seconds", duration, labels)
        self.observe_histogram("data_quality_score", quality_score, labels)
        
        if success:
            self.increment_counter("data_validations_success_total", labels=labels)
        else:
            self.increment_counter("data_validations_failed_total", labels=labels)
        
        # Track quality scores
        with self._lock:
            self.quality_scores[schema].append(quality_score)
            if len(self.quality_scores[schema]) > 1000:
                self.quality_scores[schema] = self.quality_scores[schema][-1000:]
        
        # Update schema-specific metrics
        with self._lock:
            if schema not in self.validation_metrics:
                self.validation_metrics[schema] = {
                    "total_validations": 0,
                    "successful_validations": 0,
                    "failed_validations": 0,
                    "total_duration": 0.0,
                    "quality_scores": [],
                    "last_validation": None
                }
            
            metrics = self.validation_metrics[schema]
            metrics["total_validations"] += 1
            metrics["total_duration"] += duration
            metrics["last_validation"] = datetime.utcnow().isoformat()
            
            if success:
                metrics["successful_validations"] += 1
            else:
                metrics["failed_validations"] += 1
            
            # Keep recent quality scores
            metrics["quality_scores"].append(quality_score)
            if len(metrics["quality_scores"]) > 100:
                metrics["quality_scores"] = metrics["quality_scores"][-100:]
    
    def record_schema_validation(self, schema: str, rule_name: str, success: bool, duration: float) -> None:
        """Record schema validation rule metrics."""
        labels = {"schema": schema, "rule": rule_name}
        
        self.increment_counter("schema_validations_total", labels=labels)
        self.record_timing("schema_validation_duration_seconds", duration, labels)
        
        if success:
            self.increment_counter("schema_validations_success_total", labels=labels)
        else:
            self.increment_counter("schema_validations_failed_total", labels=labels)
    
    def record_quality_check(self, schema: str, check_name: str, success: bool, duration: float) -> None:
        """Record data quality check metrics."""
        labels = {"schema": schema, "check": check_name}
        
        self.increment_counter("quality_checks_total", labels=labels)
        self.record_timing("quality_check_duration_seconds", duration, labels)
        
        if success:
            self.increment_counter("quality_checks_success_total", labels=labels)
        else:
            self.increment_counter("quality_checks_failed_total", labels=labels)
    
    def record_business_rule_validation(self, schema: str, rule_name: str, success: bool, duration: float) -> None:
        """Record business rule validation metrics."""
        labels = {"schema": schema, "rule": rule_name}
        
        self.increment_counter("business_rules_total", labels=labels)
        self.record_timing("business_rule_duration_seconds", duration, labels)
        
        if success:
            self.increment_counter("business_rules_success_total", labels=labels)
        else:
            self.increment_counter("business_rules_failed_total", labels=labels)
    
    def record_pipeline_validation(self, pipeline_name: str, success: bool, duration: float) -> None:
        """Record pipeline validation metrics."""
        labels = {"pipeline": pipeline_name}
        
        self.increment_counter("pipeline_validations_total", labels=labels)
        self.record_timing("pipeline_validation_duration_seconds", duration, labels)
        
        if success:
            self.increment_counter("pipeline_validations_success_total", labels=labels)
        else:
            self.increment_counter("pipeline_validations_failed_total", labels=labels)
    
    def record_csv_validation(self, file_size_mb: float, row_count: int, success: bool, duration: float) -> None:
        """Record CSV validation metrics."""
        self.increment_counter("csv_validations_total")
        self.record_timing("csv_validation_duration_seconds", duration)
        self.observe_histogram("csv_file_size_mb", file_size_mb)
        self.observe_histogram("csv_row_count", row_count)
        
        if success:
            self.increment_counter("csv_validations_success_total")
        else:
            self.increment_counter("csv_validations_failed_total")
    
    def record_anomaly_detection(self, schema: str, anomalies_detected: int) -> None:
        """Record anomaly detection metrics."""
        labels = {"schema": schema}
        
        self.increment_counter("anomalies_detected_total", anomalies_detected, labels)
        self.set_gauge("current_anomalies", float(anomalies_detected), labels)
    
    def record_data_source_health(self, source_name: str, healthy: bool) -> None:
        """Record data source health metrics."""
        labels = {"source": source_name}
        
        self.increment_counter("data_source_health_checks_total", labels=labels)
        
        if healthy:
            self.increment_counter("data_source_health_checks_success_total", labels=labels)
            self.set_gauge("data_source_health_status", 1.0, labels)
        else:
            self.increment_counter("data_source_health_checks_failed_total", labels=labels)
            self.set_gauge("data_source_health_status", 0.0, labels)
    
    def record_health_check(self, duration: float, success: bool) -> None:
        """Record validator health check metrics."""
        self.increment_counter("validator_health_checks_total")
        self.record_timing("validator_health_check_duration_seconds", duration)
        
        if success:
            self.increment_counter("validator_health_checks_success_total")
            self.set_gauge("validator_health_status", 1.0)
        else:
            self.increment_counter("validator_health_checks_failed_total")
            self.set_gauge("validator_health_status", 0.0)
    
    def record_error(self, error_type: str, context: Optional[str] = None) -> None:
        """Record error occurrence."""
        labels = {"error_type": error_type}
        if context:
            labels["context"] = context
        
        self.increment_counter("errors_total", labels=labels)
    
    def update_validation_queue_size(self, queue_size: int) -> None:
        """Update validation queue size gauge."""
        self.set_gauge("validation_queue_size", float(queue_size))
    
    def update_schema_coverage(self, total_schemas: int, covered_schemas: int) -> None:
        """Update schema coverage metrics."""
        self.set_gauge("total_schemas", float(total_schemas))
        self.set_gauge("covered_schemas", float(covered_schemas))
        
        coverage_percentage = (covered_schemas / total_schemas) * 100 if total_schemas > 0 else 100
        self.set_gauge("schema_coverage_percentage", coverage_percentage)
    
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
    
    def get_quality_score_stats(self, schema: str) -> Dict[str, float]:
        """Get quality score statistics for a schema."""
        with self._lock:
            scores = list(self.quality_scores.get(schema, []))
        
        if not scores:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "latest": 0}
        
        return {
            "count": len(scores),
            "min": min(scores),
            "max": max(scores),
            "avg": sum(scores) / len(scores),
            "latest": scores[-1] if scores else 0
        }
    
    def get_schema_metrics_summary(self, schema: str) -> Dict[str, Any]:
        """Get metrics summary for a specific schema."""
        validation_stats = self.get_timing_stats(
            "data_validation_duration_seconds",
            {"schema": schema}
        )
        
        quality_stats = self.get_quality_score_stats(schema)
        
        with self._lock:
            schema_specific = self.validation_metrics.get(schema, {})
        
        return {
            "schema": schema,
            "validations": {
                "total": self.get_counter_value("data_validations_total", {"schema": schema}),
                "successful": self.get_counter_value("data_validations_success_total", {"schema": schema}),
                "failed": self.get_counter_value("data_validations_failed_total", {"schema": schema}),
                "timing": validation_stats
            },
            "quality_scores": quality_stats,
            "schema_validation": {
                "total": self.get_counter_value("schema_validations_total", {"schema": schema}),
                "successful": self.get_counter_value("schema_validations_success_total", {"schema": schema}),
                "failed": self.get_counter_value("schema_validations_failed_total", {"schema": schema})
            },
            "quality_checks": {
                "total": self.get_counter_value("quality_checks_total", {"schema": schema}),
                "successful": self.get_counter_value("quality_checks_success_total", {"schema": schema}),
                "failed": self.get_counter_value("quality_checks_failed_total", {"schema": schema})
            },
            "business_rules": {
                "total": self.get_counter_value("business_rules_total", {"schema": schema}),
                "successful": self.get_counter_value("business_rules_success_total", {"schema": schema}),
                "failed": self.get_counter_value("business_rules_failed_total", {"schema": schema})
            },
            "schema_specific": schema_specific
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # System metrics
        system_metrics = {
            "uptime_seconds": uptime,
            "health_checks": {
                "validator_total": self.get_counter_value("validator_health_checks_total"),
                "validator_successful": self.get_counter_value("validator_health_checks_success_total"),
                "validator_failed": self.get_counter_value("validator_health_checks_failed_total"),
                "data_source_total": self.get_counter_value("data_source_health_checks_total"),
                "data_source_successful": self.get_counter_value("data_source_health_checks_success_total"),
                "data_source_failed": self.get_counter_value("data_source_health_checks_failed_total")
            }
        }
        
        # Data validation metrics
        validation_timing = self.get_timing_stats("data_validation_duration_seconds")
        validation_metrics = {
            "validations_total": self.get_counter_value("data_validations_total"),
            "validations_successful": self.get_counter_value("data_validations_success_total"),
            "validations_failed": self.get_counter_value("data_validations_failed_total"),
            "validation_queue_size": self.get_gauge_value("validation_queue_size"),
            "timing": validation_timing
        }
        
        # Schema validation metrics
        schema_timing = self.get_timing_stats("schema_validation_duration_seconds")
        schema_metrics = {
            "schema_validations_total": self.get_counter_value("schema_validations_total"),
            "schema_validations_successful": self.get_counter_value("schema_validations_success_total"),
            "schema_validations_failed": self.get_counter_value("schema_validations_failed_total"),
            "timing": schema_timing
        }
        
        # Quality check metrics
        quality_timing = self.get_timing_stats("quality_check_duration_seconds")
        quality_metrics = {
            "quality_checks_total": self.get_counter_value("quality_checks_total"),
            "quality_checks_successful": self.get_counter_value("quality_checks_success_total"),
            "quality_checks_failed": self.get_counter_value("quality_checks_failed_total"),
            "timing": quality_timing
        }
        
        # Business rule validation metrics
        business_timing = self.get_timing_stats("business_rule_duration_seconds")
        business_metrics = {
            "business_rules_total": self.get_counter_value("business_rules_total"),
            "business_rules_successful": self.get_counter_value("business_rules_success_total"),
            "business_rules_failed": self.get_counter_value("business_rules_failed_total"),
            "timing": business_timing
        }
        
        # Pipeline validation metrics
        pipeline_timing = self.get_timing_stats("pipeline_validation_duration_seconds")
        pipeline_metrics = {
            "pipeline_validations_total": self.get_counter_value("pipeline_validations_total"),
            "pipeline_validations_successful": self.get_counter_value("pipeline_validations_success_total"),
            "pipeline_validations_failed": self.get_counter_value("pipeline_validations_failed_total"),
            "timing": pipeline_timing
        }
        
        # CSV validation metrics
        csv_timing = self.get_timing_stats("csv_validation_duration_seconds")
        csv_metrics = {
            "csv_validations_total": self.get_counter_value("csv_validations_total"),
            "csv_validations_successful": self.get_counter_value("csv_validations_success_total"),
            "csv_validations_failed": self.get_counter_value("csv_validations_failed_total"),
            "timing": csv_timing
        }
        
        # Schema coverage metrics
        coverage_metrics = {
            "total_schemas": self.get_gauge_value("total_schemas"),
            "covered_schemas": self.get_gauge_value("covered_schemas"),
            "coverage_percentage": self.get_gauge_value("schema_coverage_percentage")
        }
        
        # Anomaly detection metrics
        anomaly_metrics = {
            "anomalies_detected_total": self.get_counter_value("anomalies_detected_total")
        }
        
        # Error metrics
        error_metrics = {
            "total": self.get_counter_value("errors_total")
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_metrics,
            "data_validation": validation_metrics,
            "schema_validation": schema_metrics,
            "quality_checks": quality_metrics,
            "business_rules": business_metrics,
            "pipeline_validation": pipeline_metrics,
            "csv_validation": csv_metrics,
            "schema_coverage": coverage_metrics,
            "anomaly_detection": anomaly_metrics,
            "errors": error_metrics,
            "validator_status": self.get_gauge_value("validator_health_status")
        }
    
    def get_all_schema_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all validated schemas."""
        with self._lock:
            schema_names = set(self.validation_metrics.keys())
        
        # Also get schema names from counter metrics
        for metric_name in self.counters.keys():
            if "data_validations_total" in metric_name and "{schema=" in metric_name:
                # Extract schema name from metric label
                start = metric_name.find("schema=") + 7
                end = metric_name.find(",", start)
                if end == -1:
                    end = metric_name.find("}", start)
                if start > 6 and end > start:
                    schema_name = metric_name[start:end]
                    schema_names.add(schema_name)
        
        return {
            schema_name: self.get_schema_metrics_summary(schema_name)
            for schema_name in schema_names
        }
    
    def get_prometheus_metrics(self) -> str:
        """Generate Prometheus-format metrics."""
        lines = []
        
        # Add help and type information
        lines.append("# HELP validator_uptime_seconds Data validator uptime in seconds")
        lines.append("# TYPE validator_uptime_seconds gauge")
        lines.append(f"validator_uptime_seconds {time.time() - self.start_time}")
        
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
            self.validation_metrics.clear()
            self.quality_scores.clear()
            self.start_time = time.time()
        
        logger.info("Data validator metrics reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get metrics collector status."""
        with self._lock:
            counter_count = len(self.counters)
            gauge_count = len(self.gauges)
            histogram_count = len(self.histograms)
            timing_count = len(self.timing_metrics)
            schema_count = len(self.validation_metrics)
        
        return {
            "metrics_collected": {
                "counters": counter_count,
                "gauges": gauge_count,
                "histograms": histogram_count,
                "timings": timing_count,
                "schemas": schema_count
            },
            "uptime_seconds": time.time() - self.start_time,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat()
        }