"""
Positioning Ratio Index - Institutional vs Retail Positioning Analysis

This module implements the positioning ratio index that compares institutional
positioning (CFTC COT data) against retail sentiment to identify contrarian
trading opportunities in the forex market.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
# Note: In production would use numpy/pandas, but for integration testing
# we use built-in Python functions to avoid dependencies
from enum import Enum

logger = logging.getLogger(__name__)


class PositioningSignal(Enum):
    """Positioning-based signals."""
    STRONG_BUY = "STRONG_BUY"      # Institutions buying, retail selling
    BUY = "BUY"                    # Moderate institutional bias
    NEUTRAL = "NEUTRAL"            # Balanced positioning
    SELL = "SELL"                  # Moderate retail bias
    STRONG_SELL = "STRONG_SELL"    # Institutions selling, retail buying


@dataclass
class PositioningData:
    """Combined positioning data point."""
    timestamp: datetime
    currency: str
    institutional_net_long: float    # % net long from CFTC
    retail_net_long: float          # % net long from retail brokers
    positioning_ratio: float        # Institutional/retail ratio
    extremity_score: float         # How extreme the positioning is (0-1)
    signal: PositioningSignal
    confidence: float              # Signal confidence (0-1)


class PositioningRatioIndex:
    """
    Calculates positioning ratio index using institutional and retail data.
    
    The index identifies divergences between institutional (CFTC COT) and 
    retail sentiment positioning to generate contrarian trading signals.
    """
    
    def __init__(self, lookback_periods: int = 52, extremity_threshold: float = 0.8):
        """
        Initialize the positioning ratio index.
        
        Args:
            lookback_periods: Number of periods for extremity calculation
            extremity_threshold: Threshold for extreme positioning (0-1)
        """
        self.lookback_periods = lookback_periods
        self.extremity_threshold = extremity_threshold
        self.historical_data: Dict[str, List[PositioningData]] = {}
    
    def calculate_positioning_ratio(
        self, 
        institutional_long: float,
        institutional_short: float,
        retail_long: float,
        retail_short: float
    ) -> Tuple[float, float, float]:
        """
        Calculate positioning metrics.
        
        Args:
            institutional_long: Institutional long positions
            institutional_short: Institutional short positions
            retail_long: Retail long positions
            retail_short: Retail short positions
            
        Returns:
            Tuple of (institutional_net_long_pct, retail_net_long_pct, ratio)
        """
        # Calculate net positioning percentages
        inst_total = institutional_long + institutional_short
        retail_total = retail_long + retail_short
        
        if inst_total == 0 or retail_total == 0:
            return 0.0, 0.0, 1.0
        
        inst_net_long_pct = (institutional_long - institutional_short) / inst_total * 100
        retail_net_long_pct = (retail_long - retail_short) / retail_total * 100
        
        # Calculate positioning ratio (institutional bias vs retail bias)
        if retail_net_long_pct == 0:
            ratio = 1.0 if inst_net_long_pct >= 0 else -1.0
        else:
            ratio = inst_net_long_pct / retail_net_long_pct
            
        return inst_net_long_pct, retail_net_long_pct, ratio
    
    def calculate_extremity_score(self, currency: str, current_ratio: float) -> float:
        """
        Calculate how extreme the current positioning is compared to history.
        
        Args:
            currency: Currency pair
            current_ratio: Current positioning ratio
            
        Returns:
            Extremity score (0-1, where 1 is most extreme)
        """
        if currency not in self.historical_data:
            return 0.5  # No historical data, assume neutral
        
        historical_ratios = [
            data.positioning_ratio 
            for data in self.historical_data[currency][-self.lookback_periods:]
        ]
        
        if len(historical_ratios) < 10:
            return 0.5  # Insufficient data
        
        # Calculate percentiles manually (simple implementation)
        sorted_ratios = sorted(historical_ratios)
        n = len(sorted_ratios)
        p10 = sorted_ratios[max(0, int(0.10 * n))]
        p25 = sorted_ratios[max(0, int(0.25 * n))]  
        p50 = sorted_ratios[max(0, int(0.50 * n))]
        p75 = sorted_ratios[max(0, int(0.75 * n))]
        p90 = sorted_ratios[max(0, int(0.90 * n))]
        percentile = [p10, p25, p50, p75, p90]
        
        if current_ratio <= percentile[0]:  # Bottom 10%
            return 0.9
        elif current_ratio <= percentile[1]:  # Bottom 25%
            return 0.7
        elif current_ratio >= percentile[4]:  # Top 10%
            return 0.9
        elif current_ratio >= percentile[3]:  # Top 25%
            return 0.7
        else:
            return abs(current_ratio - percentile[2]) / (percentile[3] - percentile[1])
    
    def generate_signal(
        self,
        institutional_net_long: float,
        retail_net_long: float,
        positioning_ratio: float,
        extremity_score: float
    ) -> Tuple[PositioningSignal, float]:
        """
        Generate positioning-based signal.
        
        Args:
            institutional_net_long: Institutional net long percentage
            retail_net_long: Retail net long percentage
            positioning_ratio: Positioning ratio
            extremity_score: Extremity score (0-1)
            
        Returns:
            Tuple of (signal, confidence)
        """
        # Base confidence on extremity
        base_confidence = extremity_score
        
        # Determine signal based on positioning divergence
        inst_bullish = institutional_net_long > 10  # Institutions net long > 10%
        retail_bullish = retail_net_long > 10       # Retail net long > 10%
        
        inst_bearish = institutional_net_long < -10  # Institutions net short > 10%
        retail_bearish = retail_net_long < -10       # Retail net short > 10%
        
        # Strong contrarian signals (institutions vs retail)
        if inst_bullish and retail_bearish and extremity_score > self.extremity_threshold:
            return PositioningSignal.STRONG_BUY, min(base_confidence + 0.2, 1.0)
        
        if inst_bearish and retail_bullish and extremity_score > self.extremity_threshold:
            return PositioningSignal.STRONG_SELL, min(base_confidence + 0.2, 1.0)
        
        # Moderate signals
        if inst_bullish and not retail_bullish:
            return PositioningSignal.BUY, base_confidence
        
        if inst_bearish and not retail_bearish:
            return PositioningSignal.SELL, base_confidence
        
        # Neutral or conflicting signals
        return PositioningSignal.NEUTRAL, base_confidence * 0.5
    
    def update(
        self,
        timestamp: datetime,
        currency: str,
        institutional_long: float,
        institutional_short: float, 
        retail_long: float,
        retail_short: float
    ) -> PositioningData:
        """
        Update positioning data and generate new signal.
        
        Args:
            timestamp: Data timestamp
            currency: Currency pair (e.g., 'EUR', 'GBP')
            institutional_long: Institutional long positions
            institutional_short: Institutional short positions
            retail_long: Retail long positions  
            retail_short: Retail short positions
            
        Returns:
            Updated positioning data with signal
        """
        # Calculate positioning metrics
        inst_net_long, retail_net_long, ratio = self.calculate_positioning_ratio(
            institutional_long, institutional_short,
            retail_long, retail_short
        )
        
        # Calculate extremity score
        extremity_score = self.calculate_extremity_score(currency, ratio)
        
        # Generate signal
        signal, confidence = self.generate_signal(
            inst_net_long, retail_net_long, ratio, extremity_score
        )
        
        # Create positioning data
        positioning_data = PositioningData(
            timestamp=timestamp,
            currency=currency,
            institutional_net_long=inst_net_long,
            retail_net_long=retail_net_long,
            positioning_ratio=ratio,
            extremity_score=extremity_score,
            signal=signal,
            confidence=confidence
        )
        
        # Store historical data
        if currency not in self.historical_data:
            self.historical_data[currency] = []
        
        self.historical_data[currency].append(positioning_data)
        
        # Keep only recent history
        if len(self.historical_data[currency]) > self.lookback_periods * 2:
            self.historical_data[currency] = self.historical_data[currency][-self.lookback_periods:]
        
        logger.info(
            f"Updated positioning data for {currency}: "
            f"ratio={ratio:.3f}, extremity={extremity_score:.3f}, "
            f"signal={signal.value}, confidence={confidence:.3f}"
        )
        
        return positioning_data
    
    def get_currency_positioning(self, currency: str) -> Optional[PositioningData]:
        """Get latest positioning data for currency."""
        if currency not in self.historical_data or not self.historical_data[currency]:
            return None
        return self.historical_data[currency][-1]
    
    def get_positioning_history(
        self, 
        currency: str, 
        periods: Optional[int] = None
    ) -> List[PositioningData]:
        """Get positioning history for currency."""
        if currency not in self.historical_data:
            return []
        
        if periods is None:
            return self.historical_data[currency].copy()
        
        return self.historical_data[currency][-periods:].copy()
    
    def get_summary_statistics(self, currency: str) -> Dict[str, float]:
        """Get summary statistics for currency positioning."""
        if currency not in self.historical_data or not self.historical_data[currency]:
            return {}
        
        data = self.historical_data[currency]
        ratios = [d.positioning_ratio for d in data]
        extremities = [d.extremity_score for d in data]
        
        return {
            "avg_positioning_ratio": sum(ratios) / len(ratios) if ratios else 0.0,
            "std_positioning_ratio": self._calculate_std(ratios),
            "min_positioning_ratio": min(ratios) if ratios else 0.0,
            "max_positioning_ratio": max(ratios) if ratios else 0.0,
            "avg_extremity_score": sum(extremities) / len(extremities) if extremities else 0.0,
            "current_positioning_ratio": ratios[-1] if ratios else 0.0,
            "current_extremity_score": extremities[-1] if extremities else 0.0,
            "total_observations": len(data)
        }
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation without numpy."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5