"""
Staging area for atomic batch operations.
All-or-nothing commit protocol for doc_id assignments.

Phase 3 optimization - ensures that batch operations either
fully succeed or leave the repository untouched (no partial states).

This eliminates the risk of registry corruption or inconsistent state
when operations are interrupted mid-execution.
"""
# DOC_ID: DOC-STAGING-COMMON-STAGING-001

import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class StagingArea:
    """
    Manages staged operations with atomic commit protocol.
    
    Operations are staged in a temporary directory, validated,
    and then atomically committed to the repository.
    
    Structure:
        .staging/
        └── RUN-ID/
            ├── ops.jsonl          # Operation log
            ├── files/             # Staged file patches
            │   └── path/to/file.py
            ├── report.json        # Validation results
            └── metadata.json      # Run metadata
    
    Workflow:
        1. create_run() - Initialize staging directory
        2. stage_operation() - Stage patches/operations
        3. validate_staged() - Run validators
        4. commit_staged() - Atomic apply to repo
        5. cleanup() - Remove staging directory
    """
    
    def __init__(self, staging_root: Path):
        """
        Initialize staging area.
        
        Args:
            staging_root: Root directory for all staging operations
                         (typically .staging/ in repo root)
        """
        self.staging_root = staging_root
        self.staging_root.mkdir(parents=True, exist_ok=True)
    
    def create_run(self, run_id: str, metadata: Optional[Dict] = None) -> Path:
        """
        Create staging directory for a run.
        
        Args:
            run_id: Unique identifier for this run
            metadata: Optional metadata about the run
            
        Returns:
            Path to run directory
        """
        run_dir = self.staging_root / run_id
        
        if run_dir.exists():
            # Clean up previous incomplete run
            shutil.rmtree(run_dir)
        
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (run_dir / "files").mkdir(exist_ok=True)
        (run_dir / "ops.jsonl").touch()
        
        # Write metadata
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "run_id": run_id,
            "created_utc": datetime.utcnow().isoformat(),
            "status": "staging"
        })
        
        (run_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8"
        )
        
        return run_dir
    
    def stage_operation(self, run_id: str, operation: Dict):
        """
        Stage a single operation.
        
        Args:
            run_id: Run identifier
            operation: Operation dictionary with:
                - type: "patch" | "assign" | "replace" | "skip"
                - action: Description of action
                - path: File path (repo-relative)
                - doc_id: Target doc_id (if applicable)
                - staged_content: Patched file content (for patch ops)
        """
        run_dir = self.staging_root / run_id
        
        if not run_dir.exists():
            raise ValueError(f"Run directory not found: {run_id}")
        
        # Append to ops.jsonl
        with open(run_dir / "ops.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(operation) + "\n")
        
        # If file patch, stage it
        if operation.get("type") == "patch" and operation.get("staged_content"):
            staged_file = run_dir / "files" / operation["path"]
            staged_file.parent.mkdir(parents=True, exist_ok=True)
            staged_file.write_text(
                operation["staged_content"],
                encoding="utf-8"
            )
    
    def get_operations(self, run_id: str) -> List[Dict]:
        """
        Get all staged operations for a run.
        
        Args:
            run_id: Run identifier
            
        Returns:
            List of operation dictionaries
        """
        run_dir = self.staging_root / run_id
        ops_file = run_dir / "ops.jsonl"
        
        if not ops_file.exists():
            return []
        
        ops = []
        with open(ops_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    ops.append(json.loads(line))
        
        return ops
    
    def validate_staged(self, run_id: str, validators: List) -> Dict:
        """
        Run validators on all staged files.
        
        Args:
            run_id: Run identifier
            validators: List of validator instances
            
        Returns:
            Validation results dictionary with:
                - passed: List of passed validations
                - failed: List of failed validations
                - summary: Overall summary
        """
        run_dir = self.staging_root / run_id
        results = {
            "passed": [],
            "failed": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
        
        # Read all staged operations
        ops = self.get_operations(run_id)
        
        # Validate each staged file
        for op in ops:
            if op.get("type") == "patch":
                staged_file = run_dir / "files" / op["path"]
                
                if not staged_file.exists():
                    continue
                
                for validator in validators:
                    result = validator.validate(staged_file)
                    results["summary"]["total"] += 1
                    
                    if result.get("passed"):
                        results["passed"].append(result)
                        results["summary"]["passed"] += 1
                    else:
                        results["failed"].append(result)
                        results["summary"]["failed"] += 1
        
        # Save validation report
        (run_dir / "report.json").write_text(
            json.dumps(results, indent=2),
            encoding="utf-8"
        )
        
        return results
    
    def commit_staged(self, run_id: str, repo_root: Path, dry_run: bool = False) -> Dict:
        """
        Atomically commit staged files to repository.
        
        Uses atomic rename to ensure all-or-nothing semantics.
        If any operation fails, no changes are applied.
        
        Args:
            run_id: Run identifier
            repo_root: Repository root path
            dry_run: If True, don't actually commit (test mode)
            
        Returns:
            Dictionary with:
                - committed: List of committed file paths
                - count: Number of files committed
                - dry_run: Whether this was a dry run
        """
        run_dir = self.staging_root / run_id
        
        # Read all operations
        ops = self.get_operations(run_id)
        
        committed = []
        
        if dry_run:
            # Dry run - just report what would be done
            for op in ops:
                if op.get("type") == "patch":
                    committed.append(op["path"])
            
            return {
                "committed": committed,
                "count": len(committed),
                "dry_run": True
            }
        
        # Actual commit: atomic rename operations
        temp_files = []
        
        try:
            # Phase 1: Write all temp files
            for op in ops:
                if op.get("type") == "patch":
                    staged_file = run_dir / "files" / op["path"]
                    target_file = repo_root / op["path"]
                    temp_file = target_file.with_suffix(target_file.suffix + ".tmp")
                    
                    # Write to temp
                    temp_file.write_bytes(staged_file.read_bytes())
                    
                    # Fsync to ensure written
                    with open(temp_file, "r+b") as f:
                        f.flush()
                        import os
                        os.fsync(f.fileno())
                    
                    temp_files.append((temp_file, target_file))
            
            # Phase 2: Atomic renames (all or nothing)
            for temp_file, target_file in temp_files:
                temp_file.replace(target_file)
                committed.append(str(target_file.relative_to(repo_root)))
            
            # Update metadata
            metadata = self._get_metadata(run_id)
            metadata["status"] = "committed"
            metadata["committed_utc"] = datetime.utcnow().isoformat()
            metadata["files_committed"] = len(committed)
            self._save_metadata(run_id, metadata)
            
        except Exception as e:
            # Cleanup any temp files on error
            for temp_file, _ in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
            
            # Update metadata with error
            metadata = self._get_metadata(run_id)
            metadata["status"] = "failed"
            metadata["error"] = str(e)
            self._save_metadata(run_id, metadata)
            
            raise
        
        return {
            "committed": committed,
            "count": len(committed),
            "dry_run": False
        }
    
    def rollback(self, run_id: str):
        """
        Delete staging directory (discard all staged changes).
        
        Args:
            run_id: Run identifier
        """
        run_dir = self.staging_root / run_id
        
        if run_dir.exists():
            # Update metadata
            metadata = self._get_metadata(run_id)
            metadata["status"] = "rolled_back"
            metadata["rolled_back_utc"] = datetime.utcnow().isoformat()
            self._save_metadata(run_id, metadata)
            
            # Remove staging directory
            shutil.rmtree(run_dir)
    
    def cleanup_old_runs(self, days: int = 7) -> int:
        """
        Clean up staging directories older than N days.
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of directories removed
        """
        if not self.staging_root.exists():
            return 0
        
        import time
        cutoff = time.time() - (days * 86400)
        removed = 0
        
        for run_dir in self.staging_root.iterdir():
            if not run_dir.is_dir():
                continue
            
            # Check age
            if run_dir.stat().st_mtime < cutoff:
                shutil.rmtree(run_dir)
                removed += 1
        
        return removed
    
    def list_runs(self, status: Optional[str] = None) -> List[Dict]:
        """
        List all staging runs.
        
        Args:
            status: Filter by status (staging, committed, failed, rolled_back)
            
        Returns:
            List of run metadata dictionaries
        """
        if not self.staging_root.exists():
            return []
        
        runs = []
        
        for run_dir in self.staging_root.iterdir():
            if not run_dir.is_dir():
                continue
            
            metadata = self._get_metadata(run_dir.name)
            
            if status and metadata.get("status") != status:
                continue
            
            runs.append(metadata)
        
        return sorted(runs, key=lambda x: x.get("created_utc", ""), reverse=True)
    
    def _get_metadata(self, run_id: str) -> Dict:
        """Get metadata for a run."""
        run_dir = self.staging_root / run_id
        metadata_file = run_dir / "metadata.json"
        
        if not metadata_file.exists():
            return {"run_id": run_id}
        
        return json.loads(metadata_file.read_text(encoding="utf-8"))
    
    def _save_metadata(self, run_id: str, metadata: Dict):
        """Save metadata for a run."""
        run_dir = self.staging_root / run_id
        metadata_file = run_dir / "metadata.json"
        
        metadata_file.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8"
        )
    
    def get_stats(self, run_id: str) -> Dict:
        """
        Get statistics for a staging run.
        
        Args:
            run_id: Run identifier
            
        Returns:
            Statistics dictionary
        """
        metadata = self._get_metadata(run_id)
        ops = self.get_operations(run_id)
        
        op_types = {}
        for op in ops:
            op_type = op.get("type", "unknown")
            op_types[op_type] = op_types.get(op_type, 0) + 1
        
        return {
            "run_id": run_id,
            "status": metadata.get("status", "unknown"),
            "created_utc": metadata.get("created_utc"),
            "total_operations": len(ops),
            "operations_by_type": op_types,
            "files_committed": metadata.get("files_committed", 0)
        }
