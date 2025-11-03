# truststream/models.py

"""
TrustStream Database Models - Neo4j and PostgreSQL extensions for TrustStream v4.4

This module defines all TrustStream-specific database models and extensions to existing models.
It includes Neo4j graph models for trust relationships and PostgreSQL models for caching and analytics.

Key Components:
- TrustProfile: Core trust scoring and user reputation
- ModerationDecision: AI moderation decisions and audit trails
- AgentAnalysis: Individual agent analysis results
- TrustRelationship: Trust-based relationships between users
- Model extensions for existing Users, Posts, Communities, etc.
"""

from neomodel import (
    StructuredNode, StringProperty, IntegerProperty, FloatProperty, 
    DateTimeProperty, BooleanProperty, UniqueIdProperty, RelationshipTo, 
    RelationshipFrom, ArrayProperty, JSONProperty
)
from django_neomodel import DjangoNode
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from enum import Enum
import json


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class TrustRank(Enum):
    """Trust ranking system for users based on their trust scores"""
    UNVERIFIED = "unverified"      # 0.0-1.0: New or problematic users
    BRONZE = "bronze"              # 1.0-2.0: Basic trust level
    SILVER = "silver"              # 2.0-3.0: Good reputation
    GOLD = "gold"                  # 3.0-4.0: High trust level
    PLATINUM = "platinum"          # 4.0-4.5: Exceptional reputation
    DIAMOND = "diamond"            # 4.5-5.0: Elite trust status

class ModerationAction(Enum):
    """Possible moderation actions that can be taken"""
    APPROVE = "approve"            # Content is safe and approved
    FLAG = "flag"                  # Content needs human review
    BLOCK = "block"                # Content is blocked/hidden
    REMOVE = "remove"              # Content is permanently removed
    WARN = "warn"                  # User receives a warning
    SUSPEND = "suspend"            # User is temporarily suspended
    BAN = "ban"                    # User is permanently banned

class ContentType(Enum):
    """Types of content that can be moderated"""
    POST = "post"
    COMMENT = "comment"
    MESSAGE = "message"
    PROFILE = "profile"
    COMMUNITY = "community"
    STORY = "story"


# ============================================================================
# CORE TRUSTSTREAM NEO4J MODELS
# ============================================================================

class TrustProfile(DjangoNode, StructuredNode):
    """
    Core TrustStream profile containing comprehensive trust scoring and reputation data.
    
    This model serves as the central hub for all trust-related information about a user,
    including their 4-layer trust scores, behavioral patterns, moderation history,
    and relationships with other trusted users.
    """
    uid = UniqueIdProperty()
    user_id = StringProperty(unique_index=True, required=True)  # Links to Users.user_id
    
    # 4-Layer Trust Pyramid Scores (0.0-5.0 scale)
    iq_score = FloatProperty(default=2.0)          # Intelligence and content quality
    appeal_score = FloatProperty(default=2.0)      # Attractiveness and engagement
    social_score = FloatProperty(default=2.0)      # Social connections and influence
    humanity_score = FloatProperty(default=2.0)    # Authenticity and human behavior
    
    # Calculated Trust Metrics
    overall_trust_score = FloatProperty(default=2.0)  # Weighted average of all layers
    trust_rank = StringProperty(default=TrustRank.BRONZE.value)  # Current trust ranking
    trust_percentile = FloatProperty(default=50.0)    # Percentile ranking among all users
    
    # Behavioral Analysis
    content_quality_score = FloatProperty(default=2.0)    # Quality of user's content
    engagement_authenticity = FloatProperty(default=2.0)  # Authenticity of interactions
    community_contribution = FloatProperty(default=2.0)   # Positive community impact
    violation_risk_score = FloatProperty(default=0.0)     # Risk of policy violations
    
    # Moderation History
    total_violations = IntegerProperty(default=0)          # Total policy violations
    recent_violations = IntegerProperty(default=0)         # Violations in last 30 days
    false_positive_rate = FloatProperty(default=0.0)      # Rate of overturned decisions
    appeal_success_rate = FloatProperty(default=0.0)      # Success rate of appeals
    
    # Trust Network
    trusted_by_count = IntegerProperty(default=0)         # Users who trust this user
    trusts_count = IntegerProperty(default=0)             # Users this user trusts
    trust_network_score = FloatProperty(default=2.0)      # Network-based trust score
    
    # Timestamps and Metadata
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    last_analyzed_at = DateTimeProperty(default_now=True)
    is_active = BooleanProperty(default=True)
    
    # Relationships
    user = RelationshipTo('auth_manager.models.Users', 'HAS_TRUST_PROFILE')
    moderation_decisions = RelationshipTo('ModerationDecision', 'HAS_MODERATION_DECISION')
    trust_relationships = RelationshipTo('TrustRelationship', 'HAS_TRUST_RELATIONSHIP')
    agent_analyses = RelationshipTo('AgentAnalysis', 'HAS_AGENT_ANALYSIS')
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'truststream'


