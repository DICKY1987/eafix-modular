# doc_id_subsystem

Document-ID governance tooling for the EAFIX repository.

## Overview

EAFIX files that participate in the document-governance system carry a
16-digit numeric prefix in their filename, for example:

```
1299900011260118_doc_id_validation.yml
```

The format is `<NNNNNNNNNNNNNNNN>_<original-name>` where `N` is a decimal
digit.  These prefixes (called *doc IDs*) uniquely identify a file across the
repository's history.

## Scripts

### `core/doc_id_scanner.py`

Scans the repository and produces a summary of which files carry doc-ID
prefixes, listing any duplicate IDs.

```
python doc_id_scanner.py --repo-root ../..
```

### `validation/validate_doc_id_coverage.py`

Validates that the ratio of doc-ID-prefixed files to total files has not
regressed below an acceptable floor since the last recorded baseline.

```
python validate_doc_id_coverage.py --baseline 0.95
```

On the **first run** (no `doc_id_coverage_baseline.json` present) the script
records the current coverage as the baseline and exits 0.  Subsequent runs
require `current_coverage >= saved_baseline * 0.95`.

### `validation/validate_doc_id_uniqueness.py`

Validates that no **new** duplicate doc IDs have been introduced since the
last snapshot.

```
python validate_doc_id_uniqueness.py
```

On the **first run** (no `known_duplicates.json` present) the script records
any currently-detected duplicates as *known* and exits 0.  Subsequent runs
fail only if **new** (previously unknown) duplicates are found.

## CI

The workflow `.github/workflows/1299900011260118_doc_id_validation.yml` runs
these scripts automatically on every push and pull request targeting `master`
or `develop`.

## Generated files (not committed)

| File | Purpose |
|---|---|
| `validation/doc_id_coverage_baseline.json` | Saved coverage snapshot (CI runtime) |
| `validation/known_duplicates.json` | Saved duplicate snapshot (CI runtime) |

Both files are listed in `.gitignore` and are created on the first CI run.
