# doc_id: DOC-AUTOOPS-021
"""Event and work item models for file system events and queue processing."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

__doc_id__ = "DOC-AUTOOPS-021"


class EventType(str, Enum):
    """File system event types."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


class WorkItemStatus(str, Enum):
    """Work item processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    QUARANTINED = "quarantined"


class FileEvent(BaseModel):
    """File system event."""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    file_path: Path
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stable: bool = False
    content_hash: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class WorkItem(BaseModel):
    """Persistent work item for event queue."""
    work_item_id: str
    path: str
    event_type: str
    first_seen: int
    last_seen: int
    attempts: int = 0
    status: WorkItemStatus = WorkItemStatus.PENDING
    error: Optional[str] = None

    class Config:
        use_enum_values = True
