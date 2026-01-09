# DOC_ID: DOC-SERVICE-0018
# advanced_indicators.py - Advanced indicators for your dashboard
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass

from dashboard_backend import (
    BaseIndicator, SignalStrength, IndicatorCategory, SignalData
)

@dataclass
class CurrencyStrengthData:
    currency: str
    strength_score: float
    rank: int
    change_1h: float
    change_4h: float
    change_24h: float
    timestamp: datetime

@dataclass
class PercentChangeData:
    symbol: str
    timeframe: str
    percent_change: float
    direction: str  # 'bullish', 'bearish', 'neutral'
    strength: str   # 'strong', 'weak', 'normal'
    timestamp: datetime

class PercentChangeIndicator(BaseIndicator):
    """Multi-timeframe percent change indicator"""
    
    def __init__(self, symbol: str, timeframe: str = "M15"):
        super().__init__(symbol, timeframe, {
            'windows': [15, 60, 240, 480, 720, 1440]  # minutes: 15m, 1h, 4h, 8h, 12h, 24h
        })
        self.price_history = deque(maxlen=1500)  # Store enough for 24h at 1-minute intervals
        self.window_results = {}
        
    def calculate_signal(self, price_data: Dict[str, Any]) -> SignalData:
        if not self.validate_data(price_data):
            return None
            
        current_price = price_data['close']
        current_time = price_data.get('timestamp', datetime.now())
        
        # Store price with timestamp
        self.price_history.append({
            'price': current_price,
            'timestamp': current_time
        })
        
        # Calculate percent changes for all windows
        percent_changes = self._calculate_percent_changes(current_price, current_time)
        
        # Determine overall signal based on multiple timeframes
        signal, confidence = self._determine_signal(percent_changes)
        
        return SignalData(
            symbol=self.symbol,
            timeframe=self.timeframe,
            indicator="PercentChange",
            signal=signal,
            confidence=confidence,
            timestamp=current_time,
            metadata={
                'percent_changes': percent_changes,
                'dominant_timeframe': self._get_dominant_timeframe(percent_changes)
            }
        )
    
    def _calculate_percent_changes(self, current_price: float, current_time: datetime) -> Dict[str, float]:
        """Calculate percent changes for all time windows"""
        percent_changes = {}
        
        if len(self.price_history) < 2:
            return {f"{w}m": 0.0 for w in self.config['windows']}
        
        for window_minutes in self.config['windows']:
            target_time = current_time - timedelta(minutes=window_minutes)
            
            # Find price closest to target time
            historical_price = self._find_price_at_time(target_time)
            
            if historical_price:
                pct_change = ((current_price - historical_price) / historical_price) * 100
                percent_changes[f"{window_minutes}m"] = round(pct_change, 3)
            else:
                percent_changes[f"{window_minutes}m"] = 0.0
                
        return percent_changes
    
    def _find_price_at_time(self, target_time: datetime) -> float:
        """Find price closest to target time"""
        if not self.price_history:
            return None
            
        # Find closest timestamp
        closest_entry = min(
            self.price_history,
            key=lambda x: abs((x['timestamp'] - target_time).total_seconds())
        )
        
        # Only return if within reasonable time tolerance (5 minutes)
        time_diff = abs((closest_entry['timestamp'] - target_time).total_seconds())
        if time_diff <= 300:  # 5 minutes
            return closest_entry['price']
        
        return None
    
    def _determine_signal(self, percent_changes: Dict[str, float]) -> Tuple[SignalStrength, float]:
        """Determine overall signal from percent changes"""
        if not percent_changes:
            return SignalStrength.NO_SIGNAL, 0.0
        
        # Weight different timeframes (longer = higher weight)
        weights = {
            '15m': 1.0, '60m': 1.5, '240m': 2.0,
            '480m': 2.5, '720m': 3.0, '1440m': 3.5
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for timeframe, pct_change in percent_changes.items():
            weight = weights.get(timeframe, 1.0)
            weighted_score += pct_change * weight
            total_weight += weight
        
        if total_weight > 0:
            avg_change = weighted_score / total_weight
        else:
            avg_change = 0.0
        
        # Determine signal strength
        abs_change = abs(avg_change)
        confidence = min(abs_change * 10, 100)  # Scale confidence
        
        if avg_change > 0.3:
            signal = SignalStrength.STRONG_BUY if avg_change > 0.8 else SignalStrength.WEAK_BUY
        elif avg_change < -0.3:
            signal = SignalStrength.STRONG_SELL if avg_change < -0.8 else SignalStrength.WEAK_SELL
        else:
            signal = SignalStrength.NO_SIGNAL
            
        return signal, confidence
    
    def _get_dominant_timeframe(self, percent_changes: Dict[str, float]) -> str:
        """Get timeframe with strongest signal"""
        if not percent_changes:
            return "none"
            
        # Find timeframe with highest absolute change
        dominant = max(percent_changes.items(), key=lambda x: abs(x[1]))
        return dominant[0]
    
    def get_percent_changes_matrix(self) -> Dict[str, float]:
        """Get current percent changes for display in matrix"""
        if hasattr(self, 'window_results'):
            return self.window_results
        return {}
    
    def get_required_periods(self) -> int:
        return max(self.config['windows']) + 10  # Extra buffer
    
    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.MOMENTUM

class CurrencyStrengthIndicator(BaseIndicator):
    """Currency strength indicator analyzing multiple pairs"""
    
    def __init__(self, currency: str, all_symbols: List[str], timeframe: str = "M15"):
        super().__init__(currency, timeframe, {
            'currency': currency,
            'pairs': self._filter_pairs_for_currency(currency, all_symbols),
            'lookback_periods': 100
        })
        self.currency = currency
        self.monitored_pairs = self.config['pairs']
        self.pair_data = {pair: deque(maxlen=self.config['lookback_periods']) 
                         for pair in self.monitored_pairs}
        self.strength_history = deque(maxlen=50)
        
    def _filter_pairs_for_currency(self, currency: str, all_symbols: List[str]) -> List[str]:
        """Filter symbol list to pairs containing the currency"""
        relevant_pairs = []
        for symbol in all_symbols:
            if currency in symbol and len(symbol) == 6:  # Standard forex pair
                relevant_pairs.append(symbol)
        return relevant_pairs
    
    def update_pair_data(self, symbol: str, price_data: Dict[str, Any]):
        """Update data for a specific pair"""
        if symbol in self.pair_data:
            self.pair_data[symbol].append({
                'timestamp': price_data.get('timestamp', datetime.now()),
                'close': price_data['close'],
                'high': price_data['high'],
                'low': price_data['low']
            })
    
    def calculate_signal(self, price_data: Dict[str, Any] = None) -> SignalData:
        """Calculate currency strength signal"""
        strength_score = self._calculate_strength_score()
        rank = self._calculate_rank()
        
        # Determine signal based on strength
        signal, confidence = self._strength_to_signal(strength_score)
        
        # Store strength history
        self.strength_history.append({
            'timestamp': datetime.now(),
            'strength': strength_score,
            'rank': rank
        })
        
        return SignalData(
            symbol=self.currency,
            timeframe=self.timeframe,
            indicator="CurrencyStrength",
            signal=signal,
            confidence=confidence,
            timestamp=datetime.now(),
            metadata={
                'strength_score': strength_score,
                'rank': rank,
                'monitored_pairs': len(self.monitored_pairs),
                'data_quality': self._assess_data_quality()
            }
        )
    
    def _calculate_strength_score(self) -> float:
        """Calculate strength score based on all pairs"""
        if not self.monitored_pairs:
            return 0.0
        
        total_score = 0.0
        valid_pairs = 0
        
        for pair in self.monitored_pairs:
            pair_data = self.pair_data.get(pair, [])
            if len(pair_data) < 20:  # Need minimum data
                continue
                
            # Calculate pair strength contribution
            pair_score = self._calculate_pair_strength(pair, pair_data)
            
            # Determine if currency is base or quote
            if pair.startswith(self.currency):
                # Currency is base - positive movement is strengthening
                total_score += pair_score
            else:
                # Currency is quote - negative movement is strengthening  
                total_score -= pair_score
                
            valid_pairs += 1
        
        if valid_pairs == 0:
            return 0.0
            
        # Normalize score
        avg_score = total_score / valid_pairs
        
        # Scale to -100 to +100 range
        normalized_score = np.tanh(avg_score / 100) * 100
        
        return round(normalized_score, 2)
    
    def _calculate_pair_strength(self, pair: str, pair_data: deque) -> float:
        """Calculate strength contribution from a single pair"""
        if len(pair_data) < 20:
            return 0.0
        
        prices = [entry['close'] for entry in pair_data]
        
        # Multiple strength metrics
        roc_strength = self._rate_of_change_strength(prices)
        momentum_strength = self._momentum_strength(prices)
        volatility_adj = self._volatility_adjustment(pair_data)
        
        # Weighted combination
        combined_strength = (
            roc_strength * 0.4 +
            momentum_strength * 0.4 +
            volatility_adj * 0.2
        )
        
        return combined_strength
    
    def _rate_of_change_strength(self, prices: List[float]) -> float:
        """Calculate rate of change based strength"""
        if len(prices) < 10:
            return 0.0
            
        # Short and medium term ROC
        short_roc = (prices[-1] - prices[-5]) / prices[-5] * 100
        medium_roc = (prices[-1] - prices[-20]) / prices[-20] * 100
        
        # Weight recent changes more
        weighted_roc = short_roc * 0.7 + medium_roc * 0.3
        return weighted_roc
    
    def _momentum_strength(self, prices: List[float]) -> float:
        """Calculate momentum based strength"""
        if len(prices) < 15:
            return 0.0
            
        # Simple momentum oscillator
        recent_avg = np.mean(prices[-5:])
        older_avg = np.mean(prices[-15:-10])
        
        if older_avg == 0:
            return 0.0
            
        momentum = (recent_avg - older_avg) / older_avg * 100
        return momentum
    
    def _volatility_adjustment(self, pair_data: deque) -> float:
        """Adjust strength based on volatility"""
        if len(pair_data) < 10:
            return 0.0
        
        # Calculate average true range for volatility
        atr_values = []
        for i in range(1, min(len(pair_data), 15)):
            high = pair_data[i]['high']
            low = pair_data[i]['low']
            prev_close = pair_data[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            atr_values.append(tr)
        
        if not atr_values:
            return 0.0
            
        avg_atr = np.mean(atr_values)
        current_range = pair_data[-1]['high'] - pair_data[-1]['low']
        
        # Higher volatility = lower reliability
        volatility_factor = 1.0 - min(current_range / (avg_atr * 2), 1.0)
        
        return volatility_factor * 10  # Scale factor
    
    def _calculate_rank(self) -> int:
        """Calculate rank among all currencies (placeholder)"""
        # This would be calculated by comparing with other currency strength indicators
        # For now, return based on strength score
        strength = self._calculate_strength_score()
        
        if strength > 50:
            return 1
        elif strength > 20:
            return 2
        elif strength > -20:
            return 3
        elif strength > -50:
            return 4
        else:
            return 5
    
    def _strength_to_signal(self, strength: float) -> Tuple[SignalStrength, float]:
        """Convert strength score to trading signal"""
        abs_strength = abs(strength)
        confidence = min(abs_strength / 50 * 100, 100)
        
        if strength > 30:
            signal = SignalStrength.STRONG_BUY
        elif strength > 10:
            signal = SignalStrength.WEAK_BUY
        elif strength < -30:
            signal = SignalStrength.STRONG_SELL
        elif strength < -10:
            signal = SignalStrength.WEAK_SELL
        else:
            signal = SignalStrength.NO_SIGNAL
            confidence = 0.0
        
        return signal, confidence
    
    def _assess_data_quality(self) -> str:
        """Assess quality of data for strength calculation"""
        total_pairs = len(self.monitored_pairs)
        valid_pairs = sum(1 for pair in self.monitored_pairs 
                         if len(self.pair_data.get(pair, [])) >= 20)
        
        if total_pairs == 0:
            return "no_data"
        
        quality_ratio = valid_pairs / total_pairs
        
        if quality_ratio >= 0.8:
            return "excellent"
        elif quality_ratio >= 0.6:
            return "good"
        elif quality_ratio >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def get_strength_data(self) -> CurrencyStrengthData:
        """Get detailed strength data for display"""
        current_strength = self._calculate_strength_score()
        
        # Calculate changes over time
        changes = self._calculate_strength_changes()
        
        return CurrencyStrengthData(
            currency=self.currency,
            strength_score=current_strength,
            rank=self._calculate_rank(),
            change_1h=changes.get('1h', 0.0),
            change_4h=changes.get('4h', 0.0),
            change_24h=changes.get('24h', 0.0),
            timestamp=datetime.now()
        )
    
    def _calculate_strength_changes(self) -> Dict[str, float]:
        """Calculate strength changes over different periods"""
        if len(self.strength_history) < 5:
            return {'1h': 0.0, '4h': 0.0, '24h': 0.0}
        
        current_strength = self.strength_history[-1]['strength']
        changes = {}
        
        # Map time periods to history indices (approximate)
        time_map = {
            '1h': -5,   # 5 periods ago (assuming 15min updates)
            '4h': -16,  # 16 periods ago
            '24h': -96  # 96 periods ago
        }
        
        for period, index in time_map.items():
            if len(self.strength_history) >= abs(index):
                old_strength = self.strength_history[index]['strength']
                changes[period] = current_strength - old_strength
            else:
                changes[period] = 0.0
        
        return changes
    
    def get_required_periods(self) -> int:
        return self.config['lookback_periods']
    
    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.CUSTOM

class ADXTrendStrengthIndicator(BaseIndicator):
    """ADX indicator for trend strength weighting"""
    
    def __init__(self, symbol: str, timeframe: str, period: int = 14):
        super().__init__(symbol, timeframe, {'period': period})
        self.period = period
        self.price_data = deque(maxlen=period * 2)
        
    def calculate_signal(self, price_data: Dict[str, Any]) -> SignalData:
        if not self.validate_data(price_data):
            return None
            
        self.price_data.append({
            'high': price_data['high'],
            'low': price_data['low'],
            'close': price_data['close'],
            'timestamp': price_data.get('timestamp', datetime.now())
        })
        
        if len(self.price_data) < self.period + 1:
            return SignalData(
                symbol=self.symbol,
                timeframe=self.timeframe,
                indicator="ADX",
                signal=SignalStrength.NO_SIGNAL,
                confidence=0.0,
                timestamp=datetime.now(),
                metadata={'adx_value': 0, 'trend_strength': 'insufficient_data'}
            )
        
        adx_value = self._calculate_adx()
        trend_strength = self._interpret_adx(adx_value)
        
        # ADX doesn't give buy/sell signals, just trend strength
        return SignalData(
            symbol=self.symbol,
            timeframe=self.timeframe,
            indicator="ADX",
            signal=SignalStrength.NO_SIGNAL,
            confidence=adx_value,  # Use ADX value as confidence multiplier
            timestamp=datetime.now(),
            metadata={
                'adx_value': adx_value,
                'trend_strength': trend_strength,
                'multiplier_effect': min(adx_value / 25, 2.0)  # Cap at 2x multiplier
            }
        )
    
    def _calculate_adx(self) -> float:
        """Calculate ADX value"""
        if len(self.price_data) < self.period + 1:
            return 0.0
        
        # Simplified ADX calculation
        dm_plus = []
        dm_minus = []
        tr_values = []
        
        for i in range(1, len(self.price_data)):
            current = self.price_data[i]
            previous = self.price_data[i-1]
            
            # Directional Movement
            high_diff = current['high'] - previous['high']
            low_diff = previous['low'] - current['low']
            
            dm_plus.append(high_diff if high_diff > low_diff and high_diff > 0 else 0)
            dm_minus.append(low_diff if low_diff > high_diff and low_diff > 0 else 0)
            
            # True Range
            tr = max(
                current['high'] - current['low'],
                abs(current['high'] - previous['close']),
                abs(current['low'] - previous['close'])
            )
            tr_values.append(tr)
        
        if len(dm_plus) < self.period:
            return 0.0
        
        # Smooth the values
        dm_plus_smooth = np.mean(dm_plus[-self.period:])
        dm_minus_smooth = np.mean(dm_minus[-self.period:])
        tr_smooth = np.mean(tr_values[-self.period:])
        
        if tr_smooth == 0:
            return 0.0
        
        # Calculate DI+ and DI-
        di_plus = (dm_plus_smooth / tr_smooth) * 100
        di_minus = (dm_minus_smooth / tr_smooth) * 100
        
        # Calculate DX
        di_diff = abs(di_plus - di_minus)
        di_sum = di_plus + di_minus
        
        if di_sum == 0:
            return 0.0
        
        dx = (di_diff / di_sum) * 100
        
        # ADX is smoothed DX (simplified as single DX value here)
        return round(dx, 2)
    
    def _interpret_adx(self, adx_value: float) -> str:
        """Interpret ADX value"""
        if adx_value > 50:
            return "very_strong"
        elif adx_value > 25:
            return "strong"
        elif adx_value > 20:
            return "trending"
        else:
            return "weak"
    
    def get_multiplier(self) -> float:
        """Get ADX multiplier for signal weighting"""
        if hasattr(self, 'last_signal') and self.last_signal:
            metadata = self.last_signal.metadata or {}
            return metadata.get('multiplier_effect', 1.0)
        return 1.0
    
    def get_required_periods(self) -> int:
        return self.period * 2
    
    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.TREND

# Enhanced Signal Aggregator with ADX weighting
class EnhancedSignalAggregator:
    """Enhanced aggregator with ADX trend strength weighting"""
    
    def __init__(self):
        self.adx_indicators = {}  # symbol_timeframe -> ADXIndicator
        
    def add_adx_indicator(self, symbol: str, timeframe: str, adx_indicator: ADXTrendStrengthIndicator):
        """Add ADX indicator for trend strength weighting"""
        key = f"{symbol}_{timeframe}"
        self.adx_indicators[key] = adx_indicator
    
    def aggregate_signals_with_adx(self, signals: List[SignalData]) -> Dict[str, Any]:
        """Aggregate signals with ADX trend strength weighting"""
        if not signals:
            return {
                'symbol': '', 'timeframe': '', 'buy_count': 0, 'sell_count': 0,
                'total_signals': 0, 'confidence': 0.0, 'dominant_signal': 'No Signal',
                'adx_multiplier': 1.0, 'trend_strength': 'unknown'
            }
        
        symbol = signals[0].symbol
        timeframe = signals[0].timeframe
        adx_key = f"{symbol}_{timeframe}"
        
        # Get ADX multiplier
        adx_multiplier = 1.0
        trend_strength = 'unknown'
        
        if adx_key in self.adx_indicators:
            adx_multiplier = self.adx_indicators[adx_key].get_multiplier()
            if hasattr(self.adx_indicators[adx_key], 'last_signal') and self.adx_indicators[adx_key].last_signal:
                metadata = self.adx_indicators[adx_key].last_signal.metadata or {}
                trend_strength = metadata.get('trend_strength', 'unknown')
        
        # Count signals
        buy_signals = [s for s in signals if 'Buy' in s.signal.value]
        sell_signals = [s for s in signals if 'Sell' in s.signal.value]
        
        buy_count = len(buy_signals)
        sell_count = len(sell_signals)
        total_signals = buy_count + sell_count
        
        if total_signals == 0:
            dominant_signal = 'No Signal'
            confidence = 0.0
        else:
            # Apply ADX weighting to confidence
            raw_confidence = max(buy_count, sell_count) / total_signals * 100
            weighted_confidence = min(raw_confidence * adx_multiplier, 100.0)
            
            if buy_count > sell_count:
                if buy_count >= sell_count * 2:
                    dominant_signal = 'Strong Buy'
                else:
                    dominant_signal = 'Buy'
            else:
                if sell_count >= buy_count * 2:
                    dominant_signal = 'Strong Sell'
                else:
                    dominant_signal = 'Sell'
            
            confidence = weighted_confidence
        
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'total_signals': total_signals,
            'confidence': round(confidence, 1),
            'dominant_signal': dominant_signal,
            'adx_multiplier': round(adx_multiplier, 2),
            'trend_strength': trend_strength,
            'raw_confidence': round(raw_confidence if 'raw_confidence' in locals() else 0.0, 1)
        }

# Matrix Display Helper
class PercentChangeMatrix:
    """Helper class for displaying percent change matrix"""
    
    def __init__(self, symbols: List[str], timeframes: List[str]):
        self.symbols = symbols
        self.timeframes = timeframes
        self.indicators = {}  # symbol -> PercentChangeIndicator
        
    def add_symbol(self, symbol: str):
        """Add percent change indicator for symbol"""
        self.indicators[symbol] = PercentChangeIndicator(symbol)
    
    def update_symbol(self, symbol: str, price_data: Dict[str, Any]):
        """Update price data for symbol"""
        if symbol in self.indicators:
            self.indicators[symbol].calculate_signal(price_data)
    
    def get_matrix_data(self) -> Dict[str, Dict[str, float]]:
        """Get matrix data for display"""
        matrix_data = {}
        
        for symbol in self.symbols:
            if symbol in self.indicators:
                percent_changes = self.indicators[symbol].get_percent_changes_matrix()
                matrix_data[symbol] = percent_changes
            else:
                # Default empty data
                matrix_data[symbol] = {f"{tf}": 0.0 for tf in ['15m', '60m', '240m', '480m', '720m', '1440m']}
        
        return matrix_data
    
    def get_color_coding(self, percent_change: float) -> str:
        """Get color coding for percent change value"""
        if percent_change > 0.5:
            return 'strong_bullish'
        elif percent_change > 0.1:
            return 'bullish'
        elif percent_change < -0.5:
            return 'strong_bearish'
        elif percent_change < -0.1:
            return 'bearish'
        else:
            return 'neutral'

class CurrencyStrengthMatrix:
    """Helper class for currency strength display"""
    
    def __init__(self, currencies: List[str], symbols: List[str]):
        self.currencies = currencies
        self.symbols = symbols
        self.strength_indicators = {}
        
        # Initialize strength indicators for each currency
        for currency in currencies:
            self.strength_indicators[currency] = CurrencyStrengthIndicator(currency, symbols)
    
    def update_pair_data(self, symbol: str, price_data: Dict[str, Any]):
        """Update data for all relevant currency strength indicators"""
        for currency in self.currencies:
            if currency in symbol:
                self.strength_indicators[currency].update_pair_data(symbol, price_data)
    
    def get_strength_rankings(self) -> List[CurrencyStrengthData]:
        """Get currency strength rankings"""
        strength_data = []
        
        for currency in self.currencies:
            if currency in self.strength_indicators:
                data = self.strength_indicators[currency].get_strength_data()
                strength_data.append(data)
        
        # Sort by strength score (descending)
        strength_data.sort(key=lambda x: x.strength_score, reverse=True)
        
        # Update ranks
        for i, data in enumerate(strength_data):
            data.rank = i + 1
        
        return strength_data
    
    def get_top_pairs(self) -> List[Dict[str, Any]]:
        """Get top trading pairs based on currency strength divergence"""
        rankings = self.get_strength_rankings()
        
        if len(rankings) < 2:
            return []
        
        top_pairs = []
        
        # Find pairs with high strength divergence
        for i in range(len(rankings)):
            for j in range(i + 1, len(rankings)):
                strong_currency = rankings[i]
                weak_currency = rankings[j]
                
                strength_diff = strong_currency.strength_score - weak_currency.strength_score
                
                if strength_diff > 30:  # Significant divergence
                    # Check if pair exists in symbols
                    pair1 = f"{strong_currency.currency}{weak_currency.currency}"
                    pair2 = f"{weak_currency.currency}{strong_currency.currency}"
                    
                    if pair1 in self.symbols:
                        top_pairs.append({
                            'symbol': pair1,
                            'direction': 'buy',
                            'strength_diff': strength_diff,
                            'strong_currency': strong_currency.currency,
                            'weak_currency': weak_currency.currency
                        })
                    elif pair2 in self.symbols:
                        top_pairs.append({
                            'symbol': pair2,
                            'direction': 'sell',
                            'strength_diff': strength_diff,
                            'strong_currency': strong_currency.currency,
                            'weak_currency': weak_currency.currency
                        })
        
        # Sort by strength difference
        top_pairs.sort(key=lambda x: x['strength_diff'], reverse=True)
        
        return top_pairs[:5]  # Return top 5 pairs