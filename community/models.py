# Community Models Module
# This module defines all the data models for the community management system.
# It handles communities, sub-communities, memberships, roles, posts, and related functionality.
# The system uses Neo4j graph database through neomodel for complex relationship management
# and traditional Django models for simpler data storage needs.

from neomodel import StructuredNode, StringProperty, IntegerProperty, ArrayProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom, FloatProperty
from django_neomodel import DjangoNode
from datetime import datetime
from auth_manager.models import Users 
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta
from vibe_manager.models import CommunityVibe
from post.models import Like,Comment

class Community(DjangoNode, StructuredNode):
    """
    Core Community Model - Represents the main community entity in the platform.
    
    This model serves as the primary container for user groups and manages:
    - Community metadata (name, description, type)
    - Member relationships and permissions
    - Content organization (posts, messages, activities)
    - Administrative controls and settings
    - Integration with Matrix chat rooms for real-time communication
    
    Business Logic:
    - Communities can have hierarchical sub-communities
    - Support different privacy levels (outer, inner, universal circles)
    - Flexible permission system for messaging and member management
    - Integration with external systems through room_id (Matrix chat)
    - Support for both user-created and AI-generated communities
    
    Relationships:
    - One-to-many with SubCommunity (parent-child hierarchy)
    - Many-to-many with Users through Membership model
    - One-to-many with various content types (posts, messages, activities)
    """
    
    # Community visibility and access control levels
    # These determine who can discover and join the community
    CIRCLE_CHOICES = {
        'Outer': 'outer circle',      # Public communities, discoverable by all
        'Inner': 'inner circle',      # Semi-private, invitation or request-based
        'Universal': 'universal'      # Platform-wide communities, visible to all users
    }

    # Community categorization for better organization and discovery
    # Helps users find relevant communities based on their interests
    GROUP_CHOICES = {
    'PersonalGroup': 'personal group',      # Personal interest or hobby groups
    'InterestGroup': 'interest group',      # Topic-specific communities
    'OfficialGroup': 'official group',      # Official organizational communities
    'BusinessGroup': 'business group'       # Business or professional communities
    }


    # Core identification and metadata fields
    uid = UniqueIdProperty()                    # Unique identifier for the community across the platform
    name = StringProperty(required=True)        # Display name of the community (user-facing)
    username = StringProperty(unique_index=True)  # Unique handle/username for the community (V2)
    description = StringProperty()              # Detailed description of community purpose and guidelines
    community_type = StringProperty()           # Additional type classification beyond GROUP_CHOICES
    community_circle = StringProperty(choices=CIRCLE_CHOICES.items())  # Privacy/visibility level
    
    # Location fields (V2)
    city = StringProperty()                     # City where community is based
    state = StringProperty()                    # State/province where community is based
    country = StringProperty()                  # Country where community is based
    address = StringProperty()                  # Full address of the community
    
    # Contact information (V2)
    website_url = StringProperty()              # Community website URL
    contact_email = StringProperty()            # Contact email for the community
    
    # Community settings (V2)
    enable_comments = BooleanProperty(default=True)  # Allow members to comment on posts
    
    # External system integration
    room_id = StringProperty()                  # Matrix chat room ID for real-time messaging integration
    
    # Timestamp tracking for audit and sorting purposes
    created_date = DateTimeProperty(default_now=True)    # When the community was first created
    updated_date = DateTimeProperty(default_now=True)    # Last modification timestamp (auto-updated)
    
    # Community statistics and metrics
    number_of_members = IntegerProperty(default=0)       # Cached count of active members for performance
    
    # Visual and branding elements
    group_invite_link = StringProperty()        # Shareable invitation link for easy joining
    group_icon_id = StringProperty()           # Reference to uploaded icon/avatar image
    cover_image_id = StringProperty()          # Reference to uploaded cover/banner image
    category = StringProperty()                # Broad categorization for discovery and filtering
    ai_generated = BooleanProperty(default=False)
    tags = ArrayProperty(StringProperty())
    # Community behavior and origin flags
    generated_community = BooleanProperty(default=False)  # True if AI-generated, False if user-created
    
    # Administrative permission controls
    # These settings determine what actions different member types can perform
    only_admin_can_message = BooleanProperty(default=False)        # Restricts messaging to admins only
    only_admin_can_add_member = BooleanProperty(default=False)     # Restricts member invitations to admins
    only_admin_can_remove_member = BooleanProperty(default=True)   # Restricts member removal to admins (default secure)
    # Core relationships - define how communities connect to other entities
    
    # User and membership relationships
    created_by = RelationshipTo('Users', 'CREATED_BY')              # The user who originally created this community
    members = RelationshipTo('Membership', 'MEMBER_OF')             # All membership records for this community
    
    # Content and engagement relationships
    community_review = RelationshipTo('CommunityReview', 'REVIEW_FOR')        # User reviews and ratings
    communitymessage = RelationshipTo('CommunityMessages', 'BELONGS_TO')      # Messages posted in community
    community_post = RelationshipTo('CommunityPost', 'HAS_POST')              # Posts created in community
    
    # Community profile and achievement relationships
    communitygoal = RelationshipTo('CommunityGoal', 'HAS_GOAL')               # Community objectives and targets
    communityactivity = RelationshipTo('CommunityActivity', 'HAS_ACTIVITY')   # Events and activities organized
    communityaffiliation = RelationshipTo('CommunityAffiliation', 'HAS_AFFILIATION')  # External partnerships/affiliations
    communityachievement = RelationshipTo('CommunityAchievement', 'HAS_ACHIEVEMENT')  # Milestones and accomplishments
    
    # Hierarchical community structure relationships
    # These enable complex community organization and nested groups
    child_communities = RelationshipTo('SubCommunity', 'HAS_CHILD_COMMUNITY')     # Direct sub-communities
    sibling_communities = RelationshipTo('SubCommunity', 'HAS_SIBLING_COMMUNITY') # Related communities at same level
    
    # Agent management relationships
    # These enable AI agent assignment and autonomous community management
    leader_agent = RelationshipTo('agentic.models.AgentCommunityAssignment', 'HAS_LEADER_AGENT')  # AI agent assigned as community leader


    def save(self, *args, **kwargs):
        """
        Override the default save method to automatically update the modification timestamp.
        
        This ensures that every time a community is modified, we track when the change occurred.
        This is crucial for:
        - Audit trails and change tracking
        - Sorting communities by recent activity
        - Cache invalidation strategies
        - API response optimization
        """
        self.updated_date = datetime.now()
        super().save(*args, **kwargs)
    
    def get_leader_agent(self):
        """
        Get the current leader agent for this community.
        
        Returns:
            Agent: The current leader agent, or None if no active leader
        """
        try:
            # Get all agent assignments for this community
            assignments = self.leader_agent.all()
            
            for assignment in assignments:
                if assignment.is_active():
                    agent = assignment.agent.single()
                    if agent and agent.is_active():
                        return agent
            
            return None
        except Exception:
            # Return None if there's any error getting the leader agent
            return None
    
    def has_leader_agent(self):
        """
        Check if this community has an active leader agent.
        
        Returns:
            bool: True if community has an active leader agent, False otherwise
        """
        return self.get_leader_agent() is not None
    
    def get_agent_assignments(self):
        """
        Get all agent assignments for this community.
        
        Returns:
            list: List of AgentCommunityAssignment objects for this community
        """
        try:
            return list(self.leader_agent.all())
        except Exception:
            return []
    
    class Meta:
        app_label = 'community'  # Django app label for proper model registration

    def __str__(self):
        """
        String representation of the community for admin interfaces and debugging.
        Returns the community name as it's the most user-friendly identifier.
        """
        return self.name


