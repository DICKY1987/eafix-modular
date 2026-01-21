#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264
"""
Glossary Patch Update Tool

Automates bulk updates to glossary terms using patch specifications.

Features:
- YAML-based patch specifications
- Atomic updates (all or nothing)
- Dry-run mode for preview
- Automatic metadata updates
- Changelog generation
- Validation before/after
- Git-friendly diffs

Usage:
    # Dry run (preview changes)
    python update_term.py --spec updates/add-schemas.yaml --dry-run

    # Apply patch
    python update_term.py --spec updates/add-schemas.yaml --apply

    # Single term update
    python update_term.py --term TERM-ENGINE-001 --field implementation --value "core/engine/orchestrator.py"

    # Validate after update
    python update_term.py --spec updates/add-schemas.yaml --apply --validate
"""
# DOC_ID: DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Paths
SCRIPT_DIR = Path(__file__).parent
GLOSSARY_ROOT = SCRIPT_DIR.parent
GLOSSARY_FILE = GLOSSARY_ROOT / "docs" / "DOC-GUIDE-GLOSSARY-665__glossary.md"
METADATA_FILE = (
    GLOSSARY_ROOT / "DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml"
)
CHANGELOG_FILE = (
    GLOSSARY_ROOT
    / "docs"
    / "DOC-GUIDE-DOC-GLOSSARY-CHANGELOG-871__DOC_GLOSSARY_CHANGELOG.md"
)


@dataclass
class PatchSpec:
    """Patch specification loaded from YAML."""

    patch_id: str
    description: str
    date: str
    author: str
    terms: List[Dict[str, Any]]

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "PatchSpec":
        """Load patch spec from YAML file."""
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls(
            patch_id=data.get("patch_id", ""),
            description=data.get("description", ""),
            date=data.get("date", datetime.now().strftime("%Y-%m-%d")),
            author=data.get("author", "unknown"),
            terms=data.get("terms", []),
        )


