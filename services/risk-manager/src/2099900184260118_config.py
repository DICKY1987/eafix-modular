# doc_id: DOC-SERVICE-0210
"""
Risk Manager Configuration
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RISK_MANAGER_",
        env_file=".env",
    )

    service_port: int = Field(8093, description="Service HTTP port")
    log_level: str = Field("INFO", description="Logging level")
    redis_url: str = Field("redis://localhost:6379", description="Redis connection URL")

    # Subscriptions / Publishing
    signals_input_topic: str = Field("eafix.signals.generated", description="Input signals topic")
    orders_output_topic: str = Field("eafix.orders.validated", description="Approved order intents topic")

    # Risk parameters (from tactical spec + FR-P2)
    max_risk_percent_per_trade: float = Field(2.0, gt=0.0, description="Max % account at risk per trade")
    max_reentry_risk_cap_percent: float = Field(3.5, gt=0.0, description="Max total chain exposure %")
    daily_drawdown_limit_percent: float = Field(5.0, gt=0.0, description="Daily drawdown halt threshold %")

    # Account balance
    account_balance_source: str = Field("config", description="Source: config or redis")
    account_balance: float = Field(10000.0, gt=0.0, description="Account balance (if source=config)")

    # Sizing defaults
    default_sl_pips: float = Field(20.0, gt=0.0, description="Default SL pips for sizing")
    pip_value_per_lot: float = Field(10.0, gt=0.0, description="Pip value per standard lot (USD)")
