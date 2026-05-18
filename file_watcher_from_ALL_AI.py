#!/usr/bin/env python3
# doc_id: DOC-CORE-AUTOMATION-FILE-WATCHER-393
"""
File Watcher with Automatic 16-Digit Numeric Prefix Assignment

Implements fs-event → classify → allocate ID → rename pattern.
Follows 5-Layer Governance Model and deterministic behavior requirements.

Features:
- Debounced file creation/modification detection
- Atomic rename with collision handling
- Locked counter registry for concurrency safety
- Coexists with doc_id system (runs first, then doc_id)
- Configurable ignore patterns and safe mode
"""

import json
import time
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Set, Optional, List, Callable
import hashlib
import os
import sys

# Platform-specific imports for file locking
if sys.platform == 'win32':
    import msvcrt
    PLATFORM_LOCKING = 'windows'
else:
    import fcntl
    PLATFORM_LOCKING = 'unix'


@dataclass
class FileWatcherConfig:
    """Configuration for file watcher."""
    watch_root: Path
    registry_path: Path
    debounce_seconds: float = 2.0
    stability_checks: int = 3
    stability_interval_ms: int = 500
    ignore_patterns: List[str] = None
    auto_rename: bool = False  # Safe default: draft mode
    allowed_extensions: Set[str] = None
    
    def __post_init__(self):
        if self.ignore_patterns is None:
            self.ignore_patterns = [
                ".git/", "node_modules/", "__pycache__/", ".venv/", "venv/",
                ".pytest_cache/", ".coverage", "htmlcov/", ".tox/",
                "*.pyc", "*.pyo", "*.swp", "*.tmp", ".DS_Store"
            ]
        if self.allowed_extensions is None:
            self.allowed_extensions = {
                '.py', '.md', '.yaml', '.yml', '.json', '.txt', '.sh', '.ps1',
                '.js', '.ts', '.jsx', '.tsx', '.rs', '.go', '.java', '.sql'
            }


@dataclass
class NumericPrefixRegistry:
    """Registry for tracking 16-digit numeric prefixes by file type."""
    version: str = "1.0"
    counters: Dict[str, int] = None
    
    def __post_init__(self):
        if self.counters is None:
            self.counters = {}
    
    def get_next(self, extension: str) -> str:
        """Get next 16-digit prefix for extension, increment counter."""
        ext = extension.lstrip('.').lower() or 'other'
        current = self.counters.get(ext, 0)
        next_id = current + 1
        self.counters[ext] = next_id
        return f"{next_id:016d}"
    
    def to_dict(self) -> dict:
        return {"version": self.version, "counters": self.counters}
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            version=data.get("version", "1.0"),
            counters=data.get("counters", {})
        )


class RegistryLock:
    """Cross-platform file-based lock for concurrent access to registry."""
    
    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self.lock_file = None
    
    def __enter__(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_file = open(self.lock_path, 'w')
        
        if PLATFORM_LOCKING == 'windows':
            # Windows: use msvcrt for file locking
            msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_LOCK, 1)
        else:
            # Unix: use fcntl for file locking
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file:
            if PLATFORM_LOCKING == 'windows':
                try:
                    msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                except:
                    pass  # Already unlocked or error
            else:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            
            self.lock_file.close()
        return False


