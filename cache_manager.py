"""Simple in-memory cache manager."""
import copy
import time
import logging
from typing import Any, Dict, Optional

_cache: Dict[str, Dict[str, Any]] = {}

logger = logging.getLogger(__name__)


def write_to_cache(key: str, value: Any, expiry: Optional[float] = None) -> None:
    """Store a value in the cache with an optional expiry timestamp."""
    if expiry is not None:
        expiry_time = time.time() + expiry
    else:
        expiry_time = None
    _cache[key] = {"value": value, "expiry": expiry_time}
    logger.debug("Stored key '%s' in cache", key)


def read_from_cache(key: str) -> Optional[Any]:
    """Return a cached value if valid.

    Lists and dicts are returned as deep copies so that mutations on the
    returned object do not modify the stored value.
    """
    if key not in _cache:
        logger.debug("Cache miss for key '%s'", key)
        return None
    if not is_cache_valid(key):
        _cache.pop(key, None)
        logger.debug("Cache expired for key '%s'", key)
        return None
    value = _cache[key]["value"]
    logger.debug("Cache hit for key '%s'", key)
    if isinstance(value, (dict, list)):
        return copy.deepcopy(value)
    return value


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
