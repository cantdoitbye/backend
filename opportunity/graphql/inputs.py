# opportunity/graphql/inputs.py

"""
GraphQL Input Type Definitions for Opportunity Module.

This module defines the input types for opportunity mutations (create, update, delete).
Input types validate and structure the data sent from frontend to backend.
"""

import graphene
from auth_manager.validators import custom_graphql_validator


class CreateOpportunityInput(graphene.InputObjectType):
    """
    Input type for CreateOpportunity mutation.
    
    This input receives ALL opportunity data in a single call after the AI
    conversation completes. The frontend chatbot collects all information first,
    then triggers the mutation with the complete payload when user clicks "Post it!"
    
    Flow:
    1. User chats with AI bot (role, location, salary, responsibilities, etc.)
    2. AI generates/assists with description, requirements, skills
    3. User reviews preview carousel with all details
    4. User uploads optional documents (JDs, company decks)
    5. User clicks "Post it!" → Frontend sends this input to CreateOpportunity mutation
    
    All fields collected during conversation are sent together.
    """
    
    # ========== OPPORTUNITY TYPE ==========
    opportunity_type = custom_graphql_validator.String.add_option(
        "opportunityType", "CreateOpportunity"
    )()  # Optional, defaults to 'job' if not provided
    
    # ========== REQUIRED CORE FIELDS ==========
    role = custom_graphql_validator.SpecialCharacterString2_200.add_option(
        "role", "CreateOpportunity"
    )(required=True)  # e.g., "UI/UX Designer – Web & Mobile Platforms"
    
    job_type = custom_graphql_validator.String.add_option(
        "jobType", "CreateOpportunity"
    )(required=True)  # "Full-Time", "Part-Time", "Contract", "Internship"
    
    location = custom_graphql_validator.String.add_option(
        "location", "CreateOpportunity"
    )(required=True)  # e.g., "Bengaluru, Hybrid (3 days in office)"
    
    experience_level = custom_graphql_validator.String.add_option(
        "experienceLevel", "CreateOpportunity"
    )(required=True)  # e.g., "2-4 years of experience"
    
    description = custom_graphql_validator.String.add_option(
        "description", "CreateOpportunity"
    )(required=True)  # AI-generated or user-written job description
    
    # ========== REQUIRED LISTS ==========
    key_responsibilities = graphene.List(
        graphene.String, required=True
    )  # ["Create wireframes...", "Collaborate with engineers..."]
    
    requirements = graphene.List(
        graphene.String, required=True
    )  # ["Bachelor's degree in Design...", "2+ years of UI/UX..."]
    
    skills = graphene.List(
        graphene.String, required=True
    )  # ["Figma", "UX Research", "Wireframing", "Prototyping"]
    
    # ========== OPTIONAL LOCATION DETAILS ==========
    is_remote = graphene.Boolean()  # True if fully remote position
    is_hybrid = graphene.Boolean()  # True if hybrid work model
    
    # ========== OPTIONAL SALARY INFORMATION ==========
    salary_range_text = custom_graphql_validator.String.add_option(
        "salaryRangeText", "CreateOpportunity"
    )()  # Human-readable: "₹6-₹10 LPA depending on portfolio"
    
    salary_min = graphene.Int()  # Numeric for filtering: 600000
    salary_max = graphene.Int()  # Numeric for filtering: 1000000
    salary_currency = graphene.String()  # "INR", "USD", "EUR", etc.
    
    # ========== OPTIONAL LISTS ==========
    good_to_have_skills = graphene.List(
        graphene.String
    )  # ["AI design tools", "motion design", "basic React"]
    
    tags = graphene.List(
        graphene.String
    )  # Additional tags for categorization
    
    # ========== ATTACHMENTS ==========
    document_ids = custom_graphql_validator.ListString.add_option(
        "documentIds", "CreateOpportunity"
    )()  # ["doc_123", "doc_456"] - JDs, company decks, etc.
    
    cover_image_id = custom_graphql_validator.String.add_option(
        "coverImageId", "CreateOpportunity"
    )()  # AI-generated or user-uploaded cover image
    
    # ========== CALL TO ACTION ==========
    cta_text = custom_graphql_validator.String.add_option(
        "ctaText", "CreateOpportunity"
    )()  # e.g., "Apply Now", "Schedule Interview", "Submit Portfolio"
    
    cta_type = custom_graphql_validator.String.add_option(
        "ctaType", "CreateOpportunity"
    )()  # "apply", "schedule_interview", "custom"
    
    # ========== PRIVACY ==========
    privacy = custom_graphql_validator.String.add_option(
        "privacy", "CreateOpportunity"
    )()  # "public", "connections", "inner", "outer"
    
    # ========== OPTIONAL EXPIRY ==========
    expires_at = graphene.DateTime()  # When this opportunity should close automatically