class CommunityMessages(DjangoNode, StructuredNode):
    """
    Community Messages Model - Handles all messaging within communities.
    
    This model manages the messaging system within communities, supporting:
    - Text messages with optional file attachments
    - Message visibility and privacy controls
    - Read/unread status tracking
    - Soft deletion for message management
    - Integration with community permission systems
    
    Business Logic:
    - Messages belong to a specific community context
    - Supports both public and private message types
    - Tracks read status for notification systems
    - Soft deletion preserves message history while hiding content
    - File attachments are referenced by ID for efficient storage
    
    Use Cases:
    - Community announcements from admins
    - General member discussions
    - File sharing within community context
    - Moderated communication channels
    """
    
    # Core identification and relationships
    uid = UniqueIdProperty()                                    # Unique message identifier
    community = RelationshipTo('Community', 'BELONGS_TO')      # Parent community for this message
    sender = RelationshipTo('Users', 'SENT_BY')               # User who sent the message
    
    # Message content and metadata
    content = StringProperty()                                  # Main text content of the message
    file_id = StringProperty()                                 # Reference to attached file (if any)
    title = StringProperty()                                   # Optional message title/subject
    
    # Message state and visibility controls
    is_read = BooleanProperty(default=False)                   # Read status for notification management
    is_deleted = BooleanProperty(default=False)                # Soft deletion flag
    is_public = BooleanProperty(default=True)                  # Public vs private message visibility
    
    # Timestamp for chronological ordering and audit
    timestamp = DateTimeProperty(default_now=True)             # When the message was created

    def send_message(self):
        """
        Process and send the message within the community.
        
        This method would typically handle:
        - Validation of message content and permissions
        - Notification dispatch to community members
        - Integration with real-time messaging systems (Matrix)
        - Spam and content filtering
        - Message delivery confirmation
        
        Note: Implementation details depend on specific business requirements
        and integration with external messaging systems.
        """
        # Implementation for sending messages
        pass
    
    class Meta:
        app_label = 'community'  # Django app registration

    def __str__(self):
        """
        String representation showing message title or content preview.
        Useful for admin interfaces and debugging.
        """
        return self.title or f"Message from {self.sender}" if hasattr(self, 'sender') else "Community Message"


class Membership(DjangoNode, StructuredNode):
    """
    Membership Model - Represents the relationship between a user and a community.
    
    This is a crucial junction model that defines:
    - User's role and permissions within a specific community
    - Membership status and approval workflow
    - Individual permission overrides and restrictions
    - Temporal tracking of membership lifecycle
    
    Business Logic:
    - Each user-community relationship requires a unique membership record
    - Supports hierarchical permission system (admin > leader > member)
    - Granular permission control for different community actions
    - Approval workflow for join requests (is_accepted flag)
    - Individual user restrictions (blocking, muting) without affecting others
    
    Permission Hierarchy:
    1. Admin: Full community management rights
    2. Leader: Limited management rights, typically content moderation
    3. Member: Basic participation rights with individual overrides
    
    Use Cases:
    - Managing community access control
    - Implementing approval workflows for private communities
    - Tracking user engagement and participation history
    - Enabling granular permission management
    """
    
    # Core identification and relationships
    uid = UniqueIdProperty()                                    # Unique membership record identifier
    user = RelationshipTo('Users', 'MEMBER')                   # The user who is a member
    community = RelationshipTo('Community', 'MEMBEROF')        # The community they belong to
    
    # Role and authority levels within the community
    is_admin = BooleanProperty(default=False)                  # Full administrative privileges
    is_leader = BooleanProperty(default=False)                 # Leadership role with limited admin rights
    
    # Membership status and lifecycle
    is_accepted = BooleanProperty(default=True)                # Whether membership is approved (for private communities)
    join_date = DateTimeProperty(default_now=True)             # When the user joined or was invited
    
    # Individual permission overrides and restrictions
    # These can override community-wide settings for specific users
    can_message = BooleanProperty(default=True)                # Permission to send messages in community
    is_blocked = BooleanProperty(default=False)                # User is blocked from community participation
    is_notification_muted = BooleanProperty(default=False)     # User has muted notifications from this community
    can_add_member = BooleanProperty(default=False)            # Permission to invite new members
    can_remove_member = BooleanProperty(default=False)         # Permission to remove other members
    
    class Meta:
        app_label = 'community'  # Django app registration

    def __str__(self):
        """
        String representation of the membership for admin and debugging.
        Shows the relationship between user and community.
        """
        return f"Membership: {self.user} in {self.community}" if hasattr(self, 'user') and hasattr(self, 'community') else self.uid





class CommunityProduct(DjangoNode, StructuredNode):
    """
    Community Product Integration Model - Links products to communities.
    
    This model manages the relationship between communities and products/services,
    enabling communities to:
    - Showcase relevant products or services
    - Create community-specific marketplaces
    - Implement approval workflows for product listings
    - Track community-product associations for analytics
    
    Business Logic:
    - Products must be approved before being visible in the community
    - Each product-community relationship is tracked separately
    - Supports moderation workflow through is_accepted flag
    - Maintains audit trail with creation and update timestamps
    
    Use Cases:
    - Community marketplaces and product showcases
    - Affiliate marketing within communities
    - Community-endorsed product recommendations
    - Integration with e-commerce platforms
    """
    
    uid = UniqueIdProperty()                                    # Unique identifier for this product-community link
    community = RelationshipTo('Community', 'HAS_PRODUCT')     # The community showcasing this product
    product_id = StringProperty(required=True)                 # Reference to the actual product in the product system
    is_accepted = BooleanProperty(default=False)               # Approval status for community moderation
    created_date = DateTimeProperty(default_now=True)          # When the product was first linked to community
    updated_date = DateTimeProperty(default_now=True)          # Last modification timestamp


class CommunityStory(DjangoNode, StructuredNode):
    """
    Community Story Integration Model - Links stories to communities.
    
    This model manages the relationship between communities and user stories,
    allowing communities to:
    - Feature relevant user stories and experiences
    - Create community-specific story collections
    - Implement approval workflows for story sharing
    - Build community narratives and testimonials
    
    Business Logic:
    - Stories require approval before being featured in communities
    - Each story-community relationship is independently managed
    - Supports content moderation through approval workflow
    - Tracks when stories are associated with communities
    
    Use Cases:
    - Community success stories and testimonials
    - User experience sharing within relevant communities
    - Community-curated content collections
    - Integration with story/content management systems
    """
    
    uid = UniqueIdProperty()                                    # Unique identifier for this story-community link
    community = RelationshipTo('Community', 'HAS_STORY')       # The community featuring this story
    story_id = StringProperty(required=True)                   # Reference to the actual story in the story system
    is_accepted = BooleanProperty(default=False)               # Approval status for community moderation
    created_date = DateTimeProperty(default_now=True)          # When the story was first linked to community
    updated_date = DateTimeProperty(default_now=True)          # Last modification timestamp


class Election(DjangoNode, StructuredNode):
    """
    Election Model - Manages democratic governance within communities.
    
    This model implements a comprehensive election system that enables:
    - Democratic selection of community leaders and roles
    - Time-bound nomination and voting periods
    - Transparent electoral processes with audit trails
    - Integration with community governance structures
    
    Business Logic:
    - Elections have distinct phases: nomination period, voting period, results
    - Only one active election per community at a time
    - Configurable duration for each phase of the election
    - Results are announced after voting period ends
    - Integration with community membership and role systems
    
    Election Lifecycle:
    1. Election created with start date and durations
    2. Nomination period: members can nominate themselves or others
    3. Voting period: eligible members vote for nominees
    4. Results announcement: winners are determined and roles assigned
    
    Use Cases:
    - Community leadership elections
    - Role-based position selection
    - Democratic decision-making processes
    - Community governance and representation
    """
    
    uid = UniqueIdProperty()                                    # Unique election identifier
    community = RelationshipTo('Community', 'HAS_ELECTION')    # Community holding this election
    is_active = BooleanProperty(default=False)                 # Whether election is currently active
    start_date = DateTimeProperty(required=True)               # When the election process begins
    nomination_duration = IntegerProperty(required=True)       # Duration in days for nomination period
    voting_duration = IntegerProperty(required=True)           # Duration in days for voting period
    result_announcement = DateTimeProperty()                    # When results will be/were announced

    def create_nomination(self, member):
        """
        Create a nomination for a member in this election.
        
        Args:
            member: The membership record of the nominee
            
        This method handles:
        - Validation that nomination period is active
        - Checking member eligibility for nomination
        - Creating the nomination record
        - Triggering any notification systems
        """
        nomination = Nomination(election=self, member=member)
        nomination.save()

    def get_nominations(self):
        """
        Retrieve all nominations for this election.
        
        Returns:
            QuerySet of Nomination objects for this election
            
        Used for:
        - Displaying candidate lists to voters
        - Election administration and monitoring
        - Results calculation and reporting
        """
        return self.nomination_set.all()

    def get_votes(self):
        """
        Retrieve all votes cast in this election.
        
        Returns:
            QuerySet of Vote objects for this election
            
        Used for:
        - Vote counting and results calculation
        - Election audit and verification
        - Statistical analysis of voting patterns
        """
        return self.vote_set.all()


