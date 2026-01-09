# DOC_ID: DOC-SERVICE-0029
"""
Rewritten python_calendar_system.py

Key updates applied from review:
- Replaced dataclass/asdict usage with Pydantic v2 and .model_dump() when writing YAML.
- Single consolidated `if __name__ == "__main__"` block supporting `test` mode.
- Conditional static mount to avoid startup crash when ./static doesn't exist.
- Safe WebSocket URL construction (ws/wss) in the embedded dashboard HTML.
- SQLite UNIQUE index + proper UPSERT to prevent duplicates; real UPDATE of status.
- Scheduler uses config-driven import day/hour; emergency stop pauses jobs AND marks events BLOCKED, with resume logic.
- Watchdog file handler posts work back to the event loop via run_coroutine_threadsafe.
- Minimum-gap logic in EventProcessor to avoid clustered triggers.
- Broadcast WebSocket updates on imports/status changes.
- Signal export filenames use microseconds + UUID to avoid collisions.
- Trimmed unused imports and added environment-variable overrides in SystemConfig.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import sys
import uuid
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from starlette.websockets import WebSocketState

# Optional: watchdog for incoming files (guarded import)
try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    _WATCHDOG_AVAILABLE = True
except Exception:  # pragma: no cover
    _WATCHDOG_AVAILABLE = False


# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

class SystemConfig(BaseModel):
    database_path: str = os.getenv("DATABASE_PATH", "./calendar.db")
    signals_export_path: str = os.getenv("SIGNALS_EXPORT_PATH", "./signals_out")
    signals_import_path: str = os.getenv("SIGNALS_IMPORT_PATH", "./signals_in")
    static_dir: str = os.getenv("STATIC_DIR", "./static")

    # Cron: day_of_week can be 'mon-sun' or numeric '0-6' where 0=mon in APScheduler.
    # We'll accept common three-letter names.
    import_day: str = os.getenv("IMPORT_DAY", "sun")
    import_hour: int = int(os.getenv("IMPORT_HOUR", "12"))  # 24h clock

    minimum_gap_minutes: int = int(os.getenv("MINIMUM_GAP_MINUTES", "0"))

    @classmethod
    def load_or_create(cls, config_file: str = "config.yaml") -> "SystemConfig":
        path = Path(config_file)
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            # YAML values are overridden by env if present (already baked in defaults)
            base = cls(**data)
        else:
            base = cls()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                yaml.dump(base.model_dump(), f, default_flow_style=False, sort_keys=False)
        # Ensure directories exist
        Path(base.signals_export_path).mkdir(parents=True, exist_ok=True)
        Path(base.signals_import_path).mkdir(parents=True, exist_ok=True)
        return base


# ----------------------------------------------------------------------------
# Database layer (SQLite)
# ----------------------------------------------------------------------------

class DB:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, detect_types=sqlite3.PARSE_DECLTYPES)
        try:
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    country TEXT NOT NULL,
                    impact TEXT,
                    event_date TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    trigger_time TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    parameter_set TEXT,
                    quality_score REAL,
                    processing_notes TEXT,
                    created_at TEXT NOT NULL DEFAULT (DATETIME('now')),
                    updated_at TEXT NOT NULL DEFAULT (DATETIME('now'))
                );
                """
            )
            # Unique semantic identity for an event occurrence
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_events_unique
                ON calendar_events (title, country, event_date, event_time);
                """
            )
            # Index for efficient status and trigger_time queries
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_status_time 
                ON calendar_events(status, trigger_time);
                """
            )

    def upsert_event(
        self,
        *,
        title: str,
        country: str,
        impact: str,
        event_date: date,
        event_time: time,
        trigger_time: datetime,
        status: str = "PENDING",
        parameter_set: Optional[Dict[str, Any]] = None,
        quality_score: Optional[float] = None,
        processing_notes: Optional[str] = None,
    ) -> int:
        """Insert or update an event by its unique natural key."""
        param_json = json.dumps(parameter_set) if isinstance(parameter_set, dict) else parameter_set
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO calendar_events (
                    title, country, impact, event_date, event_time,
                    trigger_time, status, parameter_set, quality_score, processing_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(title, country, event_date, event_time) DO UPDATE SET
                    impact=excluded.impact,
                    trigger_time=excluded.trigger_time,
                    status=excluded.status,
                    parameter_set=excluded.parameter_set,
                    quality_score=excluded.quality_score,
                    processing_notes=excluded.processing_notes,
                    updated_at=DATETIME('now')
                """,
                (
                    title,
                    country,
                    impact,
                    event_date.isoformat(),
                    event_time.strftime("%H:%M:%S"),
                    trigger_time.isoformat(),
                    status,
                    param_json,
                    quality_score,
                    processing_notes,
                ),
            )
            # Get the row id for the record
            cur2 = conn.execute(
                """
                SELECT id FROM calendar_events
                WHERE title=? AND country=? AND event_date=? AND event_time=?
                """,
                (title, country, event_date.isoformat(), event_time.strftime("%H:%M:%S")),
            )
            row = cur2.fetchone()
            return int(row[0]) if row else -1

    def bulk_upsert(self, rows: Iterable[Dict[str, Any]]) -> List[int]:
        ids: List[int] = []
        for r in rows:
            ids.append(self.upsert_event(**r))
        return ids

    def set_status(self, event_id: int, status: str, note: Optional[str] = None) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE calendar_events SET status=?, processing_notes=?, updated_at=DATETIME('now') WHERE id=?",
                (status, note, event_id),
            )

    def get_pending_events(self) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            cur = conn.execute(
                """
                SELECT id, title, country, impact, event_date, event_time, trigger_time, status,
                       parameter_set, quality_score, processing_notes
                FROM calendar_events
                WHERE status='PENDING'
                ORDER BY trigger_time ASC
                """
            )
            cols = [c[0] for c in cur.description]
            rows = []
            for row in cur.fetchall():
                row_dict = dict(zip(cols, row))
                # Deserialize parameter_set JSON
                if row_dict.get('parameter_set'):
                    try:
                        row_dict['parameter_set'] = json.loads(row_dict['parameter_set'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                rows.append(row_dict)
            return rows

    def get_blocked_events_future(self, now: datetime) -> List[int]:
        with self.connect() as conn:
            cur = conn.execute(
                "SELECT id FROM calendar_events WHERE status='BLOCKED' AND trigger_time > ?",
                (now.isoformat(),),
            )
            return [int(r[0]) for r in cur.fetchall()]

    def get_event_by_id(self, event_id: int) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            cur = conn.execute(
                """
                SELECT id, title, country, impact, event_date, event_time, trigger_time, status,
                       parameter_set, quality_score, processing_notes
                FROM calendar_events
                WHERE id=?
                """,
                (event_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [c[0] for c in cur.description]
            row_dict = dict(zip(cols, row))
            # Deserialize parameter_set JSON
            if row_dict.get('parameter_set'):
                try:
                    row_dict['parameter_set'] = json.loads(row_dict['parameter_set'])
                except (json.JSONDecodeError, TypeError):
                    pass
            return row_dict

    def list_all(self) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            cur = conn.execute(
                """
                SELECT id, title, country, impact, event_date, event_time, trigger_time, status,
                       parameter_set, quality_score, processing_notes, created_at, updated_at
                FROM calendar_events
                ORDER BY trigger_time ASC
                """
            )
            cols = [c[0] for c in cur.description]
            rows = []
            for row in cur.fetchall():
                row_dict = dict(zip(cols, row))
                # Deserialize parameter_set JSON
                if row_dict.get('parameter_set'):
                    try:
                        row_dict['parameter_set'] = json.loads(row_dict['parameter_set'])
                    except (json.JSONDecodeError, TypeError):
                        pass
                rows.append(row_dict)
            return rows


# ----------------------------------------------------------------------------
# Event Processing / Integration
# ----------------------------------------------------------------------------

class MT4Integration:
    """Example integration that exports a CSV signal when an event triggers,
    and can also process incoming .csv files from a watched directory.
    """

    def __init__(self, export_dir: str):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def export_signal(self, event: Dict[str, Any]) -> Path:
        ts = datetime.utcnow()
        # Use microseconds + UUID to prevent filename collisions
        fname = f"signal_{ts.strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:8]}.csv"
        path = self.export_dir / fname
        # Minimal CSV content; adapt to your strategy format
        content = [
            ["event_id", event.get("id")],
            ["title", event.get("title")],
            ["country", event.get("country")],
            ["impact", event.get("impact")],
            ["trigger_time", event.get("trigger_time")],
            ["parameter_set", event.get("parameter_set")],
        ]
        text = "\n".join(",".join(map(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else str(x), row)) for row in content)
        path.write_text(text, encoding="utf-8")
        logging.info("Exported signal to %s", path)
        return path

    async def process_signal_file(self, file_path: str) -> None:
        # Placeholder: read and act upon external signals
        try:
            p = Path(file_path)
            if not p.exists():
                return
            data = p.read_text(encoding="utf-8")
            logging.info("Processed incoming signal file %s (%d bytes)", p.name, len(data))
        except Exception as exc:  # pragma: no cover
            logging.exception("Failed processing %s: %s", file_path, exc)


class EventProcessor:
    def __init__(self, db: DB, integration: MT4Integration, *, minimum_gap_minutes: int = 0):
        self.db = db
        self.integration = integration
        self.minimum_gap = timedelta(minutes=max(0, int(minimum_gap_minutes)))
        self._last_trigger_time: Optional[datetime] = None

    def _respect_gap(self, when: datetime) -> bool:
        if not self.minimum_gap or self._last_trigger_time is None:
            return True
        if when - self._last_trigger_time >= self.minimum_gap:
            return True
        return False

    async def trigger_event(self, event_id: int, broadcast: "BroadcastHub") -> None:
        # Fetch latest snapshot for id using efficient lookup
        event = self.db.get_event_by_id(event_id)
        if not event:
            logging.warning("Event %s not found when triggering", event_id)
            return
        
        when = datetime.fromisoformat(event["trigger_time"])
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
            
        if not self._respect_gap(when):
            note = f"Suppressed: within {self.minimum_gap} of last trigger"
            self.db.set_status(event_id, "SUPPRESSED", note)
            await broadcast.push({"type": "status", "id": event_id, "status": "SUPPRESSED", "note": note})
            return

        # Try to export signal first, then mark triggered
        try:
            await self.integration.export_signal(event)
            # Only mark triggered if export succeeded
            self.db.set_status(event_id, "TRIGGERED", "Fired by scheduler")
            self._last_trigger_time = when
            await broadcast.push({"type": "status", "id": event_id, "status": "TRIGGERED"})
        except Exception as exc:
            # Mark as failed and record the error
            error_msg = f"Export failed: {exc}"
            logging.exception("Export failed for event %s", event_id)
            self.db.set_status(event_id, "FAILED", error_msg)
            await broadcast.push({"type": "status", "id": event_id, "status": "FAILED", "note": error_msg})


# ----------------------------------------------------------------------------
# WebSocket broadcasting
# ----------------------------------------------------------------------------

class BroadcastHub:
    def __init__(self) -> None:
        self.connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def register(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self.connections.add(ws)

    async def unregister(self, ws: WebSocket) -> None:
        async with self._lock:
            if ws in self.connections:
                self.connections.remove(ws)
        if ws.client_state != WebSocketState.DISCONNECTED:
            await ws.close()

    async def push(self, message: Dict[str, Any]) -> None:
        """Send message to all clients; remove stale ones."""
        # Copy the connection set under the lock, then release it
        async with self._lock:
            connections_copy = list(self.connections)
        
        # Send messages without holding the lock
        send_results = await asyncio.gather(
            *[ws.send_json(message) for ws in connections_copy], 
            return_exceptions=True
        )
        
        # Remove failed connections
        dead = []
        for ws, result in zip(connections_copy, send_results):
            if isinstance(result, Exception):
                dead.append(ws)
        
        if dead:
            async with self._lock:
                for ws in dead:
                    self.connections.discard(ws)


# ----------------------------------------------------------------------------
# Importer placeholder (replace with your real Excel/HTTP importer)
# ----------------------------------------------------------------------------

def sample_events_for_demo(now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Provide a tiny demo batch: two events 1 and 3 minutes in the future."""
    now = now or datetime.now(timezone.utc)
    rows: List[Dict[str, Any]] = []
    for mins, impact in [(1, "medium"), (3, "high")]:
        t = now + timedelta(minutes=mins)
        rows.append(
            dict(
                title=f"Demo Event +{mins}m",
                country="US",
                impact=impact,
                event_date=t.date(),
                event_time=time(t.hour, t.minute, 0),
                trigger_time=t,
                status="PENDING",
                parameter_set={"threshold": mins},
                quality_score=0.9,
                processing_notes=f"Inserted at {now.isoformat()}",
            )
        )
    return rows


# ----------------------------------------------------------------------------
# FastAPI app and scheduler wiring
# ----------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="Python Calendar System")
config = SystemConfig.load_or_create()
db = DB(config.database_path)
integration = MT4Integration(config.signals_export_path)
processor = EventProcessor(db, integration, minimum_gap_minutes=config.minimum_gap_minutes)
broadcast = BroadcastHub()
scheduler = AsyncIOScheduler(timezone=timezone.utc)

# Emergency stop state and observer reference
_ESTOP = {"active": False}
_OBSERVER = None


async def schedule_all_pending() -> None:
    """Walk PENDING events and ensure a job is scheduled for each."""
    pending = db.get_pending_events()
    for ev in pending:
        event_id = ev["id"]
        job_id = f"event:{event_id}"
        existing = scheduler.get_job(job_id)
        
        # Make trigger_dt timezone-aware
        trigger_dt = datetime.fromisoformat(ev["trigger_time"])
        if trigger_dt.tzinfo is None:
            trigger_dt = trigger_dt.replace(tzinfo=timezone.utc)
        
        # Skip past-due events
        now_utc = datetime.now(timezone.utc)
        if trigger_dt <= now_utc:
            continue
            
        # Check if existing job needs rescheduling
        if existing:
            if existing.next_run_time and existing.next_run_time != trigger_dt:
                # Time changed, reschedule
                scheduler.remove_job(job_id)
                scheduler.add_job(
                    trigger_event_job,
                    "date",
                    id=job_id,
                    run_date=trigger_dt,
                    args=[event_id],
                    misfire_grace_time=5,
                )
            continue
        
        # Add new job
        scheduler.add_job(
            trigger_event_job,
            "date",
            id=job_id,
            run_date=trigger_dt,
            args=[event_id],
            misfire_grace_time=5,  # seconds
        )
    logging.info("Ensured scheduling for %d pending events", len(pending))


async def trigger_event_job(event_id: int) -> None:
    if _ESTOP["active"]:
        # Persist BLOCKED to guard resume edge-cases
        db.set_status(event_id, "BLOCKED", "Emergency stop active")
        await broadcast.push({"type": "status", "id": event_id, "status": "BLOCKED"})
        return
    await processor.trigger_event(event_id, broadcast)


def compute_next_import_time_str() -> str:
    try:
        # APScheduler stores next run times; we'll construct a dummy CronTrigger
        trig = CronTrigger(day_of_week=config.import_day, hour=config.import_hour, minute=0, timezone=timezone.utc)
        # Find the next fire time from now in UTC
        now = datetime.now(timezone.utc)
        next_run = trig.get_next_fire_time(None, now)
        return next_run.isoformat() if next_run else "N/A"
    except Exception:  # pragma: no cover
        return "N/A"


@app.on_event("startup")
async def on_startup():
    # Start scheduler
    scheduler.start()

    # Weekly import job from config cron
    scheduler.add_job(
        import_job,
        trigger=CronTrigger(day_of_week=config.import_day, hour=config.import_hour, minute=0),
        id="weekly_import",
        replace_existing=True,
    )

    # Schedule any existing PENDING events
    await schedule_all_pending()

    # Start watchdog if available
    if _WATCHDOG_AVAILABLE:
        await start_watching_signals()

    logging.info("Startup complete. Next import at %s", compute_next_import_time_str())


@app.on_event("shutdown")
async def on_shutdown():  # pragma: no cover
    try:
        scheduler.shutdown(wait=False)
    finally:
        pass


async def import_job():
    """Cron-import task. Replace demo with real importer."""
    # In real code, pull from Excel/API and transform into row dicts
    rows = sample_events_for_demo()
    ids = db.bulk_upsert(rows)
    await schedule_all_pending()
    await broadcast.push({"type": "import", "count": len(ids)})
    logging.info("Imported %d events", len(ids))


# ------------------------------ API Routes ---------------------------------

@app.get("/")
async def root_page():
    return HTMLResponse(_DASHBOARD_HTML)


@app.get("/events")
async def get_events():
    return JSONResponse({
        "events": db.list_all(),
        "next_import": compute_next_import_time_str(),
        "estop": _ESTOP["active"],
    })


@app.post("/import")
async def manual_import():
    await import_job()
    return {"ok": True}


@app.post("/emergency/stop")
async def emergency_stop():
    _ESTOP["active"] = True
    # Pause each job individually to be robust across APScheduler versions
    for job in list(scheduler.get_jobs()):
        try:
            scheduler.pause_job(job.id)
        except Exception:
            logging.debug("pause_job not supported for %s", job.id)
    # Mark all pending events BLOCKED to avoid surprise fires on resume
    for ev in db.get_pending_events():
        db.set_status(ev["id"], "BLOCKED", "Emergency stop engaged")
    await broadcast.push({"type": "estop", "active": True})
    return {"ok": True}


@app.post("/emergency/resume")
async def emergency_resume():
    _ESTOP["active"] = False
    # Resume jobs
    for job in list(scheduler.get_jobs()):
        try:
            scheduler.resume_job(job.id)
        except Exception:
            logging.debug("resume_job not supported for %s", job.id)

    # Unblock future events
    now = datetime.now(timezone.utc)
    for event_id in db.get_blocked_events_future(now):
        db.set_status(event_id, "PENDING", "Emergency stop cleared")
    await schedule_all_pending()
    await broadcast.push({"type": "estop", "active": False})
    return {"ok": True}


@app.websocket("/ws")
async def ws_endp(ws: WebSocket):
    await broadcast.register(ws)
    try:
        while True:
            # We don't expect messages; keep-alive
            await ws.receive_text()
    except WebSocketDisconnect:
        await broadcast.unregister(ws)
    except Exception:  # pragma: no cover
        await broadcast.unregister(ws)


# --------------------------- Watchdog wiring --------------------------------

async def start_watching_signals():
    global _OBSERVER
    if not _WATCHDOG_AVAILABLE:
        logging.info("Watchdog not available; skipping file watching")
        return

    loop = asyncio.get_running_loop()

    class Handler(FileSystemEventHandler):  # type: ignore
        def __init__(self, signals_dir: Path):
            super().__init__()
            self.signals_dir = signals_dir

        def on_created(self, event):  # type: ignore
            try:
                if getattr(event, "is_directory", False):
                    return
                if str(event.src_path).lower().endswith(".csv"):
                    asyncio.run_coroutine_threadsafe(
                        integration.process_signal_file(event.src_path),
                        loop,
                    )
            except Exception:  # pragma: no cover
                logging.exception("Watchdog on_created failed")

    # Watch import directory, not export directory to avoid self-triggering
    handler = Handler(Path(config.signals_import_path))
    _OBSERVER = Observer()
    _OBSERVER.schedule(handler, config.signals_import_path, recursive=False)
    _OBSERVER.daemon = True

    def _start():  # pragma: no cover
        try:
            _OBSERVER.start()
            logging.info("Watchdog observing %s", config.signals_import_path)
        except Exception:
            logging.exception("Failed starting watchdog")

    # Run in a thread
    loop.run_in_executor(None, _start)


# ----------------------------------------------------------------------------
# Static files (conditionally mounted)
# ----------------------------------------------------------------------------

try:
    from fastapi.staticfiles import StaticFiles

    static_path = Path(config.static_dir)
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    else:
        logging.info("Static directory %s not present; skipping mount", static_path)
except Exception:  # pragma: no cover
    logging.info("fastapi.staticfiles unavailable; skipping static mount")


# ----------------------------------------------------------------------------
# Minimal HTML dashboard (buttons cleaned up; safe WS URL)
# ----------------------------------------------------------------------------

_DASHBOARD_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Calendar Dashboard</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 24px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; }
    th { background: #f7f7f7; text-align: left; }
    .high-impact { font-weight: bold; }
    .medium-impact { opacity: 0.85; }
    .low-impact { opacity: 0.7; }
    .pill { padding: 2px 8px; border-radius: 999px; font-size: 12px; }
    .PENDING { background:#eef; }
    .TRIGGERED { background:#efe; }
    .BLOCKED { background:#fee; }
    .SUPPRESSED { background:#ffd; }
  </style>
</head>
<body>
  <h1>Python Calendar System</h1>
  <div style="display:flex; gap:8px; margin-bottom: 12px;">
    <button id="importBtn">Run Import</button>
    <button id="stopBtn">Emergency Stop</button>
    <button id="resumeBtn">Resume</button>
  </div>
  <div id="meta"></div>
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>Title</th>
        <th>Country</th>
        <th>Impact</th>
        <th>Trigger Time (UTC)</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody id="rows"></tbody>
  </table>

  <script>
    async function refresh() {
      const res = await fetch('/events');
      const data = await res.json();
      const rows = document.getElementById('rows');
      rows.innerHTML = '';
      for (const ev of data.events) {
        const tr = document.createElement('tr');
        const impClass = (ev.impact||'').toLowerCase()+'-impact';
        tr.innerHTML = `
          <td>${ev.id}</td>
          <td>${ev.title}</td>
          <td>${ev.country}</td>
          <td class="${impClass}">${ev.impact||''}</td>
          <td>${ev.trigger_time}</td>
          <td><span class="pill ${ev.status}">${ev.status}</span></td>
        `;
        rows.appendChild(tr);
      }
      const meta = document.getElementById('meta');
      meta.textContent = `Next import: ${data.next_import} | Emergency stop: ${data.estop}`;
    }

    async function post(url){
      await fetch(url, {method:'POST'});
      await refresh();
    }

    document.getElementById('importBtn').onclick = ()=> post('/import');
    document.getElementById('stopBtn').onclick = ()=> post('/emergency/stop');
    document.getElementById('resumeBtn').onclick = ()=> post('/emergency/resume');

    function openWS(){
      const proto = (location.protocol === 'https:') ? 'wss' : 'ws';
      const ws = new WebSocket(`${proto}://${location.host}/ws`);
      ws.onmessage = (evt)=>{
        try { const msg = JSON.parse(evt.data); } catch { return; }
        refresh();
      };
      ws.onclose = ()=> setTimeout(openWS, 2000);
    }

    refresh();
    openWS();
  </script>
</body>
</html>
"""


# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------

def export_configuration(config: SystemConfig, path: str = "config.yaml") -> None:
    Path(path).write_text(yaml.dump(config.model_dump(), default_flow_style=False, sort_keys=False), encoding="utf-8")


# ----------------------------------------------------------------------------
# Main entry
# ----------------------------------------------------------------------------

async def run_system_tests() -> None:  # minimal smoke tests
    # Import a couple demo events and verify scheduling
    await import_job()
    await schedule_all_pending()
    print("Test run complete; events:", len(db.list_all()))


def main() -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(run_system_tests())
    else:
        main()
