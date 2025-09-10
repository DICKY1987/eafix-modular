# Indicator Integration Guide

## Overview

Both indicators are now pure signaling systems that indicate when conditions are met without any execution logic. Your separate execution engine can monitor these indicators and decide when/how to trade.

## 1. Friday Volume Indicator

### Purpose
Indicates when the percentage move between 7:30→14:00 America/Chicago on Fridays exceeds a threshold.

### Integration in Python Engine

```python
# indicators_engine.py
from indicators.friday_vol_indicator import FridayVolIndicator, FridayVolIndicatorConfig

# Setup
friday_indicator = FridayVolIndicator(FridayVolIndicatorConfig(
    percent_threshold=1.0,  # 1% threshold
    start_local_hhmm="07:30",
    end_local_hhmm="14:00"
))

# In your main polling loop
def poll_indicators():
    for symbol in live_symbols():
        # Get full indicator state
        state = friday_indicator.get_indicator_state(
            symbol=symbol,
            get_price_at=lambda dt: nearest_price_at_utc(symbol, dt)
        )
        
        # Log state changes
        if state["signal_active"]:
            logger.info(f"[FridayVolIndicator] {symbol} ACTIVE - {state['values']['direction']} {state['values']['pct_change']}%")
            
        # Send indicator state to execution engine
        send_indicator_state(state)

        # Simple boolean check
        if friday_indicator.is_signal_active(symbol, get_price_at):
            # Signal is active - execution engine can decide what to do
            strength = friday_indicator.get_signal_strength(symbol, get_price_at)
            send_signal_alert(f"{symbol} Friday signal active, strength: {strength}%")
```

### Settings Configuration

```json
{
  "indicators": {
    "FridayMove": {
      "enabled": true,
      "percent_threshold": 1.0,
      "start_local": "07:30",
      "end_local": "14:00"
    }
  }
}
```

### GUI Integration

Add to your Indicators panel:
- **Name**: FridayMove
- **Status**: WAITING / MONITORING / TRIGGERED / EXPIRED
- **Symbol**: Current symbol
- **Values**: Direction, %Change, p_start, p_end
- **Last Triggered**: Date of last trigger

## 2. Expiry Indicator Service

### Purpose
Provides multiple indicators based on FX options expiry data:
- **Pin Reversion**: High pin scores near strikes
- **Gamma Wall Proximity**: Large strikes within proximity
- **Post-Expiry Breakout**: Price escape after expiry
- **Volatility Compression**: Low volatility indicating potential expansion

### Service Endpoints

```
GET /indicators?symbol=EURUSD          # Full indicator states
GET /indicators.csv?symbol=EURUSD      # CSV format for MT4
GET /indicators/summary?symbol=EURUSD  # Simplified active summary
GET /expiries?symbol=EURUSD           # Raw expiry data
```

### Integration in Python Engine

```python
import requests

# Poll expiry indicators
def poll_expiry_indicators():
    for symbol in live_symbols():
        try:
            # Get indicator summary
            response = requests.get(f"http://127.0.0.1:5001/indicators/summary?symbol={symbol}")
            data = response.json()
            
            if data["any_active"]:
                logger.info(f"[ExpiryIndicators] {symbol} - {data['active_count']} active, strength: {data['overall_strength']}")
                
                # Send to execution engine
                send_indicator_state({
                    "type": "expiry_indicators",
                    "symbol": symbol,
                    "active_indicators": data["active_indicators"],
                    "overall_strength": data["overall_strength"],
                    "market_phase": data["market_phase"]
                })
        except Exception as e:
            logger.warning(f"Failed to poll expiry indicators for {symbol}: {e}")
```

### MT4 Integration

```cpp
// ExpiryIndicators.mq4 - Read indicator states
void OnTimer()
{
   string url = "http://127.0.0.1:5001/indicators.csv?symbol=" + Symbol();
   string response;
   if(HttpGet(url, response))
   {
      // Parse CSV and update indicators on chart
      ParseIndicatorCSV(response);
   }
}

void ParseIndicatorCSV(const string csv)
{
   string lines[];
   int n = StringSplit(csv, '\n', lines);
   
   for(int i = 1; i < n; i++) // Skip header
   {
      string cols[];
      if(StringSplit(lines[i], ',', cols) >= 6)
      {
         string indicator_name = cols[3];
         bool active = (cols[4] == "true");
         double strength = StrToDouble(cols[5]);
         
         // Update chart indicators based on state
         UpdateIndicatorDisplay(indicator_name, active, strength);
      }
   }
}
```

## 3. Execution Engine Integration

Your execution engine can monitor both indicators and make trading decisions:

```python
class ExecutionEngine:
    def __init__(self):
        self.friday_indicator = FridayVolIndicator(config)
        self.indicator_states = {}
    
    def process_indicator_updates(self):
        # Check Friday indicator
        for symbol in self.symbols:
            friday_state = self.friday_indicator.get_indicator_state(symbol, self.get_price_at)
            
            # Check expiry indicators
            expiry_summary = self.get_expiry_indicators(symbol)
            
            # Make execution decisions based on combined indicator states
            if self.should_execute(friday_state, expiry_summary):
                self.execute_trade(symbol, self.calculate_trade_params(friday_state, expiry_summary))
    
    def should_execute(self, friday_state, expiry_summary):
        # Your execution logic here
        # Example: Execute if Friday signal is active AND expiry strength > 50
        return (friday_state.get("signal_active", False) and 
                expiry_summary.get("overall_strength", 0) > 50)
    
    def calculate_trade_params(self, friday_state, expiry_summary):
        # Calculate position size, direction, stops based on indicator signals
        direction = friday_state.get("values", {}).get("direction", "BUY")
        strength = friday_state.get("values", {}).get("pct_change", 0)
        
        return {
            "direction": direction,
            "size": self.calculate_position_size(strength),
            "stop_loss": self.calculate_stops(strength),
            "take_profit": self.calculate_targets(strength)
        }
```

## 4. Key Benefits of Indicator Approach

1. **Separation of Concerns**: Indicators only indicate, execution engine only executes
2. **Flexibility**: Can combine multiple indicators for execution decisions
3. **Testing**: Easy to test indicators independently of execution logic
4. **Observability**: Clear indicator states for monitoring and debugging
5. **Reusability**: Same indicators can drive different execution strategies

## 5. Monitoring and Logging

```python
# Log indicator states for analysis
def log_indicator_states():
    states = {
        "friday_vol": self.get_friday_states(),
        "expiry_indicators": self.get_expiry_states(),
        "execution_decisions": self.get_execution_log()
    }
    
    # Store for backtesting and analysis
    self.indicator_logger.info(json.dumps(states))
```

This approach gives you clean, testable indicators that your execution engine can use flexibly for trading decisions.