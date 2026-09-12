Okay, let's proceed with **Part 3: Python Server Files**.

This part will create the Python server components that will act as the signal generation and distribution hub, communicating with your MQL4 EA via the DLL bridge. It also includes configuration managers, logging setup, and a requirements.txt file for managing Python dependencies.

Please copy and paste the following into your PowerShell terminal.

PowerShell

$ErrorActionPreference \= "Stop"  
Write-Host "CREATING PYTHON SERVER FILES..." \-ForegroundColor Green

\# Define project base path for Python source  
$projectPath \= "C:\\Users\\Richard Wilks\\TradingSystem"  
$pythonSourcePath \= Join-Path $projectPath "Python\\src"  
$pythonServicesPath \= Join-Path $pythonSourcePath "services"  
$pythonUtilsPath \= Join-Path $pythonSourcePath "utils"  
$pythonConfigPath \= Join-Path $projectPath "Config"  
$pythonScriptsPath \= Join-Path $projectPath "Scripts" \# For launch script  
$logPath \= Join-Path $projectPath "Logs"  
$databasePath \= Join-Path $projectPath "Database"

\# Create directory structure  
$pythonDirectories \= @(  
    $pythonSourcePath,  
    $pythonServicesPath,  
    $pythonUtilsPath,  
    $pythonConfigPath,  
    $pythonScriptsPath,  
    $logPath,  
    $databasePath  
)

foreach ($dir in $pythonDirectories) {  
    New-Item \-ItemType Directory \-Path $dir \-Force | Out-Null  
    Write-Host "📁 Created: $dir" \-ForegroundColor Cyan  
}

Write-Host "NOTE: You will need Python 3.8+ installed." \-ForegroundColor Yellow  
Write-Host "After creating files, install dependencies using 'pip install \-r requirements.txt'." \-ForegroundColor Yellow

\# \--- File Contents \---

\# trading\_server.py \- Main Python server  
$tradingServerContent \= @'  
import asyncio \# For async programming  
import websockets \# For potential future WebSocket (or use direct socket)  
import socket \# For TCP sockets  
import json \# For message serialization  
import logging  
from datetime import datetime  
import threading \# For multi-threaded server architecture  
import time  
import os  
import sys

\# Ensure custom modules are in sys.path  
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(\_\_file\_\_), 'utils')))  
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(\_\_file\_\_), 'services')))

from config\_manager import ConfigurationManager \# For configuration management  
from logger\_setup import setup\_logging \# For centralized logging  
\# from signal\_generator import SignalGeneratorService \# Placeholder, assuming it's a separate service  
\# from message\_broker import MessageBroker \# Placeholder, assuming it's a separate service  
\# from database\_manager import DatabaseManager \# Placeholder, assuming it's a separate service  
\# from monitoring import HealthMonitor \# Placeholder

\# \--- Global Configuration and Logger \---  
CONFIG\_PATH \= os.path.abspath(os.path.join(os.path.dirname(\_\_file\_\_), '..', '..', 'Config'))  
config\_manager \= ConfigurationManager(CONFIG\_PATH)  
server\_config \= config\_manager.load\_configuration('server\_config')  
logging\_config \= config\_manager.load\_configuration('logging\_config')  
system\_config \= config\_manager.load\_configuration('system\_config')

setup\_logging(logging\_config)  
logger \= logging.getLogger(\_\_name\_\_)

\# \--- Global Connection Pool and State \---  
\# { "EURUSD": socket\_object, "GBPUSD": socket\_object, ... }  
ea\_connections \= {}  
\# { "EURUSD": {"last\_heartbeat": datetime\_obj, "status": "CONNECTED", ...}, ... }  
ea\_status \= {}  
ea\_lock \= threading.Lock() \# Lock for accessing ea\_connections and ea\_status

\# \--- Constants \---  
SERVER\_HOST \= server\_config.get('server', {}).get('host', '127.0.0.1')  
SERVER\_PORT \= server\_config.get('server', {}).get('port', 8888\)  
HEARTBEAT\_INTERVAL \= system\_config.get('trading', {}).get('heartbeat\_interval\_seconds', 5\) \# Default 5s  
MAX\_MESSAGE\_SIZE \= 4096 \# Max bytes to receive in one go

