# EAFIX consolidation continuation — 2026-10-04

**Result: BLOCKED for final acceptance. Independent execution continues under scoped holds.**

Verified the ZIP committed at `296694a3c275dc2227a4da0559e55a0c499944a9`:
SHA-256 `4590170f18ec65e377063abefe6cd41d29752ca13b9c88c026657bc0b690e055`,
CRC check and 15 package checksums pass. Its nine commits applied cleanly
onto fresh master `f37f8ca8bd966031fb243a9cd9401b065c29135a` on branch
`ai/module-authority-resume-20261004`. DEC-034 records the intervening three owner
deletions and matching ZIP addition. None changed roots, process/contract
registries, runtime code or risk behavior. Historical evidence commits remain
unchanged; three deleted zero-claim source records are retained in
`run/previous_baseline/` and excluded from the fresh active inventory.

DEC-035 adds eight source-grounded static observations to two pilot candidates
(U2 GUI gateway and SK2 idempotency). Five code files were read completely; this
is not complete atomic claim extraction or source reconciliation. Three GUI
conformance findings remain open: standalone/plugin API selection, missing
aggregator/health helpers and no WebSocket route in the reviewed entrypoints.
Idempotency helper defaults do not define the MT4 bridge protocol.

| Measure | Current result |
|---|---:|
| Canonical roots | 34/34 |
| Structurally valid v2 candidates | 34/34 |
| Active v2 roots | 0/34 |
| Specification-ready candidates | 0/34 |
| Implementation-verified modules | 0/34 |
| Inventoried active source versions | 2174 |
| Source scope true / undecided / false | 965 / 570 / 639 |
| Sources fully scraped | 0/2174 |
| Sources archive eligible / actually retired | 0 / 0 |
| Claim records | 13818 |
| Mandatory unresolved review/blocker records | 192 |
| Nonblocking unresolved records | 1384 |
| Partial batch packages | 11 |
| Candidate preview projections | 70 |
| Focused tests | 42 passed |
| Offline structural/guard fixtures | 22/22 passed |
| Repository tests | 126 passed, 7 skipped, 0 failures/errors |
| Required repository coverage | 0% against unchanged 85% gate — FAILED |

Candidate structural checks pass. Full candidate and active acceptance remain
BLOCKED. Repeated validation reports match exactly. Candidate previews regenerate
deterministically; active projection generation exits nonzero before changing
active authority bytes. The full suite appended seven audit records; those test
records are preserved separately in `run/current_test_audit_append.jsonl` and the
baseline audit file was restored byte-for-byte. No runtime implementation was
modified by this continuation. Windows/MQL4/MT4 validation remains unavailable;
no live trading ran and no implementation verification is claimed.

## Exact unfinished work

1. Identify the approved current execution-only EA/interface and current B1/B2
   payloads, acknowledgement/rejection, compatibility and timeout/retry/recovery
   semantics. See `run/critical_blockers.json`; no new evidence resolving those
   definitions was introduced by the uploaded ZIP.
2. Complete pilot and W1–W8 claim-level review, root/bundle unique-claim
   adjudication, file-usage/ownership and applicability decisions. The mandatory
   queue includes review work, not only proven evidence absences.
3. Pass required coverage and P5 specification acceptance without lowering
   thresholds or converting unknown to not_applicable.
4. Only then execute the all-34 coordinated authority/routing/shared-registry
   cutover, derived projection regeneration and eligible source archival with
   byte-preserving receipts and restoration proof.

DEC-036 authorizes publishing this work as a **draft review PR**, not merging or
claiming final consolidation. The terminal Git push still lacks credentials;
connected GitHub tools have successfully created the review branch. Publication
must reproduce the local reviewed tree. `run/final_verification.json` contains
machine-readable denominators and repeatability checks. Earlier execution reports
remain historical records of their own baseline; this report is current.

## Publication and hosted CI follow-up — 2026-10-05 UTC

Draft [PR #274](https://github.com/DICKY1987/eafix-modular/pull/274) is published,
not merged. Git fetch verified the initial remote tree exactly matches the tested
local snapshot. GitHub's structural/guard job and registry-shadow job pass; the
active-authority acceptance job correctly fails while cutover remains incomplete.
The PR title was corrected to Conventional Commits format; a passing rerun is
not assumed. The six new reviewed-code-source tests are now included in CI.

Hosted document-ID validation also fails: 414/2,516 tracked files have prefixed
filenames (16.454690%), below the unchanged 18.206497% allowed floor. DEC-037
records this as BLOCK-DOCUMENT-ID-COVERAGE. There are now 193 unresolved mandatory
review/blocker records and five critical validation/evidence holds. No baseline,
threshold or immutable original was altered to hide this failure. Reconcile the
mandated artifact paths with the approved naming/applicability policy and rerun
coverage/uniqueness checks before acceptance. Earlier counts above describe the
initial reviewed snapshot; publication_verification.json records this follow-up.
