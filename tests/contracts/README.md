---
doc_id: DOC-CONTRACT-0039
---

# Contract & Scenario Testing Framework

This directory contains the comprehensive contract and scenario testing suite for the EAFIX trading system. The testing framework implements consumer-driven contract testing (Pact-like), property-based testing, and end-to-end scenario validation.

## Framework Overview

### Contract Testing Approach

Our contract testing framework follows the **consumer-driven contracts** pattern:

1. **Consumers** define contracts specifying their expectations from providers
2. **Providers** verify they can satisfy all consumer contracts
3. **Contracts** serve as executable specifications and integration tests
4. **Scenarios** validate complete end-to-end trading workflows

### Testing Strategy

- **Consumer Tests**: Define contracts from the consumer's perspective
- **Provider Tests**: Verify provider implementations satisfy contracts
- **Scenario Tests**: End-to-end integration testing with mock services
- **Property-Based Tests**: Generate random valid data to verify contract invariants

## Directory Structure

```
tests/contracts/
├── framework/                    # Core testing framework
│   └── contract_testing.py      # Pact-like contract testing framework
├── consumer/                     # Consumer contract definitions
│   ├── test_signal_generator_contracts.py   # Signal generator as consumer
│   └── test_execution_engine_contracts.py   # Execution engine as consumer
├── provider/                     # Provider contract verification
│   └── test_risk_manager_provider.py        # Risk manager provider tests
├── scenarios/                    # End-to-end scenario tests
│   └── test_trading_flow_scenarios.py       # Complete trading flow scenarios
├── properties/                   # Property-based testing
│   └── test_property_based_contracts.py     # Hypothesis-based property tests
├── fixtures/                     # Test data and golden files
├── conftest.py                   # Pytest configuration and fixtures
└── README.md                     # This documentation
```

## Contract Testing Framework

### Core Components

1. **ContractBuilder**: Fluent API for defining contracts
2. **ContractStore**: Persistent storage for contract definitions
3. **ContractVerifier**: Verification engine for provider tests
4. **Matcher**: Flexible matching rules for contract validation

### Basic Contract Example

```python
from framework.contract_testing import ContractBuilder, Matcher, MatchingRule

# Define a consumer contract
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
            "confidence": 0.85
        }
    )
    .with_matcher("$.request.body.signal_id", Matcher(MatchingRule.REGEX, regex=r"signal_\\w+"))
    .will_respond_with(
        status=200,
        body={
            "validation_id": "validation_456",
            "status": "approved",
            "risk_score": 0.3
        }
    )
    .build()
)
```

### Matching Rules

The framework supports flexible matching rules:

- **EXACT**: Exact string or numeric matching
- **REGEX**: Regular expression matching
- **NUMERIC**: Any numeric value
- **DATETIME**: ISO 8601 datetime format
- **ARRAY_MIN_LENGTH**: Arrays with minimum length
- **TYPE**: Type-based matching (string, number, boolean)

## Running Contract Tests

### All Contract Tests

```bash
# Run complete contract test suite
poetry run pytest tests/contracts/ -v

# Run with coverage
poetry run pytest tests/contracts/ --cov=tests.contracts --cov-report=html
```

### Specific Test Categories

```bash
# Consumer contract tests only
poetry run pytest tests/contracts/consumer/ -v

# Provider verification tests only
poetry run pytest tests/contracts/provider/ -v

# Scenario-based integration tests
poetry run pytest tests/contracts/scenarios/ -v

# Property-based tests
poetry run pytest tests/contracts/properties/ -v
```

### Parallel Execution

```bash
# Run tests in parallel (recommended for CI)
poetry run pytest tests/contracts/ -n auto
```

## Consumer Contract Tests

Consumer tests define contracts from the perspective of services that depend on other services.

### Signal Generator Contracts

Tests in `consumer/test_signal_generator_contracts.py`:

- **Risk Manager Validation**: Signal validation and rejection contracts
- **Indicator Engine**: Technical indicator retrieval contracts
- **Calendar Ingestor**: Economic event data contracts
- **Message Bus**: Signal publication contracts

### Execution Engine Contracts

Tests in `consumer/test_execution_engine_contracts.py`:

- **Broker API**: Order submission, cancellation, and rejection contracts
- **Position Manager**: Position query and update contracts
- **Market Data**: Price quote and market status contracts
- **Compliance Service**: Trade reporting and regulatory contracts

## Provider Contract Tests

Provider tests verify that services can satisfy the contracts defined by their consumers.

### Risk Manager Provider Tests

Tests in `provider/test_risk_manager_provider.py`:

- **Signal Validation**: Verify risk manager can validate trading signals
- **Position Sizing**: Verify position size calculation capabilities
- **Risk Limits**: Verify risk limit enforcement
- **Error Handling**: Verify appropriate error responses
- **Performance**: Verify response time requirements

## Scenario-Based Integration Tests

Scenario tests validate complete end-to-end trading workflows using mock services.

### Trading Flow Scenarios

Tests in `scenarios/test_trading_flow_scenarios.py`:

#### Successful Trading Flow
1. Market data arrives → data-ingestor
2. Indicators computed → indicator-engine  
3. Signal generated → signal-generator
4. Risk validation → risk-manager
5. Order execution → execution-engine
6. Position update → reporter

#### Error Scenarios
- Signal rejection by risk manager
- Order execution failure and retry
- High-impact news event handling
- Re-entry decision processing
- Service unavailability handling
- Market data disruption

