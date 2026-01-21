# doc_id: DOC-SERVICE-0215
# DOC_ID: DOC-SERVICE-0054
"""
Event Gateway Core

Implements event-driven messaging, Redis pub/sub management, event routing,
transformation, and validation between EAFIX services.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import re
import uuid

import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)


class MessageStatus(Enum):
    """Message processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    FILTERED = "filtered"


@dataclass
class EventMessage:
    """Event message structure."""
    
    id: str
    topic: str
    event_type: str
    schema_version: str
    payload: Dict[str, Any]
    timestamp: datetime
    producer: Optional[str] = None
    trace_id: Optional[str] = None
    retry_count: int = 0
    status: MessageStatus = MessageStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventMessage':
        """Create from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['status'] = MessageStatus(data['status'])
        return cls(**data)
    
    def to_redis_message(self) -> str:
        """Convert to Redis message format."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_redis_message(cls, message_data: str) -> 'EventMessage':
        """Create from Redis message."""
        data = json.loads(message_data)
        return cls.from_dict(data)


class EventFilter:
    """Event filtering engine."""
    
    def __init__(self, settings):
        self.settings = settings
        self.filters = settings.event_filters
    
    def apply_filters(self, message: EventMessage, filter_names: List[str]) -> bool:
        """Apply named filters to a message."""
        if not self.settings.event_filtering_enabled:
            return True
        
        for filter_name in filter_names:
            if filter_name in self.filters:
                if not self._apply_filter_rules(message, self.filters[filter_name]):
                    logger.debug(
                        "Message filtered out",
                        message_id=message.id,
                        filter=filter_name
                    )
                    return False
        
        return True
    
    def _apply_filter_rules(self, message: EventMessage, rules: List[Dict[str, Any]]) -> bool:
        """Apply a set of filter rules."""
        for rule in rules:
            if not self._apply_single_rule(message, rule):
                return False
        return True
    
    def _apply_single_rule(self, message: EventMessage, rule: Dict[str, Any]) -> bool:
        """Apply a single filter rule."""
        field = rule.get("field")
        operator = rule.get("operator")
        expected_value = rule.get("value")
        expected_values = rule.get("values", [])
        
        # Extract field value from message
        if field in message.payload:
            field_value = message.payload[field]
        elif hasattr(message, field):
            field_value = getattr(message, field)
        else:
            return operator == "not_exists"
        
        # Apply operator
        if operator == "==":
            return field_value == expected_value
        elif operator == "!=":
            return field_value != expected_value
        elif operator == ">":
            return field_value > expected_value
        elif operator == ">=":
            return field_value >= expected_value
        elif operator == "<":
            return field_value < expected_value
        elif operator == "<=":
            return field_value <= expected_value
        elif operator == "in":
            return field_value in expected_values
        elif operator == "not_in":
            return field_value not in expected_values
        elif operator == "contains":
            return expected_value in str(field_value)
        elif operator == "not_null":
            return field_value is not None
        elif operator == "is_null":
            return field_value is None
        elif operator == "recent_minutes":
            if isinstance(field_value, str):
                try:
                    msg_time = datetime.fromisoformat(field_value)
                    return datetime.utcnow() - msg_time < timedelta(minutes=expected_value)
                except ValueError:
                    return False
            return False
        elif operator == "matches_regex":
            return bool(re.match(expected_value, str(field_value)))
        else:
            logger.warning("Unknown filter operator", operator=operator)
            return True


