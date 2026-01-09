# DOC_ID: DOC-SERVICE-0058
"""
Flow Monitor Configuration

Configuration for end-to-end flow monitoring, tracing, and performance analysis
across the entire EAFIX trading system pipeline.
"""

from pathlib import Path
from pydantic import BaseSettings, Field
from typing import List, Dict, Any, Optional, Set


class Settings(BaseSettings):
    """Flow Monitor service settings."""
    
    # Basic service configuration
    service_port: int = Field(8096, description="Service HTTP port")
    log_level: str = Field("INFO", description="Logging level")
    debug_mode: bool = Field(False, description="Enable debug mode")
    
    # Redis configuration
    redis_url: str = Field(
        "redis://localhost:6379", 
        description="Redis connection URL"
    )
    
    # Flow monitoring configuration
    flow_monitoring_enabled: bool = Field(
        True,
        description="Enable flow monitoring functionality"
    )
    
    end_to_end_tracing_enabled: bool = Field(
        True,
        description="Enable end-to-end flow tracing"
    )
    
    performance_analysis_enabled: bool = Field(
        True,
        description="Enable performance analysis"
    )
    
    # Monitored flow definitions
    monitored_flows: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "price_to_signal_flow": {
                "name": "Price to Signal Generation Flow",
                "description": "Price tick → Indicators → Signal generation",
                "enabled": True,
                "stages": [
                    {
                        "stage_id": "price_ingestion",
                        "service": "data-ingestor",
                        "event_type": "PriceTick@1.0",
                        "expected_latency_ms": 50,
                        "critical_latency_ms": 200
                    },
                    {
                        "stage_id": "indicator_computation",
                        "service": "indicator-engine",
                        "event_type": "IndicatorVector@1.1",
                        "expected_latency_ms": 500,
                        "critical_latency_ms": 2000
                    },
                    {
                        "stage_id": "signal_generation",
                        "service": "signal-generator",
                        "event_type": "Signal@1.0",
                        "expected_latency_ms": 300,
                        "critical_latency_ms": 1000
                    }
                ],
                "total_expected_latency_ms": 850,
                "total_critical_latency_ms": 3200,
                "success_rate_threshold": 0.95
            },
            "signal_to_execution_flow": {
                "name": "Signal to Execution Flow",
                "description": "Signal → Risk validation → Order execution",
                "enabled": True,
                "stages": [
                    {
                        "stage_id": "signal_processing",
                        "service": "signal-generator",
                        "event_type": "Signal@1.0",
                        "expected_latency_ms": 100,
                        "critical_latency_ms": 500
                    },
                    {
                        "stage_id": "risk_validation",
                        "service": "risk-manager",
                        "event_type": "OrderIntent@1.2",
                        "expected_latency_ms": 200,
                        "critical_latency_ms": 1000
                    },
                    {
                        "stage_id": "order_execution",
                        "service": "execution-engine",
                        "event_type": "ExecutionReport@1.0",
                        "expected_latency_ms": 800,
                        "critical_latency_ms": 3000
                    }
                ],
                "total_expected_latency_ms": 1100,
                "total_critical_latency_ms": 4500,
                "success_rate_threshold": 0.98
            },
            "calendar_impact_flow": {
                "name": "Calendar Event Impact Flow",
                "description": "Calendar event → Signal adjustment → Trading decision",
                "enabled": True,
                "stages": [
                    {
                        "stage_id": "calendar_ingestion",
                        "service": "calendar-ingestor",
                        "event_type": "CalendarEvent@1.0",
                        "expected_latency_ms": 100,
                        "critical_latency_ms": 500
                    },
                    {
                        "stage_id": "calendar_signal_generation",
                        "service": "calendar-ingestor", 
                        "event_type": "ActiveCalendarSignal@1.0",
                        "expected_latency_ms": 200,
                        "critical_latency_ms": 1000
                    },
                    {
                        "stage_id": "signal_adjustment",
                        "service": "signal-generator",
                        "event_type": "Signal@1.0",
                        "expected_latency_ms": 300,
                        "critical_latency_ms": 1500
                    }
                ],
                "total_expected_latency_ms": 600,
                "total_critical_latency_ms": 3000,
                "success_rate_threshold": 0.90
            },
            "reentry_decision_flow": {
                "name": "Re-entry Decision Flow",
                "description": "Trade result → Parameter resolution → Re-entry decision",
                "enabled": True,
                "stages": [
                    {
                        "stage_id": "trade_result_processing",
                        "service": "reporter",
                        "event_type": "TradeResult@1.0",
                        "expected_latency_ms": 200,
                        "critical_latency_ms": 1000
                    },
                    {
                        "stage_id": "parameter_resolution",
                        "service": "reentry-matrix-svc",
                        "event_type": "ReentryParameters@1.0",
                        "expected_latency_ms": 500,
                        "critical_latency_ms": 2000
                    },
                    {
                        "stage_id": "reentry_decision",
                        "service": "reentry-engine",
                        "event_type": "ReentryDecision@1.0",
                        "expected_latency_ms": 800,
                        "critical_latency_ms": 3000
                    }
                ],
                "total_expected_latency_ms": 1500,
                "total_critical_latency_ms": 6000,
                "success_rate_threshold": 0.92
            },
            "system_health_monitoring_flow": {
                "name": "System Health Monitoring Flow",
                "description": "Health collection → Aggregation → Alerting",
                "enabled": True,
                "stages": [
                    {
                        "stage_id": "health_collection",
                        "service": "telemetry-daemon",
                        "event_type": "HealthMetric@1.0",
                        "expected_latency_ms": 1000,
                        "critical_latency_ms": 5000
                    },
                    {
                        "stage_id": "health_aggregation",
                        "service": "telemetry-daemon",
                        "event_type": "HealthMetric@1.0",
                        "expected_latency_ms": 500,
                        "critical_latency_ms": 2000
                    },
                    {
                        "stage_id": "alert_generation",
                        "service": "telemetry-daemon",
                        "event_type": "HealthAlert@1.0",
                        "expected_latency_ms": 200,
                        "critical_latency_ms": 1000
                    }
                ],
                "total_expected_latency_ms": 1700,
                "total_critical_latency_ms": 8000,
                "success_rate_threshold": 0.95
            }
        },
        description="Flow definitions for end-to-end monitoring"
    )
    
    # Flow tracing configuration
    trace_sampling_rate: float = Field(
        1.0,  # Sample all flows initially
        ge=0.0,
        le=1.0,
        description="Trace sampling rate (0.0 to 1.0)"
    )
    
    max_trace_duration_minutes: int = Field(
        60,
        gt=0,
        description="Maximum trace duration before timeout"
    )
    
    trace_retention_hours: int = Field(
        24,
        gt=0,
        description="Trace retention period in hours"
    )
    
    # Performance analysis configuration
    performance_window_minutes: int = Field(
        15,
        gt=0,
        description="Time window for performance analysis"
    )
    
    latency_percentiles: List[float] = Field(
        default_factory=lambda: [0.50, 0.75, 0.90, 0.95, 0.99],
        description="Latency percentiles to calculate"
    )
    
    performance_degradation_threshold: float = Field(
        0.20,  # 20% performance degradation
        gt=0.0,
        le=1.0,
        description="Performance degradation alert threshold"
    )
    
    # Monitoring intervals
    flow_monitoring_interval_seconds: int = Field(
        30,
        gt=0,
        description="Interval for flow monitoring checks"
    )
    
    trace_analysis_interval_seconds: int = Field(
        60,
        gt=0,
        description="Interval for trace analysis"
    )
    
    # Alert configuration
    flow_alerting_enabled: bool = Field(
        True,
        description="Enable flow monitoring alerts"
    )
    
    latency_alert_threshold_multiplier: float = Field(
        1.5,  # Alert if latency is 1.5x expected
        gt=1.0,
        description="Multiplier for latency alert threshold"
    )
    
    success_rate_alert_threshold: float = Field(
        0.90,  # Alert if success rate drops below 90%
        gt=0.0,
        le=1.0,
        description="Success rate threshold for alerts"
    )
    
    # Service registry for monitoring
    monitored_services: Dict[str, Dict[str, str]] = Field(
        default_factory=lambda: {
            "data-ingestor": {
                "endpoint": "http://localhost:8081",
                "health_path": "/healthz"
            },
            "indicator-engine": {
                "endpoint": "http://localhost:8082",
                "health_path": "/healthz"
            },
            "signal-generator": {
                "endpoint": "http://localhost:8083",
                "health_path": "/healthz"
            },
            "risk-manager": {
                "endpoint": "http://localhost:8084",
                "health_path": "/healthz"
            },
            "execution-engine": {
                "endpoint": "http://localhost:8085",
                "health_path": "/healthz"
            },
            "calendar-ingestor": {
                "endpoint": "http://localhost:8086",
                "health_path": "/healthz"
            },
            "reentry-matrix-svc": {
                "endpoint": "http://localhost:8087",
                "health_path": "/healthz"
            },
            "reporter": {
                "endpoint": "http://localhost:8088",
                "health_path": "/healthz"
            },
            "reentry-engine": {
                "endpoint": "http://localhost:8089",
                "health_path": "/healthz"
            },
            "transport-router": {
                "endpoint": "http://localhost:8090",
                "health_path": "/healthz"
            },
            "telemetry-daemon": {
                "endpoint": "http://localhost:8092",
                "health_path": "/healthz"
            },
            "flow-orchestrator": {
                "endpoint": "http://localhost:8093",
                "health_path": "/healthz"
            },
            "event-gateway": {
                "endpoint": "http://localhost:8094",
                "health_path": "/healthz"
            },
            "data-validator": {
                "endpoint": "http://localhost:8095",
                "health_path": "/healthz"
            }
        },
        description="Services to monitor for flow health"
    )
    
    # Event topic monitoring
    monitored_topics: List[str] = Field(
        default_factory=lambda: [
            "eafix.price.tick",
            "eafix.indicators.computed",
            "eafix.signals.generated",
            "eafix.orders.validated",
            "eafix.execution.completed",
            "eafix.calendar.events",
            "eafix.calendar.signals",
            "eafix.reentry.parameters",
            "eafix.reentry.decisions",
            "eafix.health.metrics",
            "eafix.health.alerts",
            "eafix.orchestrator.flows",
            "eafix.trade.results"
        ],
        description="Redis topics to monitor for flow events"
    )
    
    # Data storage configuration
    output_directory: str = Field(
        "./data/flow-monitor",
        description="Directory for flow monitoring data output"
    )
    
    store_trace_data: bool = Field(
        True,
        description="Store trace data for analysis"
    )
    
    generate_flow_reports: bool = Field(
        True,
        description="Generate flow performance reports"
    )
    
    report_generation_interval_hours: int = Field(
        1,
        gt=0,
        description="Interval for generating flow reports"
    )
    
    # Integration settings
    contracts_directory: str = Field(
        "../../../contracts",
        description="Path to contracts directory"
    )
    
    class Config:
        env_prefix = "FLOW_MONITOR_"
        env_file = ".env"
    
    def get_output_path(self) -> Path:
        """Get resolved output directory path."""
        return Path(self.output_directory).resolve()
    
    def get_contracts_path(self) -> Path:
        """Get resolved contracts directory path."""
        return Path(self.contracts_directory).resolve()
    
    def get_flow_config(self, flow_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific flow."""
        return self.monitored_flows.get(flow_name)
    
    def get_enabled_flows(self) -> Dict[str, Dict[str, Any]]:
        """Get all enabled flow configurations."""
        return {
            name: config for name, config in self.monitored_flows.items()
            if config.get("enabled", False)
        }
    
    def get_flow_stages(self, flow_name: str) -> List[Dict[str, Any]]:
        """Get stages for a specific flow."""
        flow_config = self.get_flow_config(flow_name)
        return flow_config.get("stages", []) if flow_config else []
    
    def get_service_info(self, service_name: str) -> Optional[Dict[str, str]]:
        """Get service information from monitored services."""
        return self.monitored_services.get(service_name)
    
    def get_flows_for_service(self, service_name: str) -> List[str]:
        """Get flows that include a specific service."""
        flows = []
        
        for flow_name, flow_config in self.monitored_flows.items():
            stages = flow_config.get("stages", [])
            for stage in stages:
                if stage.get("service") == service_name:
                    flows.append(flow_name)
                    break
        
        return flows
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get flow monitoring configuration."""
        return {
            "flow_monitoring_enabled": self.flow_monitoring_enabled,
            "end_to_end_tracing_enabled": self.end_to_end_tracing_enabled,
            "performance_analysis_enabled": self.performance_analysis_enabled,
            "flow_alerting_enabled": self.flow_alerting_enabled,
            "total_flows": len(self.monitored_flows),
            "enabled_flows": len(self.get_enabled_flows()),
            "monitored_services": len(self.monitored_services),
            "monitored_topics": len(self.monitored_topics),
            "trace_sampling_rate": self.trace_sampling_rate
        }
    
    def validate_flow_config(self) -> List[str]:
        """Validate flow configuration and return any errors."""
        errors = []
        
        for flow_name, flow_config in self.monitored_flows.items():
            # Check required fields
            if "stages" not in flow_config:
                errors.append(f"Flow {flow_name} missing required 'stages' field")
                continue
            
            stages = flow_config["stages"]
            if not stages:
                errors.append(f"Flow {flow_name} has no stages defined")
                continue
            
            # Validate each stage
            for i, stage in enumerate(stages):
                stage_id = f"{flow_name}.stage[{i}]"
                
                required_fields = ["stage_id", "service", "event_type"]
                for field in required_fields:
                    if field not in stage:
                        errors.append(f"{stage_id} missing required field: {field}")
                
                # Check if service exists in monitored services
                service_name = stage.get("service")
                if service_name and service_name not in self.monitored_services:
                    errors.append(f"{stage_id} references unknown service: {service_name}")
                
                # Validate latency thresholds
                expected_latency = stage.get("expected_latency_ms", 0)
                critical_latency = stage.get("critical_latency_ms", 0)
                
                if expected_latency <= 0:
                    errors.append(f"{stage_id} has invalid expected_latency_ms: {expected_latency}")
                
                if critical_latency <= expected_latency:
                    errors.append(f"{stage_id} critical_latency_ms must be greater than expected_latency_ms")
        
        return errors