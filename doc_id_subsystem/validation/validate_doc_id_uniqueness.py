#!/usr/bin/env python3
"""
AUTO-006: Uniqueness Validator
Validates that all doc_ids in registry are unique
"""
# DOC_ID: DOC-CORE-2-VALIDATION-FIXING-VALIDATE-DOC-ID-1164

import argparse
import json
import sys
import yaml
from pathlib import Path
from datetime import datetime
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import REPO_ROOT

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

def main(output: str = None):
    # Emit VALIDATION_STARTED event
    _emit_event(
        subsystem="SUB_DOC_ID",
        step_id="VALIDATION_STARTED",
        subject="validate_doc_id_uniqueness",
        summary="Starting doc_id uniqueness validation",
        severity="INFO",
        details={"validator": "uniqueness"}
    )
    
    # Load registry
    registry_path = Path(__file__).parent.parent / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"
    
    print(f"📖 Loading registry: {registry_path}")
    
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)
    
    # Extract all doc_ids
    doc_ids = []
    documents = registry.get('documents', [])
    
    for doc in documents:
        if 'doc_id' in doc:
            doc_ids.append(doc['doc_id'])
    
    print(f"   Found {len(doc_ids)} doc_id entries")
    
    # Check for duplicates
    doc_id_counts = Counter(doc_ids)
    duplicates = {doc_id: count for doc_id, count in doc_id_counts.items() if count > 1}
    
    # Prepare results
    results = {
        "task_id": "AUTO-006",
        "timestamp": datetime.utcnow().isoformat(),
        "total_ids": len(doc_ids),
        "unique_ids": len(doc_id_counts),
        "duplicate_count": len(duplicates),
        "duplicates": duplicates,
        "status": "PASSED" if not duplicates else "FAILED"
    }
    
    # Default output path if not provided
    if not output:
        output = str(Path(__file__).parent.parent / "reports" / "uniqueness_report.json")
    
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Display results
    if duplicates:
        print(f"\n❌ FAILED: Found {len(duplicates)} duplicate doc_ids:")
        for doc_id, count in duplicates.items():
            print(f"   {doc_id}: {count} occurrences")
        
        _emit_event(
            subsystem="SUB_DOC_ID",
            step_id="VALIDATION_COMPLETED",
            subject="validate_doc_id_uniqueness",
            summary=f"Uniqueness validation FAILED: {len(duplicates)} duplicates",
            severity="ERROR",
            details={"passed": False, "duplicates": len(duplicates)}
        )
        
        return 1
    else:
        print(f"\n✅ PASSED: All {len(doc_ids)} doc_ids are unique")
        
        _emit_event(
            subsystem="SUB_DOC_ID",
            step_id="VALIDATION_COMPLETED",
            subject="validate_doc_id_uniqueness",
            summary="Uniqueness validation PASSED: No duplicates",
            severity="NOTICE",
            details={"passed": True, "total_ids": len(doc_ids)}
        )
        
        return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uniqueness Validator")
    parser.add_argument("--output", help="Output JSON file path (optional)")
    args = parser.parse_args()
    sys.exit(main(args.output))