class TradingServer:  
    def \_\_init\_\_(self, host, port):  
        self.host \= host  
        self.port \= port  
        self.server\_socket \= None  
        self.running \= False  
        self.signal\_generation\_thread \= None  
        logger.info(f"TradingServer initialized on {self.host}:{self.port}")

    async def start\_async\_server(self):  
        """Starts the asynchronous TCP server for MQL4 EA connections."""  
        self.server\_socket \= socket.socket(socket.AF\_INET, socket.SOCK\_STREAM)  
        self.server\_socket.setsockopt(socket.SOL\_SOCKET, socket.SO\_REUSEADDR, 1\) \# Allow quick restart  
        self.server\_socket.bind((self.host, self.port))  
        self.server\_socket.listen(server\_config.get('server', {}).get('max\_connections', 30)) \# Up to 30 EAs  
        self.server\_socket.setblocking(False) \# Non-blocking accept

        logger.info(f"Python TCP Server listening on {self.host}:{self.port}...")  
        self.running \= True

        loop \= asyncio.get\_event\_loop()

        while self.running:  
            try:  
                conn, addr \= await loop.sock\_accept(self.server\_socket)  
                logger.info(f"Accepted connection from {addr}")  
                \# Start a new task to handle the client connection  
                loop.create\_task(self.handle\_ea\_connection(conn, addr))  
            except Exception as e:  
                \# Handle cases where no new connections are pending or server is shutting down  
                if self.running: \# Only log if server is still supposed to be running  
                    logger.warning(f"Error accepting connection: {e}")  
                await asyncio.sleep(0.1) \# Small delay to prevent busy-waiting

    def stop\_server(self):  
        """Stops the TCP server and closes all connections."""  
        logger.info("Stopping TradingServer...")  
        self.running \= False  
        if self.server\_socket:  
            self.server\_socket.close()  
            logger.info("Server socket closed.")

        with ea\_lock:  
            for pair, conn in ea\_connections.items():  
                try:  
                    conn.shutdown(socket.SHUT\_RDWR)  
                    conn.close()  
                    logger.info(f"Closed connection for {pair}")  
                except Exception as e:  
                    logger.error(f"Error closing connection for {pair}: {e}")  
            ea\_connections.clear()  
            ea\_status.clear()  
          
        logger.info("TradingServer stopped.")

    async def handle\_ea\_connection(self, conn, addr):  
        """Handles a single EA connection, including registration and message exchange."""  
        ea\_id \= None  
        trading\_pair \= None  
        try:  
            \# First message should be registration  
            registration\_data \= await self.recv\_message\_async(conn)  
            if not registration\_data:  
                logger.warning(f"Connection from {addr} closed before registration.")  
                return

            try:  
                msg \= json.loads(registration\_data)  
                if msg.get('type') \== 'REGISTER': \#  
                    ea\_id \= msg.get('ea\_id')  
                    trading\_pair \= msg.get('trading\_pair')  
                    magic\_number \= msg.get('magic\_number')  
                    logger.info(f"Registered EA: {ea\_id} for {trading\_pair} (Magic: {magic\_number})")

                    with ea\_lock:  
                        if trading\_pair:  
                            \# Close previous connection for this pair if it exists  
                            if trading\_pair in ea\_connections and ea\_connections\[trading\_pair\] \!= conn:  
                                logger.warning(f"Closing old connection for {trading\_pair} before accepting new one.")  
                                try:  
                                    ea\_connections\[trading\_pair\].shutdown(socket.SHUT\_RDWR)  
                                    ea\_connections\[trading\_pair\].close()  
                                except Exception as e:  
                                    logger.error(f"Error closing old connection for {trading\_pair}: {e}")  
                              
                            ea\_connections\[trading\_pair\] \= conn  
                            ea\_status\[trading\_pair\] \= {  
                                "status": "CONNECTED",  
                                "last\_heartbeat": datetime.now(),  
                                "ea\_id": ea\_id,  
                                "magic\_number": magic\_number,  
                                "address": addr  
                            }  
                            logger.info(f"Active EA connections: {len(ea\_connections)}")  
                        else:  
                            logger.error(f"Registration message missing trading\_pair: {msg}")  
                            conn.close()  
                            return  
                else:  
                    logger.warning(f"First message from {addr} was not REGISTER: {msg}")  
                    conn.close()  
                    return

            except json.JSONDecodeError:  
                logger.error(f"Received non-JSON registration from {addr}: {registration\_data}")  
                conn.close()  
                return

            \# Main loop for receiving data from EA (responses or heartbeats)  
            while self.running:  
                try:  
                    data \= await self.recv\_message\_async(conn)  
                    if not data: \# Connection closed or error  
                        logger.warning(f"EA {ea\_id} ({trading\_pair}) disconnected.")  
                        break

                    \# Process incoming message (e.g., EA response, heartbeat)  
                    self.process\_ea\_message(ea\_id, trading\_pair, data)

                except Exception as e:  
                    logger.error(f"Error handling EA {ea\_id} ({trading\_pair}): {e}")  
                    break \# Exit loop on error  
        finally:  
            \# Clean up connection  
            if trading\_pair:  
                with ea\_lock:  
                    if trading\_pair in ea\_connections and ea\_connections\[trading\_pair\] \== conn:  
                        del ea\_connections\[trading\_pair\]  
                        if trading\_pair in ea\_status:  
                            ea\_status\[trading\_pair\]\["status"\] \= "DISCONNECTED"  
                            logger.info(f"EA {ea\_id} ({trading\_pair}) removed from active connections. Active: {len(ea\_connections)}")  
            conn.close()

    async def recv\_message\_async(self, conn):  
        """Receives a length-prefixed message asynchronously."""  
        try:  
            \# Read 4-byte length prefix  
            len\_bytes \= b''  
            while len(len\_bytes) \< 4:  
                chunk \= await asyncio.get\_event\_loop().sock\_recv(conn, 4 \- len(len\_bytes))  
                if not chunk: raise ConnectionError("Socket connection broken during length read.")  
                len\_bytes \+= chunk  
              
            \# Convert bytes to integer length  
            \# Assumes little-endian as implemented in C++ DLL (len\_bytes\[0\] is LSB)  
            expected\_len \= int.from\_bytes(len\_bytes, byteorder='little')

            if expected\_len \<= 0 or expected\_len \> MAX\_MESSAGE\_SIZE:  
                logger.error(f"Received invalid or oversized message length: {expected\_len}. Discarding connection.")  
                return None \# Signal to close connection

            \# Receive the actual message data  
            data\_bytes \= b''  
            while len(data\_bytes) \< expected\_len:  
                chunk \= await asyncio.get\_event\_loop().sock\_recv(conn, expected\_len \- len(data\_bytes))  
                if not chunk: raise ConnectionError("Socket connection broken during data read.")  
                data\_bytes \+= chunk  
              
            return data\_bytes.decode('utf-8') \# Decode as UTF-8

        except (ConnectionError, asyncio.CancelledError) as e:  
            logger.warning(f"Receive operation cancelled or connection error: {e}")  
            return None  
        except Exception as e:  
            logger.error(f"Error receiving message: {e}")  
            return None

    def process\_ea\_message(self, ea\_id, trading\_pair, message):  
        """Processes messages received from an EA (heartbeats, trade responses)."""  
        try:  
            msg \= json.loads(message)  
            msg\_type \= msg.get('type')

            if msg\_type \== 'HEARTBEAT':  
                with ea\_lock:  
                    if trading\_pair in ea\_status:  
                        ea\_status\[trading\_pair\]\["last\_heartbeat"\] \= datetime.now()  
                        \# logger.debug(f"Heartbeat from {ea\_id} ({trading\_pair})") \# Too noisy for debug  
            elif msg\_type \== 'RESPONSE': \# EA sends back trade execution responses  
                logger.info(f"Received trade response from {ea\_id} ({trading\_pair}): {msg.get('status')} \- Signal ID: {msg.get('signal\_id')}")  
                \# Here, you would typically write this response to your database or log it for audit.  
                \# Example: DatabaseManager.log\_trade\_response(msg)  
            else:  
                logger.warning(f"Unknown message type from {ea\_id} ({trading\_pair}): {msg\_type} \- {message}")

        except json.JSONDecodeError:  
            logger.error(f"Received non-JSON message from {ea\_id} ({trading\_pair}): {message}")  
        except Exception as e:  
            logger.error(f"Error processing message from {ea\_id} ({trading\_pair}): {e}")

    def send\_signal\_to\_ea(self, trading\_pair: str, signal\_message: dict):  
        """Sends a signal message to a specific EA via socket."""  
        with ea\_lock:  
            conn \= ea\_connections.get(trading\_pair)  
            if conn and ea\_status.get(trading\_pair, {}).get("status") \== "CONNECTED":  
                try:  
                    json\_msg \= json.dumps(signal\_message)  
                    \# Prepend length to the message  
                    message\_bytes \= json\_msg.encode('utf-8')  
                    len\_bytes \= len(message\_bytes).to\_bytes(4, byteorder='little') \# Match C++ DLL's little-endian  
                    full\_message \= len\_bytes \+ message\_bytes

                    asyncio.create\_task(asyncio.get\_event\_loop().sock\_sendall(conn, full\_message))  
                    logger.info(f"Signal sent to EA for {trading\_pair}: {signal\_message.get('signal\_id')}")  
                    return True  
                except Exception as e:  
                    logger.error(f"Failed to send signal to {trading\_pair} via socket: {e}")  
                    ea\_status\[trading\_pair\]\["status"\] \= "DISCONNECTED" \# Mark as disconnected  
                    \# Trigger fallback logic to named pipes/CSV here if this was the primary  
                    self.fallback\_send\_signal(trading\_pair, signal\_message)  
                    return False  
            else:  
                logger.warning(f"EA for {trading\_pair} not connected via socket. Attempting fallback.")  
                self.fallback\_send\_signal(trading\_pair, signal\_message)  
                return False

    def fallback\_send\_signal(self, trading\_pair: str, signal\_message: dict):  
        """Fallback mechanism for sending signals (Named Pipes, then CSV)."""  
        \# This is where Named Pipe and CSV writing logic would go.  
        \# For Named Pipes, you'd need to create and manage the pipe server side.  
        \# For CSV, you'd write the signal directly to the MQL4/Files/\[PAIR\]\_signals.csv.  
          
        \# Example for CSV fallback:  
        \# from file\_manager\_py import FileManager \# Assuming a Python FileManager utility  
        \# file\_manager \= FileManager()  
        \# signal\_id \= signal\_message.get('signal\_id', 'unknown')  
        \# signal\_symbol \= signal\_message.get('symbol', trading\_pair)  
        \# if file\_manager.write\_signal\_to\_csv(signal\_message, signal\_symbol): \# Requires Python CSV writer  
        \#    logger.info(f"Signal {signal\_id} written to CSV for {signal\_symbol} as fallback.")  
        \# else:  
        logger.error(f"No real-time connection for {trading\_pair}. CSV/Named Pipe fallback not fully implemented in server yet. Signal {signal\_message.get('signal\_id')} dropped.")  
        \# In a full system, you would have dedicated classes/functions for pipe and CSV writing here.

    def \_heartbeat\_monitor(self):  
        """Monitors EA heartbeats and marks disconnected EAs."""  
        while self.running:  
            time.sleep(HEARTBEAT\_INTERVAL)  
            with ea\_lock:  
                disconnected\_pairs \= \[\]  
                for pair, status in ea\_status.items():  
                    if status\["status"\] \== "CONNECTED":  
                        time\_since\_last\_heartbeat \= (datetime.now() \- status\["last\_heartbeat"\]).total\_seconds()  
                        if time\_since\_last\_heartbeat \> HEARTBEAT\_INTERVAL \* 2: \# Allow some grace period  
                            logger.warning(f"EA for {pair} timed out (no heartbeat for {time\_since\_last\_heartbeat}s). Marking as DISCONNECTED.")  
                            status\["status"\] \= "DISCONNECTED"  
                            disconnected\_pairs.append(pair)  
                  
                \# Clean up actual socket objects for truly disconnected ones  
                for pair in disconnected\_pairs:  
                    if pair in ea\_connections:  
                        try:  
                            ea\_connections\[pair\].shutdown(socket.SHUT\_RDWR)  
                            ea\_connections\[pair\].close()  
                        except Exception as e:  
                            logger.error(f"Error closing timed out connection for {pair}: {e}")  
                        del ea\_connections\[pair\]  
                  
                \# logger.debug(f"Current active connections (after heartbeat check): {len(ea\_connections)}")

    def \_signal\_generation\_loop(self):  
        """Placeholder for a background signal generation and distribution loop."""  
        \# This would typically interact with a SignalGeneratorService  
        \# For demo, just sends a dummy signal periodically  
        dummy\_signal\_id\_counter \= 0  
        while self.running:  
            time.sleep(server\_config.get('signal\_generation', {}).get('interval\_seconds', 10)) \# Example interval  
              
            \# Example: Send a signal to a specific pair for testing  
            test\_pair \= "EURUSD" \# This EA instance is running EURUSD  
              
            if test\_pair in ea\_connections and ea\_status.get(test\_pair, {}).get("status") \== "CONNECTED":  
                dummy\_signal\_id\_counter \+= 1  
                signal\_data \= {  
                    "type": "SIGNAL",  
                    "signal\_id": f"dummy\_signal\_{dummy\_signal\_id\_counter}",  
                    "symbol": test\_pair,  
                    "direction": "BUY" if dummy\_signal\_id\_counter % 2 \== 0 else "SELL",  
                    "confidence": 0.85,  
                    "timestamp": datetime.now().isoformat(timespec='seconds'),  
                    "strategy\_id": "BREAKOUT\_SIGNAL", \# Matches signal\_id\_mapping.csv for SET\_02  
                    "parameter\_set": "SET\_02", \# Explicitly send set\_id via socket  
                    "metadata": {"source": "python\_simulator"}  
                }  
                logger.info(f"Attempting to send dummy signal {signal\_data\['signal\_id'\]} to {test\_pair}")  
                self.send\_signal\_to\_ea(test\_pair, signal\_data)  
            else:  
                logger.debug(f"EA for {test\_pair} not connected. Skipping dummy signal generation.")

    def run(self):  
        """Entry point for running the server and background tasks."""  
        \# Start heartbeat monitoring in a separate thread  
        heartbeat\_thread \= threading.Thread(target=self.\_heartbeat\_monitor, daemon=True)  
        heartbeat\_thread.start()

        \# Start a dummy signal generation loop in a separate thread  
        self.signal\_generation\_thread \= threading.Thread(target=self.\_signal\_generation\_loop, daemon=True)  
        self.signal\_generation\_thread.start()  
          
        \# Run the asyncio server in the main thread (or a dedicated loop)  
        try:  
            asyncio.run(self.start\_async\_server())  
        except KeyboardInterrupt:  
            logger.info("Server shutting down due to keyboard interrupt.")  
        except Exception as e:  
            logger.critical(f"Unhandled exception in main server loop: {e}", exc\_info=True)  
        finally:  
            self.stop\_server()

