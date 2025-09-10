"""
hybrid_id.py — Compose, parse, and validate the Reentry Hybrid Identifier.

Format: SIG~TB~OB~PB~G
  SIG: signal_id  (A-Z0-9_)
  TB:  time_bucket (duration token)
  OB:  outcome_bucket
  PB:  proximity_bucket
  G:   generation (1..N)

Also provides a short base32 hash to fit MT4 comment length constraints.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
import base64, hashlib, re

from .vocab import load_vocab, Vocab

RE_SIG = re.compile(r"^[A-Z0-9_]{3,64}$")

@dataclass(frozen=True)
class HybridKey:
    signal_id: str
    time_bucket: str
    outcome_bucket: str
    proximity_bucket: str
    generation: int

    def compose(self) -> str:
        return compose(self.signal_id, self.time_bucket, self.outcome_bucket, self.proximity_bucket, self.generation)

def compose(signal_id: str, time_bucket: str, outcome_bucket: str, proximity_bucket: str, generation: int) -> str:
    return f"{signal_id}~{time_bucket}~{outcome_bucket}~{proximity_bucket}~{generation}"

def parse(key: str) -> HybridKey:
    parts = key.strip().split("~")
    if len(parts) != 5:
        raise ValueError(f"Invalid reentry key: expected 5 parts, got {len(parts)}")
    sig, tb, ob, pb, g = parts
    try:
        gi = int(g)
    except ValueError:
        raise ValueError("Generation must be an integer")
    return HybridKey(sig, tb, ob, pb, gi)

def short_hash(s: str, length: int = 6) -> str:
    """
    Base32 of SHA1 digest, strip '=', first `length` chars. Regex: ^[A-Z2-7]{4,10}$
    """
    digest = hashlib.sha1(s.encode("utf-8")).digest()
    b32 = base64.b32encode(digest).decode("ascii").rstrip("=")
    return b32[:length]

def comment(prefix: str, key: str, suffix_len: int = 6) -> str:
    """
    Compose an EA-friendly comment: f"{prefix}_{short_hash(key, suffix_len)}"
    """
    return f"{prefix}_{short_hash(key, suffix_len)}"

def validate_components(signal_id: str, time_bucket: str, outcome_bucket: str, proximity_bucket: str, generation: int, vocab: Optional[Vocab]=None) -> List[str]:
    if vocab is None:
        vocab = load_vocab()
    errs: List[str] = []
    if not RE_SIG.match(signal_id):
        errs.append("signal_id must be A-Z, 0-9, or underscore, 3..64 chars")
    if time_bucket not in vocab.duration:
        errs.append(f"time_bucket '{time_bucket}' not in duration vocab {sorted(vocab.duration)}")
    if outcome_bucket not in vocab.outcome:
        errs.append(f"outcome_bucket '{outcome_bucket}' not in outcome vocab {sorted(vocab.outcome)}")
    if proximity_bucket not in vocab.proximity:
        errs.append(f"proximity_bucket '{proximity_bucket}' not in proximity vocab {sorted(vocab.proximity)}")
    if not (vocab.generation_min <= int(generation) <= vocab.generation_max):
        errs.append(f"generation must be in [{vocab.generation_min}, {vocab.generation_max}]")
    return errs

def validate_key(key: str, vocab: Optional[Vocab]=None) -> List[str]:
    try:
        hk = parse(key)
    except Exception as e:
        return [str(e)]
    return validate_components(hk.signal_id, hk.time_bucket, hk.outcome_bucket, hk.proximity_bucket, hk.generation, vocab)
