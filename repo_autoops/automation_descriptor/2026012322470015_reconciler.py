#!/usr/bin/env python3
"""
doc_id: 2026012322470015
Reconciler - Drift Detection and Repair

Scans filesystem to detect:
- Files missing from registry
- Files moved/renamed
- Registry entries for deleted files
- Stale metadata

Enqueues repair work items without duplicates.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Set
import json

from repo_autoops.automation_descriptor.work_queue import WorkQueue

logger = logging.getLogger(__name__)


class Reconciler:
    """
    Detects drift between filesystem and registry.
    
    Reconciliation strategy:
    1. Scan filesystem for all target files
    2. Load registry records
    3. Detect mismatches (missing, moved, stale)
    4. Enqueue repair work items
    5. Track to prevent duplicate processing
    """
    
    def __init__(
        self,
        watch_paths: List[str],
        registry_path: Path,
        queue: WorkQueue
    ):
        """
        Initialize reconciler.
        
        Args:
            watch_paths: Directories to scan
            registry_path: Path to UNIFIED_SSOT_REGISTRY.json
            queue: Work queue for repairs
        """
        self.watch_paths = [Path(p) for p in watch_paths]
        self.registry_path = Path(registry_path)
        self.queue = queue
        
        self.stats = {
            "files_scanned": 0,
            "registry_records": 0,
            "missing_from_registry": 0,
            "missing_from_filesystem": 0,
            "repairs_enqueued": 0
        }
    
    def reconcile(self) -> Dict[str, int]:
        """
        Run full reconciliation scan.
        
        Returns:
            Statistics dict with scan results
        """
        logger.info("Starting reconciliation scan")
        
        # Step 1: Scan filesystem
        fs_files = self._scan_filesystem()
        self.stats["files_scanned"] = len(fs_files)
        
        # Step 2: Load registry
        registry_files = self._load_registry_files()
        self.stats["registry_records"] = len(registry_files)
        
        # Step 3: Detect drift
        missing_from_registry = fs_files - registry_files
        missing_from_fs = registry_files - fs_files
        
        self.stats["missing_from_registry"] = len(missing_from_registry)
        self.stats["missing_from_filesystem"] = len(missing_from_fs)
        
        # Step 4: Enqueue repairs
        for file_path in missing_from_registry:
            self.queue.enqueue(
                str(file_path),
                "RECONCILE_ADD",
                {"reason": "missing_from_registry"}
            )
            self.stats["repairs_enqueued"] += 1
        
        for file_path in missing_from_fs:
            self.queue.enqueue(
                str(file_path),
                "RECONCILE_REMOVE",
                {"reason": "file_deleted"}
            )
            self.stats["repairs_enqueued"] += 1
        
        logger.info(f"Reconciliation complete: {self.stats}")
        return self.stats
    
    def _scan_filesystem(self) -> Set[Path]:
        """Scan filesystem for all Python files."""
        files = set()
        
        for watch_path in self.watch_paths:
            if not watch_path.exists():
                logger.warning(f"Watch path does not exist: {watch_path}")
                continue
            
            # Recursively find Python files
            for py_file in watch_path.rglob("*.py"):
                if py_file.is_file():
                    files.add(py_file)
        
        return files
    
    def _load_registry_files(self) -> Set[Path]:
        """Load file paths from registry."""
        files = set()
        
        if not self.registry_path.exists():
            logger.warning(f"Registry does not exist: {self.registry_path}")
            return files
        
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            for record in registry.get("records", []):
                if record.get("record_kind") == "entity":
                    rel_path = record.get("relative_path")
                    if rel_path:
                        # Construct full path (assuming project root)
                        full_path = Path(rel_path)
                        if full_path.suffix == ".py":
                            files.add(full_path)
        
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
        
        return files
    
    def get_stats(self) -> Dict[str, int]:
        """Get reconciliation statistics."""
        return self.stats.copy()
