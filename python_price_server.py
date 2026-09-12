#!/usr/bin/env python3
"""
Python Price Server for MT4 Bridge
Receives real-time price data from MT4 via TCP socket
Cross-platform solution - works on Windows, Linux, macOS
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional, Callable
import threading
import queue
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MT4PriceServer:
    """TCP server to receive price data from MT4"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.clients = set()
        self.price_data = {}
        self.callbacks = []
        self.running = False
        self.message_queue = queue.Queue()
        
        # Statistics
        self.stats = {
            'total_messages': 0,
            'price_updates': 0,
            'connections': 0,
            'start_time': None,
            'last_update': None
        }
    
    async def start_server(self):
        """Start the TCP server"""
        try:
            self.server = await asyncio.start_server(
                self.handle_client, self.host, self.port
            )
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            logger.info(f"🚀 MT4 Price Server started on {self.host}:{self.port}")
            logger.info("📡 Waiting for MT4 connection...")
            
            # Start message processor
            asyncio.create_task(self.process_messages())
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            raise
    
    async def handle_client(self, reader, writer):
        """Handle incoming client connection"""
        client_addr = writer.get_extra_info('peername')
        logger.info(f"🔗 New connection from {client_addr}")
        
        self.clients.add(writer)
        self.stats['connections'] += 1
        
        try:
            while True:
                # Read data from client
                data = await reader.readline()
                if not data:
                    break
                
                try:
                    # Decode and parse JSON message
                    message = data.decode('utf-8').strip()
                    if message:
                        self.message_queue.put(message)
                        self.stats['total_messages'] += 1
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Invalid JSON received: {message[:100]}...")
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"❌ Client handler error: {e}")
        finally:
            # Cleanup
            self.clients.discard(writer)
            writer.close()
            await writer.wait_closed()
            logger.info(f"🔌 Connection closed: {client_addr}")
    
    async def process_messages(self):
        """Process incoming messages from queue"""
        while self.running:
            try:
                # Get message from queue (non-blocking)
                try:
                    message = self.message_queue.get_nowait()
                    await self.handle_message(message)
                except queue.Empty:
                    await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
                    
            except Exception as e:
                logger.error(f"❌ Message processing error: {e}")
                await asyncio.sleep(1)
    
    async def handle_message(self, message: str):
        """Handle individual message"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'init':
                await self.handle_init_message(data)
            elif msg_type == 'price_update':
                await self.handle_price_update(data)
            elif msg_type == 'disconnect':
                await self.handle_disconnect_message(data)
            else:
                logger.warning(f"⚠️ Unknown message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
    
    async def handle_init_message(self, data: Dict):
        """Handle initialization message from MT4"""
        ea_name = data.get('ea_name', 'Unknown')
        symbols = data.get('symbols', [])
        timestamp = data.get('timestamp')
        
        logger.info(f"📋 Initialized connection from EA: {ea_name}")
        logger.info(f"📊 Monitoring symbols: {', '.join(symbols)}")
        logger.info(f"⏰ MT4 timestamp: {timestamp}")
        
        # Initialize price data structure
        for symbol in symbols:
            self.price_data[symbol] = {
                'bid': 0.0,
                'ask': 0.0,
                'spread': 0.0,
                'digits': 5,
                'last_update': None,
                'tick_count': 0
            }
    
    async def handle_price_update(self, data: Dict):
        """Handle price update message"""
        timestamp = data.get('timestamp')
        price_data = data.get('data', [])
        
        self.stats['price_updates'] += 1
        self.stats['last_update'] = datetime.now()
        
        # Update price data
        updated_symbols = []
        for symbol_data in price_data:
            symbol = symbol_data.get('symbol')
            if symbol:
                self.price_data[symbol] = {
                    'bid': symbol_data.get('bid', 0.0),
                    'ask': symbol_data.get('ask', 0.0),
                    'spread': symbol_data.get('spread', 0.0),
                    'digits': symbol_data.get('digits', 5),
                    'last_update': timestamp,
                    'tick_count': self.price_data.get(symbol, {}).get('tick_count', 0) + 1
                }
                updated_symbols.append(symbol)
        
        # Call all registered callbacks
        for callback in self.callbacks:
            try:
                await callback(self.price_data, updated_symbols)
            except Exception as e:
                logger.error(f"❌ Callback error: {e}")
        
        # Log update (throttled)
        if self.stats['price_updates'] % 100 == 0:
            logger.info(f"📈 Processed {self.stats['price_updates']} price updates")
    
    async def handle_disconnect_message(self, data: Dict):
        """Handle disconnect message from MT4"""
        timestamp = data.get('timestamp')
        logger.info(f"🔌 MT4 disconnect message received at {timestamp}")
    
    def add_callback(self, callback: Callable):
        """Add callback for price updates"""
        self.callbacks.append(callback)
        logger.info(f"📞 Added price update callback: {callback.__name__}")
    
    def get_price_data(self, symbol: str = None) -> Dict:
        """Get current price data"""
        if symbol:
            return self.price_data.get(symbol, {})
        return self.price_data.copy()
    
    def get_statistics(self) -> Dict:
        """Get server statistics"""
        uptime = None
        if self.stats['start_time']:
            uptime = datetime.now() - self.stats['start_time']
        
        return {
            **self.stats,
            'uptime': str(uptime) if uptime else None,
            'active_connections': len(self.clients),
            'monitored_symbols': len(self.price_data),
            'avg_updates_per_sec': self.stats['price_updates'] / uptime.total_seconds() if uptime and uptime.total_seconds() > 0 else 0
        }
    
    async def stop_server(self):
        """Stop the server"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("🛑 Server stopped")


