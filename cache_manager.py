"""Simple in-memory cache manager."""
import time
from typing import Any, Dict, Optional

_cache: Dict[str, Dict[str, Any]] = {}


def write_to_cache(key: str, value: Any, expiry: Optional[float] = None) -> None:
    """Store a value in the cache with an optional expiry timestamp."""
    if expiry is not None:
        expiry_time = time.time() + expiry
    else:
        expiry_time = None
    _cache[key] = {"value": value, "expiry": expiry_time}


def read_from_cache(key: str) -> Optional[Any]:
    """Retrieve a value from the cache if it has not expired."""
    if key not in _cache:
        return None
    if not is_cache_valid(key):
        _cache.pop(key, None)
        return None
    return _cache[key]["value"]


def is_cache_valid(key: str) -> bool:
    """Check whether a cached value is still valid based on its expiry."""
    entry = _cache.get(key)
    if not entry:
        return False
    expiry = entry["expiry"]
    return expiry is None or expiry > time.time()


def clear_cache(key: Optional[str] = None) -> None:
    """Clear a specific cache key or the entire cache."""
    if key is None:
        _cache.clear()
    else:
        _cache.pop(key, None)
