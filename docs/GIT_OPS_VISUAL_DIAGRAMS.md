<!-- doc_id: DOC-AUTOOPS-101 -->

# RepoAutoOps Visual Diagrams - Quick Reference

**Doc ID:** DOC-AUTOOPS-101  
**Version:** 1.0.0  
**Date:** 2026-01-21

---

## System Overview Diagram

```
╔═══════════════════════════════════════════════════════════════════════╗
║                     REPOAUTOOPS SYSTEM OVERVIEW                       ║
║                   Zero-Touch Git Automation System                    ║
╚═══════════════════════════════════════════════════════════════════════╝

    ┌─────────────────────────────────────────────────────────────┐
    │                        USER ACTIONS                         │
    ├─────────────────────────────────────────────────────────────┤
    │  • Create/edit files                                        │
    │  • Manual CLI commands                                      │
    │  • Scheduled tasks                                          │
    └────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
    ┌────▼─────┐                  ┌──────▼──────┐
    │FileWatch │                  │ Manual CLI  │
    │(async)   │                  │  Commands   │
    └────┬─────┘                  └──────┬──────┘
         │                               │
         │  ┌───────────────────────────┴┐
         │  │                            │
         └──▼────────────────────────────▼─┐
         ┌──────────────────────────────┐  │
         │      EventQueue (SQLite)     │◄─┘
         │   • Persistent               │
         │   • Deduplication            │
         │   • Status tracking          │
         └──────────────┬───────────────┘
                        │
         ┌──────────────▼───────────────┐
         │        Orchestrator          │
         │  (Pipeline Coordinator)      │
         └──────────────┬───────────────┘
                        │
         ┌──────────────┴───────────────┐
         │                              │
    ┌────▼────────┐              ┌──────▼──────┐
    │LoopPrevent  │              │ PolicyGate  │
    │• Suppress   │              │• Classify   │
    │  self-      │              │• Enforce    │
    │  induced    │              │  contracts  │
    └────┬────────┘              └──────┬──────┘
         │                              │
         │         ┌────────────────────┘
         │         │
         │    ┌────▼────────┐
         │    │IdentityPipe │
         │    │• 16-digit   │
         │    │  prefix     │
         │    │• Doc-ID     │
         │    └────┬────────┘
         │         │
         │    ┌────▼────────┐
         │    │ Validators  │
         │    │• Doc-ID ✓   │
         │    │• Secrets ✓  │
         │    │• Custom     │
         │    └────┬────────┘
         │         │
         └─────────┴──────────┐
                   │           │
              ┌────▼────────┐  │
              │ GitAdapter  │◄─┘
              │• Stage      │
              │• Commit     │
              │• Push       │
              └────┬────────┘
                   │
              ┌────▼────────┐
              │ AuditLogger │
              │  (JSONL)    │
              └─────────────┘
```

---

## Complete File Processing Flow

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    COMPLETE FILE PROCESSING FLOW                      ║
╚═══════════════════════════════════════════════════════════════════════╝

 USER: Creates "my_module.py"
    │
    │ OS File System Event
    ▼
╔═══════════════════════════════════════════════════════════════════╗
║ PHASE 1: DETECTION & QUEUING                                     ║
╚═══════════════════════════════════════════════════════════════════╝
    │
    ├─► FileWatcher.watch()
    │       ↓
    │   Check ignore patterns? ─Yes─► STOP
    │       ↓ No
    │   Check file patterns? ─No───► STOP
    │       ↓ Yes
    │   Wait for stability (2s)
    │       ↓
    │   Calculate MD5 hash
    │       ↓
    │   Create FileEvent
    │       ↓
    │   Callback: _on_file_event()
    │
    ├─► LoopPrevention.is_self_induced()
    │       ↓
    │   Self-induced? ─Yes─► STOP (Suppress)
    │       ↓ No
    │   EventQueue.enqueue()
    │       ↓
    │   SQLite: INSERT work_item
    │       ↓ status=PENDING
    │
