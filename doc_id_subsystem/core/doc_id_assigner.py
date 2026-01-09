#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-SCRIPTS-DOC-ID-ASSIGNER-204
# DOC_LINK: DOC-SCRIPT-SCRIPTS-DOC-ID-ASSIGNER-141
# -*- coding: utf-8 -*-
"""
Doc ID Auto-Assigner

PURPOSE:
    Use docs_inventory.jsonl + DOC_ID_REGISTRY.yaml to assign doc_ids to all
    eligible files that are currently missing them, and inject the IDs into
    the files in-place.

PATTERN: PATTERN-DOC-ID-AUTOASSIGN-002

USAGE:
    python scripts/doc_id_assigner.py auto-assign --dry-run
    python scripts/doc_id_assigner.py auto-assign --limit 50 --dry-run
    python scripts/doc_id_assigner.py auto-assign
"""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, INVENTORY_PATH
from common.rules import validate_doc_id, format_doc_id, DOC_ID_REGEX  # Phase 1: Use centralized rules
from common.utils import load_jsonl, save_jsonl
from common.registry import Registry

# Event emission (Phase 2: Observability)
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "SSOT_System" / "SSOT_SYS_tools"))
    from event_emitter import get_event_emitter
    EVENT_SYSTEM_AVAILABLE = True
except ImportError:
    EVENT_SYSTEM_AVAILABLE = False
    def get_event_emitter():
        return None

def _emit_event(subsystem: str, step_id: str, subject: str, summary: str,
                severity: str = "INFO", details: dict = None):
    """Helper to emit events with graceful degradation if event system unavailable."""
    if EVENT_SYSTEM_AVAILABLE:
        try:
            emitter = get_event_emitter()
            if emitter:
                emitter.emit(
                    subsystem=subsystem,
                    step_id=step_id,
                    subject=subject,
                    summary=summary,
                    severity=severity,
                    details=details or {}
                )
        except Exception:
            pass  # Gracefully degrade if event system fails


# --- Registry module loader -------------------------------------------------


def _load_registry_module():
    """
    Load doc_id_registry_cli.py as a module so we can reuse DocIDRegistry
    without spawning a subprocess for every file.

    This expects:
        SUB_DOC_ID/1_CORE_OPERATIONS/lib/doc_id_registry_cli.py
    """
    registry_path = Path(__file__).parent / "lib" / "doc_id_registry_cli.py"
    if not registry_path.exists():
        print(
            f"[ERROR] Could not find registry CLI at {registry_path}", file=sys.stderr
        )
        sys.exit(1)

    import importlib.util

    spec = importlib.util.spec_from_file_location("doc_id_registry_cli", registry_path)
    if spec is None or spec.loader is None:
        print("[ERROR] Failed to load doc_id_registry_cli module", file=sys.stderr)
        sys.exit(1)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_registry_module = _load_registry_module()
DocIDRegistry = _registry_module.DocIDRegistry  # type: ignore[attr-defined]


# --- Inventory model --------------------------------------------------------


@dataclass
class InventoryEntry:
    path: str
    doc_id: Optional[str] = None
    status: str = "missing"
    file_type: str = "unknown"
    last_modified: str = ""
    scanned_at: str = ""

    @classmethod
    def from_dict(cls, d: Dict) -> "InventoryEntry":
        return cls(
            path=d["path"],
            doc_id=d.get("doc_id"),
            status=d.get("status", "missing"),
            file_type=d.get("file_type", "unknown"),
            last_modified=d.get("last_modified", ""),
            scanned_at=d.get("scanned_at", ""),
        )


def load_inventory(path: Path = INVENTORY_PATH) -> List[InventoryEntry]:
    """Load docs_inventory.jsonl into memory."""
    if not path.exists():
        print(f"[ERROR] Inventory file not found: {path}", file=sys.stderr)
        print("        Run: python scripts/doc_id_scanner.py scan", file=sys.stderr)
        sys.exit(1)

    entries: List[InventoryEntry] = []
    data_list = load_jsonl(path)
    for data in data_list:
        entries.append(InventoryEntry.from_dict(data))

    return entries


