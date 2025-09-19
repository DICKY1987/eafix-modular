"""
EAFIX Trading System - Idempotency & Exactly-Once Semantics

This package provides comprehensive idempotency and exactly-once execution 
semantics for the EAFIX trading system, ensuring reliable operation in 
distributed environments.

Key Components:
- IdempotencyKey models for deterministic operation identification
- Redis-based idempotency store with atomic operations
- FastAPI middleware for automatic HTTP request idempotency
- Saga pattern coordinator for distributed transactions
- Outbox pattern for reliable event publishing
- Exactly-once execution guarantees for critical operations

Usage Example:
    from shared.idempotency import (
        IdempotencyStore, 
        ExactlyOnceExecutor,
        OutboxProcessor,
        add_idempotency_middleware
    )
    
    # Set up idempotency store
    store = IdempotencyStore(redis_client)
    
    # Set up exactly-once executor
    executor = ExactlyOnceExecutor(redis_client, outbox_processor, store)
    
    # Execute trading order exactly once
    result = await executor.execute_trading_order(
        symbol="EURUSD",
        side="buy", 
        quantity=0.1,
        broker_api=broker.submit_order
    )
"""

# Core models
from .models.idempotency_key import (
    IdempotencyKey,
    IdempotencyRequest, 
    IdempotencyResponse,
    IdempotencyStatus,
    OperationType,
    create_idempotency_key,
    create_trading_order_key,
    create_signal_key,
    create_risk_validation_key,
    generate_deterministic_hash,
    normalize_for_hashing
)

# Storage implementations
from .stores.redis_store import RedisIdempotencyStore

# FastAPI middleware
from .middleware.fastapi_middleware import (
    IdempotencyMiddleware,
    add_idempotency_middleware,
    idempotent
)

# Distributed transaction patterns
from .patterns.saga_coordinator import (
    SagaCoordinator,
    SagaTransaction,
    SagaContext,
    SagaStep,
    SagaStatus,
    StepStatus
)

# Outbox pattern
from .patterns.outbox_pattern import (
    OutboxProcessor,
    OutboxEvent,
    EventStatus,
    EventPriority
)

# Exactly-once execution
from .patterns.exactly_once_execution import (
    ExactlyOnceExecutor,
    ExecutionResult,
    ExecutionStatus
)

# Convenience aliases
IdempotencyStore = RedisIdempotencyStore

__version__ = "0.1.0"

__all__ = [
    # Models
    "IdempotencyKey",
    "IdempotencyRequest",
    "IdempotencyResponse", 
    "IdempotencyStatus",
    "OperationType",
    "create_idempotency_key",
    "create_trading_order_key",
    "create_signal_key", 
    "create_risk_validation_key",
    "generate_deterministic_hash",
    "normalize_for_hashing",
    
    # Storage
    "RedisIdempotencyStore",
    "IdempotencyStore",
    
    # Middleware
    "IdempotencyMiddleware",
    "add_idempotency_middleware",
    "idempotent",
    
    # Saga pattern
    "SagaCoordinator",
    "SagaTransaction", 
    "SagaContext",
    "SagaStep",
    "SagaStatus",
    "StepStatus",
    
    # Outbox pattern  
    "OutboxProcessor",
    "OutboxEvent",
    "EventStatus",
    "EventPriority",
    
    # Exactly-once execution
    "ExactlyOnceExecutor",
    "ExecutionResult", 
    "ExecutionStatus",
]