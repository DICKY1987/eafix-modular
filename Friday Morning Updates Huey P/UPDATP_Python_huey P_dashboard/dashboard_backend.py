# dashboard_backend.py - Scalable Trading Dashboard Backend
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Tuple
from collections import defaultdict
import sqlite3
import threading
import time

# Configuration and Enums
class SignalStrength(Enum):
    STRONG_SELL = "Strong Sell"
    WEAK_SELL = "Weak Sell"
    NO_SIGNAL = "No Signal"
    WEAK_BUY = "Weak Buy"
    STRONG_BUY = "Strong Buy"

class IndicatorCategory(Enum):
    TREND = "trend"
    OSCILLATOR = "oscillator"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    MOMENTUM = "momentum"
    CUSTOM = "custom"

@dataclass
class SignalData:
    symbol: str
    timeframe: str
    indicator: str
    signal: SignalStrength
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any] = None

@dataclass
class AggregatedSignal:
    symbol: str
    timeframe: str
    buy_count: int
    sell_count: int
    total_signals: int
    confidence: float
    dominant_signal: SignalStrength
    adx_weight: float = 1.0

# Base Indicator Interface
class BaseIndicator(ABC):
    """Enhanced base indicator class with plugin architecture"""
    
    def __init__(self, symbol: str, timeframe: str, config: Dict[str, Any] = None):
        self.symbol = symbol
        self.timeframe = timeframe
        self.config = config or {}
        self.last_signal = None
        self.last_update = None
        self.is_enabled = True
        
    @abstractmethod
    def calculate_signal(self, price_data: Dict[str, Any]) -> SignalData:
        """Calculate and return signal for this indicator"""
        pass
    
    @abstractmethod
    def get_required_periods(self) -> int:
        """Return minimum periods needed for calculation"""
        pass
    
    def get_display_config(self) -> Dict[str, Any]:
        """Return configuration for GUI display"""
        return {
            'name': self.__class__.__name__,
            'category': self.get_category(),
            'enabled': self.is_enabled,
            'timeframe': self.timeframe,
            'symbol': self.symbol
        }
    
    def get_category(self) -> IndicatorCategory:
        """Return indicator category for grouping"""
        return IndicatorCategory.CUSTOM
    
    def validate_data(self, price_data: Dict[str, Any]) -> bool:
        """Validate input data before calculation"""
        required_fields = ['open', 'high', 'low', 'close', 'timestamp']
        return all(field in price_data for field in required_fields)

# Sample Indicator Implementations
class RSIIndicator(BaseIndicator):
    def __init__(self, symbol: str, timeframe: str, period: int = 14):
        super().__init__(symbol, timeframe, {'period': period})
        self.period = period
        self.price_history = []
    
    def calculate_signal(self, price_data: Dict[str, Any]) -> SignalData:
        if not self.validate_data(price_data):
            return None
            
        # Simplified RSI calculation
        self.price_history.append(price_data['close'])
        if len(self.price_history) > self.period + 1:
            self.price_history.pop(0)
            
        if len(self.price_history) < self.period:
            signal = SignalStrength.NO_SIGNAL
            confidence = 0.0
        else:
            # Mock RSI calculation for demo
            rsi_value = 50 + (hash(str(price_data['close'])) % 50) - 25
            
            if rsi_value < 30:
                signal = SignalStrength.STRONG_BUY if rsi_value < 20 else SignalStrength.WEAK_BUY
                confidence = (30 - rsi_value) / 30 * 100
            elif rsi_value > 70:
                signal = SignalStrength.STRONG_SELL if rsi_value > 80 else SignalStrength.WEAK_SELL
                confidence = (rsi_value - 70) / 30 * 100
            else:
                signal = SignalStrength.NO_SIGNAL
                confidence = 0.0
        
        return SignalData(
            symbol=self.symbol,
            timeframe=self.timeframe,
            indicator="RSI",
            signal=signal,
            confidence=min(confidence, 100.0),
            timestamp=datetime.now(),
            metadata={'rsi_value': rsi_value if 'rsi_value' in locals() else None}
        )
    
    def get_required_periods(self) -> int:
        return self.period + 1
    
    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.OSCILLATOR

