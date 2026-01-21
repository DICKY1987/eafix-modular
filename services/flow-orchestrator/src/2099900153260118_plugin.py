# doc_id: DOC-SERVICE-0224
# DOC_ID: DOC-ARCH-0111
"""
Flow Orchestrator Plugin
Orchestrates trading flow and state transitions
"""

from typing import Dict, Any, Optional
import asyncio
import structlog
from enum import Enum

from shared.plugin_interface import BasePlugin, PluginMetadata


logger = structlog.get_logger(__name__)


class TradingState(Enum):
    """Trading flow states"""
    IDLE = "idle"
    DATA_INGESTION = "data_ingestion"
    INDICATOR_CALC = "indicator_calc"
    SIGNAL_GEN = "signal_gen"
    RISK_CHECK = "risk_check"
    EXECUTION = "execution"
    POST_TRADE = "post_trade"


class FlowOrchestratorPlugin(BasePlugin):
    """Orchestrates trading flow state machine"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="flow-orchestrator",
            version="1.0.0",
            description="Trading flow orchestration and state management",
            author="EAFIX Team",
            dependencies=["event-gateway"],
        )
        super().__init__(metadata)
        self._current_state = TradingState.IDLE
        self._state_transitions = 0
        self._flows_in_progress: Dict[str, Dict[str, Any]] = {}
    
    async def _on_initialize(self) -> None:
        """Initialize the flow orchestrator"""
        # Subscribe to key events in the trading flow
        self._context.subscribe("price_tick", self._on_price_tick)
        self._context.subscribe("indicator_update", self._on_indicator_update)
        self._context.subscribe("signal_generated", self._on_signal_generated)
        self._context.subscribe("order_approved", self._on_order_approved)
        self._context.subscribe("order_executed", self._on_order_executed)
        
        logger.info("Flow orchestrator initialized")
    
    async def _on_start(self) -> None:
        """Start the flow orchestrator"""
        self._current_state = TradingState.DATA_INGESTION
        logger.info("Flow orchestrator started", state=self._current_state.value)
    
    async def _on_stop(self) -> None:
        """Stop the flow orchestrator"""
        self._current_state = TradingState.IDLE
        logger.info(
            "Flow orchestrator stopped",
            total_transitions=self._state_transitions,
            flows_completed=len(self._flows_in_progress)
        )
    
    def _on_price_tick(self, event_type: str, data: Any, source: str) -> None:
        """Handle price tick - start of flow"""
        symbol = data.get("symbol")
        if symbol:
            flow_id = f"{symbol}_{data.get('timestamp')}"
            self._flows_in_progress[flow_id] = {
                "symbol": symbol,
                "state": TradingState.DATA_INGESTION,
                "started": data.get("timestamp")
            }
    
    def _on_indicator_update(self, event_type: str, data: Any, source: str) -> None:
        """Handle indicator update"""
        symbol = data.get("symbol")
        self._update_flow_state(symbol, TradingState.INDICATOR_CALC)
    
    def _on_signal_generated(self, event_type: str, data: Any, source: str) -> None:
        """Handle signal generation"""
        symbol = data.get("symbol")
        self._update_flow_state(symbol, TradingState.SIGNAL_GEN)
    
    def _on_order_approved(self, event_type: str, data: Any, source: str) -> None:
        """Handle order approval"""
        symbol = data.get("symbol")
        self._update_flow_state(symbol, TradingState.EXECUTION)
    
    def _on_order_executed(self, event_type: str, data: Any, source: str) -> None:
        """Handle order execution - end of flow"""
        symbol = data.get("symbol")
        self._update_flow_state(symbol, TradingState.POST_TRADE)
        
        # Clean up completed flow
        flows_to_remove = [k for k, v in self._flows_in_progress.items() if v.get("symbol") == symbol]
        for flow_id in flows_to_remove:
            del self._flows_in_progress[flow_id]
    
    def _update_flow_state(self, symbol: str, new_state: TradingState) -> None:
        """Update flow state"""
        for flow_id, flow in self._flows_in_progress.items():
            if flow.get("symbol") == symbol:
                flow["state"] = new_state
                self._state_transitions += 1
                
                logger.debug(
                    "Flow state transition",
                    flow_id=flow_id,
                    symbol=symbol,
                    state=new_state.value
                )
                break
    
    def get_flow_status(self) -> Dict[str, Any]:
        """Get current flow status"""
        return {
            "active_flows": len(self._flows_in_progress),
            "total_transitions": self._state_transitions,
            "flows": list(self._flows_in_progress.values())
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        health = await super().health_check()
        health["current_state"] = self._current_state.value
        health["active_flows"] = len(self._flows_in_progress)
        health["state_transitions"] = self._state_transitions
        return health


plugin_class = FlowOrchestratorPlugin
