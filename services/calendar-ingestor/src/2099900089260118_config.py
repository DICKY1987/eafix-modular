# doc_id: DOC-SERVICE-0134
# DOC_ID: DOC-SERVICE-0030
"""
Calendar Ingestor Service Configuration
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """Calendar Ingestor service settings"""

    model_config = SettingsConfigDict(
        env_prefix="CALENDAR_",
        env_file=".env",
    )
    
    # Redis configuration
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL for event publishing"
    )
    
    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # Service configuration
    service_name: str = Field(
        default="calendar-ingestor",
        description="Service name for logging and metrics"
    )
    
    # Calendar processing configuration
    output_directory: str = Field(
        default="./data/calendar",
        description="Directory to write active calendar signals CSV files"
    )

    calendar_source_path: Optional[str] = Field(
        default=None,
        description="Optional CSV file containing raw or normalized economic calendar events",
    )

    source_timezone: str = Field(
        default="America/New_York",
        description="Timezone for raw source date/time fields before UTC normalization",
    )
    
    # Calendar event sources
    calendar_sources: List[str] = Field(
        default=["forexfactory", "investing"],
        description="List of calendar data sources to process"
    )

    update_interval_hours: int = Field(
        default=24,
        description="Hours between calendar refreshes"
    )

    data_source: str = Field(
        default="investing.com",
        description="Primary calendar data source"
    )

    calendar_events_topic: str = Field(
        default="eafix.calendar.events",
        description="Redis topic for normalized CalendarEvent payloads",
    )

    calendar_signals_topic: str = Field(
        default="eafix.calendar.signals",
        description="Redis topic for ActiveCalendarSignal payloads",
    )
    
    # Signal generation parameters
    anticipation_window_minutes: int = Field(
        default=60,
        description="Minutes before event to generate anticipation signals"
    )
    
    event_window_minutes: int = Field(
        default=5,
        description="Minutes after event start for AT_EVENT signals"
    )
    
    stabilization_window_minutes: int = Field(
        default=30,
        description="Minutes after event for POST_30M signals"
    )
    
    # Impact level mapping
    high_impact_events: List[str] = Field(
        default=[
            "Non-Farm Payrolls", "FOMC Meeting", "ECB Meeting", "BOE Meeting",
            "BOJ Meeting", "GDP", "CPI", "NFP"
        ],
        description="Events considered high impact (CAL8)"
    )
    
    medium_impact_events: List[str] = Field(
        default=[
            "PMI", "Retail Sales", "Unemployment Rate", "PPI",
            "Industrial Production", "Consumer Confidence"
        ],
        description="Events considered medium impact (CAL5)"
    )
    
    # Currency pair mapping
    currency_pairs: List[str] = Field(
        default=["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD"],
        description="Currency pairs to generate signals for"
    )
    
    # CSV file settings
    csv_batch_size: int = Field(
        default=100,
        description="Number of signals to batch before writing CSV"
    )
    
    csv_retention_days: int = Field(
        default=7,
        description="Days to retain CSV files before cleanup"
    )
    
