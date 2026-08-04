"""
MT4 DDE Price Intelligence System
Real-time price data capture and analysis using MT4's native DDE feature
"""

import win32ui
import dde
import pandas as pd
import numpy as np
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import json
import sqlite3
import threading
import time

@dataclass
class PriceSnapshot:
    """Individual price data point"""
    timestamp: datetime
    symbol: str
    bid: float
    ask: float
    spread: float
    
@dataclass
class CurrencyStrength:
    """Currency strength metrics"""
    currency: str
    strength_1h: float
    strength_4h: float
    strength_8h: float
    strength_daily: float
    rsi_component: float
    ma_component: float
    momentum_component: float
    
@dataclass
class PriceLevel:
    """Support/Resistance level"""
    level: float
    touches: int
    last_touch: datetime
    strength: float
    level_type: str  # 'support' or 'resistance'

class MT4DDEClient:
    """
    Handles DDE connection to MT4 terminal
    """
    
    def __init__(self, server_name: str = "MT4"):
        self.server_name = server_name
        self.server = None
        self.conversation = None
        self.connected = False
        self.symbols = []
        
    def connect(self) -> bool:
        """Establish DDE connection to MT4"""
        try:
            self.server = dde.CreateServer()
            self.server.Create("PythonDDE")
            self.conversation = dde.CreateConversation(self.server)
            self.conversation.ConnectTo(self.server_name, "QUOTE")
            self.connected = True
            logging.info("DDE connection to MT4 established")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to MT4 DDE: {e}")
            return False
            
    def disconnect(self):
        """Close DDE connection"""
        if self.conversation:
            self.conversation.Disconnect()
        if self.server:
            self.server.Shutdown()
        self.connected = False
        
    def get_price(self, symbol: str) -> Optional[Tuple[float, float]]:
        """Get current bid/ask for symbol"""
        if not self.connected:
            return None
            
        try:
            # Request bid and ask prices
            bid_data = self.conversation.Request(f"{symbol}_BID")
            ask_data = self.conversation.Request(f"{symbol}_ASK")
            
            if bid_data and ask_data:
                bid = float(bid_data)
                ask = float(ask_data)
                return bid, ask
        except Exception as e:
            logging.error(f"Error getting price for {symbol}: {e}")
        return None
        
    def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        try:
            balance = self.conversation.Request("BALANCE")
            equity = self.conversation.Request("EQUITY")
            margin = self.conversation.Request("MARGIN")
            
            return {
                'balance': float(balance) if balance else 0,
                'equity': float(equity) if equity else 0,
                'margin': float(margin) if margin else 0
            }
        except Exception as e:
            logging.error(f"Error getting account info: {e}")
        return None