╔═══════════════════════════════════════════════════════════════════╗
║ PHASE 2: PROCESSING PIPELINE                                     ║
╚═══════════════════════════════════════════════════════════════════╝
    │
    ├─► Orchestrator.process_queue()
    │       ↓ (every 2 seconds)
    │   EventQueue.dequeue_batch(10)
    │       ↓ status=PROCESSING
    │   For each work_item:
    │       ↓
    │   LoopPrevention.start_operation()
    │       ↓
    │
    ├─► PolicyGate.classify_file()
    │       ↓
    │   ┌─────────────────────────────────┐
    │   │ Forbidden?      ─Yes─► QUARANTINE │
    │   │ Canonical?      ─Yes─► CONTINUE   │
    │   │ Generated?      ─Yes─► DONE       │
    │   │ Run artifact?   ─Yes─► DONE       │
    │   │ Unknown?        ─Yes─► QUARANTINE │
    │   └─────────────────────────────────┘
    │       ↓ (if CANONICAL)
    │
    ├─► ValidationRunner.validate_file()
    │       ↓
    │   ┌──────────────────────────────┐
    │   │ DocIdValidator               │
    │   │   Has doc_id? ─No─► WARNING  │
    │   │             ─Yes─► PASS      │
    │   └──────────────────────────────┘
    │       ↓
    │   ┌──────────────────────────────┐
    │   │ SecretScanner                │
    │   │   Found secret? ─Yes─► FAIL  │
    │   │               ─No──► PASS    │
    │   └──────────────────────────────┘
    │       ↓
    │   All passed? ─No─► FAILED
    │       ↓ Yes
    │
    ├─► IdentityPipeline.process_file()
    │       ↓
    │   Has prefix? ─No─► Generate & rename
    │       ↓
    │   "my_module.py" → "20260121220345​67_my_module.py"
    │       ↓ (suppressed by LoopPrevention)
    │   Has doc_id? ─No─► Prepend header
    │       ↓
    │   Add: "# doc_id: DOC-AUTOOPS-099"
    │       ↓ (suppressed by LoopPrevention)
    │
    ├─► GitAdapter.stage_files()
    │       ↓
    │   Dry-run? ─Yes─► Log "Would run: git add ..."
    │       ↓ No       Return success
    │   Execute: git add 20260121220345​67_my_module.py
    │       ↓
    │   LoopPrevention.end_operation()
    │       ↓
    │   EventQueue.mark_done()
    │       ↓ status=DONE
    │
╔═══════════════════════════════════════════════════════════════════╗
║ PHASE 3: AUDIT & COMPLETION                                      ║
╚═══════════════════════════════════════════════════════════════════╝
    │
    └─► AuditLogger.log()
            ↓
        Append to _evidence/audit/20260121.jsonl:
        {
          "timestamp": "2026-01-21T22:03:45Z",
          "event": "file_processed",
          "path": "20260121220345​67_my_module.py",
          "classification": "canonical",
          "validations": "all_passed",
          "identity_assigned": true,
          "git_staged": true,
          "dry_run": true,
          "result": "success"
        }
            ↓
        END: Success ✅

RESULT:
═══════════════════════════════════════════════════════════════════
Original file:  my_module.py
Final file:     20260121220345​67_my_module.py
Doc-ID:         DOC-AUTOOPS-099 (in header)
Git status:     Staged (or would be staged in execute mode)
Queue status:   DONE
Audit:          Logged to JSONL
═══════════════════════════════════════════════════════════════════
```

---

## Module Contract Decision Tree

```
╔═══════════════════════════════════════════════════════════════════════╗
║                  FILE CLASSIFICATION DECISION TREE                    ║
╚═══════════════════════════════════════════════════════════════════════╝

                    FILE: "example_file.ext"
                              │
                              ▼
                    ┌─────────────────────┐
                    │ Find module         │
                    │ for path            │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
             Module found?                Module found?
                 │ NO                        │ YES
                 ▼                           ▼
         ╔═══════════════════╗      ┌──────────────────┐
         ║  QUARANTINE       ║      │ Load contract    │
         ║  Reason: No       ║      └────────┬─────────┘
         ║  module contract  ║               │
         ╚═══════════════════╝               ▼
                                   ┌──────────────────┐
                                   │ Check FORBIDDEN  │
                                   │ patterns         │
                                   └────────┬─────────┘
                                            │
                              ┌─────────────┴──────────────┐
                              │ NO                         │ YES
                              ▼                            ▼
                    ┌──────────────────┐          ╔═══════════════════╗
                    │ Check CANONICAL  │          ║  QUARANTINE       ║
                    │ allowlist        │          ║  Reason: Forbidden║
                    └────────┬─────────┘          ║  pattern match    ║
                             │                    ╚═══════════════════╝
               ┌─────────────┴──────────────┐
               │ YES                        │ NO
               ▼                            ▼
       ╔═══════════════════╗      ┌──────────────────┐
       ║  CANONICAL        ║      │ Check GENERATED  │
       ║  Reason: In       ║      │ patterns         │
       ║  allowlist        ║      └────────┬─────────┘
       ║  Action: Stage    ║               │
       ║  for commit       ║ ┌─────────────┴──────────────┐
       ╚═══════════════════╝ │ YES                        │ NO
                             ▼                            ▼
                   ╔═══════════════════╗        ┌──────────────────┐
                   ║  GENERATED        ║        │ Check RUN        │
                   ║  Reason: Auto-    ║        │ ARTIFACT         │
                   ║  generated file   ║        │ patterns         │
                   ║  Action: Ignore,  ║        └────────┬─────────┘
                   ║  .gitignore       ║                 │
                   ╚═══════════════════╝   ┌─────────────┴──────────────┐
                                           │ YES                        │ NO
                                           ▼                            ▼
                                 ╔═══════════════════╗        ╔═══════════════════╗
                                 ║  RUN_ARTIFACT     ║        ║  QUARANTINE       ║
                                 ║  Reason: Runtime  ║        ║  Reason: Not in   ║
                                 ║  output file      ║        ║  any allowlist    ║
                                 ║  Action: Ignore   ║        ║  Action: Move to  ║
                                 ╚═══════════════════╝        ║  _quarantine for  ║
                                                              ║  manual review    ║
                                                              ╚═══════════════════╝

