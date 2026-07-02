from __future__ import annotations

import asyncio
import json
from typing import Any, Optional


class PlatformEventClient:
    """Optional websocket client for platform events.

    This stub avoids importing websockets at module import time to keep
    dependencies optional. Call `connect()` to start a background task.
    """

    def __init__(self, url: str, auth_token: Optional[str] = None) -> None:
        self.url = url
        self.auth_token = auth_token
        self._task: Optional[asyncio.Task] = None
        self._ws = None  # type: ignore

    async def _ensure_lib(self):
        # Import websockets lazily
        try:
            import websockets  # type: ignore
        except Exception as e:  # pragma: no cover - optional dep
            raise RuntimeError("websockets package not available") from e
        return websockets

    async def connect(self) -> None:
        websockets = await self._ensure_lib()
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        self._ws = await websockets.connect(self.url, extra_headers=headers)

    async def send_event(self, event: dict[str, Any]) -> None:
        if not self._ws:
            return
        data = json.dumps(event)
        await self._ws.send(data)

    async def close(self) -> None:
        if self._ws:
            await self._ws.close()
            self._ws = None

