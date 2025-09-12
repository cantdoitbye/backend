from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .managers import feed_cache, content_cache, user_cache
import structlog

logger = structlog.get_logger(__name__)


@receiver(post_save, sender='users.UserProfile')
def user_profile_cache_invalidation(sender, instance, created, **kwargs):
    """Invalidate user-related caches when profile is updated."""
    if not created:
        # Clear user's feed and data caches
        feed_cache.invalidate_user_feed(instance.id)
        user_cache.delete(f"scoring_weights:{instance.id}")
        user_cache.delete(f"creator_metrics:{instance.id}")
        
        logger.debug(
            "User profile cache invalidated",
            user_id=instance.id
        )


@receiver(post_save, sender='users.Connection')
@receiver(post_delete, sender='users.Connection')
def connection_cache_invalidation(sender, instance, **kwargs):
    """Invalidate connection-related caches."""
    # Clear both users' connection and feed caches
    user_ids = [instance.from_user_id, instance.to_user_id]
    
    for user_id in user_ids:
        user_cache.delete(f"connections:{user_id}")
        feed_cache.invalidate_user_feed(user_id)
    
    logger.debug(
        "Connection cache invalidated",
        from_user=instance.from_user_id,
        to_user=instance.to_user_id
    )


@receiver(post_save, sender='users.UserInterest')
@receiver(post_delete, sender='users.UserInterest')
def user_interest_cache_invalidation(sender, instance, **kwargs):
    """Invalidate interest-related caches."""
    user_cache.delete(f"interests:{instance.user_id}")
    user_cache.delete(f"scoring_weights:{instance.user_id}")
    feed_cache.invalidate_user_feed(instance.user_id)
    
    logger.debug(
        "User interest cache invalidated",
        user_id=instance.user_id,
        interest=instance.interest.name if hasattr(instance, 'interest') else 'unknown'
    )


@receiver(post_save, sender='scoring_engines.UserScoringPreference')
def scoring_preference_cache_invalidation(sender, instance, **kwargs):
    """Invalidate scoring-related caches when preferences change."""
    user_cache.delete(f"scoring_weights:{instance.user_id}")
    feed_cache.invalidate_user_feed(instance.user_id)
    
    logger.debug(
        "User scoring preference cache invalidated",
        user_id=instance.user_id
    )


@receiver(post_save, sender='scoring_engines.CreatorMetric')
def creator_metric_cache_invalidation(sender, instance, **kwargs):
    """Invalidate creator metric caches."""
    user_cache.delete(f"creator_metrics:{instance.creator_id}")
    
    # Clear content scores for this creator's content
    try:
        from content_types.registry import registry as content_registry
        
        for content_type_name, model_class in content_registry.get_all_content_types().items():
            # This is a simplified approach - in production, you might want to be more specific
            content_cache.clear_prefix()
            break  # Clear all content cache since creator reputation affects all scoring
    
    except Exception as e:
        logger.error(
            "Error clearing content cache for creator metric update",
            creator_id=instance.creator_id,
            error=str(e)
        )
    
    logger.debug(
        "Creator metric cache invalidated",
        creator_id=instance.creator_id
    )


@receiver(post_save, sender='scoring_engines.TrendingMetric')
def trending_metric_cache_invalidation(sender, instance, **kwargs):
    """Invalidate trending-related caches."""
    # Clear trending content caches
    if instance.metric_type == 'content':
        # Extract content type from metric_id
        if ':' in instance.metric_id:
            content_type = instance.metric_id.split(':', 1)[0]
            content_cache.delete(f"trending:{content_type}")
    
    # Clear global trending cache
    feed_cache.delete('global_trending')
    
    logger.debug(
        "Trending metric cache invalidated",
        metric_type=instance.metric_type,
        metric_id=instance.metric_id
    )


@receiver(post_save, sender='content_types.Post')
@receiver(post_save, sender='content_types.Community')
@receiver(post_save, sender='content_types.Product')
def content_cache_invalidation(sender, instance, created, **kwargs):
    """Invalidate content-related caches when content is updated."""
    content_type = sender.__name__.lower()
    
    # Clear content score caches
    content_cache.delete(f"score:{content_type}:{instance.id}:global")
    
    # Clear engagement caches
    content_cache.delete(f"engagements:{content_type}:{instance.id}")
    
    # If this is a new post, clear trending caches as it might affect trending
    if created:
        content_cache.delete(f"trending:{content_type}")
        feed_cache.delete('global_trending')
    
    # Clear creator's feed cache and followers' feed caches
    if hasattr(instance, 'creator'):
        feed_cache.invalidate_user_feed(instance.creator_id)
        
        # Clear feeds for users who follow this creator
        try:
            from users.models import Connection
            
            follower_ids = Connection.objects.filter(
                to_user=instance.creator,
                status='accepted'
            ).values_list('from_user_id', flat=True)[:100]  # Limit for performance
            
            for follower_id in follower_ids:
                feed_cache.invalidate_user_feed(follower_id)
        
        except Exception as e:
            logger.error(
                "Error clearing follower feed caches",
                content_id=instance.id,
                creator_id=instance.creator_id,
                error=str(e)
            )
    
    logger.debug(
        "Content cache invalidated",
        content_type=content_type,
        content_id=instance.id,
        created=created
    )


@receiver(post_save, sender='content_types.Engagement')
def engagement_cache_invalidation(sender, instance, created, **kwargs):
    """Invalidate engagement-related caches."""
    if created:
        content = instance.content_object
        if content:
            content_type = content.__class__.__name__.lower()
            
            # Clear engagement count cache
            content_cache.delete(f"engagements:{content_type}:{content.id}")
            
            # Clear content score caches (engagement affects scoring)
            content_cache.delete(f"score:{content_type}:{content.id}:global")
            content_cache.delete(f"score:{content_type}:{content.id}:user:{instance.user_id}")
            
            # Clear user's feed cache
            feed_cache.invalidate_user_feed(instance.user_id)
            
            logger.debug(
                "Engagement cache invalidated",
                content_type=content_type,
                content_id=content.id,
                user_id=instance.user_id,
                engagement_type=instance.engagement_type
            )


@receiver(post_save, sender='content_types.CommunityMembership')
@receiver(post_delete, sender='content_types.CommunityMembership')
def community_membership_cache_invalidation(sender, instance, **kwargs):
    """Invalidate community-related caches."""
    # Clear user's community data and feed cache
    feed_cache.invalidate_user_feed(instance.user_id)
    
    # Clear community member count cache if needed
    # This might be handled by other cache mechanisms
    
    logger.debug(
        "Community membership cache invalidated",
        community_id=instance.community_id,
        user_id=instance.user_id
    )