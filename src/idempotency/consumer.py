from __future__ import annotations

from .state import mark_seen

def process(account: str, symbol: str, strategy: str, nonce: int) -> bool:
    """Return True if processed; False if duplicate (idempotent)."""
    if not mark_seen(account, symbol, strategy, nonce):
        return False
    # TODO: handle message
    return True
