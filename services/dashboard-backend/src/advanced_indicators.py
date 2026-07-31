"""Compatibility import for the canonical C2 indicator engine.

P10 moved the implementation into its owning atomic module.  The dashboard
service still imports ``.advanced_indicators`` as part of its public runtime
layout, so this adapter exposes the canonical implementation without
duplicating it.
"""

from __future__ import annotations

import sys
from pathlib import Path


_CANONICAL_SOURCE = (
    Path(__file__).resolve().parents[3]
    / "m0009-c2-indicator-engine"
    / "m0009-src"
)
if str(_CANONICAL_SOURCE) not in sys.path:
    sys.path.insert(0, str(_CANONICAL_SOURCE))

from c2_indicator_engine.advanced_indicators import *  # noqa: F401,F403,E402

