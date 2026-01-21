# doc_id: DOC-AUTOOPS-009
"""Identity pipeline for assigning 16-digit prefixes and doc_ids."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog

from repo_autoops.models.results import OperationResult

__doc_id__ = "DOC-AUTOOPS-009"

logger = structlog.get_logger(__name__)


class IdentityPipeline:
    """Assign 16-digit prefixes and doc_ids to files."""

    def __init__(self, mode: str = "draft", dry_run: bool = True):
        """Initialize identity pipeline.

        Args:
            mode: 'draft' or 'auto-commit'
            dry_run: If True, don't modify files
        """
        self.mode = mode
        self.dry_run = dry_run
        logger.info("identity_pipeline_initialized", mode=mode, dry_run=dry_run)

    def generate_prefix(self) -> str:
        """Generate 16-digit timestamp prefix.

        Returns:
            16-digit prefix (YYYYMMDDHHmmssff)
        """
        now = datetime.utcnow()
        prefix = now.strftime("%Y%m%d%H%M%S") + f"{now.microsecond // 10000:02d}"
        return prefix

    def has_prefix(self, path: Path) -> bool:
        """Check if file already has a prefix.

        Args:
            path: File path

        Returns:
            True if has prefix
        """
        # Check filename
        name = path.stem
        if re.match(r"^\d{16}_", name):
            return True

        # Check file content for doc_id
        if path.suffix in [".py", ".md", ".txt"]:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                if re.search(r"#\s*doc_id:\s*DOC-\w+-\d+", content):
                    return True
                if re.search(r"__doc_id__\s*=\s*['\"]DOC-\w+-\d+['\"]", content):
                    return True
            except Exception as e:
                logger.debug("prefix_check_failed", path=str(path), error=str(e))

        return False

    def assign_prefix(self, path: Path) -> OperationResult:
        """Assign prefix to file by renaming.

        Args:
            path: File path

        Returns:
            OperationResult
        """
        if self.has_prefix(path):
            logger.debug("already_has_prefix", path=str(path))
            return OperationResult(
                success=True,
                message="File already has prefix",
                metadata={"action": "skipped", "path": str(path)},
            )

        prefix = self.generate_prefix()
        new_name = f"{prefix}_{path.name}"
        new_path = path.parent / new_name

        if new_path.exists():
            logger.warning("target_exists", path=str(path), target=str(new_path))
            return OperationResult(
                success=False,
                message="Target file already exists",
                error=f"File {new_path} exists",
            )

        if self.dry_run:
            logger.info(
                "prefix_assigned_dry_run",
                old_path=str(path),
                new_path=str(new_path),
            )
            return OperationResult(
                success=True,
                message=f"[DRY RUN] Would rename to {new_name}",
                metadata={"old_path": str(path), "new_path": str(new_path), "dry_run": True},
            )

        try:
            path.rename(new_path)
            logger.info("prefix_assigned", old_path=str(path), new_path=str(new_path))
            return OperationResult(
                success=True,
                message=f"Renamed to {new_name}",
                metadata={"old_path": str(path), "new_path": str(new_path)},
            )
        except Exception as e:
            logger.error("rename_failed", path=str(path), error=str(e))
            return OperationResult(
                success=False,
                message="Failed to rename file",
                error=str(e),
            )

    def assign_doc_id(self, path: Path, doc_id: str) -> OperationResult:
        """Assign doc_id to file by adding header comment.

        Args:
            path: File path
            doc_id: Doc ID to assign

        Returns:
            OperationResult
        """
        if not path.exists():
            return OperationResult(
                success=False,
                message="File not found",
                error=f"File {path} does not exist",
            )

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error("read_failed", path=str(path), error=str(e))
            return OperationResult(
                success=False,
                message="Failed to read file",
                error=str(e),
            )

        # Check if already has doc_id
        if re.search(r"#\s*doc_id:\s*DOC-\w+-\d+", content):
            logger.debug("already_has_doc_id", path=str(path))
            return OperationResult(
                success=True,
                message="File already has doc_id",
                metadata={"action": "skipped", "path": str(path)},
            )

        # Add doc_id based on file type
        if path.suffix == ".py":
            header = f"# doc_id: {doc_id}\n"
            new_content = header + content
        elif path.suffix in [".md", ".txt"]:
            header = f"<!-- doc_id: {doc_id} -->\n\n"
            new_content = header + content
        else:
            return OperationResult(
                success=False,
                message="Unsupported file type for doc_id",
                error=f"File type {path.suffix} not supported",
            )

        if self.dry_run:
            logger.info("doc_id_assigned_dry_run", path=str(path), doc_id=doc_id)
            return OperationResult(
                success=True,
                message=f"[DRY RUN] Would add doc_id {doc_id}",
                metadata={"path": str(path), "doc_id": doc_id, "dry_run": True},
            )

        try:
            path.write_text(new_content, encoding="utf-8")
            logger.info("doc_id_assigned", path=str(path), doc_id=doc_id)
            return OperationResult(
                success=True,
                message=f"Added doc_id {doc_id}",
                metadata={"path": str(path), "doc_id": doc_id},
            )
        except Exception as e:
            logger.error("write_failed", path=str(path), error=str(e))
            return OperationResult(
                success=False,
                message="Failed to write file",
                error=str(e),
            )

    def process_file(self, path: Path, doc_id: Optional[str] = None) -> OperationResult:
        """Process file: assign prefix and optionally doc_id.

        Args:
            path: File path
            doc_id: Optional doc_id to assign

        Returns:
            OperationResult
        """
        # First assign prefix if needed
        prefix_result = self.assign_prefix(path)

        # Get the new path if renamed
        if prefix_result.success and prefix_result.metadata:
            new_path_str = prefix_result.metadata.get("new_path")
            if new_path_str:
                path = Path(new_path_str)

        # Then assign doc_id if provided
        if doc_id:
            doc_id_result = self.assign_doc_id(path, doc_id)
            if not doc_id_result.success:
                return doc_id_result

        return prefix_result
