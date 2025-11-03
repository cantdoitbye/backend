# truststream/model_extensions.py

"""
TrustStream Model Extensions - Extensions to existing models for TrustStream integration

This module provides extensions to existing models to add TrustStream functionality
without modifying the original model files. It uses Django's model inheritance
and relationship patterns to seamlessly integrate trust scoring and moderation.

Key Features:
- Non-invasive extensions to existing models
- Trust score integration for Users, Posts, Communities
- Moderation status tracking
- Performance optimization through caching
- Backward compatibility with existing code
"""

from neomodel import (
    StringProperty, FloatProperty, BooleanProperty, DateTimeProperty,
    IntegerProperty, RelationshipTo, ArrayProperty, JSONProperty
)
from django.db import models
from datetime import datetime


# ============================================================================
# NEO4J MODEL EXTENSIONS
# ============================================================================

class UserTrustExtension:
    """
    Extension mixin for Users model to add TrustStream functionality.
    
    This mixin adds trust-related fields and relationships to the existing
    Users model without modifying the original model definition.
    """
    
    # Trust Scoring Fields
    trust_score = FloatProperty(default=2.0)               # Overall trust score (0.0-5.0)
    trust_rank = StringProperty(default='bronze')          # Current trust ranking
    trust_percentile = FloatProperty(default=50.0)         # Percentile among all users
    
    # Behavioral Analysis
    content_quality_score = FloatProperty(default=2.0)     # Quality of user's content
    engagement_authenticity = FloatProperty(default=2.0)   # Authenticity of interactions
    violation_risk_score = FloatProperty(default=0.0)      # Risk of policy violations
    
    # Moderation Status
    moderation_status = StringProperty(default='active')    # active, flagged, suspended, banned
    last_violation_date = DateTimeProperty()               # Most recent violation
    violation_count = IntegerProperty(default=0)           # Total violations
    warning_count = IntegerProperty(default=0)             # Total warnings received
    
    # Trust Network
    trusted_by_count = IntegerProperty(default=0)          # Users who trust this user
    trusts_count = IntegerProperty(default=0)              # Users this user trusts
    
    # TrustStream Timestamps
    trust_last_updated = DateTimeProperty(default_now=True)
    last_moderated = DateTimeProperty()
    
    # TrustStream Relationships
    trust_profile = RelationshipTo('truststream.models.TrustProfile', 'HAS_TRUST_PROFILE')
    moderation_decisions = RelationshipTo('truststream.models.ModerationDecision', 'HAS_MODERATION_DECISION')


class PostTrustExtension:
    """
    Extension mixin for Post model to add TrustStream moderation and scoring.
    
    This mixin adds moderation status, trust scoring, and AI analysis results
    to posts for comprehensive content moderation.
    """
    
    # Content Trust Scoring
    content_trust_score = FloatProperty(default=2.0)       # AI-assessed content quality
    authenticity_score = FloatProperty(default=2.0)        # Authenticity assessment
    safety_score = FloatProperty(default=2.0)              # Content safety rating
    
    # Moderation Status
    moderation_status = StringProperty(default='pending')   # pending, approved, flagged, blocked
    moderation_confidence = FloatProperty(default=0.0)     # AI confidence in decision
    human_reviewed = BooleanProperty(default=False)        # Human moderator involvement
    
    # Violation Detection
    violation_types = ArrayProperty(StringProperty())       # Types of violations detected
    violation_severity = FloatProperty(default=0.0)        # Severity score (0.0-1.0)
    risk_level = StringProperty(default='low')             # low, medium, high
    
    # AI Analysis Results
    ai_analysis_results = JSONProperty()                   # Detailed AI analysis
    analyzing_agents = ArrayProperty(StringProperty())     # Agents that analyzed content
    consensus_score = FloatProperty(default=0.0)          # Agreement between agents
    
    # Appeal and Review
    user_appealed = BooleanProperty(default=False)         # User appealed decision
    appeal_outcome = StringProperty()                      # Result of appeal
    appeal_date = DateTimeProperty()                       # When appeal was made
    
    # Performance Metrics
    engagement_quality = FloatProperty(default=2.0)        # Quality of engagement received
    viral_potential = FloatProperty(default=0.0)          # Potential for viral spread
    
    # TrustStream Timestamps
    moderated_at = DateTimeProperty()
    trust_last_updated = DateTimeProperty(default_now=True)
    
    # TrustStream Relationships
    moderation_decision = RelationshipTo('truststream.models.ModerationDecision', 'HAS_MODERATION_DECISION')
    agent_analyses = RelationshipTo('truststream.models.AgentAnalysis', 'HAS_AGENT_ANALYSIS')


