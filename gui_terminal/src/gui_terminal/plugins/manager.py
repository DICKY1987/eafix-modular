from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from gui_terminal.plugins import Plugin


@dataclass
class PluginRecord:
    name: str
    module_path: Path
    instance: Optional[Plugin] = None


class PluginManager:
    """Dynamic plugin loader based on configured directories."""

    def __init__(self, plugin_dirs: List[str]) -> None:
        self.search_paths = [Path(p).expanduser() for p in plugin_dirs]
        self.plugins: Dict[str, PluginRecord] = {}

    def discover(self) -> List[PluginRecord]:
        found: List[PluginRecord] = []
        for base in self.search_paths:
            if not base.exists():
                continue
            for py in base.glob("*.py"):
                name = py.stem
                found.append(PluginRecord(name=name, module_path=py))
        return found

    def load(self, record: PluginRecord) -> Optional[PluginRecord]:
        spec = importlib.util.spec_from_file_location(record.name, record.module_path)
        if not spec or not spec.loader:
            return None
        module = importlib.util.module_from_spec(spec)
        try:
            sys.modules[record.name] = module
            spec.loader.exec_module(module)  # type: ignore[attr-defined]
            obj = getattr(module, "plugin", None)
            if obj and hasattr(obj, "activate") and hasattr(obj, "deactivate"):
                record.instance = obj  # type: ignore[assignment]
                self.plugins[record.name] = record
                return record
        except Exception:
            return None
        return None

    def activate_all(self, context: Dict[str, Any]) -> None:
        for rec in list(self.plugins.values()):
            try:
                if rec.instance:
                    rec.instance.activate(context)
            except Exception:
                pass

    def deactivate_all(self) -> None:
        for rec in list(self.plugins.values()):
            try:
                if rec.instance:
                    rec.instance.deactivate()
            except Exception:
                pass

