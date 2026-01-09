# DOC_ID: DOC-SERVICE-0066
"""
Configuration for GUI Gateway Service
"""

from typing import Dict, Any


class Settings:
    """GUI Gateway configuration settings."""
    
    # Service configuration
    service_name: str = "gui-gateway"
    log_level: str = "INFO"
    debug: bool = False
    
    # Service URLs for aggregation
    data_ingestor_url: str = "http://localhost:8081"
    indicator_engine_url: str = "http://localhost:8082" 
    signal_generator_url: str = "http://localhost:8083"
    risk_manager_url: str = "http://localhost:8084"
    execution_engine_url: str = "http://localhost:8085"
    calendar_ingestor_url: str = "http://localhost:8086"
    reentry_matrix_url: str = "http://localhost:8087"
    reporter_url: str = "http://localhost:8088"
    
    # Message bus
    redis_url: str = "redis://localhost:6379"
    
    # Database (if needed for caching)
    database_url: str = "postgresql://localhost:5432/eafix"
    
    # Health check settings
    health_check_timeout: int = 5
    health_check_interval: int = 30
    
    # Data aggregation settings
    dashboard_refresh_interval: int = 5  # seconds
    max_signals_cache: int = 1000
    max_orders_cache: int = 5000
    
    # CORS settings
    cors_origins: list = ["http://localhost:3000", "http://localhost:8080"]
    
    def __init__(self):
        """Initialize settings with defaults."""
        pass