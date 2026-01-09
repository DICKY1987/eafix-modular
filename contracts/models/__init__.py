# DOC_ID: DOC-CONTRACT-0007
"""
Pydantic models for contract validation.

This module provides runtime validation models for all CSV and JSON schemas
used throughout the trading system. These models ensure data integrity and
type safety across service boundaries.
"""

from .csv_models import (
    ActiveCalendarSignal,
    ReentryDecision, 
    TradeResult,
    HealthMetric,
)

from .json_models import (
    IndicatorRecord,
    OrderIn,
    OrderOut,
    HybridId,
)

from .event_models import (
    PriceTick,
    IndicatorVector,
    Signal,
    OrderIntent,
    ExecutionReport,
    CalendarEvent,
    ReentryDecision as EventReentryDecision,
    TradingSide,
    OrderSide,
    ExecutionStatus,
    CalendarImpact,
)

__all__ = [
    # CSV Models
    "ActiveCalendarSignal",
    "ReentryDecision",
    "TradeResult", 
    "HealthMetric",
    # JSON Models
    "IndicatorRecord",
    "OrderIn",
    "OrderOut",
    "HybridId",
    # Event Models
    "PriceTick",
    "IndicatorVector",
    "Signal",
    "OrderIntent",
    "ExecutionReport",
    "CalendarEvent",
    "EventReentryDecision",
    "TradingSide",
    "OrderSide", 
    "ExecutionStatus",
    "CalendarImpact",
]