if \_\_name\_\_ \== "\_\_main\_\_":  
    \# Load initial config (config\_manager already loaded globals)  
    \# This might need to be adjusted if you want to pass CLI arguments for config paths  
      
    server \= TradingServer(SERVER\_HOST, SERVER\_PORT)  
    try:  
        server.run()  
    except Exception as e:  
        logger.critical(f"Failed to start trading server: {e}", exc\_info=True)

'@

\# signal\_generator.py \- Placeholder for signal generation  
$signalGeneratorContent \= @'  
import logging  
from typing import Dict, Any, Optional  
from datetime import datetime  
import uuid  
import json

\# from utils.config\_manager import ConfigurationManager \# Assuming BaseService handles this  
\# from models.signal import Signal \# Assuming a Signal class if more complex

\# This is a placeholder. In a real system, this service would  
\# fetch market data, run analytics, and generate signals based on models.

logger \= logging.getLogger(\_\_name\_\_)

class SignalGeneratorService: \# Not inheriting BaseService here, as it's typically part of Python server.  
                               \# If it were a standalone microservice, it would.  
    def \_\_init\_\_(self, config: Dict\[str, Any\]):  
        self.config \= config  
        self.interval \= self.config.get('interval\_seconds', 5\)  
        self.confidence\_threshold \= self.config.get('confidence\_threshold', 0.6)  
        logger.info("SignalGeneratorService initialized.")

    def generate\_signal(self, symbol: str, strategy\_id: str \= "DEFAULT\_STRATEGY") \-\> Optional\[Dict\[str, Any\]\]:  
        """  
        Generates a dummy trading signal.  
        In a real system, this would involve complex logic, ML models, etc.  
        """  
        signal\_id \= str(uuid.uuid4())  
        direction \= "BUY" if datetime.now().second % 2 \== 0 else "SELL" \# Example logic  
        confidence \= self.config.get('confidence\_threshold', 0.85) \# Use config  
        timestamp \= datetime.now().isoformat(timespec='seconds')  
          
        \# Match the EA's SignalData struct and JSON protocol  
        signal \= {  
            "type": "SIGNAL",  
            "signal\_id": signal\_id,  
            "symbol": symbol,  
            "direction": direction,  
            "confidence": confidence,  
            "timestamp": timestamp,  
            "strategy\_id": strategy\_id, \# e.g., "BREAKOUT\_SIGNAL" for 10-param EA  
            "parameter\_set": "SET\_02", \# Example: explicitly suggest a set  
            "metadata": {  
                "source": "dummy\_generator",  
                "timestamp\_ms": datetime.now().timestamp() \* 1000,  
                "some\_indicator": 123.45  
            }  
        }  
        logger.debug(f"Generated dummy signal: {signal\['signal\_id'\]} for {symbol}")  
        return signal

    def validate\_and\_enhance\_signal(self, signal: Dict\[str, Any\]) \-\> bool:  
        """  
        Performs basic validation on a generated signal.  
        In a real system, this could involve more complex rules or AI validation.  
        """  
        if not all(k in signal for k in \["signal\_id", "symbol", "direction", "confidence", "timestamp"\]):  
            logger.warning(f"Invalid signal format: {signal}")  
            return False  
          
        if not (0.0 \<= signal\["confidence"\] \<= 1.0):  
            logger.warning(f"Signal confidence out of range: {signal\['confidence'\]}")  
            return False  
              
        if signal\["confidence"\] \< self.confidence\_threshold:  
            logger.info(f"Signal {signal\['signal\_id'\]} below confidence threshold: {signal\['confidence'\]}")  
            return False  
              
        return True

    def write\_signal\_to\_csv(self, signal: Dict\[str, Any\], symbol: str):  
        """  
        Writes a signal to the MT4-compatible CSV format.  
        This is typically used for fallback or for initial testing without a full bridge.  
        This would be used by \`trading\_server.py\`'s fallback.  
        """  
        \# Ensure path aligns with MQL4/Files/signals  
        \# For simplicity, this assumes Python server runs from TradingSystem/Python/src  
        \# And writes to TradingSystem/MT4/Files/signals  
        csv\_file\_path \= os.path.abspath(os.path.join(os.path.dirname(\_\_file\_\_), '..', '..', 'MT4', 'Files', 'signals', f'{symbol}\_signals.csv'))  
          
        \# Ensure directory exists  
        os.makedirs(os.path.dirname(csv\_file\_path), exist\_ok=True)

        try:  
            with open(csv\_file\_path, 'a', newline='', encoding='utf-8') as f:  
                \# Check if file is empty to write header  
                if f.tell() \== 0:  
                    f.write("id,symbol,direction,confidence,timestamp,strategy\_id,metadata\\n") \#  
                  
                \# Write signal data  
                \# Order: id,symbol,direction,confidence,timestamp,strategy\_id,metadata  
                line \= f"{signal.get('signal\_id','')},{signal.get('symbol','')},{signal.get('direction','')},{signal.get('confidence',0.0):.2f},{signal.get('timestamp','')},{signal.get('strategy\_id','')},{json.dumps(signal.get('metadata',{}))}\\n"  
                f.write(line)  
            logger.info(f"Signal {signal.get('signal\_id')} written to CSV: {csv\_file\_path}")  
            return True  
        except Exception as e:  
            logger.error(f"Failed to write signal to CSV {csv\_file\_path}: {e}")  
            return False

