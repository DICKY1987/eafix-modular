#!/usr/bin/env python3
# doc_id: DOC-DOC-0027
# DOC_ID: DOC-CONTRACT-0002
"""
CSV Artifact Validator

Validates CSV files against documented schemas and atomic write policies.
Checks headers, file_seq monotonicity, checksum integrity, and data types.
"""

import csv
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

from .models.csv_models import (
    ActiveCalendarSignal, ReentryDecision, TradeResult, HealthMetric
)

logger = logging.getLogger(__name__)


class CSVArtifactValidator:
    """Validates CSV files against schemas and atomic write policies."""
    
    def __init__(self):
        """Initialize validator with schema mappings."""
        self.schema_models = {
            "active_calendar_signals": ActiveCalendarSignal,
            "reentry_decisions": ReentryDecision,
            "trade_results": TradeResult,
            "health_metrics": HealthMetric,
        }
        
        # Expected headers for each CSV type
        self.expected_headers = {
            "active_calendar_signals": [
                "file_seq", "checksum_sha256", "timestamp", "calendar_id", "symbol",
                "impact_level", "proximity_state", "anticipation_event", "direction_bias", "confidence_score"
            ],
            "reentry_decisions": [
                "file_seq", "checksum_sha256", "timestamp", "trade_id", "hybrid_id", "symbol",
                "outcome_class", "duration_class", "reentry_action", "parameter_set_id",
                "resolved_tier", "chain_position", "lot_size", "stop_loss", "take_profit"
            ],
            "trade_results": [
                "file_seq", "checksum_sha256", "timestamp", "trade_id", "symbol", "direction",
                "lot_size", "open_price", "close_price", "open_time", "close_time", "duration_minutes",
                "profit_loss", "profit_loss_pips", "stop_loss", "take_profit", "close_reason",
                "commission", "swap", "magic_number", "comment"
            ],
            "health_metrics": [
                "file_seq", "checksum_sha256", "timestamp", "service_name", "metric_name",
                "metric_value", "metric_unit", "health_status", "cpu_usage_percent", 
                "memory_usage_percent", "disk_usage_percent", "active_connections",
                "messages_processed", "error_count", "uptime_seconds"
            ]
        }
    
    def detect_csv_type(self, file_path: Path) -> Optional[str]:
        """Detect CSV type from filename."""
        filename = file_path.name.lower()
        
        for csv_type in self.schema_models.keys():
            if filename.startswith(csv_type.replace("_", "_")):
                return csv_type
        
        return None
    
    def validate_headers(self, headers: List[str], csv_type: str) -> Tuple[bool, List[str]]:
        """Validate CSV headers against expected schema."""
        if csv_type not in self.expected_headers:
            return False, [f"Unknown CSV type: {csv_type}"]
        
        expected = set(self.expected_headers[csv_type])
        actual = set(headers)
        
        errors = []
        
        # Check for missing required headers
        missing = expected - actual
        if missing:
            errors.append(f"Missing required headers: {sorted(missing)}")
        
        # Check for unexpected headers
        extra = actual - expected
        if extra:
            errors.append(f"Unexpected headers: {sorted(extra)}")
        
        return len(errors) == 0, errors
    
    def compute_row_checksum(self, row_data: Dict[str, Any]) -> str:
        """Compute SHA-256 checksum for CSV row (excluding checksum column)."""
        # Create ordered string of all values except checksum
        ordered_values = []
        for key in sorted(row_data.keys()):
            if key != 'checksum_sha256':
                value = row_data[key]
                ordered_values.append(str(value))
        
        # Join values and compute hash
        row_string = '|'.join(ordered_values)
        return hashlib.sha256(row_string.encode('utf-8')).hexdigest()
    
    def validate_file_sequence(self, rows: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate file_seq is monotonically increasing."""
        errors = []
        prev_seq = 0
        
        for i, row in enumerate(rows):
            try:
                current_seq = int(row.get('file_seq', 0))
                if current_seq <= prev_seq:
                    errors.append(f"Row {i+1}: file_seq {current_seq} not greater than previous {prev_seq}")
                prev_seq = current_seq
            except (ValueError, TypeError):
                errors.append(f"Row {i+1}: file_seq is not a valid integer: {row.get('file_seq')}")
        
        return len(errors) == 0, errors
    
    def validate_checksums(self, rows: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate SHA-256 checksums for all rows."""
        errors = []
        
        for i, row in enumerate(rows):
            stored_checksum = row.get('checksum_sha256', '')
            
            # Validate checksum format
            if not re.match(r'^[a-f0-9]{64}$', stored_checksum.lower()):
                errors.append(f"Row {i+1}: invalid checksum format: {stored_checksum}")
                continue
            
            # Compute expected checksum
            row_copy = row.copy()
            row_copy.pop('checksum_sha256', None)
            expected_checksum = self.compute_row_checksum(row_copy)
            
            # Compare checksums
            if stored_checksum.lower() != expected_checksum:
                errors.append(f"Row {i+1}: checksum mismatch. Expected: {expected_checksum}, Got: {stored_checksum}")
        
        return len(errors) == 0, errors
    
    def validate_data_types(self, rows: List[Dict[str, Any]], csv_type: str) -> Tuple[bool, List[str]]:
        """Validate data types using Pydantic models."""
        if csv_type not in self.schema_models:
            return False, [f"No schema model for CSV type: {csv_type}"]
        
        model_class = self.schema_models[csv_type]
        errors = []
        
        for i, row in enumerate(rows):
            try:
                # Convert string timestamps to datetime objects for Pydantic validation
                row_copy = row.copy()
                
                # Handle timestamp fields
                timestamp_fields = ['timestamp', 'open_time', 'close_time']
                for field in timestamp_fields:
                    if field in row_copy and isinstance(row_copy[field], str):
                        try:
                            # Try parsing ISO format
                            row_copy[field] = datetime.fromisoformat(row_copy[field].replace('Z', '+00:00'))
                        except ValueError:
                            # If that fails, keep as string and let Pydantic handle it
                            pass
                
                # Handle boolean fields
                boolean_fields = ['anticipation_event', 'sl_hit', 'tp_hit']
                for field in boolean_fields:
                    if field in row_copy and isinstance(row_copy[field], str):
                        if row_copy[field].lower() in ['true', '1', 'yes']:
                            row_copy[field] = True
                        elif row_copy[field].lower() in ['false', '0', 'no']:
                            row_copy[field] = False
                
                # Handle numeric fields
                numeric_fields = ['file_seq', 'confidence_score', 'lot_size', 'open_price', 'close_price',
                                'duration_minutes', 'profit_loss', 'profit_loss_pips', 'stop_loss', 'take_profit',
                                'commission', 'swap', 'magic_number', 'metric_value', 'cpu_usage_percent',
                                'memory_usage_percent', 'disk_usage_percent', 'active_connections',
                                'messages_processed', 'error_count', 'uptime_seconds', 'sl_pips', 'tp_pips']
                
                for field in numeric_fields:
                    if field in row_copy and isinstance(row_copy[field], str):
                        try:
                            if field == 'file_seq' or field in ['duration_minutes', 'magic_number', 'active_connections',
                                                              'messages_processed', 'error_count', 'uptime_seconds', 
                                                              'sl_pips', 'tp_pips']:
                                row_copy[field] = int(row_copy[field])
                            else:
                                row_copy[field] = float(row_copy[field])
                        except ValueError:
                            # Let Pydantic handle the validation error
                            pass
                
                # Validate with Pydantic model
                model_class(**row_copy)
                
            except Exception as e:
                errors.append(f"Row {i+1}: Data validation error: {str(e)}")
        
        return len(errors) == 0, errors
    
    def validate_atomic_write_compliance(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Check if file follows atomic write naming conventions."""
        errors = []
        
        # Check filename pattern
        filename = file_path.name
        if filename.endswith('.tmp'):
            errors.append("File appears to be temporary (.tmp) - may indicate incomplete write")
        
        # Check filename format: {base}_YYYYMMDD_HHMMSS.csv
        pattern = r'^[a-z_]+_\d{8}_\d{6}\.csv$'
        if not re.match(pattern, filename):
            errors.append(f"Filename does not follow atomic write convention: {filename}")
        
        # Check if file is writable (not locked)
        try:
            with open(file_path, 'r+'):
                pass
        except PermissionError:
            errors.append("File is locked - may indicate ongoing write operation")
        except Exception:
            # Other exceptions are fine (file might be read-only by design)
            pass
        
        return len(errors) == 0, errors
    
    def validate_csv_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a single CSV file comprehensively."""
        result = {
            "file": str(file_path),
            "valid": False,
            "csv_type": None,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        try:
            # Check if file exists
            if not file_path.exists():
                result["errors"].append(f"File not found: {file_path}")
                return result
            
            # Detect CSV type
            csv_type = self.detect_csv_type(file_path)
            result["csv_type"] = csv_type
            
            if not csv_type:
                result["errors"].append("Could not detect CSV type from filename")
                return result
            
            # Read CSV file
            rows = []
            headers = []
            
            try:
                with open(file_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    headers = list(reader.fieldnames or [])
                    rows = list(reader)
            except Exception as e:
                result["errors"].append(f"Failed to read CSV file: {e}")
                return result
            
            result["stats"]["total_rows"] = len(rows)
            result["stats"]["total_headers"] = len(headers)
            
            # Validate headers
            headers_valid, header_errors = self.validate_headers(headers, csv_type)
            result["errors"].extend(header_errors)
            
            # Validate atomic write compliance
            atomic_valid, atomic_errors = self.validate_atomic_write_compliance(file_path)
            result["errors"].extend(atomic_errors)
            
            # If we have data, validate it
            if rows:
                # Validate file sequence
                seq_valid, seq_errors = self.validate_file_sequence(rows)
                result["errors"].extend(seq_errors)
                
                # Validate checksums
                checksum_valid, checksum_errors = self.validate_checksums(rows)
                result["errors"].extend(checksum_errors)
                
                # Validate data types
                types_valid, type_errors = self.validate_data_types(rows, csv_type)
                result["errors"].extend(type_errors)
            
            # Overall validation status
            result["valid"] = len(result["errors"]) == 0
            
        except Exception as e:
            result["errors"].append(f"Unexpected validation error: {e}")
        
        return result
    
    def validate_directory(self, directory: Path, pattern: str = "*.csv") -> Dict[str, Any]:
        """Validate all CSV files in a directory."""
        results = {
            "directory": str(directory),
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "file_results": {}
        }
        
        if not directory.exists():
            results["errors"] = [f"Directory not found: {directory}"]
            return results
        
        csv_files = list(directory.glob(pattern))
        results["total_files"] = len(csv_files)
        
        for csv_file in csv_files:
            file_result = self.validate_csv_file(csv_file)
            results["file_results"][csv_file.name] = file_result
            
            if file_result["valid"]:
                results["valid_files"] += 1
            else:
                results["invalid_files"] += 1
        
        return results
    
    def generate_validation_report(self, results: Dict[str, Any]) -> str:
        """Generate a readable validation report."""
        report_lines = []
        report_lines.append("# CSV Artifact Validation Report")
        report_lines.append(f"Generated at: {datetime.utcnow().isoformat()}Z")
        report_lines.append("")
        
        if "directory" in results:
            # Directory validation report
            report_lines.append(f"## Directory: {results['directory']}")
            report_lines.append(f"Total files: {results['total_files']}")
            report_lines.append(f"Valid files: {results['valid_files']}")
            report_lines.append(f"Invalid files: {results['invalid_files']}")
            report_lines.append("")
            
            for filename, file_result in results["file_results"].items():
                status = "✓" if file_result["valid"] else "✗"
                csv_type = file_result.get("csv_type", "unknown")
                
                report_lines.append(f"### {status} {filename} ({csv_type})")
                
                if file_result.get("stats"):
                    stats = file_result["stats"]
                    report_lines.append(f"  Rows: {stats.get('total_rows', 0)}, Headers: {stats.get('total_headers', 0)}")
                
                if file_result["errors"]:
                    report_lines.append("  Errors:")
                    for error in file_result["errors"]:
                        report_lines.append(f"    - {error}")
                
                if file_result.get("warnings"):
                    report_lines.append("  Warnings:")
                    for warning in file_result["warnings"]:
                        report_lines.append(f"    - {warning}")
                
                report_lines.append("")
        
        else:
            # Single file validation report
            status = "✓" if results["valid"] else "✗"
            csv_type = results.get("csv_type", "unknown")
            
            report_lines.append(f"## {status} {results['file']} ({csv_type})")
            
            if results.get("stats"):
                stats = results["stats"]
                report_lines.append(f"Rows: {stats.get('total_rows', 0)}, Headers: {stats.get('total_headers', 0)}")
            
            if results["errors"]:
                report_lines.append("### Errors:")
                for error in results["errors"]:
                    report_lines.append(f"- {error}")
            
            if results.get("warnings"):
                report_lines.append("### Warnings:")
                for warning in results["warnings"]:
                    report_lines.append(f"- {warning}")
        
        return "\n".join(report_lines)


def main():
    """Main function for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate CSV artifacts")
    parser.add_argument("--file", type=Path, help="Validate specific CSV file")
    parser.add_argument("--directory", type=Path, help="Validate all CSV files in directory")
    parser.add_argument("--pattern", default="*.csv", help="File pattern for directory validation")
    parser.add_argument("--report", type=Path, help="Output report file")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create validator
    validator = CSVArtifactValidator()
    
    # Perform validation
    if args.file:
        results = validator.validate_csv_file(args.file)
    elif args.directory:
        results = validator.validate_directory(args.directory, args.pattern)
    else:
        print("Please specify --file or --directory")
        exit(1)
    
    # Generate report
    report = validator.generate_validation_report(results)
    print(report)
    
    # Write report to file if requested
    if args.report:
        with open(args.report, 'w') as f:
            f.write(report)
        print(f"\nReport written to: {args.report}")
    
    # Exit with error code if validation failed
    if isinstance(results, dict):
        if "valid" in results and not results["valid"]:
            exit(1)
        elif "invalid_files" in results and results["invalid_files"] > 0:
            exit(1)


if __name__ == "__main__":
    main()