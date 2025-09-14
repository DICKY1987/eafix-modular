from __future__ import annotations

import json
import os
import sys


def main() -> int:
    spec = os.environ.get("GDW_SPEC")
    inputs = json.loads(os.environ.get("GDW_INPUTS", "{}"))
    dry = os.environ.get("GDW_DRY_RUN", "1") == "1"
    print(f"[GDW-Python] version.bump.semver dry={dry} spec={spec} file={inputs.get('file','VERSION')} part={inputs.get('part','patch')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

