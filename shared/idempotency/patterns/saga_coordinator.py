"""
Saga pattern coordinator for distributed transactions in EAFIX trading system.
Implements distributed transaction coordination with compensation actions.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class SagaStatus(str, Enum):
    """Status of saga transaction."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    FAILED = "failed"


class StepStatus(str, Enum):
    """Status of individual saga step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


@dataclass
class SagaStep:
    """Individual step in a saga transaction."""
    
    step_id: str
    name: str
    action: Callable[..., Any]
    compensation: Callable[..., Any]
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempt_count: int = 0


class SagaContext(BaseModel):
    """Context data shared across saga steps."""
    
    saga_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data: Dict[str, Any] = Field(default_factory=dict)
    step_results: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SagaTransaction(BaseModel):
    """Complete saga transaction definition."""
    
    saga_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Human-readable saga name")
    steps: List[str] = Field(..., description="List of step IDs in order")
    status: SagaStatus = Field(default=SagaStatus.PENDING)
    context: SagaContext = Field(default_factory=SagaContext)
    current_step: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SagaCoordinator:
    """
    Saga pattern coordinator for distributed transactions.
    
    Features:
    - Sequential step execution
    - Automatic compensation on failure
    - Retry logic with exponential backoff
    - Timeout handling
    - Persistent saga state
    """
    
    def __init__(
        self,
        redis_client,
        key_prefix: str = "saga",
        default_timeout: int = 300,
        max_concurrent_sagas: int = 100
    ):
        """
        Initialize saga coordinator.
        
        Args:
            redis_client: Redis client for persistence
            key_prefix: Redis key prefix for saga data
            default_timeout: Default timeout for sagas
            max_concurrent_sagas: Maximum concurrent sagas
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.default_timeout = default_timeout
        self.max_concurrent = max_concurrent_sagas
        
        # Registry of available steps
        self.step_registry: Dict[str, SagaStep] = {}
        
        # Active saga executions
        self.active_sagas: Dict[str, asyncio.Task] = {}
        
    def register_step(
        self,
        step_id: str,
        name: str,
        action: Callable,
        compensation: Callable,
        timeout_seconds: int = 30,
        retry_attempts: int = 3,
        retry_delay: float = 1.0
    ) -> None:
        """
        Register a saga step.
        
        Args:
            step_id: Unique step identifier
            name: Human-readable step name
            action: Function to execute step
            compensation: Function to compensate step
            timeout_seconds: Step timeout
            retry_attempts: Number of retry attempts
            retry_delay: Delay between retries
        """
        step = SagaStep(
            step_id=step_id,
            name=name,
            action=action,
            compensation=compensation,
            timeout_seconds=timeout_seconds,
            retry_attempts=retry_attempts,
            retry_delay=retry_delay
        )
        
        self.step_registry[step_id] = step
        
        logger.info(
            "Registered saga step",
            step_id=step_id,
            name=name,
            timeout=timeout_seconds
        )
    
    async def create_saga(
        self,
        name: str,
        steps: List[str],
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new saga transaction.
        
        Args:
            name: Saga name
            steps: List of step IDs to execute
            initial_context: Initial context data
            
        Returns:
            Saga ID
        """
        # Validate all steps exist
        for step_id in steps:
            if step_id not in self.step_registry:
                raise ValueError(f"Step not registered: {step_id}")
        
        # Create saga context
        context = SagaContext(data=initial_context or {})
        
        # Create saga transaction
        saga = SagaTransaction(
            name=name,
            steps=steps,
            context=context
        )
        
        # Store in Redis
        await self._store_saga(saga)
        
        logger.info(
            "Created saga transaction",
            saga_id=saga.saga_id,
            name=name,
            steps=steps
        )
        
        return saga.saga_id
    
    async def execute_saga(self, saga_id: str) -> SagaTransaction:
        """
        Execute saga transaction.
        
        Args:
            saga_id: Saga identifier
            
        Returns:
            Completed saga transaction
        """
        # Check concurrent saga limit
        if len(self.active_sagas) >= self.max_concurrent:
            raise RuntimeError("Maximum concurrent sagas exceeded")
        
        # Load saga
        saga = await self._load_saga(saga_id)
        if not saga:
            raise ValueError(f"Saga not found: {saga_id}")
        
        # Create execution task
        task = asyncio.create_task(self._execute_saga_internal(saga))
        self.active_sagas[saga_id] = task
        
        try:
            # Wait for completion
            completed_saga = await task
            return completed_saga
            
        finally:
            # Clean up
            self.active_sagas.pop(saga_id, None)
    
    async def _execute_saga_internal(self, saga: SagaTransaction) -> SagaTransaction:
        """Internal saga execution logic."""
        try:
            # Mark saga as running
            saga.status = SagaStatus.RUNNING
            saga.started_at = datetime.now(timezone.utc)
            await self._store_saga(saga)
            
            logger.info(
                "Starting saga execution",
                saga_id=saga.saga_id,
                name=saga.name,
                steps_count=len(saga.steps)
            )
            
            # Execute steps sequentially
            for step_index, step_id in enumerate(saga.steps):
                saga.current_step = step_index
                await self._store_saga(saga)
                
                success = await self._execute_step(saga, step_id)
                
                if not success:
                    # Step failed, start compensation
                    logger.error(
                        "Saga step failed, starting compensation",
                        saga_id=saga.saga_id,
                        failed_step=step_id,
                        step_index=step_index
                    )
                    
                    saga.status = SagaStatus.COMPENSATING
                    saga.error = f"Step {step_id} failed"
                    await self._store_saga(saga)
                    
                    # Compensate completed steps in reverse order
                    await self._compensate_saga(saga, step_index)
                    return saga
            
            # All steps completed successfully
            saga.status = SagaStatus.COMPLETED
            saga.completed_at = datetime.now(timezone.utc)
            await self._store_saga(saga)
            
            logger.info(
                "Saga completed successfully",
                saga_id=saga.saga_id,
                name=saga.name,
                duration_seconds=(saga.completed_at - saga.started_at).total_seconds()
            )
            
            return saga
            
        except Exception as e:
            # Unexpected error
            logger.error(
                "Unexpected error in saga execution",
                saga_id=saga.saga_id,
                error=str(e)
            )
            
            saga.status = SagaStatus.FAILED
            saga.error = str(e)
            saga.completed_at = datetime.now(timezone.utc)
            await self._store_saga(saga)
            
            return saga
    
    async def _execute_step(
        self,
        saga: SagaTransaction,
        step_id: str
    ) -> bool:
        """
        Execute individual saga step with retry logic.
        
        Args:
            saga: Saga transaction
            step_id: Step to execute
            
        Returns:
            True if step succeeded, False if failed
        """
        step = self.step_registry[step_id].copy()
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now(timezone.utc)
        
        logger.info(
            "Executing saga step",
            saga_id=saga.saga_id,
            step_id=step_id,
            step_name=step.name,
            attempt=1
        )
        
        for attempt in range(step.retry_attempts):
            step.attempt_count = attempt + 1
            
            try:
                # Execute step with timeout
                result = await asyncio.wait_for(
                    step.action(saga.context),
                    timeout=step.timeout_seconds
                )
                
                # Step succeeded
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc)
                step.result = result if isinstance(result, dict) else {"result": result}
                
                # Store step result in context
                saga.context.step_results[step_id] = step.result
                
                logger.info(
                    "Saga step completed",
                    saga_id=saga.saga_id,
                    step_id=step_id,
                    attempt=attempt + 1,
                    duration_seconds=(step.completed_at - step.started_at).total_seconds()
                )
                
                return True
                
            except asyncio.TimeoutError:
                error_msg = f"Step timeout after {step.timeout_seconds}s"
                logger.warning(
                    "Saga step timeout",
                    saga_id=saga.saga_id,
                    step_id=step_id,
                    attempt=attempt + 1,
                    timeout=step.timeout_seconds
                )
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    "Saga step error",
                    saga_id=saga.saga_id,
                    step_id=step_id,
                    attempt=attempt + 1,
                    error=error_msg
                )
            
            # Retry logic (except on last attempt)
            if attempt < step.retry_attempts - 1:
                delay = step.retry_delay * (2 ** attempt)  # Exponential backoff
                await asyncio.sleep(delay)
                
                logger.info(
                    "Retrying saga step",
                    saga_id=saga.saga_id,
                    step_id=step_id,
                    attempt=attempt + 2,
                    delay=delay
                )
        
        # All attempts failed
        step.status = StepStatus.FAILED
        step.error = error_msg
        step.completed_at = datetime.now(timezone.utc)
        
        logger.error(
            "Saga step failed after all attempts",
            saga_id=saga.saga_id,
            step_id=step_id,
            attempts=step.retry_attempts,
            error=error_msg
        )
        
        return False
    
    async def _compensate_saga(
        self,
        saga: SagaTransaction,
        failed_step_index: int
    ) -> None:
        """
        Compensate saga by executing compensation actions in reverse order.
        
        Args:
            saga: Saga transaction
            failed_step_index: Index of step that failed
        """
        logger.info(
            "Starting saga compensation",
            saga_id=saga.saga_id,
            failed_step_index=failed_step_index
        )
        
        # Compensate completed steps in reverse order
        for step_index in range(failed_step_index - 1, -1, -1):
            step_id = saga.steps[step_index]
            
            # Skip if step wasn't completed
            if step_id not in saga.context.step_results:
                continue
            
            await self._compensate_step(saga, step_id)
        
        saga.status = SagaStatus.COMPENSATED
        saga.completed_at = datetime.now(timezone.utc)
        await self._store_saga(saga)
        
        logger.info(
            "Saga compensation completed",
            saga_id=saga.saga_id
        )
    
    async def _compensate_step(
        self,
        saga: SagaTransaction,
        step_id: str
    ) -> None:
        """
        Execute compensation for individual step.
        
        Args:
            saga: Saga transaction
            step_id: Step to compensate
        """
        step = self.step_registry[step_id]
        
        logger.info(
            "Compensating saga step",
            saga_id=saga.saga_id,
            step_id=step_id,
            step_name=step.name
        )
        
        try:
            # Execute compensation with timeout
            await asyncio.wait_for(
                step.compensation(saga.context),
                timeout=step.timeout_seconds
            )
            
            logger.info(
                "Saga step compensated successfully",
                saga_id=saga.saga_id,
                step_id=step_id
            )
            
        except Exception as e:
            logger.error(
                "Failed to compensate saga step",
                saga_id=saga.saga_id,
                step_id=step_id,
                error=str(e)
            )
            # Continue with other compensations
    
    async def _store_saga(self, saga: SagaTransaction) -> None:
        """Store saga state in Redis."""
        key = f"{self.key_prefix}:{saga.saga_id}"
        data = saga.json()
        
        # Store with TTL
        await self.redis.setex(key, self.default_timeout, data)
    
    async def _load_saga(self, saga_id: str) -> Optional[SagaTransaction]:
        """Load saga state from Redis."""
        key = f"{self.key_prefix}:{saga_id}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        return SagaTransaction.parse_raw(data)
    
    async def get_saga_status(self, saga_id: str) -> Optional[Dict[str, Any]]:
        """Get saga status and progress."""
        saga = await self._load_saga(saga_id)
        if not saga:
            return None
        
        return {
            "saga_id": saga.saga_id,
            "name": saga.name,
            "status": saga.status,
            "current_step": saga.current_step,
            "total_steps": len(saga.steps),
            "progress": saga.current_step / len(saga.steps) if saga.steps else 0,
            "created_at": saga.created_at,
            "started_at": saga.started_at,
            "completed_at": saga.completed_at,
            "error": saga.error
        }
    
    async def cancel_saga(self, saga_id: str) -> bool:
        """Cancel running saga and start compensation."""
        if saga_id in self.active_sagas:
            task = self.active_sagas[saga_id]
            task.cancel()
            
            # Load saga and start compensation
            saga = await self._load_saga(saga_id)
            if saga and saga.status == SagaStatus.RUNNING:
                saga.status = SagaStatus.COMPENSATING
                saga.error = "Cancelled by user"
                await self._store_saga(saga)
                
                # Start compensation for completed steps
                await self._compensate_saga(saga, saga.current_step)
                
            return True
        
        return False
    
    async def cleanup_completed_sagas(self, max_age_hours: int = 24) -> int:
        """Clean up old completed sagas."""
        pattern = f"{self.key_prefix}:*"
        cursor = 0
        deleted_count = 0
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        while True:
            cursor, keys = await self.redis.scan(
                cursor=cursor,
                match=pattern,
                count=100
            )
            
            for key in keys:
                try:
                    data = await self.redis.get(key)
                    if data:
                        saga = SagaTransaction.parse_raw(data)
                        
                        # Delete if completed and old enough
                        if (saga.status in (SagaStatus.COMPLETED, SagaStatus.COMPENSATED, SagaStatus.FAILED) and
                            saga.completed_at and saga.completed_at < cutoff_time):
                            
                            await self.redis.delete(key)
                            deleted_count += 1
                            
                except Exception as e:
                    logger.warning(
                        "Error during saga cleanup",
                        key=key,
                        error=str(e)
                    )
            
            if cursor == 0:
                break
        
        if deleted_count > 0:
            logger.info(
                "Cleaned up completed sagas",
                deleted_count=deleted_count,
                max_age_hours=max_age_hours
            )
        
        return deleted_count