# Example callback functions
async def print_price_callback(price_data: Dict, updated_symbols: List[str]):
    """Print price updates to console"""
    for symbol in updated_symbols:
        data = price_data[symbol]
        print(f"{symbol}: {data['bid']:.5f}/{data['ask']:.5f} "
              f"(Spread: {data['spread']:.5f}) [{data['last_update']}]")

async def save_to_json_callback(price_data: Dict, updated_symbols: List[str]):
    """Save price data to JSON file"""
    try:
        with open('mt4_prices_live.json', 'w') as f:
            json.dump(price_data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"❌ Error saving to JSON: {e}")

async def send_to_huey_p_callback(price_data: Dict, updated_symbols: List[str]):
    """Send price data to HUEY_P trading system"""
    try:
        # Example: Send to HUEY_P signal service
        # This would integrate with your existing signal service
        
        for symbol in updated_symbols:
            data = price_data[symbol]
            
            # Create price message for HUEY_P system
            price_message = {
                'symbol': symbol,
                'bid': data['bid'],
                'ask': data['ask'],
                'spread': data['spread'],
                'timestamp': data['last_update'],
                'source': 'MT4_LIVE'
            }
            
            # Send to your trading system (implement as needed)
            # await send_to_signal_service(price_message)
            # await update_risk_calculator(price_message)
            # await notify_eas(price_message)
            
    except Exception as e:
        logger.error(f"❌ Error sending to HUEY_P: {e}")

async def volatility_callback(price_data: Dict, updated_symbols: List[str]):
    """Calculate and monitor volatility"""
    # Example: Calculate simple volatility metrics
    for symbol in updated_symbols:
        data = price_data[symbol]
        spread_pct = (data['spread'] / data['bid']) * 100 if data['bid'] > 0 else 0
        
        if spread_pct > 0.1:  # Alert on high spreads
            logger.warning(f"⚠️ High spread on {symbol}: {spread_pct:.3f}%")


# Main execution
async def main():
    """Main server execution"""
    # Create server instance
    server = MT4PriceServer(host='127.0.0.1', port=8765)
    
    # Add callbacks
    server.add_callback(print_price_callback)
    server.add_callback(save_to_json_callback)
    server.add_callback(send_to_huey_p_callback)
    server.add_callback(volatility_callback)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("🛑 Received shutdown signal")
        asyncio.create_task(server.stop_server())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start server
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
    finally:
        await server.stop_server()


# Statistics monitoring thread
def start_stats_monitor(server: MT4PriceServer):
    """Start statistics monitoring in separate thread"""
    def monitor_loop():
        while server.running:
            try:
                time.sleep(30)  # Update every 30 seconds
                stats = server.get_statistics()
                logger.info(f"📊 Stats: {stats['price_updates']} updates, "
                           f"{stats['active_connections']} connections, "
                           f"uptime: {stats['uptime']}")
            except Exception as e:
                logger.error(f"❌ Stats monitor error: {e}")
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()


if __name__ == "__main__":
    print("🚀 Starting MT4 Python Price Server...")
    print("📡 Make sure MT4 PythonPriceBridge EA is running")
    print("🔗 Server will listen on 127.0.0.1:8765")
    print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)
