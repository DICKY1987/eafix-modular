"""Event broadcasting system for real-time updates."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import redis

from .connection_manager import connection_manager

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Supported event types."""
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PROGRESS = "workflow.progress"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    AGENT_STATUS = "agent.status"
    SYSTEM_HEALTH = "system.health"
    NOTIFICATION = "notification"
    ERROR_RECOVERY = "error.recovery"
    COST_ALERT = "cost.alert"

@dataclass
class WorkflowEvent:
    """Workflow-related event."""
    event_type: EventType
    workflow_id: str
    timestamp: datetime
    data: Dict[str, Any]
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.event_type.value,
            "workflow_id": self.workflow_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "user_id": self.user_id
        }

class EventBroadcaster:
    """Handles broadcasting of events to WebSocket connections."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        self.event_history: List[WorkflowEvent] = []
        self.max_history = 1000
        
    async def broadcast_workflow_started(self, workflow_id: str, workflow_data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast workflow started event."""
        event = WorkflowEvent(
            event_type=EventType.WORKFLOW_STARTED,
            workflow_id=workflow_id,
            timestamp=datetime.now(),
            data=workflow_data,
            user_id=user_id
        )
        await self._broadcast_event(event)
    
    async def broadcast_workflow_progress(self, workflow_id: str, progress_data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast workflow progress update."""
        event = WorkflowEvent(
            event_type=EventType.WORKFLOW_PROGRESS,
            workflow_id=workflow_id,
            timestamp=datetime.now(),
            data=progress_data,
            user_id=user_id
        )
        await self._broadcast_event(event)
    
    async def broadcast_workflow_completed(self, workflow_id: str, result_data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast workflow completion."""
        event = WorkflowEvent(
            event_type=EventType.WORKFLOW_COMPLETED,
            workflow_id=workflow_id,
            timestamp=datetime.now(),
            data=result_data,
            user_id=user_id
        )
        await self._broadcast_event(event)
    
    async def broadcast_workflow_failed(self, workflow_id: str, error_data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast workflow failure."""
        event = WorkflowEvent(
            event_type=EventType.WORKFLOW_FAILED,
            workflow_id=workflow_id,
            timestamp=datetime.now(),
            data=error_data,
            user_id=user_id
        )
        await self._broadcast_event(event)
    
    async def broadcast_task_update(self, workflow_id: str, task_id: str, status: str, data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast task status update."""
        event_type = EventType.TASK_COMPLETED if status == "completed" else EventType.TASK_STARTED
        if status == "failed":
            event_type = EventType.TASK_FAILED
            
        event = WorkflowEvent(
            event_type=event_type,
            workflow_id=workflow_id,
            timestamp=datetime.now(),
            data={
                "task_id": task_id,
                "status": status,
                **data
            },
            user_id=user_id
        )
        await self._broadcast_event(event)
    
    async def broadcast_agent_status(self, agent_id: str, status: str, data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast agent status update."""
        event = WorkflowEvent(
            event_type=EventType.AGENT_STATUS,
            workflow_id="system",  # System-level event
            timestamp=datetime.now(),
            data={
                "agent_id": agent_id,
                "status": status,
                **data
            },
            user_id=user_id
        )
        await self._broadcast_event(event)
    
    async def broadcast_system_health(self, health_data: Dict[str, Any]):
        """Broadcast system health update."""
        event = WorkflowEvent(
            event_type=EventType.SYSTEM_HEALTH,
            workflow_id="system",
            timestamp=datetime.now(),
            data=health_data
        )
        await self._broadcast_event(event)
    
    async def broadcast_notification(self, message: str, level: str = "info", data: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
        """Broadcast notification to users."""
        event = WorkflowEvent(
            event_type=EventType.NOTIFICATION,
            workflow_id="system",
            timestamp=datetime.now(),
            data={
                "message": message,
                "level": level,
                **(data or {})
            },
            user_id=user_id
        )
        await self._broadcast_event(event)
    
    async def broadcast_error_recovery(self, error_code: str, recovery_action: str, data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast error recovery event."""
        event = WorkflowEvent(
            event_type=EventType.ERROR_RECOVERY,
            workflow_id="system",
            timestamp=datetime.now(),
            data={
                "error_code": error_code,
                "recovery_action": recovery_action,
                **data
            },
            user_id=user_id
        )
        await self._broadcast_event(event)
    
    async def broadcast_cost_alert(self, service: str, cost_data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast cost alert."""
        event = WorkflowEvent(
            event_type=EventType.COST_ALERT,
            workflow_id="system",
            timestamp=datetime.now(),
            data={
                "service": service,
                **cost_data
            },
            user_id=user_id
        )
        await self._broadcast_event(event)
    
    async def _broadcast_event(self, event: WorkflowEvent):
        """Internal method to broadcast event to appropriate channels."""
        try:
            # Store in history
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history = self.event_history[-self.max_history:]
            
            # Store in Redis for persistence
            event_key = f"event:{event.workflow_id}:{event.timestamp.isoformat()}"
            self.redis_client.setex(event_key, 86400, json.dumps(event.to_dict()))  # 24h TTL
            
            # Determine broadcast targets
            message = event.to_dict()
            
            # Broadcast to workflow-specific topic
            if event.workflow_id != "system":
                topic = f"workflow:{event.workflow_id}"
                await connection_manager.broadcast_to_topic(topic, message)
            
            # Broadcast to event type topic
            event_topic = f"events:{event.event_type.value}"
            await connection_manager.broadcast_to_topic(event_topic, message)
            
            # Broadcast to user-specific topic if user_id provided
            if event.user_id:
                user_topic = f"user:{event.user_id}"
                await connection_manager.broadcast_to_topic(user_topic, message)
            
            # Broadcast system events to all connections
            if event.workflow_id == "system":
                await connection_manager.broadcast_to_all(message)
                
            logger.info(f"Broadcasted event: {event.event_type.value} for workflow: {event.workflow_id}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast event {event.event_type.value}: {e}")
    
    def get_recent_events(self, workflow_id: Optional[str] = None, event_type: Optional[EventType] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events with optional filtering."""
        events = self.event_history
        
        if workflow_id:
            events = [e for e in events if e.workflow_id == workflow_id]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Return most recent events
        return [e.to_dict() for e in events[-limit:]]
    
    async def get_workflow_events(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all events for a specific workflow."""
        try:
            # Get from Redis
            pattern = f"event:{workflow_id}:*"
            keys = self.redis_client.keys(pattern)
            
            events = []
            for key in keys:
                event_data = self.redis_client.get(key)
                if event_data:
                    events.append(json.loads(event_data))
            
            # Sort by timestamp
            events.sort(key=lambda x: x.get("timestamp", ""))
            return events
            
        except Exception as e:
            logger.error(f"Failed to get workflow events for {workflow_id}: {e}")
            return []

# Global event broadcaster instance
event_broadcaster = EventBroadcaster()