#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TRIGGER_ID: TRIGGER-HOOK-PRE-COMMIT-HOOK-003
# DOC_LINK: DOC-SCRIPT-DOC-ID-PRE-COMMIT-003
"""
Pre-commit Hook for DOC_ID Validation

PURPOSE: Validate doc_ids before commit
PATTERN: PATTERN-DOC-ID-PRE-COMMIT-003

INSTALLATION:
    # Copy to .git/hooks/pre-commit
    cp doc_id/pre_commit_hook.py .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit

    # Or use as standalone
    python doc_id/pre_commit_hook.py
"""

import re
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, DOC_ID_REGEX
from common.utils import validate_doc_id


def get_staged_files():
    """Get list of staged files"""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True,
            cwd=REPO_ROOT,
        )
        return [f for f in result.stdout.strip().split("\n") if f]
    except subprocess.CalledProcessError:
        return []


def validate_file_doc_ids(file_path: Path) -> bool:
    """Validate doc_ids in a single file"""
    if not file_path.exists():
        return True

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")
        
        # For Python files, require DOC-ID in first 50 lines
        if file_path.suffix == ".py":
            # Check first 50 lines for DOC_ID: or DOC_LINK:
            header = "\n".join(lines[:50])
            has_doc_id = bool(re.search(r"DOC_ID:|DOC_LINK:|DOC-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-[0-9]+", header))
            
            if not has_doc_id:
                print(f"❌ {file_path}: Missing DOC-ID")
                print(f"   Python files must have DOC_ID: or DOC_LINK: in first 50 lines")
                return False
        
        # Validate all DOC-IDs found (format check)
        doc_ids = re.findall(r"DOC-[A-Z0-9-]+", content)
        invalid = [did for did in doc_ids if not DOC_ID_REGEX.match(did)]

        if invalid:
            print(f"❌ {file_path}: Invalid doc_ids found:")
            for did in invalid:
                print(f"   - {did}")
            return False

        return True
    except Exception as e:
        print(f"⚠️  Warning: Could not validate {file_path}: {e}")
        return True  # Don't block commit on read errors


def main():
    """Main pre-commit validation"""
    print("🔍 Validating doc_ids in staged files...")

    staged_files = get_staged_files()
    if not staged_files:
        print("✅ No files to validate")
        return 0

    eligible_extensions = {
        ".py",
        ".md",
        ".yaml",
        ".yml",
        ".json",
        ".ps1",
        ".sh",
        ".txt",
    }
    files_to_check = [
        REPO_ROOT / f for f in staged_files if Path(f).suffix in eligible_extensions
    ]

    if not files_to_check:
        print("✅ No eligible files to validate")
        return 0

    print(f"Checking {len(files_to_check)} file(s)...")

    all_valid = True
    for file_path in files_to_check:
        if not validate_file_doc_ids(file_path):
            all_valid = False

    if all_valid:
        print("✅ All doc_ids valid")
        return 0
    else:
        print("\n❌ Commit blocked: Invalid doc_ids detected")
        print("Fix the invalid doc_ids and try again.")
        print("\nTo bypass this check (not recommended):")
        print("  git commit --no-verify")
        return 1


if __name__ == "__main__":
    sys.exit(main())