class Nomination(DjangoNode, StructuredNode):
    """
    Nomination Model - Represents a candidate nomination in community elections.
    
    This model tracks individual nominations within the democratic election process:
    - Links nominees to specific elections
    - Tracks community support through vibes/endorsements
    - Maintains nomination timeline and status
    - Enables transparent candidate management
    
    Business Logic:
    - Each nomination represents one member's candidacy in one election
    - Vibes system allows community members to show support for nominees
    - Nominations are time-bound to the election's nomination period
    - Only eligible community members can be nominated
    
    Use Cases:
    - Candidate registration and management
    - Community endorsement tracking
    - Election ballot preparation
    - Democratic participation measurement
    """
    
    uid = UniqueIdProperty()                                        # Unique nomination identifier
    election = RelationshipTo('Election', 'NOMINATION_FOR')         # The election this nomination belongs to
    member = RelationshipTo('Membership', 'NOMINATED_MEMBER')       # The community member being nominated
    vibes_received = IntegerProperty(default=0)                     # Community support/endorsement count
    created_date = DateTimeProperty(default_now=True)               # When nomination was submitted
    updated_date = DateTimeProperty(default_now=True)               # Last modification timestamp


class Vote(DjangoNode, StructuredNode):
    """
    Vote Model - Records individual votes cast in community elections.
    
    This model ensures secure and transparent voting within the democratic process:
    - Links voters to their chosen nominees
    - Maintains vote integrity and audit trails
    - Supports election result calculation
    - Enables democratic participation tracking
    
    Business Logic:
    - One vote per eligible member per election
    - Votes are anonymous but auditable
    - Voting is restricted to the election's voting period
    - Only community members can vote for nominees
    
    Security Considerations:
    - Vote records are immutable once cast
    - Voter privacy is maintained while ensuring auditability
    - Prevents duplicate voting through membership validation
    
    Use Cases:
    - Democratic decision making
    - Election result calculation
    - Participation analytics
    - Governance transparency
    """
    
    uid = UniqueIdProperty()                                        # Unique vote identifier
    election = RelationshipTo('Election', 'VOTE_FOR')              # The election this vote belongs to
    voter = RelationshipTo('Membership', 'VOTED_BY')               # The community member who cast this vote
    nominee = RelationshipTo('Nomination', 'VOTED_TO')             # The nomination this vote supports
    created_date = DateTimeProperty(default_now=True)              # When the vote was cast (immutable)
    updated_date = DateTimeProperty(default_now=True)              # System timestamp for audit purposes


class Role(DjangoNode, StructuredNode):
    """
    Role Model - Defines specific roles and positions within communities.
    
    This model creates a flexible role-based permission system that enables:
    - Custom role definition for different community needs
    - Hierarchical permission structures
    - Role-based access control implementation
    - Community-specific governance structures
    
    Business Logic:
    - Roles are community-specific and can be customized
    - Each role defines a set of permissions and responsibilities
    - Roles can be assigned through elections or administrative actions
    - Supports both permanent and temporary role assignments
    
    Common Role Types:
    - Moderator: Content moderation and community guidelines enforcement
    - Event Organizer: Planning and managing community events
    - Content Curator: Managing featured content and announcements
    - Ambassador: Representing community in external interactions
    
    Use Cases:
    - Community governance and organization
    - Permission management and access control
    - Responsibility delegation and accountability
    - Democratic role assignment through elections
    """
    
    uid = UniqueIdProperty()                                        # Unique role identifier
    community = RelationshipTo('Community', 'ROLE_IN')             # The community this role belongs to
    name = StringProperty(required=True)                           # Human-readable role name (e.g., "Moderator", "Event Organizer")
    created_date = DateTimeProperty(default_now=True)              # When the role was created
    updated_date = DateTimeProperty(default_now=True)              # Last modification timestamp


class CommunityRole(DjangoNode, StructuredNode):
    """
    CommunityRole Model - Links community members to their assigned roles.
    
    This model manages the assignment and tracking of roles within communities:
    - Connects members to their specific roles and responsibilities
    - Enables role-based permission enforcement
    - Supports role activation/deactivation for temporary assignments
    - Maintains role assignment history and accountability
    
    Business Logic:
    - Members can hold multiple roles simultaneously
    - Roles can be temporarily deactivated without deletion
    - Role assignments are community-specific
    - Supports both elected and appointed role assignments
    
    Permission Flow:
    - Role assignment grants specific permissions to members
    - Active roles determine current member capabilities
    - Inactive roles preserve historical assignments
    - Role changes are tracked through timestamps
    
    Use Cases:
    - Role-based access control implementation
    - Community governance and organization
    - Permission management and delegation
    - Role assignment tracking and auditing
    """
    
    uid = UniqueIdProperty()                                        # Unique role assignment identifier
    membership = RelationshipTo('Membership', 'ROLE_FOR')           # The member receiving this role
    role = RelationshipTo('Role', 'ROLE_OF')                       # The specific role being assigned
    created_date = DateTimeProperty(default_now=True)              # When the role was assigned
    updated_date = DateTimeProperty(default_now=True)              # Last modification (activation/deactivation)


class Message(DjangoNode, StructuredNode):
    """
    Message Model - Represents individual messages within community discussions.
    
    This model handles all forms of community communication and messaging:
    - Supports various message types (text, media, announcements)
    - Enables message hiding for moderation purposes
    - Tracks message authorship and community context
    - Maintains message history and threading capabilities
    
    Business Logic:
    - Messages are community-scoped and user-authored
    - Hidden messages are preserved but not displayed
    - Message permissions are governed by community settings
    - Timestamps enable chronological message ordering
    
    Message States:
    - Visible: Normal messages displayed to community members
    - Hidden: Messages hidden by moderation but preserved
    - Timestamped: All messages maintain creation and update times
    
    Use Cases:
    - Community discussions and conversations
    - Content moderation and message management
    - Communication history and audit trails
    - Community engagement and interaction
    """
    
    uid = UniqueIdProperty()                                        # Unique message identifier
    community = RelationshipTo('Community', 'MESSAGE_IN')          # The community this message belongs to
    sender = RelationshipTo('User', 'MESSAGE_FROM')                # The user who sent this message
    content = StringProperty(required=True)                        # The actual message content/text
    timestamp = DateTimeProperty(default_now=True)                 # When the message was sent
    is_hidden = BooleanProperty(default=False)                     # Whether message is hidden by moderation
    created_date = DateTimeProperty(default_now=True)              # Message creation timestamp
    updated_date = DateTimeProperty(default_now=True)              # Last modification timestamp


