from __future__ import annotations

from typing import Tuple, Set

# In-memory idempotency set (replace with durable store in production)
_seen: Set[Tuple[str, str, str, int]] = set()

def mark_seen(account: str, symbol: str, strategy: str, nonce: int) -> bool:
    key = (account, symbol, strategy, nonce)
    if key in _seen:
        return False
    _seen.add(key)
    return True
