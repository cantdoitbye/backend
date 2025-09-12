from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class ContentItem(models.Model):
    """
    Abstract base class for all content types in the feed system.
    Provides common fields and methods for posts, communities, products, etc.
    """
    # Basic content information
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='%(class)s_created')
    
    # Content status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Engagement metrics (denormalized for performance)
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    
    # Calculated scores
    engagement_score = models.FloatField(default=0.0)
    quality_score = models.FloatField(default=0.0)
    trending_score = models.FloatField(default=0.0)
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['creator', 'created_at']),
            models.Index(fields=['engagement_score']),
            models.Index(fields=['quality_score']),
            models.Index(fields=['trending_score']),
            models.Index(fields=['is_active', 'published_at']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def content_type_name(self):
        """Return the lowercase name of this content type."""
        return self.__class__.__name__.lower()
    
    def calculate_engagement_score(self):
        """Calculate the engagement score based on interactions."""
        # Weighted engagement calculation
        score = (
            (self.like_count * 1.0) +
            (self.comment_count * 2.0) +
            (self.share_count * 3.0) +
            (self.view_count * 0.1)
        )
        
        # Apply time decay (newer content gets slight boost)
        if self.created_at:
            hours_old = (timezone.now() - self.created_at).total_seconds() / 3600
            time_factor = max(0.1, 1.0 - (hours_old / (24 * 7)))  # Decay over a week
            score *= time_factor
        
        self.engagement_score = score
        return score
    
    def update_engagement_metrics(self, metric_type, increment=1):
        """Update engagement metrics and recalculate scores."""
        if metric_type == 'view':
            self.view_count += increment
        elif metric_type == 'like':
            self.like_count += increment
        elif metric_type == 'share':
            self.share_count += increment
        elif metric_type == 'comment':
            self.comment_count += increment
        
        self.calculate_engagement_score()
        self.save(update_fields=[
            f'{metric_type}_count', 'engagement_score', 'updated_at'
        ])
    
    def publish(self):
        """Publish this content item."""
        self.published_at = timezone.now()
        self.is_active = True
        self.save(update_fields=['published_at', 'is_active', 'updated_at'])


class Post(ContentItem):
    """
    Social media post content type.
    """
    # Post-specific fields
    content = models.TextField()
    
    # Media attachments
    image_urls = models.JSONField(default=list, blank=True)
    video_url = models.URLField(blank=True)
    
    # Post type
    post_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text Only'),
            ('image', 'Image Post'),
            ('video', 'Video Post'),
            ('link', 'Link Share'),
            ('poll', 'Poll')
        ],
        default='text'
    )
    
    # Privacy settings
    visibility = models.CharField(
        max_length=10,
        choices=[
            ('public', 'Public'),
            ('friends', 'Friends'),
            ('private', 'Private')
        ],
        default='public'
    )
    
    # Location data
    location = models.CharField(max_length=255, blank=True)
    coordinates = models.JSONField(null=True, blank=True)  # {"lat": x, "lng": y}
    
    class Meta:
        db_table = 'posts'
        indexes = [
            models.Index(fields=['post_type', 'created_at']),
            models.Index(fields=['visibility', 'is_active']),
            models.Index(fields=['location'])
        ]
    
    def __str__(self):
        return f"Post by {self.creator.username}: {self.title[:50]}..."


class Community(ContentItem):
    """
    Community/Group content type.
    """
    # Community-specific fields
    category = models.CharField(
        max_length=50,
        choices=[
            ('technology', 'Technology'),
            ('entertainment', 'Entertainment'),
            ('sports', 'Sports'),
            ('lifestyle', 'Lifestyle'),
            ('business', 'Business'),
            ('education', 'Education'),
            ('health', 'Health'),
            ('other', 'Other')
        ]
    )
    
    # Community settings
    is_private = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=False)
    
    # Member management
    member_count = models.PositiveIntegerField(default=0)
    max_members = models.PositiveIntegerField(null=True, blank=True)
    
    # Community rules
    rules = models.TextField(blank=True)
    welcome_message = models.TextField(blank=True)
    
    # Visual branding
    avatar_url = models.URLField(blank=True)
    banner_url = models.URLField(blank=True)
    theme_color = models.CharField(max_length=7, blank=True)  # Hex color
    
    class Meta:
        db_table = 'communities'
        verbose_name_plural = 'Communities'
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['member_count']),
            models.Index(fields=['is_private', 'requires_approval'])
        ]
    
    def __str__(self):
        return f"Community: {self.title}"
    
    def add_member(self, user):
        """Add a user to this community."""
        membership, created = CommunityMembership.objects.get_or_create(
            community=self,
            user=user,
            defaults={'role': 'member', 'joined_at': timezone.now()}
        )
        if created:
            self.member_count += 1
            self.save(update_fields=['member_count'])
        return membership
    
    def remove_member(self, user):
        """Remove a user from this community."""
        try:
            membership = CommunityMembership.objects.get(community=self, user=user)
            membership.delete()
            self.member_count = max(0, self.member_count - 1)
            self.save(update_fields=['member_count'])
            return True
        except CommunityMembership.DoesNotExist:
            return False