class PriceDataManager:
    """
    Manages price data collection and storage
    """
    
    def __init__(self, db_path: str = "price_data.db"):
        self.db_path = db_path
        self.price_buffers = {}  # Symbol -> deque of PriceSnapshot
        self.buffer_size = 10000  # Keep last 10k prices per symbol
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for price storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                bid REAL,
                ask REAL,
                spread REAL
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
            ON price_data(symbol, timestamp)
        ''')
        
        conn.commit()
        conn.close()
        
    def add_price(self, snapshot: PriceSnapshot):
        """Add new price snapshot"""
        symbol = snapshot.symbol
        
        # Add to memory buffer
        if symbol not in self.price_buffers:
            self.price_buffers[symbol] = deque(maxlen=self.buffer_size)
        self.price_buffers[symbol].append(snapshot)
        
        # Store to database (could be async for better performance)
        self._store_to_db(snapshot)
        
    def _store_to_db(self, snapshot: PriceSnapshot):
        """Store price snapshot to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO price_data (timestamp, symbol, bid, ask, spread)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            snapshot.timestamp.isoformat(),
            snapshot.symbol,
            snapshot.bid,
            snapshot.ask,
            snapshot.spread
        ))
        
        conn.commit()
        conn.close()
        
    def get_recent_prices(self, symbol: str, minutes: int = 60) -> pd.DataFrame:
        """Get recent prices for analysis"""
        if symbol not in self.price_buffers:
            return pd.DataFrame()
            
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_data = [
            {
                'timestamp': p.timestamp,
                'bid': p.bid,
                'ask': p.ask,
                'spread': p.spread,
                'mid': (p.bid + p.ask) / 2
            }
            for p in self.price_buffers[symbol]
            if p.timestamp >= cutoff_time
        ]
        
        return pd.DataFrame(recent_data)

class TechnicalIndicators:
    """
    Calculate technical indicators from price data
    """
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def moving_average(prices: pd.Series, period: int) -> pd.Series:
        """Calculate moving average"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def momentum(prices: pd.Series, period: int = 10) -> pd.Series:
        """Calculate momentum"""
        return prices / prices.shift(period) * 100
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

class CurrencyStrengthAnalyzer:
    """
    Analyzes multi-currency strength using price relationships
    """
    
    def __init__(self):
        self.currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD']
        self.pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
            'EURGBP', 'EURJPY', 'EURCHF', 'EURAUD', 'EURCAD', 'EURNZD',
            'GBPJPY', 'GBPCHF', 'GBPAUD', 'GBPCAD', 'GBPNZD',
            'AUDJPY', 'AUDCHF', 'AUDCAD', 'AUDNZD',
            'CADJPY', 'CADCHF', 'NZDJPY', 'NZDCHF', 'NZDCAD'
        ]
        
    def calculate_strength(self, price_manager: PriceDataManager, 
                          timeframe_minutes: int = 60) -> Dict[str, CurrencyStrength]:
        """Calculate currency strength for all currencies"""
        strengths = {}
        
        for currency in self.currencies:
            rsi_sum = 0
            ma_sum = 0
            momentum_sum = 0
            pair_count = 0
            
            for pair in self.pairs:
                if currency in pair:
                    df = price_manager.get_recent_prices(pair, timeframe_minutes)
                    if len(df) < 20:  # Need minimum data
                        continue
                        
                    prices = df['mid']
                    
                    # Calculate indicators
                    rsi = TechnicalIndicators.rsi(prices).iloc[-1]
                    ma_short = TechnicalIndicators.moving_average(prices, 10).iloc[-1]
                    ma_long = TechnicalIndicators.moving_average(prices, 20).iloc[-1]
                    momentum = TechnicalIndicators.momentum(prices).iloc[-1]
                    
                    # Determine if currency is base or quote
                    is_base = pair.startswith(currency)
                    
                    # Adjust indicators based on position
                    if is_base:
                        rsi_component = rsi
                        ma_component = 100 if ma_short > ma_long else 0
                        momentum_component = momentum
                    else:
                        rsi_component = 100 - rsi
                        ma_component = 0 if ma_short > ma_long else 100
                        momentum_component = 200 - momentum
                    
                    rsi_sum += rsi_component
                    ma_sum += ma_component
                    momentum_sum += momentum_component
                    pair_count += 1
            
            if pair_count > 0:
                # Calculate weighted strength (configurable weights)
                rsi_avg = rsi_sum / pair_count
                ma_avg = ma_sum / pair_count
                momentum_avg = momentum_sum / pair_count
                
                # Apply weights (from configuration)
                rsi_weight = 0.33
                ma_weight = 0.33
                momentum_weight = 0.34
                
                overall_strength = (
                    rsi_avg * rsi_weight +
                    ma_avg * ma_weight +
                    momentum_avg * momentum_weight
                ) / 10  # Scale to 0-10
                
                strengths[currency] = CurrencyStrength(
                    currency=currency,
                    strength_1h=overall_strength,  # Would calculate for different timeframes
                    strength_4h=overall_strength,
                    strength_8h=overall_strength,
                    strength_daily=overall_strength,
                    rsi_component=rsi_avg,
                    ma_component=ma_avg,
                    momentum_component=momentum_avg
                )
        
        return strengths

class PriceLevelDetector:
    """
    Detects support and resistance levels from price data
    """
    
    def __init__(self, sensitivity: float = 1.0, min_touches: int = 3):
        self.sensitivity = sensitivity
        self.min_touches = min_touches
        
    def detect_levels(self, price_data: pd.DataFrame, 
                     zone_width_pips: int = 5) -> List[PriceLevel]:
        """Detect support and resistance levels"""
        if len(price_data) < 50:
            return []
            
        levels = []
        prices = price_data['mid'].values
        timestamps = price_data['timestamp'].values
        
        # Find local highs and lows
        highs = self._find_local_extrema(prices, 'high')
        lows = self._find_local_extrema(prices, 'low')
        
        # Cluster similar price levels
        resistance_levels = self._cluster_levels(highs, prices, timestamps, zone_width_pips, 'resistance')
        support_levels = self._cluster_levels(lows, prices, timestamps, zone_width_pips, 'support')
        
        # Filter by minimum touches
        levels.extend([level for level in resistance_levels if level.touches >= self.min_touches])
        levels.extend([level for level in support_levels if level.touches >= self.min_touches])
        
        return levels
    
    def _find_local_extrema(self, prices: np.array, extrema_type: str) -> List[int]:
        """Find local highs or lows"""
        window = max(5, int(len(prices) * 0.02))  # Adaptive window
        extrema = []
        
        for i in range(window, len(prices) - window):
            window_prices = prices[i-window:i+window+1]
            center_price = prices[i]
            
            if extrema_type == 'high':
                if center_price == max(window_prices):
                    extrema.append(i)
            else:  # low
                if center_price == min(window_prices):
                    extrema.append(i)
                    
        return extrema
    
    def _cluster_levels(self, extrema_indices: List[int], prices: np.array, 
                       timestamps: np.array, zone_width_pips: int, 
                       level_type: str) -> List[PriceLevel]:
        """Cluster similar price levels"""
        if not extrema_indices:
            return []
            
        clustered_levels = []
        extrema_prices = [prices[i] for i in extrema_indices]
        
        # Simple clustering by zone width
        pip_value = 0.0001  # Assuming 4-digit pricing
        zone_width = zone_width_pips * pip_value
        
        processed = set()
        
        for i, price in enumerate(extrema_prices):
            if i in processed:
                continue
                
            cluster_prices = [price]
            cluster_times = [timestamps[extrema_indices[i]]]
            processed.add(i)
            
            # Find similar prices within zone
            for j, other_price in enumerate(extrema_prices):
                if j != i and j not in processed:
                    if abs(price - other_price) <= zone_width:
                        cluster_prices.append(other_price)
                        cluster_times.append(timestamps[extrema_indices[j]])
                        processed.add(j)
            
            # Create level if enough touches
            if len(cluster_prices) >= 2:
                avg_price = np.mean(cluster_prices)
                latest_touch = max(cluster_times)
                strength = len(cluster_prices) * self.sensitivity
                
                level = PriceLevel(
                    level=avg_price,
                    touches=len(cluster_prices),
                    last_touch=latest_touch,
                    strength=strength,
                    level_type=level_type
                )
                clustered_levels.append(level)
        
        return clustered_levels

class SignalGenerator:
    """
    Generates trading signals based on price intelligence
    """
    
    def __init__(self, strength_analyzer: CurrencyStrengthAnalyzer,
                 level_detector: PriceLevelDetector):
        self.strength_analyzer = strength_analyzer
        self.level_detector = level_detector
        
    def generate_signals(self, price_manager: PriceDataManager) -> List[Dict]:
        """Generate trading signals based on current analysis"""
        signals = []
        
        # Get currency strengths
        strengths = self.strength_analyzer.calculate_strength(price_manager)
        
        # Generate strength-based signals
        strong_currencies = [c for c, s in strengths.items() if s.strength_1h > 6.0]
        weak_currencies = [c for c, s in strengths.items() if s.strength_1h < 4.0]
        
        # Create signals for strong vs weak currency pairs
        for strong in strong_currencies:
            for weak in weak_currencies:
                # Check if valid pair exists
                pair1 = f"{strong}{weak}"
                pair2 = f"{weak}{strong}"
                
                if pair1 in self.strength_analyzer.pairs:
                    signal = {
                        'timestamp': datetime.now(),
                        'signal_type': 'STRENGTH_DIVERGENCE',
                        'symbol': pair1,
                        'action': 'BUY',
                        'confidence': min(strengths[strong].strength_1h, 10 - strengths[weak].strength_1h) / 10,
                        'source': 'CURRENCY_STRENGTH',
                        'details': {
                            'strong_currency': strong,
                            'weak_currency': weak,
                            'strong_value': strengths[strong].strength_1h,
                            'weak_value': strengths[weak].strength_1h
                        }
                    }
                    signals.append(signal)
                elif pair2 in self.strength_analyzer.pairs:
                    signal = {
                        'timestamp': datetime.now(),
                        'signal_type': 'STRENGTH_DIVERGENCE',
                        'symbol': pair2,
                        'action': 'SELL',
                        'confidence': min(strengths[strong].strength_1h, 10 - strengths[weak].strength_1h) / 10,
                        'source': 'CURRENCY_STRENGTH',
                        'details': {
                            'strong_currency': strong,
                            'weak_currency': weak,
                            'strong_value': strengths[strong].strength_1h,
                            'weak_value': strengths[weak].strength_1h
                        }
                    }
                    signals.append(signal)
        
        return signals

class MT4PriceIntelligenceSystem:
    """
    Main system coordinator
    """
    
    def __init__(self, symbols: List[str], update_interval: int = 15):
        self.symbols = symbols
        self.update_interval = update_interval
        self.running = False
        
        # Initialize components
        self.dde_client = MT4DDEClient()
        self.price_manager = PriceDataManager()
        self.strength_analyzer = CurrencyStrengthAnalyzer()
        self.level_detector = PriceLevelDetector()
        self.signal_generator = SignalGenerator(self.strength_analyzer, self.level_detector)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    async def start(self):
        """Start the price intelligence system"""
        if not self.dde_client.connect():
            logging.error("Failed to connect to MT4 DDE")
            return
            
        self.running = True
        logging.info("Price Intelligence System started")
        
        # Start concurrent tasks
        tasks = [
            self.price_collection_loop(),
            self.analysis_loop(),
            self.signal_generation_loop()
        ]
        
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Stop the system"""
        self.running = False
        self.dde_client.disconnect()
        logging.info("Price Intelligence System stopped")
    
    async def price_collection_loop(self):
        """Continuously collect price data"""
        while self.running:
            for symbol in self.symbols:
                price_data = self.dde_client.get_price(symbol)
                if price_data:
                    bid, ask = price_data
                    spread = ask - bid
                    
                    snapshot = PriceSnapshot(
                        timestamp=datetime.now(),
                        symbol=symbol,
                        bid=bid,
                        ask=ask,
                        spread=spread
                    )
                    
                    self.price_manager.add_price(snapshot)
            
            await asyncio.sleep(1)  # Collect every second
    
    async def analysis_loop(self):
        """Periodic analysis of currency strength and levels"""
        while self.running:
            try:
                # Calculate currency strengths
                strengths = self.strength_analyzer.calculate_strength(self.price_manager)
                
                # Detect price levels for each symbol
                for symbol in self.symbols:
                    df = self.price_manager.get_recent_prices(symbol, 240)  # 4 hours
                    if len(df) > 50:
                        levels = self.level_detector.detect_levels(df)
                        logging.info(f"{symbol}: Found {len(levels)} price levels")
                
                # Log currency strengths
                for currency, strength in strengths.items():
                    logging.info(f"{currency} strength: {strength.strength_1h:.2f}")
                    
            except Exception as e:
                logging.error(f"Error in analysis loop: {e}")
            
            await asyncio.sleep(self.update_interval)
    
    async def signal_generation_loop(self):
        """Generate and export trading signals"""
        while self.running:
            try:
                signals = self.signal_generator.generate_signals(self.price_manager)
                
                if signals:
                    logging.info(f"Generated {len(signals)} trading signals")
                    # Export signals to file for MT4 to read
                    self._export_signals(signals)
                
            except Exception as e:
                logging.error(f"Error in signal generation: {e}")
            
            await asyncio.sleep(self.update_interval)
    
    def _export_signals(self, signals: List[Dict]):
        """Export signals to CSV file for MT4 consumption"""
        df = pd.DataFrame(signals)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"signals_{timestamp}.csv"
        df.to_csv(filename, index=False)
        logging.info(f"Exported {len(signals)} signals to {filename}")

# Example usage and configuration
if __name__ == "__main__":
    # Define currency pairs to monitor
    SYMBOLS = [
        'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
        'EURGBP', 'EURJPY', 'EURCHF', 'GBPJPY', 'GBPCHF', 'AUDJPY'
    ]
    
    # Create and start the system
    system = MT4PriceIntelligenceSystem(symbols=SYMBOLS, update_interval=15)
    
    try:
        # Run the system
        asyncio.run(system.start())
    except KeyboardInterrupt:
        print("Shutting down system...")
        asyncio.run(system.stop())
