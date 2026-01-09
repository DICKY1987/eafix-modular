# DOC_ID: DOC-SERVICE-0042
"""
Core data ingestion logic for the Data Ingestor service
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid

import redis.asyncio as redis
import structlog
from pydantic import ValidationError

from .config import Settings
from .models import PriceTick
from .adapters.mt4_adapter import MT4Adapter
from .adapters.csv_adapter import CSVAdapter
from .adapters.socket_adapter import SocketAdapter


logger = structlog.get_logger(__name__)


class DataIngestor:
    """Core data ingestion service"""
    
    def __init__(self, settings: Settings, metrics=None):
        self.settings = settings
        self.metrics = metrics
        self.redis_client: Optional[redis.Redis] = None
        self.running = False
        
        # Initialize adapters
        self.adapters = []
        
        if self.settings.enable_dde:
            self.adapters.append(MT4Adapter(settings))
            
        if self.settings.enable_csv:
            self.adapters.append(CSVAdapter(settings))
            
        if self.settings.enable_socket:
            self.adapters.append(SocketAdapter(settings))
    
    async def start(self):
        """Start the data ingestion service"""
        logger.info("Starting data ingestor", adapters=len(self.adapters))
        
        # Connect to Redis
        self.redis_client = redis.from_url(self.settings.redis_url)
        await self.redis_client.ping()
        logger.info("Connected to Redis", url=self.settings.redis_url)
        
        # Start all adapters
        for adapter in self.adapters:
            await adapter.start()
        
        self.running = True
        
        # Start processing task
        asyncio.create_task(self._process_data())
        
    async def stop(self):
        """Stop the data ingestion service"""
        logger.info("Stopping data ingestor")
        self.running = False
        
        # Stop all adapters
        for adapter in self.adapters:
            await adapter.stop()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
    
    async def _process_data(self):
        """Main data processing loop"""
        logger.info("Starting data processing loop")
        
        while self.running:
            try:
                # Process data from all adapters
                for adapter in self.adapters:
                    price_data = await adapter.get_price_data()
                    if price_data:
                        for data in price_data:
                            await self.process_price_tick(data)
                
                # Brief pause to prevent CPU spinning
                await asyncio.sleep(0.01)  # 10ms
                
            except Exception as e:
                logger.error("Error in data processing loop", error=str(e))
                await asyncio.sleep(1.0)  # Back off on error
    
    async def process_price_tick(self, raw_data: Dict[str, Any]):
        """Process and publish a single price tick"""
        try:
            # Normalize the data
            normalized_data = await self._normalize_price_data(raw_data)
            
            # Validate against schema
            price_tick = PriceTick(**normalized_data)
            
            # Add metadata
            price_tick_data = {
                **price_tick.dict(),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "source": raw_data.get("source", "unknown")
            }
            
            # Publish to Redis
            await self._publish_price_tick(price_tick_data)
            
            # Update metrics
            if self.metrics:
                self.metrics.increment_tick_count(price_tick.symbol)
                
            logger.debug("Processed price tick", 
                        symbol=price_tick.symbol, 
                        bid=price_tick.bid, 
                        ask=price_tick.ask)
                        
        except ValidationError as e:
            logger.warning("Invalid price data", error=str(e), data=raw_data)
            if self.metrics:
                self.metrics.increment_error_count("validation_error")
                
        except Exception as e:
            logger.error("Failed to process price tick", error=str(e), data=raw_data)
            if self.metrics:
                self.metrics.increment_error_count("processing_error")
    
    async def _normalize_price_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize price data from different sources"""
        
        # Common normalization logic
        normalized = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": str(raw_data.get("symbol", "")).upper(),
            "bid": float(raw_data.get("bid", 0)),
            "ask": float(raw_data.get("ask", 0))
        }
        
        # Add volume if available
        if "volume" in raw_data:
            normalized["volume"] = int(raw_data["volume"])
        
        # Validate basic requirements
        if not normalized["symbol"] or len(normalized["symbol"]) != 6:
            raise ValueError(f"Invalid symbol: {normalized['symbol']}")
            
        if normalized["bid"] <= 0 or normalized["ask"] <= 0:
            raise ValueError(f"Invalid prices: bid={normalized['bid']}, ask={normalized['ask']}")
            
        if normalized["ask"] <= normalized["bid"]:
            raise ValueError(f"Ask price must be greater than bid: {normalized['ask']} <= {normalized['bid']}")
        
        # Calculate spread and validate
        spread_pips = (normalized["ask"] - normalized["bid"]) * 10000  # Assuming 4-decimal pricing
        if spread_pips < self.settings.min_spread_pips:
            raise ValueError(f"Spread too small: {spread_pips} pips")
            
        if spread_pips > self.settings.max_spread_pips:
            raise ValueError(f"Spread too large: {spread_pips} pips")
        
        return normalized
    
    async def _publish_price_tick(self, price_tick_data: Dict[str, Any]):
        """Publish price tick to Redis channel"""
        try:
            message = json.dumps(price_tick_data)
            await self.redis_client.publish(self.settings.redis_channel, message)
            
            logger.debug("Published price tick", 
                        channel=self.settings.redis_channel,
                        symbol=price_tick_data["symbol"])
                        
        except Exception as e:
            logger.error("Failed to publish price tick", error=str(e))
            raise