#!/usr/bin/env python3
"""
File-Based MT4 to Python Price Bridge
Simple solution using shared files for price data exchange
Works with any MT4 version, cross-platform
"""

import json
import time
import os
import csv
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FilePriceBridge:
    """File-based price data bridge from MT4"""
    
    def __init__(self, data_directory: str = "mt4_data"):
        self.data_dir = Path(data_directory)
        self.data_dir.mkdir(exist_ok=True)
        
        # File paths
        self.price_file = self.data_dir / "live_prices.csv"
        self.account_file = self.data_dir / "account_data.csv"
        self.status_file = self.data_dir / "status.json"
        
        # Data storage
        self.price_data = {}
        self.account_data = {}
        self.callbacks = []
        
        # Monitoring
        self.running = False
        self.last_file_mod = {}
        
        # Initialize files if they don't exist
        self.init_files()
    
    def init_files(self):
        """Initialize data files"""
        # Create price file with headers if it doesn't exist
        if not self.price_file.exists():
            with open(self.price_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'symbol', 'bid', 'ask', 'spread'])
        
        # Create account file with headers if it doesn't exist
        if not self.account_file.exists():
            with open(self.account_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'balance', 'equity', 'margin', 'free_margin', 'margin_level'])
        
        # Create status file
        status = {
            'mt4_connected': False,
            'last_update': None,
            'python_reader_active': True,
            'start_time': datetime.now().isoformat()
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def start_monitoring(self, check_interval: float = 0.1):
        """Start monitoring files for changes"""
        self.running = True
        
        # Update status
        self.update_status({'python_reader_active': True})
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitor_loop, args=(check_interval,))
        monitor_thread.daemon = True
        monitor_thread.start()
        
        logger.info(f"📂 Started file monitoring in {self.data_dir}")
        logger.info(f"🔄 Check interval: {check_interval}s")
    
    def _monitor_loop(self, check_interval: float):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check for file updates
                files_to_check = [
                    ('prices', self.price_file),
                    ('account', self.account_file)
                ]
                
                for file_type, file_path in files_to_check:
                    if file_path.exists():
                        mod_time = file_path.stat().st_mtime
                        last_mod = self.last_file_mod.get(file_type, 0)
                        
                        if mod_time > last_mod:
                            self.last_file_mod[file_type] = mod_time
                            
                            if file_type == 'prices':
                                self.process_price_file()
                            elif file_type == 'account':
                                self.process_account_file()
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"❌ Monitor loop error: {e}")
                time.sleep(1)
    
    def process_price_file(self):
        """Process updated price file"""
        try:
            # Read last few lines (most recent data)
            with open(self.price_file, 'r') as f:
                lines = f.readlines()
            
            # Process last 10 lines (skip header)
            recent_lines = lines[-10:] if len(lines) > 10 else lines[1:]
            
            updated_symbols = set()
            
            for line in recent_lines:
                try:
                    parts = line.strip().split(',')
                    if len(parts) >= 5:
                        timestamp, symbol, bid, ask, spread = parts[:5]
                        
                        self.price_data[symbol] = {
                            'bid': float(bid),
                            'ask': float(ask),
                            'spread': float(spread),
                            'timestamp': timestamp,
                            'last_update': datetime.now()
                        }
                        
                        updated_symbols.add(symbol)
                        
                except ValueError as e:
                    continue  # Skip malformed lines
            
            # Call callbacks if we have updates
            if updated_symbols:
                for callback in self.callbacks:
                    try:
                        callback(self.price_data, list(updated_symbols))
                    except Exception as e:
                        logger.error(f"❌ Callback error: {e}")
                
                # Update status
                self.update_status({
                    'last_update': datetime.now().isoformat(),
                    'mt4_connected': True
                })
        
        except Exception as e:
            logger.error(f"❌ Error processing price file: {e}")
    
    def process_account_file(self):
        """Process updated account file"""
        try:
            with open(self.account_file, 'r') as f:
                lines = f.readlines()
            
            # Get the last line (most recent data)
            if len(lines) > 1:
                last_line = lines[-1].strip()
                parts = last_line.split(',')
                
                if len(parts) >= 6:
                    timestamp, balance, equity, margin, free_margin, margin_level = parts[:6]
                    
                    self.account_data = {
                        'balance': float(balance),
                        'equity': float(equity),
                        'margin': float(margin),
                        'free_margin': float(free_margin),
                        'margin_level': float(margin_level),
                        'timestamp': timestamp,
                        'last_update': datetime.now()
                    }
        
        except Exception as e:
            logger.error(f"❌ Error processing account file: {e}")
    
    def update_status(self, updates: Dict):
        """Update status file"""
        try:
            # Read current status
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    status = json.load(f)
            else:
                status = {}
            
            # Update with new data
            status.update(updates)
            
            # Write back
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
        
        except Exception as e:
            logger.error(f"❌ Error updating status: {e}")
    
    def add_callback(self, callback: Callable):
        """Add callback for price updates"""
        self.callbacks.append(callback)
        logger.info(f"📞 Added callback: {callback.__name__}")
    
    def get_price_data(self, symbol: str = None) -> Dict:
        """Get current price data"""
        if symbol:
            return self.price_data.get(symbol, {})
        return self.price_data.copy()
    
    def get_account_data(self) -> Dict:
        """Get current account data"""
        return self.account_data.copy()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        self.update_status({'python_reader_active': False})
        logger.info("🛑 Stopped file monitoring")


