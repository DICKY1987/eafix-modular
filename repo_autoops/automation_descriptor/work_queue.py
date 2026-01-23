#!/usr/bin/env python3
"""
doc_id: 2026012322470005
Work Queue - SQLite-backed FIFO Queue with UPSERT-by-path

Persistent queue for filesystem events. Deduplicates by path to avoid
processing the same file multiple times when rapid changes occur.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WorkItemStatus(Enum):
    """Status values for work items."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class WorkQueue:
    """
    SQLite-backed work queue with UPSERT-by-path deduplication.
    
    Features:
    - UNIQUE constraint on path (latest event wins)
    - Status tracking (queued/running/completed/failed)
    - Retry limit enforcement
    - Dead letter queue for poison messages
    - Persistent across restarts
    """
    
    def __init__(self, db_path: Optional[Path] = None, max_attempts: int = 3):
        """
        Initialize work queue.
        
        Args:
            db_path: Path to SQLite database (default: ~/.dms/queue/work_queue.db)
            max_attempts: Maximum retry attempts before dead-letter
        """
        if db_path is None:
            db_path = Path.home() / ".dms" / "queue" / "work_queue.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_attempts = max_attempts
        
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS work_items (
                    path TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    metadata TEXT,
                    enqueued_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    last_error TEXT,
                    CHECK (status IN ('queued', 'running', 'completed', 'failed', 'dead_letter'))
                )
            """)
            
            # Index for efficient polling
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status_enqueued 
                ON work_items(status, enqueued_at)
            """)
            
            conn.commit()
    
    def enqueue(
        self,
        path: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Enqueue work item (UPSERT by path).
        
        If item already exists with same path:
        - If completed/failed: reset to queued (new event)
        - If queued/running: update metadata (latest event wins)
        
        Args:
            path: File path (unique key)
            event_type: Event type (e.g., "FILE_ADDED", "FILE_MODIFIED")
            metadata: Additional metadata
        
        Returns:
            True if enqueued, False on error
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # UPSERT logic
                conn.execute("""
                    INSERT INTO work_items (path, event_type, status, attempts, metadata, enqueued_at)
                    VALUES (?, ?, 'queued', 0, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        event_type = excluded.event_type,
                        status = CASE
                            WHEN status IN ('completed', 'failed') THEN 'queued'
                            ELSE status
                        END,
                        attempts = CASE
                            WHEN status IN ('completed', 'failed') THEN 0
                            ELSE attempts
                        END,
                        metadata = excluded.metadata,
                        enqueued_at = excluded.enqueued_at,
                        last_error = NULL
                """, (
                    path,
                    event_type,
                    json.dumps(metadata) if metadata else None,
                    datetime.now(timezone.utc).isoformat()
                ))
                conn.commit()
            
            logger.info(f"Enqueued: {event_type} {path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to enqueue {path}: {e}")
            return False
    
    def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Dequeue next work item (FIFO by enqueued_at).
        
        Atomically marks item as 'running' and increments attempts.
        
        Returns:
            Work item dict or None if queue empty
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Find next queued item
                cursor = conn.execute("""
                    SELECT path, event_type, attempts, metadata
                    FROM work_items
                    WHERE status = 'queued'
                    ORDER BY enqueued_at ASC
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                path = row['path']
                
                # Mark as running
                conn.execute("""
                    UPDATE work_items
                    SET status = 'running',
                        attempts = attempts + 1,
                        started_at = ?
                    WHERE path = ?
                """, (datetime.now(timezone.utc).isoformat(), path))
                
                conn.commit()
                
                item = {
                    'path': path,
                    'event_type': row['event_type'],
                    'attempts': row['attempts'] + 1,
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                }
                
                logger.info(f"Dequeued: {item['event_type']} {path} (attempt {item['attempts']})")
                return item
        
        except Exception as e:
            logger.error(f"Failed to dequeue: {e}")
            return None
    
    def mark_completed(self, path: str):
        """Mark work item as completed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE work_items
                    SET status = 'completed',
                        completed_at = ?
                    WHERE path = ?
                """, (datetime.now(timezone.utc).isoformat(), path))
                conn.commit()
            
            logger.info(f"Completed: {path}")
        
        except Exception as e:
            logger.error(f"Failed to mark completed {path}: {e}")
    
    def mark_failed(self, path: str, error: str):
        """
        Mark work item as failed.
        
        If attempts >= max_attempts, move to dead-letter queue.
        Otherwise, reset to queued for retry.
        
        Args:
            path: File path
            error: Error message
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT attempts FROM work_items WHERE path = ?
                """, (path,))
                
                row = cursor.fetchone()
                if not row:
                    return
                
                attempts = row[0]
                
                if attempts >= self.max_attempts:
                    # Move to dead-letter
                    conn.execute("""
                        UPDATE work_items
                        SET status = 'dead_letter',
                            last_error = ?
                        WHERE path = ?
                    """, (error, path))
                    logger.warning(f"Dead-letter: {path} (exceeded {self.max_attempts} attempts)")
                else:
                    # Retry
                    conn.execute("""
                        UPDATE work_items
                        SET status = 'queued',
                            last_error = ?
                        WHERE path = ?
                    """, (error, path))
                    logger.info(f"Retry queued: {path} (attempt {attempts + 1}/{self.max_attempts})")
                
                conn.commit()
        
        except Exception as e:
            logger.error(f"Failed to mark failed {path}: {e}")
    
    def get_queue_depth(self) -> Dict[str, int]:
        """Get count of items by status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count
                    FROM work_items
                    GROUP BY status
                """)
                
                return {row[0]: row[1] for row in cursor.fetchall()}
        
        except Exception as e:
            logger.error(f"Failed to get queue depth: {e}")
            return {}
    
    def get_dead_letters(self) -> List[Dict[str, Any]]:
        """Get all dead-letter items for investigation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT path, event_type, attempts, last_error, enqueued_at
                    FROM work_items
                    WHERE status = 'dead_letter'
                    ORDER BY enqueued_at DESC
                """)
                
                return [dict(row) for row in cursor.fetchall()]
        
        except Exception as e:
            logger.error(f"Failed to get dead letters: {e}")
            return []
    
    def clear_completed(self, older_than_hours: int = 24):
        """
        Clear completed items older than threshold.
        
        Args:
            older_than_hours: Clear items completed more than N hours ago
        """
        try:
            from datetime import timedelta
            
            cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
            cutoff_iso = cutoff.isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM work_items
                    WHERE status = 'completed'
                    AND completed_at < ?
                """, (cutoff_iso,))
                
                deleted = cursor.rowcount
                conn.commit()
            
            logger.info(f"Cleared {deleted} completed items older than {older_than_hours}h")
        
        except Exception as e:
            logger.error(f"Failed to clear completed: {e}")
    
    def reset_stale_running(self, older_than_minutes: int = 5):
        """
        Reset stale 'running' items back to 'queued'.
        
        Handles cases where worker crashed mid-processing.
        
        Args:
            older_than_minutes: Reset items running longer than N minutes
        """
        try:
            from datetime import timedelta
            
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=older_than_minutes)
            cutoff_iso = cutoff.isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE work_items
                    SET status = 'queued'
                    WHERE status = 'running'
                    AND started_at < ?
                """, (cutoff_iso,))
                
                reset = cursor.rowcount
                conn.commit()
            
            if reset > 0:
                logger.warning(f"Reset {reset} stale running items")
        
        except Exception as e:
            logger.error(f"Failed to reset stale running: {e}")
