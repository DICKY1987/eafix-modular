# doc_id: DOC-AUTOOPS-007
"""Policy gate for file classification and contract enforcement."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Dict, Optional

import structlog

from repo_autoops.models.contracts import FileClassification, ModuleContract

__doc_id__ = "DOC-AUTOOPS-007"

logger = structlog.get_logger(__name__)


class PolicyGate:
    """Enforce module contracts and classify files."""

    def __init__(self, contracts: Dict[str, ModuleContract]):
        """Initialize policy gate.

        Args:
            contracts: Module contracts by module_id
        """
        self.contracts = contracts
        logger.info("policy_gate_initialized", contract_count=len(contracts))

    def find_module_for_path(self, path: Path) -> Optional[str]:
        """Find module that owns a path.

        Args:
            path: File path

        Returns:
            Module ID or None
        """
        for module_id, contract in self.contracts.items():
            if self._is_under_root(path, contract.root):
                return module_id
        return None

    def _is_under_root(self, path: Path, root: Path) -> bool:
        """Check if path is under root.

        Args:
            path: File path
            root: Root path

        Returns:
            True if path is under root
        """
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    def _matches_pattern(self, path: Path, pattern: str) -> bool:
        """Check if path matches pattern.

        Args:
            path: File path
            pattern: Glob pattern

        Returns:
            True if matches
        """
        path_str = str(path)
        return fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path_str, f"*{pattern}")

    def classify_file(self, path: Path) -> FileClassification:
        """Classify a file according to contracts.

        Args:
            path: File path

        Returns:
            FileClassification
        """
        module_id = self.find_module_for_path(path)

        if not module_id:
            logger.warning("no_module_found", path=str(path))
            return FileClassification(
                classification="quarantine",
                reason="No module contract found for path",
                suggested_action="Create module contract or move file",
            )

        contract = self.contracts[module_id]

        # Check forbidden patterns first
        for pattern in contract.forbidden_patterns:
            if self._matches_pattern(path, pattern):
                logger.warning(
                    "forbidden_file",
                    path=str(path),
                    pattern=pattern,
                    module=module_id,
                )
                return FileClassification(
                    classification="quarantine",
                    reason=f"Matches forbidden pattern: {pattern}",
                    matched_pattern=pattern,
                    suggested_action="Remove file or update contract",
                )

        # Check canonical allowlist
        for pattern in contract.canonical_allowlist:
            if self._matches_pattern(path, pattern):
                logger.debug(
                    "canonical_file",
                    path=str(path),
                    pattern=pattern,
                    module=module_id,
                )
                return FileClassification(
                    classification="canonical",
                    reason="Matches canonical allowlist",
                    matched_pattern=pattern,
                    suggested_action="Stage and commit",
                )

        # Check generated patterns
        for pattern in contract.generated_patterns:
            if self._matches_pattern(path, pattern):
                logger.debug(
                    "generated_file",
                    path=str(path),
                    pattern=pattern,
                    module=module_id,
                )
                return FileClassification(
                    classification="generated",
                    reason="Matches generated pattern",
                    matched_pattern=pattern,
                    suggested_action="Move to _generated or ignore",
                )

        # Check run artifacts
        for pattern in contract.run_artifact_patterns:
            if self._matches_pattern(path, pattern):
                logger.debug(
                    "run_artifact",
                    path=str(path),
                    pattern=pattern,
                    module=module_id,
                )
                return FileClassification(
                    classification="run_artifact",
                    reason="Matches run artifact pattern",
                    matched_pattern=pattern,
                    suggested_action="Ignore or add to gitignore",
                )

        # Default: quarantine unknown files
        logger.warning("unclassified_file", path=str(path), module=module_id)
        return FileClassification(
            classification="quarantine",
            reason="Not in any allowlist",
            suggested_action="Add to contract or move to quarantine",
        )

    def enforce_contract(self, module_id: str) -> Dict[str, list]:
        """Check contract compliance for a module.

        Args:
            module_id: Module identifier

        Returns:
            Dict with 'missing', 'unexpected', 'forbidden' lists
        """
        if module_id not in self.contracts:
            logger.error("contract_not_found", module_id=module_id)
            return {"missing": [], "unexpected": [], "forbidden": []}

        contract = self.contracts[module_id]
        root = contract.root

        if not root.exists():
            logger.error("root_not_found", module_id=module_id, root=str(root))
            return {"missing": contract.required_paths, "unexpected": [], "forbidden": []}

        # Check required paths
        missing = []
        for req_path in contract.required_paths:
            full_path = root / req_path
            if not full_path.exists():
                missing.append(req_path)

        # Scan for unexpected files
        unexpected = []
        forbidden = []
        
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue

            classification = self.classify_file(file_path)

            if classification.classification == "quarantine":
                if classification.matched_pattern in contract.forbidden_patterns:
                    forbidden.append(str(file_path.relative_to(root)))
                else:
                    unexpected.append(str(file_path.relative_to(root)))

        logger.info(
            "contract_enforced",
            module_id=module_id,
            missing_count=len(missing),
            unexpected_count=len(unexpected),
            forbidden_count=len(forbidden),
        )

        return {
            "missing": missing,
            "unexpected": unexpected,
            "forbidden": forbidden,
        }
