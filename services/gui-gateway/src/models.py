"""
Data models for GUI Gateway API responses
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from enum import Enum


class ServiceStatus(str, Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceHealth(BaseModel):
    """Individual service health information."""
    name: str
    status: ServiceStatus
    url: str
    response_time_ms: Optional[float]
    last_check: datetime
    error_message: Optional[str] = None


class SystemMetrics(BaseModel):
    """System-wide performance metrics."""
    total_services: int
    healthy_services: int
    cpu_usage_percent: Optional[float]
    memory_usage_percent: Optional[float]
    active_connections: int
    messages_per_second: float
    uptime_seconds: int


class SystemStatus(BaseModel):
    """Overall system status."""
    overall_status: str
    services: Dict[str, Dict[str, Any]]
    metrics: SystemMetrics
    timestamp: datetime


class PositionSummary(BaseModel):
    """Current trading position summary."""
    symbol: str
    side: str  # LONG/SHORT
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    duration_minutes: int
    stop_loss: Optional[float]
    take_profit: Optional[float]
    reentry_key: Optional[str]


class SignalFeed(BaseModel):
    """Live trading signal information."""
    id: str
    timestamp: datetime
    symbol: str
    side: str
    confidence: float
    explanation: Optional[str]
    source_indicators: List[str]
    expiry: Optional[datetime]
    status: str  # ACTIVE, EXPIRED, USED


class OrderHistory(BaseModel):
    """Order execution history."""
    order_id: str
    signal_id: str
    timestamp: datetime
    symbol: str
    side: str
    quantity: float
    entry_price: Optional[float]
    exit_price: Optional[float]
    status: str
    pnl: Optional[float]
    duration_minutes: Optional[int]
    commission: Optional[float]


class CalendarEvent(BaseModel):
    """Economic calendar event."""
    id: str
    timestamp: datetime
    currency: str
    title: str
    impact: str
    actual: Optional[str]
    forecast: Optional[str]
    previous: Optional[str]


class TradingStatistics(BaseModel):
    """Trading performance statistics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_percent: float
    total_pnl: float
    average_win: float
    average_loss: float
    profit_factor: float
    max_drawdown_percent: float
    sharpe_ratio: Optional[float]


class MarketData(BaseModel):
    """Current market data snapshot."""
    symbol: str
    bid: float
    ask: float
    spread_pips: float
    volume: Optional[int]
    last_update: datetime


class TradingDashboard(BaseModel):
    """Comprehensive trading dashboard data."""
    system_status: SystemStatus
    active_positions: List[PositionSummary]
    recent_signals: List[SignalFeed]
    market_data: List[MarketData]
    statistics: TradingStatistics
    upcoming_events: List[CalendarEvent]
    timestamp: datetime


class EmergencyControl(BaseModel):
    """Emergency trading control action."""
    action: str  # PAUSE, RESUME, STOP_ALL, CLOSE_ALL
    reason: str
    timestamp: datetime
    user: str


class PerformanceMetrics(BaseModel):
    """System performance metrics over time."""
    period: str
    metrics: Dict[str, List[Dict[str, Any]]]  # time series data
    aggregated: Dict[str, float]  # summary statistics