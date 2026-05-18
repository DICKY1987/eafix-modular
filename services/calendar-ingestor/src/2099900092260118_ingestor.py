# doc_id: DOC-SERVICE-0136
# DOC_ID: DOC-SERVICE-0032
"""
Calendar Ingestor Core Logic
Processes economic calendar events and generates ActiveCalendarSignal CSV files using contracts
"""

import asyncio
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import tempfile
from zoneinfo import ZoneInfo

import structlog

try:
    import redis.asyncio as redis
except ImportError:  # pragma: no cover - exercised only in minimal test envs
    class _MissingRedis:
        Redis = Any

        @staticmethod
        def from_url(*args, **kwargs):
            raise RuntimeError("redis package is not installed")

    redis = _MissingRedis()

# Add contracts to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from contracts.models.csv_models import ActiveCalendarSignal
from .config import Settings
from .metrics import MetricsCollector

logger = structlog.get_logger(__name__)

ACTIVE_SIGNAL_FIELDS = [
    "file_seq",
    "checksum_sha256",
    "timestamp",
    "calendar_id",
    "symbol",
    "impact_level",
    "proximity_state",
    "anticipation_event",
    "direction_bias",
    "confidence_score",
]


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
        """Fetch and normalize calendar events from the configured CSV source."""
        source_path = getattr(self.settings, "calendar_source_path", None)
        if not source_path:
            logger.info("No calendar source path configured")
            return []

        path = Path(source_path)
        if not path.exists():
            logger.warning("Calendar source path does not exist", source_path=str(path))
            return []

        events: List[Dict[str, Any]] = []
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row_number, row in enumerate(reader, start=2):
                try:
                    events.append(self._normalize_event(row))
                except Exception as exc:
                    logger.warning(
                        "Skipping invalid calendar source row",
                        row_number=row_number,
                        error=str(exc),
                    )

        logger.info("Fetched calendar events", count=len(events), source_path=str(path))
        return events
    
    async def stop(self):
        """Stop the calendar ingestor service"""
        self.running = False
        
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
        
        logger.info("Calendar ingestor stopped")

    def _normalize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw/vendor calendar rows into CalendarEvent@1.0 shape."""
        title = (
            event.get("title")
            or event.get("name")
            or event.get("event")
            or event.get("Event")
            or event.get("Title")
        )
        if not title:
            raise ValueError("Calendar event title/name is required")

        currency = (
            event.get("currency")
            or event.get("Currency")
            or event.get("country")
            or event.get("Country")
            or "USD"
        )
        currency = str(currency).strip().upper()
        if len(currency) != 3:
            raise ValueError(f"Currency must be a 3-letter code: {currency}")

        event_time = self._parse_event_time(event)
        impact = self._normalize_impact(
            event.get("impact") or event.get("Impact") or event.get("importance") or event.get("Importance")
        )

        event_id = event.get("id") or event.get("event_id")
        if not event_id:
            stable_key = f"{event_time.isoformat()}|{currency}|{title}"
            event_id = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:16]

        event_time_text = event_time.isoformat().replace("+00:00", "Z")
        return {
            "id": str(event_id),
            "start_ts": event_time_text,
            "datetime": event_time_text,
            "title": str(title).strip(),
            "name": str(title).strip(),
            "currency": currency,
            "impact": impact,
            "forecast": event.get("forecast") or event.get("Forecast"),
            "actual": event.get("actual") or event.get("Actual"),
            "previous": event.get("previous") or event.get("Previous"),
            "source": event.get("source") or event.get("Source") or self.settings.data_source,
            "ingested_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    def _parse_event_time(self, event: Dict[str, Any]) -> datetime:
        """Parse event datetime fields and normalize to UTC."""
        raw_datetime = (
            event.get("start_ts")
            or event.get("datetime")
            or event.get("timestamp")
            or event.get("event_time_utc")
            or event.get("DateTime")
        )

        if raw_datetime:
            parsed = datetime.fromisoformat(str(raw_datetime).replace("Z", "+00:00"))
        else:
            raw_date = event.get("raw_date") or event.get("date") or event.get("Date") or event.get("day")
            raw_time = event.get("raw_time") or event.get("time") or event.get("Time") or event.get("hour")
            if not raw_date or not raw_time:
                raise ValueError("Calendar event requires start_ts/datetime or date+time fields")
            parsed = datetime.fromisoformat(f"{raw_date} {raw_time}")

        if parsed.tzinfo is None:
            try:
                source_tz = ZoneInfo(self.settings.source_timezone)
            except Exception:
                source_tz = timezone.utc
            parsed = parsed.replace(tzinfo=source_tz)

        return parsed.astimezone(timezone.utc)

    def _normalize_impact(self, impact: Any) -> str:
        """Normalize vendor impact labels into HIGH/MEDIUM/LOW."""
        value = str(impact or "MEDIUM").strip().upper()
        if value in {"H", "HIGH", "3", "RED"}:
            return "HIGH"
        if value in {"M", "MED", "MEDIUM", "2", "ORANGE"}:
            return "MEDIUM"
        return "LOW"
    
    def _determine_calendar_id(self, event: Dict[str, Any]) -> str:
        """Determine calendar ID (CAL8 or CAL5) based on event characteristics"""
        event_name = (event.get("name") or event.get("title") or "").lower()
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
        
        if 0 < time_diff_minutes <= self.settings.anticipation_window_minutes:
            return "PRE_1H"  # Pre-event anticipation window
        elif -self.settings.event_window_minutes <= time_diff_minutes <= self.settings.event_window_minutes:
            return "AT_EVENT"  # Event happening now
        elif -self.settings.stabilization_window_minutes <= time_diff_minutes < -self.settings.event_window_minutes:
            return "POST_30M"  # Stabilization period
        else:
            return "FAR"  # Too far from event
    
    def _determine_direction_bias(self, event: Dict[str, Any]) -> str:
        """Determine expected market direction bias"""
        # This is a simplified implementation - in practice would use more sophisticated logic
        event_name = (event.get("name") or event.get("title") or "").lower()
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
            event = self._normalize_event(event)
            current_time = datetime.now(timezone.utc)
            event_time = datetime.fromisoformat(event["start_ts"].replace("Z", "+00:00"))
            
            # Determine calendar characteristics
            calendar_id = self._determine_calendar_id(event)
            proximity_state = self._determine_proximity_state(event_time, current_time)
            direction_bias = self._determine_direction_bias(event)
            
            # Skip if too far from event
            if proximity_state == "FAR":
                logger.debug("Event too far, skipping", event_name=event.get("title"))
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
                "proximity_state": proximity_state,
                "signals": generated_signals,
                "event": event,
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
                    writer = csv.DictWriter(f, fieldnames=ACTIVE_SIGNAL_FIELDS)
                    writer.writeheader()
                    writer.writerows(
                        {field: signal.get(field) for field in ACTIVE_SIGNAL_FIELDS}
                        for signal in signals
                    )
                    
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
        """Publish normalized calendar event and active signals to Redis topics."""
        try:
            event_data = {
                "event_type": "CalendarEvent",
                "schema_version": "1.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "generated_signals": len(signals),
            }
            
            await self.redis_client.publish(
                self.settings.calendar_events_topic,
                json.dumps(event_data),
            )

            for signal in signals:
                signal_data = {
                    "event_type": "ActiveCalendarSignal",
                    "schema_version": "1.0",
                    **signal,
                }
                await self.redis_client.publish(
                    self.settings.calendar_signals_topic,
                    json.dumps(signal_data),
                )
            
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