class CommunityTrustExtension:
    """
    Extension mixin for Community model to add TrustStream community health monitoring.
    
    This mixin adds community health metrics, moderation settings, and trust-based
    features to communities for better community management.
    """
    
    # Community Health Metrics
    community_health_score = FloatProperty(default=2.0)    # Overall community health
    content_quality_avg = FloatProperty(default=2.0)       # Average content quality
    member_trust_avg = FloatProperty(default=2.0)          # Average member trust score
    engagement_authenticity = FloatProperty(default=2.0)   # Authenticity of engagement
    
    # Moderation Settings
    auto_moderation_enabled = BooleanProperty(default=True) # Enable AI moderation
    moderation_strictness = StringProperty(default='medium') # low, medium, high, strict
    trust_threshold = FloatProperty(default=1.0)           # Minimum trust for participation
    
    # Community Safety
    violation_rate = FloatProperty(default=0.0)            # Rate of violations
    toxicity_score = FloatProperty(default=0.0)           # Community toxicity level
    safety_rating = StringProperty(default='safe')         # safe, caution, unsafe
    
    # Trust-Based Features
    trust_based_permissions = BooleanProperty(default=False) # Use trust for permissions
    high_trust_benefits = BooleanProperty(default=False)   # Special benefits for trusted users
    trust_verification_required = BooleanProperty(default=False) # Require trust verification
    
    # Moderation Activity
    total_moderations = IntegerProperty(default=0)         # Total moderation actions
    auto_approvals = IntegerProperty(default=0)            # Automatic approvals
    human_reviews = IntegerProperty(default=0)             # Human moderator reviews
    
    # Community Analytics
    growth_rate = FloatProperty(default=0.0)               # Member growth rate
    retention_rate = FloatProperty(default=0.0)            # Member retention rate
    activity_score = FloatProperty(default=2.0)            # Community activity level
    
    # TrustStream Timestamps
    health_last_updated = DateTimeProperty(default_now=True)
    last_moderated = DateTimeProperty()
    
    # TrustStream Relationships
    community_moderations = RelationshipTo('truststream.models.ModerationDecision', 'HAS_COMMUNITY_MODERATION')
    trust_analytics = RelationshipTo('truststream.models.TrustNetworkAnalytics', 'HAS_TRUST_ANALYTICS')


class CommentTrustExtension:
    """
    Extension mixin for Comment model to add TrustStream comment moderation.
    
    This mixin adds moderation capabilities specifically designed for comments,
    including thread-level analysis and context-aware moderation.
    """
    
    # Comment Trust Scoring
    comment_trust_score = FloatProperty(default=2.0)       # Comment quality score
    relevance_score = FloatProperty(default=2.0)          # Relevance to parent content
    constructiveness = FloatProperty(default=2.0)         # Constructive contribution
    
    # Moderation Status
    moderation_status = StringProperty(default='pending')  # pending, approved, flagged, hidden
    moderation_reason = StringProperty()                   # Reason for moderation action
    auto_moderated = BooleanProperty(default=False)       # Automatically moderated
    
    # Context Analysis
    thread_toxicity = FloatProperty(default=0.0)          # Toxicity in comment thread
    parent_context_score = FloatProperty(default=2.0)     # Context from parent content
    conversation_quality = FloatProperty(default=2.0)      # Overall conversation quality
    
    # Behavioral Indicators
    spam_likelihood = FloatProperty(default=0.0)          # Likelihood of being spam
    harassment_indicators = ArrayProperty(StringProperty()) # Harassment pattern indicators
    manipulation_risk = FloatProperty(default=0.0)        # Risk of manipulation
    
    # TrustStream Timestamps
    moderated_at = DateTimeProperty()
    trust_analyzed_at = DateTimeProperty()
    
    # TrustStream Relationships
    comment_moderation = RelationshipTo('truststream.models.ModerationDecision', 'HAS_COMMENT_MODERATION')


# ============================================================================
# POSTGRESQL MODEL EXTENSIONS
# ============================================================================

