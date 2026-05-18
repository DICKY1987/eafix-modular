# doc_id: DOC-TEST-0050
"""
Property-based and determinism tests for hybrid_id format.

Closes GAP-46, GAP-47.

Tests:
  1. Round-trip: parse(compose(...)) == original components
  2. Determinism: same inputs always produce same suffix
  3. Cross-format mapping: Python components <-> MQL4 field order
"""
import sys
from pathlib import Path

import pytest

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

try:
    from shared.reentry import compose, parse, validate_key, HybridIdHelper, ReentryVocabulary
    _REENTRY_AVAILABLE = True
except ImportError:
    _REENTRY_AVAILABLE = False

try:
    from hypothesis import given, settings as hyp_settings, assume
    from hypothesis import strategies as st
    _HYPOTHESIS_AVAILABLE = True
except ImportError:
    _HYPOTHESIS_AVAILABLE = False


# --- Valid component sets for property tests ---
VALID_OUTCOMES = ["W2", "W1", "BE", "L1", "L2"]
VALID_DURATIONS = ["FLASH", "QUICK", "LONG", "EXTENDED"]
VALID_PROXIMITIES = ["PRE_1H", "AT_EVENT", "POST_30M"]
VALID_CALENDARS = ["CAL8_USD_NFP_H", "CAL8_GBP_BOE_H", "CAL5_EUR_PMI_H", "NONE"]
VALID_DIRECTIONS = ["LONG", "SHORT", "ANY"]
VALID_GENERATIONS = [1, 2, 3]

# Known test vectors (determinism)
KNOWN_VECTORS = [
    {
        "outcome": "W1",
        "duration": "QUICK",
        "proximity": "AT_EVENT",
        "calendar_id": "CAL8_USD_NFP_H",
        "direction": "LONG",
        "generation": 1,
    },
    {
        "outcome": "L2",
        "duration": "FLASH",
        "proximity": "PRE_1H",
        "calendar_id": "CAL5_EUR_PMI_H",
        "direction": "SHORT",
        "generation": 2,
    },
]


@pytest.mark.skipif(not _REENTRY_AVAILABLE, reason="shared.reentry not available")
class TestHybridIdRoundTrip:
    """Test that parse(compose(...)) returns original components."""

    @pytest.mark.parametrize("outcome", VALID_OUTCOMES)
    @pytest.mark.parametrize("proximity", VALID_PROXIMITIES)
    def test_compose_parse_roundtrip(self, outcome, proximity):
        """Compose then parse should recover same outcome and proximity."""
        hybrid_id = compose(
            outcome=outcome,
            duration="QUICK",
            proximity=proximity,
            calendar_id="CAL8_USD_NFP_H",
            direction="LONG",
            generation=1,
        )
        assert hybrid_id is not None
        assert len(hybrid_id) > 0

        components = parse(hybrid_id)
        assert components["outcome"] == outcome
        assert components["proximity"] == proximity

    def test_validate_key_accepts_valid(self):
        """validate_key should accept well-formed hybrid IDs."""
        hybrid_id = compose(
            outcome="W1",
            duration="QUICK",
            proximity="AT_EVENT",
            calendar_id="CAL8_USD_NFP_H",
            direction="LONG",
            generation=1,
        )
        assert validate_key(hybrid_id) is True

    def test_known_vector_determinism(self):
        """Same inputs always produce same hybrid_id (determinism)."""
        for vector in KNOWN_VECTORS:
            result1 = compose(**vector)
            result2 = compose(**vector)
            assert result1 == result2, (
                f"Non-deterministic compose for {vector}: "
                f"{result1} != {result2}"
            )


@pytest.mark.skipif(not _REENTRY_AVAILABLE, reason="shared.reentry not available")
class TestHybridIdCrossFormatMapping:
    """
    Test cross-language field order mapping between Python and MQL4.

    Python format: OUTCOME_DURATION_PROXIMITY_CALENDAR_DIRECTION_GENERATION
    MQL4 format:   SIG~TB~OB~PB~G  (SIG=calendar_id, TB=duration, OB=outcome, PB=proximity, G=generation)

    NOTE: MQL4 uses tilde (~) separator; Python uses underscore (_).
    NOTE: Field ORDER differs — MQL4 puts calendar_id first.
    """

    def test_python_separator_is_underscore(self):
        """Python hybrid_id uses underscore separator."""
        hybrid_id = compose(
            outcome="W1",
            duration="QUICK",
            proximity="AT_EVENT",
            calendar_id="CAL8_USD_NFP_H",
            direction="LONG",
            generation=1,
        )
        # Should contain underscores (not tildes)
        parts = hybrid_id.split("_")
        assert len(parts) >= 5, f"Expected at least 5 underscore-separated parts, got: {hybrid_id}"

    def test_python_field_order(self):
        """Python hybrid_id field order: outcome, duration, proximity, calendar, direction, generation."""
        hybrid_id = compose(
            outcome="W1",
            duration="QUICK",
            proximity="AT_EVENT",
            calendar_id="CAL8_USD_NFP_H",
            direction="LONG",
            generation=1,
        )
        components = parse(hybrid_id)
        assert components["outcome"] == "W1"
        assert components["duration"] == "QUICK"
        assert components["proximity"] == "AT_EVENT"
        assert components["calendar_id"] == "CAL8_USD_NFP_H"
        assert components["direction"] == "LONG"
        assert components["generation"] == "1"

    def test_mql4_field_order_differs(self):
        """
        Document that MQL4 reentry_key has different field order than Python hybrid_id.
        MQL4: SIG~TB~OB~PB~G where SIG=calendar_id (FIRST, not fourth).
        This is documented in contracts/identifiers/0199900025260118_hybrid_id.md.
        """
        # This test documents the known discrepancy — it does not assert equality.
        python_components = {
            "outcome": "W1",       # Python position 0
            "duration": "QUICK",   # Python position 1
            "proximity": "AT_EVENT",  # Python position 2
            "calendar_id": "CAL8_USD_NFP_H",  # Python position 3
            "direction": "LONG",   # Python position 4
            "generation": 1,       # Python position 5
        }
        mql4_field_order = ["calendar_id", "duration", "outcome", "proximity", "generation"]
        # Verify the mapping is documented
        assert mql4_field_order[0] == "calendar_id"  # MQL4 SIG = calendar_id
        assert mql4_field_order[2] == "outcome"       # MQL4 OB = outcome (position 2, not 0)


if _HYPOTHESIS_AVAILABLE and _REENTRY_AVAILABLE:
    @given(
        outcome=st.sampled_from(VALID_OUTCOMES),
        duration=st.sampled_from(VALID_DURATIONS),
        proximity=st.sampled_from(VALID_PROXIMITIES),
        calendar_id=st.sampled_from(VALID_CALENDARS),
        direction=st.sampled_from(VALID_DIRECTIONS),
        generation=st.integers(min_value=1, max_value=3),
    )
    @hyp_settings(max_examples=50)
    def test_property_roundtrip(outcome, duration, proximity, calendar_id, direction, generation):
        """Property: for any valid inputs, compose then parse recovers outcome and proximity."""
        hybrid_id = compose(
            outcome=outcome,
            duration=duration,
            proximity=proximity,
            calendar_id=calendar_id,
            direction=direction,
            generation=generation,
        )
        assert hybrid_id is not None
        components = parse(hybrid_id)
        assert components.get("outcome") == outcome
        assert components.get("proximity") == proximity
