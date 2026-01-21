# doc_id: DOC-SERVICE-0151
# DOC_ID: DOC-SERVICE-0045
"""
Metrics collection for the Data Ingestor service
"""

import time
from collections import defaultdict, deque
from typing import Dict

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import structlog

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """Prometheus metrics collector for data ingestor"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Metrics
        self.tick_counter = Counter(
            'price_ticks_processed_total',
            'Total number of price ticks processed',
            ['symbol', 'source'],
            registry=self.registry
        )
        
        self.error_counter = Counter(
            'processing_errors_total',
            'Total number of processing errors',
            ['error_type'],
            registry=self.registry
        )
        
        self.processing_duration = Histogram(
            'tick_processing_duration_seconds',
            'Time spent processing each tick',
            ['symbol'],
            registry=self.registry
        )
        
        self.active_connections = Gauge(
            'active_connections',
            'Number of active adapter connections',
            ['adapter_type'],
            registry=self.registry
        )
        
        self.last_tick_timestamp = Gauge(
            'last_tick_timestamp_seconds',
            'Timestamp of the last processed tick',
            registry=self.registry
        )
        
        # Internal metrics tracking
        self.tick_rates = defaultdict(lambda: deque(maxlen=60))  # 1 minute window
        self.symbol_counts = defaultdict(int)
    
    def increment_tick_count(self, symbol: str, source: str = "unknown"):
        """Increment tick counter and update rates"""
        self.tick_counter.labels(symbol=symbol, source=source).inc()
        self.symbol_counts[symbol] += 1
        
        # Track tick rate
        current_time = time.time()
        self.tick_rates[symbol].append(current_time)
        self.last_tick_timestamp.set(current_time)
        
        logger.debug("Tick processed", symbol=symbol, source=source)
    
    def increment_error_count(self, error_type: str):
        """Increment error counter"""
        self.error_counter.labels(error_type=error_type).inc()
        logger.debug("Error recorded", error_type=error_type)
    
    def record_processing_time(self, symbol: str, duration: float):
        """Record processing time for a tick"""
        self.processing_duration.labels(symbol=symbol).observe(duration)
    
    def set_connection_count(self, adapter_type: str, count: int):
        """Set active connection count for adapter type"""
        self.active_connections.labels(adapter_type=adapter_type).set(count)
    
    def get_tick_rate(self, symbol: str = None) -> float:
        """Get current tick rate (ticks per second)"""
        if symbol:
            rates = self.tick_rates[symbol]
        else:
            # Combined rate for all symbols
            rates = deque(maxlen=300)  # 5 minute window for total
            for symbol_rates in self.tick_rates.values():
                rates.extend(symbol_rates)
        
        if len(rates) < 2:
            return 0.0
        
        # Calculate rate over the time window
        time_span = rates[-1] - rates[0]
        return len(rates) / time_span if time_span > 0 else 0.0
    
    def get_total_ticks(self, symbol: str = None) -> int:
        """Get total tick count"""
        if symbol:
            return self.symbol_counts[symbol]
        return sum(self.symbol_counts.values())