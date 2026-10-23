# doc_id: DOC-SERVICE-0213
"""
Trade Close Classifier — assigns close_reason enum, computes canonical PnL.

Closes GAP-21, GAP-25.
"""
import decimal
from datetime import datetime, timezone
from typing import Any, Dict
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

_CLOSE_REASON_MAP = {
    "tp": "TAKE_PROFIT",
    "take_profit": "TAKE_PROFIT",
    "sl": "STOP_LOSS",
    "stop_loss": "STOP_LOSS",
    "manual": "MANUAL",
    "timeout": "TIMEOUT",
    "broker_reject": "BROKER_REJECT",
    "rejected": "BROKER_REJECT",
}


def _round_half_up(value: float, decimals: int = 1) -> float:
    """Deterministic round-half-up to N decimal places."""
    d = decimal.Decimal(str(value))
    quantize_str = "0." + "0" * decimals
    return float(d.quantize(decimal.Decimal(quantize_str),
                            rounding=decimal.ROUND_HALF_UP))


class TradeCloseClassifier:
    """Classifies close reason and computes canonical pip PnL."""

    def classify(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input raw execution report dict.
        Returns updated dict with close_reason and profit_loss_pips (canonical).
        """
        raw_reason = str(
            raw.get("raw_close_reason") or raw.get("close_reason", "manual")
        ).lower()
        close_reason = _CLOSE_REASON_MAP.get(raw_reason, "MANUAL")

        open_price = float(raw.get("open_price") or raw.get("executed_price", 0.0))
        close_price = float(raw.get("close_price", 0.0))
        direction = str(raw.get("direction", "BUY")).upper()
        symbol = str(raw.get("symbol", "EURUSD"))

        pip_size = 0.01 if "JPY" in symbol else 0.0001
        if direction == "BUY":
            raw_pips = (close_price - open_price) / pip_size
        else:
            raw_pips = (open_price - close_price) / pip_size

        profit_loss_pips = _round_half_up(raw_pips, 1)

        result = {
            **raw,
            "close_reason": close_reason,
            "profit_loss_pips": profit_loss_pips,
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info("Trade classified",
                    close_reason=close_reason,
                    profit_loss_pips=profit_loss_pips,
                    symbol=symbol)
        return result
