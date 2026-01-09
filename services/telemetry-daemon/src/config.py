# DOC_ID: DOC-SERVICE-0088
"""
Telemetry Daemon Configuration

Configuration for centralized health monitoring, metrics collection,
system aggregation, and alerting capabilities.
"""

from pathlib import Path
from pydantic import BaseSettings, Field
from typing import List, Dict, Any


class Settings(BaseSettings):
    """Telemetry Daemon service settings."""
    
    # Basic service configuration
    service_port: int = Field(8092, description="Service HTTP port")
    log_level: str = Field("INFO", description="Logging level")
    debug_mode: bool = Field(False, description="Enable debug mode")
    
    # Redis configuration
    redis_url: str = Field(
        "redis://localhost:6379", 
        description="Redis connection URL"
    )
    
    # Health collection configuration
    health_collection_enabled: bool = Field(
        True,
        description="Enable health metrics collection"
    )
    
    health_collection_interval_seconds: int = Field(
        30,
        gt=0,
        description="Interval between health collection cycles"
    )
    
    monitored_services: Dict[str, str] = Field(
        default_factory=lambda: {
            "calendar-ingestor": "http://localhost:8086",
            "reentry-matrix-svc": "http://localhost:8087",
            "reentry-engine": "http://localhost:8089",
            "transport-router": "http://localhost:8090",
            "data-ingestor": "http://localhost:8081",
            "indicator-engine": "http://localhost:8082",
            "signal-generator": "http://localhost:8083",
            "risk-manager": "http://localhost:8084",
            "execution-engine": "http://localhost:8085",
            "reporter": "http://localhost:8088",
            "gui-gateway": "http://localhost:8080"
        },
        description="Services to monitor with their endpoints"
    )
    
    service_timeout_seconds: float = Field(
        5.0,
        gt=0.0,
        description="Timeout for service health checks"
    )
    
    # System aggregation configuration
    system_aggregation_enabled: bool = Field(
        True,
        description="Enable system-wide health aggregation"
    )
    
    aggregation_interval_seconds: int = Field(
        60,
        gt=0,
        description="Interval between system aggregation cycles"
    )
    
    # Alerting configuration
    alerting_enabled: bool = Field(
        True,
        description="Enable alerting system"
    )
    
    alerting_check_interval_seconds: int = Field(
        30,
        gt=0,
        description="Interval between alerting checks"
    )
    
    # Health thresholds
    default_health_thresholds: Dict[str, Dict[str, float]] = Field(
        default_factory=lambda: {
            "response_time_ms": {
                "warning": 1000.0,
                "critical": 5000.0
            },
            "cpu_usage_percent": {
                "warning": 80.0,
                "critical": 95.0
            },
            "memory_usage_percent": {
                "warning": 85.0,
                "critical": 95.0
            },
            "disk_usage_percent": {
                "warning": 80.0,
                "critical": 90.0
            },
            "error_rate_percent": {
                "warning": 5.0,
                "critical": 15.0
            },
            "uptime_hours": {
                "warning": 1.0,  # Less than 1 hour uptime
                "critical": 0.1   # Less than 6 minutes uptime
            }
        },
        description="Default health thresholds for alerting"
    )
    
    # Alert notification configuration
    alert_notifications_enabled: bool = Field(
        False,  # Disabled by default for testing
        description="Enable alert notifications"
    )
    
    notification_channels: List[str] = Field(
        default_factory=lambda: ["console", "redis"],
        description="Alert notification channels"
    )
    
    alert_cooldown_minutes: int = Field(
        15,
        gt=0,
        description="Cooldown period between duplicate alerts"
    )
    
    # Data storage configuration
    output_directory: str = Field(
        "./data/telemetry-daemon",
        description="Directory for telemetry data output"
    )
    
    health_metrics_retention_hours: int = Field(
        72,
        gt=0,
        description="Retention period for health metrics"
    )
    
    alert_history_retention_days: int = Field(
        30,
        gt=0,
        description="Retention period for alert history"
    )
    
    # CSV output for health metrics
    csv_output_enabled: bool = Field(
        True,
        description="Enable CSV output for health metrics"
    )
    
    csv_rotation_hours: int = Field(
        24,
        gt=0,
        description="Hours between CSV file rotation"
    )
    
    # Performance settings
    concurrent_health_checks: int = Field(
        10,
        gt=0,
        description="Maximum concurrent health check operations"
    )
    
    health_check_retry_attempts: int = Field(
        2,
        ge=0,
        description="Number of retry attempts for failed health checks"
    )
    
    health_data_batch_size: int = Field(
        100,
        gt=0,
        description="Batch size for health data processing"
    )
    
    # System health calculation
    service_weight_override: Dict[str, float] = Field(
        default_factory=lambda: {
            "data-ingestor": 1.5,      # Critical for data flow
            "execution-engine": 1.5,   # Critical for trading
            "risk-manager": 1.3,       # Important for safety
            "reentry-engine": 1.2,     # Important for strategy
            "transport-router": 1.1,   # Important for coordination
            "calendar-ingestor": 1.0,  # Standard importance
            "reentry-matrix-svc": 1.0, # Standard importance
            "indicator-engine": 1.0,   # Standard importance
            "signal-generator": 1.0,   # Standard importance
            "reporter": 0.8,           # Less critical
            "gui-gateway": 0.7         # Least critical
        },
        description="Weight override for services in system health calculation"
    )
    
    minimum_healthy_services_percent: float = Field(
        70.0,
        ge=0.0,
        le=100.0,
        description="Minimum percentage of services that must be healthy"
    )
    
    # Monitoring dashboard configuration
    dashboard_refresh_seconds: int = Field(
        15,
        gt=0,
        description="Dashboard refresh interval"
    )
    
    dashboard_history_points: int = Field(
        100,
        gt=0,
        description="Number of historical data points for dashboard charts"
    )
    
    # Integration settings
    contracts_directory: str = Field(
        "../../../contracts",
        description="Path to contracts directory"
    )
    
    # Event publishing
    publish_health_events: bool = Field(
        True,
        description="Publish health events to Redis"
    )
    
    health_events_topic: str = Field(
        "eafix.telemetry.health",
        description="Redis topic for health events"
    )
    
    alert_events_topic: str = Field(
        "eafix.telemetry.alerts",
        description="Redis topic for alert events"
    )
    
    class Config:
        env_prefix = "TELEMETRY_DAEMON_"
        env_file = ".env"
    
    def get_output_path(self) -> Path:
        """Get resolved output directory path."""
        return Path(self.output_directory).resolve()
    
    def get_contracts_path(self) -> Path:
        """Get resolved contracts directory path."""
        return Path(self.contracts_directory).resolve()
    
    def get_service_endpoints(self) -> Dict[str, str]:
        """Get all monitored service endpoints."""
        return self.monitored_services.copy()
    
    def get_health_collection_config(self) -> Dict[str, Any]:
        """Get health collection configuration."""
        return {
            "enabled": self.health_collection_enabled,
            "interval_seconds": self.health_collection_interval_seconds,
            "timeout_seconds": self.service_timeout_seconds,
            "retry_attempts": self.health_check_retry_attempts,
            "concurrent_checks": self.concurrent_health_checks
        }
    
    def get_aggregation_config(self) -> Dict[str, Any]:
        """Get system aggregation configuration."""
        return {
            "enabled": self.system_aggregation_enabled,
            "interval_seconds": self.aggregation_interval_seconds,
            "service_weights": self.service_weight_override,
            "min_healthy_percent": self.minimum_healthy_services_percent
        }
    
    def get_alerting_config(self) -> Dict[str, Any]:
        """Get alerting configuration."""
        return {
            "enabled": self.alerting_enabled,
            "check_interval_seconds": self.alerting_check_interval_seconds,
            "notifications_enabled": self.alert_notifications_enabled,
            "notification_channels": self.notification_channels,
            "cooldown_minutes": self.alert_cooldown_minutes,
            "thresholds": self.default_health_thresholds
        }
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get data storage configuration."""
        return {
            "output_directory": str(self.get_output_path()),
            "csv_output_enabled": self.csv_output_enabled,
            "csv_rotation_hours": self.csv_rotation_hours,
            "health_metrics_retention_hours": self.health_metrics_retention_hours,
            "alert_history_retention_days": self.alert_history_retention_days
        }
    
    def get_dashboard_config(self) -> Dict[str, Any]:
        """Get dashboard configuration."""
        return {
            "refresh_seconds": self.dashboard_refresh_seconds,
            "history_points": self.dashboard_history_points
        }
    
    def validate_paths(self) -> List[str]:
        """Validate all configured paths and return any errors."""
        errors = []
        
        # Check output directory
        output_path = self.get_output_path()
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create output directory {output_path}: {e}")
        elif not output_path.is_dir():
            errors.append(f"Output path {output_path} is not a directory")
        
        # Check contracts directory
        contracts_path = self.get_contracts_path()
        if not contracts_path.exists():
            errors.append(f"Contracts directory does not exist: {contracts_path}")
        
        return errors
    
    def get_service_weight(self, service_name: str) -> float:
        """Get weight for a specific service in system health calculations."""
        return self.service_weight_override.get(service_name, 1.0)