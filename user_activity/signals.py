from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth.models import User
from user_activity.services.activity_service import ActivityService
import logging

logger = logging.getLogger(__name__)
activity_service = ActivityService()


@receiver(user_logged_in)
def track_user_login(sender, request, user, **kwargs):
    """Track user login activity."""
    try:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        activity_service.track_activity_async(
            user=user,
            activity_type='login',
            description=f"User logged in from {ip_address}",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                'login_method': 'standard',  # Can be extended for social login
                'session_key': request.session.session_key,
            }
        )
    except Exception as e:
        logger.error(f"Failed to track login activity: {e}")


@receiver(user_logged_out)
def track_user_logout(sender, request, user, **kwargs):
    """Track user logout activity."""
    try:
        if user:  # user might be None in some cases
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            activity_service.track_activity_async(
                user=user,
                activity_type='logout',
                description=f"User logged out from {ip_address}",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'session_key': request.session.session_key,
                }
            )
    except Exception as e:
        logger.error(f"Failed to track logout activity: {e}")


# Post model signals for tracking content creation/modification
try:
    from post.models import Post, Comment, Like, Review, PostView, PostShare, SavedPost, PinedPost
    
    @receiver(post_save, sender=Post)
    def track_post_activity(sender, instance, created, **kwargs):
        """Track post creation and updates."""
        try:
            if created:
                activity_service.track_activity_async(
                    user=instance.user,
                    activity_type='post_create',
                    description=f"Created post: {instance.uid}",
                    metadata={
                        'post_id': str(instance.uid),
                        'post_type': getattr(instance, 'post_type', 'standard'),
                    }
                )
                
                ActivityService.track_content_interaction(
                    user=instance.user,
                    content_type='post',
                    content_id=str(instance.uid),
                    interaction_type='create'
                )
            else:
                activity_service.track_activity_async(
                    user=instance.user,
                    activity_type='post_update',
                    description=f"Updated post: {instance.uid}",
                    metadata={
                        'post_id': str(instance.uid),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to track post activity: {e}")
    
    @receiver(post_save, sender=Comment)
    def track_comment_activity(sender, instance, created, **kwargs):
        """Track comment creation and updates."""
        try:
            if created:
                ActivityService.track_content_interaction(
                    user=instance.user,
                    content_type='post',
                    content_id=str(instance.post.uid),
                    interaction_type='comment',
                    metadata={
                        'comment_id': str(instance.uid),
                        'comment_text_length': len(instance.comment_text or ''),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to track comment activity: {e}")
    
    @receiver(post_save, sender=Like)
    def track_like_activity(sender, instance, created, **kwargs):
        """Track like creation."""
        try:
            if created:
                # Handle Neo4j relationship - get the first (and should be only) post
                post_node = instance.post.single()
                if post_node:
                    ActivityService.track_content_interaction(
                        user=instance.user.single(),
                        content_type='post',
                        content_id=str(post_node.uid),
                        interaction_type='like',
                        metadata={
                            'like_id': str(instance.uid),
                            'reaction_type': getattr(instance, 'reaction', 'like'),
                        }
                    )
        except Exception as e:
            logger.error(f"Failed to track like activity: {e}")
    
    @receiver(post_delete, sender=Like)
    def track_unlike_activity(sender, instance, **kwargs):
        """Track like deletion (unlike)."""
        try:
            # Handle Neo4j relationship - get the first (and should be only) post
            post_node = instance.post.single()
            if post_node:
                ActivityService.track_content_interaction(
                    user=instance.user.single(),
                    content_type='post',
                    content_id=str(post_node.uid),
                    interaction_type='unlike',
                    metadata={
                        'like_id': str(instance.uid),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to track unlike activity: {e}")
    
    @receiver(post_save, sender=PostView)
    def track_post_view_activity(sender, instance, created, **kwargs):
        """Track post views."""
        try:
            if created:
                # Handle Neo4j relationship - get the first (and should be only) post
                post_node = instance.post.single()
                if post_node:
                    ActivityService.track_content_interaction(
                        user=instance.user.single(),
                        content_type='post',
                        content_id=str(post_node.uid),
                        interaction_type='view',
                        metadata={
                            'view_id': str(instance.uid),
                            'view_source': getattr(instance, 'source', 'unknown'),
                        }
                    )
        except Exception as e:
            logger.error(f"Failed to track post view activity: {e}")
    
    @receiver(post_save, sender=PostShare)
    def track_post_share_activity(sender, instance, created, **kwargs):
        """Track post shares."""
        try:
            if created:
                # Handle Neo4j relationship - get the first (and should be only) post
                post_node = instance.post.single()
                if post_node:
                    ActivityService.track_content_interaction(
                        user=instance.user.single(),
                        content_type='post',
                        content_id=str(post_node.uid),
                        interaction_type='share',
                        metadata={
                            'share_id': str(instance.uid),
                            'share_platform': getattr(instance, 'share_type', 'internal'),
                        }
                    )
        except Exception as e:
            logger.error(f"Failed to track post share activity: {e}")
    
    @receiver(post_save, sender=SavedPost)
    def track_saved_post_activity(sender, instance, created, **kwargs):
        """Track saved posts."""
        try:
            if created:
                # Handle Neo4j relationship - get the first (and should be only) post
                post_node = instance.post.single()
                if post_node:
                    ActivityService.track_content_interaction(
                        user=instance.user.single(),
                        content_type='post',
                        content_id=str(post_node.uid),
                        interaction_type='save',
                        metadata={
                            'saved_id': str(instance.uid),
                        }
                    )
        except Exception as e:
            logger.error(f"Failed to track saved post activity: {e}")
    
    @receiver(post_delete, sender=SavedPost)
    def track_unsaved_post_activity(sender, instance, **kwargs):
        """Track unsaved posts."""
        try:
            # Handle Neo4j relationship - get the first (and should be only) post
            post_node = instance.post.single()
            if post_node:
                ActivityService.track_content_interaction(
                    user=instance.user.single(),
                    content_type='post',
                    content_id=str(post_node.uid),
                    interaction_type='unsave',
                    metadata={
                        'saved_id': str(instance.uid),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to track unsaved post activity: {e}")

except ImportError:
    logger.warning("Post models not found, skipping post-related signals")


# Story model signals
try:
    from story.models import Story, StoryComment, StoryReaction, StoryRating
    
    @receiver(post_save, sender=Story)
    def track_story_activity(sender, instance, created, **kwargs):
        """Track story creation and updates."""
        try:
            if created:
                ActivityService.track_activity_async(
                    user=instance.user,
                    activity_type='story_create',
                    description=f"Created story: {instance.uid}",
                    metadata={
                        'story_id': str(instance.uid),
                        'story_type': getattr(instance, 'story_type', 'standard'),
                    }
                )
                
                ActivityService.track_content_interaction(
                    user=instance.user,
                    content_type='story',
                    content_id=str(instance.uid),
                    interaction_type='create'
                )
        except Exception as e:
            logger.error(f"Failed to track story activity: {e}")
    
    @receiver(post_save, sender=StoryComment)
    def track_story_comment_activity(sender, instance, created, **kwargs):
        """Track story comment creation."""
        try:
            if created:
                ActivityService.track_content_interaction(
                    user=instance.user,
                    content_type='story',
                    content_id=str(instance.story.uid),
                    interaction_type='comment',
                    metadata={
                        'comment_id': str(instance.uid),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to track story comment activity: {e}")
    
    @receiver(post_save, sender=StoryReaction)
    def track_story_reaction_activity(sender, instance, created, **kwargs):
        """Track story reactions."""
        try:
            if created:
                ActivityService.track_content_interaction(
                    user=instance.user,
                    content_type='story',
                    content_id=str(instance.story.uid),
                    interaction_type='react',
                    metadata={
                        'reaction_id': str(instance.uid),
                        'reaction_type': getattr(instance, 'reaction_type', 'like'),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to track story reaction activity: {e}")

except ImportError:
    logger.warning("Story models not found, skipping story-related signals")


# Connection model signals
try:
    from connection.models import Connection
    
    @receiver(post_save, sender=Connection)
    def track_connection_activity(sender, instance, created, **kwargs):
        """Track connection creation."""
        try:
            if created:
                # Create ActivityService instance
                activity_service = ActivityService()
                activity_service.track_social_interaction(
                    user=instance.created_by,
                    target_user=instance.receiver,
                    interaction_type='connection_request',
                    metadata={
                        'connection_id': str(instance.uid),
                        'connection_status': getattr(instance, 'connection_status', 'pending'),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to track connection activity: {e}")

except ImportError:
    logger.warning("Connection models not found, skipping connection-related signals")


# Community model signals
try:
    from community.models import Community, Membership
    
    @receiver(post_save, sender=Community)
    def track_community_creation(sender, instance, created, **kwargs):
        """Track community creation."""
        try:
            if created:
                ActivityService.track_activity_async(
                    user=instance.creator,
                    activity_type='community_create',
                    description=f"Created community: {instance.name}",
                    metadata={
                        'community_id': str(instance.uid),
                        'community_name': instance.name,
                    }
                )
        except Exception as e:
            logger.error(f"Failed to track community creation: {e}")
    
    @receiver(post_save, sender=Membership)
    def track_community_join(sender, instance, created, **kwargs):
        """Track community joining."""
        try:
            if created:
                # Create ActivityService instance
                activity_service = ActivityService()
                activity_service.track_social_interaction(
                    user=instance.user,
                    interaction_type='group_join',
                    context_type='community',
                    context_id=str(instance.community.uid),
                    metadata={
                        'community_name': instance.community.name,
                        'member_role': getattr(instance, 'role', 'member'),
                    }
                )
        except Exception as e:
            logger.error(f"Failed to track community join: {e}")

except ImportError:
    logger.warning("Community models not found, skipping community-related signals")


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip