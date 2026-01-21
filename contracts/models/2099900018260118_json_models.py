# doc_id: DOC-MODEL-0006
# DOC_ID: DOC-CONTRACT-0006
"""
Pydantic models for JSON data structures.

These models validate JSON messages and API payloads used throughout the system.
They correspond to JSON schemas in contracts/schemas/json/.
"""

from datetime import datetime
from typing import Optional, Union, List, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


class OutputTypeEnum(str, Enum):
    """Valid indicator output types."""
    Z_SCORE = "z_score"
    PROBABILITY_0_1 = "probability_0_1" 
    STATE_ENUM = "state_enum"
    BOOLEAN = "boolean"
    RAW_VALUE = "raw_value"
    SCALAR_0_100 = "scalar_0_100"
    PIPS = "pips"
    PERCENT = "percent"


class ThresholdDirection(str, Enum):
    """Threshold direction types."""
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    BOTH = "both"
    UP = "up"
    DOWN = "down"


class ZScoreThreshold(BaseModel):
    """Z-score based threshold configuration."""
    kind: Literal["zscore"] = "zscore"
    gte: float = Field(..., description="Greater than or equal threshold")
    lte: Optional[float] = Field(None, description="Less than or equal threshold")
    hysteresis: float = Field(0.0, ge=0.0, description="Hysteresis value")
    persistence_bars: int = Field(0, ge=0, description="Required persistence in bars")
    direction: ThresholdDirection = Field(ThresholdDirection.BOTH, description="Signal direction")


class BandThreshold(BaseModel):
    """Oscillator band threshold configuration."""
    kind: Literal["band"] = "band"
    upper: float = Field(..., description="Upper band threshold")
    lower: float = Field(..., description="Lower band threshold") 
    hysteresis: float = Field(0.0, ge=0.0, description="Hysteresis value")
    persistence_bars: int = Field(0, ge=0, description="Required persistence in bars")
    
    @validator('upper')
    def upper_greater_than_lower(cls, v, values):
        """Ensure upper > lower."""
        if 'lower' in values and v <= values['lower']:
            raise ValueError('upper must be greater than lower')
        return v


class TimeWindow(BaseModel):
    """Time window specification for percent change thresholds."""
    tz: str = Field(..., description="Timezone identifier")
    start: str = Field(..., pattern=r'^\d{2}:\d{2}$', description="Start time HH:MM")
    end: str = Field(..., pattern=r'^\d{2}:\d{2}$', description="End time HH:MM")
    days: List[str] = Field(..., min_items=1, description="Days of week")


class PercentChangeThreshold(BaseModel):
    """Percent change threshold with time window."""
    kind: Literal["percent_change"] = "percent_change"
    abs_change_gte: float = Field(..., ge=0.0, description="Absolute change threshold")
    direction: ThresholdDirection = Field(ThresholdDirection.BOTH, description="Change direction")
    one_shot: bool = Field(False, description="One-shot trigger mode")
    window: TimeWindow = Field(..., description="Time window specification")


ThresholdType = Union[ZScoreThreshold, BandThreshold, PercentChangeThreshold]


class IndicatorInputs(BaseModel):
    """Indicator input configuration."""
    symbol_scope: Optional[List[str]] = Field(None, description="Applicable symbols")
    timeframe: Optional[str] = Field(None, description="Chart timeframe")
    price_source: Optional[str] = Field(None, description="Price data source")
    external_series: Optional[str] = Field(None, description="External data series")
    provider: Optional[str] = Field(None, description="Data provider")
    resample: Optional[str] = Field(None, description="Resampling configuration")
    transform: Optional[str] = Field(None, description="Data transformation")
    components: Optional[List[str]] = Field(None, description="Component indicators")
    blend: Optional[str] = Field(None, description="Blending method")
    weights: Optional[Dict[str, float]] = Field(None, description="Component weights")
    update_freq: Optional[str] = Field(None, description="Update frequency")
    offsets: Optional[Dict[str, Any]] = Field(None, description="Offset configurations")
    notes: Optional[str] = Field(None, description="Implementation notes")


class IndicatorRecord(BaseModel):
    """Complete indicator specification record."""
    
    IndicatorID: str = Field(..., min_length=3, pattern=r'^[A-Z0-9_]+$', description="Unique identifier")
    Concept: str = Field(..., min_length=3, description="Indicator concept description")
    Indicator_Computation: str = Field(..., min_length=3, description="Computation specification")
    Signal_Logic: str = Field(..., min_length=3, description="Signal logic description")
    OutputType: OutputTypeEnum = Field(..., description="Output data type")
    Thresholds: ThresholdType = Field(..., description="Threshold configuration")
    Inputs: IndicatorInputs = Field(..., description="Input configuration")
    Notes: Optional[str] = Field(None, description="Additional notes")
    
    @validator('IndicatorID')
    def validate_indicator_id_format(cls, v):
        """Validate indicator ID follows naming conventions."""
        if not v.isupper():
            raise ValueError('IndicatorID must be uppercase')
        if '__' in v:
            raise ValueError('IndicatorID cannot contain double underscores')
        return v


class OrderStatus(str, Enum):
    """Order status enumeration."""
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED" 
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class CloseReason(str, Enum):
    """Order close reason enumeration."""
    SL = "SL"           # Stop Loss
    TP = "TP"           # Take Profit
    MANUAL = "MANUAL"   # Manual close
    TIMEOUT = "TIMEOUT" # Timeout close
    UNKNOWN = "UNKNOWN" # Unknown reason