class UserTrustCache(models.Model):
    """
    PostgreSQL cache for user trust data for fast lookups.
    
    This model caches frequently accessed user trust information
    to improve performance of trust-based features and queries.
    """
    user_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Cached Trust Scores
    trust_score = models.FloatField(default=2.0)
    trust_rank = models.CharField(max_length=20, default='bronze')
    trust_percentile = models.FloatField(default=50.0)
    
    # Cached Behavioral Scores
    content_quality_score = models.FloatField(default=2.0)
    engagement_authenticity = models.FloatField(default=2.0)
    violation_risk_score = models.FloatField(default=0.0)
    
    # Cached Status
    moderation_status = models.CharField(max_length=20, default='active')
    violation_count = models.IntegerField(default=0)
    warning_count = models.IntegerField(default=0)
    
    # Cache Metadata
    last_updated = models.DateTimeField(auto_now=True)
    cache_version = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'truststream_user_cache'
        indexes = [
            models.Index(fields=['trust_score']),
            models.Index(fields=['trust_rank']),
            models.Index(fields=['moderation_status']),
        ]


class ContentModerationCache(models.Model):
    """
    PostgreSQL cache for content moderation results.
    
    This model caches moderation decisions and analysis results
    for fast content filtering and display decisions.
    """
    content_type = models.CharField(max_length=50)
    content_id = models.CharField(max_length=255)
    
    # Cached Moderation Results
    moderation_status = models.CharField(max_length=20)
    moderation_confidence = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=20, default='low')
    
    # Cached Scores
    content_trust_score = models.FloatField(default=2.0)
    safety_score = models.FloatField(default=2.0)
    authenticity_score = models.FloatField(default=2.0)
    
    # Cached Analysis
    violation_types = models.JSONField(default=list)
    analyzing_agents = models.JSONField(default=list)
    consensus_score = models.FloatField(default=0.0)
    
    # Cache Metadata
    moderated_at = models.DateTimeField()
    cached_at = models.DateTimeField(auto_now=True)
    cache_version = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'truststream_content_cache'
        unique_together = ['content_type', 'content_id']
        indexes = [
            models.Index(fields=['moderation_status']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['content_trust_score']),
        ]


class CommunityHealthCache(models.Model):
    """
    PostgreSQL cache for community health metrics.
    
    This model caches community health data for dashboard
    displays and community management features.
    """
    community_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Cached Health Metrics
    community_health_score = models.FloatField(default=2.0)
    content_quality_avg = models.FloatField(default=2.0)
    member_trust_avg = models.FloatField(default=2.0)
    engagement_authenticity = models.FloatField(default=2.0)
    
    # Cached Safety Metrics
    violation_rate = models.FloatField(default=0.0)
    toxicity_score = models.FloatField(default=0.0)
    safety_rating = models.CharField(max_length=20, default='safe')
    
    # Cached Activity Metrics
    total_moderations = models.IntegerField(default=0)
    auto_approvals = models.IntegerField(default=0)
    human_reviews = models.IntegerField(default=0)
    
    # Cache Metadata
    last_updated = models.DateTimeField(auto_now=True)
    cache_version = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'truststream_community_cache'
        indexes = [
            models.Index(fields=['community_health_score']),
            models.Index(fields=['safety_rating']),
            models.Index(fields=['violation_rate']),
        ]


# ============================================================================
# EXTENSION APPLICATION HELPERS
# ============================================================================

def apply_truststream_extensions():
    """
    Apply TrustStream extensions to existing models.
    
    This function dynamically adds TrustStream fields and methods
    to existing models at runtime, enabling TrustStream functionality
    without modifying original model files.
    """
    from auth_manager.models import Users, Profile
    from post.models import Post, Comment
    from community.models import Community
    
    # Apply User extensions
    for attr_name in dir(UserTrustExtension):
        if not attr_name.startswith('_'):
            attr_value = getattr(UserTrustExtension, attr_name)
            if hasattr(attr_value, '__class__') and 'Property' in str(attr_value.__class__):
                setattr(Users, f'truststream_{attr_name}', attr_value)
    
    # Apply Post extensions
    for attr_name in dir(PostTrustExtension):
        if not attr_name.startswith('_'):
            attr_value = getattr(PostTrustExtension, attr_name)
            if hasattr(attr_value, '__class__') and 'Property' in str(attr_value.__class__):
                setattr(Post, f'truststream_{attr_name}', attr_value)
    
    # Apply Community extensions
    for attr_name in dir(CommunityTrustExtension):
        if not attr_name.startswith('_'):
            attr_value = getattr(CommunityTrustExtension, attr_name)
            if hasattr(attr_value, '__class__') and 'Property' in str(attr_value.__class__):
                setattr(Community, f'truststream_{attr_name}', attr_value)
    
    # Apply Comment extensions
    for attr_name in dir(CommentTrustExtension):
        if not attr_name.startswith('_'):
            attr_value = getattr(CommentTrustExtension, attr_name)
            if hasattr(attr_value, '__class__') and 'Property' in str(attr_value.__class__):
                setattr(Comment, f'truststream_{attr_name}', attr_value)


