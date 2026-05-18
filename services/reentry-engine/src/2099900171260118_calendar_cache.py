# doc_id: DOC-SERVICE-0215
"""
Calendar Context Cache — subscribes to eafix.calendar.signals Redis topic,
caches latest ActiveCalendarSignal per symbol with configurable TTL.

Used by TradeResultProcessor to resolve proximity_state and calendar_id
for hybrid_id composition (GAP-29, GAP-30).
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
import structlog

logger = structlog.get_logger(__name__)


class CalendarContextCache:
    """
    Caches latest ActiveCalendarSignal per symbol.

    Provides lookup methods for proximity_state and calendar_id.
    Falls back to conservative defaults when cache is stale.
    """

    def __init__(self, ttl_seconds: int = 120,
                 fallback_proximity: str = "POST_30M",
                 fallback_calendar_id: str = "NONE") -> None:
        self._ttl = timedelta(seconds=ttl_seconds)
        self._fallback_proximity = fallback_proximity
        self._fallback_calendar_id = fallback_calendar_id
        # symbol -> {signal_data, cached_at}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def update(self, signal: Dict[str, Any]) -> None:
        """Store or update a calendar signal in cache."""
        symbol = signal.get("symbol")
        if not symbol:
            return
        async with self._lock:
            self._cache[symbol] = {
                "signal": signal,
                "cached_at": datetime.now(timezone.utc),
            }
            logger.debug("Calendar cache updated", symbol=symbol,
                         calendar_id=signal.get("calendar_id"),
                         proximity_state=signal.get("proximity_state"))

    async def get_proximity_state(self, symbol: str) -> str:
        """
        Return cached proximity_state for symbol.
        Falls back to fallback_proximity if no valid cache entry.
        """
        entry = await self._get_valid_entry(symbol)
        if entry:
            return entry["signal"].get("proximity_state", self._fallback_proximity)
        logger.warning("Calendar cache miss — using fallback proximity",
                       symbol=symbol, fallback=self._fallback_proximity)
        return self._fallback_proximity

    async def get_calendar_id(self, symbol: str,
                              trade_time: Optional[datetime] = None) -> str:
        """
        Return cached calendar_id for symbol, optionally filtered by time window.
        Falls back to fallback_calendar_id if no valid cache entry.
        """
        entry = await self._get_valid_entry(symbol)
        if entry:
            signal = entry["signal"]
            # Optional: filter by time window proximity
            if trade_time is not None:
                event_time_str = signal.get("event_time")
                if event_time_str:
                    try:
                        event_time = datetime.fromisoformat(
                            event_time_str.replace("Z", "+00:00")
                        )
                        delta = abs((trade_time - event_time).total_seconds())
                        # Accept if within 2 hours of event
                        if delta > 7200:
                            logger.debug("Calendar entry outside time window",
                                         symbol=symbol, delta_seconds=delta)
                            return self._fallback_calendar_id
                    except (ValueError, TypeError):
                        pass
            return signal.get("calendar_id", self._fallback_calendar_id)

        logger.warning("Calendar cache miss — using fallback calendar_id",
                       symbol=symbol, fallback=self._fallback_calendar_id)
        return self._fallback_calendar_id

    async def _get_valid_entry(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return cache entry if present and not expired."""
        async with self._lock:
            entry = self._cache.get(symbol)
        if not entry:
            return None
        age = datetime.now(timezone.utc) - entry["cached_at"]
        if age > self._ttl:
            logger.debug("Calendar cache entry expired", symbol=symbol,
                         age_seconds=age.total_seconds())
            return None
        return entry
