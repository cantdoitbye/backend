# post/models.py

"""
Post Module Models - Core data structures for social media posts and interactions.

This module defines all the database models for the post functionality including:
- Posts (main content)
- Comments, Likes, Reviews (user interactions)
- Tags, Shares, Views (content organization and analytics)
- Saved/Pinned posts (user personalization)

All models use Neo4j graph database via neomodel and include relationships
between users, posts, and various interaction types.
"""

from neomodel import StructuredNode, StringProperty, IntegerProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom,FloatProperty,ArrayProperty,ZeroOrOne
from django_neomodel import DjangoNode
from datetime import datetime
from auth_manager.models import Users 
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from vibe_manager.models import IndividualVibe
from django.contrib.contenttypes.models import ContentType




class Post(DjangoNode, StructuredNode):
    """
    Main Post model representing user-generated content in the social platform.
    
    This is the core content model that stores posts created by users.
    Each post can have text, media files, privacy settings, and various interaction counts.
    Used throughout the app for feed display, user profiles, and content management.
    
    Relationships:
    - Connected to Users (creator/updater)
    - Has many Comments, Likes, Shares, Views
    - Can be saved/pinned by users
    - Can have reviews and tags
    """
    uid = UniqueIdProperty()  # Unique identifier for each post
    
    # Privacy level choices - determines who can see the post
    PRIVACY_CHOICES = {
        'public': 'Public',           # Everyone can see
        'outer': 'Outer Circle',      # Extended connections only
        'inner': 'Inner Circle',      # Close connections only
        'universal': 'Universal',     # All app users
        'private': 'Private'          # Only creator can see
    }
    
    # Core post content fields
    post_title = StringProperty()                    # Optional title for the post
    post_text = StringProperty()                     # Main text content of the post
    post_type = StringProperty(required=True)        # Type: text, image, video, etc.
    post_file_id = ArrayProperty(base_property=StringProperty())  # Array of file IDs for media
    privacy = StringProperty(default='public', choices=PRIVACY_CHOICES.items())  # Privacy setting
    
    # Engagement and scoring
    vibe_score = FloatProperty(default=2.0)          # Overall engagement score (1.0-5.0)
    comment_count = IntegerProperty(default=0)       # Cached count of comments
    vibes_count = IntegerProperty(default=0)         # Cached count of likes/reactions
    share_count = IntegerProperty(default=0)         # Cached count of shares
    
    # Metadata
    created_at = DateTimeProperty(default_now=True)  # When post was created
    updated_at = DateTimeProperty(default_now=True)  # Last modification time
    is_deleted = BooleanProperty(default=False)      # Soft delete flag
    
    # Relationships to other models
    created_by = RelationshipTo('Users', 'HAS_USER')           # Post creator
    updated_by = RelationshipTo('Users','HAS_UPDATED_USER')    # Last person to update
    comment = RelationshipTo('Comment','HAS_COMMENT')          # Comments on this post
    like = RelationshipTo('Like','HAS_LIKE')                   # Likes/reactions on this post
    postshare = RelationshipTo('PostShare','HAS_POST_SHARE')   # Shares of this post
    view = RelationshipTo('PostView','HAS_VIEW')               # Views of this post
    postsave = RelationshipTo('SavedPost','HAS_SAVED_POST')    # Users who saved this post
    review = RelationshipTo('Review','HAS_REVIEW')             # Reviews of this post
    pinpost = RelationshipTo('PinedPost','HAS_PINNED_POST')    # Users who pinned this post
    tags = ArrayProperty(base_property=StringProperty())  # Array of tags for post categorization

    def save(self, *args, **kwargs):
        """
        Override save method to automatically update the modification timestamp.
        Called whenever a post is created or modified.
        """
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'post'
        
    def __str__(self):
        """String representation showing post title for admin/debugging"""
        return self.post_title
    

