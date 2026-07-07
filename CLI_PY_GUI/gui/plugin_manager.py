# plugin_manager.py
from __future__ import annotations
import os, importlib.util, types
from typing import Any, Callable, Dict, List

class Plugin:
    def __init__(self, mod: types.ModuleType):
        self.mod = mod

    def hook(self, name: str) -> Callable[..., Any] | None:
        fn = getattr(self.mod, name, None)
        return fn if callable(fn) else None

class PluginManager:
    def __init__(self):
        self.plugins: list[Plugin] = []
        self._load_paths = [os.path.expanduser("~/.python_cockpit/plugins"), os.path.join(os.path.dirname(__file__), "plugins")]
        for p in self._load_paths:
            self._load_dir(p)

    def _load_dir(self, path: str) -> None:
        if not os.path.isdir(path):
            return
        for fn in os.listdir(path):
            if not fn.endswith(".py"):
                continue
            full = os.path.join(path, fn)
            name = f"cockpit_plugin_{fn[:-3]}"
            try:
                spec = importlib.util.spec_from_file_location(name, full)
                mod = importlib.util.module_from_spec(spec)  # type: ignore
                assert spec and spec.loader
                spec.loader.exec_module(mod)                 # type: ignore
                self.plugins.append(Plugin(mod))
            except Exception:
                continue

    def dispatch_event(self, event: dict) -> None:
        for p in self.plugins:
            cb = p.hook("on_event")
            if cb:
                try:
                    cb(event)
                except Exception:
                    pass

    def before_exec(self, req) -> None:
        for p in self.plugins:
            cb = p.hook("before_exec")
            if cb:
                try:
                    cb(req)
                except Exception:
                    pass

    def after_exec(self, resp) -> None:
        for p in self.plugins:
            cb = p.hook("after_exec")
            if cb:
                try:
                    cb(resp)
                except Exception:
                    pass
