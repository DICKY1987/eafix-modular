# Active Calendar Signals CSV Schema

## Description
Calendar signals generated from economic calendar events with proximity states and anticipation events.

## File Format
- **File naming**: `active_calendar_signals_YYYYMMDD_HHMMSS.csv`
- **Encoding**: UTF-8
- **Delimiter**: Comma (`,`)
- **Header**: Required (first row)

## Required Columns

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `file_seq` | Integer | Monotonic sequence number for ordering | 1, 2, 3, ... |
| `checksum_sha256` | String | SHA-256 checksum of row data (excluding this field) | `a1b2c3d4e5f6...` |
| `timestamp` | ISO 8601 | Event timestamp in UTC | `2024-09-10T14:30:00Z` |
| `calendar_id` | String | Calendar identifier (CAL8 or CAL5) | `CAL8_USD_NFP_HIGH` |
| `symbol` | String | Currency pair | `EURUSD`, `GBPJPY` |
| `impact_level` | String | Event impact level | `HIGH`, `MEDIUM`, `LOW` |
| `proximity_state` | String | Distance to event | `IMMEDIATE`, `NEAR`, `FAR` |
| `anticipation_event` | Boolean | Whether this is an anticipation signal | `true`, `false` |
| `direction_bias` | String | Expected market direction | `BULLISH`, `BEARISH`, `NEUTRAL` |
| `confidence_score` | Float | Signal confidence (0.0-1.0) | `0.85` |

## Constraints
- `file_seq` must be monotonically increasing within file
- `checksum_sha256` must match computed SHA-256 of row data
- `timestamp` must be valid ISO 8601 format
- `calendar_id` must follow CAL8/CAL5 format specification
- `confidence_score` must be between 0.0 and 1.0

## Atomic Write Policy
1. Write to temporary file with `.tmp` extension
2. Compute SHA-256 for each row (excluding checksum column)
3. Call `fsync()` to ensure data is written to disk
4. Rename from `.tmp` to final filename atomically