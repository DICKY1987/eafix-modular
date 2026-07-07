# Cost Tracker & Budget Guardrails (v0.1)

- Ledger file: `state/cost_ledger.jsonl` (append-only)
- Entry schema: `{ ts, task_id, tool, action, tokens, amount }`
- API:
  - `lib.cost_tracker.record_cost(task_id, tool, action, tokens, amount)`
  - `lib.cost_tracker.get_total_cost(task_id)`
- Planner must compare `estimated_cost` vs `budget` and executor must halt when budget exhausted.

