from __future__ import annotations


class ToolBar:  # pragma: no cover - GUI placeholder
    def __init__(self) -> None:
        self.actions = []

    def add_action(self, name: str) -> None:
        self.actions.append(name)

