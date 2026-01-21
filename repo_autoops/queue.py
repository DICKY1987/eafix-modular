# doc_id: DOC-AUTOOPS-005
"""SQLite-backed event queue for persistent work item management."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import List

import structlog

from repo_autoops.models.events import WorkItem, WorkItemStatus

__doc_id__ = "DOC-AUTOOPS-005"

logger = structlog.get_logger(__name__)


class EventQueue:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS work_items (
                    work_item_id TEXT PRIMARY KEY,
                    path TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    first_seen INTEGER NOT NULL,
                    last_seen INTEGER NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    error TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON work_items(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_path ON work_items(path)")
            conn.commit()
            logger.info("event_queue_initialized", db_path=str(self.db_path))

    def enqueue(self, path: Path, event_type: str) -> str:
        path_str = str(path)
        work_item_id = f"work_{int(time.time() * 1000)}_{hash(path_str) % 10000}"
        now = int(time.time())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT work_item_id, last_seen FROM work_items WHERE path = ? AND status = 'pending'",
                (path_str,),
            )
            existing = cursor.fetchone()

            if existing:
                conn.execute(
                    "UPDATE work_items SET last_seen = ?, event_type = ? WHERE work_item_id = ?",
                    (now, event_type, existing[0]),
                )
                conn.commit()
                logger.debug("work_item_updated", work_item_id=existing[0], path=path_str)
                return existing[0]

            conn.execute(
                """INSERT INTO work_items (work_item_id, path, event_type, first_seen, last_seen, attempts, status)
                VALUES (?, ?, ?, ?, ?, 0, 'pending')""",
                (work_item_id, path_str, event_type, now, now),
            )
            conn.commit()
            logger.info("work_item_enqueued", work_item_id=work_item_id, path=path_str)

        return work_item_id

    def dequeue_batch(self, limit: int = 10) -> List[WorkItem]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM work_items WHERE status = 'pending' ORDER BY first_seen ASC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()

            work_items = []
            for row in rows:
                work_item = WorkItem(
                    work_item_id=row["work_item_id"],
                    path=row["path"],
                    event_type=row["event_type"],
                    first_seen=row["first_seen"],
                    last_seen=row["last_seen"],
                    attempts=row["attempts"],
                    status=WorkItemStatus(row["status"]),
                    error=row["error"],
                )
                work_items.append(work_item)
                conn.execute(
                    "UPDATE work_items SET status = 'processing', attempts = attempts + 1 WHERE work_item_id = ?",
                    (work_item.work_item_id,),
                )

            conn.commit()
            logger.info("work_items_dequeued", count=len(work_items))

        return work_items

    def mark_done(self, work_item_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE work_items SET status = 'done' WHERE work_item_id = ?", (work_item_id,))
            conn.commit()
            logger.info("work_item_done", work_item_id=work_item_id)

    def mark_failed(self, work_item_id: str, error: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE work_items SET status = 'failed', error = ? WHERE work_item_id = ?",
                (error, work_item_id),
            )
            conn.commit()
            logger.error("work_item_failed", work_item_id=work_item_id, error=error)

    def get_pending_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM work_items WHERE status = 'pending'")
            count = cursor.fetchone()[0]
        return count
