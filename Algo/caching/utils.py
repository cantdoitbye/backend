"""
Caching utilities for the Ooumph Feed Algorithm system.

Provides Redis-based caching for feed data, trending content,
connections, and other performance-critical operations.
"""

from django.core.cache import cache, caches
from django.conf import settings
from django.utils import timezone
from typing import List, Dict, Any, Optional, Union
import json
import redis
import structlog
import hashlib
import time

logger = structlog.get_logger(__name__)


class FeedCacheManager:
    """
    Manages feed-specific caching operations.
    
    Handles caching for user feeds, trending content, connections,
    and interest-based recommendations.
    """
    
    def __init__(self):
        """
        Initialize the feed cache manager.
        """
        self.default_cache = caches['default']
        self.feed_cache = caches['feed_cache']
        self.trending_cache = caches['trending_cache']
        self.config = settings.FEED_ALGORITHM_CONFIG
        
        logger.debug("Feed cache manager initialized")
    
    def _generate_cache_key(self, key_type: str, *args) -> str:
        """
        Generate a standardized cache key.
        
        Args:
            key_type: Type of cache key (feed, trending, etc.)
            *args: Arguments to include in key
        
        Returns:
            Formatted cache key
        """
        key_parts = [key_type] + [str(arg) for arg in args]
        key_string = ":".join(key_parts)
        
        # Hash long keys to avoid Redis key length limits
        if len(key_string) > 250:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{key_type}:hashed:{key_hash}"
        
        return key_string
    
    # User Feed Caching
    def get_user_feed(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached user feed.
        
        Args:
            user_id: User ID
        
        Returns:
            Cached feed items or None
        """
        try:
            cache_key = self._generate_cache_key("user_feed", user_id)
            cached_feed = self.feed_cache.get(cache_key)
            
            if cached_feed:
                logger.debug(
                    "User feed cache hit",
                    user_id=user_id,
                    cache_key=cache_key
                )
                return cached_feed
            
            logger.debug(
                "User feed cache miss",
                user_id=user_id,
                cache_key=cache_key
            )
            return None
            
        except Exception as e:
            logger.error(
                "Failed to get user feed from cache",
                user_id=user_id,
                error=str(e)
            )
            return None
    
    def set_user_feed(
        self, 
        user_id: int, 
        feed_items: List[Any], 
        timeout: Optional[int] = None
    ) -> bool:
        """
        Cache user feed.
        
        Args:
            user_id: User ID
            feed_items: Feed items to cache
            timeout: Cache timeout in seconds
        
        Returns:
            Success status
        """
        try:
            cache_key = self._generate_cache_key("user_feed", user_id)
            cache_timeout = timeout or self.config['CACHE_TIMEOUTS']['user_feed']
            
            # Serialize feed items for caching
            serialized_items = self._serialize_feed_items(feed_items)
            
            self.feed_cache.set(
                cache_key, 
                serialized_items, 
                timeout=cache_timeout
            )
            
            logger.debug(
                "User feed cached",
                user_id=user_id,
                cache_key=cache_key,
                timeout=cache_timeout,
                items_count=len(feed_items)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to cache user feed",
                user_id=user_id,
                error=str(e)
            )
            return False
    
    def invalidate_user_feed(self, user_id: int) -> bool:
        """
        Invalidate cached user feed.
        
        Args:
            user_id: User ID
        
        Returns:
            Success status
        """
        try:
            cache_key = self._generate_cache_key("user_feed", user_id)
            self.feed_cache.delete(cache_key)
            
            logger.debug(
                "User feed cache invalidated",
                user_id=user_id,
                cache_key=cache_key
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to invalidate user feed cache",
                user_id=user_id,
                error=str(e)
            )
            return False
    
    # Trending Content Caching
    def get_trending_content(
        self, 
        content_type: Optional[str] = None,
        window_hours: int = 24
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached trending content.
        
        Args:
            content_type: Optional content type filter
            window_hours: Trending window in hours
        
        Returns:
            Cached trending content or None
        """
        try:
            cache_key = self._generate_cache_key(
                "trending", content_type or "all", window_hours
            )
            
            cached_trending = self.trending_cache.get(cache_key)
            
            if cached_trending:
                logger.debug(
                    "Trending content cache hit",
                    content_type=content_type,
                    window_hours=window_hours
                )
                return cached_trending
            
            return None
            
        except Exception as e:
            logger.error(
                "Failed to get trending content from cache",
                content_type=content_type,
                error=str(e)
            )
            return None
    
    def set_trending_content(
        self, 
        trending_items: List[Any],
        content_type: Optional[str] = None,
        window_hours: int = 24,
        timeout: Optional[int] = None
    ) -> bool:
        """
        Cache trending content.
        
        Args:
            trending_items: Trending items to cache
            content_type: Optional content type
            window_hours: Trending window in hours
            timeout: Cache timeout in seconds
        
        Returns:
            Success status
        """
        try:
            cache_key = self._generate_cache_key(
                "trending", content_type or "all", window_hours
            )
            cache_timeout = timeout or self.config['CACHE_TIMEOUTS']['trending_metrics']
            
            # Serialize trending items
            serialized_items = self._serialize_feed_items(trending_items)
            
            self.trending_cache.set(
                cache_key,
                serialized_items,
                timeout=cache_timeout
            )
            
            logger.debug(
                "Trending content cached",
                content_type=content_type,
                window_hours=window_hours,
                items_count=len(trending_items)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to cache trending content",
                content_type=content_type,
                error=str(e)
            )
            return False
    
    # Connection Caching
    def get_connection_circles(self, user_id: int) -> Optional[Dict[str, List[int]]]:
        """
        Get cached connection circles for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary of circle_type -> [user_ids] or None
        """
        try:
            cache_key = self._generate_cache_key("connections", user_id)
            cached_circles = self.default_cache.get(cache_key)
            
            if cached_circles:
                logger.debug(
                    "Connection circles cache hit",
                    user_id=user_id
                )
                return cached_circles
            
            return None
            
        except Exception as e:
            logger.error(
                "Failed to get connection circles from cache",
                user_id=user_id,
                error=str(e)
            )
            return None
    
    def set_connection_circles(
        self, 
        user_id: int, 
        circles: Dict[str, List[int]],
        timeout: Optional[int] = None
    ) -> bool:
        """
        Cache user's connection circles.
        
        Args:
            user_id: User ID
            circles: Dictionary of circle_type -> [user_ids]
            timeout: Cache timeout in seconds
        
        Returns:
            Success status
        """
        try:
            cache_key = self._generate_cache_key("connections", user_id)
            cache_timeout = timeout or self.config['CACHE_TIMEOUTS']['connection_circles']
            
            self.default_cache.set(
                cache_key,
                circles,
                timeout=cache_timeout
            )
            
            logger.debug(
                "Connection circles cached",
                user_id=user_id,
                circles_count=sum(len(circle) for circle in circles.values())
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to cache connection circles",
                user_id=user_id,
                error=str(e)
            )
            return False
    
    def invalidate_connection_cache(self, user_id: int) -> bool:
        """
        Invalidate cached connection data for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Success status
        """
        try:
            cache_key = self._generate_cache_key("connections", user_id)
            self.default_cache.delete(cache_key)
            
            logger.debug(
                "Connection cache invalidated",
                user_id=user_id
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to invalidate connection cache",
                user_id=user_id,
                error=str(e)
            )
            return False
    
    # Interest Recommendations Caching
    def get_interest_recommendations(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached interest recommendations for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Cached interest recommendations or None
        """
        try:
            cache_key = self._generate_cache_key("interest_recommendations", user_id)
            cached_recommendations = self.default_cache.get(cache_key)
            
            if cached_recommendations:
                logger.debug(
                    "Interest recommendations cache hit",
                    user_id=user_id
                )
                return cached_recommendations
            
            return None
            
        except Exception as e:
            logger.error(
                "Failed to get interest recommendations from cache",
                user_id=user_id,
                error=str(e)
            )
            return None
    
    def set_interest_recommendations(
        self, 
        user_id: int, 
        recommendations: List[Dict[str, Any]],
        timeout: Optional[int] = None
    ) -> bool:
        """
        Cache interest recommendations for a user.
        
        Args:
            user_id: User ID
            recommendations: Interest recommendations to cache
            timeout: Cache timeout in seconds
        
        Returns:
            Success status
        """
        try:
            cache_key = self._generate_cache_key("interest_recommendations", user_id)
            cache_timeout = timeout or self.config['CACHE_TIMEOUTS']['interest_recommendations']
            
            self.default_cache.set(
                cache_key,
                recommendations,
                timeout=cache_timeout
            )
            
            logger.debug(
                "Interest recommendations cached",
                user_id=user_id,
                recommendations_count=len(recommendations)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to cache interest recommendations",
                user_id=user_id,
                error=str(e)
            )
            return False
    
    def invalidate_interest_cache(self, user_id: int) -> bool:
        """
        Invalidate cached interest data for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Success status
        """
        try:
            cache_key = self._generate_cache_key("interest_recommendations", user_id)
            self.default_cache.delete(cache_key)
            
            logger.debug(
                "Interest cache invalidated",
                user_id=user_id
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to invalidate interest cache",
                user_id=user_id,
                error=str(e)
            )
            return False
    
    # Utility Methods
    def _serialize_feed_items(self, items: List[Any]) -> List[Dict[str, Any]]:
        """
        Serialize feed items for caching.
        
        Args:
            items: Feed items to serialize
        
        Returns:
            Serialized items
        """
        serialized = []
        
        for item in items:
            try:
                if isinstance(item, dict):
                    # Already serialized
                    serialized.append(item)
                else:
                    # Serialize model instance
                    serialized_item = {
                        'id': str(item.id),
                        'content_type': item.__class__.__name__.lower(),
                        'title': getattr(item, 'title', ''),
                        'creator_id': getattr(item, 'creator_id', None),
                        'engagement_score': getattr(item, 'engagement_score', 0),
                        'trending_score': getattr(item, 'trending_score', 0),
                        'published_at': getattr(item, 'published_at', timezone.now()).isoformat(),
                        'cached_at': timezone.now().isoformat()
                    }
                    serialized.append(serialized_item)
            except Exception as e:
                logger.warning(
                    "Failed to serialize feed item",
                    item_type=type(item).__name__,
                    error=str(e)
                )
                continue
        
        return serialized
    
    def clear_all_user_caches(self, user_id: int) -> bool:
        """
        Clear all cached data for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Success status
        """
        try:
            success = True
            
            # Clear user feed
            success &= self.invalidate_user_feed(user_id)
            
            # Clear connection circles
            success &= self.invalidate_connection_cache(user_id)
            
            # Clear interest recommendations
            success &= self.invalidate_interest_cache(user_id)
            
            logger.info(
                "All user caches cleared",
                user_id=user_id,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error(
                "Failed to clear all user caches",
                user_id=user_id,
                error=str(e)
            )
            return False


class CacheMonitor:
    """
    Monitors cache performance and provides analytics.
    """
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.
        
        Returns:
            Cache statistics dictionary
        """
        try:
            info = self.redis_client.info()
            
            stats = {
                'redis_info': {
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'total_commands_processed': info.get('total_commands_processed'),
                    'keyspace_hits': info.get('keyspace_hits'),
                    'keyspace_misses': info.get('keyspace_misses'),
                },
                'cache_databases': {}
            }
            
            # Get keyspace info for each database
            for key, value in info.items():
                if key.startswith('db'):
                    stats['cache_databases'][key] = value
            
            # Calculate hit rate
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total_requests = hits + misses
            
            if total_requests > 0:
                stats['hit_rate_percent'] = (hits / total_requests) * 100
            else:
                stats['hit_rate_percent'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'error': str(e)}
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get detailed memory usage information.
        
        Returns:
            Memory usage statistics
        """
        try:
            memory_info = self.redis_client.memory_usage_stats()
            return {
                'total_system_memory': memory_info.get('total.allocated'),
                'used_memory': memory_info.get('dataset.bytes'),
                'memory_fragmentation_ratio': memory_info.get('fragmentation'),
                'memory_efficiency': memory_info.get('efficiency'),
            }
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {'error': str(e)}
    
    def get_key_patterns(self, pattern: str = "*") -> List[str]:
        """
        Get cache keys matching a pattern.
        
        Args:
            pattern: Redis key pattern
        
        Returns:
            List of matching keys
        """
        try:
            keys = self.redis_client.keys(pattern)
            return [key.decode('utf-8') for key in keys]
        except Exception as e:
            logger.error(f"Failed to get key patterns: {e}")
            return []


# Utility functions
def test_redis_connections() -> bool:
    """
    Test all Redis cache connections.
    
    Returns:
        True if all connections are working
    """
    try:
        # Test default cache
        cache.set('test_key', 'test_value', 10)
        if cache.get('test_key') != 'test_value':
            raise Exception("Default cache test failed")
        cache.delete('test_key')
        
        # Test feed cache
        feed_cache = caches['feed_cache']
        feed_cache.set('test_feed_key', 'test_value', 10)
        if feed_cache.get('test_feed_key') != 'test_value':
            raise Exception("Feed cache test failed")
        feed_cache.delete('test_feed_key')
        
        # Test trending cache
        trending_cache = caches['trending_cache']
        trending_cache.set('test_trending_key', 'test_value', 10)
        if trending_cache.get('test_trending_key') != 'test_value':
            raise Exception("Trending cache test failed")
        trending_cache.delete('test_trending_key')
        
        logger.info("All Redis cache connections tested successfully")
        return True
        
    except Exception as e:
        logger.error(f"Redis connection test failed: {e}")
        return False


def warm_cache_for_user(user_id: int) -> bool:
    """
    Pre-warm cache for a user.
    
    Args:
        user_id: User ID to warm cache for
    
    Returns:
        Success status
    """
    try:
        from feed_algorithm.models import UserProfile
        from feed_algorithm.services import FeedGenerationService
        
        # Get user profile
        user_profile = UserProfile.objects.get(user_id=user_id)
        
        # Generate and cache feed
        feed_service = FeedGenerationService(user_profile)
        feed_items = feed_service.generate_feed(size=20)
        
        # Cache will be set automatically by the service
        logger.info(f"Cache warmed for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to warm cache for user {user_id}: {e}")
        return False


def clear_all_caches() -> bool:
    """
    Clear all application caches.
    
    Returns:
        Success status
    """
    try:
        cache.clear()
        caches['feed_cache'].clear()
        caches['trending_cache'].clear()
        
        logger.info("All caches cleared")
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear all caches: {e}")
        return False
