"""
Pydantic models for event schemas.

These models correspond to the event schemas in contracts/events/ and are used
for message validation in the event-driven microservices architecture.

Generated from JSON schemas - DO NOT EDIT MANUALLY.
Use the codegen tooling to regenerate when schemas change.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


class TradingSide(str, Enum):
    """Trading side enumeration for signals and orders."""
    BUY = "BUY"
    SELL = "SELL"


class PriceTick(BaseModel):
    """Market price tick data from broker feeds - Version 1.0"""
    
    timestamp: datetime = Field(..., description="UTC timestamp of the tick")
    symbol: str = Field(..., pattern=r"^[A-Z]{6}$", description="Currency pair symbol (e.g., EURUSD)")
    bid: float = Field(..., ge=0, description="Bid price")
    ask: float = Field(..., ge=0, description="Ask price")
    volume: Optional[int] = Field(None, ge=0, description="Optional tick volume")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class IndicatorVector(BaseModel):
    """Technical indicator computation results - Version 1.1"""
    
    timestamp: datetime = Field(..., description="UTC timestamp of computation")
    symbol: str = Field(..., pattern=r"^[A-Z]{6}$", description="Currency pair symbol")
    indicator_id: str = Field(..., description="Unique indicator identifier")
    values: Dict[str, Any] = Field(..., description="Indicator output values")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Signal(BaseModel):
    """Trading signal generated from indicators and rules - Version 1.0"""
    
    id: UUID = Field(..., description="Unique signal identifier")
    timestamp: datetime = Field(..., description="UTC timestamp of signal generation")
    symbol: str = Field(..., pattern=r"^[A-Z]{6}$", description="Currency pair symbol")
    side: TradingSide = Field(..., description="Trading direction")
    confidence: float = Field(..., ge=0, le=1, description="Signal confidence score (0-1)")
    explanation: Optional[str] = Field(None, description="Optional explanation of signal logic")
    source_indicators: Optional[List[str]] = Field(None, description="List of indicators used for this signal")
    expiry: Optional[datetime] = Field(None, description="Signal expiry timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class OrderSide(str, Enum):
    """Order side enumeration."""
    LONG = "LONG"
    SHORT = "SHORT"


class OrderIntent(BaseModel):
    """Risk-approved order ready for execution - Version 1.2"""
    
    id: UUID = Field(..., description="Unique order intent identifier")
    signal_id: UUID = Field(..., description="Source signal identifier")
    timestamp: datetime = Field(..., description="UTC timestamp of order intent")
    symbol: str = Field(..., pattern=r"^[A-Z]{6}$", description="Currency pair symbol")
    side: OrderSide = Field(..., description="Order side")
    quantity: float = Field(..., gt=0, description="Order quantity/lot size")
    price: Optional[float] = Field(None, gt=0, description="Optional limit price")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    take_profit: Optional[float] = Field(None, gt=0, description="Take profit price")
    expiry: Optional[datetime] = Field(None, description="Order expiry time")
    reentry_key: Optional[str] = Field(None, description="Re-entry tracking key")
    risk_metadata: Optional[Dict[str, Any]] = Field(None, description="Risk management metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class ExecutionStatus(str, Enum):
    """Execution status enumeration."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIAL_FILL = "PARTIAL_FILL"
    REJECTED = "REJECTED"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"


class ExecutionReport(BaseModel):
    """Broker execution results and status updates - Version 1.0"""
    
    order_intent_id: UUID = Field(..., description="Source order intent identifier")
    broker_order_id: Optional[str] = Field(None, description="Broker's order identifier")
    timestamp: datetime = Field(..., description="UTC timestamp of execution report")
    status: ExecutionStatus = Field(..., description="Execution status")
    filled_quantity: Optional[float] = Field(None, ge=0, description="Filled quantity")
    filled_price: Optional[float] = Field(None, gt=0, description="Average fill price")
    commission: Optional[float] = Field(None, ge=0, description="Commission charged")
    error_message: Optional[str] = Field(None, description="Error message if rejected")
    execution_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional execution details")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class CalendarImpact(str, Enum):
    """Economic event impact levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CalendarEvent(BaseModel):
    """Economic calendar event data - Version 1.0"""
    
    id: str = Field(..., description="Unique calendar event identifier")
    timestamp: datetime = Field(..., description="Event timestamp in UTC")
    currency: str = Field(..., pattern=r"^[A-Z]{3}$", description="Currency code (e.g., USD)")
    title: str = Field(..., description="Event title/description")
    impact: CalendarImpact = Field(..., description="Expected market impact")
    actual: Optional[str] = Field(None, description="Actual value/result")
    forecast: Optional[str] = Field(None, description="Forecasted value")
    previous: Optional[str] = Field(None, description="Previous value")
    source: Optional[str] = Field(None, description="Data source")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ReentryDecision(BaseModel):
    """Matrix-based re-entry decision logic results - Version 1.0"""
    
    reentry_key: str = Field(..., description="Hybrid ID re-entry key")
    timestamp: datetime = Field(..., description="UTC timestamp of decision")
    symbol: str = Field(..., pattern=r"^[A-Z]{6}$", description="Currency pair symbol")
    generation: int = Field(..., ge=1, le=3, description="Re-entry generation (1-3)")
    should_reenter: bool = Field(..., description="Whether re-entry should occur")
    matrix_outcome: str = Field(..., description="Matrix decision outcome")
    confidence_score: float = Field(..., ge=0, le=1, description="Decision confidence")
    wait_time_minutes: Optional[int] = Field(None, ge=0, description="Suggested wait time")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional decision context")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Export all event models for easy imports
__all__ = [
    "PriceTick",
    "IndicatorVector", 
    "Signal",
    "OrderIntent",
    "ExecutionReport",
    "CalendarEvent",
    "ReentryDecision",
    "TradingSide",
    "OrderSide",
    "ExecutionStatus",
    "CalendarImpact"
]