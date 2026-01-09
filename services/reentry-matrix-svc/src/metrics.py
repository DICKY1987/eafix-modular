# DOC_ID: DOC-SERVICE-0081
"""
Metrics Collection for Re-entry Matrix Service

Provides comprehensive metrics collection including Prometheus integration,
re-entry specific metrics, and shared library performance tracking.
"""

import time
import asyncio
from typing import Dict, Any, List
from collections import defaultdict, Counter

import structlog
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Collects and exposes metrics for re-entry matrix service."""
    
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
        """Initialize Prometheus metrics for re-entry matrix service."""
        
        # Service lifecycle metrics
        self.prometheus_counters["service_starts"] = PrometheusCounter(
            "reentry_matrix_service_starts_total",
            "Total number of service starts"
        )
        
        # Re-entry processing metrics
        self.prometheus_counters["reentry_requests_total"] = PrometheusCounter(
            "reentry_matrix_requests_total",
            "Total number of re-entry requests processed"
        )
        
        self.prometheus_counters["reentry_decisions_total"] = PrometheusCounter(
            "reentry_matrix_decisions_total", 
            "Total number of re-entry decisions generated",
            ["action", "tier"]
        )
        
        self.prometheus_counters["hybrid_id_operations"] = PrometheusCounter(
            "reentry_matrix_hybrid_id_operations_total",
            "Total hybrid ID operations",
            ["operation_type"]  # compose, parse, validate
        )
        
        self.prometheus_counters["parameter_resolutions"] = PrometheusCounter(
            "reentry_matrix_parameter_resolutions_total",
            "Total parameter resolutions by tier",
            ["resolved_tier"]
        )
        
        # Error tracking
        self.prometheus_counters["reentry_errors"] = PrometheusCounter(
            "reentry_matrix_errors_total",
            "Total number of re-entry processing errors",
            ["error_type"]
        )
        
        self.prometheus_counters["csv_writes_total"] = PrometheusCounter(
            "reentry_matrix_csv_writes_total",
            "Total number of CSV writes"
        )
        
        # Processing time metrics
        self.prometheus_histograms["request_processing_duration"] = Histogram(
            "reentry_matrix_request_processing_duration_seconds",
            "Time spent processing re-entry requests",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
        )
        
        self.prometheus_histograms["decision_processing_duration"] = Histogram(
            "reentry_matrix_decision_processing_duration_seconds",
            "Time spent processing individual decisions",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
        )
        
        self.prometheus_histograms["parameter_resolution_duration"] = Histogram(
            "reentry_matrix_parameter_resolution_duration_seconds",
            "Time spent resolving parameters",
            buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
        )
        
        self.prometheus_histograms["hybrid_id_duration"] = Histogram(
            "reentry_matrix_hybrid_id_duration_seconds",
            "Time spent on hybrid ID operations",
            buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05]
        )
        
        self.prometheus_histograms["csv_write_duration"] = Histogram(
            "reentry_matrix_csv_write_duration_seconds",
            "Time spent writing CSV files",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
        )
        
        # System metrics
        self.prometheus_gauges["uptime_seconds"] = Gauge(
            "reentry_matrix_uptime_seconds",
            "Service uptime in seconds"
        )
        
        self.prometheus_gauges["active_parameter_sets"] = Gauge(
            "reentry_matrix_active_parameter_sets",
            "Number of active parameter sets"
        )
        
        self.prometheus_gauges["csv_sequence_current"] = Gauge(
            "reentry_matrix_csv_sequence_current",
            "Current CSV sequence number"
        )
        
        # Re-entry decision quality metrics
        self.prometheus_histograms["confidence_scores"] = Histogram(
            "reentry_matrix_confidence_scores",
            "Distribution of confidence scores for decisions",
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )
        
        self.prometheus_histograms["lot_size_multipliers"] = Histogram(
            "reentry_matrix_lot_size_multipliers",
            "Distribution of lot size multipliers",
            buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 5.0]
        )
        
        # Shared library performance
        self.prometheus_histograms["vocabulary_validation_duration"] = Histogram(
            "reentry_matrix_vocabulary_validation_duration_seconds",
            "Time spent on vocabulary validation",
            buckets=[0.00001, 0.0001, 0.001, 0.01, 0.1]
        )
        
        logger.info("Initialized Prometheus metrics for re-entry matrix service")
    
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
    
    def record_reentry_processed(self, processing_time: float):
        """Record metrics for a processed re-entry request."""
        self.increment_counter("reentry_requests_total")
        self.record_histogram("request_processing_duration", processing_time)
    
    def record_decision_processed(self, processing_time: float):
        """Record metrics for a processed decision."""
        self.record_histogram("decision_processing_duration", processing_time)
    
    def record_parameter_resolution(self, resolution_time: float, resolved_tier: str):
        """Record metrics for parameter resolution."""
        self.record_histogram("parameter_resolution_duration", resolution_time)
        self.increment_counter("parameter_resolutions", 1, {"resolved_tier": resolved_tier})
    
    def record_hybrid_id_operation(self, operation_type: str, duration: float):
        """Record metrics for hybrid ID operations."""
        self.increment_counter("hybrid_id_operations", 1, {"operation_type": operation_type})
        self.record_histogram("hybrid_id_duration", duration)
    
    def record_csv_write(self, write_time: float):
        """Record metrics for CSV write operations."""
        self.record_histogram("csv_write_duration", write_time)
    
    def record_decision_quality(self, confidence_score: float, lot_size_multiplier: float):
        """Record decision quality metrics."""
        self.record_histogram("confidence_scores", confidence_score)
        self.record_histogram("lot_size_multipliers", lot_size_multiplier)
    
    def record_reentry_decision(self, action: str, tier: str):
        """Record re-entry decision metrics."""
        self.increment_counter("reentry_decisions_total", 1, {
            "action": action,
            "tier": tier
        })
    
    def record_vocabulary_validation(self, validation_time: float):
        """Record vocabulary validation performance."""
        self.record_histogram("vocabulary_validation_duration", validation_time)
    
    def record_error(self, error_type: str):
        """Record an error occurrence."""
        self.increment_counter("reentry_errors", 1, {"error_type": error_type})
    
    def update_active_parameter_sets(self, count: int):
        """Update count of active parameter sets."""
        self.set_gauge("active_parameter_sets", count)
    
    def update_csv_sequence(self, sequence: int):
        """Update current CSV sequence number."""
        self.set_gauge("csv_sequence_current", sequence)
    
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
        
        # Get recent performance stats
        request_stats = self.get_histogram_stats("request_processing_duration")
        decision_stats = self.get_histogram_stats("decision_processing_duration")
        
        return {
            "service": "reentry-matrix-svc",
            "uptime_seconds": uptime,
            "timestamp": time.time(),
            
            "counters": {
                "reentry_requests": self.get_counter_value("reentry_requests_total"),
                "reentry_decisions": self.get_counter_value("reentry_decisions_total"),
                "csv_writes": self.get_counter_value("csv_writes_total"),
                "hybrid_id_operations": self.get_counter_value("hybrid_id_operations"),
                "errors": self.get_counter_value("reentry_errors")
            },
            
            "gauges": {
                "active_parameter_sets": self.get_gauge_value("active_parameter_sets"),
                "csv_sequence": self.get_gauge_value("csv_sequence_current")
            },
            
            "performance": {
                "request_processing": request_stats,
                "decision_processing": decision_stats,
                "parameter_resolution": self.get_histogram_stats("parameter_resolution_duration"),
                "hybrid_id_operations": self.get_histogram_stats("hybrid_id_duration"),
                "csv_writes": self.get_histogram_stats("csv_write_duration")
            },
            
            "quality": {
                "confidence_scores": self.get_histogram_stats("confidence_scores"),
                "lot_size_multipliers": self.get_histogram_stats("lot_size_multipliers")
            }
        }
    
    def get_tier_distribution(self) -> Dict[str, int]:
        """Get distribution of decisions by tier."""
        # This would require tracking tier-specific counters
        # For now, return a placeholder
        return {
            "EXACT": 0,
            "TIER1": 0,
            "TIER2": 0,
            "TIER3": 0,
            "GLOBAL": 0
        }
    
    def get_reentry_action_distribution(self) -> Dict[str, int]:
        """Get distribution of re-entry actions."""
        # This would require tracking action-specific counters
        # For now, return a placeholder
        return {
            "R1": 0,
            "R2": 0,
            "HOLD": 0,
            "NO_REENTRY": 0
        }