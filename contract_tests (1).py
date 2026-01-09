# DOC_ID: DOC-CONTRACT-0001
# tests/contracts/test_service_contracts.py

import pytest
import asyncio
import json
from typing import Dict, Any, List
from pathlib import Path
import jsonschema
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from tests.conftest import TestCategories, TestDataFactory, ContractValidator


@TestCategories.CONTRACT
class TestServiceAPIContracts:
    """Test API contracts between services"""
    
    def test_data_ingestor_api_contract(self, test_client, contract_validator):
        """Test data ingestor API contract"""
        
        # Test GET /api/v1/status endpoint
        response = test_client.get("/api/v1/status")
        assert response.status_code == 200
        
        expected_schema = {
            "type": "object",
            "required": ["status", "version", "uptime"],
            "properties": {
                "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
                "version": {"type": "string"},
                "uptime": {"type": "number"},
                "metrics": {
                    "type": "object",
                    "properties": {
                        "processed_ticks": {"type": "integer"},
                        "error_rate": {"type": "number"},
                        "latency_p99": {"type": "number"}
                    }
                }
            }
        }
        
        contract_validator.validate_response_schema(response.json(), expected_schema)
    
    def test_indicator_engine_api_contract(self, test_client, contract_validator):
        """Test indicator engine API contract"""
        
        # Mock indicator calculation request
        request_data = {
            "symbol": "EURUSD",
            "indicator": "sma",
            "period": 20,
            "data": [1.0950, 1.0955, 1.0948, 1.0952]
        }
        
        with patch('services.indicator_engine.core.IndicatorEngine.calculate') as mock_calc:
            mock_calc.return_value = {
                "indicator": "sma",
                "value": 1.0951,
                "timestamp": "2024-01-01T12:00:00Z",
                "confidence": 0.95
            }
            
            response = test_client.post("/api/v1/calculate", json=request_data)
            assert response.status_code == 200
            
            expected_response_schema = {
                "type": "object",
                "required": ["indicator", "value", "timestamp"],
                "properties": {
                    "indicator": {"type": "string"},
                    "value": {"type": "number"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "metadata": {"type": "object"}
                }
            }
            
            contract_validator.validate_response_schema(response.json(), expected_response_schema)
    
    def test_signal_generator_api_contract(self, test_client, contract_validator):
        """Test signal generator API contract"""
        
        request_data = {
            "symbol": "EURUSD", 
            "indicators": {
                "sma_20": 1.0951,
                "rsi_14": 65.5,
                "macd": 0.0015
            },
            "market_data": {
                "price": 1.0952,
                "volume": 1000000,
                "spread": 0.0002
            }
        }
        
        with patch('services.signal_generator.core.SignalGenerator.generate') as mock_gen:
            mock_gen.return_value = {
                "signal_id": "SIG_001",
                "symbol": "EURUSD",
                "direction": "BUY",
                "strength": 0.75,
                "entry_price": 1.0952,
                "stop_loss": 1.0900,
                "take_profit": 1.1000,
                "confidence": 0.85,
                "timestamp": "2024-01-01T12:00:00Z"
            }
            
            response = test_client.post("/api/v1/generate-signal", json=request_data)
            assert response.status_code == 200
            
            expected_schema = {
                "type": "object",
                "required": ["signal_id", "symbol", "direction", "strength", "timestamp"],
                "properties": {
                    "signal_id": {"type": "string"},
                    "symbol": {"type": "string"},
                    "direction": {"type": "string", "enum": ["BUY", "SELL", "HOLD"]},
                    "strength": {"type": "number", "minimum": 0, "maximum": 1},
                    "entry_price": {"type": "number"},
                    "stop_loss": {"type": "number"},
                    "take_profit": {"type": "number"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            }
            
            contract_validator.validate_response_schema(response.json(), expected_schema)
    
    def test_risk_manager_api_contract(self, test_client, contract_validator):
        """Test risk manager API contract"""
        
        request_data = {
            "signal": TestDataFactory.create_trading_signal(),
            "portfolio": {
                "balance": 10000.0,
                "equity": 9850.0,
                "margin_used": 500.0,
                "open_positions": 3
            },
            "risk_parameters": {
                "max_risk_per_trade": 0.02,
                "max_portfolio_risk": 0.10,
                "max_positions": 5
            }
        }
        
        with patch('services.risk_manager.core.RiskManager.assess') as mock_assess:
            mock_assess.return_value = {
                "approved": True,
                "risk_score": 0.15,
                "position_size": 0.1,
                "adjusted_stop_loss": 1.0900,
                "adjusted_take_profit": 1.1000,
                "risk_metrics": {
                    "value_at_risk": 150.0,
                    "expected_loss": 50.0,
                    "reward_risk_ratio": 2.5
                }
            }
            
            response = test_client.post("/api/v1/assess-risk", json=request_data)
            assert response.status_code == 200
            
            expected_schema = {
                "type": "object",
                "required": ["approved", "risk_score"],
                "properties": {
                    "approved": {"type": "boolean"},
                    "risk_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "position_size": {"type": "number"},
                    "adjusted_stop_loss": {"type": "number"},
                    "adjusted_take_profit": {"type": "number"},
                    "risk_metrics": {
                        "type": "object",
                        "properties": {
                            "value_at_risk": {"type": "number"},
                            "expected_loss": {"type": "number"},
                            "reward_risk_ratio": {"type": "number"}
                        }
                    },
                    "rejection_reason": {"type": "string"}
                }
            }
            
            contract_validator.validate_response_schema(response.json(), expected_schema)


@TestCategories.CONTRACT
class TestEventContracts:
    """Test event message contracts"""
    
    def test_market_data_event_contract(self, contract_validator):
        """Test market data event schema"""
        
        event_data = {
            "event_type": "market_data",
            "event_id": "md_001",
            "timestamp": "2024-01-01T12:00:00Z",
            "source": "data-ingestor",
            "data": {
                "symbol": "EURUSD",
                "bid": 1.0950,
                "ask": 1.0952,
                "volume": 1000000,
                "spread": 0.0002,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
        
        contract_validator.validate_event_schema(event_data, "market_data")
    
    def test_indicator_calculated_event_contract(self, contract_validator):
        """Test indicator calculated event schema"""
        
        event_data = {
            "event_type": "indicator_calculated",
            "event_id": "ind_001", 
            "timestamp": "2024-01-01T12:00:00Z",
            "source": "indicator-engine",
            "data": {
                "symbol": "EURUSD",
                "indicator": "sma",
                "period": 20,
                "value": 1.0951,
                "confidence": 0.95,
                "calculation_time_ms": 15
            }
        }
        
        contract_validator.validate_event_schema(event_data, "indicator_calculated")
    
    def test_signal_generated_event_contract(self, contract_validator):
        """Test signal generated event schema"""
        
        event_data = {
            "event_type": "signal_generated",
            "event_id": "sig_001",
            "timestamp": "2024-01-01T12:00:00Z",
            "source": "signal-generator",
            "data": {
                "signal_id": "SIG_001",
                "symbol": "EURUSD",
                "direction": "BUY",
                "strength": 0.75,
                "entry_price": 1.0952,
                "stop_loss": 1.0900,
                "take_profit": 1.1000,
                "confidence": 0.85,
                "indicators_used": ["sma_20", "rsi_14", "macd"],
                "generation_time_ms": 25
            }
        }
        
        contract_validator.validate_event_schema(event_data, "signal_generated")
    
    def test_order_placed_event_contract(self, contract_validator):
        """Test order placed event schema"""
        
        event_data = {
            "event_type": "order_placed",
            "event_id": "ord_001",
            "timestamp": "2024-01-01T12:00:00Z",
            "source": "execution-engine",
            "data": {
                "order_id": "ORD_12345",
                "signal_id": "SIG_001",
                "symbol": "EURUSD",
                "order_type": "MARKET",
                "direction": "BUY",
                "volume": 0.1,
                "price": 1.0952,
                "stop_loss": 1.0900,
                "take_profit": 1.1000,
                "status": "PENDING",
                "broker": "mt4_demo"
            }
        }
        
        contract_validator.validate_event_schema(event_data, "order_placed")


@TestCategories.CONTRACT
class TestServiceIntegrationContracts:
    """Test contracts between service integrations"""
    
    @pytest.mark.asyncio
    async def test_data_flow_contract(self, contract_validator):
        """Test complete data flow contract from ingestion to execution"""
        
        # 1. Market data ingestion
        market_data = {
            "symbol": "EURUSD",
            "bid": 1.0950,
            "ask": 1.0952,
            "volume": 1000000,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        # 2. Indicator calculation request
        indicator_request = {
            "symbol": "EURUSD",
            "indicator": "sma",
            "period": 20,
            "price_data": [1.0950, 1.0955, 1.0948, 1.0952]
        }
        
        # 3. Signal generation request
        signal_request = {
            "symbol": "EURUSD",
            "indicators": {"sma_20": 1.0951},
            "market_data": market_data
        }
        
        # 4. Risk assessment request
        risk_request = {
            "signal": TestDataFactory.create_trading_signal(),
            "portfolio": {"balance": 10000.0, "equity": 9850.0}
        }
        
        # 5. Order execution request
        execution_request = {
            "signal_id": "SIG_001",
            "symbol": "EURUSD",
            "direction": "BUY",
            "volume": 0.1,
            "order_type": "MARKET"
        }
        
        # Validate each step's contract
        schemas = [
            ("market_data", market_data),
            ("indicator_request", indicator_request),
            ("signal_request", signal_request),
            ("risk_request", risk_request),
            ("execution_request", execution_request)
        ]
        
        for schema_name, data in schemas:
            try:
                contract_validator.validate_event_schema(data, schema_name)
            except Exception as e:
                pytest.fail(f"Contract validation failed for {schema_name}: {e}")
    
    def test_error_response_contracts(self, test_client, contract_validator):
        """Test error response contracts are consistent across services"""
        
        # Test various error scenarios
        error_scenarios = [
            ("/api/v1/nonexistent", 404),
            ("/api/v1/calculate", 422),  # Invalid request body
        ]
        
        expected_error_schema = {
            "type": "object",
            "required": ["error", "message", "timestamp"],
            "properties": {
                "error": {"type": "string"},
                "message": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "details": {"type": "object"},
                "request_id": {"type": "string"}
            }
        }
        
        for endpoint, expected_status in error_scenarios:
            if expected_status == 422:
                response = test_client.post(endpoint, json={"invalid": "data"})
            else:
                response = test_client.get(endpoint)
            
            assert response.status_code == expected_status
            
            if response.status_code >= 400:
                contract_validator.validate_response_schema(
                    response.json(), 
                    expected_error_schema
                )


@TestCategories.CONTRACT 
class TestAPIVersioningContracts:
    """Test API versioning contracts"""
    
    def test_version_header_contract(self, test_client):
        """Test API version header contract"""
        
        response = test_client.get("/api/v1/status")
        assert response.status_code == 200
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "1.0.0"
    
    def test_backward_compatibility_contract(self, test_client):
        """Test backward compatibility contract"""
        
        # Test that v1 API still works when v2 is available
        v1_response = test_client.get("/api/v1/status")
        assert v1_response.status_code == 200
        
        # If v2 exists, it should also work
        v2_response = test_client.get("/api/v2/status")
        # Should either work (200) or not exist (404), but not error (5xx)
        assert v2_response.status_code in [200, 404]
    
    def test_deprecation_header_contract(self, test_client):
        """Test deprecation header contract"""
        
        # Mock deprecated endpoint
        with patch('services.common.base_enterprise_service.BaseEnterpriseService') as mock_service:
            mock_service.deprecated_endpoints = ["/api/v1/legacy"]
            
            response = test_client.get("/api/v1/legacy")
            
            if response.status_code == 200:
                assert "X-Deprecated" in response.headers
                assert "X-Sunset" in response.headers


@TestCategories.CONTRACT
class TestPerformanceContracts:
    """Test performance contracts/SLAs"""
    
    @pytest.mark.performance
    def test_response_time_contracts(self, test_client, performance_monitor):
        """Test response time SLA contracts"""
        
        performance_monitor.start()
        
        # Define SLA targets (in seconds)
        sla_targets = {
            "/health": 0.010,         # 10ms
            "/ready": 0.010,          # 10ms  
            "/api/v1/status": 0.050,  # 50ms
            "/metrics": 0.100,        # 100ms
        }
        
        for endpoint, target_time in sla_targets.items():
            start_time = asyncio.get_event_loop().time()
            
            response = test_client.get(endpoint)
            
            response_time = asyncio.get_event_loop().time() - start_time
            performance_monitor.record_metric(f"{endpoint}_response_time", response_time)
            
            assert response.status_code in [200, 404]  # Allow 404 for optional endpoints
            assert response_time <= target_time, f"{endpoint} response time {response_time:.3f}s exceeds SLA {target_time}s"
    
    @pytest.mark.performance
    def test_throughput_contracts(self, test_client, performance_monitor):
        """Test throughput SLA contracts"""
        
        import concurrent.futures
        import time
        
        def make_request():
            return test_client.get("/health")
        
        # Test concurrent requests
        num_requests = 100
        max_duration = 5.0  # 5 seconds for 100 requests = 20 RPS minimum
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        duration = time.time() - start_time
        throughput = num_requests / duration
        
        performance_monitor.record_metric("throughput_rps", throughput)
        
        # Assert minimum throughput
        assert throughput >= 20, f"Throughput {throughput:.1f} RPS below minimum 20 RPS"
        assert duration <= max_duration, f"Duration {duration:.1f}s exceeds maximum {max_duration}s"
        
        # Assert all requests succeeded
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == num_requests, f"Only {success_count}/{num_requests} requests succeeded"


@TestCategories.CONTRACT
class TestSecurityContracts:
    """Test security contracts"""
    
    def test_authentication_contract(self, test_client):
        """Test authentication contract"""
        
        # Test unauthenticated access to protected endpoint
        response = test_client.get("/api/v1/protected")
        assert response.status_code == 401
        
        # Test invalid token
        headers = {"Authorization": "Bearer invalid-token"}
        response = test_client.get("/api/v1/protected", headers=headers)
        assert response.status_code == 403
    
    def test_authorization_contract(self, test_client):
        """Test authorization contract"""
        
        # Mock different user roles
        test_cases = [
            ("guest", ["/api/v1/read-only"], ["/api/v1/admin"]),
            ("trader", ["/api/v1/trading"], ["/api/v1/admin"]), 
            ("admin", ["/api/v1/admin"], [])
        ]
        
        for role, allowed_endpoints, forbidden_endpoints in test_cases:
            # Mock JWT token for role
            mock_token = f"mock-{role}-token"
            headers = {"Authorization": f"Bearer {mock_token}"}
            
            with patch('services.common.security.verify_token') as mock_verify:
                mock_verify.return_value = {"role": role}
                
                # Test allowed endpoints
                for endpoint in allowed_endpoints:
                    response = test_client.get(endpoint, headers=headers)
                    assert response.status_code in [200, 404], f"{role} should access {endpoint}"
                
                # Test forbidden endpoints
                for endpoint in forbidden_endpoints:
                    response = test_client.get(endpoint, headers=headers)
                    assert response.status_code == 403, f"{role} should not access {endpoint}"
    
    def test_input_validation_contract(self, test_client, contract_validator):
        """Test input validation contract"""
        
        # Test various invalid inputs
        invalid_inputs = [
            {"symbol": ""},           # Empty symbol
            {"symbol": "INVALID123"}, # Invalid symbol format
            {"volume": -1},           # Negative volume
            {"volume": "not_a_number"}, # Wrong type
        ]
        
        for invalid_input in invalid_inputs:
            response = test_client.post("/api/v1/validate-input", json=invalid_input)
            assert response.status_code == 422, f"Should reject invalid input: {invalid_input}"
            
            # Validate error response format
            error_schema = {
                "type": "object",
                "required": ["detail"],
                "properties": {
                    "detail": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["loc", "msg", "type"],
                            "properties": {
                                "loc": {"type": "array"},
                                "msg": {"type": "string"},
                                "type": {"type": "string"}
                            }
                        }
                    }
                }
            }
            
            contract_validator.validate_response_schema(response.json(), error_schema)