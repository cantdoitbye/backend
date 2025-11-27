# opportunity/models.py

"""
Opportunity Module Models - Neo4j data structures for job opportunities.

This module defines the Opportunity model which stores job postings created
through the AI-driven conversational interface. Each opportunity contains
structured information about roles, requirements, responsibilities, and
compensation.

The model is designed to integrate seamlessly with the feed system and
reuses existing interaction models (likes, comments, shares, etc.)
"""

from neomodel import (
    StructuredNode, 
    StringProperty, 
    IntegerProperty,
    FloatProperty,
    ArrayProperty, 
    DateTimeProperty, 
    BooleanProperty,
    UniqueIdProperty,
    RelationshipTo,
    RelationshipFrom
)
from django_neomodel import DjangoNode
from datetime import datetime


class Opportunity(DjangoNode, StructuredNode):
    """
    Opportunity model representing job postings in the platform.
    
    This is the core model for job opportunities created through AI conversation.
    Each opportunity contains structured fields for role details, requirements,
    responsibilities, and compensation. It integrates with the feed system and
    supports all standard interactions (likes, comments, shares, etc.).
    
    Relationships:
    - Connected to Users (creator/updater)
    - Has many Comments, Likes, Shares, Views (reused from post module)
    - Can be saved by users
    - Future: Will connect to Applications
    
    Used throughout the app for:
    - Feed display (shows alongside posts and debates)
    - Job search and filtering
    - Applicant management
    - Opportunity analytics
    """
    
    uid = UniqueIdProperty()  # Unique identifier for each opportunity
    
    # ========== OPPORTUNITY TYPE ==========
    # Type of opportunity - supports multiple use cases
    # Current: "job" (job postings)
    # Future: "event" (conferences, meetups), "cause" (volunteering, donations), 
    #         "collaboration" (project partnerships), "mentorship", etc.
    OPPORTUNITY_TYPES = {
        'job': 'Job Posting',           # Current implementation
        'event': 'Event',               # Future: Conferences, workshops, meetups
        'cause': 'Social Cause',        # Future: Volunteering, donations, campaigns
        'collaboration': 'Collaboration',  # Future: Project partnerships
        'mentorship': 'Mentorship',     # Future: Mentorship opportunities
        'internship': 'Internship',     # Future: Internship programs
        'gig': 'Gig/Freelance'          # Future: Freelance/contract work
    }
    opportunity_type = StringProperty(default='job')  # Default: job
    
    # ========== CORE FIELDS ==========
    # Role information collected from AI conversation
    role = StringProperty(required=True)  # e.g., "UI/UX Designer – Web & Mobile Platforms"
    job_type = StringProperty(required=True)  # "Full-Time", "Part-Time", "Contract", "Internship"
    
    # ========== LOCATION DETAILS ==========
    location = StringProperty(required=True)  # e.g., "Bengaluru, Hybrid (3 days in office)"
    is_remote = BooleanProperty(default=False)  # True if fully remote
    is_hybrid = BooleanProperty(default=False)  # True if hybrid work model
    
    # ========== EXPERIENCE & COMPENSATION ==========
    experience_level = StringProperty(required=True)  # e.g., "2-4 years of experience"
    salary_range_text = StringProperty()  # Human-readable: "₹6-₹10 LPA depending on portfolio"
    salary_min = IntegerProperty()  # Numeric for filtering: 600000
    salary_max = IntegerProperty()  # Numeric for filtering: 1000000
    salary_currency = StringProperty(default='INR')  # Currency code
    
    # ========== AI-GENERATED CONTENT ==========
    description = StringProperty(required=True)  # Full job description (AI-generated)
    
    # ========== STRUCTURED LISTS ==========
    # These are collected/generated during AI conversation and stored as arrays
    key_responsibilities = ArrayProperty(StringProperty())  # List of job responsibilities
    requirements = ArrayProperty(StringProperty())  # List of required qualifications
    good_to_have_skills = ArrayProperty(StringProperty())  # Optional/nice-to-have skills
    
    # ========== SKILLS & TAGS ==========
    skills = ArrayProperty(StringProperty())  # Extracted skills for search/matching
    tags = ArrayProperty(StringProperty())  # Additional tags for categorization
    
    # ========== ATTACHMENTS ==========
    document_ids = ArrayProperty(StringProperty())  # Document IDs (JDs, company decks, etc.)
    cover_image_id = StringProperty()  # AI-generated or user-uploaded cover image
    
    # ========== CALL TO ACTION ==========
    cta_text = StringProperty(default="Apply Now")  # CTA button text
    cta_type = StringProperty(default="apply")  # "apply", "schedule_interview", "custom"
    
    # ========== PRIVACY & VISIBILITY ==========
    privacy = StringProperty(default='public')  # 'public', 'connections', 'inner', 'outer'
    
    # ========== STATUS & LIFECYCLE ==========
    is_active = BooleanProperty(default=True)  # False when opportunity is closed
    is_deleted = BooleanProperty(default=False)  # Soft delete flag
    expires_at = DateTimeProperty()  # Optional expiration date
    
    # ========== MATRIX INTEGRATION ==========
    # Matrix room ID where applicants can join and apply
    # Each opportunity has its own Matrix chat room (similar to communities)
    # Example: "!abc123xyz:chat.ooumph.com"
    room_id = StringProperty()  # Matrix room ID
    
    # ========== SCORING ==========
    # Score for feed ranking and recommendation algorithm
    score = FloatProperty(default=3.2)  # Default score for opportunities
    
    # ========== TIMESTAMPS ==========
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)
    
    # ========== RELATIONSHIPS ==========
    
    # Creator and updater relationships
    created_by = RelationshipTo('auth_manager.models.Users', 'CREATED_BY')
    updated_by = RelationshipTo('auth_manager.models.Users', 'UPDATED_BY')
    
    # Reuse existing interaction models from post module
    # These allow opportunities to have the same engagement features as posts
    like = RelationshipFrom('post.models.Like', 'HAS_OPPORTUNITY')
    comment = RelationshipFrom('post.models.Comment', 'HAS_OPPORTUNITY')
    share = RelationshipFrom('post.models.PostShare', 'HAS_OPPORTUNITY')
    view = RelationshipFrom('post.models.PostView', 'HAS_OPPORTUNITY')
    saved = RelationshipFrom('post.models.SavedPost', 'HAS_OPPORTUNITY')
    
    # Future: Application tracking
    # applications = RelationshipFrom('opportunity.models.Application', 'APPLIED_TO')
    
    class Meta:
        app_label = 'opportunity'
    
    def save(self, *args, **kwargs):
        """
        Override save to update timestamp.
        """
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.role} - {self.location}"
    
    def close_opportunity(self):
        """
        Close/deactivate this opportunity.
        Used when position is filled or no longer accepting applications.
        """
        self.is_active = False
        self.save()
    
    def reopen_opportunity(self):
        """
        Reactivate a closed opportunity.
        """
        self.is_active = True
        self.save()
    
    @property
    def is_expired(self):
        """
        Check if opportunity has expired based on expires_at date.
        """
        if self.expires_at and datetime.now() > self.expires_at:
            return True
        return False
    
    @property
    def engagement_score(self):
        """
        Calculate basic engagement score based on interactions.
        Used by feed algorithm for ranking.
        """
        likes = len(self.like.all())
        comments = len(self.comment.all())
        shares = len(self.share.all())
        views = len(self.view.all())
        
        # Weighted scoring (similar to post scoring)
        score = (likes * 1.0) + (comments * 2.0) + (shares * 3.0) + (views * 0.1)
        return score


# ========== FUTURE MODELS ==========
# Uncomment and implement when adding applicant tracking features

# class Application(DjangoNode, StructuredNode):
#     """
#     Application model for tracking job applications to opportunities.
#     
#     Future implementation for applicant tracking system.
#     """
#     uid = UniqueIdProperty()
#     status = StringProperty(default='pending')  # pending, reviewed, shortlisted, rejected, hired
#     cover_letter = StringProperty()
#     resume_id = StringProperty()
#     applied_at = DateTimeProperty(default_now=True)
#     
#     # Relationships
#     applicant = RelationshipTo('auth_manager.models.Users', 'APPLICANT')
#     opportunity = RelationshipTo('Opportunity', 'APPLIED_TO')
#     
#     class Meta:
#         app_label = 'opportunity'
