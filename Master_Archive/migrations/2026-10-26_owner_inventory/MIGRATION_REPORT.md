# Archive migration report - 2026-10-26

Status: **PARTIALLY COMPLETE** (5 entries BLOCKED, 64 archived).

Base: master @ `1fc267b`. Branch: `chore/archive-inventory-2026-10-26`. Moves used `git mv`; every file's SHA-256 was recorded before and checked after the move.

## Counts (from `migration_manifest.json`)
| Metric | Value |
|---|---|
| Inventory entries (after splitting grouped lines) | 70 |
| Unique normalized paths | 69 |
| Duplicate entries | 1 (PATTERN_INDEX.yaml listed twice) |
| File entries / directory entries | 63 / 6 |
| File entries moved | 61 |
| Directory entries moved | 3 (branch-archive, backups, docs/api) |
| Total files moved (incl. directory contents) | 123 |
| Already archived | 0 |
| Blocked / out of scope | 5 / 0 |
| Missing or unresolved | 0 |
| Reference updates | 0 |

## Layout
Root items go to `Master_Archive/<name>`; `docs/...` items go to `Master_Archive/docs/...`, so `docs/README.md` cannot collide with `Master_Archive/README.md`. No existing archive file was overwritten. Each moved file has an `archive_manifest.json` entry with `replacement: null` and `reviewer_decision: owner_inventory_2026-10-26`, because the owner inventory does not name replacements.

## Resolved ambiguities
- `docs/adr/0110000001260118_ADR-0001-` is `docs/adr/0110000001260118_ADR-0001-service-decomposition.md` (only candidate).
- `0110000015260118_slo-definitions.md` has no directory in the inventory; the only match in the repo is `docs/observability/0110000015260118_slo-definitions.md`. **Please confirm this was intended.**
- `branch-archive (54)` counts files (54, in 2 top-level entries). `backups (7)` counts files (7).

## BLOCKED (left in place)
| Path | Reason |
|---|---|
| `EAFIX_Consolidation_Review.zip` | Cited by path and sha256 as evidence in governance/module_consolidation/resolution_decisions.json (DEC-036) and run/baseline_continuity.json; consolidation holds still open. Needs owner decision. |
| `doc_id_subsystem` | Active consumers: .github/workflows/1299900011260118_doc_id_validation.yml, Makefile doc-id targets, tests/doc_id_subsystem imports (doc_id_subsystem.core...). Move would break CI and imports. |
| `The_Process` | Holds EAFIX_PROCESS_AUTHORITY_REPAIR_AND_REGISTRY_CONSOLIDATION_PLAN_v1_1_0.json, named as the live replacement in Master_Archive/archive_manifest.json; archiving would demote a current authority. Needs owner decision. |
| `scenarios` | tests/contracts/2099900225260118_conftest.py imports scenarios.test_trading_flow_scenarios; the file is an import shim for tests/contracts/scenarios. |
| `docs/reference/generated/indicator_record.schema.json` | Generated output asserted by tests/migration/test_p20_regeneration.py at this path; moving would fail the regeneration test. |

## Moved with caveats (no code consumers found, so not blocked)
- `PATTERN_INDEX.yaml`, `routing_rules*.json`, `submodule_*catalog*.json`: referenced only as path strings in `.state/evidence/**` records and four `.state/patterns/*/test_fixture/input.json` inputs. No script reads them. Not listed in `doc_authority.json`. If pattern golden tests are run later, those fixtures need the new path.
- `COUNTER_STORE.json` is an ID allocation counter (`next_id_to_issue`). Nothing in the repo reads it; if an outside tool does, restore it.
- `docs/reference/2010000001260118_apf_apply_stub.py` appears as a path in `context_packets/50000000000000000099/context_packet.json` and in inventory/mapping data; those are records and were left unchanged.
- `langgraph_*.py` are byte-identical to `branch-archive/main/` copies. `.gemini/GEMINI.md` line 23 still mentions `langgraph_git_integration.py` and was not edited.
- Historical mentions in ledgers, inventories and `file_list.txt` were intentionally not rewritten.

## Secrets
Pattern scan of moved text files found only documentation/code-sample strings (a secret-scanner description and examples); no credential values. Nothing was printed.

## Validation
See PR description for results of the checks that were run.
