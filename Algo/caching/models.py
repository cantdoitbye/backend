from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.cache import cache
import json


class CacheConfiguration(models.Model):
    """
    Configuration for different cache strategies.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Cache strategy
    cache_type = models.CharField(
        max_length=30,
        choices=[
            ('feed', 'User Feed Cache'),
            ('trending', 'Trending Content Cache'),
            ('connections', 'Connection Circle Cache'),
            ('interests', 'Interest-based Cache'),
            ('scores', 'Scoring Cache'),
            ('analytics', 'Analytics Cache')
        ]
    )
    
    # Cache settings
    default_ttl_seconds = models.PositiveIntegerField(default=3600)  # 1 hour
    max_entries = models.PositiveIntegerField(default=10000)
    
    # Cache strategy configuration
    strategy = models.CharField(
        max_length=20,
        choices=[
            ('lru', 'Least Recently Used'),
            ('lfu', 'Least Frequently Used'),
            ('ttl', 'Time To Live'),
            ('write_through', 'Write Through'),
            ('write_back', 'Write Back')
        ],
        default='ttl'
    )
    
    # Additional configuration
    config = models.JSONField(default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cache_configurations'
        indexes = [
            models.Index(fields=['cache_type', 'is_active']),
            models.Index(fields=['strategy'])
        ]
    
    def __str__(self):
        return f"{self.name} ({self.cache_type})"


class CacheEntry(models.Model):
    """
    Tracks cache entries for monitoring and management.
    """
    cache_key = models.CharField(max_length=250, unique=True)
    cache_type = models.CharField(max_length=30)
    
    # Entry metadata
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Cache metrics
    hit_count = models.PositiveIntegerField(default=0)
    miss_count = models.PositiveIntegerField(default=0)
    size_bytes = models.PositiveIntegerField(default=0)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'cache_entries'
        indexes = [
            models.Index(fields=['cache_type', 'is_active']),
            models.Index(fields=['user', 'cache_type']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['last_accessed']),
            models.Index(fields=['hit_count'])
        ]
    
    def __str__(self):
        return f"Cache: {self.cache_key}"
    
    @property
    def is_expired(self):
        """Check if this cache entry has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def hit_rate(self):
        """Calculate cache hit rate."""
        total_requests = self.hit_count + self.miss_count
        if total_requests == 0:
            return 0.0
        return self.hit_count / total_requests
    
    def record_hit(self):
        """Record a cache hit."""
        self.hit_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['hit_count', 'last_accessed'])
    
    def record_miss(self):
        """Record a cache miss."""
        self.miss_count += 1
        self.save(update_fields=['miss_count'])


class FeedCache(models.Model):
    """
    Specific cache model for user feeds.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feed_caches')
    
    # Cache content
    feed_data = models.JSONField(default=list)
    composition = models.JSONField(default=dict)  # The composition used
    
    # Cache metadata
    cache_key = models.CharField(max_length=200)
    generation_time_ms = models.PositiveIntegerField(default=0)
    content_count = models.PositiveIntegerField(default=0)
    
    # Cache validation
    version = models.CharField(max_length=50, default='1.0')
    checksum = models.CharField(max_length=64, blank=True)  # MD5 hash
    
    # Status and timing
    is_valid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'feed_caches'
        unique_together = ('user', 'cache_key')
        indexes = [
            models.Index(fields=['user', 'is_valid']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['generation_time_ms']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"Feed cache for {self.user.username}"
    
    @property
    def is_expired(self):
        """Check if this feed cache has expired."""
        return timezone.now() > self.expires_at or not self.is_valid
    
    def invalidate(self):
        """Mark this cache as invalid."""
        self.is_valid = False
        self.save(update_fields=['is_valid'])
        
        # Also remove from Redis cache
        cache.delete(self.cache_key)


class TrendingCache(models.Model):
    """
    Cache for trending content across different time windows.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    
    # Trending window
    time_window = models.CharField(
        max_length=10,
        choices=[
            ('1h', '1 Hour'),
            ('6h', '6 Hours'),
            ('24h', '24 Hours'),
            ('7d', '7 Days')
        ],
        default='24h'
    )
    
    # Trending data
    trending_items = models.JSONField(default=list)
    total_items = models.PositiveIntegerField(default=0)
    
    # Cache metadata
    cache_key = models.CharField(max_length=200)
    calculation_time_ms = models.PositiveIntegerField(default=0)
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'trending_caches'
        unique_together = ('content_type', 'time_window')
        indexes = [
            models.Index(fields=['time_window', 'expires_at']),
            models.Index(fields=['content_type', 'calculated_at']),
            models.Index(fields=['total_items'])
        ]
    
    def __str__(self):
        return f"Trending {self.content_type.name} ({self.time_window})"
    
    @property
    def is_expired(self):
        """Check if this trending cache has expired."""
        return timezone.now() > self.expires_at


class ConnectionCache(models.Model):
    """
    Cache for user connection circles to optimize feed generation.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='connection_caches')
    
    # Connection data by circle type
    inner_circle_users = models.JSONField(default=list)
    outer_circle_users = models.JSONField(default=list)
    universe_users = models.JSONField(default=list)
    
    # Cache metadata
    cache_key = models.CharField(max_length=200)
    total_connections = models.PositiveIntegerField(default=0)
    
    # Cache validation
    last_connection_update = models.DateTimeField(null=True, blank=True)
    is_stale = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'connection_caches'
        unique_together = ('user', 'cache_key')
        indexes = [
            models.Index(fields=['user', 'is_stale']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['total_connections'])
        ]
    
    def __str__(self):
        return f"Connection cache for {self.user.username}"
    
    @property
    def is_expired(self):
        """Check if this connection cache has expired or is stale."""
        return timezone.now() > self.expires_at or self.is_stale
    
    def mark_stale(self):
        """Mark this cache as stale due to connection changes."""
        self.is_stale = True
        self.save(update_fields=['is_stale'])


class CacheInvalidationEvent(models.Model):
    """
    Tracks cache invalidation events for auditing and optimization.
    """
    cache_type = models.CharField(max_length=30)
    cache_key = models.CharField(max_length=250, blank=True)
    
    # Invalidation details
    event_type = models.CharField(
        max_length=30,
        choices=[
            ('manual', 'Manual Invalidation'),
            ('expired', 'TTL Expiration'),
            ('dependency', 'Dependency Change'),
            ('capacity', 'Cache Capacity Limit'),
            ('error', 'Error Occurred')
        ]
    )
    
    # Event context
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Event details
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cache_invalidation_events'
        indexes = [
            models.Index(fields=['cache_type', 'event_type']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"Cache invalidation: {self.cache_type} ({self.event_type})"
