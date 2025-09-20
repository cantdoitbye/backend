# auth_manager/models.py
from neomodel import StructuredNode , StringProperty,IntegerProperty, FloatProperty, DateTimeProperty, BooleanProperty, UniqueIdProperty, OneOrMore, RelationshipTo,RelationshipFrom,ArrayProperty,ZeroOrMore
from django_neomodel import DjangoNode
from datetime import datetime
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .enums.otp_purpose_enum import OtpPurposeEnum
from django.db import models
# from vibe_manager.models import IndividualVibe  # Removed to prevent circular import
import uuid
import hashlib
from django.apps import apps


class Users(DjangoNode, StructuredNode):
    """
    Core user model representing the main user entity in the system.
    
    This model serves as the central hub for all user-related data and relationships,
    connecting users to their profiles, content, connections, and activities across
    the entire platform. It acts as the primary authentication and identity model.
    
    Business Logic:
    - Each user has a unique identifier (uid) and user_id for cross-system references
    - Username serves as the primary display identifier
    - Email is used for authentication and communication
    - User type distinguishes between personal and business accounts
    - is_active flag controls account status and access permissions
    
    Use Cases:
    - User authentication and session management
    - Profile and content ownership tracking
    - Social connections and networking
    - Cross-platform user identification
    - Account status and permission management
    """
    uid = UniqueIdProperty()  # Unique system-wide identifier
    user_id = StringProperty(unique_index=True, required=True)  # External reference ID
    username = StringProperty(unique_index=True)  # Display name and login identifier
    password = StringProperty(required=False)  # Encrypted password (optional for OAuth users)
    email = StringProperty(unique_index=True)  # Primary email for authentication
    first_name = StringProperty()  # User's first name
    last_name = StringProperty()  # User's last name
    user_type = StringProperty(default="personal")  # Account type: personal/business
    created_at = DateTimeProperty(default_now=True)  # Account creation timestamp
    created_by = StringProperty()  # Creator reference for admin accounts
    updated_at = DateTimeProperty(default_now=True)  # Last modification timestamp
    updated_by = StringProperty()  # Last modifier reference
    is_active = BooleanProperty(default=False)  # Account activation status
    
    profile = RelationshipTo('Profile', 'HAS_PROFILE')  # Define the relationship 
    story=RelationshipTo('story.models.Story','HAS_STORY')
    post=RelationshipTo('post.models.Post','HAS_POST')
    connection=RelationshipTo('connection.models.Connection','HAS_CONNECTION')
    connectionv2=RelationshipTo('connection.models.ConnectionV2','HAS_CONNECTION')
    community=RelationshipTo('community.models.Community','HAS_COMMUNITY')
    conversation=RelationshipTo('msg.models.Conversation','HAS_CONVERSATION')
    service=RelationshipTo('service.models.Service','HAS_SERVICE')
    meetings=RelationshipTo('dairy.models.Meeting','HAS_MEETING')
    todo=RelationshipTo('dairy.models.ToDo','HAS_TODO')
    note=RelationshipTo('dairy.models.Note','HAS_NOTE')
    reminder=RelationshipTo('dairy.models.Reminder','HAS_REMINDER')
    product=RelationshipTo('shop.models.Product','HAS_PRODUCT')
    user_review=RelationshipTo('UsersReview','HAS_USER_REVIEW')
    vibe=RelationshipTo('vibe_manager.models.Vibe','HAS_VIBES')
    userviberepo=RelationshipTo('UserVibeRepo','HAS_REPO')
    connection_stat=RelationshipTo('ConnectionStats','HAS_CONNECTION_STAT')
    company=RelationshipTo('job.models.Company','HAS_COMPANY')
    job=RelationshipTo('job.models.Job','HAS_JOB')
    blocked=RelationshipTo('msg.models.Block','HAS_BLOCK')
    user_back_profile_review=RelationshipTo('BackProfileUsersReview','HAS_USER_REVIEW')

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'auth_manager'
        
        
    
    def __str__(self):
        return self.username


class Profile(DjangoNode, StructuredNode):
    """
    Comprehensive user profile model containing detailed personal information and relationships.
    
    This model serves as the central hub for all user profile data, including personal details,
    contact information, location data, and relationships to various profile components like
    education, skills, achievements, and experiences. It acts as the primary data source for
    profile display, user discovery, and social networking features.
    
    Business Logic:
    - Each profile is uniquely linked to a Users instance via user_id
    - Contains both basic personal info and extended profile data
    - Manages relationships to modular profile components (education, skills, etc.)
    - Supports profile customization through images and biographical information
    - Tracks onboarding progress and completion status
    
    Use Cases:
    - User profile display and customization
    - Social networking and user discovery
    - Profile completion tracking
    - Contact information management
    - Location-based features and filtering
    - Professional networking (designation, workplace)
    """
    uid = UniqueIdProperty()  # Unique profile identifier
    user_id = StringProperty(unique_index=True, required=True)  # Reference to Users model
    gender = StringProperty()  # User's gender identity
    device_id = StringProperty()  # Device identifier for push notifications
    fcm_token = StringProperty()  # Firebase Cloud Messaging token
    bio = StringProperty()  # User's biography or description
    designation = StringProperty()  # Job title or professional designation
    worksat = StringProperty()  # Current workplace or company
    phone_number = StringProperty()  # Contact phone number
    born = DateTimeProperty()  # Birth timestamp (legacy field)
    dob = DateTimeProperty()  # Date of birth
    school = StringProperty()  # School information
    college = StringProperty()  # College/university information
    lives_in = StringProperty()  # Current residence location
    state = StringProperty()  # State/province of residence
    city = StringProperty()  # City of residence
    profile_pic_id = StringProperty()  # Profile picture file identifier
    cover_image_id = StringProperty()  # Cover image file identifier
    
    # Core relationships
    user = RelationshipTo('Users', 'HAS_USER')  # Link to main user account
    onboarding = RelationshipTo('OnboardingStatus', 'HAS_ONBOARDING_STATUS')  # Onboarding progress
    contactinfo = RelationshipTo('ContactInfo', 'HAS_CONTACT_INFO')  # Contact information
    score = RelationshipTo('Score', 'HAS_SCORE')  # User scoring and ratings
    interest = RelationshipTo('Interest', 'HAS_INTEREST')  # User interests and hobbies
    
    # Professional and educational relationships
    achievement = RelationshipTo('Achievement', 'HAS_ACHIEVEMENT')  # User achievements
    education = RelationshipTo('Education', 'HAS_EDUCATION')  # Educational background
    skill = RelationshipTo('Skill', 'HAS_SKILL')  # Skills and competencies
    experience = RelationshipTo('Experience', 'HAS_EXPERIENCE')  # Work experience
    
    
    class Meta:
        app_label = 'auth_manager'


