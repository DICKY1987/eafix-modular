#!/usr/bin/env python3
# DOC_ID: DOC-SERVICE-0007
"""
Doc ID Subsystem - Quick Setup Script

Automates the initial setup of the doc_id subsystem for eafix-modular.
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess

def print_header(message):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70 + "\n")

def print_step(step_num, message):
    """Print formatted step."""
    print(f"\n[Step {step_num}] {message}")
    print("-" * 70)

def check_python_version():
    """Verify Python version >= 3.7."""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def get_repo_root():
    """Get repository root path."""
    # Assume this script is in doc_id_subsystem/ under repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    return repo_root.resolve()

def setup_registry(subsystem_dir):
    """Create DOC_ID_REGISTRY.yaml from template."""
    registry_dir = subsystem_dir / "registry"
    template = registry_dir / "DOC_ID_REGISTRY.yaml.template"
    target = registry_dir / "DOC_ID_REGISTRY.yaml"
    
    if target.exists():
        print(f"⚠️  Registry already exists: {target}")
        response = input("   Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("   Skipping registry setup")
            return False
    
    shutil.copy(template, target)
    print(f"✅ Created registry: {target}")
    return True

def customize_registry(registry_path):
    """Guide user through registry customization."""
    print("\n📝 Registry Customization")
    print("\nThe registry defines categories for your doc IDs.")
    print("Default categories: CORE, CONFIG, TEST, SCRIPT, GUIDE\n")
    
    response = input("Would you like to customize categories now? (y/N): ").strip().lower()
    if response != 'y':
        print("You can edit registry/DOC_ID_REGISTRY.yaml later")
        return
    
    print("\nOpening registry in default editor...")
    if sys.platform == 'win32':
        os.startfile(registry_path)
    elif sys.platform == 'darwin':  # macOS
        subprocess.run(['open', registry_path])
    else:  # Linux
        subprocess.run(['xdg-open', registry_path])
    
    input("\nPress Enter after saving your changes...")

def run_initial_scan(subsystem_dir, repo_root):
    """Run initial repository scan."""
    scanner = subsystem_dir / "core" / "doc_id_scanner.py"
    
    print(f"\n🔍 Scanning repository: {repo_root}")
    print("   This may take a minute for large repositories...\n")
    
    try:
        result = subprocess.run(
            [sys.executable, str(scanner), "--repo-root", str(repo_root)],
            cwd=subsystem_dir / "core",
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Initial scan complete")
            print(result.stdout)
            return True
        else:
            print("❌ Scan failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running scanner: {e}")
        return False

def show_next_steps(subsystem_dir, repo_root):
    """Display next steps for user."""
    print_header("Setup Complete! 🎉")
    
    print("📋 Next Steps:\n")
    
    print("1. Review scan results:")
    print(f"   cat {subsystem_dir}/core/docs_inventory.jsonl\n")
    
    print("2. Assign doc IDs to files:")
    print(f"   cd {subsystem_dir}/core")
    print("   python batch_assign_docids.py --batch-size 50\n")
    
    print("3. Validate results:")
    print(f"   cd {subsystem_dir}/validation")
    print("   python validate_doc_id_coverage.py")
    print("   python validate_doc_id_uniqueness.py\n")
    
    print("4. Set up automation (optional):")
    print("   - Pre-commit hook: See INTEGRATION_GUIDE.md")
    print("   - File watcher: See INTEGRATION_GUIDE.md\n")
    
    print("📚 Documentation:")
    print(f"   - Quick Reference: {subsystem_dir}/docs/QUICK_REFERENCE.md")
    print(f"   - Complete Spec: {subsystem_dir}/docs/DOC_ID_SYSTEM_COMPLETE_SPECIFICATION.md")
    print(f"   - Integration Guide: {subsystem_dir}/INTEGRATION_GUIDE.md\n")

def main():
    """Main setup workflow."""
    print_header("Doc ID Subsystem - Quick Setup")
    
    # Step 1: Check Python version
    print_step(1, "Checking Python version")
    check_python_version()
    
    # Step 2: Detect paths
    print_step(2, "Detecting repository paths")
    repo_root = get_repo_root()
    subsystem_dir = repo_root / "doc_id_subsystem"
    
    print(f"Repository root: {repo_root}")
    print(f"Subsystem dir: {subsystem_dir}")
    
    if not subsystem_dir.exists():
        print("❌ Error: doc_id_subsystem directory not found")
        print(f"   Expected at: {subsystem_dir}")
        sys.exit(1)
    print("✅ Subsystem directory found")
    
    # Step 3: Setup registry
    print_step(3, "Setting up doc ID registry")
    if setup_registry(subsystem_dir):
        registry_path = subsystem_dir / "registry" / "DOC_ID_REGISTRY.yaml"
        customize_registry(registry_path)
    
    # Step 4: Run initial scan
    print_step(4, "Running initial repository scan")
    response = input("\nRun initial scan now? (Y/n): ").strip().lower()
    if response != 'n':
        run_initial_scan(subsystem_dir, repo_root)
    else:
        print("⏭️  Skipping initial scan (you can run it later)")
    
    # Step 5: Show next steps
    show_next_steps(subsystem_dir, repo_root)
    
    print("\n" + "=" * 70)
    print("Setup script complete!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
