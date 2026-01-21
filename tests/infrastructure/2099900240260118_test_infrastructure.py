# doc_id: DOC-TEST-0041
# DOC_ID: DOC-TEST-0001
# tests/conftest.py - Master test configuration

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi.testclient import TestClient
from testcontainers.postgres import PostgreSqlContainer
from testcontainers.redis import RedisContainer

from services.common.base_enterprise_service import BaseEnterpriseService, ServiceMetadata
from services.common.service_config import ServiceConfig
from packages.security.src.security.framework import SecurityFramework, SecurityPolicy


# Test Categories
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.timeout(30)  # Default timeout for all tests
]


class TestCategories:
    """Test category markers for pytest"""
    UNIT = pytest.mark.unit
    INTEGRATION = pytest.mark.integration
    E2E = pytest.mark.e2e
    CONTRACT = pytest.mark.contract
    PERFORMANCE = pytest.mark.performance
    SECURITY = pytest.mark.security
    SLOW = pytest.mark.slow


# Test Fixtures

@pytest_asyncio.fixture(scope="session")
async def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container():
    """PostgreSQL test container"""
    with PostgreSqlContainer("postgres:13") as postgres:
        yield postgres


@pytest.fixture(scope="session")  
def redis_container():
    """Redis test container"""
    with RedisContainer("redis:7") as redis_container:
        yield redis_container


@pytest_asyncio.fixture(scope="session")
async def test_db_engine(postgres_container):
    """Test database engine"""
    connection_url = postgres_container.get_connection_url().replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    
    engine = create_async_engine(
        connection_url,
        echo=False,
        future=True
    )
    
    # Create tables
    from packages.apf_core.src.apf_core.database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_db_engine):
    """Test database session"""
    async with AsyncSession(test_db_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_redis(redis_container):
    """Test Redis client"""
    redis_client = redis.from_url(
        redis_container.get_connection_url(),
        decode_responses=True
    )
    
    yield redis_client
    
    await redis_client.flushall()
    await redis_client.close()


@pytest.fixture
def test_security_policy():
    """Test security policy"""
    return SecurityPolicy(
        jwt_secret="test-secret-key-for-testing-only",
        jwt_expiry_hours=1,
        max_login_attempts=3,
        lockout_duration_minutes=5,
        password_min_length=6,
        require_mfa=False,
        session_timeout_minutes=60,
        allowed_origins=["http://localhost:3000"],
        rate_limit_per_minute=100
    )


@pytest_asyncio.fixture
async def test_security_framework(test_redis, test_security_policy):
    """Test security framework"""
    framework = SecurityFramework(test_security_policy, test_redis)
    
    # Create test users
    await framework.create_user(
        username="testuser",
        email="test@example.com", 
        password="testpass123",
        roles={framework.rbac.Role.TRADER}
    )
    
    await framework.create_user(
        username="admin",
        email="admin@example.com",
        password="adminpass123", 
        roles={framework.rbac.Role.ADMIN}
    )
    
    yield framework


@pytest.fixture
def test_service_config():
    """Test service configuration"""
    return ServiceConfig(
        cors_origins=["http://localhost:3000"],
        database_url="postgresql://test:test@localhost:5432/test",
        redis_url="redis://localhost:6379",
        jwt_secret="test-secret",
        log_level="DEBUG"
    )


class MockService(BaseEnterpriseService):
    """Mock service for testing"""
    
    def __init__(self, config: ServiceConfig = None):
        metadata = ServiceMetadata(
            name="test-service",
            version="1.0.0",
            description="Test service for unit tests",
            dependencies=[],
            health_check_interval=10,
            circuit_breaker_enabled=True,
            metrics_enabled=True
        )
        
        super().__init__(metadata, config or ServiceConfig())
        self.mock_impl = AsyncMock()
    
    async def service_logic(self):
        """Mock service logic"""
        await self.mock_impl.start()
    
    async def cleanup(self):
        """Mock cleanup"""
        await self.mock_impl.stop()


@pytest_asyncio.fixture
async def test_service(test_service_config):
    """Test service instance"""
    service = MockService(test_service_config)
    yield service
    await service.cleanup()


@pytest.fixture
def test_client(test_service):
    """Test client for API testing"""
    return TestClient(test_service.app)


# Test Data Factories

class TestDataFactory:
    """Factory for generating test data"""
    
    @staticmethod
    def create_atomic_process_data() -> Dict[str, Any]:
        """Create test atomic process data"""
        return {
            "metadata": {
                "id": "TEST_PROCESS_001",
                "version": "1.0.0",
                "name": "Test Trading Process",
                "description": "Test process for unit testing",
                "created_at": "2024-01-01T00:00:00Z",
                "author": "test-user",
                "tags": ["test", "trading"]
            },
            "process_flow": {
                "steps": [
                    {
                        "id": "step_001",
                        "name": "Data Input",
                        "type": "data_input",
                        "parameters": {
                            "source": "market_data",
                            "symbols": ["EURUSD", "GBPUSD"]
                        }
                    },
                    {
                        "id": "step_002", 
                        "name": "Technical Analysis",
                        "type": "indicator",
                        "parameters": {
                            "indicator": "sma",
                            "period": 20
                        },
                        "depends_on": ["step_001"]
                    }
                ]
            }
        }
    
    @staticmethod
    def create_market_data() -> Dict[str, Any]:
        """Create test market data"""
        return {
            "symbol": "EURUSD",
            "timestamp": "2024-01-01T12:00:00Z",
            "bid": 1.0950,
            "ask": 1.0952,
            "volume": 1000000,
            "spread": 0.0002
        }
    
    @staticmethod
    def create_trading_signal() -> Dict[str, Any]:
        """Create test trading signal"""
        return {
            "signal_id": "SIG_001",
            "symbol": "EURUSD",
            "direction": "BUY",
            "strength": 0.75,
            "entry_price": 1.0950,
            "stop_loss": 1.0900,
            "take_profit": 1.1000,
            "timestamp": "2024-01-01T12:00:00Z",
            "confidence": 0.85
        }


# Test Utilities

class TestUtils:
    """Utilities for testing"""
    
    @staticmethod
    async def wait_for_condition(
        condition_func,
        timeout: float = 5.0,
        poll_interval: float = 0.1
    ):
        """Wait for a condition to become true"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if await condition_func():
                return True
            
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(f"Condition not met within {timeout} seconds")
            
            await asyncio.sleep(poll_interval)
    
    @staticmethod
    def assert_valid_uuid(uuid_string: str):
        """Assert that string is valid UUID"""
        import uuid
        try:
            uuid.UUID(uuid_string)
        except ValueError:
            pytest.fail(f"Invalid UUID: {uuid_string}")
    
    @staticmethod
    def assert_valid_timestamp(timestamp_string: str):
        """Assert that string is valid ISO timestamp"""
        from datetime import datetime
        try:
            datetime.fromisoformat(timestamp_string.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Invalid timestamp: {timestamp_string}")
    
    @staticmethod
    def assert_response_time(response_time: float, max_time: float):
        """Assert response time is within acceptable limits"""
        assert response_time <= max_time, f"Response time {response_time}s exceeds {max_time}s"


# Performance Testing Utilities

class PerformanceMonitor:
    """Monitor performance during tests"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = None
    
    def start(self):
        """Start monitoring"""
        self.start_time = asyncio.get_event_loop().time()
    
    def record_metric(self, name: str, value: float):
        """Record a performance metric"""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)
    
    def get_duration(self) -> float:
        """Get total duration"""
        if self.start_time is None:
            return 0.0
        return asyncio.get_event_loop().time() - self.start_time
    
    def get_average(self, metric_name: str) -> float:
        """Get average for a metric"""
        values = self.metrics.get(metric_name, [])
        return sum(values) / len(values) if values else 0.0
    
    def assert_performance_targets(self, targets: Dict[str, float]):
        """Assert performance targets are met"""
        for metric, target in targets.items():
            actual = self.get_average(metric)
            assert actual <= target, f"{metric}: {actual} exceeds target {target}"


