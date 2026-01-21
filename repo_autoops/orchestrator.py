# doc_id: DOC-AUTOOPS-012
"""Main orchestrator for RepoAutoOps."""

from __future__ import annotations

import asyncio
from pathlib import Path

import structlog

from repo_autoops.config import Config
from repo_autoops.queue import EventQueue

__doc_id__ = "DOC-AUTOOPS-012"

logger = structlog.get_logger(__name__)


class Orchestrator:
    """Main orchestrator coordinating all components."""

    def __init__(self, config: Config, dry_run: bool = True):
        self.config = config
        self.dry_run = dry_run
        self.queue = EventQueue(config.repository_root / ".repo_autoops_queue.db")
        self.running = False

    async def start(self) -> None:
        """Start the orchestrator."""
        self.running = True
        logger.info("orchestrator_started", dry_run=self.dry_run)

        while self.running:
            try:
                await self._process_cycle()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error("orchestrator_cycle_failed", error=str(e))
                await asyncio.sleep(10)

    async def _process_cycle(self) -> None:
        """Process one cycle of work items."""
        work_items = self.queue.dequeue_batch(limit=10)

        if not work_items:
            return

        logger.info("processing_work_items", count=len(work_items))

        for item in work_items:
            try:
                if self.dry_run:
                    logger.info("dry_run_would_process", path=item.path, event_type=item.event_type)
                else:
                    # Actual processing would go here
                    logger.info("processing_item", path=item.path)

                self.queue.mark_done(item.work_item_id)

            except Exception as e:
                logger.error("item_processing_failed", work_item_id=item.work_item_id, error=str(e))
                self.queue.mark_failed(item.work_item_id, str(e))

    def stop(self) -> None:
        """Stop the orchestrator."""
        self.running = False
        logger.info("orchestrator_stopped")
