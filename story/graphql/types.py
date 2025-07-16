# story/graphql/types.py

# This file defines GraphQL type definitions for the story module
# Converts Neo4j neomodel objects to GraphQL-compatible types for API responses
# Used by: All story-related GraphQL queries and mutations
# Handles: Type conversion, file URL generation, relationship resolution

from neomodel import db
import graphene
from graphene import ObjectType

from auth_manager.graphql.types import UserType

import requests
from django.urls import reverse
import graphene

from vibe_manager.models import IndividualVibe
from story.models import StoryReactionManager

from auth_manager.Utils import generate_presigned_url
from post.utils.time_format import time_ago
from story.redis import has_user_viewed_story,get_story_views_count,get_user_data_from_cache,get_story_views_list,check_story_cache_key_exists
from story.graphql.raw_queries.retrieve_story import get_inner_story,get_outer_story,get_universe_story,get_inner_storyV2,get_outer_storyV2,get_universe_storyV2

# File detail type for handling media attachments
# Provides structured file information including URLs, types, and metadata
# Used by: All story types that include media (images/videos)
# Generates: Presigned URLs for secure file access from cloud storage
class FileDetailType(graphene.ObjectType):
    url = graphene.String()          # Presigned URL for file access
    file_extension = graphene.String() # File extension (.jpg, .mp4, etc.)
    file_type = graphene.String()     # MIME type (image/jpeg, video/mp4)
    file_size = graphene.Int()        # File size in bytes

# Main story GraphQL type - complete story representation with all relationships
# Used by: Story detail queries, admin interfaces, comprehensive story data needs
# Includes: All story metadata, creator info, and relationship counts
class StoryType(ObjectType):
    # Basic story fields
    uid = graphene.String()
    title = graphene.String()
    content = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    privacy = graphene.List(graphene.String)  # Privacy circles array
    is_deleted = graphene.Boolean()
    story_image_id = graphene.String()
    
    # Computed fields
    story_image_url = graphene.Field(FileDetailType)  # Resolved file URL with metadata
    
    # User relationships
    created_by = graphene.Field(UserType)
    updated_by = graphene.Field(UserType)
    
    # Story interaction relationships - uses lambda to avoid circular imports
    storycomment = graphene.List(lambda: StoryCommentNonStoryType)
    storyreaction = graphene.List(lambda: StoryReactionNonStoryType)
    storyrating = graphene.List(lambda: StoryRatingNonStoryType)
    storyview = graphene.List(lambda: StoryViewNonStoryType)
    storyshare = graphene.List(lambda: StoryShareNonStoryType)

    # Class method for converting neomodel Story objects to GraphQL types
    # Handles: Relationship resolution, file URL generation, null safety
    # Called by: GraphQL resolvers when returning story data
    # Input: neomodel Story instance
    # Returns: StoryType GraphQL object
    @classmethod
    def from_neomodel(cls, story):
        return cls(
            uid=story.uid,
            title=story.title,
            content=story.content,
            created_at=story.created_at,
            updated_at=story.updated_at,
            privacy=story.privacy,
            is_deleted=story.is_deleted,
            story_image_id=story.story_image_id,
            # Generate presigned URL for story image with file metadata
            story_image_url=FileDetailType(**generate_presigned_url.generate_file_info(story.story_image_id)),
            # Safely resolve single relationships with null checks
            created_by=UserType.from_neomodel(story.created_by.single()) if story.created_by.single() else None,
            updated_by=UserType.from_neomodel(story.updated_by.single()) if story.updated_by.single() else None,
            # Convert relationship collections to GraphQL types
            storycomment=[StoryCommentNonStoryType.from_neomodel(x) for x in story.storycomment],
            storyreaction=[StoryReactionNonStoryType.from_neomodel(x) for x in story.storyreaction],
            storyrating=[StoryRatingNonStoryType.from_neomodel(x) for x in story.storyrating],
            storyview=[StoryViewNonStoryType.from_neomodel(x) for x in story.storyview],
            storyshare=[StoryShareNonStoryType.from_neomodel(x) for x in story.storyshare],
        )

