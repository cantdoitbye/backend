from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


class UserProfile(models.Model):
    """
    Extended user profile for feed customization and preferences.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # Feed preferences
    feed_enabled = models.BooleanField(default=True)
    content_language = models.CharField(max_length=10, default='en')
    
    # Engagement tracking
    total_engagement_score = models.FloatField(default=0.0)
    last_active = models.DateTimeField(auto_now=True)
    
    # Privacy settings
    privacy_level = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('friends', 'Friends Only'),
            ('private', 'Private')
        ],
        default='public'
    )
    
    # Analytics
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['last_active']),
            models.Index(fields=['total_engagement_score']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def update_engagement_score(self, score_delta):
        """Update the user's total engagement score."""
        self.total_engagement_score += score_delta
        self.save(update_fields=['total_engagement_score'])


class Connection(models.Model):
    """
    Represents connections between users with different circle types.
    """
    CIRCLE_TYPES = [
        ('inner', 'Inner Circle'),      # Weight: 1.0
        ('outer', 'Outer Circle'),      # Weight: 0.7
        ('universe', 'Universe')        # Weight: 0.4
    ]
    
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='algorithm_connections_from'
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='algorithm_connections_to'
    )
    
    circle_type = models.CharField(
        max_length=10, 
        choices=CIRCLE_TYPES, 
        default='universe'
    )
    
    # Connection strength metrics
    interaction_count = models.PositiveIntegerField(default=0)
    last_interaction = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'connections'
        unique_together = ('from_user', 'to_user')
        indexes = [
            models.Index(fields=['from_user', 'circle_type']),
            models.Index(fields=['to_user', 'circle_type']),
            models.Index(fields=['last_interaction']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.circle_type})"
    
    @property
    def circle_weight(self):
        """Return the scoring weight for this circle type."""
        weights = {
            'inner': 1.0,
            'outer': 0.7,
            'universe': 0.4
        }
        return weights.get(self.circle_type, 0.4)
    
    def update_interaction(self):
        """Update interaction metrics when users interact."""
        self.interaction_count += 1
        self.last_interaction = timezone.now()
        self.save(update_fields=['interaction_count', 'last_interaction'])


