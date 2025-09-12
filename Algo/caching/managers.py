"""Redis caching utilities and managers for the feed algorithm system."""

from typing import Dict, List, Any, Optional, Union
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import json
import hashlib
import structlog

logger = structlog.get_logger(__name__)


class CacheManager:
    """Base cache manager with common functionality."""
    
    def __init__(self, prefix: str, default_ttl: int = 3600):
        self.prefix = prefix
        self.default_ttl = default_ttl
    
    def _make_key(self, key: str) -> str:
        """Create a cache key with prefix."""
        return f"{self.prefix}:{key}"
    
    def get(self, key: str, default=None):
        """Get value from cache."""
        cache_key = self._make_key(key)
        try:
            value = cache.get(cache_key, default)
            if value is not None:
                logger.debug("Cache hit", key=cache_key)
            else:
                logger.debug("Cache miss", key=cache_key)
            return value
        except Exception as e:
            logger.error("Cache get error", key=cache_key, error=str(e))
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        cache_key = self._make_key(key)
        ttl = ttl or self.default_ttl
        
        try:
            cache.set(cache_key, value, ttl)
            logger.debug("Cache set", key=cache_key, ttl=ttl)
            return True
        except Exception as e:
            logger.error("Cache set error", key=cache_key, error=str(e))
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        cache_key = self._make_key(key)
        try:
            cache.delete(cache_key)
            logger.debug("Cache delete", key=cache_key)
            return True
        except Exception as e:
            logger.error("Cache delete error", key=cache_key, error=str(e))
            return False
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        cache_keys = [self._make_key(key) for key in keys]
        try:
            result = cache.get_many(cache_keys)
            # Convert back to original keys
            return {
                key: result.get(self._make_key(key))
                for key in keys
            }
        except Exception as e:
            logger.error("Cache get_many error", keys=cache_keys, error=str(e))
            return {}
    
    def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        cache_data = {
            self._make_key(key): value
            for key, value in data.items()
        }
        ttl = ttl or self.default_ttl
        
        try:
            cache.set_many(cache_data, ttl)
            logger.debug("Cache set_many", count=len(cache_data), ttl=ttl)
            return True
        except Exception as e:
            logger.error("Cache set_many error", error=str(e))
            return False
    
    def delete_many(self, keys: List[str]) -> bool:
        """Delete multiple values from cache."""
        cache_keys = [self._make_key(key) for key in keys]
        try:
            cache.delete_many(cache_keys)
            logger.debug("Cache delete_many", count=len(cache_keys))
            return True
        except Exception as e:
            logger.error("Cache delete_many error", error=str(e))
            return False
    
    def clear_prefix(self) -> bool:
        """Clear all keys with this prefix (Redis specific)."""
        try:
            # This requires django-redis and direct Redis access
            from django_redis import get_redis_connection
            
            redis_conn = get_redis_connection("default")
            pattern = f"{self.prefix}:*"
            
            # Get all keys matching pattern
            keys = redis_conn.keys(pattern)
            
            if keys:
                redis_conn.delete(*keys)
                logger.info("Cache prefix cleared", prefix=self.prefix, count=len(keys))
            
            return True
        except Exception as e:
            logger.error("Cache clear_prefix error", prefix=self.prefix, error=str(e))
            return False