# Story comment type with user details
# Used by: Comment sections, story interaction displays
# Includes: Comment content, user info, timestamp for chronological sorting
class StoryCommentType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(lambda:UserStoryDetailsType)  # Specialized user type for stories
    content = graphene.String()
    is_deleted = graphene.Boolean()
    timestamp = graphene.DateTime()
       
    # Converts neomodel StoryComment to GraphQL type
    # Handles user relationship resolution with null safety
    @classmethod
    def from_neomodel(cls, storycomment):
        return cls(
            uid=storycomment.uid,
            user=UserStoryDetailsType.from_neomodel(storycomment.user.single()) if storycomment.user.single() else None,
            content=storycomment.content,
            is_deleted=storycomment.is_deleted,
            timestamp=storycomment.timestamp,
        )

# Story reaction type with vibe information
# Used by: Reaction displays, vibe analytics, emotion tracking
# Includes: Reaction name, vibe score, user who reacted
class StoryReactionType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(lambda:UserStoryDetailsType)
    reaction = graphene.String()  # Name of the vibe/emotion
    vibe = graphene.Float()       # Vibe intensity score
    is_deleted = graphene.Boolean()
    
    @classmethod
    def from_neomodel(cls, storyreaction):
        return cls(
            uid=storyreaction.uid,
            user=UserStoryDetailsType.from_neomodel(storyreaction.user.single()) if storyreaction.user.single() else None,
            reaction=storyreaction.reaction,
            vibe=storyreaction.vibe,
            is_deleted=storyreaction.is_deleted,    
        )

# Story rating type with numeric rating
# Used by: Rating displays, quality metrics, user feedback systems
class StoryRatingType(ObjectType):
    uid = graphene.String()
    story = graphene.Field(StoryType)  # Back-reference to story
    user = graphene.Field(UserType)
    rating = graphene.Int()  # 1-5 rating value
    
    @classmethod
    def from_neomodel(cls, storyrating):
        return cls(
            uid=storyrating.uid,
            story=StoryType.from_neomodel(storyrating.story.single()) if storyrating.story.single() else None,
            user=UserType.from_neomodel(storyrating.user.single()) if storyrating.user.single() else None,
            rating=storyrating.rating,
        )

# Story view tracking type
# Used by: View analytics, "seen by" lists, engagement metrics
class StoryViewType(ObjectType):
    uid = graphene.String()
    story = graphene.Field(StoryType)
    user = graphene.Field(UserType)
    viewed_at = graphene.DateTime()
    
    @classmethod
    def from_neomodel(cls, storyview):
        return cls(
            uid=storyview.uid,
            story=StoryType.from_neomodel(storyview.story.single()) if storyview.story.single() else None,
            user=UserType.from_neomodel(storyview.user.single()) if storyview.user.single() else None,
            viewed_at=storyview.viewed_at,
        )

# Story sharing type with platform information
# Used by: Share analytics, viral tracking, platform-specific metrics
class StoryShareType(ObjectType):
    uid = graphene.String()
    story = graphene.Field(StoryType)
    user = graphene.Field(UserType)
    share_type = graphene.String()  # Platform where story was shared
    shared_at = graphene.DateTime()
    
    @classmethod
    def from_neomodel(cls, storyshare):
        return cls(
            uid=storyshare.uid,
            story=StoryType.from_neomodel(storyshare.story.single()) if storyshare.story.single() else None,
            user=UserType.from_neomodel(storyshare.user.single()) if storyshare.user.single() else None,
            share_type=storyshare.share_type,
            shared_at=storyshare.shared_at,
        )

