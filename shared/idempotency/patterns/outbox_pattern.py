"""
Outbox pattern implementation for reliable event publishing in EAFIX trading system.
Ensures exactly-once delivery of events by storing them in the same transaction as business data.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum
import uuid

from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class EventStatus(str, Enum):
    """Status of outbox event."""
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
    EXPIRED = "expired"


class EventPriority(str, Enum):
    """Priority of outbox event."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class OutboxEvent(BaseModel):
    """Event stored in the outbox for reliable publishing."""
    
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(..., description="Type of event")
    aggregate_id: str = Field(..., description="ID of the aggregate that produced the event")
    aggregate_type: str = Field(..., description="Type of aggregate")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Routing information
    topic: str = Field(..., description="Message topic/channel")
    routing_key: Optional[str] = Field(None, description="Message routing key")
    
    # Status and timing
    status: EventStatus = Field(default=EventStatus.PENDING)
    priority: EventPriority = Field(default=EventPriority.NORMAL)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = Field(None, description="When to publish the event")
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Retry information
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    retry_delay_seconds: float = Field(default=1.0)
    last_error: Optional[str] = None
    
    # Idempotency
    idempotency_key: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class OutboxProcessor:
    """
    Outbox pattern processor for reliable event publishing.
    
    Features:
    - Transactional event storage
    - Reliable event publishing
    - Retry with exponential backoff
    - Dead letter queue for failed events
    - Event deduplication
    - Batch processing
    """
    
    def __init__(
        self,
        redis_client,
        event_publisher: Callable[[OutboxEvent], bool],
        outbox_table: str = "outbox_events",
        batch_size: int = 100,
        processing_interval: float = 1.0,
        max_retry_delay: float = 300.0,  # 5 minutes
        event_ttl_hours: int = 24
    ):
        """
        Initialize outbox processor.
        
        Args:
            redis_client: Redis client for event storage
            event_publisher: Function to publish events
            outbox_table: Redis key prefix for events
            batch_size: Number of events to process per batch
            processing_interval: Seconds between processing cycles
            max_retry_delay: Maximum delay between retries
            event_ttl_hours: TTL for events in hours
        """
        self.redis = redis_client
        self.publisher = event_publisher
        self.outbox_table = outbox_table
        self.batch_size = batch_size
        self.processing_interval = processing_interval
        self.max_retry_delay = max_retry_delay
        self.event_ttl = event_ttl_hours * 3600  # Convert to seconds
        
        # Processing state
        self.is_running = False
        self.processor_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.events_processed = 0
        self.events_published = 0
        self.events_failed = 0
        
        # Event type handlers
        self.event_handlers: Dict[str, Callable[[OutboxEvent], bool]] = {}
        
        # Dead letter queue
        self.dlq_key = f"{outbox_table}:dlq"
    
    def register_event_handler(
        self,
        event_type: str,
        handler: Callable[[OutboxEvent], bool]
    ) -> None:
        """
        Register custom handler for specific event type.
        
        Args:
            event_type: Event type to handle
            handler: Handler function
        """
        self.event_handlers[event_type] = handler
        logger.info(
            "Registered event handler",
            event_type=event_type
        )
    
    async def store_event(
        self,
        event: OutboxEvent,
        transaction_key: Optional[str] = None
    ) -> None:
        """
        Store event in outbox for later publishing.
        
        Args:
            event: Event to store
            transaction_key: Optional transaction key for grouping
        """
        # Generate event key
        event_key = f"{self.outbox_table}:event:{event.event_id}"
        
        # Set expiration if not provided
        if not event.expires_at:
            event.expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.event_ttl)
        
        # Store event
        await self.redis.setex(
            event_key,
            self.event_ttl,
            event.json()
        )
        
        # Add to pending queue with priority
        priority_score = self._get_priority_score(event)
        await self.redis.zadd(
            f"{self.outbox_table}:pending",
            {event.event_id: priority_score}
        )
        
        # Add to transaction group if specified
        if transaction_key:
            await self.redis.sadd(
                f"{self.outbox_table}:tx:{transaction_key}",
                event.event_id
            )
            await self.redis.expire(
                f"{self.outbox_table}:tx:{transaction_key}",
                self.event_ttl
            )
        
        logger.info(
            "Stored event in outbox",
            event_id=event.event_id,
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
            topic=event.topic,
            priority=event.priority
        )
    
    async def store_events_batch(
        self,
        events: List[OutboxEvent],
        transaction_key: Optional[str] = None
    ) -> None:
        """
        Store multiple events atomically.
        
        Args:
            events: List of events to store
            transaction_key: Optional transaction key for grouping
        """
        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()
        
        for event in events:
            # Generate event key
            event_key = f"{self.outbox_table}:event:{event.event_id}"
            
            # Set expiration if not provided
            if not event.expires_at:
                event.expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.event_ttl)
            
            # Store event
            pipe.setex(event_key, self.event_ttl, event.json())
            
            # Add to pending queue
            priority_score = self._get_priority_score(event)
            pipe.zadd(
                f"{self.outbox_table}:pending",
                {event.event_id: priority_score}
            )
            
            # Add to transaction group if specified
            if transaction_key:
                pipe.sadd(
                    f"{self.outbox_table}:tx:{transaction_key}",
                    event.event_id
                )
        
        # Set transaction expiration
        if transaction_key:
            pipe.expire(
                f"{self.outbox_table}:tx:{transaction_key}",
                self.event_ttl
            )
        
        # Execute all operations atomically
        await pipe.execute()
        
        logger.info(
            "Stored events batch in outbox",
            event_count=len(events),
            transaction_key=transaction_key
        )
    
    def _get_priority_score(self, event: OutboxEvent) -> float:
        """Calculate priority score for event ordering."""
        # Base score from priority
        priority_scores = {
            EventPriority.CRITICAL: 4.0,
            EventPriority.HIGH: 3.0,
            EventPriority.NORMAL: 2.0,
            EventPriority.LOW: 1.0
        }
        
        base_score = priority_scores.get(event.priority, 2.0)
        
        # Add timestamp component (newer events get slightly higher priority)
        timestamp_score = event.created_at.timestamp() / 1e10
        
        # Scheduled events get lower priority until their time
        if event.scheduled_at and event.scheduled_at > datetime.now(timezone.utc):
            base_score *= 0.1
        
        return base_score + timestamp_score
    
    async def start_processing(self) -> None:
        """Start the outbox processor."""
        if self.is_running:
            logger.warning("Outbox processor already running")
            return
        
        self.is_running = True
        self.processor_task = asyncio.create_task(self._processing_loop())
        
        logger.info(
            "Started outbox processor",
            batch_size=self.batch_size,
            processing_interval=self.processing_interval
        )
    
    async def stop_processing(self) -> None:
        """Stop the outbox processor."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped outbox processor")
    
    async def _processing_loop(self) -> None:
        """Main processing loop."""
        while self.is_running:
            try:
                # Process batch of events
                processed_count = await self._process_batch()
                
                if processed_count == 0:
                    # No events to process, wait
                    await asyncio.sleep(self.processing_interval)
                else:
                    # Events processed, small delay
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Error in outbox processing loop",
                    error=str(e)
                )
                await asyncio.sleep(self.processing_interval)
        
        logger.info("Outbox processing loop stopped")
    
    async def _process_batch(self) -> int:
        """Process a batch of pending events."""
        # Get pending events by priority
        pending_events = await self.redis.zrevrange(
            f"{self.outbox_table}:pending",
            0, self.batch_size - 1,
            withscores=True
        )
        
        if not pending_events:
            return 0
        
        processed_count = 0
        
        for event_id_bytes, score in pending_events:
            event_id = event_id_bytes.decode('utf-8')
            
            try:
                # Load event
                event = await self._load_event(event_id)
                if not event:
                    # Event not found, remove from pending
                    await self.redis.zrem(f"{self.outbox_table}:pending", event_id)
                    continue
                
                # Check if event is ready to be processed
                if not self._is_event_ready(event):
                    continue
                
                # Process event
                success = await self._process_event(event)
                
                if success:
                    # Remove from pending queue
                    await self.redis.zrem(f"{self.outbox_table}:pending", event_id)
                    self.events_published += 1
                else:
                    # Handle failure
                    await self._handle_event_failure(event)
                    self.events_failed += 1
                
                processed_count += 1
                self.events_processed += 1
                
            except Exception as e:
                logger.error(
                    "Error processing event",
                    event_id=event_id,
                    error=str(e)
                )
        
        return processed_count
    
    def _is_event_ready(self, event: OutboxEvent) -> bool:
        """Check if event is ready to be processed."""
        now = datetime.now(timezone.utc)
        
        # Check expiration
        if event.expires_at and now > event.expires_at:
            return False
        
        # Check scheduled time
        if event.scheduled_at and now < event.scheduled_at:
            return False
        
        return True
    
    async def _process_event(self, event: OutboxEvent) -> bool:
        """Process individual event."""
        try:
            # Use custom handler if available
            if event.event_type in self.event_handlers:
                handler = self.event_handlers[event.event_type]
                success = await self._call_handler(handler, event)
            else:
                # Use default publisher
                success = await self._call_handler(self.publisher, event)
            
            if success:
                # Update event status
                event.status = EventStatus.PUBLISHED
                event.published_at = datetime.now(timezone.utc)
                await self._update_event(event)
                
                logger.info(
                    "Published event successfully",
                    event_id=event.event_id,
                    event_type=event.event_type,
                    topic=event.topic,
                    retry_count=event.retry_count
                )
                
                return True
            else:
                logger.warning(
                    "Failed to publish event",
                    event_id=event.event_id,
                    event_type=event.event_type,
                    retry_count=event.retry_count
                )
                return False
                
        except Exception as e:
            logger.error(
                "Exception while processing event",
                event_id=event.event_id,
                error=str(e)
            )
            event.last_error = str(e)
            return False
    
    async def _call_handler(self, handler: Callable, event: OutboxEvent) -> bool:
        """Call event handler with timeout."""
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await asyncio.wait_for(handler(event), timeout=30.0)
            else:
                result = handler(event)
            
            return bool(result)
            
        except asyncio.TimeoutError:
            logger.warning(
                "Event handler timeout",
                event_id=event.event_id,
                handler=handler.__name__
            )
            return False
        except Exception as e:
            logger.error(
                "Event handler exception",
                event_id=event.event_id,
                handler=handler.__name__,
                error=str(e)
            )
            return False
    
    async def _handle_event_failure(self, event: OutboxEvent) -> None:
        """Handle failed event processing."""
        event.retry_count += 1
        
        if event.retry_count >= event.max_retries:
            # Move to dead letter queue
            await self._move_to_dlq(event)
            await self.redis.zrem(f"{self.outbox_table}:pending", event.event_id)
            
            logger.error(
                "Event moved to dead letter queue",
                event_id=event.event_id,
                event_type=event.event_type,
                retry_count=event.retry_count
            )
        else:
            # Schedule retry with exponential backoff
            delay = min(
                event.retry_delay_seconds * (2 ** (event.retry_count - 1)),
                self.max_retry_delay
            )
            
            retry_time = datetime.now(timezone.utc) + timedelta(seconds=delay)
            event.scheduled_at = retry_time
            
            # Update priority score to delay processing
            priority_score = self._get_priority_score(event)
            await self.redis.zadd(
                f"{self.outbox_table}:pending",
                {event.event_id: priority_score}
            )
            
            await self._update_event(event)
            
            logger.info(
                "Scheduled event retry",
                event_id=event.event_id,
                retry_count=event.retry_count,
                retry_delay=delay,
                retry_at=retry_time
            )
    
    async def _move_to_dlq(self, event: OutboxEvent) -> None:
        """Move event to dead letter queue."""
        event.status = EventStatus.FAILED
        
        # Store in DLQ
        dlq_event_key = f"{self.dlq_key}:event:{event.event_id}"
        await self.redis.setex(dlq_event_key, self.event_ttl, event.json())
        
        # Add to DLQ index
        await self.redis.zadd(
            self.dlq_key,
            {event.event_id: datetime.now(timezone.utc).timestamp()}
        )
    
    async def _load_event(self, event_id: str) -> Optional[OutboxEvent]:
        """Load event from storage."""
        event_key = f"{self.outbox_table}:event:{event_id}"
        data = await self.redis.get(event_key)
        
        if not data:
            return None
        
        try:
            return OutboxEvent.parse_raw(data)
        except Exception as e:
            logger.error(
                "Error parsing event data",
                event_id=event_id,
                error=str(e)
            )
            return None
    
    async def _update_event(self, event: OutboxEvent) -> None:
        """Update event in storage."""
        event_key = f"{self.outbox_table}:event:{event.event_id}"
        await self.redis.setex(event_key, self.event_ttl, event.json())
    
    async def get_pending_count(self) -> int:
        """Get count of pending events."""
        return await self.redis.zcard(f"{self.outbox_table}:pending")
    
    async def get_dlq_count(self) -> int:
        """Get count of dead letter queue events."""
        return await self.redis.zcard(self.dlq_key)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics."""
        pending_count = await self.get_pending_count()
        dlq_count = await self.get_dlq_count()
        
        return {
            "is_running": self.is_running,
            "pending_events": pending_count,
            "dead_letter_events": dlq_count,
            "events_processed": self.events_processed,
            "events_published": self.events_published,
            "events_failed": self.events_failed,
            "success_rate": (
                self.events_published / max(self.events_processed, 1)
            ) if self.events_processed > 0 else 0.0,
            "batch_size": self.batch_size,
            "processing_interval": self.processing_interval
        }
    
    async def reprocess_dlq_events(self, limit: int = 100) -> int:
        """Reprocess events from dead letter queue."""
        # Get DLQ events
        dlq_events = await self.redis.zrange(
            self.dlq_key,
            0, limit - 1
        )
        
        reprocessed = 0
        
        for event_id_bytes in dlq_events:
            event_id = event_id_bytes.decode('utf-8')
            
            try:
                # Load event from DLQ
                dlq_event_key = f"{self.dlq_key}:event:{event_id}"
                data = await self.redis.get(dlq_event_key)
                
                if data:
                    event = OutboxEvent.parse_raw(data)
                    
                    # Reset for reprocessing
                    event.status = EventStatus.PENDING
                    event.retry_count = 0
                    event.scheduled_at = None
                    event.last_error = None
                    
                    # Move back to pending queue
                    priority_score = self._get_priority_score(event)
                    await self.redis.zadd(
                        f"{self.outbox_table}:pending",
                        {event.event_id: priority_score}
                    )
                    
                    # Update event
                    await self._update_event(event)
                    
                    # Remove from DLQ
                    await self.redis.zrem(self.dlq_key, event_id)
                    await self.redis.delete(dlq_event_key)
                    
                    reprocessed += 1
                    
                    logger.info(
                        "Moved event from DLQ to pending",
                        event_id=event_id
                    )
                    
            except Exception as e:
                logger.error(
                    "Error reprocessing DLQ event",
                    event_id=event_id,
                    error=str(e)
                )
        
        if reprocessed > 0:
            logger.info(
                "Reprocessed DLQ events",
                reprocessed_count=reprocessed
            )
        
        return reprocessed