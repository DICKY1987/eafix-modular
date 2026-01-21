# doc_id: DOC-SERVICE-0160
# DOC_ID: DOC-SERVICE-0075
"""
Metrics Collection for Re-entry Engine Service

Comprehensive metrics for trade result processing, re-entry decisions,
matrix service integration, and atomic CSV write performance.
"""

import time
import asyncio
from typing import Dict, Any, List
from collections import defaultdict, Counter

import structlog
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Collects and exposes metrics for re-entry engine service."""
    
    def __init__(self):
        self.start_time = time.time()
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        
        # Prometheus metrics
        self.prometheus_counters = {}
        self.prometheus_gauges = {}
        self.prometheus_histograms = {}
        
        self._initialize_prometheus_metrics()
    
    def _initialize_prometheus_metrics(self):
        """Initialize Prometheus metrics for re-entry engine service."""
        
        # Service lifecycle metrics
        self.prometheus_counters["service_starts"] = PrometheusCounter(
            "reentry_engine_service_starts_total",
            "Total number of service starts"
        )
        
        # Trade processing metrics
        self.prometheus_counters["trade_results_received"] = PrometheusCounter(
            "reentry_engine_trade_results_received_total",
            "Total number of trade results received"
        )
        
        self.prometheus_counters["trade_results_processed"] = PrometheusCounter(
            "reentry_engine_trade_results_processed_total",
            "Total number of trade results processed",
            ["outcome_class", "duration_class"]
        )
        
        self.prometheus_counters["trade_results_skipped"] = PrometheusCounter(
            "reentry_engine_trade_results_skipped_total",
            "Total number of trade results skipped",
            ["reason"]
        )
        
        # Re-entry decision metrics
        self.prometheus_counters["reentry_decisions_requested"] = PrometheusCounter(
            "reentry_engine_reentry_decisions_requested_total",
            "Total number of re-entry decisions requested from matrix service"
        )
        
        self.prometheus_counters["reentry_decisions_received"] = PrometheusCounter(
            "reentry_engine_reentry_decisions_received_total",
            "Total number of re-entry decisions received",
            ["reentry_action", "resolved_tier"]
        )
        
        # Matrix service integration metrics
        self.prometheus_counters["matrix_service_calls"] = PrometheusCounter(
            "reentry_engine_matrix_service_calls_total",
            "Total number of calls to matrix service",
            ["endpoint", "status"]
        )
        
        self.prometheus_histograms["matrix_service_response_time"] = Histogram(
            "reentry_engine_matrix_service_response_time_seconds",
            "Response time for matrix service calls",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
        )
        
        # Error tracking
        self.prometheus_counters["reentry_errors"] = PrometheusCounter(
            "reentry_engine_errors_total",
            "Total number of re-entry processing errors",
            ["error_type"]
        )
        
        # CSV write metrics
        self.prometheus_counters["csv_writes_total"] = PrometheusCounter(
            "reentry_engine_csv_writes_total",
            "Total number of CSV writes"
        )
        
        self.prometheus_counters["csv_write_failures"] = PrometheusCounter(
            "reentry_engine_csv_write_failures_total",
            "Total number of CSV write failures"
        )
        
        self.prometheus_histograms["csv_write_duration"] = Histogram(
            "reentry_engine_csv_write_duration_seconds",
            "Time spent writing CSV files",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
        )
        
        # Processing time metrics
        self.prometheus_histograms["trade_processing_duration"] = Histogram(
            "reentry_engine_trade_processing_duration_seconds",
            "Time spent processing individual trades",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        self.prometheus_histograms["outcome_classification_duration"] = Histogram(
            "reentry_engine_outcome_classification_duration_seconds",
            "Time spent classifying trade outcomes",
            buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05]
        )
        
        self.prometheus_histograms["duration_classification_duration"] = Histogram(
            "reentry_engine_duration_classification_duration_seconds",
            "Time spent classifying trade durations",
            buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05]
        )
        
        # System metrics
        self.prometheus_gauges["uptime_seconds"] = Gauge(
            "reentry_engine_uptime_seconds",
            "Service uptime in seconds"
        )
        
        self.prometheus_gauges["active_cooldowns"] = Gauge(
            "reentry_engine_active_cooldowns",
            "Number of symbols currently in cooldown"
        )
        
        self.prometheus_gauges["csv_sequence_current"] = Gauge(
            "reentry_engine_csv_sequence_current",
            "Current CSV sequence number"
        )
        
        self.prometheus_gauges["recent_decisions_count"] = Gauge(
            "reentry_engine_recent_decisions_count",
            "Number of recent decisions tracked"
        )
        
        # Quality and performance metrics
        self.prometheus_histograms["confidence_scores"] = Histogram(
            "reentry_engine_confidence_scores",
            "Distribution of confidence scores from matrix service",
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )
        
        self.prometheus_histograms["lot_size_multipliers"] = Histogram(
            "reentry_engine_lot_size_multipliers",
            "Distribution of lot size multipliers",
            buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 5.0]
        )
        
        # Cooldown and eligibility metrics
        self.prometheus_counters["eligibility_checks"] = PrometheusCounter(
            "reentry_engine_eligibility_checks_total",
            "Total number of eligibility checks performed",
            ["result"]  # eligible, ineligible
        )
        
        self.prometheus_counters["cooldown_violations"] = PrometheusCounter(
            "reentry_engine_cooldown_violations_total",
            "Total number of cooldown violations"
        )
        
        self.prometheus_counters["daily_limit_violations"] = PrometheusCounter(
            "reentry_engine_daily_limit_violations_total",
            "Total number of daily limit violations"
        )
        
        # Redis pub/sub metrics
        self.prometheus_counters["redis_messages_received"] = PrometheusCounter(
            "reentry_engine_redis_messages_received_total",
            "Total number of Redis messages received"
        )
        
        self.prometheus_counters["redis_messages_published"] = PrometheusCounter(
            "reentry_engine_redis_messages_published_total",
            "Total number of Redis messages published"
        )
        
        logger.info("Initialized Prometheus metrics for re-entry engine service")
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        # Internal counter
        self.counters[name] += value
        
        # Prometheus counter
        if name in self.prometheus_counters:
            if labels:
                self.prometheus_counters[name].labels(**labels).inc(value)
            else:
                self.prometheus_counters[name].inc(value)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric value."""
        # Internal gauge
        self.gauges[name] = value
        
        # Prometheus gauge
        if name in self.prometheus_gauges:
            if labels:
                self.prometheus_gauges[name].labels(**labels).set(value)
            else:
                self.prometheus_gauges[name].set(value)
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram observation."""
        # Internal histogram
        self.histograms[name].append(value)
        
        # Keep only recent values (last 1000)
        if len(self.histograms[name]) > 1000:
            self.histograms[name] = self.histograms[name][-1000:]
        
        # Prometheus histogram
        if name in self.prometheus_histograms:
            if labels:
                self.prometheus_histograms[name].labels(**labels).observe(value)
            else:
                self.prometheus_histograms[name].observe(value)
    
    def get_uptime(self) -> float:
        """Get service uptime in seconds."""
        uptime = time.time() - self.start_time
        self.set_gauge("uptime_seconds", uptime)
        return uptime
    
    def record_trade_received(self):
        """Record that a trade result was received."""
        self.increment_counter("trade_results_received")
    
    def record_trade_processed(self, processing_time: float, outcome_class: str, duration_class: str):
        """Record metrics for a processed trade result."""
        self.increment_counter("trade_results_processed", 1, {
            "outcome_class": outcome_class,
            "duration_class": duration_class
        })
        self.record_histogram("trade_processing_duration", processing_time)
    
    def record_trade_skipped(self, reason: str):
        """Record that a trade result was skipped."""
        self.increment_counter("trade_results_skipped", 1, {"reason": reason})
    
    def record_reentry_decision_request(self):
        """Record a request for re-entry decision."""
        self.increment_counter("reentry_decisions_requested")
    
    def record_reentry_decision_received(self, reentry_action: str, resolved_tier: str, confidence_score: float):
        """Record a received re-entry decision."""
        self.increment_counter("reentry_decisions_received", 1, {
            "reentry_action": reentry_action,
            "resolved_tier": resolved_tier
        })
        self.record_histogram("confidence_scores", confidence_score)
    
    def record_matrix_service_call(self, endpoint: str, status: str, response_time: float):
        """Record metrics for matrix service calls."""
        self.increment_counter("matrix_service_calls", 1, {
            "endpoint": endpoint,
            "status": status
        })
        self.record_histogram("matrix_service_response_time", response_time)
    
    def record_outcome_classification(self, classification_time: float):
        """Record outcome classification performance."""
        self.record_histogram("outcome_classification_duration", classification_time)
    
    def record_duration_classification(self, classification_time: float):
        """Record duration classification performance."""
        self.record_histogram("duration_classification_duration", classification_time)
    
    def record_csv_write(self, write_time: float, success: bool):
        """Record CSV write metrics."""
        if success:
            self.increment_counter("csv_writes_total")
        else:
            self.increment_counter("csv_write_failures")
        
        self.record_histogram("csv_write_duration", write_time)
    
    def record_eligibility_check(self, eligible: bool):
        """Record eligibility check result."""
        result = "eligible" if eligible else "ineligible"
        self.increment_counter("eligibility_checks", 1, {"result": result})
    
    def record_cooldown_violation(self):
        """Record a cooldown violation."""
        self.increment_counter("cooldown_violations")
    
    def record_daily_limit_violation(self):
        """Record a daily limit violation."""
        self.increment_counter("daily_limit_violations")
    
    def record_redis_message_received(self):
        """Record a Redis message received."""
        self.increment_counter("redis_messages_received")
    
    def record_redis_message_published(self):
        """Record a Redis message published."""
        self.increment_counter("redis_messages_published")
    
    def record_error(self, error_type: str):
        """Record an error occurrence."""
        self.increment_counter("reentry_errors", 1, {"error_type": error_type})
    
    def update_active_cooldowns(self, count: int):
        """Update count of active cooldowns."""
        self.set_gauge("active_cooldowns", count)
    
    def update_csv_sequence(self, sequence: int):
        """Update current CSV sequence number."""
        self.set_gauge("csv_sequence_current", sequence)
    
    def update_recent_decisions_count(self, count: int):
        """Update count of recent decisions."""
        self.set_gauge("recent_decisions_count", count)
    
    def get_counter_value(self, name: str) -> int:
        """Get current counter value."""
        return self.counters.get(name, 0)
    
    def get_gauge_value(self, name: str) -> float:
        """Get current gauge value."""
        return self.gauges.get(name, 0.0)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics."""
        values = self.histograms.get(name, [])
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p95": 0, "p99": 0}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p95": sorted_values[int(count * 0.95)] if count > 0 else 0,
            "p99": sorted_values[int(count * 0.99)] if count > 0 else 0
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        uptime = self.get_uptime()
        
        return {
            "service": "reentry-engine",
            "uptime_seconds": uptime,
            "timestamp": time.time(),
            
            "trade_processing": {
                "trades_received": self.get_counter_value("trade_results_received"),
                "trades_processed": self.get_counter_value("trade_results_processed"),
                "trades_skipped": self.get_counter_value("trade_results_skipped"),
                "processing_time": self.get_histogram_stats("trade_processing_duration")
            },
            
            "reentry_decisions": {
                "decisions_requested": self.get_counter_value("reentry_decisions_requested"),
                "decisions_received": self.get_counter_value("reentry_decisions_received"),
                "confidence_scores": self.get_histogram_stats("confidence_scores")
            },
            
            "matrix_service": {
                "total_calls": self.get_counter_value("matrix_service_calls"),
                "response_time": self.get_histogram_stats("matrix_service_response_time")
            },
            
            "csv_operations": {
                "writes_successful": self.get_counter_value("csv_writes_total"),
                "writes_failed": self.get_counter_value("csv_write_failures"),
                "write_duration": self.get_histogram_stats("csv_write_duration"),
                "current_sequence": self.get_gauge_value("csv_sequence_current")
            },
            
            "eligibility": {
                "eligibility_checks": self.get_counter_value("eligibility_checks"),
                "cooldown_violations": self.get_counter_value("cooldown_violations"),
                "daily_limit_violations": self.get_counter_value("daily_limit_violations"),
                "active_cooldowns": self.get_gauge_value("active_cooldowns")
            },
            
            "redis": {
                "messages_received": self.get_counter_value("redis_messages_received"),
                "messages_published": self.get_counter_value("redis_messages_published")
            },
            
            "errors": {
                "total_errors": self.get_counter_value("reentry_errors")
            },
            
            "system": {
                "recent_decisions_count": self.get_gauge_value("recent_decisions_count")
            }
        }
    
    def get_processing_performance_summary(self) -> Dict[str, Any]:
        """Get processing performance summary."""
        return {
            "trade_processing": self.get_histogram_stats("trade_processing_duration"),
            "outcome_classification": self.get_histogram_stats("outcome_classification_duration"),
            "duration_classification": self.get_histogram_stats("duration_classification_duration"),
            "matrix_service_calls": self.get_histogram_stats("matrix_service_response_time"),
            "csv_writes": self.get_histogram_stats("csv_write_duration")
        }