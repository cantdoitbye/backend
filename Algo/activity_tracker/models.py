from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils import timezone
from django.db.models import JSONField

class ActivityType(models.TextChoices):
    # Engagement
    VIBE = 'vibe', 'Vibe Interaction'
    COMMENT = 'comment', 'Comment/Reply'
    SHARE = 'share', 'Share'
    SAVE = 'save', 'Save/Bookmark'
    MEDIA_EXPAND = 'media_expand', 'Media Expand'
    
    # User Interactions
    PROFILE_VISIT = 'profile_visit', 'Profile Visit'
    
    # Content Creation
    POST_CREATE = 'post_create', 'Post Creation'
    
    # Search & Discovery
    EXPLORE_CLICK = 'explore_click', 'Explore Click'
    
    # Negative Signals
    REPORT = 'report', 'Content Report'
    
    # Social Graph
    CIRCLE_UPDATE = 'circle_update', 'Circle Update'
    GROUP_JOIN = 'group_join', 'Group Join'
    
    # Page Views
    PAGE_VIEW = 'page_view', 'Page View'


class UserActivity(models.Model):
    """Core model for tracking user activities."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(
        max_length=50,
        choices=ActivityType.choices
    )
    
    # Generic foreign key to the content object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional context for the activity
    metadata = JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'User Activities'
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['activity_type', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.created_at}"


class UserEngagementScore(models.Model):
    """Aggregated engagement scores for users."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='engagement_score'
    )
    
    # Engagement metrics
    total_activities = models.PositiveIntegerField(default=0)
    last_activity_at = models.DateTimeField(null=True, blank=True)
    
    # Activity type counts (for quick lookups)
    vibe_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    save_count = models.PositiveIntegerField(default=0)
    
    # Composite scores (0-100)
    engagement_score = models.FloatField(default=0.0)  # Overall engagement
    content_score = models.FloatField(default=0.0)     # Content creation
    social_score = models.FloatField(default=0.0)      # Social interactions
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Engagement Score'
        verbose_name_plural = 'User Engagement Scores'
    
    def update_scores(self):
        """Recalculate all engagement scores."""
        # Calculate engagement score based on activity counts with weights
        # These weights can be adjusted based on business requirements
        activity_weights = {
            'vibe': 1.0,
            'comment': 1.5,
            'share': 2.0,
            'save': 1.8,
        }
        
        # Calculate total weighted activities
        total_weighted = sum(
            getattr(self, f"{activity_type}_count", 0) * weight 
            for activity_type, weight in activity_weights.items()
        )
        
        # Calculate content score (based on content creation activities)
        content_activities = ['post_create', 'comment']
        content_score = sum(
            getattr(self, f"{activity_type}_count", 0)
            for activity_type in content_activities
        )
        
        # Calculate social score (based on social interactions)
        social_activities = ['vibe', 'share', 'profile_visit']
        social_score = sum(
            getattr(self, f"{activity_type}_count", 0)
            for activity_type in social_activities
        )
        
        # Apply decay to older activities to prioritize recent engagement
        # This is a simple linear decay - you might want to adjust based on your needs
        days_since_last_activity = (timezone.now() - (self.last_activity_at or timezone.now())).days
        decay_factor = max(0, 1 - (days_since_last_activity * 0.01))  # 1% decay per day
        
        # Update the scores with decay applied
        self.engagement_score = total_weighted * decay_factor
        self.content_score = content_score * decay_factor
        self.social_score = social_score * decay_factor
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - Engagement: {self.engagement_score:.1f}"