EXAMPLE CLASSIFICATIONS:
═══════════════════════════════════════════════════════════════════════

┌──────────────────────┬───────────────┬─────────────────────────────┐
│ File                 │ Classification│ Reason                      │
├──────────────────────┼───────────────┼─────────────────────────────┤
│ main.py              │ CANONICAL     │ Matches *.py allowlist      │
│ README.md            │ CANONICAL     │ Explicitly allowed          │
│ __pycache__/x.pyc    │ GENERATED     │ Matches generated pattern   │
│ output.log           │ RUN_ARTIFACT  │ Matches *.log pattern       │
│ secrets.txt          │ QUARANTINE    │ Forbidden pattern           │
│ unknown.xyz          │ QUARANTINE    │ Not in any list             │
│ malware.exe          │ QUARANTINE    │ Forbidden pattern           │
└──────────────────────┴───────────────┴─────────────────────────────┘
```

---

## Identity Assignment Flow

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    IDENTITY ASSIGNMENT PROCESS                        ║
╚═══════════════════════════════════════════════════════════════════════╝

INPUT: "my_module.py"
   │
   │ NO PREFIX, NO DOC-ID
   │
   ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ STEP 1: GENERATE 16-DIGIT PREFIX                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
   │
   ├─► Get current timestamp:
   │   datetime.utcnow() → 2026-01-21 22:03:45.​67
   │
   ├─► Format as 16 digits:
   │   YYYYMMDDHHmmssff
   │   2026 01 21 22 03 45 67
   │   │    │  │  │  │  │  └─ Centiseconds
   │   │    │  │  │  │  └──── Seconds
   │   │    │  │  │  └──────── Minutes
   │   │    │  │  └─────────── Hour
   │   │    │  └────────────── Day
   │   │    └───────────────── Month
   │   └────────────────────── Year
   │
   ├─► Result: "20260121220345​67"
   │
   ├─► Construct new filename:
   │   "20260121220345​67" + "_" + "my_module.py"
   │   = "20260121220345​67_my_module.py"
   │
   └─► Rename file:
       os.rename("my_module.py", "20260121220345​67_my_module.py")
       (File system event suppressed by LoopPrevention)
   │
   │ FILE NOW: "20260121220345​67_my_module.py"
   │
   ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ STEP 2: ASSIGN DOC-ID                                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
   │
   ├─► Doc-ID provided: "DOC-AUTOOPS-099"
   │
   ├─► Determine file type: .py
   │
   ├─► Select header format:
   │   Python → "# doc_id: {doc_id}\n"
   │   Markdown → "<!-- doc_id: {doc_id} -->\n\n"
   │
   ├─► Read current file content:
   │   ┌──────────────────────────┐
   │   │ def my_function():       │
   │   │     return "hello"       │
   │   └──────────────────────────┘
   │
   ├─► Prepend doc_id header:
   │   ┌──────────────────────────────────────┐
   │   │ # doc_id: DOC-AUTOOPS-099            │
   │   │                                      │
   │   │ def my_function():                   │
   │   │     return "hello"                   │
   │   └──────────────────────────────────────┘
   │
   └─► Write modified content
       (File system event suppressed by LoopPrevention)
   │
   │ FILE FINAL STATE:
   │
   ▼
╔═══════════════════════════════════════════════════════════════════╗
║ Filename: 20260121220345​67_my_module.py                          ║
║ Content:                                                          ║
║ ┌─────────────────────────────────────────────────────────────┐ ║
║ │ # doc_id: DOC-AUTOOPS-099                                   │ ║
║ │                                                             │ ║
║ │ def my_function():                                          │ ║
║ │     return "hello"                                          │ ║
║ └─────────────────────────────────────────────────────────────┘ ║
╚═══════════════════════════════════════════════════════════════════╝

IDENTITY COMPONENTS:
═══════════════════════════════════════════════════════════════════
16-Digit Prefix:  20260121220345​67 (in filename)
Doc-ID:           DOC-AUTOOPS-099 (in file header)
Original Name:    my_module.py (preserved with underscore)
═══════════════════════════════════════════════════════════════════
```

