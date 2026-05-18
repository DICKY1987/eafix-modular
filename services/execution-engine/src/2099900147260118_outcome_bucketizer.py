# doc_id: DOC-SERVICE-0214
"""
Outcome Bucketizer — maps profit_loss_pips to W2/W1/BE/L1/L2 outcome bucket.

Thresholds (configurable):
  pips >= strong_win_threshold  -> W2
  pips >= profit_threshold      -> W1
  loss_threshold < pips < profit_threshold -> BE
  pips <= -profit_threshold     -> L1
  pips <= -strong_win_threshold -> L2

Closes GAP-28.
"""
from typing import Any, Dict
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class OutcomeBucketizer:
    """Maps trade PnL pips to outcome bucket W2/W1/BE/L1/L2."""

    def __init__(self,
                 strong_win_threshold: float = 50.0,
                 profit_threshold: float = 5.0) -> None:
        self.strong_win_threshold = strong_win_threshold
        self.profit_threshold = profit_threshold

    def bucketize(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Add outcome_bucket field. Returns updated dict."""
        pips = float(trade.get("profit_loss_pips", 0.0))

        if pips >= self.strong_win_threshold:
            bucket = "W2"
        elif pips >= self.profit_threshold:
            bucket = "W1"
        elif pips <= -self.strong_win_threshold:
            bucket = "L2"
        elif pips <= -self.profit_threshold:
            bucket = "L1"
        else:
            bucket = "BE"

        result = {**trade, "outcome_bucket": bucket}
        logger.debug("Outcome bucketized",
                     pips=pips,
                     bucket=bucket,
                     symbol=trade.get("symbol"))
        return result
