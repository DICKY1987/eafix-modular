# Health Metrics CSV Schema

## Description
System health and performance metrics collected by the telemetry daemon.

## File Format
- **File naming**: `health_metrics_YYYYMMDD_HHMMSS.csv`
- **Encoding**: UTF-8
- **Delimiter**: Comma (`,`)
- **Header**: Required (first row)

## Required Columns

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `file_seq` | Integer | Monotonic sequence number for ordering | 1, 2, 3, ... |
| `checksum_sha256` | String | SHA-256 checksum of row data (excluding this field) | `a1b2c3d4e5f6...` |
| `timestamp` | ISO 8601 | Metric collection timestamp in UTC | `2024-09-10T14:30:00Z` |
| `service_name` | String | Name of the service | `data-ingestor`, `signal-generator` |
| `metric_name` | String | Name of the metric | `latency_p95`, `error_rate`, `memory_usage` |
| `metric_value` | Float | Metric value | `150.5`, `0.02`, `85.6` |
| `metric_unit` | String | Unit of measurement | `ms`, `percent`, `MB` |
| `health_status` | String | Overall health status | `HEALTHY`, `DEGRADED`, `UNHEALTHY` |
| `cpu_usage_percent` | Float | CPU usage percentage | `25.5` |
| `memory_usage_percent` | Float | Memory usage percentage | `45.2` |
| `disk_usage_percent` | Float | Disk usage percentage | `35.8` |
| `active_connections` | Integer | Number of active connections | `15` |
| `messages_processed` | Integer | Messages processed since last report | `1250` |
| `error_count` | Integer | Errors since last report | `2` |
| `uptime_seconds` | Integer | Service uptime in seconds | `3600` |

## Health Status Definitions
- **HEALTHY**: All metrics within normal ranges
- **DEGRADED**: Some metrics elevated but service functional
- **UNHEALTHY**: Critical metrics breached, service impaired

## Constraints
- `file_seq` must be monotonically increasing within file
- `checksum_sha256` must match computed SHA-256 of row data
- Percentage values must be between 0.0 and 100.0
- `uptime_seconds` must be non-negative

## Atomic Write Policy
1. Write to temporary file with `.tmp` extension
2. Compute SHA-256 for each row (excluding checksum column)
3. Call `fsync()` to ensure data is written to disk
4. Rename from `.tmp` to final filename atomically