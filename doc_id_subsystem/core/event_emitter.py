#!/usr/bin/env python3
"""
Async Event Emitter - Non-blocking event emission with trace context injection.

Provides queue-based async event emission that works in both synchronous
and asynchronous code. Events are processed by a background worker task
and routed to multiple sinks in parallel.

Alignment:
- Leverages trace_context.py for automatic trace_id/run_id injection
- Compatible with PHASE_7 pattern_events.jsonl format
- Zero-impact on critical path (non-blocking emit)
"""
# DOC_ID: DOC-CORE-SSOT-SYS-TOOLS-EVENT-EMITTER-1109

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from enum import Enum
import threading

try:
    from .trace_context import get_or_create_trace_id, get_or_create_run_id
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from trace_context import get_or_create_trace_id, get_or_create_run_id


class EventSeverity(str, Enum):
    """Event severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def generate_ulid() -> str:
    """
    Generate ULID-style sortable event ID.

    Format: EVT-{timestamp_ms}-{random}
    Sortable by timestamp, unique via random component.

    Returns:
        str: Event ID in format EVT-{ms}-{rand}
    """
    import uuid
    timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    random_part = str(uuid.uuid4())[:8].upper()
    return f"EVT-{timestamp_ms}-{random_part}"


class AsyncEventEmitter:
    """
    Queue-based async event emitter with trace context injection.

    Features:
    - Non-blocking emit() method (just queue insertion)
    - Background worker task processes queue asynchronously
    - Auto-inject trace_id and run_id on every event
    - Graceful shutdown with queue flush
    - Works in both sync and async code

    Usage:
        emitter = AsyncEventEmitter(router)
        await emitter.start()

        # Non-blocking emit (works in sync code)
        emitter.emit(
            subsystem="SUB_DOC_ID",
            step_id="FILE_DETECTED",
            subject="test.py",
            summary="File detected",
            severity="INFO"
        )

        await emitter.stop()
    """

    def __init__(
        self,
        router: 'EventRouter',
        queue_size: int = 10000,
        worker_timeout: float = 0.1
    ):
        """
        Initialize async event emitter.

        Args:
            router: EventRouter instance for dispatching events
            queue_size: Maximum queue size (default 10,000)
            worker_timeout: Worker poll timeout in seconds (default 0.1s)
        """
        self.router = router
        self.queue_size = queue_size
        self.worker_timeout = worker_timeout

        self.queue: Optional[asyncio.Queue] = None
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        self.logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """
        Start background event worker.

        Creates event queue and starts async worker task.
        Must be called before emit().
        """
        if self.running:
            self.logger.warning("Event emitter already started")
            return

        # Get or create event loop
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        # Create queue
        self.queue = asyncio.Queue(maxsize=self.queue_size)

        # Start worker task
        self.running = True
        self.worker_task = asyncio.create_task(self._event_worker())

        self.logger.info(
            f"Event emitter started (queue_size={self.queue_size}, "
            f"worker_timeout={self.worker_timeout}s)"
        )

    async def stop(self) -> None:
        """
        Stop background worker and flush queue.

        Gracefully shuts down:
        1. Signals worker to stop accepting new events
        2. Waits for queue to drain
        3. Cancels worker task
        """
        if not self.running:
            return

        self.running = False

        # Wait for queue to drain (max 5 seconds)
        if self.queue:
            try:
                await asyncio.wait_for(self.queue.join(), timeout=5.0)
                self.logger.info("Event queue drained successfully")
            except asyncio.TimeoutError:
                pending = self.queue.qsize()
                self.logger.warning(
                    f"Queue drain timeout - {pending} events lost"
                )

        # Cancel worker task
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Event emitter stopped")

    def emit(
        self,
        subsystem: str,
        step_id: str,
        subject: str,
        summary: str,
        severity: str = "INFO",
        automation_chain_id: Optional[str] = None,
        sequence_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Emit event (non-blocking - just queue insertion).

        Works in both synchronous and asynchronous code.
        Event is queued and processed by background worker.

        Args:
            subsystem: Source subsystem (e.g., "SUB_DOC_ID")
            step_id: Process step identifier
            subject: Event subject (file path, operation, etc.)
            summary: Human-readable event summary
            severity: Event severity (DEBUG|INFO|NOTICE|WARN|ERROR|CRITICAL)
            automation_chain_id: Optional automation chain ID
            sequence_id: Optional sequence ID
            correlation_id: Optional correlation ID for grouping
            details: Optional additional structured data

        Raises:
            RuntimeError: If emitter not started
            asyncio.QueueFull: If queue is full (should be rare with 10k size)
        """
        if not self.running or not self.queue:
            raise RuntimeError(
                "Event emitter not started - call await emitter.start() first"
            )

        # Build event dict (trace context injected by worker)
        event = {
            "subsystem": subsystem,
            "step_id": step_id,
            "subject": subject,
            "summary": summary,
            "severity": severity,
        }

        # Add optional fields
        if automation_chain_id:
            event["automation_chain_id"] = automation_chain_id
        if sequence_id:
            event["sequence_id"] = sequence_id
        if correlation_id:
            event["correlation_id"] = correlation_id
        if details:
            event["details"] = details

        # Non-blocking queue insertion
        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            self.logger.error(
                f"Event queue full ({self.queue_size}) - event dropped: {summary}"
            )
            raise

    async def _event_worker(self) -> None:
        """
        Background worker that processes event queue.

        Continuously:
        1. Gets events from queue
        2. Injects trace context (trace_id, run_id, event_id, timestamp)
        3. Routes to sinks via router
        4. Handles failures gracefully
        """
        self.logger.info("Event worker started")

        while self.running or (self.queue and not self.queue.empty()):
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=self.worker_timeout
                )

                # Inject trace context
                event["trace_id"] = get_or_create_trace_id()
                event["run_id"] = get_or_create_run_id()
                event["event_id"] = generate_ulid()
                event["timestamp_utc"] = datetime.now(timezone.utc).isoformat() + "Z"

                # Route to sinks (parallel dispatch)
                try:
                    await self.router.route(event)
                except Exception as e:
                    self.logger.error(f"Router failed for event {event['event_id']}: {e}")

                # Mark task done
                self.queue.task_done()

            except asyncio.TimeoutError:
                # No events in queue, continue
                continue

            except asyncio.CancelledError:
                # Worker cancelled during shutdown
                self.logger.info("Event worker cancelled")
                break

            except Exception as e:
                # Unexpected error - log and continue
                self.logger.error(f"Event worker error: {e}", exc_info=True)

        self.logger.info("Event worker stopped")


