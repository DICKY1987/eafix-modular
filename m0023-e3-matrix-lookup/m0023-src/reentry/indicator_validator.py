"""Stable import wrapper for indicator record validation."""

from ._id_loader import load_id_module

_MODULE = load_id_module("2099900219260118_indicator_validator.py", "indicator_validator")

IndicatorValidator = _MODULE.IndicatorValidator

__all__ = ["IndicatorValidator"]

