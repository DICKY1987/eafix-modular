"""
Re-entry Engine Configuration

Central configuration for the re-entry engine service including
trade result processing, matrix client integration, and CSV output.
"""

from pathlib import Path
from pydantic import BaseSettings, Field
from typing import List, Dict, Any


class Settings(BaseSettings):
    """Re-entry Engine service settings."""
    
    # Basic service configuration
    service_port: int = Field(8089, description="Service HTTP port")
    log_level: str = Field("INFO", description="Logging level")
    debug_mode: bool = Field(False, description="Enable debug mode")
    
    # Redis configuration
    redis_url: str = Field(
        "redis://localhost:6379", 
        description="Redis connection URL"
    )
    
    # Event subscription
    subscribe_to_trade_results: bool = Field(
        True,
        description="Subscribe to trade result events from Redis"
    )
    
    trade_results_topic: str = Field(
        "eafix.trades.results",
        description="Redis topic for trade results"
    )
    
    # Event publishing
    publish_reentry_events: bool = Field(
        True,
        description="Publish re-entry decision events to Redis"
    )
    
    reentry_decisions_topic: str = Field(
        "eafix.reentry.decisions",
        description="Redis topic for re-entry decisions"
    )
    
    # Re-entry Matrix Service integration
    reentry_matrix_service_url: str = Field(
        "http://localhost:8087",
        description="URL of the re-entry matrix service"
    )
    
    reentry_matrix_timeout_seconds: float = Field(
        10.0,
        gt=0.0,
        description="Timeout for re-entry matrix service calls"
    )
    
    # Data storage
    output_directory: str = Field(
        "./data/reentry-engine",
        description="Directory for CSV output files"
    )
    
    # Trade result processing
    process_completed_trades_only: bool = Field(
        True,
        description="Only process trades with close_time set"
    )
    
    min_trade_duration_minutes: int = Field(
        1,
        ge=0,
        description="Minimum trade duration to consider for re-entry"
    )
    
    exclude_manual_closes: bool = Field(
        False,
        description="Exclude manually closed trades from re-entry analysis"
    )
    
    # Re-entry eligibility criteria
    reentry_cooldown_minutes: int = Field(
        15,
        ge=0,
        description="Cooldown period between re-entries for same symbol"
    )
    
    max_reentry_attempts_per_day: int = Field(
        5,
        ge=1,
        description="Maximum re-entry attempts per symbol per day"
    )
    
    min_confidence_threshold: float = Field(
        0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to execute re-entry"
    )
    
    # Outcome classification
    profit_threshold_pips: float = Field(
        5.0,
        ge=0.0,
        description="Minimum pips profit to classify as WIN"
    )
    
    loss_threshold_pips: float = Field(
        -5.0,
        le=0.0,
        description="Maximum pips loss to classify as LOSS (negative value)"
    )
    
    # Duration classification thresholds (in minutes)
    flash_duration_max_minutes: int = Field(5, description="FLASH duration threshold")
    quick_duration_max_minutes: int = Field(30, description="QUICK duration threshold")
    long_duration_max_minutes: int = Field(240, description="LONG duration threshold")
    # EXTENDED is anything above long_duration_max_minutes
    
    # Calendar proximity detection
    calendar_proximity_window_minutes: int = Field(
        60,
        ge=5,
        description="Window in minutes to detect proximity to calendar events"
    )
    
    # CSV output settings
    csv_atomic_writes: bool = Field(
        True,
        description="Use atomic writes for CSV files"
    )
    
    csv_backup_enabled: bool = Field(
        True,
        description="Create backup copies of CSV files"
    )
    
    csv_file_rotation_hours: int = Field(
        24,
        gt=0,
        description="Hours between CSV file rotation"
    )
    
    # Performance settings
    batch_processing_enabled: bool = Field(
        False,
        description="Enable batch processing of trade results"
    )
    
    batch_size: int = Field(
        10,
        gt=0,
        description="Number of trade results to process in a batch"
    )
    
    processing_timeout_seconds: float = Field(
        30.0,
        gt=0.0,
        description="Maximum time to process a single trade result"
    )
    
    concurrent_processing_limit: int = Field(
        5,
        gt=0,
        description="Maximum concurrent trade result processing"
    )
    
    # Health check settings
    health_check_interval_seconds: int = Field(
        30,
        gt=0,
        description="Health check interval in seconds"
    )
    
    redis_connection_timeout_seconds: int = Field(
        5,
        gt=0,
        description="Redis connection timeout"
    )
    
    # Metrics and monitoring
    metrics_enabled: bool = Field(True, description="Enable metrics collection")
    metrics_retention_hours: int = Field(24, gt=0, description="Metrics retention period")
    
    # Shared library configuration
    shared_library_path: str = Field(
        "../../../shared/reentry",
        description="Path to shared re-entry library"
    )
    
    vocabulary_file: str = Field(
        "../../../shared/reentry/reentry_vocab.json",
        description="Path to re-entry vocabulary JSON file"
    )
    
    # Hybrid ID validation
    enable_hybrid_id_validation: bool = Field(
        True,
        description="Enable strict hybrid ID validation"
    )
    
    class Config:
        env_prefix = "REENTRY_ENGINE_"
        env_file = ".env"
    
    def get_output_path(self) -> Path:
        """Get resolved output directory path."""
        return Path(self.output_directory).resolve()
    
    def get_shared_library_path(self) -> Path:
        """Get resolved shared library path."""
        return Path(self.shared_library_path).resolve()
    
    def get_vocabulary_file_path(self) -> Path:
        """Get resolved vocabulary file path."""
        return Path(self.vocabulary_file).resolve()
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get trade result processing configuration."""
        return {
            "process_completed_only": self.process_completed_trades_only,
            "min_duration_minutes": self.min_trade_duration_minutes,
            "exclude_manual_closes": self.exclude_manual_closes,
            "cooldown_minutes": self.reentry_cooldown_minutes,
            "max_attempts_per_day": self.max_reentry_attempts_per_day,
            "min_confidence": self.min_confidence_threshold
        }
    
    def get_outcome_classification_config(self) -> Dict[str, Any]:
        """Get outcome classification configuration."""
        return {
            "profit_threshold_pips": self.profit_threshold_pips,
            "loss_threshold_pips": self.loss_threshold_pips,
            "breakeven_tolerance_pips": 1.0  # Within 1 pip is considered breakeven
        }
    
    def get_duration_classification_config(self) -> Dict[str, Any]:
        """Get duration classification configuration."""
        return {
            "flash_max_minutes": self.flash_duration_max_minutes,
            "quick_max_minutes": self.quick_duration_max_minutes,
            "long_max_minutes": self.long_duration_max_minutes
        }
    
    def get_csv_config(self) -> Dict[str, Any]:
        """Get CSV output configuration."""
        return {
            "atomic_writes": self.csv_atomic_writes,
            "backup_enabled": self.csv_backup_enabled,
            "rotation_hours": self.csv_file_rotation_hours,
            "output_directory": str(self.get_output_path())
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
        
        # Check shared library path
        shared_path = self.get_shared_library_path()
        if not shared_path.exists():
            errors.append(f"Shared library path does not exist: {shared_path}")
        
        # Check vocabulary file
        vocab_path = self.get_vocabulary_file_path()
        if not vocab_path.exists():
            errors.append(f"Vocabulary file does not exist: {vocab_path}")
        
        return errors