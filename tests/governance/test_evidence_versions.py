"""Preserved evidence must not conceal an unexpected current-source mutation."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "governance/module_consolidation"))
from authority_core import evidence_version, file_sha


def test_governed_snapshot_requires_both_version_hashes(tmp_path):
    current = tmp_path / "source.txt"
    snapshot = tmp_path / "baseline.txt"
    snapshot.write_bytes(b"original")
    current.write_bytes(b"approved successor")
    old_hash = file_sha(snapshot)
    versions = {"source.txt": {"baseline_sha256": old_hash,
        "current_sha256": file_sha(current), "baseline_snapshot_path": "baseline.txt"}}
    assert evidence_version(tmp_path, "source.txt", old_hash, versions) == snapshot
    current.write_bytes(b"unexpected edit")
    assert evidence_version(tmp_path, "source.txt", old_hash, versions) == current
    assert file_sha(current) != old_hash


def test_corrupt_snapshot_is_rejected(tmp_path):
    current = tmp_path / "source.txt"
    snapshot = tmp_path / "baseline.txt"
    snapshot.write_bytes(b"original")
    current.write_bytes(b"successor")
    old_hash = file_sha(snapshot)
    versions = {"source.txt": {"baseline_sha256": old_hash,
        "current_sha256": file_sha(current), "baseline_snapshot_path": "baseline.txt"}}
    snapshot.write_bytes(b"corrupt")
    assert evidence_version(tmp_path, "source.txt", old_hash, versions) == current
