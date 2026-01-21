# doc_id: DOC-SERVICE-0184
# DOC_ID: DOC-SERVICE-0096
"""
Metrics Collection for Transport Router Service

Comprehensive metrics for file watching, validation, routing,
and downstream service coordination.
"""

import time
import asyncio
from typing import Dict, Any, List
from collections import defaultdict, Counter

import structlog
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Collects and exposes metrics for transport router service."""
    
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
        """Initialize Prometheus metrics for transport router service."""
        
        # Service lifecycle metrics
        self.prometheus_counters["service_starts"] = PrometheusCounter(
            "transport_router_service_starts_total",
            "Total number of service starts"
        )
        
        # File watching metrics
        self.prometheus_counters["file_events_generated"] = PrometheusCounter(
            "transport_router_file_events_generated_total",
            "Total number of file events generated"
        )
        
        self.prometheus_counters["files_processed"] = PrometheusCounter(
            "transport_router_files_processed_total",
            "Total number of files processed",
            ["file_type"]
        )
        
        self.prometheus_counters["files_skipped"] = PrometheusCounter(
            "transport_router_files_skipped_total",
            "Total number of files skipped",
            ["reason"]
        )
        
        # Validation metrics
        self.prometheus_counters["validations_performed"] = PrometheusCounter(
            "transport_router_validations_performed_total",
            "Total number of validations performed",
            ["file_type", "result"]  # result: success, failure
        )
        
        self.prometheus_counters["validation_errors"] = PrometheusCounter(
            "transport_router_validation_errors_total",
            "Total number of validation errors",
            ["error_type", "file_type"]  # checksum, sequence, schema
        )
        
        self.prometheus_histograms["validation_duration"] = Histogram(
            "transport_router_validation_duration_seconds",
            "Time spent validating files",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
        )
        
        # Routing metrics
        self.prometheus_counters["routing_attempts"] = PrometheusCounter(
            "transport_router_routing_attempts_total",
            "Total number of routing attempts",
            ["file_type", "result"]  # result: success, failure
        )
        
        self.prometheus_counters["service_deliveries"] = PrometheusCounter(
            "transport_router_service_deliveries_total",
            "Total number of service deliveries",
            ["service_name", "result"]  # result: success, failure
        )
        
        self.prometheus_histograms["routing_duration"] = Histogram(
            "transport_router_routing_duration_seconds",
            "Time spent routing files",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
        )
        
        self.prometheus_histograms["service_delivery_duration"] = Histogram(
            "transport_router_service_delivery_duration_seconds",
            "Time spent delivering files to services",
            ["service_name"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
        )
        
        # Error tracking
        self.prometheus_counters["transport_errors"] = PrometheusCounter(
            "transport_router_errors_total",
            "Total number of transport router errors",
            ["error_type"]
        )
        
        # Event publishing metrics
        self.prometheus_counters["events_published"] = PrometheusCounter(
            "transport_router_events_published_total",
            "Total number of events published to Redis"
        )
        
        # System metrics
        self.prometheus_gauges["uptime_seconds"] = Gauge(
            "transport_router_uptime_seconds",
            "Service uptime in seconds"
        )
        
        self.prometheus_gauges["watched_directories"] = Gauge(
            "transport_router_watched_directories",
            "Number of directories being watched"
        )
        
        self.prometheus_gauges["downstream_services"] = Gauge(
            "transport_router_downstream_services",
            "Number of configured downstream services"
        )
        
        self.prometheus_gauges["healthy_services"] = Gauge(
            "transport_router_healthy_services",
            "Number of healthy downstream services"
        )
        
        # File system metrics
        self.prometheus_gauges["total_csv_files"] = Gauge(
            "transport_router_total_csv_files",
            "Total number of CSV files in watched directories"
        )
        
        self.prometheus_histograms["file_sizes"] = Histogram(
            "transport_router_file_sizes_mb",
            "Distribution of processed file sizes in MB",
            buckets=[0.001, 0.01, 0.1, 1, 10, 50, 100, 500]
        )
        
        # Processing performance metrics
        self.prometheus_histograms["file_processing_duration"] = Histogram(
            "transport_router_file_processing_duration_seconds",
            "Total time to process a file (validation + routing)",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        # Cache metrics
        self.prometheus_gauges["validation_cache_size"] = Gauge(
            "transport_router_validation_cache_size",
            "Number of entries in validation cache"
        )
        
        # Queue metrics
        self.prometheus_gauges["pending_file_events"] = Gauge(
            "transport_router_pending_file_events",
            "Number of pending file events to process"
        )
        
        # Quality metrics
        self.prometheus_histograms["checksum_validation_rate"] = Histogram(
            "transport_router_checksum_validation_rate",
            "Success rate of checksum validations",
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
        )
        
        self.prometheus_histograms["routing_success_rate"] = Histogram(
            "transport_router_routing_success_rate",
            "Success rate of file routing attempts",
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
        )
        
        logger.info("Initialized Prometheus metrics for transport router service")
    
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
    
    def record_file_processed(self, file_type: str):
        """Record that a file was processed."""
        self.increment_counter("files_processed", 1, {"file_type": file_type})
    
    def record_file_skipped(self, reason: str):
        """Record that a file was skipped."""
        self.increment_counter("files_skipped", 1, {"reason": reason})
    
    def record_file_validation(self, validation_time: float, success: bool, 
                              file_type: str = "unknown"):
        """Record file validation metrics."""
        result = "success" if success else "failure"
        self.increment_counter("validations_performed", 1, {
            "file_type": file_type,
            "result": result
        })
        self.record_histogram("validation_duration", validation_time)
    
    def record_validation_error(self, error_type: str, file_type: str = "unknown"):
        """Record validation error."""
        self.increment_counter("validation_errors", 1, {
            "error_type": error_type,
            "file_type": file_type
        })
    
    def record_file_routing(self, routing_time: float, success: bool, 
                           file_type: str = "unknown"):
        """Record file routing metrics."""
        result = "success" if success else "failure"
        self.increment_counter("routing_attempts", 1, {
            "file_type": file_type,
            "result": result
        })
        self.record_histogram("routing_duration", routing_time)
    
    def record_service_delivery(self, service_name: str, delivery_time: float, 
                               success: bool):
        """Record service delivery metrics."""
        result = "success" if success else "failure"
        self.increment_counter("service_deliveries", 1, {
            "service_name": service_name,
            "result": result
        })
        self.record_histogram("service_delivery_duration", delivery_time, {
            "service_name": service_name
        })
    
    def record_file_size(self, size_mb: float):
        """Record processed file size."""
        self.record_histogram("file_sizes", size_mb)
    
    def record_file_processing(self, processing_time: float):
        """Record total file processing time."""
        self.record_histogram("file_processing_duration", processing_time)
    
    def record_checksum_validation_rate(self, success_rate: float):
        """Record checksum validation success rate."""
        self.record_histogram("checksum_validation_rate", success_rate)
    
    def record_routing_success_rate(self, success_rate: float):
        """Record routing success rate."""
        self.record_histogram("routing_success_rate", success_rate)
    
    def record_error(self, error_type: str):
        """Record an error occurrence."""
        self.increment_counter("transport_errors", 1, {"error_type": error_type})
    
    def update_watched_directories(self, count: int):
        """Update count of watched directories."""
        self.set_gauge("watched_directories", count)
    
    def update_downstream_services(self, total: int, healthy: int):
        """Update downstream service counts."""
        self.set_gauge("downstream_services", total)
        self.set_gauge("healthy_services", healthy)
    
    def update_total_csv_files(self, count: int):
        """Update total CSV files count."""
        self.set_gauge("total_csv_files", count)
    
    def update_validation_cache_size(self, size: int):
        """Update validation cache size."""
        self.set_gauge("validation_cache_size", size)
    
    def update_pending_file_events(self, count: int):
        """Update pending file events count."""
        self.set_gauge("pending_file_events", count)
    
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
            "service": "transport-router",
            "uptime_seconds": uptime,
            "timestamp": time.time(),
            
            "file_processing": {
                "files_processed": self.get_counter_value("files_processed"),
                "files_skipped": self.get_counter_value("files_skipped"),
                "file_events_generated": self.get_counter_value("file_events_generated"),
                "processing_duration": self.get_histogram_stats("file_processing_duration")
            },
            
            "validation": {
                "validations_performed": self.get_counter_value("validations_performed"),
                "validation_errors": self.get_counter_value("validation_errors"),
                "validation_duration": self.get_histogram_stats("validation_duration"),
                "cache_size": self.get_gauge_value("validation_cache_size")
            },
            
            "routing": {
                "routing_attempts": self.get_counter_value("routing_attempts"),
                "service_deliveries": self.get_counter_value("service_deliveries"),
                "routing_duration": self.get_histogram_stats("routing_duration"),
                "service_delivery_duration": self.get_histogram_stats("service_delivery_duration")
            },
            
            "system": {
                "watched_directories": self.get_gauge_value("watched_directories"),
                "downstream_services": self.get_gauge_value("downstream_services"),
                "healthy_services": self.get_gauge_value("healthy_services"),
                "total_csv_files": self.get_gauge_value("total_csv_files"),
                "pending_file_events": self.get_gauge_value("pending_file_events")
            },
            
            "quality": {
                "checksum_validation_rate": self.get_histogram_stats("checksum_validation_rate"),
                "routing_success_rate": self.get_histogram_stats("routing_success_rate"),
                "file_sizes": self.get_histogram_stats("file_sizes")
            },
            
            "events": {
                "events_published": self.get_counter_value("events_published")
            },
            
            "errors": {
                "total_errors": self.get_counter_value("transport_errors")
            }
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance-focused metrics summary."""
        return {
            "file_processing": self.get_histogram_stats("file_processing_duration"),
            "validation": self.get_histogram_stats("validation_duration"),
            "routing": self.get_histogram_stats("routing_duration"),
            "service_delivery": self.get_histogram_stats("service_delivery_duration"),
            "file_sizes": self.get_histogram_stats("file_sizes")
        }