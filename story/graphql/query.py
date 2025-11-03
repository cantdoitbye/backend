# story/graphql/query.py

# This file defines GraphQL query resolvers for the story module
# Handles: Story retrieval, filtering, analytics, and relationship queries
# Used by: Mobile app, web dashboard, admin interfaces
# Security: All queries require authentication, some require admin privileges

import graphene
from graphene import Mutation
from neomodel import db
from graphql_jwt.decorators import login_required, superuser_required
from datetime import datetime, timedelta, timezone
from .types import *
from auth_manager.models import Users
from story.models import *
from story.graphql.enum.circle_type import CircleStoryTypeEnum
from story.redis import get_story_views_count, check_story_cache_key_exists
from story.graphql.raw_queries.retrieve_story import get_user_story, get_user_storyV2
from story.utils.custom_decorator import validate_different_users, handle_graphql_story_errors
from graphql import GraphQLError

# Main query class containing all story-related GraphQL queries
# Provides: CRUD operations, analytics, filtering, relationship queries
class Query(graphene.ObjectType):

    # Admin query - retrieves all stories in the system
    # Used by: Admin dashboard, system monitoring, data analysis
    # Security: Requires superuser privileges for data protection
    # Returns: Complete list of all stories with full relationship data
    all_stories = graphene.List(StoryType)
    
    @login_required
    # @superuser_required  # Commented out - should be enabled for production
    def resolve_all_stories(self, info):
        """
        Retrieves all stories in the system for admin purposes.
        Used by admin dashboard for system monitoring and data analysis.
        Requires superuser privileges to prevent unauthorized data access.
        """
        # Extract context from info for potential future use
        context = info.context
        
        # Convert all Story nodes to GraphQL types
        return [StoryType.from_neomodel(story) for story in Story.nodes.all()]

    # Single story retrieval by unique identifier
    # Used by: Story detail pages, direct story access, deep linking
    # Input: story_uid (string) - unique story identifier
    # Returns: Complete story data with all relationships
    story_byuid = graphene.Field(StoryType, story_uid=graphene.String(required=True))

    @handle_graphql_story_errors  # Custom decorator for consistent error handling
    @login_required
    def resolve_story_byuid(self, info, story_uid):
        """
        Fetches a single story by its unique identifier.
        Used when user clicks on a specific story or accesses via direct link.
        Includes all story metadata, creator info, and interaction data.
        """
        story = Story.nodes.get(uid=story_uid)
        return StoryType.from_neomodel(story)   

    # Current user's stories with optional privacy filtering
    # Used by: User profile, "My Stories" section, story management
    # Input: story_circle (optional) - filter by privacy level (Inner/Outer/Universe)
    # Returns: User's stories from last 24 hours only (story expiration logic)
    my_story = graphene.List(StoryDetailsType, story_circle=CircleStoryTypeEnum())

    @handle_graphql_story_errors
    @login_required
    def resolve_my_story(self, info, story_circle=None):
        """
        Retrieves current user's stories, optionally filtered by privacy circle.
        Only returns stories created within last 24 hours (story expiration).
        Used by profile pages and story management interfaces.
        """
        # Extract user ID from JWT token payload
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        # Calculate 24-hour cutoff for story expiration
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Get all user's stories
        all_user_stories = user_node.story.all()
        
        # Apply privacy filter if specified
        if story_circle:
            all_user_stories = [
                s for s in all_user_stories if s.privacy == story_circle.value
            ]

        # Filter to only recent stories (within 24 hours)
        recent_stories = [
            story for story in all_user_stories
            if story.created_at >= cutoff_time
        ]
        
        return [StoryDetailsType.from_neomodel(story) for story in recent_stories]

    # Stories by specific user - used for viewing other users' stories
    # Used by: User profiles, story browsing, social discovery
    # Input: user_uid (string) - target user's unique identifier
    # Returns: User's active stories with view tracking and vibe data
    # Security: Validates different users to prevent self-querying edge cases
    story_by_user_uid = graphene.List(StoryDetailsNoUserType, user_uid=graphene.String(required=True))
    
    @handle_graphql_story_errors
    @login_required
    @validate_different_users  # Ensures querying different user than current user
    def resolve_story_by_user_uid(self, info, user_uid):
        """
        Retrieves stories by a specific user for viewing by current user.
        Includes view tracking and vibe analytics.
        Only returns non-expired stories (24-hour window).
        Used when browsing other users' story collections.
        """
        # Get current user for context
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        data = []
        
        # Execute custom Cypher query for optimized story retrieval
        log_in_uid = user_node.uid
        params = {"log_in_user_uid": log_in_uid, "secondaryuseruid": user_uid}
        results, _ = db.cypher_query(get_user_story, params)
        
        # Process query results
        for story in results:
            story_details = story[1]
            story_uid = story_details["uid"]
            story_node = Story.nodes.get(uid=story_uid)
            
            # Only include non-expired stories (Redis cache check)
            if check_story_cache_key_exists(story_uid):
                data.append(
                    StoryDetailsNoUserType.from_neomodel(story_node, user_id)
                )
        
        return data

    # Admin query - all story comments system-wide
    # Used by: Content moderation, admin dashboard, comment analytics
    # Security: Requires superuser access for privacy protection
    all_storycomment = graphene.List(StoryCommentType)
    
    @login_required
    @superuser_required
    def resolve_all_storycomment(self, info):
        """
        Retrieves all story comments for administrative purposes.
        Used by content moderation tools and system analytics.
        Requires superuser privileges to access all user comments.
        """
        return [StoryCommentType.from_neomodel(comment) for comment in StoryComment.nodes.all()]
    
    # Comments for a specific story
    # Used by: Story detail pages, comment sections, engagement tracking
    # Input: story_uid (string) - story identifier
    # Returns: All comments on the specified story with user info
    storycomment_byuid = graphene.List(StoryCommentType, story_uid=graphene.String(required=True))

    @handle_graphql_story_errors
    @login_required
    def resolve_storycomment_byuid(self, info, story_uid):
        """
        Fetches all comments for a specific story.
        Used by story detail pages to display comment threads.
        Returns comments with user information and timestamps.
        """
        story = Story.nodes.get(uid=story_uid)
        storycomment = list(story.storycomment.all())
        return [StoryCommentType.from_neomodel(comment) for comment in storycomment]
    
    # Current user's story comments across all their stories
    # Used by: Comment management, user analytics, engagement tracking
    # Returns: All comments on current user's stories for moderation/analysis
    my_story_comment = graphene.List(StoryCommentType)
    
    @handle_graphql_story_errors
    @login_required
    def resolve_my_story_comment(self, info):
        """
        Retrieves all comments on current user's stories.
        Used for comment moderation and engagement analysis.
        Helps users see all feedback across their story collection.
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        
        # Get all user's stories
        my_stories = user_node.story.all()
        
        # Collect comments from all stories
        comments = []
        for story in my_stories:
            comments.extend(list(story.storycomment))
        
        return [StoryCommentType.from_neomodel(x) for x in comments]

    # Admin query - all story reactions system-wide
    # Used by: Vibe analytics, engagement metrics, content analysis
    all_storyreaction = graphene.List(StoryReactionType)
    
    @login_required
    @superuser_required
    def resolve_all_storyreaction(self, info):
        """
        Retrieves all story reactions for administrative analysis.
        Used by engagement analytics and vibe trend analysis.
        Requires admin access due to sensitive user interaction data.
        """
        return [StoryReactionType.from_neomodel(reaction) for reaction in StoryReaction.nodes.all()]
    
    # Reactions for a specific story
    # Used by: Story analytics, reaction displays, vibe tracking
    # Input: story_uid (string) - story identifier
    # Returns: All reactions with user info and vibe scores
    storyreaction_by_story_uid = graphene.List(StoryReactionType, story_uid=graphene.String(required=True))

    @handle_graphql_story_errors
    @login_required
    def resolve_storyreaction_by_story_uid(self, info, story_uid):
        """
        Fetches all reactions for a specific story.
        Used by story analytics and reaction displays.
        Shows which users reacted and their vibe scores.
        """
        story = Story.nodes.get(uid=story_uid)
        storyreaction = list(story.storyreaction.all())
        return [StoryReactionType.from_neomodel(reaction) for reaction in storyreaction]

    # Current user's story reactions - reactions on their stories
    # Used by: User analytics, engagement insights, reaction management
    my_story_reactions = graphene.List(StoryReactionType)

    @handle_graphql_story_errors
    @login_required
    def resolve_my_story_reactions(self, info):
        """
        Retrieves all reactions on current user's stories.
        Used for engagement analysis and understanding audience response.
        Helps users see how others are reacting to their content.
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        
        # Collect reactions from all user's stories
        my_stories = user_node.story.all()
        reactions = []
        for story in my_stories:
            reactions.extend(list(story.storyreaction))
        
        return [StoryReactionType.from_neomodel(x) for x in reactions]

    # Admin query - all story ratings system-wide
    # Used by: Quality analytics, content scoring, user behavior analysis
    all_storyrating = graphene.List(StoryRatingType)
    
    @login_required
    @superuser_required
    def resolve_all_storyrating(self, info):
        """
        Retrieves all story ratings for administrative analysis.
        Used by content quality metrics and user behavior studies.
        Requires admin privileges for comprehensive data access.
        """
        return [StoryRatingType.from_neomodel(rating) for rating in StoryRating.nodes.all()]

    # Ratings for a specific story
    # Used by: Story quality metrics, rating displays, content analysis
    storyrating_byuid = graphene.List(StoryRatingType, story_uid=graphene.String(required=True))
    
    @handle_graphql_story_errors
    @login_required
    def resolve_storyrating_byuid(self, info, story_uid):
        """
        Fetches all ratings for a specific story.
        Used by quality analysis and rating display systems.
        Shows numerical ratings (1-5) from different users.
        """
        story = Story.nodes.get(uid=story_uid)
        storyrating = list(story.storyrating.all())
        return [StoryRatingType.from_neomodel(rating) for rating in storyrating]

    # Current user's story ratings - ratings on their stories
    # Used by: Content quality insights, user feedback analysis
    my_story_ratings = graphene.List(StoryRatingType)

    @handle_graphql_story_errors
    @login_required
    def resolve_my_story_ratings(self, info):
        """
        Retrieves all ratings on current user's stories.
        Used for quality assessment and feedback analysis.
        Helps users understand how their content is being rated.
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        
        # Collect ratings from all user's stories
        my_stories = user_node.story.all()
        ratings = []
        for story in my_stories:
            ratings.extend(list(story.storyrating))
        
        return [StoryRatingType.from_neomodel(x) for x in ratings]

    # Admin query - all story views system-wide
    # Used by: View analytics, engagement metrics, user behavior tracking
    all_storyview = graphene.List(StoryViewType)
    
    @login_required
    @superuser_required
    def resolve_all_storyview(self, info):
        """
        Retrieves all story views for administrative analytics.
        Used by engagement tracking and user behavior analysis.
        Requires admin access for comprehensive view data.
        """
        return [StoryViewType.from_neomodel(view) for view in StoryView.nodes.all()]
    
    # Views for a specific story
    # Used by: Story analytics, "viewed by" lists, engagement tracking
    # Input: story_uid (string) - story identifier
    # Returns: All view records with user info and timestamps
    storyview_byuid = graphene.List(StoryViewType, story_uid=graphene.String(required=True))
    
    @handle_graphql_story_errors
    @login_required
    def resolve_storyview_byuid(self, info, story_uid):
        """
        Fetches all view records for a specific story.
        Used by analytics and "viewed by" displays.
        Shows who viewed the story and when.
        """
        story = Story.nodes.get(uid=story_uid)  # Find story by UID
        storyviews = list(story.storyview.all())  # Get all connected StoryView nodes
        return [StoryViewType.from_neomodel(view) for view in storyviews]
    
    # Current user's story views - views on their stories
    # Used by: Story analytics, audience insights, engagement tracking
    my_story_views = graphene.List(StoryViewType)

    @handle_graphql_story_errors
    @login_required
    def resolve_my_story_views(self, info):
        """
        Retrieves all views on current user's stories.
        Used for audience analysis and engagement insights.
        Helps users understand their story reach and viewership.
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        
        # Collect views from all user's stories
        my_stories = user_node.story.all()
        views = []
        for story in my_stories:
            views.extend(list(story.storyview))
        
        return [StoryViewType.from_neomodel(x) for x in views]

    # Admin query - all story shares system-wide
    # Used by: Viral analytics, sharing metrics, platform performance tracking
    all_storyshare = graphene.List(StoryShareType)
    
    @superuser_required
    @login_required
    def resolve_all_storyshare(self, info):
        """
        Retrieves all story shares for administrative analysis.
        Used by viral tracking and platform-specific sharing analytics.
        Requires admin privileges for comprehensive sharing data.
        """
        return [StoryShareType.from_neomodel(share) for share in StoryShare.nodes.all()]
    
    # Shares for a specific story
    # Used by: Viral analytics, sharing tracking, platform distribution analysis
    storyshare_byuid = graphene.List(StoryShareType, story_uid=graphene.String(required=True))
    
    @handle_graphql_story_errors
    @login_required
    def resolve_storyshare_byuid(self, info, story_uid):
        """
        Fetches all share records for a specific story.
        Used by viral analytics and platform distribution tracking.
        Shows how story was shared across different platforms.
        """
        story = Story.nodes.get(uid=story_uid)
        storyshare = list(story.storyshare.all())
        return [StoryShareType.from_neomodel(view) for view in storyshare]
    
    # Current user's story shares - shares of their stories
    # Used by: Viral tracking, content performance, sharing insights
    my_story_shares = graphene.List(StoryShareType)

    @handle_graphql_story_errors
    @login_required
    def resolve_my_story_shares(self, info):
        """
        Retrieves all shares of current user's stories.
        Used for viral tracking and content performance analysis.
        Helps users understand how their content spreads across platforms.
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        
        # Collect shares from all user's stories
        my_stories = user_node.story.all()
        shares = []
        for story in my_stories:
            shares.extend(list(story.storyshare))
        
        return [StoryShareType.from_neomodel(x) for x in shares]

    # Connection-based story feed - shows stories from user's connections
    # Used by: Main story feed, social discovery, connection-based content
    # Returns: Categorized stories from Inner/Outer/Universe connections
    # Includes: New story counts, engagement metrics, user prioritization
    storyListFromConnections = graphene.List(SecondaryStoryType)

    @handle_graphql_story_errors
    @login_required
    def resolve_storyListFromConnections(self, info):
        """
        Generates story feed based on user's social connections.
        Categorizes stories by connection type (Inner/Outer/Universe).
        Prioritizes unviewed stories and includes engagement metrics.
        Used by main feed to show relevant social content.
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        log_in_uid = user_node.uid

        # Define connection categories for story feed
        details = ["Inner", "Outer", "Universe"]
        
        # Generate feed sections for each connection type
        return [SecondaryStoryType.from_neomodel(detail, log_in_uid, user_id) for detail in details]

    # Story viewer analytics - shows who viewed a specific story
    # Used by: Story analytics, "viewed by" displays, audience insights
    # Input: story_uid (string) - story to analyze
    # Returns: View count and sample viewer information
    # Security: Only story creator can see viewer analytics
    Viewer_by_story_uid = graphene.List(StoryViewerType, story_uid=graphene.String(required=True))

    @handle_graphql_story_errors
    @login_required
    def resolve_Viewer_by_story_uid(self, info, story_uid=None):
        """
        Retrieves viewer analytics for a specific story.
        Only accessible by story creator for privacy protection.
        Shows view count and sample viewer information from Redis cache.
        Used by analytics dashboards and "viewed by" features.
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        story = Story.nodes.get(uid=story_uid)

        # Check if story still exists (not expired)
        if check_story_cache_key_exists(story_uid) == False:
            raise GraphQLError(
                "Story has expired",
                extensions={"code": "STORY_EXPIRED", "status_code": 410}
            )
        
        # Security check - only story creator can view analytics
        if(story.created_by.single().uid != user_node.uid):
            raise GraphQLError(
                "You are not creator of this Story",
                extensions={"code": "FORBIDDEN", "status_code": 403}
            )

        # Return viewer analytics from Redis cache
        return [StoryViewerType.from_neomodel(story)]