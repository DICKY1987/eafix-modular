"""
doc_id: 2026011822400002
Audit Logger - Append-only JSONL event log for all identity operations.

Events logged:
- allocations
- moves/renames
- deprecations
- validation errors
- registry operations
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class AuditLogger:
    """Append-only audit log for identity system events."""

    def __init__(self, log_path: str):
        """
        Initialize audit logger.
        
        Args:
            log_path: Path to JSONL audit log file
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create log file if it doesn't exist
        if not self.log_path.exists():
            self.log_path.touch()

    def log_event(
        self,
        event_type: str,
        data: Dict,
        run_id: Optional[str] = None,
        severity: str = "info"
    ):
        """
        Log an event to the audit log.
        
        Args:
            event_type: Type of event (allocation, move, validation_error, etc.)
            data: Event data dictionary
            run_id: Optional run identifier for grouping events
            severity: Event severity (info, warning, error, critical)
        """
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "data": data
        }
        
        if run_id:
            event["run_id"] = run_id
        
        # Append to log file
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def log_allocation(
        self,
        doc_id: str,
        file_path: str,
        ns_code: str,
        type_code: str,
        allocated_by: str = "system",
        run_id: Optional[str] = None
    ):
        """Log an ID allocation event."""
        self.log_event(
            event_type="allocation",
            data={
                "doc_id": doc_id,
                "file_path": file_path,
                "ns_code": ns_code,
                "type_code": type_code,
                "allocated_by": allocated_by
            },
            run_id=run_id,
            severity="info"
        )

    def log_move(
        self,
        doc_id: str,
        old_path: str,
        new_path: str,
        run_id: Optional[str] = None
    ):
        """Log a file move/rename event."""
        self.log_event(
            event_type="move",
            data={
                "doc_id": doc_id,
                "old_path": old_path,
                "new_path": new_path
            },
            run_id=run_id,
            severity="info"
        )

    def log_deprecation(
        self,
        doc_id: str,
        reason: str,
        superseded_by: Optional[str] = None,
        run_id: Optional[str] = None
    ):
        """Log an ID deprecation event."""
        self.log_event(
            event_type="deprecation",
            data={
                "doc_id": doc_id,
                "reason": reason,
                "superseded_by": superseded_by
            },
            run_id=run_id,
            severity="warning"
        )

    def log_validation_error(
        self,
        error_type: str,
        details: Dict,
        run_id: Optional[str] = None
    ):
        """Log a validation error event."""
        self.log_event(
            event_type="validation_error",
            data={
                "error_type": error_type,
                "details": details
            },
            run_id=run_id,
            severity="error"
        )

    def log_registry_operation(
        self,
        operation: str,
        details: Dict,
        run_id: Optional[str] = None
    ):
        """Log a registry operation event."""
        self.log_event(
            event_type="registry_operation",
            data={
                "operation": operation,
                "details": details
            },
            run_id=run_id,
            severity="info"
        )

    def get_recent_events(self, limit: int = 100) -> list:
        """
        Get most recent events from the log.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        if not self.log_path.exists():
            return []
        
        events = []
        with open(self.log_path, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        
        return events[-limit:]

    def get_events_by_type(self, event_type: str, limit: int = 100) -> list:
        """
        Get events of a specific type.
        
        Args:
            event_type: Type of events to retrieve
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        if not self.log_path.exists():
            return []
        
        matching_events = []
        with open(self.log_path, 'r') as f:
            for line in f:
                if line.strip():
                    event = json.loads(line)
                    if event['event_type'] == event_type:
                        matching_events.append(event)
        
        return matching_events[-limit:]

    def get_events_by_run(self, run_id: str) -> list:
        """
        Get all events for a specific run.
        
        Args:
            run_id: Run identifier
            
        Returns:
            List of event dictionaries
        """
        if not self.log_path.exists():
            return []
        
        events = []
        with open(self.log_path, 'r') as f:
            for line in f:
                if line.strip():
                    event = json.loads(line)
                    if event.get('run_id') == run_id:
                        events.append(event)
        
        return events
