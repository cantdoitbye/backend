from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserActivity, UserEngagementScore

@receiver(post_save, sender=UserActivity)
def update_engagement_score(sender, instance, created, **kwargs):
    """Update engagement scores when a new activity is created."""
    if created:
        # Get or create the user's engagement score
        score, created = UserEngagementScore.objects.get_or_create(
            user=instance.user
        )
        
        # Update the last activity timestamp
        if not score.last_activity_at or instance.created_at > score.last_activity_at:
            score.last_activity_at = instance.created_at
        
        # Increment the appropriate counter based on activity type
        activity_field = f"{instance.activity_type}_count"
        if hasattr(score, activity_field):
            current_count = getattr(score, activity_field, 0)
            setattr(score, activity_field, current_count + 1)
        
        # Recalculate the composite scores
        score.update_scores()
