"""
doc_id: 2026011822400005
Phase 1 Demo and Test Script

Demonstrates core Phase 1 functionality:
- Registry creation and allocation
- Uniqueness validation
- Sync validation
- Audit logging
"""

import sys
from pathlib import Path
import json

# Add DIR_OPT/id_16_digit to path
sys.path.insert(0, str(Path(__file__).parent))

from core.registry_store import RegistryStore
from monitoring.audit_logger import AuditLogger


def demo_phase_1():
    """Demonstrate Phase 1 functionality."""
    
    print("=" * 70)
    print("EAFIX IDENTITY SYSTEM - PHASE 1 DEMO")
    print("=" * 70)
    print()
    
    # Setup paths
    registry_path = Path(__file__).parent / "registry" / "ID_REGISTRY.json"
    audit_path = Path(__file__).parent / "registry" / "identity_audit_log.jsonl"
    
    # Initialize components
    print("1. Initializing Registry and Audit Logger...")
    registry = RegistryStore(str(registry_path))
    audit_logger = AuditLogger(str(audit_path))
    print(f"   ✓ Registry: {registry_path}")
    print(f"   ✓ Audit log: {audit_path}")
    print()
    
    # Allocate some IDs
    print("2. Allocating IDs...")
    test_files = [
        ("services/api.py", "999", "20"),
        ("services/auth.py", "999", "20"),
        ("docs/README.md", "999", "30"),
        ("scripts/deploy.ps1", "999", "40"),
    ]
    
    allocated_ids = []
    for file_path, ns_code, type_code in test_files:
        try:
            doc_id = registry.allocate_id(
                ns_code=ns_code,
                type_code=type_code,
                file_path=file_path,
                allocated_by="demo_script"
            )
            allocated_ids.append((doc_id, file_path))
            
            # Log allocation
            audit_logger.log_allocation(
                doc_id=doc_id,
                file_path=file_path,
                ns_code=ns_code,
                type_code=type_code,
                allocated_by="demo_script",
                run_id="demo_001"
            )
            
            print(f"   ✓ {doc_id} → {file_path}")
        except ValueError as e:
            print(f"   ✗ Error allocating for {file_path}: {e}")
    
    print()
    
    # Check uniqueness
    print("3. Validating Uniqueness...")
    is_unique, duplicates = registry.check_uniqueness()
    if is_unique:
        print("   ✓ All IDs are unique")
    else:
        print(f"   ✗ Found {len(duplicates)} duplicates: {duplicates}")
    print()
    
    # Get stats
    print("4. Registry Statistics:")
    stats = registry.get_stats()
    for key, value in stats.items():
        print(f"   - {key}: {value}")
    print()
    
    # Test file move
    print("5. Simulating File Move...")
    if allocated_ids:
        test_id, old_path = allocated_ids[0]
        new_path = "services/v2/api.py"
        registry.update_file_path(test_id, new_path)
        audit_logger.log_move(
            doc_id=test_id,
            old_path=old_path,
            new_path=new_path,
            run_id="demo_001"
        )
        print(f"   ✓ Moved {test_id}: {old_path} → {new_path}")
    print()
    
    # Test deprecation
    print("6. Simulating Deprecation...")
    if len(allocated_ids) >= 2:
        old_id, _ = allocated_ids[1]
        new_id, _ = allocated_ids[2]
        registry.mark_deprecated(
            id=old_id,
            reason="Replaced with new version",
            superseded_by=new_id
        )
        audit_logger.log_deprecation(
            doc_id=old_id,
            reason="Replaced with new version",
            superseded_by=new_id,
            run_id="demo_001"
        )
        print(f"   ✓ Deprecated {old_id} (superseded by {new_id})")
    print()
    
    # Show recent audit events
    print("7. Recent Audit Events:")
    recent_events = audit_logger.get_recent_events(limit=5)
    for event in recent_events:
        print(f"   [{event['timestamp']}] {event['event_type']}")
        if 'doc_id' in event['data']:
            print(f"      ID: {event['data']['doc_id']}")
    print()
    
    # Display registry contents
    print("8. Active Allocations:")
    active_ids = registry.get_all_active_ids()
    for doc_id, file_path in active_ids:
        print(f"   {doc_id} → {file_path}")
    print()
    
    print("=" * 70)
    print("PHASE 1 DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  - Run: python validation/validate_uniqueness.py <scan_csv> registry/ID_REGISTRY.json")
    print("  - Run: python validation/validate_identity_sync.py <scan_csv> registry/ID_REGISTRY.json")
    print("  - View registry: cat registry/ID_REGISTRY.json")
    print("  - View audit log: cat registry/identity_audit_log.jsonl")
    print()


if __name__ == '__main__':
    try:
        demo_phase_1()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