---

## Loop Prevention Mechanism

```
╔═══════════════════════════════════════════════════════════════════════╗
║                      LOOP PREVENTION TIMELINE                         ║
╚═══════════════════════════════════════════════════════════════════════╝

TIME: 22:00:00.000
EVENT: User creates "my_module.py"
───────────────────────────────────────────────────────────────────────
│
├─► FileWatcher detects CREATED event
├─► Enqueued to EventQueue
│
▼

TIME: 22:00:02.000
EVENT: Orchestrator processes work item
───────────────────────────────────────────────────────────────────────
│
├─► LoopPrevention.start_operation(
│       path="my_module.py",
│       operation_id=uuid-1234
│   )
│
│   INTERNAL STATE:
│   ┌────────────────────────────────────────┐
│   │ operations_in_progress = {             │
│   │   "my_module.py": Operation(           │
│   │     id=uuid-1234,                      │
│   │     started_at=22:00:02.000            │
│   │   )                                    │
│   │ }                                      │
│   └────────────────────────────────────────┘
│
▼

TIME: 22:00:02.500
EVENT: IdentityPipeline renames file
      "my_module.py" → "20260121220002​50_my_module.py"
───────────────────────────────────────────────────────────────────────
│
├─► FileSystem: File renamed
├─► FileWatcher detects MODIFIED event
│       path="20260121220002​50_my_module.py"
│
├─► Callback: _on_file_event()
│
├─► LoopPrevention.is_self_induced()
│       ↓
│   Check: operations_in_progress?
│       ↓
│   ┌────────────────────────────────────────┐
│   │ Path: "my_module.py" (original)        │
│   │ New:  "20260121220002​50_my_module.py" │
│   │ Match: YES (same file)                 │
│   │ In progress: YES                       │
│   └────────────────────────────────────────┘
│       ↓
│   RESULT: TRUE (self-induced)
│
├─► ACTION: SUPPRESS EVENT
│       ↓
│   ╔═══════════════════════════════════╗
│   ║ EVENT SUPPRESSED                  ║
│   ║ Log: "self_induced_in_progress"   ║
│   ║ Do not enqueue                    ║
│   ╚═══════════════════════════════════╝
│
▼

TIME: 22:00:03.000
EVENT: Processing completes
───────────────────────────────────────────────────────────────────────
│
├─► LoopPrevention.end_operation(uuid-1234)
│
│   INTERNAL STATE:
│   ┌────────────────────────────────────────┐
│   │ operations_in_progress = {} (empty)    │
│   │ recent_operations = {                  │
│   │   "20260121220002​50_my_module.py":    │
│   │       completed_at=22:00:03.000        │
│   │ }                                      │
│   └────────────────────────────────────────┘
│
▼

TIME: 22:00:04.500
EVENT: Another file event (e.g., editor auto-save)
───────────────────────────────────────────────────────────────────────
│
├─► FileWatcher detects MODIFIED event
│       path="20260121220002​50_my_module.py"
│
├─► LoopPrevention.is_self_induced()
│       ↓
│   Check 1: operations_in_progress?
│       NO (operation ended)
│       ↓
│   Check 2: recent_operations?
│       ↓
│   ┌────────────────────────────────────────┐
│   │ Path in recent_operations: YES         │
│   │ Completed at: 22:00:03.000             │
│   │ Current time: 22:00:04.500             │
│   │ Elapsed: 1.5 seconds                   │
│   │ Suppression window: 5 seconds          │
│   │ Within window: YES                     │
│   └────────────────────────────────────────┘
│       ↓
│   RESULT: TRUE (recently completed)
│
├─► ACTION: SUPPRESS EVENT
│       ↓
│   ╔═══════════════════════════════════╗
│   ║ EVENT SUPPRESSED                  ║
│   ║ Log: "self_induced_recent"        ║
│   ║ Do not enqueue                    ║
│   ╚═══════════════════════════════════╝
│
▼

TIME: 22:00:10.000
EVENT: User manually edits file (outside suppression window)
───────────────────────────────────────────────────────────────────────
│
├─► FileWatcher detects MODIFIED event
│       path="20260121220002​50_my_module.py"
│
├─► LoopPrevention.is_self_induced()
│       ↓
│   Check 1: operations_in_progress?
│       NO
│       ↓
│   Check 2: recent_operations?
│       ↓
│   ┌────────────────────────────────────────┐
│   │ Completed at: 22:00:03.000             │
│   │ Current time: 22:00:10.000             │
│   │ Elapsed: 7 seconds                     │
│   │ Suppression window: 5 seconds          │
│   │ Within window: NO                      │
│   └────────────────────────────────────────┘
│       ↓
│   RESULT: FALSE (outside window)
│
├─► ACTION: PROCESS EVENT NORMALLY
│       ↓
│   ╔═══════════════════════════════════╗
│   ║ EVENT PROCESSED                   ║
│   ║ Enqueue to EventQueue             ║
│   ║ Normal pipeline execution         ║
│   ╚═══════════════════════════════════╝
│
▼

SUMMARY:
═══════════════════════════════════════════════════════════════════
Suppression Window: 5 seconds after operation completion
Self-Induced Events: 2 (both suppressed successfully)
User Event: 1 (processed normally after window expired)
Result: NO INFINITE LOOP ✅
═══════════════════════════════════════════════════════════════════
```

