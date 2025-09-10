\
#!/usr/bin/env python3
"""
Scan CSV files for cells that look like reentry keys and validate them.
Exit 1 if any invalid keys are found.
"""
import sys, os, re, csv, glob
from reentry_helpers.hybrid_id import validate_key
from reentry_helpers.vocab import load_vocab

PATTERN = re.compile(r"^[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~[A-Z0-9_]+~\d+$")

def scan(paths):
    vocab = load_vocab()
    ok = True
    for path in paths:
        if os.path.isdir(path):
            for fp in glob.glob(os.path.join(path, "**", "*.csv"), recursive=True):
                ok &= scan_file(fp, vocab)
        else:
            ok &= scan_file(path, vocab)
    return ok

def scan_file(fp, vocab):
    ok = True
    try:
        with open(fp, newline="", encoding="utf-8") as f:
            r = csv.reader(f)
            for i, row in enumerate(r, start=1):
                for j, cell in enumerate(row, start=1):
                    if isinstance(cell, str) and "~" in cell and PATTERN.match(cell):
                        errs = validate_key(cell, vocab)
                        if errs:
                            sys.stderr.write(f"{fp}:{i}:{j}: invalid reentry_key '{cell}': {errs}\n")
                            ok = False
    except Exception as e:
        # Non-fatal; just report
        sys.stderr.write(f"{fp}: error reading file: {e}\n")
    return ok

if __name__ == "__main__":
    args = sys.argv[1:] or ["runtime", "registries"]
    ok = scan(args)
    sys.exit(0 if ok else 1)
