#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265
"""
Glossary Validation Tool

Validates glossary structure, content quality, and cross-references.

Usage:
    python validate_glossary.py                    # Full validation
    python validate_glossary.py --check-orphans    # Check orphaned terms only
    python validate_glossary.py --check-paths      # Verify implementation paths
    python validate_glossary.py --quick            # Fast validation (structure only)
"""
# DOC_ID: DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set
import yaml

# Add project root to path
# Script location: /glossary/scripts/validate_glossary.py
GLOSSARY_ROOT = Path(__file__).parent.parent  # /glossary/
PROJECT_ROOT = GLOSSARY_ROOT.parent  # Repository root


class GlossaryValidator:
    """Validates DOC-GUIDE-GLOSSARY-665__glossary.md and DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml"""

    def __init__(self, glossary_path: Path, metadata_path: Path):
        self.glossary_path = glossary_path
        self.metadata_path = metadata_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.terms: Dict[str, Dict] = {}
        self.term_names: Set[str] = set()
        self.related_links: Dict[str, Set[str]] = {}

    def validate(self, quick: bool = False, check_orphans: bool = False,
                 check_paths: bool = False) -> Tuple[int, int]:
        """Run validation checks. Returns (errors, warnings)."""
        print("🔍 Validating glossary...")

        # Load files
        if not self._load_files():
            return len(self.errors), len(self.warnings)

        if quick:
            self._validate_structure()
        elif check_orphans:
            self._check_orphaned_terms()
        elif check_paths:
            self._validate_implementation_paths()
        else:
            # Full validation
            self._validate_structure()
            self._validate_content()
            self._validate_metadata()
            self._validate_cross_references()
            self._validate_quality()

        self._print_results()
        return len(self.errors), len(self.warnings)

    def _load_files(self) -> bool:
        """Load glossary and metadata files."""
        try:
            with open(self.glossary_path, 'r', encoding='utf-8') as f:
                self.glossary_text = f.read()
            print(f"✅ Loaded {self.glossary_path}")
        except Exception as e:
            self.errors.append(f"Failed to load glossary: {e}")
            return False

        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = yaml.safe_load(f)
            print(f"✅ Loaded {self.metadata_path}")
        except Exception as e:
            self.warnings.append(f"Failed to load metadata: {e}")
            self.metadata = {}

        return True

    def _validate_structure(self):
        """Validate glossary document structure."""
        print("\n📋 Validating structure...")

        # Check required sections
        required_sections = [
            "# Glossary",
            "## A",  # At least one alphabetical section
            "## Index by Category",
            "## Quick Reference",
            "## See Also"
        ]

        for section in required_sections:
            if section not in self.glossary_text:
                self.errors.append(f"Missing required section: {section}")

        # Extract all terms
        term_pattern = r'^### (.+?)$'
        for match in re.finditer(term_pattern, self.glossary_text, re.MULTILINE):
            term_name = match.group(1).strip()
            self.term_names.add(term_name)

        print(f"   Found {len(self.term_names)} terms")

        # Check alphabetical ordering within sections
        current_section = None
        last_term = None
        for line in self.glossary_text.split('\n'):
            if line.startswith('## ') and len(line) == 4:  # Single letter section
                current_section = line[3]
                last_term = None
            elif line.startswith('### '):
                term = line[4:].strip()
                if current_section and last_term:
                    if term.lower() < last_term.lower():
                        self.warnings.append(
                            f"Term '{term}' out of alphabetical order in section {current_section}"
                        )
                last_term = term

    def _validate_content(self):
        """Validate term content quality."""
        print("\n📝 Validating content quality...")

        # Pattern for term sections
        term_block_pattern = r'### (.+?)\n(.*?)(?=\n##|\n###|$)'

        for match in re.finditer(term_block_pattern, self.glossary_text,
                                 re.DOTALL | re.MULTILINE):
            term_name = match.group(1).strip()
            term_content = match.group(2)

            # Check for required fields
            if '**Category**:' not in term_content:
                self.errors.append(f"Term '{term_name}' missing Category field")

            if '**Definition**:' not in term_content:
                self.errors.append(f"Term '{term_name}' missing Definition field")

            # Check definition length
            def_match = re.search(r'\*\*Definition\*\*:\s*(.+?)(?=\n\n|\*\*)',
                                 term_content, re.DOTALL)
            if def_match:
                definition = def_match.group(1).strip()
                if len(definition) < 20:
                    self.warnings.append(
                        f"Term '{term_name}' has short definition ({len(definition)} chars)"
                    )
                if len(definition) > 1000:
                    self.warnings.append(
                        f"Term '{term_name}' has very long definition ({len(definition)} chars)"
                    )

                # Check definition style
                bad_starts = ['It is', 'This is', 'A thing that']
                if any(definition.startswith(bad) for bad in bad_starts):
                    self.warnings.append(
                        f"Term '{term_name}' has weak definition start"
                    )

            # Extract related terms
            related_pattern = r'\[(.+?)\]\(#(.+?)\)'
            related = set(re.findall(related_pattern, term_content))
            self.related_links[term_name] = {r[0] for r in related}

            if len(related) < 1:
                self.warnings.append(
                    f"Term '{term_name}' has no related terms (recommend 2-5)"
                )

    def _validate_metadata(self):
        """Validate metadata file."""
        print("\n🗂️  Validating metadata...")

        if not self.metadata:
            self.warnings.append("No metadata file loaded")
            return

        # Check schema version
        if 'schema_version' not in self.metadata:
            self.errors.append("Metadata missing schema_version")

        # Validate term entries
        meta_terms = self.metadata.get('terms', {})

        for term_id, term_data in meta_terms.items():
            # Check term_id format
            if not re.match(r'^TERM-[A-Z]+-\d{3}$', term_id):
                self.errors.append(
                    f"Invalid term_id format: {term_id} (expected TERM-XXX-NNN)"
                )

            # Check required metadata fields
            required = ['name', 'category', 'status', 'added_date', 'last_modified']
            for field in required:
                if field not in term_data:
                    self.errors.append(
                        f"Term {term_id} missing required metadata field: {field}"
                    )

            # Validate status
            valid_status = ['proposed', 'draft', 'active', 'deprecated', 'archived']
            if term_data.get('status') not in valid_status:
                self.errors.append(
                    f"Term {term_id} has invalid status: {term_data.get('status')}"
                )

        # Check statistics match
        if 'statistics' in self.metadata:
            stats = self.metadata['statistics']
            total = sum(stats.get('by_status', {}).values())
            if total != len(meta_terms):
                self.warnings.append(
                    f"Statistics mismatch: counted {total} terms, "
                    f"but {len(meta_terms)} defined"
                )

    def _validate_cross_references(self):
        """Validate cross-references between terms."""
        print("\n🔗 Validating cross-references...")

        # Check all related term links point to existing terms
        for term, related in self.related_links.items():
            for related_term in related:
                if related_term not in self.term_names:
                    self.errors.append(
                        f"Term '{term}' links to non-existent term '{related_term}'"
                    )

        # Check for orphaned terms (not linked by any other term)
        all_linked = set()
        for related in self.related_links.values():
            all_linked.update(related)

        orphans = self.term_names - all_linked
        if orphans:
            # Filter out section headers and index entries
            real_orphans = {o for o in orphans if not o.startswith('See')}
            if real_orphans:
                self.warnings.append(
                    f"Found {len(real_orphans)} orphaned terms: {list(real_orphans)[:5]}"
                )

    def _validate_implementation_paths(self):
        """Validate implementation file paths exist."""
        print("\n📁 Validating implementation paths...")

        meta_terms = self.metadata.get('terms', {})

        for term_id, term_data in meta_terms.items():
            impl = term_data.get('implementation', {})
            files = impl.get('files', [])

            for file_path in files:
                full_path = PROJECT_ROOT / file_path
                if not full_path.exists():
                    self.warnings.append(
                        f"Term {term_id} references non-existent file: {file_path}"
                    )

    def _check_orphaned_terms(self):
        """Check for orphaned terms only."""
        print("\n🔍 Checking for orphaned terms...")

        # Extract all terms
        term_pattern = r'^### (.+?)$'
        for match in re.finditer(term_pattern, self.glossary_text, re.MULTILINE):
            term_name = match.group(1).strip()
            self.term_names.add(term_name)

        # Extract related links
        link_pattern = r'\[(.+?)\]\(#(.+?)\)'
        for match in re.finditer(link_pattern, self.glossary_text):
            linked_term = match.group(1)
            self.related_links.setdefault('_all', set()).add(linked_term)

        all_linked = self.related_links.get('_all', set())
        orphans = self.term_names - all_linked

        if orphans:
            print(f"\n⚠️  Found {len(orphans)} orphaned terms:")
            for orphan in sorted(orphans):
                print(f"   - {orphan}")
        else:
            print("✅ No orphaned terms found")

    def _validate_quality(self):
        """Check overall quality metrics."""
        print("\n📊 Checking quality metrics...")

        # Calculate metrics
        total_terms = len(self.term_names)
        terms_with_examples = sum(
            1 for t in self.term_names
            if f"### {t}" in self.glossary_text and "```" in self.glossary_text
        )

        meta_terms = self.metadata.get('terms', {})
        terms_with_impl = sum(
            1 for t in meta_terms.values()
            if t.get('implementation', {}).get('files')
        )

        print(f"   Total terms: {total_terms}")
        print(f"   Terms with implementation: {terms_with_impl}/{len(meta_terms)}")
        print(f"   Average related terms: {sum(len(r) for r in self.related_links.values()) / max(len(self.related_links), 1):.1f}")

        # Quality targets
        if terms_with_impl < len(meta_terms) * 0.9:
            self.warnings.append(
                f"Only {terms_with_impl}/{len(meta_terms)} terms have implementation references (target: 90%)"
            )

    def _print_results(self):
        """Print validation results."""
        print("\n" + "="*60)

        if self.errors:
            print(f"\n❌ {len(self.errors)} ERRORS:")
            for error in self.errors:
                print(f"   • {error}")

        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All validation checks passed!")

        print("\n" + "="*60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate glossary structure and content")
    parser.add_argument('--quick', action='store_true',
                       help='Fast validation (structure only)')
    parser.add_argument('--check-orphans', action='store_true',
                       help='Check for orphaned terms only')
    parser.add_argument('--check-paths', action='store_true',
                       help='Verify implementation paths exist')

    args = parser.parse_args()

    # Paths
    glossary_path = GLOSSARY_ROOT / "docs" / "DOC-GUIDE-GLOSSARY-665__glossary.md"
    metadata_path = (
        GLOSSARY_ROOT / "DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml"
    )

    # Validate
    validator = GlossaryValidator(glossary_path, metadata_path)
    errors, warnings = validator.validate(
        quick=args.quick,
        check_orphans=args.check_orphans,
        check_paths=args.check_paths
    )

    # Exit code
    sys.exit(1 if errors > 0 else 0)


if __name__ == '__main__':
    main()