class FeedCacheManager(CacheManager):
    """Cache manager specifically for user feeds."""
    
    def __init__(self):
        feed_ttl = getattr(settings, 'FEED_CONFIG', {}).get(
            'CACHE_SETTINGS', {}
        ).get('FEED_CACHE_TTL', 1800)
        
        super().__init__(prefix='feed', default_ttl=feed_ttl)
    
    def get_user_feed(self, user_id: int, page: int = 1) -> Optional[Dict[str, Any]]:
        """Get cached user feed."""
        key = f"user:{user_id}:page:{page}"
        return self.get(key)
    
    def set_user_feed(self, user_id: int, feed_data: Dict[str, Any], page: int = 1) -> bool:
        """Cache user feed."""
        key = f"user:{user_id}:page:{page}"
        
        # Add timestamp for cache validation
        feed_data['cached_at'] = timezone.now().isoformat()
        
        return self.set(key, feed_data)
    
    def invalidate_user_feed(self, user_id: int) -> bool:
        """Invalidate all cached pages for a user's feed."""
        # Clear first few pages (most commonly accessed)
        keys_to_delete = [f"user:{user_id}:page:{page}" for page in range(1, 6)]
        return self.delete_many(keys_to_delete)
    
    def get_global_trending(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached global trending content."""
        return self.get('global_trending')
    
    def set_global_trending(self, trending_data: List[Dict[str, Any]]) -> bool:
        """Cache global trending content."""
        trending_ttl = getattr(settings, 'FEED_CONFIG', {}).get(
            'CACHE_SETTINGS', {}
        ).get('TRENDING_CACHE_TTL', 300)
        
        return self.set('global_trending', trending_data, ttl=trending_ttl)
    
    def get_feed_composition(self, user_id: int) -> Optional[Dict[str, float]]:
        """Get cached user feed composition."""
        key = f"composition:{user_id}"
        return self.get(key)
    
    def set_feed_composition(self, user_id: int, composition: Dict[str, float]) -> bool:
        """Cache user feed composition."""
        key = f"composition:{user_id}"
        # Composition changes less frequently, cache longer
        return self.set(key, composition, ttl=3600)


class ContentCacheManager(CacheManager):
    """Cache manager for content-related data."""
    
    def __init__(self):
        super().__init__(prefix='content', default_ttl=1800)
    
    def get_content_score(self, content_type: str, content_id: str, user_id: Optional[int] = None) -> Optional[float]:
        """Get cached content score."""
        if user_id:
            key = f"score:{content_type}:{content_id}:user:{user_id}"
        else:
            key = f"score:{content_type}:{content_id}:global"
        
        return self.get(key)
    
    def set_content_score(
        self, 
        content_type: str, 
        content_id: str, 
        score: float, 
        user_id: Optional[int] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache content score."""
        if user_id:
            key = f"score:{content_type}:{content_id}:user:{user_id}"
        else:
            key = f"score:{content_type}:{content_id}:global"
        
        return self.set(key, score, ttl)
    
    def get_trending_content(self, content_type: str) -> Optional[List[str]]:
        """Get cached trending content IDs for a content type."""
        key = f"trending:{content_type}"
        return self.get(key)
    
    def set_trending_content(self, content_type: str, content_ids: List[str]) -> bool:
        """Cache trending content IDs."""
        key = f"trending:{content_type}"
        trending_ttl = getattr(settings, 'FEED_CONFIG', {}).get(
            'CACHE_SETTINGS', {}
        ).get('TRENDING_CACHE_TTL', 300)
        
        return self.set(key, content_ids, ttl=trending_ttl)
    
    def get_content_engagements(self, content_type: str, content_id: str) -> Optional[Dict[str, int]]:
        """Get cached content engagement counts."""
        key = f"engagements:{content_type}:{content_id}"
        return self.get(key)
    
    def set_content_engagements(
        self, 
        content_type: str, 
        content_id: str, 
        engagements: Dict[str, int]
    ) -> bool:
        """Cache content engagement counts."""
        key = f"engagements:{content_type}:{content_id}"
        return self.set(key, engagements, ttl=600)  # 10 minutes for engagement counts


class UserCacheManager(CacheManager):
    """Cache manager for user-related data."""
    
    def __init__(self):
        connection_ttl = getattr(settings, 'FEED_CONFIG', {}).get(
            'CACHE_SETTINGS', {}
        ).get('CONNECTION_CACHE_TTL', 3600)
        
        super().__init__(prefix='user', default_ttl=connection_ttl)
    
    def get_user_connections(self, user_id: int) -> Optional[Dict[str, List[int]]]:
        """Get cached user connections by circle type."""
        key = f"connections:{user_id}"
        return self.get(key)
    
    def set_user_connections(self, user_id: int, connections: Dict[str, List[int]]) -> bool:
        """Cache user connections."""
        key = f"connections:{user_id}"
        return self.set(key, connections)
    
    def get_user_interests(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached user interests."""
        key = f"interests:{user_id}"
        return self.get(key)
    
    def set_user_interests(self, user_id: int, interests: List[Dict[str, Any]]) -> bool:
        """Cache user interests."""
        key = f"interests:{user_id}"
        return self.set(key, interests)
    
    def get_user_scoring_weights(self, user_id: int) -> Optional[Dict[str, float]]:
        """Get cached user scoring weights."""
        key = f"scoring_weights:{user_id}"
        return self.get(key)
    
    def set_user_scoring_weights(self, user_id: int, weights: Dict[str, float]) -> bool:
        """Cache user scoring weights."""
        key = f"scoring_weights:{user_id}"
        return self.set(key, weights)
    
    def get_creator_metrics(self, user_id: int) -> Optional[Dict[str, float]]:
        """Get cached creator metrics."""
        key = f"creator_metrics:{user_id}"
        return self.get(key)
    
    def set_creator_metrics(self, user_id: int, metrics: Dict[str, float]) -> bool:
        """Cache creator metrics."""
        key = f"creator_metrics:{user_id}"
        return self.set(key, metrics, ttl=1800)  # 30 minutes for creator metrics


class CacheKeyGenerator:
    """Utility for generating consistent cache keys."""
    
    @staticmethod
    def hash_key(data: Union[str, Dict, List]) -> str:
        """Generate a hash from data for cache key."""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)
        
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    @staticmethod
    def feed_key(user_id: int, composition: Dict[str, float], page: int = 1) -> str:
        """Generate cache key for user feed."""
        comp_hash = CacheKeyGenerator.hash_key(composition)
        return f"feed:user:{user_id}:comp:{comp_hash}:page:{page}"
    
    @staticmethod
    def recommendation_key(user_id: int, content_type: str, limit: int) -> str:
        """Generate cache key for user recommendations."""
        return f"rec:user:{user_id}:type:{content_type}:limit:{limit}"
    
    @staticmethod
    def search_key(query: str, filters: Dict[str, Any]) -> str:
        """Generate cache key for search results."""
        query_hash = CacheKeyGenerator.hash_key(query)
        filters_hash = CacheKeyGenerator.hash_key(filters)
        return f"search:q:{query_hash}:f:{filters_hash}"


class CacheWarmer:
    """Cache warming utilities for proactive cache population."""
    
    def __init__(self):
        self.feed_cache = FeedCacheManager()
        self.content_cache = ContentCacheManager()
        self.user_cache = UserCacheManager()
    
    def warm_popular_feeds(self, user_ids: List[int]) -> Dict[str, int]:
        """Warm cache for popular/active users' feeds."""
        results = {'success': 0, 'error': 0}
        
        for user_id in user_ids:
            try:
                # This would normally call the feed generation service
                # For now, we'll just ensure the cache keys exist
                
                from feed_algorithm.services import FeedGenerationService
                
                service = FeedGenerationService()
                feed_data = service.generate_feed(user_id, page=1, use_cache=False)
                
                if feed_data:
                    self.feed_cache.set_user_feed(user_id, feed_data)
                    results['success'] += 1
                else:
                    results['error'] += 1
                    
            except Exception as e:
                logger.error(
                    "Error warming feed cache",
                    user_id=user_id,
                    error=str(e)
                )
                results['error'] += 1
        
        logger.info(
            "Feed cache warming completed",
            **results,
            total_users=len(user_ids)
        )
        
        return results
    
    def warm_trending_content(self) -> Dict[str, int]:
        """Warm cache for trending content across all content types."""
        from content_types.registry import registry as content_registry
        from scoring_engines.models import TrendingMetric
        
        results = {'success': 0, 'error': 0}
        
        for content_type_name in content_registry.get_all_content_types().keys():
            try:
                # Get trending content IDs for this type
                trending_metrics = TrendingMetric.objects.filter(
                    metric_type='content',
                    trending_score__gte=0.5
                ).order_by('-trending_score')[:50]
                
                # Extract content IDs for this content type
                content_ids = []
                for metric in trending_metrics:
                    if metric.metric_id.startswith(f"{content_type_name}:"):
                        content_id = metric.metric_id.split(':', 1)[1]
                        content_ids.append(content_id)
                
                if content_ids:
                    self.content_cache.set_trending_content(content_type_name, content_ids)
                    results['success'] += 1
                
            except Exception as e:
                logger.error(
                    "Error warming trending content cache",
                    content_type=content_type_name,
                    error=str(e)
                )
                results['error'] += 1
        
        return results
    
    def warm_user_data(self, user_ids: List[int]) -> Dict[str, int]:
        """Warm cache for user-related data."""
        from users.models import Connection, UserInterest
        from scoring_engines.utils import get_personalized_weights
        
        results = {'success': 0, 'error': 0}
        
        for user_id in user_ids:
            try:
                # Cache user connections
                connections = Connection.objects.filter(
                    from_user_id=user_id,
                    status='accepted'
                ).values('to_user_id', 'circle_type')
                
                connection_data = {
                    'inner': [],
                    'outer': [],
                    'universe': []
                }
                
                for conn in connections:
                    circle_type = conn['circle_type']
                    if circle_type in connection_data:
                        connection_data[circle_type].append(conn['to_user_id'])
                
                self.user_cache.set_user_connections(user_id, connection_data)
                
                # Cache user interests
                interests = UserInterest.objects.filter(
                    user_id=user_id
                ).select_related('interest').values(
                    'interest__name',
                    'interest__category',
                    'strength',
                    'interest_type'
                )
                
                interest_data = list(interests)
                self.user_cache.set_user_interests(user_id, interest_data)
                
                # Cache user scoring weights
                from users.models import UserProfile
                user = UserProfile.objects.get(id=user_id)
                weights = get_personalized_weights(user)
                self.user_cache.set_user_scoring_weights(user_id, weights)
                
                results['success'] += 1
                
            except Exception as e:
                logger.error(
                    "Error warming user data cache",
                    user_id=user_id,
                    error=str(e)
                )
                results['error'] += 1
        
        return results


# Global cache manager instances
feed_cache = FeedCacheManager()
content_cache = ContentCacheManager()
user_cache = UserCacheManager()
cache_warmer = CacheWarmer()