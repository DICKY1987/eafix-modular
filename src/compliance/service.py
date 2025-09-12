from __future__ import annotations

import json
from pathlib import Path


def evaluate_rules(rules_path: str = "policy/compliance_rules.json") -> bool:
    p = Path(rules_path)
    if not p.exists():
        return False
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return isinstance(data.get("rules", []), list)
    except Exception:
        return False


if __name__ == "__main__":  # manual check
    ok = evaluate_rules()
    print({"ok": ok})
