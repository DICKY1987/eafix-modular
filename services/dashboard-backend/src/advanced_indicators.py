"""Compatibility import for the canonical C2 indicator engine.

P10 moved the implementation into its owning atomic module.  The dashboard
service still imports ``.advanced_indicators`` as part of its public runtime
layout, so this adapter exposes the canonical implementation without
duplicating it.
"""

from c2_indicator_engine.advanced_indicators import *  # noqa: F401,F403
