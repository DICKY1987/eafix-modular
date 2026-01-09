# DOC_ID: DOC-SERVICE-0053
"""
Event Gateway Configuration

Configuration for event-driven messaging, Redis pub/sub management,
and event routing between EAFIX services.
"""

from pathlib import Path
from pydantic import BaseSettings, Field
from typing import List, Dict, Any, Optional, Set


class Settings(BaseSettings):
    """Event Gateway service settings."""
    
    # Basic service configuration
    service_port: int = Field(8094, description="Service HTTP port")
    log_level: str = Field("INFO", description="Logging level")
    debug_mode: bool = Field(False, description="Enable debug mode")
    
    # Redis configuration
    redis_url: str = Field(
        "redis://localhost:6379", 
        description="Redis connection URL"
    )
    
    redis_pool_max_connections: int = Field(
        50,
        gt=0,
        description="Maximum Redis connection pool size"
    )
    
    # Event gateway configuration
    event_routing_enabled: bool = Field(
        True,
        description="Enable event routing functionality"
    )
    
    event_validation_enabled: bool = Field(
        True,
        description="Enable event schema validation"
    )
    
    event_transformation_enabled: bool = Field(
        True,
        description="Enable event transformation"
    )
    
    # Event topic configuration
    event_topics: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "eafix.price.tick": {
                "description": "Price tick events from data ingestor",
                "schema": "PriceTick@1.0",
                "producers": ["data-ingestor"],
                "consumers": ["indicator-engine", "signal-generator"],
                "retention_hours": 24,
                "max_message_size": 1024
            },
            "eafix.indicators.computed": {
                "description": "Computed indicator events",
                "schema": "IndicatorVector@1.1", 
                "producers": ["indicator-engine"],
                "consumers": ["signal-generator"],
                "retention_hours": 24,
                "max_message_size": 2048
            },
            "eafix.signals.generated": {
                "description": "Generated trading signals",
                "schema": "Signal@1.0",
                "producers": ["signal-generator"],
                "consumers": ["risk-manager", "reporter"],
                "retention_hours": 72,
                "max_message_size": 1024
            },
            "eafix.orders.validated": {
                "description": "Risk-validated order intents",
                "schema": "OrderIntent@1.2",
                "producers": ["risk-manager"],
                "consumers": ["execution-engine"],
                "retention_hours": 168,  # 1 week
                "max_message_size": 2048
            },
            "eafix.execution.completed": {
                "description": "Order execution reports",
                "schema": "ExecutionReport@1.0",
                "producers": ["execution-engine"],
                "consumers": ["reporter", "reentry-matrix-svc"],
                "retention_hours": 8760,  # 1 year
                "max_message_size": 2048
            },
            "eafix.calendar.events": {
                "description": "Economic calendar events",
                "schema": "CalendarEvent@1.0",
                "producers": ["calendar-ingestor"],
                "consumers": ["signal-generator", "risk-manager"],
                "retention_hours": 168,  # 1 week
                "max_message_size": 1024
            },
            "eafix.calendar.signals": {
                "description": "Active calendar signals",
                "schema": "ActiveCalendarSignal@1.0",
                "producers": ["calendar-ingestor"],
                "consumers": ["signal-generator", "transport-router"],
                "retention_hours": 72,
                "max_message_size": 1024
            },
            "eafix.reentry.parameters": {
                "description": "Re-entry parameter decisions",
                "schema": "ReentryParameters@1.0",
                "producers": ["reentry-matrix-svc"],
                "consumers": ["reentry-engine"],
                "retention_hours": 168,  # 1 week
                "max_message_size": 1024
            },
            "eafix.reentry.decisions": {
                "description": "Re-entry trading decisions",
                "schema": "ReentryDecision@1.0",
                "producers": ["reentry-engine"],
                "consumers": ["execution-engine", "transport-router"],
                "retention_hours": 168,  # 1 week
                "max_message_size": 1024
            },
            "eafix.health.metrics": {
                "description": "System health metrics",
                "schema": "HealthMetric@1.0",
                "producers": ["telemetry-daemon"],
                "consumers": ["reporter", "gui-gateway"],
                "retention_hours": 168,  # 1 week
                "max_message_size": 2048
            },
            "eafix.health.alerts": {
                "description": "System health alerts",
                "schema": "HealthAlert@1.0",
                "producers": ["telemetry-daemon"],
                "consumers": ["gui-gateway", "reporter"],
                "retention_hours": 720,  # 30 days
                "max_message_size": 1024
            },
            "eafix.orchestrator.flows": {
                "description": "Flow orchestration events",
                "schema": "FlowEvent@1.0",
                "producers": ["flow-orchestrator"],
                "consumers": ["telemetry-daemon", "gui-gateway"],
                "retention_hours": 72,
                "max_message_size": 2048
            },
            "eafix.orchestrator.status": {
                "description": "Orchestrator status events",
                "schema": "OrchestratorStatus@1.0",
                "producers": ["flow-orchestrator"],
                "consumers": ["telemetry-daemon"],
                "retention_hours": 24,
                "max_message_size": 1024
            },
            "eafix.trade.results": {
                "description": "Trade result events",
                "schema": "TradeResult@1.0",
                "producers": ["reporter"],
                "consumers": ["reentry-matrix-svc"],
                "retention_hours": 8760,  # 1 year
                "max_message_size": 2048
            },
            "eafix.reports.generated": {
                "description": "Generated reports",
                "schema": "Report@1.0",
                "producers": ["reporter"],
                "consumers": ["gui-gateway"],
                "retention_hours": 168,  # 1 week
                "max_message_size": 5120
            }
        },
        description="Event topic definitions with schemas and routing"
    )
    
    # Event routing rules
    event_routing_rules: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=lambda: {
            "PriceTick@1.0": [
                {
                    "condition": "symbol == 'EURUSD'",
                    "target_topics": ["eafix.price.tick.eurusd"],
                    "transform": "add_timestamp"
                },
                {
                    "condition": "always",
                    "target_topics": ["eafix.price.tick"],
                    "transform": "none"
                }
            ],
            "Signal@1.0": [
                {
                    "condition": "confidence_score > 0.8",
                    "target_topics": ["eafix.signals.high_confidence"],
                    "transform": "add_priority_flag"
                },
                {
                    "condition": "always",
                    "target_topics": ["eafix.signals.generated"],
                    "transform": "none"
                }
            ],
            "ExecutionReport@1.0": [
                {
                    "condition": "status == 'FILLED'",
                    "target_topics": ["eafix.execution.filled"],
                    "transform": "extract_fill_info"
                },
                {
                    "condition": "status == 'REJECTED'",
                    "target_topics": ["eafix.execution.rejected"],
                    "transform": "extract_rejection_info"
                },
                {
                    "condition": "always",
                    "target_topics": ["eafix.execution.completed"],
                    "transform": "none"
                }
            ]
        },
        description="Event routing rules with conditions and transformations"
    )
    
    # Message processing configuration
    message_batch_size: int = Field(
        100,
        gt=0,
        description="Batch size for message processing"
    )
    
    message_processing_interval_ms: int = Field(
        50,
        gt=0,
        description="Interval between message processing batches (milliseconds)"
    )
    
    max_message_queue_size: int = Field(
        10000,
        gt=0,
        description="Maximum message queue size per topic"
    )
    
    message_timeout_seconds: int = Field(
        30,
        gt=0,
        description="Message processing timeout"
    )
    
    # Dead letter queue configuration
    dead_letter_enabled: bool = Field(
        True,
        description="Enable dead letter queue for failed messages"
    )
    
    dead_letter_topic_suffix: str = Field(
        ".dlq",
        description="Suffix for dead letter queue topics"
    )
    
    max_retry_attempts: int = Field(
        3,
        ge=0,
        description="Maximum retry attempts for failed messages"
    )
    
    retry_backoff_seconds: int = Field(
        5,
        gt=0,
        description="Retry backoff delay in seconds"
    )
    
    # Event validation configuration
    schema_validation_strict: bool = Field(
        True,
        description="Enable strict schema validation"
    )
    
    schema_registry_enabled: bool = Field(
        True,
        description="Enable schema registry integration"
    )
    
    # Event filtering configuration
    event_filtering_enabled: bool = Field(
        True,
        description="Enable event filtering"
    )
    
    event_filters: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=lambda: {
            "symbol_filter": [
                {"field": "symbol", "operator": "in", "values": ["EURUSD", "GBPUSD", "USDJPY"]},
                {"field": "symbol", "operator": "not_null"}
            ],
            "confidence_filter": [
                {"field": "confidence_score", "operator": ">=", "value": 0.3}
            ],
            "timestamp_filter": [
                {"field": "timestamp", "operator": "recent_minutes", "value": 60}
            ]
        },
        description="Event filtering rules"
    )
    
    # Performance monitoring
    performance_monitoring_enabled: bool = Field(
        True,
        description="Enable performance monitoring"
    )
    
    latency_warning_threshold_ms: int = Field(
        100,
        gt=0,
        description="Warning threshold for message latency (milliseconds)"
    )
    
    latency_critical_threshold_ms: int = Field(
        500,
        gt=0,
        description="Critical threshold for message latency (milliseconds)"
    )
    
    throughput_monitoring_interval_seconds: int = Field(
        60,
        gt=0,
        description="Interval for throughput monitoring"
    )
    
    # Message persistence
    message_persistence_enabled: bool = Field(
        False,  # Disabled by default, Redis handles persistence
        description="Enable message persistence to disk"
    )
    
    output_directory: str = Field(
        "./data/event-gateway",
        description="Directory for event gateway data output"
    )
    
    # Service discovery integration
    service_discovery_enabled: bool = Field(
        True,
        description="Enable service discovery integration"
    )
    
    service_registry_topics: Dict[str, str] = Field(
        default_factory=lambda: {
            "service_up": "eafix.services.up",
            "service_down": "eafix.services.down",
            "service_health": "eafix.services.health"
        },
        description="Service discovery topics"
    )
    
    # Event transformation configuration
    transformation_scripts_enabled: bool = Field(
        True,
        description="Enable JavaScript transformation scripts"
    )
    
    max_transformation_time_ms: int = Field(
        10,
        gt=0,
        description="Maximum time allowed for event transformation (milliseconds)"
    )
    
    # Integration settings
    contracts_directory: str = Field(
        "../../../contracts",
        description="Path to contracts directory"
    )
    
    class Config:
        env_prefix = "EVENT_GATEWAY_"
        env_file = ".env"
    
    def get_output_path(self) -> Path:
        """Get resolved output directory path."""
        return Path(self.output_directory).resolve()
    
    def get_contracts_path(self) -> Path:
        """Get resolved contracts directory path."""
        return Path(self.contracts_directory).resolve()
    
    def get_topic_config(self, topic_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific topic."""
        return self.event_topics.get(topic_name)
    
    def get_topics_for_schema(self, schema: str) -> List[str]:
        """Get topics that use a specific schema."""
        return [
            topic_name for topic_name, config in self.event_topics.items()
            if config.get("schema") == schema
        ]
    
    def get_topics_for_producer(self, producer: str) -> List[str]:
        """Get topics that a service produces to."""
        return [
            topic_name for topic_name, config in self.event_topics.items()
            if producer in config.get("producers", [])
        ]
    
    def get_topics_for_consumer(self, consumer: str) -> List[str]:
        """Get topics that a service consumes from."""
        return [
            topic_name for topic_name, config in self.event_topics.items()
            if consumer in config.get("consumers", [])
        ]
    
    def get_routing_rules(self, event_type: str) -> List[Dict[str, Any]]:
        """Get routing rules for an event type."""
        return self.event_routing_rules.get(event_type, [])
    
    def get_all_topics(self) -> Set[str]:
        """Get all configured topics."""
        topics = set(self.event_topics.keys())
        
        # Add topics from routing rules
        for rules in self.event_routing_rules.values():
            for rule in rules:
                topics.update(rule.get("target_topics", []))
        
        # Add dead letter queue topics
        if self.dead_letter_enabled:
            dlq_topics = {f"{topic}{self.dead_letter_topic_suffix}" for topic in self.event_topics.keys()}
            topics.update(dlq_topics)
        
        return topics
    
    def get_dead_letter_topic(self, original_topic: str) -> str:
        """Get dead letter queue topic name for a topic."""
        return f"{original_topic}{self.dead_letter_topic_suffix}"
    
    def validate_topic_config(self) -> List[str]:
        """Validate topic configuration and return any errors."""
        errors = []
        
        for topic_name, config in self.event_topics.items():
            # Check required fields
            required_fields = ["description", "schema", "producers", "consumers"]
            for field in required_fields:
                if field not in config:
                    errors.append(f"Topic {topic_name} missing required field: {field}")
            
            # Validate retention hours
            retention = config.get("retention_hours", 0)
            if retention <= 0:
                errors.append(f"Topic {topic_name} has invalid retention_hours: {retention}")
            
            # Validate message size
            max_size = config.get("max_message_size", 0)
            if max_size <= 0:
                errors.append(f"Topic {topic_name} has invalid max_message_size: {max_size}")
        
        return errors
    
    def get_event_gateway_config(self) -> Dict[str, Any]:
        """Get event gateway configuration."""
        return {
            "routing_enabled": self.event_routing_enabled,
            "validation_enabled": self.event_validation_enabled,
            "transformation_enabled": self.event_transformation_enabled,
            "dead_letter_enabled": self.dead_letter_enabled,
            "filtering_enabled": self.event_filtering_enabled,
            "performance_monitoring_enabled": self.performance_monitoring_enabled,
            "service_discovery_enabled": self.service_discovery_enabled,
            "total_topics": len(self.event_topics),
            "batch_size": self.message_batch_size,
            "processing_interval_ms": self.message_processing_interval_ms
        }