# --- Inference helpers ------------------------------------------------------


def infer_category(path: str, available_categories: List[str]) -> str:
    """
    Infer registry category from file path.

    Enhanced with comprehensive directory-to-category mappings for 100% coverage.
    Priority order:
    1. Exact directory path matches (most specific)
    2. Partial path matches
    3. File extension fallbacks
    4. Default fallback (legacy/patterns)
    """
    normalized = path.replace("\\", "/")
    if not normalized.startswith("/"):
        normalized = "/" + normalized

    # Priority 1: Exact directory mappings (most specific first)
    exact_mappings: List[Tuple[str, str]] = [
        # Core system components
        ("core", "/core/"),
        ("error", "/error/"),
        ("aim", "/aim/"),
        ("pm", "/pm/"),
        ("engine", "/engine/"),
        ("infra", "/infra/"),
        # Patterns and UET
        ("patterns", "/UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK/patterns/"),
        ("patterns", "/patterns/"),
        ("guide", "/UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK/guides/"),
        ("spec", "/UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK/specs/"),
        # Documentation
        ("guide", "/docs/"),
        ("guide", "/documentation/"),
        ("guide", "/developer/"),
        ("arch", "/adr/"),
        # Modules and components
        ("core", "/modules/"),
        ("spec", "/specifications/"),
        ("spec", "/schema/"),
        ("spec", "/openspec/"),
        # Testing
        ("test", "/tests/"),
        # Scripts and tools
        ("script", "/scripts/"),
        ("script", "/tools/"),
        # Configuration
        ("config", "/config/"),
        ("config", "/.github/"),
        # Special directories
        ("legacy", "/archive/"),
        ("legacy", "/legacy/"),
        ("task", "/ToDo_Task/"),
        ("task", "/workstreams/"),
        ("task", "/workstreams_uet/"),
        # Doc_id system
        ("guide", "/doc_id/"),
        # Build and package artifacts
        ("infra", "/build/"),
        ("infra", "/__pycache__/"),
        ("infra", "/.venv/"),
        ("infra", "/node_modules/"),
    ]

    # Priority 2: Partial path matches (for nested structures)
    partial_mappings: List[Tuple[str, str]] = [
        ("test", "/test"),
        ("spec", "/spec"),
        ("guide", "/guide"),
        ("patterns", "/pattern"),
        ("config", "/config"),
    ]

    # Priority 3: File extension mappings
    extension_mappings: List[Tuple[str, str]] = [
        ("script", ".ps1"),
        ("script", ".sh"),
        ("script", ".bat"),
        ("config", ".yaml"),
        ("config", ".yml"),
        ("config", ".toml"),
        ("config", ".ini"),
        ("config", ".json"),
        ("guide", ".md"),
        ("guide", ".txt"),
        ("core", ".py"),
    ]

    # Try exact directory matches first
    for candidate, marker in exact_mappings:
        if marker in normalized and candidate in available_categories:
            return candidate

    # Try partial path matches
    for candidate, marker in partial_mappings:
        if marker in normalized and candidate in available_categories:
            return candidate

    # Try extension-based mapping
    for candidate, ext in extension_mappings:
        if normalized.endswith(ext) and candidate in available_categories:
            return candidate

    # Fallback priority: patterns > guide > legacy > first available
    for fallback in ("patterns", "guide", "legacy"):
        if fallback in available_categories:
            return fallback

    # Absolute fallback: first category defined in registry
    if available_categories:
        return available_categories[0]

    print("[ERROR] No categories available in DOC_ID_REGISTRY.yaml", file=sys.stderr)
    sys.exit(1)


