"""
Configuration settings for Data Ingestor service
"""

import os
from typing import Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Service configuration settings"""
    
    # Redis connection
    redis_url: str = "redis://localhost:6379"
    redis_channel: str = "price_ticks"
    
    # Service settings
    log_level: str = "INFO"
    service_name: str = "data-ingestor"
    
    # MT4 DDE settings (Windows only)
    enable_dde: bool = True
    dde_server: str = "MT4"
    dde_topic: str = "QUOTE"
    dde_poll_interval: float = 0.1  # 100ms
    
    # CSV file settings
    enable_csv: bool = True
    csv_watch_dir: str = "./data/prices"
    csv_poll_interval: float = 1.0  # 1 second
    
    # Socket settings
    enable_socket: bool = False
    socket_host: str = "localhost"
    socket_port: int = 5555
    
    # Data validation
    max_price_age_seconds: int = 30
    min_spread_pips: float = 0.1
    max_spread_pips: float = 100.0
    
    # Performance
    batch_size: int = 100
    flush_interval: float = 1.0
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()
    
    @validator("redis_url")
    def validate_redis_url(cls, v):
        if not v.startswith(("redis://", "rediss://")):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        return v
    
    class Config:
        env_prefix = "INGESTOR_"
        env_file = ".env"
        case_sensitive = False