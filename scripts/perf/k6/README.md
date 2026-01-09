---
doc_id: DOC-DOC-0017
---

# k6 Performance Tests

Quick-start to run baseline and stress tests with k6.

## Prerequisites
- k6 installed locally (https://k6.io/)

## Run
```
k6 run script.js -e TARGET_URL=http://localhost:8080/healthz -e VUS=10 -e DURATION=30s
```

## CI Outputs
- Configure `--out json=results.json` or `--summary-export summary.json` for artifacts.

