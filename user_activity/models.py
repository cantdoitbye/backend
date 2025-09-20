from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import uuid


class BaseActivityModel(models.Model):
    """Base model for all activity tracking models."""
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['created_at']),
        ]


class UserActivity(BaseActivityModel):
    """Base activity tracking for all user actions."""
    
    ACTIVITY_TYPES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('profile_update', 'Profile Update'),
        ('password_change', 'Password Change'),
        ('email_change', 'Email Change'),
        ('account_deactivation', 'Account Deactivation'),
        ('account_reactivation', 'Account Reactivation'),
        ('settings_update', 'Settings Update'),
        ('privacy_update', 'Privacy Settings Update'),
        ('notification_update', 'Notification Settings Update'),
        ('search', 'Search Activity'),
        ('navigation', 'Page Navigation'),
        ('error', 'Error Encountered'),
        ('feature_usage', 'Feature Usage'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField(null=True, blank=True)
    success = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_activity'
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
            models.Index(fields=['user', 'activity_type']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp}"


class ContentInteraction(BaseActivityModel):
    """Track interactions with posts, stories, and other content."""
    
    CONTENT_TYPES = [
        ('post', 'Post'),
        ('story', 'Story'),
        ('comment', 'Comment'),
        ('community_post', 'Community Post'),
        ('review', 'Review'),
    ]
    
    INTERACTION_TYPES = [
        ('view', 'View'),
        ('like', 'Like'),
        ('unlike', 'Unlike'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('save', 'Save'),
        ('unsave', 'Unsave'),
        ('pin', 'Pin'),
        ('unpin', 'Unpin'),
        ('report', 'Report'),
        ('hide', 'Hide'),
        ('react', 'React'),
        ('unreact', 'Unreact'),
        ('rate', 'Rate'),
        ('scroll_depth', 'Scroll Depth'),
        ('time_spent', 'Time Spent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_interactions')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_id = models.CharField(max_length=100)  # UUID or ID of the content
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    scroll_depth_percentage = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = 'content_interaction'
        verbose_name = 'Content Interaction'
        verbose_name_plural = 'Content Interactions'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['interaction_type', 'timestamp']),
            models.Index(fields=['user', 'content_type', 'interaction_type']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} on {self.content_type}:{self.content_id}"


class ProfileActivity(BaseActivityModel):
    """Track profile visits and interactions."""
    
    ACTIVITY_TYPES = [
        ('profile_view', 'Profile View'),
        ('profile_follow', 'Profile Follow'),
        ('profile_unfollow', 'Profile Unfollow'),
        ('profile_block', 'Profile Block'),
        ('profile_unblock', 'Profile Unblock'),
        ('profile_report', 'Profile Report'),
        ('profile_message', 'Profile Message'),
        ('profile_share', 'Profile Share'),
        ('achievement_view', 'Achievement View'),
        ('experience_view', 'Experience View'),
        ('posts_browse', 'Posts Browse'),
        ('stories_browse', 'Stories Browse'),
    ]
    
    visitor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_visits')
    profile_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_views_received')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'profile_activity'
        verbose_name = 'Profile Activity'
        verbose_name_plural = 'Profile Activities'
        indexes = [
            models.Index(fields=['visitor', 'timestamp']),
            models.Index(fields=['profile_owner', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
            models.Index(fields=['visitor', 'profile_owner']),
        ]

    def __str__(self):
        return f"{self.visitor.username} - {self.activity_type} on {self.profile_owner.username}'s profile"


class MediaInteraction(BaseActivityModel):
    """Track image/video click and interaction tracking."""
    
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('gif', 'GIF'),
        ('thumbnail', 'Thumbnail'),
    ]
    
    INTERACTION_TYPES = [
        ('click', 'Click'),
        ('view', 'View'),
        ('download', 'Download'),
        ('share', 'Share'),
        ('zoom', 'Zoom'),
        ('play', 'Play'),
        ('pause', 'Pause'),
        ('seek', 'Seek'),
        ('fullscreen', 'Fullscreen'),
        ('volume_change', 'Volume Change'),
        ('quality_change', 'Quality Change'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_interactions')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    media_id = models.CharField(max_length=100)  # UUID or ID of the media
    media_url = models.URLField(null=True, blank=True)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    position_seconds = models.PositiveIntegerField(null=True, blank=True)  # For video/audio seeking
    
    class Meta:
        db_table = 'media_interaction'
        verbose_name = 'Media Interaction'
        verbose_name_plural = 'Media Interactions'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['media_type', 'media_id']),
            models.Index(fields=['interaction_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} on {self.media_type}:{self.media_id}"


class SocialInteraction(BaseActivityModel):
    """Track connection-related activities and social interactions."""
    
    INTERACTION_TYPES = [
        ('connection_request', 'Connection Request'),
        ('connection_accept', 'Connection Accept'),
        ('connection_decline', 'Connection Decline'),
        ('connection_remove', 'Connection Remove'),
        ('message_send', 'Message Send'),
        ('message_read', 'Message Read'),
        ('group_join', 'Group Join'),
        ('group_leave', 'Group Leave'),
        ('group_invite', 'Group Invite'),
        ('mention', 'Mention'),
        ('tag', 'Tag'),
        ('recommendation_view', 'Recommendation View'),
        ('recommendation_dismiss', 'Recommendation Dismiss'),
        ('profile_visit', 'Profile Visit'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_interactions')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_interactions_received', null=True, blank=True)
    interaction_type = models.CharField(max_length=25, choices=INTERACTION_TYPES)
    context_type = models.CharField(max_length=50, null=True, blank=True)  # e.g., 'community', 'direct_message'
    context_id = models.CharField(max_length=100, null=True, blank=True)  # ID of the context object
    
    class Meta:
        db_table = 'social_interaction'
        verbose_name = 'Social Interaction'
        verbose_name_plural = 'Social Interactions'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['target_user', 'timestamp']),
            models.Index(fields=['interaction_type', 'timestamp']),
            models.Index(fields=['user', 'target_user']),
        ]

    def __str__(self):
        target = self.target_user.username if self.target_user else 'N/A'
        return f"{self.user.username} - {self.interaction_type} with {target}"


class SessionActivity(BaseActivityModel):
    """Track user session and navigation patterns."""
    
    SESSION_TYPES = [
        ('web', 'Web Session'),
        ('mobile', 'Mobile Session'),
        ('api', 'API Session'),
        ('admin', 'Admin Session'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.CharField(max_length=100)
    session_type = models.CharField(max_length=10, choices=SESSION_TYPES, default='web')
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    pages_visited = models.PositiveIntegerField(default=0)
    actions_performed = models.PositiveIntegerField(default=0)
    device_info = models.JSONField(default=dict, blank=True)
    location_data = models.JSONField(default=dict, blank=True)
    referrer = models.URLField(null=True, blank=True)
    exit_page = models.CharField(max_length=200, null=True, blank=True)
    
    class Meta:
        db_table = 'session_activity'
        verbose_name = 'Session Activity'
        verbose_name_plural = 'Session Activities'
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['session_id']),
            models.Index(fields=['session_type', 'start_time']),
        ]

    def save(self, *args, **kwargs):
        if self.end_time and self.start_time:
            self.duration_seconds = int((self.end_time - self.start_time).total_seconds())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.session_type} session {self.session_id}"


class VibeActivity(BaseActivityModel):
    """Track vibe-related activities including creation, sending, and receiving."""
    
    VIBE_ACTIVITY_TYPES = [
        ('vibe_create', 'Vibe Create'),
        ('vibe_send', 'Vibe Send'),
        ('vibe_receive', 'Vibe Receive'),
        ('vibe_view', 'Vibe View'),
        ('vibe_search', 'Vibe Search'),
        ('vibe_category_browse', 'Vibe Category Browse'),
        ('vibe_popularity_view', 'Vibe Popularity View'),
        ('vibe_score_update', 'Vibe Score Update'),
    ]
    
    # Alias for compatibility with test expectations
    ACTIVITY_TYPES = VIBE_ACTIVITY_TYPES
    
    VIBE_TYPES = [
        ('individual', 'Individual Vibe'),
        ('community', 'Community Vibe'),
        ('brand', 'Brand Vibe'),
        ('service', 'Service Vibe'),
        ('main', 'Main Vibe'),  # For Neo4j Vibe model
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vibe_activities')
    activity_type = models.CharField(max_length=25, choices=VIBE_ACTIVITY_TYPES)
    vibe_type = models.CharField(max_length=15, choices=VIBE_TYPES)
    vibe_id = models.CharField(max_length=100)  # UUID or ID of the vibe
    vibe_name = models.CharField(max_length=255, null=True, blank=True)
    vibe_category = models.CharField(max_length=100, null=True, blank=True)
    
    # For vibe sending/receiving activities
    target_user_id = models.CharField(max_length=100, null=True, blank=True)  # ID of user receiving/sending vibe
    vibe_score = models.FloatField(null=True, blank=True)  # Score value for vibe interaction
    
    # Score impact tracking
    iq_impact = models.FloatField(null=True, blank=True)
    aq_impact = models.FloatField(null=True, blank=True)
    sq_impact = models.FloatField(null=True, blank=True)
    hq_impact = models.FloatField(null=True, blank=True)
    
    # Additional context
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'vibe_activity'
        verbose_name = 'Vibe Activity'
        verbose_name_plural = 'Vibe Activities'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
            models.Index(fields=['vibe_type', 'timestamp']),
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['vibe_id', 'activity_type']),
            models.Index(fields=['target_user_id', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} ({self.vibe_name or self.vibe_id}) at {self.timestamp}"


class ActivityAggregation(models.Model):
    """Aggregated activity data for analytics and reporting."""
    
    AGGREGATION_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_aggregations')
    aggregation_type = models.CharField(max_length=10, choices=AGGREGATION_TYPES)
    date = models.DateField()
    activity_counts = models.JSONField(default=dict)  # {"posts_created": 5, "likes_given": 20, etc.}
    engagement_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'activity_aggregation'
        verbose_name = 'Activity Aggregation'
        verbose_name_plural = 'Activity Aggregations'
        unique_together = ['user', 'aggregation_type', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['aggregation_type', 'date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.aggregation_type} aggregation for {self.date}"