@pytest.fixture
def performance_monitor():
    """Performance monitoring fixture"""
    return PerformanceMonitor()


# Contract Testing Utilities

class ContractValidator:
    """Validate API contracts"""
    
    @staticmethod
    def validate_response_schema(response_data: Dict, expected_schema: Dict):
        """Validate response matches expected schema"""
        import jsonschema
        try:
            jsonschema.validate(response_data, expected_schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Response schema validation failed: {e}")
    
    @staticmethod
    def validate_event_schema(event_data: Dict, event_type: str):
        """Validate event data matches schema"""
        # Load event schema
        schema_path = f"schemas/events/{event_type}.schema.json"
        try:
            import json
            with open(schema_path) as f:
                schema = json.load(f)
            ContractValidator.validate_response_schema(event_data, schema)
        except FileNotFoundError:
            pytest.fail(f"Event schema not found: {schema_path}")


@pytest.fixture
def contract_validator():
    """Contract validation fixture"""
    return ContractValidator()


# Test Configuration

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "contract: Contract tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "slow: Slow tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add default markers based on test location
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "contract" in str(item.fspath):
            item.add_marker(pytest.mark.contract)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)


# Coverage Configuration
pytest_plugins = [
    "pytest_asyncio",
    "pytest_mock",
    "pytest_cov",
    "pytest_benchmark",
    "pytest_timeout"
]