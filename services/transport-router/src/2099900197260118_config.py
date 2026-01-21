# doc_id: DOC-SERVICE-0181
# DOC_ID: DOC-SERVICE-0093
"""
Transport Router Configuration

Configuration for CSV file routing, integrity validation, file watching,
and downstream service coordination.
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Dict, Any


class Settings(BaseSettings):
    """Transport Router service settings."""

    model_config = SettingsConfigDict(
        env_prefix="TRANSPORT_ROUTER_",
        env_file=".env",
    )
    
    # Basic service configuration
    service_port: int = Field(8090, description="Service HTTP port")
    log_level: str = Field("INFO", description="Logging level")
    debug_mode: bool = Field(False, description="Enable debug mode")
    
    # Redis configuration
    redis_url: str = Field(
        "redis://localhost:6379", 
        description="Redis connection URL"
    )
    
    # Event publishing
    publish_file_events: bool = Field(
        True,
        description="Publish file processing events to Redis"
    )
    
    file_events_topic: str = Field(
        "eafix.transport.files",
        description="Redis topic for file processing events"
    )
    
    # File watching configuration
    file_watching_enabled: bool = Field(
        True,
        description="Enable file system watching"
    )
    
    watched_directories: List[str] = Field(
        default_factory=lambda: [
            "./data/calendar-ingestor",
            "./data/reentry-engine", 
            "./data/reentry-matrix",
            "./data/execution-engine"
        ],
        description="Directories to watch for CSV files"
    )
    
    watch_recursive: bool = Field(
        True,
        description="Watch directories recursively"
    )
    
    watch_file_patterns: List[str] = Field(
        default_factory=lambda: ["*.csv"],
        description="File patterns to watch"
    )
    
    # File validation settings
    validate_all_files: bool = Field(
        True,
        description="Validate all discovered CSV files"
    )
    
    checksum_validation_enabled: bool = Field(
        True,
        description="Validate CSV checksums"
    )
    
    sequence_validation_enabled: bool = Field(
        True,
        description="Validate CSV sequence numbers"
    )
    
    schema_validation_enabled: bool = Field(
        True,
        description="Validate CSV against contract schemas"
    )
    
    # Routing configuration
    routing_enabled: bool = Field(
        True,
        description="Enable automatic file routing"
    )
    
    default_routing_rules: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "ActiveCalendarSignal": ["signal-analyzer", "risk-manager"],
            "ReentryDecision": ["execution-engine", "reporter"],
            "TradeResult": ["reentry-engine", "reporter"],
            "HealthMetric": ["telemetry-daemon", "reporter"]
        },
        description="Default routing rules by file type"
    )
    
    # Downstream service configuration
    service_endpoints: Dict[str, str] = Field(
        default_factory=lambda: {
            "signal-analyzer": "http://localhost:8091",
            "risk-manager": "http://localhost:8084",
            "execution-engine": "http://localhost:8085",
            "reporter": "http://localhost:8088",
            "reentry-engine": "http://localhost:8089",
            "telemetry-daemon": "http://localhost:8092"
        },
        description="Downstream service endpoints"
    )
    
    service_timeout_seconds: float = Field(
        10.0,
        gt=0.0,
        description="Timeout for downstream service calls"
    )
    
    # File processing settings
    process_existing_files_on_startup: bool = Field(
        False,
        description="Process existing files when service starts"
    )
    
    file_processing_delay_seconds: float = Field(
        1.0,
        ge=0.0,
        description="Delay before processing file events (allows writes to complete)"
    )
    
    max_file_size_mb: int = Field(
        100,
        gt=0,
        description="Maximum file size to process (MB)"
    )
    
    ignore_temp_files: bool = Field(
        True,
        description="Ignore temporary files (.tmp, .temp, etc.)"
    )
    
    # Retry and reliability settings
    max_retry_attempts: int = Field(
        3,
        ge=1,
        description="Maximum retry attempts for failed operations"
    )
    
    retry_delay_seconds: float = Field(
        2.0,
        gt=0.0,
        description="Delay between retry attempts"
    )
    
    dead_letter_directory: str = Field(
        "./data/transport-router/dead-letters",
        description="Directory for files that failed processing"
    )
    
    # Performance settings
    concurrent_processing_limit: int = Field(
        10,
        gt=0,
        description="Maximum concurrent file processing operations"
    )
    
    batch_processing_enabled: bool = Field(
        False,
        description="Enable batch processing of multiple files"
    )
    
    batch_size: int = Field(
        5,
        gt=0,
        description="Number of files to process in a batch"
    )
    
    batch_timeout_seconds: float = Field(
        30.0,
        gt=0.0,
        description="Maximum time to wait for batch to fill"
    )
    
    # Health check settings
    health_check_interval_seconds: int = Field(
        30,
        gt=0,
        description="Health check interval in seconds"
    )
    
    downstream_health_check_enabled: bool = Field(
        True,
        description="Check health of downstream services"
    )
    
    # Metrics and monitoring
    metrics_enabled: bool = Field(True, description="Enable metrics collection")
    metrics_retention_hours: int = Field(24, gt=0, description="Metrics retention period")
    
    track_file_history: bool = Field(
        True,
        description="Track history of processed files"
    )
    
    file_history_retention_hours: int = Field(
        72,
        gt=0,
        description="File history retention period in hours"
    )
    
    # Contracts integration
    contracts_directory: str = Field(
        "../../../contracts",
        description="Path to contracts directory"
    )
    
    shared_library_path: str = Field(
        "../../../shared/reentry",
        description="Path to shared re-entry library"
    )
    
    # Output settings
    output_directory: str = Field(
        "./data/transport-router",
        description="Directory for service output files"
    )
    
    def get_output_path(self) -> Path:
        """Get resolved output directory path."""
        return Path(self.output_directory).resolve()
    
    def get_contracts_path(self) -> Path:
        """Get resolved contracts directory path."""
        return Path(self.contracts_directory).resolve()
    
    def get_shared_library_path(self) -> Path:
        """Get resolved shared library path."""
        return Path(self.shared_library_path).resolve()
    
    def get_dead_letter_path(self) -> Path:
        """Get resolved dead letter directory path."""
        return Path(self.dead_letter_directory).resolve()
    
    def get_watched_paths(self) -> List[Path]:
        """Get resolved watched directory paths."""
        return [Path(d).resolve() for d in self.watched_directories]
    
    def get_routing_config(self) -> Dict[str, Any]:
        """Get routing configuration."""
        return {
            "enabled": self.routing_enabled,
            "rules": self.default_routing_rules,
            "service_endpoints": self.service_endpoints,
            "timeout_seconds": self.service_timeout_seconds
        }
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation configuration."""
        return {
            "validate_all": self.validate_all_files,
            "checksum_validation": self.checksum_validation_enabled,
            "sequence_validation": self.sequence_validation_enabled,
            "schema_validation": self.schema_validation_enabled
        }
    
    def get_file_watching_config(self) -> Dict[str, Any]:
        """Get file watching configuration."""
        return {
            "enabled": self.file_watching_enabled,
            "directories": self.watched_directories,
            "recursive": self.watch_recursive,
            "patterns": self.watch_file_patterns,
            "processing_delay": self.file_processing_delay_seconds
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get file processing configuration."""
        return {
            "max_file_size_mb": self.max_file_size_mb,
            "ignore_temp_files": self.ignore_temp_files,
            "processing_delay": self.file_processing_delay_seconds,
            "concurrent_limit": self.concurrent_processing_limit,
            "batch_enabled": self.batch_processing_enabled,
            "batch_size": self.batch_size
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
        
        # Check dead letter directory
        dead_letter_path = self.get_dead_letter_path()
        if not dead_letter_path.exists():
            try:
                dead_letter_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create dead letter directory {dead_letter_path}: {e}")
        
        # Check watched directories
        for i, watch_dir in enumerate(self.watched_directories):
            watch_path = Path(watch_dir)
            if not watch_path.exists():
                # Only warn for watched directories, don't create them
                errors.append(f"Watched directory {watch_path} does not exist")
        
        # Check contracts directory
        contracts_path = self.get_contracts_path()
        if not contracts_path.exists():
            errors.append(f"Contracts directory does not exist: {contracts_path}")
        
        # Check shared library path
        shared_path = self.get_shared_library_path()
        if not shared_path.exists():
            errors.append(f"Shared library path does not exist: {shared_path}")
        
        return errors