class Product(ContentItem):
    """
    Product/Marketplace content type.
    """
    # Product-specific fields
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    # Product details
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=50, blank=True)
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    is_in_stock = models.BooleanField(default=True)
    
    # Product images
    primary_image_url = models.URLField(blank=True)
    gallery_urls = models.JSONField(default=list, blank=True)
    
    # Product categorization
    category = models.CharField(
        max_length=50,
        choices=[
            ('electronics', 'Electronics'),
            ('clothing', 'Clothing'),
            ('home', 'Home & Garden'),
            ('sports', 'Sports & Outdoors'),
            ('books', 'Books'),
            ('health', 'Health & Beauty'),
            ('toys', 'Toys & Games'),
            ('automotive', 'Automotive'),
            ('other', 'Other')
        ]
    )
    
    # Product attributes (size, color, etc.)
    attributes = models.JSONField(default=dict, blank=True)
    
    # Seller information
    seller = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='products_sold',
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'products'
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['price', 'currency']),
            models.Index(fields=['brand', 'model']),
            models.Index(fields=['is_in_stock', 'stock_quantity']),
            models.Index(fields=['seller'])
        ]
    
    def __str__(self):
        price_str = f" (${self.price})" if self.price else ""
        return f"Product: {self.title}{price_str}"
    
    @property
    def formatted_price(self):
        """Return formatted price string."""
        if self.price:
            return f"{self.currency} {self.price:.2f}"
        return "Price not available"
    
    def update_stock(self, quantity_change):
        """Update stock quantity and availability."""
        self.stock_quantity = max(0, self.stock_quantity + quantity_change)
        self.is_in_stock = self.stock_quantity > 0
        self.save(update_fields=['stock_quantity', 'is_in_stock'])


class Engagement(models.Model):
    """
    Generic engagement model that can track interactions with any content type.
    """
    # User who performed the engagement
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='engagements')
    
    # Generic foreign key to any content item
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Engagement type
    engagement_type = models.CharField(
        max_length=20,
        choices=[
            ('view', 'View'),
            ('like', 'Like'),
            ('dislike', 'Dislike'),
            ('share', 'Share'),
            ('comment', 'Comment'),
            ('bookmark', 'Bookmark'),
            ('report', 'Report')
        ]
    )
    
    # Engagement context
    source = models.CharField(
        max_length=30,
        choices=[
            ('feed', 'Feed'),
            ('search', 'Search'),
            ('profile', 'Profile'),
            ('trending', 'Trending'),
            ('notification', 'Notification'),
            ('direct', 'Direct Link')
        ],
        default='feed'
    )
    
    # Additional data (comment text, share message, etc.)
    data = models.JSONField(default=dict, blank=True)
    
    # Analytics
    session_id = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'engagements'
        unique_together = (
            ('user', 'content_type', 'object_id', 'engagement_type'),
        )
        indexes = [
            models.Index(fields=['user', 'engagement_type']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['engagement_type', 'created_at']),
            models.Index(fields=['source']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.engagement_type} {self.content_object}"
    
    def save(self, *args, **kwargs):
        """Update content item engagement metrics when saving."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update the content item's engagement metrics
        if is_new and self.content_object:
            self.content_object.update_engagement_metrics(self.engagement_type)


class CommunityMembership(models.Model):
    """
    Tracks community membership and roles.
    """
    community = models.ForeignKey(
        Community, 
        on_delete=models.CASCADE, 
        related_name='memberships'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='community_memberships'
    )
    
    # Membership role
    role = models.CharField(
        max_length=20,
        choices=[
            ('member', 'Member'),
            ('moderator', 'Moderator'),
            ('admin', 'Admin'),
            ('owner', 'Owner')
        ],
        default='member'
    )
    
    # Membership status
    status = models.CharField(
        max_length=15,
        choices=[
            ('active', 'Active'),
            ('pending', 'Pending Approval'),
            ('suspended', 'Suspended'),
            ('banned', 'Banned')
        ],
        default='active'
    )
    
    # Activity tracking
    post_count = models.PositiveIntegerField(default=0)
    last_active = models.DateTimeField(null=True, blank=True)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'community_memberships'
        unique_together = ('community', 'user')
        indexes = [
            models.Index(fields=['community', 'role']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['last_active'])
        ]
    
    def __str__(self):
        return f"{self.user.username} in {self.community.title} ({self.role})"