class NumericPrefixAssigner:
    """Handles allocation and application of 16-digit numeric prefixes."""
    
    def __init__(self, config: FileWatcherConfig):
        self.config = config
        self.registry_path = config.registry_path
        self.lock_path = config.registry_path.parent / ".numeric_prefix.lock"
    
    def load_registry(self) -> NumericPrefixRegistry:
        """Load registry from disk."""
        if not self.registry_path.exists():
            return NumericPrefixRegistry()
        
        with open(self.registry_path) as f:
            data = json.load(f)
        return NumericPrefixRegistry.from_dict(data)
    
    def save_registry(self, registry: NumericPrefixRegistry):
        """Save registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(registry.to_dict(), f, indent=2)
    
    def has_numeric_prefix(self, filename: str) -> bool:
        """Check if filename already has 16-digit prefix."""
        return len(filename) >= 17 and filename[:16].isdigit() and filename[16] == '_'
    
    def allocate_prefix(self, file_path: Path) -> Optional[str]:
        """
        Allocate next numeric prefix for file.
        
        Uses locked registry access for concurrency safety.
        Returns 16-digit prefix string or None if error.
        """
        extension = file_path.suffix.lower()
        
        try:
            with RegistryLock(self.lock_path):
                registry = self.load_registry()
                prefix = registry.get_next(extension)
                self.save_registry(registry)
                return prefix
        except Exception as e:
            print(f"Error allocating prefix: {e}")
            return None
    
    def compute_target_path(self, file_path: Path, prefix: str) -> Path:
        """Compute target path with numeric prefix."""
        new_name = f"{prefix}_{file_path.name}"
        return file_path.parent / new_name
    
    def rename_with_prefix(self, file_path: Path, prefix: str, max_retries: int = 5) -> Optional[Path]:
        """
        Atomically rename file with numeric prefix.
        
        Handles collisions by retrying with next prefix.
        Returns final path or None if failed.
        """
        for attempt in range(max_retries):
            target_path = self.compute_target_path(file_path, prefix)
            
            if target_path.exists():
                # Collision - allocate new prefix
                print(f"Collision detected: {target_path.name} exists, retrying...")
                prefix = self.allocate_prefix(file_path)
                if not prefix:
                    return None
                continue
            
            try:
                # Atomic rename on same filesystem
                file_path.rename(target_path)
                return target_path
            except OSError as e:
                print(f"Rename failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.1)
                continue
        
        return None


class FileStabilityChecker:
    """Checks if file has finished being written (stable size/mtime)."""
    
    def __init__(self, stability_checks: int = 3, interval_ms: int = 500):
        self.stability_checks = stability_checks
        self.interval_seconds = interval_ms / 1000.0
    
    def is_stable(self, file_path: Path) -> bool:
        """
        Check if file is stable (not being written).
        
        Returns True if size and mtime are unchanged for N checks.
        """
        if not file_path.exists():
            return False
        
        try:
            last_stat = file_path.stat()
            last_size = last_stat.st_size
            last_mtime = last_stat.st_mtime
            
            for _ in range(self.stability_checks):
                time.sleep(self.interval_seconds)
                
                if not file_path.exists():
                    return False
                
                current_stat = file_path.stat()
                current_size = current_stat.st_size
                current_mtime = current_stat.st_mtime
                
                if current_size != last_size or current_mtime != last_mtime:
                    return False
                
                last_size = current_size
                last_mtime = current_mtime
            
            return True
        except OSError:
            return False


class FileWatcher:
    """
    File system watcher with automatic 16-digit numeric prefix assignment.
    
    Monitors directory for new/modified files and assigns numeric prefixes.
    Designed to run before doc_id assignment in the identity pipeline.
    """
    
    def __init__(self, config: FileWatcherConfig):
        self.config = config
        self.assigner = NumericPrefixAssigner(config)
        self.stability_checker = FileStabilityChecker(
            config.stability_checks,
            config.stability_interval_ms
        )
        self.pending_files: Dict[Path, float] = {}
        self.processed_files: Set[str] = set()
        self.lock = threading.Lock()
        self.running = False
    
    def should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored based on patterns."""
        path_str = str(file_path.relative_to(self.config.watch_root))
        
        for pattern in self.config.ignore_patterns:
            if pattern.endswith('/'):
                # Directory pattern
                if pattern[:-1] in path_str.split(os.sep):
                    return True
            elif pattern.startswith('*.'):
                # Extension pattern
                if file_path.suffix == pattern[1:]:
                    return True
            elif pattern in path_str:
                # Substring pattern
                return True
        
        return False
    
    def should_process(self, file_path: Path) -> bool:
        """Check if file should be processed for prefix assignment."""
        # Must be a file
        if not file_path.is_file():
            return False
        
        # Must not be ignored
        if self.should_ignore(file_path):
            return False
        
        # Must have allowed extension (if configured)
        if self.config.allowed_extensions:
            if file_path.suffix.lower() not in self.config.allowed_extensions:
                return False
        
        # Must not already have numeric prefix
        if self.assigner.has_numeric_prefix(file_path.name):
            return False
        
        # Must not have been processed already (by hash)
        file_hash = self._compute_file_hash(file_path)
        if file_hash in self.processed_files:
            return False
        
        return True
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute stable hash of file for deduplication."""
        try:
            stat = file_path.stat()
            content = f"{file_path.absolute()}:{stat.st_size}:{stat.st_mtime_ns}"
            return hashlib.sha256(content.encode()).hexdigest()[:16]
        except OSError:
            return ""
    
    def on_file_event(self, file_path: Path):
        """Handle file creation or modification event."""
        should_proc = self.should_process(file_path)
        print(f"  File: {file_path.name} - Should process: {should_proc}")
        
        if not should_proc:
            # Debug why it was rejected
            if not file_path.is_file():
                print(f"    Reason: Not a file")
            elif self.should_ignore(file_path):
                print(f"    Reason: Ignored by pattern")
            elif self.config.allowed_extensions and file_path.suffix.lower() not in self.config.allowed_extensions:
                print(f"    Reason: Extension {file_path.suffix} not in allowed list")
            elif self.assigner.has_numeric_prefix(file_path.name):
                print(f"    Reason: Already has numeric prefix")
            else:
                file_hash = self._compute_file_hash(file_path)
                if file_hash in self.processed_files:
                    print(f"    Reason: Already processed")
            return
        
        # Add to pending with debounce timestamp
        with self.lock:
            self.pending_files[file_path] = time.time()
            print(f"    Added to pending queue (debounce: {self.config.debounce_seconds}s)")
    
    def process_pending_files(self):
        """Process files that have passed debounce window."""
        now = time.time()
        to_process = []
        
        with self.lock:
            for file_path, timestamp in list(self.pending_files.items()):
                if now - timestamp >= self.config.debounce_seconds:
                    to_process.append(file_path)
                    del self.pending_files[file_path]
        
        for file_path in to_process:
            self._process_file(file_path)
    
    def _process_file(self, file_path: Path):
        """Process a single file (stability check + rename)."""
        # Check if still exists and should be processed
        if not file_path.exists() or not self.should_process(file_path):
            return
        
        # Wait for file stability
        print(f"Checking stability: {file_path.name}")
        if not self.stability_checker.is_stable(file_path):
            print(f"File not stable, skipping: {file_path.name}")
            return
        
        # Allocate numeric prefix
        prefix = self.assigner.allocate_prefix(file_path)
        if not prefix:
            print(f"Failed to allocate prefix for: {file_path.name}")
            return
        
        # Apply prefix
        if self.config.auto_rename:
            # Auto-rename mode (direct application)
            new_path = self.assigner.rename_with_prefix(file_path, prefix)
            if new_path:
                print(f"✓ Renamed: {file_path.name} → {new_path.name}")
                file_hash = self._compute_file_hash(new_path)
                self.processed_files.add(file_hash)
            else:
                print(f"✗ Failed to rename: {file_path.name}")
        else:
            # Draft mode (log only, no rename)
            target_path = self.assigner.compute_target_path(file_path, prefix)
            print(f"[DRAFT] Would rename: {file_path.name} → {target_path.name}")
            file_hash = self._compute_file_hash(file_path)
            self.processed_files.add(file_hash)
    
    def scan_directory(self, directory: Path):
        """Recursively scan directory for files to process."""
        try:
            for item in directory.iterdir():
                if item.is_dir():
                    if not self.should_ignore(item):
                        self.scan_directory(item)
                elif item.is_file():
                    self.on_file_event(item)
        except PermissionError:
            pass
    
    def run_once(self):
        """Run one-time scan of watch root."""
        print(f"Scanning: {self.config.watch_root}")
        self.scan_directory(self.config.watch_root)
        
        # Wait for debounce + a bit extra for stability checks
        if self.pending_files:
            wait_time = self.config.debounce_seconds + (self.config.stability_checks * self.config.stability_interval_ms / 1000.0) + 0.5
            print(f"Waiting {wait_time:.1f}s for debounce + stability checks...")
            time.sleep(wait_time)
        
        self.process_pending_files()
        print("Scan complete.")
    
    def run_watch_loop(self, interval_seconds: float = 5.0):
        """Run continuous watch loop (basic polling implementation)."""
        self.running = True
        print(f"Watching: {self.config.watch_root}")
        print(f"Auto-rename: {'ENABLED' if self.config.auto_rename else 'DISABLED (draft mode)'}")
        
        try:
            while self.running:
                self.scan_directory(self.config.watch_root)
                self.process_pending_files()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\nStopping watcher...")
            self.running = False
    
    def stop(self):
        """Stop watch loop."""
        self.running = False


def create_default_config(watch_root: Path, registry_path: Path) -> FileWatcherConfig:
    """Create default configuration for file watcher."""
    return FileWatcherConfig(
        watch_root=watch_root,
        registry_path=registry_path,
        debounce_seconds=2.0,
        stability_checks=3,
        stability_interval_ms=500,
        auto_rename=False  # Safe default: draft mode
    )


def main():
    """CLI entry point."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description="File Watcher with Automatic 16-Digit Numeric Prefix Assignment",
        epilog="""
Safe Mode (default):
  Runs in draft mode - logs proposed renames without applying them.
  Use --auto-rename to enable automatic renaming.

Examples:
  # Scan directory in draft mode (safe)
  python file_watcher.py /path/to/dir --once
  
  # Scan and actually rename files
  python file_watcher.py /path/to/dir --once --auto-rename
  
  # Continuous watch in draft mode
  python file_watcher.py /path/to/dir
  
  # Continuous watch with auto-rename
  python file_watcher.py /path/to/dir --auto-rename
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('watch_root', type=Path, help='Directory to watch')
    parser.add_argument('--registry', type=Path, default=Path("./data/numeric_prefix_registry.json"),
                       help='Registry path (default: ./data/numeric_prefix_registry.json)')
    parser.add_argument('--auto-rename', action='store_true',
                       help='Enable auto-rename (default: draft mode)')
    parser.add_argument('--once', action='store_true',
                       help='Run one-time scan (default: continuous watch)')
    parser.add_argument('--debounce', type=float, default=2.0,
                       help='Debounce window in seconds (default: 2.0)')
    parser.add_argument('--interval', type=float, default=5.0,
                       help='Watch loop interval in seconds (default: 5.0)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = create_default_config(args.watch_root, args.registry)
    config.auto_rename = args.auto_rename
    config.debounce_seconds = args.debounce
    
    # Create and run watcher
    watcher = FileWatcher(config)
    
    if args.once:
        watcher.run_once()
    else:
        watcher.run_watch_loop(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
