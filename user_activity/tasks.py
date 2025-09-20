from celery import shared_task
from django.contrib.auth.models import User
from user_activity.models import (
    UserActivity,
    ContentInteraction,
    ProfileActivity,
    MediaInteraction,
    SocialInteraction
)
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def track_user_activity_task(self, user_id: int, activity_type: str,
                           description: str = None, success: bool = True,
                           ip_address: str = None, user_agent: str = None,
                           metadata: Dict[str, Any] = None):
    """Async task to track user activity."""
    try:
        user = User.objects.get(id=user_id)
        UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        logger.info(f"Tracked activity {activity_type} for user {user.username}")
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
    except Exception as exc:
        logger.error(f"Failed to track user activity: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        raise


@shared_task(bind=True, max_retries=3)
def track_content_interaction_task(self, user_id: int, content_type: str, content_id: str,
                                 interaction_type: str, duration_seconds: int = None,
                                 scroll_depth_percentage: float = None,
                                 ip_address: str = None, user_agent: str = None,
                                 metadata: Dict[str, Any] = None):
    """Async task to track content interaction."""
    try:
        user = User.objects.get(id=user_id)
        ContentInteraction.objects.create(
            user=user,
            content_type=content_type,
            content_id=content_id,
            interaction_type=interaction_type,
            duration_seconds=duration_seconds,
            scroll_depth_percentage=scroll_depth_percentage,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        logger.info(f"Tracked {interaction_type} interaction on {content_type}:{content_id} for user {user.username}")
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
    except Exception as exc:
        logger.error(f"Failed to track content interaction: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        raise


@shared_task(bind=True, max_retries=3)
def track_profile_activity_task(self, visitor_id: int, profile_owner_id: int,
                              activity_type: str, duration_seconds: int = None,
                              ip_address: str = None, user_agent: str = None,
                              metadata: Dict[str, Any] = None):
    """Async task to track profile activity."""
    try:
        visitor = User.objects.get(id=visitor_id)
        profile_owner = User.objects.get(id=profile_owner_id)
        ProfileActivity.objects.create(
            visitor=visitor,
            profile_owner=profile_owner,
            activity_type=activity_type,
            duration_seconds=duration_seconds,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        logger.info(f"Tracked {activity_type} by {visitor.username} on {profile_owner.username}'s profile")
    except User.DoesNotExist as e:
        logger.error(f"User does not exist: {e}")
    except Exception as exc:
        logger.error(f"Failed to track profile activity: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        raise


@shared_task(bind=True, max_retries=3)
def track_media_interaction_task(self, user_id: int, media_type: str, media_id: str,
                               interaction_type: str, duration_seconds: int = None,
                               position_seconds: int = None, media_url: str = None,
                               ip_address: str = None, user_agent: str = None,
                               metadata: Dict[str, Any] = None):
    """Async task to track media interaction."""
    try:
        user = User.objects.get(id=user_id)
        MediaInteraction.objects.create(
            user=user,
            media_type=media_type,
            media_id=media_id,
            interaction_type=interaction_type,
            duration_seconds=duration_seconds,
            position_seconds=position_seconds,
            media_url=media_url,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        logger.info(f"Tracked {interaction_type} on {media_type}:{media_id} for user {user.username}")
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
    except Exception as exc:
        logger.error(f"Failed to track media interaction: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        raise


@shared_task(bind=True, max_retries=3)
def track_social_interaction_task(self, user_id: int, target_user_id: Optional[int] = None,
                                interaction_type: str = None, context_type: str = None,
                                context_id: str = None, ip_address: str = None,
                                user_agent: str = None, metadata: Dict[str, Any] = None):
    """Async task to track social interaction."""
    try:
        user = User.objects.get(id=user_id)
        target_user = User.objects.get(id=target_user_id) if target_user_id else None
        
        SocialInteraction.objects.create(
            user=user,
            target_user=target_user,
            interaction_type=interaction_type,
            context_type=context_type,
            context_id=context_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        target_name = target_user.username if target_user else 'N/A'
        logger.info(f"Tracked {interaction_type} by {user.username} with {target_name}")
    except User.DoesNotExist as e:
        logger.error(f"User does not exist: {e}")
    except Exception as exc:
        logger.error(f"Failed to track social interaction: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        raise


@shared_task
def aggregate_daily_activities():
    """Daily task to aggregate activity data for performance optimization."""
    from user_activity.services.aggregation_service import AggregationService
    
    try:
        aggregation_service = AggregationService()
        aggregation_service.aggregate_daily_activities()
        logger.info("Daily activity aggregation completed successfully")
    except Exception as exc:
        logger.error(f"Failed to aggregate daily activities: {exc}")
        raise


@shared_task
def cleanup_old_activities():
    """Task to cleanup old activity data based on retention policy."""
    from user_activity.services.cleanup_service import CleanupService
    
    try:
        cleanup_service = CleanupService()
        cleanup_service.cleanup_old_activities()
        logger.info("Activity cleanup completed successfully")
    except Exception as exc:
        logger.error(f"Failed to cleanup old activities: {exc}")
        raise


@shared_task
def generate_user_insights(user_id: int):
    """Generate user insights and recommendations based on activity data."""
    from user_activity.services.insights_service import InsightsService
    
    try:
        user = User.objects.get(id=user_id)
        insights_service = InsightsService()
        insights_service.generate_user_insights(user)
        logger.info(f"Generated insights for user {user.username}")
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
    except Exception as exc:
        logger.error(f"Failed to generate user insights: {exc}")
        raise