---

## Git Operations Workflow

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    GIT OPERATIONS WORKFLOW                            ║
╚═══════════════════════════════════════════════════════════════════════╝

SCENARIO: Commit and push validated file

┌───────────────────────────────────────────────────────────────────┐
│ STEP 1: STAGE FILES                                              │
└───────────────────────────────────────────────────────────────────┘
│
├─► GitAdapter.stage_files([
│       "20260121220345​67_my_module.py"
│   ])
│
│   ┌──────────────────────────────────────┐
│   │ Check: Dry-run mode?                 │
│   │   YES → Log "Would run: git add ..." │
│   │         Return success               │
│   │   NO  → Continue                     │
│   └──────────────────────────────────────┘
│
├─► Execute: git -C /repo/root add 20260121220345​67_my_module.py
│
│   ┌──────────────────────────────────────┐
│   │ SUCCESS                              │
│   │ OperationResult:                     │
│   │   success: true                      │
│   │   message: "Staged 1 files"          │
│   │   metadata: {file_count: 1}          │
│   └──────────────────────────────────────┘
│
▼

┌───────────────────────────────────────────────────────────────────┐
│ STEP 2: CREATE COMMIT                                            │
└───────────────────────────────────────────────────────────────────┘
│
├─► GitAdapter.commit(
│       message="feat: Add my_module with identity"
│   )
│
│   ┌──────────────────────────────────────┐
│   │ Check: Dry-run mode?                 │
│   │   YES → Log "Would commit"           │
│   │         Return success               │
│   │   NO  → Continue                     │
│   └──────────────────────────────────────┘
│
├─► Execute: git -C /repo/root commit -m "feat: Add my_module..."
│
│   ┌──────────────────────────────────────┐
│   │ SUCCESS                              │
│   │ [master abc123d] feat: Add...        │
│   │  1 file changed, 5 insertions(+)     │
│   │                                      │
│   │ OperationResult:                     │
│   │   success: true                      │
│   │   message: "Commit created"          │
│   │   output: "abc123d"                  │
│   └──────────────────────────────────────┘
│
▼

┌───────────────────────────────────────────────────────────────────┐
│ STEP 3: PULL WITH REBASE (sync with remote)                      │
└───────────────────────────────────────────────────────────────────┘
│
├─► GitAdapter.pull_rebase()
│
├─► Execute: git -C /repo/root pull --rebase
│
│   ┌──────────────────────────────────────┐
│   │ Check result:                        │
│   │                                      │
│   │ ┌─ SUCCESS ────────────────────────┐ │
│   │ │ Current branch master is up      │ │
│   │ │ to date.                         │ │
│   │ └──────────────────────────────────┘ │
│   │         ↓                            │
│   │ ┌─ OR: FAST-FORWARD ───────────────┐ │
│   │ │ Fast-forwarded master to         │ │
│   │ │ origin/master                    │ │
│   │ └──────────────────────────────────┘ │
│   │         ↓                            │
│   │ ┌─ OR: CONFLICT ───────────────────┐ │
│   │ │ CONFLICT (content): Merge        │ │
│   │ │ conflict in file.txt             │ │
│   │ │ ACTION: Create quarantine branch │ │
│   │ └──────────────────────────────────┘ │
│   └──────────────────────────────────────┘
│
│   ┌──────────────────────────────────────┐
│   │ OperationResult:                     │
│   │   success: true                      │
│   │   message: "Pull successful"         │
│   └──────────────────────────────────────┘
│
▼

