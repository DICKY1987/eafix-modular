# doc_id_subsystem

Utilities and CI gates for the EAFIX doc-ID naming convention.

## Naming Convention

Files in this repository may carry a numeric doc-ID prefix:

| File type     | Prefix format                           | Example                              |
|---------------|-----------------------------------------|--------------------------------------|
| Default files | `<20-digit-id>_<original-name>`         | `0099900002260118_.coverage`         |
| Python files  | `P_<20-digit-id>_<original-name>`       | `P_2099900005260118_eafix_cli.py`    |

IDs are allocated from `COUNTER_STORE.json` and must be unique across the repository.

## Structure

```
doc_id_subsystem/
├── core/
│   └── doc_id_scanner.py       # Repo walker — finds prefixed files, measures coverage, surfaces duplicate IDs
└── validation/
    ├── validate_doc_id_coverage.py    # CI gate: coverage must not regress below threshold
    └── validate_doc_id_uniqueness.py  # CI gate: no new duplicate IDs may be introduced
```

## CI Usage

The `.github/workflows/1299900011260118_doc_id_validation.yml` workflow runs:

```bash
cd doc_id_subsystem/validation
python validate_doc_id_coverage.py --baseline 0.95
python validate_doc_id_uniqueness.py
```

### First run behaviour

Both scripts operate in **bootstrap mode** on first execution (no saved snapshot files):

- **`validate_doc_id_coverage.py`** records the current doc-ID coverage ratio as the baseline and exits 0.
- **`validate_doc_id_uniqueness.py`** snapshots the currently known duplicate IDs as *pre-existing* and exits 0.

### Subsequent run behaviour

- **Coverage gate**: fails if `current_coverage < baseline_coverage × threshold` (default threshold = 0.95).
- **Uniqueness gate**: fails if any NEW duplicate IDs are introduced beyond the known pre-existing set.

### Runtime-generated files (excluded from git)

| File                                                     | Purpose                                    |
|----------------------------------------------------------|--------------------------------------------|
| `doc_id_subsystem/validation/doc_id_coverage_baseline.json` | Saved coverage baseline from first run  |
| `doc_id_subsystem/validation/known_duplicates.json`         | Snapshot of pre-existing duplicate IDs  |

These files are listed in `.gitignore` and must not be committed.
