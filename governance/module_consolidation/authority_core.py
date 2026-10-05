"""Shared, offline primitives for the guarded module-authority workflow."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
CONTROL = REPO / "governance/module_consolidation"
REGISTRIES = "EAFIX_auth_docs/01_canonical_registries"
SCHEMA = f"{REGISTRIES}/eafix_unified_atomic_module_schema_v2_0_0.json"
PROCESS = f"{REGISTRIES}/process_registry.jsonl"
SHARED = f"{REGISTRIES}/shared_file_registry.json"
BUNDLE = "EAFIX_auth_docs/manifests/eafix_module_manifests_bundle.vNext.schema_valid.json"
FINAL_DISPOSITIONS = {"MIGRATE", "ALREADY_COVERED", "MERGE", "REJECTED", "RETAINED_EXTERNAL"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def value_sha(value: Any) -> str:
    return sha_bytes(canonical(value))


def file_sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def evidence_version(repo: Path, source_path: str, expected_sha: str, versions: dict) -> Path:
    """Resolve preserved baseline evidence only for an exact governed successor."""
    current = repo / source_path
    if current.is_file() and file_sha(current) == expected_sha:
        return current
    record = versions.get(source_path)
    if record and current.is_file() and file_sha(current) == record["current_sha256"]:
        snapshot = repo / record["baseline_snapshot_path"]
        if record["baseline_sha256"] == expected_sha and snapshot.is_file() and file_sha(snapshot) == expected_sha:
            return snapshot
    return current  # The caller's hash check fails; never accept an arbitrary edit.


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(canonical(value) + b"\n" for value in values))


def pointer(value: Any, address: str) -> Any:
    if address and not address.startswith("/"):
        raise ValueError("JSON pointer must be empty or begin with /")
    for token in address[1:].split("/") if address else []:
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def leaves(value: Any, address: str = ""):
    if isinstance(value, dict) and value:
        for key, item in value.items():
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from leaves(item, address + "/" + escaped)
    elif isinstance(value, list) and value:
        for index, item in enumerate(value):
            yield from leaves(item, address + f"/{index}")
    else:
        yield address, value


def git(*arguments: str, repo: Path = REPO) -> str:
    return subprocess.check_output(["git", *arguments], cwd=repo, text=True).strip()


def guarded_replace(path: Path, expected_sha: str, old_value: Any, new_value: Any,
                    baseline_commit: str, *, repo: Path = REPO) -> None:
    """Reject stale bytes or ancestry before replacing a reviewed candidate."""
    subprocess.run(["git", "merge-base", "--is-ancestor", baseline_commit, "HEAD"],
                   cwd=repo, check=True, capture_output=True)
    if file_sha(path) != expected_sha or load(path) != old_value:
        raise ValueError("STALE_BASELINE: reviewed content changed; reconcile again")
    write(path, new_value)


def safe_relative(path: str) -> str:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("Repository-relative path required")
    return candidate.as_posix()


def archive_copy(source: Path, destination: Path, receipt: dict) -> None:
    """Copy only sources independently cleared by both gates; never annotate bytes."""
    if not receipt.get("fully_scraped") or not receipt.get("safe_to_archive"):
        raise ValueError("ARCHIVE_BLOCKED: reconciliation and retention gates required")
    if receipt.get("unresolved_claim_count", 1) != 0:
        raise ValueError("ARCHIVE_BLOCKED: unresolved claims remain")
    if receipt.get("active_authority") is not False or receipt.get("required_live_input") is not False:
        raise ValueError("ARCHIVE_BLOCKED: source is still required")
    data = source.read_bytes()
    if sha_bytes(data) != receipt["original_sha256"]:
        raise ValueError("STALE_SOURCE: archive source changed")
    destination.mkdir(parents=True, exist_ok=True)
    original = destination / ("original" + source.suffix)
    if original.exists() and original.read_bytes() != data:
        raise ValueError("IMMUTABLE_ARCHIVE: original already exists with other bytes")
    original.write_bytes(data)
    if file_sha(original) != receipt["original_sha256"]:
        raise ValueError("ARCHIVE_HASH_MISMATCH")
    write(destination / "receipt.json", {**receipt, "archived_sha256": file_sha(original),
          "archive_original_filename": original.name})
    (destination / "README.md").write_text(
        "# Historical source\n\nOriginal bytes are immutable and are not active authority. "
        "Restore the original to the path recorded in receipt.json.\n", encoding="utf-8")
