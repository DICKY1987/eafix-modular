# doc_id: DOC-SERVICE-0218
"""
Flow Coordinator — orchestrates the full reentry loop.

Subscribes to:
  eafix.reentry.decisions  -> ReentryDecision
  eafix.system.risk_off    -> risk-off flag

On R1/R2 action:
  - Check velocity limit (Redis counter with per-hour TTL)
  - Check loop idempotency (Redis SET NX on hybrid_id)
  - Enforce max chain depth
  - Emit new signal event to risk-manager pipeline

On NO_REENTRY/HOLD:
  - Emit terminal status event

Closes GAP-38, GAP-39, GAP-40.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class FlowCoordinator:
    """Orchestrates reentry dispatch with velocity and idempotency controls."""

    def __init__(self, settings, emit_fn) -> None:
        """
        Args:
            settings: Settings instance with max_chain_depth, velocity_limit, etc.
            emit_fn: Callable(event_type, data) for emitting events.
        """
        self.settings = settings
        self._emit = emit_fn
        self._redis = None  # Set via set_redis()
        self._risk_off: bool = False
        # In-memory fallbacks when Redis unavailable
        self._velocity_counts: Dict[str, int] = {}
        self._idem_keys: set = set()

    def set_redis(self, redis_client) -> None:
        """Wire Redis client after construction."""
        self._redis = redis_client

    async def handle_reentry_decision(self, decision: Dict[str, Any]) -> None:
        """Process a ReentryDecision event."""
        reentry_action = decision.get("reentry_action", "NO_REENTRY")
        symbol = decision.get("symbol", "UNKNOWN")
        hybrid_id = decision.get("hybrid_id", "")
        generation = int(decision.get("generation", 1))

        logger.info("FlowCoordinator received decision",
                    action=reentry_action, symbol=symbol, hybrid_id=hybrid_id)

        if reentry_action not in ("R1", "R2"):
            # Terminal — emit status event
            self._emit("eafix.orchestrator.status", {
                "event_type": "OrchestratorStatus",
                "symbol": symbol,
                "hybrid_id": hybrid_id,
                "reentry_action": reentry_action,
                "terminal": True,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            })
            return

        # Risk-off gate
        if self._risk_off:
            logger.warning("Reentry halted — risk-off posture", symbol=symbol)
            self._emit("eafix.orchestrator.status", {
                "event_type": "OrchestratorStatus",
                "symbol": symbol,
                "hybrid_id": hybrid_id,
                "reentry_action": "HALTED_RISK_OFF",
                "terminal": True,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            })
            return

        # Chain depth check
        if generation >= self.settings.max_chain_depth:
            logger.info("Chain depth limit reached", symbol=symbol, generation=generation)
            self._emit("eafix.orchestrator.status", {
                "event_type": "OrchestratorStatus",
                "symbol": symbol,
                "hybrid_id": hybrid_id,
                "reentry_action": "CHAIN_DEPTH_LIMIT",
                "terminal": True,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            })
            return

        # Velocity check
        if not await self._check_velocity(symbol):
            logger.warning("Velocity limit reached", symbol=symbol)
            self._emit("eafix.orchestrator.status", {
                "event_type": "OrchestratorStatus",
                "symbol": symbol,
                "hybrid_id": hybrid_id,
                "reentry_action": "VELOCITY_LIMITED",
                "terminal": True,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            })
            return

        # Idempotency check
        if not await self._check_idempotency(hybrid_id):
            logger.warning("Duplicate hybrid_id — idempotency guard",
                           symbol=symbol, hybrid_id=hybrid_id)
            return  # Silently drop duplicate

        # Dispatch new signal into pipeline
        correlation_id = decision.get("correlation_id") or decision.get("trade_id", "")
        calendar_id = decision.get("calendar_id", "NONE")
        direction = decision.get("direction", "LONG")
        confidence = float(decision.get("confidence", 0.7))

        new_signal = {
            "event_type": "Signal",
            "schema_version": "1.0",
            "correlation_id": correlation_id,
            "calendar_id": calendar_id,
            "symbol": symbol,
            "direction": direction,
            "confidence": confidence,
            "proximity_state": decision.get("proximity_state", "POST_30M"),
            "reentry_generation": generation + 1,
            "parent_hybrid_id": hybrid_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        self._emit("eafix.signals.generated", new_signal)
        logger.info("Reentry signal dispatched",
                    symbol=symbol, generation=generation + 1, hybrid_id=hybrid_id)

    def on_risk_off(self, data: Dict[str, Any]) -> None:
        """Activate risk-off flag."""
        self._risk_off = True
        logger.warning("FlowCoordinator: risk-off activated", reason=data.get("reason"))

    async def _check_velocity(self, symbol: str) -> bool:
        """Return True if within velocity limit. Increments counter."""
        limit = self.settings.velocity_limit_per_symbol_per_hour
        redis_key = f"flow:velocity:{symbol}"

        if self._redis:
            try:
                count = await self._redis.incr(redis_key)
                if count == 1:
                    await self._redis.expire(redis_key, 3600)  # 1-hour window
                return count <= limit
            except Exception as exc:
                logger.warning("Velocity Redis error", error=str(exc))

        # Fallback in-memory
        count = self._velocity_counts.get(symbol, 0) + 1
        self._velocity_counts[symbol] = count
        return count <= limit

    async def _check_idempotency(self, hybrid_id: str) -> bool:
        """Return True if hybrid_id not seen recently (SET NX). False if duplicate."""
        if not hybrid_id:
            return True
        ttl = self.settings.loop_idempotency_ttl_seconds
        redis_key = f"flow:idem:{hybrid_id}"

        if self._redis:
            try:
                result = await self._redis.set(redis_key, "1", nx=True, ex=ttl)
                return result is not None  # None = key existed
            except Exception as exc:
                logger.warning("Idempotency Redis error", error=str(exc))

        # Fallback in-memory
        if hybrid_id in self._idem_keys:
            return False
        self._idem_keys.add(hybrid_id)
        return True
