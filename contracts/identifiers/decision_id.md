# decision_id

## Definition

`decision_id` is a 16-character hex string uniquely identifying a ReentryDecision record.

## Generation Algorithm

```python
decision_id = hashlib.sha256(f"{hybrid_id}:{utc_iso_timestamp}".encode()).hexdigest()[:16]
```

Where:
- `hybrid_id`: The full hybrid ID of the trade being processed
- `utc_iso_timestamp`: UTC timestamp as ISO 8601 string at time of decision

## Generated At

Step S24 — reentry-engine when writing the ReentryDecision CSV record.

## Location in Schema

The `decision_id` field is added to `contracts/models/2099900016260118_csv_models.py::ReentryDecision`.

## Purpose

Provides a stable, deterministic identifier for each ReentryDecision that:
- Is unique per (hybrid_id, decision_timestamp) pair
- Can be reproduced from the CSV fields alone
- Enables correlation across the telemetry/reporter pipeline

## Notes

- GAP-49 closed by this definition
- Truncated to 16 hex chars = 64 bits of collision resistance (sufficient for this use case)