class Interest(models.Model):
    """
    Represents user interests for content personalization.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    
    # Interest metadata
    is_trending = models.BooleanField(default=False)
    popularity_score = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'interests'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['popularity_score']),
            models.Index(fields=['is_trending'])
        ]
    
    def __str__(self):
        return self.name


class InterestCollection(models.Model):
    """
    Links users to their interests with strength indicators.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interests')
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)
    
    # Interest strength (0.0 to 1.0)
    strength = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # How the interest was determined
    source = models.CharField(
        max_length=20,
        choices=[
            ('explicit', 'User Selected'),
            ('inferred', 'AI Inferred'),
            ('behavioral', 'Behavioral Analysis')
        ],
        default='explicit'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_interests'
        unique_together = ('user', 'interest')
        indexes = [
            models.Index(fields=['user', 'strength']),
            models.Index(fields=['interest', 'strength']),
            models.Index(fields=['source'])
        ]
    
    def __str__(self):
        return f"{self.user.username} -> {self.interest.name} ({self.strength})"


class FeedComposition(models.Model):
    """
    Configurable feed composition settings per user.
    Allows dynamic adjustment of content type ratios.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='composition_config'
    )
    
    # Content type percentages (must sum to 1.0)
    personal_connections = models.FloatField(
        default=0.40,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    interest_based = models.FloatField(
        default=0.25,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    trending_content = models.FloatField(
        default=0.15,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    discovery_content = models.FloatField(
        default=0.10,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    community_content = models.FloatField(
        default=0.05,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    product_content = models.FloatField(
        default=0.05,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # A/B Testing
    experiment_group = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'feed_compositions'
        indexes = [
            models.Index(fields=['experiment_group']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"{self.user.username}'s Feed Composition"
    
    def clean(self):
        """Validate that all percentages sum to 1.0."""
        from django.core.exceptions import ValidationError
        total = (
            self.personal_connections + self.interest_based + 
            self.trending_content + self.discovery_content +
            self.community_content + self.product_content
        )
        if abs(total - 1.0) > 0.01:  # Allow small floating point errors
            raise ValidationError(
                f'Feed composition percentages must sum to 1.0, got {total}'
            )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def composition_dict(self):
        """Return composition as a dictionary."""
        return {
            'personal_connections': self.personal_connections,
            'interest_based': self.interest_based,
            'trending_content': self.trending_content,
            'discovery_content': self.discovery_content,
            'community_content': self.community_content,
            'product_content': self.product_content
        }


class TrendingMetric(models.Model):
    """
    Tracks trending metrics for content with Redis caching support.
    """
    content_type = models.CharField(max_length=50)  # 'post', 'community', 'product'
    content_id = models.PositiveIntegerField()
    
    # Trending metrics
    velocity_score = models.FloatField(default=0.0)  # Rate of engagement growth
    viral_coefficient = models.FloatField(default=0.0)  # Share/engagement ratio
    engagement_rate = models.FloatField(default=0.0)  # Engagements per view
    
    # Time-based metrics
    trending_window = models.CharField(
        max_length=10,
        choices=[
            ('1h', '1 Hour'),
            ('6h', '6 Hours'),
            ('24h', '24 Hours'),
            ('7d', '7 Days')
        ],
        default='24h'
    )
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'trending_metrics'
        unique_together = ('content_type', 'content_id', 'trending_window')
        indexes = [
            models.Index(fields=['velocity_score']),
            models.Index(fields=['viral_coefficient']),
            models.Index(fields=['trending_window', 'calculated_at']),
            models.Index(fields=['expires_at'])
        ]
    
    def __str__(self):
        return f"Trending: {self.content_type}#{self.content_id} ({self.trending_window})"
    
    @property
    def cache_key(self):
        """Generate Redis cache key for this metric."""
        return f"trending:{self.content_type}:{self.content_id}:{self.trending_window}"


class CreatorMetric(models.Model):
    """
    Tracks creator reputation and performance metrics.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='creator_metrics'
    )
    
    # Reputation scores
    overall_reputation = models.FloatField(default=0.0)
    content_quality_score = models.FloatField(default=0.0)
    engagement_rate = models.FloatField(default=0.0)
    follower_growth_rate = models.FloatField(default=0.0)
    
    # Content statistics
    total_posts = models.PositiveIntegerField(default=0)
    total_engagements = models.PositiveIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)
    
    # Time-based tracking
    last_calculated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'creator_metrics'
        indexes = [
            models.Index(fields=['overall_reputation']),
            models.Index(fields=['content_quality_score']),
            models.Index(fields=['engagement_rate']),
            models.Index(fields=['last_calculated'])
        ]
    
    def __str__(self):
        return f"{self.user.username}'s Creator Metrics"
    
    def update_metrics(self):
        """Recalculate all metrics for this creator."""
        # This would contain the logic to recalculate metrics
        # based on recent performance data
        pass


class FeedDebugEvent(models.Model):
    """
    Logs feed generation events for debugging, A/B testing, and auditing.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='debug_events')
    
    # Event details
    event_type = models.CharField(
        max_length=30,
        choices=[
            ('feed_generated', 'Feed Generated'),
            ('composition_changed', 'Composition Changed'),
            ('ab_test_assigned', 'A/B Test Assigned'),
            ('cache_hit', 'Cache Hit'),
            ('cache_miss', 'Cache Miss')
        ]
    )
    
    # Event data (JSON)
    event_data = models.JSONField(default=dict)
    
    # Performance metrics
    generation_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # Context
    request_id = models.CharField(max_length=100, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feed_debug_events'
        indexes = [
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['request_id']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.event_type} at {self.created_at}"
