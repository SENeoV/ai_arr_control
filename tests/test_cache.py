"""Comprehensive tests for caching and utility functions."""

import pytest
import time
from datetime import datetime, timedelta, timezone
from core.cache import HealthCheckCache, CacheEntry
from core.utils import CircuitBreaker

# Get current UTC time in a timezone-aware manner
def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class TestCacheEntry:
    """Test individual cache entry behavior."""
    
    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            service="radarr",
            indexer_id=1,
            indexer_name="BluRay",
            success=True
        )
        assert entry.service == "radarr"
        assert entry.indexer_id == 1
        assert entry.indexer_name == "BluRay"
        assert entry.success is True
        assert entry.error is None
    
    def test_cache_entry_age(self):
        """Test age calculation."""
        entry = CacheEntry(
            service="radarr",
            indexer_id=1,
            indexer_name="Test",
            success=True,
            timestamp=utc_now() - timedelta(seconds=100)
        )
        age = entry.age_seconds
        assert 99 <= age <= 101  # Allow 1 second tolerance
    
    def test_cache_entry_freshness_fresh(self):
        """Test fresh cache entry."""
        entry = CacheEntry(
            service="radarr",
            indexer_id=1,
            indexer_name="Test",
            success=True,
            timestamp=utc_now() - timedelta(seconds=10)
        )
        assert entry.is_fresh(ttl_seconds=300) is True
    
    def test_cache_entry_freshness_expired(self):
        """Test expired cache entry."""
        entry = CacheEntry(
            service="radarr",
            indexer_id=1,
            indexer_name="Test",
            success=True,
            timestamp=utc_now() - timedelta(seconds=350)
        )
        assert entry.is_fresh(ttl_seconds=300) is False


class TestHealthCheckCache:
    """Test health check cache functionality."""
    
    @pytest.fixture
    def cache(self):
        """Create a test cache."""
        return HealthCheckCache(ttl_seconds=300, max_entries=100)
    
    def test_cache_initialization(self, cache):
        """Test cache initialization."""
        assert cache.ttl_seconds == 300
        assert cache.max_entries == 100
        assert cache._hit_count == 0
        assert cache._miss_count == 0
    
    def test_cache_set_and_get_hit(self, cache):
        """Test setting and retrieving a cache entry (hit)."""
        cache.set("radarr", 1, "BluRay", True)
        entry = cache.get("radarr", 1)
        
        assert entry is not None
        assert entry.indexer_name == "BluRay"
        assert entry.success is True
        assert cache._hit_count == 1
        assert cache._miss_count == 0
    
    def test_cache_miss(self, cache):
        """Test cache miss."""
        entry = cache.get("radarr", 999)
        assert entry is None
        assert cache._miss_count == 1
    
    def test_cache_expiration(self, cache):
        """Test cache entry expiration."""
        # Use very short TTL
        cache.ttl_seconds = 1
        cache.set("radarr", 1, "Test", True)
        
        # Should hit initially
        entry = cache.get("radarr", 1)
        assert entry is not None
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should miss now
        entry = cache.get("radarr", 1)
        assert entry is None
    
    def test_cache_invalidate(self, cache):
        """Test invalidating a cache entry."""
        cache.set("radarr", 1, "BluRay", True)
        assert cache.get("radarr", 1) is not None
        
        cache.invalidate("radarr", 1)
        assert cache.get("radarr", 1) is None
    
    def test_cache_invalidate_service(self, cache):
        """Test invalidating all entries for a service."""
        cache.set("radarr", 1, "BluRay", True)
        cache.set("radarr", 2, "NZB", False)
        cache.set("sonarr", 1, "TVReleases", True)
        
        cache.invalidate_service("radarr")
        
        assert cache.get("radarr", 1) is None
        assert cache.get("radarr", 2) is None
        assert cache.get("sonarr", 1) is not None
    
    def test_cache_clear(self, cache):
        """Test clearing entire cache."""
        cache.set("radarr", 1, "BluRay", True)
        cache.set("sonarr", 1, "TVReleases", True)
        
        cache.clear()
        
        assert cache.get("radarr", 1) is None
        assert cache.get("sonarr", 1) is None
    
    def test_cache_stats(self, cache):
        """Test cache statistics."""
        cache.set("radarr", 1, "BluRay", True)
        
        # Generate hits and misses
        cache.get("radarr", 1)  # hit
        cache.get("radarr", 1)  # hit
        cache.get("radarr", 999)  # miss
        
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["total_accesses"] == 3
        assert stats["size"] == 1
        assert 66.0 <= stats["hit_rate_percent"] <= 67.0  # 2/3
    
    def test_cache_eviction(self):
        """Test LRU eviction when capacity reached."""
        cache = HealthCheckCache(ttl_seconds=300, max_entries=2)
        
        # Fill cache
        cache.set("radarr", 1, "Index1", True)
        cache.set("radarr", 2, "Index2", True)
        
        assert cache.get("radarr", 1) is not None
        assert cache.get("radarr", 2) is not None
        
        # Add one more - should evict oldest
        cache.set("radarr", 3, "Index3", True)
        
        # First entry should be evicted (oldest)
        assert cache.get("radarr", 1) is None
        assert cache.get("radarr", 2) is not None
        assert cache.get("radarr", 3) is not None


class TestCircuitBreaker:
    """Test circuit breaker resilience pattern."""
    
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=3,
            recovery_timeout=60.0
        )
        assert cb.name == "test"
        assert cb.failure_threshold == 3
        assert cb.is_open is False
    
    def test_circuit_breaker_success(self):
        """Test circuit breaker on success."""
        cb = CircuitBreaker(name="test")
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.is_open is False
        assert cb.can_proceed() is True
    
    def test_circuit_breaker_failure_threshold(self):
        """Test circuit opens after threshold."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2
        )
        cb.record_failure()
        assert cb.can_proceed() is True
        
        cb.record_failure()
        assert cb.is_open is True
        assert cb.can_proceed() is False
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=1,
            recovery_timeout=0.1
        )
        cb.record_failure()
        assert cb.is_open is True
        
        time.sleep(0.15)
        
        # Should allow recovery
        assert cb.can_proceed() is True
        assert cb.is_open is False
