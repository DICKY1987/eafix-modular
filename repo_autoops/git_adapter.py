# doc_id: DOC-AUTOOPS-008
"""Git adapter with safety preconditions and operations."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

import structlog

from repo_autoops.models.results import OperationResult

__doc_id__ = "DOC-AUTOOPS-008"

logger = structlog.get_logger(__name__)


class GitAdapter:
    """Safe Git operations with precondition checks."""

    def __init__(self, repo_root: Path, dry_run: bool = True):
        """Initialize Git adapter.

        Args:
            repo_root: Repository root directory
            dry_run: If True, log but don't execute Git commands
        """
        self.repo_root = repo_root
        self.dry_run = dry_run
        logger.info("git_adapter_initialized", repo_root=str(repo_root), dry_run=dry_run)

    def _run_git(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command.

        Args:
            args: Git command arguments
            check: Whether to check return code

        Returns:
            CompletedProcess
        """
        cmd = ["git", "-C", str(self.repo_root)] + args
        
        if self.dry_run:
            logger.info("dry_run_git", command=" ".join(cmd))
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="[DRY RUN]", stderr=""
            )

        logger.debug("git_command", command=" ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
        )
        return result

    def check_clean_tree(self) -> bool:
        """Check if working tree is clean.

        Returns:
            True if clean
        """
        try:
            result = self._run_git(["status", "--porcelain"])
            clean = len(result.stdout.strip()) == 0
            logger.debug("clean_tree_check", clean=clean)
            return clean
        except subprocess.CalledProcessError as e:
            logger.error("clean_tree_check_failed", error=str(e))
            return False

    def get_current_branch(self) -> Optional[str]:
        """Get current branch name.

        Returns:
            Branch name or None
        """
        try:
            result = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
            branch = result.stdout.strip()
            logger.debug("current_branch", branch=branch)
            return branch
        except subprocess.CalledProcessError as e:
            logger.error("branch_check_failed", error=str(e))
            return None

    def stage_files(self, paths: List[Path]) -> OperationResult:
        """Stage files for commit.

        Args:
            paths: File paths to stage

        Returns:
            OperationResult
        """
        if not paths:
            return OperationResult(
                success=False,
                message="No files to stage",
            )

        try:
            path_strs = [str(p) for p in paths]
            result = self._run_git(["add"] + path_strs)

            logger.info("files_staged", count=len(paths), dry_run=self.dry_run)

            return OperationResult(
                success=True,
                message=f"Staged {len(paths)} files",
                output=result.stdout,
                metadata={"file_count": len(paths), "dry_run": self.dry_run},
            )
        except subprocess.CalledProcessError as e:
            logger.error("stage_failed", error=str(e))
            return OperationResult(
                success=False,
                message="Failed to stage files",
                error=str(e),
            )

    def commit(self, message: str, paths: Optional[List[Path]] = None) -> OperationResult:
        """Create a commit.

        Args:
            message: Commit message
            paths: Optional specific paths to commit

        Returns:
            OperationResult
        """
        try:
            args = ["commit", "-m", message]
            if paths:
                args.extend([str(p) for p in paths])

            result = self._run_git(args)

            logger.info("commit_created", message=message, dry_run=self.dry_run)

            return OperationResult(
                success=True,
                message="Commit created",
                output=result.stdout,
                metadata={"commit_message": message, "dry_run": self.dry_run},
            )
        except subprocess.CalledProcessError as e:
            logger.error("commit_failed", error=str(e))
            return OperationResult(
                success=False,
                message="Failed to commit",
                error=str(e),
            )

    def pull_rebase(self) -> OperationResult:
        """Pull with rebase.

        Returns:
            OperationResult
        """
        try:
            result = self._run_git(["pull", "--rebase"])

            logger.info("pull_rebase_success", dry_run=self.dry_run)

            return OperationResult(
                success=True,
                message="Pull with rebase successful",
                output=result.stdout,
                metadata={"dry_run": self.dry_run},
            )
        except subprocess.CalledProcessError as e:
            logger.error("pull_rebase_failed", error=str(e))
            return OperationResult(
                success=False,
                message="Pull rebase failed",
                error=str(e),
            )

    def push(self, retry_count: int = 0) -> OperationResult:
        """Push commits to remote.

        Args:
            retry_count: Current retry attempt

        Returns:
            OperationResult
        """
        try:
            result = self._run_git(["push"])

            logger.info("push_success", retry_count=retry_count, dry_run=self.dry_run)

            return OperationResult(
                success=True,
                message="Push successful",
                output=result.stdout,
                metadata={"retry_count": retry_count, "dry_run": self.dry_run},
            )
        except subprocess.CalledProcessError as e:
            logger.error("push_failed", error=str(e), retry_count=retry_count)
            return OperationResult(
                success=False,
                message=f"Push failed (attempt {retry_count + 1})",
                error=str(e),
                metadata={"retry_count": retry_count},
            )

    def create_branch(self, branch_name: str) -> OperationResult:
        """Create and checkout a new branch.

        Args:
            branch_name: Branch name

        Returns:
            OperationResult
        """
        try:
            self._run_git(["checkout", "-b", branch_name])

            logger.info("branch_created", branch=branch_name, dry_run=self.dry_run)

            return OperationResult(
                success=True,
                message=f"Branch {branch_name} created",
                metadata={"branch_name": branch_name, "dry_run": self.dry_run},
            )
        except subprocess.CalledProcessError as e:
            logger.error("branch_create_failed", error=str(e))
            return OperationResult(
                success=False,
                message=f"Failed to create branch {branch_name}",
                error=str(e),
            )

    def get_staged_files(self) -> List[Path]:
        """Get list of staged files.

        Returns:
            List of staged file paths
        """
        try:
            result = self._run_git(["diff", "--cached", "--name-only"])
            files = [
                self.repo_root / line.strip()
                for line in result.stdout.splitlines()
                if line.strip()
            ]
            return files
        except subprocess.CalledProcessError as e:
            logger.error("staged_files_check_failed", error=str(e))
            return []