# Comment type without story back-reference - prevents circular references
# Used by: Story detail views where story context is already known
# Optimizes: Query performance by avoiding unnecessary story data loading
class StoryCommentNonStoryType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    content = graphene.String()
    is_deleted = graphene.Boolean()
    timestamp = graphene.DateTime()
       
    @classmethod
    def from_neomodel(cls, storycomment):
        return cls(
            uid=storycomment.uid,
            user=UserType.from_neomodel(storycomment.user.single()) if storycomment.user.single() else None,
            content=storycomment.content,
            is_deleted=storycomment.is_deleted,
            timestamp=storycomment.timestamp,
        )

# Reaction type without story back-reference
# Used by: Story detail views, user reaction history
class StoryReactionNonStoryType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    reaction = graphene.String()
    vibe = graphene.Int()
    is_deleted = graphene.Boolean()
    
    @classmethod
    def from_neomodel(cls, storyreaction):
        return cls(
            uid=storyreaction.uid,
            user=UserType.from_neomodel(storyreaction.user.single()) if storyreaction.user.single() else None,
            reaction=storyreaction.reaction,
            vibe=storyreaction.vibe,
            is_deleted=storyreaction.is_deleted,    
        )

# Rating type without story back-reference
# Used by: Story detail views, user rating history
class StoryRatingNonStoryType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    rating = graphene.Int()
    
    @classmethod
    def from_neomodel(cls, storyrating):
        return cls(
            uid=storyrating.uid,
            user=UserType.from_neomodel(storyrating.user.single()) if storyrating.user.single() else None,
            rating=storyrating.rating,
        )

# View type without story back-reference
# Used by: Story analytics, viewer lists
class StoryViewNonStoryType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    viewed_at = graphene.DateTime()
    
    @classmethod
    def from_neomodel(cls, storyview):
        return cls(
            uid=storyview.uid,
            user=UserType.from_neomodel(storyview.user.single()) if storyview.user.single() else None,
            viewed_at=storyview.viewed_at,
        )

# Share type without story back-reference
# Used by: Story analytics, sharing history
class StoryShareNonStoryType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    share_type = graphene.String()
    shared_at = graphene.DateTime()
    
    @classmethod
    def from_neomodel(cls, storyshare):
        return cls(
            uid=storyshare.uid,
            user=UserType.from_neomodel(storyshare.user.single()) if storyshare.user.single() else None,
            share_type=storyshare.share_type,
            shared_at=storyshare.shared_at,
        )

# Specialized user type for story contexts
# Used by: Story interactions where limited user info is needed
# Includes: Essential user data plus profile information for story displays
class UserStoryDetailsType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    user_type = graphene.String()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    profile = graphene.Field(lambda:ProfileStoryDetailsType)
    
    @classmethod
    def from_neomodel(cls, user):
        return cls(
            uid=user.uid,
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            user_type=user.user_type,
            created_at=user.created_at,
            updated_at=user.updated_at,
            profile=ProfileStoryDetailsType.from_neomodel(user.profile.single()) if user.profile.single() else None,
        )

# User profile type optimized for story contexts
# Used by: Story user displays, compact profile information
# Includes: Essential profile data with profile picture handling
class ProfileStoryDetailsType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    gender = graphene.String()
    device_id = graphene.String()
    fcm_token = graphene.String()  # Firebase Cloud Messaging for notifications
    bio = graphene.String()
    designation = graphene.String()
    worksat = graphene.String()
    phone_number = graphene.String()
    born = graphene.DateTime()
    dob = graphene.DateTime()
    school = graphene.String()
    college = graphene.String()
    lives_in = graphene.String()
    profile_pic_id = graphene.String()
    profile_pic = graphene.Field(FileDetailType)  # Resolved profile picture URL
    
    @classmethod
    def from_neomodel(cls, profile):
        return cls(
            uid=profile.uid,
            user_id=profile.user_id,
            gender=profile.gender,
            device_id=profile.device_id,
            fcm_token=profile.fcm_token,
            bio=profile.bio,
            designation=profile.designation,
            worksat=profile.worksat,
            phone_number=profile.phone_number,
            born=profile.born,
            dob=profile.dob,
            school=profile.school,
            college=profile.college,
            lives_in=profile.lives_in,
            profile_pic_id=profile.profile_pic_id,
            # Generate presigned URL for profile picture
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile.profile_pic_id)),
        )

