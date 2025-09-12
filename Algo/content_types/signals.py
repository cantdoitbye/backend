from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache
from django.db import models
from django.contrib.contenttypes.models import ContentType
from .models import (
    Post, Community, Product, Engagement,
    CommunityMembership, ContentTag, ContentTagging
)
from analytics.utils import log_content_event
import structlog

logger = structlog.get_logger(__name__)


@receiver(post_save, sender=Post)
@receiver(post_save, sender=Community)
@receiver(post_save, sender=Product)
def content_item_updated(sender, instance, created, **kwargs):
    """Handle content item creation/updates."""
    content_type = sender.__name__.lower()
    
    if created:
        log_content_event(
            content_id=instance.id,
            content_type=content_type,
            event_type='content_created',
            user_id=instance.creator_id,
            metadata={
                'title': instance.title,
                'visibility': instance.visibility
            }
        )
        
        logger.info(
            "Content created",
            content_id=str(instance.id),
            content_type=content_type,
            creator_id=instance.creator_id,
            title=instance.title
        )
        
        # Update creator's engagement score
        instance.creator.update_engagement_score()
    else:
        log_content_event(
            content_id=instance.id,
            content_type=content_type,
            event_type='content_updated',
            user_id=instance.creator_id,
            metadata={
                'updated_fields': list(kwargs.get('update_fields', []))
            }
        )
    
    # Clear relevant caches
    cache.delete_many([
        f'user_content:{instance.creator_id}',
        f'trending_content:{content_type}',
        'feed_popular_content',
    ])
    
    # Clear feeds for users who might see this content
    if instance.visibility == 'public':
        # For public content, we can't clear all user feeds, 
        # but we can clear popular/trending caches
        cache.delete_many([
            'trending_content_global',
            'popular_content_global'
        ])


@receiver(post_delete, sender=Post)
@receiver(post_delete, sender=Community)
@receiver(post_delete, sender=Product)
def content_item_deleted(sender, instance, **kwargs):
    """Handle content item deletion."""
    content_type = sender.__name__.lower()
    
    log_content_event(
        content_id=instance.id,
        content_type=content_type,
        event_type='content_deleted',
        user_id=instance.creator_id,
        metadata={'title': instance.title}
    )
    
    logger.info(
        "Content deleted",
        content_id=str(instance.id),
        content_type=content_type,
        title=instance.title
    )
    
    # Clear related caches
    cache.delete_many([
        f'user_content:{instance.creator_id}',
        f'trending_content:{content_type}',
    ])


@receiver(post_save, sender=Engagement)
def engagement_created(sender, instance, created, **kwargs):
    """Handle engagement creation/updates."""
    if created:
        content = instance.content_object
        if content:
            # Update content engagement scores
            content.calculate_engagement_score()
            content.calculate_trending_score()
            content.save(update_fields=[
                'engagement_score', 'trending_score'
            ])
            
            # Update user engagement tracking
            if hasattr(content, 'creator'):
                content.creator.update_engagement_score()
            
            log_content_event(
                content_id=content.id,
                content_type=content.get_content_type_name().lower(),
                event_type='engagement_created',
                user_id=instance.user_id,
                metadata={
                    'engagement_type': instance.engagement_type,
                    'score': instance.score
                }
            )
            
            logger.info(
                "Engagement created",
                content_id=str(content.id),
                engagement_type=instance.engagement_type,
                user_id=instance.user_id,
                score=instance.score
            )
            
            # Clear relevant feed caches
            cache.delete_many([
                f'user_feed:{instance.user_id}',
                f'content_engagement:{content.id}',
                f'trending_content:{content.get_content_type_name().lower()}',
            ])


@receiver(post_save, sender=CommunityMembership)
def community_membership_updated(sender, instance, created, **kwargs):
    """Handle community membership changes."""
    if created:
        # Update community member count
        if instance.status == 'approved':
            Community.objects.filter(
                id=instance.community_id
            ).update(
                member_count=models.F('member_count') + 1
            )
        
        log_content_event(
            content_id=instance.community_id,
            content_type='community',
            event_type='member_joined',
            user_id=instance.user_id,
            metadata={
                'status': instance.status,
                'role': instance.role
            }
        )
        
        logger.info(
            "Community membership created",
            community_id=str(instance.community_id),
            user_id=instance.user_id,
            status=instance.status,
            role=instance.role
        )
    else:
        # Handle status changes
        if 'status' in kwargs.get('update_fields', []):
            if instance.status == 'approved':
                Community.objects.filter(
                    id=instance.community_id
                ).update(
                    member_count=models.F('member_count') + 1
                )
            elif instance.status in ['left', 'banned']:
                Community.objects.filter(
                    id=instance.community_id
                ).update(
                    member_count=models.F('member_count') - 1
                )
    
    # Clear community and user caches
    cache.delete_many([
        f'user_communities:{instance.user_id}',
        f'community_members:{instance.community_id}',
        f'user_feed:{instance.user_id}',
    ])


@receiver(post_delete, sender=CommunityMembership)
def community_membership_deleted(sender, instance, **kwargs):
    """Handle community membership deletion."""
    if instance.status == 'approved':
        Community.objects.filter(
            id=instance.community_id
        ).update(
            member_count=models.F('member_count') - 1
        )
    
    log_content_event(
        content_id=instance.community_id,
        content_type='community',
        event_type='member_left',
        user_id=instance.user_id,
        metadata={'role': instance.role}
    )
    
    # Clear caches
    cache.delete_many([
        f'user_communities:{instance.user_id}',
        f'community_members:{instance.community_id}',
        f'user_feed:{instance.user_id}',
    ])


@receiver(post_save, sender=ContentTag)
def content_tag_updated(sender, instance, created, **kwargs):
    """Handle content tag updates."""
    if created:
        logger.info(
            "Content tag created",
            tag_name=instance.name,
            category=instance.category
        )
    
    # Clear tag-related caches
    cache.delete_many([
        'trending_tags',
        'popular_tags',
        f'tag_content:{instance.name}',
    ])


@receiver(post_save, sender=ContentTagging)
def content_tagged(sender, instance, created, **kwargs):
    """Handle content tagging."""
    if created:
        # Update tag usage count
        ContentTag.objects.filter(
            id=instance.tag_id
        ).update(
            usage_count=models.F('usage_count') + 1
        )
        
        logger.info(
            "Content tagged",
            content_id=str(instance.object_id),
            tag=instance.tag.name
        )
        
        # Clear tag and content caches
        cache.delete_many([
            f'content_tags:{instance.object_id}',
            f'tag_content:{instance.tag.name}',
            'trending_tags',
        ])


@receiver(post_delete, sender=ContentTagging)
def content_untagged(sender, instance, **kwargs):
    """Handle content tag removal."""
    # Update tag usage count
    ContentTag.objects.filter(
        id=instance.tag_id
    ).update(
        usage_count=models.F('usage_count') - 1
    )
    
    # Clear caches
    cache.delete_many([
        f'content_tags:{instance.object_id}',
        f'tag_content:{instance.tag.name}',
    ])