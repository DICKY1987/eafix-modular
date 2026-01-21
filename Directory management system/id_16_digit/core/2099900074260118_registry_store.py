"""
doc_id: 2026011822400001
Registry Store - Central ID allocation and tracking.

Provides thread-safe, collision-resistant ID allocation with:
- File-based locking for concurrent access
- Atomic read-modify-write operations
- Allocation history tracking
- Status management (active/deprecated/superseded)
"""

import json
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Platform-specific imports
if platform.system() != 'Windows':
    import fcntl


@dataclass
class AllocationRecord:
    """Record of a single ID allocation."""
    id: str
    file_path: str
    allocated_at: str
    allocated_by: str
    status: str  # active, deprecated, superseded
    superseded_by: Optional[str] = None
    deprecated_reason: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class RegistryStore:
    """Central registry for ID allocation and tracking."""

    def __init__(self, registry_path: str):
        """
        Initialize registry store.
        
        Args:
            registry_path: Path to ID_REGISTRY.json file
        """
        self.registry_path = Path(registry_path)
        self.lock_path = self.registry_path.parent / f".{self.registry_path.name}.lock"
        self._ensure_registry_exists()

    def _canonicalize_path(self, path: str) -> str:
        """Normalize paths for consistent comparisons."""
        if not path:
            return ""

        normalized = os.path.normpath(path.strip())
        normalized = normalized.replace("\\", "/")
        if normalized.startswith("./"):
            normalized = normalized[2:]
        if platform.system() == 'Windows':
            normalized = normalized.lower()
        return normalized

    def canonicalize_path(self, path: str) -> str:
        """Public wrapper for canonical path normalization."""
        return self._canonicalize_path(path)

    def _is_id(self, value: str) -> bool:
        """Check if a value looks like a 16-digit ID."""
        return value.isdigit() and len(value) == 16

    def _get_alloc_canonical_path(self, alloc: Dict) -> str:
        """Get canonical path from allocation data."""
        metadata = alloc.get('metadata') or {}
        raw_path = metadata.get('canonical_path') or alloc.get('file_path', '')
        return self._canonicalize_path(raw_path)

    def _find_active_allocations_by_path(self, data: Dict, canonical_path: str) -> List[Dict]:
        """Find active allocations matching a canonical path."""
        matches = []
        for alloc in data.get('allocations', []):
            if alloc.get('status') != 'active':
                continue
            if self._get_alloc_canonical_path(alloc) == canonical_path:
                matches.append(alloc)
        return matches

    def _supersede_allocations(self, allocations: List[Dict], keep_id: str, reason: str):
        """Supersede allocations in-place, keeping one ID active."""
        superseded_at = datetime.now().isoformat()
        for alloc in allocations:
            if alloc.get('id') == keep_id:
                continue
            alloc['status'] = 'superseded'
            alloc['superseded_by'] = keep_id
            alloc['deprecated_reason'] = reason
            metadata = alloc.setdefault('metadata', {})
            metadata['superseded_at'] = superseded_at

    def _classify_legacy_id(self, doc_id: str, scope: str) -> Tuple[bool, Optional[str]]:
        """Classify IDs that do not match the current scope."""
        if not doc_id or not self._is_id(doc_id):
            return True, "non_standard_id"
        if scope and doc_id[-6:] != scope:
            return True, "scope_mismatch"
        return False, None

    def _ensure_registry_exists(self):
        """Create empty registry if it doesn't exist."""
        if not self.registry_path.exists():
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            initial_data = {
                "schema_version": "1.0",
                "scope": datetime.now().strftime("%y%m%d"),
                "counters": {},
                "allocations": [],
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "version": 1,
                    "total_allocations": 0
                }
            }
            with open(self.registry_path, 'w') as f:
                json.dump(initial_data, f, indent=2)

    @contextmanager
    def _lock(self, timeout: int = 5):
        """
        Acquire file lock for thread-safe operations.
        
        Args:
            timeout: Seconds to wait for lock (Windows only)
            
        Yields:
            Lock file handle
        """
        lock_file = open(self.lock_path, 'w')
        try:
            if platform.system() == 'Windows':
                # Windows file locking
                import msvcrt
                start_time = datetime.now()
                while True:
                    try:
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                        break
                    except OSError:
                        if (datetime.now() - start_time).seconds >= timeout:
                            raise TimeoutError(f"Could not acquire lock after {timeout}s")
                        import time
                        time.sleep(0.1)
            else:
                # Unix file locking
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            
            yield lock_file
        finally:
            if platform.system() == 'Windows':
                try:
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                except:
                    pass
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
            if self.lock_path.exists():
                self.lock_path.unlink()

    def _read_registry(self) -> Dict:
        """Read registry data (must be called within lock)."""
        with open(self.registry_path, 'r') as f:
            return json.load(f)

    def _write_registry(self, data: Dict):
        """Write registry data (must be called within lock)."""
        data['metadata']['last_updated'] = datetime.now().isoformat()
        data['metadata']['version'] = data['metadata'].get('version', 0) + 1
        
        # Write atomically using temp file
        temp_path = self.registry_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)
        temp_path.replace(self.registry_path)

    def _get_counter_key(self, ns_code: str, type_code: str, scope: str) -> str:
        """Generate counter key from components."""
        return f"{ns_code}_{type_code}_{scope}"

    def allocate_id(
        self,
        ns_code: str,
        type_code: str,
        file_path: str,
        allocated_by: str = "system",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Allocate next available ID for given namespace/type.
        
        Args:
            ns_code: 3-digit namespace code (e.g., "999")
            type_code: 2-digit type code (e.g., "20")
            file_path: Relative path to file
            allocated_by: User or system allocating the ID
            metadata: Optional additional metadata
            
        Returns:
            16-digit ID string
            
        Raises:
            ValueError: If sequence exhausted (>99999)
            TimeoutError: If lock cannot be acquired
        """
        with self._lock():
            data = self._read_registry()
            scope = data['scope']
            canonical_path = self._canonicalize_path(file_path)
            existing = self._find_active_allocations_by_path(data, canonical_path)
            if existing:
                primary = existing[0]
                metadata = primary.setdefault('metadata', {})
                metadata['canonical_path'] = canonical_path
                if primary.get('file_path') != file_path:
                    primary['file_path'] = file_path
                    metadata['normalized_at'] = datetime.now().isoformat()
                if len(existing) > 1:
                    self._supersede_allocations(existing, primary['id'], "duplicate_path")
                self._write_registry(data)
                return primary['id']

            counter_key = self._get_counter_key(ns_code, type_code, scope)
            
            # Initialize counter if needed
            if counter_key not in data['counters']:
                data['counters'][counter_key] = {
                    "current": 0,
                    "allocated": 0,
                    "reserved": []
                }
            
            counter = data['counters'][counter_key]
            
            # Find next available sequence
            next_seq = counter['current'] + 1
            while next_seq in counter.get('reserved', []):
                next_seq += 1
            
            if next_seq > 99999:
                raise ValueError(f"Sequence exhausted for {counter_key}")
            
            # Construct 16-digit ID
            allocated_id = f"{type_code}{ns_code}{next_seq:05d}{scope}"
            
            # Update counter
            counter['current'] = next_seq
            counter['allocated'] = counter.get('allocated', 0) + 1
            
            # Record allocation
            allocation = AllocationRecord(
                id=allocated_id,
                file_path=file_path,
                allocated_at=datetime.now().isoformat(),
                allocated_by=allocated_by,
                status="active",
                metadata=metadata
            )
            allocation.metadata = allocation.metadata or {}
            allocation.metadata.setdefault('canonical_path', canonical_path)
            data['allocations'].append(allocation.to_dict())
            data['metadata']['total_allocations'] = len(data['allocations'])
            
            self._write_registry(data)
            return allocated_id

    def check_uniqueness(self) -> Tuple[bool, List[str]]:
        """
        Check if all IDs in registry are unique.
        
        Returns:
            Tuple of (is_unique, list_of_duplicate_ids)
        """
        with self._lock():
            data = self._read_registry()
            ids = [alloc['id'] for alloc in data['allocations'] if alloc['status'] == 'active']
            
            seen = set()
            duplicates = []
            for id_val in ids:
                if id_val in seen:
                    duplicates.append(id_val)
                seen.add(id_val)
            
            return len(duplicates) == 0, duplicates

    def get_allocation(self, id_or_path: str) -> Optional[AllocationRecord]:
        """
        Get allocation record by ID or file path.
        
        Args:
            id_or_path: 16-digit ID or file path
            
        Returns:
            AllocationRecord if found, None otherwise
        """
        with self._lock():
            data = self._read_registry()
            if self._is_id(id_or_path):
                for alloc in data['allocations']:
                    if alloc['id'] == id_or_path:
                        return AllocationRecord(**alloc)
            else:
                canonical_path = self._canonicalize_path(id_or_path)
                for alloc in data['allocations']:
                    if self._get_alloc_canonical_path(alloc) == canonical_path:
                        return AllocationRecord(**alloc)
            
            return None

    def get_active_allocation_by_path(self, file_path: str) -> Optional[AllocationRecord]:
        """Get active allocation record by file path."""
        with self._lock():
            data = self._read_registry()
            canonical_path = self._canonicalize_path(file_path)
            matches = self._find_active_allocations_by_path(data, canonical_path)
            if matches:
                return AllocationRecord(**matches[0])
            return None

    def register_existing_id(
        self,
        doc_id: str,
        file_path: str,
        allocated_by: str = "import_existing",
        metadata: Optional[Dict] = None
    ) -> Tuple[str, str]:
        """
        Register an ID that already exists in the filename.

        Returns:
            Tuple of (action, doc_id)
        """
        with self._lock():
            data = self._read_registry()
            canonical_path = self._canonicalize_path(file_path)

            for alloc in data.get('allocations', []):
                if alloc.get('id') == doc_id:
                    existing_path = self._get_alloc_canonical_path(alloc)
                    meta = alloc.setdefault('metadata', {})
                    meta['canonical_path'] = canonical_path
                    if existing_path != canonical_path:
                        alloc['file_path'] = file_path
                        meta['moved_at'] = datetime.now().isoformat()
                    self._write_registry(data)
                    return "already_registered", doc_id

            active_matches = self._find_active_allocations_by_path(data, canonical_path)
            if active_matches:
                active_ids = {alloc.get('id') for alloc in active_matches}
                if doc_id in active_ids:
                    primary = next((alloc for alloc in active_matches if alloc.get('id') == doc_id), active_matches[0])
                    for alloc in active_matches:
                        if alloc.get('id') == doc_id:
                            meta = alloc.setdefault('metadata', {})
                            meta['canonical_path'] = canonical_path
                    if len(active_matches) > 1:
                        self._supersede_allocations(active_matches, primary.get('id', doc_id), "duplicate_path")
                    self._write_registry(data)
                    return "already_registered", doc_id
                self._supersede_allocations(active_matches, doc_id, "path_reassigned")

            record_meta = dict(metadata or {})
            record_meta['canonical_path'] = canonical_path
            is_legacy, legacy_reason = self._classify_legacy_id(doc_id, data.get('scope', ''))
            if is_legacy:
                record_meta['legacy_id'] = True
                record_meta['legacy_reason'] = legacy_reason
                if legacy_reason == "scope_mismatch" and self._is_id(doc_id):
                    record_meta['legacy_scope'] = doc_id[-6:]

            allocation = AllocationRecord(
                id=doc_id,
                file_path=file_path,
                allocated_at=datetime.now().isoformat(),
                allocated_by=allocated_by,
                status="active",
                metadata=record_meta
            )
            data['allocations'].append(allocation.to_dict())
            data['metadata']['total_allocations'] = len(data['allocations'])

            self._write_registry(data)
            return "registered", doc_id

    def mark_deprecated(
        self,
        id: str,
        reason: str,
        superseded_by: Optional[str] = None
    ):
        """
        Mark an ID as deprecated.
        
        Args:
            id: 16-digit ID to deprecate
            reason: Reason for deprecation
            superseded_by: Optional ID that supersedes this one
        """
        with self._lock():
            data = self._read_registry()
            
            for alloc in data['allocations']:
                if alloc['id'] == id:
                    alloc['status'] = 'superseded' if superseded_by else 'deprecated'
                    alloc['deprecated_reason'] = reason
                    if superseded_by:
                        alloc['superseded_by'] = superseded_by
                    break
            
            self._write_registry(data)

    def update_file_path(self, id: str, new_path: str):
        """
        Update file path for an allocation (for moves/renames).
        
        Args:
            id: 16-digit ID
            new_path: New relative file path
        """
        with self._lock():
            data = self._read_registry()
            
            for alloc in data['allocations']:
                if alloc['id'] == id:
                    alloc['file_path'] = new_path
                    if 'metadata' not in alloc:
                        alloc['metadata'] = {}
                    alloc['metadata']['moved_at'] = datetime.now().isoformat()
                    alloc['metadata']['canonical_path'] = self._canonicalize_path(new_path)
                    break
            
            self._write_registry(data)

    def get_stats(self) -> Dict:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with stats
        """
        with self._lock():
            data = self._read_registry()
            
            active = sum(1 for a in data['allocations'] if a['status'] == 'active')
            deprecated = sum(1 for a in data['allocations'] if a['status'] == 'deprecated')
            superseded = sum(1 for a in data['allocations'] if a['status'] == 'superseded')
            
            return {
                'total_allocations': len(data['allocations']),
                'active_allocations': active,
                'deprecated_allocations': deprecated,
                'superseded_allocations': superseded,
                'total_counters': len(data['counters']),
                'registry_version': data['metadata']['version'],
                'last_updated': data['metadata']['last_updated']
            }

    def get_all_active_ids(self) -> List[Tuple[str, str]]:
        """
        Get all active IDs and their file paths.
        
        Returns:
            List of (id, file_path) tuples
        """
        with self._lock():
            data = self._read_registry()
            return [
                (alloc['id'], alloc['file_path'])
                for alloc in data['allocations']
                if alloc['status'] == 'active'
            ]