# Enhanced story type with view status and vibe analytics
# Used by: Story feeds, detailed story views, engagement tracking
# Includes: Time formatting, view status, sorted vibe information
class StoryDetailsType(ObjectType):
    uid = graphene.String()
    title = graphene.String()
    content = graphene.String()
    privacy = graphene.List(graphene.String)
    captions = graphene.String()
    created_at = graphene.String()  # Formatted as "X time ago"
    updated_at = graphene.DateTime()
    is_deleted = graphene.Boolean()
    story_image_id = graphene.String()
    story_image_url = graphene.Field(FileDetailType)
    created_by = graphene.Field(UserStoryDetailsType)
    
    # Converts Neo4j timestamp to user-friendly format
    # Uses time_ago utility for "2 hours ago" style formatting
    @classmethod
    def from_neomodel(cls, story):
        return cls(
            uid=story.uid,
            title=story.title,
            content=story.content,
            captions=story.captions,
            privacy=story.privacy,
            created_at=time_ago(story.created_at),  # Human-readable time format
            updated_at=story.updated_at,
            is_deleted=story.is_deleted,
            story_image_id=story.story_image_id,
            story_image_url=FileDetailType(**generate_presigned_url.generate_file_info(story.story_image_id)),
            created_by=UserStoryDetailsType.from_neomodel(story.created_by.single()) if story.created_by.single() else None,
        )

# Story details without user info - used for clicked story views
# Used by: Story detail pages when viewing specific user's stories
# Includes: View tracking, vibe analytics, engagement metrics
# Special features: Checks if current user has viewed story, provides vibe rankings
class StoryDetailsNoUserType(ObjectType):
    uid = graphene.String()
    title = graphene.String()
    content = graphene.String()
    captions = graphene.String()
    created_at = graphene.String()  # Human-readable format
    updated_at = graphene.DateTime()
    privacy = graphene.List(graphene.String)
    is_deleted = graphene.Boolean()
    story_image_id = graphene.String()
    story_image_url = graphene.Field(FileDetailType)
    has_user_view_story = graphene.Boolean()  # Whether current user has viewed this story
    vibe_List = graphene.List(lambda:VibeStoryListType)  # Sorted list of vibes by score
    
    # Complex conversion with vibe analytics and view tracking
    # Integrates: Redis cache, reaction aggregation, vibe sorting
    # Input: story (neomodel object), user_id (current user identifier)
    # Output: Enhanced story type with engagement data
    @classmethod
    def from_neomodel(cls, story, user_id):
        # Fetch aggregated reaction data from Django model
        story_reaction_manager = StoryReactionManager.objects.filter(story_uid=story.uid).first()

        # Sort vibes by cumulative score for display ranking
        # Falls back to default 10 vibes if no reactions exist yet
        if story_reaction_manager:
            all_reactions = story_reaction_manager.story_vibe
            sorted_reactions = sorted(all_reactions, key=lambda x: x.get('cumulative_vibe_score', 0), reverse=True)
        else:
            # Use default vibes when no reactions exist
            sorted_reactions = IndividualVibe.objects.all()[:10]

        return cls(
            uid=story.uid,
            title=story.title,
            content=story.content,
            captions=story.captions,
            created_at=time_ago(story.created_at),
            updated_at=story.updated_at,
            privacy=story.privacy,
            is_deleted=story.is_deleted,
            story_image_id=story.story_image_id,
            story_image_url=FileDetailType(**generate_presigned_url.generate_file_info(story.story_image_id)),
            # Check Redis cache to see if user has viewed this story
            has_user_view_story=has_user_viewed_story(story.uid, user_id),
            # Convert sorted vibes to GraphQL types
            vibe_List=[VibeStoryListType.from_neomodel(vibe) for vibe in sorted_reactions] 
        )

