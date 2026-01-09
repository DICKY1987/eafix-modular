"""
Simple caching utilities for DOC_ID system.

Provides:
- In-memory caching with TTL
- File modification tracking
- Cache invalidation
"""
# DOC_ID: DOC-CORE-COMMON-CACHE-1168

import time
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from functools import wraps


class SimpleCache:
    """
    Simple in-memory cache with TTL support.
    
    Thread-safe for single-process use.
    """
    
    def __init__(self, ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if expired/missing
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if time.time() - entry['timestamp'] > self._ttl:
            del self._cache[key]
            return None
        
        return entry['value']
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = {
            'value': value,
            'timestamp': time.time(),
        }
    
    def invalidate(self, key: str) -> None:
        """Invalidate a cache entry."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def size(self) -> int:
        """Get number of cached entries."""
        return len(self._cache)


class FileCache(SimpleCache):
    """
    Cache that invalidates when file is modified.
    
    Tracks file modification times and automatically
    invalidates cache when file changes.
    """
    
    def __init__(self, ttl: int = 300):
        super().__init__(ttl)
        self._file_mtimes: Dict[str, float] = {}
    
    def get_file(self, path: Path, key: Optional[str] = None) -> Optional[Any]:
        """
        Get cached value for a file.
        
        Automatically invalidates if file was modified.
        
        Args:
            path: File path
            key: Cache key (defaults to str(path))
            
        Returns:
            Cached value or None
        """
        cache_key = key or str(path)
        
        # Check if file exists
        if not path.exists():
            self.invalidate(cache_key)
            return None
        
        # Check if file was modified
        current_mtime = path.stat().st_mtime
        cached_mtime = self._file_mtimes.get(cache_key)
        
        if cached_mtime is not None and current_mtime > cached_mtime:
            # File was modified, invalidate cache
            self.invalidate(cache_key)
            return None
        
        return self.get(cache_key)
    
    def set_file(self, path: Path, value: Any, key: Optional[str] = None) -> None:
        """
        Cache value for a file.
        
        Args:
            path: File path
            value: Value to cache
            key: Cache key (defaults to str(path))
        """
        cache_key = key or str(path)
        
        # Store value and mtime
        self.set(cache_key, value)
        if path.exists():
            self._file_mtimes[cache_key] = path.stat().st_mtime


# Global cache instances
_default_cache = SimpleCache(ttl=300)  # 5 minutes
_file_cache = FileCache(ttl=600)  # 10 minutes


def cached(ttl: int = 300, cache: Optional[SimpleCache] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time-to-live in seconds
        cache: Cache instance (uses default if None)
        
    Example:
        >>> @cached(ttl=60)
        >>> def expensive_operation(arg):
        >>>     return complex_calculation(arg)
    """
    def decorator(func: Callable) -> Callable:
        nonlocal cache
        if cache is None:
            cache = SimpleCache(ttl=ttl)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try cache first
            result = cache.get(key)
            if result is not None:
                return result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        # Add cache management methods
        wrapper.cache = cache
        wrapper.invalidate = lambda: cache.clear()
        
        return wrapper
    return decorator


def get_cache(name: str = "default") -> SimpleCache:
    """
    Get or create a named cache instance.
    
    Args:
        name: Cache name
        
    Returns:
        Cache instance
    """
    if name == "default":
        return _default_cache
    elif name == "file":
        return _file_cache
    else:
        # Create new cache for custom names
        return SimpleCache()
