# doc_id: DOC-SERVICE-0211
"""
Risk Processor — applies risk rules, emits OrderIntent@1.2 or RiskRejected.

Subscribes to: eafix.signals.generated (Signal@1.0)
Emits to:
  eafix.orders.validated  -> OrderIntent@1.2  (approved)
  eafix.risk.rejected     -> RiskRejected      (rejected)

Closes GAP-09, GAP-11 (client_order_id, idempotency_key generation).
"""
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class RiskProcessor:
    """Validates Signal against risk rules, emits OrderIntent or RiskRejected."""

    def __init__(self, settings) -> None:
        self.settings = settings
        self._cumulative_loss_today: float = 0.0
        self._today_date = datetime.now(timezone.utc).date()
        # calendar_id -> open exposure % (for chain cap)
        self._open_chain_exposure: Dict[str, float] = {}

    def _reset_daily_if_needed(self) -> None:
        today = datetime.now(timezone.utc).date()
        if today != self._today_date:
            self._cumulative_loss_today = 0.0
            self._today_date = today

    def _account_balance(self) -> float:
        return float(getattr(self.settings, "account_balance", 10000.0))

    def _compute_lot_size(self, sl_pips: float) -> float:
        """Lot = (balance * risk%) / (sl_pips * pip_value)."""
        balance = self._account_balance()
        risk_pct = getattr(self.settings, "max_risk_percent_per_trade", 2.0)
        pip_value = getattr(self.settings, "pip_value_per_lot", 10.0)
        risk_amount = balance * (risk_pct / 100.0)
        if sl_pips <= 0 or pip_value <= 0:
            return 0.01
        return max(0.01, round(risk_amount / (sl_pips * pip_value), 2))

    def process_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Validate signal. Returns OrderIntent or RiskRejected dict."""
        self._reset_daily_if_needed()

        calendar_id = signal.get("calendar_id", "NONE")
        correlation_id = signal.get("correlation_id", str(uuid.uuid4()))
        symbol = signal.get("symbol", "UNKNOWN")

        balance = self._account_balance()
        dd_limit = balance * (getattr(self.settings, "daily_drawdown_limit_percent", 5.0) / 100.0)

        # Rule 1: Daily drawdown halt
        if self._cumulative_loss_today >= dd_limit:
            return self._rejected(signal, correlation_id, "DAILY_DRAWDOWN_LIMIT_REACHED")

        # Rule 2: Reentry chain exposure cap
        chain_exposure = self._open_chain_exposure.get(calendar_id, 0.0)
        cap = getattr(self.settings, "max_reentry_risk_cap_percent", 3.5)
        if chain_exposure >= cap:
            return self._rejected(signal, correlation_id, "REENTRY_RISK_CAP_REACHED")

        sl_pips = float(signal.get("sl_pips",
                                   getattr(self.settings, "default_sl_pips", 20.0)))
        lot_size = self._compute_lot_size(sl_pips)

        # Rule 3: Per-trade risk check
        pip_value = getattr(self.settings, "pip_value_per_lot", 10.0)
        trade_risk_pct = (lot_size * sl_pips * pip_value / balance) * 100.0
        max_risk = getattr(self.settings, "max_risk_percent_per_trade", 2.0)
        if trade_risk_pct > max_risk:
            return self._rejected(signal, correlation_id,
                                  f"PER_TRADE_RISK_EXCEEDED:{trade_risk_pct:.2f}%")

        # Generate IDs (GAP-11)
        client_order_id = str(uuid.uuid4())
        utc_iso = datetime.now(timezone.utc).isoformat()
        idempotency_key = hashlib.sha256(
            f"{correlation_id}:{utc_iso}".encode()
        ).hexdigest()

        order_intent: Dict[str, Any] = {
            "event_type": "OrderIntent",
            "schema_version": "1.2",
            "client_order_id": client_order_id,
            "idempotency_key": idempotency_key,
            "correlation_id": correlation_id,
            "calendar_id": calendar_id,
            "symbol": symbol,
            "direction": signal.get("direction", "LONG"),
            "lot_size": lot_size,
            "sl_pips": sl_pips,
            "tp_pips": float(signal.get("tp_pips", sl_pips * 2.0)),
            "confidence": signal.get("confidence"),
            "proximity_state": signal.get("proximity_state"),
            "generated_at": utc_iso,
        }

        logger.info("OrderIntent approved",
                    client_order_id=client_order_id,
                    symbol=symbol,
                    lot_size=lot_size,
                    correlation_id=correlation_id)
        return order_intent

    def record_loss(self, loss_amount: float) -> None:
        """Record a realised loss for daily drawdown tracking."""
        if loss_amount > 0:
            self._cumulative_loss_today += loss_amount

    def _rejected(self, signal: Dict[str, Any], correlation_id: str,
                  reason: str) -> Dict[str, Any]:
        logger.warning("Signal risk-rejected",
                       reason=reason,
                       symbol=signal.get("symbol"),
                       correlation_id=correlation_id)
        return {
            "event_type": "RiskRejected",
            "schema_version": "1.0",
            "correlation_id": correlation_id,
            "symbol": signal.get("symbol"),
            "calendar_id": signal.get("calendar_id"),
            "reason": reason,
            "rejected_at": datetime.now(timezone.utc).isoformat(),
        }
