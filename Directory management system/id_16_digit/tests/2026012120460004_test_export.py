#!/usr/bin/env python3
"""
doc_id: 2026012120460004
Test suite for export functionality (CSV and SQLite)

Tests deterministic ordering, correct serialization, and queryable SQLite output.
"""

import os
import sys
import json
import csv
import sqlite3
import tempfile
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util

# Dynamic import of CLI
cli_path = Path(__file__).parent.parent / "automation" / "2026012120420011_registry_cli.py"
spec = importlib.util.spec_from_file_location("registry_cli", cli_path)
registry_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry_cli)
RegistryCLI = registry_cli.RegistryCLI


def test_csv_export_deterministic_columns():
    """Test that CSV export has deterministic column ordering."""
    print("Test: CSV export deterministic columns")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        csv_path = Path(tmpdir) / "export.csv"
        
        # Create test registry
        test_registry = {
            "meta": {"version": "1.0"},
            "records": [
                {
                    "record_id": "ENT-001",
                    "record_kind": "entity",
                    "doc_id": "1234567890123456",
                    "entity_kind": "file",
                    "filename": "test.py",
                    "extension": "py",
                    "extra_field": "value"
                },
                {
                    "record_id": "ENT-002",
                    "record_kind": "entity",
                    "doc_id": "1234567890123457",
                    "entity_kind": "directory",
                    "filename": "src",
                    "another_field": "data"
                }
            ]
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(test_registry, f)
        
        # Export to CSV
        cli = RegistryCLI()
        cli.registry_path = registry_path
        result = cli._export_csv(test_registry["records"], str(csv_path), verbose=False)
        
        assert result == 0, "Export failed"
        assert csv_path.exists(), "CSV file not created"
        
        # Read CSV and check header
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            # Check priority columns come first
            assert headers[0] == "record_id", "record_id not first column"
            assert headers[1] == "record_kind", "record_kind not second column"
            assert headers[2] == "doc_id", "doc_id not third column"
            
            # Check all records have same columns
            rows = list(reader)
            assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
            
            # Each row should have all columns (blanks for missing)
            for row in rows:
                assert len(row) == len(headers), "Row has different column count"
        
        print("  ✓ CSV columns deterministic and consistent")


def test_csv_export_stable_ordering():
    """Test that CSV rows are sorted stably (by record_kind, then record_id)."""
    print("Test: CSV export stable row ordering")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        csv_path = Path(tmpdir) / "export.csv"
        
        # Create test registry with records in random order
        test_registry = {
            "meta": {"version": "1.0"},
            "records": [
                {"record_id": "ENT-003", "record_kind": "entity", "filename": "c.py"},
                {"record_id": "EDGE-001", "record_kind": "edge", "source_doc_id": "123", "target_doc_id": "456"},
                {"record_id": "ENT-001", "record_kind": "entity", "filename": "a.py"},
                {"record_id": "ENT-002", "record_kind": "entity", "filename": "b.py"},
            ]
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(test_registry, f)
        
        # Export to CSV
        cli = RegistryCLI()
        cli.registry_path = registry_path
        result = cli._export_csv(test_registry["records"], str(csv_path), verbose=False)
        
        assert result == 0, "Export failed"
        
        # Read CSV and check ordering
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check ordering: edge records before entity records (alphabetical)
            # Then within each kind, sorted by record_id
            assert rows[0]["record_id"] == "EDGE-001", "Ordering wrong"
            assert rows[1]["record_id"] == "ENT-001", "Ordering wrong"
            assert rows[2]["record_id"] == "ENT-002", "Ordering wrong"
            assert rows[3]["record_id"] == "ENT-003", "Ordering wrong"
        
        print("  ✓ CSV rows stably ordered")


def test_csv_export_serializes_complex_fields():
    """Test that lists/dicts are serialized as JSON strings."""
    print("Test: CSV serializes complex fields")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        csv_path = Path(tmpdir) / "export.csv"
        
        test_registry = {
            "meta": {"version": "1.0"},
            "records": [
                {
                    "record_id": "ENT-001",
                    "record_kind": "entity",
                    "semantic_tags": ["policy", "validator"],
                    "metadata": {"key": "value", "count": 42}
                }
            ]
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(test_registry, f)
        
        cli = RegistryCLI()
        cli.registry_path = registry_path
        result = cli._export_csv(test_registry["records"], str(csv_path), verbose=False)
        
        assert result == 0, "Export failed"
        
        # Read CSV and check serialization
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            
            # Check list serialized as JSON
            tags = json.loads(row["semantic_tags"])
            assert tags == ["policy", "validator"], "List not serialized correctly"
            
            # Check dict serialized as JSON
            metadata = json.loads(row["metadata"])
            assert metadata == {"key": "value", "count": 42}, "Dict not serialized correctly"
        
        print("  ✓ Complex fields serialized correctly")


def test_sqlite_export_creates_tables():
    """Test that SQLite export creates correct table structure."""
    print("Test: SQLite creates tables with indexes")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        sqlite_path = Path(tmpdir) / "export.sqlite"
        
        test_registry = {
            "meta": {"version": "1.0", "created_at": "2026-01-21"},
            "records": [
                {
                    "record_id": "ENT-001",
                    "record_kind": "entity",
                    "doc_id": "1234567890123456",
                    "entity_kind": "file",
                    "filename": "test.py"
                },
                {
                    "record_id": "EDGE-001",
                    "record_kind": "edge",
                    "source_doc_id": "1234567890123456",
                    "target_doc_id": "1234567890123457",
                    "rel_type": "IMPORTS"
                },
                {
                    "record_id": "GEN-001",
                    "record_kind": "generator",
                    "generator_kind": "compile",
                    "output_doc_id": "1234567890123458"
                }
            ]
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(test_registry, f)
        
        cli = RegistryCLI()
        cli.registry_path = registry_path
        result = cli._export_sqlite(test_registry["records"], test_registry, str(sqlite_path), verbose=False)
        
        assert result == 0, "Export failed"
        assert sqlite_path.exists(), "SQLite DB not created"
        
        # Check tables exist
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert "meta" in tables, "meta table missing"
        assert "entity_records" in tables, "entity_records table missing"
        assert "edge_records" in tables, "edge_records table missing"
        assert "generator_records" in tables, "generator_records table missing"
        
        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name")
        indexes = [row[0] for row in cursor.fetchall()]
        
        assert "idx_entity_doc_id" in indexes, "entity doc_id index missing"
        assert "idx_edge_source" in indexes, "edge source index missing"
        
        conn.close()
        
        print("  ✓ SQLite tables and indexes created")


def test_sqlite_export_row_counts():
    """Test that SQLite export has correct row counts."""
    print("Test: SQLite row counts match input")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        sqlite_path = Path(tmpdir) / "export.sqlite"
        
        test_registry = {
            "meta": {"version": "1.0"},
            "records": [
                {"record_id": "ENT-001", "record_kind": "entity", "doc_id": "111", "entity_kind": "file"},
                {"record_id": "ENT-002", "record_kind": "entity", "doc_id": "222", "entity_kind": "file"},
                {"record_id": "EDGE-001", "record_kind": "edge", "source_doc_id": "111", "target_doc_id": "222"},
                {"record_id": "GEN-001", "record_kind": "generator", "generator_kind": "test"},
            ]
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(test_registry, f)
        
        cli = RegistryCLI()
        cli.registry_path = registry_path
        result = cli._export_sqlite(test_registry["records"], test_registry, str(sqlite_path), verbose=False)
        
        assert result == 0, "Export failed"
        
        # Check row counts
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM entity_records")
        entity_count = cursor.fetchone()[0]
        assert entity_count == 2, f"Expected 2 entity records, got {entity_count}"
        
        cursor.execute("SELECT COUNT(*) FROM edge_records")
        edge_count = cursor.fetchone()[0]
        assert edge_count == 1, f"Expected 1 edge record, got {edge_count}"
        
        cursor.execute("SELECT COUNT(*) FROM generator_records")
        gen_count = cursor.fetchone()[0]
        assert gen_count == 1, f"Expected 1 generator record, got {gen_count}"
        
        conn.close()
        
        print("  ✓ SQLite row counts correct")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing export functionality")
    print("=" * 60)
    print()
    
    try:
        test_csv_export_deterministic_columns()
        test_csv_export_stable_ordering()
        test_csv_export_serializes_complex_fields()
        test_sqlite_export_creates_tables()
        test_sqlite_export_row_counts()
        
        print()
        print("=" * 60)
        print("✅ All export tests PASSED")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
