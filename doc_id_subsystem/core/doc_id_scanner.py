#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_LINK: DOC-SCRIPT-DOC-ID-SCANNER-046
"""
Doc ID Scanner

PURPOSE: Scan repository for doc_id presence and generate inventory
PATTERN: PATTERN-DOC-ID-SCAN-001

USAGE:
    python doc_id_scanner.py --repo-root "../.."
    python doc_id_scanner.py --stats
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Import from local modules
try:
    from config import ELIGIBLE_PATTERNS, EXCLUDE_PATTERNS
    from rules import DOC_ID_REGEX, validate_doc_id
    from utils import save_jsonl, load_jsonl
except ImportError:
    # Fallback for direct execution
    ELIGIBLE_PATTERNS = [
        "**/*.py", "**/*.yaml", "**/*.yml", "**/*.json", "**/*.md",
        "**/*.sh", "**/*.ps1", "**/*.bat", "**/Dockerfile*", "**/*.toml"
    ]
    EXCLUDE_PATTERNS = [
        ".git", ".venv", "venv", "node_modules", "__pycache__",
        "*.pyc", ".aider*", ".claude", "*.db", "*.sqlite"
    ]
    DOC_ID_REGEX = re.compile(r'DOC-[A-Z]+-\d{3,4}')
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


class DocIDScanner:
    """Scan repository for doc_id presence."""


    def __init__(self, repo_root: Path = None):
        if repo_root is None:
            # Default to parent parent of core directory (eafix-modular root)
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)
        self.inventory: List[Dict] = []
        self.inventory_path = self.repo_root / "doc_id_subsystem" / "registry" / "docs_inventory.jsonl"

    def is_excluded(self, path: Path) -> bool:
        """Check if path should be excluded."""
        path_str = str(path.relative_to(self.repo_root))

        for pattern in EXCLUDE_PATTERNS:
            if pattern in path_str:
                return True

        return False

    def extract_doc_id_python(self, content: str) -> Optional[str]:
        """Extract doc_id from Python file."""
        # Look for DOC_ID: or DOC_LINK: in first 50 lines
        lines = content.split("\n")[:50]

        for line in lines:
            # Module docstring: DOC_ID: DOC-...
            match = re.search(r"DOC_ID:\s*(DOC-[A-Z0-9-]+)", line)
            if match:
                return match.group(1)

            # Test header: # DOC_LINK: DOC-...
            match = re.search(r"DOC_LINK:\s*(DOC-[A-Z0-9-]+)", line)
            if match:
                return match.group(1)

        return None

    def extract_doc_id_markdown(self, content: str) -> Optional[str]:
        """Extract doc_id from Markdown YAML frontmatter."""
        # Look for YAML frontmatter
        if not content.startswith("---"):
            return None

        # Find closing ---
        lines = content.split("\n")
        if len(lines) < 3:
            return None

        frontmatter_end = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                frontmatter_end = i
                break

        if not frontmatter_end:
            return None

        # Parse frontmatter
        frontmatter = "\n".join(lines[1:frontmatter_end])
        match = re.search(r'doc_id:\s*["\']?(DOC-[A-Z0-9-]+)["\']?', frontmatter)
        if match:
            return match.group(1)

        return None

    def extract_doc_id_yaml(self, content: str) -> Optional[str]:
        """Extract doc_id from YAML file."""
        # Look for top-level doc_id field
        lines = content.split("\n")[:20]

        for line in lines:
            match = re.search(r'^doc_id:\s*["\']?(DOC-[A-Z0-9-]+)["\']?', line)
            if match:
                return match.group(1)

        return None

    def extract_doc_id_json(self, content: str) -> Optional[str]:
        """Extract doc_id from JSON file."""
        # Support header comments for non-object JSON payloads
        for line in content.split("\n")[:10]:
            match = re.search(r"DOC_ID:\s*(DOC-[A-Z0-9-]+)", line)
            if match:
                return match.group(1)

        try:
            data = json.loads(content)
            if isinstance(data, dict) and "doc_id" in data:
                return data["doc_id"]
        except json.JSONDecodeError:
            pass

        return None

    def extract_doc_id_script(self, content: str) -> Optional[str]:
        """Extract doc_id from script file (PowerShell, Bash)."""
        # Look for # DOC_LINK: in first 20 lines
        lines = content.split("\n")[:20]

        for line in lines:
            match = re.search(r"DOC_LINK:\s*(DOC-[A-Z0-9-]+)", line)
            if match:
                return match.group(1)

        return None

    def extract_doc_id(self, file_path: Path) -> Optional[str]:
        """Extract doc_id from file based on type."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"[WARN] Could not read {file_path}: {e}")
            return None

        suffix = file_path.suffix.lower()

        if suffix == ".py":
            return self.extract_doc_id_python(content)
        elif suffix == ".md":
            return self.extract_doc_id_markdown(content)
        elif suffix in [".yaml", ".yml"]:
            return self.extract_doc_id_yaml(content)
        elif suffix == ".json":
            return self.extract_doc_id_json(content)
        elif suffix in [".ps1", ".sh"]:
            return self.extract_doc_id_script(content)
        elif suffix == ".txt":
            # Try markdown frontmatter first, then YAML
            doc_id = self.extract_doc_id_markdown(content)
            if doc_id:
                return doc_id
            return self.extract_doc_id_yaml(content)

        return None

    def validate_doc_id_local(self, doc_id: str) -> bool:
        """Validate doc_id format."""
        if not doc_id:
            return False
        # Simple validation: DOC-CATEGORY-NUMBER format
        match = DOC_ID_REGEX.match(doc_id)
        return match is not None

    def scan_file(self, file_path: Path) -> Dict:
        """Scan a single file for doc_id."""
        rel_path = file_path.relative_to(self.repo_root)

        doc_id = self.extract_doc_id(file_path)

        if doc_id:
            valid = self.validate_doc_id_local(doc_id)
            status = "registered" if valid else "invalid"
        else:
            valid = False
            status = "missing"

        return {
            "path": str(rel_path).replace("\\", "/"),
            "doc_id": doc_id,
            "status": status,
            "file_type": file_path.suffix[1:] if file_path.suffix else "unknown",
            "last_modified": datetime.fromtimestamp(
                file_path.stat().st_mtime
            ).isoformat(),
            "scanned_at": datetime.now().isoformat(),
        }

    def scan_repository_incremental(self, index_store, run_id: str) -> List[Dict]:
        """
        Scan repository incrementally using index cache.

        Phase 2 optimization: Only re-scans files when mtime/size changes.
        Target: < 10 seconds for unchanged repositories.

        Args:
            index_store: IndexStore instance for caching
            run_id: Unique identifier for this scan run

        Returns:
            List of inventory entries
        """
        from common.index_store import detect_language, compute_file_hash

        print(f"[INFO] Incremental scan starting (run_id: {run_id})")

        # Emit SCAN_STARTED event
        _emit_event(
            subsystem="SUB_DOC_ID",
            step_id="SCAN_STARTED",
            subject="doc_id_scanner.scan_repository_incremental()",
            summary=f"Starting incremental scan (run_id: {run_id})",
            severity="INFO",
            details={"run_id": run_id, "scan_type": "incremental"}
        )

        stats = {
            "files_scanned": 0,
            "files_changed": 0,
            "cache_hits": 0
        }
        
        # Start scan run tracking
        index_store.start_scan_run(run_id)
        
        # Collect all eligible files
        eligible_files = []
        for pattern in ELIGIBLE_PATTERNS:
            for file_path in self.repo_root.glob(pattern):
                if file_path.is_file() and not self.is_excluded(file_path):
                    eligible_files.append(file_path)
        
        print(f"[INFO] Found {len(eligible_files)} eligible files")
        
        # Scan with cache
        self.inventory = []
        existing_paths = set()
        
        for i, file_path in enumerate(eligible_files, start=1):
            if i % 100 == 0:
                print(f"[INFO] Progress: {i}/{len(eligible_files)} files ({stats['cache_hits']} cache hits)...")
                # Emit progress event every 100 files
                _emit_event(
                    subsystem="SUB_DOC_ID",
                    step_id="SCAN_PROGRESS",
                    subject="scan_progress",
                    summary=f"Scanned {i}/{len(eligible_files)} files",
                    severity="INFO",
                    details={
                        "files_scanned": i,
                        "total_files": len(eligible_files),
                        "cache_hits": stats['cache_hits'],
                        "progress_pct": round(i / len(eligible_files) * 100, 1)
                    }
                )

            stats["files_scanned"] += 1
            rel_path = str(file_path.relative_to(self.repo_root)).replace("\\", "/")
            existing_paths.add(rel_path)
            
            # Get current file metadata
            file_stat = file_path.stat()
            mtime_ns = file_stat.st_mtime_ns
            size = file_stat.st_size
            
            # Check cache
            cached = index_store.get_file_state(rel_path)
            
            if cached and cached["mtime_ns"] == mtime_ns and cached["size"] == size:
                # Cache hit - reuse cached data
                stats["cache_hits"] += 1
                entry = {
                    "path": rel_path,
                    "doc_id": cached["doc_id"],
                    "status": "registered" if cached["doc_id"] else "missing",
                    "file_type": cached["ext"][1:] if cached["ext"] else "unknown",
                    "last_modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "scanned_at": datetime.now().isoformat(),
                }
                self.inventory.append(entry)
            else:
                # Cache miss - re-scan file
                stats["files_changed"] += 1
                entry = self.scan_file(file_path)
                self.inventory.append(entry)
                
                # Compute hash only for changed files
                sha256 = compute_file_hash(file_path)
                
                # Update index
                index_store.update_file_state(rel_path, {
                    "ext": file_path.suffix,
                    "lang": detect_language(file_path),
                    "mtime_ns": mtime_ns,
                    "size": size,
                    "sha256": sha256,
                    "doc_id": entry["doc_id"],
                    "doc_id_source": self._detect_doc_id_source(file_path),
                    "parse_status": "ok" if entry["status"] != "invalid" else "parse_error",
                    "last_seen_run_id": run_id
                })
        
        # Cleanup stale entries (deleted files)
        stale_count = index_store.cleanup_stale_entries(existing_paths)
        if stale_count > 0:
            print(f"[INFO] Cleaned up {stale_count} stale index entries")
        
        # Mark scan complete
        index_store.mark_scan_complete(run_id, stats)
        
        # Report stats
        cache_hit_rate = (stats["cache_hits"] / stats["files_scanned"] * 100) if stats["files_scanned"] > 0 else 0
        print(f"[OK] Incremental scan complete:")
        print(f"     Total: {stats['files_scanned']} files")
        print(f"     Changed: {stats['files_changed']} files")
        print(f"     Cache hits: {stats['cache_hits']} ({cache_hit_rate:.1f}%)")

        # Emit SCAN_COMPLETED event
        _emit_event(
            subsystem="SUB_DOC_ID",
            step_id="SCAN_COMPLETED",
            subject="doc_id_scanner.scan_repository_incremental()",
            summary=f"Incremental scan completed: {stats['files_scanned']} files scanned",
            severity="NOTICE",
            details={
                "run_id": run_id,
                "total_files": stats["files_scanned"],
                "files_changed": stats["files_changed"],
                "cache_hits": stats["cache_hits"],
                "cache_hit_rate_pct": round(cache_hit_rate, 1),
                "stale_entries_cleaned": stale_count
            }
        )

        return self.inventory
    
    def _detect_doc_id_source(self, file_path: Path) -> str:
        """Detect where doc_id was found in file."""
        suffix = file_path.suffix.lower()
        if suffix == ".py":
            return "python_comment"
        elif suffix == ".md":
            return "markdown_frontmatter"
        elif suffix in [".yaml", ".yml"]:
            return "yaml_key"
        elif suffix == ".json":
            return "json_key"
        elif suffix in [".ps1", ".sh"]:
            return "script_comment"
        return "unknown"

    def scan_repository(self) -> List[Dict]:
        """Scan entire repository for eligible files (full scan - no cache)."""
        print(f"[INFO] Full scan starting (no cache): {self.repo_root}")

        # Emit SCAN_STARTED event
        _emit_event(
            subsystem="SUB_DOC_ID",
            step_id="SCAN_STARTED",
            subject="doc_id_scanner.scan_repository()",
            summary=f"Starting full scan of {self.repo_root}",
            severity="INFO",
            details={"scan_type": "full", "repo_root": str(self.repo_root)}
        )

        eligible_files = []

        # Collect all eligible files
        for pattern in ELIGIBLE_PATTERNS:
            for file_path in self.repo_root.glob(pattern):
                if file_path.is_file() and not self.is_excluded(file_path):
                    eligible_files.append(file_path)

        print(f"[INFO] Found {len(eligible_files)} eligible files")

        # Scan each file
        self.inventory = []
        for i, file_path in enumerate(eligible_files, start=1):
            if i % 50 == 0:
                print(f"[INFO] Scanned {i}/{len(eligible_files)} files...")
                # Emit progress event every 50 files
                _emit_event(
                    subsystem="SUB_DOC_ID",
                    step_id="SCAN_PROGRESS",
                    subject="scan_progress",
                    summary=f"Scanned {i}/{len(eligible_files)} files",
                    severity="INFO",
                    details={
                        "files_scanned": i,
                        "total_files": len(eligible_files),
                        "progress_pct": round(i / len(eligible_files) * 100, 1)
                    }
                )

            entry = self.scan_file(file_path)
            self.inventory.append(entry)

        print(f"[INFO] Scan complete: {len(self.inventory)} files")

        # Emit SCAN_COMPLETED event
        _emit_event(
            subsystem="SUB_DOC_ID",
            step_id="SCAN_COMPLETED",
            subject="doc_id_scanner.scan_repository()",
            summary=f"Full scan completed: {len(self.inventory)} files scanned",
            severity="NOTICE",
            details={
                "total_files": len(self.inventory),
                "scan_type": "full"
            }
        )

        return self.inventory

    def save_inventory(self, output_path: Path = None):
        """Save inventory to JSONL file."""
        if output_path is None:
            output_path = self.inventory_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            for entry in self.inventory:
                f.write(json.dumps(entry) + '\n')
        print(f"[OK] Inventory saved: {output_path}")

    def load_inventory(self, input_path: Path = None) -> List[Dict]:
        """Load inventory from JSONL file."""
        if input_path is None:
            input_path = self.inventory_path
        if not input_path.exists():
            print(f"[ERROR] Inventory not found: {input_path}")
            sys.exit(1)

        self.inventory = []
        with open(input_path, 'r') as f:
            for line in f:
                if line.strip():
                    self.inventory.append(json.loads(line))
        print(f"[INFO] Loaded {len(self.inventory)} entries from {input_path}")
        return self.inventory

    def get_stats(self) -> Dict:
        """Calculate statistics from inventory."""
        total = len(self.inventory)

        if total == 0:
            return {
                "total": 0,
                "with_id": 0,
                "without_id": 0,
                "invalid": 0,
                "coverage": 0.0,
            }

        with_id = len([e for e in self.inventory if e["status"] == "registered"])
        invalid = len([e for e in self.inventory if e["status"] == "invalid"])
        without_id = len([e for e in self.inventory if e["status"] == "missing"])

        # Stats by file type
        by_type = {}
        for entry in self.inventory:
            ft = entry["file_type"]
            if ft not in by_type:
                by_type[ft] = {"total": 0, "with_id": 0, "without_id": 0}

            by_type[ft]["total"] += 1
            if entry["status"] == "registered":
                by_type[ft]["with_id"] += 1
            elif entry["status"] == "missing":
                by_type[ft]["without_id"] += 1

        return {
            "total": total,
            "with_id": with_id,
            "without_id": without_id,
            "invalid": invalid,
            "coverage": with_id / total if total > 0 else 0.0,
            "by_type": by_type,
        }

    def print_stats(self):
        """Print statistics to console."""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("DOC_ID COVERAGE STATISTICS")
        print("=" * 60)
        print(f"Total eligible files:    {stats['total']}")
        print(f"Files with doc_id:       {stats['with_id']} ({stats['coverage']:.1%})")
        print(f"Files without doc_id:    {stats['without_id']}")
        print(f"Files with invalid ID:   {stats['invalid']}")
        print(f"\nCoverage: {stats['coverage']:.1%}")

        print("\nBy file type:")
        print("-" * 60)
        for ft, counts in sorted(stats["by_type"].items()):
            cov = counts["with_id"] / counts["total"] if counts["total"] > 0 else 0.0
            print(
                f"  {ft:10s}  {counts['with_id']:3d} / {counts['total']:3d}  ({cov:6.1%})"
            )
        print("=" * 60 + "\n")

    def generate_markdown_report(self) -> str:
        """Generate Markdown coverage report."""
        stats = self.get_stats()

        report = f"""# Doc ID Coverage Report
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Repository**: {self.repo_root}

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Files** | {stats['total']} |
| **With doc_id** | {stats['with_id']} ({stats['coverage']:.1%}) |
| **Without doc_id** | {stats['without_id']} |
| **Invalid doc_id** | {stats['invalid']} |
| **Coverage** | **{stats['coverage']:.1%}** |

---

## Coverage by File Type

| File Type | With ID | Total | Coverage |
|-----------|---------|-------|----------|
"""

        for ft, counts in sorted(
            stats["by_type"].items(), key=lambda x: x[1]["total"], reverse=True
        ):
            cov = counts["with_id"] / counts["total"] if counts["total"] > 0 else 0.0
            report += (
                f"| {ft} | {counts['with_id']} | {counts['total']} | {cov:.1%} |\n"
            )

        # Files without doc_id
        missing = [e for e in self.inventory if e["status"] == "missing"]

        if missing:
            report += f"\n---\n\n## Files Without doc_id ({len(missing)})\n\n"

            # Group by file type
            missing_by_type = {}
            for entry in missing:
                ft = entry["file_type"]
                if ft not in missing_by_type:
                    missing_by_type[ft] = []
                missing_by_type[ft].append(entry["path"])

            for ft, paths in sorted(missing_by_type.items()):
                report += f"\n### {ft.upper()} Files ({len(paths)})\n\n"
                for path in sorted(paths)[:20]:  # Show first 20
                    report += f"- `{path}`\n"

                if len(paths) > 20:
                    report += f"\n_... and {len(paths) - 20} more_\n"

        # Invalid doc_ids
        invalid = [e for e in self.inventory if e["status"] == "invalid"]

        if invalid:
            report += f"\n---\n\n## Files with Invalid doc_id ({len(invalid)})\n\n"
            for entry in invalid:
                report += f"- `{entry['path']}`: `{entry['doc_id']}`\n"

        report += "\n---\n\n**Next Steps:**\n"
        if stats["without_id"] > 0:
            report += f"1. Run auto-assigner: `python scripts/doc_id_assigner.py auto-assign --dry-run`\n"
            report += f"2. Review proposed changes\n"
            report += f"3. Execute: `python scripts/doc_id_assigner.py auto-assign`\n"
        else:
            report += "✅ **100% coverage achieved!**\n"

        return report


def main():
    parser = argparse.ArgumentParser(description="Scan repository for doc_id presence")
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Repository root path (default: auto-detect)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics only (no scan)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for inventory (default: auto-detect)",
    )

    args = parser.parse_args()

    scanner = DocIDScanner(repo_root=args.repo_root)
    
    if args.stats:
        # Load existing inventory and show stats
        scanner.load_inventory(scanner.inventory_path)
        scanner.print_stats()
    else:
        # Perform full scan
        print(f"Scanning repository: {scanner.repo_root}")
        scanner.scan_repository()
        
        # Save inventory
        output = args.output or scanner.inventory_path
        scanner.save_inventory(output)
        
        # Show stats
        scanner.print_stats()


if __name__ == "__main__":
    main()