if \_\_name\_\_ \== "\_\_main\_\_":  
    \# Example usage:  
    \# This requires logger\_setup and config\_manager to be available.  
    \# For a quick test, you might simplify imports or run via trading\_server.py.

    \# Dummy config for standalone test  
    dummy\_config \= {  
        'signal\_generation': {  
            'interval\_seconds': 1,  
            'confidence\_threshold': 0.7  
        }  
    }  
      
    \# Simple logging setup for standalone run  
    logging.basicConfig(level=logging.INFO, format='%(asctime)s \- %(name)s \- %(levelname)s \- %(message)s')  
      
    \# Initialize service  
    signal\_gen \= SignalGeneratorService(dummy\_config\['signal\_generation'\])  
      
    test\_symbol \= "EURUSD"  
    for i in range(3):  
        generated\_signal \= signal\_gen.generate\_signal(test\_symbol, "BREAKOUT\_SIGNAL")  
        if generated\_signal and signal\_gen.validate\_and\_enhance\_signal(generated\_signal):  
            print(f"Generated: {generated\_signal}")  
            signal\_gen.write\_signal\_to\_csv(generated\_signal, test\_symbol)  
        time.sleep(1)

'@

\# message\_broker.py \- Message routing placeholder  
$messageBrokerContent \= @'  
import logging  
from typing import Dict, Any, Callable

logger \= logging.getLogger(\_\_name\_\_)

class MessageBroker:  
    """  
    Placeholder for an internal message broker.  
    In a full system, this could use queues (e.g., Python's queue.Queue, RabbitMQ, Redis Pub/Sub)  
    to facilitate communication between different internal services (SignalGenerator, MarketData, TradingServer).  
    """  
    def \_\_init\_\_(self):  
        self.subscribers: Dict\[str, Callable\[\[Dict\[str, Any\]\], None\]\] \= {}  
        logger.info("MessageBroker initialized (placeholder).")

    def publish(self, topic: str, message: Dict\[str, Any\]):  
        """Publishes a message to a specific topic."""  
        logger.debug(f"Publishing to topic '{topic}': {message}")  
        if topic in self.subscribers:  
            try:  
                self.subscribers\[topic\](message)  
            except Exception as e:  
                logger.error(f"Error processing message for topic '{topic}': {e}")  
        else:  
            logger.warning(f"No subscribers for topic '{topic}'. Message not delivered.")

    def subscribe(self, topic: str, callback: Callable\[\[Dict\[str, Any\]\], None\]):  
        """Subscribes a callback function to a topic."""  
        if topic in self.subscribers:  
            logger.warning(f"Topic '{topic}' already has a subscriber. Overwriting.")  
        self.subscribers\[topic\] \= callback  
        logger.info(f"Subscribed callback to topic '{topic}'.")

    def unsubscribe(self, topic: str):  
        """Unsubscribes from a topic."""  
        if topic in self.subscribers:  
            del self.subscribers\[topic\]  
            logger.info(f"Unsubscribed from topic '{topic}'.")  
        else:  
            logger.warning(f"No subscriber found for topic '{topic}'.")

if \_\_name\_\_ \== "\_\_main\_\_":  
    \# Example Usage:  
    logging.basicConfig(level=logging.INFO, format='%(asctime)s \- %(name)s \- %(levelname)s \- %(message)s')  
    broker \= MessageBroker()

    def signal\_handler(signal\_data):  
        print(f"Signal Handler received: {signal\_data}")

    def trade\_response\_handler(response\_data):  
        print(f"Trade Response Handler received: {response\_data}")

    broker.subscribe("signals.new", signal\_handler)  
    broker.subscribe("trades.response", trade\_response\_handler)

    broker.publish("signals.new", {"id": "123", "symbol": "EURUSD", "direction": "BUY"})  
    broker.publish("trades.response", {"signal\_id": "123", "status": "EXECUTED", "price": 1.1234})  
    broker.publish("some.other.topic", {"data": "test"})

    broker.unsubscribe("signals.new")  
    broker.publish("signals.new", {"id": "456", "symbol": "GBPUSD", "direction": "SELL"}) \# Won't be received  
'@

\# database\_manager.py \- Database operations placeholder  
$databaseManagerContent \= @'  
import sqlite3 \# For SQLite database  
import logging  
import os  
from typing import Dict, Any, List, Tuple

logger \= logging.getLogger(\_\_name\_\_)

