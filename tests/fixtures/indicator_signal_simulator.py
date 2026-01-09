#!/usr/bin/env python3
# DOC_ID: DOC-SERVICE-0117
"""
Manual Indicator Signal Simulator
Simulates technical indicator triggers to test the complete signal flow
"""

import json
import csv
import hashlib
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum


class IndicatorType(Enum):
    """Supported indicator types for simulation"""
    MOVING_AVERAGE = "MA_CROSS"
    RSI = "RSI_EXTREME" 
    BOLLINGER = "BB_SQUEEZE"
    MACD = "MACD_SIGNAL"
    STOCHASTIC = "STOCH_SIGNAL"
    VOLUME = "VOLUME_SPIKE"
    VOLATILITY = "VOL_BREAKOUT"
    CUSTOM = "CUSTOM_SIGNAL"


class SignalDirection(Enum):
    """Signal directions"""
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class ConfidenceLevel(Enum):
    """Confidence levels"""
    LOW = "LOW"
    MED = "MED" 
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class IndicatorSignalSimulator:
    """Simulates technical indicator signals for testing"""
    
    def __init__(self, csv_dir: str = None):
        self.csv_dir = Path(csv_dir) if csv_dir else Path.cwd() / "test_data"
        self.csv_dir.mkdir(exist_ok=True)
        self.file_seq = 1
        
    def generate_hybrid_id(self, signal_type: str, generation: str = "O",
                          duration: str = "FL", outcome: str = "O1", 
                          proximity: str = "IM", symbol: str = "EURUSD") -> str:
        """Generate Hybrid ID for indicator signals"""
        # For indicator signals, use 00000000 as CAL8 placeholder
        cal8_placeholder = "00000000"
        return f"{cal8_placeholder}-{generation}-{signal_type}-{duration}-{outcome}-{proximity}-{symbol}"
    
    def create_indicator_signal(self, signal_config: Dict) -> Dict:
        """Create a single indicator signal"""
        now = datetime.utcnow()
        
        # Generate hybrid ID
        hybrid_id = self.generate_hybrid_id(
            signal_type=signal_config.get('signal_type', 'ALL_INDICATORS'),
            generation=signal_config.get('generation', 'O'),
            duration=signal_config.get('duration', 'FL'),
            outcome=signal_config.get('outcome', 'O1'),
            proximity=signal_config.get('proximity', 'IM'),
            symbol=signal_config.get('symbol', 'EURUSD')
        )
        
        signal = {
            'id': f"ind_{self.file_seq}_{int(time.time())}",
            'ts': now.isoformat() + 'Z',
            'source': signal_config.get('source', 'manual_test'),
            'symbol': signal_config.get('symbol', 'EURUSD'),
            'kind': signal_config.get('kind', 'breakout'),
            'direction': signal_config.get('direction', SignalDirection.LONG.value),
            'strength': signal_config.get('strength', 75),  # 0-100
            'confidence': signal_config.get('confidence', ConfidenceLevel.HIGH.value),
            'ttl': signal_config.get('ttl', 300),  # 5 minutes
            'tags': signal_config.get('tags', ['test', 'manual']),
            'hybrid_id': hybrid_id,
            'trigger': signal_config.get('trigger', 'Manual test trigger'),
            'target': signal_config.get('target', 'Price breakout above resistance'),
            'p': signal_config.get('probability', 0.75),  # 0-1
            'n': signal_config.get('sample_size', 100),
            'horizon': signal_config.get('horizon', '4H'),
            'file_seq': self.file_seq,
            'created_at_utc': now.isoformat() + 'Z'
        }
        
        # Add checksum
        signal_str = json.dumps(signal, sort_keys=True)
        signal['checksum_sha256'] = hashlib.sha256(signal_str.encode()).hexdigest()
        
        return signal
    
    def write_indicator_signals(self, signals: List[Dict], filename: str = "indicator_signals.csv") -> str:
        """Write signals to CSV with atomic write"""
        temp_file = self.csv_dir / f"{filename}.tmp"
        final_file = self.csv_dir / filename
        
        # Headers for indicator signals
        headers = [
            'id', 'ts', 'source', 'symbol', 'kind', 'direction', 'strength', 
            'confidence', 'ttl', 'tags', 'hybrid_id', 'trigger', 'target', 
            'p', 'n', 'horizon', 'file_seq', 'created_at_utc', 'checksum_sha256'
        ]
        
        with open(temp_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for signal in signals:
                # Convert tags list to string for CSV
                signal_copy = signal.copy()
                signal_copy['tags'] = ','.join(signal['tags'])
                writer.writerow(signal_copy)
        
        # Atomic rename
        temp_file.rename(final_file)
        self.file_seq += 1
        
        return str(final_file)
    
    def simulate_ma_crossover(self, symbol: str = "EURUSD", direction: str = "LONG") -> str:
        """Simulate moving average crossover signal"""
        signal_config = {
            'symbol': symbol,
            'signal_type': 'MA_CROSS_SIGNAL',
            'kind': 'trend_following',
            'direction': direction,
            'strength': 85,
            'confidence': ConfidenceLevel.HIGH.value,
            'source': 'ma_crossover_indicator',
            'trigger': f"50-period MA crossed above 200-period MA for {symbol}",
            'target': f"Price move of 50+ pips in {direction} direction",
            'probability': 0.68,
            'sample_size': 150,
            'horizon': '4H',
            'tags': ['ma_cross', 'trend', 'test']
        }
        
        signal = self.create_indicator_signal(signal_config)
        return self.write_indicator_signals([signal], "ma_crossover_signals.csv")
    
    def simulate_rsi_extreme(self, symbol: str = "EURUSD", oversold: bool = True) -> str:
        """Simulate RSI extreme (oversold/overbought) signal"""
        direction = SignalDirection.LONG.value if oversold else SignalDirection.SHORT.value
        condition = "oversold" if oversold else "overbought"
        rsi_value = 25 if oversold else 75
        
        signal_config = {
            'symbol': symbol,
            'signal_type': 'RSI_EXTREME_SIGNAL',
            'kind': 'mean_reversion',
            'direction': direction,
            'strength': 90,
            'confidence': ConfidenceLevel.VERY_HIGH.value,
            'source': 'rsi_indicator',
            'trigger': f"RSI({rsi_value}) {condition} condition for {symbol}",
            'target': f"Mean reversion bounce of 30+ pips",
            'probability': 0.72,
            'sample_size': 200,
            'horizon': '2H',
            'tags': ['rsi', 'mean_reversion', 'test']
        }
        
        signal = self.create_indicator_signal(signal_config)
        return self.write_indicator_signals([signal], "rsi_extreme_signals.csv")
    
    def simulate_bollinger_squeeze(self, symbol: str = "EURUSD") -> str:
        """Simulate Bollinger Band squeeze breakout"""
        signal_config = {
            'symbol': symbol,
            'signal_type': 'BB_SQUEEZE_SIGNAL',
            'kind': 'volatility_breakout',
            'direction': SignalDirection.LONG.value,  # Direction determined by breakout
            'strength': 80,
            'confidence': ConfidenceLevel.HIGH.value,
            'source': 'bollinger_indicator',
            'trigger': f"Bollinger Bands squeeze breakout for {symbol}",
            'target': f"Volatility expansion with 40+ pip move",
            'probability': 0.65,
            'sample_size': 120,
            'horizon': '6H',
            'tags': ['bollinger', 'volatility', 'breakout', 'test']
        }
        
        signal = self.create_indicator_signal(signal_config)
        return self.write_indicator_signals([signal], "bollinger_squeeze_signals.csv")
    
    def simulate_volume_spike(self, symbol: str = "EURUSD") -> str:
        """Simulate volume spike confirmation signal"""
        signal_config = {
            'symbol': symbol,
            'signal_type': 'VOLUME_SPIKE_SIGNAL',
            'kind': 'volume_confirmation',
            'direction': SignalDirection.LONG.value,
            'strength': 70,
            'confidence': ConfidenceLevel.MED.value,
            'source': 'volume_indicator',
            'trigger': f"Volume spike 3x average for {symbol}",
            'target': f"Sustained move with volume confirmation",
            'probability': 0.58,
            'sample_size': 80,
            'horizon': '1H',
            'tags': ['volume', 'confirmation', 'test']
        }
        
        signal = self.create_indicator_signal(signal_config)
        return self.write_indicator_signals([signal], "volume_spike_signals.csv")
    
    def simulate_multi_indicator_confluence(self, symbol: str = "EURUSD") -> str:
        """Simulate multiple indicators agreeing (confluence)"""
        signals = []
        
        # RSI oversold
        rsi_signal = self.create_indicator_signal({
            'symbol': symbol,
            'signal_type': 'RSI_SIGNAL',
            'kind': 'mean_reversion',
            'direction': SignalDirection.LONG.value,
            'strength': 85,
            'confidence': ConfidenceLevel.HIGH.value,
            'source': 'rsi_indicator',
            'tags': ['confluence', 'rsi', 'test']
        })
        signals.append(rsi_signal)
        
        # MACD bullish divergence
        macd_signal = self.create_indicator_signal({
            'symbol': symbol,
            'signal_type': 'MACD_SIGNAL',
            'kind': 'momentum',
            'direction': SignalDirection.LONG.value,
            'strength': 75,
            'confidence': ConfidenceLevel.HIGH.value,
            'source': 'macd_indicator',
            'tags': ['confluence', 'macd', 'test']
        })
        signals.append(macd_signal)
        
        # Support level bounce
        support_signal = self.create_indicator_signal({
            'symbol': symbol,
            'signal_type': 'SUPPORT_BOUNCE_SIGNAL',
            'kind': 'support_resistance',
            'direction': SignalDirection.LONG.value,
            'strength': 80,
            'confidence': ConfidenceLevel.HIGH.value,
            'source': 'support_resistance_indicator',
            'tags': ['confluence', 'support', 'test']
        })
        signals.append(support_signal)
        
        return self.write_indicator_signals(signals, "confluence_signals.csv")
    
    def create_test_battery(self) -> List[str]:
        """Create a comprehensive battery of test signals"""
        created_files = []
        
        print("Creating comprehensive indicator signal test battery...\n")
        
        # Test different symbols
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        
        for symbol in symbols:
            # MA Crossover
            file1 = self.simulate_ma_crossover(symbol, SignalDirection.LONG.value)
            created_files.append(file1)
            print(f"✓ MA Crossover signal for {symbol}: {file1}")
            
            # RSI Extreme
            file2 = self.simulate_rsi_extreme(symbol, oversold=True)
            created_files.append(file2)
            print(f"✓ RSI Oversold signal for {symbol}: {file2}")
            
            # Volume spike
            file3 = self.simulate_volume_spike(symbol)
            created_files.append(file3)
            print(f"✓ Volume Spike signal for {symbol}: {file3}")
        
        # Bollinger squeeze for EURUSD
        file4 = self.simulate_bollinger_squeeze('EURUSD')
        created_files.append(file4)
        print(f"✓ Bollinger Squeeze signal: {file4}")
        
        # Multi-indicator confluence
        file5 = self.simulate_multi_indicator_confluence('EURUSD')
        created_files.append(file5)
        print(f"✓ Multi-indicator confluence signals: {file5}")
        
        return created_files


def main():
    """Demo script for indicator signal simulation"""
    simulator = IndicatorSignalSimulator()
    
    print("=== Indicator Signal Simulator ===\n")
    
    # Create test battery
    created_files = simulator.create_test_battery()
    
    print(f"\n=== Created {len(created_files)} Signal Files ===")
    print("\nNext steps:")
    print("1. Copy these CSV files to your system's input directory")
    print("2. Monitor the Signals Tab for new indicator signals")
    print("3. Check signal processing in the system logs")
    print("4. Verify signals flow through to reentry_decisions.csv")
    print("5. Confirm MT4 receives and processes the signals")
    print("\nFiles can be found in:", simulator.csv_dir)


if __name__ == "__main__":
    main()