class OnboardingStatus(DjangoNode,StructuredNode):
    """
    Tracks user onboarding progress through a multi-step setup process.
    
    This model manages the user's journey through the initial setup and profile
    completion process, ensuring users complete all necessary steps to fully
    activate their account and access all platform features.
    
    Business Logic:
    - Each step represents a specific onboarding milestone
    - Steps must typically be completed in sequence
    - Profile completion tracking enables personalized onboarding experiences
    - Incomplete onboarding may restrict certain features
    
    Use Cases:
    - Onboarding flow management and progress tracking
    - Feature access control based on completion status
    - User experience personalization
    - Onboarding analytics and optimization
    - Support for incomplete profile identification
    """
    uid=UniqueIdProperty()  # Unique onboarding status identifier
    email_verified = BooleanProperty(default=False)  # Email verification status
    phone_verified = BooleanProperty(default=False)  # Phone verification status
    username_selected = BooleanProperty(default=False)  # Username selection completion
    first_name_set = BooleanProperty(default=False)  # First name completion
    last_name_set = BooleanProperty(default=False)  # Last name completion
    gender_set = BooleanProperty(default=False)  # Gender selection completion
    bio_set = BooleanProperty(default=False)  # Biography completion
    state = BooleanProperty(default=False)  # State/province selection completion
    city = BooleanProperty(default=False)  # City selection completion
    profile = RelationshipTo('Profile', 'HAS_PROFILE')  # Link to user profile

    class Meta:
        app_label = 'auth_manager'


class ContactInfo(DjangoNode,StructuredNode):
    """
    Manages comprehensive contact information for users.
    
    This model stores detailed contact and platform information, supporting
    communication, social media linking, and user verification processes.
    It provides a flexible structure for various contact methods and platforms.
    
    Business Logic:
    - Stores multiple contact methods with type classification
    - Supports platform-specific contact information (social media, etc.)
    - Used for user verification and communication
    - Enables contact method validation and management
    - Maintains contact history and soft deletion
    
    Use Cases:
    - User communication and notifications
    - Social media profile linking
    - Contact method verification and validation
    - Multi-platform user discovery
    - Contact information backup and recovery
    """
    uid=UniqueIdProperty()  # Unique contact info identifier
    type = StringProperty(required=True)  # Contact type (email, phone, social, etc.)
    value = StringProperty(required=True)  # Contact value (email address, phone number, etc.)
    platform = StringProperty()  # Platform name (Instagram, LinkedIn, etc.)
    link = StringProperty()  # Direct link to profile or contact method
    profile = RelationshipTo('Profile', 'HAS_PROFILE')  # Link to user profile
    is_deleted = BooleanProperty(default=False)  # Soft deletion flag

    class Meta:
        app_label = 'auth_manager'


class Score(DjangoNode,StructuredNode):
    """
    Manages user scoring and rating systems across different categories.
    
    This model tracks various types of scores and ratings for users, supporting
    gamification, reputation systems, and performance metrics. It provides a
    flexible framework for different scoring mechanisms and achievements.
    
    Business Logic:
    - Supports multiple score types (reputation, skill level, activity, etc.)
    - Maintains score values with optional maximum limits
    - Enables score-based user ranking and comparison
    - Supports score history and progression tracking
    - Used for gamification and user engagement features
    
    Use Cases:
    - User reputation and credibility systems
    - Skill level assessment and tracking
    - Gamification and achievement systems
    - User ranking and leaderboards
    - Performance metrics and analytics
    """
    uid = UniqueIdProperty()  # Unique score identifier
    vibers_count = FloatProperty(default=2.0)  # Number of users who gave vibes
    cumulative_vibescore = FloatProperty(default=2.0)  # Total accumulated vibe score
    intelligence_score = FloatProperty(default=2.0)  # Intelligence rating score
    appeal_score = FloatProperty(default=2.0)  # Appeal/attractiveness rating
    social_score = FloatProperty(default=2.0)  # Social interaction score
    human_score = FloatProperty(default=2.0)  # Human connection score
    repo_score = FloatProperty(default=2.0)  # Repository/content score
    overall_score = FloatProperty(default=0.0) # user's overall score
    profile = RelationshipTo('Profile', 'HAS_SCORE')  # Link to user profile


    class Meta:
        app_label = 'auth_manager'


class Interest(DjangoNode,StructuredNode):
    """
    Manages user interests and hobbies for personalization and matching.
    
    This model stores user interests across various categories, enabling
    personalized content delivery, user matching, and community building
    based on shared interests and preferences.
    
    Business Logic:
    - Categorizes interests for better organization and filtering
    - Supports interest-based user discovery and matching
    - Enables personalized content recommendations
    - Used for community and group suggestions
    - Maintains interest history and preferences
    
    Use Cases:
    - Personalized content and feed curation
    - User matching and connection suggestions
    - Interest-based community recommendations
    - Targeted content and advertising
    - Social networking and discovery features
    """
    uid=UniqueIdProperty()  # Unique interest identifier
    names = ArrayProperty(base_property=StringProperty(), required=True)  # List of interest names
    profile = RelationshipTo('Profile', 'HAS_PROFILE')  # Link to user profile
    is_deleted = BooleanProperty(default=False)  # Soft deletion flag