def infer_name_and_title(path: str, file_type: str) -> Tuple[str, str]:
    """
    Infer logical 'name' and human-readable 'title' for the registry.

    name: short machine-friendly identifier (used in doc_id)
    title: human-readable description shown in registry
    """
    rel = Path(path)
    stem = rel.stem
    parent = rel.parent.name or "root"

    def _sanitize(segment: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9_-]", "-", segment)
        cleaned = re.sub(r"-+", "-", cleaned).strip("-")
        return cleaned or "ROOT"

    # Special case: __*__ files (dunder files)
    if stem.startswith("__") and stem.endswith("__"):
        stem_clean = stem[2:-2].upper()  # Remove __ from both ends
        if not stem_clean:
            stem_clean = "DUNDER"
    else:
        # Sanitize stem: remove special chars, limit length
        stem_clean = re.sub(r"[^a-zA-Z0-9_-]", "-", stem)
        stem_clean = re.sub(r"-+", "-", stem_clean).strip("-")

    parent_clean = _sanitize(parent)

    # Limit to reasonable length (max 50 chars for stem)
    if len(stem_clean) > 50:
        stem_clean = stem_clean[:50].rsplit("-", 1)[0]  # Cut at word boundary

    if file_type == "py":
        if stem.startswith("test_"):
            name = f"{parent_clean}-{stem_clean}".replace("_", "-")
            title = f"Tests for {parent}.{stem.replace('test_', '')}"
        else:
            name = f"{parent_clean}-{stem_clean}".replace("_", "-")
            title = f"{parent} module: {stem}"
    elif file_type in ("ps1", "sh"):
        name = stem_clean.replace("_", "-")
        title = f"Script: {stem}"
    elif file_type in ("yaml", "yml"):
        name = stem_clean.replace("_", "-")
        title = f"Config: {stem}"
    elif file_type == "json":
        name = stem_clean.replace("_", "-")
        title = f"JSON spec: {stem}"
    elif file_type == "md":
        name = stem_clean.replace("_", "-")
        # Clean up title too
        title = stem.replace("-", " ").replace("_", " ").title()
        if len(title) > 80:
            title = title[:77] + "..."
    else:
        name = stem_clean.replace("_", "-")
        title = stem

    # Final name cleanup: ensure uppercase, no underscores
    name = name.replace("_", "-").upper()
    # Remove leading/trailing dashes and collapse multiple dashes
    name = re.sub(r"-+", "-", name).strip("-")
    # If name is empty or invalid, use fallback
    if not name or not re.match(r"^[A-Z0-9]", name):
        name = f"FILE-{parent_clean.upper()}-{stem_clean[:20].upper()}"
        name = re.sub(r"-+", "-", name).strip("-")
    # Limit total name length to avoid overly long IDs
    if len(name) > 40:
        name = name[:40].rsplit("-", 1)[0] if "-" in name[:40] else name[:40]
    # Remove any trailing dashes again
    name = name.rstrip("-")
    # Final validation: must not be empty and not end with dash
    if not name or name.endswith("-"):
        name = "UNNAMED"

    return name, title


# --- Injection helpers ------------------------------------------------------


