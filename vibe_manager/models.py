# vibe_manager/models.py
from neomodel import StructuredNode, StringProperty, IntegerProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom,FloatProperty
from django_neomodel import DjangoNode
from datetime import datetime
from django.db import models

# Main Vibe model stored in Neo4j graph database
# This represents the core vibe entity that users can create and send to each other
# Used across the app for vibe creation, scoring, and social interactions
class Vibe(DjangoNode, StructuredNode):
    """
    Core vibe entity stored in Neo4j graph database.
    Represents a vibe that users can create and send to others.
    
    This model combines both Neo4j graph capabilities (for relationships) 
    and Django integration (for admin interface and validation).
    
    Used by:
    - Vibe creation API (when users create new vibes)
    - Vibe sending system (when users send vibes to each other)
    - Scoring algorithm (IQ, AQ, SQ, HQ values affect user scores)
    - Social features (popularity tracking, creator relationships)
    """
    
    # Unique identifier for each vibe - automatically generated
    uid = UniqueIdProperty()
    
    # Basic vibe information
    name = StringProperty()  # Display name of the vibe
    category = StringProperty()  # Main category (e.g., "positive", "motivational")
    description = StringProperty()  # Detailed description of the vibe
    subCategory = StringProperty()  # More specific categorization
    desc = StringProperty()  # Additional description field (might be deprecated)
    
    # Vibe scoring dimensions - these affect user scores when vibe is sent
    # Each dimension ranges from 0.0 to 4.0 and represents different aspects
    iq = FloatProperty(default=2.0)  # Intelligence quotient impact
    aq = FloatProperty(default=2.0)  # Appeal quotient impact  
    sq = FloatProperty(default=2.0)  # Social quotient impact
    hq = FloatProperty(default=2.0)  # Human quotient impact
    
    # Relationship to the user who created this vibe
    # Used for attribution and possibly creator-specific features
    created_by = RelationshipTo('Users','VIBE_CREATED_BY')
    
    # Tracks how popular this vibe is across the platform
    # Incremented when vibe is sent/used by users
    popularity = IntegerProperty(default=0)
    
    class Meta:
        app_label = 'vibe_manager'
    
    # String representation for admin interface and debugging
    def __str__(self):
        return self.name


# Individual Vibe model stored in traditional Django/PostgreSQL database
# Represents vibe templates specifically for individual users
# Used for creating personalized vibe experiences based on individual characteristics
class IndividualVibe(models.Model):
    """
    Individual vibe template stored in relational database.
    Defines vibe patterns that affect individual user characteristics.
    
    This is separate from the main Vibe model to allow for different
    scoring algorithms and weightings for individual vs community vibes.
    
    Used by:
    - Individual vibe creation system
    - Personal scoring algorithms
    - Vibe recommendation engine for individual users
    """
    
    # Unique name for this individual vibe type
    name_of_vibe = models.CharField(max_length=255, unique=True)
    
    # Optional description explaining what this vibe represents
    description = models.TextField(null=True, blank=True)
    
    # Weightage values determine how much this vibe affects each dimension
    # Higher values = stronger impact on that dimension when vibe is applied
    weightage_iaq = models.IntegerField()  # Individual Appeal Quotient weight
    weightage_iiq = models.IntegerField()  # Individual Intelligence Quotient weight  
    weightage_ihq = models.IntegerField()  # Individual Human Quotient weight
    weightage_isq = models.IntegerField()  # Individual Social Quotient weight
    
    def __str__(self):
        return f"Individual Vibe: {self.name_of_vibe}"


# Community Vibe model for group/community-based vibes
# Represents vibe templates that affect community dynamics and group interactions
# Used when vibes are sent within communities or groups
class CommunityVibe(models.Model):
    """
    Community vibe template for group-based interactions.
    Defines how vibes affect community dynamics and group relationships.
    
    Different from individual vibes because community interactions
    require different scoring dimensions and social considerations.
    
    Used by:
    - Community vibe creation
    - Group interaction scoring
    - Community health metrics
    - Social network analysis within communities
    """
    
    name_of_vibe = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    
    # Community-specific weightage dimensions
    weightage_ceq = models.IntegerField()  # Community Engagement Quotient
    weightage_csq = models.IntegerField()  # Community Social Quotient
    weightage_cgq = models.IntegerField()  # Community Growth Quotient
    weightage_ciq = models.IntegerField()  # Community Intelligence Quotient
    
    def __str__(self):
        return f"Community Vibe: {self.name_of_vibe}"


# Brand Vibe model for brand-related interactions
# Represents vibe templates used in brand contexts or marketing scenarios
# Used when vibes are associated with brands or commercial entities
class BrandVibe(models.Model):
    """
    Brand vibe template for commercial/marketing contexts.
    Defines how vibes work in brand-user interactions and marketing scenarios.
    
    Separate model allows for brand-specific metrics and commercial considerations
    that don't apply to personal or community vibes.
    
    Used by:
    - Brand marketing campaigns
    - Commercial vibe interactions
    - Brand reputation scoring
    - Marketing analytics and brand health metrics
    """
    
    name_of_vibe = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    
    # Brand-specific weightage dimensions
    weightage_bqq = models.IntegerField()  # Brand Quality Quotient
    weightage_brq = models.IntegerField()  # Brand Reputation Quotient
    weightage_biq = models.IntegerField()  # Brand Intelligence Quotient
    weightage_bsq = models.IntegerField()  # Brand Social Quotient
    
    def __str__(self):
        return f"Brand Vibe: {self.name_of_vibe}"


# Service Vibe model for service-based interactions
# Represents vibe templates used in service contexts or customer service scenarios
# Used when vibes are related to service delivery or customer interactions
class ServiceVibe(models.Model):
    """
    Service vibe template for service delivery and customer interaction contexts.
    Defines how vibes work in service-provider scenarios and customer experiences.
    
    Separate from other vibe types to handle service-specific metrics
    like service quality, reliability, and customer satisfaction.
    
    Used by:
    - Customer service interactions
    - Service quality assessment
    - Customer satisfaction scoring
    - Service provider reputation systems
    """
    
    name_of_vibe = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    
    # Service-specific weightage dimensions
    weightage_seq = models.IntegerField()  # Service Excellence Quotient
    weightage_srq = models.IntegerField()  # Service Reliability Quotient
    weightage_ssq = models.IntegerField()  # Service Social Quotient
    weightage_suq = models.IntegerProperty()  # Service User Experience Quotient
    
    def __str__(self):
        return f"Service Vibe: {self.name_of_vibe}"