class OTP(models.Model):
    """
    Manages One-Time Password (OTP) verification for user authentication.
    
    This model handles secure OTP generation, validation, and expiration for
    various verification processes including email and phone number verification,
    password resets, and two-factor authentication.
    
    Business Logic:
    - Generates time-limited OTP codes for security verification
    - Supports multiple OTP types (email, phone, 2FA)
    - Implements automatic expiration to prevent replay attacks
    - Tracks verification status and usage history
    - Integrates with Django's User model for authentication
    
    Use Cases:
    - Email and phone number verification
    - Password reset and account recovery
    - Two-factor authentication (2FA)
    - Secure transaction verification
    - Account security and fraud prevention
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)  # User requesting OTP
    otp = models.CharField(max_length=6)  # Generated OTP code
    purpose = models.CharField(max_length=255, choices=[(tag.value, tag.name) for tag in OtpPurposeEnum],default=OtpPurposeEnum.EMAIL_VERIFICATION)  # OTP purpose/type
    created_at = models.DateTimeField(auto_now_add=True)  # OTP generation timestamp
    expires_at = models.DateTimeField()  # OTP expiration timestamp

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)  # OTP valid for 10 minutes
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP {self.otp} for {self.user}"
    

class UsersReview(DjangoNode,StructuredNode):
    """
    Manages user-to-user reviews and ratings system.
    
    This model enables users to review and rate each other, supporting
    reputation building, trust establishment, and quality assessment
    within the platform's social and professional networking features.
    
    Business Logic:
    - Enables bidirectional user reviews and ratings
    - Supports both numerical ratings (vibe scores) and textual feedback
    - Maintains review history and modification tracking
    - Implements soft deletion for review management
    - Used for reputation and trust score calculations
    
    Use Cases:
    - User reputation and credibility assessment
    - Professional networking and endorsements
    - Service provider rating and feedback
    - Community trust and safety features
    - Quality control and user experience improvement
    """
    uid=UniqueIdProperty()  # Unique review identifier
    byuser = RelationshipTo('Users','REVIEW_BY_USER' )  # User giving the review
    touser = RelationshipTo('Users','REVIEW_TO_USER' )  # User being reviewed
    reaction = StringProperty()  # Review reaction/sentiment
    vibe = FloatProperty(default=2.0)  # Numerical rating score
    title = StringProperty()  # Review title/summary
    content =StringProperty()  # Detailed review content
    file_id = StringProperty()  # Attached file identifier
    is_deleted = BooleanProperty(default=False)  # Soft deletion flag
    timestamp=DateTimeProperty(default_now=True)  # Review creation timestamp
    
    class Meta:
        app_label = 'auth_manager'

    def __str__(self):
        return self.reaction
    

class UserVibeRepo(DjangoNode,StructuredNode):
    """
    Tracks user-to-user vibe interactions and ratings.
    
    This model manages the vibe system where users can rate each other
    across different dimensions, contributing to overall user scores and
    reputation within the platform's social networking features.
    
    Business Logic:
    - Records vibe interactions between users
    - Maintains vibe scores for reputation calculation
    - Supports bidirectional user rating system
    - Tracks interaction history and timestamps
    - Used for user matching and recommendation algorithms
    
    Use Cases:
    - User reputation and scoring systems
    - Social interaction tracking
    - User matching and compatibility assessment
    - Community engagement metrics
    - Trust and credibility establishment
    """
    uid=UniqueIdProperty()  # Unique vibe interaction identifier
    user = RelationshipTo('Users','VIBE_REPO' )  # User associated with this vibe repository
    category = StringProperty()  # Vibe category or type
    custom_value = FloatProperty()  # Custom vibe score value
    created_at = DateTimeProperty(default_now=True)  # Vibe creation timestamp
    
    class Meta:
        app_label = 'auth_manager'

    def __str__(self):
        return ""
    
class ConnectionStats(DjangoNode, StructuredNode):
    """
    Tracks comprehensive user connection and networking statistics.
    
    This model maintains real-time statistics about user connections,
    follow relationships, and networking activity, providing insights
    into user engagement and social network growth.
    
    Business Logic:
    - Aggregates various connection metrics in real-time
    - Tracks both incoming and outgoing connection requests
    - Maintains follower/following counts for social features
    - Monitors blocked users for safety and moderation
    - Updates automatically based on user interactions
    
    Use Cases:
    - User profile statistics display
    - Social networking analytics
    - User engagement measurement
    - Network growth tracking
    - Social influence assessment
    """
    uid=UniqueIdProperty()  # Unique connection stats identifier
    received_connections_count = IntegerProperty(default=0)  # Number of received connection requests
    accepted_connections_count = IntegerProperty(default=0)  # Number of accepted connections
    rejected_connections_count = IntegerProperty(default=0)  # Number of rejected connection requests
    sent_connections_count = IntegerProperty(default=0)  # Number of sent connection requests
    inner_circle_count=IntegerProperty(default=0)  # Number of inner circle connections
    outer_circle_count=IntegerProperty(default=0)  # Number of outer circle connections
    universal_circle_count=IntegerProperty(default=0)  # Number of universal circle connections

    class Meta:
        app_label = 'connection'


class WelcomeScreenMessage(models.Model):
    """
    Manages welcome screen messages for user onboarding and engagement.
    
    This model stores customizable welcome messages that are displayed to users
    during onboarding, app launches, or special events, enabling personalized
    user experiences and important announcements.
    
    Business Logic:
    - Supports multiple welcome messages with activation control
    - Enables dynamic message rotation and A/B testing
    - Maintains message history and modification tracking
    - Used for user engagement and onboarding optimization
    - Supports seasonal or event-based messaging
    
    Use Cases:
    - User onboarding and welcome experiences
    - Important announcements and notifications
    - Seasonal greetings and special events
    - A/B testing for user engagement
    - Personalized user experience enhancement
    """
    BRAND = 'brand'
    PERSONAL = 'personal'

    CONTENT_TYPE_CHOICES = [
        (BRAND, 'Brand'),
        (PERSONAL, 'Personal Account'),
    ]

    title = models.CharField(max_length=255)  # Welcome message title
    content = models.TextField()  # Welcome message content
    image = models.FileField(upload_to='welcomescreenimages/', blank=True, null=True)  # Optional welcome image
    rank = models.PositiveIntegerField(null=True, blank=True)  # Display order ranking
    timestamp = models.DateTimeField(default=timezone.now, editable=False)  # Message creation timestamp
    is_visible = models.BooleanField(default=False)  # Message visibility status
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES, default=PERSONAL)  # Message target type

    class Meta:
        ordering = ['rank', '-timestamp']
        verbose_name = 'Welcome Screen Message'
        verbose_name_plural = 'Welcome Screen Messages'

    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"

    def save(self, *args, **kwargs):
        if not self.rank:
            self.rank = WelcomeScreenMessage.objects.count() + 1
        super().save(*args, **kwargs)


class UploadContact(models.Model):
    """
    Manages user-uploaded contact information for network building and invitations.
    
    This model stores contacts uploaded by users from their address books,
    enabling friend discovery, invitation systems, and network expansion
    features within the platform.
    
    Business Logic:
    - Stores contact information uploaded from user devices
    - Tracks registration status of uploaded contacts
    - Links registered contacts to existing user accounts
    - Supports invitation and referral systems
    - Maintains privacy and data protection compliance
    
    Use Cases:
    - Friend discovery and network building
    - User invitation and referral systems
    - Contact synchronization and management
    - Network expansion recommendations
    - Social graph construction and analysis
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User who uploaded contacts
    contact = models.JSONField() # JSON array field to store contact information
    created_on = models.DateTimeField(default=timezone.now)  # Contact upload timestamp
    is_deleted = models.BooleanField(default=False)  # Soft deletion flag

    class Meta:
        verbose_name = 'Upload Contact'
        verbose_name_plural = 'Upload Contact'
        ordering = ['-created_on']

    def __str__(self):
        return f"UploadContact for {self.user.username} with contacts {self.contact}"

    def save(self, *args, **kwargs):
        if not self.created_on:
            self.created_on = timezone.now()
        super().save(*args, **kwargs)

    
