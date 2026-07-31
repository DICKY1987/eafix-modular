# Document-ID validation

This subsystem enforces the repository's filename document-ID convention.
It recognizes a 16-20 digit prefix, optionally preceded by `P_`, and scans
only paths tracked by Git so caches and local environments cannot change CI
results.

Run the same commands used by CI from the repository root:

```bash
python doc_id_subsystem/validation/validate_doc_id_coverage.py --baseline 0.95
python doc_id_subsystem/validation/validate_doc_id_uniqueness.py
```

The committed coverage and duplicate snapshots represent accepted legacy
state. Coverage may not fall below 95% of the recorded ratio, and a duplicate
ID fails validation if it is new or gains another tracked path. Updating either
snapshot requires a reviewed commit; validators never rewrite their baselines.
