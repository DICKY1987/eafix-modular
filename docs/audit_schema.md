# Audit Trail (v0.1)

- File: `state/audit.jsonl`
- Entry schema:

```
{
  ts: number,          // epoch seconds
  task_id: string,
  phase: string,
  action: string,
  details: object,
  cost_delta: number | null,
  tool: string | null,
  sha: string          // sha256 of details
}
```

- Writer: `lib.audit_logger.log_action(...)`
- Consumers should treat the file as append-only.

