#!/usr/bin/env python3
"""
Quick Start Migration Script - Phase 0
Creates initial structure and prepares for module-centric migration.
"""
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Repository root
REPO_ROOT = Path(__file__).parent.parent.parent
MODULES_DIR = REPO_ROOT / "modules"
STATE_DIR = REPO_ROOT / ".state"
ARCHIVE_DIR = REPO_ROOT / "archive" / f"pre_module_centric_{datetime.now().strftime('%Y%m%d')}"
REPORTS_DIR = REPO_ROOT / "reports" / "migration"


def run_command(cmd, check=True):
    """Run shell command and return result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        raise RuntimeError(f"Command failed: {cmd}")
    return result


def create_directory_structure():
    """Create new directory structure."""
    print("\n=== Creating Directory Structure ===")
    
    dirs_to_create = [
        MODULES_DIR,
        STATE_DIR / "dag",
        ARCHIVE_DIR,
        REPORTS_DIR,
        REPO_ROOT / "docs" / "architecture",
        REPO_ROOT / "docs" / "developer",
        REPO_ROOT / "docs" / "migration",
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {dir_path.relative_to(REPO_ROOT)}")


def create_migration_checkpoint():
    """Create Git checkpoint before migration."""
    print("\n=== Creating Migration Checkpoint ===")
    
    # Get current commit
    result = run_command("git rev-parse HEAD")
    commit_sha = result.stdout.strip()
    
    # Save checkpoint
    checkpoint_file = REPO_ROOT / ".execution" / "migration_start.commit"
    checkpoint_file.parent.mkdir(exist_ok=True)
    checkpoint_file.write_text(commit_sha)
    
    print(f"Checkpoint saved: {commit_sha}")
    
    # Create tag
    try:
        run_command(f'git tag pre-migration-snapshot-{datetime.now().strftime("%Y%m%d")}')
        print("Git tag created: pre-migration-snapshot")
    except:
        print("Warning: Could not create git tag (may already exist)")


def analyze_current_structure():
    """Analyze current repository structure."""
    print("\n=== Analyzing Current Structure ===")
    
    # Find all services
    services_dir = REPO_ROOT / "services"
    if services_dir.exists():
        services = [d.name for d in services_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        print(f"Found {len(services)} services:")
        for svc in sorted(services):
            print(f"  - {svc}")
    
    # Find shared code
    shared_dir = REPO_ROOT / "shared"
    if shared_dir.exists():
        shared_items = [d.name for d in shared_dir.iterdir() if d.is_dir() or d.suffix == '.py']
        print(f"\nFound {len(shared_items)} shared items:")
        for item in sorted(shared_items):
            print(f"  - {item}")
    
    # Find tests
    tests_dir = REPO_ROOT / "tests"
    if tests_dir.exists():
        test_dirs = [d.name for d in tests_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        print(f"\nFound {len(test_dirs)} test directories:")
        for td in sorted(test_dirs):
            print(f"  - {td}")
    
    # Save analysis
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "services": services if services_dir.exists() else [],
        "shared_items": shared_items if shared_dir.exists() else [],
        "test_dirs": test_dirs if tests_dir.exists() else [],
    }
    
    analysis_file = REPORTS_DIR / "structure_analysis.json"
    analysis_file.write_text(json.dumps(analysis, indent=2))
    print(f"\nAnalysis saved to: {analysis_file.relative_to(REPO_ROOT)}")


def create_modules_inventory_template():
    """Create template MODULES_INVENTORY.yaml."""
    print("\n=== Creating Module Inventory Template ===")
    
    inventory_template = """# Module Inventory
# Generated: {timestamp}

