from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.db import models
from .models import (
    ScoringFactor, UserScoringPreference, ContentScore,
    TrendingMetric, CreatorMetric
)
from analytics.utils import log_scoring_event
import structlog

logger = structlog.get_logger(__name__)


@receiver(post_save, sender=ScoringFactor)
def scoring_factor_updated(sender, instance, created, **kwargs):
    """Handle scoring factor updates."""
    if created:
        log_scoring_event(
            event_type='scoring_factor_created',
            metadata={
                'factor_name': instance.name,
                'factor_type': instance.factor_type,
                'weight': instance.weight
            }
        )
        logger.info(
            "Scoring factor created",
            factor_name=instance.name,
            factor_type=instance.factor_type,
            weight=instance.weight
        )
    else:
        log_scoring_event(
            event_type='scoring_factor_updated',
            metadata={
                'factor_name': instance.name,
                'updated_fields': list(kwargs.get('update_fields', []))
            }
        )
    
    # Clear scoring-related caches
    cache.delete_many([
        'scoring_factors',
        'default_scoring_config',
        'active_scoring_factors'
    ])
    
    # Clear all user feed caches since scoring has changed
    cache.delete_pattern('user_feed:*')


@receiver(post_save, sender=UserScoringPreference)
def user_scoring_preference_updated(sender, instance, created, **kwargs):
    """Handle user scoring preference updates."""
    if created:
        log_scoring_event(
            event_type='user_scoring_preference_created',
            user_id=instance.user_id,
            metadata={'algorithm_variant': instance.algorithm_variant}
        )
        logger.info(
            "User scoring preferences created",
            user_id=instance.user_id,
            algorithm_variant=instance.algorithm_variant
        )
    else:
        log_scoring_event(
            event_type='user_scoring_preference_updated',
            user_id=instance.user_id,
            metadata={
                'updated_fields': list(kwargs.get('update_fields', [])),
                'algorithm_variant': instance.algorithm_variant
            }
        )
    
    # Clear user-specific caches
    cache.delete_many([
        f'user_scoring_weights:{instance.user_id}',
        f'user_feed:{instance.user_id}',
        f'user_personalized_scores:{instance.user_id}'
    ])


@receiver(post_save, sender=ContentScore)
def content_score_updated(sender, instance, created, **kwargs):
    """Handle content score updates."""
    if created:
        log_scoring_event(
            event_type='content_score_calculated',
            user_id=instance.user_id if instance.user else None,
            metadata={
                'content_type': instance.content_type,
                'content_id': str(instance.content_id),
                'final_score': instance.final_score,
                'algorithm_version': instance.algorithm_version
            }
        )
        
        logger.debug(
            "Content score calculated",
            content_type=instance.content_type,
            content_id=str(instance.content_id),
            final_score=instance.final_score,
            user_id=instance.user_id if instance.user else None
        )
    
    # Clear related feed caches
    cache_keys = [
        f'content_score:{instance.content_type}:{instance.content_id}'
    ]
    
    if instance.user:
        cache_keys.append(f'user_feed:{instance.user_id}')
        cache_keys.append(f'user_recommendations:{instance.user_id}')
    else:
        # Global score changed, clear trending/popular caches
        cache_keys.extend([
            'trending_content_global',
            'popular_content_global',
            f'trending_content:{instance.content_type}'
        ])
    
    cache.delete_many(cache_keys)


@receiver(post_save, sender=TrendingMetric)
def trending_metric_updated(sender, instance, created, **kwargs):
    """Handle trending metric updates."""
    if created:
        log_scoring_event(
            event_type='trending_metric_created',
            metadata={
                'metric_type': instance.metric_type,
                'metric_id': instance.metric_id,
                'trending_score': instance.trending_score,
                'velocity_score': instance.velocity_score
            }
        )
        
        logger.debug(
            "Trending metric created",
            metric_type=instance.metric_type,
            metric_id=instance.metric_id,
            trending_score=instance.trending_score
        )
    else:
        # Log significant trending score changes
        if 'trending_score' in kwargs.get('update_fields', []):
            log_scoring_event(
                event_type='trending_score_changed',
                metadata={
                    'metric_type': instance.metric_type,
                    'metric_id': instance.metric_id,
                    'new_trending_score': instance.trending_score
                }
            )
    
    # Clear trending-related caches
    cache.delete_many([
        f'trending_metrics:{instance.metric_type}',
        f'trending_content:{instance.metric_type}',
        'trending_content_global',
        'hot_content',
        f'content_trending_score:{instance.metric_id}'
    ])


@receiver(post_save, sender=CreatorMetric)
def creator_metric_updated(sender, instance, created, **kwargs):
    """Handle creator metric updates."""
    if created:
        log_scoring_event(
            event_type='creator_metrics_created',
            user_id=instance.creator_id,
            metadata={
                'reputation_score': instance.reputation_score,
                'authority_score': instance.authority_score,
                'total_content_created': instance.total_content_created
            }
        )
        
        logger.info(
            "Creator metrics created",
            creator_id=instance.creator_id,
            reputation_score=instance.reputation_score,
            authority_score=instance.authority_score
        )
    else:
        # Log significant reputation changes
        if 'reputation_score' in kwargs.get('update_fields', []):
            log_scoring_event(
                event_type='creator_reputation_changed',
                user_id=instance.creator_id,
                metadata={
                    'new_reputation_score': instance.reputation_score,
                    'authority_score': instance.authority_score
                }
            )
    
    # Clear creator-related caches
    cache.delete_many([
        f'creator_metrics:{instance.creator_id}',
        f'creator_content_scores:{instance.creator_id}',
        f'user_content:{instance.creator_id}',
        'top_creators',
        'featured_creators'
    ])
    
    # Clear feeds for users who follow this creator
    from users.models import Connection
    
    try:
        # Get followers of this creator
        follower_ids = Connection.objects.filter(
            to_user=instance.creator,
            status='accepted'
        ).values_list('from_user_id', flat=True)[:1000]  # Limit for performance
        
        # Clear their feed caches
        follower_cache_keys = [f'user_feed:{user_id}' for user_id in follower_ids]
        if follower_cache_keys:
            cache.delete_many(follower_cache_keys)
    
    except Exception as e:
        logger.error(
            "Error clearing follower feed caches",
            creator_id=instance.creator_id,
            error=str(e)
        )


@receiver(post_delete, sender=ContentScore)
def content_score_deleted(sender, instance, **kwargs):
    """Handle content score deletion."""
    log_scoring_event(
        event_type='content_score_deleted',
        user_id=instance.user_id if instance.user else None,
        metadata={
            'content_type': instance.content_type,
            'content_id': str(instance.content_id)
        }
    )
    
    # Clear related caches
    cache.delete_many([
        f'content_score:{instance.content_type}:{instance.content_id}',
        f'user_feed:{instance.user_id}' if instance.user else 'global_scores'
    ])


@receiver(post_delete, sender=TrendingMetric)
def trending_metric_deleted(sender, instance, **kwargs):
    """Handle trending metric deletion."""
    log_scoring_event(
        event_type='trending_metric_deleted',
        metadata={
            'metric_type': instance.metric_type,
            'metric_id': instance.metric_id
        }
    )
    
    # Clear trending caches
    cache.delete_many([
        f'trending_metrics:{instance.metric_type}',
        f'trending_content:{instance.metric_type}',
        'trending_content_global'
    ])