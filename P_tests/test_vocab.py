\
import os, sys
sys.path.insert(0, os.path.abspath("."))

from reentry_helpers.vocab import load_vocab

def test_vocab_defaults():
    v = load_vocab()
    assert "FLASH" in v.duration
    assert "AT_EVENT" in v.proximity
    assert "W1" in v.outcome
    assert v.generation_min == 1 and v.generation_max >= 2
