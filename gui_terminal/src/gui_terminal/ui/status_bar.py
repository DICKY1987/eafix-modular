from __future__ import annotations


class StatusBar:  # pragma: no cover - GUI placeholder
    def __init__(self) -> None:
        self.status = "Ready"

    def set_status(self, text: str) -> None:
        self.status = text