class ProfileReactionManager(models.Model):
    """
    Manages and aggregates user profile reaction statistics and vibe interactions.
    
    This model tracks various types of reactions and engagement metrics
    for user profiles, providing insights into profile popularity,
    engagement levels, and social interaction patterns through the vibe system.
    
    Business Logic:
    - Aggregates reaction counts across different vibe types
    - Updates in real-time as users interact with profiles
    - Supports multiple reaction types with cumulative scoring
    - Used for profile ranking and recommendation algorithms
    - Maintains historical engagement data and vibe statistics
    
    Use Cases:
    - Profile engagement analytics and insights
    - User popularity and influence measurement
    - Content recommendation algorithms
    - Social interaction tracking
    - Profile performance optimization
    """
    profile_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)  # Unique profile identifier
    profile_vibe = models.JSONField(default=list)  # List to hold multiple vibe reactions and scores

    class Meta:
        verbose_name = 'Profile Reaction Manager'
        verbose_name_plural = 'Profile Reaction Managers'

    def __str__(self):
        return f"ProfileReactionManager for profile {self.profile_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        IndividualVibe = apps.get_model('vibe_manager', 'IndividualVibe')
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the ProfileVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.profile_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.profile_vibe:
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
        return self.profile_vibe

class InterestList(models.Model):
    """
    Manages the master list of available interests with sub-categories for user selection.
    
    This model maintains a curated list of interests that users can select
    from during profile setup and customization, ensuring consistency
    and enabling effective interest-based matching and recommendations.
    
    Business Logic:
    - Provides a standardized list of selectable interests
    - Supports hierarchical interest structure with sub-interests
    - Used as reference data for user interest selection
    - Enables interest-based user matching and content curation
    - Maintains interest taxonomy for better organization
    
    Use Cases:
    - User profile setup and interest selection
    - Interest-based user matching and recommendations
    - Content categorization and filtering
    - Interest analytics and trending topics
    - Platform content strategy and curation
    """
    name = models.CharField(max_length=255, unique=True)  # Primary interest name
    sub_interests = models.JSONField(default=list)  # List of sub-interests under this category

    def __str__(self):
        """Return the interest name for string representation."""
        return self.name
    

class BackProfileUsersReview(DjangoNode,StructuredNode):
    """
    Backup model for user-to-user reviews and ratings system using Neo4j.
    
    This model serves as a backup or alternative implementation for the
    user review system, maintaining review data with Neo4j graph database
    while supporting rich relationship-based queries and analysis.
    
    Business Logic:
    - Enables bidirectional user reviews and ratings
    - Supports both numerical ratings (vibe scores) and textual feedback
    - Maintains review history and modification tracking
    - Implements soft deletion for review management
    - Used for reputation and trust score calculations
    
    Use Cases:
    - User reputation and credibility assessment
    - Professional networking and endorsements
    - Service provider rating and feedback
    - Community trust and safety features
    - Graph-based review analysis and insights
    """
    uid=UniqueIdProperty()  # Unique review identifier
    byuser = RelationshipTo('Users','REVIEW_BY_USER' )  # User giving the review
    touser = RelationshipTo('Users','REVIEW_TO_USER' )  # User being reviewed
    reaction = StringProperty()  # Review reaction/sentiment
    vibe = FloatProperty(default=2.0)  # Numerical vibe rating score
    title = StringProperty()  # Review title/summary
    content =StringProperty()  # Detailed review content
    # file_id = StringProperty()  # Attached file identifier
    image_ids = ArrayProperty(base_property=StringProperty())  # Multiple attached image identifiers
    rating = IntegerProperty(default=4)  # Star rating (1-5 stars)
    is_deleted = BooleanProperty(default=False)  # Soft deletion flag
    timestamp=DateTimeProperty(default_now=True)  # Review creation timestamp
    
    class Meta:
        app_label = 'auth_manager'

    def __str__(self):
        return self.reaction
    


class BackProfileReactionManager(models.Model):
    profile_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_vibe = models.JSONField(default=list)  # List to hold multiple reactions

    class Meta:
        verbose_name = 'Profile Reaction Manager'
        verbose_name_plural = 'Profile Reaction Managers'

    def __str__(self):
        return f"ProfileReactionManager for profile {self.profile_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the ProfileVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.profile_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.profile_vibe:
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
        return self.profile_vibe
    

class Country(models.Model):
    """
    Manages country information with associated states for location services.
    
    This model stores country data with their respective states, supporting
    location-based features, user registration, and geographic filtering
    across the platform. Note: Currently not actively used in the project.
    
    Business Logic:
    - Maintains hierarchical location data (country -> states)
    - Supports dynamic state management and updates
    - Used for location validation and selection
    - Enables geographic user filtering and discovery
    - Provides location reference data for forms and APIs
    
    Use Cases:
    - User registration and profile location setup
    - Location-based user discovery and filtering
    - Geographic content and service targeting
    - Address validation and standardization
    - Location analytics and demographics
    """
    country = models.CharField(max_length=255, unique=True)  # Country name
    states = models.JSONField(default=list)  # List of states/provinces in this country

    class Meta:
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'

    def __str__(self):
        return f"Country: {self.country}"

    def update_state_name(self, old_state_name, new_state_name):
        """
        Rename a state inside the `states` JSON field and update it in the State model.
        """
        updated = False
        for state in self.states:
            if state == old_state_name:
                state_index = self.states.index(old_state_name)
                self.states[state_index] = new_state_name
                updated = True
                break

        if updated:
            self.save()

            # Rename the state in the State table
            try:
                state_obj = State.objects.get(state=old_state_name)
                state_obj.state = new_state_name
                state_obj.save()
            except State.DoesNotExist:
                return f"Warning: State '{old_state_name}' not found in State table."

            return f"State '{old_state_name}' renamed to '{new_state_name}' in both Country and State tables."

        return f"Error: State '{old_state_name}' not found in Country."

