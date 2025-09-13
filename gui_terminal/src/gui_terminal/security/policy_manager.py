from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback
    yaml = None


class PolicyManager:
    """Loads and evaluates terminal security policies.

    This is a lightweight subset mapped from the plan's security_configuration.py.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path(__file__).resolve().parents[3]
        self._config = self._load()

    def _load(self) -> dict:
        policy_path = self.base_dir / "config" / "security_policies.yaml"
        if yaml is None:
            return {}
        try:
            with policy_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}

    def command_allowed(self, command_line: str) -> Tuple[bool, str]:
        cfg = self._config.get("command_filtering", {})
        mode = (cfg.get("mode") or "disabled").lower()
        allowed: Iterable[str] = cfg.get("allowed_commands", []) or []
        blocked: Iterable[str] = cfg.get("blocked_commands", []) or []

        # Rough match: exact token prefix or substring for blocked patterns.
        cl = command_line.strip().lower()
        if mode == "disabled":
            return True, "filtering_disabled"

        for pattern in blocked:
            if pattern and pattern.lower() in cl:
                return False, f"blocked:{pattern}"

        if mode == "blacklist":
            return True, "not_blocked"

        # whitelist mode: must start with an allowed command token
        for token in allowed:
            if not token:
                continue
            t = token.lower()
            if cl.startswith(t + " ") or cl == t:
                return True, f"allowed:{t}"
        return False, "not_whitelisted"

