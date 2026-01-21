# doc_id: DOC-SERVICE-0187
# DOC_ID: DOC-SERVICE-0099
"""
File Watcher

Monitors directories for CSV file changes and generates file events
for the transport router to process.
"""

import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, AsyncIterator
import os

import structlog
import watchfiles

logger = structlog.get_logger(__name__)


class FileWatcher:
    """Watches directories for CSV file changes."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        self.watched_paths = self.settings.get_watched_paths()
        self.running = False
        
        # Event filtering
        self.ignore_patterns = ['.tmp', '.temp', '.swp', '~']
        
        # Processing delay to handle file write completion
        self.processing_delay = self.settings.file_processing_delay_seconds
    
    async def start(self) -> None:
        """Start the file watcher."""
        if not self.settings.file_watching_enabled:
            logger.info("File watching disabled")
            return
        
        # Ensure watched directories exist
        for path in self.watched_paths:
            if not path.exists():
                logger.warning("Watched directory does not exist", path=str(path))
                continue
                
            if not path.is_dir():
                logger.warning("Watched path is not a directory", path=str(path))
                continue
        
        self.running = True
        logger.info(
            "File watcher started",
            watched_directories=[str(p) for p in self.watched_paths],
            recursive=self.settings.watch_recursive,
            patterns=self.settings.watch_file_patterns
        )
    
    async def stop(self) -> None:
        """Stop the file watcher."""
        self.running = False
        logger.info("File watcher stopped")
    
    async def watch_directories(self) -> AsyncIterator[Dict[str, Any]]:
        """Watch directories and yield file events."""
        if not self.running:
            return
        
        try:
            # Convert paths to strings for watchfiles
            watch_paths = [str(p) for p in self.watched_paths if p.exists()]
            
            if not watch_paths:
                logger.warning("No valid directories to watch")
                return
            
            logger.info("Starting directory watching", paths=watch_paths)
            
            async for changes in watchfiles.awatch(
                *watch_paths,
                recursive=self.settings.watch_recursive,
                ignore_paths=None  # We'll filter manually
            ):
                for change in changes:
                    event_type_int, file_path_str = change
                    file_path = Path(file_path_str)
                    
                    # Convert numeric event type to string
                    event_type_map = {
                        1: "created",
                        2: "modified", 
                        3: "deleted"
                    }
                    event_type = event_type_map.get(event_type_int, "unknown")
                    
                    # Filter events
                    if not await self._should_process_event(file_path, event_type):
                        continue
                    
                    # Add processing delay
                    if self.processing_delay > 0:
                        await asyncio.sleep(self.processing_delay)
                    
                    # Generate file event
                    file_event = {
                        "event_type": event_type,
                        "path": str(file_path),
                        "timestamp": datetime.utcnow().isoformat(),
                        "file_size": file_path.stat().st_size if file_path.exists() else 0,
                        "file_modified": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat() if file_path.exists() else None
                    }
                    
                    self.metrics.increment_counter("file_events_generated")
                    
                    logger.debug(
                        "File event generated",
                        event_type=event_type,
                        path=str(file_path)
                    )
                    
                    yield file_event
                    
        except Exception as e:
            logger.error("Directory watching failed", error=str(e))
            self.metrics.record_error("watcher_error")
            raise
    
    async def _should_process_event(self, file_path: Path, event_type: str) -> bool:
        """Determine if a file event should be processed."""
        try:
            # Skip non-CSV files
            if file_path.suffix.lower() != '.csv':
                return False
            
            # Skip ignored patterns
            filename = file_path.name.lower()
            for pattern in self.ignore_patterns:
                if pattern in filename:
                    return False
            
            # Skip temporary files if configured
            if self.settings.ignore_temp_files:
                temp_patterns = ['.tmp', '.temp', '~']
                if any(pattern in filename for pattern in temp_patterns):
                    return False
            
            # Only process certain event types
            if event_type not in ['created', 'modified']:
                return False
            
            # Check file size limits
            if file_path.exists():
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                if file_size_mb > self.settings.max_file_size_mb:
                    logger.warning(
                        "File too large, skipping",
                        path=str(file_path),
                        size_mb=file_size_mb,
                        limit_mb=self.settings.max_file_size_mb
                    )
                    return False
            
            # Check if file path matches our watch patterns
            filename = file_path.name
            patterns = self.settings.watch_file_patterns
            
            if patterns:
                import fnmatch
                matches_pattern = any(
                    fnmatch.fnmatch(filename, pattern) 
                    for pattern in patterns
                )
                if not matches_pattern:
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(
                "Error checking file event",
                path=str(file_path),
                event_type=event_type,
                error=str(e)
            )
            return False
    
    async def scan_existing_files(self) -> List[Dict[str, Any]]:
        """Scan for existing CSV files in watched directories."""
        existing_files = []
        
        try:
            for watch_path in self.watched_paths:
                if not watch_path.exists():
                    continue
                
                # Find CSV files
                if self.settings.watch_recursive:
                    csv_files = watch_path.rglob("*.csv")
                else:
                    csv_files = watch_path.glob("*.csv")
                
                for csv_file in csv_files:
                    if await self._should_process_event(csv_file, "existing"):
                        file_info = {
                            "path": str(csv_file),
                            "size_bytes": csv_file.stat().st_size,
                            "modified_time": datetime.fromtimestamp(
                                csv_file.stat().st_mtime
                            ).isoformat(),
                            "directory": str(watch_path)
                        }
                        existing_files.append(file_info)
            
            logger.info(
                "Scanned existing files",
                file_count=len(existing_files),
                directories=[str(p) for p in self.watched_paths]
            )
            
            return existing_files
            
        except Exception as e:
            logger.error("Failed to scan existing files", error=str(e))
            return []
    
    async def get_watched_directories(self) -> List[Dict[str, Any]]:
        """Get information about watched directories."""
        directory_info = []
        
        for path in self.watched_paths:
            info = {
                "path": str(path),
                "exists": path.exists(),
                "is_directory": path.is_dir() if path.exists() else False,
                "readable": os.access(path, os.R_OK) if path.exists() else False
            }
            
            if path.exists() and path.is_dir():
                try:
                    # Count CSV files
                    if self.settings.watch_recursive:
                        csv_files = list(path.rglob("*.csv"))
                    else:
                        csv_files = list(path.glob("*.csv"))
                    
                    info["csv_file_count"] = len(csv_files)
                    info["total_size_mb"] = sum(
                        f.stat().st_size for f in csv_files
                    ) / (1024 * 1024)
                    
                except Exception as e:
                    info["error"] = str(e)
            
            directory_info.append(info)
        
        return directory_info
    
    async def get_status(self) -> Dict[str, Any]:
        """Get file watcher status."""
        watched_dirs = await self.get_watched_directories()
        existing_dirs = sum(1 for d in watched_dirs if d["exists"])
        readable_dirs = sum(1 for d in watched_dirs if d.get("readable", False))
        
        return {
            "running": self.running,
            "enabled": self.settings.file_watching_enabled,
            "watched_directories": len(self.watched_paths),
            "existing_directories": existing_dirs,
            "readable_directories": readable_dirs,
            "recursive_watching": self.settings.watch_recursive,
            "file_patterns": self.settings.watch_file_patterns,
            "processing_delay_seconds": self.processing_delay,
            "ignore_patterns": self.ignore_patterns
        }