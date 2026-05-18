"""Stable import wrapper for hybrid ID helpers."""

import re

from ._id_loader import load_id_module
from .vocab import ReentryVocabulary

_MODULE = load_id_module("2099900218260118_hybrid_id.py", "hybrid_id")


class HybridIdHelper(_MODULE.HybridIdHelper):
    """Stable helper that parses underscore-bearing proximity and calendar IDs."""

    def __init__(self, vocabulary=None):
        self.vocab = vocabulary or ReentryVocabulary()

    def compose(
        self,
        outcome: str,
        duration: str,
        proximity: str,
        calendar: str = None,
        direction: str = None,
        generation: int = None,
        suffix: str = None,
        calendar_id: str = None,
    ) -> str:
        calendar_value = calendar if calendar is not None else calendar_id
        return super().compose(
            outcome,
            duration,
            proximity,
            calendar_value,
            direction,
            generation,
            suffix,
        )

    def parse(self, hybrid_id: str) -> dict:
        if not isinstance(hybrid_id, str) or not hybrid_id:
            raise ValueError("Hybrid ID must be a non-empty string")

        parts = hybrid_id.split("_")
        if len(parts) < 6:
            raise ValueError(f"Hybrid ID must have at least 6 components, got {len(parts)}: {hybrid_id}")

        outcome = parts[0]
        duration = parts[1]
        proximity, proximity_end = self._parse_proximity(parts)

        suffix = None
        generation_idx = len(parts) - 1
        if (
            len(parts) > proximity_end + 3
            and re.match(r"^[a-z0-9]{6}$", parts[-1])
            and parts[-2].isdigit()
        ):
            suffix = parts[-1]
            generation_idx = len(parts) - 2

        if not parts[generation_idx].isdigit():
            raise ValueError(f"No valid generation found in hybrid ID: {hybrid_id}")

        direction_idx = generation_idx - 1
        if direction_idx < proximity_end:
            raise ValueError(f"Missing direction component in hybrid ID: {hybrid_id}")

        direction = parts[direction_idx]
        calendar_parts = parts[proximity_end:direction_idx]
        calendar = "_".join(calendar_parts) if calendar_parts else "NONE"
        generation = int(parts[generation_idx])

        valid, errors = self.vocab.is_valid_hybrid_context(
            outcome,
            duration,
            proximity,
            calendar,
            direction,
            generation,
        )
        if not valid:
            raise ValueError(f"Invalid hybrid ID components: {'; '.join(errors)}")

        result = {
            "outcome": outcome,
            "duration": duration,
            "proximity": proximity,
            "calendar": calendar,
            "calendar_id": calendar,
            "direction": direction,
            "generation": str(generation),
        }
        if suffix:
            result["suffix"] = suffix
        return result

    def validate_key(self, hybrid_id: str) -> bool:
        try:
            self.parse(hybrid_id)
            return True
        except Exception:
            return False

    def _parse_proximity(self, parts: list[str]) -> tuple[str, int]:
        proximity_tokens = sorted(
            self.vocab.get_proximity_tokens(),
            key=lambda token: len(token.split("_")),
            reverse=True,
        )
        for token in proximity_tokens:
            token_parts = token.split("_")
            token_end = 2 + len(token_parts)
            if "_".join(parts[2:token_end]) == token:
                return token, token_end
        raise ValueError(f"Invalid proximity token in hybrid ID: {'_'.join(parts)}")


_HELPER = HybridIdHelper()


def compose(
    outcome: str,
    duration: str,
    proximity: str,
    calendar: str = None,
    direction: str = None,
    generation: int = None,
    suffix: str = None,
    calendar_id: str = None,
) -> str:
    """Compose a hybrid ID, accepting either calendar or calendar_id."""
    calendar_value = calendar if calendar is not None else calendar_id
    return _HELPER.compose(
        outcome,
        duration,
        proximity,
        calendar_value,
        direction,
        generation,
        suffix,
    )


def parse(hybrid_id: str) -> dict:
    """Parse a hybrid ID into stable component names."""
    return _HELPER.parse(hybrid_id)


def validate_key(hybrid_id: str) -> bool:
    """Validate a hybrid ID against current vocabulary."""
    return _HELPER.validate_key(hybrid_id)


def comment_suffix_hash(hybrid_id: str) -> str:
    """Generate the deterministic legacy comment suffix hash."""
    return _HELPER.comment_suffix_hash(hybrid_id)

__all__ = [
    "HybridIdHelper",
    "compose",
    "parse",
    "validate_key",
    "comment_suffix_hash",
]