┌───────────────────────────────────────────────────────────────────┐
│ STEP 4: PUSH TO REMOTE (with retry)                              │
└───────────────────────────────────────────────────────────────────┘
│
├─► GitAdapter.push(retry_count=0)
│
├─► Execute: git -C /repo/root push
│
│   ┌──────────────────────────────────────────────────┐
│   │ Attempt 1: git push                              │
│   │   ↓                                              │
│   │ ┌─ SUCCESS ───────────────────────────────────┐  │
│   │ │ To https://github.com/user/repo.git         │  │
│   │ │    abc123d..def456e  master -> master       │  │
│   │ │ SUCCESS ✅                                   │  │
│   │ └─────────────────────────────────────────────┘  │
│   │         ↓                                        │
│   │ ┌─ OR: NETWORK ERROR ─────────────────────────┐  │
│   │ │ fatal: unable to access                     │  │
│   │ │ ACTION: Retry                               │  │
│   │ │   ↓                                         │  │
│   │ │ Wait: 5 seconds (backoff[0])                │  │
│   │ │   ↓                                         │  │
│   │ │ Attempt 2: git push                         │  │
│   │ │   ↓                                         │  │
│   │ │ Still fails?                                │  │
│   │ │   ↓                                         │  │
│   │ │ Wait: 15 seconds (backoff[1])               │  │
│   │ │   ↓                                         │  │
│   │ │ Attempt 3: git push                         │  │
│   │ │   ↓                                         │  │
│   │ │ Still fails?                                │  │
│   │ │   ↓                                         │  │
│   │ │ Wait: 45 seconds (backoff[2])               │  │
│   │ │   ↓                                         │  │
│   │ │ Final attempt: git push                     │  │
│   │ │   ↓                                         │  │
│   │ │ SUCCESS or give up                          │  │
│   │ └─────────────────────────────────────────────┘  │
│   └──────────────────────────────────────────────────┘
│
│   ┌──────────────────────────────────────┐
│   │ OperationResult:                     │
│   │   success: true                      │
│   │   message: "Push successful"         │
│   │   metadata: {retry_count: 0}         │
│   └──────────────────────────────────────┘
│
▼

COMPLETE WORKFLOW RESULT:
═══════════════════════════════════════════════════════════════════
Stage:   ✅ 1 file staged
Commit:  ✅ abc123d created
Pull:    ✅ Up to date (or fast-forwarded)
Push:    ✅ Pushed to origin/master
═══════════════════════════════════════════════════════════════════
```

---

## Validation Plugin System

```
╔═══════════════════════════════════════════════════════════════════════╗
║                   VALIDATION PLUGIN ARCHITECTURE                      ║
╚═══════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│                    ValidationRunner                             │
│                 (Orchestrates all validators)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ validators: List[Validator]
                         │
         ┌───────────────┼───────────────┬────────────────┐
         │               │               │                │
    ┌────▼─────┐   ┌─────▼──────┐  ┌────▼────────┐  ┌───▼────────┐
    │ DocId    │   │  Secret    │  │  Custom     │  │  Custom    │
    │Validator │   │  Scanner   │  │Validator 1  │  │Validator 2 │
    └────┬─────┘   └─────┬──────┘  └────┬────────┘  └───┬────────┘
         │               │               │               │
         │               │               │               │
         └───────────────┴───────────────┴───────────────┘
                         │
                         │ All return ValidationResult
                         │
                         ▼
                ┌────────────────┐
                │ Aggregate      │
                │ Results        │
                └────────┬───────┘
                         │
                         ▼
                    all_passed()?
                         │
         ┌───────────────┴───────────────┐
         │ YES                           │ NO
         ▼                               ▼
    Continue processing            Mark FAILED, stop


VALIDATOR INTERFACE:
═══════════════════════════════════════════════════════════════════
class Validator(Protocol):
    def validate(self, path: Path) -> ValidationResult
        """
        Validate a file and return result.
        
        Returns:
            ValidationResult with:
            - passed: bool
            - validator_name: str
            - message: str
            - details: Optional[Dict]
            - suggestions: List[str]
        """


BUILT-IN VALIDATORS:
═══════════════════════════════════════════════════════════════════

