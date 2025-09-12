from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class UserProfile(AbstractUser):
    """Extended user model with feed preferences and social features."""
    
    # Core Profile Information
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Feed Preferences (Dynamic Configuration)
    feed_composition = models.JSONField(default=dict, help_text="Custom feed composition ratios")
    feed_preferences = models.JSONField(default=dict, help_text="User's feed preferences and settings")
    
    # Privacy Settings
    is_private = models.BooleanField(default=False)
    allow_recommendations = models.BooleanField(default=True)
    
    # Engagement Tracking
    total_connections = models.PositiveIntegerField(default=0)
    engagement_score = models.FloatField(default=0.0)
    last_active = models.DateTimeField(auto_now=True)
    
    # A/B Testing
    ab_test_group = models.CharField(max_length=50, blank=True, help_text="A/B testing group identifier")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_profile'
        indexes = [
            models.Index(fields=['engagement_score']),
            models.Index(fields=['last_active']),
            models.Index(fields=['ab_test_group']),
        ]
    
    def get_feed_composition(self):
        """Get user's feed composition or default if not set."""
        from django.conf import settings
        return self.feed_composition or settings.FEED_CONFIG['DEFAULT_COMPOSITION']
    
    def update_engagement_score(self):
        """Calculate and update user engagement score."""
        from scoring_engines.utils import calculate_user_engagement
        self.engagement_score = calculate_user_engagement(self)
        self.save(update_fields=['engagement_score'])
    
    def __str__(self):
        return f"{self.username} ({self.email})"


class Connection(models.Model):
    """User connections with circle classification for feed algorithm."""
    
    CIRCLE_CHOICES = [
        ('inner', 'Inner Circle'),      # Close friends/family - weight 1.0
        ('outer', 'Outer Circle'),      # Friends/colleagues - weight 0.7  
        ('universe', 'Universe'),       # Acquaintances/follows - weight 0.4
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('blocked', 'Blocked'),
    ]
    
    from_user = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE, 
        related_name='connections_from'
    )
    to_user = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE, 
        related_name='connections_to'
    )
    
    circle_type = models.CharField(
        max_length=10, 
        choices=CIRCLE_CHOICES, 
        default='universe',
        help_text="Connection strength for feed algorithm weighting"
    )
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Interaction tracking for dynamic circle adjustment
    interaction_count = models.PositiveIntegerField(default=0)
    last_interaction = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_connection'
        unique_together = ['from_user', 'to_user']
        indexes = [
            models.Index(fields=['from_user', 'status']),
            models.Index(fields=['circle_type']),
            models.Index(fields=['last_interaction']),
        ]
    
    def get_circle_weight(self):
        """Get the weight for this connection's circle type."""
        from django.conf import settings
        return settings.FEED_CONFIG['CIRCLE_WEIGHTS'].get(self.circle_type, 0.4)
    
    def update_interaction(self):
        """Update interaction tracking and potentially adjust circle."""
        from django.utils import timezone
        self.interaction_count += 1
        self.last_interaction = timezone.now()
        
        # Auto-adjust circle based on interaction frequency
        if self.interaction_count > 50 and self.circle_type == 'universe':
            self.circle_type = 'outer'
        elif self.interaction_count > 200 and self.circle_type == 'outer':
            self.circle_type = 'inner'
        
        self.save()
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.circle_type})"


class Interest(models.Model):
    """User interests for content recommendation."""
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    # Popularity and trending metrics
    follower_count = models.PositiveIntegerField(default=0)
    trending_score = models.FloatField(default=0.0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users_interest'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['trending_score']),
            models.Index(fields=['follower_count']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class UserInterest(models.Model):
    """User-Interest relationship with engagement tracking."""
    
    INTEREST_TYPE_CHOICES = [
        ('explicit', 'Explicitly Selected'),
        ('inferred', 'Algorithmically Inferred'),
    ]
    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user_interests')
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE, related_name='interested_users')
    
    interest_type = models.CharField(max_length=10, choices=INTEREST_TYPE_CHOICES, default='explicit')
    strength = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.5,
        help_text="Interest strength (0.0 to 1.0)"
    )
    
    # Engagement tracking
    engagement_count = models.PositiveIntegerField(default=0)
    last_engaged = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_user_interest'
        unique_together = ['user', 'interest']
        indexes = [
            models.Index(fields=['user', 'strength']),
            models.Index(fields=['interest_type']),
        ]
    
    def update_engagement(self):
        """Update interest engagement and strength."""
        from django.utils import timezone
        self.engagement_count += 1
        self.last_engaged = timezone.now()
        
        # Gradually increase strength based on engagement
        self.strength = min(1.0, self.strength + 0.01)
        self.save()
    
    def __str__(self):
        return f"{self.user.username} -> {self.interest.name} ({self.strength})"


class InterestCollection(models.Model):
    """Collections of related interests for better organization."""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    interests = models.ManyToManyField(Interest, related_name='collections')
    
    # System or user-created
    is_system = models.BooleanField(default=False)
    creator = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='created_collections'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users_interest_collection'
        indexes = [
            models.Index(fields=['is_system']),
            models.Index(fields=['creator']),
        ]
    
    def __str__(self):
        return self.name