class Tag(DjangoNode, StructuredNode):
    """
    Tag model for categorizing and organizing posts with hashtags or keywords.
    
    Tags help users discover content and organize posts by topics.
    Each tag can be associated with multiple posts and tracks who created it.
    Used in post creation, search functionality, and content discovery.
    
    Expects: Array of tag names (strings), post_uid, creator user
    Returns: Tag object with relationships to post and creator
    """
    uid = UniqueIdProperty()                                    # Unique tag identifier
    names = ArrayProperty(base_property=StringProperty(), required=True)  # Array of tag names/keywords
    created_on = DateTimeProperty(default_now=True)            # When tag was created
    is_deleted = BooleanProperty(default=False)                # Soft delete flag
    
    # Relationships
    created_by = RelationshipTo('Users', 'HAS_USER')           # User who created the tag
    post = RelationshipTo('Post','TAG_BELONG_TO')              # Post this tag belongs to
    
    def save(self, *args, **kwargs):
        """Update creation timestamp on save"""
        self.created_on = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'post'
        
    def __str__(self):
        """String representation showing tag names"""
        return self.name
    

class CommentVibe(DjangoNode, StructuredNode):
    """
    Model for storing vibe reactions sent to comments.
    Integrates with the existing vibe system in PostgreSQL.
    
    Used in: Comment vibe reactions, engagement analytics
    Expects: comment_uid, individual_vibe_id, vibe_intensity
    Returns: CommentVibe object with bidirectional relationships
    """
    uid = UniqueIdProperty()
    
    # Relationships
    comment = RelationshipFrom('Comment', 'HAS_VIBE_REACTION')
    reacted_by = RelationshipTo('Users', 'REACTED_BY')
    
    # Vibe data from PostgreSQL IndividualVibe model
    individual_vibe_id = IntegerProperty()  # References IndividualVibe.id
    vibe_name = StringProperty(required=True)  # From name_of_vibe field
    vibe_intensity = FloatProperty(required=True)  # 1.0 to 5.0 user selection
    
    # Metadata
    reaction_type = StringProperty(default="vibe")
    timestamp = DateTimeProperty(default_now=True)
    is_active = BooleanProperty(default=True)
    
    def save(self, *args, **kwargs):
        """Update timestamp on save"""
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'post'
    
    def __str__(self):
        return f"{self.vibe_name} - {self.vibe_intensity}"


class Comment(DjangoNode, StructuredNode):
    """
    Comment model for user responses and discussions on posts.
    
    Represents threaded conversations under posts. Comments are displayed
    in the post detail view and contribute to engagement scoring.
    Each comment belongs to one post and one user.
    
    Used in: Post detail screens, notification system, engagement calculations
    Expects: post_uid, user_uid, comment content text
    Edge cases: Empty comments are not allowed, deleted comments are soft-deleted
    """
    uid = UniqueIdProperty()                           # Unique comment identifier
    content = StringProperty()                         # The actual comment text
    timestamp = DateTimeProperty(default_now=True)    # When comment was posted
    is_deleted = BooleanProperty(default=False)       # Soft delete flag
    comment_file_id = ArrayProperty(base_property=StringProperty())
    is_answer = BooleanProperty(default=False)

    # Relationships
    post = RelationshipTo('Post','HAS_POST')
    community_post = RelationshipTo('community.models.CommunityPost', 'HAS_COMMUNITY_POST')

    user = RelationshipTo('Users','HAS_USER')         # User who wrote the comment
    vibe_reactions = RelationshipTo('CommentVibe', 'HAS_VIBE_REACTION')  # Vibe reactions on this comment
    #Self-referencing relationships for nested replies
    parent_comment = RelationshipTo('Comment', 'REPLIED_TO')  # Parent comment if this is a reply
    replies = RelationshipFrom('Comment', 'REPLIED_TO') 

    def save(self, *args, **kwargs):
        """Update timestamp on save"""
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    def get_reply_depth(self):
        """
        Calculate the depth level of this comment in the reply chain.
        Returns 0 for top-level comments, 1 for direct replies, etc.
        """
        depth = 0
        current_comment = self
        while current_comment.parent_comment.single():
            depth += 1
            current_comment = current_comment.parent_comment.single()
            if depth > 10:  # Max depth limit
                break
        return depth

    def get_root_comment(self):
        """
        Get the root (top-level) comment in this reply chain.
        """
        current_comment = self
        while current_comment.parent_comment.single():
            current_comment = current_comment.parent_comment.single()
        return current_comment

    def get_all_descendants(self):
        """
        Get all nested replies recursively.
        Returns a flat list of all descendant comments.
        """
        descendants = []
        direct_replies = list(self.replies.all())
        for reply in direct_replies:
            if not reply.is_deleted:
                descendants.append(reply)
                descendants.extend(reply.get_all_descendants())
        return descendants            

    class Meta:
        app_label = 'post'

    def __str__(self):
        """String representation showing comment content preview"""
        return self.content