1. DocIdValidator
   ┌────────────────────────────────────────────────────────┐
   │ Purpose: Check for doc_id presence                     │
   │ Patterns searched:                                     │
   │   • # doc_id: DOC-XXX-NNN                              │
   │   • __doc_id__ = "DOC-XXX-NNN"                         │
   │   • <!-- doc_id: DOC-XXX-NNN -->                       │
   │                                                        │
   │ Configuration:                                         │
   │   required: bool (default False)                       │
   │                                                        │
   │ Results:                                               │
   │   PASS: Doc-ID found (or not required)                 │
   │   FAIL: No doc-ID and required=True                    │
   └────────────────────────────────────────────────────────┘

2. SecretScanner
   ┌────────────────────────────────────────────────────────┐
   │ Purpose: Detect hardcoded secrets                      │
   │ Patterns detected:                                     │
   │   • password|passwd|pwd = "..."                        │
   │   • api_key|apikey = "..."                             │
   │   • secret|token = "..."                               │
   │   • -----BEGIN PRIVATE KEY-----                        │
   │   • aws_access_key_id = "..."                          │
   │                                                        │
   │ Results:                                               │
   │   PASS: No secrets found                               │
   │   FAIL: Secret(s) detected with details                │
   │         - type: "password" | "api_key" | ...           │
   │         - line: line number                            │
   │         - match: matched text (truncated)              │
   └────────────────────────────────────────────────────────┘


CUSTOM VALIDATOR EXAMPLE:
═══════════════════════════════════════════════════════════════════

# plugins/validators/copyright_validator.py

class CopyrightValidator:
    def validate(self, path: Path) -> ValidationResult:
        if not path.suffix in ['.py', '.js', '.java']:
            return ValidationResult(
                passed=True,
                validator_name="copyright",
                message="File type does not require copyright"
            )
        
        content = path.read_text()
        
        if "Copyright (c)" in content:
            return ValidationResult(
                passed=True,
                validator_name="copyright",
                message="Copyright notice found"
            )
        else:
            return ValidationResult(
                passed=False,
                validator_name="copyright",
                message="Missing copyright notice",
                suggestions=["Add copyright header to file"]
            )

# Register in config.yaml:
validation:
  custom_validators:
    - copyright_validator


VALIDATION FLOW:
═══════════════════════════════════════════════════════════════════
File → ValidationRunner.validate_file(path)
  ├─► DocIdValidator.validate(path)      → Result 1
  ├─► SecretScanner.validate(path)       → Result 2
  ├─► CopyrightValidator.validate(path)  → Result 3
  └─► CustomValidator.validate(path)     → Result 4
       ↓
  Aggregate: [Result1, Result2, Result3, Result4]
       ↓
  all_passed = all(r.passed for r in results)
       ↓
  ┌─────────────────────┐
  │ if all_passed:      │
  │   Continue pipeline │
  │ else:               │
  │   Log failures      │
  │   Mark FAILED       │
  │   Stop processing   │
  └─────────────────────┘
```

---

## System States & Transitions

```
╔═══════════════════════════════════════════════════════════════════════╗
║                  WORK ITEM STATE MACHINE                              ║
╚═══════════════════════════════════════════════════════════════════════╝

┌──────────────┐
│  File Event  │ (File system change detected)
└──────┬───────┘
       │ EventQueue.enqueue()
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                       PENDING                                    │
│  • Waiting in queue                                              │
│  • Not yet processed                                             │
│  • Can be dequeued by orchestrator                               │
└────────────────────┬─────────────────────────────────────────────┘
                     │
                     │ Orchestrator.dequeue_batch()
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                    PROCESSING                                    │
│  • Currently being processed                                     │
│  • Loop prevention active                                        │
│  • Pipeline operations in progress                               │
└────────────────────┬─────────────────────────────────────────────┘
                     │
         ┌───────────┴────────────┬──────────────┬──────────────┐
         │                        │              │              │
         │ Success                │ Validation   │ Error        │ Quarantine
         │                        │ Failed       │              │ Needed
         ▼                        ▼              ▼              ▼
┌─────────────────┐   ┌─────────────────┐   ┌──────────┐   ┌────────────┐
│      DONE       │   │     FAILED      │   │  FAILED  │   │ QUARANTINED│
│  • Processed    │   │  • Validation   │   │  • Error │   │ • Unknown  │
│    successfully │   │    failed       │   │    during │   │   file type│
│  • Logged to    │   │  • Logged       │   │    proc.  │   │ • Forbidden│
│    audit        │   │  • Not staged   │   │  • Retry  │   │   pattern  │
│  • May be       │   │  • Manual       │   │    later  │   │ • Manual   │
│    cleaned up   │   │    review       │   │           │   │   review   │
└─────────────────┘   └─────────────────┘   └──────────┘   └────────────┘