class State(models.Model):
    """
    Manages state/province information with associated cities for location services.
    
    This model stores state data with their respective cities, supporting
    hierarchical location management and geographic filtering features.
    Note: Currently not actively used in the project.
    
    Business Logic:
    - Maintains hierarchical location data (state -> cities)
    - Supports dynamic city management and updates
    - Used for location validation and selection
    - Enables geographic user filtering and discovery
    - Provides location reference data for forms and APIs
    
    Use Cases:
    - User registration and profile location setup
    - Location-based user discovery and filtering
    - Geographic content and service targeting
    - Address validation and standardization
    - Regional analytics and demographics
    """
    state = models.CharField(max_length=255, unique=True)  # State/province name
    cities = models.JSONField(default=list)  # List of cities in this state

    class Meta:
        verbose_name = 'State'
        verbose_name_plural = 'States'

    def __str__(self):
        """Return formatted state name for string representation."""
        return f"State: {self.state}"
    

class CountryInfo(models.Model):
    """
    Stores country information for location-based features and user registration.
    
    This model provides a normalized approach to country data management,
    supporting location-based features, user registration, and geographic
    filtering across the platform with proper relational structure.
    
    Business Logic:
    - Maintains standardized country information
    - Supports relational location hierarchy (country -> states -> cities)
    - Used for location validation and selection
    - Enables geographic user filtering and discovery
    - Provides location reference data for forms and APIs
    
    Use Cases:
    - User registration and profile location setup
    - Location-based user discovery and filtering
    - Geographic content and service targeting
    - Address validation and standardization
    - International user management and analytics
    """
    id = models.AutoField(primary_key=True)  # Primary key
    country_name = models.CharField(max_length=255, unique=True)  # Country name

    class Meta:
        verbose_name = "Country Information"
        verbose_name_plural = "Countries Information"

    def __str__(self):
        """Return country name for string representation."""
        return self.country_name


class StateInfo(models.Model):
    """
    Stores state/province information with country relationships for location services.
    
    This model provides normalized state data management with proper foreign key
    relationships to countries, supporting hierarchical location features and
    geographic filtering across the platform.
    
    Business Logic:
    - Maintains state information linked to specific countries
    - Supports relational location hierarchy (country -> states -> cities)
    - Used for location validation and selection
    - Enables geographic user filtering and discovery
    - Provides location reference data for forms and APIs
    
    Use Cases:
    - User registration and profile location setup
    - Location-based user discovery and filtering
    - Geographic content and service targeting
    - Address validation and standardization
    - Regional analytics and demographics
    """
    id = models.AutoField(primary_key=True)  # Primary key
    state_name = models.CharField(max_length=255, unique=True)  # State/province name
    country = models.ForeignKey(CountryInfo, on_delete=models.CASCADE, related_name="states")  # Parent country

    class Meta:
        verbose_name = "State Information"
        verbose_name_plural = "States Information"

    def __str__(self):
        """Return state name for string representation."""
        return self.state_name


class CityInfo(models.Model):
    """
    Stores city information with state relationships for location services.
    
    This model provides normalized city data management with proper foreign key
    relationships to states, completing the hierarchical location structure
    and supporting detailed geographic filtering across the platform.
    
    Business Logic:
    - Maintains city information linked to specific states
    - Completes relational location hierarchy (country -> states -> cities)
    - Used for location validation and selection
    - Enables precise geographic user filtering and discovery
    - Provides detailed location reference data for forms and APIs
    
    Use Cases:
    - User registration and profile location setup
    - Precise location-based user discovery and filtering
    - Local content and service targeting
    - Address validation and standardization
    - Local analytics and demographics
    """
    id = models.AutoField(primary_key=True)  # Primary key
    city_name = models.CharField(max_length=255)  # City name
    state = models.ForeignKey(StateInfo, on_delete=models.CASCADE, related_name="cities")  # Parent state

    class Meta:
        verbose_name = "City Information"
        verbose_name_plural = "Cities Information"

    def __str__(self):
        """Return city name for string representation."""
        return self.city_name


# These Models are used in V2 version of api


def generate_hashed_uuid():
    """Generate a secure hashed UUID."""
    raw_uuid = str(uuid.uuid4())  # Generate raw UUID
    return hashlib.sha256(raw_uuid.encode()).hexdigest()  # Hash it


def default_expiry_date():
    """Returns the default expiry date (30 days from now)."""
    return timezone.now() + timedelta(days=30)


class Invite(models.Model):
    """
    Enhanced invitation system for V2 API with token-based security and usage tracking.
    
    This model provides a more sophisticated invitation system with secure token
    generation, origin tracking, expiry management, and comprehensive usage analytics
    for controlled platform growth and user acquisition.
    
    Business Logic:
    - Generates secure hashed tokens for invitation security
    - Tracks invitation origin and context (menu, community, truth section)
    - Manages invitation expiry and lifecycle
    - Monitors usage patterns and user engagement
    - Supports multiple users per invitation token
    - Provides soft deletion for data retention
    
    Use Cases:
    - Secure user invitation and onboarding
    - Origin-based invitation analytics and tracking
    - Controlled platform growth with expiry management
    - Multi-user invitation sharing and tracking
    - Invitation performance and conversion analysis
    """
    class OriginType(models.TextChoices):
        """Defines the source context where invitation was generated."""
        MENU = "menu", "Menu"
        COMMUNITY = "community", "Community"
        TRUTH_SECTION = "truth_section", "Truth Section"

    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_invites")  # User creating invitation
    invite_token = models.CharField(max_length=64, unique=True, editable=False, default=generate_hashed_uuid)  # Secure invitation token
    origin_type = models.CharField(max_length=20, choices=OriginType.choices)  # Invitation source context
    creation_date = models.DateTimeField(default=timezone.now)  # Invitation creation timestamp
    expiry_date = models.DateTimeField(default=default_expiry_date)  # Invitation expiry timestamp
    usage_count = models.PositiveIntegerField(default=0)  # Number of times invitation used
    last_used_timestamp = models.DateTimeField(null=True, blank=True)  # Last usage timestamp
    login_users = models.ManyToManyField(User, related_name="used_invites", blank=True)  # Users who used this invitation
    is_deleted = models.BooleanField(default=False)  # Soft deletion flag

    class Meta:
        verbose_name = "Invite"
        verbose_name_plural = "Invites"
        ordering = ["-creation_date"]

    def __str__(self):
        return f"Invite {self.invite_token[:8]}... by {self.inviter.username}"  # Shortened token for readability

    def save(self, *args, **kwargs):
        """Ensure default values before saving."""
        if not self.expiry_date:
            self.expiry_date = default_expiry_date()
        super().save(*args, **kwargs)

