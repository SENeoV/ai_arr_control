"""Health check caching for performance optimization.

Caches indexer health results to reduce unnecessary API calls
while maintaining freshness guarantees.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from loguru import logger

# Get current UTC time in a timezone-aware manner
def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


@dataclass
class CacheEntry:
    """Single cached health check result."""
    service: str
    indexer_id: int
    indexer_name: str
    success: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=utc_now)
    
    @property
    def age_seconds(self) -> float:
        """How old is this cache entry (in seconds)."""
        return (utc_now() - self.timestamp).total_seconds()
    
    def is_fresh(self, ttl_seconds: int = 300) -> bool:
        """Check if this entry is still fresh (not expired)."""
        return self.age_seconds < ttl_seconds


class HealthCheckCache:
    """In-memory cache for health check results.
    
    Reduces duplicate API calls within a TTL window while maintaining
    freshness guarantees. Useful for reducing load during multi-service checks.
    """
    
    def __init__(self, ttl_seconds: int = 300, max_entries: int = 10000) -> None:
        """Initialize health check cache.
        
        Args:
            ttl_seconds: Time-to-live for cache entries (default 5 min)
            max_entries: Maximum entries before LRU eviction
        """
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._cache: Dict[str, CacheEntry] = {}
        self._hit_count = 0
        self._miss_count = 0
        logger.info(f"Initialized HealthCheckCache (ttl={ttl_seconds}s, max={max_entries})")
    
    def _make_key(self, service: str, indexer_id: int) -> str:
        """Create cache key from service and indexer."""
        return f"{service}:{indexer_id}"
    
    def get(self, service: str, indexer_id: int) -> Optional[CacheEntry]:
        """Get cached health check result if fresh.
        
        Args:
            service: Service name (radarr, sonarr, etc.)
            indexer_id: Indexer ID
            
        Returns:
            CacheEntry if found and fresh, None otherwise
        """
        key = self._make_key(service, indexer_id)
        entry = self._cache.get(key)
        
        if entry is None:
            self._miss_count += 1
            return None
        
        if not entry.is_fresh(self.ttl_seconds):
            # Expired, remove it
            del self._cache[key]
            self._miss_count += 1
            return None
        
        self._hit_count += 1
        logger.debug(f"Cache HIT for {service} indexer {indexer_id}")
        return entry
    
    def set(self, service: str, indexer_id: int, indexer_name: str, 
            success: bool, error: Optional[str] = None) -> None:
        """Store health check result in cache.
        
        Args:
            service: Service name
            indexer_id: Indexer ID
            indexer_name: Human-readable indexer name
            success: Whether the health check passed
            error: Error message if check failed
        """
        # Evict oldest entry if at capacity
        if len(self._cache) >= self.max_entries:
            # Find and remove oldest entry (simple LRU)
            oldest_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].timestamp
            )
            del self._cache[oldest_key]
            logger.debug(f"Evicted cache entry {oldest_key} (capacity reached)")
        
        key = self._make_key(service, indexer_id)
        self._cache[key] = CacheEntry(
            service=service,
            indexer_id=indexer_id,
            indexer_name=indexer_name,
            success=success,
            error=error,
            timestamp=utc_now()
        )
        logger.debug(f"Cached result for {service} indexer {indexer_id}")
    
    def invalidate(self, service: str, indexer_id: int) -> None:
        """Manually invalidate a cache entry.
        
        Args:
            service: Service name
            indexer_id: Indexer ID
        """
        key = self._make_key(service, indexer_id)
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Invalidated cache for {service} indexer {indexer_id}")
    
    def invalidate_service(self, service: str) -> None:
        """Invalidate all entries for a service.
        
        Args:
            service: Service name (e.g., 'radarr')
        """
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{service}:")]
        for key in keys_to_remove:
            del self._cache[key]
        logger.debug(f"Invalidated {len(keys_to_remove)} cache entries for {service}")
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cleared health check cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with hit rate, miss rate, size, etc.
        """
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0
        
        return {
            "size": len(self._cache),
            "hits": self._hit_count,
            "misses": self._miss_count,
            "total_accesses": total,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_seconds": self.ttl_seconds,
            "max_entries": self.max_entries,
        }