class Like(DjangoNode, StructuredNode):
    """
    Like/Reaction model for user engagement with posts.
    
    Represents emotional reactions to posts using the "vibe" system.
    Each like has a reaction type (emoji/name) and numerical vibe score (1.0-5.0).
    Used for engagement tracking, feed algorithm scoring, and vibe analytics.
    
    Connected to: Post detail screens, reaction buttons, analytics dashboard
    Expects: post_uid, user_uid, reaction name, vibe score (1.0-5.0)
    Assumptions: One user can have multiple reactions per post with different vibes
    """
    uid = UniqueIdProperty()                           # Unique like identifier
    reaction = StringProperty(default='Like')          # Type of reaction (Like, Love, etc.)
    vibe = FloatProperty(default=2)                   # Numerical score for this reaction (1.0-5.0)
    timestamp = DateTimeProperty(default_now=True)    # When reaction was given
    is_deleted = BooleanProperty(default=False)       # Soft delete flag
    
    # Relationships
    post = RelationshipTo('Post','HAS_POST')          # Post being reacted to
    user = RelationshipTo('Users','HAS_USER')         # User giving the reaction

    def save(self, *args, **kwargs):
        """Update timestamp on save"""
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'post'

    def __str__(self):
        """String representation showing reaction type"""
        return self.reaction


class Review(DjangoNode, StructuredNode):
    """
    Review model for detailed feedback on posts.
    
    More comprehensive than likes - includes rating (1-5) and text review.
    Used for posts that need detailed evaluation or feedback.
    Different from comments as reviews include numerical ratings.
    
    Used in: Premium content evaluation, product posts, detailed feedback systems
    Expects: post_uid, user_uid, rating (1-5), review text
    Returns: Review object with rating and text content
    """
    uid = UniqueIdProperty()                           # Unique review identifier
    rating = IntegerProperty(default=2)                # Numerical rating (1-5)
    review_text = StringProperty(default='Like')       # Detailed review text
    timestamp = DateTimeProperty(default_now=True)     # When review was posted
    is_deleted = BooleanProperty(default=False)        # Soft delete flag
    
    # Relationships
    post = RelationshipTo('Post','HAS_POST')           # Post being reviewed
    user = RelationshipTo('Users','HAS_USER')          # User writing the review

    def save(self, *args, **kwargs):
        """Update timestamp on save"""
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'post'

    def __str__(self):
        """String representation showing review text preview"""
        return self.review_text


class SavedPost(DjangoNode, StructuredNode):
    """
    SavedPost model for bookmarking posts for later viewing.
    
    Allows users to save interesting posts to view later in their saved collection.
    Creates a personal library of bookmarked content for each user.
    
    Used in: Saved posts screen, bookmark functionality, personal collections
    Expects: post_uid, user_uid
    Returns: SavedPost relationship between user and post
    Edge cases: User can only save a post once (should check for duplicates)
    """
    uid = UniqueIdProperty()                           # Unique saved post identifier
    saved_at = DateTimeProperty(default_now=True)      # When post was saved
    
    # Relationships
    post = RelationshipTo('Post','HAS_POST')           # Post being saved
    user = RelationshipTo('Users','HAS_USER')          # User saving the post
    
    def save(self, *args, **kwargs):
        """Update saved timestamp on save"""
        self.saved_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'post'

    def __str__(self):
        return ""


class PinedPost(DjangoNode, StructuredNode):
    """
    PinnedPost model for highlighting important posts on user profiles.
    
    Allows users to pin their most important posts to the top of their profile.
    Pinned posts are displayed prominently and stay at the top regardless of date.
    
    Used in: User profile screens, post management, content highlighting
    Expects: post_uid, user_uid
    Returns: PinnedPost relationship with timestamp
    Assumptions: Users can pin multiple posts but should have a reasonable limit
    """
    uid = UniqueIdProperty()                           # Unique pinned post identifier
    name = StringProperty(default="pin")               # Label/name for the pin
    pined_at = DateTimeProperty(default_now=True)      # When post was pinned
    
    # Relationships
    post = RelationshipTo('Post','HAS_POST')           # Post being pinned
    user = RelationshipTo('Users','HAS_USER')          # User pinning the post
    
    def save(self, *args, **kwargs):
        """Update pinned timestamp on save"""
        self.pined_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'post'

    def __str__(self):
        return ""


