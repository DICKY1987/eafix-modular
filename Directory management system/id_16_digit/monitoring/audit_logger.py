"""
Compatibility shim for imports expecting monitoring.audit_logger.
"""

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

_module_path = Path(__file__).with_name("2099900076260118_audit_logger.py")
_spec = spec_from_file_location("monitoring._audit_logger_impl", _module_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load audit logger implementation from {_module_path}")

_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)

AuditLogger = _module.AuditLogger

__all__ = ["AuditLogger"]
