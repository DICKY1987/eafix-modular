---
doc_id: DOC-REG-0002
---
# Generated Process Catalog

> Generated from `process_registry.jsonl`. Do not edit manually.

- `S01` Resolve configuration snapshot — owner `50000000000000000001`
- `S02` Emit schedule tick (calendar polling cadence) — owner `50000000000000000002`
- `S03` Poll calendar source(s) — owner `50000000000000000003`
- `S04` Normalize raw calendar entries — owner `50000000000000000004`
- `S05` Persist calendar events (append-only) — owner `50000000000000000005`
- `S06` Build anticipation triggers from calendar — owner `50000000000000000006`
- `S07` Ingest market ticks — owner `50000000000000000007`
- `S08` Aggregate ticks into bars — owner `50000000000000000008`
- `S09` Compute indicators — owner `50000000000000000009`
- `S10` Assemble strategy feature frame — owner `50000000000000000010`
- `S11` Generate signal (or suppression) — owner `50000000000000000011`
- `S12` Convert signal to trade intent — owner `50000000000000000012`
- `S13` Evaluate risk and size — owner `50000000000000000013`
- `S14` Compile order intent — owner `50000000000000000014`
- `S15` Route order to broker — owner `50000000000000000015`
- `S16` Serialize and send to MT4 adapter — owner `50000000000000000016`
- `S17` EA executes broker order — owner `50000000000000000017`
- `S18` Normalize broker events to canonical reports — owner `50000000000000000018`
- `S19` Apply execution reports to OMS state — owner `50000000000000000019`
- `S20` Classify trade close and compute canonical PnL — owner `50000000000000000020`
- `S21` Bucketize outcome — owner `50000000000000000021`
- `S22` Compute event proximity — owner `50000000000000000022`
- `S23` Lookup matrix decision — owner `50000000000000000023`
- `S24` Build reentry trade intent (or suppress) — owner `50000000000000000024`
- `S25` Loop: reentry intent follows same risk->order->route->transport->execute chain — owner `50000000000000000025`
- `S26` Health aggregation + SLO evaluation — owner `50000000000000000026`