class PostShare(DjangoNode, StructuredNode):
    """
    PostShare model for tracking when users share posts to external platforms.
    
    Records sharing activity for analytics and viral tracking.
    Supports different sharing platforms (WhatsApp, Facebook, etc.) and generates
    shareable links. Used for measuring content reach and social distribution.
    
    Connected to: Share buttons, analytics dashboard, viral content tracking
    Expects: post_uid, user_uid, share_type (platform)
    Returns: PostShare record with platform and timestamp
    """
    uid = UniqueIdProperty()                           # Unique share identifier
    
    # Supported sharing platforms
    SHARE_CHOICES = {
        'LINK': 'Link',                # Generic shareable link
        'WHATSAPP': 'WhatsApp',        # WhatsApp sharing
        'FACEBOOK': 'Facebook',        # Facebook sharing
        'INSTAGRAM': 'Instagram',      # Instagram sharing
        'OTHERS': 'Others',            # Other platforms
    }
    
    share_type = StringProperty(default='LINK', choices=SHARE_CHOICES.items())  # Platform shared to
    timestamp = DateTimeProperty(default_now=True)     # When share was created
    shared_at = DateTimeProperty(default_now=True)     # When actually shared (may differ from creation)
    is_deleted = BooleanProperty(default=False)        # Soft delete flag
    
    # Relationships
    post = RelationshipTo('Post','HAS_POST')           # Post being shared
    user = RelationshipTo('Users','HAS_USER')          # User sharing the post

    def save(self, *args, **kwargs):
        """Update shared timestamp on save"""
        self.shared_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'post'

    def __str__(self):
        """String representation showing share platform"""
        return self.share_type


class PostView(DjangoNode, StructuredNode):
    """
    PostView model for tracking post impressions and view analytics.
    
    Records when users view posts for analytics and engagement tracking.
    Used to calculate reach, popular content, and user behavior patterns.
    Essential for feed algorithm and content recommendation systems.
    
    Connected to: Feed display, analytics, recommendation algorithms
    Expects: post_uid, user_uid (automatically created when posts are viewed)
    Returns: PostView record with timestamp
    Edge cases: Should handle anonymous views and prevent spam counting
    """
    uid = UniqueIdProperty()                           # Unique view identifier
    viewed_at = DateTimeProperty(default_now=True)     # When post was viewed
    
    # Relationships
    post = RelationshipTo('Post','HAS_POST')           # Post being viewed
    user = RelationshipTo('Users','HAS_USER')          # User viewing the post

    def save(self, *args, **kwargs):
        """Update viewed timestamp on save"""
        self.viewed_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'post'

    def __str__(self):
        return ""
    


class UserMention(DjangoNode, StructuredNode):
    """
    Generic model for tracking user mentions/tags across all content types.
    
    This model can handle mentions in posts, community posts, comments, stories, 
    bios, and any future content types using a generic approach.
    """
    uid = UniqueIdProperty()
    mentioned_at = DateTimeProperty(default_now=True)
    is_active = BooleanProperty(default=True)
    
    # Generic content identification
    content_type = StringProperty(required=True)  # 'post', 'community_post', 'comment', 'story', 'bio', etc.
    content_uid = StringProperty(required=True)   # UID of the content being mentioned in
    
    # Optional: specific context within content
    mention_context = StringProperty()  # 'description', 'title', 'body', etc.
    
    # Relationships
    mentioned_user = RelationshipTo('Users', 'MENTIONED_USER')
    mentioned_by = RelationshipTo('Users', 'MENTIONED_BY')
    
    # Optional: keep specific relationships for common queries (indexes)
    post = RelationshipTo('Post', 'MENTIONED_IN_POST')
    community_post = RelationshipTo('community.models.CommunityPost', 'MENTIONED_IN_COMMUNITY_POST')
    comment = RelationshipTo('Comment', 'MENTIONED_IN_COMMENT')
    story = RelationshipTo('story.models.Story', 'MENTIONED_IN_STORY')
    community_description = RelationshipTo('community.models.Community', 'MENTIONED_IN_COMMUNITY_DESCRIPTION')


    
    def save(self, *args, **kwargs):
        self.mentioned_at = datetime.now()
        super().save(*args, **kwargs)
        
    class Meta:
        app_label = 'post'
        
    def __str__(self):
        return f"Mention: {self.mentioned_user} by {self.mentioned_by} in {self.content_type}:{self.content_uid}"    


