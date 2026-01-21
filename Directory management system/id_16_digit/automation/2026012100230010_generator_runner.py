"""
doc_id: 2026012100230010
title: Generator Runner
version: 1.0
date: 2026-01-21T00:23:14Z
purpose: Execute generators with dependency tracking and build traceability
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class GeneratorRunner:
    """Executes generator records with dependency tracking."""
    
    def __init__(self, registry_path: str):
        """
        Initialize generator runner.
        
        Args:
            registry_path: Path to registry JSON file
        """
        self.registry_path = Path(registry_path)
        self.registry = self._load_registry()
        self.generators = self._extract_generators()
        
    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from file."""
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        print(f"✓ Loaded registry from {self.registry_path}")
        print(f"  Registry version: {registry.get('meta', {}).get('version')}")
        print(f"  Total records: {len(registry.get('records', []))}")
        
        return registry
    
    def _extract_generators(self) -> List[Dict[str, Any]]:
        """Extract generator records from registry."""
        records = self.registry.get('records', [])
        generators = [r for r in records if r.get('record_kind') == 'generator']
        
        print(f"✓ Found {len(generators)} generator(s)")
        
        return generators
    
    def _compute_registry_hash(self, dependency_columns: List[str]) -> str:
        """
        Compute hash of registry state for specific columns.
        
        Args:
            dependency_columns: Columns to include in hash
            
        Returns:
            SHA256 hash of dependency data
        """
        # Extract dependency data
        records = self.registry.get('records', [])
        dependency_data = []
        
        for record in records:
            row_data = {}
            for col in dependency_columns:
                if col in record:
                    row_data[col] = record[col]
            if row_data:
                dependency_data.append(row_data)
        
        # Sort for determinism
        dependency_data.sort(key=lambda x: str(x))
        
        # Hash
        data_str = json.dumps(dependency_data, sort_keys=True)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    def _filter_records(
        self,
        records: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter records by criteria.
        
        Args:
            records: Records to filter
            filters: Filter criteria (e.g., {"record_kind": "entity"})
            
        Returns:
            Filtered records
        """
        if not filters:
            return records
        
        filtered = []
        for record in records:
            matches = True
            for key, value in filters.items():
                if record.get(key) != value:
                    matches = False
                    break
            if matches:
                filtered.append(record)
        
        return filtered
    
    def _sort_records(
        self,
        records: List[Dict[str, Any]],
        sort_keys: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Sort records by keys.
        
        Args:
            records: Records to sort
            sort_keys: Keys to sort by (in order)
            
        Returns:
            Sorted records
        """
        if not sort_keys:
            return records
        
        def sort_key_func(record):
            return tuple(str(record.get(key, '')) for key in sort_keys)
        
        return sorted(records, key=sort_key_func)
    
    def _generate_output(
        self,
        generator: Dict[str, Any],
        filtered_records: List[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Generate output content.
        
        Args:
            generator: Generator record
            filtered_records: Records to include in output
            
        Returns:
            (output_content, output_path)
        """
        generator_name = generator.get('generator_name', 'unknown')
        output_path = generator.get('output_path')
        output_path_pattern = generator.get('output_path_pattern')
        output_kind = generator.get('output_kind', 'index')
        
        # Determine output path
        if output_path:
            final_output_path = output_path
        elif output_path_pattern:
            # Simple pattern replacement (expand as needed)
            final_output_path = output_path_pattern.replace('{date}', datetime.now().strftime('%Y%m%d'))
        else:
            raise ValueError(f"Generator {generator_name} missing output_path or output_path_pattern")
        
        # Generate content based on output_kind
        if output_kind == 'index':
            content = self._generate_index(generator_name, filtered_records)
        elif output_kind == 'report':
            content = self._generate_report(generator_name, filtered_records)
        elif output_kind == 'json':
            content = json.dumps(filtered_records, indent=2, ensure_ascii=False)
        elif output_kind == 'csv':
            content = self._generate_csv(filtered_records)
        else:
            content = self._generate_custom(generator, filtered_records)
        
        return content, final_output_path
    
    def _generate_index(self, name: str, records: List[Dict[str, Any]]) -> str:
        """Generate markdown index."""
        lines = [
            f"# {name}",
            "",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Total records: {len(records)}",
            "",
            "## Records",
            ""
        ]
        
        for record in records:
            record_id = record.get('record_id', 'UNKNOWN')
            entity_id = record.get('entity_id', '')
            filename = record.get('filename', '')
            directory = record.get('directory_path', '')
            
            if filename:
                lines.append(f"- `{record_id}` - {directory}/{filename}")
            else:
                lines.append(f"- `{record_id}` - {entity_id}")
        
        return "\n".join(lines)
    
    def _generate_report(self, name: str, records: List[Dict[str, Any]]) -> str:
        """Generate markdown report."""
        lines = [
            f"# {name}",
            "",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## Summary",
            f"- Total records: {len(records)}",
            ""
        ]
        
        # Group by entity_kind
        by_kind = {}
        for record in records:
            kind = record.get('entity_kind', 'unknown')
            by_kind[kind] = by_kind.get(kind, 0) + 1
        
        if by_kind:
            lines.append("## By Entity Kind")
            for kind, count in sorted(by_kind.items()):
                lines.append(f"- {kind}: {count}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_csv(self, records: List[Dict[str, Any]]) -> str:
        """Generate CSV output."""
        if not records:
            return ""
        
        # Get all unique columns
        columns = set()
        for record in records:
            columns.update(record.keys())
        
        columns = sorted(columns)
        
        # Write CSV
        lines = [",".join(columns)]
        for record in records:
            row = [str(record.get(col, '')) for col in columns]
            lines.append(",".join(row))
        
        return "\n".join(lines)
    
    def _generate_custom(self, generator: Dict[str, Any], records: List[Dict[str, Any]]) -> str:
        """Generate custom output (placeholder)."""
        return f"# Custom Generator Output\n\nRecords: {len(records)}\n"
    
    def _compute_output_hash(self, content: str) -> str:
        """Compute SHA256 hash of output content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def run_generator(
        self,
        generator: Dict[str, Any],
        dry_run: bool = False
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Run single generator.
        
        Args:
            generator: Generator record
            dry_run: If True, don't write output (just report)
            
        Returns:
            (success, message, build_report)
        """
        generator_id = generator.get('generator_id', 'UNKNOWN')
        generator_name = generator.get('generator_name', 'unknown')
        
        print(f"\n{'='*60}")
        print(f"Running generator: {generator_name} ({generator_id})")
        print(f"{'='*60}")
        
        # Validate required fields
        declared_dependencies = generator.get('declared_dependencies')
        if not declared_dependencies:
            return False, "Generator missing declared_dependencies", {}
        
        sort_keys = generator.get('sort_keys')
        sort_rule_id = generator.get('sort_rule_id')
        if not sort_keys and not sort_rule_id:
            return False, "Generator missing sort_keys or sort_rule_id", {}
        
        output_path = generator.get('output_path')
        output_path_pattern = generator.get('output_path_pattern')
        if not output_path and not output_path_pattern:
            return False, "Generator missing output_path or output_path_pattern", {}
        
        # Compute registry hash for dependencies
        source_registry_hash = self._compute_registry_hash(declared_dependencies)
        print(f"✓ Computed source registry hash: {source_registry_hash[:16]}...")
        
        # Check if regeneration needed
        last_source_hash = generator.get('source_registry_hash')
        if last_source_hash == source_registry_hash and not dry_run:
            print(f"✓ No changes detected (hash match), skipping generation")
            return True, "Skipped (no changes)", {}
        
        # Filter records
        records = self.registry.get('records', [])
        input_filters = generator.get('input_filters', {})
        filtered_records = self._filter_records(records, input_filters)
        print(f"✓ Filtered {len(records)} → {len(filtered_records)} records")
        
        # Sort records
        sorted_records = self._sort_records(filtered_records, sort_keys)
        print(f"✓ Sorted by: {sort_keys or 'default'}")
        
        # Generate output
        output_content, output_file_path = self._generate_output(generator, sorted_records)
        output_hash = self._compute_output_hash(output_content)
        print(f"✓ Generated output: {len(output_content)} bytes")
        print(f"  Output hash: {output_hash[:16]}...")
        print(f"  Output path: {output_file_path}")
        
        # Write output
        if not dry_run:
            output_path_obj = Path(output_file_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path_obj, 'w', encoding='utf-8') as f:
                f.write(output_content)
            
            print(f"✓ Wrote output to {output_file_path}")
        else:
            print(f"✓ DRY RUN: Would write to {output_file_path}")
        
        # Build report
        build_report = {
            'generator_id': generator_id,
            'generator_name': generator_name,
            'build_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'source_registry_hash': source_registry_hash,
            'output_hash': output_hash,
            'output_path': output_file_path,
            'records_processed': len(sorted_records),
            'dry_run': dry_run
        }
        
        return True, "Generated successfully", build_report
    
    def run_all_generators(self, dry_run: bool = False) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Run all generators in registry.
        
        Args:
            dry_run: If True, don't write outputs
            
        Returns:
            (success_count, failed_count, build_reports)
        """
        success_count = 0
        failed_count = 0
        build_reports = []
        
        print(f"\n{'='*60}")
        print(f"Running {len(self.generators)} generator(s)")
        print(f"{'='*60}")
        
        for generator in self.generators:
            success, message, build_report = self.run_generator(generator, dry_run)
            
            if success:
                success_count += 1
            else:
                failed_count += 1
                print(f"✗ Failed: {message}")
            
            if build_report:
                build_reports.append(build_report)
        
        return success_count, failed_count, build_reports


def main():
    """CLI entry point for generator runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run registry generators')
    parser.add_argument('registry', help='Path to registry JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be generated without writing')
    parser.add_argument('--generator-id', help='Run specific generator by ID')
    
    args = parser.parse_args()
    
    print(f"Generator Runner")
    print("=" * 60)
    
    # Run generators
    runner = GeneratorRunner(args.registry)
    
    if args.generator_id:
        # Run specific generator
        generator = next((g for g in runner.generators if g.get('generator_id') == args.generator_id), None)
        if not generator:
            print(f"✗ Generator not found: {args.generator_id}")
            sys.exit(1)
        
        success, message, build_report = runner.run_generator(generator, args.dry_run)
        
        print("\n" + "=" * 60)
        if success:
            print("✓ Generator completed successfully")
            sys.exit(0)
        else:
            print(f"✗ Generator failed: {message}")
            sys.exit(1)
    else:
        # Run all generators
        success_count, failed_count, build_reports = runner.run_all_generators(args.dry_run)
        
        print("\n" + "=" * 60)
        print(f"Results:")
        print(f"  Succeeded: {success_count}")
        print(f"  Failed: {failed_count}")
        print(f"  Total: {len(runner.generators)}")
        
        if failed_count > 0:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == '__main__':
    main()
