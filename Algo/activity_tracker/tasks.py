from celery import shared_task
from django.utils import timezone
from django.conf import settings
from celery.utils.log import get_task_logger
from .models import UserEngagementScore, UserActivity
from django.contrib.auth import get_user_model

logger = get_task_logger(__name__)
User = get_user_model()

@shared_task(name='update_engagement_scores')
def update_engagement_scores(user_id=None):
    """
    Update engagement scores for all users or a specific user.
    
    Args:
        user_id: If provided, only update this user's scores
    """
    decay_rate = settings.ACTIVITY_TRACKING.get('SCORE_DECAY_RATE', 0.95)
    weights = settings.ACTIVITY_TRACKING.get('ENGAGEMENT_WEIGHTS', {})
    
    # Get base queryset
    if user_id:
        users = User.objects.filter(id=user_id)
    else:
        # Only process users with recent activity (last 7 days)
        week_ago = timezone.now() - timezone.timedelta(days=7)
        users = User.objects.filter(
            activities__created_at__gte=week_ago
        ).distinct()
    
    updated_count = 0
    
    for user in users.iterator():
        try:
            score, created = UserEngagementScore.objects.get_or_create(user=user)
            
            # Apply time decay to existing scores
            if not created:
                days_since_update = (timezone.now() - score.updated_at).days
                if days_since_update > 0:
                    decay = decay_rate ** days_since_update
                    score.engagement_score *= decay
                    score.content_score *= decay
                    score.social_score *= decay
            
            # Get recent activities (last 30 days)
            month_ago = timezone.now() - timezone.timedelta(days=30)
            activities = UserActivity.objects.filter(
                user=user,
                created_at__gte=month_ago
            )
            
            # Reset counts
            score.vibe_count = 0
            score.comment_count = 0
            score.share_count = 0
            score.save_count = 0
            
            # Process activities
            for activity in activities:
                # Update activity type counts
                if activity.activity_type == 'vibe':
                    score.vibe_count += 1
                elif activity.activity_type == 'comment':
                    score.comment_count += 1
                elif activity.activity_type == 'share':
                    score.share_count += 1
                elif activity.activity_type == 'save':
                    score.save_count += 1
            
            # Calculate scores based on weights and counts
            score.engagement_score = min(100, (
                (score.vibe_count * weights.get('vibe', 1.0)) +
                (score.comment_count * weights.get('comment', 1.5)) +
                (score.share_count * weights.get('share', 2.0)) +
                (score.save_count * weights.get('save', 1.2))
            ))
            
            # Update timestamps
            last_activity = activities.order_by('-created_at').first()
            if last_activity:
                score.last_activity_at = last_activity.created_at
            
            score.save()
            updated_count += 1
            
        except Exception as e:
            logger.error(f"Error updating engagement score for user {user.id}: {e}")
    
    logger.info(f"Updated engagement scores for {updated_count} users")
    return updated_count
