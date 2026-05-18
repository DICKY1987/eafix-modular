"""G-01 Gate Validator: Validate physical_inventory_baseline.csv.

Checks:
- All required columns exist
- object_type is 'file' or 'directory'
- exists_on_disk is boolean (True/False)
- is_excluded is boolean (True/False)
- No empty relative_path values
- Prints summary stats

Exit 0 on pass, 1 on fail.
"""

import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "object_type",
    "relative_path",
    "name",
    "parent_relative_path",
    "extension",
    "exists_on_disk",
    "is_excluded",
    "object_scope_class",
    "candidate_semantic_role",
    "path_normalized",
    "is_semantic_candidate",
    "inferred_module_hint",
]

VALID_OBJECT_TYPES = {"file", "directory"}
VALID_BOOLEANS = {"True", "False"}


def validate(csv_path: str) -> bool:
    path = Path(csv_path)
    if not path.exists():
        print(f"FAIL: File not found: {csv_path}")
        return False

    errors = []
    total = 0
    files = 0
    dirs = 0
    excluded = 0

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        # Check columns
        if reader.fieldnames is None:
            print("FAIL: CSV has no header row")
            return False

        missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
        if missing:
            errors.append(f"Missing columns: {sorted(missing)}")

        for i, row in enumerate(reader, start=2):  # line 2 = first data row
            total += 1

            # object_type
            ot = row.get("object_type", "")
            if ot not in VALID_OBJECT_TYPES:
                errors.append(f"Row {i}: invalid object_type '{ot}'")
            elif ot == "file":
                files += 1
            else:
                dirs += 1

            # exists_on_disk
            eod = row.get("exists_on_disk", "")
            if eod not in VALID_BOOLEANS:
                errors.append(f"Row {i}: invalid exists_on_disk '{eod}'")

            # is_excluded
            ie = row.get("is_excluded", "")
            if ie not in VALID_BOOLEANS:
                errors.append(f"Row {i}: invalid is_excluded '{ie}'")

            # relative_path not empty
            rp = row.get("relative_path", "")
            if not rp.strip():
                errors.append(f"Row {i}: empty relative_path")

            # is_excluded counting
            if ie == "True":
                excluded += 1

            # Cap error output
            if len(errors) > 50:
                errors.append("... (truncated, too many errors)")
                break

    # Report
    print("=" * 60)
    print("G-01 Gate: Baseline CSV Validation")
    print("=" * 60)
    print(f"File:        {csv_path}")
    print(f"Total rows:  {total}")
    print(f"Directories: {dirs}")
    print(f"Files:       {files}")
    print(f"Excluded:    {excluded}")
    print(f"Errors:      {len(errors)}")
    print("=" * 60)

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  - {e}")
        print("\nRESULT: FAIL")
        return False
    else:
        print("\nRESULT: PASS")
        return True


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path_to_baseline_csv>", file=sys.stderr)
        sys.exit(1)

    passed = validate(sys.argv[1])
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
