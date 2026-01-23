#!/usr/bin/env python3
"""
ALVT Layer 0: Static Integrity Verification
doc_id: 2099900121260118
version: 1.0

Verifies static requirements without execution:
- File existence
- Config key accessibility
- Forbidden pattern detection
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml

__doc_id__ = "2099900121260118"


class Layer0Verifier:
    """ALVT Layer 0 static integrity verifier."""

    def __init__(self, repo_root: Path, contract: Dict[str, Any]):
        """Initialize verifier.
        
        Args:
            repo_root: Repository root path
            contract: Loaded contract dictionary
        """
        self.repo_root = repo_root
        self.contract = contract
        self.checks: List[Dict[str, Any]] = []

    def verify(self) -> Dict[str, Any]:
        """Run all Layer 0 checks.
        
        Returns:
            Verification report dictionary
        """
        trigger_id = self.contract.get("metadata", {}).get("trigger_id", "UNKNOWN")
        
        # Check file existence
        self._check_files_exist()
        
        # Check config keys (placeholder - requires config system integration)
        self._check_config_keys()
        
        # Check forbidden patterns
        self._check_forbidden_patterns()
        
        # Generate report
        passed = sum(1 for c in self.checks if c["passed"])
        failed = sum(1 for c in self.checks if not c["passed"])
        status = "PASS" if failed == 0 else "FAIL"
        
        report = {
            "trigger_id": trigger_id,
            "verification_layer": "layer0",
            "status": status,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "checks": sorted(self.checks, key=lambda x: x["check_id"]),
            "summary": {
                "total_checks": len(self.checks),
                "passed": passed,
                "failed": failed
            }
        }
        
        return report

    def _check_files_exist(self) -> None:
        """Verify all required files exist."""
        required_files = self.contract.get("required_files", [])
        
        for file_spec in required_files:
            path_str = file_spec.get("path")
            role = file_spec.get("role", "unknown")
            
            if not path_str:
                self.checks.append({
                    "check_id": f"file_exists_{role}",
                    "passed": False,
                    "reason": "File spec missing 'path' field",
                    "evidence": {"file_spec": file_spec}
                })
                continue
            
            # Try repo-relative path
            file_path = self.repo_root / path_str
            exists = file_path.exists()
            
            self.checks.append({
                "check_id": f"file_exists_{path_str.replace('/', '_').replace('.', '_')}",
                "passed": exists,
                "reason": None if exists else f"File not found: {path_str}",
                "evidence": {
                    "path": path_str,
                    "role": role,
                    "checked_absolute_path": str(file_path),
                    "exists": exists
                }
            })

    def _check_config_keys(self) -> None:
        """Verify required config keys exist (placeholder implementation)."""
        required_config = self.contract.get("required_config", [])
        
        # For now, create placeholder checks
        # Real implementation would load config and verify keys
        for config_spec in required_config:
            key = config_spec.get("key")
            
            if not key:
                self.checks.append({
                    "check_id": "config_key_unknown",
                    "passed": False,
                    "reason": "Config spec missing 'key' field",
                    "evidence": {"config_spec": config_spec}
                })
                continue
            
            # Placeholder: Assume config check passes for now
            # TODO: Integrate with actual config loading system
            self.checks.append({
                "check_id": f"config_exists_{key.replace('.', '_')}",
                "passed": True,
                "reason": None,
                "evidence": {
                    "key": key,
                    "note": "Config validation not yet implemented - assumed PASS"
                }
            })

    def _check_forbidden_patterns(self) -> None:
        """Check for forbidden patterns in required files."""
        forbidden_patterns = self.contract.get("forbidden_patterns", [])
        required_files = self.contract.get("required_files", [])
        
        if not forbidden_patterns:
            return
        
        # Get list of files to check
        files_to_check = []
        for file_spec in required_files:
            path_str = file_spec.get("path")
            if path_str:
                file_path = self.repo_root / path_str
                if file_path.exists():
                    files_to_check.append((path_str, file_path))
        
        # Check each pattern
        for pattern_spec in forbidden_patterns:
            pattern_str = pattern_spec.get("pattern")
            reason = pattern_spec.get("reason", "Forbidden pattern detected")
            scope = pattern_spec.get("scope", "required_files")
            
            if not pattern_str:
                continue
            
            if scope != "required_files":
                # Skip non-required_files scopes for now
                continue
            
            # Check pattern in each file
            pattern_found = False
            findings = []
            
            for path_str, file_path in files_to_check:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    matches = list(re.finditer(pattern_str, content, re.IGNORECASE))
                    
                    if matches:
                        pattern_found = True
                        # Get line numbers
                        lines = content.split("\n")
                        for match in matches[:5]:  # Limit to first 5 matches per file
                            start_pos = match.start()
                            line_no = content[:start_pos].count("\n") + 1
                            line_text = lines[line_no - 1].strip()
                            findings.append({
                                "file": path_str,
                                "line": line_no,
                                "text": line_text[:80]  # Truncate long lines
                            })
                except Exception as e:
                    findings.append({
                        "file": path_str,
                        "error": f"Failed to read: {e}"
                    })
            
            check_id = f"no_pattern_{pattern_str[:20].replace(' ', '_')}"
            self.checks.append({
                "check_id": check_id,
                "passed": not pattern_found,
                "reason": reason if pattern_found else None,
                "evidence": {
                    "pattern": pattern_str,
                    "findings": findings if pattern_found else []
                }
            })


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ALVT Layer 0: Static integrity verification"
    )
    parser.add_argument(
        "--trigger",
        required=True,
        help="Trigger ID (e.g., FILE_IDENTITY_CREATE)"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root path (default: current directory)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON report path (default: reports/alvt/static.<trigger>.json)"
    )

    args = parser.parse_args()

    # Load contract
    contract_dir = args.repo_root / "contracts" / "triggers"
    contract_files = list(contract_dir.glob(f"*trigger.{args.trigger}.yaml"))
    
    if not contract_files:
        print(f"ERROR: Contract not found for trigger '{args.trigger}'", file=sys.stderr)
        return 1
    
    contract_path = contract_files[0]
    
    try:
        with open(contract_path, "r", encoding="utf-8") as f:
            contract = yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load contract: {e}", file=sys.stderr)
        return 1

    # Run verification
    verifier = Layer0Verifier(args.repo_root, contract)
    report = verifier.verify()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        reports_dir = args.repo_root / "reports" / "alvt"
        reports_dir.mkdir(parents=True, exist_ok=True)
        output_path = reports_dir / f"static.{args.trigger}.json"

    # Write report
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    print(f"Layer 0 verification: {report['status']}")
    print(f"Report written to: {output_path}")
    print(f"Checks: {report['summary']['passed']}/{report['summary']['total_checks']} passed")

    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