class ProfileDataReactionManager(models.Model):
    """
    Centralized reaction management system for all profile data categories.
    
    This model consolidates reaction management across education, achievements,
    skills, and experience data, providing unified vibe tracking and engagement
    analytics. Note: Currently marked as complex and not actively used.
    
    Business Logic:
    - Centralizes reaction management for all profile data types
    - Tracks vibes and engagement across multiple categories
    - Supports dynamic reaction initialization and updates
    - Provides unified analytics for profile engagement
    - Manages cumulative scoring and reaction patterns
    
    Use Cases:
    - Unified profile engagement tracking and analytics
    - Cross-category reaction pattern analysis
    - Simplified reaction management and reporting
    - Profile data engagement insights and recommendations
    - Consolidated vibe scoring and user interaction metrics
    """
    profile_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)  # Profile identifier

    education_vibe = models.JSONField(default=list)  # Education-related reactions
    achievement_vibe = models.JSONField(default=list)  # Achievement-related reactions
    skill_vibe = models.JSONField(default=list)  # Skill-related reactions
    experience_vibe = models.JSONField(default=list)  # Experience-related reactions

    class Meta:
        verbose_name = 'Profile Data Reaction Manager'
        verbose_name_plural = 'Profile Data Reaction Managers'

    def __str__(self):
        return f"ProfileDataReactionManager for profile {self.profile_uid}"

    def initialize_reactions(self, category):
        """
        Initialize the first 10 vibes for the specified category with `vibes_count=0` and `cumulative_vibe_score=0`.
        """
        category_map = {
            "education": "education_vibe",
            "achievement": "achievement_vibe",
            "skill": "skill_vibe",
            "experience": "experience_vibe"  # Added experience category
        }

        if category not in category_map:
            raise ValueError("Invalid category. Choose from 'education', 'achievement', 'skill', or 'experience'.")

        first_10_vibes = IndividualVibe.objects.all()[:10]  

        setattr(self, category_map[category], [
            {
                'id': vibe.id,
                'vibes_id': vibe.id,
                'vibes_name': vibe.name_of_vibe,
                'vibes_count': 0,
                'cumulative_vibe_score': 0
            } for vibe in first_10_vibes
        ])
        self.save()  

    def add_reaction(self, category, vibes_name, score):
        """
        Add or update a reaction for a specific category (education, achievement, skill, experience).
        """
        category_map = {
            "education": self.education_vibe,
            "achievement": self.achievement_vibe,
            "skill": self.skill_vibe,
            "experience": self.experience_vibe  # Added experience category
        }

        if category not in category_map:
            raise ValueError("Invalid category. Choose from 'education', 'achievement', 'skill', or 'experience'.")

        vibe_list = category_map[category]

        for reaction in vibe_list:
            if reaction['vibes_name'] == vibes_name:
                reaction['vibes_count'] += 1
                total_score = reaction['cumulative_vibe_score'] * (reaction['vibes_count'] - 1) + score
                reaction['cumulative_vibe_score'] = total_score / reaction['vibes_count']
                break
        else:
            raise ValueError(f"No initialized reaction for vibes_name {vibes_name} found in {category}.")

        setattr(self, category + "_vibe", vibe_list)
        self.save()

    def get_reactions(self, category):
        """
        Retrieve all reactions for a specific category (education, achievement, skill, experience).
        """
        category_map = {
            "education": self.education_vibe,
            "achievement": self.achievement_vibe,
            "skill": self.skill_vibe,
            "experience": self.experience_vibe  # Added experience category
        }

        if category not in category_map:
            raise ValueError("Invalid category. Choose from 'education', 'achievement', 'skill', or 'experience'.")

        return category_map[category]


class Achievement(DjangoNode,StructuredNode):
    """
    Neo4j-based model for storing user achievements and accomplishments.
    
    This model represents user achievements using Neo4j graph database,
    supporting rich relationship mapping, engagement tracking, and
    comprehensive achievement management with file attachments.
    
    Business Logic:
    - Stores achievement data in Neo4j graph structure
    - Supports relationships to profiles, reactions, and comments
    - Tracks achievement timeline with from/to dates
    - Manages file attachments and media content
    - Provides engagement analytics through likes and comments
    - Supports soft deletion for data retention
    
    Use Cases:
    - User achievement and accomplishment tracking
    - Professional portfolio and credential management
    - Achievement-based networking and discovery
    - Engagement tracking and social validation
    - Achievement analytics and reporting
    """
    uid = UniqueIdProperty()  # Unique identifier
    profile = RelationshipTo('Profile', 'HAS_PROFILE')  # Associated user profile
    like= RelationshipTo('ProfileDataReaction', 'HAS_LIKE')  # Achievement reactions
    comment= RelationshipTo('ProfileDataComment', 'HAS_COMMENT')  # Achievement comments
    what = StringProperty(required=True)  # Achievement title/name
    description = StringProperty(required=True)  # Achievement description
    from_source = StringProperty(required=True)  # Achievement source/issuer
    created_on = DateTimeProperty(default_now=True)  # Creation timestamp
    from_date=DateTimeProperty()  # Achievement start date
    to_date=DateTimeProperty()  # Achievement end date
    is_deleted = BooleanProperty(default=False)  # Soft deletion flag
    file_id=ArrayProperty(base_property=StringProperty())  # Attached file identifiers
    
    def save(self, *args, **kwargs):
        """Override save to ensure creation timestamp is set."""
        self.created_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'auth_manager'

class Education(DjangoNode,StructuredNode):
    """
    Neo4j-based model for storing user education and academic background.
    
    This model represents user education data using Neo4j graph database,
    supporting rich relationship mapping, engagement tracking, and
    comprehensive academic history management with file attachments.
    
    Business Logic:
    - Stores education data in Neo4j graph structure
    - Supports relationships to profiles, reactions, and comments
    - Tracks education timeline with from/to dates
    - Manages field of study and institution information
    - Provides engagement analytics through likes and comments
    - Supports file attachments for certificates and documents
    - Supports soft deletion for data retention
    
    Use Cases:
    - User academic background and credential tracking
    - Educational networking and alumni connections
    - Academic achievement validation and verification
    - Education-based user discovery and matching
    - Academic analytics and reporting
    """
    uid = UniqueIdProperty()  # Unique identifier
    profile = RelationshipTo('Profile', 'HAS_PROFILE')  # Associated user profile
    like= RelationshipTo('ProfileDataReaction', 'HAS_LIKE')  # Education reactions
    comment= RelationshipTo('ProfileDataComment', 'HAS_COMMENT')  # Education comments
    what = StringProperty(required=True)  # Degree/qualification name
    field_of_study = StringProperty(required=True)  # Academic field/major
    from_source = StringProperty(required=True)  # Institution/school name
    from_date=DateTimeProperty()  # Education start date
    to_date=DateTimeProperty()  # Education end date
    created_on = DateTimeProperty(default_now=True)  # Creation timestamp
    is_deleted = BooleanProperty(default=False)  # Soft deletion flag
    file_id=ArrayProperty(base_property=StringProperty())  # Attached file identifiers

    def save(self, *args, **kwargs):
        """Override save to ensure creation timestamp is set."""
        self.created_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'auth_manager'

