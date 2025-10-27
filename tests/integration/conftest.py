"""
Integration Test Configuration

Pytest configuration and fixtures for end-to-end integration testing
of the complete EAFIX modular trading system.
"""

import pytest
import asyncio
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock
import subprocess
import signal
import os

import httpx
import redis.asyncio as redis


class ServiceManager:
    """Manages test services lifecycle."""
    
    def __init__(self):
        self.services: Dict[str, Dict[str, Any]] = {}
        self.base_dir = Path(__file__).parent.parent.parent
        
    async def start_service(self, service_name: str, port: int, 
                          service_dir: str, timeout: int = 30) -> Dict[str, Any]:
        """Start a service for testing."""
        if service_name in self.services:
            return self.services[service_name]
        
        service_path = self.base_dir / "services" / service_dir
        if not service_path.exists():
            raise FileNotFoundError(f"Service directory not found: {service_path}")
        
        # Start service process
        env = os.environ.copy()
        env.update({
            f"{service_name.upper().replace('-', '_')}_SERVICE_PORT": str(port),
            f"{service_name.upper().replace('-', '_')}_DEBUG_MODE": "true",
            f"{service_name.upper().replace('-', '_')}_LOG_LEVEL": "DEBUG"
        })
        
        cmd = ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", str(port)]
        process = subprocess.Popen(
            cmd,
            cwd=service_path,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for service to be ready
        client = httpx.AsyncClient()
        service_ready = False
        
        for _ in range(timeout):
            try:
                response = await client.get(f"http://localhost:{port}/healthz", timeout=2.0)
                if response.status_code == 200:
                    service_ready = True
                    break
            except:
                pass
            
            await asyncio.sleep(1)
        
        await client.aclose()
        
        if not service_ready:
            process.terminate()
            raise TimeoutError(f"Service {service_name} failed to start within {timeout} seconds")
        
        service_info = {
            "name": service_name,
            "port": port,
            "process": process,
            "endpoint": f"http://localhost:{port}",
            "ready": True
        }
        
        self.services[service_name] = service_info
        return service_info
    
    async def stop_service(self, service_name: str):
        """Stop a service."""
        if service_name not in self.services:
            return
        
        service_info = self.services[service_name]
        process = service_info["process"]
        
        # Graceful shutdown
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        
        del self.services[service_name]
    
    async def stop_all_services(self):
        """Stop all managed services."""
        for service_name in list(self.services.keys()):
            await self.stop_service(service_name)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def service_manager():
    """Service manager fixture."""
    manager = ServiceManager()
    yield manager
    await manager.stop_all_services()


@pytest.fixture(scope="session")
async def redis_client():
    """Redis client fixture."""
    client = redis.from_url("redis://localhost:6379")
    
    # Test Redis connectivity
    try:
        await client.ping()
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
    
    yield client
    await client.close()


@pytest.fixture(scope="session")
async def http_client():
    """HTTP client fixture."""
    client = httpx.AsyncClient(timeout=30.0)
    yield client
    await client.aclose()


@pytest.fixture(scope="session")
async def temp_data_dir():
    """Temporary data directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="session")
async def contracts_registry(service_manager: ServiceManager):
    """Start contracts registry service."""
    # Mock contracts registry or use file-based contracts
    contracts_dir = Path(__file__).parent.parent.parent / "contracts"
    
    return {
        "endpoint": None,  # File-based contracts
        "contracts_dir": str(contracts_dir),
        "schemas": {
            "PriceTick@1.0": {
                "required_fields": ["symbol", "bid", "ask", "timestamp"],
                "field_types": {
                    "symbol": "string",
                    "bid": "number", 
                    "ask": "number",
                    "timestamp": "datetime"
                }
            },
            "Signal@1.0": {
                "required_fields": ["signal_id", "symbol", "direction", "confidence_score", "timestamp"],
                "field_types": {
                    "signal_id": "string",
                    "symbol": "string",
                    "direction": "string",
                    "confidence_score": "number",
                    "timestamp": "datetime"
                }
            },
            "ExecutionReport@1.0": {
                "required_fields": ["execution_id", "order_id", "symbol", "status", "timestamp"],
                "field_types": {
                    "execution_id": "string",
                    "order_id": "string", 
                    "symbol": "string",
                    "status": "string",
                    "timestamp": "datetime"
                }
            }
        }
    }


@pytest.fixture(scope="session")
async def flow_orchestrator(service_manager: ServiceManager):
    """Start flow orchestrator service."""
    return await service_manager.start_service(
        "flow-orchestrator", 8093, "flow-orchestrator"
    )


@pytest.fixture(scope="session")
async def event_gateway(service_manager: ServiceManager):
    """Start event gateway service."""
    return await service_manager.start_service(
        "event-gateway", 8094, "event-gateway"
    )


@pytest.fixture(scope="session") 
async def data_validator(service_manager: ServiceManager):
    """Start data validator service."""
    return await service_manager.start_service(
        "data-validator", 8095, "data-validator"
    )


@pytest.fixture(scope="session")
async def flow_monitor(service_manager: ServiceManager):
    """Start flow monitor service."""
    return await service_manager.start_service(
        "flow-monitor", 8096, "flow-monitor"
    )


@pytest.fixture(scope="session")
async def telemetry_daemon(service_manager: ServiceManager):
    """Start telemetry daemon service."""
    return await service_manager.start_service(
        "telemetry-daemon", 8092, "telemetry-daemon"
    )


@pytest.fixture
async def sample_price_tick() -> Dict[str, Any]:
    """Sample price tick data for testing."""
    return {
        "symbol": "EURUSD",
        "bid": 1.1234,
        "ask": 1.1236,
        "timestamp": "2025-01-15T10:30:00Z",
        "volume": 1000000,
        "spread": 0.0002
    }


@pytest.fixture
async def sample_signal() -> Dict[str, Any]:
    """Sample signal data for testing."""
    return {
        "signal_id": "sig_001",
        "symbol": "EURUSD", 
        "direction": "BUY",
        "confidence_score": 0.85,
        "timestamp": "2025-01-15T10:30:30Z",
        "entry_price": 1.1235,
        "stop_loss": 1.1220,
        "take_profit": 1.1250,
        "risk_reward_ratio": 2.0
    }


@pytest.fixture
async def sample_execution_report() -> Dict[str, Any]:
    """Sample execution report for testing."""
    return {
        "execution_id": "exec_001",
        "order_id": "ord_001", 
        "symbol": "EURUSD",
        "status": "FILLED",
        "timestamp": "2025-01-15T10:31:00Z",
        "fill_price": 1.1235,
        "fill_quantity": 10000,
        "execution_time_ms": 150
    }


@pytest.fixture
async def sample_calendar_event() -> Dict[str, Any]:
    """Sample calendar event for testing."""
    return {
        "event_id": "cal_001",
        "currency": "USD",
        "event_name": "Non-Farm Payrolls",
        "scheduled_time": "2025-01-15T13:30:00Z",
        "impact": "HIGH",
        "actual_value": 250000,
        "forecast_value": 200000,
        "previous_value": 180000
    }


@pytest.fixture
async def integration_test_config():
    """Configuration for integration tests."""
    return {
        "test_timeout_seconds": 30,
        "service_startup_timeout": 30,
        "redis_url": "redis://localhost:6379",
        "expected_services": [
            "flow-orchestrator",
            "event-gateway", 
            "data-validator",
            "flow-monitor",
            "telemetry-daemon"
        ],
        "test_topics": [
            "eafix.test.price.tick",
            "eafix.test.signals.generated", 
            "eafix.test.execution.completed"
        ]
    }


class TestEventPublisher:
    """Utility class for publishing test events."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
    
    async def publish_event(self, topic: str, event_data: Dict[str, Any]) -> None:
        """Publish a test event."""
        await self.redis_client.publish(topic, json.dumps(event_data))
    
    async def publish_price_tick(self, data: Dict[str, Any], topic: str = "eafix.test.price.tick") -> None:
        """Publish price tick event."""
        event_data = {
            "event_type": "PriceTick@1.0",
            "timestamp": data.get("timestamp", time.time()),
            "payload": data
        }
        await self.publish_event(topic, event_data)
    
    async def publish_signal(self, data: Dict[str, Any], topic: str = "eafix.test.signals.generated") -> None:
        """Publish signal event."""
        event_data = {
            "event_type": "Signal@1.0", 
            "timestamp": data.get("timestamp", time.time()),
            "payload": data
        }
        await self.publish_event(topic, event_data)


@pytest.fixture
async def test_event_publisher(redis_client):
    """Test event publisher fixture."""
    return TestEventPublisher(redis_client)


class TestServiceClient:
    """Utility class for making service API calls."""
    
    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client
    
    async def get_service_health(self, endpoint: str) -> Dict[str, Any]:
        """Get service health status."""
        response = await self.http_client.get(f"{endpoint}/healthz")
        response.raise_for_status()
        return response.json()
    
    async def get_service_readiness(self, endpoint: str) -> Dict[str, Any]:
        """Get service readiness status."""
        response = await self.http_client.get(f"{endpoint}/readyz")
        response.raise_for_status()
        return response.json()
    
    async def get_service_metrics(self, endpoint: str) -> Dict[str, Any]:
        """Get service metrics."""
        response = await self.http_client.get(f"{endpoint}/metrics")
        response.raise_for_status()
        return response.json()
    
    async def validate_data(self, validator_endpoint: str, data: Dict[str, Any], schema: str) -> Dict[str, Any]:
        """Validate data using data validator service."""
        payload = {
            "data": data,
            "schema": schema
        }
        response = await self.http_client.post(f"{validator_endpoint}/validate/data", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def publish_event_via_gateway(self, gateway_endpoint: str, event_type: str, 
                                      schema_version: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Publish event via event gateway."""
        event_data = {
            "event_type": event_type,
            "schema_version": schema_version,
            "payload": payload
        }
        response = await self.http_client.post(f"{gateway_endpoint}/events/publish", json=event_data)
        response.raise_for_status()
        return response.json()
    
    async def get_flow_traces(self, monitor_endpoint: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get flow traces from flow monitor."""
        params = {"limit": limit}
        response = await self.http_client.get(f"{monitor_endpoint}/traces/completed", params=params)
        response.raise_for_status()
        return response.json()
    
    async def trigger_flow(self, orchestrator_endpoint: str, flow_name: str, 
                          trigger_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger flow via orchestrator."""
        payload = {
            "flow_name": flow_name,
            "trigger_data": trigger_data
        }
        response = await self.http_client.post(f"{orchestrator_endpoint}/orchestrator/flows/trigger", json=payload)
        response.raise_for_status() 
        return response.json()


@pytest.fixture
async def test_service_client(http_client):
    """Test service client fixture."""
    return TestServiceClient(http_client)


@pytest.fixture(autouse=True)
async def cleanup_redis_test_data(redis_client):
    """Clean up Redis test data after each test."""
    yield
    
    # Clean up test topics
    test_topics = [
        "eafix.test.*",
        "eafix.flow.alerts",
        "eafix.orchestrator.test.*"
    ]
    
    # Note: In a real test environment, you might want to use a separate Redis database
    # or implement more sophisticated cleanup


# Test data generators
@pytest.fixture
def price_tick_generator():
    """Generate test price tick data."""
    def generate(symbol="EURUSD", bid=1.1234, ask=None, **kwargs):
        if ask is None:
            ask = bid + 0.0002  # Default 2 pip spread
        
        return {
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "timestamp": kwargs.get("timestamp", "2025-01-15T10:30:00Z"),
            "volume": kwargs.get("volume", 1000000),
            "spread": ask - bid,
            **kwargs
        }
    
    return generate


@pytest.fixture 
def signal_generator():
    """Generate test signal data."""
    def generate(symbol="EURUSD", direction="BUY", confidence=0.85, **kwargs):
        return {
            "signal_id": kwargs.get("signal_id", f"sig_{int(time.time())}"),
            "symbol": symbol,
            "direction": direction,
            "confidence_score": confidence,
            "timestamp": kwargs.get("timestamp", "2025-01-15T10:30:30Z"),
            "entry_price": kwargs.get("entry_price", 1.1235),
            "stop_loss": kwargs.get("stop_loss", 1.1220 if direction == "BUY" else 1.1250),
            "take_profit": kwargs.get("take_profit", 1.1250 if direction == "BUY" else 1.1220),
            **kwargs
        }
    
    return generate


# Pytest markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "integration: End-to-end integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests") 
    config.addinivalue_line("markers", "redis_required: Tests requiring Redis")
    config.addinivalue_line("markers", "services_required: Tests requiring running services")