class ModerationDecision(DjangoNode, StructuredNode):
    """
    Records of AI moderation decisions with full audit trail and explainability.
    
    This model stores every moderation decision made by TrustStream agents,
    including the reasoning, confidence levels, and outcomes for transparency
    and continuous improvement.
    """
    uid = UniqueIdProperty()
    
    # Content Information
    content_type = StringProperty(required=True)           # Type of content moderated
    content_id = StringProperty(required=True)             # ID of the moderated content
    content_text = StringProperty()                        # Text content (if applicable)
    content_metadata = JSONProperty()                      # Additional content data
    
    # Decision Details
    decision = StringProperty(required=True)               # Final moderation action
    confidence_score = FloatProperty(required=True)        # AI confidence (0.0-1.0)
    risk_level = StringProperty(required=True)             # HIGH, MEDIUM, LOW
    
    # Agent Analysis
    primary_agent = StringProperty(required=True)          # Main analyzing agent
    contributing_agents = ArrayProperty(StringProperty())  # Other agents involved
    consensus_score = FloatProperty(default=0.0)          # Agreement between agents
    
    # Violation Details
    violation_types = ArrayProperty(StringProperty())      # Types of violations detected
    violation_severity = FloatProperty(default=0.0)       # Severity score (0.0-1.0)
    policy_references = ArrayProperty(StringProperty())    # Relevant policy sections
    
    # Explainability
    reasoning = StringProperty()                           # Human-readable explanation
    evidence = JSONProperty()                              # Supporting evidence data
    similar_cases = ArrayProperty(StringProperty())        # Similar past decisions
    
    # Outcomes and Appeals
    action_taken = StringProperty()                        # Actual action implemented
    user_appealed = BooleanProperty(default=False)        # Whether user appealed
    appeal_outcome = StringProperty()                      # Result of appeal if any
    human_reviewed = BooleanProperty(default=False)       # Human moderator involvement
    
    # Timestamps
    created_at = DateTimeProperty(default_now=True)
    reviewed_at = DateTimeProperty()
    appealed_at = DateTimeProperty()
    
    # Relationships
    trust_profile = RelationshipTo('TrustProfile', 'MODERATED_USER')
    agent_analyses = RelationshipTo('AgentAnalysis', 'BASED_ON_ANALYSIS')
    
    class Meta:
        app_label = 'truststream'


class AgentAnalysis(DjangoNode, StructuredNode):
    """
    Individual agent analysis results for content moderation decisions.
    
    This model stores the detailed analysis from each TrustStream agent,
    allowing for consensus building and performance tracking of individual agents.
    """
    uid = UniqueIdProperty()
    
    # Agent Information
    agent_name = StringProperty(required=True)             # Name of the analyzing agent
    agent_version = StringProperty(required=True)          # Version of the agent
    analysis_type = StringProperty(required=True)          # Type of analysis performed
    
    # Content Analysis
    content_id = StringProperty(required=True)             # ID of analyzed content
    content_type = StringProperty(required=True)           # Type of content
    
    # Analysis Results
    risk_score = FloatProperty(required=True)              # Risk assessment (0.0-1.0)
    confidence = FloatProperty(required=True)              # Analysis confidence (0.0-1.0)
    recommendation = StringProperty(required=True)         # Agent's recommendation
    
    # Detailed Findings
    violations_detected = ArrayProperty(StringProperty())   # Specific violations found
    risk_factors = JSONProperty()                          # Detailed risk analysis
    behavioral_indicators = JSONProperty()                 # User behavior patterns
    content_quality_metrics = JSONProperty()              # Content quality assessment
    
    # AI Provider Details
    ai_provider = StringProperty(required=True)            # OpenAI, Claude, Gemini, etc.
    model_used = StringProperty(required=True)             # Specific model version
    processing_time = FloatProperty()                      # Analysis duration (seconds)
    token_usage = IntegerProperty()                        # Tokens consumed
    
    # Performance Metrics
    accuracy_score = FloatProperty()                       # Historical accuracy
    false_positive_rate = FloatProperty()                  # False positive rate
    false_negative_rate = FloatProperty()                  # False negative rate
    
    # Timestamps
    created_at = DateTimeProperty(default_now=True)
    
    # Relationships
    moderation_decision = RelationshipTo('ModerationDecision', 'CONTRIBUTES_TO_DECISION')
    trust_profile = RelationshipTo('TrustProfile', 'ANALYZED_USER')
    
    class Meta:
        app_label = 'truststream'


