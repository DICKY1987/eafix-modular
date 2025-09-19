# Trade Results CSV Schema

## Description
Completed trade results written by the EA bridge, including execution details and performance metrics.

## File Format
- **File naming**: `trade_results_YYYYMMDD_HHMMSS.csv`
- **Encoding**: UTF-8
- **Delimiter**: Comma (`,`)
- **Header**: Required (first row)

## Required Columns

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `file_seq` | Integer | Monotonic sequence number for ordering | 1, 2, 3, ... |
| `checksum_sha256` | String | SHA-256 checksum of row data (excluding this field) | `a1b2c3d4e5f6...` |
| `timestamp` | ISO 8601 | Trade close timestamp in UTC | `2024-09-10T14:30:00Z` |
| `trade_id` | String | Unique trade identifier | `TRADE_20240910_001` |
| `symbol` | String | Currency pair | `EURUSD`, `GBPJPY` |
| `direction` | String | Trade direction | `BUY`, `SELL` |
| `lot_size` | Float | Position size in lots | `0.01`, `0.1`, `1.0` |
| `open_price` | Float | Trade opening price | `1.10500` |
| `close_price` | Float | Trade closing price | `1.10750` |
| `open_time` | ISO 8601 | Trade opening timestamp | `2024-09-10T14:00:00Z` |
| `close_time` | ISO 8601 | Trade closing timestamp | `2024-09-10T14:30:00Z` |
| `duration_minutes` | Integer | Trade duration in minutes | `30` |
| `profit_loss` | Float | P&L in account currency | `25.00`, `-15.50` |
| `profit_loss_pips` | Float | P&L in pips | `25.0`, `-15.5` |
| `stop_loss` | Float | Stop loss level (if set) | `1.10250` |
| `take_profit` | Float | Take profit level (if set) | `1.10750` |
| `close_reason` | String | Reason for trade closure | `TP`, `SL`, `MANUAL`, `TIMEOUT` |
| `commission` | Float | Commission paid | `0.50` |
| `swap` | Float | Overnight swap | `0.25`, `-0.15` |
| `magic_number` | Integer | EA magic number | `12345` |
| `comment` | String | Trade comment with hybrid ID | `O_DUR5_PROX2_HIGH_BUY_abc123` |

## Constraints
- `file_seq` must be monotonically increasing within file
- `checksum_sha256` must match computed SHA-256 of row data
- `close_time` must be >= `open_time`
- `duration_minutes` must match calculated difference
- `comment` should contain hybrid ID for re-entry processing

## Atomic Write Policy
1. Write to temporary file with `.tmp` extension
2. Compute SHA-256 for each row (excluding checksum column)
3. Call `fsync()` to ensure data is written to disk
4. Rename from `.tmp` to final filename atomically