def inject_doc_id_into_content(content: str, file_type: str, doc_id: str) -> str:
    """
    Inject doc_id into file content based on type.

    Simple and idempotent: if the doc_id is already present, content is
    returned unchanged.
    
    NOTE: Phase 1 refactoring - now uses common.rules.validate_doc_id()
    """
    # Use centralized validation
    def is_valid(existing: str) -> bool:
        return validate_doc_id(existing)

    # Python: module docstring or header comment
    if file_type == "py":
        lines = content.splitlines()
        new_lines: List[str] = []

        # If a doc_id is already near the top, leave unchanged
        for line in lines[:50]:
            found = re.search(r"DOC_(ID|LINK):\s*(DOC-[A-Z0-9-]+)", line)
            if found and is_valid(found.group(2)):
                return content

        idx = 0
        # Preserve shebang
        if lines and lines[0].startswith("#!"):
            new_lines.append(lines[0])
            idx = 1

        # Look for a top-level docstring
        if idx < len(lines) and (
            lines[idx].lstrip().startswith('"""')
            or lines[idx].lstrip().startswith("'''")
        ):
            quote = lines[idx].lstrip()[:3]
            new_lines.append(lines[idx])

            # Single-line docstring
            if lines[idx].rstrip().endswith(quote) and len(lines[idx].strip()) > 3:
                remainder = lines[idx + 1 :]
            else:
                i = idx + 1
                while i < len(lines):
                    new_lines.append(lines[i])
                    if lines[i].rstrip().endswith(quote):
                        i += 1
                        break
                    i += 1
                remainder = lines[i:]

            new_lines.append(f"# DOC_ID: {doc_id}")
            new_lines.extend(remainder)
        else:
            # No obvious docstring - insert comment near top
            new_lines.append(f"# DOC_LINK: {doc_id}")
            new_lines.extend(lines[idx:])

        result = "\n".join(new_lines)
        if content.endswith("\n"):
            result += "\n"
        return result

    # Markdown: YAML frontmatter
    if file_type == "md":
        if content.startswith("---\n"):
            lines = content.splitlines()
            end_idx = None
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    end_idx = i
                    break
            if end_idx is not None:
                fm = lines[1:end_idx]
                for idx, l in enumerate(fm):
                    m = re.match(r"doc_id:\s*[\"']?(DOC-[A-Z0-9-]+)", l.strip())
                    if m:
                        if is_valid(m.group(1)):
                            return content
                        fm[idx] = f"doc_id: {doc_id}"
                        new_lines = ["---", *fm, "---", *lines[end_idx + 1 :]]
                        result = "\n".join(new_lines)
                        if content.endswith("\n"):
                            result += "\n"
                        return result
                new_fm = ["doc_id: " + doc_id] + fm
                new_lines = ["---", *new_fm, "---", *lines[end_idx + 1 :]]
                result = "\n".join(new_lines)
                if content.endswith("\n"):
                    result += "\n"
                return result
        # No frontmatter
        fm = f"---\ndoc_id: {doc_id}\n---\n\n"
        return fm + content

    # YAML
    if file_type in ("yaml", "yml"):
        lines = content.splitlines()
        for idx, l in enumerate(lines[:20]):
            m = re.match(r"doc_id:\s*[\"']?(DOC-[A-Z0-9-]+)", l.strip())
            if m:
                if is_valid(m.group(1)):
                    return content
                lines[idx] = f"doc_id: {doc_id}"
                result = "\n".join(lines)
                if content.endswith("\n"):
                    result += "\n"
                return result
        return "doc_id: " + doc_id + "\n" + content

    # JSON
    if file_type == "json":
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                if "doc_id" in data:
                    if is_valid(str(data["doc_id"])):
                        return content
                data["doc_id"] = doc_id
                data["doc_id"] = doc_id
                return json.dumps(data, indent=2) + "\n"
        except json.JSONDecodeError:
            # Fall back to a header comment
            pass
        return f"/* DOC_ID: {doc_id} */\n" + content

    # PowerShell / Shell
    if file_type in ("ps1", "sh"):
        lines = content.splitlines()
        new_lines: List[str] = []
        idx = 0
        if lines and lines[0].startswith("#!"):
            new_lines.append(lines[0])
            idx = 1
        new_lines.append(f"# DOC_LINK: {doc_id}")
        new_lines.extend(lines[idx:])
        result = "\n".join(new_lines)
        if content.endswith("\n"):
            result += "\n"
        return result

    # TXT: treat like light markdown
    if file_type == "txt":
        if content.startswith("---\n"):
            lines = content.splitlines()
            end_idx = None
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    end_idx = i
                    break
            if end_idx is not None:
                fm = lines[1:end_idx]
                if any(l.strip().startswith("doc_id:") for l in fm):
                    return content
                new_fm = ["doc_id: " + doc_id] + fm
                new_lines = ["---", *new_fm, "---", *lines[end_idx + 1 :]]
                result = "\n".join(new_lines)
                if content.endswith("\n"):
                    result += "\n"
                return result
        fm = f"---\ndoc_id: {doc_id}\n---\n\n"
        return fm + content

    # Unknown / other: leave unchanged
    return content


# --- Assignment core --------------------------------------------------------


@dataclass
class AssignmentResult:
    path: str
    doc_id: str
    category: str
    name: str
    skipped: bool
    reason: Optional[str] = None


