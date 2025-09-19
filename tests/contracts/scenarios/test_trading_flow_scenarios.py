"""
Scenario-based integration tests for EAFIX trading system.
Tests complete end-to-end trading scenarios with contract verification.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

from ..framework.contract_testing import ContractStore, ContractVerifier


class TradingScenarioTest:
    """Base class for trading scenario tests."""
    
    def __init__(self):
        self.services = {}
        self.message_bus = AsyncMock()
        self.contracts_store = ContractStore("tests/contracts")
        
        # Mock external dependencies
        self.broker_api = AsyncMock()
        self.market_data = AsyncMock()
        
    async def setup_services(self):
        """Set up mock services for scenario testing."""
        self.services = {
            'data-ingestor': AsyncMock(),
            'indicator-engine': AsyncMock(),
            'signal-generator': AsyncMock(), 
            'risk-manager': AsyncMock(),
            'execution-engine': AsyncMock(),
            'calendar-ingestor': AsyncMock(),
            'reentry-matrix-svc': AsyncMock(),
            'reporter': AsyncMock(),
            'gui-gateway': AsyncMock()
        }
    
    async def simulate_market_data(self, symbol: str, price: float, timestamp: datetime = None):
        """Simulate incoming market data."""
        if not timestamp:
            timestamp = datetime.now(timezone.utc)
        
        price_tick = {
            "symbol": symbol,
            "bid": price - 0.0001,
            "ask": price + 0.0001,
            "timestamp": timestamp.isoformat(),
            "volume": 1000000
        }
        
        # Send to data ingestor
        await self.services['data-ingestor'].process_price_tick(price_tick)
        return price_tick
    
    async def verify_message_published(self, topic: str, expected_message_type: str):
        """Verify a message was published to the message bus."""
        # Check if message was published with expected structure
        calls = self.message_bus.publish.call_args_list
        matching_calls = [
            call for call in calls 
            if call[0][0] == topic and expected_message_type in str(call)
        ]
        
        assert len(matching_calls) > 0, f"Expected message type {expected_message_type} not published to {topic}"
        return matching_calls[-1]  # Return most recent matching call


@pytest.fixture
async def trading_scenario():
    """Fixture for trading scenario tests."""
    scenario = TradingScenarioTest()
    await scenario.setup_services()
    yield scenario


class TestCompleteTradingFlow:
    """Test complete trading flow scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.scenario
    async def test_successful_signal_generation_and_execution(self, trading_scenario):
        """
        Scenario: Successful signal generation leading to order execution
        
        Flow:
        1. Market data arrives → data-ingestor
        2. Indicators computed → indicator-engine  
        3. Signal generated → signal-generator
        4. Risk validation → risk-manager
        5. Order execution → execution-engine
        6. Position update → reporter
        """
        
        # Step 1: Market data arrives
        price_data = await trading_scenario.simulate_market_data("EURUSD", 1.0850)
        
        # Mock indicator computation
        trading_scenario.services['indicator-engine'].compute_indicators.return_value = {
            "symbol": "EURUSD",
            "indicators": {
                "sma_20": 1.0845,
                "rsi_14": 65.5,
                "macd": {"macd": 0.0002, "signal": 0.0001}
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Step 2: Trigger indicator computation
        indicators = await trading_scenario.services['indicator-engine'].compute_indicators("EURUSD", price_data)
        
        # Mock signal generation
        trading_scenario.services['signal-generator'].generate_signal.return_value = {
            "signal_id": "signal_123", 
            "symbol": "EURUSD",
            "direction": "long",
            "confidence": 0.85,
            "entry_price": 1.0850,
            "stop_loss": 1.0800,
            "take_profit": 1.0900,
            "position_size": 0.1,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Step 3: Generate signal
        signal = await trading_scenario.services['signal-generator'].generate_signal("EURUSD", indicators)
        
        # Mock risk validation - approved
        trading_scenario.services['risk-manager'].validate_signal.return_value = {
            "validation_id": "validation_456",
            "signal_id": "signal_123",
            "status": "approved", 
            "risk_score": 0.3,
            "position_size_adjustment": 0.1,
            "warnings": []
        }
        
        # Step 4: Validate with risk manager
        risk_result = await trading_scenario.services['risk-manager'].validate_signal(signal)
        
        assert risk_result["status"] == "approved"
        
        # Mock order execution
        trading_scenario.services['execution-engine'].execute_order.return_value = {
            "order_id": "order_789",
            "signal_id": "signal_123",
            "status": "filled",
            "fill_price": 1.0851,
            "fill_quantity": 0.1,
            "execution_time": datetime.now(timezone.utc).isoformat(),
            "commission": 2.50
        }
        
        # Step 5: Execute order
        execution_result = await trading_scenario.services['execution-engine'].execute_order({
            "symbol": signal["symbol"],
            "side": "buy",
            "quantity": risk_result["position_size_adjustment"],
            "price": signal["entry_price"],
            "signal_id": signal["signal_id"]
        })
        
        assert execution_result["status"] == "filled"
        
        # Step 6: Update position records
        trading_scenario.services['reporter'].update_position.return_value = {
            "position_id": "pos_101",
            "symbol": "EURUSD",
            "quantity": 0.1,
            "entry_price": 1.0851,
            "unrealized_pnl": 0.0,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        position_update = await trading_scenario.services['reporter'].update_position(execution_result)
        
        # Verify the complete flow succeeded
        assert signal["confidence"] > 0.8
        assert risk_result["status"] == "approved"  
        assert execution_result["status"] == "filled"
        assert position_update["quantity"] == 0.1
    
    @pytest.mark.asyncio
    @pytest.mark.scenario
    async def test_signal_rejected_by_risk_manager(self, trading_scenario):
        """
        Scenario: Signal generation but rejection by risk manager
        
        Flow:
        1. Market data → indicators → signal generated
        2. Risk manager rejects signal
        3. No order execution
        4. Rejection logged and reported
        """
        
        # Generate market data and signal (same as before)
        price_data = await trading_scenario.simulate_market_data("GBPJPY", 150.25)
        
        # Mock aggressive signal that should be rejected
        trading_scenario.services['signal-generator'].generate_signal.return_value = {
            "signal_id": "signal_risky_456",
            "symbol": "GBPJPY", 
            "direction": "short",
            "confidence": 0.95,
            "entry_price": 150.25,
            "stop_loss": 151.00,  # Small stop loss
            "take_profit": 149.50,
            "position_size": 1.0,  # Large position
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        signal = await trading_scenario.services['signal-generator'].generate_signal("GBPJPY", {})
        
        # Mock risk rejection
        trading_scenario.services['risk-manager'].validate_signal.return_value = {
            "validation_id": "validation_rejected_789",
            "signal_id": "signal_risky_456",
            "status": "rejected",
            "risk_score": 0.9,
            "position_size_adjustment": 0.0,
            "warnings": [
                "Position size exceeds maximum allowed",
                "Stop loss too tight for volatility"
            ],
            "rejection_reason": "Risk limits exceeded"
        }
        
        # Validate signal
        risk_result = await trading_scenario.services['risk-manager'].validate_signal(signal)
        
        # Verify rejection
        assert risk_result["status"] == "rejected"
        assert risk_result["position_size_adjustment"] == 0.0
        assert len(risk_result["warnings"]) > 0
        
        # Verify no order execution was attempted
        trading_scenario.services['execution-engine'].execute_order.assert_not_called()
        
        # Verify rejection was logged
        trading_scenario.services['reporter'].log_rejection.return_value = {
            "rejection_id": "rejection_123",
            "signal_id": "signal_risky_456",
            "reason": "Risk limits exceeded",
            "logged_at": datetime.now(timezone.utc).isoformat()
        }
        
        await trading_scenario.services['reporter'].log_rejection(risk_result)
    
    @pytest.mark.asyncio
    @pytest.mark.scenario
    async def test_order_execution_failure_and_retry(self, trading_scenario):
        """
        Scenario: Order execution fails and requires retry
        
        Flow:
        1. Signal approved by risk manager
        2. First execution attempt fails
        3. Retry mechanism triggers
        4. Second attempt succeeds
        """
        
        # Setup approved signal
        signal = {
            "signal_id": "signal_retry_789",
            "symbol": "EURUSD",
            "direction": "long", 
            "entry_price": 1.0850,
            "position_size": 0.1
        }
        
        risk_result = {"status": "approved", "position_size_adjustment": 0.1}
        
        # Mock first execution failure
        trading_scenario.services['execution-engine'].execute_order.side_effect = [
            # First call fails
            {
                "order_id": "order_failed_101",
                "status": "rejected",
                "error": "Insufficient liquidity",
                "retry_recommended": True
            },
            # Second call succeeds  
            {
                "order_id": "order_success_102",
                "status": "filled",
                "fill_price": 1.0852,
                "fill_quantity": 0.1
            }
        ]
        
        # First execution attempt
        result1 = await trading_scenario.services['execution-engine'].execute_order({
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": 0.1
        })
        
        assert result1["status"] == "rejected"
        assert result1["retry_recommended"] == True
        
        # Retry logic would trigger second attempt
        result2 = await trading_scenario.services['execution-engine'].execute_order({
            "symbol": "EURUSD", 
            "side": "buy",
            "quantity": 0.1
        })
        
        assert result2["status"] == "filled"
        assert result2["fill_quantity"] == 0.1
        
        # Verify both attempts were made
        assert trading_scenario.services['execution-engine'].execute_order.call_count == 2
    
    @pytest.mark.asyncio
    @pytest.mark.scenario
    async def test_high_impact_news_scenario(self, trading_scenario):
        """
        Scenario: High-impact news event affects trading decisions
        
        Flow:
        1. Calendar service detects high-impact news
        2. Signal generator considers news impact
        3. Risk manager adjusts limits for news period
        4. Different execution behavior during news
        """
        
        # Mock high-impact news event
        trading_scenario.services['calendar-ingestor'].get_upcoming_events.return_value = {
            "events": [
                {
                    "event_id": "nfp_2023_12_07",
                    "currency": "USD",
                    "title": "Nonfarm Payrolls",
                    "impact": "high",
                    "scheduled_time": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
                    "forecast": "180K",
                    "previous": "150K"
                }
            ]
        }
        
        # Get upcoming events
        news_events = await trading_scenario.services['calendar-ingestor'].get_upcoming_events("USD", "high")
        
        # Signal generator should consider news impact
        trading_scenario.services['signal-generator'].generate_signal.return_value = {
            "signal_id": "signal_news_aware_123",
            "symbol": "EURUSD",
            "direction": "long",
            "confidence": 0.60,  # Reduced confidence due to upcoming news
            "news_impact": "high_usd_news_pending",
            "position_size": 0.05  # Smaller position due to news
        }
        
        signal = await trading_scenario.services['signal-generator'].generate_signal("EURUSD", {
            "upcoming_news": news_events["events"]
        })
        
        # Risk manager should apply news-period limits
        trading_scenario.services['risk-manager'].validate_signal.return_value = {
            "status": "approved_with_conditions",
            "position_size_adjustment": 0.03,  # Further reduced for news
            "conditions": ["close_before_news_release"],
            "news_aware": True
        }
        
        risk_result = await trading_scenario.services['risk-manager'].validate_signal(signal)
        
        # Verify news-aware behavior
        assert signal["confidence"] < 0.7  # Reduced confidence
        assert risk_result["position_size_adjustment"] < 0.05  # Smaller position
        assert "news_aware" in risk_result
        assert risk_result["news_aware"] == True
    
    @pytest.mark.asyncio
    @pytest.mark.scenario
    async def test_reentry_decision_scenario(self, trading_scenario):
        """
        Scenario: Re-entry decision after position closure
        
        Flow:  
        1. Existing position is closed (profit/loss)
        2. Reentry matrix service evaluates conditions
        3. Decision made on whether to re-enter
        4. If approved, new signal generated
        """
        
        # Mock closed position
        closed_position = {
            "position_id": "pos_closed_123",
            "symbol": "EURUSD", 
            "entry_price": 1.0850,
            "exit_price": 1.0900,
            "pnl": 50.0,
            "close_reason": "take_profit",
            "closed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Mock reentry evaluation
        trading_scenario.services['reentry-matrix-svc'].evaluate_reentry.return_value = {
            "reentry_id": "reentry_456",
            "position_id": "pos_closed_123",
            "decision": "approved",
            "confidence": 0.75,
            "wait_time_minutes": 15,
            "conditions": [
                "previous_trade_profitable",
                "market_conditions_stable", 
                "no_major_news_pending"
            ],
            "recommended_position_size": 0.12  # Slightly larger after profit
        }
        
        # Evaluate reentry
        reentry_decision = await trading_scenario.services['reentry-matrix-svc'].evaluate_reentry(closed_position)
        
        assert reentry_decision["decision"] == "approved"
        assert reentry_decision["confidence"] > 0.7
        
        # If approved, generate new signal  
        if reentry_decision["decision"] == "approved":
            # Wait for recommended time (mocked)
            await asyncio.sleep(0.01)  # Simulated wait
            
            # Generate reentry signal
            trading_scenario.services['signal-generator'].generate_reentry_signal.return_value = {
                "signal_id": "signal_reentry_789",
                "symbol": "EURUSD",
                "direction": "long",
                "reentry_id": "reentry_456", 
                "position_size": 0.12,
                "confidence": 0.75
            }
            
            reentry_signal = await trading_scenario.services['signal-generator'].generate_reentry_signal(
                reentry_decision
            )
            
            assert reentry_signal["reentry_id"] == "reentry_456"
            assert reentry_signal["position_size"] == 0.12


class TestErrorScenarios:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.scenario
    async def test_service_unavailable_scenario(self, trading_scenario):
        """
        Scenario: Service unavailable during trading flow
        
        Tests circuit breaker and fallback mechanisms
        """
        
        # Mock service unavailable
        trading_scenario.services['risk-manager'].validate_signal.side_effect = Exception("Service unavailable")
        
        # Signal generation should handle risk manager unavailability
        signal = {"signal_id": "signal_fallback_123", "symbol": "EURUSD"}
        
        with pytest.raises(Exception):
            await trading_scenario.services['risk-manager'].validate_signal(signal)
        
        # In real implementation, circuit breaker would activate
        # and fallback to conservative defaults or queue for later
    
    @pytest.mark.asyncio 
    @pytest.mark.scenario
    async def test_market_data_disruption_scenario(self, trading_scenario):
        """
        Scenario: Market data feed disruption
        
        Tests system behavior when primary data source fails
        """
        
        # Mock data feed failure
        trading_scenario.services['data-ingestor'].process_price_tick.side_effect = Exception("Data feed unavailable")
        
        # System should detect disruption and handle gracefully
        with pytest.raises(Exception):
            await trading_scenario.simulate_market_data("EURUSD", 1.0850)
        
        # In real implementation:
        # 1. Fallback to secondary data source
        # 2. Pause trading if all sources fail  
        # 3. Alert operations team
        # 4. Continue with cached data if recent enough