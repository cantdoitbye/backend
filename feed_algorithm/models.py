from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class UserProfile(models.Model):
    """Extended user profile for feed customization and preferences."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feed_profile')
    
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'feed_user_profiles'
        indexes = [
            models.Index(fields=['last_active']),
            models.Index(fields=['total_engagement_score']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"{self.user.username}'s Feed Profile"

class FeedComposition(models.Model):
    """Configurable feed composition settings per user."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='feed_composition'
    )
    
    # Content type ratios (must sum to 1.0)
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
    
    # Experiment tracking
    experiment_group = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'feed_compositions'
    
    def __str__(self):
        return f"Feed Composition for {self.user.username}"
    
    def clean(self):
        """Validate that all percentages sum to 1.0."""
        from django.core.exceptions import ValidationError
        total = sum([
            self.personal_connections,
            self.interest_based,
            self.trending_content,
            self.discovery_content,
            self.community_content,
            self.product_content
        ])
        
        if not 0.99 <= total <= 1.01:  # Allow for floating point imprecision
            raise ValidationError("Feed composition ratios must sum to 1.0")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def composition_dict(self):
        """Return composition as a dictionary."""
        return {
            'personal_connections': self.personal_connections,
            'interest_based': self.interest_based,
            'trending_content': self.trending_content,
            'discovery_content': self.discovery_content,
            'community_content': self.community_content,
            'product_content': self.product_content,
        }
