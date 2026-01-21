# doc_id: DOC-SERVICE-0193
# DOC_ID: DOC-SERVICE-0103
"""
Shared positioning analysis library.

This module provides institutional positioning analysis capabilities including
CFTC COT data processing, retail sentiment aggregation, and positioning ratio
indices for trading system signal enhancement.
"""

from .positioning_ratio_index import PositioningRatioIndex, PositioningData

__all__ = [
    "PositioningRatioIndex",
    "PositioningData"
]

# Note: CFTC processor and retail sentiment aggregator would be implemented
# in a full production system but are not required for Phase 2A integration