modules:
  # PIPELINE_STAGE_MODULE - Core data flow stages
  - module_id: calendar-ingestor
    module_kind: PIPELINE_STAGE_MODULE
    layer: 1
    status: active
    description: Ingest economic calendar data
    
  - module_id: data-ingestor
    module_kind: PIPELINE_STAGE_MODULE
    layer: 1
    status: active
    description: Ingest market data
    
  - module_id: data-validator
    module_kind: PIPELINE_STAGE_MODULE
    layer: 1
    status: active
    description: Validate incoming data
    
  - module_id: indicator-engine
    module_kind: PIPELINE_STAGE_MODULE
    layer: 2
    status: active
    description: Calculate technical indicators
    
  - module_id: signal-generator
    module_kind: PIPELINE_STAGE_MODULE
    layer: 2
    status: active
    description: Generate trading signals
    
  - module_id: reentry-engine
    module_kind: PIPELINE_STAGE_MODULE
    layer: 2
    status: active
    description: Reentry logic processing
    
  - module_id: reentry-matrix-svc
    module_kind: PIPELINE_STAGE_MODULE
    layer: 2
    status: active
    description: Matrix calculation service
    
  - module_id: execution-engine
    module_kind: PIPELINE_STAGE_MODULE
    layer: 3
    status: active
    description: Order execution
    
  - module_id: flow-orchestrator
    module_kind: PIPELINE_STAGE_MODULE
    layer: 3
    status: active
    description: Workflow orchestration
    
  # FEATURE_SERVICE_MODULE - Cross-cutting services
  - module_id: risk-manager
    module_kind: FEATURE_SERVICE_MODULE
    layer: 2
    status: active
    description: Risk management service
    
  - module_id: plugin-system
    module_kind: FEATURE_SERVICE_MODULE
    layer: 1
    status: active
    description: Plugin infrastructure
    
  # INTEGRATION_BRIDGE_MODULE - External systems
  - module_id: event-gateway
    module_kind: INTEGRATION_BRIDGE_MODULE
    layer: 2
    status: active
    description: Event system bridge
    
  - module_id: transport-router
    module_kind: INTEGRATION_BRIDGE_MODULE
    layer: 2
    status: active
    description: Message transport routing
    
  # INTERFACE_MODULE - User-facing
  - module_id: desktop-ui
    module_kind: INTERFACE_MODULE
    layer: 4
    status: active
    description: Desktop user interface
    
  - module_id: dashboard-backend
    module_kind: INTERFACE_MODULE
    layer: 4
    status: active
    description: Dashboard API backend
    
  - module_id: gui-gateway
    module_kind: INTERFACE_MODULE
    layer: 4
    status: active
    description: GUI communication gateway
    
  # OBSERVABILITY_REPORTING_MODULE - Monitoring
  - module_id: compliance-monitor
    module_kind: OBSERVABILITY_REPORTING_MODULE
    layer: 3
    status: active
    description: Compliance monitoring
    
  - module_id: telemetry-daemon
    module_kind: OBSERVABILITY_REPORTING_MODULE
    layer: 3
    status: active
    description: Telemetry collection daemon
    
  - module_id: flow-monitor
    module_kind: OBSERVABILITY_REPORTING_MODULE
    layer: 3
    status: active
    description: Flow monitoring
    
  - module_id: reporter
    module_kind: OBSERVABILITY_REPORTING_MODULE
    layer: 3
    status: active
    description: Report generation
    
  # REGISTRY_METADATA_MODULE - Identity systems
  - module_id: id-system
    module_kind: REGISTRY_METADATA_MODULE
    layer: 1
    status: active
    description: 16-digit ID system

migration:
  started: {timestamp}
  current_phase: 0
  completed_phases: []
""".format(timestamp=datetime.now().isoformat())
    
    inventory_file = REPO_ROOT / "MODULES_INVENTORY.yaml"
    inventory_file.write_text(inventory_template)
    print(f"Created: {inventory_file.relative_to(REPO_ROOT)}")


def create_module_manifest_template():
    """Create template module.manifest.yaml."""
    print("\n=== Creating Module Manifest Template ===")
    
    template = """# Module Manifest Template
# Copy this to each module as module.manifest.yaml

module_id: "<module-id>"
module_kind: "<MODULE_KIND>"  # See classification taxonomy
version: "1.0.0"
ulid_prefix: ""  # Optional: ULID for file naming

name: "<Human Readable Name>"
description: "<What this module does>"
owner: "platform-team"
status: "active"  # active|deprecated|experimental

layer: 2  # Architectural layer (1-4)

dependencies:
  # - module_id: "other-module"
  #   version: "^1.0.0"
  #   reason: "Why this dependency exists"

exports:
  # - name: "ClassName"
  #   type: "class"
  #   path: "src/main.py"
  # - name: "function_name"
  #   type: "function"
  #   path: "src/api.py"

state_schema: ""  # Optional: Path to state schema
produces_events: []  # Optional: Events produced

test_coverage_minimum: 77
required_validators:
  - "python -m compileall src/ -q"
  - "pytest tests/ --cov=src --cov-report=term"
"""
    
    template_file = REPO_ROOT / "docs" / "developer" / "MODULE_MANIFEST_TEMPLATE.yaml"
    template_file.parent.mkdir(parents=True, exist_ok=True)
    template_file.write_text(template)
    print(f"Created: {template_file.relative_to(REPO_ROOT)}")


def create_validation_script():
    """Create validation script."""
    print("\n=== Creating Validation Script ===")
    
    validation_script = """#!/usr/bin/env python3
