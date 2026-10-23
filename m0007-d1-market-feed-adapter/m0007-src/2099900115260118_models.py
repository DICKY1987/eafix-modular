# doc_id: DOC-MODEL-0001
# DOC_ID: DOC-SERVICE-0046
"""
Pydantic models for the Data Ingestor service
"""

from datetime import datetime
from typing import Optional
import re

from pydantic import BaseModel, validator, Field


class PriceTick(BaseModel):
    """Price tick data model matching PriceTick@1.0 schema"""
    
    timestamp: str = Field(..., description="UTC timestamp of the tick")
    symbol: str = Field(..., description="Currency pair symbol (e.g., EURUSD)")
    bid: float = Field(..., gt=0, description="Bid price")
    ask: float = Field(..., gt=0, description="Ask price") 
    volume: Optional[int] = Field(None, ge=0, description="Optional tick volume")
    
    @validator("timestamp")
    def validate_timestamp(cls, v):
        """Validate timestamp format"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("Invalid timestamp format, must be ISO format")
    
    @validator("symbol")
    def validate_symbol(cls, v):
        """Validate currency pair symbol"""
        if not re.match(r'^[A-Z]{6}$', v):
            raise ValueError("Symbol must be 6 uppercase letters (e.g., EURUSD)")
        return v
    
    @validator("ask")
    def validate_ask_greater_than_bid(cls, v, values):
        """Ensure ask price is greater than bid price"""
        if "bid" in values and v <= values["bid"]:
            raise ValueError("Ask price must be greater than bid price")
        return v
    
    class Config:
        # Example data for documentation
        schema_extra = {
            "example": {
                "timestamp": "2025-01-15T10:30:45.123456Z",
                "symbol": "EURUSD",
                "bid": 1.08450,
                "ask": 1.08452,
                "volume": 100
            }
        }


class HealthStatus(BaseModel):
    """Health check response model"""
    
    status: str = Field(..., description="Service health status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    adapters_status: dict = Field(..., description="Status of data adapters")
    redis_connected: bool = Field(..., description="Redis connection status")
    last_tick_timestamp: Optional[str] = Field(None, description="Last processed tick timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-01-15T10:30:45Z",
                "version": "1.0.0",
                "uptime_seconds": 3661.5,
                "adapters_status": {
                    "mt4": "connected",
                    "csv": "monitoring",
                    "socket": "disabled"
                },
                "redis_connected": True,
                "last_tick_timestamp": "2025-01-15T10:30:44Z"
            }
        }


class ServiceMetrics(BaseModel):
    """Service metrics model"""
    
    ticks_processed: int = Field(..., description="Total ticks processed")
    ticks_per_second: float = Field(..., description="Current ticks per second rate")
    errors_total: int = Field(..., description="Total errors encountered")
    error_rate: float = Field(..., description="Current error rate")
    uptime_seconds: float = Field(..., description="Service uptime")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    
    class Config:
        schema_extra = {
            "example": {
                "ticks_processed": 15420,
                "ticks_per_second": 12.5,
                "errors_total": 3,
                "error_rate": 0.0002,
                "uptime_seconds": 3661.5,
                "memory_usage_mb": 45.2
            }
        }