def auto_assign(
    dry_run: bool = True,
    limit: Optional[int] = None,
    include_types: Optional[List[str]] = None,
) -> Dict:
    """
    Assign doc_ids to all inventory entries marked as 'missing'.

    Returns a dict with summary + per-file assignment details.
    """
    inventory = load_inventory()
    registry = DocIDRegistry()
    available_categories = list(registry.data["categories"].keys())

    missing = [e for e in inventory if e.status in ("missing", "invalid")]
    total_missing = len(missing)

    if include_types:
        include_set = set(include_types)
        missing = [e for e in missing if e.file_type in include_set]

    if limit is not None:
        missing = missing[:limit]

    # Emit ASSIGN_STARTED event
    _emit_event(
        subsystem="SUB_DOC_ID",
        step_id="ASSIGN_STARTED",
        subject="doc_id_assigner.auto_assign()",
        summary=f"Starting doc_id assignment to {len(missing)} files (dry_run={dry_run})",
        severity="INFO",
        details={
            "total_files": len(missing),
            "dry_run": dry_run,
            "limit": limit,
            "include_types": include_types
        }
    )

    assignments: List[AssignmentResult] = []
    skipped: List[AssignmentResult] = []

    for idx, entry in enumerate(missing, start=1):
        rel_path = entry.path
        full_path = REPO_ROOT / rel_path

        if not full_path.exists():
            skipped.append(
                AssignmentResult(
                    path=rel_path,
                    doc_id="",
                    category="",
                    name="",
                    skipped=True,
                    reason="File does not exist",
                )
            )
            continue

        category = infer_category(rel_path, available_categories)
        name, title = infer_name_and_title(rel_path, entry.file_type)
        existing_doc_ids = [
            doc["doc_id"]
            for doc in registry.data["docs"]
            if any(a.get("path") == rel_path for a in doc.get("artifacts", []))
        ]
        existing_doc_id = existing_doc_ids[-1] if existing_doc_ids else None

        if dry_run:
            # We just preview what *would* happen
            preview_id = f"DOC-{category.upper()}-{name.upper().replace('_', '-')}-XXX"
            assignments.append(
                AssignmentResult(
                    path=rel_path,
                    doc_id=preview_id,
                    category=category,
                    name=name,
                    skipped=False,
                )
            )
        else:
            artifacts = [{"type": "source", "path": rel_path}]
            new_doc_id = existing_doc_id or registry.mint_doc_id(
                category=category,
                name=name,
                title=title,
                artifacts=artifacts,
                tags=[entry.file_type],
            )

            content = full_path.read_text(encoding="utf-8", errors="ignore")
            new_content = inject_doc_id_into_content(
                content, entry.file_type, new_doc_id
            )
            full_path.write_text(new_content, encoding="utf-8")

            assignments.append(
                AssignmentResult(
                    path=rel_path,
                    doc_id=new_doc_id,
                    category=category,
                    name=name,
                    skipped=False,
                )
            )

            # Emit DOC_ID_ASSIGNED event
            _emit_event(
                subsystem="SUB_DOC_ID",
                step_id="DOC_ID_ASSIGNED",
                subject=rel_path,
                summary=f"Assigned {new_doc_id} to {rel_path}",
                severity="INFO",
                details={
                    "doc_id": new_doc_id,
                    "category": category,
                    "file_type": entry.file_type,
                    "path": rel_path
                }
            )

        # Progress event every 10 files
        if idx % 10 == 0:
            print(f"[INFO] Processed {idx}/{len(missing)} files...")
            _emit_event(
                subsystem="SUB_DOC_ID",
                step_id="ASSIGN_PROGRESS",
                subject="assignment_progress",
                summary=f"Processed {idx}/{len(missing)} files",
                severity="INFO",
                details={
                    "files_processed": idx,
                    "total_files": len(missing),
                    "progress_pct": round(idx / len(missing) * 100, 1),
                    "assignments": len([a for a in assignments if not a.skipped]),
                    "skipped": len(skipped)
                }
            )

    summary = {
        "total_missing_in_inventory": total_missing,
        "processed": len(missing),
        "assigned": len([a for a in assignments if not a.skipped]),
        "skipped": len(skipped),
        "dry_run": dry_run,
        "timestamp": datetime.now().isoformat(),
    }

    # Emit ASSIGN_COMPLETED event
    _emit_event(
        subsystem="SUB_DOC_ID",
        step_id="ASSIGN_COMPLETED",
        subject="doc_id_assigner.auto_assign()",
        summary=f"Assignment completed: {summary['assigned']} files assigned (dry_run={dry_run})",
        severity="NOTICE",
        details=summary
    )

    return {
        "summary": summary,
        "assignments": [asdict(a) for a in assignments],
        "skipped": [asdict(s) for s in skipped],
    }