class DatabaseManager:  
    """  
    Manages database operations for the trading system.  
    Uses SQLite for simplicity in this initial setup.  
    """  
    def \_\_init\_\_(self, db\_path: str \= "trading\_system.db", schema\_path: str \= None):  
        self.db\_path \= db\_path  
        self.schema\_path \= schema\_path  
        self.conn \= None  
        self.setup\_database()  
        logger.info(f"DatabaseManager initialized for {self.db\_path}")

    def setup\_database(self):  
        """Connects to the database and creates schema if it doesn't exist."""  
        try:  
            self.conn \= sqlite3.connect(self.db\_path, check\_same\_thread=False) \# Allow multiple threads to use same connection  
            self.conn.row\_factory \= sqlite3.Row \# Access columns by name  
            logger.info(f"Connected to database: {self.db\_path}")  
            if self.schema\_path and os.path.exists(self.schema\_path):  
                self.create\_schema\_from\_file()  
            else:  
                logger.warning(f"No database schema file found at {self.schema\_path}. Schema might not be created automatically.")  
                \# Fallback to direct schema creation if file not found (for initial run)  
                self.create\_default\_schema()  
              
            \# Performance optimizations  
            self.conn.execute("PRAGMA journal\_mode \= WAL") \# Write-Ahead Logging for concurrency  
            self.conn.execute("PRAGMA synchronous \= NORMAL") \# Reduce syncs to disk  
            self.conn.execute("PRAGMA cache\_size \= 10000") \# Increase cache size  
            self.conn.execute("PRAGMA temp\_store \= MEMORY") \# Use memory for temp tables  
              
            logger.info("Database setup complete.")  
        except sqlite3.Error as e:  
            logger.critical(f"Failed to connect or set up database at {self.db\_path}: {e}")  
            self.conn \= None \# Ensure connection is None on failure

    def create\_schema\_from\_file(self):  
        """Executes SQL commands from a schema file to create tables."""  
        if not self.conn:  
            logger.error("No database connection to create schema.")  
            return

        try:  
            with open(self.schema\_path, 'r', encoding='utf-8') as f:  
                sql\_script \= f.read()  
            self.conn.executescript(sql\_script)  
            self.conn.commit()  
            logger.info(f"Database schema loaded from {self.schema\_path}")  
        except Exception as e:  
            logger.error(f"Error loading database schema from file {self.schema\_path}: {e}", exc\_info=True)

    def create\_default\_schema(self):  
        """Creates a basic default schema if no file is provided/found."""  
        if not self.conn: return  
        try:  
            cursor \= self.conn.cursor()  
            cursor.execute("""  
                CREATE TABLE IF NOT EXISTS signals (  
                    id TEXT PRIMARY KEY,  
                    symbol TEXT NOT NULL,  
                    direction TEXT NOT NULL CHECK (direction IN ('BUY', 'SELL')),  
                    confidence REAL NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),  
                    timestamp TIMESTAMP NOT NULL,  
                    strategy\_id TEXT NOT NULL,  
                    metadata TEXT,  
                    processed BOOLEAN DEFAULT FALSE,  
                    created\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP  
                )  
            """)  
            cursor.execute("""  
                CREATE TABLE IF NOT EXISTS trades (  
                    id TEXT PRIMARY KEY,  
                    signal\_id TEXT NOT NULL,  
                    symbol TEXT NOT NULL,  
                    direction TEXT NOT NULL,  
                    lot\_size REAL NOT NULL,  
                    entry\_price REAL,  
                    exit\_price REAL,  
                    stop\_loss REAL,  
                    take\_profit REAL,  
                    status TEXT NOT NULL, \-- e.g., 'PENDING', 'EXECUTED', 'CLOSED', 'REJECTED', 'FAILED'  
                    pnl REAL DEFAULT 0.0,  
                    opened\_at TIMESTAMP,  
                    closed\_at TIMESTAMP,  
                    error\_message TEXT, \-- For trade failures  
                    mt4\_ticket INTEGER,  
                    FOREIGN KEY (signal\_id) REFERENCES signals (id)  
                )  
            """)  
            cursor.execute("""  
                CREATE INDEX IF NOT EXISTS idx\_signals\_symbol ON signals(symbol)  
            """)  
            cursor.execute("""  
                CREATE INDEX IF NOT EXISTS idx\_signals\_timestamp ON signals(timestamp DESC)  
            """)  
            cursor.execute("""  
                CREATE INDEX IF NOT EXISTS idx\_trades\_symbol ON trades(symbol)  
            """)  
            self.conn.commit()  
            logger.info("Default database schema created.")  
        except sqlite3.Error as e:  
            logger.error(f"Error creating default database schema: {e}", exc\_info=True)

    def insert\_signal(self, signal\_data: Dict\[str, Any\]):  
        """Inserts a new signal into the signals table."""  
        if not self.conn: return  
        try:  
            cursor \= self.conn.cursor()  
            cursor.execute("""  
                INSERT INTO signals (id, symbol, direction, confidence, timestamp, strategy\_id, metadata)  
                VALUES (?, ?, ?, ?, ?, ?, ?)  
            """, (  
                signal\_data.get('signal\_id'),  
                signal\_data.get('symbol'),  
                signal\_data.get('direction'),  
                signal\_data.get('confidence'),  
                signal\_data.get('timestamp'),  
                signal\_data.get('strategy\_id'),  
                json.dumps(signal\_data.get('metadata', {}))  
            ))  
            self.conn.commit()  
            logger.info(f"Signal {signal\_data.get('signal\_id')} inserted into DB.")  
        except sqlite3.Error as e:  
            logger.error(f"Error inserting signal {signal\_data.get('signal\_id')}: {e}", exc\_info=True)

    def log\_trade\_response(self, response\_data: Dict\[str, Any\]):  
        """Logs a trade response from EA into the trades table."""  
        if not self.conn: return  
        try:  
            cursor \= self.conn.cursor()  
              
            signal\_id \= response\_data.get('signal\_id')  
            status \= response\_data.get('status')  
            trade\_id \= response\_data.get('trade\_id', f"AUTO\_{signal\_id}")  
            execution\_price \= response\_data.get('execution\_price', 0.0)  
            lot\_size \= response\_data.get('lot\_size', 0.0)  
            error\_message \= response\_data.get('error\_message', '')  
            timestamp \= response\_data.get('timestamp', datetime.now().isoformat(timespec='seconds')) \# Use server time if not provided  
            magic\_number \= response\_data.get('magic\_number', 0\)  
              
            \# Try to get symbol from signals table if available  
            symbol \= ""  
            cursor.execute("SELECT symbol, direction FROM signals WHERE id \= ?", (signal\_id,))  
            signal\_info \= cursor.fetchone()  
            if signal\_info:  
                symbol \= signal\_info\['symbol'\]  
                direction \= signal\_info\['direction'\]  
            else:  
                logger.warning(f"Could not find signal\_id {signal\_id} in DB for trade response. Symbol/Direction unknown.")  
                symbol \= "UNKNOWN" \# Fallback  
                direction \= "UNKNOWN" \# Fallback

            \# Update trade if it already exists (e.g., from PENDING to EXECUTED/CLOSED)  
            cursor.execute("SELECT id FROM trades WHERE id \= ?", (trade\_id,))  
            existing\_trade \= cursor.fetchone()

            if existing\_trade:  
                \# Update existing trade record (e.g., status, exit\_price, pnl, closed\_at)  
                cursor.execute("""  
                    UPDATE trades  
                    SET status \= ?, exit\_price \= ?, closed\_at \= ?, pnl \= ?, error\_message \= ?  
                    WHERE id \= ?  
                """, (status, execution\_price, timestamp, response\_data.get('pnl', 0.0), error\_message, trade\_id))  
                logger.info(f"Updated trade {trade\_id} status to {status}.")  
            else:  
                \# Insert new trade record  
                cursor.execute("""  
                    INSERT INTO trades (id, signal\_id, symbol, direction, lot\_size, entry\_price, status, opened\_at, error\_message, mt4\_ticket)  
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)  
                """, (  
                    trade\_id, signal\_id, symbol, direction, lot\_size,  
                    execution\_price, status, timestamp, error\_message, magic\_number \# MT4 ticket or magic number  
                ))  
                logger.info(f"Trade {trade\_id} logged with status {status}.")  
              
            self.conn.commit()  
              
            \# Mark signal as processed  
            cursor.execute("UPDATE signals SET processed \= TRUE WHERE id \= ?", (signal\_id,))  
            self.conn.commit()  
            logger.debug(f"Signal {signal\_id} marked as processed.")

        except sqlite3.Error as e:  
            logger.error(f"Error logging trade response {response\_data.get('signal\_id')}: {e}", exc\_info=True)

    def get\_unprocessed\_signals(self, symbol: str \= None) \-\> List\[Dict\[str, Any\]\]:  
        """Retrieves unprocessed signals from the database."""  
        if not self.conn: return \[\]  
        try:  
            cursor \= self.conn.cursor()  
            query \= "SELECT \* FROM signals WHERE processed \= FALSE"  
            params \= \[\]  
            if symbol:  
                query \+= " AND symbol \= ?"  
                params.append(symbol)  
            query \+= " ORDER BY timestamp ASC"  
            cursor.execute(query, tuple(params))  
              
            signals \= \[\]  
            for row in cursor.fetchall():  
                signal \= dict(row)  
                \# Convert metadata string back to dict  
                if 'metadata' in signal and signal\['metadata'\]:  
                    try:  
                        signal\['metadata'\] \= json.loads(signal\['metadata'\])  
                    except json.JSONDecodeError:  
                        logger.warning(f"Could not parse metadata for signal {signal\['id'\]}: {signal\['metadata'\]}")  
                        signal\['metadata'\] \= {}  
                signals.append(signal)  
            return signals  
        except sqlite3.Error as e:  
            logger.error(f"Error retrieving unprocessed signals: {e}", exc\_info=True)  
            return \[\]

    def close(self):  
        """Closes the database connection."""  
        if self.conn:  
            self.conn.close()  
            logger.info(f"Database connection to {self.db\_path} closed.")

if \_\_name\_\_ \== "\_\_main\_\_":  
    \# Example Usage:  
    \# Ensure logs directory exists for setup\_logging if not running via main server  
    log\_dir \= os.path.abspath(os.path.join(os.path.dirname(\_\_file\_\_), '..', '..', 'Logs'))  
    os.makedirs(log\_dir, exist\_ok=True)  
      
    \# Dummy logging config for standalone test  
    logging\_config\_test \= {  
        'level': 'DEBUG',  
        'file\_path': os.path.join(log\_dir, 'database\_manager\_test.log'),  
        'format': '%(asctime)s \- %(name)s \- %(levelname)s \- %(message)s'  
    }  
    setup\_logging(logging\_config\_test)

    \# Define paths relative to the script for testing  
    db\_file \= os.path.abspath(os.path.join(os.path.dirname(\_\_file\_\_), '..', '..', 'Database', 'test\_trading\_system.db'))  
    schema\_file \= os.path.abspath(os.path.join(os.path.dirname(\_\_file\_\_), '..', '..', 'Database', 'schema', 'trading\_schema.sql'))  
      
    \# Ensure DB directory exists  
    os.makedirs(os.path.dirname(db\_file), exist\_ok=True)

    db\_manager \= DatabaseManager(db\_path=db\_file, schema\_path=schema\_file)

    \# Test signal insertion  
    test\_signal \= {  
        "signal\_id": "test-signal-123",  
        "symbol": "EURUSD",  
        "direction": "BUY",  
        "confidence": 0.9,  
        "timestamp": datetime.now().isoformat(timespec='seconds'),  
        "strategy\_id": "TEST\_STRATEGY",  
        "metadata": {"reason": "unit\_test", "version": 1.0}  
    }  
    db\_manager.insert\_signal(test\_signal)

    \# Test trade response logging (execution)  
    test\_response\_executed \= {  
        "signal\_id": "test-signal-123",  
        "trade\_id": "TRADE\_ABC\_456",  
        "status": "EXECUTED",  
        "execution\_price": 1.1234,  
        "timestamp": datetime.now().isoformat(timespec='seconds'),  
        "error\_message": "",  
        "lot\_size": 0.01,  
        "magic\_number": 10001,  
        "slippage": 2,  
        "pnl": 0.0 \# Initial PnL  
    }  
    db\_manager.log\_trade\_response(test\_response\_executed)

    \# Test trade response logging (close with profit)  
    test\_response\_closed \= {  
        "signal\_id": "test-signal-123", \# Same signal ID, but refers to closing the trade  
        "trade\_id": "TRADE\_ABC\_456",  
        "status": "CLOSED",  
        "execution\_price": 1.1254, \# Closing price  
        "timestamp": datetime.now().isoformat(timespec='seconds'),  
        "error\_message": "",  
        "lot\_size": 0.01,  
        "magic\_number": 10001,  
        "slippage": 0,  
        "pnl": 20.0 \# Profit  
    }  
    db\_manager.log\_trade\_response(test\_response\_closed)

    \# Test getting unprocessed signals  
    unprocessed \= db\_manager.get\_unprocessed\_signals()  
    print("\\nUnprocessed Signals:")  
    for s in unprocessed:  
        print(s)

    db\_manager.close()

    \# Clean up test database  
    \# os.remove(db\_file)  
    \# print(f"Cleaned up {db\_file}")