class Experience(DjangoNode,StructuredNode):
    """
    Neo4j-based model for storing user work experience and professional background.
    
    This model represents user professional experience using Neo4j graph database,
    supporting rich relationship mapping, engagement tracking, and comprehensive
    career history management with file attachments and detailed descriptions.
    
    Business Logic:
    - Stores experience data in Neo4j graph structure
    - Supports relationships to profiles, reactions, and comments
    - Tracks experience timeline with from/to dates
    - Manages job titles, companies, and role descriptions
    - Provides engagement analytics through likes and comments
    - Supports file attachments for portfolios and documents
    - Supports soft deletion for data retention
    
    Use Cases:
    - User professional background and career tracking
    - Professional networking and career connections
    - Work experience validation and verification
    - Experience-based user discovery and matching
    - Career analytics and professional insights
    """
    uid = UniqueIdProperty()  # Unique identifier
    profile = RelationshipTo('Profile', 'HAS_PROFILE')  # Associated user profile
    like= RelationshipTo('ProfileDataReaction', 'HAS_LIKE')  # Experience reactions
    comment= RelationshipTo('ProfileDataComment', 'HAS_COMMENT')  # Experience comments
    what =StringProperty(required=True)  # Job title/position name
    from_source = StringProperty(required=True)  # Company/organization name
    from_date=DateTimeProperty()  # Experience start date
    to_date=DateTimeProperty()  # Experience end date
    description =  StringProperty(default_now=True)  # Role description and responsibilities
    created_on = DateTimeProperty(default_now=True)  # Creation timestamp
    is_deleted = BooleanProperty(default=False)  # Soft deletion flag
    file_id=ArrayProperty(base_property=StringProperty())  # Attached file identifiers

    def save(self, *args, **kwargs):
        """Override save to ensure creation timestamp is set."""
        self.created_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'auth_manager'

class Skill(DjangoNode,StructuredNode):
    """
    Neo4j-based model for storing user skills and competencies.
    
    This model represents user skills using Neo4j graph database,
    supporting rich relationship mapping, engagement tracking, and
    comprehensive skill management with validation and file attachments.
    
    Business Logic:
    - Stores skill data in Neo4j graph structure
    - Supports relationships to profiles, reactions, and comments
    - Tracks skill acquisition timeline with from/to dates
    - Manages skill names and validation sources
    - Provides engagement analytics through likes and comments
    - Supports file attachments for certificates and portfolios
    - Supports soft deletion for data retention
    
    Use Cases:
    - User skill tracking and competency management
    - Skill-based networking and professional matching
    - Skill validation and endorsement systems
    - Competency-based user discovery and recommendations
    - Skill analytics and professional development insights
    """
    uid = UniqueIdProperty()  # Unique identifier
    profile = RelationshipTo('Profile', 'HAS_PROFILE')  # Associated user profile
    like= RelationshipTo('ProfileDataReaction', 'HAS_LIKE')  # Skill reactions
    comment= RelationshipTo('ProfileDataComment', 'HAS_COMMENT')  # Skill comments
    what = StringProperty(required=True)  # Skill name/title
    from_source = StringProperty(required=True)  # Skill source/validation authority
    from_date=DateTimeProperty()  # Skill acquisition start date
    to_date=DateTimeProperty()  # Skill acquisition end date
    created_on = DateTimeProperty(default_now=True)  # Creation timestamp
    is_deleted = BooleanProperty(default=False)  # Soft deletion flag
    file_id=ArrayProperty(base_property=StringProperty())  # Attached file identifiers

    def save(self, *args, **kwargs):
        """Override save to ensure creation timestamp is set."""
        self.created_on = datetime.now()
        super().save(*args, **kwargs)
    
    class Meta:
        app_label = 'auth_manager'

class AchievementReactionManager(models.Model):
    """
    Manages reactions and vibes for individual achievement entries.
    
    This model provides specialized reaction management for achievement data,
    tracking user engagement, vibe scores, and reaction patterns with
    comprehensive analytics and cumulative scoring capabilities.
    
    Business Logic:
    - Manages achievement-specific reaction data
    - Tracks vibe counts and cumulative scoring
    - Initializes default reaction sets for consistency
    - Supports dynamic reaction updates and analytics
    - Provides engagement insights for achievement content
    
    Use Cases:
    - Achievement engagement tracking and analytics
    - User reaction pattern analysis for achievements
    - Achievement popularity and validation metrics
    - Personalized achievement recommendation systems
    - Achievement-based social validation features
    """
    achievement_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)  # Achievement identifier
    achievement_vibe = models.JSONField(default=list)  # Achievement reaction data

    class Meta:
        verbose_name = 'Achievement Reaction Manager'
        verbose_name_plural = 'Achievement Reaction Managers'

    def __str__(self):
        """Return formatted manager identification for string representation."""
        return f"AchievementReactionManager for achievement {self.achievement_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the AchievementVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.achievement_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.achievement_vibe:
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
        return self.achievement_vibe

class EducationReactionManager(models.Model):
    """
    Manages reactions and vibes for individual education entries.
    
    This model provides specialized reaction management for education data,
    tracking user engagement, vibe scores, and reaction patterns with
    comprehensive analytics and cumulative scoring capabilities.
    
    Business Logic:
    - Manages education-specific reaction data
    - Tracks vibe counts and cumulative scoring
    - Initializes default reaction sets for consistency
    - Supports dynamic reaction updates and analytics
    - Provides engagement insights for education content
    
    Use Cases:
    - Education engagement tracking and analytics
    - User reaction pattern analysis for academic content
    - Education validation and credibility metrics
    - Academic networking and alumni engagement
    - Education-based recommendation systems
    """
    education_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)  # Education identifier
    education_vibe = models.JSONField(default=list)  # Education reaction data

    class Meta:
        verbose_name = 'Education Reaction Manager'
        verbose_name_plural = 'Education Reaction Managers'

    def __str__(self):
        """Return formatted manager identification for string representation."""
        return f"EducationReactionManager for education {self.education_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the EducationVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.education_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.education_vibe:
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
        return self.education_vibe