# Story viewer analytics type - shows who viewed the story
# Used by: "Viewed by" lists, story analytics, engagement tracking
# Integrates: Redis view tracking, cached user data
class StoryViewerType(ObjectType):
    view_count = graphene.String()  # Total view count as string
    user = graphene.Field(lambda:UserStoryViewType)  # Sample viewer (first viewer)
    
    # Fetches view data from Redis cache for performance
    # Redis stores: view counts, viewer user IDs, cached user data
    # Used by: Story creators to see who viewed their stories
    @classmethod
    def from_neomodel(cls, story):
        count = get_story_views_count(story.uid)  # Get total view count from Redis
        user_ids = get_story_views_list(story.uid)  # Get list of viewer IDs
        
        # Return first viewer's details as sample
        # Could be extended to return multiple viewers
        for uid in user_ids:
            user_details = get_user_data_from_cache(uid)  # Cached user data
            return cls(
                view_count=count,
                user=UserStoryViewType.from_neomodel(user_details) if user_details else None,
            )

# User type optimized for story view lists
# Used by: "Viewed by" displays, viewer analytics
# Handles: Cached user data from Redis
class UserStoryViewType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    user_type = graphene.String()
    profile = graphene.Field(lambda:ProfileStoryViewType)
    
    # Converts cached user data (dict) to GraphQL type
    # Input: user (dict from Redis cache, not neomodel object)
    # Used when displaying viewer lists without database queries
    @classmethod
    def from_neomodel(cls, user):
        return cls(
            uid = user['uid'],
            user_id = user['user_id'],
            username = user['username'],
            email = user['email'],
            first_name = user['first_name'],
            last_name = user['last_name'],
            user_type = user['user_type'],
            profile=ProfileStoryViewType.from_neomodel(user) if user else None,
        )

# Profile type for story viewer displays
# Used by: Viewer lists, minimal profile information
# Optimized: For cached data, minimal fields for performance
class ProfileStoryViewType(ObjectType):
    uid = graphene.String()
    gender = graphene.String()
    phone_number = graphene.String()
    lives_in = graphene.String()
    profile_pic_id = graphene.String()
    profile_pic = graphene.Field(FileDetailType)
    
    # Handles cached profile data (dict format)
    # Generates profile picture URLs from cached IDs
    @classmethod
    def from_neomodel(cls, profile):
        return cls(
            uid=profile['profile_uid'],
            gender=profile['gender'],
            phone_number=profile['phone_number'],
            lives_in=profile['lives_in'],
            profile_pic_id=profile['profile_pic_id'],
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile['profile_pic_id'])),
        )

# Vibe information type for story analytics
# Used by: Reaction displays, vibe ranking, emotion analytics
# Shows: Vibe names, IDs, and cumulative scores
class VibeStoryListType(ObjectType):
    vibe_id = graphene.String()
    vibe_name = graphene.String()
    vibe_cumulative_score = graphene.String()  # Rounded score as string
    
    # Handles both dict (from aggregated data) and object (from database) formats
    # Used by: Vibe ranking systems, reaction analytics
    # Input: vibe (dict from StoryReactionManager or IndividualVibe object)
    @classmethod
    def from_neomodel(cls, vibe):
        if isinstance(vibe, dict):
            # Handle aggregated vibe data from StoryReactionManager
            return cls(
                vibe_id=vibe.get("vibes_id"),
                vibe_name=vibe.get("vibes_name"),
                vibe_cumulative_score=round(vibe.get("cumulative_vibe_score"), 1)  # Round to 1 decimal
            )
        else:
            # Handle IndividualVibe objects (default case with no reactions)
            return cls(
                vibe_id=vibe.id,
                vibe_name=vibe.name_of_vibe,
                vibe_cumulative_score="0"  # Default score for new vibes
            )

