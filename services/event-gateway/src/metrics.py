# DOC_ID: DOC-SERVICE-0057
"""
Event Gateway Metrics Collection

Prometheus-compatible metrics for event gateway performance,
message processing statistics, and topic monitoring.
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
import threading

import structlog

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Collects and manages metrics for event gateway."""
    
    def __init__(self):
        # Metrics storage
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Timing metrics
        self.timing_metrics: Dict[str, List[float]] = defaultdict(list)
        
        # Topic-specific metrics
        self.topic_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Message processing tracking
        self.message_counts: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)
        
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Start time for uptime calculation
        self.start_time = time.time()
        
        logger.info("Event gateway metrics collector initialized")
    
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
    
    # Event gateway specific metrics
    
    def record_message_enqueued(self, topic: str) -> None:
        """Record message enqueued for processing."""
        labels = {"topic": topic}
        self.increment_counter("messages_enqueued_total", labels=labels)
        
        # Update topic-specific metrics
        with self._lock:
            if topic not in self.topic_metrics:
                self.topic_metrics[topic] = {
                    "messages_enqueued": 0,
                    "messages_processed": 0,
                    "messages_failed": 0,
                    "last_activity": None
                }
            
            self.topic_metrics[topic]["messages_enqueued"] += 1
            self.topic_metrics[topic]["last_activity"] = datetime.utcnow().isoformat()
    
    def record_message_processed(self, topic: str, processing_time: float, success: bool) -> None:
        """Record message processing metrics."""
        labels = {"topic": topic}
        
        self.increment_counter("messages_processed_total", labels=labels)
        self.record_timing("message_processing_duration_seconds", processing_time, labels)
        
        if success:
            self.increment_counter("messages_processed_success_total", labels=labels)
        else:
            self.increment_counter("messages_processed_failed_total", labels=labels)
        
        # Update topic-specific metrics
        with self._lock:
            if topic in self.topic_metrics:
                if success:
                    self.topic_metrics[topic]["messages_processed"] += 1
                else:
                    self.topic_metrics[topic]["messages_failed"] += 1
                self.topic_metrics[topic]["last_activity"] = datetime.utcnow().isoformat()
    
    def record_message_batch_processed(self, topic: str, processed_count: int, 
                                     failed_count: int, batch_duration: float) -> None:
        """Record message batch processing metrics."""
        labels = {"topic": topic}
        
        self.increment_counter("message_batches_processed_total", labels=labels)
        self.record_timing("message_batch_duration_seconds", batch_duration, labels)
        self.observe_histogram("message_batch_size", processed_count + failed_count, labels)
        
        # Record individual message counts
        if processed_count > 0:
            self.increment_counter("messages_processed_success_total", processed_count, labels)
        if failed_count > 0:
            self.increment_counter("messages_processed_failed_total", failed_count, labels)
    
    def record_message_published(self, topic: str) -> None:
        """Record message published to Redis."""
        labels = {"topic": topic}
        self.increment_counter("messages_published_total", labels=labels)
    
    def record_dead_letter_message(self, topic: str) -> None:
        """Record message sent to dead letter queue."""
        labels = {"topic": topic}
        self.increment_counter("dead_letter_messages_total", labels=labels)
    
    def record_event_routed(self, source_topic: str, target_topic: str, success: bool) -> None:
        """Record event routing metrics."""
        labels = {"source_topic": source_topic, "target_topic": target_topic}
        
        self.increment_counter("events_routed_total", labels=labels)
        
        if success:
            self.increment_counter("events_routed_success_total", labels=labels)
        else:
            self.increment_counter("events_routed_failed_total", labels=labels)
    
    def record_event_filtered(self, topic: str, filter_name: str) -> None:
        """Record event filtering metrics."""
        labels = {"topic": topic, "filter": filter_name}
        self.increment_counter("events_filtered_total", labels=labels)
    
    def record_event_transformed(self, topic: str, transformation: str, success: bool) -> None:
        """Record event transformation metrics."""
        labels = {"topic": topic, "transformation": transformation}
        
        self.increment_counter("events_transformed_total", labels=labels)
        
        if success:
            self.increment_counter("events_transformed_success_total", labels=labels)
        else:
            self.increment_counter("events_transformed_failed_total", labels=labels)
    
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
        """Record gateway health check metrics."""
        self.increment_counter("gateway_health_checks_total")
        self.record_timing("gateway_health_check_duration_seconds", duration)
        
        if success:
            self.increment_counter("gateway_health_checks_success_total")
            self.set_gauge("gateway_health_status", 1.0)
        else:
            self.increment_counter("gateway_health_checks_failed_total")
            self.set_gauge("gateway_health_status", 0.0)
    
    def record_error(self, error_type: str, context: Optional[str] = None) -> None:
        """Record error occurrence."""
        labels = {"error_type": error_type}
        if context:
            labels["context"] = context
        
        self.increment_counter("errors_total", labels=labels)
        
        # Update error tracking
        with self._lock:
            key = f"{error_type}:{context}" if context else error_type
            self.error_counts[key] += 1
    
    def update_queue_sizes(self, queue_sizes: Dict[str, int]) -> None:
        """Update message queue size gauges."""
        total_queue_size = 0
        
        for topic, size in queue_sizes.items():
            self.set_gauge("message_queue_size", float(size), {"topic": topic})
            total_queue_size += size
        
        self.set_gauge("total_queue_size", float(total_queue_size))
    
    def update_topic_stats(self, topic_stats: Dict[str, Dict[str, Any]]) -> None:
        """Update topic-level statistics."""
        for topic, stats in topic_stats.items():
            labels = {"topic": topic}
            
            # Update throughput metrics
            if "messages_per_second" in stats:
                self.set_gauge("topic_throughput_messages_per_second", 
                             float(stats["messages_per_second"]), labels)
            
            # Update latency metrics
            if "average_latency_ms" in stats:
                self.set_gauge("topic_latency_avg_ms", 
                             float(stats["average_latency_ms"]), labels)
            
            # Update error rate
            if "error_rate" in stats:
                self.set_gauge("topic_error_rate", float(stats["error_rate"]), labels)
    
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
    
    def get_topic_metrics_summary(self, topic: str) -> Dict[str, Any]:
        """Get metrics summary for a specific topic."""
        processing_stats = self.get_timing_stats(
            "message_processing_duration_seconds",
            {"topic": topic}
        )
        
        with self._lock:
            topic_specific = self.topic_metrics.get(topic, {})
        
        return {
            "topic": topic,
            "messages": {
                "enqueued_total": self.get_counter_value("messages_enqueued_total", {"topic": topic}),
                "processed_total": self.get_counter_value("messages_processed_total", {"topic": topic}),
                "processed_success": self.get_counter_value("messages_processed_success_total", {"topic": topic}),
                "processed_failed": self.get_counter_value("messages_processed_failed_total", {"topic": topic}),
                "published_total": self.get_counter_value("messages_published_total", {"topic": topic}),
                "dead_letter_total": self.get_counter_value("dead_letter_messages_total", {"topic": topic}),
                "current_queue_size": self.get_gauge_value("message_queue_size", {"topic": topic})
            },
            "processing": {
                "timing_stats": processing_stats,
                "batches_processed": self.get_counter_value("message_batches_processed_total", {"topic": topic})
            },
            "events": {
                "routed_total": self.get_counter_value("events_routed_total", {"source_topic": topic}),
                "filtered_total": self.get_counter_value("events_filtered_total", {"topic": topic}),
                "transformed_total": self.get_counter_value("events_transformed_total", {"topic": topic})
            },
            "topic_specific": topic_specific
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # System metrics
        system_metrics = {
            "uptime_seconds": uptime,
            "health_checks": {
                "gateway_total": self.get_counter_value("gateway_health_checks_total"),
                "gateway_successful": self.get_counter_value("gateway_health_checks_success_total"),
                "gateway_failed": self.get_counter_value("gateway_health_checks_failed_total")
            }
        }
        
        # Message processing metrics
        message_processing_timing = self.get_timing_stats("message_processing_duration_seconds")
        message_metrics = {
            "messages_enqueued_total": self.get_counter_value("messages_enqueued_total"),
            "messages_processed_total": self.get_counter_value("messages_processed_total"),
            "messages_processed_success": self.get_counter_value("messages_processed_success_total"),
            "messages_processed_failed": self.get_counter_value("messages_processed_failed_total"),
            "messages_published_total": self.get_counter_value("messages_published_total"),
            "dead_letter_messages_total": self.get_counter_value("dead_letter_messages_total"),
            "total_queue_size": self.get_gauge_value("total_queue_size"),
            "processing_timing": message_processing_timing
        }
        
        # Event processing metrics
        event_metrics = {
            "events_routed_total": self.get_counter_value("events_routed_total"),
            "events_routed_success": self.get_counter_value("events_routed_success_total"),
            "events_routed_failed": self.get_counter_value("events_routed_failed_total"),
            "events_filtered_total": self.get_counter_value("events_filtered_total"),
            "events_transformed_total": self.get_counter_value("events_transformed_total"),
            "events_transformed_success": self.get_counter_value("events_transformed_success_total"),
            "events_transformed_failed": self.get_counter_value("events_transformed_failed_total")
        }
        
        # Redis metrics
        redis_timing = self.get_timing_stats("redis_operation_duration_seconds")
        redis_metrics = {
            "operations_total": self.get_counter_value("redis_operations_total"),
            "operations_successful": self.get_counter_value("redis_operations_success_total"),
            "operations_failed": self.get_counter_value("redis_operations_failed_total"),
            "timing": redis_timing
        }
        
        # Batch processing metrics
        batch_timing = self.get_timing_stats("message_batch_duration_seconds")
        batch_metrics = {
            "batches_processed_total": self.get_counter_value("message_batches_processed_total"),
            "batch_timing": batch_timing
        }
        
        # Error metrics
        with self._lock:
            error_breakdown = dict(self.error_counts)
        
        error_metrics = {
            "total": self.get_counter_value("errors_total"),
            "breakdown": error_breakdown
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_metrics,
            "message_processing": message_metrics,
            "event_processing": event_metrics,
            "batch_processing": batch_metrics,
            "redis": redis_metrics,
            "errors": error_metrics,
            "gateway_status": self.get_gauge_value("gateway_health_status")
        }
    
    def get_all_topic_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all topics."""
        with self._lock:
            topic_names = set(self.topic_metrics.keys())
        
        # Also get topic names from counter metrics
        for metric_name in self.counters.keys():
            if "messages_enqueued_total" in metric_name and "{topic=" in metric_name:
                # Extract topic name from metric label
                start = metric_name.find("topic=") + 6
                end = metric_name.find(",", start)
                if end == -1:
                    end = metric_name.find("}", start)
                if start > 5 and end > start:
                    topic_name = metric_name[start:end]
                    topic_names.add(topic_name)
        
        return {
            topic_name: self.get_topic_metrics_summary(topic_name)
            for topic_name in topic_names
        }
    
    def get_prometheus_metrics(self) -> str:
        """Generate Prometheus-format metrics."""
        lines = []
        
        # Add help and type information
        lines.append("# HELP gateway_uptime_seconds Event gateway uptime in seconds")
        lines.append("# TYPE gateway_uptime_seconds gauge")
        lines.append(f"gateway_uptime_seconds {time.time() - self.start_time}")
        
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
            self.topic_metrics.clear()
            self.message_counts.clear()
            self.error_counts.clear()
            self.start_time = time.time()
        
        logger.info("Event gateway metrics reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get metrics collector status."""
        with self._lock:
            counter_count = len(self.counters)
            gauge_count = len(self.gauges)
            histogram_count = len(self.histograms)
            timing_count = len(self.timing_metrics)
            topic_count = len(self.topic_metrics)
        
        return {
            "metrics_collected": {
                "counters": counter_count,
                "gauges": gauge_count,
                "histograms": histogram_count,
                "timings": timing_count,
                "topics": topic_count
            },
            "uptime_seconds": time.time() - self.start_time,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat()
        }