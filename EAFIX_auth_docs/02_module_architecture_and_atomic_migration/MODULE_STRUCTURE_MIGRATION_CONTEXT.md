# EAFIX 34-Module Structure Migration Context

**Status:** Draft structural scaffold. Existing implementation files have not been relocated.

## Purpose

This branch creates the proposed module-centric directory scaffold for the 34 current atomic modules. It is intended to make the target repository shape concrete and reviewable before source-code relocation.

## Naming rules implemented

- Module root: `<locator>-<canonical-symbol-as-kebab-case>`
- First-level governed container: `<locator>-<role>`
- Hidden state container: `.<locator>-state`
- Nested folders remain conventional and unprefixed.
- Python package names remain snake_case.
- MQL4 runtime folders retain `Experts`, `Indicators`, and `Include`.
- Every module root contains `.module-id` with the full 20-digit module ID.

## Standard module shape

```text
m####-module-symbol/
├── .module-id
├── m####-src/
├── m####-tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── acceptance/
├── m####-docs/
│   ├── architecture/
│   ├── decisions/
│   ├── runbook/
│   └── failure-modes/
├── m####-schemas/
│   ├── inputs/
│   ├── outputs/
│   └── examples/
├── m####-config/
├── m####-scripts/
├── m####-context/
└── .m####-state/
```

## Module roots

1. `m0001-f1-config-preferences`
2. `m0002-f3-clock-scheduler`
3. `m0003-d2-calendar-source-adapter`
4. `m0004-d3-calendar-normalizer`
5. `m0005-f2-event-log`
6. `m0006-d4-calendar-trigger-builder`
7. `m0007-d1-market-feed-adapter`
8. `m0008-c1-bar-builder`
9. `m0009-c2-indicator-engine`
10. `m0010-c3-feature-packager`
11. `m0011-s1-signal-engine`
12. `m0012-s2-intent-builder`
13. `m0013-r1-risk-evaluator`
14. `m0014-r2-order-intent-compiler`
15. `m0015-o1-order-router`
16. `m0016-b1-mt4-adapter-transport`
17. `m0017-b2-mt4-ea-executor`
18. `m0018-b3-exec-event-normalizer`
19. `m0019-o2-oms-state-machine`
20. `m0020-o3-trade-close-classifier`
21. `m0021-e1-outcome-bucketizer`
22. `m0022-e2-proximity-evaluator`
23. `m0023-e3-matrix-lookup`
24. `m0024-e4-reentry-intent-builder`
25. `m0025-f4-flow-orchestrator`
26. `m0026-p1-health-aggregator`
27. `m0027-r3-correlation-guard`
28. `m0028-u1-dashboard-backend`
29. `m0029-u2-gui-gateway`
30. `m0030-u3-mt4-expiry-overlay`
31. `m0031-u4-desktop-operator`
32. `m0032-p2-reporter`
33. `m0033-sk1-plugin-interface`
34. `m0034-sk2-idempotency`

## Profile-specific additions

- `M0016`: Python plus MQL4 `Experts`, `Indicators`, and `Include` source areas.
- `M0017` and `M0030`: MQL4 `Experts`, `Indicators`, and `Include` source areas.
- `M0028` and `M0029`: REST and WebSocket schema areas.
- `M0031`: backend and frontend source areas.
- `M0032`: report templates container.
- `M0033`: plugin examples container.

## Deliberately not performed in this PR

Existing implementation files are not moved because the current file-to-module mapping contains many-to-many ownership records. For example, calendar-ingestor files map simultaneously to D2, D3, F2, and D4; transport-router files map simultaneously to R2, O1, and B1. Moving those files without an accepted ownership decomposition would create arbitrary duplication or assign shared runtime code to the wrong module.

The current vNext catalog also declares 34 modules while its `modules` array is empty. The scaffold uses the 34 approved manifest identities, but the catalog authority must be repaired before this layout can become canonical.

## Required follow-on gate before file relocation

1. Repair or replace the populated 34-module catalog authority.
2. Ratify `M0001` through `M0034` as explicit display locators or approve their derivation rule.
3. Approve a per-module container inventory.
4. Resolve every many-to-many file ownership record.
5. Generate a complete old-path-to-new-path rename map.
6. Scan Python imports, packaging, tests, CI, Docker, PowerShell, documentation, MT4 includes, and deployment paths.
7. Migrate representative Python, UI, bridge, and MT4 pilot modules.
8. Move remaining files only after pilot validation.
