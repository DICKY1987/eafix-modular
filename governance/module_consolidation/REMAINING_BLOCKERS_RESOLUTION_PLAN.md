# EAFIX 34-module authority consolidation

DEC-031 update: independent execution is **ACTIVE_WITH_SCOPED_HOLDS** under
`SCOPED_SUSPENSION.md`. Final specification/validation acceptance remains
**BLOCKED**. Run `progress_gate.py` to check independent-progress integrity.
This is the
requested execution program, with reviewable artifacts and exact evidence of
the stopping conditions. It is not a declaration of completed consolidation.

The frozen default-branch baseline is
`f37f8ca8bd966031fb243a9cd9401b065c29135a` on `master`. The local work branch is
`ai/module-authority-resume-20261004`. The existing 34 active root
manifests remain v1. No trading implementation or source file location changed.

## Authorities and decisions

After the coordinated cutover, each existing root `manifest.json` owns its
module-specific facts. `process_registry.jsonl` retains global process facts;
shared contracts retain their specialized external authorities. The proposed
shared-file registry owns global consumer topology. Bundles, indexes, packets,
diagrams and work tracking are one-way projections. None may write back to a
module root. The v1 schema remains immutable.

The owner's DEC-001 through DEC-026 are recorded in
`resolution_decisions.json`; they are approved policy awaiting cutover.
DEC-027 through DEC-030 apply preservation and fail-closed rules from the same
instructions. They do not approve absent protocol semantics. The field-authority
matrix describes the future cutover state and explicitly labels that state.

## Exact blockers

See `run/critical_blockers.json` for source hashes, JSON pointers and line ranges.

| Blocker | Required evidence or decision | Action |
|---|---|---|
| B1/B2 wire definitions | Approved `BrokerOrderEnvelope` and `AdapterAck` payloads, types, units, version/compatibility and acknowledgement/rejection semantics | Reconcile into the external contract authority, then reference it locally. An absent schema alone is a permitted gap; an undefined mandatory boundary is not waived. |
| B1 retry and timeout | Approved active transport, EA acknowledgement deadline, retry count/backoff, exhaustion and recovery | Resolve the bridge protocol. Python downstream-service timeout/retry defaults do not establish the EA protocol. |
| Current B2 EA authority | Approved execution EA/interface or intended execution-only specification | Do not promote the supplied moving-average strategy replacement. Its header states the original EA was unavailable. |
| Required validation route | Passing required repository coverage/CI and full active-authority acceptance | DEC-032 replaced obsolete callers and test imports. The suite has zero test failures, but measured coverage remains 0% against the unchanged 85% requirement. |

The blocker queue also contains review items seeded from unconfirmed v1 fields.
These are not all proven absent from the supporting corpus. They require source
review, applicability decisions and reconciled local values. A source scan is
not full semantic review.

DEC-033 applied 60 reviewed boundary facts to all 34 candidates with guarded
proposals in `batches/independent-boundary-review/`. It closes 60 candidate
nonblocking gaps, preserves all mandatory holds, and is not full source review.

## Remaining execution

1. Establish the approved bridge/EA evidence listed above. Keep implementation
   conformance separate from intended specification.
2. Complete the four-module pilot, including source-level claim extraction and
   reviewed local behavior, contracts, required files, failure and acceptance
   criteria. Offline guard fixtures already pass; full pilot reconciliation does
   not.
3. Review the remaining source scope and process W1-W8. The eleven partial batch packages
   currently record candidate preservation only and say `completed: false`.
   Resolve all root/bundle unique claims, current paths and historical mappings.
4. Apply guarded semantic patches to candidates. Freeze the old value and source
   hashes for every accepted change. Do not regenerate over approved semantic
   work from supporting sources.
5. Pass P5 over all 34 together. Both source reconciliation and mandatory
   specification gaps must close. Structural PASS alone cannot authorize P6.
6. In one coordinated P6 change, replace all 34 roots, establish the canonical
   shared-file registry, update authority/routing, retire shadow module authority,
   redirect old writers and validators, and generate the bundle and context
   projections from roots. Validate exact projection parity.
7. For P7, independently prove full scraping and retention eligibility. Copy
   original bytes with receipts, verify SHA-256 and restoration, then retire only
   eligible sources. Do not archive a required live authority or tool input.
8. Pass the final acceptance checklist before declaring P8 complete. Publish
   denominators for active roots, candidates, source versions, claims, shared
   records and archived sources separately.

## Reproducible checks

From the repository root, with Python 3.12 and `jsonschema`, `pytest` and
`pytest-cov` installed:

```bash
python governance/module_consolidation/validate_consolidation.py --mode candidate --structural-only
python governance/module_consolidation/validation/fixture_runner.py
python governance/module_consolidation/generate_projections.py --candidate-preview --check
python -m pytest -q -o addopts= tests/governance/test_module_authority.py tests/registries/test_registry_framework.py tests/migration/test_p20_regeneration.py
python governance/module_consolidation/validate_consolidation.py --mode candidate
python governance/module_consolidation/validate_consolidation.py --mode active
python governance/module_consolidation/generate_projections.py --check
```

The last three commands must return nonzero at this blocked state. The active CI
job is deliberately blocking. It must not be made green by certifying staging.
The repository-wide `python -m pytest -q --cov=src` gate also remains failed;
its current raw evidence is in `run/current_repository_suite.log`.

The generator's `--candidate-preview` mode writes 70 review-only projections
under `projection_preview/`. Its active mode first validates authority inputs;
it cannot mutate active projections while this state is blocked.

DEC-034 verified package continuity against fresh master. DEC-035 records eight
static U2/SK2 observations and three open GUI conformance findings. These do not
complete the pilot. DEC-036 authorizes only a review branch/draft PR; final gates
remain in force. Current execution evidence is in `run/final_verification.json`.
