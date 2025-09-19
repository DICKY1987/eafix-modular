"""
Contract testing pytest configuration and shared fixtures.
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from typing import Dict, Any, AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, timezone

from framework.contract_testing import ContractStore, ContractVerifier


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def contract_store():
    """Provide a contract store for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield ContractStore(temp_dir)


@pytest.fixture
def contract_verifier():
    """Provide a contract verifier for provider tests."""
    return ContractVerifier("http://localhost:8084")  # Default to risk-manager


@pytest.fixture
def redis_client():
    """Mock Redis client for testing."""
    mock_redis = AsyncMock()
    mock_redis.publish = AsyncMock()
    mock_redis.subscribe = AsyncMock()
    mock_redis.get = AsyncMock()
    mock_redis.set = AsyncMock()
    return mock_redis


@pytest.fixture
def sample_price_tick():
    """Sample price tick data for testing."""
    return {
        "symbol": "EURUSD",
        "bid": 1.0849,
        "ask": 1.0851,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "volume": 1000000,
        "spread": 0.0002
    }


@pytest.fixture
def sample_trading_signal():
    """Sample trading signal data for testing."""
    return {
        "signal_id": "signal_test_123",
        "symbol": "EURUSD",
        "direction": "long",
        "confidence": 0.85,
        "entry_price": 1.0850,
        "stop_loss": 1.0800,
        "take_profit": 1.0900,
        "position_size": 0.1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_risk_validation():
    """Sample risk validation response for testing."""
    return {
        "validation_id": "validation_test_456",
        "signal_id": "signal_test_123",
        "status": "approved",
        "risk_score": 0.3,
        "position_size_adjustment": 0.1,
        "warnings": [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_order_intent():
    """Sample order intent data for testing."""
    return {
        "order_id": "order_test_789",
        "signal_id": "signal_test_123",
        "symbol": "EURUSD",
        "side": "buy",
        "quantity": 0.1,
        "order_type": "market",
        "price": 1.0850,
        "stop_loss": 1.0800,
        "take_profit": 1.0900,
        "time_in_force": "IOC",
        "client_order_id": "eafix_order_test_789"
    }


@pytest.fixture
def sample_execution_report():
    """Sample execution report data for testing."""
    return {
        "execution_id": "exec_test_101",
        "order_id": "order_test_789",
        "broker_order_id": "broker_test_456",
        "signal_id": "signal_test_123",
        "symbol": "EURUSD",
        "side": "buy",
        "quantity": 0.1,
        "fill_price": 1.0851,
        "fill_quantity": 0.1,
        "commission": 2.50,
        "execution_time": datetime.now(timezone.utc).isoformat(),
        "status": "filled",
        "slippage": 0.0001
    }


@pytest.fixture
def sample_calendar_event():
    """Sample economic calendar event for testing."""
    return {
        "event_id": "nfp_test_2023_12_07",
        "currency": "USD",
        "title": "Nonfarm Payrolls",
        "impact": "high",
        "scheduled_time": "2023-12-07T13:30:00Z",
        "forecast": "180K",
        "previous": "150K",
        "actual": None,
        "description": "US monthly employment change"
    }


@pytest.fixture
def sample_reentry_decision():
    """Sample re-entry decision data for testing."""
    return {
        "reentry_id": "reentry_test_789",
        "position_id": "pos_closed_123",
        "decision": "approved",
        "confidence": 0.75,
        "wait_time_minutes": 15,
        "conditions": [
            "previous_trade_profitable",
            "market_conditions_stable"
        ],
        "recommended_position_size": 0.12
    }


@pytest.fixture
def mock_broker_api():
    """Mock broker API for testing."""
    mock_api = AsyncMock()
    
    # Configure default responses
    mock_api.submit_order = AsyncMock(return_value={
        "broker_order_id": "broker_12345",
        "status": "filled",
        "fill_price": 1.0851,
        "execution_time": datetime.now(timezone.utc).isoformat()
    })
    
    mock_api.cancel_order = AsyncMock(return_value={
        "broker_order_id": "broker_12345",
        "status": "cancelled",
        "cancelled_at": datetime.now(timezone.utc).isoformat()
    })
    
    return mock_api


@pytest.fixture
def mock_market_data():
    """Mock market data service for testing."""
    mock_service = AsyncMock()
    
    mock_service.get_current_prices = AsyncMock(return_value={
        "quotes": [
            {
                "symbol": "EURUSD",
                "bid": 1.0849,
                "ask": 1.0851,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
    })
    
    return mock_service


@pytest.fixture
def mock_position_manager():
    """Mock position manager service for testing."""
    mock_service = AsyncMock()
    
    mock_service.get_positions = AsyncMock(return_value={
        "positions": [
            {
                "position_id": "pos_789",
                "symbol": "EURUSD",
                "side": "long",
                "quantity": 0.2,
                "entry_price": 1.0845,
                "unrealized_pnl": 20.0
            }
        ],
        "total_unrealized_pnl": 20.0
    })
    
    return mock_service


@pytest.fixture
def mock_compliance_service():
    """Mock compliance service for testing."""
    mock_service = AsyncMock()
    
    mock_service.report_trade = AsyncMock(return_value={
        "report_id": "report_789",
        "status": "submitted",
        "regulatory_submissions": [
            {
                "regulation": "MiFID II",
                "status": "submitted"
            }
        ]
    })
    
    return mock_service


@pytest.fixture
async def trading_scenario():
    """Comprehensive trading scenario fixture with all mock services."""
    from scenarios.test_trading_flow_scenarios import TradingScenarioTest
    
    scenario = TradingScenarioTest()
    await scenario.setup_services()
    
    # Configure additional mocks
    scenario.broker_api = mock_broker_api()
    scenario.market_data = mock_market_data()
    scenario.position_manager = mock_position_manager()
    scenario.compliance_service = mock_compliance_service()
    
    return scenario


@pytest.fixture
def contract_test_data():
    """Collection of test data for contract validation."""
    return {
        "valid_symbols": ["EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "AUDUSD"],
        "valid_directions": ["long", "short", "close"],
        "valid_order_types": ["market", "limit", "stop", "stop_limit"],
        "valid_time_in_force": ["IOC", "FOK", "GTC", "DAY"],
        "valid_currencies": ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"],
        "valid_impacts": ["low", "medium", "high"],
        "valid_statuses": {
            "orders": ["pending", "filled", "rejected", "cancelled"],
            "signals": ["generated", "validated", "executed", "expired"],
            "positions": ["open", "closed", "closing"]
        }
    }


@pytest.fixture
def performance_thresholds():
    """Performance thresholds for contract validation."""
    return {
        "max_response_time_ms": 100,
        "max_signal_generation_time_ms": 500,
        "max_order_execution_time_ms": 2000,
        "max_risk_validation_time_ms": 50,
        "max_concurrent_requests": 1000
    }


@pytest.fixture
def contract_matchers():
    """Common matchers for contract testing."""
    from framework.contract_testing import Matcher, MatchingRule
    
    return {
        "signal_id": Matcher(MatchingRule.REGEX, regex=r"signal_\w+"),
        "order_id": Matcher(MatchingRule.REGEX, regex=r"order_\w+"),
        "execution_id": Matcher(MatchingRule.REGEX, regex=r"exec_\w+"),
        "validation_id": Matcher(MatchingRule.REGEX, regex=r"validation_\w+"),
        "broker_order_id": Matcher(MatchingRule.REGEX, regex=r"broker_\w+"),
        "position_id": Matcher(MatchingRule.REGEX, regex=r"pos_\w+"),
        "correlation_id": Matcher(MatchingRule.REGEX, regex=r"corr_\w+"),
        "timestamp": Matcher(MatchingRule.DATETIME),
        "numeric": Matcher(MatchingRule.NUMERIC),
        "price": Matcher(MatchingRule.NUMERIC),
        "quantity": Matcher(MatchingRule.NUMERIC),
        "confidence": Matcher(MatchingRule.NUMERIC),
        "array_min_0": Matcher(MatchingRule.ARRAY_MIN_LENGTH, min_length=0)
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up common test environment variables."""
    import os
    
    # Test environment configuration
    os.environ["REDIS_URL"] = "redis://localhost:6379"
    os.environ["TEST_MODE"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["CONTRACT_STORE_PATH"] = "tests/contracts/store"
    
    # Service endpoints for provider testing
    os.environ["RISK_MANAGER_URL"] = "http://localhost:8084"
    os.environ["SIGNAL_GENERATOR_URL"] = "http://localhost:8083"
    os.environ["EXECUTION_ENGINE_URL"] = "http://localhost:8085"
    os.environ["INDICATOR_ENGINE_URL"] = "http://localhost:8082"
    os.environ["DATA_INGESTOR_URL"] = "http://localhost:8081"
    
    yield
    
    # Cleanup (if needed)
    pass


class ContractTestMixin:
    """Mixin class with common contract testing utilities."""
    
    def assert_contract_response_structure(self, response: Dict[str, Any], expected_fields: list):
        """Assert response contains expected fields."""
        for field in expected_fields:
            assert field in response, f"Missing required field: {field}"
    
    def assert_valid_timestamp(self, timestamp_str: str):
        """Assert timestamp is valid ISO 8601 format."""
        try:
            datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp_str}")
    
    def assert_numeric_range(self, value: float, min_val: float, max_val: float):
        """Assert numeric value is within expected range."""
        assert min_val <= value <= max_val, f"Value {value} not in range [{min_val}, {max_val}]"
    
    def assert_valid_symbol(self, symbol: str, valid_symbols: list):
        """Assert trading symbol is valid."""
        assert symbol in valid_symbols, f"Invalid symbol: {symbol}"


@pytest.fixture
def contract_test_mixin():
    """Provide contract test mixin utilities."""
    return ContractTestMixin()


# Pytest markers for test organization
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "consumer: Consumer contract tests")
    config.addinivalue_line("markers", "provider: Provider verification tests")
    config.addinivalue_line("markers", "scenario: End-to-end scenario tests")
    config.addinivalue_line("markers", "property: Property-based tests")
    config.addinivalue_line("markers", "contract: All contract-related tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")


# Async test configuration
pytest_plugins = ['pytest_asyncio']


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on file path
        if "consumer" in item.nodeid:
            item.add_marker(pytest.mark.consumer)
        if "provider" in item.nodeid:
            item.add_marker(pytest.mark.provider)
        if "scenarios" in item.nodeid:
            item.add_marker(pytest.mark.scenario)
        if "properties" in item.nodeid:
            item.add_marker(pytest.mark.property)
        
        # Mark all contract tests
        if "contracts" in item.nodeid:
            item.add_marker(pytest.mark.contract)
        
        # Mark slow tests
        if "scenario" in item.nodeid or "integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)