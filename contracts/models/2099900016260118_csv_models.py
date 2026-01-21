# doc_id: DOC-MODEL-0004
# DOC_ID: DOC-CONTRACT-0004
"""
Pydantic models for CSV data structures.

These models validate CSV row data and ensure atomic write policy compliance.
All models include required metadata columns (file_seq, checksum_sha256).
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator
import hashlib


class BaseCSVModel(BaseModel):
    """Base model for all CSV data with required metadata columns."""
    
    file_seq: int = Field(..., ge=1, description="Monotonic sequence number")
    checksum_sha256: str = Field(..., min_length=64, max_length=64, description="SHA-256 checksum")
    timestamp: datetime = Field(..., description="Record timestamp in UTC")
    
    @validator('checksum_sha256')
    def validate_checksum_format(cls, v):
        """Validate checksum is valid hex string."""
        if not all(c in '0123456789abcdef' for c in v.lower()):
            raise ValueError('Checksum must be valid hexadecimal string')
        return v.lower()
    
    def compute_checksum(self) -> str:
        """Compute SHA-256 checksum for this record (excluding checksum field)."""
        # Get all field values except checksum
        data = self.dict(exclude={'checksum_sha256'})
        
        # Create ordered string representation
        ordered_values = []
        for key in sorted(data.keys()):
            value = data[key]
            if isinstance(value, datetime):
                value = value.isoformat()
            ordered_values.append(str(value))
        
        # Compute hash
        row_string = '|'.join(ordered_values)
        return hashlib.sha256(row_string.encode('utf-8')).hexdigest()
    
    def verify_checksum(self) -> bool:
        """Verify the stored checksum matches computed checksum."""
        return self.checksum_sha256 == self.compute_checksum()


class ActiveCalendarSignal(BaseCSVModel):
    """Active calendar signal generated from economic events."""
    
    calendar_id: str = Field(..., description="Calendar identifier (CAL8 or CAL5)")
    symbol: str = Field(..., min_length=6, max_length=8, description="Currency pair")
    impact_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(..., description="Event impact level")
    proximity_state: Literal["IMMEDIATE", "NEAR", "FAR"] = Field(..., description="Distance to event")
    anticipation_event: bool = Field(..., description="Whether this is an anticipation signal")
    direction_bias: Literal["BULLISH", "BEARISH", "NEUTRAL"] = Field(..., description="Expected direction")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Signal confidence (0.0-1.0)")
    
    @validator('calendar_id')
    def validate_calendar_id(cls, v):
        """Validate calendar ID format."""
        if v.startswith('CAL8_') and len(v) >= 8:
            return v
        elif v.startswith('CAL5_') and len(v) >= 8:
            return v
        elif v == 'NONE':
            return v
        else:
            raise ValueError('calendar_id must be CAL8_*, CAL5_*, or NONE')
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate currency pair format."""
        if len(v) not in [6, 7, 8] or not v.isalpha() or not v.isupper():
            raise ValueError('symbol must be uppercase currency pair (e.g., EURUSD, GBPJPY)')
        return v


class ReentryDecision(BaseCSVModel):
    """Trading re-entry decision from the re-entry engine."""
    
    trade_id: str = Field(..., description="Original trade identifier")
    hybrid_id: str = Field(..., description="Hybrid reentry identifier")
    symbol: str = Field(..., min_length=6, max_length=8, description="Currency pair")
    outcome_class: Literal["WIN", "LOSS", "BREAKEVEN"] = Field(..., description="Trade outcome")
    duration_class: Literal["FLASH", "QUICK", "LONG", "EXTENDED"] = Field(..., description="Duration class")
    reentry_action: Literal["R1", "R2", "HOLD", "NO_REENTRY"] = Field(..., description="Recommended action")
    parameter_set_id: str = Field(..., description="Applied parameter set identifier")
    resolved_tier: Literal["EXACT", "TIER1", "TIER2", "TIER3", "GLOBAL"] = Field(..., description="Fallback tier")
    chain_position: Literal["O", "R1", "R2"] = Field(..., description="Position in O→R1→R2 chain")
    lot_size: float = Field(..., gt=0, description="Recommended lot size")
    stop_loss: float = Field(..., gt=0, description="Stop loss in pips")
    take_profit: float = Field(..., gt=0, description="Take profit in pips")
    
    @validator('hybrid_id')
    def validate_hybrid_id(cls, v):
        """Validate hybrid ID format."""
        parts = v.split('_')
        if len(parts) < 5:
            raise ValueError('hybrid_id must have at least 5 components')
        
        # Basic format validation - detailed validation in shared.reentry module
        outcome, duration, proximity, calendar, direction = parts[:5]
        
        valid_outcomes = ['W2', 'W1', 'BE', 'L1', 'L2']
        valid_durations = ['FLASH', 'QUICK', 'LONG', 'EXTENDED']
        valid_proximities = ['PRE_1H', 'AT_EVENT', 'POST_30M']
        valid_directions = ['LONG', 'SHORT', 'ANY']
        
        if outcome not in valid_outcomes:
            raise ValueError(f'Invalid outcome in hybrid_id: {outcome}')
        if duration not in valid_durations:
            raise ValueError(f'Invalid duration in hybrid_id: {duration}')
        if proximity not in valid_proximities:
            raise ValueError(f'Invalid proximity in hybrid_id: {proximity}')
        if direction not in valid_directions:
            raise ValueError(f'Invalid direction in hybrid_id: {direction}')
            
        return v


