#!/usr/bin/env python3
"""
Doc ID Coverage Provider

Provides real-time coverage metrics for GUI panels and dashboards.

PURPOSE: Calculate and expose coverage metrics from registry and file scans
PATTERN: PATTERN-DOC-ID-COVERAGE-PROVIDER-001

Integration Points:
- SUB_GUI/src/gui_app/panels/doc_id_coverage_panel.py
- Event system for real-time updates
- Registry V3 for data queries
"""
# DOC_ID: DOC-CORE-SUB-DOC-ID-COMMON-COVERAGE-PROVIDER-1115

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, ELIGIBLE_PATTERNS, EXCLUDE_PATTERNS
from common.registry import Registry
from common.rules import validate_doc_id
import re


@dataclass
class CoverageByType:
    """Coverage metrics for a specific file type."""
    file_type: str
    total_files: int
    covered_files: int
    coverage_pct: float


@dataclass
class CoverageByRule:
    """Coverage metrics for a specific validation rule."""
    rule_name: str
    files_checked: int
    files_passed: int
    compliance_pct: float


@dataclass
class CoverageMetrics:
    """Complete coverage metrics for Doc ID system."""
    overall_percentage: float
    compliance_state: str  # "compliant" | "non-compliant" | "partial"
    total_files: int
    covered_files: int
    by_file_type: Dict[str, CoverageByType]
    by_rule: Dict[str, CoverageByRule]
    last_updated: str


