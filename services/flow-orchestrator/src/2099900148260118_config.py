# doc_id: DOC-SERVICE-0217
"""
Flow Orchestrator Configuration
Closes GAP-38, GAP-39, GAP-40, GAP-44, GAP-45.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FLOW_ORCHESTRATOR_",
        env_file=".env",
    )

    service_port: int = Field(8094, description="Service HTTP port")
    log_level: str = Field("INFO", description="Logging level")
    redis_url: str = Field("redis://localhost:6379", description="Redis connection URL")

    # Subscriptions
    reentry_decisions_topic: str = Field("eafix.reentry.decisions", description="ReentryDecision events")
    risk_off_topic: str = Field("eafix.system.risk_off", description="System risk-off events")

    # Chain depth limits
    max_chain_depth: int = Field(3, ge=1, description="Maximum reentry chain depth (generations)")

    # Velocity limiting (GAP-39)
    velocity_limit_per_symbol_per_hour: int = Field(5, ge=1,
        description="Max reentry dispatches per symbol per hour")

    # Loop idempotency (GAP-40)
    loop_idempotency_ttl_seconds: int = Field(300, ge=10,
        description="TTL for loop idempotency keys (prevents duplicate dispatch)")

    # Bootstrap health gate (GAP-44, GAP-45)
    startup_health_check_enabled: bool = Field(True, description="Gate on dependency health at startup")
    startup_health_timeout_seconds: int = Field(30, description="Per-dependency health check timeout")
    dependency_services: list = Field(
        default=["calendar-ingestor:8081", "reentry-engine:8089", "reentry-matrix-svc:8087"],
        description="Services to await on startup"
    )
