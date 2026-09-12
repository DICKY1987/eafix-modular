"""Deterministic scanner for EAFIX filename document identifiers."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

DOC_ID_PATTERN = re.compile(r"^(?:P_)?(\d{16,20})_(.+)$")
DEFAULT_EXCLUDED_PREFIXES = (
    ".git/",
    ".venv/",
    "venv/",
    "node_modules/",
    "build/",
    "dist/",
)


@dataclass(frozen=True)
class ScannedFile:
    path: str
    doc_id: str
    basename: str


@dataclass
class ScanResult:
    root: str
    total_files: int = 0
    prefixed_files: list[ScannedFile] = field(default_factory=list)
    unprefixed_files: list[str] = field(default_factory=list)
    duplicate_ids: dict[str, list[str]] = field(default_factory=dict)

    @property
    def coverage_ratio(self) -> float:
        return len(self.prefixed_files) / self.total_files if self.total_files else 1.0

    @property
    def duplicate_count(self) -> int:
        return sum(len(paths) for paths in self.duplicate_ids.values())


def _tracked_paths(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [
        raw.decode("utf-8", errors="surrogateescape").replace("\\", "/")
        for raw in completed.stdout.split(b"\0")
        if raw
    ]


def _filesystem_paths(root: Path) -> list[str]:
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and not path.relative_to(root).as_posix().startswith(DEFAULT_EXCLUDED_PREFIXES)
    )


def scan_paths(root: str | Path, paths: Iterable[str]) -> ScanResult:
    """Classify a supplied repository-relative path set."""
    resolved = Path(root).resolve()
    result = ScanResult(root=str(resolved))
    by_id: dict[str, list[str]] = {}

    for raw_path in sorted(set(paths)):
        path = raw_path.replace("\\", "/")
        if path.startswith(DEFAULT_EXCLUDED_PREFIXES):
            continue
        result.total_files += 1
        match = DOC_ID_PATTERN.match(Path(path).name)
        if not match:
            result.unprefixed_files.append(path)
            continue
        scanned = ScannedFile(path=path, doc_id=match.group(1), basename=match.group(2))
        result.prefixed_files.append(scanned)
        by_id.setdefault(scanned.doc_id, []).append(path)

    result.duplicate_ids = {
        doc_id: sorted(found)
        for doc_id, found in sorted(by_id.items())
        if len(found) > 1
    }
    return result


def scan_repository(
    root: str | Path = ".",
    extensions: Sequence[str] | None = None,
    *,
    tracked_only: bool = True,
) -> ScanResult:
    """Scan tracked files by default so local caches cannot change CI results."""
    resolved = Path(root).resolve()
    paths = _tracked_paths(resolved) if tracked_only else _filesystem_paths(resolved)
    if extensions is not None:
        normalized = {ext.lower() for ext in extensions}
        paths = [path for path in paths if Path(path).suffix.lower() in normalized]
    return scan_paths(resolved, paths)
