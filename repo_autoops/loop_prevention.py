# doc_id: DOC-AUTOOPS-006
"""Loop prevention to avoid processing self-induced file changes."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID, uuid4

import structlog

__doc_id__ = "DOC-AUTOOPS-006"

logger = structlog.get_logger(__name__)


class Operation:
    """Represents an in-progress operation."""

    def __init__(self, operation_id: UUID, path: Path, operation_type: str):
        self.operation_id = operation_id
        self.path = path
        self.operation_type = operation_type
        self.started_at = time.time()


class LoopPrevention:
    """Prevents processing of self-induced file changes."""

    def __init__(self, suppression_window_seconds: float = 5.0):
        """Initialize loop prevention.

        Args:
            suppression_window_seconds: Time window to suppress events after operations
        """
        self.suppression_window = suppression_window_seconds
        self.operations_in_progress: Dict[str, Operation] = {}
        self.recent_operations: Dict[str, float] = {}  # path -> completed_at

    def start_operation(
        self, path: Path, operation_type: str
    ) -> UUID:
        """Mark the start of an operation that will modify a file.

        Args:
            path: File path being operated on
            operation_type: Type of operation (rename, write, etc.)

        Returns:
            Operation ID
        """
        operation_id = uuid4()
        path_str = str(path)

        operation = Operation(operation_id, path, operation_type)
        self.operations_in_progress[path_str] = operation

        logger.debug(
            "operation_started",
            operation_id=str(operation_id),
            path=path_str,
            type=operation_type,
        )

        return operation_id

    def end_operation(self, operation_id: UUID) -> None:
        """Mark the end of an operation.

        Args:
            operation_id: Operation ID from start_operation
        """
        # Find and remove from in-progress
        for path_str, op in list(self.operations_in_progress.items()):
            if op.operation_id == operation_id:
                del self.operations_in_progress[path_str]
                self.recent_operations[path_str] = time.time()
                logger.debug("operation_ended", operation_id=str(operation_id), path=path_str)
                break

    def is_self_induced(self, path: Path, event_time: Optional[float] = None) -> bool:
        """Check if a file event is self-induced.

        Args:
            path: File path
            event_time: Event timestamp (defaults to current time)

        Returns:
            True if event is likely self-induced
        """
        path_str = str(path)
        event_time = event_time or time.time()

        # Check if operation in progress
        if path_str in self.operations_in_progress:
            op = self.operations_in_progress[path_str]
            if event_time - op.started_at < self.suppression_window:
                logger.debug(
                    "self_induced_in_progress",
                    path=path_str,
                    operation_id=str(op.operation_id),
                )
                return True

        # Check recent operations
        if path_str in self.recent_operations:
            completed_at = self.recent_operations[path_str]
            elapsed = event_time - completed_at

            if elapsed < self.suppression_window:
                logger.debug(
                    "self_induced_recent",
                    path=path_str,
                    elapsed_seconds=elapsed,
                )
                return True

            # Clean up old entries
            if elapsed > self.suppression_window * 2:
                del self.recent_operations[path_str]

        return False

    def cleanup_stale_operations(self, max_age_seconds: float = 300.0) -> None:
        """Clean up operations that never ended (likely due to errors).

        Args:
            max_age_seconds: Max age before considering operation stale
        """
        now = time.time()
        stale_paths = [
            path_str
            for path_str, op in self.operations_in_progress.items()
            if now - op.started_at > max_age_seconds
        ]

        for path_str in stale_paths:
            op = self.operations_in_progress[path_str]
            logger.warning(
                "stale_operation_cleaned",
                path=path_str,
                operation_id=str(op.operation_id),
                age_seconds=now - op.started_at,
            )
            del self.operations_in_progress[path_str]
