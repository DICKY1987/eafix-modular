# doc_id: DOC-SERVICE-0216
"""
Reentry Chain Store — durable per-symbol chain history backed by Redis.

Redis HASH key: reentry:chain:{symbol}:{original_trade_id}
Fields: current_generation, last_trade_id, daily_attempts,
        cooldown_expires_utc, last_hybrid_id
TTL: 24 hours (auto-expire)

Falls back to in-memory if Redis unavailable.
Closes GAP-36.
"""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
import structlog

logger = structlog.get_logger(__name__)

_CHAIN_TTL_SECONDS = 86400  # 24h


class ReentryChainStore:
    """Durable chain history store for reentry tracking."""

    def __init__(self, redis_client=None) -> None:
        self._redis = redis_client
        # Fallback in-memory: (symbol, original_trade_id) -> dict
        self._memory: Dict[str, Dict[str, Any]] = {}

    def _key(self, symbol: str, original_trade_id: str) -> str:
        return f"reentry:chain:{symbol}:{original_trade_id}"

    async def get(self, symbol: str, original_trade_id: str) -> Optional[Dict[str, Any]]:
        """Load chain record. Returns None if not found."""
        key = self._key(symbol, original_trade_id)
        if self._redis:
            try:
                data = await self._redis.hgetall(key)
                if data:
                    return {
                        (k.decode() if isinstance(k, bytes) else k):
                        (v.decode() if isinstance(v, bytes) else v)
                        for k, v in data.items()
                    }
            except Exception as exc:
                logger.warning("ChainStore Redis get failed", error=str(exc), key=key)
        return self._memory.get(key)

    async def put(self, symbol: str, original_trade_id: str,
                  record: Dict[str, Any]) -> None:
        """Persist chain record with 24h TTL."""
        key = self._key(symbol, original_trade_id)
        flat = {k: str(v) for k, v in record.items()}

        self._memory[key] = flat  # Always update in-memory

        if self._redis:
            try:
                await self._redis.hset(key, mapping=flat)
                await self._redis.expire(key, _CHAIN_TTL_SECONDS)
                logger.debug("ChainStore persisted to Redis", key=key)
            except Exception as exc:
                logger.warning("ChainStore Redis put failed", error=str(exc), key=key)

    async def increment_daily_attempts(self, symbol: str,
                                       original_trade_id: str) -> int:
        """Increment and return the daily_attempts counter."""
        record = await self.get(symbol, original_trade_id) or {}
        attempts = int(record.get("daily_attempts", 0)) + 1
        record["daily_attempts"] = str(attempts)
        await self.put(symbol, original_trade_id, record)
        return attempts

    async def set_cooldown(self, symbol: str, original_trade_id: str,
                           minutes: int) -> None:
        """Set cooldown expiry timestamp."""
        expires = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        record = await self.get(symbol, original_trade_id) or {}
        record["cooldown_expires_utc"] = expires.isoformat()
        await self.put(symbol, original_trade_id, record)

    async def is_in_cooldown(self, symbol: str, original_trade_id: str) -> bool:
        """Check whether the chain is currently in cooldown."""
        record = await self.get(symbol, original_trade_id)
        if not record:
            return False
        expires_str = record.get("cooldown_expires_utc")
        if not expires_str:
            return False
        try:
            expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) < expires
        except ValueError:
            return False
