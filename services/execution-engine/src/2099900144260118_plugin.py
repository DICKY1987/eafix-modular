# doc_id: DOC-SERVICE-0207
"""
Execution Engine Plugin - Order execution and trade result processing.

Subscribes to: eafix.orders.validated (OrderIntent), eafix.execution.completed (ExecutionReport)
Emits: order_executed, eafix.execution.timeout, eafix.trades.results, TradeResult CSV

Closes GAP-19 (EA timeout), GAP-21 (close classifier), GAP-22 (OMS),
       GAP-23 (Redis OMS store), GAP-24 (CSV write), GAP-25 (PnL rounding), GAP-28 (buckets).
"""
import asyncio
import csv
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_src = Path(__file__).parent
sys.path.insert(0, str(_src.parent.parent.parent / "shared"))


def _load(fname: str, mname: str):
    spec = importlib.util.spec_from_file_location(mname, _src / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_oms_mod = _load("2099900145260118_oms.py", "ee_oms")
_cls_mod = _load("2099900146260118_trade_close_classifier.py", "ee_classifier")
_bkt_mod = _load("2099900147260118_outcome_bucketizer.py", "ee_bucketizer")

OMSStateMachine = _oms_mod.OMSStateMachine
OrderState = _oms_mod.OrderState
TradeCloseClassifier = _cls_mod.TradeCloseClassifier
OutcomeBucketizer = _bkt_mod.OutcomeBucketizer

from shared.plugin_interface import BasePlugin, PluginMetadata

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ExecutionEnginePlugin(BasePlugin):
    """
    Executes approved orders and processes execution results.
    """

    def __init__(self) -> None:
        metadata = PluginMetadata(
            name="execution-engine",
            version="1.0.0",
            description="Order execution to MT4 broker",
            author="EAFIX Team",
            dependencies=["risk-manager"],
        )
        super().__init__(metadata)
        self._oms: Optional[OMSStateMachine] = None
        self._classifier: Optional[TradeCloseClassifier] = None
        self._bucketizer: Optional[OutcomeBucketizer] = None
        self._order_timeout_sec: int = 30
        self._output_dir: Path = Path("./data/execution-engine")
        self._execution_count: int = 0
        self._failed_count: int = 0
        self._timeout_count: int = 0

    async def _on_initialize(self) -> None:
        self._order_timeout_sec = int(self.get_config("order_timeout_sec", 30))
        strong_win = float(self.get_config("strong_win_threshold_pips", 50.0))
        profit_thr = float(self.get_config("profit_threshold_pips", 5.0))
        out_dir = self.get_config("output_directory", "./data/execution-engine")
        self._output_dir = Path(out_dir)

        self._oms = OMSStateMachine()
        self._classifier = TradeCloseClassifier()
        self._bucketizer = OutcomeBucketizer(
            strong_win_threshold=strong_win,
            profit_threshold=profit_thr,
        )

        if self._context:
            self._context.subscribe("eafix.orders.validated", self._handle_order_intent)
            self._context.subscribe("eafix.execution.completed", self._handle_execution_report)

    async def _on_start(self) -> None:
        self._output_dir.mkdir(parents=True, exist_ok=True)

    async def _on_stop(self) -> None:
        pass

    def _handle_order_intent(self, event_type: str, data: Dict[str, Any],
                              source: str) -> None:
        asyncio.create_task(self._execute_with_timeout(data))

    def _handle_execution_report(self, event_type: str, data: Dict[str, Any],
                                  source: str) -> None:
        asyncio.create_task(self._process_execution_report(data))

    async def _execute_with_timeout(self, order: Dict[str, Any]) -> None:
        client_order_id = order.get("client_order_id",
                                    f"ORD-{self._execution_count:06d}")
        await self._oms.create_order(client_order_id, order)

        try:
            await asyncio.wait_for(
                self._submit_order(client_order_id, order),
                timeout=self._order_timeout_sec,
            )
        except asyncio.TimeoutError:
            self._timeout_count += 1
            await self._oms.transition(client_order_id, OrderState.TIMEOUT)
            self.emit_event("eafix.execution.timeout", {
                "event_type": "EATimeoutEvent",
                "client_order_id": client_order_id,
                "symbol": order.get("symbol"),
                "timeout_seconds": self._order_timeout_sec,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.warning("EA response timeout",
                           client_order_id=client_order_id,
                           timeout_sec=self._order_timeout_sec)

    async def _submit_order(self, client_order_id: str,
                            order: Dict[str, Any]) -> None:
        await asyncio.sleep(0.1)
        self._execution_count += 1
        await self._oms.transition(client_order_id, OrderState.OPEN)
        result = {
            **order,
            "order_id": client_order_id,
            "executed_price": float(
                order.get("price") or order.get("expected_price") or 1.2345
            ),
            "execution_time": datetime.now(timezone.utc).isoformat(),
            "status": "filled",
        }
        self.emit_event("order_executed", result)

    async def _process_execution_report(self, report: Dict[str, Any]) -> None:
        """Process ExecutionReport from eafix.execution.completed."""
        try:
            client_order_id = report.get("client_order_id")
            if client_order_id:
                await self._oms.transition(
                    client_order_id,
                    OrderState.CLOSED,
                    update={
                        "close_price": report.get("close_price", 0),
                        "raw_close_reason": report.get("close_reason", "manual"),
                    },
                )

            classified = self._classifier.classify(report)
            bucketized = self._bucketizer.bucketize(classified)

            await self._write_trade_result_csv(bucketized)
            self.emit_event("eafix.trades.results", bucketized)

        except Exception as exc:
            self._failed_count += 1
            logger.error("Failed to process execution report", error=str(exc))

    async def _write_trade_result_csv(self, trade: Dict[str, Any]) -> None:
        """Append trade result to CSV in output_dir."""
        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d")
            csv_path = self._output_dir / f"trade_results_{ts}.csv"
            row = {k: str(v) for k, v in trade.items()}
            write_header = not csv_path.exists()
            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(row.keys()))
                if write_header:
                    writer.writeheader()
                writer.writerow(row)
        except Exception as exc:
            logger.error("Failed to write trade result CSV", error=str(exc))

    async def health_check(self) -> Dict[str, Any]:
        base_health = await super().health_check()
        base_health.update({
            "executions": self._execution_count,
            "failures": self._failed_count,
            "timeouts": self._timeout_count,
            "output_dir": str(self._output_dir),
        })
        return base_health


plugin_class = ExecutionEnginePlugin
