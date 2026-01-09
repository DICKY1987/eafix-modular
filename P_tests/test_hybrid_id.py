# DOC_ID: DOC-TEST-0005
\
import os, sys, re
sys.path.insert(0, os.path.abspath("."))

from reentry_helpers.hybrid_id import compose, parse, validate_key, short_hash
from reentry_helpers.vocab import load_vocab

def test_compose_parse_roundtrip():
    key = compose("NFP_BREAKOUT","FLASH","W1","AT_EVENT",1)
    hk = parse(key)
    assert hk.signal_id == "NFP_BREAKOUT"
    assert hk.time_bucket == "FLASH"
    assert hk.outcome_bucket == "W1"
    assert hk.proximity_bucket == "AT_EVENT"
    assert hk.generation == 1

def test_validate_ok_defaults():
    vocab = load_vocab()  # defaults or reentry_vocab.json if present
    key = compose("CPI_REVERSAL","QUICK","BE","POST_30M",2)
    errs = validate_key(key, vocab)
    assert errs == []

def test_validate_rejects_bad_tokens():
    vocab = load_vocab()
    key = compose("BAD$SIG","FASTER","W9","AT_EVENT",9)
    errs = validate_key(key, vocab)
    assert errs
    assert any("signal_id" in e for e in errs)
    assert any("time_bucket" in e for e in errs)
    assert any("outcome_bucket" in e for e in errs)
    assert any("generation" in e for e in errs)

def test_short_hash_format():
    key = compose("NFP_BREAKOUT","FLASH","W1","AT_EVENT",1)
    h = short_hash(key, length=6)
    assert re.match(r"^[A-Z2-7]{6}$", h)