class CommunityKeyword(DjangoNode, StructuredNode):
    """
    CommunityKeyword Model - Manages searchable keywords and tags for communities.
    
    This model enables community discovery and categorization through keywords:
    - Associates relevant keywords with communities for search optimization
    - Supports community categorization and filtering
    - Enables tag-based community discovery
    - Facilitates content organization and findability
    
    Business Logic:
    - Keywords are community-specific and help with discoverability
    - Unique indexing prevents duplicate keywords across the platform
    - Keywords support search functionality and filtering
    - Community admins can manage keyword associations
    
    Search and Discovery:
    - Keywords improve community search results
    - Enable category-based community browsing
    - Support recommendation algorithms
    - Facilitate community matching based on interests
    
    Use Cases:
    - Community search and discovery
    - Content categorization and organization
    - Interest-based community recommendations
    - SEO optimization for community visibility
    """
    
    uid = UniqueIdProperty()                                        # Unique keyword association identifier
    community = RelationshipTo('Community', 'KEYWORD_FOR')         # The community this keyword describes
    keyword = StringProperty(unique_index=True, required=True)     # The actual keyword/tag text (globally unique)
    created_date = DateTimeProperty(default_now=True)              # When the keyword was added
    updated_date = DateTimeProperty(default_now=True)              # Last modification timestamp


class CommunityExit(DjangoNode, StructuredNode):
    """
    CommunityExit Model - Records when users leave communities.
    
    This model tracks community departures for analytics and improvement:
    - Documents user exit patterns and timing
    - Enables community health monitoring
    - Supports retention analysis and improvement strategies
    - Maintains historical records of community membership changes
    
    Business Logic:
    - Exit records are created when users voluntarily leave communities
    - Exit data supports community analytics and health metrics
    - Historical exit patterns inform community management decisions
    - Helps identify potential issues affecting member retention
    
    Analytics Applications:
    - Member retention rate calculation
    - Exit pattern identification and analysis
    - Community health monitoring
    - Churn prediction and prevention
    
    Use Cases:
    - Community retention analysis
    - Exit trend monitoring
    - Community health assessment
    - Member lifecycle tracking
    """
    
    uid = UniqueIdProperty()                                        # Unique exit record identifier
    community = RelationshipTo('Community', 'EXIT_FROM')           # The community the user left
    user = RelationshipTo('User', 'EXIT_BY')                       # The user who left the community
    exit_date = DateTimeProperty(default_now=True)                 # When the user left the community
    created_date = DateTimeProperty(default_now=True)              # Record creation timestamp
    updated_date = DateTimeProperty(default_now=True)              # Last modification timestamp


class CommunityRule(DjangoNode, StructuredNode):
    """
    CommunityRule Model - Defines and manages community guidelines and rules.
    
    This model establishes the governance framework for community behavior:
    - Sets clear expectations for community member conduct
    - Enables rule-based moderation and enforcement
    - Supports community self-governance and transparency
    - Provides foundation for consistent community management
    
    Business Logic:
    - Rules are community-specific and customizable
    - Rule text contains the complete guideline or policy
    - Rules provide basis for moderation decisions
    - Clear rule definitions ensure member understanding
    
    Rule Categories (Common):
    - Content Guidelines: What can and cannot be posted
    - Behavior Standards: Expected member conduct and interactions
    - Participation Rules: How members should engage
    - Moderation Policies: Consequences for rule violations
    
    Use Cases:
    - Community governance and moderation
    - Member onboarding and expectation setting
    - Conflict resolution and dispute handling
    - Transparent community management
    """
    
    uid = UniqueIdProperty()                                        # Unique rule identifier
    community = RelationshipTo('Community', 'RULE_FOR')            # The community this rule applies to
    rule_text = StringProperty(required=True)                      # Complete rule text and guidelines
    created_date = DateTimeProperty(default_now=True)              # When the rule was created
    updated_date = DateTimeProperty(default_now=True)              # Last rule modification timestamp


class CommunityReview(DjangoNode, StructuredNode):
    """
    CommunityReview Model - Manages user reviews and feedback for communities and subcommunities.
    
    This model enables comprehensive community assessment and feedback collection:
    - Allows users to rate and review community experiences
    - Supports both community and subcommunity reviews
    - Enables reaction-based feedback with vibes scoring
    - Provides insights for community improvement and reputation
    
    Business Logic:
    - Users can review communities or subcommunities they have experience with
    - Vibe scoring provides quantitative assessment (typically 1.0-5.0 scale)
    - Reactions provide quick qualitative feedback (Like, Love, etc.)
    - Reviews can include detailed content and optional file attachments
    - Soft deletion preserves review history while hiding inappropriate content
    
    Review Components:
    - Reaction: Quick emotional response (Like, Love, Dislike, etc.)
    - Vibe: Numerical score reflecting overall experience
    - Title: Brief summary of the review
    - Content: Detailed feedback about community experience
    - File: Optional supporting media or documentation
    
    Use Cases:
    - Community quality assessment and improvement
    - User decision-making for community joining
    - Community reputation management
    - Feedback collection for community enhancement
    - Subcommunity evaluation within larger communities
    """
    
    uid = UniqueIdProperty()                                        # Unique review identifier
    byuser = RelationshipTo('Users', 'REVIEW_BY')                  # The user who wrote this review
    tocommunity = RelationshipTo('Community', 'REVIEW_FOR')        # The community being reviewed (optional)
    tosubcommunity=RelationshipTo('SubCommunity', 'REVIEW_FOR')    # The subcommunity being reviewed (optional)
    reaction = StringProperty(default='Like')                      # Quick reaction type (Like, Love, etc.)
    vibe = FloatProperty(default=2.0)                              # Numerical rating score (1.0-5.0 scale)
    title = StringProperty()                                        # Brief review title or summary
    content = StringProperty()                                      # Detailed review content and feedback
    file_id = StringProperty()                                      # Optional attached file identifier
    is_deleted = BooleanProperty(default=False)                    # Soft deletion flag for content moderation
    timestamp = DateTimeProperty(default_now=True)                 # When the review was submitted

    class Meta:
        app_label = 'community'

    def __str__(self):
        """
        String representation showing the reaction type.
        
        Returns:
            str: The reaction type (e.g., 'Like', 'Love')
        """
        return self.reaction


class CommunityUserBlock(DjangoNode, StructuredNode):
    """
    CommunityUserBlock Model - Manages user blocking relationships within communities.
    
    This model handles user-to-user blocking for community safety and comfort:
    - Enables users to block other users to prevent unwanted interactions
    - Supports community moderation and harassment prevention
    - Maintains blocking relationships and timestamps
    - Provides foundation for content filtering and interaction control
    
    Business Logic:
    - Users can block other users to prevent direct communication
    - Blocking is unidirectional (blocker blocks blocked user)
    - Blocked users cannot send messages or interact with blocker
    - Blocking relationships are preserved with creation timestamps
    - Supports community safety and user comfort
    
    Blocking Effects:
    - Prevents direct messaging between users
    - Filters blocked user's content from blocker's view
    - Restricts interaction capabilities
    - Maintains user privacy and safety
    
    Use Cases:
    - Harassment prevention and user safety
    - Content filtering and personalization
    - Community moderation support
    - User comfort and control enhancement
    """
    
    uid = UniqueIdProperty()                                        # Unique blocking relationship identifier
    blocker = RelationshipTo('User', 'BLOCKER')                    # The user who initiated the block
    blocked = RelationshipTo('User', 'BLOCKED')                    # The user who is being blocked
    created_at = DateTimeProperty(default_now=True)                # When the blocking relationship was created

    def __str__(self):
        """
        String representation showing the blocking relationship.
        
        Returns:
            str: Description of who blocked whom
        """
        return "{} blocked by {}".format(self.blocked.username, self.blocker.username)

