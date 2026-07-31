"""
doc_id_scanner.py — walks the repository tree, identifies files that carry
the doc-ID naming convention (<16-digit-numeric-prefix>_ or P_<20-digit>_),
computes coverage, and surfaces duplicate IDs.

The doc-ID naming convention used in this repository:
  - Default files:  <20-digit-id>_<original-name>  (e.g. 0099900002260118_.coverage)
  - Python files:   P_<20-digit-id>_<original-name>
  - Some older files use a 16-digit prefix

Usage:
    from doc_id_subsystem.core.doc_id_scanner import scan_repository
    results = scan_repository(root=".")
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# Match patterns:
#   20-digit prefix: "0099900002260118_..."   (some are only 16 digits historically)
#   Python prefix:   "P_0099900002260118_..."
_DOC_ID_PATTERN = re.compile(
    r"^(?:P_)?(\d{16,20})_"
)

_EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
}


@dataclass
class ScannedFile:
    path: str           # relative to root
    doc_id: str         # extracted numeric ID
    basename: str       # original filename without the ID prefix


@dataclass
class ScanResult:
    root: str
    total_files: int = 0
    prefixed_files: List[ScannedFile] = field(default_factory=list)
    unprefixed_files: List[str] = field(default_factory=list)
    duplicate_ids: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def coverage_ratio(self) -> float:
        if self.total_files == 0:
            return 1.0
        return len(self.prefixed_files) / self.total_files

    @property
    def duplicate_count(self) -> int:
        return sum(len(v) for v in self.duplicate_ids.values())


def _should_skip(dirpath: str) -> bool:
    parts = set(Path(dirpath).parts)
    return bool(parts & _EXCLUDED_DIRS)


def scan_repository(
    root: str = ".",
    extensions: Optional[List[str]] = None,
) -> ScanResult:
    """
    Walk *root*, classify every regular file, and return a ScanResult.

    Parameters
    ----------
    root:
        Directory to scan.  Defaults to the current working directory.
    extensions:
        If provided, only files whose suffix is in this list are counted.
        Pass ``None`` (default) to scan all files.
    """
    root = str(Path(root).resolve())
    result = ScanResult(root=root)

    id_to_paths: Dict[str, List[str]] = {}

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded directories in-place so os.walk doesn't descend.
        dirnames[:] = [
            d for d in dirnames
            if d not in _EXCLUDED_DIRS
        ]

        for filename in filenames:
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, root)

            if extensions is not None:
                _, ext = os.path.splitext(filename)
                if ext.lower() not in extensions:
                    continue

            result.total_files += 1

            m = _DOC_ID_PATTERN.match(filename)
            if m:
                doc_id = m.group(1)
                # Strip the prefix to get the original basename.
                basename = _DOC_ID_PATTERN.sub("", filename)
                if filename.startswith("P_"):
                    basename = _DOC_ID_PATTERN.sub("", filename[2:])
                sf = ScannedFile(path=rel_path, doc_id=doc_id, basename=basename)
                result.prefixed_files.append(sf)
                id_to_paths.setdefault(doc_id, []).append(rel_path)
            else:
                result.unprefixed_files.append(rel_path)

    # Identify duplicates (same ID assigned to more than one path).
    result.duplicate_ids = {
        doc_id: paths
        for doc_id, paths in id_to_paths.items()
        if len(paths) > 1
    }

    return result
