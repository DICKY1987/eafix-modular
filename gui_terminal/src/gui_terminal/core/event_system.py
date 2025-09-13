from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, DefaultDict, List


Subscriber = Callable[[Any], None]


class EventBus:
    """Simple in-process pub/sub event bus (stub)."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Subscriber]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Subscriber) -> None:
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, payload: Any) -> None:
        for handler in list(self._subscribers.get(topic, [])):
            try:
                handler(payload)
            except Exception:
                # Intentionally swallow to keep stub minimal; real impl will log.
                pass


class PlatformEventIntegration:
    """Placeholder for platform event system integration (websocket)."""

    def __init__(self, websocket_url: str | None = None, auth_token: str | None = None) -> None:
        self.websocket_url = websocket_url
        self.auth_token = auth_token

    def handle_workflow_event(self, event: dict) -> None:  # noqa: D401
        _ = event

    def broadcast_terminal_event(self, event: dict) -> None:  # noqa: D401
        _ = event

