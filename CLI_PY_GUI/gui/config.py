# config.py
from __future__ import annotations
import os, json, dataclasses
from dataclasses import dataclass, field
from typing import Optional

CFG_PATH = os.path.expanduser("~/.python_cockpit/config.json")

@dataclass
class AppearanceConfig:
    font_family: str = "Consolas"
    font_size: int = 11
    dark_mode: bool = True

@dataclass
class PerformanceConfig:
    max_buffer_chars: int = 1_000_000  # ring buffer cap
    poll_interval_ms: int = 30

@dataclass
class SecurityConfig:
    sandbox_enabled: bool = False  # placeholder
    allowed_commands: list[str] = field(default_factory=list)

@dataclass
class GUIConfig:
    appearance: AppearanceConfig = field(default_factory=AppearanceConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    timeout_default_sec: int = 0  # 0 = no timeout

    @classmethod
    def load(cls) -> "GUIConfig":
        try:
            if os.path.exists(CFG_PATH):
                data = json.load(open(CFG_PATH, "r", encoding="utf-8"))
                def _merge(dc, src):
                    for k,v in src.items():
                        if hasattr(dc, k):
                            attr = getattr(dc, k)
                            if dataclasses.is_dataclass(attr):
                                _merge(attr, v)
                            else:
                                setattr(dc, k, v)
                cfg = cls()
                _merge(cfg, data)
                return cfg
        except Exception:
            pass
        return cls()