# Global emitter instance (set by application)
_global_emitter: Optional[AsyncEventEmitter] = None
_global_emitter_lock = threading.Lock()


def set_global_emitter(emitter: AsyncEventEmitter) -> None:
    """
    Set global event emitter instance.

    Allows synchronous code to access emitter without passing it around.
    Should be called once during application startup.

    Args:
        emitter: AsyncEventEmitter instance
    """
    global _global_emitter
    with _global_emitter_lock:
        _global_emitter = emitter


def get_event_emitter() -> AsyncEventEmitter:
    """
    Get global event emitter instance.

    Returns:
        AsyncEventEmitter: Global emitter instance

    Raises:
        RuntimeError: If global emitter not set
    """
    if _global_emitter is None:
        raise RuntimeError(
            "Global event emitter not set - call set_global_emitter() first"
        )
    return _global_emitter


if __name__ == "__main__":
    # Demo usage
    import sys

    # Mock router for demo
    class MockRouter:
        async def route(self, event):
            print(f"[ROUTED] {event['severity']} | {event['summary']}")

    async def demo():
        print("AsyncEventEmitter Demo")
        print("=" * 60)

        # Create emitter
        router = MockRouter()
        emitter = AsyncEventEmitter(router, queue_size=100)

        # Start background worker
        await emitter.start()
        set_global_emitter(emitter)

        # Emit some events
        print("\nEmitting events...")
        for i in range(5):
            emitter.emit(
                subsystem="DEMO",
                step_id=f"STEP_{i}",
                subject=f"demo_operation_{i}",
                summary=f"Demo event {i}",
                severity="INFO",
                details={"index": i}
            )

        # Give worker time to process
        await asyncio.sleep(0.5)

        # Graceful shutdown
        print("\nShutting down...")
        await emitter.stop()

        print("\n✓ Demo complete")

    # Run demo
    asyncio.run(demo())
