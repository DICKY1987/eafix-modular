# doc_id: DOC-AUTOOPS-012
"""Main orchestrator coordinating all components."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import structlog

from repo_autoops.config import Config
from repo_autoops.git_adapter import GitAdapter
from repo_autoops.identity_pipeline import IdentityPipeline
from repo_autoops.loop_prevention import LoopPrevention
from repo_autoops.models.events import FileEvent
from repo_autoops.policy_gate import PolicyGate
from repo_autoops.queue import EventQueue
from repo_autoops.validators import DocIdValidator, SecretScanner, ValidationRunner
from repo_autoops.watcher import FileWatcher

__doc_id__ = "DOC-AUTOOPS-012"

logger = structlog.get_logger(__name__)


class Orchestrator:
    """Coordinate file watching, identity, policy, git operations."""

    def __init__(self, config: Config):
        """Initialize orchestrator.

        Args:
            config: Configuration
        """
        self.config = config
        self.queue = EventQueue(config.repository_root / ".repo_autoops_queue.db")
        self.running = False
        
        # Initialize components
        contracts = config.load_contracts()
        self.policy_gate = PolicyGate(contracts)
        self.git_adapter = GitAdapter(config.repository_root, dry_run=config.safety.dry_run_default)
        self.identity_pipeline = IdentityPipeline(
            mode=config.identity.numeric_prefix_mode,
            dry_run=config.safety.dry_run_default,
        )
        self.loop_prevention = LoopPrevention(suppression_window_seconds=5.0)
        
        # Initialize validators
        validators = [
            DocIdValidator(required=False),
            SecretScanner(),
        ]
        self.validation_runner = ValidationRunner(validators)
        
        # Initialize watcher
        self.watcher: Optional[FileWatcher] = None
        if config.watch.enabled:
            self.watcher = FileWatcher(
                roots=config.watch.roots,
                ignore_patterns=config.watch.ignore_patterns,
                file_patterns=config.watch.file_patterns,
                stability_delay=config.watch.processing_delay_seconds,
            )
            self.watcher.add_callback(self._on_file_event)
        
        logger.info("orchestrator_initialized", contracts=len(contracts))

    def _on_file_event(self, event: FileEvent) -> None:
        """Handle file event from watcher.

        Args:
            event: File event
        """
        # Check if self-induced
        if self.loop_prevention.is_self_induced(event.file_path):
            logger.debug("event_suppressed_self_induced", path=str(event.file_path))
            return

        # Enqueue for processing
        self.queue.enqueue(event.file_path, event.event_type.value)
        logger.info("event_enqueued", path=str(event.file_path), type=event.event_type.value)

    async def process_work_item(self, path: Path) -> bool:
        """Process a single work item.

        Args:
            path: File path

        Returns:
            True if successful
        """
        logger.info("processing_file", path=str(path))

        # Mark operation start for loop prevention
        operation_id = self.loop_prevention.start_operation(path, "process")

        try:
            # Step 1: Classify file
            classification = self.policy_gate.classify_file(path)
            logger.info("file_classified", path=str(path), classification=classification.classification)

            if classification.classification == "quarantine":
                logger.warning("file_quarantined", path=str(path), reason=classification.reason)
                return False

            if classification.classification != "canonical":
                logger.info("skipping_non_canonical", path=str(path), classification=classification.classification)
                return True

            # Step 2: Run validations
            validation_results = self.validation_runner.validate_file(path)
            if not self.validation_runner.all_passed(validation_results):
                logger.warning("validation_failed", path=str(path))
                for result in validation_results:
                    if not result.passed:
                        logger.warning("validator_failed", validator=result.validator_name, message=result.message)
                return False

            # Step 3: Assign identity if enabled
            if self.config.identity.numeric_prefix_enabled:
                identity_result = self.identity_pipeline.process_file(path)
                if not identity_result.success:
                    logger.error("identity_failed", path=str(path), error=identity_result.error)
                    return False

            # Step 4: Stage file
            stage_result = self.git_adapter.stage_files([path])
            if not stage_result.success:
                logger.error("stage_failed", path=str(path), error=stage_result.error)
                return False

            logger.info("file_processed_successfully", path=str(path))
            return True

        finally:
            # Mark operation end
            self.loop_prevention.end_operation(operation_id)

    async def process_queue(self) -> None:
        """Process pending work items from queue."""
        while self.running:
            pending = self.queue.get_pending_count()
            if pending > 0:
                logger.info("processing_queue", pending_count=pending)

                work_items = self.queue.dequeue_batch(limit=10)

                for item in work_items:
                    path = Path(item.path)
                    success = await self.process_work_item(path)

                    if success:
                        self.queue.mark_done(item.work_item_id)
                    else:
                        self.queue.mark_failed(item.work_item_id, "Processing failed")

            await asyncio.sleep(self.config.watch.processing_delay_seconds)

    async def run(self) -> None:
        """Start the orchestrator."""
        logger.info("orchestrator_starting")
        self.running = True

        tasks = []

        # Start queue processor
        tasks.append(asyncio.create_task(self.process_queue()))

        # Start watcher if enabled
        if self.watcher:
            tasks.append(asyncio.create_task(self.watcher.watch()))

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("orchestrator_interrupted")
        finally:
            self.running = False
            logger.info("orchestrator_stopped")

    def stop(self) -> None:
        """Stop the orchestrator."""
        self.running = False
