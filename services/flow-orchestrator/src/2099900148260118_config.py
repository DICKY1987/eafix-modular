# doc_id: DOC-SERVICE-0219
# DOC_ID: DOC-SERVICE-0060
"""
Flow Orchestrator Configuration

Configuration for runtime flow orchestration, event-driven messaging,
and data pipeline coordination across all EAFIX services.
"""

from pathlib import Path
from pydantic import BaseSettings, Field
from typing import List, Dict, Any, Optional


class Settings(BaseSettings):
    """Flow Orchestrator service settings."""
    
    # Basic service configuration
    service_port: int = Field(8093, description="Service HTTP port")
    log_level: str = Field("INFO", description="Logging level")
    debug_mode: bool = Field(False, description="Enable debug mode")
    
    # Redis configuration for event messaging
    redis_url: str = Field(
        "redis://localhost:6379", 
        description="Redis connection URL"
    )
    
    # Flow orchestration configuration
    flow_orchestration_enabled: bool = Field(
        True,
        description="Enable runtime flow orchestration"
    )
    
    flow_monitoring_enabled: bool = Field(
        True,
        description="Enable flow monitoring and metrics"
    )
    
    # Service registry - all services in the EAFIX system
    service_registry: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "data-ingestor": {
                "endpoint": "http://localhost:8081",
                "health_path": "/healthz",
                "role": "data_source",
                "produces": ["PriceTick@1.0"],
                "consumes": [],
                "priority": 1
            },
            "indicator-engine": {
                "endpoint": "http://localhost:8082",
                "health_path": "/healthz",
                "role": "processor",
                "produces": ["IndicatorVector@1.1"],
                "consumes": ["PriceTick@1.0"],
                "priority": 2
            },
            "signal-generator": {
                "endpoint": "http://localhost:8083",
                "health_path": "/healthz",
                "role": "processor",
                "produces": ["Signal@1.0"],
                "consumes": ["PriceTick@1.0", "IndicatorVector@1.1"],
                "priority": 3
            },
            "risk-manager": {
                "endpoint": "http://localhost:8084",
                "health_path": "/healthz",
                "role": "validator",
                "produces": ["OrderIntent@1.2"],
                "consumes": ["Signal@1.0"],
                "priority": 4
            },
            "execution-engine": {
                "endpoint": "http://localhost:8085",
                "health_path": "/healthz",
                "role": "executor",
                "produces": ["ExecutionReport@1.0"],
                "consumes": ["OrderIntent@1.2"],
                "priority": 5
            },
            "calendar-ingestor": {
                "endpoint": "http://localhost:8086",
                "health_path": "/healthz",
                "role": "data_source",
                "produces": ["CalendarEvent@1.0", "ActiveCalendarSignal@1.0"],
                "consumes": [],
                "priority": 1
            },
            "reentry-matrix-svc": {
                "endpoint": "http://localhost:8087",
                "health_path": "/healthz", 
                "role": "processor",
                "produces": ["ReentryParameters@1.0"],
                "consumes": ["TradeResult@1.0"],
                "priority": 3
            },
            "reentry-engine": {
                "endpoint": "http://localhost:8089",
                "health_path": "/healthz",
                "role": "processor", 
                "produces": ["ReentryDecision@1.0"],
                "consumes": ["ReentryParameters@1.0", "TradeResult@1.0"],
                "priority": 4
            },
            "transport-router": {
                "endpoint": "http://localhost:8090",
                "health_path": "/healthz",
                "role": "router",
                "produces": [],
                "consumes": ["ActiveCalendarSignal@1.0", "ReentryDecision@1.0"],
                "priority": 6
            },
            "reporter": {
                "endpoint": "http://localhost:8088",
                "health_path": "/healthz",
                "role": "sink",
                "produces": ["Report@1.0"],
                "consumes": ["ExecutionReport@1.0", "Signal@1.0"],
                "priority": 7
            },
            "gui-gateway": {
                "endpoint": "http://localhost:8080",
                "health_path": "/healthz",
                "role": "gateway",
                "produces": [],
                "consumes": ["*"],
                "priority": 8
            },
            "telemetry-daemon": {
                "endpoint": "http://localhost:8092",
                "health_path": "/healthz",
                "role": "monitor",
                "produces": ["HealthMetric@1.0"],
                "consumes": [],
                "priority": 9
            }
        },
        description="Registry of all services in the system"
    )
    
    # Flow definitions - data pipelines through the system
    flow_definitions: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "price_processing_flow": {
                "name": "Price Data Processing Pipeline",
                "enabled": True,
                "trigger_events": ["PriceTick@1.0"],
                "steps": [
                    {
                        "service": "data-ingestor", 
                        "action": "publish",
                        "event": "PriceTick@1.0",
                        "topics": ["eafix.price.tick"]
                    },
                    {
                        "service": "indicator-engine",
                        "action": "consume_and_process", 
                        "consumes": "PriceTick@1.0",
                        "produces": "IndicatorVector@1.1",
                        "topics": ["eafix.indicators.computed"]
                    },
                    {
                        "service": "signal-generator",
                        "action": "consume_and_process",
                        "consumes": ["PriceTick@1.0", "IndicatorVector@1.1"],
                        "produces": "Signal@1.0", 
                        "topics": ["eafix.signals.generated"]
                    },
                    {
                        "service": "risk-manager",
                        "action": "validate",
                        "consumes": "Signal@1.0",
                        "produces": "OrderIntent@1.2",
                        "topics": ["eafix.orders.validated"]
                    },
                    {
                        "service": "execution-engine",
                        "action": "execute",
                        "consumes": "OrderIntent@1.2",
                        "produces": "ExecutionReport@1.0",
                        "topics": ["eafix.execution.completed"]
                    }
                ],
                "monitoring": {
                    "latency_target_ms": 1000,
                    "success_rate_target": 0.99
                }
            },
            "calendar_processing_flow": {
                "name": "Economic Calendar Processing Pipeline",
                "enabled": True,
                "trigger_events": ["CalendarEvent@1.0"],
                "steps": [
                    {
                        "service": "calendar-ingestor",
                        "action": "publish",
                        "event": "CalendarEvent@1.0", 
                        "topics": ["eafix.calendar.events"]
                    },
                    {
                        "service": "calendar-ingestor",
                        "action": "process_and_publish",
                        "consumes": "CalendarEvent@1.0",
                        "produces": "ActiveCalendarSignal@1.0",
                        "topics": ["eafix.calendar.signals"]
                    },
                    {
                        "service": "transport-router",
                        "action": "route",
                        "consumes": "ActiveCalendarSignal@1.0",
                        "destinations": ["signal-generator", "risk-manager"]
                    }
                ],
                "monitoring": {
                    "latency_target_ms": 500,
                    "success_rate_target": 0.995
                }
            },
            "reentry_processing_flow": {
                "name": "Re-entry Decision Processing Pipeline", 
                "enabled": True,
                "trigger_events": ["TradeResult@1.0"],
                "steps": [
                    {
                        "service": "reentry-matrix-svc",
                        "action": "resolve_parameters",
                        "consumes": "TradeResult@1.0",
                        "produces": "ReentryParameters@1.0",
                        "topics": ["eafix.reentry.parameters"]
                    },
                    {
                        "service": "reentry-engine", 
                        "action": "make_decision",
                        "consumes": ["ReentryParameters@1.0", "TradeResult@1.0"],
                        "produces": "ReentryDecision@1.0",
                        "topics": ["eafix.reentry.decisions"]
                    },
                    {
                        "service": "transport-router",
                        "action": "route",
                        "consumes": "ReentryDecision@1.0",
                        "destinations": ["execution-engine", "reporter"]
                    }
                ],
                "monitoring": {
                    "latency_target_ms": 2000,
                    "success_rate_target": 0.99
                }
            },
            "health_monitoring_flow": {
                "name": "System Health Monitoring Pipeline",
                "enabled": True, 
                "trigger_events": ["periodic"],
                "schedule": "*/30 * * * * *",  # Every 30 seconds
                "steps": [
                    {
                        "service": "telemetry-daemon",
                        "action": "collect_health",
                        "produces": "HealthMetric@1.0",
                        "topics": ["eafix.health.metrics"]
                    },
                    {
                        "service": "telemetry-daemon", 
                        "action": "aggregate_and_alert",
                        "consumes": "HealthMetric@1.0",
                        "topics": ["eafix.health.alerts"]
                    }
                ],
                "monitoring": {
                    "latency_target_ms": 5000,
                    "success_rate_target": 0.95
                }
            }
        },
        description="Flow definitions for data pipelines"
    )
    
    # Event routing configuration
    event_routing_rules: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "PriceTick@1.0": ["eafix.price.tick"],
            "IndicatorVector@1.1": ["eafix.indicators.computed"],
            "Signal@1.0": ["eafix.signals.generated"], 
            "OrderIntent@1.2": ["eafix.orders.validated"],
            "ExecutionReport@1.0": ["eafix.execution.completed"],
            "CalendarEvent@1.0": ["eafix.calendar.events"],
            "ActiveCalendarSignal@1.0": ["eafix.calendar.signals"],
            "ReentryParameters@1.0": ["eafix.reentry.parameters"],
            "ReentryDecision@1.0": ["eafix.reentry.decisions"],
            "HealthMetric@1.0": ["eafix.health.metrics"],
            "TradeResult@1.0": ["eafix.trade.results"],
            "Report@1.0": ["eafix.reports.generated"]
        },
        description="Event to Redis topic routing rules"
    )
    
    # Flow monitoring configuration
    flow_monitoring_interval_seconds: int = Field(
        15,
        gt=0,
        description="Interval for flow monitoring checks"
    )
    
    flow_latency_warning_ms: int = Field(
        2000,
        gt=0,
        description="Warning threshold for flow latency"
    )
    
    flow_latency_critical_ms: int = Field(
        5000,
        gt=0,
        description="Critical threshold for flow latency"
    )
    
    # Service health check configuration
    service_health_check_interval_seconds: int = Field(
        30,
        gt=0,
        description="Interval for service health checks"
    )
    
    service_timeout_seconds: float = Field(
        5.0,
        gt=0.0,
        description="Timeout for service API calls"
    )
    
    # Flow execution configuration
    max_concurrent_flows: int = Field(
        10,
        gt=0,
        description="Maximum concurrent flow executions"
    )
    
    flow_retry_attempts: int = Field(
        3,
        ge=0,
        description="Number of retry attempts for failed flow steps"
    )
    
    flow_timeout_seconds: int = Field(
        30,
        gt=0,
        description="Timeout for individual flow execution"
    )
    
    # Data storage configuration
    output_directory: str = Field(
        "./data/flow-orchestrator",
        description="Directory for flow orchestrator data output"
    )
    
    flow_history_retention_hours: int = Field(
        72,
        gt=0,
        description="Retention period for flow execution history"
    )
    
    # Event publishing configuration
    publish_flow_events: bool = Field(
        True,
        description="Publish flow execution events to Redis"
    )
    
    flow_events_topic: str = Field(
        "eafix.orchestrator.flows",
        description="Redis topic for flow execution events"
    )
    
    orchestrator_events_topic: str = Field(
        "eafix.orchestrator.status",
        description="Redis topic for orchestrator status events"
    )
    
    # Circuit breaker configuration
    circuit_breaker_enabled: bool = Field(
        True,
        description="Enable circuit breaker for service calls"
    )
    
    circuit_breaker_failure_threshold: int = Field(
        5,
        gt=0,
        description="Number of failures before opening circuit"
    )
    
    circuit_breaker_timeout_seconds: int = Field(
        60,
        gt=0,
        description="Circuit breaker timeout before retry"
    )
    
    # Integration settings
    contracts_directory: str = Field(
        "../../../contracts",
        description="Path to contracts directory"
    )
    
    class Config:
        env_prefix = "FLOW_ORCHESTRATOR_"
        env_file = ".env"
    
    def get_output_path(self) -> Path:
        """Get resolved output directory path."""
        return Path(self.output_directory).resolve()
    
    def get_contracts_path(self) -> Path:
        """Get resolved contracts directory path."""
        return Path(self.contracts_directory).resolve()
    
    def get_service_info(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get service information from registry."""
        return self.service_registry.get(service_name)
    
    def get_services_by_role(self, role: str) -> Dict[str, Dict[str, Any]]:
        """Get all services with specific role."""
        return {
            name: info for name, info in self.service_registry.items()
            if info.get("role") == role
        }
    
    def get_service_dependencies(self, service_name: str) -> Dict[str, List[str]]:
        """Get service dependencies (what it produces and consumes)."""
        service_info = self.get_service_info(service_name)
        if not service_info:
            return {"produces": [], "consumes": []}
        
        return {
            "produces": service_info.get("produces", []),
            "consumes": service_info.get("consumes", [])
        }
    
    def get_flow_definition(self, flow_name: str) -> Optional[Dict[str, Any]]:
        """Get flow definition by name."""
        return self.flow_definitions.get(flow_name)
    
    def get_enabled_flows(self) -> Dict[str, Dict[str, Any]]:
        """Get all enabled flow definitions."""
        return {
            name: definition for name, definition in self.flow_definitions.items()
            if definition.get("enabled", False)
        }
    
    def get_event_topics(self, event_type: str) -> List[str]:
        """Get Redis topics for an event type."""
        return self.event_routing_rules.get(event_type, [])
    
    def get_flow_config(self) -> Dict[str, Any]:
        """Get flow orchestration configuration."""
        return {
            "enabled": self.flow_orchestration_enabled,
            "monitoring_enabled": self.flow_monitoring_enabled,
            "monitoring_interval_seconds": self.flow_monitoring_interval_seconds,
            "max_concurrent_flows": self.max_concurrent_flows,
            "flow_timeout_seconds": self.flow_timeout_seconds,
            "retry_attempts": self.flow_retry_attempts
        }
    
    def get_circuit_breaker_config(self) -> Dict[str, Any]:
        """Get circuit breaker configuration."""
        return {
            "enabled": self.circuit_breaker_enabled,
            "failure_threshold": self.circuit_breaker_failure_threshold,
            "timeout_seconds": self.circuit_breaker_timeout_seconds
        }
    
    def validate_flow_definitions(self) -> List[str]:
        """Validate flow definitions and return any errors."""
        errors = []
        
        for flow_name, flow_def in self.flow_definitions.items():
            # Check required fields
            if "steps" not in flow_def:
                errors.append(f"Flow {flow_name} missing required 'steps' field")
                continue
            
            # Validate each step
            for i, step in enumerate(flow_def["steps"]):
                step_id = f"{flow_name}.step[{i}]"
                
                if "service" not in step:
                    errors.append(f"{step_id} missing required 'service' field")
                    continue
                
                service_name = step["service"]
                if service_name not in self.service_registry:
                    errors.append(f"{step_id} references unknown service: {service_name}")
                
                if "action" not in step:
                    errors.append(f"{step_id} missing required 'action' field")
        
        return errors