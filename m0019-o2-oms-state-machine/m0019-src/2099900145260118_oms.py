# doc_id: DOC-SERVICE-0212
"""
OMS State Machine — tracks order lifecycle PENDING->OPEN->PARTIAL->CLOSED.

Persists to Redis HASH: oms:order:{client_order_id} with 24h TTL.
Falls back to in-memory if Redis unavailable.
Closes GAP-22, GAP-23.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class OrderState(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    CLOSED = "CLOSED"
    TIMEOUT = "TIMEOUT"
    REJECTED = "REJECTED"


_VALID_TRANSITIONS = {
    OrderState.PENDING: {OrderState.OPEN, OrderState.REJECTED, OrderState.TIMEOUT},
    OrderState.OPEN: {OrderState.PARTIAL, OrderState.CLOSED},
    OrderState.PARTIAL: {OrderState.CLOSED},
    OrderState.CLOSED: set(),
    OrderState.TIMEOUT: set(),
    OrderState.REJECTED: set(),
}


class OMSStateMachine:
    """Tracks order state machine with Redis persistence."""

    def __init__(self, redis_client=None) -> None:
        self._redis = redis_client
        self._orders: Dict[str, Dict[str, Any]] = {}

    async def create_order(self, client_order_id: str,
                           order_data: Dict[str, Any]) -> None:
        """Create a new order in PENDING state."""
        record = {
            "client_order_id": client_order_id,
            "state": OrderState.PENDING.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **{k: str(v) for k, v in order_data.items()},
        }
        await self._persist(client_order_id, record)
        logger.info("OMS order created", client_order_id=client_order_id)

    async def transition(self, client_order_id: str,
                         new_state: OrderState,
                         update: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Transition order to new state. Returns updated record or None."""
        record = await self._load(client_order_id)
        if not record:
            logger.warning("OMS order not found", client_order_id=client_order_id)
            return None

        current_str = record.get("state", OrderState.PENDING.value)
        try:
            current = OrderState(current_str)
        except ValueError:
            current = OrderState.PENDING

        allowed = _VALID_TRANSITIONS.get(current, set())
        if new_state not in allowed:
            logger.warning("Invalid OMS transition",
                           client_order_id=client_order_id,
                           from_state=current.value,
                           to_state=new_state.value)
            return None

        record["state"] = new_state.value
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        if update:
            record.update({k: str(v) for k, v in update.items()})

        await self._persist(client_order_id, record)
        logger.info("OMS state transition",
                    client_order_id=client_order_id,
                    from_state=current.value,
                    to_state=new_state.value)
        return record

    async def get_order(self, client_order_id: str) -> Optional[Dict[str, Any]]:
        """Load order record."""
        return await self._load(client_order_id)

    async def _persist(self, client_order_id: str, record: Dict[str, Any]) -> None:
        self._orders[client_order_id] = record
        if self._redis:
            try:
                key = f"oms:order:{client_order_id}"
                await self._redis.hset(key, mapping=record)
                await self._redis.expire(key, 86400)
            except Exception as exc:
                logger.warning("OMS Redis persist failed", error=str(exc))

    async def _load(self, client_order_id: str) -> Optional[Dict[str, Any]]:
        if self._redis:
            try:
                key = f"oms:order:{client_order_id}"
                data = await self._redis.hgetall(key)
                if data:
                    return {
                        (k.decode() if isinstance(k, bytes) else k):
                        (v.decode() if isinstance(v, bytes) else v)
                        for k, v in data.items()
                    }
            except Exception as exc:
                logger.warning("OMS Redis load failed", error=str(exc))
        return self._orders.get(client_order_id)