class UpdateOpportunityInput(graphene.InputObjectType):
    """
    Input type for UpdateOpportunity mutation.
    
    Allows opportunity creator to update any field of an existing opportunity.
    All fields are optional - only provided fields will be updated.
    """
    
    uid = custom_graphql_validator.String.add_option(
        "uid", "UpdateOpportunity"
    )(required=True)  # Opportunity UID to update
    
    # Opportunity type (optional update)
    opportunity_type = custom_graphql_validator.String.add_option(
        "opportunityType", "UpdateOpportunity"
    )()
    
    # All other fields are optional - same as CreateOpportunityInput
    role = custom_graphql_validator.SpecialCharacterString2_200.add_option(
        "role", "UpdateOpportunity"
    )()
    
    job_type = custom_graphql_validator.String.add_option(
        "jobType", "UpdateOpportunity"
    )()
    
    location = custom_graphql_validator.String.add_option(
        "location", "UpdateOpportunity"
    )()
    
    is_remote = graphene.Boolean()
    is_hybrid = graphene.Boolean()
    
    experience_level = custom_graphql_validator.String.add_option(
        "experienceLevel", "UpdateOpportunity"
    )()
    
    salary_range_text = custom_graphql_validator.String.add_option(
        "salaryRangeText", "UpdateOpportunity"
    )()
    
    salary_min = graphene.Int()
    salary_max = graphene.Int()
    salary_currency = graphene.String()
    
    description = custom_graphql_validator.String.add_option(
        "description", "UpdateOpportunity"
    )()
    
    key_responsibilities = graphene.List(graphene.String)
    requirements = graphene.List(graphene.String)
    good_to_have_skills = graphene.List(graphene.String)
    skills = graphene.List(graphene.String)
    
    document_ids = custom_graphql_validator.ListString.add_option(
        "documentIds", "UpdateOpportunity"
    )()
    
    cover_image_id = custom_graphql_validator.String.add_option(
        "coverImageId", "UpdateOpportunity"
    )()
    
    cta_text = custom_graphql_validator.String.add_option(
        "ctaText", "UpdateOpportunity"
    )()
    
    cta_type = custom_graphql_validator.String.add_option(
        "ctaType", "UpdateOpportunity"
    )()
    
    privacy = custom_graphql_validator.String.add_option(
        "privacy", "UpdateOpportunity"
    )()
    
    tags = graphene.List(graphene.String)
    
    expires_at = graphene.DateTime()
    
    # Status updates
    is_active = graphene.Boolean()  # Close/reopen opportunity


class DeleteOpportunityInput(graphene.InputObjectType):
    """
    Input type for DeleteOpportunity mutation (soft delete).
    """
    uid = custom_graphql_validator.String.add_option(
        "uid", "DeleteOpportunity"
    )(required=True)


class OpportunityFilterInput(graphene.InputObjectType):
    """
    Input type for filtering opportunities in queries.
    
    Used for searching and filtering opportunities in feed and search results.
    """
    # Opportunity type filter
    opportunity_type = graphene.String()  # Filter by type: job, event, cause, etc.
    
    # Search
    search_query = graphene.String()  # Search in role, description, skills
    
    # Filters
    job_type = graphene.String()  # Filter by job type
    location = graphene.String()  # Filter by location
    is_remote = graphene.Boolean()  # Show only remote positions
    is_hybrid = graphene.Boolean()  # Show only hybrid positions
    
    salary_min = graphene.Int()  # Minimum salary
    salary_max = graphene.Int()  # Maximum salary
    
    skills = graphene.List(graphene.String)  # Filter by required skills
    tags = graphene.List(graphene.String)  # Filter by tags
    
    # Status
    is_active = graphene.Boolean()  # Show only active opportunities
    
    # Creator
    created_by_uid = graphene.String()  # Filter by creator
    
    # Pagination
    limit = graphene.Int(default_value=20)
    offset = graphene.Int(default_value=0)
    
    # Sorting
    sort_by = graphene.String()  # "created_at", "engagement", "salary_max"
    sort_order = graphene.String()  # "asc", "desc"

class CreateOpportunityCommentInput(graphene.InputObjectType):
    """Input type for creating comments on opportunities"""
    opportunity_uid = graphene.String(required=True, description="UID of the opportunity to comment on")
    content = graphene.String(required=True, description="Comment text content")
    parent_comment_uid = graphene.String(description="UID of parent comment for nested replies")
    comment_file_id = graphene.List(graphene.String, description="File IDs for attachments")


class CreateOpportunityLikeInput(graphene.InputObjectType):
    """Input type for liking/vibing opportunities"""
    opportunity_uid = graphene.String(required=True, description="UID of the opportunity to like")
    individual_vibe_id = graphene.String(required=True, description="UID of the vibe type")
    vibe = graphene.Float(required=True, description="Vibe intensity (1.0-5.0)")



class ShareOpportunityInput(graphene.InputObjectType):
    """Input type for sharing opportunities"""
    opportunity_uid = graphene.String(required=True, description="UID of the opportunity to share")
    share_text = graphene.String(description="Optional text to include with share")


class DeleteOpportunityLikeInput(graphene.InputObjectType):
    """Input type for removing like from opportunity"""
    opportunity_uid = graphene.String(required=True, description="UID of the opportunity")


