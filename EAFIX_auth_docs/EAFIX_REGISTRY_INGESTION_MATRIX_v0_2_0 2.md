# EAFIX Registry Ingestion Matrix — v0.2.0 (dispositions folded)

- Repository: `DICKY1987/eafix-modular` · Pinned commit: `e846d04a6eede56e6b790701d0fa762fe90297d6`
- Status: **dispositions_folded_pending_validation** · Decisions folded: DEC-REG-008..014
- Append decisions from: `EAFIX_decision_registry_additions.jsonl`

## Resolved decisions

| decision | was | disposition |
|---|---|---|
| DEC-REG-008 | OD-1 | IndicatorVector canonical; IndicatorSnapshot alias; fix step S09 |
| DEC-REG-009 | OD-2 | OrderIntent.side=BUY/SELL; fix LONG/SHORT model |
| DEC-REG-010 | OD-3 | Split into two contracts; CSV name pending owner confirmation |
| DEC-REG-011 | OD-4 | Regenerate 27 packets before ingest |
| DEC-REG-012 | OD-5 | Author explicit dag_process_crosswalk; catalog is authority |
| DEC-REG-013 | OD-6 | Retire component entity; derive if needed |
| DEC-REG-014 | OD-7 | Do not promote snapshot records (zero delta) |

**Remaining owner input:** DEC-REG-010: confirm the split-out CSV contract name (proposed: ReentryMatrixOutcome)

## Candidate source rows

| source_id | exists | priority | governing decisions | human gate | status |
|---|:---:|:---:|---|:---:|---|
| SRC-CONTRACT-EVENTS | OK | P1 | DEC-REG-008,DEC-REG-009,DEC-REG-010 | no | folded |
| SRC-CONTRACT-MODELS | OK | P1 | DEC-REG-009,DEC-REG-010 | no | folded |
| SRC-CONTRACT-SNAPSHOT | OK | P1 | DEC-REG-014 | no | folded |
| SRC-CONTRACT-TRIGGERS | OK | P1 | — | no | skeleton |
| SRC-CTX-SCHEMA | OK | P1 | DEC-REG-011 | no | folded |
| SRC-CTX-PACKETS | OK | P1 | DEC-REG-011 | no | folded |
| SRC-DAG-CONFIG | OK | P1 | DEC-REG-012 | yes | folded |
| SRC-MANIFEST-GAP-REPORT | OK | P3 | — | no | skeleton |
| SRC-MANIFESTS-BUNDLE | OK | P1 | — | no | skeleton |
| SRC-REPO-AUTOOPS | OK | P2 | — | no | skeleton |
| SRC-EAREG-GENERATOR | OK | P2 | DEC-REG-013 | no | folded |
| SRC-CONTRACT-VALIDATORS | OK | P2 | — | no | skeleton |
| SRC-EAREG-SUPERSEDED | OK | EXCLUDE | — | no | skeleton |
| SRC-ARCHIVE-DNR | OK | EXCLUDE | — | no | skeleton |
| SRC-COMPONENTS-LEGACY | OK | EXCLUDE | DEC-REG-013 | no | folded |
