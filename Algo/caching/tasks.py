"""Celery tasks for cache management and warming."""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .managers import cache_warmer, feed_cache, content_cache, user_cache
import structlog

logger = structlog.get_logger(__name__)


@shared_task
def warmup_popular_feeds():
    """Warm up cache for popular/active users' feeds."""
    try:
        from users.models import UserProfile
        from django.db.models import F
        
        # Get users who have been active in the last 24 hours
        # or have high engagement scores
        since = timezone.now() - timedelta(hours=24)
        
        popular_users = UserProfile.objects.filter(
            Q(last_active__gte=since) | Q(engagement_score__gte=5.0)
        ).order_by('-engagement_score', '-last_active')[:100]  # Top 100 users
        
        user_ids = list(popular_users.values_list('id', flat=True))
        
        if user_ids:
            results = cache_warmer.warm_popular_feeds(user_ids)
            
            logger.info(
                "Popular feeds cache warmup completed",
                **results,
                user_count=len(user_ids)
            )
            
            return {
                'success': True,
                'user_count': len(user_ids),
                'results': results
            }
        else:
            return {
                'success': True,
                'user_count': 0,
                'message': 'No popular users found'
            }
    
    except Exception as e:
        logger.error(
            "Error in popular feeds cache warmup task",
            error=str(e)
        )
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def warmup_trending_content():
    """Warm up cache for trending content."""
    try:
        results = cache_warmer.warm_trending_content()
        
        logger.info(
            "Trending content cache warmup completed",
            **results
        )
        
        return {
            'success': True,
            'results': results
        }
    
    except Exception as e:
        logger.error(
            "Error in trending content cache warmup task",
            error=str(e)
        )
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def warmup_user_data():
    """Warm up cache for user-related data."""
    try:
        from users.models import UserProfile
        
        # Get recently active users
        since = timezone.now() - timedelta(hours=6)
        
        active_users = UserProfile.objects.filter(
            last_active__gte=since
        ).values_list('id', flat=True)[:200]  # Top 200 active users
        
        user_ids = list(active_users)
        
        if user_ids:
            results = cache_warmer.warm_user_data(user_ids)
            
            logger.info(
                "User data cache warmup completed",
                **results,
                user_count=len(user_ids)
            )
            
            return {
                'success': True,
                'user_count': len(user_ids),
                'results': results
            }
        else:
            return {
                'success': True,
                'user_count': 0,
                'message': 'No active users found'
            }
    
    except Exception as e:
        logger.error(
            "Error in user data cache warmup task",
            error=str(e)
        )
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def cleanup_stale_cache_entries():
    """Clean up stale or expired cache entries."""
    try:
        from django_redis import get_redis_connection
        
        redis_conn = get_redis_connection("default")
        
        # Get cache statistics before cleanup
        info_before = redis_conn.info('memory')
        used_memory_before = info_before.get('used_memory', 0)
        
        # Clean up different cache prefixes
        prefixes_to_clean = ['feed:', 'content:', 'user:']
        total_deleted = 0
        
        for prefix in prefixes_to_clean:
            try:
                # Get keys matching pattern
                pattern = f"{prefix}*"
                keys = redis_conn.keys(pattern)
                
                if keys:
                    # Check which keys have expired or are very old
                    # This is a simplified cleanup - in production you might want more sophisticated logic
                    pipeline = redis_conn.pipeline()
                    
                    for key in keys:
                        ttl = redis_conn.ttl(key)
                        # If TTL is very low or key is set to expire soon, delete it
                        if ttl < 300:  # Less than 5 minutes remaining
                            pipeline.delete(key)
                            total_deleted += 1
                    
                    pipeline.execute()
            
            except Exception as e:
                logger.error(
                    "Error cleaning cache prefix",
                    prefix=prefix,
                    error=str(e)
                )
        
        # Get cache statistics after cleanup
        info_after = redis_conn.info('memory')
        used_memory_after = info_after.get('used_memory', 0)
        memory_freed = used_memory_before - used_memory_after
        
        logger.info(
            "Cache cleanup completed",
            total_deleted=total_deleted,
            memory_freed_bytes=memory_freed,
            used_memory_before=used_memory_before,
            used_memory_after=used_memory_after
        )
        
        return {
            'success': True,
            'total_deleted': total_deleted,
            'memory_freed_bytes': memory_freed
        }
    
    except Exception as e:
        logger.error(
            "Error in cache cleanup task",
            error=str(e)
        )
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def refresh_global_caches():
    """Refresh global caches that are shared across all users."""
    try:
        refresh_count = 0
        
        # Refresh global trending content
        try:
            from scoring_engines.models import TrendingMetric
            
            # Get top trending content across all types
            trending_content = TrendingMetric.objects.filter(
                metric_type='content',
                trending_score__gte=0.3
            ).order_by('-trending_score')[:100]
            
            trending_data = []
            for metric in trending_content:
                trending_data.append({
                    'metric_id': metric.metric_id,
                    'trending_score': metric.trending_score,
                    'velocity_score': metric.velocity_score,
                    'engagement_volume': metric.engagement_volume
                })
            
            if trending_data:
                feed_cache.set_global_trending(trending_data)
                refresh_count += 1
        
        except Exception as e:
            logger.error(
                "Error refreshing global trending cache",
                error=str(e)
            )
        
        # Refresh content type trending caches
        try:
            from content_types.registry import registry as content_registry
            
            for content_type_name in content_registry.get_all_content_types().keys():
                # Get trending content for this type
                trending_metrics = TrendingMetric.objects.filter(
                    metric_type='content',
                    trending_score__gte=0.4
                ).order_by('-trending_score')[:50]
                
                content_ids = []
                for metric in trending_metrics:
                    if metric.metric_id.startswith(f"{content_type_name}:"):
                        content_id = metric.metric_id.split(':', 1)[1]
                        content_ids.append(content_id)
                
                if content_ids:
                    content_cache.set_trending_content(content_type_name, content_ids)
                    refresh_count += 1
        
        except Exception as e:
            logger.error(
                "Error refreshing content type trending caches",
                error=str(e)
            )
        
        logger.info(
            "Global caches refresh completed",
            refresh_count=refresh_count
        )
        
        return {
            'success': True,
            'refresh_count': refresh_count
        }
    
    except Exception as e:
        logger.error(
            "Error in global caches refresh task",
            error=str(e)
        )
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def cache_performance_monitoring():
    """Monitor cache performance and generate metrics."""
    try:
        from django_redis import get_redis_connection
        
        redis_conn = get_redis_connection("default")
        
        # Get Redis info
        info = redis_conn.info()
        
        # Calculate hit ratio
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total_requests = hits + misses
        
        hit_ratio = (hits / total_requests * 100) if total_requests > 0 else 0
        
        # Get memory usage
        used_memory = info.get('used_memory', 0)
        used_memory_peak = info.get('used_memory_peak', 0)
        
        # Get key count by prefix
        key_counts = {}
        prefixes = ['feed:', 'content:', 'user:']
        
        for prefix in prefixes:
            pattern = f"{prefix}*"
            keys = redis_conn.keys(pattern)
            key_counts[prefix.rstrip(':')] = len(keys)
        
        metrics = {
            'hit_ratio_percent': hit_ratio,
            'total_requests': total_requests,
            'hits': hits,
            'misses': misses,
            'used_memory_bytes': used_memory,
            'used_memory_peak_bytes': used_memory_peak,
            'key_counts': key_counts,
            'connected_clients': info.get('connected_clients', 0)
        }
        
        # Log performance metrics
        from analytics.utils import log_cache_event
        
        log_cache_event(
            event_type='cache_performance_metrics',
            metadata=metrics
        )
        
        logger.info(
            "Cache performance metrics collected",
            **metrics
        )
        
        return {
            'success': True,
            'metrics': metrics
        }
    
    except Exception as e:
        logger.error(
            "Error in cache performance monitoring task",
            error=str(e)
        )
        return {
            'success': False,
            'error': str(e)
        }