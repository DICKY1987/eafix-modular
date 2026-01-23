#!/usr/bin/env python3
"""
doc_id: 2026012322470011
Watcher Daemon - Filesystem Monitoring Service
"""

import time
import logging
from pathlib import Path
from typing import List, Optional

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object

from repo_autoops.automation_descriptor.work_queue import WorkQueue
from repo_autoops.automation_descriptor.suppression_manager import SuppressionManager

logger = logging.getLogger(__name__)


class RegistryEventHandler(FileSystemEventHandler):
    """Handles filesystem events."""
    
    def __init__(self, queue: WorkQueue, suppressor: SuppressionManager):
        self.queue = queue
        self.suppressor = suppressor
    
    def on_created(self, event: 'FileSystemEvent'):
        if not event.is_directory and not self.suppressor.should_suppress(event.src_path):
            self.queue.enqueue(event.src_path, "FILE_CREATED")
    
    def on_modified(self, event: 'FileSystemEvent'):
        if not event.is_directory and not self.suppressor.should_suppress(event.src_path):
            self.queue.enqueue(event.src_path, "FILE_MODIFIED")


class WatcherDaemon:
    """Filesystem watcher daemon."""
    
    def __init__(
        self,
        watch_paths: List[str],
        queue: Optional[WorkQueue] = None,
        suppressor: Optional[SuppressionManager] = None
    ):
        if not WATCHDOG_AVAILABLE:
            raise ImportError("watchdog library required")
        
        self.watch_paths = [Path(p) for p in watch_paths]
        self.queue = queue or WorkQueue()
        self.suppressor = suppressor or SuppressionManager()
        self.observer = Observer()
        self.handler = RegistryEventHandler(self.queue, self.suppressor)
        self.running = False
    
    def start(self):
        """Start watching."""
        for path in self.watch_paths:
            if path.exists():
                self.observer.schedule(self.handler, str(path), recursive=True)
        self.observer.start()
        self.running = True
        logger.info("Watcher started")
    
    def stop(self):
        """Stop watching."""
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
