# doc_id: DOC-AUTOOPS-004
"""File system watcher with debounce and stability checks."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import Callable, List, Optional, Set

import structlog
from watchfiles import Change, awatch

from repo_autoops.models.events import EventType, FileEvent

__doc_id__ = "DOC-AUTOOPS-004"

logger = structlog.get_logger(__name__)


class FileWatcher:
    """Watch filesystem for changes with stability checking."""

    def __init__(
        self,
        roots: List[Path],
        ignore_patterns: List[str],
        file_patterns: List[str],
        stability_delay: float = 2.0,
    ):
        """Initialize file watcher.

        Args:
            roots: Root directories to watch
            ignore_patterns: Patterns to ignore
            file_patterns: File patterns to watch
            stability_delay: Seconds to wait for file stability
        """
        self.roots = [Path(r) for r in roots]
        self.ignore_patterns = ignore_patterns
        self.file_patterns = file_patterns
        self.stability_delay = stability_delay
        self.callbacks: List[Callable[[FileEvent], None]] = []

    def add_callback(self, callback: Callable[[FileEvent], None]) -> None:
        """Add a callback for file events.

        Args:
            callback: Function to call on file events
        """
        self.callbacks.append(callback)

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored.

        Args:
            path: File path

        Returns:
            True if should ignore
        """
        path_str = str(path)
        for pattern in self.ignore_patterns:
            if pattern in path_str:
                return True
        return False

    def _matches_patterns(self, path: Path) -> bool:
        """Check if path matches watch patterns.

        Args:
            path: File path

        Returns:
            True if matches
        """
        if not self.file_patterns:
            return True

        for pattern in self.file_patterns:
            if path.match(pattern):
                return True
        return False

    async def _get_content_hash(self, path: Path) -> Optional[str]:
        """Get content hash of file.

        Args:
            path: File path

        Returns:
            MD5 hash or None if error
        """
        try:
            content = await asyncio.to_thread(path.read_bytes)
            return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.warning("hash_failed", path=str(path), error=str(e))
            return None

    async def _wait_for_stability(self, path: Path) -> bool:
        """Wait for file to become stable.

        Args:
            path: File path

        Returns:
            True if file is stable
        """
        if not path.exists():
            return False

        try:
            hash1 = await self._get_content_hash(path)
            await asyncio.sleep(self.stability_delay)
            
            if not path.exists():
                return False
                
            hash2 = await self._get_content_hash(path)
            
            stable = hash1 == hash2
            logger.debug(
                "stability_check",
                path=str(path),
                stable=stable,
                hash_match=hash1 == hash2,
            )
            return stable
        except Exception as e:
            logger.error("stability_check_failed", path=str(path), error=str(e))
            return False

    def _change_to_event_type(self, change: Change) -> EventType:
        """Convert watchfiles Change to EventType.

        Args:
            change: Watchfiles change type

        Returns:
            EventType
        """
        mapping = {
            Change.added: EventType.CREATED,
            Change.modified: EventType.MODIFIED,
            Change.deleted: EventType.DELETED,
        }
        return mapping.get(change, EventType.MODIFIED)

    async def watch(self) -> None:
        """Start watching filesystem."""
        logger.info("watcher_started", roots=[str(r) for r in self.roots])

        watch_paths = [str(r) for r in self.roots]

        async for changes in awatch(*watch_paths):
            for change_type, path_str in changes:
                path = Path(path_str)

                if self._should_ignore(path):
                    logger.debug("ignored", path=str(path))
                    continue

                if not self._matches_patterns(path):
                    logger.debug("pattern_mismatch", path=str(path))
                    continue

                event_type = self._change_to_event_type(change_type)

                # For created/modified, wait for stability
                stable = True
                content_hash = None
                
                if event_type in (EventType.CREATED, EventType.MODIFIED):
                    stable = await self._wait_for_stability(path)
                    if stable:
                        content_hash = await self._get_content_hash(path)

                event = FileEvent(
                    event_type=event_type,
                    file_path=path,
                    stable=stable,
                    content_hash=content_hash,
                )

                logger.info(
                    "file_event",
                    event_type=event_type.value,
                    path=str(path),
                    stable=stable,
                )

                for callback in self.callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(
                            "callback_failed",
                            callback=callback.__name__,
                            error=str(e),
                        )
