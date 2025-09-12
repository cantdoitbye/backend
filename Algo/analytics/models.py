from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from decimal import Decimal


class AnalyticsEvent(models.Model):
    """
    Generic analytics event tracking for all system interactions.
    """
    # Event identification
    event_name = models.CharField(max_length=100)
    event_category = models.CharField(
        max_length=50,
        choices=[
            ('feed', 'Feed Interaction'),
            ('content', 'Content Interaction'),
            ('user', 'User Action'),
            ('system', 'System Event'),
            ('performance', 'Performance Metric'),
            ('error', 'Error Event')
        ]
    )
    
    # User context
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    # Content context (generic foreign key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Event data
    properties = models.JSONField(default=dict, blank=True)
    value = models.FloatField(null=True, blank=True)  # For numeric metrics
    
    # Context metadata
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    referrer = models.URLField(blank=True)
    
    # Device and platform info
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('mobile', 'Mobile'),
            ('tablet', 'Tablet'),
            ('desktop', 'Desktop'),
            ('unknown', 'Unknown')
        ],
        default='unknown'
    )
    platform = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_events'
        indexes = [
            models.Index(fields=['event_name', 'event_category']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['event_category', 'created_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{self.event_name} by {user_str} at {self.created_at}"


class FeedAnalytics(models.Model):
    """
    Analytics specific to feed performance and user engagement.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feed_analytics')
    
    # Feed generation metrics
    generation_time_ms = models.PositiveIntegerField()
    content_count = models.PositiveIntegerField()
    composition_used = models.JSONField(default=dict)
    
    # Content breakdown
    personal_connections_count = models.PositiveIntegerField(default=0)
    interest_based_count = models.PositiveIntegerField(default=0)
    trending_count = models.PositiveIntegerField(default=0)
    discovery_count = models.PositiveIntegerField(default=0)
    community_count = models.PositiveIntegerField(default=0)
    product_count = models.PositiveIntegerField(default=0)
    
    # Cache performance
    cache_hit = models.BooleanField(default=False)
    cache_key = models.CharField(max_length=200, blank=True)
    
    # User engagement with this feed
    items_viewed = models.PositiveIntegerField(default=0)
    items_engaged = models.PositiveIntegerField(default=0)
    total_engagement_time_seconds = models.PositiveIntegerField(default=0)
    
    # A/B Testing
    experiment_group = models.CharField(max_length=50, blank=True)
    
    # Context
    request_id = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feed_analytics'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['generation_time_ms']),
            models.Index(fields=['cache_hit', 'generation_time_ms']),
            models.Index(fields=['experiment_group']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"Feed analytics for {self.user.username} at {self.created_at}"
    
    @property
    def engagement_rate(self):
        """Calculate engagement rate for this feed."""
        if self.items_viewed == 0:
            return 0.0
        return self.items_engaged / self.items_viewed


class UserEngagementMetrics(models.Model):
    """
    Aggregated user engagement metrics over time periods.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='engagement_metrics')
    
    # Time period
    period_type = models.CharField(
        max_length=10,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly')
        ]
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Engagement metrics
    sessions_count = models.PositiveIntegerField(default=0)
    total_session_duration_seconds = models.PositiveIntegerField(default=0)
    feed_views = models.PositiveIntegerField(default=0)
    content_views = models.PositiveIntegerField(default=0)
    
    # Interaction metrics
    likes_given = models.PositiveIntegerField(default=0)
    comments_made = models.PositiveIntegerField(default=0)
    shares_made = models.PositiveIntegerField(default=0)
    
    # Content creation
    posts_created = models.PositiveIntegerField(default=0)
    communities_joined = models.PositiveIntegerField(default=0)
    connections_made = models.PositiveIntegerField(default=0)
    
    # Calculated scores
    engagement_score = models.FloatField(default=0.0)
    activity_score = models.FloatField(default=0.0)
    
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_engagement_metrics'
        unique_together = ('user', 'period_type', 'period_start')
        indexes = [
            models.Index(fields=['user', 'period_type']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['engagement_score']),
            models.Index(fields=['activity_score'])
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.period_type} metrics for {self.period_start.date()}"


class ContentPerformanceMetrics(models.Model):
    """
    Performance metrics for content items across different time periods.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Time period
    period_type = models.CharField(
        max_length=10,
        choices=[
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly')
        ]
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # View metrics
    impressions = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    total_view_time_seconds = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    bookmarks = models.PositiveIntegerField(default=0)
    
    # Calculated metrics
    engagement_rate = models.FloatField(default=0.0)
    viral_coefficient = models.FloatField(default=0.0)
    average_view_time_seconds = models.FloatField(default=0.0)
    
    # Distribution metrics
    feed_appearances = models.PositiveIntegerField(default=0)
    trending_appearances = models.PositiveIntegerField(default=0)
    search_appearances = models.PositiveIntegerField(default=0)
    
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'content_performance_metrics'
        unique_together = ('content_type', 'object_id', 'period_type', 'period_start')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['period_type', 'period_start']),
            models.Index(fields=['engagement_rate']),
            models.Index(fields=['viral_coefficient']),
            models.Index(fields=['impressions'])
        ]
    
    def __str__(self):
        content_name = f"{self.content_type.name}#{self.object_id}"
        return f"{content_name} {self.period_type} metrics for {self.period_start.date()}"


class SystemPerformanceMetrics(models.Model):
    """
    System-wide performance and health metrics.
    """
    metric_name = models.CharField(max_length=100)
    metric_category = models.CharField(
        max_length=30,
        choices=[
            ('database', 'Database'),
            ('cache', 'Cache'),
            ('api', 'API'),
            ('feed_generation', 'Feed Generation'),
            ('scoring', 'Scoring Engine'),
            ('memory', 'Memory Usage'),
            ('cpu', 'CPU Usage')
        ]
    )
    
    # Metric values
    value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)
    
    # Performance thresholds
    warning_threshold = models.FloatField(null=True, blank=True)
    critical_threshold = models.FloatField(null=True, blank=True)
    
    # Metric context
    server_id = models.CharField(max_length=50, blank=True)
    environment = models.CharField(
        max_length=20,
        choices=[
            ('development', 'Development'),
            ('staging', 'Staging'),
            ('production', 'Production')
        ],
        default='production'
    )
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'system_performance_metrics'
        indexes = [
            models.Index(fields=['metric_name', 'metric_category']),
            models.Index(fields=['recorded_at']),
            models.Index(fields=['server_id', 'recorded_at']),
            models.Index(fields=['environment', 'metric_category'])
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.value} {self.unit}"
    
    @property
    def status(self):
        """Determine the status based on thresholds."""
        if self.critical_threshold and self.value >= self.critical_threshold:
            return 'critical'
        elif self.warning_threshold and self.value >= self.warning_threshold:
            return 'warning'
        else:
            return 'normal'


class ABTestMetrics(models.Model):
    """
    Metrics for A/B testing experiments.
    """
    experiment_name = models.CharField(max_length=100)
    variant = models.CharField(max_length=50)
    
    # Experiment details
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    # Metric being tracked
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    
    # Conversion tracking
    is_conversion = models.BooleanField(default=False)
    conversion_value = models.FloatField(null=True, blank=True)
    
    # Context
    metadata = models.JSONField(default=dict, blank=True)
    
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ab_test_metrics'
        indexes = [
            models.Index(fields=['experiment_name', 'variant']),
            models.Index(fields=['user', 'experiment_name']),
            models.Index(fields=['metric_name', 'recorded_at']),
            models.Index(fields=['is_conversion'])
        ]
    
    def __str__(self):
        return f"{self.experiment_name} ({self.variant}): {self.metric_name}"


class ErrorLog(models.Model):
    """
    System error logging and tracking.
    """
    # Error identification
    error_type = models.CharField(max_length=100)
    error_message = models.TextField()
    stack_trace = models.TextField(blank=True)
    
    # Error context
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    request_id = models.CharField(max_length=100, blank=True)
    
    # Request context
    url_path = models.TextField(blank=True)
    http_method = models.CharField(max_length=10, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Error severity
    severity = models.CharField(
        max_length=20,
        choices=[
            ('debug', 'Debug'),
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('critical', 'Critical')
        ],
        default='error'
    )
    
    # Resolution tracking
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'error_logs'
        indexes = [
            models.Index(fields=['error_type', 'severity']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_resolved', 'created_at']),
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"{self.error_type} ({self.severity}) at {self.created_at}"
    
    def resolve(self, notes=""):
        """Mark this error as resolved."""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save(update_fields=['is_resolved', 'resolved_at', 'resolution_notes'])