# --- Single File Assignment -------------------------------------------------


def assign_single(file_path: Path, category: str, dry_run: bool = False) -> Dict:
    """
    Assign doc_id to a single file.
    
    Args:
        file_path: Path to file needing doc_id
        category: Category for doc_id (glossary, spec, script, etc.)
        dry_run: If True, preview only
    
    Returns:
        Dict with status and assigned doc_id
    """
    if not file_path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "doc_id": None
        }
    
    # Check if already has doc_id
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        existing = re.search(r'DOC-[A-Z]+-[A-Z0-9-]+-[0-9]+', content)
        if existing:
            return {
                "success": True,
                "doc_id": existing.group(0),
                "message": f"File already has doc_id: {existing.group(0)}",
                "assigned": False
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Could not read file: {e}",
            "doc_id": None
        }
    
    # Load registry
    registry = DocIDRegistry()
    
    # Verify category exists
    if category not in registry.data["categories"]:
        return {
            "success": False,
            "error": f"Unknown category: {category}. Available: {list(registry.data['categories'].keys())}",
            "doc_id": None
        }
    
    # Generate doc_id
    try:
        name = file_path.stem.replace('_', '-').replace(' ', '-').upper()
        title = file_path.name
        
        doc_id = registry.mint_doc_id(
            category=category,
            name=name,
            title=title
        )
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to mint doc_id: {e}",
            "doc_id": None
        }
    
    if dry_run:
        return {
            "success": True,
            "doc_id": doc_id,
            "message": "Dry run - would assign doc_id",
            "assigned": False,
            "dry_run": True
        }
    
    # Inject doc_id
    try:
        file_type = file_path.suffix.lstrip('.')
        new_content = inject_doc_id_into_content(content, file_type, doc_id)

        file_path.write_text(new_content, encoding='utf-8')

        # Emit DOC_ID_ASSIGNED event
        _emit_event(
            subsystem="SUB_DOC_ID",
            step_id="DOC_ID_ASSIGNED",
            subject=str(file_path),
            summary=f"Assigned {doc_id} to {file_path.name}",
            severity="INFO",
            details={
                "doc_id": doc_id,
                "category": category,
                "file_type": file_type,
                "path": str(file_path)
            }
        )

        return {
            "success": True,
            "doc_id": doc_id,
            "message": f"Assigned {doc_id}",
            "assigned": True
        }
    except Exception as e:
        # Emit assignment failure event
        _emit_event(
            subsystem="SUB_DOC_ID",
            step_id="ASSIGN_FAILED",
            subject=str(file_path),
            summary=f"Failed to assign doc_id to {file_path.name}: {e}",
            severity="ERROR",
            details={
                "error": str(e),
                "path": str(file_path)
            }
        )

        return {
            "success": False,
            "error": f"Failed to inject doc_id: {e}",
            "doc_id": doc_id
        }


