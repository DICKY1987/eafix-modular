# DOC_ID: DOC-LEGACY-0013
"""
vocab.py — Canonical tokens for GUI, Matrix, and Hybrid IDs.

Usage:
    from reentry_helpers.vocab import load_vocab, Vocab

    vocab = load_vocab()  # auto-find reentry_vocab.json relative to CWD or use defaults
    print(vocab.duration)  # set of allowed duration tokens

Conventions:
- Duration: FLASH, QUICK, LONG, EXTENDED
- Proximity: PRE_1H, AT_EVENT, POST_30M
- Outcome: W2, W1, BE, L1, L2
- Direction: LONG, SHORT, ANY
- Generation range: 1..3 (inclusive)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Set, Any, Optional, Tuple
import json, os

_DEFAULTS = {
    "duration_buckets": [
        {"token":"FLASH","max_minutes":5,"iso_limit":"PT5M","desc":"Very short; <=5m"},
        {"token":"QUICK","max_minutes":30,"iso_limit":"PT30M","desc":"Short; <=30m"},
        {"token":"LONG","max_minutes":240,"iso_limit":"PT4H","desc":"Sustained; <=4h"},
        {"token":"EXTENDED","max_minutes":None,"iso_limit":None,"desc":">4h"},
    ],
    "proximity_buckets": [
        {"token":"PRE_1H","window_minutes":[-60,0],"desc":"-60 to 0"},
        {"token":"AT_EVENT","window_minutes":[0,5],"desc":"0 to +5m"},
        {"token":"POST_30M","window_minutes":[1,30],"desc":"+1m to +30m"},
    ],
    "outcome_buckets": [
        {"token":"W2","rank":2,"desc":"Strong win"},
        {"token":"W1","rank":1,"desc":"Win"},
        {"token":"BE","rank":0,"desc":"Break-even"},
        {"token":"L1","rank":-1,"desc":"Loss"},
        {"token":"L2","rank":-2,"desc":"Strong loss"},
    ],
    "direction_enum": ["LONG","SHORT","ANY"],
    "generation_range": {"min":1,"max":3},
    "strength_range": {"min":0.0,"max":1.0},
}

@dataclass(frozen=True)
class Vocab:
    duration: Set[str]
    proximity: Set[str]
    outcome: Set[str]
    direction: Set[str]
    generation_min: int
    generation_max: int
    raw: Dict[str, Any]

def _from_dict(d: Dict[str, Any]) -> Vocab:
    dur = {x["token"] for x in d["duration_buckets"]}
    prox = {x["token"] for x in d["proximity_buckets"]}
    outc = {x["token"] for x in d["outcome_buckets"]}
    dire = set(d["direction_enum"])
    gen_min = int(d["generation_range"]["min"])
    gen_max = int(d["generation_range"]["max"])
    return Vocab(dur, prox, outc, dire, gen_min, gen_max, d)

def _find_vocab_file(start_dir: str) -> Optional[str]:
    candidates = [
        os.path.join(start_dir, "reentry_vocab.json"),
        os.path.join(start_dir, "config", "reentry_vocab.json"),
        os.path.join(os.getcwd(), "reentry_vocab.json"),
        os.path.join(os.getcwd(), "config", "reentry_vocab.json"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None

def load_vocab(path: Optional[str]=None) -> Vocab:
    """
    Load vocab from JSON file; if not found, fallback to defaults.
    """
    if path is None:
        path = _find_vocab_file(os.getcwd())
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _from_dict(data)
    return _from_dict(_DEFAULTS)