class OrderSide(str, Enum):
    """Order side enumeration."""
    LONG = "LONG"
    SHORT = "SHORT"


class OrderIn(BaseModel):
    """Order status update from EA to Python system."""
    
    ts_utc: datetime = Field(..., description="Timestamp in UTC")
    reentry_key: str = Field(..., pattern=r'^[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[1-9][0-9]*$', 
                            description="Reentry key identifier")
    ticket: int = Field(..., ge=1, description="Broker ticket number")
    status: OrderStatus = Field(..., description="Order status")
    fill_price: float = Field(..., ge=0.0, description="Fill price")
    sl_hit: bool = Field(..., description="Stop loss hit flag")
    tp_hit: bool = Field(..., description="Take profit hit flag")
    close_reason: CloseReason = Field(..., description="Close reason")
    
    @validator('reentry_key')
    def validate_reentry_key_components(cls, v):
        """Validate reentry key has correct format."""
        parts = v.split('~')
        if len(parts) != 5:
            raise ValueError('reentry_key must have exactly 5 tilde-separated components')
        
        # Last component should be numeric
        try:
            int(parts[4])
        except ValueError:
            raise ValueError('Last component of reentry_key must be numeric')
            
        return v


class OrderOut(BaseModel):
    """Order request from Python system to EA."""
    
    ts_utc: datetime = Field(..., description="Timestamp in UTC")
    reentry_key: str = Field(..., pattern=r'^[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[1-9][0-9]*$',
                            description="Reentry key identifier")
    symbol: str = Field(..., pattern=r'^[A-Z]{6}$', description="Currency pair")
    side: OrderSide = Field(..., description="Order side")
    lot: float = Field(..., gt=0.0, description="Lot size")
    sl_pips: int = Field(..., ge=1, description="Stop loss in pips")
    tp_pips: int = Field(..., ge=1, description="Take profit in pips")
    comment_prefix: str = Field(..., max_length=25, description="Comment prefix")
    comment_suffix: str = Field(..., pattern=r'^[A-Z2-7]{4,10}$', description="Comment suffix")
    comment: str = Field(..., max_length=31, description="Full comment")
    
    @validator('comment')
    def validate_comment_composition(cls, v, values):
        """Validate comment is composed of prefix + suffix."""
        if 'comment_prefix' in values and 'comment_suffix' in values:
            expected = f"{values['comment_prefix']}_{values['comment_suffix']}"
            if len(expected) <= 31 and v != expected:
                raise ValueError(f'comment should be "{expected}" based on prefix and suffix')
        return v
    
    @validator('symbol')
    def validate_currency_pair(cls, v):
        """Validate symbol is a proper currency pair."""
        if len(v) != 6 or not v.isalpha() or not v.isupper():
            raise ValueError('symbol must be 6-character uppercase currency pair')
        return v


class HybridId(BaseModel):
    """Hybrid ID structure for validation and parsing."""
    
    outcome: Literal["W2", "W1", "BE", "L1", "L2"] = Field(..., description="Trade outcome")
    duration: Literal["FLASH", "QUICK", "LONG", "EXTENDED"] = Field(..., description="Duration class") 
    proximity: Literal["PRE_1H", "AT_EVENT", "POST_30M"] = Field(..., description="Proximity to event")
    calendar: str = Field(..., description="Calendar identifier")
    direction: Literal["LONG", "SHORT", "ANY"] = Field(..., description="Trade direction")
    generation: int = Field(..., ge=1, le=3, description="Re-entry generation (1-3)")
    suffix: Optional[str] = Field(None, pattern=r'^[a-z0-9]{6}$', description="Comment suffix hash")
    
    @validator('calendar')
    def validate_calendar_format(cls, v):
        """Validate calendar identifier format."""
        if v.startswith('CAL8_') and len(v) >= 8:
            return v
        elif v.startswith('CAL5_') and len(v) >= 8:
            return v
        elif v == 'NONE':
            return v
        else:
            raise ValueError('calendar must be CAL8_*, CAL5_*, or NONE')
    
    def compose(self) -> str:
        """Compose hybrid ID string from components."""
        parts = [
            self.outcome,
            self.duration, 
            self.proximity,
            self.calendar,
            self.direction,
            str(self.generation)
        ]
        
        base_id = '_'.join(parts)
        
        if self.suffix:
            return f"{base_id}_{self.suffix}"
        else:
            return base_id
    
    @classmethod
    def parse(cls, hybrid_id_str: str) -> 'HybridId':
        """Parse hybrid ID string into components."""
        parts = hybrid_id_str.split('_')
        
        if len(parts) < 6:
            raise ValueError('Hybrid ID must have at least 6 components')
        
        outcome, duration, proximity, calendar, direction, generation = parts[:6]
        
        # Reconstruct calendar if it has underscores
        if len(parts) > 6 and not parts[6].isdigit():
            # Calendar has underscores, reconstruct it
            calendar_parts = [calendar] + parts[6:-2]  # All parts except last 2
            calendar = '_'.join(calendar_parts)
            generation = parts[-2]
            suffix = parts[-1] if len(parts) > 6 else None
        else:
            generation = parts[6]
            suffix = parts[7] if len(parts) > 7 else None
        
        return cls(
            outcome=outcome,
            duration=duration,
            proximity=proximity,
            calendar=calendar,
            direction=direction,
            generation=int(generation),
            suffix=suffix
        )