#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-1017
"""
Fix Doc ID Format - Add comment format to files with docstring doc IDs

This script processes files that have doc IDs in docstrings but not in comment format.
It extracts the doc ID from the docstring and adds a proper # DOC_ID: comment.

DOC_ID: A-TOOL-FIX-DOCID-FORMAT-001
"""

import re
import sys
from pathlib import Path

# Files to process
FILES_TO_FIX = [
    "AI_CLI_PROVENANCE_SOLUTION/ai_cli_provenance_collector.py",
    "AI_CLI_PROVENANCE_SOLUTION/conftest.py",
    "RUNTIME/doc_id/SUB_DOC_ID/id_type_manager.py",
    "RUNTIME/doc_id/SUB_DOC_ID/migrate_pattern_ids.py",
    "RUNTIME/doc_id/SUB_DOC_ID/migrate_trigger_ids.py",
    "RUNTIME/doc_id/SUB_DOC_ID/restructure_registry.py",
    "RUNTIME/doc_id/SUB_DOC_ID/sync_all_registries.py",
    "RUNTIME/doc_id/SUB_DOC_ID/unified_pre_commit_hook.py",
    "RUNTIME/doc_id/SUB_DOC_ID/validate_id_type_registry.py",
    "RUNTIME/doc_id/SUB_DOC_ID/1_CORE_OPERATIONS/batch_assign_docids.py",
    "RUNTIME/doc_id/SUB_DOC_ID/5_REGISTRY_DATA/sync_doc_id_registry.py",
    "RUNTIME/doc_id/SUB_DOC_ID/6_TESTS/conftest.py",
    "RUNTIME/doc_id/SUB_DOC_ID/6_TESTS/run_tests.py",
    "RUNTIME/doc_id/SUB_DOC_ID/6_TESTS/test_integration_unified.py",
    "RUNTIME/doc_id/SUB_DOC_ID/6_TESTS/test_registry_integrity.py",
    "RUNTIME/doc_id/SUB_DOC_ID/6_TESTS/test_suite_master.py",
    "RUNTIME/doc_id/SUB_DOC_ID/6_TESTS/test_syntax_all.py",
    "RUNTIME/doc_id/SUB_DOC_ID/pattern_id/1_CORE_OPERATIONS/pattern_id_manager.py",
    "RUNTIME/doc_id/SUB_DOC_ID/pattern_id/1_CORE_OPERATIONS/pattern_id_scanner.py",
    "RUNTIME/doc_id/SUB_DOC_ID/pattern_id/2_VALIDATION_FIXING/validate_pattern_id_coverage.py",
    "RUNTIME/doc_id/SUB_DOC_ID/pattern_id/2_VALIDATION_FIXING/validate_pattern_id_format.py",
    "RUNTIME/doc_id/SUB_DOC_ID/pattern_id/2_VALIDATION_FIXING/validate_pattern_id_references.py",
    "RUNTIME/doc_id/SUB_DOC_ID/pattern_id/2_VALIDATION_FIXING/validate_pattern_id_sync.py",
    "RUNTIME/doc_id/SUB_DOC_ID/pattern_id/2_VALIDATION_FIXING/validate_pattern_id_uniqueness.py",
    "RUNTIME/doc_id/SUB_DOC_ID/pattern_id/common/rules.py",
    "RUNTIME/doc_id/SUB_DOC_ID/trigger_id/1_CORE_OPERATIONS/trigger_id_assigner.py",
    "RUNTIME/doc_id/SUB_DOC_ID/trigger_id/1_CORE_OPERATIONS/trigger_id_scanner.py",
    "RUNTIME/doc_id/SUB_DOC_ID/trigger_id/2_VALIDATION_FIXING/validate_trigger_coverage.py",
    "RUNTIME/doc_id/SUB_DOC_ID/trigger_id/2_VALIDATION_FIXING/validate_trigger_id_format.py",
    "RUNTIME/doc_id/SUB_DOC_ID/trigger_id/2_VALIDATION_FIXING/validate_trigger_id_references.py",
    "RUNTIME/doc_id/SUB_DOC_ID/trigger_id/2_VALIDATION_FIXING/validate_trigger_id_sync.py",
    "RUNTIME/doc_id/SUB_DOC_ID/trigger_id/2_VALIDATION_FIXING/validate_trigger_id_uniqueness.py",
    "RUNTIME/doc_id/SUB_DOC_ID/trigger_id/common/rules.py",
    "RUNTIME/relationship_index/SUB_RELATIONSHIP_INDEX/check_nodes.py",
    "RUNTIME/relationship_index/SUB_RELATIONSHIP_INDEX/deep_debug.py",
    "RUNTIME/relationship_index/SUB_RELATIONSHIP_INDEX/test_markdown.py",
    "scripts/generators/generate_id_automation.py",
    "scripts/generators/generate_id_docs.py",
    "scripts/generators/generate_id_validators.py",
]

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