# Secondary story type for connection-based feeds
# Used by: Story feeds showing stories from user connections
# Includes: Category classification, engagement metrics, user management
class SecondaryStoryType(ObjectType):
    title = graphene.String()  # Category name (Inner/Outer/Universe)
    count = graphene.String()  # Number of new/unviewed stories
    score = graphene.Float()   # Category engagement score
    vibes = graphene.Int()     # Total vibe count across category
    user = graphene.List(lambda: SecondaryUserStoryViewType)  # Users with stories

    # Complex feed generation with connection-based story retrieval
    # Processes: User connections, story privacy, view tracking, vibe aggregation
    # Input: details (category name), log_in_uid (current user), user_id (current user ID)
    # Output: Categorized story feed with engagement metrics
    @classmethod
    def from_neomodel(cls, details, log_in_uid, user_id):
        # Internal function to process story results from Cypher queries
        # Handles: Story validation, view status, user categorization
        def process_story_results(results):
            """Process story results to classify users and count new stories."""
            nonlocal new_story, story_uids_in_category
            for story_details in results:
                user_data = story_details[0]
                profile_data = story_details[1]
                story_data = story_details[2]
                story_uid = story_data['uid']

                # Only process stories that exist in Redis (not expired)
                if check_story_cache_key_exists(story_uid):
                    story_uids_in_category.append(story_uid) 
                    total_vibes += story_vibes_count  # Note: variable not defined in original
                    
                    # Create user instance with story data
                    user_instance = SecondaryUserStoryViewType.from_neomodel(
                        user_data, profile_data, story_data, user_id,
                    )
                    
                    # Categorize by view status - unviewed stories shown first
                    if not has_user_viewed_story(story_uid, user_id):
                        non_viewed_users.append(user_instance)
                        new_story += 1
                    else:
                        viewed_users.append(user_instance)

        # Initialize tracking variables
        new_story = 0
        story_uids_in_category = [] 
        viewed_users = []
        non_viewed_users = []

        # Query mapping for different connection circles
        # Each query returns stories from specific user connection types
        query_mapping = {
            "Inner": get_inner_story,      # Close connections
            "Outer": get_outer_story,      # Extended connections  
            "Universe": get_universe_story, # All connections
        }

        # Execute appropriate Cypher query based on category
        if details in query_mapping:
            params = {"log_in_user_uid": log_in_uid}
            results, _ = db.cypher_query(query_mapping[details], params)
            process_story_results(results)

        # Get aggregated vibe count for category from Redis
        from story.redis import get_category_vibes_count
        total_vibes = get_category_vibes_count(story_uids_in_category)
    
        # Prioritize unviewed stories in feed ordering
        user = non_viewed_users + viewed_users

        return cls(
            title=details,
            count=new_story,
            score=3.0,  # Static score - could be made dynamic
            vibes=total_vibes, 
            user=user
        )

# User story details for secondary displays
# Used by: Story feeds, user story previews
# Includes: Story metadata, view tracking
class SecondaryUserStoryDetailsType(ObjectType):
    uid = graphene.String()
    title = graphene.String()
    content = graphene.String()
    captions = graphene.String()
    is_deleted = graphene.Boolean()
    story_image_id = graphene.String()
    story_image_url = graphene.Field(FileDetailType)
    has_user_view_story = graphene.Boolean()
    
    # Converts dict story data (from Cypher queries) to GraphQL type
    # Input: story (dict from raw query), user_id (for view tracking)
    # Used by: Feed generation where story data comes from custom queries
    @classmethod
    def from_neomodel(cls, story, user_id):
        story_uid = story['uid']
        return cls(
            uid=story['uid'],
            title=story['title'],
            content=story['content'],
            captions=story['captions'],
            is_deleted=story['is_deleted'],
            story_image_id=story['story_image_id'],
            story_image_url=FileDetailType(**generate_presigned_url.generate_file_info(story['story_image_id'])) if story['story_image_id'] else None,
            has_user_view_story=has_user_viewed_story(story_uid, user_id),
        )

