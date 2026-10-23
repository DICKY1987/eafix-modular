# doc_id: DOC-SERVICE-0208
"""
Signal Generator Configuration
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SIGNAL_GENERATOR_",
        env_file=".env",
    )

    service_port: int = Field(8092, description="Service HTTP port")
    log_level: str = Field("INFO", description="Logging level")

    # Redis
    redis_url: str = Field("redis://localhost:6379", description="Redis connection URL")

    # Subscriptions
    calendar_signals_topic: str = Field("eafix.calendar.signals", description="Topic for calendar signals")
    indicators_topic: str = Field("eafix.indicators.computed", description="Topic for computed indicators")

    # Publishing
    signals_output_topic: str = Field("eafix.signals.generated", description="Topic to publish signals")

    # Processing
    feature_frame_ttl_seconds: int = Field(300, description="TTL for cached feature frames")
    min_confidence_threshold: float = Field(0.6, ge=0.0, le=1.0, description="Minimum confidence to emit signal")
    suppression_window_seconds: int = Field(300, description="Duplicate suppression window (5 min)")

    # Risk-off
    risk_off_topic: str = Field("eafix.system.risk_off", description="Topic for system risk-off events")