class DocIDCoverageProvider:
    """
    Provides real-time coverage metrics for Doc ID system.

    Queries registry and file system to calculate:
    - Overall coverage percentage
    - Coverage by file type (.py, .yaml, .json, etc.)
    - Coverage by validation rule (ID present, registry entry, metadata complete)
    - Compliance state

    Usage:
        provider = DocIDCoverageProvider()
        metrics = provider.get_coverage_metrics()

        print(f"Overall Coverage: {metrics.overall_percentage}%")
        print(f"Compliance State: {metrics.compliance_state}")

        # By file type
        for file_type, coverage in metrics.by_file_type.items():
            print(f"{file_type}: {coverage.coverage_pct}%")
    """

    def __init__(self, repo_root: Path = REPO_ROOT):
        """
        Initialize coverage provider.

        Args:
            repo_root: Repository root path
        """
        self.repo_root = repo_root
        self.registry = Registry()

    def _should_scan_file(self, file_path: Path) -> bool:
        """Check if file should be scanned for doc_id."""
        try:
            rel_path = file_path.relative_to(self.repo_root)
            rel_path_str = str(rel_path)

            # Check exclude patterns
            for pattern in EXCLUDE_PATTERNS:
                if pattern in rel_path_str:
                    return False

            return True
        except ValueError:
            return False

    def _scan_files_by_type(self) -> Dict[str, List[Path]]:
        """
        Scan repository and group files by type.

        Returns:
            Dict mapping file extension to list of file paths
        """
        files_by_type: Dict[str, List[Path]] = {}

        for pattern in ELIGIBLE_PATTERNS:
            for file_path in self.repo_root.glob(pattern):
                if not file_path.is_file():
                    continue

                if not self._should_scan_file(file_path):
                    continue

                file_ext = file_path.suffix.lstrip('.')
                if not file_ext:
                    file_ext = "other"

                if file_ext not in files_by_type:
                    files_by_type[file_ext] = []

                files_by_type[file_ext].append(file_path)

        return files_by_type

    def _has_doc_id(self, file_path: Path) -> bool:
        """Check if file contains a valid doc_id."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            # Search for DOC_ID or DOC_LINK pattern
            match = re.search(r'DOC_(ID|LINK):\s*(DOC-[A-Z0-9-]+)', content)

            if match:
                doc_id = match.group(2)
                return validate_doc_id(doc_id)

            return False
        except Exception:
            return False

    def _get_coverage_by_type(self, files_by_type: Dict[str, List[Path]]) -> Dict[str, CoverageByType]:
        """Calculate coverage metrics by file type."""
        coverage_by_type: Dict[str, CoverageByType] = {}

        for file_type, files in files_by_type.items():
            total = len(files)
            covered = sum(1 for f in files if self._has_doc_id(f))
            coverage_pct = (covered / total * 100) if total > 0 else 0

            coverage_by_type[file_type] = CoverageByType(
                file_type=file_type,
                total_files=total,
                covered_files=covered,
                coverage_pct=round(coverage_pct, 1)
            )

        return coverage_by_type

    def _get_coverage_by_rule(self, files_by_type: Dict[str, List[Path]]) -> Dict[str, CoverageByRule]:
        """Calculate coverage metrics by validation rule."""
        all_files = []
        for files in files_by_type.values():
            all_files.extend(files)

        total_files = len(all_files)

        # Rule 1: ID Present (file has DOC_ID or DOC_LINK)
        files_with_id = sum(1 for f in all_files if self._has_doc_id(f))
        id_present_pct = (files_with_id / total_files * 100) if total_files > 0 else 0

        # Rule 2: Registry Entry (file has entry in registry)
        files_in_registry = self._count_files_in_registry(all_files)
        registry_pct = (files_in_registry / total_files * 100) if total_files > 0 else 0

        # Rule 3: Metadata Complete (registry entry has complete metadata)
        files_complete_metadata = self._count_files_with_complete_metadata(all_files)
        metadata_pct = (files_complete_metadata / total_files * 100) if total_files > 0 else 0

        return {
            "ID Present": CoverageByRule(
                rule_name="ID Present",
                files_checked=total_files,
                files_passed=files_with_id,
                compliance_pct=round(id_present_pct, 1)
            ),
            "Registry Entry": CoverageByRule(
                rule_name="Registry Entry",
                files_checked=total_files,
                files_passed=files_in_registry,
                compliance_pct=round(registry_pct, 1)
            ),
            "Metadata Complete": CoverageByRule(
                rule_name="Metadata Complete",
                files_checked=total_files,
                files_passed=files_complete_metadata,
                compliance_pct=round(metadata_pct, 1)
            )
        }

    def _count_files_in_registry(self, files: List[Path]) -> int:
        """Count how many files have entries in registry."""
        count = 0

        for file_path in files:
            try:
                rel_path = str(file_path.relative_to(self.repo_root))

                # Check if file is referenced in any doc's artifacts
                for doc in self.registry.data.get("docs", []):
                    artifacts = doc.get("artifacts", [])
                    for artifact in artifacts:
                        if artifact.get("path") == rel_path:
                            count += 1
                            break
            except Exception:
                continue

        return count

    def _count_files_with_complete_metadata(self, files: List[Path]) -> int:
        """Count how many files have complete metadata in registry."""
        count = 0

        for file_path in files:
            try:
                rel_path = str(file_path.relative_to(self.repo_root))

                # Find doc entry for this file
                for doc in self.registry.data.get("docs", []):
                    artifacts = doc.get("artifacts", [])
                    for artifact in artifacts:
                        if artifact.get("path") == rel_path:
                            # Check if metadata is complete
                            if self._is_metadata_complete(doc):
                                count += 1
                            break
            except Exception:
                continue

        return count

    def _is_metadata_complete(self, doc: dict) -> bool:
        """Check if doc entry has complete metadata."""
        # Required fields
        required_fields = ["doc_id", "title", "category"]

        for field in required_fields:
            if not doc.get(field):
                return False

        # Artifacts should exist
        if not doc.get("artifacts"):
            return False

        return True

    def _determine_compliance_state(self, coverage_pct: float) -> str:
        """
        Determine compliance state based on coverage percentage.

        Args:
            coverage_pct: Overall coverage percentage (0-100)

        Returns:
            "compliant" (>= 90%), "partial" (50-90%), or "non-compliant" (< 50%)
        """
        if coverage_pct >= 90:
            return "compliant"
        elif coverage_pct >= 50:
            return "partial"
        else:
            return "non-compliant"

    def get_coverage_metrics(self) -> CoverageMetrics:
        """
        Calculate and return complete coverage metrics.

        Returns:
            CoverageMetrics object with all coverage data
        """
        from datetime import datetime

        # Scan files by type
        files_by_type = self._scan_files_by_type()

        # Calculate total files
        total_files = sum(len(files) for files in files_by_type.values())

        # Calculate covered files
        covered_files = sum(
            1 for files in files_by_type.values()
            for f in files
            if self._has_doc_id(f)
        )

        # Calculate overall percentage
        overall_pct = (covered_files / total_files * 100) if total_files > 0 else 0

        # Calculate coverage by type
        by_file_type = self._get_coverage_by_type(files_by_type)

        # Calculate coverage by rule
        by_rule = self._get_coverage_by_rule(files_by_type)

        # Determine compliance state
        compliance_state = self._determine_compliance_state(overall_pct)

        return CoverageMetrics(
            overall_percentage=round(overall_pct, 1),
            compliance_state=compliance_state,
            total_files=total_files,
            covered_files=covered_files,
            by_file_type=by_file_type,
            by_rule=by_rule,
            last_updated=datetime.utcnow().isoformat() + "Z"
        )


if __name__ == "__main__":
    # Demo usage
    print("Doc ID Coverage Provider - Demo")
    print("=" * 60)

    provider = DocIDCoverageProvider()
    metrics = provider.get_coverage_metrics()

    print(f"\nOverall Coverage: {metrics.overall_percentage}%")
    print(f"Compliance State: {metrics.compliance_state}")
    print(f"Total Files: {metrics.total_files}")
    print(f"Covered Files: {metrics.covered_files}")

    print("\n==> Coverage by File Type:")
    for file_type, coverage in metrics.by_file_type.items():
        print(f"   {file_type:8s}: {coverage.covered_files:4d}/{coverage.total_files:4d} ({coverage.coverage_pct:5.1f}%)")

    print("\n==> Coverage by Validation Rule:")
    for rule_name, coverage in metrics.by_rule.items():
        print(f"   {rule_name:20s}: {coverage.files_passed:4d}/{coverage.files_checked:4d} ({coverage.compliance_pct:5.1f}%)")

    print(f"\nLast Updated: {metrics.last_updated}")
    print("\n" + "=" * 60)
