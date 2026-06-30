from __future__ import annotations

import json
from typing import Any, Dict
import urllib.request


class EventBusClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def publish(self, message: Dict[str, Any]) -> None:
        data = json.dumps(message).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/publish",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:  # nosec B310
            resp.read()

