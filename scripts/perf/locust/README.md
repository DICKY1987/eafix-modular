---
doc_id: DOC-DOC-0018
---

# Locust Performance Tests

Quick-start to run Locust for HTTP load.

## Prerequisites
- Python 3.11, `pip install locust`

## Run
```
locust -f locustfile.py --headless -u 20 -r 5 -t 1m --host http://localhost:8080
```

## CI Outputs
- Use `--csv results` for CSV artifacts.

