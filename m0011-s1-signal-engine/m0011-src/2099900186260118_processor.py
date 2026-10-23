# doc_id: DOC-SERVICE-0209
"""
Signal Processor — evaluates FeatureFrame, emits Signal@1.0 or SignalSuppressed.

Subscribes to:
  eafix.calendar.signals     -> ActiveCalendarSignal
  eafix.indicators.computed  -> IndicatorVector
  eafix.system.risk_off      -> risk-off posture flag

Emits to:
  eafix.signals.generated -> Signal@1.0 | SignalSuppressed

Closes GAP-06.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Proximity states that suppress signals when combined with low-impact calendar
_SUPPRESSING_PROXIMITIES = {"PRE_1H"}
# Calendar ID prefixes considered low impact
_LOW_IMPACT_PREFIXES = ("CAL5",)


class SignalProcessor:
    """Evaluates calendar signal + indicator vector -> Signal or suppression."""

    def __init__(self, settings) -> None:
        self.settings = settings
        # Cache: symbol -> latest ActiveCalendarSignal dict
        self._calendar_cache: Dict[str, Dict[str, Any]] = {}
        # Cache: symbol -> latest IndicatorVector dict
        self._indicator_cache: Dict[str, Dict[str, Any]] = {}
        # Recent signals for dedup: dedup_key -> datetime
        self._recent_signals: Dict[str, datetime] = {}
        self._risk_off: bool = False

    def on_calendar_signal(self, data: Dict[str, Any]) -> None:
        """Cache incoming ActiveCalendarSignal keyed by symbol."""
        symbol = data.get("symbol")
        if symbol:
            self._calendar_cache[symbol] = {**data, "_cached_at": datetime.now(timezone.utc)}

    def on_indicator_vector(self, data: Dict[str, Any]) -> None:
        """Cache incoming IndicatorVector keyed by symbol."""
        symbol = data.get("symbol")
        if symbol:
            self._indicator_cache[symbol] = {**data, "_cached_at": datetime.now(timezone.utc)}

    def on_risk_off(self, data: Dict[str, Any]) -> None:
        """Activate risk-off flag."""
        self._risk_off = True
        logger.warning("Risk-off posture activated", reason=data.get("reason", "unknown"))

    def evaluate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Evaluate latest FeatureFrame for symbol.
        Returns Signal dict, SignalSuppressed dict, or None if insufficient data.
        """
        cal = self._calendar_cache.get(symbol)
        if not cal:
            return None  # No calendar context available yet

        # Risk-off suppression
        if self._risk_off:
            return self._suppressed(cal, "RISK_OFF_POSTURE")

        proximity_state = cal.get("proximity_state", "POST_30M")
        calendar_id = cal.get("calendar_id", "NONE")
        confidence = float(cal.get("confidence_score", 0.0))
        direction_bias = cal.get("direction_bias", "NEUTRAL")

        # Suppression: PRE_1H + low-impact calendar (FR-S2)
        if proximity_state in _SUPPRESSING_PROXIMITIES:
            if any(calendar_id.startswith(p) for p in _LOW_IMPACT_PREFIXES):
                return self._suppressed(cal, f"LOW_IMPACT_PRE_EVENT:{calendar_id}")

        # Confidence gate
        if confidence < self.settings.min_confidence_threshold:
            return self._suppressed(cal, f"LOW_CONFIDENCE:{confidence:.2f}")

        # Map direction
        direction_map = {"BULLISH": "LONG", "BEARISH": "SHORT", "NEUTRAL": "LONG"}
        direction = direction_map.get(direction_bias, "LONG")

        # Dedup: suppress if same calendar+symbol+direction seen within window
        dedup_key = f"{symbol}:{calendar_id}:{direction}"
        window_seconds = getattr(self.settings, "suppression_window_seconds", 300)
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        if dedup_key in self._recent_signals and self._recent_signals[dedup_key] > cutoff:
            return self._suppressed(cal, "DUPLICATE_WITHIN_WINDOW")

        # Compose Signal@1.0
        correlation_id = str(uuid.uuid4())
        ind = self._indicator_cache.get(symbol, {})
        signal: Dict[str, Any] = {
            "event_type": "Signal",
            "schema_version": "1.0",
            "correlation_id": correlation_id,
            "calendar_id": calendar_id,
            "symbol": symbol,
            "direction": direction,
            "confidence": confidence,
            "proximity_state": proximity_state,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "indicator_snapshot": {k: v for k, v in ind.items() if not k.startswith("_")},
        }

        # Record dedup
        self._recent_signals[dedup_key] = datetime.now(timezone.utc)
        self._prune_recent_signals(cutoff)

        logger.info("Signal emitted",
                    correlation_id=correlation_id,
                    symbol=symbol,
                    direction=direction,
                    confidence=confidence,
                    calendar_id=calendar_id)
        return signal

    def _suppressed(self, cal: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """Build SignalSuppressed event."""
        logger.info("Signal suppressed", reason=reason, symbol=cal.get("symbol"))
        return {
            "event_type": "SignalSuppressed",
            "schema_version": "1.0",
            "symbol": cal.get("symbol"),
            "calendar_id": cal.get("calendar_id"),
            "reason": reason,
            "suppressed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _prune_recent_signals(self, cutoff: datetime) -> None:
        """Remove expired dedup entries."""
        expired = [k for k, v in self._recent_signals.items() if v <= cutoff]
        for k in expired:
            del self._recent_signals[k]