'@

\# config\_manager.py \- Configuration management with hot-reload  
$configManagerContent \= @'  
import yaml  
import os  
import logging  
from typing import Dict, Any, List  
from datetime import datetime  
\# For hot-reload, watchdog library is needed. Install with: pip install watchdog  
try:  
    from watchdog.observers import Observer  
    from watchdog.events import FileSystemEventHandler  
    WATCHDOG\_AVAILABLE \= True  
except ImportError:  
    WATCHDOG\_AVAILABLE \= False  
    print("Warning: 'watchdog' library not found. Hot-reload will be disabled. Install with 'pip install watchdog'")

logger \= logging.getLogger(\_\_name\_\_)

class ConfigManagerObserver:  
    """Interface for components that want to be notified of config changes."""  
    def on\_config\_changed(self, config\_name: str, old\_config: Dict\[str, Any\], new\_config: Dict\[str, Any\]):  
        raise NotImplementedError

class ConfigurationManager:  
    """  
    Manages loading and hot-reloading of YAML configuration files.  
    Supports environment variable overrides.  
    """  
    def \_\_init\_\_(self, config\_dir: str):  
        self.config\_dir \= os.path.abspath(config\_dir)  
        self.configs: Dict\[str, Dict\[str, Any\]\] \= {}  
        self.file\_watchers: Dict\[str, Observer\] \= {} \# For watchdog observers  
        self.observers: List\[ConfigManagerObserver\] \= \[\] \# List of registered observers  
          
        if not os.path.exists(self.config\_dir):  
            raise FileNotFoundError(f"Configuration directory not found: {self.config\_dir}")  
          
        logger.info(f"ConfigurationManager initialized. Config directory: {self.config\_dir}")  
        if not WATCHDOG\_AVAILABLE:  
            logger.warning("Configuration hot-reload is disabled because 'watchdog' library is not installed.")

    def \_load\_yaml\_file(self, config\_path: str) \-\> Dict\[str, Any\]:  
        """Loads a single YAML configuration file."""  
        if not os.path.exists(config\_path):  
            logger.error(f"Config file not found: {config\_path}")  
            return {}

        try:  
            with open(config\_path, 'r', encoding='utf-8') as file:  
                config \= yaml.safe\_load(file)  
            if config is None: \# Handle empty YAML file  
                config \= {}  
            logger.info(f"Loaded config from: {config\_path}")  
            return self.\_apply\_env\_overrides(config)  
        except Exception as e:  
            logger.error(f"Error loading YAML file {config\_path}: {e}", exc\_info=True)  
            return {}

    def \_apply\_env\_overrides(self, config: Dict\[str, Any\]) \-\> Dict\[str, Any\]:  
        """Applies environment variable overrides to the configuration.  
        Environment variables should be prefixed with 'TRADING\_SYSTEM\_'.  
        E.g., TRADING\_SYSTEM\_SERVER\_PORT will override server.port in config.  
        """  
        for key, value in os.environ.items():  
            if key.startswith('TRADING\_SYSTEM\_'):  
                \# Convert ENV\_VAR to dot.notation.key for dictionary traversal  
                config\_key\_path \= key\[len('TRADING\_SYSTEM\_'):\].lower().replace('\_\_', '.') \# '\_\_' for nested keys  
                parts \= config\_key\_path.split('.')  
                  
                current\_level \= config  
                for i, part in enumerate(parts):  
                    if i \== len(parts) \- 1: \# Last part is the actual key  
                        try: \# Attempt to cast to int/float/bool if possible  
                            if value.lower() \== 'true': current\_level\[part\] \= True  
                            elif value.lower() \== 'false': current\_level\[part\] \= False  
                            elif value.isdigit(): current\_level\[part\] \= int(value)  
                            elif value.replace('.', '', 1).isdigit(): current\_level\[part\] \= float(value)  
                            else: current\_level\[part\] \= value  
                            logger.info(f"Overridden config: {config\_key\_path} \= {current\_level\[part\]} (from ENV)")  
                        except ValueError:  
                            current\_level\[part\] \= value \# Fallback to string  
                    else: \# Not the last part, navigate or create dictionary  
                        if part not in current\_level or not isinstance(current\_level\[part\], dict):  
                            current\_level\[part\] \= {}  
                        current\_level \= current\_level\[part\]  
        return config

    def load\_configuration(self, config\_name: str) \-\> Dict\[str, Any\]:  
        """  
        Loads a configuration and sets up hot-reload monitoring.  
        config\_name should be without .yaml extension (e.g., 'server\_config').  
        """  
        config\_path \= os.path.join(self.config\_dir, f"{config\_name}.yaml")  
          
        config \= self.\_load\_yaml\_file(config\_path)  
        self.configs\[config\_name\] \= config  
          
        if WATCHDOG\_AVAILABLE and config\_name not in self.file\_watchers:  
            self.\_setup\_file\_watcher(config\_name, config\_path)  
          
        return config

    def get\_configuration(self, config\_name: str) \-\> Dict\[str, Any\]:  
        """Retrieves a loaded configuration by name."""  
        return self.configs.get(config\_name, {})

    def \_setup\_file\_watcher(self, config\_name: str, config\_path: str):  
        """Sets up a file system watcher for configuration changes."""  
        class ConfigChangeHandler(FileSystemEventHandler):  
            def \_\_init\_\_(self, manager\_instance, name):  
                self.manager \= manager\_instance  
                self.config\_name \= name  
                self.last\_modified \= datetime.now()

            def on\_modified(self, event):  
                if not event.is\_directory and event.src\_path \== config\_path:  
                    \# Debounce multiple events for a single save operation  
                    if (datetime.now() \- self.last\_modified).total\_seconds() \> 1: \# Only process if \>1 sec since last  
                        logger.info(f"Config file '{self.config\_name}.yaml' modified. Reloading...")  
                        self.manager.\_reload\_configuration(self.config\_name)  
                        self.last\_modified \= datetime.now()

        event\_handler \= ConfigChangeHandler(self, config\_name)  
        observer \= Observer()  
        observer.schedule(event\_handler, os.path.dirname(config\_path), recursive=False)  
        observer.start()  
          
        self.file\_watchers\[config\_name\] \= observer  
        logger.debug(f"File watcher set up for {config\_path}")

    def \_reload\_configuration(self, config\_name: str):  
        """Reloads a specific configuration and notifies registered observers."""  
        config\_path \= os.path.join(self.config\_dir, f"{config\_name}.yaml")  
        new\_config \= self.\_load\_yaml\_file(config\_path)  
        old\_config \= self.configs.get(config\_name, {})  
          
        self.configs\[config\_name\] \= new\_config  
        logger.info(f"Configuration '{config\_name}' reloaded.")

        \# Notify observers of change  
        for observer in self.observers:  
            try:  
                observer.on\_config\_changed(config\_name, old\_config, new\_config)  
            except Exception as e:  
                logger.error(f"Error notifying observer {observer.\_\_class\_\_.\_\_name\_\_} of config change: {e}", exc\_info=True)

    def register\_observer(self, observer: ConfigManagerObserver):  
        """Registers an object to receive notifications on config changes."""  
        if not isinstance(observer, ConfigManagerObserver):  
            logger.error("Registered observer must implement ConfigManagerObserver interface.")  
            return  
        self.observers.append(observer)  
        logger.info(f"Registered observer: {observer.\_\_class\_\_.\_\_name\_\_}")

    def stop\_watchers(self):  
        """Stops all file watchers."""  
        for name, observer in self.file\_watchers.items():  
            if observer.is\_alive():  
                observer.stop()  
                observer.join()  
                logger.info(f"Stopped watcher for {name}.yaml")  
        self.file\_watchers.clear()

