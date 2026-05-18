"""Stable import wrapper for reentry vocabulary."""

from pathlib import Path

from ._id_loader import load_id_module

_MODULE = load_id_module("2099900221260118_vocab.py", "vocab")


class ReentryVocabulary(_MODULE.ReentryVocabulary):
    """Stable wrapper that points the legacy loader at the ID-prefixed vocab."""

    def __init__(self, vocab_file=None):
        if vocab_file is None:
            vocab_file = Path(__file__).with_name("1199900031260118_reentry_vocab.json")
        super().__init__(vocab_file)

__all__ = ["ReentryVocabulary"]
