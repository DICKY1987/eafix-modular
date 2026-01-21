# doc_id: DOC-SERVICE-0136
# DOC_ID: DOC-SERVICE-0032
"""
Calendar Ingestor Core Logic
Processes economic calendar events and generates ActiveCalendarSignal CSV files using contracts
"""

import asyncio
import csv
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import tempfile

import structlog
import redis.asyncio as redis

# Add contracts to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from contracts.models.csv_models import ActiveCalendarSignal
from .config import Settings
from .metrics import MetricsCollector

logger = structlog.get_logger(__name__)


class CalendarIngestor:
    """Core calendar processing logic with contract integration"""
    
    def __init__(self, settings: Settings, metrics: MetricsCollector):
        self.settings = settings
        self.metrics = metrics
        self.redis_client: Optional[redis.Redis] = None
        self.running = False
        self.active_signals: List[Dict[str, Any]] = []
        self.file_seq_counter = 1
        
        # Ensure output directory exists
        Path(self.settings.output_directory).mkdir(parents=True, exist_ok=True)
    
    async def start(self):
        """Start the calendar ingestor service"""
        try:
            # Connect to Redis
            try:
                self.redis_client = redis.from_url(self.settings.redis_url)
                await self.redis_client.ping()
                logger.info("Connected to Redis", redis_url=self.settings.redis_url)
            except Exception as e:
                logger.warning(
                    "Redis unavailable, continuing without pub/sub",
                    error=str(e),
                )
                self.redis_client = None
            
            # Start processing
            self.running = True
            logger.info("Calendar ingestor started successfully")
            
        except Exception as e:
            logger.error("Failed to start calendar ingestor", error=str(e))
            raise

    async def fetch_events(self) -> List[Dict[str, Any]]:
        """Fetch calendar events from configured sources (placeholder)."""
        return []
    
    async def stop(self):
        """Stop the calendar ingestor service"""
        self.running = False
        
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
        
        logger.info("Calendar ingestor stopped")
    
    def _determine_calendar_id(self, event: Dict[str, Any]) -> str:
        """Determine calendar ID (CAL8 or CAL5) based on event characteristics"""
        event_name = event.get("name", "").lower()
        currency = event.get("currency", "USD").upper()
        impact = event.get("impact", "MEDIUM").upper()
        
        # Check for high impact events (CAL8)
        for high_event in self.settings.high_impact_events:
            if high_event.lower() in event_name:
                # Create CAL8 identifier
                event_code = self._get_event_code(high_event)
                return f"CAL8_{currency}_{event_code}_H"
        
        # Check for medium impact events (CAL5) 
        for med_event in self.settings.medium_impact_events:
            if med_event.lower() in event_name:
                event_code = self._get_event_code(med_event)
                return f"CAL5_{event_code}"
        
        # Default based on impact level
        if impact == "HIGH":
            return f"CAL8_{currency}_MISC_H"
        else:
            return f"CAL5_MISC"
    
    def _get_event_code(self, event_name: str) -> str:
        """Convert event name to standard code"""
        code_mapping = {
            "Non-Farm Payrolls": "NFP",
            "FOMC Meeting": "FOMC", 
            "ECB Meeting": "ECB",
            "BOE Meeting": "BOE",
            "BOJ Meeting": "BOJ",
            "Gross Domestic Product": "GDP",
            "GDP": "GDP",
            "Consumer Price Index": "CPI", 
            "CPI": "CPI",
            "Producer Price Index": "PPI",
            "PMI": "PMI",
            "Retail Sales": "RET",
            "Unemployment Rate": "UNE",
            "Industrial Production": "IND",
            "Consumer Confidence": "CONF"
        }
        
        return code_mapping.get(event_name, "MISC")
    
    def _determine_proximity_state(self, event_time: datetime, current_time: datetime) -> str:
        """Determine proximity state based on time difference"""
        time_diff_minutes = (event_time - current_time).total_seconds() / 60
        
        if -self.settings.anticipation_window_minutes <= time_diff_minutes <= 0:
            return "PRE_1H"  # Anticipation window
        elif 0 <= time_diff_minutes <= self.settings.event_window_minutes:
            return "AT_EVENT"  # Event happening now
        elif self.settings.event_window_minutes < time_diff_minutes <= self.settings.stabilization_window_minutes:
            return "POST_30M"  # Stabilization period
        else:
            return "FAR"  # Too far from event
    
    def _determine_direction_bias(self, event: Dict[str, Any]) -> str:
        """Determine expected market direction bias"""
        # This is a simplified implementation - in practice would use more sophisticated logic
        event_name = event.get("name", "").lower()
        impact = event.get("impact", "MEDIUM").upper()
        currency = event.get("currency", "USD").upper()
        
        # Simple heuristics for demonstration
        if "employment" in event_name or "nfp" in event_name:
            return "BULLISH" if impact == "HIGH" else "NEUTRAL"
        elif "inflation" in event_name or "cpi" in event_name:
            return "BEARISH" if impact == "HIGH" else "NEUTRAL"
        elif "gdp" in event_name:
            return "BULLISH" if impact == "HIGH" else "NEUTRAL"
        else:
            return "NEUTRAL"
    
    def _calculate_confidence_score(self, event: Dict[str, Any], proximity_state: str) -> float:
        """Calculate signal confidence score (0.0-1.0)"""
        base_confidence = 0.5
        
        # Adjust based on impact level
        impact = event.get("impact", "MEDIUM").upper()
        if impact == "HIGH":
            base_confidence += 0.3
        elif impact == "MEDIUM":
            base_confidence += 0.1
        
        # Adjust based on proximity
        proximity_adjustment = {
            "PRE_1H": 0.1,    # Anticipation signals are less certain
            "AT_EVENT": 0.2,   # Event happening now, highest confidence
            "POST_30M": 0.15,  # Post-event, moderate confidence
            "FAR": -0.2        # Too far, low confidence
        }
        
        base_confidence += proximity_adjustment.get(proximity_state, 0)
        
        # Ensure within bounds
        return max(0.0, min(1.0, base_confidence))
    
    def _compute_row_checksum(self, row_data: Dict[str, Any]) -> str:
        """Compute SHA-256 checksum for CSV row (excluding checksum column)"""
        # Create ordered string of all values except checksum
        ordered_values = []
        for key in sorted(row_data.keys()):
            if key != 'checksum_sha256':
                value = row_data[key]
                ordered_values.append(str(value))
        
        # Join values and compute hash
        row_string = '|'.join(ordered_values)
        return hashlib.sha256(row_string.encode('utf-8')).hexdigest()
    
    async def process_calendar_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single calendar event and generate signals"""
        try:
            current_time = datetime.now(timezone.utc)
            event_time = datetime.fromisoformat(event.get("datetime", current_time.isoformat()))
            
            # Determine calendar characteristics
            calendar_id = self._determine_calendar_id(event)
            proximity_state = self._determine_proximity_state(event_time, current_time)
            direction_bias = self._determine_direction_bias(event)
            
            # Skip if too far from event
            if proximity_state == "FAR":
                logger.debug("Event too far, skipping", event_name=event.get("name"))
                return {"status": "skipped", "reason": "too_far_from_event"}
            
            # Generate signals for each currency pair
            generated_signals = []
            
            for symbol in self.settings.currency_pairs:
                # Check if this symbol is affected by the event currency
                event_currency = event.get("currency", "USD")
                if event_currency not in symbol:
                    continue  # Skip unrelated pairs
                
                # Determine if this is an anticipation event
                anticipation_event = proximity_state == "PRE_1H"
                
                # Calculate confidence score
                confidence_score = self._calculate_confidence_score(event, proximity_state)
                
                # Create signal data
                signal_data = {
                    "file_seq": self.file_seq_counter,
                    "timestamp": current_time.isoformat().replace('+00:00', 'Z'),
                    "calendar_id": calendar_id,
                    "symbol": symbol,
                    "impact_level": event.get("impact", "MEDIUM").upper(),
                    "proximity_state": proximity_state,
                    "anticipation_event": anticipation_event,
                    "direction_bias": direction_bias,
                    "confidence_score": confidence_score
                }
                
                # Compute checksum
                signal_data["checksum_sha256"] = self._compute_row_checksum(signal_data)
                
                # Validate using contract model
                try:
                    validated_signal = ActiveCalendarSignal(**signal_data)
                    generated_signals.append(signal_data)
                    self.file_seq_counter += 1
                    
                    logger.info(
                        "Generated calendar signal",
                        symbol=symbol,
                        calendar_id=calendar_id,
                        proximity_state=proximity_state,
                        confidence_score=confidence_score
                    )
                    
                except Exception as validation_error:
                    logger.error(
                        "Signal validation failed", 
                        signal=signal_data,
                        error=str(validation_error)
                    )
                    continue
            
            # Add to active signals and write to CSV
            if generated_signals:
                self.active_signals.extend(generated_signals)
                await self._write_signals_to_csv(generated_signals)
                
                # Publish event to Redis
                if self.redis_client:
                    await self._publish_calendar_event(event, generated_signals)
            
            return {
                "status": "success",
                "signals_generated": len(generated_signals),
                "calendar_id": calendar_id,
                "proximity_state": proximity_state
            }
            
        except Exception as e:
            logger.error("Failed to process calendar event", event=event, error=str(e))
            raise
    
    async def _write_signals_to_csv(self, signals: List[Dict[str, Any]]):
        """Write signals to CSV file using atomic write policy"""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"active_calendar_signals_{timestamp}.csv"
            file_path = Path(self.settings.output_directory) / filename
            temp_path = file_path.with_suffix('.csv.tmp')
            
            # Write to temporary file
            with open(temp_path, 'w', newline='', encoding='utf-8') as f:
                if signals:
                    # Get headers from first signal
                    headers = list(signals[0].keys())
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(signals)
                    
                    # Force write to disk
                    f.flush()
                    os.fsync(f.fileno())
            
            # Atomic rename
            temp_path.rename(file_path)
            
            logger.info(
                "Wrote calendar signals to CSV",
                filename=filename,
                signal_count=len(signals)
            )
            
            # Update metrics
            self.metrics.increment_counter("calendar_signals_written", len(signals))
            
        except Exception as e:
            logger.error("Failed to write signals to CSV", error=str(e))
            raise
    
    async def _publish_calendar_event(self, event: Dict[str, Any], signals: List[Dict[str, Any]]):
        """Publish calendar event to Redis"""
        try:
            event_data = {
                "event_type": "CalendarEvent",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_event": event,
                "generated_signals": len(signals),
                "calendar_signals": signals
            }
            
            # Publish to calendar events channel
            await self.redis_client.publish("calendar_events", str(event_data))
            
            logger.debug("Published calendar event to Redis", signal_count=len(signals))
            
        except Exception as e:
            logger.warning("Failed to publish calendar event to Redis", error=str(e))
    
    async def get_active_signals(self) -> List[Dict[str, Any]]:
        """Get current active calendar signals"""
        # Filter signals that are still relevant (within time windows)
        current_time = datetime.now(timezone.utc)
        active_signals = []
        
        for signal in self.active_signals:
            signal_time = datetime.fromisoformat(signal["timestamp"].replace('Z', '+00:00'))
            time_diff_minutes = (current_time - signal_time).total_seconds() / 60
            
            # Keep signals that are still within relevance window
            if time_diff_minutes <= max(
                self.settings.anticipation_window_minutes,
                self.settings.stabilization_window_minutes
            ):
                active_signals.append(signal)
        
        return active_signals
