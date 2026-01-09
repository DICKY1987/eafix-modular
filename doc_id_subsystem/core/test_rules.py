"""
Tests for common/rules.py - doc_id rules and validation.
"""
# DOC_ID: DOC-TEST-RULES-001

import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.rules import (
    DOC_ID_WIDTH,
    DOC_ID_REGEX,
    CategoryPrefix,
    validate_doc_id,
    validate_doc_id_strict,
    parse_doc_id,
    parse_doc_id_full,
    format_doc_id,
    normalize_doc_id,
    extract_category,
    extract_name,
    extract_sequence,
    compare_doc_ids,
    doc_ids_match,
    is_sequence_exhausted,
    get_next_width,
    max_sequence_for_width,
    is_legacy_format,
    suggest_next_sequence,
)


class TestValidation:
    """Test validation functions."""
    
    def test_validate_doc_id_valid_4_digit(self):
        assert validate_doc_id("DOC-CORE-TEST-0001") is True
        assert validate_doc_id("DOC-SCRIPT-AUTO-ASSIGN-0042") is True
        assert validate_doc_id("DOC-GUIDE-USER-MANUAL-9999") is True
    
    def test_validate_doc_id_valid_3_digit_legacy(self):
        assert validate_doc_id("DOC-CORE-TEST-001") is True
        assert validate_doc_id("DOC-SCRIPT-SCANNER-999") is True
    
    def test_validate_doc_id_valid_5_digit(self):
        assert validate_doc_id("DOC-CORE-TEST-10000") is True
        assert validate_doc_id("DOC-CORE-TEST-99999") is True
    
    def test_validate_doc_id_with_multi_part_name(self):
        assert validate_doc_id("DOC-CORE-TEST-SUITE-RUNNER-0001") is True
        assert validate_doc_id("DOC-PATTERN-BATCH-DOC-ID-001") is True
    
    def test_validate_doc_id_invalid_formats(self):
        assert validate_doc_id("") is False
        assert validate_doc_id("DOC-INVALID") is False
        assert validate_doc_id("DOC-TEST-01") is False  # Too short (2 digits)
        assert validate_doc_id("doc-core-test-001") is False  # Lowercase
        assert validate_doc_id("CORE-TEST-001") is False  # Missing DOC prefix
        assert validate_doc_id("DOC-CORE-TEST") is False  # Missing sequence
    
    def test_validate_doc_id_strict_width(self):
        assert validate_doc_id_strict("DOC-CORE-TEST-0001", width=4) is True
        assert validate_doc_id_strict("DOC-CORE-TEST-001", width=4) is False  # Wrong width
        assert validate_doc_id_strict("DOC-CORE-TEST-001", width=3) is True
        assert validate_doc_id_strict("DOC-CORE-TEST-00001", width=5) is True


class TestParsing:
    """Test parsing functions."""
    
    def test_parse_doc_id_simple(self):
        result = parse_doc_id("DOC-CORE-TEST-0001")
        assert result == {
            "category": "CORE",
            "name": "TEST",
            "sequence": "0001"
        }
    
    def test_parse_doc_id_multi_part_name(self):
        result = parse_doc_id("DOC-PATTERN-BATCH-DOC-ID-001")
        assert result == {
            "category": "PAT",
            "name": "BATCH-DOC-ID",
            "sequence": "001"
        }
    
    def test_parse_doc_id_invalid(self):
        assert parse_doc_id("") is None
        assert parse_doc_id("INVALID") is None
        assert parse_doc_id("DOC-INVALID") is None
    
    def test_parse_doc_id_full(self):
        result = parse_doc_id_full("DOC-CORE-TEST-0001")
        assert result["category"] == "CORE"
        assert result["name"] == "TEST"
        assert result["sequence"] == "0001"
        assert result["sequence_int"] == 1
        assert result["width"] == 4
        assert result["is_legacy"] is False
    
    def test_parse_doc_id_full_legacy(self):
        result = parse_doc_id_full("DOC-CORE-TEST-001")
        assert result["sequence_int"] == 1
        assert result["width"] == 3
        assert result["is_legacy"] is True


class TestFormatting:
    """Test formatting functions."""
    
    def test_format_doc_id_default_width(self):
        assert format_doc_id("CORE", "TEST", 1) == "DOC-CORE-TEST-0001"
        assert format_doc_id("SCRIPT", "SCANNER", 42) == "DOC-SCRIPT-SCANNER-0042"
    
    def test_format_doc_id_custom_width(self):
        assert format_doc_id("CORE", "TEST", 1, width=3) == "DOC-CORE-TEST-001"
        assert format_doc_id("CORE", "TEST", 1, width=5) == "DOC-CORE-TEST-00001"
    
    def test_format_doc_id_multi_part_name(self):
        result = format_doc_id("PAT", "BATCH-DOC-ID", 337, width=3)
        assert result == "DOC-PATTERN-BATCH-DOC-ID-337"
    
    def test_format_doc_id_case_normalization(self):
        # Should uppercase inputs
        assert format_doc_id("core", "test", 1) == "DOC-CORE-TEST-0001"
        assert format_doc_id("Core", "Test", 1) == "DOC-CORE-TEST-0001"
    
    def test_normalize_doc_id_legacy_to_standard(self):
        assert normalize_doc_id("DOC-CORE-TEST-001") == "DOC-CORE-TEST-0001"
        assert normalize_doc_id("DOC-SCRIPT-SCANNER-999") == "DOC-SCRIPT-SCANNER-0999"
    
    def test_normalize_doc_id_already_standard(self):
        assert normalize_doc_id("DOC-CORE-TEST-0001") == "DOC-CORE-TEST-0001"
    
    def test_normalize_doc_id_invalid(self):
        assert normalize_doc_id("") is None
        assert normalize_doc_id("INVALID") is None


