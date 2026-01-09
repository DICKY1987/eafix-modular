# DOC_ID: DOC-SERVICE-0078
"""
Re-entry Matrix Service Configuration

Manages all configuration parameters for the re-entry matrix service including
tiered resolver settings, shared library integration, and CSV output policies.
"""

import os
from pathlib import Path
from pydantic import BaseSettings, Field
from typing import Dict, Any, List


class Settings(BaseSettings):
    """Re-entry Matrix Service settings."""
    
    # Basic service configuration
    service_port: int = Field(8087, description="Service HTTP port")
    log_level: str = Field("INFO", description="Logging level")
    debug_mode: bool = Field(False, description="Enable debug mode")
    
    # Redis configuration
    redis_url: str = Field(
        "redis://localhost:6379", 
        description="Redis connection URL"
    )
    
    # Event publishing
    publish_events: bool = Field(True, description="Whether to publish events to Redis")
    reentry_decisions_topic: str = Field(
        "eafix.reentry.decisions",
        description="Redis topic for re-entry decisions"
    )
    
    # Data storage
    output_directory: str = Field(
        "./data/reentry",
        description="Directory for CSV output files"
    )
    
    # Parameter set configuration
    parameter_sets_file: str = Field(
        "./config/parameter_sets.json",
        description="Path to parameter sets configuration file"
    )
    
    # Tiered resolver settings
    tier_fallback_enabled: bool = Field(
        True,
        description="Enable tier-based parameter fallback"
    )
    
    tier_hierarchy: List[str] = Field(
        default_factory=lambda: ["EXACT", "TIER1", "TIER2", "TIER3", "GLOBAL"],
        description="Tier fallback hierarchy in order"
    )
    
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
    
    enable_cross_language_parity: bool = Field(
        True,
        description="Enable cross-language parity checking"
    )
    
    # Re-entry decision parameters
    default_confidence_threshold: float = Field(
        0.6,
        ge=0.0,
        le=1.0,
        description="Default confidence threshold for re-entry decisions"
    )
    
    max_reentry_generation: int = Field(
        3,
        ge=1,
        le=3,
        description="Maximum re-entry generation (1=O, 2=R1, 3=R2)"
    )
    
    # Risk management settings
    default_stop_loss_pips: float = Field(
        20.0,
        gt=0.0,
        description="Default stop loss in pips"
    )
    
    default_take_profit_pips: float = Field(
        40.0,
        gt=0.0,
        description="Default take profit in pips"
    )
    
    lot_size_multiplier: float = Field(
        1.0,
        gt=0.0,
        description="Lot size multiplier for re-entries"
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
    
    csv_max_file_size_mb: int = Field(
        100,
        gt=0,
        description="Maximum CSV file size in MB before rotation"
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
    
    # Performance settings
    process_timeout_seconds: float = Field(
        10.0,
        gt=0.0,
        description="Maximum time to process a single request"
    )
    
    concurrent_requests_limit: int = Field(
        100,
        gt=0,
        description="Maximum concurrent re-entry requests"
    )
    
    # Metrics collection
    metrics_enabled: bool = Field(True, description="Enable metrics collection")
    metrics_retention_hours: int = Field(24, gt=0, description="Metrics retention period")
    
    class Config:
        env_prefix = "REENTRY_MATRIX_"
        env_file = ".env"
    
    def get_output_path(self) -> Path:
        """Get resolved output directory path."""
        return Path(self.output_directory).resolve()
    
    def get_parameter_sets_path(self) -> Path:
        """Get resolved parameter sets file path."""
        return Path(self.parameter_sets_file).resolve()
    
    def get_shared_library_path(self) -> Path:
        """Get resolved shared library path."""
        return Path(self.shared_library_path).resolve()
    
    def get_vocabulary_file_path(self) -> Path:
        """Get resolved vocabulary file path."""
        return Path(self.vocabulary_file).resolve()
    
    def get_tier_config(self) -> Dict[str, Any]:
        """Get tier configuration for the resolver."""
        return {
            "enabled": self.tier_fallback_enabled,
            "hierarchy": self.tier_hierarchy,
            "confidence_threshold": self.default_confidence_threshold,
            "max_generation": self.max_reentry_generation
        }
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get risk management configuration."""
        return {
            "default_stop_loss_pips": self.default_stop_loss_pips,
            "default_take_profit_pips": self.default_take_profit_pips,
            "lot_size_multiplier": self.lot_size_multiplier
        }
    
    def get_csv_config(self) -> Dict[str, Any]:
        """Get CSV output configuration."""
        return {
            "atomic_writes": self.csv_atomic_writes,
            "backup_enabled": self.csv_backup_enabled,
            "max_file_size_mb": self.csv_max_file_size_mb,
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
        
        # Check parameter sets file directory
        param_path = self.get_parameter_sets_path()
        if not param_path.parent.exists():
            try:
                param_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create parameter sets directory {param_path.parent}: {e}")
        
        # Check shared library path
        shared_path = self.get_shared_library_path()
        if not shared_path.exists():
            errors.append(f"Shared library path does not exist: {shared_path}")
        
        # Check vocabulary file
        vocab_path = self.get_vocabulary_file_path()
        if not vocab_path.exists():
            errors.append(f"Vocabulary file does not exist: {vocab_path}")
        
        return errors