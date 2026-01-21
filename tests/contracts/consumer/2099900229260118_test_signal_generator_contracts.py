# doc_id: DOC-TEST-0079
# DOC_ID: DOC-TEST-0028
"""
Consumer contract tests for signal-generator service.
Defines contracts that signal-generator expects from its dependencies.
"""

import pytest
import asyncio
from datetime import datetime, timezone

from ..framework.contract_testing import (
    ContractBuilder, ContractStore, Matcher, MatchingRule, ContractTestCase
)


class TestSignalGeneratorContracts(ContractTestCase):
    """Contract tests from signal-generator's perspective as a consumer."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        super().__init__()
        yield
        # Teardown happens via teardown method
    
    @pytest.mark.asyncio
    @pytest.mark.consumer
    @pytest.mark.contract
    async def test_risk_manager_validate_signal_contract(self):
        """Contract: signal-generator -> risk-manager for signal validation."""
        
        # Build contract
        contract = (ContractBuilder("signal-generator", "risk-manager")
            .given("risk limits are configured")
            .upon_receiving("a signal validation request")
            .with_request(
                method="POST",
                path="/validate",
                headers={"Content-Type": "application/json"},
                body={
                    "signal_id": "signal_123",
                    "symbol": "EURUSD",
                    "direction": "long",
                    "confidence": 0.85,
                    "entry_price": 1.0850,
                    "stop_loss": 1.0800,
                    "take_profit": 1.0900,
                    "position_size": 0.1,
                    "timestamp": "2023-12-07T10:30:00Z"
                }
            )
            .with_matcher("$.request.body.signal_id", Matcher(MatchingRule.REGEX, regex=r"signal_\w+"))
            .with_matcher("$.request.body.confidence", Matcher(MatchingRule.NUMERIC))
            .with_matcher("$.request.body.timestamp", Matcher(MatchingRule.DATETIME))
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "validation_id": "validation_456",
                    "signal_id": "signal_123",
                    "status": "approved",
                    "risk_score": 0.3,
                    "position_size_adjustment": 0.1,
                    "warnings": [],
                    "timestamp": "2023-12-07T10:30:05Z"
                }
            )
            .with_matcher("$.response.body.validation_id", Matcher(MatchingRule.REGEX, regex=r"validation_\w+"))
            .with_matcher("$.response.body.risk_score", Matcher(MatchingRule.NUMERIC))
            .with_matcher("$.response.body.timestamp", Matcher(MatchingRule.DATETIME))
            .build()
        )
        
        # Save contract
        self.store.save_contract(contract)
        
        # Verify contract (would typically be done in provider tests)
        await self.verify_contract("signal-generator", "risk-manager", "1.0.0")
    
    @pytest.mark.asyncio
    @pytest.mark.consumer
    @pytest.mark.contract
    async def test_risk_manager_rejected_signal_contract(self):
        """Contract: signal-generator -> risk-manager for rejected signals."""
        
        contract = (ContractBuilder("signal-generator", "risk-manager")
            .given("risk limits are exceeded")
            .upon_receiving("a signal validation request that exceeds risk limits")
            .with_request(
                method="POST",
                path="/validate",
                headers={"Content-Type": "application/json"},
                body={
                    "signal_id": "signal_456",
                    "symbol": "GBPJPY",
                    "direction": "short",
                    "confidence": 0.95,
                    "entry_price": 150.25,
                    "stop_loss": 151.00,
                    "take_profit": 149.50,
                    "position_size": 1.0,  # Large position
                    "timestamp": "2023-12-07T14:15:00Z"
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "validation_id": "validation_789",
                    "signal_id": "signal_456",
                    "status": "rejected",
                    "risk_score": 0.9,
                    "position_size_adjustment": 0.0,
                    "warnings": [
                        "Position size exceeds maximum allowed",
                        "Correlation risk with existing positions"
                    ],
                    "rejection_reason": "Risk limits exceeded",
                    "timestamp": "2023-12-07T14:15:03Z"
                }
            )
            .build()
        )
        
        self.store.save_contract(contract)
        await self.verify_contract("signal-generator", "risk-manager", "1.0.0")
    
    @pytest.mark.asyncio
    @pytest.mark.consumer
    @pytest.mark.contract
    async def test_indicator_engine_get_indicators_contract(self):
        """Contract: signal-generator -> indicator-engine for getting indicators."""
        
        contract = (ContractBuilder("signal-generator", "indicator-engine")
            .given("indicators are computed for EURUSD")
            .upon_receiving("a request for current indicators")
            .with_request(
                method="GET",
                path="/indicators/EURUSD",
                query={"timeframe": "M5", "count": "50"},
                headers={"Accept": "application/json"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "symbol": "EURUSD",
                    "timeframe": "M5",
                    "timestamp": "2023-12-07T10:30:00Z",
                    "indicators": {
                        "sma_20": 1.0845,
                        "sma_50": 1.0840,
                        "ema_12": 1.0847,
                        "ema_26": 1.0843,
                        "macd": {
                            "macd": 0.0002,
                            "signal": 0.0001,
                            "histogram": 0.0001
                        },
                        "rsi_14": 65.5,
                        "bollinger_bands": {
                            "upper": 1.0865,
                            "middle": 1.0845,
                            "lower": 1.0825
                        },
                        "stochastic": {
                            "k": 72.3,
                            "d": 68.1
                        },
                        "atr_14": 0.0012
                    },
                    "metadata": {
                        "computation_time_ms": 15,
                        "data_quality_score": 0.98,
                        "last_price": 1.0850
                    }
                }
            )
            .with_matcher("$.response.body.indicators.sma_20", Matcher(MatchingRule.NUMERIC))
            .with_matcher("$.response.body.indicators.rsi_14", Matcher(MatchingRule.NUMERIC))
            .with_matcher("$.response.body.metadata.computation_time_ms", Matcher(MatchingRule.NUMERIC))
            .build()
        )
        
        self.store.save_contract(contract)
        await self.verify_contract("signal-generator", "indicator-engine", "1.0.0")
    
    @pytest.mark.asyncio
    @pytest.mark.consumer
    @pytest.mark.contract
    async def test_calendar_ingestor_get_events_contract(self):
        """Contract: signal-generator -> calendar-ingestor for economic events."""
        
        contract = (ContractBuilder("signal-generator", "calendar-ingestor")
            .given("economic events are available for EUR and USD")
            .upon_receiving("a request for upcoming economic events")
            .with_request(
                method="GET",
                path="/events",
                query={
                    "currencies": "EUR,USD",
                    "impact": "high",
                    "hours_ahead": "24"
                },
                headers={"Accept": "application/json"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "events": [
                        {
                            "event_id": "ecb_rate_decision_123",
                            "currency": "EUR",
                            "title": "ECB Interest Rate Decision",
                            "impact": "high",
                            "scheduled_time": "2023-12-07T13:45:00Z",
                            "forecast": "4.50%",
                            "previous": "4.50%",
                            "actual": None,
                            "description": "European Central Bank announces monetary policy decision"
                        },
                        {
                            "event_id": "us_nonfarm_payrolls_456",
                            "currency": "USD", 
                            "title": "Nonfarm Payrolls",
                            "impact": "high",
                            "scheduled_time": "2023-12-07T13:30:00Z",
                            "forecast": "180K",
                            "previous": "150K",
                            "actual": None,
                            "description": "US monthly employment change"
                        }
                    ],
                    "metadata": {
                        "total_events": 2,
                        "query_time_ms": 5,
                        "cache_hit": True,
                        "last_updated": "2023-12-07T10:00:00Z"
                    }
                }
            )
            .with_matcher("$.response.body.events", Matcher(MatchingRule.ARRAY_MIN_LENGTH, min_length=0))
            .with_matcher("$.response.body.events[0].event_id", Matcher(MatchingRule.REGEX, regex=r"\w+_\w+_\d+"))
            .with_matcher("$.response.body.events[0].scheduled_time", Matcher(MatchingRule.DATETIME))
            .build()
        )
        
        self.store.save_contract(contract)
        await self.verify_contract("signal-generator", "calendar-ingestor", "1.0.0")
    
    @pytest.mark.asyncio
    @pytest.mark.consumer
    @pytest.mark.contract  
    async def test_message_bus_signal_published_contract(self):
        """Contract: signal-generator publishes trading signals to message bus."""
        
        contract = (ContractBuilder("signal-generator", "message-bus")
            .given("message bus is available")
            .upon_publishing("trading signal generated", "trading.signals.generated")
            .with_message(
                message_type="TradingSignalGenerated",
                schema_version="1.0",
                payload={
                    "signal_id": "signal_789",
                    "symbol": "EURUSD",
                    "direction": "long",
                    "confidence": 0.78,
                    "entry_price": 1.0852,
                    "stop_loss": 1.0802,
                    "take_profit": 1.0902,
                    "position_size": 0.15,
                    "indicators_used": [
                        "sma_crossover",
                        "rsi_oversold",
                        "macd_bullish"
                    ],
                    "risk_reward_ratio": 2.0,
                    "generated_at": "2023-12-07T10:32:15Z",
                    "expires_at": "2023-12-07T10:37:15Z"
                },
                metadata={
                    "source_service": "signal-generator",
                    "correlation_id": "corr_123",
                    "idempotency_key": "signal_789_generation"
                }
            )
            .with_matcher("$.message.payload.signal_id", Matcher(MatchingRule.REGEX, regex=r"signal_\w+"))
            .with_matcher("$.message.payload.confidence", Matcher(MatchingRule.NUMERIC))
            .with_matcher("$.message.payload.generated_at", Matcher(MatchingRule.DATETIME))
            .with_matcher("$.message.payload.expires_at", Matcher(MatchingRule.DATETIME))
            .with_matcher("$.message.metadata.correlation_id", Matcher(MatchingRule.REGEX, regex=r"corr_\w+"))
            .build()
        )
        
        self.store.save_contract(contract)
        # Message contracts are typically verified differently
        # await self.verify_contract("signal-generator", "message-bus", "1.0.0")
    
    async def teardown(self):
        """Clean up test resources."""
        await super().teardown()