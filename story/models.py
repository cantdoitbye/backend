# story/models.py

# This file defines the Neo4j database models for the story module using neomodel
# Stories are temporary content (24-hour expiration) that users can create, view, and interact with
# Similar to Instagram/Facebook stories functionality

from neomodel import StructuredNode, StringProperty, IntegerProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom,ArrayProperty
from django_neomodel import DjangoNode
from datetime import datetime
from auth_manager.models import Users 
from django.db import models
from vibe_manager.models import IndividualVibe

# Main Story model - represents user-created temporary content
# Stories expire after 24 hours and support privacy controls (Inner/Outer/Universe circles)
# Used by: Story creation API, Story viewing API, Story feed generation
# Connected to: Users (creator), Comments, Reactions, Ratings, Views, Shares
class Story(DjangoNode, StructuredNode):
    # Unique identifier for each story - auto-generated UUID
    uid = UniqueIdProperty()
    
    # Story content fields
    title = StringProperty(required=True)  # Story title/headline
    content = StringProperty()  # Main story text content
    captions = StringProperty()  # Additional captions for media
    
    # Timestamp management - tracks when story was created and last modified
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    
    # Privacy control - array of circle types this story is visible to
    # Values: ["Inner"], ["Outer"], ["Universe"], or combinations
    # Used by story feed filtering logic to show relevant stories to users
    privacy = ArrayProperty(base_property=StringProperty(), required=True)
    
    # Soft delete flag - allows marking stories as deleted without permanent removal
    # Used for data retention and potential recovery scenarios
    is_deleted = BooleanProperty(default=False)
    
    # Media attachment - stores file ID for story image/video
    # Links to file storage system for retrieving actual media content
    story_image_id = StringProperty()
    
    # Relationship definitions - Neo4j graph connections to other entities
    # These create the social graph structure for stories
    created_by = RelationshipTo('Users', 'CREATED_BY')  # Story creator
    updated_by = RelationshipTo('Users', 'UPDATED_BY')  # Last editor
    storycomment = RelationshipTo('StoryComment', 'BELONGS_TO')  # User comments
    storyreaction = RelationshipTo('StoryReaction', 'REACTED_BY')  # User reactions/vibes
    storyrating = RelationshipTo('StoryRating', 'RATED_BY')  # Numeric ratings
    storyview = RelationshipTo('StoryView', 'VIEWED_BY')  # View tracking
    storyshare = RelationshipTo('StoryShare', 'SHARED_BY')  # Share tracking

    # Custom save method - automatically updates timestamp on every save
    # Ensures updated_at is always current when story is modified
    # Called by: Create/Update story mutations
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    # Django model metadata - required for Django-neomodel integration
    class Meta:
        app_label = 'story'  

    # String representation for debugging and admin interface
    def __str__(self):
        return self.title


# Story comment model - represents user comments on stories
# Allows users to engage with story content through text responses
# Used by: Comment creation/update APIs, Story detail views
class StoryComment(DjangoNode, StructuredNode):
    # Unique identifier for each comment
    uid = UniqueIdProperty()
    
    # Bidirectional relationships - comments belong to stories and users
    story = RelationshipTo('Story', 'HAS_COMMENT')  # Which story this comment is on
    user = RelationshipTo('Users', 'COMMENTED_BY')  # Who made the comment
    
    # Comment content and metadata
    content = StringProperty()  # The actual comment text
    timestamp = DateTimeProperty(default_now=True)  # When comment was created
    is_deleted = BooleanProperty(default=False)  # Soft delete for moderation

    # Auto-update timestamp when comment is modified
    # Used for tracking comment edit history
    def save(self, *args, **kwargs):
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'story'

    def __str__(self):
        return ""  # Empty string - could show comment preview