class TrustRelationship(DjangoNode, StructuredNode):
    """
    Trust-based relationships between users for network analysis and scoring.
    
    This model captures explicit and implicit trust relationships between users,
    which are used to calculate network-based trust scores and detect coordinated behavior.
    """
    uid = UniqueIdProperty()
    
    # Relationship Participants
    truster_id = StringProperty(required=True)             # User giving trust
    trustee_id = StringProperty(required=True)             # User receiving trust
    
    # Trust Metrics
    trust_level = FloatProperty(required=True)             # Explicit trust level (0.0-5.0)
    relationship_type = StringProperty(required=True)      # EXPLICIT, IMPLICIT, DERIVED
    trust_source = StringProperty(required=True)           # How trust was established
    
    # Relationship Strength
    interaction_count = IntegerProperty(default=0)         # Number of interactions
    positive_interactions = IntegerProperty(default=0)     # Positive interaction count
    negative_interactions = IntegerProperty(default=0)     # Negative interaction count
    
    # Network Analysis
    network_weight = FloatProperty(default=1.0)           # Weight in trust network
    influence_score = FloatProperty(default=0.0)          # Influence of this relationship
    reciprocal = BooleanProperty(default=False)           # Whether trust is mutual
    
    # Behavioral Patterns
    consistency_score = FloatProperty(default=1.0)        # Consistency of interactions
    authenticity_score = FloatProperty(default=1.0)       # Authenticity indicators
    manipulation_risk = FloatProperty(default=0.0)        # Risk of manipulation
    
    # Timestamps
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    last_interaction_at = DateTimeProperty()
    
    # Status
    is_active = BooleanProperty(default=True)
    is_verified = BooleanProperty(default=False)
    
    # Relationships
    truster = RelationshipTo('TrustProfile', 'TRUSTS')
    trustee = RelationshipTo('TrustProfile', 'TRUSTED_BY')
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'truststream'


# ============================================================================
# POSTGRESQL MODELS FOR CACHING AND ANALYTICS
# ============================================================================

class TrustScoreCache(models.Model):
    """
    PostgreSQL model for caching trust scores for performance optimization.
    
    This model provides fast access to frequently requested trust scores
    without requiring complex Neo4j queries every time.
    """
    user_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Cached Trust Scores
    iq_score = models.FloatField(default=2.0)
    appeal_score = models.FloatField(default=2.0)
    social_score = models.FloatField(default=2.0)
    humanity_score = models.FloatField(default=2.0)
    overall_trust_score = models.FloatField(default=2.0)
    
    # Cached Rankings
    trust_rank = models.CharField(max_length=20, default='bronze')
    trust_percentile = models.FloatField(default=50.0)
    
    # Cache Metadata
    last_updated = models.DateTimeField(auto_now=True)
    cache_version = models.IntegerField(default=1)
    is_stale = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'truststream_score_cache'
        indexes = [
            models.Index(fields=['overall_trust_score']),
            models.Index(fields=['trust_rank']),
            models.Index(fields=['last_updated']),
        ]