\"\"\"
Module Structure Validator
Validates that modules follow the standard structure.
\"\"\"
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
MODULES_DIR = REPO_ROOT / "modules"

REQUIRED_DIRS = ["src", "tests", "docs", ".state"]
REQUIRED_FILES = ["module.manifest.yaml", "__init__.py"]

def validate_module(module_path):
    \"\"\"Validate single module structure.\"\"\"
    errors = []
    
    # Check required directories
    for dir_name in REQUIRED_DIRS:
        dir_path = module_path / dir_name
        if not dir_path.exists():
            errors.append(f"Missing directory: {dir_name}")
    
    # Check required files
    for file_name in REQUIRED_FILES:
        file_path = module_path / file_name
        if not file_path.exists():
            errors.append(f"Missing file: {file_name}")
    
    return errors

def main():
    \"\"\"Validate all modules.\"\"\"
    if not MODULES_DIR.exists():
        print("Error: modules/ directory does not exist")
        return 1
    
    modules = [d for d in MODULES_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if not modules:
        print("No modules found")
        return 0
    
    print(f"Validating {len(modules)} modules...\\n")
    
    all_valid = True
    for module in sorted(modules):
        errors = validate_module(module)
        if errors:
            print(f"❌ {module.name}:")
            for error in errors:
                print(f"  - {error}")
            all_valid = False
        else:
            print(f"✅ {module.name}")
    
    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())
"""
    
    script_file = REPO_ROOT / "scripts" / "validation" / "validate_module_structure.py"
    script_file.parent.mkdir(parents=True, exist_ok=True)
    script_file.write_text(validation_script)
    print(f"Created: {script_file.relative_to(REPO_ROOT)}")


def create_readme():
    """Create migration README."""
    print("\n=== Creating Migration README ===")
    
    readme = """# Module-Centric Migration

This directory contains scripts and documentation for migrating to module-centric architecture.

## Quick Start

1. **Run Phase 0** (Preparation):
   ```bash
   python scripts/migration/quick_start_migration.py
   ```

2. **Review the plan**:
   - Read `MIGRATION_TO_MODULE_CENTRIC.md`
   - Review `MODULES_INVENTORY.yaml`

3. **Proceed with Phase 1**:
   ```bash
   python scripts/migration/phase1_create_skeletons.py
   ```

## Structure Created

- `modules/` - All modules will go here
- `.state/` - Global state (registry, DAG)
- `archive/` - Old structure preserved here
- `reports/migration/` - Analysis and reports
- `MODULES_INVENTORY.yaml` - Module catalog

## Validation

Validate structure at any time:
```bash
python scripts/validation/validate_module_structure.py
```

## Rollback

If needed, rollback to pre-migration state:
```bash
git reset --hard $(cat .execution/migration_start.commit)
rm -rf modules/ .state/
```

## Reference

- Best Practices: `MODULE_CENTRIC_REPOSITORY_BEST_PRACTICES.md`
- Migration Plan: `MIGRATION_TO_MODULE_CENTRIC.md`
- Module Template: `docs/developer/MODULE_MANIFEST_TEMPLATE.yaml`
"""
    
    readme_file = REPORTS_DIR / "README.md"
    readme_file.write_text(readme)
    print(f"Created: {readme_file.relative_to(REPO_ROOT)}")


def main():
    """Main execution."""
    print("=" * 60)
    print("Module-Centric Migration - Phase 0: Preparation")
    print("=" * 60)
    
    try:
        # Step 1: Create directories
        create_directory_structure()
        
        # Step 2: Create checkpoint
        create_migration_checkpoint()
        
        # Step 3: Analyze current structure
        analyze_current_structure()
        
        # Step 4: Create inventory template
        create_modules_inventory_template()
        
        # Step 5: Create manifest template
        create_module_manifest_template()
        
        # Step 6: Create validation script
        create_validation_script()
        
        # Step 7: Create README
        create_readme()
        
        print("\n" + "=" * 60)
        print("✅ Phase 0 Complete!")
        print("=" * 60)
        print("\nNext Steps:")
        print("1. Review: MIGRATION_TO_MODULE_CENTRIC.md")
        print("2. Review: MODULES_INVENTORY.yaml")
        print("3. Customize module inventory as needed")
        print("4. Proceed to Phase 1 when ready")
        print("\nTo proceed to Phase 1:")
        print("  python scripts/migration/phase1_create_skeletons.py")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