def extract_doc_id_from_docstring(content: str) -> str:
    """Extract doc_id from docstring (various formats)"""
    # Pattern 1: doc_id: DOC-...
    match = re.search(r'doc_id:\s*(DOC-[A-Z0-9-]+)', content, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 2: DOC-ID: DOC-... (in docstring)
    match = re.search(r'DOC-ID:\s*(DOC-[A-Z0-9-]+)', content, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 3: DOC_ID: DOC-... (in docstring)
    match = re.search(r'DOC_ID:\s*(DOC-[A-Z0-9-]+)', content, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return None


def has_comment_doc_id(content: str) -> bool:
    """Check if file already has # DOC_ID: comment"""
    return bool(re.search(r'^#\s*DOC_ID:\s*DOC-', content, re.MULTILINE))


def add_comment_doc_id(file_path: Path, doc_id: str, dry_run: bool = False) -> bool:
    """Add # DOC_ID: comment to file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check if already has comment format
        if has_comment_doc_id(content):
            print(f"  ⚠️  Already has comment doc ID: {file_path.name}")
            return False
        
        # Extract doc ID from docstring if not provided
        if not doc_id:
            doc_id = extract_doc_id_from_docstring(content)
            if not doc_id:
                print(f"  ❌ No doc ID found in docstring: {file_path.name}")
                return False
        
        lines = content.splitlines(keepends=True)
        insert_idx = 0
        
        # Skip shebang
        if lines and lines[0].startswith('#!'):
            insert_idx = 1
        
        # Skip encoding declaration
        if insert_idx < len(lines) and 'coding' in lines[insert_idx]:
            insert_idx += 1
        
        # Add comment doc ID
        doc_id_line = f"# DOC_ID: {doc_id}\n"
        
        if dry_run:
            print(f"  [DRY-RUN] Would add: {doc_id} to {file_path.name}")
            return True
        
        lines.insert(insert_idx, doc_id_line)
        file_path.write_text(''.join(lines), encoding='utf-8')
        print(f"  ✅ Added: {doc_id}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fix doc ID format in remaining Python files')
    parser.add_argument('--execute', action='store_true', help='Execute changes (default is dry-run)')
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    print(f"\n{'='*60}")
    print(f"Fix Doc ID Format - Add Comment Format")
    print(f"{'='*60}")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY-RUN'}")
    print(f"Files to process: {len(FILES_TO_FIX)}")
    print(f"{'='*60}\n")
    
    success = 0
    skipped = 0
    failed = 0
    
    for i, rel_path in enumerate(FILES_TO_FIX, 1):
        file_path = REPO_ROOT / rel_path
        
        if not file_path.exists():
            print(f"{i:2d}. ❌ NOT FOUND: {rel_path}")
            failed += 1
            continue
        
        print(f"{i:2d}. {file_path.name}")
        
        # Extract doc ID from file
        content = file_path.read_text(encoding='utf-8')
        doc_id = extract_doc_id_from_docstring(content)
        
        if not doc_id:
            print(f"    ⚠️  No doc ID found in docstring")
            skipped += 1
            continue
        
        print(f"    Found doc ID: {doc_id}")
        
        if add_comment_doc_id(file_path, doc_id, dry_run):
            success += 1
        else:
            skipped += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total files:     {len(FILES_TO_FIX)}")
    print(f"Success:         {success}")
    print(f"Skipped:         {skipped}")
    print(f"Failed:          {failed}")
    print(f"{'='*60}\n")
    
    if dry_run:
        print("⚠️  This was a DRY-RUN. No files were modified.")
        print("   Run with --execute to actually modify files.\n")
    else:
        print("✅ Files modified successfully!")
        print("   Next steps:")
        print("   1. Re-scan: python doc_id_scanner.py scan")
        print("   2. Verify: python validate_doc_id_coverage.py\n")


if __name__ == '__main__':
    main()