class ModerationLog(models.Model):
    """
    PostgreSQL model for logging all moderation activities for analytics and compliance.
    
    This model provides efficient querying and reporting capabilities for
    moderation activities, performance metrics, and compliance auditing.
    """
    # Decision Identifiers
    decision_uid = models.CharField(max_length=255, unique=True, db_index=True)
    content_type = models.CharField(max_length=50)
    content_id = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255, db_index=True)
    
    # Decision Details
    decision = models.CharField(max_length=50)
    confidence_score = models.FloatField()
    risk_level = models.CharField(max_length=20)
    
    # Agent Information
    primary_agent = models.CharField(max_length=100)
    contributing_agents = models.JSONField(default=list)
    consensus_score = models.FloatField(default=0.0)
    
    # Violation Information
    violation_types = models.JSONField(default=list)
    violation_severity = models.FloatField(default=0.0)
    
    # Outcomes
    action_taken = models.CharField(max_length=50)
    user_appealed = models.BooleanField(default=False)
    appeal_outcome = models.CharField(max_length=50, blank=True)
    human_reviewed = models.BooleanField(default=False)
    
    # Performance Metrics
    processing_time = models.FloatField(null=True)
    ai_provider_used = models.CharField(max_length=50)
    token_usage = models.IntegerField(null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True)
    appealed_at = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'truststream_moderation_log'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['decision']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['primary_agent']),
        ]


class AgentPerformanceMetrics(models.Model):
    """
    PostgreSQL model for tracking individual agent performance metrics.
    
    This model enables performance monitoring, optimization, and comparison
    of different TrustStream agents and AI providers.
    """
    # Agent Identification
    agent_name = models.CharField(max_length=100, db_index=True)
    agent_version = models.CharField(max_length=50)
    ai_provider = models.CharField(max_length=50)
    model_used = models.CharField(max_length=100)
    
    # Performance Metrics (calculated daily)
    date = models.DateField(db_index=True)
    total_analyses = models.IntegerField(default=0)
    accuracy_rate = models.FloatField(default=0.0)
    false_positive_rate = models.FloatField(default=0.0)
    false_negative_rate = models.FloatField(default=0.0)
    
    # Processing Metrics
    avg_processing_time = models.FloatField(default=0.0)
    avg_confidence_score = models.FloatField(default=0.0)
    total_token_usage = models.IntegerField(default=0)
    
    # Decision Distribution
    approve_count = models.IntegerField(default=0)
    flag_count = models.IntegerField(default=0)
    block_count = models.IntegerField(default=0)
    remove_count = models.IntegerField(default=0)
    
    # Quality Metrics
    human_agreement_rate = models.FloatField(default=0.0)
    appeal_overturn_rate = models.FloatField(default=0.0)
    consistency_score = models.FloatField(default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'truststream_agent_performance'
        unique_together = ['agent_name', 'date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['agent_name', 'date']),
            models.Index(fields=['accuracy_rate']),
        ]


class TrustNetworkAnalytics(models.Model):
    """
    PostgreSQL model for storing trust network analytics and insights.
    
    This model provides aggregated analytics about trust networks,
    community health, and behavioral patterns for dashboard reporting.
    """
    # Time Period
    date = models.DateField(db_index=True)
    period_type = models.CharField(max_length=20)  # daily, weekly, monthly
    
    # Network Metrics
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    new_users = models.IntegerField(default=0)
    
    # Trust Distribution
    unverified_users = models.IntegerField(default=0)
    bronze_users = models.IntegerField(default=0)
    silver_users = models.IntegerField(default=0)
    gold_users = models.IntegerField(default=0)
    platinum_users = models.IntegerField(default=0)
    diamond_users = models.IntegerField(default=0)
    
    # Network Health
    avg_trust_score = models.FloatField(default=2.0)
    trust_score_std = models.FloatField(default=0.0)
    network_density = models.FloatField(default=0.0)
    clustering_coefficient = models.FloatField(default=0.0)
    
    # Moderation Activity
    total_decisions = models.IntegerField(default=0)
    approval_rate = models.FloatField(default=0.0)
    flag_rate = models.FloatField(default=0.0)
    block_rate = models.FloatField(default=0.0)
    
    # Community Health Indicators
    content_quality_avg = models.FloatField(default=2.0)
    engagement_authenticity_avg = models.FloatField(default=2.0)
    violation_rate = models.FloatField(default=0.0)
    appeal_rate = models.FloatField(default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'truststream_network_analytics'
        unique_together = ['date', 'period_type']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['period_type', 'date']),
        ]