from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        payload = {
            "ts": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


@dataclass
class LoggerConfig:
    name: str = "gui_terminal"
    audit_log_file: str = "./gui_terminal_audit.log"
    level: int = logging.INFO


class StructuredLogger:
    """Enterprise-style structured + console logger.

    Minimal, dependency-free: JSON to file, readable to console.
    """

    def __init__(self, cfg: LoggerConfig | None = None) -> None:
        cfg = cfg or LoggerConfig()
        self.logger = logging.getLogger(cfg.name)
        self.logger.setLevel(cfg.level)
        self._ensure_handlers(cfg)

    def _ensure_handlers(self, cfg: LoggerConfig) -> None:
        # Avoid duplicate handlers on repeated construction
        if self.logger.handlers:
            return
        # File handler (JSON)
        try:
            log_path = Path(cfg.audit_log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setFormatter(JsonFormatter())
            self.logger.addHandler(fh)
        except Exception:
            pass
        # Console handler (human-readable)
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        self.logger.addHandler(ch)

    def audit(self, action: str, context: Dict[str, Any] | None = None, result: str | None = None) -> None:
        payload = {
            "event": "audit",
            "action": action,
            "context": context or {},
            "result": result,
        }
        self.logger.info(json.dumps(payload))

