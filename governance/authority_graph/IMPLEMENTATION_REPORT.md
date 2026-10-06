# EAFIX authority graph implementation

Baseline: `f37f8ca8bd966031fb243a9cd9401b065c29135a` on `master`.
Working branch: `ai/module-authority-graph-20261006`.

## Request and implemented scope

The final substantive response in the supplied shared chat recommends a small
authority graph connecting module identity, process behavior, shared contracts,
file ownership, work cells, and derived AI context. It contains an architectural
recommendation, not a numbered execution plan or authorization to approve
unresolved trading interfaces. This change implements the graph and its validation
against the current active repository sources.

The 34 module registry records now point to verified manifests and physical
module roots. Their candidate authority status is preserved. A deterministic
builder produces one graph, 34 module navigation packets, 34 boundary diagrams,
an index, and a validation report. Each artifact is a derived projection. This
adds no competing authored module or file registry.

Process steps use the canonical process registry. Boundary validation checks
the input and output contracts against the owning module's manifest. Files have
one manifest owner. File-to-step links are generated only for declared entrypoints
whose exclusive ownership is established. Reverse links are checked. Shared
contract producers, consumers, and stewards are represented separately.

Work-cell records are grouped by identity and explicit module relationship;
service-directory membership alone does not establish ownership. Overbroad
source/test lists remain evidence, and only corroborated owned files appear as
verified references. This index does not assert that the work-cell behavior has
been extracted or implemented.

The attached 86-file decisions and action manifest are preserved as pinned input
evidence. Every action has a current filesystem observation. Target existence
does not certify semantic migration, reference repair, tests, or scrape completion.
All 17 attachments were read locally; their byte hashes and extraction sizes are
recorded in `source_inventory.json`.

## Decisions made

1. Reuse the existing registries and manifests. Do not introduce another authored
   mapping database or a new permanent identity scheme.
2. Reconcile missing module locators, roots and manifest paths from actual files.
   Keep logical locators in the existing schema's uppercase `M0001` format while
   physical folders remain lowercase `m0001-*`.
3. Preserve candidate/evidence authority states. Navigation generation cannot
   promote a contract, approve an unresolved schema, or perform a module cutover.
4. Omit shared or foreign service entrypoints from verified step links; record
   each omitted link and each missing verified executor explicitly.
5. Generate navigation under `EAFIX_auth_docs/generated/authority_graph/`. The
   older active context packets are not overwritten while the separate module
   authority consolidation remains on scoped holds.
6. Keep `contracts/` physically shared. The attached decisions establish R2 as
   OrderIntent steward and S1 as Signal steward; other stewardship is unspecified
   until evidence establishes it.
7. Preserve the previous `ai/module-authority-resume-20261004` branch and its
   holds. Its recorded B1/B2 interface, document-ID, extraction, coverage and
   runtime blockers are not waived or superseded by this graph implementation.
8. Use a blocking CI job for graph integrity and byte-for-byte regeneration.
   Keep broader authority promotion separate from successful navigation checks.

## Validation and remaining work

The registry and graph validation commands pass. The 27 registry unit tests
include 12 new graph tests for ownership collisions, foreign executors,
schema-to-step misuse, contract drift, bidirectional links, path traversal,
tampered outputs, unexpected outputs and deterministic regeneration.

See `EAFIX_auth_docs/generated/authority_graph/validation_report.json` for
current counts and `authority_graph.current.json` for every finding. Navigation
validation is not production readiness. At this baseline the graph exposes:

- 21 process steps without a verified exclusively owned entrypoint.
- 13 entrypoint claims excluded because exclusive ownership is not established.
- 22 contracts requiring review.
- 15 artifact ownership claims not corroborated by current manifests.

The full 34-module authority cutover and repository migration remain incomplete.
Resolve the listed claims using code/import/runtime evidence, finish the existing
consolidation branch's gates, then regenerate from the promoted authority. Do
not fill missing execution claims by guessing from filenames or service folders.

The broader repository suite was run against both the unchanged baseline and
this branch. Baseline: 102 passed, 3 failed, 7 skipped (112 tests). Current:
114 passed, 3 failed, 7 skipped (124 tests). The same three legacy generator/
validator tests fail in both runs. Both runs also fail the existing 85% runtime
coverage gate with 0% reported coverage. No runtime release or successful full
suite is claimed. Windows and MT4/MQL4 runtime verification were unavailable.

The new graph builder separately reaches 91% coverage with all 12 tests passing.
The blocking navigation CI does not certify the broader runtime coverage gate.

## Use and rollback

Start at `EAFIX_auth_docs/generated/authority_graph/README.md`. Select a module's
JSON packet to inspect its manifest, steps, owned files, contracts and work cells.
The boundary view shows trigger, input, module, validation decision, output,
failure controls and declared consumers. Non-process modules explicitly show
that trigger and failure policies remain unspecified.

Regenerate with `python tools/registries/build_authority_graph.py` and verify with
`python tools/registries/build_authority_graph.py --check`. The check is read-only
and returns a nonzero exit status when generated bytes drift.

Rollback consists of reverting this branch's commit. It performs no runtime code
moves, archive operations, deletions, trading actions or authority promotion.
