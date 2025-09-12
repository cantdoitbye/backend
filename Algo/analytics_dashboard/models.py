from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json
from django.db import models


class ExperimentStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    RUNNING = 'running', 'Running'
    PAUSED = 'paused', 'Paused'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class ABTestExperiment(models.Model):
    """
    A/B Testing experiments for feed algorithm optimization
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Experiment configuration
    status = models.CharField(
        max_length=20, 
        choices=ExperimentStatus.choices, 
        default=ExperimentStatus.DRAFT
    )
    
    # Traffic allocation (percentage)
    traffic_allocation = models.FloatField(
        default=10.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(100.0)],
        help_text="Percentage of users to include in experiment"
    )
    
    # Control and treatment configurations
    control_config = models.JSONField(
        default=dict,
        help_text="Feed composition configuration for control group"
    )
    treatment_config = models.JSONField(
        default=dict,
        help_text="Feed composition configuration for treatment group"
    )
    
    # Experiment timeline
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    duration_days = models.IntegerField(
        default=14,
        validators=[MinValueValidator(1), MaxValueValidator(90)],
        help_text="Experiment duration in days"
    )
    
    # Success metrics
    primary_metric = models.CharField(
        max_length=50,
        default='engagement_rate',
        choices=[
            ('engagement_rate', 'Engagement Rate'),
            ('session_duration', 'Session Duration'),
            ('content_consumption', 'Content Consumption'),
            ('user_retention', 'User Retention'),
            ('conversion_rate', 'Conversion Rate')
        ]
    )
    
    # Statistical significance
    confidence_level = models.FloatField(
        default=95.0,
        validators=[MinValueValidator(80.0), MaxValueValidator(99.9)],
        help_text="Statistical confidence level for results"
    )
    minimum_sample_size = models.IntegerField(
        default=1000,
        help_text="Minimum users per group for statistical significance"
    )
    
    # Results and insights
    is_statistically_significant = models.BooleanField(default=False)
    winner = models.CharField(
        max_length=20,
        choices=[('control', 'Control'), ('treatment', 'Treatment'), ('inconclusive', 'Inconclusive')],
        blank=True
    )
    results_summary = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_experiments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ab_test_experiments'
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['created_by', 'status']),
            models.Index(fields=['primary_metric'])
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    @property
    def is_active(self):
        return self.status == ExperimentStatus.RUNNING
    
    @property
    def days_running(self):
        if self.start_date:
            return (timezone.now() - self.start_date).days
        return 0


class ExperimentParticipant(models.Model):
    """
    Users participating in A/B test experiments
    """
    experiment = models.ForeignKey(
        ABTestExperiment, 
        on_delete=models.CASCADE, 
        related_name='participants'
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Assignment
    group = models.CharField(
        max_length=20,
        choices=[('control', 'Control'), ('treatment', 'Treatment')]
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    # Participation tracking
    first_exposure = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'experiment_participants'
        unique_together = ('experiment', 'user')
        indexes = [
            models.Index(fields=['experiment', 'group']),
            models.Index(fields=['user', 'assigned_at']),
            models.Index(fields=['is_active'])
        ]
    
    def __str__(self):
        return f"{self.user.username} in {self.experiment.name} ({self.group})"


class ExperimentMetric(models.Model):
    """
    Metrics collected during A/B test experiments
    """
    experiment = models.ForeignKey(
        ABTestExperiment, 
        on_delete=models.CASCADE, 
        related_name='metrics'
    )
    participant = models.ForeignKey(
        ExperimentParticipant, 
        on_delete=models.CASCADE, 
        related_name='metrics'
    )
    
    # Metric data
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    metric_type = models.CharField(
        max_length=20,
        choices=[
            ('count', 'Count'),
            ('duration', 'Duration'),
            ('rate', 'Rate'),
            ('score', 'Score')
        ]
    )
    
    # Context
    session_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'experiment_metrics'
        indexes = [
            models.Index(fields=['experiment', 'metric_name']),
            models.Index(fields=['participant', 'recorded_at']),
            models.Index(fields=['recorded_at'])
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} ({self.participant.group})"


class AnalyticsDashboard(models.Model):
    """
    Custom dashboard configurations for analytics
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Dashboard configuration
    layout_config = models.JSONField(
        default=dict,
        help_text="Dashboard layout and widget configuration"
    )
    
    # Widget definitions
    widgets = models.JSONField(
        default=list,
        help_text="List of widgets and their configurations"
    )
    
    # Access control
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        blank=True, 
        related_name='accessible_dashboards'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_dashboards'
        indexes = [
            models.Index(fields=['created_by', 'is_public']),
            models.Index(fields=['created_at'])
        ]
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name


class RealTimeMetric(models.Model):
    """
    Real-time metrics for live dashboard updates
    """
    metric_name = models.CharField(max_length=100)
    metric_category = models.CharField(
        max_length=50,
        choices=[
            ('feed_performance', 'Feed Performance'),
            ('user_engagement', 'User Engagement'),
            ('system_health', 'System Health'),
            ('cache_performance', 'Cache Performance'),
            ('api_metrics', 'API Metrics')
        ]
    )
    
    # Metric data
    value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)  # ms, %, count, etc.
    
    # Aggregation info
    aggregation_window = models.CharField(
        max_length=10,
        choices=[
            ('1m', '1 Minute'),
            ('5m', '5 Minutes'),
            ('15m', '15 Minutes'),
            ('1h', '1 Hour'),
            ('1d', '1 Day')
        ],
        default='5m'
    )
    
    # Metadata
    timestamp = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'realtime_metrics'
        indexes = [
            models.Index(fields=['metric_name', 'timestamp']),
            models.Index(fields=['metric_category', 'timestamp']),
            models.Index(fields=['timestamp'])
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.metric_name}: {self.value} {self.unit}"


class UserBehaviorInsight(models.Model):
    """
    User behavior insights and patterns
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='behavior_insights')
    
    # Behavior patterns
    session_duration_avg = models.FloatField(default=0.0)  # minutes
    daily_active_hours = models.JSONField(default=list)  # hours of day when active
    preferred_content_types = models.JSONField(default=dict)  # content type preferences
    engagement_patterns = models.JSONField(default=dict)  # engagement behavior
    
    # Feed preferences
    optimal_feed_composition = models.JSONField(
        default=dict,
        help_text="AI-determined optimal feed composition for this user"
    )
    
    # Performance metrics
    engagement_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Overall engagement score (0-1)"
    )
    retention_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="User retention score (0-1)"
    )
    
    # Insights metadata
    last_calculated = models.DateTimeField(auto_now=True)
    data_points_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'user_behavior_insights'
        indexes = [
            models.Index(fields=['user', 'last_calculated']),
            models.Index(fields=['engagement_score']),
            models.Index(fields=['retention_score'])
        ]
    
    def __str__(self):
        return f"Insights for {self.user.username}"