class TestComponentExtraction:
    """Test component extraction functions."""
    
    def test_extract_category(self):
        assert extract_category("DOC-CORE-TEST-0001") == "CORE"
        assert extract_category("DOC-SCRIPT-SCANNER-0042") == "SCRIPT"
        assert extract_category("INVALID") is None
    
    def test_extract_name(self):
        assert extract_name("DOC-CORE-TEST-0001") == "TEST"
        assert extract_name("DOC-PATTERN-BATCH-DOC-ID-001") == "BATCH-DOC-ID"
        assert extract_name("INVALID") is None
    
    def test_extract_sequence(self):
        assert extract_sequence("DOC-CORE-TEST-0001") == 1
        assert extract_sequence("DOC-SCRIPT-SCANNER-0042") == 42
        assert extract_sequence("DOC-CORE-TEST-001") == 1  # Legacy
        assert extract_sequence("INVALID") is None


class TestComparison:
    """Test comparison functions."""
    
    def test_compare_doc_ids_by_category(self):
        assert compare_doc_ids("DOC-CORE-TEST-0001", "DOC-SCRIPT-TEST-0001") == -1
        assert compare_doc_ids("DOC-SCRIPT-TEST-0001", "DOC-CORE-TEST-0001") == 1
    
    def test_compare_doc_ids_by_name(self):
        assert compare_doc_ids("DOC-CORE-AAA-0001", "DOC-CORE-BBB-0001") == -1
        assert compare_doc_ids("DOC-CORE-BBB-0001", "DOC-CORE-AAA-0001") == 1
    
    def test_compare_doc_ids_by_sequence(self):
        assert compare_doc_ids("DOC-CORE-TEST-0001", "DOC-CORE-TEST-0002") == -1
        assert compare_doc_ids("DOC-CORE-TEST-0042", "DOC-CORE-TEST-0001") == 1
    
    def test_compare_doc_ids_equal(self):
        assert compare_doc_ids("DOC-CORE-TEST-0001", "DOC-CORE-TEST-0001") == 0
    
    def test_doc_ids_match_exact(self):
        assert doc_ids_match("DOC-CORE-TEST-0001", "DOC-CORE-TEST-0001") is True
        assert doc_ids_match("DOC-CORE-TEST-0001", "DOC-CORE-TEST-0002") is False
    
    def test_doc_ids_match_ignore_width(self):
        # Should match legacy 3-digit with standard 4-digit
        assert doc_ids_match("DOC-CORE-TEST-001", "DOC-CORE-TEST-0001", ignore_width=True) is True
        assert doc_ids_match("DOC-CORE-TEST-001", "DOC-CORE-TEST-0002", ignore_width=True) is False
    
    def test_doc_ids_match_strict_width(self):
        # Should NOT match when ignore_width=False
        assert doc_ids_match("DOC-CORE-TEST-001", "DOC-CORE-TEST-0001", ignore_width=False) is False


class TestRangeFunctions:
    """Test range and capacity functions."""
    
    def test_is_sequence_exhausted_4_digit(self):
        # Max for 4 digits = 9999, threshold = 9999 * 0.9 = 8999.1
        assert is_sequence_exhausted(8998, width=4) is False  # Under threshold
        assert is_sequence_exhausted(8999, width=4) is False  # Just under (8999 < 8999.1)
        assert is_sequence_exhausted(9000, width=4) is True   # Over threshold
        assert is_sequence_exhausted(9999, width=4) is True   # At max
    
    def test_is_sequence_exhausted_3_digit(self):
        # Max for 3 digits = 999, threshold = 999 * 0.9 = 899.1
        assert is_sequence_exhausted(899, width=3) is False   # Just under (899 < 899.1)
        assert is_sequence_exhausted(900, width=3) is True    # Over threshold
    
    def test_get_next_width(self):
        assert get_next_width(3) == 4
        assert get_next_width(4) == 5
        assert get_next_width(5) == 6
    
    def test_max_sequence_for_width(self):
        assert max_sequence_for_width(3) == 999
        assert max_sequence_for_width(4) == 9999
        assert max_sequence_for_width(5) == 99999


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_is_legacy_format(self):
        assert is_legacy_format("DOC-CORE-TEST-001") is True
        assert is_legacy_format("DOC-CORE-TEST-0001") is False
        assert is_legacy_format("DOC-CORE-TEST-00001") is False
    
    def test_suggest_next_sequence_empty(self):
        assert suggest_next_sequence("CORE", []) == 1
    
    def test_suggest_next_sequence_with_existing(self):
        assert suggest_next_sequence("CORE", [1, 2, 3]) == 4
        assert suggest_next_sequence("CORE", [1, 5, 10]) == 11
        assert suggest_next_sequence("CORE", [42]) == 43


class TestCategoryPrefix:
    """Test CategoryPrefix enum."""
    
    def test_category_prefix_values(self):
        assert CategoryPrefix.CORE.value == "CORE"
        assert CategoryPrefix.SCRIPT.value == "SCRIPT"
        assert CategoryPrefix.GUIDE.value == "GUIDE"
    
    def test_category_prefix_in_format(self):
        result = format_doc_id(CategoryPrefix.CORE.value, "TEST", 1)
        assert result == "DOC-CORE-TEST-0001"


class TestConstants:
    """Test module constants."""
    
    def test_doc_id_width(self):
        assert DOC_ID_WIDTH == 4
    
    def test_doc_id_regex_pattern(self):
        assert DOC_ID_REGEX is not None
        # Test basic match
        assert DOC_ID_REGEX.match("DOC-CORE-TEST-0001") is not None
        assert DOC_ID_REGEX.match("INVALID") is None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