class GlossaryPatcher:
    """Applies patches to glossary and metadata."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.glossary_text = ""
        self.metadata = {}
        self.changes_made = []

    def load(self):
        """Load glossary and metadata."""
        print("📖 Loading glossary files...")

        with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
            self.glossary_text = f.read()

        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            self.metadata = yaml.safe_load(f) or {"terms": {}}

        print(f"   ✓ Loaded {GLOSSARY_FILE.name}")
        print(f"   ✓ Loaded {METADATA_FILE.name}")

    def apply_patch(self, spec: PatchSpec) -> bool:
        """Apply patch specification."""
        print(f"\n🔧 Applying patch: {spec.patch_id}")
        print(f"   Description: {spec.description}")
        print(f"   Terms to update: {len(spec.terms)}")

        if self.dry_run:
            print("   🔍 DRY RUN MODE - No changes will be saved")

        print()

        success = True
        for term_update in spec.terms:
            if not self._apply_term_update(term_update, spec):
                success = False

        return success

    def _apply_term_update(self, update: Dict[str, Any], spec: PatchSpec) -> bool:
        """Apply update to single term."""
        term_id = update.get("term_id")
        action = update.get("action")
        field = update.get("field")
        value = update.get("value")

        print(f"📝 {term_id}: {action} {field}")

        # Validate term exists
        if term_id not in self.metadata.get("terms", {}):
            print(f"   ❌ Term {term_id} not found in metadata")
            return False

        term_data = self.metadata["terms"][term_id]

        # Apply action
        if action == "update":
            success = self._update_field(term_id, term_data, field, value)
        elif action == "add":
            success = self._add_to_field(term_id, term_data, field, value)
        elif action == "remove":
            success = self._remove_from_field(term_id, term_data, field, value)
        elif action == "replace":
            success = self._replace_field(term_id, term_data, field, value)
        else:
            print(f"   ❌ Unknown action: {action}")
            return False

        if success:
            # Update metadata timestamps
            term_data["last_modified"] = datetime.now().isoformat()

            # Add to patch history
            if "patch_history" not in term_data:
                term_data["patch_history"] = []

            term_data["patch_history"].append(
                {
                    "patch_id": spec.patch_id,
                    "action": f"{action}_{field}",
                    "date": spec.date,
                    "description": spec.description,
                }
            )

            # Track change
            self.changes_made.append(
                {"term_id": term_id, "action": action, "field": field, "value": value}
            )

            print(f"   ✅ Updated")

        return success

    def _update_field(
        self, term_id: str, term_data: Dict, field: str, value: Any
    ) -> bool:
        """Update a field value."""
        # Handle nested fields (e.g., "implementation.files")
        parts = field.split(".")
        target = term_data

        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]

        final_field = parts[-1]

        # Update value
        if isinstance(value, list) and isinstance(target.get(final_field), list):
            # Extend list
            target[final_field].extend(value)
            # Remove duplicates
            target[final_field] = list(set(target[final_field]))
        else:
            target[final_field] = value

        return True

    def _add_to_field(
        self, term_id: str, term_data: Dict, field: str, value: Any
    ) -> bool:
        """Add value to field (append to list or create new field)."""
        parts = field.split(".")
        target = term_data

        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]

        final_field = parts[-1]

        if final_field not in target:
            target[final_field] = []

        if isinstance(target[final_field], list):
            if isinstance(value, list):
                target[final_field].extend(value)
            else:
                target[final_field].append(value)
        else:
            print(f"   ⚠️  Field {field} is not a list, cannot add")
            return False

        return True

    def _remove_from_field(
        self, term_id: str, term_data: Dict, field: str, value: Any
    ) -> bool:
        """Remove value from field."""
        parts = field.split(".")
        target = term_data

        for part in parts[:-1]:
            if part not in target:
                return False
            target = target[part]

        final_field = parts[-1]

        if final_field not in target:
            return False

        if isinstance(target[final_field], list):
            try:
                target[final_field].remove(value)
                return True
            except ValueError:
                print(f"   ⚠️  Value not found in {field}")
                return False
        else:
            del target[final_field]
            return True

    def _replace_field(
        self, term_id: str, term_data: Dict, field: str, value: Any
    ) -> bool:
        """Replace entire field value."""
        parts = field.split(".")
        target = term_data

        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]

        final_field = parts[-1]
        target[final_field] = value

        return True

    def save(self):
        """Save updated metadata."""
        if self.dry_run:
            print("\n🔍 DRY RUN - Changes preview:")
            print("\n" + "=" * 60)
            print(
                yaml.dump(
                    {
                        "terms": {
                            change["term_id"]: self.metadata["terms"][change["term_id"]]
                            for change in self.changes_made[:3]  # Show first 3
                        }
                    },
                    default_flow_style=False,
                )
            )
            print("=" * 60)
            print(f"\n   Total changes: {len(self.changes_made)}")
            print("   Run with --apply to save changes")
            return

        print(f"\n💾 Saving changes...")

        # Update metadata timestamps
        self.metadata["last_updated"] = datetime.now().isoformat()

        # Save metadata
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            yaml.dump(self.metadata, f, default_flow_style=False, sort_keys=False)

        print(f"   ✅ Saved {METADATA_FILE.name}")
        print(f"   ✅ Updated {len(self.changes_made)} terms")

    def update_changelog(self, spec: PatchSpec):
        """Add entry to changelog."""
        if self.dry_run:
            print("\n📋 Changelog entry (preview):")
            print(f"   Patch: {spec.patch_id}")
            print(f"   Description: {spec.description}")
            print(f"   Terms updated: {len(self.changes_made)}")
            return

        print(f"\n📋 Updating changelog...")

        # Read current changelog
        with open(CHANGELOG_FILE, "r", encoding="utf-8") as f:
            changelog = f.read()

        # Create entry
        entry = f"\n### Patch: {spec.patch_id} - {spec.date}\n\n"
        entry += f"**Description**: {spec.description}\n\n"
        entry += f"**Terms Updated**: {len(self.changes_made)}\n\n"

        # Group by action
        by_action = {}
        for change in self.changes_made:
            action = change["action"]
            if action not in by_action:
                by_action[action] = []
            by_action[action].append(change)

        for action, changes in by_action.items():
            entry += f"**{action.title()}**:\n"
            for change in changes[:10]:  # Limit to 10
                entry += f"- `{change['term_id']}` - {change['field']}\n"
            if len(changes) > 10:
                entry += f"- ... and {len(changes) - 10} more\n"
            entry += "\n"

        # Insert after "## Patch-Based Changes" section
        patch_section = "## Patch-Based Changes"
        if patch_section in changelog:
            insert_pos = changelog.find(patch_section) + len(patch_section) + 1
            changelog = changelog[:insert_pos] + entry + changelog[insert_pos:]
        else:
            # Append at end
            changelog += "\n" + entry

        # Save
        with open(CHANGELOG_FILE, "w", encoding="utf-8") as f:
            f.write(changelog)

        print(f"   ✅ Updated {CHANGELOG_FILE.name}")

    def validate(self) -> bool:
        """Run validation on updated glossary."""
        print(f"\n✅ Running validation...")

        try:
            result = subprocess.run(
                [
                    "python",
                    str(
                        SCRIPT_DIR
                        / "DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py"
                    ),
                    "--quick",
                ],
                cwd=GLOSSARY_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print("   ✅ Validation passed")
                return True
            else:
                print("   ❌ Validation failed:")
                print(result.stdout)
                return False
        except Exception as e:
            print(f"   ⚠️  Could not run validation: {e}")
            return False


def single_term_update(term_id: str, field: str, value: str, dry_run: bool = False):
    """Quick update of single term field."""
    # Create temporary patch spec
    spec = PatchSpec(
        patch_id=f"manual-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        description=f"Manual update of {term_id}.{field}",
        date=datetime.now().strftime("%Y-%m-%d"),
        author="manual",
        terms=[
            {"term_id": term_id, "action": "update", "field": field, "value": value}
        ],
    )

    patcher = GlossaryPatcher(dry_run=dry_run)
    patcher.load()

    if patcher.apply_patch(spec):
        patcher.save()
        if not dry_run:
            patcher.update_changelog(spec)
        return True

    return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Apply patches to glossary",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview)
  python update_term.py --spec updates/add-schemas.yaml --dry-run

  # Apply patch
  python update_term.py --spec updates/add-schemas.yaml --apply

  # Single term update
  python update_term.py --term TERM-ENGINE-001 \\
    --field implementation.files \\
    --value "core/engine/orchestrator.py"

  # Apply and validate
  python update_term.py --spec updates/add-schemas.yaml --apply --validate
        """,
    )

    # Patch spec mode
    parser.add_argument("--spec", type=str, help="Path to patch specification YAML")
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default: dry-run)"
    )

    # Single term mode
    parser.add_argument("--term", type=str, help="Term ID to update")
    parser.add_argument("--field", type=str, help="Field to update")
    parser.add_argument("--value", type=str, help="New value")

    # Options
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without saving"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Run validation after update"
    )
    parser.add_argument(
        "--no-changelog", action="store_true", help="Skip changelog update"
    )

    args = parser.parse_args()

    # Determine mode
    if args.spec:
        # Patch spec mode
        spec_path = (
            GLOSSARY_ROOT / "updates" / args.spec
            if "/" not in args.spec
            else Path(args.spec)
        )

        if not spec_path.exists():
            print(f"❌ Patch spec not found: {spec_path}")
            sys.exit(1)

        print(f"📦 Loading patch spec: {spec_path.name}")
        spec = PatchSpec.from_yaml(spec_path)

        patcher = GlossaryPatcher(dry_run=not args.apply or args.dry_run)
        patcher.load()

        if patcher.apply_patch(spec):
            patcher.save()

            if not patcher.dry_run and not args.no_changelog:
                patcher.update_changelog(spec)

                if args.validate:
                    if not patcher.validate():
                        print("\n⚠️  Validation failed - review changes")
                        sys.exit(1)

            print("\n✅ Patch applied successfully")
            sys.exit(0)
        else:
            print("\n❌ Patch application failed")
            sys.exit(1)

    elif args.term and args.field and args.value:
        # Single term mode
        if single_term_update(
            args.term, args.field, args.value, dry_run=args.dry_run or not args.apply
        ):
            print("\n✅ Term updated successfully")
            sys.exit(0)
        else:
            print("\n❌ Term update failed")
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