class SkillReactionManager(models.Model):
    """
    Manages reactions and vibes for individual skill entries.
    
    This model provides specialized reaction management for skill data,
    tracking user engagement, vibe scores, and reaction patterns with
    comprehensive analytics and cumulative scoring capabilities.
    
    Business Logic:
    - Manages skill-specific reaction data
    - Tracks vibe counts and cumulative scoring
    - Initializes default reaction sets for consistency
    - Supports dynamic reaction updates and analytics
    - Provides engagement insights for skill content
    
    Use Cases:
    - Skill engagement tracking and analytics
    - User reaction pattern analysis for skills
    - Skill validation and endorsement metrics
    - Skill-based networking and professional matching
    - Competency-based recommendation systems
    """
    skill_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)  # Skill identifier
    skill_vibe = models.JSONField(default=list)  # Skill reaction data

    class Meta:
        verbose_name = 'Skill Reaction Manager'
        verbose_name_plural = 'Skill Reaction Managers'

    def __str__(self):
        """Return formatted manager identification for string representation."""
        return f"SkillReactionManager for skill {self.skill_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the SkillVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.skill_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.skill_vibe:
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
        return self.skill_vibe

class ExperienceReactionManager(models.Model):
    """
    Manages reactions and vibes for individual experience entries.
    
    This model provides specialized reaction management for experience data,
    tracking user engagement, vibe scores, and reaction patterns with
    comprehensive analytics and cumulative scoring capabilities.
    
    Business Logic:
    - Manages experience-specific reaction data
    - Tracks vibe counts and cumulative scoring
    - Initializes default reaction sets for consistency
    - Supports dynamic reaction updates and analytics
    - Provides engagement insights for experience content
    
    Use Cases:
    - Experience engagement tracking and analytics
    - User reaction pattern analysis for professional content
    - Experience validation and credibility metrics
    - Professional networking and career connections
    - Experience-based recommendation systems
    """
    experience_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)  # Experience identifier
    experience_vibe = models.JSONField(default=list)  # Experience reaction data

    class Meta:
        verbose_name = 'Experience Reaction Manager'
        verbose_name_plural = 'Experience Reaction Managers'

    def __str__(self):
        """Return formatted manager identification for string representation."""
        return f"ExperienceReactionManager for experience {self.experience_uid}"

    def initialize_reactions(self):
        """Populate the initial 10 vibes with `vibes_count=0` and `cumulative_vibe_score=0`."""
        first_10_vibes = IndividualVibe.objects.all()[:10]  # Get the first 10 vibes
        for vibe in first_10_vibes:
            reaction_info = {
                'id': vibe.id,  # Use the actual ID of the ExperienceVibe
                'vibes_id': vibe.id,  # Store the vibe's ID
                'vibes_name': vibe.name_of_vibe,  # Store the name of the vibe
                'vibes_count': 0,  # Initialize count as 0
                'cumulative_vibe_score': 0  # Initialize cumulative score as 0
            }
            self.experience_vibe.append(reaction_info)

    def add_reaction(self, vibes_name, score):
        """
        Add or update a reaction for a specific vibe. 
        If it exists, increment the count and update the cumulative vibe score.
        """
        # Check if the reaction for the given vibes_name exists
        for reaction in self.experience_vibe:
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
        return self.experience_vibe


class ProfileDataReaction(DjangoNode,StructuredNode):
    """
    Neo4j-based model for storing user reactions to profile data elements.
    
    This model represents user reactions using Neo4j graph database,
    supporting rich relationship mapping between users and various profile
    data types (achievements, education, skills, experience) with vibe scoring.
    
    Business Logic:
    - Stores reaction data in Neo4j graph structure
    - Supports relationships to multiple profile data types
    - Tracks reaction types and vibe scores
    - Manages reaction timestamps and lifecycle
    - Provides engagement analytics through graph relationships
    - Supports soft deletion for data retention
    
    Use Cases:
    - User engagement tracking across profile data
    - Social validation and endorsement systems
    - Reaction-based recommendation algorithms
    - Profile data popularity and credibility metrics
    - User interaction analytics and insights
    """
    uid=UniqueIdProperty()  # Unique identifier
    achievement=RelationshipTo('Achievement','HAS_ACHIEVEMENT')  # Related achievement
    education=RelationshipTo('Education','HAS_EDUCATION')  # Related education
    skill=RelationshipTo('Skill','HAS_SKILL')  # Related skill
    experience=RelationshipTo('Experience','HAS_EXPERIENCE')  # Related experience
    user = RelationshipTo('Users','HAS_USER')  # User who made the reaction
    reaction = StringProperty(default='Like')  # Reaction type
    vibe = FloatProperty(default=2.0)  # Vibe score for the reaction
    timestamp = DateTimeProperty(default_now=True)  # Reaction timestamp
    is_deleted = BooleanProperty(default=False)  # Soft deletion flag

    def save(self, *args, **kwargs):
        """Override save to ensure timestamp is set."""
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'auth_manager'

    def __str__(self):
        """Return reaction type for string representation."""
        return self.reaction
    

class ProfileDataComment(DjangoNode,StructuredNode):
    """
    Neo4j-based model for storing user comments on profile data elements.
    
    This model represents user comments using Neo4j graph database,
    supporting rich relationship mapping between users and various profile
    data types (achievements, education, skills, experience) with content management.
    
    Business Logic:
    - Stores comment data in Neo4j graph structure
    - Supports relationships to multiple profile data types
    - Manages comment content and metadata
    - Tracks comment timestamps and lifecycle
    - Provides engagement analytics through graph relationships
    - Supports soft deletion for data retention
    
    Use Cases:
    - User feedback and discussion on profile data
    - Social engagement and community building
    - Profile data validation and peer review
    - Comment-based recommendation and insights
    - User interaction analytics and moderation
    """
    uid=UniqueIdProperty()  # Unique identifier
    achievement=RelationshipTo('Achievement','HAS_ACHIEVEMENT')  # Related achievement
    education=RelationshipTo('Education','HAS_EDUCATION')  # Related education
    skill=RelationshipTo('Skill','HAS_SKILL')  # Related skill
    experience=RelationshipTo('Experience','HAS_EXPERIENCE')  # Related experience
    user = RelationshipTo('Users','HAS_USER')  # User who made the comment
    content = StringProperty()  # Comment content
    timestamp = DateTimeProperty(default_now=True)  # Comment timestamp
    is_deleted = BooleanProperty(default=False)  # Soft deletion flag

    def save(self, *args, **kwargs):
        """Override save to ensure timestamp is set."""
        self.timestamp = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'auth_manager'

    def __str__(self):
        """Return comment content preview for string representation."""
        return self.content[:50] + "..." if len(self.content) > 50 else self.content
