"""
Exactly-once execution semantics for EAFIX trading operations.
Ensures critical trading operations execute exactly once, even in the presence of failures and retries.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid
import hashlib

from pydantic import BaseModel, Field
import structlog

from .outbox_pattern import OutboxProcessor, OutboxEvent, EventPriority
from ..models.idempotency_key import (
    IdempotencyRequest, IdempotencyResponse, IdempotencyStatus,
    create_trading_order_key, create_signal_key
)
from ..stores.redis_store import RedisIdempotencyStore

logger = structlog.get_logger(__name__)


class ExecutionStatus(str, Enum):
    """Status of exactly-once execution."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExecutionResult(BaseModel):
    """Result of exactly-once execution."""
    
    execution_id: str = Field(..., description="Unique execution identifier")
    operation_type: str = Field(..., description="Type of operation")
    status: ExecutionStatus = Field(..., description="Execution status")
    result: Optional[Dict[str, Any]] = Field(None, description="Operation result")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # Timing information
    started_at: datetime = Field(..., description="When execution started")
    completed_at: Optional[datetime] = Field(None, description="When execution completed")
    duration_seconds: Optional[float] = Field(None, description="Execution duration")
    
    # Idempotency information
    idempotency_key: str = Field(..., description="Idempotency key")
    retry_count: int = Field(default=0)
    
    # Event information
    events_published: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ExactlyOnceExecutor:
    """
    Exactly-once execution coordinator for critical trading operations.
    
    Features:
    - Idempotent operation execution
    - Atomic result storage with event publishing
    - Distributed locking for exclusive access
    - Automatic cleanup of completed executions
    - Comprehensive error handling and recovery
    """
    
    def __init__(
        self,
        redis_client,
        outbox_processor: OutboxProcessor,
        idempotency_store: RedisIdempotencyStore,
        execution_timeout: int = 300,  # 5 minutes
        lock_timeout: int = 60,        # 1 minute
        cleanup_interval: int = 3600   # 1 hour
    ):
        """
        Initialize exactly-once executor.
        
        Args:
            redis_client: Redis client for coordination
            outbox_processor: Outbox pattern processor for events
            idempotency_store: Idempotency store for operation tracking
            execution_timeout: Maximum execution time in seconds
            lock_timeout: Distributed lock timeout in seconds
            cleanup_interval: Cleanup interval in seconds
        """
        self.redis = redis_client
        self.outbox = outbox_processor
        self.idempotency_store = idempotency_store
        self.execution_timeout = execution_timeout
        self.lock_timeout = lock_timeout
        self.cleanup_interval = cleanup_interval
        
        # Key prefixes
        self.execution_prefix = "execution"
        self.lock_prefix = "execution_lock"
        
        # Active executions
        self.active_executions: Dict[str, asyncio.Task] = {}
        
        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.executions_started = 0
        self.executions_completed = 0
        self.executions_failed = 0
        self.executions_duplicate = 0
    
    async def execute_exactly_once(
        self,
        operation_func: Callable[..., Any],
        idempotency_key: str,
        operation_type: str,
        operation_args: Tuple = (),
        operation_kwargs: Dict[str, Any] = None,
        timeout_seconds: Optional[int] = None,
        events_to_publish: Optional[List[OutboxEvent]] = None
    ) -> ExecutionResult:
        """
        Execute operation exactly once with idempotency guarantees.
        
        Args:
            operation_func: Function to execute
            idempotency_key: Idempotency key for the operation
            operation_type: Type of operation being performed
            operation_args: Arguments for the operation function
            operation_kwargs: Keyword arguments for the operation function
            timeout_seconds: Execution timeout override
            events_to_publish: Events to publish on successful completion
            
        Returns:
            Execution result
        """
        operation_kwargs = operation_kwargs or {}
        timeout = timeout_seconds or self.execution_timeout
        execution_id = f"{operation_type}:{idempotency_key}"
        
        # Check for existing execution
        existing_result = await self._get_execution_result(execution_id)
        if existing_result:
            if existing_result.status == ExecutionStatus.COMPLETED:
                logger.info(
                    "Found completed execution",
                    execution_id=execution_id,
                    idempotency_key=idempotency_key
                )
                self.executions_duplicate += 1
                return existing_result
            
            elif existing_result.status == ExecutionStatus.EXECUTING:
                # Wait for existing execution to complete
                logger.info(
                    "Waiting for existing execution",
                    execution_id=execution_id,
                    idempotency_key=idempotency_key
                )
                return await self._wait_for_execution(execution_id, timeout)
            
            elif existing_result.status in (ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT):
                # Previous execution failed, allow retry
                logger.info(
                    "Previous execution failed, retrying",
                    execution_id=execution_id,
                    status=existing_result.status,
                    retry_count=existing_result.retry_count
                )
        
        # Start new execution
        return await self._start_execution(
            execution_id=execution_id,
            operation_func=operation_func,
            idempotency_key=idempotency_key,
            operation_type=operation_type,
            operation_args=operation_args,
            operation_kwargs=operation_kwargs,
            timeout_seconds=timeout,
            events_to_publish=events_to_publish or [],
            retry_count=existing_result.retry_count + 1 if existing_result else 0
        )
    
    async def _start_execution(
        self,
        execution_id: str,
        operation_func: Callable,
        idempotency_key: str,
        operation_type: str,
        operation_args: Tuple,
        operation_kwargs: Dict[str, Any],
        timeout_seconds: int,
        events_to_publish: List[OutboxEvent],
        retry_count: int = 0
    ) -> ExecutionResult:
        """Start new execution with distributed locking."""
        lock_key = f"{self.lock_prefix}:{execution_id}"
        
        # Try to acquire distributed lock
        lock_acquired = await self.redis.set(
            lock_key,
            "locked",
            px=self.lock_timeout * 1000,  # Convert to milliseconds
            nx=True  # Only set if not exists
        )
        
        if not lock_acquired:
            # Another instance is executing this operation
            logger.info(
                "Could not acquire execution lock, waiting",
                execution_id=execution_id,
                idempotency_key=idempotency_key
            )
            return await self._wait_for_execution(execution_id, timeout_seconds)
        
        try:
            # Create initial execution result
            result = ExecutionResult(
                execution_id=execution_id,
                operation_type=operation_type,
                status=ExecutionStatus.EXECUTING,
                started_at=datetime.now(timezone.utc),
                idempotency_key=idempotency_key,
                retry_count=retry_count
            )
            
            # Store initial state
            await self._store_execution_result(result)
            
            # Update idempotency store
            await self.idempotency_store.update_status(
                idempotency_key=idempotency_key,
                status=IdempotencyStatus.IN_PROGRESS
            )
            
            self.executions_started += 1
            
            logger.info(
                "Starting exactly-once execution",
                execution_id=execution_id,
                operation_type=operation_type,
                retry_count=retry_count,
                timeout=timeout_seconds
            )
            
            # Execute operation with timeout
            try:
                operation_result = await asyncio.wait_for(
                    operation_func(*operation_args, **operation_kwargs),
                    timeout=timeout_seconds
                )
                
                # Operation completed successfully
                completion_time = datetime.now(timezone.utc)
                result.status = ExecutionStatus.COMPLETED
                result.result = operation_result if isinstance(operation_result, dict) else {"result": operation_result}
                result.completed_at = completion_time
                result.duration_seconds = (completion_time - result.started_at).total_seconds()
                
                # Publish events atomically with result storage
                if events_to_publish:
                    await self._publish_events_atomically(result, events_to_publish)
                
                # Update idempotency store
                await self.idempotency_store.update_status(
                    idempotency_key=idempotency_key,
                    status=IdempotencyStatus.COMPLETED,
                    result=result.result
                )
                
                self.executions_completed += 1
                
                logger.info(
                    "Exactly-once execution completed successfully",
                    execution_id=execution_id,
                    duration_seconds=result.duration_seconds,
                    events_published=len(events_to_publish)
                )
                
            except asyncio.TimeoutError:
                # Execution timed out
                result.status = ExecutionStatus.TIMEOUT
                result.error = f"Execution timed out after {timeout_seconds} seconds"
                result.completed_at = datetime.now(timezone.utc)
                result.duration_seconds = timeout_seconds
                
                await self.idempotency_store.update_status(
                    idempotency_key=idempotency_key,
                    status=IdempotencyStatus.FAILED,
                    error=result.error
                )
                
                self.executions_failed += 1
                
                logger.error(
                    "Exactly-once execution timed out",
                    execution_id=execution_id,
                    timeout=timeout_seconds
                )
                
            except Exception as e:
                # Execution failed
                result.status = ExecutionStatus.FAILED
                result.error = str(e)
                result.completed_at = datetime.now(timezone.utc)
                result.duration_seconds = (result.completed_at - result.started_at).total_seconds()
                
                await self.idempotency_store.update_status(
                    idempotency_key=idempotency_key,
                    status=IdempotencyStatus.FAILED,
                    error=result.error
                )
                
                self.executions_failed += 1
                
                logger.error(
                    "Exactly-once execution failed",
                    execution_id=execution_id,
                    error=str(e),
                    duration_seconds=result.duration_seconds
                )
            
            # Store final result
            await self._store_execution_result(result)
            
            return result
            
        finally:
            # Always release the lock
            await self.redis.delete(lock_key)
    
    async def _wait_for_execution(
        self,
        execution_id: str,
        timeout_seconds: int
    ) -> ExecutionResult:
        """Wait for existing execution to complete."""
        start_time = datetime.now(timezone.utc)
        poll_interval = 0.5  # 500ms
        
        while True:
            # Check if execution completed
            result = await self._get_execution_result(execution_id)
            
            if result and result.status not in (ExecutionStatus.PENDING, ExecutionStatus.EXECUTING):
                return result
            
            # Check timeout
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            if elapsed >= timeout_seconds:
                # Create timeout result
                return ExecutionResult(
                    execution_id=execution_id,
                    operation_type="unknown",
                    status=ExecutionStatus.TIMEOUT,
                    error="Timed out waiting for execution to complete",
                    started_at=start_time,
                    completed_at=datetime.now(timezone.utc),
                    duration_seconds=elapsed,
                    idempotency_key="unknown"
                )
            
            # Wait before polling again
            await asyncio.sleep(poll_interval)
    
    async def _publish_events_atomically(
        self,
        result: ExecutionResult,
        events: List[OutboxEvent]
    ) -> None:
        """Publish events atomically with execution result."""
        # Add execution metadata to events
        for event in events:
            event.metadata.update({
                "execution_id": result.execution_id,
                "operation_type": result.operation_type,
                "idempotency_key": result.idempotency_key
            })
        
        # Store events in outbox
        await self.outbox.store_events_batch(
            events,
            transaction_key=result.execution_id
        )
        
        # Track published events
        result.events_published = [event.event_id for event in events]
        
        logger.info(
            "Published events atomically",
            execution_id=result.execution_id,
            event_count=len(events)
        )
    
    async def _store_execution_result(self, result: ExecutionResult) -> None:
        """Store execution result in Redis."""
        key = f"{self.execution_prefix}:{result.execution_id}"
        ttl = 3600 * 24  # 24 hours
        
        await self.redis.setex(key, ttl, result.json())
    
    async def _get_execution_result(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get execution result from Redis."""
        key = f"{self.execution_prefix}:{execution_id}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        try:
            return ExecutionResult.parse_raw(data)
        except Exception as e:
            logger.error(
                "Error parsing execution result",
                execution_id=execution_id,
                error=str(e)
            )
            return None
    
    async def execute_trading_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = "market",
        client_order_id: Optional[str] = None,
        broker_api: Callable = None
    ) -> ExecutionResult:
        """
        Execute trading order exactly once.
        
        Args:
            symbol: Trading symbol
            side: Order side ("buy" or "sell")
            quantity: Order quantity
            price: Order price (for limit orders)
            order_type: Order type
            client_order_id: Client order ID
            broker_api: Broker API function to execute order
            
        Returns:
            Execution result
        """
        # Create idempotency key
        idempotency_key_obj = create_trading_order_key(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
            client_order_id=client_order_id,
            timestamp=datetime.now(timezone.utc)
        )
        
        idempotency_key = str(idempotency_key_obj)
        
        # Create order execution function
        async def execute_order():
            if broker_api:
                return await broker_api(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=price,
                    order_type=order_type,
                    client_order_id=client_order_id
                )
            else:
                # Mock implementation for testing
                return {
                    "order_id": f"order_{hash(idempotency_key)}",
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                    "status": "filled",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        
        # Create events to publish on success
        events = [
            OutboxEvent(
                event_type="order_executed",
                aggregate_id=symbol,
                aggregate_type="trading_pair",
                payload={
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                    "order_type": order_type,
                    "client_order_id": client_order_id
                },
                topic="trading.orders.executed",
                priority=EventPriority.HIGH,
                idempotency_key=idempotency_key
            )
        ]
        
        # Execute exactly once
        return await self.execute_exactly_once(
            operation_func=execute_order,
            idempotency_key=idempotency_key,
            operation_type="order_execution",
            events_to_publish=events,
            timeout_seconds=30  # Orders should execute quickly
        )
    
    async def execute_signal_generation(
        self,
        symbol: str,
        signal_type: str,
        indicator_values: Dict[str, float],
        signal_func: Callable,
        signal_args: Tuple = (),
        signal_kwargs: Dict[str, Any] = None
    ) -> ExecutionResult:
        """
        Execute signal generation exactly once.
        
        Args:
            symbol: Trading symbol
            signal_type: Type of signal
            indicator_values: Indicator values for the signal
            signal_func: Signal generation function
            signal_args: Arguments for signal function
            signal_kwargs: Keyword arguments for signal function
            
        Returns:
            Execution result
        """
        signal_kwargs = signal_kwargs or {}
        
        # Create idempotency key
        idempotency_key_obj = create_signal_key(
            symbol=symbol,
            signal_type=signal_type,
            direction="unknown",  # Will be determined by signal function
            confidence=0.0,       # Will be determined by signal function
            indicator_values=indicator_values,
            timestamp=datetime.now(timezone.utc)
        )
        
        idempotency_key = str(idempotency_key_obj)
        
        # Create signal generation wrapper
        async def generate_signal():
            if asyncio.iscoroutinefunction(signal_func):
                return await signal_func(*signal_args, **signal_kwargs)
            else:
                return signal_func(*signal_args, **signal_kwargs)
        
        # Execute exactly once
        result = await self.execute_exactly_once(
            operation_func=generate_signal,
            idempotency_key=idempotency_key,
            operation_type="signal_generation",
            timeout_seconds=60  # Signals may take some time to compute
        )
        
        # Publish signal event on success
        if result.status == ExecutionStatus.COMPLETED and result.result:
            signal_event = OutboxEvent(
                event_type="signal_generated",
                aggregate_id=symbol,
                aggregate_type="trading_pair",
                payload={
                    "symbol": symbol,
                    "signal_type": signal_type,
                    "signal_result": result.result,
                    "indicator_values": indicator_values
                },
                topic="trading.signals.generated",
                priority=EventPriority.NORMAL,
                idempotency_key=idempotency_key
            )
            
            await self.outbox.store_event(signal_event)
            result.events_published.append(signal_event.event_id)
        
        return result
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status."""
        result = await self._get_execution_result(execution_id)
        if not result:
            return None
        
        return {
            "execution_id": result.execution_id,
            "operation_type": result.operation_type,
            "status": result.status,
            "idempotency_key": result.idempotency_key,
            "started_at": result.started_at,
            "completed_at": result.completed_at,
            "duration_seconds": result.duration_seconds,
            "retry_count": result.retry_count,
            "events_published": len(result.events_published),
            "error": result.error
        }
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel pending or executing operation."""
        result = await self._get_execution_result(execution_id)
        if not result:
            return False
        
        if result.status not in (ExecutionStatus.PENDING, ExecutionStatus.EXECUTING):
            return False  # Cannot cancel completed operations
        
        # Update status to cancelled
        result.status = ExecutionStatus.CANCELLED
        result.completed_at = datetime.now(timezone.utc)
        result.error = "Cancelled by user"
        
        await self._store_execution_result(result)
        
        # Update idempotency store
        await self.idempotency_store.update_status(
            idempotency_key=result.idempotency_key,
            status=IdempotencyStatus.FAILED,
            error="Execution cancelled"
        )
        
        logger.info(
            "Cancelled exactly-once execution",
            execution_id=execution_id
        )
        
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        return {
            "executions_started": self.executions_started,
            "executions_completed": self.executions_completed,
            "executions_failed": self.executions_failed,
            "executions_duplicate": self.executions_duplicate,
            "success_rate": (
                self.executions_completed / max(self.executions_started, 1)
            ) if self.executions_started > 0 else 0.0,
            "duplicate_rate": (
                self.executions_duplicate / max(self.executions_started + self.executions_duplicate, 1)
            ) if (self.executions_started + self.executions_duplicate) > 0 else 0.0,
            "execution_timeout": self.execution_timeout,
            "lock_timeout": self.lock_timeout
        }