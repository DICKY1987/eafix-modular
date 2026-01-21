# doc_id: DOC-TEST-0078
# DOC_ID: DOC-TEST-0027
"""
Consumer contract tests for execution-engine service.
Defines contracts that execution-engine expects from its dependencies.
"""

import pytest
import asyncio
from datetime import datetime, timezone

from ..framework.contract_testing import (
    ContractBuilder, ContractStore, Matcher, MatchingRule, ContractTestCase
)


class TestExecutionEngineContracts(ContractTestCase):
    """Contract tests from execution-engine's perspective as a consumer."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        super().__init__()
        yield
    
    @pytest.mark.asyncio
    @pytest.mark.consumer
    @pytest.mark.contract
    async def test_broker_api_order_submission_contract(self):
        """Contract: execution-engine -> broker-api for order submission."""
        
        contract = (ContractBuilder("execution-engine", "broker-api")
            .given("broker is available and account has sufficient margin")
            .upon_receiving("a market order submission request")
            .with_request(
                method="POST",
                path="/api/v1/orders",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer broker_api_token",
                    "X-Account-ID": "trading_account_123"
                },
                body={
                    "symbol": "EURUSD",
                    "side": "buy",
                    "quantity": 0.1,
                    "order_type": "market",
                    "client_order_id": "eafix_order_123",
                    "time_in_force": "IOC"
                }
            )
            .with_matcher("$.request.body.client_order_id", Matcher(MatchingRule.REGEX, regex=r"eafix_order_\w+"))
            .with_matcher("$.request.body.quantity", Matcher(MatchingRule.NUMERIC))
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "broker_order_id": "broker_12345",
                    "client_order_id": "eafix_order_123",
                    "status": "filled",
                    "symbol": "EURUSD",
                    "side": "buy",
                    "quantity": 0.1,
                    "fill_price": 1.0851,
                    "fill_quantity": 0.1,
                    "commission": 2.50,
                    "currency": "USD",
                    "execution_time": "2023-12-07T10:30:15.123Z",
                    "remaining_quantity": 0.0
                }
            )
            .with_matcher("$.response.body.broker_order_id", Matcher(MatchingRule.REGEX, regex=r"broker_\w+"))
            .with_matcher("$.response.body.fill_price", Matcher(MatchingRule.NUMERIC))
            .with_matcher("$.response.body.execution_time", Matcher(MatchingRule.DATETIME))
            .build()
        )
        
        self.store.save_contract(contract)
        await self.verify_contract("execution-engine", "broker-api", "1.0.0")
    
    @pytest.mark.asyncio
    @pytest.mark.consumer
    @pytest.mark.contract
    async def test_broker_api_order_cancellation_contract(self):
        """Contract: execution-engine -> broker-api for order cancellation."""
        
        contract = (ContractBuilder("execution-engine", "broker-api")
            .given("order exists and is cancellable")
            .upon_receiving("an order cancellation request")
            .with_request(
                method="DELETE",
                path="/api/v1/orders/broker_12345",
                headers={
                    "Authorization": "Bearer broker_api_token",
                    "X-Account-ID": "trading_account_123"
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "broker_order_id": "broker_12345",
                    "status": "cancelled",
                    "cancelled_at": "2023-12-07T10:35:20.456Z",
                    "remaining_quantity": 0.0,
                    "cancellation_reason": "client_request"
                }
            )
            .with_matcher("$.response.body.cancelled_at", Matcher(MatchingRule.DATETIME))
            .build()
        )
        
        self.store.save_contract(contract)
        await self.verify_contract("execution-engine", "broker-api", "1.0.0")
    
    @pytest.mark.asyncio
    @pytest.mark.consumer
    @pytest.mark.contract
    async def test_broker_api_order_rejection_contract(self):
        """Contract: execution-engine -> broker-api for order rejection scenarios."""
        
        contract = (ContractBuilder("execution-engine", "broker-api")
            .given("insufficient margin or invalid parameters")
            .upon_receiving("an order submission with insufficient margin")
            .with_request(
                method="POST",
                path="/api/v1/orders",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer broker_api_token",
                    "X-Account-ID": "trading_account_123"
                },
                body={
                    "symbol": "EURUSD",
                    "side": "buy", 
                    "quantity": 10.0,  # Very large quantity
                    "order_type": "market",
                    "client_order_id": "eafix_order_large_456"
                }
            )
            .will_respond_with(
                status=400,
                headers={"Content-Type": "application/json"},
                body={
                    "error": "insufficient_margin",
                    "error_description": "Insufficient margin for requested position size",
                    "client_order_id": "eafix_order_large_456",
                    "required_margin": 100000.0,
                    "available_margin": 5000.0,
                    "rejected_at": "2023-12-07T10:30:16.789Z"
                }
            )
            .with_matcher("$.response.body.required_margin", Matcher(MatchingRule.NUMERIC))
            .with_matcher("$.response.body.available_margin", Matcher(MatchingRule.NUMERIC))
            .with_matcher("$.response.body.rejected_at", Matcher(MatchingRule.DATETIME))
            .build()
        )
        
        self.store.save_contract(contract)
        await self.verify_contract("execution-engine", "broker-api", "1.0.0")
    
    @pytest.mark.asyncio
    @pytest.mark.consumer 
    @pytest.mark.contract
    async def test_position_manager_get_positions_contract(self):
        """Contract: execution-engine -> position-manager for position queries."""
        
        contract = (ContractBuilder("execution-engine", "position-manager")
            .given("positions exist for account")
            .upon_receiving("a request for current positions")
            .with_request(
                method="GET",
                path="/positions",
                query={"account_id": "trading_account_123", "symbol": "EURUSD"},
                headers={"Accept": "application/json"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "positions": [
                        {
                            "position_id": "pos_789",
                            "symbol": "EURUSD",
                            "side": "long",
                            "quantity": 0.2,
                            "entry_price": 1.0845,
                            "current_price": 1.0855,
                            "unrealized_pnl": 20.0,
                            "margin_used": 200.0,
                            "opened_at": "2023-12-07T09:15:30.123Z"
                        }
                    ],
                    "total_positions": 1,
                    "total_unrealized_pnl": 20.0,
                    "total_margin_used": 200.0,
                    "account_balance": 4980.0,
                    "free_margin": 4780.0
                }
            )
            .with_matcher("$.response.body.positions", Matcher(MatchingRule.ARRAY_MIN_LENGTH, min_length=0))
            .with_matcher("$.response.body.positions[0].unrealized_pnl", Matcher(MatchingRule.NUMERIC))
            .with_matcher("$.response.body.account_balance", Matcher(MatchingRule.NUMERIC))
            .build()
        )
        
        self.store.save_contract(contract)
        await self.verify_contract("execution-engine", "position-manager", "1.0.0")
    
    @pytest.mark.asyncio
    @pytest.mark.consumer
    @pytest.mark.contract
    async def test_market_data_get_current_prices_contract(self):
        """Contract: execution-engine -> market-data for current price quotes."""
        
        contract = (ContractBuilder("execution-engine", "market-data")
            .given("market is open and prices are available")
            .upon_receiving("a request for current market prices")
            .with_request(
                method="GET",
                path="/quotes/current",
                query={"symbols": "EURUSD,GBPUSD,USDJPY"},
                headers={"Accept": "application/json"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "quotes": [
                        {
                            "symbol": "EURUSD",
                            "bid": 1.0849,
                            "ask": 1.0851,
                            "spread": 0.0002,
                            "timestamp": "2023-12-07T10:30:14.567Z"
                        },
                        {
                            "symbol": "GBPUSD", 
                            "bid": 1.2645,
                            "ask": 1.2648,
                            "spread": 0.0003,
                            "timestamp": "2023-12-07T10:30:14.567Z"
                        },
                        {
                            "symbol": "USDJPY",
                            "bid": 149.85,
                            "ask": 149.88,
                            "spread": 0.03,
                            "timestamp": "2023-12-07T10:30:14.567Z"
                        }
                    ],
                    "server_time": "2023-12-07T10:30:14.567Z",
                    "market_status": "open"
                }
            )
            .with_matcher("$.response.body.quotes[0].bid", Matcher(MatchingRule.NUMERIC))
            .with_matcher("$.response.body.quotes[0].ask", Matcher(MatchingRule.NUMERIC))
            .with_matcher("$.response.body.quotes[0].timestamp", Matcher(MatchingRule.DATETIME))
            .build()
        )
        
        self.store.save_contract(contract)
        await self.verify_contract("execution-engine", "market-data", "1.0.0")
    
    @pytest.mark.asyncio
    @pytest.mark.consumer
    @pytest.mark.contract
    async def test_message_bus_execution_events_contract(self):
        """Contract: execution-engine publishes execution events to message bus."""
        
        contract = (ContractBuilder("execution-engine", "message-bus")
            .given("message bus is available")
            .upon_publishing("order execution completed", "trading.orders.executed")
            .with_message(
                message_type="OrderExecuted",
                schema_version="1.0",
                payload={
                    "execution_id": "exec_456",
                    "order_id": "order_123",
                    "broker_order_id": "broker_789",
                    "signal_id": "signal_123",
                    "symbol": "EURUSD",
                    "side": "buy",
                    "quantity": 0.1,
                    "fill_price": 1.0851,
                    "fill_quantity": 0.1,
                    "commission": 2.50,
                    "execution_time": "2023-12-07T10:30:15.123Z",
                    "slippage": 0.0001,
                    "execution_venue": "prime_broker_1"
                },
                metadata={
                    "source_service": "execution-engine", 
                    "correlation_id": "corr_789",
                    "idempotency_key": "order_execution_123",
                    "account_id": "trading_account_123"
                }
            )
            .with_matcher("$.message.payload.execution_id", Matcher(MatchingRule.REGEX, regex=r"exec_\w+"))
            .with_matcher("$.message.payload.fill_price", Matcher(MatchingRule.NUMERIC))
            .with_matcher("$.message.payload.execution_time", Matcher(MatchingRule.DATETIME))
            .with_matcher("$.message.payload.slippage", Matcher(MatchingRule.NUMERIC))
            .build()
        )
        
        self.store.save_contract(contract)
        # Message contracts verified differently
    
    @pytest.mark.asyncio
    @pytest.mark.consumer
    @pytest.mark.contract
    async def test_compliance_service_trade_reporting_contract(self):
        """Contract: execution-engine -> compliance-service for trade reporting."""
        
        contract = (ContractBuilder("execution-engine", "compliance-service")
            .given("compliance service is available")
            .upon_receiving("a trade reporting request")
            .with_request(
                method="POST",
                path="/reports/trades",
                headers={"Content-Type": "application/json"},
                body={
                    "trade_id": "trade_456",
                    "execution_id": "exec_456",
                    "symbol": "EURUSD",
                    "side": "buy",
                    "quantity": 0.1,
                    "price": 1.0851,
                    "execution_time": "2023-12-07T10:30:15.123Z",
                    "counterparty": "prime_broker_1",
                    "trade_venue": "otc",
                    "regulatory_flags": {
                        "mifid_ii": True,
                        "dodd_frank": False,
                        "emir": True
                    }
                }
            )
            .will_respond_with(
                status=201,
                headers={"Content-Type": "application/json"},
                body={
                    "report_id": "report_789",
                    "trade_id": "trade_456", 
                    "status": "submitted",
                    "regulatory_submissions": [
                        {
                            "regulation": "MiFID II",
                            "submission_id": "mifid_sub_123",
                            "status": "submitted",
                            "submitted_at": "2023-12-07T10:30:20.456Z"
                        }
                    ],
                    "created_at": "2023-12-07T10:30:16.789Z"
                }
            )
            .with_matcher("$.response.body.report_id", Matcher(MatchingRule.REGEX, regex=r"report_\w+"))
            .with_matcher("$.response.body.created_at", Matcher(MatchingRule.DATETIME))
            .build()
        )
        
        self.store.save_contract(contract)
        await self.verify_contract("execution-engine", "compliance-service", "1.0.0")
    
    async def teardown(self):
        """Clean up test resources."""
        await super().teardown()