class CommunityGoal(DjangoNode,StructuredNode):
    """
    CommunityGoal Model - Manages community objectives and aspirational targets.
    
    This model enables communities to define and track their collective goals:
    - Allows communities to set clear objectives and aspirations
    - Supports both community-wide and subcommunity-specific goals
    - Enables goal tracking with supporting documentation
    - Facilitates community alignment and progress measurement
    
    Business Logic:
    - Goals can be created by community members and assigned to communities/subcommunities
    - Each goal has a clear name and detailed description
    - Supporting files can be attached for context or documentation
    - Soft deletion preserves goal history while hiding outdated objectives
    - Goals help align community efforts and measure progress
    
    Goal Types (Common):
    - Growth Goals: Membership, engagement, or reach targets
    - Impact Goals: Community influence or social impact objectives
    - Quality Goals: Content quality or community culture improvements
    - Event Goals: Organizing events, meetups, or activities
    
    Use Cases:
    - Community strategic planning and alignment
    - Progress tracking and accountability
    - Member motivation and engagement
    - Community development and growth
    - Subcommunity focus and direction
    """
    
    uid = UniqueIdProperty()                                        # Unique goal identifier
    name = StringProperty(required=True)                           # Goal name or title
    description = StringProperty(required=True)                    # Detailed goal description and context
    file_id=ArrayProperty(base_property=StringProperty())          # Supporting files or documentation
    created_by = RelationshipTo('Users', 'CREATED_BY')             # User who created this goal
    community = RelationshipTo('Community', 'GOAL_FOR')           # Community this goal belongs to (optional)
    subcommunity = RelationshipTo('SubCommunity', 'GOAL_FOR')     # Subcommunity this goal belongs to (optional)
    vibe_reactions = RelationshipTo('CommunityContentVibe', 'HAS_VIBE_REACTION')  # Vibe reactions
    timestamp = DateTimeProperty(default_now=True)                # When the goal was created
    is_deleted = BooleanProperty(default=False)                   # Soft deletion flag

    class Meta:
        app_label = 'community'

    def __str__(self):
        """
        String representation showing the goal name.
        
        Returns:
            str: The goal name
        """
        return self.name
    

class CommunityActivity(DjangoNode, StructuredNode):
    """
    CommunityActivity Model - Manages community events, activities, and engagements.
    
    This model handles the organization and tracking of community activities:
    - Enables communities to organize events, meetups, and activities
    - Supports both community-wide and subcommunity-specific activities
    - Allows activity categorization through activity types
    - Facilitates community engagement and participation tracking
    
    Business Logic:
    - Activities can be created by community members for communities/subcommunities
    - Each activity has a name, description, and optional type categorization
    - Activities can be scheduled with specific dates and times
    - Supporting files can include event materials, agendas, or resources
    - Soft deletion preserves activity history while hiding cancelled events
    
    Activity Types (Common):
    - meetup: In-person or virtual community gatherings
    - workshop: Educational or skill-building sessions
    - social: Social events and community bonding activities
    - project: Collaborative community projects or initiatives
    - discussion: Structured discussions or forums
    
    Use Cases:
    - Event planning and organization
    - Community engagement and participation
    - Activity scheduling and coordination
    - Community building and networking
    - Subcommunity-specific events and activities
    """
    
    uid = UniqueIdProperty()                                        # Unique activity identifier
    name = StringProperty(required=True)                           # Activity name or title
    description = StringProperty()                                  # Detailed activity description
    activity_type = StringProperty()                               # Type/category of activity (meetup, workshop, etc.)
    file_id=ArrayProperty(base_property=StringProperty())          # Supporting files, materials, or resources
    created_by = RelationshipTo('Users', 'CREATED_BY')             # User who created this activity
    community = RelationshipTo('Community', 'ACTIVITY_FOR')       # Community this activity belongs to (optional)
    subcommunity = RelationshipTo('SubCommunity', 'ACTIVITY_FOR') # Subcommunity this activity belongs to (optional)
    vibe_reactions = RelationshipTo('CommunityContentVibe', 'HAS_VIBE_REACTION')  # Vibe reactions
    date = DateTimeProperty()                                      # Scheduled date and time for the activity
    is_deleted = BooleanProperty(default=False)                   # Soft deletion flag

    class Meta:
        app_label = 'community'

    def __str__(self):
        """
        String representation showing the activity name.
        
        Returns:
            str: The activity name
        """
        return self.name
    

class CommunityAffiliation(DjangoNode, StructuredNode):
    """
    CommunityAffiliation Model - Manages community partnerships and organizational relationships.
    
    This model tracks formal and informal affiliations between communities and external entities:
    - Records partnerships with organizations, institutions, or other communities
    - Maintains affiliation history with dates and documentation
    - Supports both community-wide and subcommunity-specific affiliations
    - Enables relationship tracking for networking and collaboration
    
    Business Logic:
    - Affiliations represent formal or informal relationships with external entities
    - Each affiliation has a specific subject/purpose and date of establishment
    - Supporting documentation can be attached for verification or details
    - Soft deletion preserves affiliation history while hiding ended relationships
    - Affiliations help communities build networks and credibility
    
    Affiliation Types (Common):
    - Partnership: Formal business or organizational partnerships
    - Sponsorship: Financial or resource sponsorship relationships
    - Collaboration: Joint projects or initiatives with other entities
    - Membership: Community membership in larger organizations
    - Recognition: Official recognition or endorsement from entities
    
    Use Cases:
    - Partnership and collaboration tracking
    - Community credibility and networking
    - Relationship management and history
    - External validation and recognition
    - Resource and opportunity identification
    """
    
    uid = UniqueIdProperty()                                        # Unique affiliation identifier
    entity = StringProperty(required=True)                         # Name of the affiliated entity/organization
    date = DateTimeProperty(required=True)                         # Date when the affiliation was established
    subject = StringProperty(required=True)                        # Purpose or subject of the affiliation
    file_id=ArrayProperty(base_property=StringProperty())          # Supporting documentation or agreements
    created_by = RelationshipTo('Users', 'CREATED_BY')             # User who recorded this affiliation
    community = RelationshipTo('Community', 'AFFILIATION_FOR')    # Community this affiliation belongs to (optional)
    subcommunity = RelationshipTo('SubCommunity', 'AFFILIATION_FOR') # Subcommunity this affiliation belongs to (optional)
    vibe_reactions = RelationshipTo('CommunityContentVibe', 'HAS_VIBE_REACTION')  # Vibe reactions
    timestamp = DateTimeProperty(default_now=True)                # When the affiliation record was created
    is_deleted = BooleanProperty(default=False)                   # Soft deletion flag

    class Meta:
        app_label = 'community'

    def __str__(self):
        """
        String representation showing the affiliated entity name.
        
        Returns:
            str: The entity name
        """
        return self.entity

class CommunityAchievement(DjangoNode, StructuredNode):
    """
    CommunityAchievement Model - Records community accomplishments and milestones.
    
    This model tracks significant achievements and milestones for communities:
    - Documents community successes, awards, and recognitions
    - Maintains achievement history with dates and supporting evidence
    - Supports both community-wide and subcommunity-specific achievements
    - Enables progress tracking and community pride building
    
    Business Logic:
    - Achievements represent significant accomplishments or milestones
    - Each achievement has a specific subject/description and date of accomplishment
    - Supporting files can include certificates, media coverage, or evidence
    - Soft deletion preserves achievement history while hiding disputed accomplishments
    - Achievements help build community reputation and member pride
    
    Achievement Types (Common):
    - Awards: External recognition, prizes, or honors received
    - Milestones: Membership, engagement, or growth milestones reached
    - Impact: Measurable positive impact or outcomes achieved
    - Recognition: Media coverage, features, or public recognition
    - Goals: Completion of significant community goals or projects
    
    Use Cases:
    - Community reputation and credibility building
    - Member motivation and pride enhancement
    - Progress tracking and milestone celebration
    - External validation and recognition
    - Community marketing and promotion
    """
    
    uid = UniqueIdProperty()                                        # Unique achievement identifier
    entity = StringProperty(required=True)                         # Name or title of the achievement
    date = DateTimeProperty(required=True)                         # Date when the achievement was accomplished
    subject = StringProperty(required=True)                        # Description or subject of the achievement
    file_id=ArrayProperty(base_property=StringProperty())          # Supporting evidence, certificates, or media
    created_by = RelationshipTo('Users', 'CREATED_BY')             # User who recorded this achievement
    community = RelationshipTo('Community', 'ACHIEVEMENT_FOR')    # Community this achievement belongs to (optional)
    subcommunity = RelationshipTo('SubCommunity', 'ACHIEVEMENT_FOR') # Subcommunity this achievement belongs to (optional)
    vibe_reactions = RelationshipTo('CommunityContentVibe', 'HAS_VIBE_REACTION')  # Vibe reactions
    timestamp = DateTimeProperty(default_now=True)                # When the achievement record was created
    is_deleted = BooleanProperty(default=False)                   # Soft deletion flag

    class Meta:
        app_label = 'community'

    def __str__(self):
        """
        String representation showing the achievement entity name.
        
        Returns:
            str: The achievement entity name
        """
        return self.entity