class MACDIndicator(BaseIndicator):
    def __init__(self, symbol: str, timeframe: str, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__(symbol, timeframe, {'fast': fast, 'slow': slow, 'signal': signal})
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
        
    def calculate_signal(self, price_data: Dict[str, Any]) -> SignalData:
        # Mock MACD calculation
        macd_value = (hash(str(price_data['close'])) % 200) - 100
        signal_line = macd_value * 0.8
        
        if macd_value > signal_line and macd_value > 0:
            signal = SignalStrength.STRONG_BUY if macd_value > 50 else SignalStrength.WEAK_BUY
            confidence = min(abs(macd_value) / 50 * 100, 100)
        elif macd_value < signal_line and macd_value < 0:
            signal = SignalStrength.STRONG_SELL if macd_value < -50 else SignalStrength.WEAK_SELL
            confidence = min(abs(macd_value) / 50 * 100, 100)
        else:
            signal = SignalStrength.NO_SIGNAL
            confidence = 0.0
            
        return SignalData(
            symbol=self.symbol,
            timeframe=self.timeframe,
            indicator="MACD",
            signal=signal,
            confidence=confidence,
            timestamp=datetime.now(),
            metadata={'macd': macd_value, 'signal_line': signal_line}
        )
    
    def get_required_periods(self) -> int:
        return self.slow + self.signal_period
    
    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.TREND

# Indicator Registry for Plugin Management
class IndicatorRegistry:
    """Registry for managing indicator plugins"""
    
    def __init__(self):
        self._indicators = {}
        self._register_default_indicators()
    
    def _register_default_indicators(self):
        """Register built-in indicators"""
        self.register("RSI", RSIIndicator)
        self.register("MACD", MACDIndicator)
        # Add more default indicators here
    
    def register(self, name: str, indicator_class: type):
        """Register a new indicator class"""
        if not issubclass(indicator_class, BaseIndicator):
            raise ValueError(f"Indicator {name} must inherit from BaseIndicator")
        self._indicators[name] = indicator_class
    
    def get_available_indicators(self) -> Dict[IndicatorCategory, List[str]]:
        """Get available indicators grouped by category"""
        result = defaultdict(list)
        for name, indicator_class in self._indicators.items():
            # Create temporary instance to get category
            temp_instance = indicator_class("TEMP", "M15")
            category = temp_instance.get_category()
            result[category].append(name)
        return dict(result)
    
    def create_indicator(self, name: str, symbol: str, timeframe: str, **kwargs) -> BaseIndicator:
        """Create indicator instance"""
        if name not in self._indicators:
            raise ValueError(f"Unknown indicator: {name}")
        return self._indicators[name](symbol, timeframe, **kwargs)

# Signal Aggregation Engine
class SignalAggregator:
    """Aggregates individual signals into summary signals"""
    
    def __init__(self):
        self.adx_weight = 1.0  # Default ADX multiplier
    
    def aggregate_signals(self, signals: List[SignalData]) -> AggregatedSignal:
        """Aggregate list of signals into summary"""
        if not signals:
            return AggregatedSignal(
                symbol="", timeframe="", buy_count=0, sell_count=0,
                total_signals=0, confidence=0.0, dominant_signal=SignalStrength.NO_SIGNAL
            )
        
        symbol = signals[0].symbol
        timeframe = signals[0].timeframe
        
        buy_count = sum(1 for s in signals if 'Buy' in s.signal.value)
        sell_count = sum(1 for s in signals if 'Sell' in s.signal.value)
        total_signals = buy_count + sell_count
        
        if total_signals == 0:
            dominant_signal = SignalStrength.NO_SIGNAL
            confidence = 0.0
        else:
            if buy_count > sell_count:
                dominant_signal = SignalStrength.STRONG_BUY if buy_count >= sell_count * 2 else SignalStrength.WEAK_BUY
                confidence = (buy_count / total_signals) * 100 * self.adx_weight
            else:
                dominant_signal = SignalStrength.STRONG_SELL if sell_count >= buy_count * 2 else SignalStrength.WEAK_SELL
                confidence = (sell_count / total_signals) * 100 * self.adx_weight
        
        return AggregatedSignal(
            symbol=symbol,
            timeframe=timeframe,
            buy_count=buy_count,
            sell_count=sell_count,
            total_signals=total_signals,
            confidence=min(confidence, 100.0),
            dominant_signal=dominant_signal,
            adx_weight=self.adx_weight
        )

# Data Storage Manager
class SignalDataManager:
    """Manages storage and retrieval of signal data"""
    
    def __init__(self, db_path: str = "signals.db"):
        self.db_path = db_path
        self.connection_lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    indicator TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS aggregated_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    buy_count INTEGER NOT NULL,
                    sell_count INTEGER NOT NULL,
                    total_signals INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    dominant_signal TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_signals_symbol_timeframe 
                ON signals(symbol, timeframe, timestamp)
            ''')
    
    def store_signal(self, signal: SignalData):
        """Store individual signal"""
        with self.connection_lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO signals 
                    (symbol, timeframe, indicator, signal, confidence, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal.symbol, signal.timeframe, signal.indicator,
                    signal.signal.value, signal.confidence,
                    signal.timestamp.isoformat(),
                    json.dumps(signal.metadata) if signal.metadata else None
                ))
    
    def store_aggregated_signal(self, agg_signal: AggregatedSignal):
        """Store aggregated signal"""
        with self.connection_lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO aggregated_signals
                    (symbol, timeframe, buy_count, sell_count, total_signals, 
                     confidence, dominant_signal, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agg_signal.symbol, agg_signal.timeframe,
                    agg_signal.buy_count, agg_signal.sell_count,
                    agg_signal.total_signals, agg_signal.confidence,
                    agg_signal.dominant_signal.value, datetime.now().isoformat()
                ))
    
    def get_latest_signals(self, symbol: str = None, timeframe: str = None, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get latest signals with optional filtering"""
        with self.connection_lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = "SELECT * FROM signals WHERE 1=1"
                params = []
                
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                
                if timeframe:
                    query += " AND timeframe = ?"
                    params.append(timeframe)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

# Main Dashboard Engine
class DashboardEngine:
    """Main engine coordinating all dashboard components"""
    
    def __init__(self, symbols: List[str], timeframes: List[str]):
        self.symbols = symbols
        self.timeframes = timeframes
        self.registry = IndicatorRegistry()
        self.aggregator = SignalAggregator()
        self.data_manager = SignalDataManager()
        self.active_indicators = {}
        self.is_running = False
        self.update_interval = 5  # seconds
        
    def add_indicator(self, symbol: str, timeframe: str, indicator_name: str, **kwargs):
        """Add indicator for specific symbol/timeframe"""
        key = f"{symbol}_{timeframe}_{indicator_name}"
        indicator = self.registry.create_indicator(indicator_name, symbol, timeframe, **kwargs)
        self.active_indicators[key] = indicator
        logging.info(f"Added indicator: {key}")
    
    def remove_indicator(self, symbol: str, timeframe: str, indicator_name: str):
        """Remove indicator"""
        key = f"{symbol}_{timeframe}_{indicator_name}"
        if key in self.active_indicators:
            del self.active_indicators[key]
            logging.info(f"Removed indicator: {key}")
    
    def setup_default_indicators(self):
        """Setup default indicator set for all symbols/timeframes"""
        default_indicators = ["RSI", "MACD"]
        
        for symbol in self.symbols:
            for timeframe in self.timeframes:
                for indicator in default_indicators:
                    self.add_indicator(symbol, timeframe, indicator)
    
    def update_signals(self, price_data: Dict[str, Dict[str, Any]]):
        """Update all signals with new price data"""
        all_signals = []
        
        for key, indicator in self.active_indicators.items():
            if not indicator.is_enabled:
                continue
                
            symbol = indicator.symbol
            timeframe = indicator.timeframe
            
            if symbol in price_data and timeframe in price_data[symbol]:
                try:
                    signal = indicator.calculate_signal(price_data[symbol][timeframe])
                    if signal:
                        all_signals.append(signal)
                        self.data_manager.store_signal(signal)
                except Exception as e:
                    logging.error(f"Error calculating signal for {key}: {e}")
        
        # Aggregate signals by symbol/timeframe
        signal_groups = defaultdict(list)
        for signal in all_signals:
            key = f"{signal.symbol}_{signal.timeframe}"
            signal_groups[key].append(signal)
        
        # Create aggregated signals
        for group_key, signals in signal_groups.items():
            agg_signal = self.aggregator.aggregate_signals(signals)
            self.data_manager.store_aggregated_signal(agg_signal)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data for frontend"""
        # This would be called by your web API to get current state
        signal_matrix = {}
        summary_data = {}
        
        for symbol in self.symbols:
            signal_matrix[symbol] = {}
            summary_data[symbol] = {}
            
            for timeframe in self.timeframes:
                # Get latest signals for this symbol/timeframe
                signals = self.data_manager.get_latest_signals(symbol, timeframe, 50)
                
                # Organize by indicator
                indicator_signals = {}
                for signal in signals:
                    indicator_signals[signal['indicator']] = signal['signal']
                
                signal_matrix[symbol][timeframe] = indicator_signals
                
                # Get aggregated summary
                # This would come from your aggregated_signals table
                summary_data[symbol][timeframe] = {
                    'summary': 'Buy',  # Placeholder
                    'confidence': 75,
                    'buy_signals': 5,
                    'sell_signals': 2
                }
        
        return {
            'signal_matrix': signal_matrix,
            'summary_data': summary_data,
            'last_update': datetime.now().isoformat()
        }
    
    def start_real_time_updates(self):
        """Start real-time signal updates"""
        self.is_running = True
        
        def update_loop():
            while self.is_running:
                try:
                    # Simulate getting price data (replace with your DDE client)
                    price_data = self._get_mock_price_data()
                    self.update_signals(price_data)
                    time.sleep(self.update_interval)
                except Exception as e:
                    logging.error(f"Error in update loop: {e}")
                    time.sleep(1)
        
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
        logging.info("Started real-time signal updates")
    
    def stop_real_time_updates(self):
        """Stop real-time updates"""
        self.is_running = False
        logging.info("Stopped real-time signal updates")
    
    def _get_mock_price_data(self) -> Dict[str, Dict[str, Any]]:
        """Generate mock price data for testing"""
        import random
        price_data = {}
        
        for symbol in self.symbols:
            price_data[symbol] = {}
            base_price = 1.1000 if 'EUR' in symbol else 1.0000
            
            for timeframe in self.timeframes:
                # Generate realistic OHLC data
                close = base_price + random.uniform(-0.01, 0.01)
                high = close + random.uniform(0, 0.005)
                low = close - random.uniform(0, 0.005)
                open_price = low + random.uniform(0, high - low)
                
                price_data[symbol][timeframe] = {
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': random.randint(1000, 10000),
                    'timestamp': datetime.now()
                }
        
        return price_data

# Web API Integration Layer
class DashboardAPI:
    """FastAPI/Flask integration layer for web interface"""
    
    def __init__(self, dashboard_engine: DashboardEngine):
        self.engine = dashboard_engine
    
    def get_signals(self, symbol: str = None, timeframe: str = None):
        """API endpoint to get current signals"""
        return self.engine.get_dashboard_data()
    
    def add_indicator_endpoint(self, symbol: str, timeframe: str, 
                             indicator_name: str, config: Dict[str, Any] = None):
        """API endpoint to add new indicator"""
        try:
            self.engine.add_indicator(symbol, timeframe, indicator_name, **(config or {}))
            return {"status": "success", "message": f"Added {indicator_name} for {symbol} {timeframe}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def remove_indicator_endpoint(self, symbol: str, timeframe: str, indicator_name: str):
        """API endpoint to remove indicator"""
        try:
            self.engine.remove_indicator(symbol, timeframe, indicator_name)
            return {"status": "success", "message": f"Removed {indicator_name} for {symbol} {timeframe}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_available_indicators(self):
        """API endpoint to get available indicators"""
        return self.engine.registry.get_available_indicators()

# Configuration and Setup Classes
@dataclass
class DashboardConfig:
    """Configuration for dashboard setup"""
    symbols: List[str]
    timeframes: List[str]
    update_interval: int = 5
    db_path: str = "signals.db"
    default_indicators: List[str] = None
    
    def __post_init__(self):
        if self.default_indicators is None:
            self.default_indicators = ["RSI", "MACD"]

class IndicatorPluginLoader:
    """Dynamic plugin loader for custom indicators"""
    
    def __init__(self, plugin_directory: str = "indicators"):
        self.plugin_directory = plugin_directory
        self.loaded_plugins = {}
    
    def load_plugins(self, registry: IndicatorRegistry):
        """Load indicator plugins from directory"""
        import os
        import importlib.util
        
        if not os.path.exists(self.plugin_directory):
            os.makedirs(self.plugin_directory)
            return
        
        for filename in os.listdir(self.plugin_directory):
            if filename.endswith('.py') and not filename.startswith('__'):
                plugin_path = os.path.join(self.plugin_directory, filename)
                plugin_name = filename[:-3]  # Remove .py extension
                
                try:
                    spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for indicator classes in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseIndicator) and 
                            attr != BaseIndicator):
                            
                            registry.register(attr_name, attr)
                            self.loaded_plugins[attr_name] = plugin_path
                            logging.info(f"Loaded plugin indicator: {attr_name}")
                            
                except Exception as e:
                    logging.error(f"Error loading plugin {filename}: {e}")

# Example Usage and Factory
class DashboardFactory:
    """Factory for creating configured dashboard instances"""
    
    @staticmethod
    def create_forex_dashboard() -> DashboardEngine:
        """Create dashboard configured for forex trading"""
        config = DashboardConfig(
            symbols=['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD'],
            timeframes=['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'],
            update_interval=5,
            default_indicators=['RSI', 'MACD']
        )
        
        engine = DashboardEngine(config.symbols, config.timeframes)
        engine.update_interval = config.update_interval
        
        # Load plugins
        plugin_loader = IndicatorPluginLoader()
        plugin_loader.load_plugins(engine.registry)
        
        # Setup default indicators
        engine.setup_default_indicators()
        
        return engine
    
    @staticmethod
    def create_crypto_dashboard() -> DashboardEngine:
        """Create dashboard configured for cryptocurrency trading"""
        config = DashboardConfig(
            symbols=['BTCUSD', 'ETHUSD', 'ADAUSD', 'DOTUSD', 'LINKUSD'],
            timeframes=['M5', 'M15', 'H1', 'H4', 'D1'],
            update_interval=3,  # Faster updates for crypto
            default_indicators=['RSI', 'MACD']
        )
        
        engine = DashboardEngine(config.symbols, config.timeframes)
        engine.update_interval = config.update_interval
        engine.setup_default_indicators()
        
        return engine

# Integration with your existing DDE system
class DDEIntegration:
    """Integration layer with your existing DDE price feed"""
    
    def __init__(self, dashboard_engine: DashboardEngine, dde_client):
        self.engine = dashboard_engine
        self.dde_client = dde_client
    
    def setup_dde_callbacks(self):
        """Setup callbacks to update dashboard when DDE data arrives"""
        def on_price_update(symbol: str, price_data: Dict[str, Any]):
            # Convert DDE format to dashboard format
            formatted_data = {
                symbol: {
                    'M15': {  # You'd need to determine timeframe from DDE
                        'open': price_data.get('open'),
                        'high': price_data.get('high'),
                        'low': price_data.get('low'),
                        'close': price_data.get('bid'),  # or ask
                        'volume': price_data.get('volume', 0),
                        'timestamp': datetime.now()
                    }
                }
            }
            
            self.engine.update_signals(formatted_data)
        
        # Register callback with your DDE client
        # self.dde_client.register_callback(on_price_update)

# Example main execution
def main():
    """Example main function showing how to use the dashboard"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create dashboard
    dashboard = DashboardFactory.create_forex_dashboard()
    
    # Create API layer
    api = DashboardAPI(dashboard)
    
    # Start real-time updates
    dashboard.start_real_time_updates()
    
    try:
        # Keep running (in real app, this would be your web server)
        while True:
            # Get current dashboard state
            data = api.get_signals()
            print(f"Dashboard updated at {data['last_update']}")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("Shutting down...")
        dashboard.stop_real_time_updates()

if __name__ == "__main__":
    main()

# Plugin Example - Custom Indicator
# Save this as indicators/custom_macd.py to see plugin loading in action

"""
# Custom MACD with different parameters
class CustomMACDIndicator(BaseIndicator):
    def __init__(self, symbol: str, timeframe: str, fast: int = 10, slow: int = 21, signal: int = 7):
        super().__init__(symbol, timeframe, {'fast': fast, 'slow': slow, 'signal': signal})
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
        
    def calculate_signal(self, price_data: Dict[str, Any]) -> SignalData:
        # Your custom MACD logic here
        return SignalData(
            symbol=self.symbol,
            timeframe=self.timeframe,
            indicator="CustomMACD",
            signal=SignalStrength.NO_SIGNAL,
            confidence=0.0,
            timestamp=datetime.now()
        )
    
    def get_required_periods(self) -> int:
        return self.slow + self.signal_period
    
    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.TREND
"""