# Django model for aggregated reaction analytics (Note: Review and Optimization needed)
class PostReactionManager(models.Model):
    """
    PostReactionManager - Django model for aggregating and managing post reaction analytics.
    
    This model bridges between Neo4j post data and Django for complex analytics.
    Stores aggregated vibe data for each post including counts and cumulative scores.
    Used for generating reaction analytics, top vibes, and engagement insights.
    
    IMPORTANT: This model needs review and optimization as noted in comments.
    
    Connected to: Analytics dashboard, vibe management, reaction summaries
    Expects: post_uid and initializes with first 10 individual vibes
    Returns: Aggregated reaction data with counts and scores
    Performance note: JSON field operations can be expensive, consider optimization
    """
    post_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)  # Reference to Neo4j post
    post_vibe = models.JSONField(default=list)  # Aggregated vibe data as JSON array

    class Meta:
        verbose_name = 'Post Reaction Manager'
        verbose_name_plural = 'Post Reaction Managers'

    def __str__(self):
        return f"PostReactionManager for post {self.post_uid}"

    def initialize_reactions(self):
        """
        Initialize the post with the first 10 available individual vibes.
        
        Sets up base reaction structure with zero counts for all vibe types.
        Called when a post receives its first reaction to establish baseline data.
        
        Used during: First reaction on any post
        Modifies: self.post_vibe array with initial vibe structure
        Assumptions: IndividualVibe model contains at least 10 vibe types
        """
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,                      # Use the actual ID of the IndividualVibe
                'vibes_id': vibe.id,                # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,    # Store the name of the vibe
                'vibes_count': 0,                   # Initialize count as 0
                'cumulative_vibe_score': 0          # Initialize cumulative score as 0
            }
            self.post_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe type.
        
        Updates the count and recalculates the cumulative average score for the vibe.
        Called whenever a user gives a reaction to a post.
        
        Used in: CreateLike mutation, reaction processing
        Expects: vibes_name (string), score (float 1.0-5.0)
        Modifies: Updates existing vibe entry with new count and average score
        Edge cases: Raises ValueError if vibe type not found in initialized list
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.post_vibe:
            if reaction['vibes_name'] == vibes_name:
                # Update existing reaction with new count and cumulative score
                reaction['vibes_count'] += 1
                # Calculate new average score: (old_total + new_score) / new_count
                total_score = reaction['cumulative_vibe_score'] * (reaction['vibes_count'] - 1) + score
                reaction['cumulative_vibe_score'] = total_score / reaction['vibes_count']
                break
        else:
            # If no reaction exists, this should initialize (but this case shouldn't happen as we initialize 10 vibes)
            raise ValueError(f"No initialized reaction for vibes_name {vibes_name} found.")

    def get_reactions(self):
        """
        Retrieve all reaction data with vibe details.
        
        Returns the complete aggregated reaction data for analytics and display.
        Used in analytics views and reaction summary displays.
        
        Returns: Array of reaction objects with counts and scores
        Used by: Analytics queries, reaction display components
        """
        return self.post_vibe

    def update_reaction(self, old_vibes_name, new_vibes_name, old_score, new_score):
        """
        Update an existing reaction from one vibe type to another.
        
        This handles the case where a user changes their reaction. It removes the
        old reaction's contribution and adds the new one, ensuring analytics are correct.
        """
        # Remove the old reaction
        for reaction in self.post_vibe:
            if reaction['vibes_name'] == old_vibes_name:
                if reaction['vibes_count'] > 0:
                    # Decrement count and recalculate score
                    total_score = reaction['cumulative_vibe_score'] * reaction['vibes_count'] - old_score
                    reaction['vibes_count'] -= 1
                    if reaction['vibes_count'] > 0:
                        reaction['cumulative_vibe_score'] = total_score / reaction['vibes_count']
                    else:
                        reaction['cumulative_vibe_score'] = 0
                break
        
        # Add the new reaction
        self.add_reaction(new_vibes_name, new_score)