STATE PROPERTIES:
═══════════════════════════════════════════════════════════════════
┌──────────────┬──────────┬──────────┬─────────────────────────┐
│ State        │ Attempts │ Error    │ Next Action             │
├──────────────┼──────────┼──────────┼─────────────────────────┤
│ PENDING      │ 0        │ NULL     │ Will be processed       │
│ PROCESSING   │ 1+       │ NULL     │ Currently processing    │
│ DONE         │ N/A      │ NULL     │ Cleanup after 24h       │
│ FAILED       │ Max      │ Set      │ Manual intervention     │
│ QUARANTINED  │ N/A      │ Set      │ Manual review           │
└──────────────┴──────────┴──────────┴─────────────────────────┘

EXAMPLE TRANSITIONS:
═══════════════════════════════════════════════════════════════════
Scenario 1: Successful Processing
  PENDING → PROCESSING → DONE
  
Scenario 2: Validation Failure
  PENDING → PROCESSING → FAILED (no doc_id, secrets found)
  
Scenario 3: Unknown File Type
  PENDING → PROCESSING → QUARANTINED (not in any allowlist)
  
Scenario 4: Processing Error
  PENDING → PROCESSING → FAILED (git command failed)
  
Scenario 5: Retry After Error
  PENDING → PROCESSING → FAILED → (manual fix) → PENDING → ...
```

---

## Documentation Index

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    COMPLETE DOCUMENTATION INDEX                       ║
╚═══════════════════════════════════════════════════════════════════════╝

MAIN DOCUMENTS:
═══════════════════════════════════════════════════════════════════════

1. COMPLETE_SYSTEM_DOCUMENTATION.md (DOC-AUTOOPS-100)
   • All phases detailed documentation
   • Component specifications
   • Implementation details
   • 66KB comprehensive reference

2. VISUAL_DIAGRAMS.md (DOC-AUTOOPS-101) - THIS DOCUMENT
   • Quick reference diagrams
   • Flow visualizations
   • Decision trees
   • State machines

3. RUNBOOK.md (DOC-AUTOOPS-071)
   • Operational guide
   • CLI commands
   • Troubleshooting
   • Daily operations
   • 11KB practical guide

4. PROJECT_COMPLETION_SUMMARY.md
   • Delivery metrics
   • Success criteria
   • GitHub status
   • Phase summaries

ARCHITECTURE DOCUMENTS:
═══════════════════════════════════════════════════════════════════════

5. GIT_AUTOMATION_ARCHITECTURE_COMPLETE.txt (62KB)
   • Complete system architecture
   • Trigger taxonomy
   • Component specifications

6. GIT_AUTOMATION_GAP_ANALYSIS.txt (71KB)
   • Gap identification
   • Implementation roadmap
   • Prioritized backlog

PHASE SUMMARIES:
═══════════════════════════════════════════════════════════════════════

7. PHASE_1_DELIVERY_SUMMARY.md
   • MVP foundation details
   • Installation validation
   • Quick start guide

CONFIGURATION:
═══════════════════════════════════════════════════════════════════════

8. config/repo_autoops.yaml (DOC-AUTOOPS-041)
   • System configuration
   • All settings documented

9. config/module_contracts/*.yaml (DOC-AUTOOPS-043)
   • Module contract examples
   • Policy definitions

SOURCE CODE:
═══════════════════════════════════════════════════════════════════════

10. repo_autoops/ (11 modules)
    • All source code with doc_ids
    • Complete implementation
    • ~3,500 lines of code

TESTS:
═══════════════════════════════════════════════════════════════════════

11. tests/ (6 test files)
    • 53 comprehensive tests
    • 100% passing
    • Full coverage


QUICK NAVIGATION:
═══════════════════════════════════════════════════════════════════════
Getting Started     → RUNBOOK.md
Understanding       → COMPLETE_SYSTEM_DOCUMENTATION.md
Visual Overview     → VISUAL_DIAGRAMS.md (this file)
Operations          → RUNBOOK.md
Configuration       → config/repo_autoops.yaml
Troubleshooting     → RUNBOOK.md § Troubleshooting
Architecture        → GIT_AUTOMATION_ARCHITECTURE_COMPLETE.txt
Implementation      → COMPLETE_SYSTEM_DOCUMENTATION.md § Phases
```

---

**End of Visual Diagrams Quick Reference**

For detailed information, see:
- COMPLETE_SYSTEM_DOCUMENTATION.md (66KB)
- RUNBOOK.md (11KB)
- Repository: https://github.com/DICKY1987/eafix-modular