# Story reaction model - represents user emotional reactions to stories
# Implements vibe-based reaction system with customizable emotions
# Used by: Reaction APIs, Story analytics, Vibe scoring system
class StoryReaction(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    
    # Relationships to story and user who reacted
    story = RelationshipTo('Story', 'HAS_REACTION')
    user = RelationshipTo('Users', 'REACTED_BY')
    
    # Reaction data - combines emotion type with intensity score
    reaction = StringProperty(default='Like')  # Name of the vibe/emotion
    vibe = IntegerProperty(default=2)  # Intensity score (1-5 typically)
    is_deleted = BooleanProperty(default=False)

    class Meta:
        app_label = 'story'

    def __str__(self):
        return self.reaction


# Story rating model - numeric rating system (1-5 stars)
# Provides quantitative feedback mechanism separate from vibe reactions
# Used by: Rating APIs, Story quality analytics
class StoryRating(DjangoNode, StructuredNode):
    # Predefined choices for rating values - ensures data consistency
    RATING_CHOICES = (
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    )

    uid = UniqueIdProperty()
    
    # Relationships for rating context
    story = RelationshipTo('Story', 'HAS_RATED')
    user = RelationshipTo('Users', 'RATED_BY')
    
    # Rating value with validation constraints
    # Default of 1 ensures no null ratings, choices enforce valid range
    rating = IntegerProperty(default=1, choices=RATING_CHOICES)

    class Meta:
        app_label = 'story'

    def __str__(self):
        return ""  # Could show rating value


# Story view tracking model - records when users view stories
# Critical for analytics and determining story reach/engagement
# Used by: View tracking API, Story analytics, "Viewed by" lists
class StoryView(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    
    # Relationships for view context
    story = RelationshipTo('Story', 'HAS_VIEW')
    user = RelationshipTo('Users', 'VIEWD_BY')  # Note: typo in original "VIEWD_BY"
    
    # Timestamp for view analytics and sorting
    viewed_at = DateTimeProperty(default_now=True)

    # Updates timestamp if view record is modified (rare case)
    def save(self, *args, **kwargs):
        self.viewed_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'story'

    def __str__(self):
        return ""


# Story sharing model - tracks how stories are shared across platforms
# Enables viral tracking and platform-specific sharing analytics
# Used by: Share APIs, Social media integration, Viral analytics
class StoryShare(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()
    
    # Predefined sharing platform options - extensible for new platforms
    SHARE_CHOICES = {
        'LINK': 'Link',          # Direct link sharing
        'WHATSAPP': 'WhatsApp',  # WhatsApp sharing
        'FACEBOOK': 'Facebook',   # Facebook sharing
        'INSTAGRAM': 'Instagram', # Instagram sharing
        'OTHERS': 'Others',      # Catch-all for other platforms
    }

    # Relationships and sharing metadata
    story = RelationshipTo('Story', 'HAS_SHARE')
    user = RelationshipTo('Users', 'SHARED_BY')
    
    # Platform tracking with default to link sharing
    share_type = StringProperty(default='LINK', choices=SHARE_CHOICES.items())
    shared_at = DateTimeProperty(default_now=True)

    # Updates timestamp for share modifications
    def save(self, *args, **kwargs):
        self.shared_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'story'

    def __str__(self):
        return ""


# Story reaction aggregation manager - Django model for vibe analytics
# NOTE: This is a Django model (not Neo4j) for performance reasons
# Aggregates reaction data for fast story vibe calculations without complex graph queries
# Used by: Story feed ranking, Vibe analytics, Real-time reaction updates
class StoryReactionManager(models.Model):
    # Links to Neo4j story via UID - hybrid database approach
    story_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # JSON field stores aggregated vibe data for performance
    # Structure: [{"vibes_id": 1, "vibes_name": "Happy", "vibes_count": 5, "cumulative_vibe_score": 3.2}, ...]
    # Avoids complex Neo4j aggregation queries for real-time feeds
    story_vibe = models.JSONField(default=list)

    class Meta:
        verbose_name = 'Story Reaction Manager'
        verbose_name_plural = 'Story Reaction Managers'

    def __str__(self):
        return f"PostReactionManager for post {self.story_uid}"

    # Initializes story with default 10 vibes at zero counts
    # Called when: First reaction is added to a story
    # Ensures consistent vibe structure across all stories for feed algorithms
    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the IndividualVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.story_vibe.append(reaction_info)

    # Updates vibe counts and calculates running average scores
    # Called when: User adds a new reaction to a story
    # Calculates cumulative average to show overall vibe intensity over time
    # Input: vibes_name (string), score (integer 1-5)
    # Throws: ValueError if vibe not found in initialized list
    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_id exists
        for reaction in self.story_vibe:
            if reaction['vibes_name'] == vibes_name:
                # Update existing reaction with new count and cumulative score
                reaction['vibes_count'] += 1
                # Update cumulative vibe score (average score calculation)
                total_score = reaction['cumulative_vibe_score'] * (reaction['vibes_count'] - 1) + score
                reaction['cumulative_vibe_score'] = total_score / reaction['vibes_count']
                break
        else:
            # If no reaction exists, this should initialize (but this case shouldn't happen as we initialize 10 vibes)
            raise ValueError(f"No initialized reaction for vibes_id {vibes_name} found.")

    # Returns aggregated vibe data for API responses
    # Used by: Story detail APIs, Vibe ranking algorithms
    # Returns: List of vibe dictionaries with counts and scores
    def get_reactions(self):
        """Retrieve all reactions with their vibe details."""
        return self.story_vibe