class CommunityContentVibe(DjangoNode, StructuredNode):
    """
    Neo4j-based model for storing vibe reactions to community content.
    
    This model represents vibe reactions using Neo4j graph database,
    similar to ProfileContentVibe but for community content (achievements, activities, goals, affiliations).
    Integrates with the IndividualVibe system from PostgreSQL for standardized vibe metadata.
    
    Business Logic:
    - Stores vibe reaction data in Neo4j graph structure
    - Each reaction references an IndividualVibe for metadata (weightages, name)
    - Supports relationships to multiple community content types
    - Intensity range: 1.0 to 5.0 for granular reactions
    - Only one active vibe per user per content item (updates replace)
    - Used for user score calculations via VibeUtils
    
    Use Cases:
    - User engagement and endorsement of community content
    - Community content validation and credibility
    - Vibe-based scoring and reputation systems
    - Community content popularity tracking
    - Analytics and recommendation algorithms
    """
    uid = UniqueIdProperty()  # Unique identifier
    
    # Content relationships (one will be active per vibe)
    community_achievement = RelationshipFrom('CommunityAchievement', 'HAS_VIBE_REACTION')  # Related achievement
    community_activity = RelationshipFrom('CommunityActivity', 'HAS_VIBE_REACTION')  # Related activity
    community_goal = RelationshipFrom('CommunityGoal', 'HAS_VIBE_REACTION')  # Related goal
    community_affiliation = RelationshipFrom('CommunityAffiliation', 'HAS_VIBE_REACTION')  # Related affiliation
    
    # User relationship
    reacted_by = RelationshipTo('Users', 'REACTED_BY')  # User who sent the vibe
    
    # Vibe data from PostgreSQL IndividualVibe model
    individual_vibe_id = IntegerProperty()  # References IndividualVibe.id
    vibe_name = StringProperty(required=True)  # From IndividualVibe.name_of_vibe
    vibe_intensity = FloatProperty(required=True)  # User's intensity selection (1.0-5.0)
    
    # Metadata
    reaction_type = StringProperty(default="vibe")  # Type of reaction
    timestamp = DateTimeProperty(default_now=True)  # Reaction timestamp
    is_active = BooleanProperty(default=True)  # Active status flag
    
    def save(self, *args, **kwargs):
        """Override save to ensure timestamp is updated."""
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'community'
    
    def __str__(self):
        """Return vibe name and intensity for string representation."""
        return f"{self.vibe_name} - {self.vibe_intensity}"
    

class CommunityRoleManager(models.Model):
    """
    Manages custom roles and permissions for communities.
    
    This model allows communities to define custom roles beyond the basic admin/member
    structure, with granular permissions for different community actions. Each role
    is stored as JSON data with specific permissions and can be assigned to members.
    
    Business Logic:
    - Enables flexible permission systems for large communities
    - Supports hierarchical role structures with custom permissions
    - Allows dynamic role creation and modification by community admins
    - Integrates with CommunityRoleAssignment for user-role mapping
    
    Use Cases:
    - Creating moderator roles with specific permissions
    - Setting up content curator roles for community management
    - Defining custom roles for community events or projects
    """
    community_uid = models.CharField(max_length=255, null=True, blank=True)  # Unique identifier for the community
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  # Admin who created the role system
    created_on = models.DateTimeField(default=timezone.now)  # Timestamp of role system creation
    roles = models.JSONField(default=list)  # JSON array storing role definitions with permissions
    
    class Meta:
        verbose_name = 'Community Role Manager'
        verbose_name_plural = 'Community Role Managers'
        ordering = ['-created_on']

    def __str__(self):
        return f"CommunityRoleManager for {self.community_uid} by {self.created_by.username}"

    def add_roles(self, role_name, **permissions):
        """Add a role with an incremented ID and permissions to the roles list."""
        # Determine the next ID
        if self.roles:
            # Extract current IDs and find the max
            max_id = max(role.get('id', 0) for role in self.roles)
            next_id = max_id + 1
        else:
            # Start IDs from 1 if there are no existing roles
            next_id = 1

        role_info = {
            'id': next_id,  # Assign the next available ID
            'role_name': role_name,
            **permissions
        }
        
        self.roles.append(role_info)

    def get_roles(self):
        """Retrieve all roles and their permissions."""
        return self.roles

    def get_role_permissions(self, role_name):
        """Retrieve permissions for a specific role."""
        for role in self.roles:
            if role['role_name'] == role_name:
                return role
        return None  # Role not found

class CommunityRoleAssignment(models.Model):
    """
    Manages the assignment of custom roles to community members.
    
    This model handles the mapping between users and their assigned roles within
    a community, ensuring proper permission enforcement and role management.
    
    Business Logic:
    - Prevents users from having multiple conflicting roles
    - Maintains audit trail of role assignments
    - Supports bulk role assignments for efficiency
    - Integrates with CommunityRoleManager for role definitions
    
    Use Cases:
    - Assigning moderator roles to trusted members
    - Bulk assignment of roles during community setup
    - Managing role changes and promotions
    """
    community_uid = models.CharField(max_length=255, null=True, blank=True)  # Community identifier for role assignments
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  # Admin who made the role assignments
    created_on = models.DateTimeField(default=timezone.now)  # Timestamp of assignment creation
    assigned_to = models.JSONField(default=list)  # JSON array mapping role IDs to user UIDs

    class Meta:
        verbose_name = 'Role Assignment'
        verbose_name_plural = 'Role Assignments'
        ordering = ['-created_on']

    def __str__(self):
        return f"RoleAssignment for {self.community_uid} by {self.created_by.username}"

    def assign_role(self, role_id, user_uid_list):
        """
        Assign a role to multiple users.
        Ensure the same user is not assigned to multiple roles within the same community.
        """
        # Collect all existing user_uids across all role assignments
        all_assigned_users = {user_uid for assignment in self.assigned_to for user_uid in assignment['user_uids']}

        # Check if any user_uid in user_uid_list is already assigned to a different role
        for user_uid in user_uid_list:
            if user_uid in all_assigned_users:
                raise ValueError(f"User with UID '{user_uid}' is already assigned to another role in this community.")

        # Check if the role_id already exists in the assigned_to list
        for assignment in self.assigned_to:
            if assignment['role_id'] == role_id:
                # Append new user_uids to the existing list if role_id exists
                assignment['user_uids'] = list(set(assignment['user_uids'] + user_uid_list))
                break
        else:
            # Add a new role assignment if role_id does not exist
            new_assignment = {
                'role_id': role_id,
                'user_uids': user_uid_list
            }
            self.assigned_to.append(new_assignment)

        self.save()

    def get_assigned_roles(self):
        """
        Retrieve all role assignments for this community.
        """
        return self.assigned_to

    def get_users_for_role(self, role_id):
        """
        Retrieve all users assigned to a specific role_id.
        """
        for assignment in self.assigned_to:
            if assignment['role_id'] == role_id:
                return assignment['user_uids']
        return []


