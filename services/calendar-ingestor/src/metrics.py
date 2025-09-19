"""
Calendar Ingestor Metrics Collection
"""

import time
from typing import Dict, Any
from collections import defaultdict, Counter
import structlog
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Collects and exposes metrics for calendar ingestor service"""
    
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
        """Initialize Prometheus metrics"""
        
        # Calendar processing metrics
        self.prometheus_counters["calendar_events_processed"] = PrometheusCounter(
            "calendar_events_processed_total",
            "Total number of calendar events processed"
        )
        
        self.prometheus_counters["calendar_signals_generated"] = PrometheusCounter(
            "calendar_signals_generated_total", 
            "Total number of calendar signals generated"
        )
        
        self.prometheus_counters["calendar_signals_written"] = PrometheusCounter(
            "calendar_signals_written_total",
            "Total number of signals written to CSV"
        )
        
        self.prometheus_counters["calendar_errors"] = PrometheusCounter(
            "calendar_errors_total",
            "Total number of calendar processing errors",
            ["error_type"]
        )
        
        # Processing time metrics
        self.prometheus_histograms["event_processing_duration"] = Histogram(
            "calendar_event_processing_duration_seconds",
            "Time spent processing calendar events",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        )
        
        self.prometheus_histograms["csv_write_duration"] = Histogram(
            "calendar_csv_write_duration_seconds",
            "Time spent writing CSV files",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
        )
        
        # System metrics
        self.prometheus_gauges["active_signals_count"] = Gauge(
            "calendar_active_signals_count",
            "Current number of active calendar signals"
        )
        
        self.prometheus_gauges["uptime_seconds"] = Gauge(
            "calendar_ingestor_uptime_seconds",
            "Service uptime in seconds"
        )
        
        # Signal quality metrics
        self.prometheus_histograms["signal_confidence_score"] = Histogram(
            "calendar_signal_confidence_score",
            "Distribution of signal confidence scores",
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )
        
        logger.info("Initialized Prometheus metrics for calendar ingestor")
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        # Internal counter
        self.counters[name] += value
        
        # Prometheus counter
        if name in self.prometheus_counters:
            if labels:
                self.prometheus_counters[name].labels(**labels).inc(value)
            else:
                self.prometheus_counters[name].inc(value)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric value"""
        # Internal gauge
        self.gauges[name] = value
        
        # Prometheus gauge
        if name in self.prometheus_gauges:
            if labels:
                self.prometheus_gauges[name].labels(**labels).set(value)
            else:
                self.prometheus_gauges[name].set(value)
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram observation"""
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
        """Get service uptime in seconds"""
        uptime = time.time() - self.start_time
        self.set_gauge("uptime_seconds", uptime)
        return uptime
    
    def get_counter_value(self, name: str) -> int:
        """Get current counter value"""
        return self.counters.get(name, 0)
    
    def get_gauge_value(self, name: str) -> float:
        """Get current gauge value"""
        return self.gauges.get(name, 0.0)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics"""
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
        """Get comprehensive metrics summary"""
        uptime = self.get_uptime()
        
        return {
            "service": "calendar-ingestor",
            "uptime_seconds": uptime,
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                name: self.get_histogram_stats(name) 
                for name in self.histograms.keys()
            },
            "timestamp": time.time()
        }
    
    def record_event_processed(self, processing_time: float, signals_generated: int):
        """Record metrics for a processed calendar event"""
        self.increment_counter("calendar_events_processed")
        self.increment_counter("calendar_signals_generated", signals_generated)
        self.record_histogram("event_processing_duration", processing_time)
    
    def record_csv_write(self, write_time: float, signal_count: int):
        """Record metrics for CSV write operation"""
        self.increment_counter("calendar_signals_written", signal_count)
        self.record_histogram("csv_write_duration", write_time)
    
    def record_error(self, error_type: str):
        """Record an error occurrence"""
        self.increment_counter("calendar_errors", 1, {"error_type": error_type})
    
    def update_active_signals_count(self, count: int):
        """Update the count of currently active signals"""
        self.set_gauge("active_signals_count", count)
    
    def record_signal_confidence(self, confidence_score: float):
        """Record signal confidence score for quality metrics"""
        self.record_histogram("signal_confidence_score", confidence_score)