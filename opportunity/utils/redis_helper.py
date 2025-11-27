"""
Redis helper functions for opportunity engagement caching.
Mirrors post Redis services for consistency.
"""

from django.core.cache import cache


def increment_opportunity_like_count(opportunity_uid):
    """Increment like count for an opportunity in Redis cache"""
    cache_key = f"opportunity:{opportunity_uid}:like_count"
    try:
        count = cache.get(cache_key, 0)
        cache.set(cache_key, count + 1, timeout=3600)  # 1 hour cache
        return count + 1
    except Exception as e:
        print(f"Error incrementing opportunity like count: {e}")
        return 0


def increment_opportunity_comment_count(opportunity_uid):
    """Increment comment count for an opportunity in Redis cache"""
    cache_key = f"opportunity:{opportunity_uid}:comment_count"
    try:
        count = cache.get(cache_key, 0)
        cache.set(cache_key, count + 1, timeout=3600)
        return count + 1
    except Exception as e:
        print(f"Error incrementing opportunity comment count: {e}")
        return 0


def increment_opportunity_share_count(opportunity_uid):
    """Increment share count for an opportunity in Redis cache"""
    cache_key = f"opportunity:{opportunity_uid}:share_count"
    try:
        count = cache.get(cache_key, 0)
        cache.set(cache_key, count + 1, timeout=3600)
        return count + 1
    except Exception as e:
        print(f"Error incrementing opportunity share count: {e}")
        return 0


def increment_opportunity_view_count(opportunity_uid):
    """Increment view count for an opportunity in Redis cache"""
    cache_key = f"opportunity:{opportunity_uid}:view_count"
    try:
        count = cache.get(cache_key, 0)
        cache.set(cache_key, count + 1, timeout=3600)
        return count + 1
    except Exception as e:
        print(f"Error incrementing opportunity view count: {e}")
        return 0


def get_opportunity_engagement_counts(opportunity_uid):
    """
    Get all engagement counts for an opportunity from Redis cache.
    Returns dict with like_count, comment_count, share_count, view_count.
    """
    try:
        return {
            'like_count': cache.get(f"opportunity:{opportunity_uid}:like_count", 0),
            'comment_count': cache.get(f"opportunity:{opportunity_uid}:comment_count", 0),
            'share_count': cache.get(f"opportunity:{opportunity_uid}:share_count", 0),
            'view_count': cache.get(f"opportunity:{opportunity_uid}:view_count", 0),
        }
    except Exception as e:
        print(f"Error getting opportunity engagement counts: {e}")
        return {
            'like_count': 0,
            'comment_count': 0,
            'share_count': 0,
            'view_count': 0,
        }


def clear_opportunity_engagement_cache(opportunity_uid):
    """Clear all engagement counts for an opportunity from Redis cache"""
    try:
        cache.delete(f"opportunity:{opportunity_uid}:like_count")
        cache.delete(f"opportunity:{opportunity_uid}:comment_count")
        cache.delete(f"opportunity:{opportunity_uid}:share_count")
        cache.delete(f"opportunity:{opportunity_uid}:view_count")
        return True
    except Exception as e:
        print(f"Error clearing opportunity engagement cache: {e}")
        return False