class TradeResult(BaseCSVModel):
    """Completed trade result from EA bridge."""
    
    trade_id: str = Field(..., description="Unique trade identifier")
    symbol: str = Field(..., min_length=6, max_length=8, description="Currency pair")
    direction: Literal["BUY", "SELL"] = Field(..., description="Trade direction")
    lot_size: float = Field(..., gt=0, description="Position size in lots")
    open_price: float = Field(..., gt=0, description="Trade opening price")
    close_price: float = Field(..., gt=0, description="Trade closing price")
    open_time: datetime = Field(..., description="Trade opening timestamp")
    close_time: datetime = Field(..., description="Trade closing timestamp")
    duration_minutes: int = Field(..., ge=0, description="Trade duration in minutes")
    profit_loss: float = Field(..., description="P&L in account currency")
    profit_loss_pips: float = Field(..., description="P&L in pips")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss level")
    take_profit: Optional[float] = Field(None, gt=0, description="Take profit level")
    close_reason: Literal["TP", "SL", "MANUAL", "TIMEOUT"] = Field(..., description="Closure reason")
    commission: float = Field(..., description="Commission paid")
    swap: float = Field(..., description="Overnight swap")
    magic_number: int = Field(..., description="EA magic number")
    comment: str = Field(..., description="Trade comment with hybrid ID")
    
    @validator('close_time')
    def validate_close_after_open(cls, v, values):
        """Ensure close_time is after open_time."""
        if 'open_time' in values and v <= values['open_time']:
            raise ValueError('close_time must be after open_time')
        return v
    
    @validator('duration_minutes')
    def validate_duration_consistency(cls, v, values):
        """Ensure duration matches time difference."""
        if 'open_time' in values and 'close_time' in values:
            expected_duration = int((values['close_time'] - values['open_time']).total_seconds() / 60)
            if abs(v - expected_duration) > 1:  # Allow 1 minute tolerance
                raise ValueError(f'duration_minutes ({v}) does not match calculated duration ({expected_duration})')
        return v


class HealthMetric(BaseCSVModel):
    """System health and performance metrics."""
    
    service_name: str = Field(..., description="Name of the service")
    metric_name: str = Field(..., description="Name of the metric")
    metric_value: float = Field(..., description="Metric value")
    metric_unit: str = Field(..., description="Unit of measurement")
    health_status: Literal["HEALTHY", "DEGRADED", "UNHEALTHY"] = Field(..., description="Health status")
    cpu_usage_percent: float = Field(..., ge=0.0, le=100.0, description="CPU usage percentage")
    memory_usage_percent: float = Field(..., ge=0.0, le=100.0, description="Memory usage percentage")
    disk_usage_percent: float = Field(..., ge=0.0, le=100.0, description="Disk usage percentage")
    active_connections: int = Field(..., ge=0, description="Active connections")
    messages_processed: int = Field(..., ge=0, description="Messages processed")
    error_count: int = Field(..., ge=0, description="Error count")
    uptime_seconds: int = Field(..., ge=0, description="Service uptime")
    
    @validator('service_name')
    def validate_service_name(cls, v):
        """Validate service name format."""
        valid_services = [
            'data-ingestor', 'indicator-engine', 'signal-generator',
            'risk-manager', 'execution-engine', 'calendar-ingestor', 
            'reentry-matrix-svc', 'reporter', 'gui-gateway'
        ]
        if v not in valid_services:
            raise ValueError(f'service_name must be one of: {valid_services}')
        return v