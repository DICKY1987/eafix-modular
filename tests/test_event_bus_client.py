from __future__ import annotations

from lib.event_bus_client import publish_event


def test_publish_event_disabled(monkeypatch):
    monkeypatch.delenv("GDW_BROADCAST", raising=False)
    assert publish_event({"hello": "world"}) is True