class EventTransformer:
    """Event transformation engine."""
    
    def __init__(self, settings):
        self.settings = settings
    
    def transform_message(self, message: EventMessage, transformation: str) -> EventMessage:
        """Transform a message using the specified transformation."""
        if not self.settings.event_transformation_enabled or transformation == "none":
            return message
        
        try:
            if transformation == "add_timestamp":
                return self._add_timestamp(message)
            elif transformation == "add_priority_flag":
                return self._add_priority_flag(message)
            elif transformation == "extract_fill_info":
                return self._extract_fill_info(message)
            elif transformation == "extract_rejection_info":
                return self._extract_rejection_info(message)
            else:
                logger.warning("Unknown transformation", transformation=transformation)
                return message
        
        except Exception as e:
            logger.error("Transformation failed", error=str(e), transformation=transformation)
            return message
    
    def _add_timestamp(self, message: EventMessage) -> EventMessage:
        """Add processing timestamp to message."""
        message.payload["processed_at"] = datetime.utcnow().isoformat()
        return message
    
    def _add_priority_flag(self, message: EventMessage) -> EventMessage:
        """Add priority flag to high-confidence signals."""
        if message.payload.get("confidence_score", 0) > 0.8:
            message.payload["priority"] = "HIGH"
        return message
    
    def _extract_fill_info(self, message: EventMessage) -> EventMessage:
        """Extract fill information from execution report."""
        if "fill_price" in message.payload and "fill_quantity" in message.payload:
            message.payload["fill_info"] = {
                "price": message.payload["fill_price"],
                "quantity": message.payload["fill_quantity"],
                "timestamp": message.payload.get("fill_timestamp", message.timestamp.isoformat())
            }
        return message
    
    def _extract_rejection_info(self, message: EventMessage) -> EventMessage:
        """Extract rejection information from execution report."""
        if "rejection_reason" in message.payload:
            message.payload["rejection_info"] = {
                "reason": message.payload["rejection_reason"],
                "code": message.payload.get("rejection_code"),
                "timestamp": message.timestamp.isoformat()
            }
        return message


class EventRouter:
    """Event routing engine."""
    
    def __init__(self, settings):
        self.settings = settings
        self.transformer = EventTransformer(settings)
        self.filter = EventFilter(settings)
    
    def route_event(self, message: EventMessage) -> List[Dict[str, Any]]:
        """Route an event to target topics based on routing rules."""
        routing_results = []
        
        if not self.settings.event_routing_enabled:
            return [{"topic": message.topic, "message": message, "routed": False, "reason": "routing_disabled"}]
        
        # Get routing rules for this event type
        event_schema = f"{message.event_type}@{message.schema_version}"
        routing_rules = self.settings.get_routing_rules(event_schema)
        
        if not routing_rules:
            # No specific routing rules, use default topic
            return [{"topic": message.topic, "message": message, "routed": False, "reason": "no_rules"}]
        
        for rule in routing_rules:
            if self._evaluate_condition(message, rule.get("condition", "always")):
                # Apply transformation
                transformation = rule.get("transform", "none")
                transformed_message = self.transformer.transform_message(message, transformation)
                
                # Route to target topics
                target_topics = rule.get("target_topics", [])
                for target_topic in target_topics:
                    # Create new message for this topic
                    routed_message = EventMessage(
                        id=str(uuid.uuid4()),
                        topic=target_topic,
                        event_type=transformed_message.event_type,
                        schema_version=transformed_message.schema_version,
                        payload=transformed_message.payload.copy(),
                        timestamp=transformed_message.timestamp,
                        producer=transformed_message.producer,
                        trace_id=transformed_message.trace_id
                    )
                    
                    routing_results.append({
                        "topic": target_topic,
                        "message": routed_message,
                        "routed": True,
                        "rule": rule
                    })
        
        return routing_results
    
    def _evaluate_condition(self, message: EventMessage, condition: str) -> bool:
        """Evaluate a routing condition."""
        if condition == "always":
            return True
        
        try:
            # Simple condition evaluation (could be extended with a proper expression engine)
            if "==" in condition:
                field, value = condition.split("==", 1)
                field = field.strip()
                value = value.strip().strip("'\"")
                
                if field in message.payload:
                    return str(message.payload[field]) == value
                elif hasattr(message, field):
                    return str(getattr(message, field)) == value
            
            elif ">" in condition:
                field, value = condition.split(">", 1)
                field = field.strip()
                value = float(value.strip())
                
                if field in message.payload:
                    return float(message.payload[field]) > value
            
            # Add more condition types as needed
            
            return False
            
        except Exception as e:
            logger.error("Condition evaluation failed", condition=condition, error=str(e))
            return False


