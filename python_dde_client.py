#!/usr/bin/env python3
"""
Python DDE Client for MT4 Price Data
Receives real-time price feeds directly from MT4 via DDE protocol
Windows only - requires pywin32 library
"""

import win32ui
import win32con
import win32api
import dde
import time
import threading
import json
from datetime import datetime
from typing import Dict, Optional, Callable

class MT4_DDE_Client:
    """Python DDE client for MT4 price data"""
    
    def __init__(self, server_name: str = "MT4"):
        self.server_name = server_name
        self.dde_server = None
        self.conversations = {}
        self.price_data = {}
        self.callbacks = []
        self.running = False
        
    def connect(self) -> bool:
        """Connect to MT4 DDE server"""
        try:
            # Create DDE server instance
            self.dde_server = dde.CreateServer()
            self.dde_server.Create("PythonDDEClient")
            
            print(f"✅ Connected to DDE server: {self.server_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to DDE server: {e}")
            return False
    
    def subscribe_to_symbol(self, symbol: str) -> bool:
        """Subscribe to bid, ask, and time data for a symbol"""
        try:
            # Create conversations for each data type
            topics = ['BID', 'ASK', 'TIME']
            
            for topic in topics:
                conv = dde.CreateConversation(self.dde_server)
                conv.ConnectTo(self.server_name, topic)
                
                # Set up advise loop for real-time updates
                conv.StartAdviseLoop(symbol)
                
                # Store conversation
                conv_key = f"{symbol}_{topic}"
                self.conversations[conv_key] = conv
                
                print(f"📡 Subscribed to {symbol} {topic}")
            
            # Initialize price data structure
            self.price_data[symbol] = {
                'bid': 0.0,
                'ask': 0.0,
                'spread': 0.0,
                'timestamp': None,
                'last_update': None
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to subscribe to {symbol}: {e}")
            return False
    
    def get_price_data(self, symbol: str) -> Optional[Dict]:
        """Get latest price data for symbol"""
        try:
            if symbol not in self.conversations:
                return None
                
            # Get bid price
            bid_conv = self.conversations[f"{symbol}_BID"]
            bid_data = bid_conv.Request(symbol)
            bid_price = float(bid_data) if bid_data and bid_data != "N/A" else 0.0
            
            # Get ask price  
            ask_conv = self.conversations[f"{symbol}_ASK"]
            ask_data = ask_conv.Request(symbol)
            ask_price = float(ask_data) if ask_data and ask_data != "N/A" else 0.0
            
            # Get timestamp
            time_conv = self.conversations[f"{symbol}_TIME"]
            time_data = time_conv.Request(symbol)
            
            # Update price data
            self.price_data[symbol].update({
                'bid': bid_price,
                'ask': ask_price,
                'spread': ask_price - bid_price if ask_price > 0 and bid_price > 0 else 0.0,
                'timestamp': time_data,
                'last_update': datetime.now()
            })
            
            return self.price_data[symbol].copy()
            
        except Exception as e:
            print(f"❌ Error getting price data for {symbol}: {e}")
            return None
    
    def add_price_callback(self, callback: Callable):
        """Add callback function for price updates"""
        self.callbacks.append(callback)
    
    def start_monitoring(self, symbols: list, update_interval: float = 0.1):
        """Start monitoring prices for multiple symbols"""
        self.running = True
        
        # Subscribe to all symbols
        for symbol in symbols:
            self.subscribe_to_symbol(symbol)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(symbols, update_interval)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        print(f"🔄 Started monitoring {len(symbols)} symbols")
    
    def _monitor_loop(self, symbols: list, update_interval: float):
        """Main monitoring loop"""
        while self.running:
            try:
                updated_data = {}
                
                for symbol in symbols:
                    price_data = self.get_price_data(symbol)
                    if price_data:
                        updated_data[symbol] = price_data
                
                # Call all registered callbacks
                for callback in self.callbacks:
                    try:
                        callback(updated_data)
                    except Exception as e:
                        print(f"❌ Callback error: {e}")
                
                time.sleep(update_interval)
                
            except Exception as e:
                print(f"❌ Monitor loop error: {e}")
                time.sleep(1)
    
    def stop_monitoring(self):
        """Stop monitoring and cleanup"""
        self.running = False
        
        # Close all conversations
        for conv in self.conversations.values():
            try:
                conv.Disconnect()
            except:
                pass
        
        # Cleanup DDE server
        if self.dde_server:
            try:
                self.dde_server.Shutdown()
            except:
                pass
        
        print("🛑 Stopped DDE monitoring")
    
    def get_all_prices(self) -> Dict:
        """Get all current price data"""
        return self.price_data.copy()


# Example usage and callback functions
def price_update_callback(price_data: Dict):
    """Example callback for price updates"""
    for symbol, data in price_data.items():
        if data['bid'] > 0:
            print(f"{symbol}: Bid={data['bid']:.5f} Ask={data['ask']:.5f} "
                  f"Spread={data['spread']:.5f} [{data['last_update']}]")

def save_to_json_callback(price_data: Dict):
    """Save price data to JSON file"""
    try:
        with open('mt4_prices.json', 'w') as f:
            json.dump(price_data, f, indent=2, default=str)
    except Exception as e:
        print(f"❌ Error saving to JSON: {e}")

def send_to_trading_system_callback(price_data: Dict):
    """Send price data to trading system via socket/API"""
    # Example: Send to HUEY_P signal service
    try:
        # Implementation would depend on your trading system architecture
        # Could be TCP socket, HTTP API, message queue, etc.
        pass
    except Exception as e:
        print(f"❌ Error sending to trading system: {e}")


# Main execution example
if __name__ == "__main__":
    # Create DDE client
    client = MT4_DDE_Client()
    
    # Connect to MT4
    if not client.connect():
        print("❌ Failed to connect to MT4 DDE server")
        exit(1)
    
    # Define symbols to monitor
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
    
    # Add callbacks
    client.add_price_callback(price_update_callback)
    client.add_price_callback(save_to_json_callback)
    client.add_price_callback(send_to_trading_system_callback)
    
    try:
        # Start monitoring
        client.start_monitoring(symbols, update_interval=0.1)
        
        print("📊 DDE price monitoring started. Press Ctrl+C to stop...")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping DDE client...")
        client.stop_monitoring()
        print("✅ DDE client stopped")

# Requirements:
# pip install pywin32
# pip install pyDDE (alternative: pip install dde)