if \_\_name\_\_ \== "\_\_main\_\_":  
    \# Example usage for testing purposes  
    logging.basicConfig(level=logging.INFO, format='%(asctime)s \- %(name)s \- %(levelname)s \- %(message)s')

    \# Create a dummy config directory and file for testing  
    test\_config\_dir \= "temp\_config\_test"  
    os.makedirs(test\_config\_dir, exist\_ok=True)  
      
    test\_config\_path \= os.path.join(test\_config\_dir, "my\_app\_config.yaml")  
    initial\_content \= """  
    app:  
      name: TestApp  
      version: 1.0  
    settings:  
      polling\_interval: 5  
      debug\_mode: false  
    """  
    with open(test\_config\_path, "w") as f:  
        f.write(initial\_content)

    print(f"Initial config file created at: {test\_config\_path}")

    try:  
        config\_manager \= ConfigurationManager(test\_config\_dir)  
        app\_config \= config\_manager.load\_configuration("my\_app\_config")  
        print("\\nInitial Config:")  
        print(app\_config)  
        print(f"Polling Interval: {app\_config\['settings'\]\['polling\_interval'\]}")

        class MyComponent(ConfigManagerObserver):  
            def \_\_init\_\_(self, name):  
                self.name \= name  
            def on\_config\_changed(self, config\_name, old\_config, new\_config):  
                print(f"\\n\[{self.name}\] Config '{config\_name}' changed\!")  
                print(f"Old polling\_interval: {old\_config\['settings'\]\['polling\_interval'\]}")  
                print(f"New polling\_interval: {new\_config\['settings'\]\['polling\_interval'\]}")  
                print(f"New debug\_mode: {new\_config\['settings'\]\['debug\_mode'\]}")  
          
        comp1 \= MyComponent("ComponentA")  
        config\_manager.register\_observer(comp1)

        if WATCHDOG\_AVAILABLE:  
            print("\\nWaiting for config file changes (modify my\_app\_config.yaml in temp\_config\_test)...")  
            print("Try changing 'polling\_interval' to 10 and 'debug\_mode' to true.")  
            print("Set environment variable TRADING\_SYSTEM\_APP\_\_VERSION to '2.0' (note double underscore for nested key)")  
            print("Press Ctrl+C to stop.")  
            while True:  
                time.sleep(1) \# Keep main thread alive for watchdog  
        else:  
            print("\\nWatchdog not available. Hot-reload disabled. Install 'watchdog' for this feature.")

    except Exception as e:  
        print(f"Error during test: {e}")  
    finally:  
        config\_manager.stop\_watchers()  
        \# Clean up dummy config directory  
        if os.path.exists(test\_config\_path):  
            os.remove(test\_config\_path)  
        if os.path.exists(test\_config\_dir):  
            os.rmdir(test\_config\_dir)  
        print("\\nCleaned up test directory.")

'@

\# logger\_setup.py \- Centralized logging configuration  
$loggerSetupContent \= @'  
import logging  
import logging.handlers  
import os  
from typing import Dict, Any

def setup\_logging(config: Dict\[str, Any\]):  
    """  
    Sets up a centralized logging configuration for Python services.  
    Supports file logging with rotation and console logging.  
    Logs are structured to include common fields.  
    """  
    log\_level\_str \= config.get('level', 'INFO').upper()  
    log\_level \= getattr(logging, log\_level\_str, logging.INFO)  
    log\_format \= config.get('format', '%(asctime)s \- %(name)s \- %(levelname)s \- %(message)s')  
      
    \# Ensure log directory exists  
    log\_file\_path \= config.get('file\_path', None)  
    if log\_file\_path:  
        log\_dir \= os.path.dirname(log\_file\_path)  
        if log\_dir and not os.path.exists(log\_dir):  
            os.makedirs(log\_dir, exist\_ok=True)  
      
    \# Root logger configuration  
    root\_logger \= logging.getLogger()  
    root\_logger.setLevel(log\_level)

    \# Clear existing handlers to prevent duplicate logs on re-setup  
    if root\_logger.handlers:  
        for handler in root\_logger.handlers\[:\]:  
            root\_logger.removeHandler(handler)  
            handler.close()

    formatter \= logging.Formatter(log\_format)

    \# Console Handler  
    console\_handler \= logging.StreamHandler()  
    console\_handler.setFormatter(formatter)  
    root\_logger.addHandler(console\_handler)

    \# File Handler with rotation (if file\_path is provided)  
    if log\_file\_path:  
        max\_bytes\_str \= config.get('file\_config', {}).get('max\_size', '10MB')  
        \# Convert string like "10MB" to bytes  
        if max\_bytes\_str.upper().endswith('MB'):  
            max\_bytes \= int(max\_bytes\_str\[:-2\]) \* 1024 \* 1024  
        elif max\_bytes\_str.upper().endswith('KB'):  
            max\_bytes \= int(max\_bytes\_str\[:-2\]) \* 1024  
        else:  
            max\_bytes \= int(max\_bytes\_str) \# Assume bytes if no unit

        backup\_count \= config.get('file\_config', {}).get('backup\_count', 5\)  
        rotation\_type \= config.get('file\_config', {}).get('rotation', 'size')

        if rotation\_type.lower() \== 'size':  
            file\_handler \= logging.handlers.RotatingFileHandler(  
                log\_file\_path,  
                maxBytes=max\_bytes,  
                backupCount=backup\_count,  
                encoding='utf-8'  
            )  
        elif rotation\_type.lower() \== 'time':  
            \# Example: rotate daily at midnight  
            file\_handler \= logging.handlers.TimedRotatingFileHandler(  
                log\_file\_path,  
                when="midnight",  
                interval=1,  
                backupCount=backup\_count,  
                encoding='utf-8'  
            )  
        else:  
            file\_handler \= logging.FileHandler(log\_file\_path, encoding='utf-8')

        file\_handler.setFormatter(formatter)  
        root\_logger.addHandler(file\_handler)

    \# Set specific log levels for other modules if defined in config  
    for logger\_name, level\_str in config.get('loggers', {}).items():  
        logging.getLogger(logger\_name).setLevel(getattr(logging, level\_str.upper(), logging.INFO))  
      
    \# Test logging  
    logging.info("Logging setup complete.")  
    logging.debug("Debug logging is enabled.")

if \_\_name\_\_ \== "\_\_main\_\_":  
    \# Test setup\_logging directly  
    test\_log\_dir \= "temp\_logs"  
    os.makedirs(test\_log\_dir, exist\_ok=True)  
    test\_log\_file \= os.path.join(test\_log\_dir, "test\_app.log")

    test\_config \= {  
        'level': 'DEBUG',  
        'file\_path': test\_log\_file,  
        'format': '%(asctime)s \- %(name)s \- %(levelname)s \- %(message)s',  
        'file\_config': {  
            'max\_size': '1KB', \# Small size for quick rotation test  
            'backup\_count': 3,  
            'rotation': 'size'  
        },  
        'loggers': {  
            'my\_module': 'WARNING'  
        }  
    }  
      
    setup\_logging(test\_config)  
      
    logger \= logging.getLogger('my\_app')  
    my\_module\_logger \= logging.getLogger('my\_module')

    logger.info("This is an info message from my\_app.")  
    logger.debug("This is a debug message from my\_app.")  
    my\_module\_logger.info("This is an info message from my\_module (should not show if level is WARNING).")  
    my\_module\_logger.warning("This is a warning message from my\_module.")  
      
    \# Simulate file growth and rotation  
    print(f"Writing to {test\_log\_file} to test rotation...")  
    for i in range(100):  
        logger.info(f"Log line {i}. This is a test to make the log file grow beyond 1KB.")  
          
    print("Check temp\_logs directory for rotated files (e.g., test\_app.log.1, test\_app.log.2).")

    \# Clean up  
    for f in os.listdir(test\_log\_dir):  
        os.remove(os.path.join(test\_log\_dir, f))  
    os.rmdir(test\_log\_dir)  
    print(f"\\nCleaned up {test\_log\_dir} directory.")  
'@

\# monitoring.py \- System health monitoring placeholder  
$monitoringContent \= @'  
import logging  
from typing import Dict, Any  
import psutil \# For system resource monitoring. Install with: pip install psutil  
import platform  
import os

logger \= logging.getLogger(\_\_name\_\_)

