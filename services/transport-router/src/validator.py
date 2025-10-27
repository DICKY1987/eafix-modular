"""
Integrity Validator

Validates CSV files for checksum integrity, sequence consistency,
and contract schema compliance using the centralized contract system.
"""

import asyncio
import csv
import hashlib
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import structlog

# Add contracts and shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "contracts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from contracts.models import ActiveCalendarSignal, ReentryDecision, TradeResult, HealthMetric

logger = structlog.get_logger(__name__)


class IntegrityValidator:
    """Validates CSV file integrity and schema compliance."""
    
    def __init__(self, settings, metrics):
        self.settings = settings
        self.metrics = metrics
        
        # Contract model mapping
        self.contract_models = {
            "ActiveCalendarSignal": ActiveCalendarSignal,
            "ReentryDecision": ReentryDecision,
            "TradeResult": TradeResult,
            "HealthMetric": HealthMetric
        }
        
        # Validation cache
        self.validation_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_seconds = 300  # 5 minutes
        
        self.running = False
    
    async def start(self) -> None:
        """Start the validator."""
        self.running = True
        logger.info("Integrity validator started")
    
    async def stop(self) -> None:
        """Stop the validator."""
        self.running = False
        logger.info("Integrity validator stopped")
    
    async def validate_file(self, file_path: Path, expected_type: str) -> Dict[str, Any]:
        """
        Validate a CSV file for integrity and schema compliance.
        
        Args:
            file_path: Path to CSV file
            expected_type: Expected contract type
            
        Returns:
            Validation result with detailed information
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(
                "Validating file",
                file_path=str(file_path),
                expected_type=expected_type
            )
            
            # Check cache first
            cache_key = f"{file_path}:{expected_type}:{file_path.stat().st_mtime}"
            if cache_key in self.validation_cache:
                cache_entry = self.validation_cache[cache_key]
                if (datetime.utcnow() - cache_entry["timestamp"]).seconds < self.cache_ttl_seconds:
                    return cache_entry["result"]
            
            # Basic file checks
            basic_checks = await self._perform_basic_checks(file_path)
            if not basic_checks["valid"]:
                return basic_checks
            
            # Read and parse CSV
            csv_data = await self._read_csv_file(file_path)
            if not csv_data["valid"]:
                return csv_data
            
            rows = csv_data["rows"]
            header = csv_data["header"]
            
            validation_result = {
                "valid": True,
                "file_path": str(file_path),
                "expected_type": expected_type,
                "row_count": len(rows),
                "validation_timestamp": datetime.utcnow().isoformat(),
                "checks_performed": [],
                "errors": [],
                "warnings": []
            }
            
            # Checksum validation
            if self.settings.checksum_validation_enabled:
                checksum_result = await self._validate_checksums(rows, header)
                validation_result["checks_performed"].append("checksum")
                if not checksum_result["valid"]:
                    validation_result["valid"] = False
                    validation_result["errors"].extend(checksum_result["errors"])
                else:
                    validation_result["checksum_validation"] = checksum_result
            
            # Sequence validation
            if self.settings.sequence_validation_enabled:
                sequence_result = await self._validate_sequences(rows, header)
                validation_result["checks_performed"].append("sequence")
                if not sequence_result["valid"]:
                    validation_result["warnings"].extend(sequence_result["warnings"])
                else:
                    validation_result["sequence_validation"] = sequence_result
            
            # Schema validation
            if self.settings.schema_validation_enabled:
                schema_result = await self._validate_schema(rows, header, expected_type)
                validation_result["checks_performed"].append("schema")
                if not schema_result["valid"]:
                    validation_result["valid"] = False
                    validation_result["errors"].extend(schema_result["errors"])
                else:
                    validation_result["schema_validation"] = schema_result
            
            # Cache result
            self.validation_cache[cache_key] = {
                "timestamp": datetime.utcnow(),
                "result": validation_result
            }
            
            # Clean old cache entries
            await self._clean_validation_cache()
            
            # Record metrics
            validation_time = asyncio.get_event_loop().time() - start_time
            self.metrics.record_file_validation(validation_time, validation_result["valid"])
            
            if validation_result["valid"]:
                logger.info(
                    "File validation passed",
                    file_path=str(file_path),
                    row_count=validation_result["row_count"],
                    checks=validation_result["checks_performed"]
                )
            else:
                logger.error(
                    "File validation failed",
                    file_path=str(file_path),
                    errors=validation_result["errors"]
                )
            
            return validation_result
            
        except Exception as e:
            validation_time = asyncio.get_event_loop().time() - start_time
            logger.error(
                "File validation error",
                file_path=str(file_path),
                error=str(e),
                exc_info=True
            )
            
            self.metrics.record_file_validation(validation_time, False)
            self.metrics.record_error("validation_error")
            
            return {
                "valid": False,
                "file_path": str(file_path),
                "error": str(e),
                "validation_timestamp": datetime.utcnow().isoformat()
            }
    
    async def _perform_basic_checks(self, file_path: Path) -> Dict[str, Any]:
        """Perform basic file system checks."""
        try:
            # Check file exists
            if not file_path.exists():
                return {"valid": False, "error": "File does not exist"}
            
            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.settings.max_file_size_mb:
                return {
                    "valid": False, 
                    "error": f"File too large: {file_size_mb:.1f}MB > {self.settings.max_file_size_mb}MB"
                }
            
            # Check file extension
            if file_path.suffix.lower() != '.csv':
                return {"valid": False, "error": "File is not a CSV file"}
            
            # Check file is readable
            try:
                with open(file_path, 'r') as f:
                    f.read(1)
            except Exception as e:
                return {"valid": False, "error": f"File not readable: {e}"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def _read_csv_file(self, file_path: Path) -> Dict[str, Any]:
        """Read and parse CSV file."""
        try:
            rows = []
            header = None
            
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                
                # Read header
                try:
                    header = next(reader)
                except StopIteration:
                    return {"valid": False, "error": "Empty CSV file"}
                
                # Read data rows
                for row_num, row in enumerate(reader, start=2):
                    if len(row) != len(header):
                        return {
                            "valid": False, 
                            "error": f"Row {row_num} has {len(row)} columns, expected {len(header)}"
                        }
                    
                    # Create row dictionary
                    row_dict = dict(zip(header, row))
                    rows.append(row_dict)
            
            if not rows:
                return {"valid": False, "error": "CSV file has no data rows"}
            
            return {
                "valid": True,
                "rows": rows,
                "header": header,
                "row_count": len(rows)
            }
            
        except Exception as e:
            return {"valid": False, "error": f"CSV parsing error: {e}"}
    
    async def _validate_checksums(self, rows: List[Dict[str, str]], header: List[str]) -> Dict[str, Any]:
        """Validate SHA-256 checksums in CSV rows."""
        try:
            if "checksum_sha256" not in header:
                return {
                    "valid": False,
                    "errors": ["Missing checksum_sha256 column"]
                }
            
            errors = []
            valid_checksums = 0
            
            for i, row in enumerate(rows):
                stored_checksum = row.get("checksum_sha256", "").lower()
                
                if not stored_checksum:
                    errors.append(f"Row {i+2}: Missing checksum")
                    continue
                
                if len(stored_checksum) != 64:
                    errors.append(f"Row {i+2}: Invalid checksum length ({len(stored_checksum)})")
                    continue
                
                # Compute expected checksum
                row_copy = row.copy()
                del row_copy["checksum_sha256"]
                
                # Create ordered string representation
                ordered_values = []
                for key in sorted(row_copy.keys()):
                    value = row_copy[key]
                    ordered_values.append(str(value))
                
                row_string = '|'.join(ordered_values)
                expected_checksum = hashlib.sha256(row_string.encode('utf-8')).hexdigest()
                
                if stored_checksum != expected_checksum:
                    errors.append(
                        f"Row {i+2}: Checksum mismatch (expected: {expected_checksum[:8]}..., "
                        f"got: {stored_checksum[:8]}...)"
                    )
                else:
                    valid_checksums += 1
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "total_rows": len(rows),
                "valid_checksums": valid_checksums,
                "checksum_success_rate": valid_checksums / len(rows) if rows else 0
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Checksum validation error: {e}"]
            }
    
    async def _validate_sequences(self, rows: List[Dict[str, str]], header: List[str]) -> Dict[str, Any]:
        """Validate file sequence numbers."""
        try:
            if "file_seq" not in header:
                return {
                    "valid": False,
                    "warnings": ["Missing file_seq column - sequence validation skipped"]
                }
            
            warnings = []
            sequences = []
            
            for i, row in enumerate(rows):
                seq_str = row.get("file_seq", "")
                
                if not seq_str:
                    warnings.append(f"Row {i+2}: Missing sequence number")
                    continue
                
                try:
                    seq_num = int(seq_str)
                    sequences.append(seq_num)
                except ValueError:
                    warnings.append(f"Row {i+2}: Invalid sequence number '{seq_str}'")
            
            if not sequences:
                return {
                    "valid": False,
                    "warnings": ["No valid sequence numbers found"]
                }
            
            # Check for monotonic increasing
            is_monotonic = all(sequences[i] < sequences[i+1] for i in range(len(sequences)-1))
            
            # Check for duplicates
            unique_sequences = len(set(sequences))
            has_duplicates = unique_sequences != len(sequences)
            
            # Check for gaps
            if sequences:
                expected_range = range(min(sequences), max(sequences) + 1)
                missing_sequences = set(expected_range) - set(sequences)
                has_gaps = len(missing_sequences) > 0
            else:
                missing_sequences = set()
                has_gaps = False
            
            if not is_monotonic:
                warnings.append("Sequence numbers are not monotonically increasing")
            
            if has_duplicates:
                warnings.append(f"Found {len(sequences) - unique_sequences} duplicate sequence numbers")
            
            if has_gaps:
                warnings.append(f"Found {len(missing_sequences)} gaps in sequence numbers")
            
            return {
                "valid": True,  # Sequence issues are warnings, not errors
                "warnings": warnings,
                "total_sequences": len(sequences),
                "unique_sequences": unique_sequences,
                "min_sequence": min(sequences) if sequences else None,
                "max_sequence": max(sequences) if sequences else None,
                "is_monotonic": is_monotonic,
                "has_duplicates": has_duplicates,
                "has_gaps": has_gaps,
                "missing_sequences": sorted(missing_sequences) if missing_sequences else []
            }
            
        except Exception as e:
            return {
                "valid": False,
                "warnings": [f"Sequence validation error: {e}"]
            }
    
    async def _validate_schema(self, rows: List[Dict[str, str]], header: List[str], 
                             expected_type: str) -> Dict[str, Any]:
        """Validate rows against contract schema."""
        try:
            if expected_type not in self.contract_models:
                return {
                    "valid": False,
                    "errors": [f"Unknown contract type: {expected_type}"]
                }
            
            model_class = self.contract_models[expected_type]
            errors = []
            valid_rows = 0
            
            for i, row in enumerate(rows):
                try:
                    # Convert datetime strings if present
                    row_copy = row.copy()
                    
                    # Handle common datetime fields
                    datetime_fields = ["timestamp", "open_time", "close_time"]
                    for field in datetime_fields:
                        if field in row_copy and row_copy[field]:
                            try:
                                # Try ISO format parsing
                                if 'T' in row_copy[field]:
                                    parsed_dt = datetime.fromisoformat(row_copy[field].replace('Z', '+00:00'))
                                    row_copy[field] = parsed_dt
                            except Exception:
                                pass  # Leave as string, let Pydantic handle it
                    
                    # Handle numeric fields
                    numeric_fields = [
                        "file_seq", "lot_size", "open_price", "close_price", 
                        "profit_loss", "profit_loss_pips", "stop_loss", "take_profit",
                        "confidence_score", "duration_minutes"
                    ]
                    for field in numeric_fields:
                        if field in row_copy and row_copy[field]:
                            try:
                                if field == "file_seq" or field == "duration_minutes":
                                    row_copy[field] = int(row_copy[field])
                                else:
                                    row_copy[field] = float(row_copy[field])
                            except ValueError:
                                pass  # Leave as string, let Pydantic handle validation error
                    
                    # Validate with Pydantic model
                    validated_row = model_class(**row_copy)
                    valid_rows += 1
                    
                except Exception as e:
                    errors.append(f"Row {i+2}: {str(e)}")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "total_rows": len(rows),
                "valid_rows": valid_rows,
                "schema_success_rate": valid_rows / len(rows) if rows else 0,
                "contract_type": expected_type
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Schema validation error: {e}"]
            }
    
    async def _clean_validation_cache(self) -> None:
        """Clean old entries from validation cache."""
        try:
            now = datetime.utcnow()
            expired_keys = []
            
            for key, entry in self.validation_cache.items():
                if (now - entry["timestamp"]).seconds > self.cache_ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.validation_cache[key]
                
        except Exception as e:
            logger.warning("Failed to clean validation cache", error=str(e))
    
    async def validate_file_batch(self, file_specs: List[Tuple[Path, str]]) -> List[Dict[str, Any]]:
        """Validate multiple files in batch."""
        results = []
        
        for file_path, expected_type in file_specs:
            result = await self.validate_file(file_path, expected_type)
            results.append(result)
        
        return results
    
    async def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            "cache_entries": len(self.validation_cache),
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "checksum_validation_enabled": self.settings.checksum_validation_enabled,
            "sequence_validation_enabled": self.settings.sequence_validation_enabled,
            "schema_validation_enabled": self.settings.schema_validation_enabled,
            "supported_contract_types": list(self.contract_models.keys())
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get validator status."""
        return {
            "running": self.running,
            "validation_cache_size": len(self.validation_cache),
            "supported_types": list(self.contract_models.keys()),
            "validation_config": self.settings.get_validation_config()
        }