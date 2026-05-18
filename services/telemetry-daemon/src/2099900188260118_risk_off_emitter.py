# doc_id: DOC-SERVICE-0221
"""
Risk-Off Emitter — publishes eafix.system.risk_off when health degrades.

Subscribes to: health_report events (from telemetry-daemon health aggregator)
Emits: eafix.system.risk_off (triggers risk-off posture in signal-generator + flow-orchestrator)

Closes GAP-51.
"""
from datetime import datetime, timezone
from typing import Any, Dict
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Health states that trigger risk-off
_RISK_OFF_STATES = {"degraded", "unhealthy", "unknown", "error"}


class RiskOffEmitter:
    """Emits risk-off event when system health degrades."""

    def __init__(self, emit_fn) -> None:
        """
        Args:
            emit_fn: Callable(event_type, data) for emitting events
        """
        self._emit = emit_fn
        self._risk_off_active: bool = False

    def handle_health_report(self, report: Dict[str, Any]) -> None:
        """
        Process a HealthReport. Emit risk-off if status is degraded/unhealthy.

        Args:
            report: Dict with at least {"status": "healthy"|"degraded"|"unhealthy", ...}
        """
        status = str(report.get("status", "unknown")).lower()

        if status in _RISK_OFF_STATES and not self._risk_off_active:
            self._risk_off_active = True
            event = {
                "event_type": "SystemRiskOff",
                "schema_version": "1.0",
                "status": status,
                "source_report": report.get("source", "telemetry-daemon"),
                "reason": f"Health status degraded to: {status}",
                "triggered_at": datetime.now(timezone.utc).isoformat(),
            }
            self._emit("eafix.system.risk_off", event)
            logger.warning("Risk-off event emitted",
                           status=status,
                           source=report.get("source"))

        elif status == "healthy" and self._risk_off_active:
            # Recovery — log but don't auto-reset (manual intervention required)
            logger.info("System health restored but risk-off NOT auto-reset",
                        note="Manual intervention required to re-enable signals")