def auto_assign_staged(
    input_file: Path,
    staging_area,
    run_id: str,
    batch_size: int = 50,
) -> Dict:
    """
    Assign doc_ids with staging (Phase 3 optimization).
    
    No immediate writes - all operations staged for atomic commit.
    
    Args:
        input_file: Path to missing.json from scanner
        staging_area: StagingArea instance
        run_id: Unique run identifier
        batch_size: Number of files to process per batch
        
    Returns:
        Dictionary with staging statistics
    """
    from common.staging import StagingArea
    
    # Load missing files list
    if not input_file.exists():
        return {"error": f"Input file not found: {input_file}"}
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    missing_files = data.get("files", [])
    
    if not missing_files:
        return {"message": "No missing files to process", "count": 0}
    
    # Initialize registry
    registry = DocIDRegistry()
    available_categories = list(registry.data["categories"].keys())
    
    # Create staging run
    staging_area.create_run(run_id, {
        "type": "doc_id_assignment",
        "source": str(input_file),
        "total_files": len(missing_files)
    })
    
    staged_count = 0
    skipped_count = 0
    
    # Process files
    for file_entry in missing_files[:batch_size]:
        rel_path = file_entry["path"]
        full_path = REPO_ROOT / rel_path
        
        if not full_path.exists():
            skipped_count += 1
            staging_area.stage_operation(run_id, {
                "type": "skip",
                "path": rel_path,
                "reason": "File does not exist"
            })
            continue
        
        # Infer category and name
        category = infer_category(rel_path, available_categories)
        name, _ = infer_name_and_title(rel_path, file_entry.get("ext", "").lstrip("."))
        
        # Mint doc_id
        doc_id = registry.mint_doc_id(category, name)
        
        # Load and patch file content
        try:
            content = full_path.read_text(encoding="utf-8")
            file_type = full_path.suffix.lstrip(".")
            patched_content = inject_doc_id_into_content(content, file_type, doc_id)
            
            # Stage operation
            staging_area.stage_operation(run_id, {
                "type": "patch",
                "action": "assign_doc_id",
                "path": rel_path,
                "doc_id": doc_id,
                "staged_content": patched_content
            })
            
            staged_count += 1
            
        except Exception as e:
            skipped_count += 1
            staging_area.stage_operation(run_id, {
                "type": "skip",
                "path": rel_path,
                "reason": f"Error: {e}"
            })
    
    return {
        "run_id": run_id,
        "staged": staged_count,
        "skipped": skipped_count,
        "total": len(missing_files),
        "status": "staged"
    }


# --- CLI --------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auto-assign doc_ids to files based on docs_inventory.jsonl"
    )
    subparsers = parser.add_subparsers(dest="command")

    assign_parser = subparsers.add_parser(
        "auto-assign",
        help="Assign doc_ids to files that are missing them",
    )
    assign_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview assignments without modifying files or registry",
    )
    assign_parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of files processed (for testing)",
    )
    assign_parser.add_argument(
        "--types",
        nargs="+",
        help="Limit to specific file types (e.g. py md yaml json ps1 sh txt)",
    )
    assign_parser.add_argument(
        "--report",
        type=Path,
        help="Optional JSON file to write a detailed report",
    )
    
    # Single file assignment
    single_parser = subparsers.add_parser(
        "single",
        help="Assign doc_id to a single file",
    )
    single_parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to file needing doc_id",
    )
    single_parser.add_argument(
        "--category",
        type=str,
        required=True,
        help="Category for doc_id (glossary, spec, script, etc.)",
    )
    single_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview assignment without modifying file",
    )

    args = parser.parse_args()

    if args.command == "auto-assign":
        result = auto_assign(
            dry_run=args.dry_run,
            limit=args.limit,
            include_types=args.types,
        )
        summary = result["summary"]

        print("\n=== DOC_ID AUTO-ASSIGN REPORT ===")
        print(f"Total missing in inventory: {summary['total_missing_in_inventory']}")
        print(f"Processed in this run:      {summary['processed']}")
        print(f"Assigned:                   {summary['assigned']}")
        print(f"Skipped:                    {summary['skipped']}")
        print(f"Dry run:                    {summary['dry_run']}")
        print(f"Timestamp:                  {summary['timestamp']}")

        if args.report:
            args.report.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(f"\n[OK] Detailed report written to {args.report}")

        # Non-zero exit if anything was skipped so you see it in CI if you choose
        return 0 if summary["skipped"] == 0 else 1
    
    elif args.command == "single":
        result = assign_single(
            file_path=args.file,
            category=args.category,
            dry_run=args.dry_run
        )
        
        if result["success"]:
            if result.get("assigned"):
                print(f"✅ Assigned {result['doc_id']} to {args.file.name}")
            else:
                print(f"ℹ️  {result.get('message', 'No action taken')}")
            return 0
        else:
            print(f"❌ {result.get('error', 'Unknown error')}")
            return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
