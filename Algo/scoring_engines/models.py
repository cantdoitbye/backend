from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class ScoringAlgorithm(models.Model):
    """
    Configuration for different scoring algorithms in the system.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Algorithm configuration
    algorithm_type = models.CharField(
        max_length=30,
        choices=[
            ('personal_connections', 'Personal Connections'),
            ('interest_based', 'Interest Based'),
            ('trending', 'Trending Content'),
            ('discovery', 'Discovery'),
            ('community', 'Community Based'),
            ('product', 'Product Recommendation')
        ]
    )
    
    # Scoring weights and parameters
    config = models.JSONField(default=dict)
    
    # Algorithm status
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20, default='1.0')
    
    # Performance tracking
    last_executed = models.DateTimeField(null=True, blank=True)
    execution_count = models.PositiveIntegerField(default=0)
    average_execution_time_ms = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'scoring_algorithms'
        indexes = [
            models.Index(fields=['algorithm_type', 'is_active']),
            models.Index(fields=['last_executed']),
            models.Index(fields=['version'])
        ]
    
    def __str__(self):
        return f"{self.name} (v{self.version})"
    
    def update_performance_metrics(self, execution_time_ms):
        """Update algorithm performance metrics."""
        self.execution_count += 1
        self.last_executed = timezone.now()
        
        # Calculate running average
        if self.average_execution_time_ms == 0:
            self.average_execution_time_ms = execution_time_ms
        else:
            # Weighted average (give more weight to recent executions)
            weight = 0.1
            self.average_execution_time_ms = (
                (1 - weight) * self.average_execution_time_ms + 
                weight * execution_time_ms
            )
        
        self.save(update_fields=[
            'execution_count', 'last_executed', 'average_execution_time_ms'
        ])


class PersonalConnectionsScore(models.Model):
    """
    Caches personal connections scoring for users.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='connection_scores')
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_object_id = models.PositiveIntegerField()
    
    # Scoring components
    inner_circle_score = models.FloatField(default=0.0)
    outer_circle_score = models.FloatField(default=0.0)
    universe_score = models.FloatField(default=0.0)
    
    # Final weighted score
    total_score = models.FloatField(default=0.0)
    
    # Score metadata
    connection_count = models.PositiveIntegerField(default=0)
    calculation_method = models.CharField(max_length=50, blank=True)
    
    calculated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'personal_connections_scores'
        unique_together = ('user', 'target_content_type', 'target_object_id')
        indexes = [
            models.Index(fields=['user', 'total_score']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['calculated_at'])
        ]
    
    def __str__(self):
        return f"Connection score for {self.user.username}: {self.total_score}"
    
    @property
    def is_expired(self):
        """Check if this score has expired."""
        return timezone.now() > self.expires_at


class InterestBasedScore(models.Model):
    """
    Caches interest-based scoring for content items.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interest_scores')
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_object_id = models.PositiveIntegerField()
    
    # Interest matching scores
    explicit_interests_score = models.FloatField(default=0.0)
    inferred_interests_score = models.FloatField(default=0.0)
    behavioral_interests_score = models.FloatField(default=0.0)
    
    # Final weighted score
    total_score = models.FloatField(default=0.0)
    
    # Interest match details
    matched_interests = models.JSONField(default=list)
    interest_strength_avg = models.FloatField(default=0.0)
    
    calculated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'interest_based_scores'
        unique_together = ('user', 'target_content_type', 'target_object_id')
        indexes = [
            models.Index(fields=['user', 'total_score']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['interest_strength_avg'])
        ]
    
    def __str__(self):
        return f"Interest score for {self.user.username}: {self.total_score}"


class TrendingScore(models.Model):
    """
    Calculated trending scores for content items.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    
    # Trending components
    velocity_score = models.FloatField(default=0.0)
    viral_coefficient = models.FloatField(default=0.0)
    engagement_velocity = models.FloatField(default=0.0)
    time_decay_factor = models.FloatField(default=1.0)
    
    # Final trending score
    total_score = models.FloatField(default=0.0)
    
    # Trending window
    window_hours = models.PositiveIntegerField(default=24)
    
    # Score metadata
    engagement_count = models.PositiveIntegerField(default=0)
    unique_users = models.PositiveIntegerField(default=0)
    
    calculated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'trending_scores'
        unique_together = ('content_type', 'object_id', 'window_hours')
        indexes = [
            models.Index(fields=['total_score', 'expires_at']),
            models.Index(fields=['content_type', 'calculated_at']),
            models.Index(fields=['window_hours', 'total_score'])
        ]
    
    def __str__(self):
        content_name = f"{self.content_type.name}#{self.object_id}"
        return f"Trending score for {content_name}: {self.total_score}"


class DiscoveryScore(models.Model):
    """
    Discovery and serendipity scores for content recommendation.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='discovery_scores')
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_object_id = models.PositiveIntegerField()
    
    # Discovery components
    collaborative_filtering_score = models.FloatField(default=0.0)
    serendipity_score = models.FloatField(default=0.0)
    diversity_score = models.FloatField(default=0.0)
    novelty_score = models.FloatField(default=0.0)
    
    # Final discovery score
    total_score = models.FloatField(default=0.0)
    
    # Discovery metadata
    similar_users = models.JSONField(default=list)
    recommendation_reason = models.CharField(max_length=100, blank=True)
    
    calculated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'discovery_scores'
        unique_together = ('user', 'target_content_type', 'target_object_id')
        indexes = [
            models.Index(fields=['user', 'total_score']),
            models.Index(fields=['total_score', 'expires_at']),
            models.Index(fields=['serendipity_score'])
        ]
    
    def __str__(self):
        return f"Discovery score for {self.user.username}: {self.total_score}"


class ScoringWeight(models.Model):
    """
    Configurable weights for different scoring factors.
    Allows fine-tuning of the scoring system without code changes.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Weight configuration
    weight_value = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)]
    )
    
    # Scope of the weight
    scope = models.CharField(
        max_length=20,
        choices=[
            ('global', 'Global'),
            ('content_type', 'Content Type Specific'),
            ('user_segment', 'User Segment Specific'),
            ('experimental', 'A/B Testing')
        ],
        default='global'
    )
    
    # Additional configuration
    config = models.JSONField(default=dict, blank=True)
    
    # Status and versioning
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=10, default='1.0')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'scoring_weights'
        indexes = [
            models.Index(fields=['scope', 'is_active']),
            models.Index(fields=['name', 'version'])
        ]
    
    def __str__(self):
        return f"{self.name}: {self.weight_value}"


class ScoreAuditLog(models.Model):
    """
    Audit log for scoring calculations and changes.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Audit event details
    event_type = models.CharField(
        max_length=30,
        choices=[
            ('score_calculated', 'Score Calculated'),
            ('weight_changed', 'Weight Changed'),
            ('algorithm_updated', 'Algorithm Updated'),
            ('cache_cleared', 'Cache Cleared'),
            ('performance_issue', 'Performance Issue')
        ]
    )
    
    # Event details
    event_data = models.JSONField(default=dict)
    
    # Performance metrics
    execution_time_ms = models.FloatField(null=True, blank=True)
    
    # Context
    session_id = models.CharField(max_length=100, blank=True)
    request_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'score_audit_logs'
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['execution_time_ms']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"{self.event_type} at {self.created_at}"