def get_truststream_fields_for_model(model_class):
    """
    Get all TrustStream fields for a given model class.
    
    Args:
        model_class: The model class to get TrustStream fields for
        
    Returns:
        dict: Dictionary of TrustStream field names and their properties
    """
    truststream_fields = {}
    
    for attr_name in dir(model_class):
        if attr_name.startswith('truststream_'):
            field_name = attr_name.replace('truststream_', '')
            truststream_fields[field_name] = getattr(model_class, attr_name)
    
    return truststream_fields


def initialize_truststream_for_existing_data():
    """
    Initialize TrustStream fields for existing data in the database.
    
    This function sets default values for TrustStream fields on existing
    records that were created before TrustStream was implemented.
    """
    from auth_manager.models import Users
    from post.models import Post
    from community.models import Community
    
    # Initialize default trust scores for existing users
    users_without_trust = Users.nodes.filter(trust_score__isnull=True)
    for user in users_without_trust:
        user.trust_score = 2.0
        user.trust_rank = 'bronze'
        user.trust_percentile = 50.0
        user.moderation_status = 'active'
        user.save()
    
    # Initialize moderation status for existing posts
    posts_without_moderation = Post.nodes.filter(moderation_status__isnull=True)
    for post in posts_without_moderation:
        post.moderation_status = 'approved'  # Assume existing posts are approved
        post.content_trust_score = 2.0
        post.safety_score = 2.0
        post.save()
    
    # Initialize health scores for existing communities
    communities_without_health = Community.nodes.filter(community_health_score__isnull=True)
    for community in communities_without_health:
        community.community_health_score = 2.0
        community.safety_rating = 'safe'
        community.auto_moderation_enabled = True
        community.save()


# ============================================================================
# MIGRATION HELPERS
# ============================================================================

class TrustStreamMigrationHelper:
    """
    Helper class for managing TrustStream database migrations and updates.
    
    This class provides utilities for safely migrating existing data
    to include TrustStream functionality and maintaining data integrity.
    """
    
    @staticmethod
    def create_trust_profiles_for_existing_users():
        """Create TrustProfile nodes for all existing users."""
        from auth_manager.models import Users
        from truststream.models import TrustProfile
        
        users_without_trust_profile = Users.nodes.all()
        
        for user in users_without_trust_profile:
            # Check if trust profile already exists
            existing_profile = TrustProfile.nodes.filter(user_id=user.user_id).first()
            
            if not existing_profile:
                trust_profile = TrustProfile(
                    user_id=user.user_id,
                    iq_score=2.0,
                    appeal_score=2.0,
                    social_score=2.0,
                    humanity_score=2.0,
                    overall_trust_score=2.0,
                    trust_rank='bronze'
                ).save()
                
                # Create relationship
                user.trust_profile.connect(trust_profile)
    
    @staticmethod
    def populate_cache_tables():
        """Populate PostgreSQL cache tables with current data."""
        from auth_manager.models import Users
        from truststream.model_extensions import UserTrustCache
        
        for user in Users.nodes.all():
            cache_entry, created = UserTrustCache.objects.get_or_create(
                user_id=user.user_id,
                defaults={
                    'trust_score': getattr(user, 'trust_score', 2.0),
                    'trust_rank': getattr(user, 'trust_rank', 'bronze'),
                    'trust_percentile': getattr(user, 'trust_percentile', 50.0),
                    'moderation_status': getattr(user, 'moderation_status', 'active'),
                }
            )
    
    @staticmethod
    def validate_truststream_integration():
        """Validate that TrustStream integration is working correctly."""
        from auth_manager.models import Users
        from truststream.models import TrustProfile
        
        # Check that all users have trust profiles
        users_count = Users.nodes.count()
        trust_profiles_count = TrustProfile.nodes.count()
        
        if users_count != trust_profiles_count:
            print(f"Warning: {users_count} users but {trust_profiles_count} trust profiles")
            return False
        
        # Check that cache tables are populated
        from truststream.model_extensions import UserTrustCache
        cache_count = UserTrustCache.objects.count()
        
        if cache_count != users_count:
            print(f"Warning: {users_count} users but {cache_count} cache entries")
            return False
        
        print("TrustStream integration validation passed")
        return True