# Example MQL4 code to write files (add to EA)
mql4_file_writer_code = '''
//+------------------------------------------------------------------+
//| Write price data to file for Python                              |
//+------------------------------------------------------------------+
void WritePriceDataToFile()
{
   string filename = "mt4_data\\live_prices.csv";
   
   // Open file for writing (append mode)
   int handle = FileOpen(filename, FILE_WRITE|FILE_CSV|FILE_READ);
   if(handle == INVALID_HANDLE)
   {
      Print("Failed to open price file: ", GetLastError());
      return;
   }
   
   // Go to end of file
   FileSeek(handle, 0, SEEK_END);
   
   // Write current prices for monitored symbols
   string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD"};
   
   for(int i = 0; i < ArraySize(symbols); i++)
   {
      string symbol = symbols[i];
      double bid = MarketInfo(symbol, MODE_BID);
      double ask = MarketInfo(symbol, MODE_ASK);
      double spread = ask - bid;
      
      if(bid > 0 && ask > 0)
      {
         string timestamp = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
         
         // Write CSV line: timestamp,symbol,bid,ask,spread
         FileWrite(handle, timestamp, symbol, 
                  DoubleToString(bid, 5), 
                  DoubleToString(ask, 5), 
                  DoubleToString(spread, 5));
      }
   }
   
   FileClose(handle);
}

//+------------------------------------------------------------------+
//| Write account data to file for Python                           |
//+------------------------------------------------------------------+
void WriteAccountDataToFile()
{
   string filename = "mt4_data\\account_data.csv";
   
   int handle = FileOpen(filename, FILE_WRITE|FILE_CSV);
   if(handle == INVALID_HANDLE)
   {
      Print("Failed to open account file: ", GetLastError());
      return;
   }
   
   // Write header if file is empty
   if(FileSize(handle) == 0)
   {
      FileWrite(handle, "timestamp", "balance", "equity", "margin", "free_margin", "margin_level");
   }
   
   // Go to end of file
   FileSeek(handle, 0, SEEK_END);
   
   string timestamp = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
   double margin_level = 0;
   if(AccountMargin() > 0)
      margin_level = AccountEquity() / AccountMargin() * 100;
   
   // Write account data
   FileWrite(handle, timestamp,
            DoubleToString(AccountBalance(), 2),
            DoubleToString(AccountEquity(), 2),
            DoubleToString(AccountMargin(), 2),
            DoubleToString(AccountFreeMargin(), 2),
            DoubleToString(margin_level, 2));
   
   FileClose(handle);
}

// Call these functions in OnTick():
// WritePriceDataToFile();
// WriteAccountDataToFile();
'''

# Example usage callbacks
def print_updates_callback(price_data: Dict, updated_symbols: List[str]):
    """Print price updates"""
    for symbol in updated_symbols:
        data = price_data[symbol]
        print(f"{symbol}: {data['bid']:.5f}/{data['ask']:.5f} [{data['timestamp']}]")

def save_to_database_callback(price_data: Dict, updated_symbols: List[str]):
    """Save to database (implement as needed)"""
    # Example: Save to SQLite, PostgreSQL, etc.
    pass

def send_to_trading_system_callback(price_data: Dict, updated_symbols: List[str]):
    """Send to HUEY_P trading system"""
    # Integration with your existing system
    pass


# Main execution
if __name__ == "__main__":
    # Create bridge
    bridge = FilePriceBridge("mt4_data")
    
    # Add callbacks
    bridge.add_callback(print_updates_callback)
    bridge.add_callback(save_to_database_callback)
    bridge.add_callback(send_to_trading_system_callback)
    
    print("📂 File-based MT4 Price Bridge")
    print(f"📁 Monitoring directory: {bridge.data_dir}")
    print("🔧 Add this MQL4 code to your EA:")
    print(mql4_file_writer_code)
    print("\n🚀 Starting monitoring...")
    
    try:
        # Start monitoring
        bridge.start_monitoring(check_interval=0.1)
        
        # Keep running
        while True:
            time.sleep(1)
            
            # Print status every 30 seconds
            if int(time.time()) % 30 == 0:
                price_count = len(bridge.get_price_data())
                account_data = bridge.get_account_data()
                print(f"📊 Status: {price_count} symbols, "
                      f"Account: {account_data.get('equity', 'N/A')}")
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping bridge...")
        bridge.stop_monitoring()
        print("✅ Bridge stopped")
