# CSV Atomic Write Policy

## Overview
This policy ensures data integrity and consistency for all CSV files written by the trading system. It prevents partial writes, data corruption, and race conditions through atomic file operations.

## Atomic Write Sequence

### 1. Temporary File Creation
```python
import tempfile
import os
from pathlib import Path

def atomic_csv_write(target_path: str, data: list, headers: list):
    """Write CSV data atomically with integrity checks."""
    target_file = Path(target_path)
    temp_file = target_file.with_suffix('.tmp')
```

### 2. Data Preparation
- Validate all data against schema
- Compute `file_seq` (monotonically increasing)
- Calculate `checksum_sha256` for each row (excluding checksum column itself)

### 3. Write to Temporary File
```python
with open(temp_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)  # Write header
    writer.writerows(data_with_checksums)  # Write data rows
```

### 4. Force Disk Sync
```python
f.flush()  # Flush Python buffers
os.fsync(f.fileno())  # Force OS to write to disk
```

### 5. Atomic Rename
```python
temp_file.rename(target_file)  # Atomic operation on most filesystems
```

## Required Metadata Columns

### file_seq (Integer)
- **Purpose**: Provides total ordering of records
- **Format**: Monotonically increasing positive integer
- **Validation**: Each row must have `file_seq > previous_file_seq`
- **Recovery**: Can detect and recover from partial writes

### checksum_sha256 (String)
- **Purpose**: Detects data corruption and tampering
- **Format**: Hexadecimal SHA-256 hash (64 characters)
- **Computation**: SHA-256 of all row data excluding the checksum column itself
- **Validation**: Recompute hash and compare with stored value

## Checksum Calculation

### Algorithm
```python
import hashlib
import csv
from typing import List, Dict, Any

def compute_row_checksum(row_data: Dict[str, Any], exclude_column: str = 'checksum_sha256') -> str:
    """Compute SHA-256 checksum for a CSV row."""
    # Create ordered string of all values except checksum column
    ordered_values = []
    for key, value in sorted(row_data.items()):
        if key != exclude_column:
            ordered_values.append(str(value))
    
    # Join values and compute hash
    row_string = '|'.join(ordered_values)
    return hashlib.sha256(row_string.encode('utf-8')).hexdigest()
```

### Example Row Processing
```python
row = {
    'file_seq': 1,
    'timestamp': '2024-09-10T14:30:00Z',
    'trade_id': 'TRADE_20240910_001',
    'symbol': 'EURUSD',
    'profit_loss': 25.00
}

# Compute checksum (excluding checksum_sha256 column)
checksum = compute_row_checksum(row)
row['checksum_sha256'] = checksum

# Result: 
# {
#     'file_seq': 1,
#     'timestamp': '2024-09-10T14:30:00Z', 
#     'trade_id': 'TRADE_20240910_001',
#     'symbol': 'EURUSD',
#     'profit_loss': 25.00,
#     'checksum_sha256': 'a1b2c3d4e5f6789...'
# }
```

## Error Handling

### Partial Write Detection
```python
def validate_csv_integrity(file_path: str) -> bool:
    """Validate CSV file integrity."""
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            prev_seq = 0
            
            for row in reader:
                # Check sequence ordering
                current_seq = int(row['file_seq'])
                if current_seq <= prev_seq:
                    raise ValueError(f"Sequence violation: {current_seq} <= {prev_seq}")
                
                # Verify checksum
                stored_checksum = row.pop('checksum_sha256')
                computed_checksum = compute_row_checksum(row)
                if stored_checksum != computed_checksum:
                    raise ValueError(f"Checksum mismatch in seq {current_seq}")
                
                prev_seq = current_seq
                
        return True
    except Exception as e:
        logger.error(f"CSV integrity validation failed: {e}")
        return False
```

### Recovery Procedures
1. **Corrupted File**: Restore from backup, replay from last known good state
2. **Partial Write**: Remove temporary file, retry operation
3. **Sequence Gap**: Log gap, investigate data loss, potentially backfill

## File Naming Convention

### Pattern
```
{base_name}_YYYYMMDD_HHMMSS.csv
```

### Examples
```
active_calendar_signals_20240910_143000.csv
reentry_decisions_20240910_143015.csv  
trade_results_20240910_143030.csv
health_metrics_20240910_143045.csv
```

### Temporary Files
```
{base_name}_YYYYMMDD_HHMMSS.csv.tmp
```

## Implementation Requirements

### Services Must Implement
1. **Atomic write function** following the 5-step sequence
2. **Integrity validation** before and after writes
3. **Error handling** with proper logging and recovery
4. **Backup procedures** for critical files
5. **Monitoring** of write operations and file integrity

### Prohibited Operations
1. **Direct writes** to final filenames (always use temporary files)
2. **Partial updates** to existing CSV files
3. **Missing metadata** columns (`file_seq`, `checksum_sha256`)
4. **Concurrent writes** to same target file

## Testing Requirements

### Unit Tests
- Validate atomic write sequence
- Test checksum calculation accuracy
- Verify error handling scenarios
- Check recovery procedures

### Integration Tests
- Test concurrent access scenarios
- Validate filesystem-level atomicity
- Test backup and recovery procedures
- Verify monitoring and alerting

## Monitoring and Alerting

### Key Metrics
- Write operation latency (p95, p99)
- Integrity validation success rate
- File sequence gap detection
- Temporary file cleanup success

### Alerts
- Integrity validation failures
- Sequence gaps detected
- Temporary files not cleaned up
- Write operation timeouts

This atomic write policy ensures data integrity and prevents corruption in all CSV files throughout the trading system.