# Secondary user type for story feeds
# Used by: Connection-based story feeds, user story combinations
# Combines: User data, profile info, story content
class SecondaryUserStoryViewType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    user_type = graphene.String()
    profile = graphene.Field(lambda:SecondaryProfileStoryViewType)
    story = graphene.Field(lambda:SecondaryUserStoryDetailsType)
    
    # Converts multiple data sources into combined user-story type
    # Input: user (dict), profile (dict), story_data (dict), user_id (current user)
    # Used by: Feed generation where data comes from optimized Cypher queries
    @classmethod
    def from_neomodel(cls, user, profile, story_data, user_id):
        return cls(
            uid = user['uid'],
            user_id = user['user_id'],
            username = user['username'],
            email = user['email'],
            first_name = user['first_name'],
            last_name = user['last_name'],
            user_type = user['user_type'],
            profile=SecondaryProfileStoryViewType.from_neomodel(profile) if profile else None,
            story=SecondaryUserStoryDetailsType.from_neomodel(story_data, user_id) if story_data else None
        )

# Secondary profile type for feed displays
# Used by: Story feeds, minimal profile info in combined views
class SecondaryProfileStoryViewType(ObjectType):
    uid = graphene.String()
    gender = graphene.String()
    phone_number = graphene.String()
    lives_in = graphene.String()
    profile_pic_id = graphene.String()
    profile_pic = graphene.Field(FileDetailType)
    
    # Handles dict profile data from optimized queries
    @classmethod
    def from_neomodel(cls, profile):
        return cls(
            uid=profile['uid'],
            gender=profile['gender'],
            phone_number=profile['phone_number'],
            lives_in=profile['lives_in'],
            profile_pic_id=profile['profile_pic_id'],
            profile_pic=FileDetailType(**generate_presigned_url.generate_file_info(profile['profile_pic_id'])),
        )

# Version 2 secondary story type - simplified without vibe analytics
# Used by: Performance-optimized story feeds
# Removes: Vibe counting, complex analytics for faster loading
class SecondaryStoryTypeV2(ObjectType):
    title = graphene.String()  # Category name
    count = graphene.String()  # New story count
    user = graphene.List(lambda: SecondaryUserStoryViewType)  # Users with stories

    # Simplified version of SecondaryStoryType without vibe processing
    # Optimized for: Faster feed loading, reduced Redis queries
    # Trade-off: Less analytics data for better performance
    @classmethod
    def from_neomodel(cls, details, log_in_uid, user_id):
        def process_story_results(results):
            """Process story results to classify users and count new stories."""
            nonlocal new_story
            for story_details in results:
                user_data = story_details[0]
                profile_data = story_details[1]
                story_data = story_details[2]
                story_uid = story_data['uid']

                # Only process non-expired stories
                if check_story_cache_key_exists(story_uid):
                    user_instance = SecondaryUserStoryViewType.from_neomodel(
                        user_data, profile_data, story_data, user_id,
                    )
                    
                    # Prioritize unviewed stories
                    if not has_user_viewed_story(story_uid, user_id):
                        non_viewed_users.append(user_instance)
                        new_story += 1
                    else:
                        viewed_users.append(user_instance)

        # Initialize variables
        new_story = 0
        viewed_users = []
        non_viewed_users = []

        # Use V2 queries for optimized performance
        query_mapping = {
            "Inner": get_inner_storyV2,
            "Outer": get_outer_storyV2,
            "Universe": get_universe_storyV2,
        }

        # Execute query and process results
        if details in query_mapping:
            params = {"log_in_user_uid": log_in_uid}
            results, _ = db.cypher_query(query_mapping[details], params)
            process_story_results(results)

        # Combine and return results
        user = non_viewed_users + viewed_users

        return cls(
            title=details,
            count=new_story,
            user=user
        )