class SubCommunity(DjangoNode, StructuredNode):
    """
    Represents a sub-community within a larger community structure.
    
    Sub-communities allow for hierarchical organization of communities, enabling
    specialized groups within larger communities. They inherit some properties
    from their parent community while maintaining their own identity and rules.
    
    Business Logic:
    - Supports nested community structures for better organization
    - Inherits permissions and settings from parent community when applicable
    - Allows independent management while maintaining parent-child relationships
    - Enables specialized groups for different interests or purposes
    
    Use Cases:
    - Creating topic-specific groups within larger communities
    - Organizing regional chapters of global communities
    - Setting up project teams within organizational communities
    """
    CIRCLE_CHOICES = {
        'Outer': 'outer circle',  # Public access level
        'Inner': 'inner circle',  # Restricted access level
        'Universal': 'universal'  # Universal access level
    }

    uid = UniqueIdProperty()  # Unique identifier for the sub-community
    name = StringProperty(required=True)  # Name of the sub-community
    username = StringProperty(unique_index=True)  # Unique handle/username for the sub-community (V2)
    description = StringProperty()  # Detailed description of the sub-community's purpose
    sub_community_type = StringProperty()  # Type classification of the sub-community
    sub_community_group_type = StringProperty()  # Group type for organizational purposes
    sub_community_circle = StringProperty(choices=CIRCLE_CHOICES.items())  # Access level circle
    
    # Location fields (V2)
    city = StringProperty()  # City where sub-community is based
    state = StringProperty()  # State/province where sub-community is based
    country = StringProperty()  # Country where sub-community is based
    address = StringProperty()  # Full address of the sub-community
    
    # Contact information (V2)
    website_url = StringProperty()  # Sub-community website URL
    contact_email = StringProperty()  # Contact email for the sub-community
    
    # Sub-community settings (V2)
    enable_comments = BooleanProperty(default=True)  # Allow members to comment on posts
    
    room_id = StringProperty()  # Associated chat room identifier
    created_date = DateTimeProperty(default_now=True)  # Timestamp of sub-community creation
    updated_date = DateTimeProperty(default_now=True)  # Timestamp of last update
    number_of_members = IntegerProperty(default=0)  # Current member count
    group_invite_link = StringProperty()  # Invitation link for joining
    group_icon_id = StringProperty()  # Icon image identifier
    cover_image_id = StringProperty()  # Cover image identifier
    category = StringProperty()  # Category classification
    only_admin_can_message = BooleanProperty(default=False)  # Message permission restriction
    only_admin_can_add_member = BooleanProperty(default=False)  # Member addition permission
    only_admin_can_remove_member = BooleanProperty(default=True)  # Member removal permission
    created_by = RelationshipTo('Users', 'CREATED_BY')
    parent_community = RelationshipTo('Community', 'PARENT_COMMUNITY')
    sub_community_members=RelationshipTo('SubCommunityMembership', 'MEMBER_OF')

    # Self-referencing relationship for hierarchy
    sub_community_parent = RelationshipTo('SubCommunity', 'PARENT_OF')
    sub_community_children = RelationshipTo('SubCommunity', 'HAS_CHILD_COMMUNITY')
    sub_community_sibling = RelationshipTo('SubCommunity', 'HAS_SIBLING_COMMUNITY')
    community_post=RelationshipTo('CommunityPost', 'HAS_POST')
    communitygoal=RelationshipTo('CommunityGoal', 'HAS_GOAL')
    communityactivity=RelationshipTo('CommunityActivity', 'HAS_ACTIVITY')
    communityaffiliation=RelationshipTo('CommunityAffiliation', 'HAS_AFFILIATION')
    communityachievement=RelationshipTo('CommunityAchievement', 'HAS_ACHIEVEMENT')
    community_review = RelationshipTo('CommunityReview', 'REVIEW_FOR')

    def save(self, *args, **kwargs):
        self.updated_date = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'community' #this is the name of app registered in setting.py

    def __str__(self):
        return self.name
    


class SubCommunityMembership(DjangoNode, StructuredNode):
    """
    Manages membership relationships between users and sub-communities.
    
    This model handles the specific membership details for users within
    sub-communities, including permissions, status, and administrative roles.
    
    Business Logic:
    - Inherits base permissions from parent community membership
    - Allows sub-community specific permission overrides
    - Supports hierarchical permission inheritance
    - Maintains separate admin roles for sub-community management
    
    Use Cases:
    - Managing sub-community specific permissions
    - Tracking user participation in specialized groups
    - Handling sub-community administrative roles
    """
    uid = UniqueIdProperty()  # Unique identifier for the membership
    user = RelationshipTo('Users', 'MEMBER')  # User who is a member
    sub_community = RelationshipTo('SubCommunity', 'MEMBEROF')  # Sub-community being joined
    is_admin = BooleanProperty(default=False)  # Administrative privileges in sub-community
    is_accepted = BooleanProperty(default=True)  # Membership acceptance status
    join_date = DateTimeProperty(default_now=True)  # Date when user joined sub-community
    can_message = BooleanProperty(default=True)  # Permission to send messages
    is_blocked = BooleanProperty(default=False)  # Blocked status in sub-community
    is_notification_muted = BooleanProperty(default=False)  # Notification preferences
    can_add_member = BooleanProperty(default=False)  # Permission to add new members
    can_remove_member = BooleanProperty(default=False)  # Permission to remove members
    room_id = StringProperty()  # Associated chat room identifier
    

    
    class Meta:
        app_label='community'

    def __str__(self):
        return self.uid
    




    
class SubCommunityRoleManager(models.Model):
    """
    Manages custom roles and permissions for sub-communities.
    
    Similar to CommunityRoleManager but specifically for sub-community role management.
    Allows sub-communities to have their own role hierarchy independent of or
    in addition to the parent community's role system.
    
    Business Logic:
    - Enables sub-community specific role definitions
    - Supports inheritance from parent community roles
    - Allows granular permission control at sub-community level
    - Integrates with SubCommunityRoleAssignment for user mapping
    
    Use Cases:
    - Creating specialized roles for project teams
    - Setting up sub-community specific moderator roles
    - Managing permissions for topic-specific groups
    """
    sub_community_uid = models.CharField(max_length=255, null=True, blank=True)  # Sub-community identifier
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  # Admin who created the role system
    created_on = models.DateTimeField(default=timezone.now)  # Timestamp of role system creation
    role_data = models.JSONField(default=list)  # JSON array storing role definitions with permissions

    class Meta:
        verbose_name = 'Sub Community Role Manager'
        verbose_name_plural = 'Sub Community Role Managers'
        ordering = ['-created_on']

    def __str__(self):
        return f"SubCommunityRoleManager for {self.sub_community_uid} by {self.created_by.username}"

    def add_role(self, role_name, **permissions):
        """Add a role with an incremented ID and permissions to the role_data list."""
        # Determine the next available ID
        if self.role_data:
            # Extract current IDs and find the maximum
            max_id = max(role.get('id', 0) for role in self.role_data if 'id' in role)
            next_id = max_id + 1
        else:
            # Start IDs from 1 if there are no existing roles
            next_id = 1

        role_info = {
            'id': next_id,  # Assign the next available ID
            'role_name': role_name,  # Store the role name
            **permissions  # Include all provided permissions
        }
        
        # Append the new role information to the role_data list
        self.role_data.append(role_info)

    def get_roles(self):
        """Retrieve all roles and their permissions."""
        return self.role_data

    def get_role_permissions(self, role_name):
        """Retrieve permissions for a specific role."""
        for role in self.role_data:
            if role['role_name'] == role_name:
                return role
        return None  # Role not found