class HealthMonitor:  
    """  
    Provides functions for monitoring the health and performance of the system.  
    This is a placeholder for a more comprehensive monitoring solution that would  
    integrate with metrics collection (e.g., Prometheus) and alerting systems.  
    """  
    def \_\_init\_\_(self, config: Dict\[str, Any\]):  
        self.config \= config  
        self.system\_name \= config.get('system', {}).get('name', 'TradingSystem')  
        logger.info("HealthMonitor initialized.")

    def get\_system\_health(self) \-\> Dict\[str, Any\]:  
        """Collects general system health metrics."""  
        health\_data \= {  
            "system\_name": self.system\_name,  
            "timestamp": datetime.now().isoformat(),  
            "cpu\_percent": psutil.cpu\_percent(interval=1), \# CPU usage over 1 second  
            "memory\_percent": psutil.virtual\_memory().percent, \# System memory usage  
            "disk\_usage\_percent": psutil.disk\_usage(os.getcwd()).percent, \# Disk usage of current drive  
            "network\_io": psutil.net\_io\_counters().\_asdict(), \# Network I/O stats  
            "uptime\_seconds": time.time() \- psutil.boot\_time(), \# System uptime  
            "platform": {  
                "system": platform.system(),  
                "node\_name": platform.node(),  
                "release": platform.release(),  
                "version": platform.version(),  
                "machine": platform.machine(),  
            }  
        }  
        logger.debug("Collected system health metrics.")  
        return health\_data

    def get\_process\_health(self) \-\> Dict\[str, Any\]:  
        """Collects metrics for the current Python process."""  
        process \= psutil.Process(os.getpid())  
        process\_data \= {  
            "pid": os.getpid(),  
            "name": process.name(),  
            "status": process.status(),  
            "cpu\_percent": process.cpu\_percent(interval=None), \# CPU usage since last call  
            "memory\_info": process.memory\_info().\_asdict(), \# Memory details (rss, vms, etc.)  
            "num\_threads": process.num\_threads(),  
            "open\_files": process.num\_fds(), \# Number of open file descriptors  
            "connections": len(process.connections()), \# Number of active network connections  
        }  
        logger.debug("Collected process health metrics.")  
        return process\_data  
      
    def get\_ea\_connection\_status(self, ea\_connections\_map: Dict\[str, Any\]) \-\> Dict\[str, Any\]:  
        """Reports on the status of connected EAs."""  
        status\_summary \= {  
            "total\_expected\_eas": self.config.get('trading', {}).get('total\_expected\_eas', 30), \# Example from config  
            "active\_ea\_connections": len(ea\_connections\_map),  
            "connected\_pairs": list(ea\_connections\_map.keys()),  
            "details": {}  
        }  
        \# In a real scenario, you'd use ea\_status for detailed info  
        \# For this placeholder, we just list connected pairs  
        logger.debug("Collected EA connection status.")  
        return status\_summary

    def perform\_health\_check(self, ea\_connections\_map: Dict\[str, Any\]) \-\> Dict\[str, Any\]:  
        """Performs a comprehensive health check."""  
        overall\_status \= "healthy"  
          
        system\_health \= self.get\_system\_health()  
        process\_health \= self.get\_process\_health()  
        ea\_status \= self.get\_ea\_connection\_status(ea\_connections\_map)

        if system\_health.get('cpu\_percent', 0\) \> 90 or system\_health.get('memory\_percent', 0\) \> 90:  
            overall\_status \= "warning"  
            logger.warning("High CPU or Memory usage detected\!")  
          
        if ea\_status.get('active\_ea\_connections', 0\) \< ea\_status.get('total\_expected\_eas', 30\) \* 0.5:  
            overall\_status \= "warning"  
            logger.warning("Less than 50% of expected EAs are connected\!")

        return {  
            "overall\_status": overall\_status,  
            "system\_health": system\_health,  
            "process\_health": process\_health,  
            "ea\_connection\_status": ea\_status  
        }

if \_\_name\_\_ \== "\_\_main\_\_":  
    \# Example Usage:  
    \# Ensure logs directory exists for setup\_logging if not running via main server  
    log\_dir \= os.path.abspath(os.path.join(os.path.dirname(\_\_file\_\_), '..', '..', 'Logs'))  
    os.makedirs(log\_dir, exist\_ok=True)  
      
    \# Dummy logging config for standalone test  
    logging\_config\_test \= {  
        'level': 'DEBUG',  
        'file\_path': os.path.join(log\_dir, 'monitoring\_test.log'),  
        'format': '%(asctime)s \- %(name)s \- %(levelname)s \- %(message)s'  
    }  
    setup\_logging(logging\_config\_test)

    \# Dummy config for health monitor  
    monitor\_config \= {  
        'system': {'name': 'TestTradingSystem'},  
        'trading': {'total\_expected\_eas': 3} \# For EA connection status test  
    }  
      
    monitor \= HealthMonitor(monitor\_config)

    \# Simulate some dummy EA connections for testing  
    dummy\_ea\_connections \= {  
        "EURUSD": "socket\_obj\_1",  
        "GBPUSD": "socket\_obj\_2"  
    }

    health\_report \= monitor.perform\_health\_check(dummy\_ea\_connections)  
      
    print("\\n--- Health Report \---")  
    print(json.dumps(health\_report, indent=4))  
      
    logger.info("Health monitoring test complete.")

    \# Clean up  
    for f in os.listdir(log\_dir):  
        os.remove(os.path.join(log\_dir, f))  
    os.rmdir(log\_dir)  
    print(f"\\nCleaned up {log\_dir} directory.")

'@

\# requirements.txt \- Python dependencies  
$requirementsContent \= @'  
pyyaml\>=6.0.1  
websockets\>=10.3  
psutil\>=5.9.1  
watchdog\>=2.3.1 \# For config hot-reload  
aiofiles\>=22.1.0 \# For async file operations (if needed for CSV fallback)  
'@

\# \--- File Writing \---  
$files \= @{  
    (Join-Path $pythonSourcePath "trading\_server.py")  \= $tradingServerContent;  
    (Join-Path $pythonServicesPath "signal\_generator.py") \= $signalGeneratorContent;  
    (Join-Path $pythonServicesPath "message\_broker.py") \= $messageBrokerContent;  
    (Join-Path $pythonServicesPath "database\_manager.py") \= $databaseManagerContent;  
    (Join-Path $pythonUtilsPath "config\_manager.py") \= $configManagerContent;  
    (Join-Path $pythonUtilsPath "logger\_setup.py") \= $loggerSetupContent;  
    (Join-Path $pythonUtilsPath "monitoring.py") \= $monitoringContent;  
    (Join-Path $projectPath "requirements.txt")    \= $requirementsContent;  
}

foreach ($filePath in $files.Keys) {  
    $files\[$filePath\] | Out-File \-FilePath $filePath \-Encoding UTF8  
    $fileName \= Split-Path $filePath \-Leaf  
    Write-Host "✅ Created: $fileName" \-ForegroundColor Green  
}

\# \--- Success message and next steps \---  
Write-Host "\`n🎉 PYTHON SERVER FILES CREATED SUCCESSFULLY\!" \-ForegroundColor Green  
Write-Host "📂 Python Project Root: $projectPath" \-ForegroundColor Cyan  
Write-Host "📂 Python Source Code: $pythonSourcePath" \-ForegroundColor Cyan  
Write-Host "\`n🚀 Next steps for Python Setup:" \-ForegroundColor Yellow  
Write-Host "1. \*\*Install Python\*\*: If not already installed, download Python 3.8+ from python.org. Ensure it's added to your PATH." \-ForegroundColor White  
Write-Host "2. \*\*Create Virtual Environment (Recommended)\*\*: Open PowerShell/CMD, navigate to \`C:\\Users\\Richard Wilks\\TradingSystem\`." \-ForegroundColor White  
Write-Host "   Run: \`python \-m venv venv\`" \-ForegroundColor White  
Write-Host "   Then activate: \`.\\venv\\Scripts\\activate\` (Windows PowerShell/CMD) or \`source venv/bin/activate\` (Git Bash/Linux)" \-ForegroundColor White  
Write-Host "3. \*\*Install Dependencies\*\*: While in the virtual environment, run: \`pip install \-r requirements.txt\`" \-ForegroundColor White  
Write-Host "4. \*\*Crucial\*\*: You must ensure \`SocketBridge.dll\` from \*\*Part 2\*\* is correctly compiled and located in \`C:\\Users\\Richard Wilks\\AppData\\Roaming\\MetaQuotes\\Terminal\\F2262CFAFF47C27887389DAB2852351A\\MQL4\\Libraries\` before trying to run the EA." \-ForegroundColor Red  
Write-Host "5. Once Python dependencies are installed, you can proceed to \*\*Part 4: Configuration and Database Files\*\*." \-ForegroundColor Yellow