class EventGateway:
    """Core event gateway for message routing and processing."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # Redis clients
        self.redis_client: Optional[redis.Redis] = None
        self.redis_pool: Optional[redis.ConnectionPool] = None
        
        # Message processing
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        
        # Event processing components
        self.router = EventRouter(settings)
        self.filter = EventFilter(settings)
        
        # Performance tracking
        self.message_counts: Dict[str, int] = {}
        self.latency_tracking: Dict[str, List[float]] = {}
        
        # Dead letter queue
        self.dead_letter_messages: List[EventMessage] = []
        
        self.running = False
    
    async def start(self) -> None:
        """Start the event gateway."""
        if self.running:
            return
        
        logger.info("Starting Event Gateway")
        
        # Validate configuration
        config_errors = self.settings.validate_topic_config()
        if config_errors:
            raise RuntimeError(f"Invalid topic configuration: {config_errors}")
        
        # Initialize Redis connection
        self.redis_pool = redis.ConnectionPool.from_url(
            self.settings.redis_url,
            max_connections=self.settings.redis_pool_max_connections
        )
        self.redis_client = redis.Redis(connection_pool=self.redis_pool)
        await self.redis_client.ping()
        logger.info("Connected to Redis", url=self.settings.redis_url)
        
        # Initialize message queues for all topics
        all_topics = self.settings.get_all_topics()
        for topic in all_topics:
            self.message_queues[topic] = asyncio.Queue(maxsize=self.settings.max_message_queue_size)
            self.message_counts[topic] = 0
            self.latency_tracking[topic] = []
        
        # Start processing tasks for each topic
        for topic in all_topics:
            self.processing_tasks[topic] = asyncio.create_task(
                self._process_topic_messages(topic)
            )
        
        # Start Redis subscriber tasks
        if self.settings.event_routing_enabled:
            asyncio.create_task(self._start_redis_subscribers())
        
        # Start performance monitoring
        if self.settings.performance_monitoring_enabled:
            asyncio.create_task(self._run_performance_monitoring())
        
        self.running = True
        logger.info("Event Gateway started successfully")
    
    async def stop(self) -> None:
        """Stop the event gateway."""
        if not self.running:
            return
        
        logger.info("Stopping Event Gateway")
        
        # Cancel all processing tasks
        for task in self.processing_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.processing_tasks.values(), return_exceptions=True)
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        if self.redis_pool:
            await self.redis_pool.disconnect()
        
        self.running = False
        logger.info("Event Gateway stopped")
    
    async def _start_redis_subscribers(self) -> None:
        """Start Redis pub/sub subscribers for all topics."""
        try:
            pubsub = self.redis_client.pubsub()
            
            # Subscribe to all configured topics
            topics_to_subscribe = list(self.settings.event_topics.keys())
            if topics_to_subscribe:
                await pubsub.subscribe(*topics_to_subscribe)
                logger.info("Subscribed to topics", topics=topics_to_subscribe)
            
            # Process messages
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        await self._handle_redis_message(
                            message["channel"].decode(),
                            message["data"].decode()
                        )
                    except Exception as e:
                        logger.error(
                            "Error processing Redis message",
                            channel=message["channel"].decode(),
                            error=str(e)
                        )
                        self.metrics.record_error("redis_message_error")
                        
        except asyncio.CancelledError:
            logger.info("Redis subscribers cancelled")
            await pubsub.unsubscribe()
            await pubsub.close()
        except Exception as e:
            logger.error("Redis subscriber failed", error=str(e))
    
    async def _handle_redis_message(self, channel: str, data: str) -> None:
        """Handle incoming Redis pub/sub message."""
        try:
            # Parse message
            message_data = json.loads(data)
            
            # Create event message
            event_message = EventMessage(
                id=message_data.get("id", str(uuid.uuid4())),
                topic=channel,
                event_type=message_data.get("event_type", "unknown"),
                schema_version=message_data.get("schema_version", "1.0"),
                payload=message_data.get("payload", message_data),
                timestamp=datetime.fromisoformat(message_data.get("timestamp", datetime.utcnow().isoformat())),
                producer=message_data.get("producer"),
                trace_id=message_data.get("trace_id")
            )
            
            # Queue for processing
            await self.enqueue_message(event_message)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in Redis message", channel=channel, data=data[:100])
            self.metrics.record_error("json_decode_error")
        except Exception as e:
            logger.error("Error handling Redis message", error=str(e), exc_info=True)
            self.metrics.record_error("message_handling_error")
    
    async def enqueue_message(self, message: EventMessage) -> None:
        """Enqueue a message for processing."""
        topic = message.topic
        
        if topic not in self.message_queues:
            logger.warning("Unknown topic", topic=topic)
            return
        
        try:
            await self.message_queues[topic].put(message)
            self.metrics.record_message_enqueued(topic)
            
            logger.debug(
                "Message enqueued",
                message_id=message.id,
                topic=topic,
                event_type=message.event_type
            )
            
        except asyncio.QueueFull:
            logger.error("Message queue full", topic=topic)
            self.metrics.record_error("queue_full", topic)
            
            # Send to dead letter queue
            if self.settings.dead_letter_enabled:
                await self._send_to_dead_letter(message, "queue_full")
    
    async def _process_topic_messages(self, topic: str) -> None:
        """Process messages for a specific topic."""
        try:
            queue = self.message_queues[topic]
            batch = []
            
            while self.running:
                try:
                    # Collect batch of messages
                    batch.clear()
                    
                    # Wait for at least one message
                    message = await asyncio.wait_for(
                        queue.get(),
                        timeout=self.settings.message_processing_interval_ms / 1000.0
                    )
                    batch.append(message)
                    
                    # Collect additional messages up to batch size
                    while len(batch) < self.settings.message_batch_size:
                        try:
                            message = queue.get_nowait()
                            batch.append(message)
                        except asyncio.QueueEmpty:
                            break
                    
                    # Process batch
                    await self._process_message_batch(topic, batch)
                    
                except asyncio.TimeoutError:
                    # No messages received in the timeout period, continue
                    continue
                except Exception as e:
                    logger.error("Message processing error", topic=topic, error=str(e))
                    self.metrics.record_error("message_processing_error", topic)
                    await asyncio.sleep(1)  # Brief pause before retry
                    
        except asyncio.CancelledError:
            logger.info("Message processing cancelled", topic=topic)
        except Exception as e:
            logger.error("Message processing task failed", topic=topic, error=str(e))
    
    async def _process_message_batch(self, topic: str, messages: List[EventMessage]) -> None:
        """Process a batch of messages."""
        start_time = time.time()
        
        try:
            processed_count = 0
            failed_count = 0
            
            for message in messages:
                try:
                    await self._process_single_message(message)
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(
                        "Message processing failed",
                        message_id=message.id,
                        topic=topic,
                        error=str(e)
                    )
                    failed_count += 1
                    
                    # Handle retry or dead letter
                    await self._handle_message_failure(message, str(e))
            
            batch_duration = time.time() - start_time
            
            # Record metrics
            self.metrics.record_message_batch_processed(
                topic, processed_count, failed_count, batch_duration
            )
            
            logger.debug(
                "Message batch processed",
                topic=topic,
                processed=processed_count,
                failed=failed_count,
                duration_seconds=batch_duration
            )
            
        except Exception as e:
            logger.error("Batch processing failed", topic=topic, error=str(e))
            self.metrics.record_error("batch_processing_error", topic)
    
    async def _process_single_message(self, message: EventMessage) -> None:
        """Process a single event message."""
        start_time = time.time()
        message.status = MessageStatus.PROCESSING
        
        try:
            # Validate message schema if enabled
            if self.settings.event_validation_enabled:
                if not await self._validate_message_schema(message):
                    message.status = MessageStatus.FILTERED
                    return
            
            # Apply event filtering
            topic_config = self.settings.get_topic_config(message.topic)
            if topic_config and "filters" in topic_config:
                if not self.filter.apply_filters(message, topic_config["filters"]):
                    message.status = MessageStatus.FILTERED
                    return
            
            # Route the message
            routing_results = self.router.route_event(message)
            
            # Publish routed messages
            for result in routing_results:
                if result["routed"]:
                    await self._publish_message(result["message"], result["topic"])
            
            message.status = MessageStatus.PROCESSED
            
            # Record processing metrics
            processing_time = time.time() - start_time
            self.metrics.record_message_processed(message.topic, processing_time, True)
            
            # Track latency
            if message.topic in self.latency_tracking:
                self.latency_tracking[message.topic].append(processing_time * 1000)
                if len(self.latency_tracking[message.topic]) > 1000:
                    self.latency_tracking[message.topic] = self.latency_tracking[message.topic][-1000:]
            
        except Exception as e:
            message.status = MessageStatus.FAILED
            processing_time = time.time() - start_time
            self.metrics.record_message_processed(message.topic, processing_time, False)
            raise
    
    async def _validate_message_schema(self, message: EventMessage) -> bool:
        """Validate message against its schema."""
        # Placeholder for schema validation
        # In a real implementation, this would validate against JSON schemas from contracts
        topic_config = self.settings.get_topic_config(message.topic)
        
        if not topic_config:
            return True  # Unknown topic, allow
        
        expected_schema = topic_config.get("schema")
        message_schema = f"{message.event_type}@{message.schema_version}"
        
        if expected_schema != message_schema:
            logger.warning(
                "Schema mismatch",
                message_id=message.id,
                expected=expected_schema,
                actual=message_schema
            )
            return not self.settings.schema_validation_strict
        
        return True
    
    async def _publish_message(self, message: EventMessage, topic: str) -> None:
        """Publish a message to Redis topic."""
        try:
            message_data = message.to_redis_message()
            await self.redis_client.publish(topic, message_data)
            
            self.metrics.record_message_published(topic)
            
            logger.debug(
                "Message published",
                message_id=message.id,
                topic=topic
            )
            
        except Exception as e:
            logger.error("Message publish failed", message_id=message.id, topic=topic, error=str(e))
            self.metrics.record_error("message_publish_error", topic)
            raise
    
    async def _handle_message_failure(self, message: EventMessage, error: str) -> None:
        """Handle message processing failure."""
        message.retry_count += 1
        
        if message.retry_count <= self.settings.max_retry_attempts:
            # Schedule for retry
            logger.info(
                "Scheduling message retry",
                message_id=message.id,
                retry_count=message.retry_count,
                max_retries=self.settings.max_retry_attempts
            )
            
            # Add delay before retry
            await asyncio.sleep(self.settings.retry_backoff_seconds)
            await self.enqueue_message(message)
        else:
            # Send to dead letter queue
            if self.settings.dead_letter_enabled:
                await self._send_to_dead_letter(message, f"max_retries_exceeded: {error}")
            
            logger.error(
                "Message failed after max retries",
                message_id=message.id,
                retry_count=message.retry_count,
                error=error
            )
    
    async def _send_to_dead_letter(self, message: EventMessage, reason: str) -> None:
        """Send message to dead letter queue."""
        message.status = MessageStatus.DEAD_LETTER
        
        # Add failure information
        message.payload["_failure_info"] = {
            "reason": reason,
            "failed_at": datetime.utcnow().isoformat(),
            "original_topic": message.topic,
            "retry_count": message.retry_count
        }
        
        # Store in dead letter queue
        self.dead_letter_messages.append(message)
        
        # Also publish to dead letter topic
        dead_letter_topic = self.settings.get_dead_letter_topic(message.topic)
        await self._publish_message(message, dead_letter_topic)
        
        self.metrics.record_dead_letter_message(message.topic)
        
        logger.warning(
            "Message sent to dead letter queue",
            message_id=message.id,
            original_topic=message.topic,
            reason=reason
        )
    
    async def _run_performance_monitoring(self) -> None:
        """Run performance monitoring loop."""
        try:
            while self.running:
                await self._update_performance_metrics()
                await asyncio.sleep(self.settings.throughput_monitoring_interval_seconds)
                
        except asyncio.CancelledError:
            logger.info("Performance monitoring cancelled")
        except Exception as e:
            logger.error("Performance monitoring failed", error=str(e))
    
    async def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        for topic, latencies in self.latency_tracking.items():
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                max_latency = max(latencies)
                
                self.metrics.set_gauge(f"message_latency_avg_ms", avg_latency, {"topic": topic})
                self.metrics.set_gauge(f"message_latency_max_ms", max_latency, {"topic": topic})
                
                # Check thresholds
                if avg_latency > self.settings.latency_critical_threshold_ms:
                    logger.error("Critical latency detected", topic=topic, avg_latency=avg_latency)
                elif avg_latency > self.settings.latency_warning_threshold_ms:
                    logger.warning("High latency detected", topic=topic, avg_latency=avg_latency)
    
    # Public API methods
    
    async def publish_event(self, event_type: str, schema_version: str, payload: Dict[str, Any],
                           topic: Optional[str] = None, producer: Optional[str] = None,
                           trace_id: Optional[str] = None) -> Dict[str, Any]:
        """Publish an event message."""
        try:
            # Determine topic if not specified
            if not topic:
                schema = f"{event_type}@{schema_version}"
                possible_topics = self.settings.get_topics_for_schema(schema)
                if not possible_topics:
                    raise ValueError(f"No topics configured for schema: {schema}")
                topic = possible_topics[0]
            
            # Create event message
            message = EventMessage(
                id=str(uuid.uuid4()),
                topic=topic,
                event_type=event_type,
                schema_version=schema_version,
                payload=payload,
                timestamp=datetime.utcnow(),
                producer=producer,
                trace_id=trace_id or str(uuid.uuid4())
            )
            
            # Queue for processing
            await self.enqueue_message(message)
            
            return {
                "success": True,
                "message_id": message.id,
                "topic": topic,
                "trace_id": message.trace_id
            }
            
        except Exception as e:
            logger.error("Event publish failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_topic_metrics(self, topic: str) -> Dict[str, Any]:
        """Get metrics for a specific topic."""
        queue_size = self.message_queues[topic].qsize() if topic in self.message_queues else 0
        message_count = self.message_counts.get(topic, 0)
        
        latencies = self.latency_tracking.get(topic, [])
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        return {
            "topic": topic,
            "queue_size": queue_size,
            "total_messages": message_count,
            "average_latency_ms": avg_latency,
            "latency_samples": len(latencies),
            "topic_config": self.settings.get_topic_config(topic)
        }
    
    async def get_dead_letter_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get dead letter messages."""
        return [msg.to_dict() for msg in self.dead_letter_messages[-limit:]]
    
    async def get_status(self) -> Dict[str, Any]:
        """Get event gateway status."""
        total_queue_size = sum(queue.qsize() for queue in self.message_queues.values())
        
        return {
            "running": self.running,
            "total_topics": len(self.message_queues),
            "total_queue_size": total_queue_size,
            "dead_letter_messages": len(self.dead_letter_messages),
            "processing_tasks": len(self.processing_tasks),
            "configuration": self.settings.get_event_gateway_config()
        }