## Property-Based Testing

Property-based tests use the Hypothesis library to generate random valid trading data and verify contract properties.

### Trading Domain Generators

```python
from hypothesis import strategies as st, given
from hypothesis.strategies import composite

@composite
def trading_signal(draw):
    return {
        'signal_id': f"signal_{draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=6, max_size=12))}",
        'symbol': draw(currency_pair()),
        'direction': draw(st.sampled_from(['long', 'short', 'close'])),
        'confidence': draw(st.floats(min_value=0.0, max_value=1.0))
    }

@given(trading_signal())
def test_signal_contract_invariants(signal):
    # Verify signal always produces valid contract structure
    assert 'signal_id' in signal
    assert signal['confidence'] >= 0.0 and signal['confidence'] <= 1.0
    assert signal['direction'] in ['long', 'short', 'close']
```

### Contract Property Tests

- **Signal Properties**: Valid signal structure, confidence bounds, expiry logic
- **Order Properties**: Valid order data, quantity limits, price constraints
- **Execution Properties**: Fill price validation, commission calculations
- **Risk Properties**: Position size limits, risk score bounds
- **Calendar Properties**: Event scheduling, impact classifications

## Test Configuration

### Pytest Configuration (`conftest.py`)

```python
import pytest
import asyncio
from unittest.mock import AsyncMock
from framework.contract_testing import ContractStore

@pytest.fixture
def contract_store():
    return ContractStore("tests/contracts")

@pytest.fixture
def redis_client():
    return AsyncMock()

@pytest.fixture
async def trading_scenario():
    from scenarios.test_trading_flow_scenarios import TradingScenarioTest
    scenario = TradingScenarioTest()
    await scenario.setup_services()
    return scenario
```

### Environment Variables

```bash
# Test configuration
export REDIS_URL=redis://localhost:6379
export TEST_TIMEOUT=30
export CONTRACT_STORE_PATH=tests/contracts/store

# Provider verification endpoints
export RISK_MANAGER_URL=http://localhost:8084
export SIGNAL_GENERATOR_URL=http://localhost:8083
export EXECUTION_ENGINE_URL=http://localhost:8085
```

## Integration with CI/CD

### GitHub Actions Integration

The contract tests are integrated into the CI/CD pipeline:

```yaml
# .github/workflows/contract-tests.yml
- name: Run Contract Tests
  run: |
    poetry run pytest tests/contracts/ -v --junitxml=contract-test-results.xml
    
- name: Upload Contract Test Results
  uses: actions/upload-artifact@v3
  with:
    name: contract-test-results
    path: contract-test-results.xml
```

### Contract Validation in Pipeline

```bash
# Validate all contracts before deployment
make contracts-validate-full
make contracts-test
```

## Best Practices

### Writing Consumer Contracts

1. **Focus on Intent**: Define what the consumer needs, not how it's implemented
2. **Use Flexible Matchers**: Use regex and type matchers for non-critical fields
3. **Document Scenarios**: Use clear descriptions for contract interactions
4. **Version Contracts**: Include schema versions in contract definitions

### Provider Verification

1. **State Management**: Set up appropriate provider states for each contract
2. **Mock External Dependencies**: Isolate provider logic from external systems
3. **Error Scenario Coverage**: Test all error conditions specified in contracts
4. **Performance Testing**: Verify response times meet contract requirements

### Scenario Design

1. **Real-World Flows**: Model actual trading scenarios from production
2. **Error Injection**: Test system behavior under various failure conditions
3. **Data Validation**: Verify data consistency throughout the flow
4. **Timing Constraints**: Test time-sensitive operations like signal expiry

### Property-Based Testing

1. **Domain Constraints**: Generate data that respects trading domain rules
2. **Invariant Testing**: Focus on properties that must always be true
3. **Edge Case Discovery**: Let Hypothesis find edge cases automatically
4. **Reproducible Tests**: Use fixed seeds for debugging failing tests

## Troubleshooting

### Common Issues

1. **Contract Mismatches**: Check that consumer expectations match provider implementations
2. **Async Test Issues**: Ensure proper async/await usage in test fixtures
3. **Mock Configuration**: Verify mock services are properly configured for scenarios
4. **Data Generation**: Check Hypothesis strategies generate valid domain data

### Debugging Contract Failures

```bash
# Run specific failing contract test
poetry run pytest tests/contracts/consumer/test_signal_generator_contracts.py::TestSignalGeneratorContracts::test_risk_manager_validate_signal_contract -v -s

# Run with detailed output
poetry run pytest tests/contracts/ -v -s --tb=long

# Debug property-based test failures
poetry run pytest tests/contracts/properties/ --hypothesis-show-statistics
```

## Future Enhancements

### Planned Improvements

1. **Contract Compatibility Checking**: Automated contract evolution validation
2. **Performance Benchmarking**: Integrate performance requirements into contracts
3. **Cross-Language Contracts**: Extend to MQL4 integration contracts
4. **Contract Documentation Generation**: Auto-generate API docs from contracts
5. **Real Provider Testing**: Integration with actual service deployments

### Contributing

When adding new contracts:

1. Follow the consumer-driven approach
2. Add both positive and negative test cases
3. Include property-based tests for complex domains
4. Update documentation with new scenarios
5. Ensure CI/CD integration passes

This contract testing framework provides comprehensive validation of service interactions, ensuring reliable integration between EAFIX trading system components.