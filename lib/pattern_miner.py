from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple


def mine_sequences(jsonl_path: Path, top_n: int = 5) -> List[Tuple[Tuple[str, ...], int]]:
    """Mine simple sequences of actions from a JSONL audit log.

    This is a minimal placeholder that expects lines with a field 'action'.
    """
    sequences: List[Tuple[str, ...]] = []
    if not jsonl_path.exists():
        return []
    window: List[str] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            action = str(obj.get("action", "")).strip()
            if not action:
                continue
            window.append(action)
            if len(window) >= 3:
                sequences.append(tuple(window[-3:]))
    counter = Counter(sequences)
    return counter.most_common(top_n)

