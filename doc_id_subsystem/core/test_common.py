"""
Comprehensive test suite for common module.

Tests all utilities, config, errors, caching, and registry.
"""
# DOC_ID: DOC-TEST-COMMON-TEST-COMMON-670

import pytest
import sys
import tempfile
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import (
    REPO_ROOT, MODULE_ROOT, DOC_ID_REGEX,
    validate_doc_id, extract_category_from_doc_id,
    load_yaml, save_yaml, load_jsonl, save_jsonl,
    SimpleCache, FileCache, cached,
    DocIDError, InvalidDocIDError, RegistryNotFoundError,
)


class TestConfig:
    """Test configuration module."""
    
    def test_repo_root_exists(self):
        """REPO_ROOT should point to existing directory."""
        assert REPO_ROOT.exists()
        assert REPO_ROOT.is_dir()
    
    def test_module_root_exists(self):
        """MODULE_ROOT should point to SUB_DOC_ID."""
        assert MODULE_ROOT.exists()
        assert MODULE_ROOT.name == "SUB_DOC_ID"
    
    def test_doc_id_regex_valid(self):
        """DOC_ID_REGEX should match valid doc_ids."""
        valid_ids = [
            "DOC-CORE-SCHEDULER-001",
            "DOC-ERROR-HANDLER-RETRY-042",
            "DOC-SCRIPT-TEST-999",
        ]
        for doc_id in valid_ids:
            assert DOC_ID_REGEX.match(doc_id), f"Should match: {doc_id}"
    
    def test_doc_id_regex_invalid(self):
        """DOC_ID_REGEX should not match invalid doc_ids."""
        invalid_ids = [
            "DOC-CORE",  # Missing number
            "doc-core-test-001",  # Lowercase
            "DOC-CORE-TEST",  # Missing number
            "CORE-TEST-001",  # Missing DOC prefix
        ]
        for doc_id in invalid_ids:
            assert not DOC_ID_REGEX.match(doc_id), f"Should not match: {doc_id}"


class TestUtils:
    """Test utility functions."""
    
    def test_validate_doc_id_valid(self):
        """validate_doc_id should return True for valid IDs."""
        assert validate_doc_id("DOC-CORE-TEST-001")
        assert validate_doc_id("DOC-ERROR-HANDLER-999")
    
    def test_validate_doc_id_invalid(self):
        """validate_doc_id should return False for invalid IDs."""
        assert not validate_doc_id("invalid")
        assert not validate_doc_id("DOC-CORE")
        assert not validate_doc_id("doc-core-test-001")
    
    def test_extract_category_valid(self):
        """extract_category_from_doc_id should extract category."""
        assert extract_category_from_doc_id("DOC-CORE-TEST-001") == "core"
        assert extract_category_from_doc_id("DOC-ERROR-HANDLER-001") == "error"
        assert extract_category_from_doc_id("DOC-SCRIPT-TEST-001") == "script"
    
    def test_extract_category_unknown(self):
        """extract_category_from_doc_id should return 'unknown' for invalid."""
        assert extract_category_from_doc_id("invalid") == "unknown"
        assert extract_category_from_doc_id("DOC-UNKNOWN-TEST-001") == "unknown"
    
    def test_yaml_roundtrip(self):
        """YAML save/load should preserve data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            data = {"test": "value", "number": 42, "list": [1, 2, 3]}
            save_yaml(temp_path, data)
            loaded = load_yaml(temp_path)
            assert loaded == data
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_jsonl_roundtrip(self):
        """JSONL save/load should preserve data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            data = [
                {"id": 1, "name": "test1"},
                {"id": 2, "name": "test2"},
            ]
            save_jsonl(temp_path, data)
            loaded = load_jsonl(temp_path)
            assert loaded == data
        finally:
            temp_path.unlink(missing_ok=True)


class TestErrors:
    """Test custom exceptions."""
    
    def test_doc_id_error_base(self):
        """DocIDError should be base exception."""
        with pytest.raises(DocIDError):
            raise DocIDError("test error")
    
    def test_invalid_doc_id_error(self):
        """InvalidDocIDError should inherit from DocIDError."""
        with pytest.raises(DocIDError):
            raise InvalidDocIDError("DOC-INVALID")
        
        with pytest.raises(InvalidDocIDError):
            raise InvalidDocIDError("DOC-INVALID")
    
    def test_registry_not_found_error(self):
        """RegistryNotFoundError should inherit from DocIDError."""
        with pytest.raises(DocIDError):
            raise RegistryNotFoundError("/fake/path")


class TestCache:
    """Test caching utilities."""
    
    def test_simple_cache_basic(self):
        """SimpleCache should store and retrieve values."""
        cache = SimpleCache(ttl=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_simple_cache_miss(self):
        """SimpleCache should return None for missing keys."""
        cache = SimpleCache()
        assert cache.get("nonexistent") is None
    
    def test_simple_cache_invalidate(self):
        """SimpleCache invalidate should remove key."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        cache.invalidate("key1")
        assert cache.get("key1") is None
    
    def test_simple_cache_clear(self):
        """SimpleCache clear should remove all keys."""
        cache = SimpleCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.size() == 0
    
    def test_cached_decorator(self):
        """@cached decorator should cache function results."""
        call_count = 0
        
        @cached(ttl=10)
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = expensive_func(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call (should use cache)
        result2 = expensive_func(5)
        assert result2 == 10
        assert call_count == 1  # Not called again
        
        # Different argument
        result3 = expensive_func(10)
        assert result3 == 20
        assert call_count == 2  # Called with new arg
    
    def test_file_cache_basic(self):
        """FileCache should store and retrieve file-based data."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            cache = FileCache()
            cache.set_file(temp_path, "test_data")
            cached = cache.get_file(temp_path)
            assert cached == "test_data"
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_file_cache_modification(self):
        """FileCache should invalidate on file modification."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = Path(f.name)
            f.write("original")
        
        try:
            cache = FileCache()
            
            # Cache original
            cache.set_file(temp_path, "cached_data")
            assert cache.get_file(temp_path) == "cached_data"
            
            # Modify file
            import time
            time.sleep(0.1)  # Ensure mtime changes
            temp_path.write_text("modified")
            
            # Cache should be invalidated
            assert cache.get_file(temp_path) is None
        finally:
            temp_path.unlink(missing_ok=True)


class TestIntegration:
    """Integration tests for common module."""
    
    def test_full_workflow(self):
        """Test complete workflow: config + utils + cache."""
        # 1. Validate doc_id
        doc_id = "DOC-CORE-TEST-001"
        assert validate_doc_id(doc_id)
        
        # 2. Extract category
        category = extract_category_from_doc_id(doc_id)
        assert category == "core"
        
        # 3. Cache result
        cache = SimpleCache()
        cache.set(f"category:{doc_id}", category)
        assert cache.get(f"category:{doc_id}") == "core"
    
    def test_error_handling_workflow(self):
        """Test error handling in workflows."""
        # Invalid doc_id should raise error
        with pytest.raises(InvalidDocIDError):
            if not validate_doc_id("INVALID"):
                raise InvalidDocIDError("INVALID")


def run_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("Running Common Module Test Suite")
    print("="*60 + "\n")
    
    # Run pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes",
    ])
    
    return exit_code


if __name__ == "__main__":
    exit(run_tests())