class SubCommunityRoleAssignment(models.Model):
    """
    Manages the assignment of custom roles to sub-community members.
    
    Handles role assignments specifically within sub-communities, allowing for
    granular permission management at the sub-community level while maintaining
    integration with the broader community structure.
    
    Business Logic:
    - Prevents conflicting role assignments within sub-communities
    - Supports role inheritance from parent community when applicable
    - Maintains audit trail of sub-community role changes
    - Enables bulk role assignments for sub-community management
    
    Use Cases:
    - Assigning project lead roles in team sub-communities
    - Managing topic moderators in specialized groups
    - Handling temporary role assignments for events
    """
    subcommunity_uid = models.CharField(max_length=255, null=True, blank=True)  # Sub-community identifier
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)  # Admin who made the role assignments
    created_on = models.DateTimeField(default=timezone.now)  # Timestamp of assignment creation
    assigned_to = models.JSONField(default=list)  # JSON array mapping role IDs to user UIDs

    class Meta:
        verbose_name = 'Subcommunity Role Assignment'  # Updated verbose name
        verbose_name_plural = 'Subcommunity Role Assignments'  # Updated plural verbose name
        ordering = ['-created_on']

    def __str__(self):
        return f"SubcommunityRoleAssignment for {self.subcommunity_uid} by {self.created_by.username}"  # Updated string representation

    def assign_role(self, role_id, user_uid_list):
        """
        Assign a role to multiple users.
        Ensure the same user is not assigned to multiple roles within the same subcommunity.
        """
        # Collect all existing user_uids across all role assignments
        all_assigned_users = {user_uid for assignment in self.assigned_to for user_uid in assignment['user_uids']}

        # Check if any user_uid in user_uid_list is already assigned to a different role
        for user_uid in user_uid_list:
            if user_uid in all_assigned_users:
                raise ValueError(f"User with UID '{user_uid}' is already assigned to another role in this subcommunity.")

        # Check if the role_id already exists in the assigned_to list
        for assignment in self.assigned_to:
            if assignment['role_id'] == role_id:
                # Append new user_uids to the existing list if role_id exists
                assignment['user_uids'] = list(set(assignment['user_uids'] + user_uid_list))
                break
        else:
            # Add a new role assignment if role_id does not exist
            new_assignment = {
                'role_id': role_id,
                'user_uids': user_uid_list
            }
            self.assigned_to.append(new_assignment)

        self.save()

    def get_assigned_roles(self):
        """
        Retrieve all role assignments for this subcommunity.
        """
        return self.assigned_to

    def get_users_for_role(self, role_id):
        """
        Retrieve all users assigned to a specific role_id.
        """
        for assignment in self.assigned_to:
            if assignment['role_id'] == role_id:
                return assignment['user_uids']
        return []


class CommunityReactionManager(models.Model):
    """
    Manages community-wide reaction and vibe tracking.
    
    This model aggregates and manages emotional reactions and vibes within
    a community, providing insights into community sentiment and engagement.
    
    Business Logic:
    - Tracks cumulative vibe scores for community sentiment analysis
    - Manages reaction counts and averages for community health metrics
    - Supports multiple reaction types with scoring systems
    - Provides data for community analytics and insights
    
    Use Cases:
    - Monitoring community sentiment and mood
    - Analyzing engagement patterns and reactions
    - Providing feedback to community managers
    """
    community_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)  # Community identifier
    community_vibe = models.JSONField(default=list)  # JSON array storing reaction data and vibe scores

    class Meta:
        verbose_name = 'Community Reaction Manager'
        verbose_name_plural = 'Community Reaction Managers'

    def __str__(self):
        return f"CommunityReactionManager for community {self.community_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = CommunityVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the IndividualVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.community_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_id exists
        for reaction in self.community_vibe:
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

    def get_reactions(self):
        """Retrieve all reactions with their vibe details."""
        return self.community_vibe

class GeneratedCommunityUserManager(models.Model):
    """
    Manages users for automatically generated communities.
    
    This model handles user management for communities that are created through
    automated processes, such as AI-generated communities or system-created groups
    based on user interests and behaviors.
    
    Business Logic:
    - Tracks users added to generated communities
    - Prevents duplicate user additions
    - Supports bulk user management for automated community creation
    - Maintains audit trail of generated community membership
    
    Use Cases:
    - Managing AI-generated community memberships
    - Tracking users in algorithm-created interest groups
    - Handling automated community population
    """
    community_uid = models.CharField(max_length=255, unique=True)  # Unique identifier for the generated community
    community_name = models.CharField(max_length=255)  # Name of the generated community
    created_on = models.DateTimeField(default=timezone.now)  # Timestamp of community creation
    user_ids = models.JSONField(default=list)  # JSON array storing user IDs for the community

    class Meta:
        verbose_name = 'Generated Community User Manager'
        verbose_name_plural = 'Generated Community User Managers'
        ordering = ['-created_on']

    def __str__(self):
        return f"Community: {self.community_name} - UID: {self.community_uid}"

    def add_user_to_community(self, user_id):
        """Add a user to the community if they are not already in the user_ids list."""
        if user_id not in self.user_ids:
            self.user_ids.append(user_id)
            self.save()
        else:
            return False
        

class CommunityPost(DjangoNode, StructuredNode):
    """
    Represents posts created within communities and sub-communities.
    
    This model handles all types of content posts within the community ecosystem,
    supporting various media types, privacy settings, and engagement tracking.
    
    Business Logic:
    - Supports multiple content types (text, images, files)
    - Tracks engagement metrics (likes, comments, shares)
    - Manages privacy settings for post visibility
    - Calculates and stores vibe scores for content quality
    
    Use Cases:
    - Creating text posts for community discussions
    - Sharing media content within communities
    - Managing post visibility and privacy
    - Tracking community engagement and content quality
    """
    uid = UniqueIdProperty()  # Unique identifier for the post
    PRIVACY_CHOICES = {
        'public': 'Public',    # Visible to all community members
        'private': 'Private'   # Restricted visibility
    }
    post_title = StringProperty()  # Title of the post
    post_text = StringProperty()  # Main text content of the post
    post_type = StringProperty(required=True)  # Type classification of the post
    post_file_id = ArrayProperty(base_property=StringProperty())  # Array of attached file identifiers
    privacy = StringProperty(default='public', choices=PRIVACY_CHOICES.items())  # Privacy setting for post visibility
    vibe_score = FloatProperty(default=2.0)  # Calculated vibe score for post quality
    created_at = DateTimeProperty(default_now=True)  # Timestamp of post creation
    updated_at = DateTimeProperty(default_now=True)  # Timestamp of last update
    is_deleted = BooleanProperty(default=False)  # Soft deletion flag
    tags = ArrayProperty(base_property=StringProperty())  # Array of tags for post categorization
    # Relationship Properties - Community/Sub-community Context
    created_by = RelationshipTo('Community', 'HAS_COMMUNITY')  # Community where post was created
    created_by_subcommunity = RelationshipTo('SubCommunity', 'HAS_SUBCOMMUNITY')  # Sub-community context if applicable

    # Relationship Properties - User Context
    creator = RelationshipTo('Users', 'HAS_CREATOR')  # User who created the post
    updated_by = RelationshipTo('Users', 'HAS_UPDATED_USER')  # User who last updated the post
    
    # Engagement Metrics
    comment_count = IntegerProperty(default=0)  # Total number of comments on the post
    vibes_count = IntegerProperty(default=0)  # Total number of vibe reactions
    share_count = IntegerProperty(default=0)  # Total number of times post was shared
    
    # Relationship Properties - Engagement
    comment = RelationshipTo('Comment', 'HAS_COMMENT')  # Comments associated with the post
    like = RelationshipTo('Like', 'HAS_LIKE')  # Likes/reactions associated with the post

    def save(self, *args, **kwargs):
        """
        Custom save method to update the timestamp on every save.
        
        Automatically updates the updated_at field whenever the post is modified,
        ensuring accurate tracking of post modification history.
        """
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'community'  # Django app label for model organization
        
    def __str__(self):
        """
        String representation of the post.
        
        Returns:
            str: The post title for easy identification
        """
        return self.post_title