from __future__ import annotations

try:
    from prometheus_client import Counter, Histogram  # type: ignore
except Exception:  # pragma: no cover - optional
    Counter = None  # type: ignore
    Histogram = None  # type: ignore


GDW_RUNS_TOTAL = Counter("gdw_runs_total", "Total number of GDW runs", ["workflow"]) if Counter else None
GDW_RUN_DURATION = Histogram(
    "gdw_run_duration_seconds",
    "GDW run duration in seconds",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300),
    labelnames=("workflow",),
) if Histogram else None

