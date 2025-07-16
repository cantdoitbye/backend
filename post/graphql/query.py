# post/graphql/query.py

"""
Post GraphQL Query Resolvers - API endpoints for fetching post-related data.

This module contains all GraphQL query resolvers for the post system including:
- Post retrieval (individual posts, user posts, feed generation)
- Interaction queries (comments, likes, shares, views)
- Analytics and recommendations
- Tag and reaction management

All resolvers handle authentication, error handling, and data optimization.
Used by: Mobile app, web frontend, admin dashboard
"""

import json
import graphene
from graphene import Mutation
from neomodel import db
from graphql_jwt.decorators import login_required,superuser_required

from post.utils.file_url import FileURL
from post.utils.reaction_manager import PostReactionUtils,IndividualVibeManager
from .types import *
from auth_manager.models import Users,Profile
from post.models import *
from connection.models import Circle
from connection.graphql.types import CircleTypeEnum,CircleTypeEnumV2
from community.models import CommunityPost
from post.utils.post_decorator import handle_graphql_post_errors
from community.models import CommunityPost

from post.graphql.raw_queries import users,post_queries
from datetime import datetime
import time


class Query(graphene.ObjectType):
    """
    Main GraphQL Query class containing all post-related query resolvers.
    
    Provides endpoints for fetching posts, interactions, analytics, and recommendations.
    All queries require authentication unless marked as public.
    Used by frontend applications to retrieve and display post data.
    """

    # Administrative query to get all posts (superuser only)
    all_posts = graphene.List(PostType)
    
    @login_required
    @superuser_required
    def resolve_all_posts(self, info):
        """
        Fetch all posts in the system for administrative purposes.
        
        Used by: Admin dashboard, system monitoring
        Requires: Superuser privileges
        Returns: List of all PostType objects
        Security: Only accessible to superusers
        """
        return [PostType.from_neomodel(post,info) for post in Post.nodes.all()]

    # Get specific post by unique identifier
    post_by_uid = graphene.Field(PostType, post_uid = graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_post_by_uid(self, info, post_uid):
        """
        Retrieve a single post by its unique identifier.
        
        Handles both regular posts and community posts. Returns empty if post is deleted.
        Used in: Post detail screens, direct post links, post sharing
        
        Expects: post_uid (string) - unique identifier for the post
        Returns: PostType object or raises exception if not found
        Edge cases: Checks for soft-deleted posts, falls back to community posts
        """
        try:
            post = Post.nodes.get(uid=post_uid)
            if post.is_deleted:
                return []
            return PostType.from_neomodel(post,info)
        except Post.DoesNotExist:
            try:
                # Fallback to community posts if regular post not found
                post = CommunityPost.nodes.get(uid=post_uid)
                if post.is_deleted:
                    return []
                return PostType.from_neomodel(post,info)
            except CommunityPost.DoesNotExist:
                raise Exception("Post not found")

    # Get posts created by the current logged-in user
    my_post = graphene.List(PostType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post(self,info):
        """
        Fetch all posts created by the currently authenticated user.
        
        Used in: User profile screen, "My Posts" section, post management
        Expects: User authentication via JWT token
        Returns: List of user's own posts (excluding deleted ones)
        Filters: Automatically excludes soft-deleted posts
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        my_post = list(user_node.post.all())
        my_posts = [post for post in my_post if not post.is_deleted]

        return [PostType.from_neomodel(post,info) for post in my_posts]
        
    # Tag-related queries
    all_tags = graphene.List(TagType)
    
    @login_required
    @superuser_required
    def resolve_all_tags(self, info):
        """
        Administrative query to fetch all tags in the system.
        
        Used by: Admin dashboard, tag management, content moderation
        Requires: Superuser privileges
        Returns: List of all TagType objects
        """
        return [TagType.from_neomodel(tag) for tag in Tag.nodes.all()]

    # Get tags associated with a specific post
    tags_by_post_uid = graphene.List(TagType, post_uid = graphene.String(required=True))
    
    @login_required
    def resolve_tags_by_post_uid(self, info, post_uid):
        """
        Retrieve all tags associated with a specific post.
        
        Used in: Post detail view, tag display, content categorization
        Expects: post_uid (string) - identifier of the post
        Returns: List of TagType objects for the post
        Assumptions: Post exists and user has permission to view it
        """
        post_node = Post.nodes.get(uid=post_uid)
        tags = list(post_node.tag.all())
        return [TagType.from_neomodel(tag) for tag in tags]

    # Get tags from all posts created by current user
    my_posttags = graphene.List(TagType)
    
    @login_required
    def resolve_my_posttags(self, info):
        """
        Fetch all tags from posts created by the current user.
        
        Used in: Tag management, user's content organization, tag analytics
        Expects: User authentication
        Returns: List of tags from user's posts
        Performance note: Iterates through all user posts to collect tags
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            my_posts = user_node.post.all()
            tags = []
            for post in my_posts:
                tags.extend(list(post.tag))
            return [TagType.from_neomodel(x) for x in tags]
        except Exception as e:
            raise Exception(e)

    # Reaction/Like queries
    all_postreactions = graphene.List(LikeType)
    
    @login_required
    @superuser_required
    def resolve_all_postreactions(self, info):
        """
        Administrative query to fetch all post reactions/likes.
        
        Used by: Admin analytics, reaction monitoring, system insights
        Requires: Superuser privileges
        Returns: List of all LikeType objects
        """
        return [LikeType.from_neomodel(like) for like in Like.nodes.all()]

    # Get reactions for a specific post (limited to 10 for performance)
    post_reactions_by_post_uid = graphene.List(LikeType, post_uid = graphene.String(required=True))
    
    @handle_graphql_post_errors
    @login_required
    def resolve_post_reactions_by_post_uid(self, info, post_uid):
        """
        Fetch reactions/likes for a specific post with performance optimization.
        
        Used in: Post detail screen, reaction display, engagement metrics
        Expects: post_uid (string) - identifier of the post
        Returns: List of up to 10 LikeType objects (for performance)
        Edge cases: Handles both regular and community posts, excludes deleted posts
        Performance: Limited to 10 reactions to prevent large data loads
        """
        try:
            post_node = Post.nodes.get(uid=post_uid)
            if post_node.is_deleted:
                return []

            like_node = post_node.like.all()
            likes_detail = like_node[:10]  # Limit to 10 for performance
            likes = list(likes_detail)
            return [LikeType.from_neomodel(like) for like in likes]
        except Post.DoesNotExist:
            # Fallback to community posts
            post_node = CommunityPost.nodes.get(uid=post_uid)
            if post_node.is_deleted:
                return []
            like_node = post_node.like.all()
            likes_detail = like_node[:10]
            likes = list(likes_detail)
            return [LikeType.from_neomodel(like) for like in likes]

    # Get aggregated vibe analytics for a specific post
    post_reactions_analytic_by_post_uid = graphene.List(VibeAnalyticType, post_uid = graphene.String(required=True))
    
    @handle_graphql_post_errors
    @login_required
    def resolve_post_reactions_analytic_by_post_uid(self, info, post_uid):
        """
        Fetch aggregated reaction analytics for a specific post.
        
        Provides detailed vibe breakdown with counts and cumulative scores.
        Used in: Analytics dashboard, post insights, engagement reports
        
        Expects: post_uid (string) - identifier of the post
        Returns: List of VibeAnalyticType with aggregated vibe data
        Data source: PostReactionManager for optimized analytics
        """
        try:
            post_node = Post.nodes.get(uid=post_uid)
            if post_node.is_deleted:
                return []
            return VibeAnalyticType.from_neomodel(post_uid)
        except Post.DoesNotExist:
            post_node = CommunityPost.nodes.get(uid=post_uid)
            if post_node.is_deleted:
                return []
            return VibeAnalyticType.from_neomodel(post_uid)

    # Get reactions from all posts by current user
    my_postreactions = graphene.List(LikeType)
    
    @handle_graphql_post_errors
    @login_required
    def resolve_my_postreactions(self, info):
        """
        Fetch all reactions received on posts created by the current user.
        
        Used in: User analytics, engagement overview, notification systems
        Expects: User authentication
        Returns: List of all reactions on user's posts
        Performance consideration: May be expensive for users with many posts
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        
        my_posts = user_node.post.all()
        reactions = []
        for post in my_posts:
            reactions.extend(list(post.like))
        return [LikeType.from_neomodel(x) for x in reactions]
        
    # Comment queries
    all_postcomments = graphene.List(CommentType)
    
    @login_required
    @superuser_required
    def resolve_all_postcomments(self, info):
        """
        Administrative query to fetch all comments in the system.
        
        Used by: Admin dashboard, comment moderation, system monitoring
        Requires: Superuser privileges
        Returns: List of all CommentType objects
        """
        return [CommentType.from_neomodel(comment) for comment in Comment.nodes.all()]

    # Get comments for a specific post with enhanced metrics
    postcomments_by_post_uid = graphene.List(CommentType, post_uid = graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_postcomments_by_post_uid(self, info, post_uid):
        """
        Fetch comments for a specific post with enhanced engagement metrics.
        
        Uses optimized Cypher query to get comments along with calculated metrics
        like views, shares, vibes count, and engagement scores for each comment.
        
        Used in: Post detail screen, comment sections, engagement analytics
        Expects: post_uid (string) - identifier of the post
        Returns: List of CommentType objects with enhanced metrics
        Performance: Uses raw Cypher queries for optimization
        Edge cases: Handles both regular posts and community posts
        """
        params = {"post_uid": post_uid}
        results, _ = db.cypher_query(post_queries.post_comments_with_metrics_query, params)
        
        if not results:
            return []
        
        enhanced_comments = []
        for result in results:
            comment_data = result[0]
            vibes_count = result[4]
            comments_count = result[5]
            shares_count = result[6]
            views_count = result[7]
            calculated_score = result[8]
            
            # Create comment object from neomodel
            comment_uid = comment_data.get('uid')
            comment_node = Comment.nodes.get(uid=comment_uid)
            
            # Create CommentType with metrics from Cypher query
            enhanced_comment = CommentType(
                uid=comment_node.uid,
                post=PostType.from_neomodel(comment_node.post.single(), info) if comment_node.post.single() else None,
                user=UserType.from_neomodel(comment_node.user.single()) if comment_node.user.single() else None,
                content=comment_node.content,
                timestamp=comment_node.timestamp,
                is_deleted=comment_node.is_deleted,
                score=float(calculated_score) if calculated_score is not None else 2.0,
                views=int(views_count) if views_count is not None else 0,
                comments=int(comments_count) if comments_count is not None else 0,
                shares=int(shares_count) if shares_count is not None else 0,
                vibes=int(vibes_count) if vibes_count is not None else 0
            )
            enhanced_comments.append(enhanced_comment)
        
        return enhanced_comments

    # Get comments from all posts by current user
    my_postcomment = graphene.List(CommentType)
    
    @handle_graphql_post_errors
    @login_required
    def resolve_my_postcomments(self, info):
        """
        Fetch all comments received on posts created by the current user.
        
        Used in: User engagement analytics, comment management, notifications
        Expects: User authentication
        Returns: List of comments on user's posts
        Performance note: Iterates through all user posts to collect comments
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_posts = user_node.post.all()
        comments = []
        for post in my_posts:
            comments.extend(list(post.comment))
        return [CommentType.from_neomodel(x) for x in comments]

    # Review queries (detailed feedback system)
    all_postreviews = graphene.List(ReviewType)
    
    @login_required
    @superuser_required
    def resolve_all_postreviews(self, info):
        """
        Administrative query to fetch all post reviews.
        
        Used by: Admin dashboard, review moderation, quality control
        Requires: Superuser privileges
        Returns: List of all ReviewType objects
        """
        return [ReviewType.from_neomodel(review) for review in Review.nodes.all()]

    # Get reviews for a specific post
    postreviews_by_post_uid = graphene.List(CommentType, post_uid = graphene.String(required=True))
    
    @handle_graphql_post_errors
    @login_required
    def resolve_postreviews_by_post_uid(self, info, post_uid):
        """
        Fetch detailed reviews for a specific post.
        
        Used in: Post detail screen, review display, quality assessment
        Expects: post_uid (string) - identifier of the post
        Returns: List of ReviewType objects with ratings and text
        """
        post_node = Post.nodes.get(uid=post_uid)
        review = list(post_node.review.all())
        return [ReviewType.from_neomodel(review) for review in review]

    # Get reviews from all posts by current user
    my_postreview = graphene.List(ReviewType)
    
    @handle_graphql_post_errors
    @login_required
    def resolve_my_postreview(self, info):
        """
        Fetch all reviews received on posts created by the current user.
        
        Used in: User feedback analytics, content quality insights
        Expects: User authentication
        Returns: List of reviews on user's posts
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_posts = user_node.post.all()
        reviews = []
        for post in my_posts:
            reviews.extend(list(post.review))
        return [ReviewType.from_neomodel(x) for x in reviews]

    # Post view analytics queries
    all_postview = graphene.List(PostViewType)
    
    @login_required
    @superuser_required
    def resolve_all_postview(self, info):
        """
        Administrative query to fetch all post view records.
        
        Used by: Admin analytics, view tracking, reach analysis
        Requires: Superuser privileges
        Returns: List of all PostViewType objects
        """
        return [PostViewType.from_neomodel(view) for view in PostView.nodes.all()]
    
    # Get views for a specific post
    postview_byuid = graphene.List(PostViewType, post_uid=graphene.String(required=True))
    
    @handle_graphql_post_errors
    @login_required
    def resolve_postview_byuid(self, info, post_uid):
        """
        Fetch view records for a specific post.
        
        Used in: Post analytics, reach metrics, view tracking
        Expects: post_uid (string) - identifier of the post
        Returns: List of PostViewType objects showing who viewed the post
        """
        post_node = Post.nodes.get(uid=post_uid)
        postview = list(post_node.view.all())
        return [PostViewType.from_neomodel(view) for view in postview]
    
    # Get views from all posts by current user
    my_post_views = graphene.List(PostViewType)
    
    @handle_graphql_post_errors
    @login_required
    def resolve_my_post_views(self, info):
        """
        Fetch all view records for posts created by the current user.
        
        Used in: User analytics dashboard, reach insights, engagement tracking
        Expects: User authentication
        Returns: List of views on user's posts
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_posts = user_node.post.all()
        views = []
        for post in my_posts:
            views.extend(list(post.view))
        return [PostViewType.from_neomodel(x) for x in views]

    # Post sharing queries
    all_postshare = graphene.List(PostShareType)
    
    @superuser_required
    @login_required
    def resolve_all_postshare(self, info):
        """
        Administrative query to fetch all post share records.
        
        Used by: Admin analytics, viral content tracking, platform insights
        Requires: Superuser privileges
        Returns: List of all PostShareType objects
        """
        return [PostShareType.from_neomodel(share) for share in PostShare.nodes.all()]
    
    # Get shares for a specific post
    postshare_byuid = graphene.List(PostShareType, post_uid=graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_postshare_byuid(self, info, post_uid):
        """
        Fetch share records for a specific post.
        
        Used in: Post analytics, viral tracking, platform distribution analysis
        Expects: post_uid (string) - identifier of the post
        Returns: List of PostShareType objects showing sharing activity
        """
        post_node = Post.nodes.get(uid=post_uid)
        postshare = list(post_node.postshare.all())
        return [PostShareType.from_neomodel(share) for share in postshare]

    # Get shares from all posts by current user
    my_post_shares = graphene.List(PostShareType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post_shares(self, info):
        """
        Fetch all share records for posts created by the current user.
        
        Used in: User viral analytics, content distribution insights
        Expects: User authentication
        Returns: List of shares on user's posts
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)            
        my_posts = user_node.post.all()
        shares = []
        for post in my_posts:
            shares.extend(list(post.postshare))
        return [PostShareType.from_neomodel(x) for x in shares]

    # Pinned post queries
    all_postpined = graphene.List(PinedPostType)
    
    @superuser_required
    @login_required
    def resolve_all_postpined(self, info):
        """
        Administrative query to fetch all pinned post records.
        
        Used by: Admin monitoring, pinned content management
        Requires: Superuser privileges
        Returns: List of all PinedPostType objects
        """
        return [PinedPostType.from_neomodel(pined,info) for pined in PinedPost.nodes.all()]
    
    # Get pinned status for a specific post
    postpined_byuid = graphene.List(PinedPostType, post_uid=graphene.String())
    
    @handle_graphql_post_errors
    @login_required
    def resolve_postpined_byuid(self, info, post_uid):
        """
        Fetch pinned records for a specific post.
        
        Used in: Post detail screen, pin status display
        Expects: post_uid (string) - identifier of the post
        Returns: List of PinedPostType objects showing who pinned the post
        Note: Method name doesn't match decorator name (postshare vs postpined)
        """
        post_node = Post.nodes.get(uid=post_uid)
        pinpost = list(post_node.pinpost.all())
        return [PinedPostType.from_neomodel(pined,info) for pined in pinpost]

    # Get pinned posts by current user
    my_post_pined = graphene.List(PinedPostType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post_pined(self, info):
        """
        Fetch posts pinned by the current user.
        
        Used in: User profile, pinned posts section, profile management
        Expects: User authentication
        Returns: List of posts the user has pinned
        Note: May have typo in relationship name (postpin vs pinpost)
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)            
        my_posts = user_node.post.all()
        pined = []
        for post in my_posts:
            pined.extend(list(post.pinpost))  # Note: Fixed relationship name
        return [PinedPostType.from_neomodel(x,info) for x in pined]

    # Saved post queries
    all_savedpost = graphene.List(SavedPostType)
    
    @superuser_required
    @login_required
    def resolve_all_savedpost(self, info):
        """
        Administrative query to fetch all saved post records.
        
        Used by: Admin analytics, user behavior insights
        Requires: Superuser privileges
        Returns: List of all SavedPostType objects
        """
        return [SavedPostType.from_neomodel(saved) for saved in SavedPost.nodes.all()]
    
    # Get saved status for a specific post
    savedpost_byuid = graphene.List(SavedPostType, post_uid=graphene.String(required=True))
    
    @handle_graphql_post_errors
    @login_required
    def resolve_savedpost_byuid(self, info, post_uid):
        """
        Fetch saved records for a specific post.
        
        Used in: Post detail screen, save status display
        Expects: post_uid (string) - identifier of the post
        Returns: List of SavedPostType objects showing who saved the post
        """
        post_node = Post.nodes.get(uid=post_uid)
        savedpost = list(post_node.postsave.all())
        return [SavedPostType.from_neomodel(x) for x in savedpost]

    # Get posts saved by current user
    my_post_saved = graphene.List(SavedPostType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post_saved(self, info):
        """
        Fetch posts saved by the current user.
        
        Used in: Saved posts screen, bookmarks, personal collections
        Expects: User authentication
        Returns: List of posts the user has saved
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)   
        my_posts = user_node.post.all()
        saved = []
        for post in my_posts:
            saved.extend(list(post.postsave))
        return [SavedPostType.from_neomodel(x) for x in saved]

    # Main feed generation query (needs optimization and review)
    my_feed = graphene.List(FeedType,circle_type=CircleTypeEnum())

    @handle_graphql_post_errors
    @login_required
    def resolve_my_feed(self, info,circle_type=None):
        """
        Generate personalized feed for the current user (LEGACY VERSION - needs optimization).
        
        Creates a personalized content feed based on user connections and circle types.
        Filters out blocked users and the user's own posts. Includes connection context
        for relationship-aware content display.
        
        IMPORTANT: This resolver needs optimization and review as noted in comments.
        
        Used in: Main feed screen, home timeline, content discovery
        Expects: User authentication, optional circle_type filter
        Returns: List of FeedType objects with posts and connection context
        Performance issues: Multiple database queries, could be optimized with bulk operations
        Edge cases: Handles users with no connections, blocked user filtering
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        log_in_user_node = Users.nodes.get(user_id=user_id)

        # Get blocked users and their IDs for filtering
        blocked_users = users.get_blocked_users(user_id)
        blocked_user_ids = {user['user_id'] for user in blocked_users}

        # Fetch all posts (performance concern: loads all posts)
        all_posts = Post.nodes.all()

        # Filter posts based on blocking and ownership rules
        filtered_posts = filter(
            lambda post: (
                post.created_by.single().user_id not in blocked_user_ids and
                post.created_by.single().user_id != str(user_id)  # Exclude user's own posts
            ),
            all_posts
        )
        
        # Reverse chronological order (latest first)
        reversed_posts = list(filtered_posts)[::-1]
        
        result_feed = []
        feed_count = 0
        user_has_connection = False
        
        # Process each post for feed inclusion (limited to 100 posts)
        for post_data in reversed_posts:
            if feed_count >= 100:
                break  # Prevent excessive processing
            
            post_user = post_data.created_by.single()  # Get post creator

            # Query connection between viewing user and post creator using Cypher
            query = """
            MATCH (byuser:Users {uid: $log_in_user_node_uid})-[c1:HAS_CONNECTION]->(conn:Connection)
            MATCH (conn)-[c3:HAS_CIRCLE]->(circle:Circle)
            MATCH (touser:Users {uid: $post_user_uid})-[c2:HAS_CONNECTION]->(conn)
            RETURN conn, circle
            """
            
            params = {
                "log_in_user_node_uid": log_in_user_node.uid,
                "post_user_uid": post_user.uid,
            }
        
            results = db.cypher_query(query, params)

            if results and results[0]: 
                user_has_connection = True
                connection_node = results[0][0][0]
                circle_node = results[0][0][1]
                original_circle_type = circle_node.get('circle_type')
                
                # Include post if circle type matches filter or no filter specified
                if circle_type is None or original_circle_type == circle_type.value:
                    result_feed.append(FeedType.from_neomodel(post_data, connection_node, circle_node,log_in_user_node))
            else: 
                # Include posts from non-connected users if no circle filter
                if circle_type is None:
                    result_feed.append(FeedType.from_neomodel(post_data, connection_node=None, circle_node=None,log_in_user_node=log_in_user_node))

        # Return empty if circle type specified but user has no connections
        if not user_has_connection and circle_type is not None:
            return []
        return result_feed

    # Get posts by specific user ID
    post_by_userid = graphene.List(PostType,user_id=graphene.String(required=True))
    
    @handle_graphql_post_errors
    @login_required
    def resolve_post_by_userid(self,info,user_id):
        """
        Fetch all posts created by a specific user.
        
        Used in: User profile viewing, content browsing, user post exploration
        Expects: user_id (string) - ID of the user whose posts to fetch
        Returns: List of PostType objects created by the specified user
        Filters: Excludes soft-deleted posts
        """
        user_node = Users.nodes.get(user_id=user_id)
        my_post = list(user_node.post.all())
        my_posts = [post for post in my_post if not post.is_deleted]
        return [PostType.from_neomodel(post,info) for post in my_posts]

    # Optimized feed query with better performance
    my_feed_test = graphene.List(FeedTestType,circle_type=CircleTypeEnum())
    
    @login_required
    def resolve_my_feed_test(self, info, circle_type=None):
        """
        Generate optimized personalized feed using raw Cypher queries (IMPROVED VERSION).
        
        This is an optimized version of the feed resolver that uses raw Cypher queries
        for better performance. Pre-loads file URLs and reaction data for efficient rendering.
        
        Used in: Main feed screen (optimized version), performance-critical contexts
        Expects: User authentication, optional circle_type filter
        Returns: List of FeedTestType objects with enhanced performance
        Performance improvements: Bulk data loading, pre-cached file URLs, optimized queries
        Features: Includes engagement scoring, file URL pre-loading, reaction analytics
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        
        params = {
            "log_in_user_node_id": str(user_id)  # ID of the logged-in user
        }

        # Execute optimized Cypher query for feed generation
        results, _ = db.cypher_query(post_queries.post_feed_query, params)
        
        result_feed = []
        user_has_connection = False

        # Initialize reaction mapping and vibe data for performance
        PostReactionUtils.initialize_map(results)
        IndividualVibeManager.store_data()  # Cache vibe data

        # Collect all file IDs for bulk URL generation
        file_ids = []
        for post in results:
            post_data = post[0]
            file_id = post_data.get('post_file_id')
            if file_id:
                for id in file_id:
                    if id:
                        file_ids.append(id)

        # Pre-generate file URLs for better performance
        FileURL.store_file_urls(file_ids)

        # Process each post result for feed display
        for post in results:
            post_node = post[0] if post[0] else None
            connection = post[4] if post[4] else None
            likes = post[3] if post[3] else None  # Reaction data
            user_node = post[1] if post[1] else None
            circle = post[5] if post[5] else None
            profile_node = post[2] if post[2] else None
            share_count = post[6] if len(post) > 6 and post[6] is not None else 0
            calculated_overall_score = post[7] if len(post) > 7 and post[7] is not None else 2.0

            if connection is not None:
                user_has_connection = True
                       
            original_circle_type = circle.get('circle_type') if circle else None

            # Include post if circle type matches filter or no filter specified
            if circle_type is None or original_circle_type == circle_type.value:
                result_feed.append(FeedTestType.from_neomodel(
                    post_node, likes, connection, circle, user_node, profile_node, share_count, calculated_overall_score
                ))

        # Return empty if circle type specified but user has no connections
        if not user_has_connection:
            if circle_type is not None:
                return []

        return result_feed

    # Content recommendation system
    recommended_post = graphene.List(PostCategoryType)
    
    @handle_graphql_post_errors
    @login_required
    def resolve_recommended_post(self,info):
        """
        Generate categorized post recommendations for content discovery.
        
        Creates different categories of recommended content including:
        - Top vibes by content type (memes, podcasts, videos, etc.)
        - Posts from connections
        - Popular posts by engagement
        - Recent posts
        
        Used in: Discovery screen, recommendation sections, content exploration
        Expects: User authentication
        Returns: List of PostCategoryType objects with categorized recommendations
        Categories: Includes 8 different recommendation categories for diverse content
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        # Define recommendation categories
        details = [
            "Top Vibes - Meme", "Top Vibes - Podcasts", "Top Vibes - Videos", 
            "Top Vibes - Music", "Top Vibes - Articles", "Post From Connection", 
            "Popular Post", "Recent Post"
        ]
        return [PostCategoryType.from_neomodel(user_node,detail) for detail in details]


class QueryV2(graphene.ObjectType):
    """
    Version 2 GraphQL Query class with improved connection handling and performance.
    
    This class provides upgraded versions of queries with better connection management,
    improved circle relationship handling, and enhanced performance optimizations.
    Uses ConnectionV2 and CircleV2 models for advanced relationship features.
    """

    # Optimized feed with version 2 connection handling
    my_feed_test = graphene.List(FeedTestTypeV2,circle_type=CircleTypeEnumV2())

    @handle_graphql_post_errors
    @login_required
    def resolve_my_feed_test(self, info, circle_type=None):
        """
        Generate optimized feed using version 2 connection and circle models.
        
        Enhanced version with improved user relationship handling and better
        circle type management. Uses JSON-based user relations for flexible
        relationship modeling.
        
        Used in: Main feed (v2), advanced relationship contexts, enhanced personalization
        Expects: User authentication, optional CircleTypeEnumV2 filter
        Returns: List of FeedTestTypeV2 objects with enhanced relationship context
        Improvements: Better circle type handling, JSON-based user relations, enhanced performance
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
           
        params = {
            "log_in_user_node_id": str(user_id)
        }

        # Execute version 2 feed query
        results, _ = db.cypher_query(post_queries.post_feed_queryV2, params)
        
        result_feed = []
        user_has_connection = False

        # Initialize performance optimization utilities
        PostReactionUtils.initialize_map(results)
        IndividualVibeManager.store_data()

        # Pre-load file URLs for performance
        file_ids = []
        for post in results:
            post_data = post[0]
            file_id = post_data.get('post_file_id')
            if file_id:
                for id in file_id:
                    if id:
                        file_ids.append(id)
        
        FileURL.store_file_urls(file_ids)
                
        login_user_node = Users.nodes.get(user_id=user_id)
        login_user_uid = login_user_node.uid
        
        # Process feed results with enhanced relationship context
        for post in results:
            post_node = post[0] if post[0] else None
            connection = post[4] if post[4] else None
            likes = post[3] if post[3] else None
            user_node = post[1] if post[1] else None
            circle = post[5] if post[5] else None
            profile_node = post[2] if post[2] else None

            if connection is not None:
                user_has_connection = True

            # Enhanced circle type handling with JSON user relations
            if circle:
                user_relations = json.loads(circle.get("user_relations", "{}"))
                original_circle_type = user_relations.get(login_user_uid, {}).get("circle_type")
            else:
                original_circle_type = None
                user_relations = None
            
            # Include post based on circle type matching
            if circle_type is None or original_circle_type == circle_type.value:
                result_feed.append(FeedTestTypeV2.from_neomodel(
                    post_node, likes, connection, circle, user_node, profile_node, user_relations, login_user_uid
                ))

        if not user_has_connection:
            if circle_type is not None:
                return []

        return result_feed

    # Inherit common queries from main Query class
    post_by_uid = Query.post_by_uid
    resolve_post_by_uid = Query.resolve_post_by_uid

    my_post = Query.my_post
    resolve_my_post = Query.resolve_my_post

    post_by_userid = Query.post_by_userid
    resolve_post_by_userid = Query.resolve_post_by_userid

    post_reactions_by_post_uid = Query.post_reactions_by_post_uid
    resolve_post_reactions_by_post_uid = Query.resolve_post_reactions_by_post_uid

    post_reactions_analytic_by_post_uid = Query.post_reactions_analytic_by_post_uid
    resolve_post_reactions_analytic_by_post_uid = Query.resolve_post_reactions_analytic_by_post_uid

    postcomments_by_post_uid = Query.postcomments_by_post_uid
    resolve_postcomments_by_post_uid = Query.resolve_postcomments_by_post_uid

    # Enhanced recommendation system for version 2
    recommended_post = graphene.List(PostCategoryTypeV2)
    
    @handle_graphql_post_errors
    @login_required
    def resolve_recommended_post(self,info):
        """
        Generate version 2 categorized recommendations with enhanced features.
        
        Improved recommendation system with better category handling and
        enhanced content discovery algorithms.
        
        Used in: Discovery screen (v2), enhanced recommendations, improved content exploration
        Expects: User authentication
        Returns: List of PostCategoryTypeV2 objects with enhanced recommendation features
        Improvements: Better categorization, enhanced algorithms, improved performance
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            details = [
                "Top Vibes - Meme", "Top Vibes - Podcasts", "Top Vibes - Videos", 
                "Top Vibes - Music", "Top Vibes - Articles", "Post From Connection", 
                "Popular Post", "Recent Post"
            ]
            return [PostCategoryTypeV2.from_neomodel(user_node,detail) for detail in details]
        except Exception as e:
            raise Exception(e)# post/graphql/query.py

"""
Post GraphQL Query Resolvers - API endpoints for fetching post-related data.

This module contains all GraphQL query resolvers for the post system including:
- Post retrieval (individual posts, user posts, feed generation)
- Interaction queries (comments, likes, shares, views)
- Analytics and recommendations
- Tag and reaction management

All resolvers handle authentication, error handling, and data optimization.
Used by: Mobile app, web frontend, admin dashboard
"""

import json
import graphene
from graphene import Mutation
from neomodel import db
from graphql_jwt.decorators import login_required,superuser_required

from post.utils.file_url import FileURL
from post.utils.reaction_manager import PostReactionUtils,IndividualVibeManager
from .types import *
from auth_manager.models import Users,Profile
from post.models import *
from connection.models import Circle
from connection.graphql.types import CircleTypeEnum,CircleTypeEnumV2
from community.models import CommunityPost
from post.utils.post_decorator import handle_graphql_post_errors
from community.models import CommunityPost

from post.graphql.raw_queries import users,post_queries
from datetime import datetime
import time


class Query(graphene.ObjectType):
    """
    Main GraphQL Query class containing all post-related query resolvers.
    
    Provides endpoints for fetching posts, interactions, analytics, and recommendations.
    All queries require authentication unless marked as public.
    Used by frontend applications to retrieve and display post data.
    """

    # Get comments for a specific post with enhanced metrics
    postcomments_by_post_uid = graphene.List(CommentType, post_uid = graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_postcomments_by_post_uid(self, info, post_uid):
        """
        Fetch comments for a specific post with enhanced engagement metrics.
        
        Uses optimized Cypher query to get comments along with calculated metrics
        like views, shares, vibes count, and engagement scores for each comment.
        
        Used in: Post detail screen, comment sections, engagement analytics
        Expects: post_uid (string) - identifier of the post
        Returns: List of CommentType objects with enhanced metrics
        Performance: Uses raw Cypher queries for optimization
        Edge cases: Handles both regular posts and community posts
        """
        params = {"post_uid": post_uid}
        results, _ = db.cypher_query(post_queries.post_comments_with_metrics_query, params)
        
        if not results:
            return []
        
        enhanced_comments = []
        for result in results:
            comment_data = result[0]
            vibes_count = result[4]
            comments_count = result[5]
            shares_count = result[6]
            views_count = result[7]
            calculated_score = result[8]
            
            # Create comment object from neomodel
            comment_uid = comment_data.get('uid')
            comment_node = Comment.nodes.get(uid=comment_uid)
            
            # Create CommentType with metrics from Cypher query
            enhanced_comment = CommentType(
                uid=comment_node.uid,
                post=PostType.from_neomodel(comment_node.post.single(), info) if comment_node.post.single() else None,
                user=UserType.from_neomodel(comment_node.user.single()) if comment_node.user.single() else None,
                content=comment_node.content,
                timestamp=comment_node.timestamp,
                is_deleted=comment_node.is_deleted,
                score=float(calculated_score) if calculated_score is not None else 2.0,
                views=int(views_count) if views_count is not None else 0,
                comments=int(comments_count) if comments_count is not None else 0,
                shares=int(shares_count) if shares_count is not None else 0,
                vibes=int(vibes_count) if vibes_count is not None else 0
            )
            enhanced_comments.append(enhanced_comment)
        
        return enhanced_comments

    # Get comments from all posts by current user
    my_postcomment = graphene.List(CommentType)
    
    @handle_graphql_post_errors
    @login_required
    def resolve_my_postcomments(self, info):
        """
        Fetch all comments received on posts created by the current user.
        
        Used in: User engagement analytics, comment management, notifications
        Expects: User authentication
        Returns: List of comments on user's posts
        Performance note: Iterates through all user posts to collect comments
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_posts = user_node.post.all()
        comments = []
        for post in my_posts:
            comments.extend(list(post.comment))
        return [CommentType.from_neomodel(x) for x in comments]

    # Review queries (detailed feedback system)
    all_postreviews = graphene.List(ReviewType)
    
    @login_required
    @superuser_required
    def resolve_all_postreviews(self, info):
        """
        Administrative query to fetch all post reviews.
        
        Used by: Admin dashboard, review moderation, quality control
        Requires: Superuser privileges
        Returns: List of all ReviewType objects
        """
        return [ReviewType.from_neomodel(review) for review in Review.nodes.all()]

    # Get reviews for a specific post
    postreviews_by_post_uid = graphene.List(CommentType, post_uid = graphene.String(required=True))
    
    @handle_graphql_post_errors
    @login_required
    def resolve_postreviews_by_post_uid(self, info, post_uid):
        """
        Fetch detailed reviews for a specific post.
        
        Used in: Post detail screen, review display, quality assessment
        Expects: post_uid (string) - identifier of the post
        Returns: List of ReviewType objects with ratings and text
        """
        post_node = Post.nodes.get(uid=post_uid)
        review = list(post_node.review.all())
        return [ReviewType.from_neomodel(review) for review in review]

    # Get reviews from all posts by current user
    my_postreview = graphene.List(ReviewType)
    
    @handle_graphql_post_errors
    @login_required
    def resolve_my_postreview(self, info):
        """
        Fetch all reviews received on posts created by the current user.
        
        Used in: User feedback analytics, content quality insights
        Expects: User authentication
        Returns: List of reviews on user's posts
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_posts = user_node.post.all()
        reviews = []
        for post in my_posts:
            reviews.extend(list(post.review))
        return [ReviewType.from_neomodel(x) for x in reviews]

    # Post view analytics queries
    all_postview = graphene.List(PostViewType)
    
    @login_required
    @superuser_required
    def resolve_all_postview(self, info):
        """
        Administrative query to fetch all post view records.
        
        Used by: Admin analytics, view tracking, reach analysis
        Requires: Superuser privileges
        Returns: List of all PostViewType objects
        """
        return [PostViewType.from_neomodel(view) for view in PostView.nodes.all()]
    
    # Get views for a specific post
    postview_byuid = graphene.List(PostViewType, post_uid=graphene.String(required=True))
    
    @handle_graphql_post_errors
    @login_required
    def resolve_postview_byuid(self, info, post_uid):
        """
        Fetch view records for a specific post.
        
        Used in: Post analytics, reach metrics, view tracking
        Expects: post_uid (string) - identifier of the post
        Returns: List of PostViewType objects showing who viewed the post
        """
        post_node = Post.nodes.get(uid=post_uid)
        postview = list(post_node.view.all())
        return [PostViewType.from_neomodel(view) for view in postview]
    
    # Get views from all posts by current user
    my_post_views = graphene.List(PostViewType)
    
    @handle_graphql_post_errors
    @login_required
    def resolve_my_post_views(self, info):
        """
        Fetch all view records for posts created by the current user.
        
        Used in: User analytics dashboard, reach insights, engagement tracking
        Expects: User authentication
        Returns: List of views on user's posts
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_posts = user_node.post.all()
        views = []
        for post in my_posts:
            views.extend(list(post.view))
        return [PostViewType.from_neomodel(x) for x in views]

    # Post sharing queries
    all_postshare = graphene.List(PostShareType)
    
    @superuser_required
    @login_required
    def resolve_all_postshare(self, info):
        """
        Administrative query to fetch all post share records.
        
        Used by: Admin analytics, viral content tracking, platform insights
        Requires: Superuser privileges
        Returns: List of all PostShareType objects
        """
        return [PostShareType.from_neomodel(share) for share in PostShare.nodes.all()]
    
    # Get shares for a specific post
    postshare_byuid = graphene.List(PostShareType, post_uid=graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_postshare_byuid(self, info, post_uid):
        """
        Fetch share records for a specific post.
        
        Used in: Post analytics, viral tracking, platform distribution analysis
        Expects: post_uid (string) - identifier of the post
        Returns: List of PostShareType objects showing sharing activity
        """
        post_node = Post.nodes.get(uid=post_uid)
        postshare = list(post_node.postshare.all())
        return [PostShareType.from_neomodel(share) for share in postshare]

    # Get shares from all posts by current user
    my_post_shares = graphene.List(PostShareType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post_shares(self, info):
        """
        Fetch all share records for posts created by the current user.
        
        Used in: User viral analytics, content distribution insights
        Expects: User authentication
        Returns: List of shares on user's posts
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)            
        my_posts = user_node.post.all()
        shares = []
        for post in my_posts:
            shares.extend(list(post.postshare))
        return [PostShareType.from_neomodel(x) for x in shares]

    # Pinned post queries
    all_postpined = graphene.List(PinedPostType)
    
    @superuser_required
    @login_required
    def resolve_all_postpined(self, info):
        """
        Administrative query to fetch all pinned post records.
        
        Used by: Admin monitoring, pinned content management
        Requires: Superuser privileges
        Returns: List of all PinedPostType objects
        """
        return [PinedPostType.from_neomodel(pined,info) for pined in PinedPost.nodes.all()]
    
    # Get pinned status for a specific post
    postpined_byuid = graphene.List(PinedPostType, post_uid=graphene.String())
    
    @handle_graphql_post_errors
    @login_required
    def resolve_postshare_byuid(self, info, post_uid):
        """
        Fetch pinned records for a specific post.
        
        Used in: Post detail screen, pin status display
        Expects: post_uid (string) - identifier of the post
        Returns: List of PinedPostType objects showing who pinned the post
        """
        post_node = Post.nodes.get(uid=post_uid)
        pinpost = list(post_node.pinpost.all())
        return [PinedPostType.from_neomodel(pined,info) for pined in pinpost]

    # Get pinned posts by current user
    my_post_pined = graphene.List(PinedPostType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post_pined(self, info):
        """
        Fetch posts pinned by the current user.
        
        Used in: User profile, pinned posts section, profile management
        Expects: User authentication
        Returns: List of posts the user has pinned
        Note: May have typo in relationship name (postpin vs pinpost)
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)            
        my_posts = user_node.post.all()
        pined = []
        for post in my_posts:
            pined.extend(list(post.postpin))  # Note: Possible relationship name inconsistency
        return [PinedPostType.from_neomodel(x) for x in pined]

    # Saved post queries
    all_savedpost = graphene.List(SavedPostType)
    
    @superuser_required
    @login_required
    def resolve_all_savedpost(self, info):
        """
        Administrative query to fetch all saved post records.
        
        Used by: Admin analytics, user behavior insights
        Requires: Superuser privileges
        Returns: List of all SavedPostType objects
        """
        return [SavedPostType.from_neomodel(saved) for saved in SavedPost.nodes.all()]
    
    # Get saved status for a specific post
    savedpost_byuid = graphene.List(SavedPostType, post_uid=graphene.String(required=True))
    
    @handle_graphql_post_errors
    @login_required
    def resolve_savedpost_byuid(self, info, post_uid):
        """
        Fetch saved records for a specific post.
        
        Used in: Post detail screen, save status display
        Expects: post_uid (string) - identifier of the post
        Returns: List of SavedPostType objects showing who saved the post
        """
        post_node = Post.nodes.get(uid=post_uid)
        savedpost = list(post_node.postsave.all())
        return [SavedPostType.from_neomodel(x) for x in savedpost]

    # Get posts saved by current user
    my_post_saved = graphene.List(SavedPostType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post_saved(self, info):
        """
        Fetch posts saved by the current user.
        
        Used in: Saved posts screen, bookmarks, personal collections
        Expects: User authentication
        Returns: List of posts the user has saved
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)   
        my_posts = user_node.post.all()
        saved = []
        for post in my_posts:
            saved.extend(list(post.postsave))
        return [SavedPostType.from_neomodel(x) for x in saved]

    # Main feed generation query (needs optimization and review)
    my_feed = graphene.List(FeedType,circle_type=CircleTypeEnum())

    @handle_graphql_post_errors
    @login_required
    def resolve_my_feed(self, info,circle_type=None):
        """
        Generate personalized feed for the current user (LEGACY VERSION - needs optimization).
        
        Creates a personalized content feed based on user connections and circle types.
        Filters out blocked users and the user's own posts. Includes connection context
        for relationship-aware content display.
        
        IMPORTANT: This resolver needs optimization and review as noted in comments.
        
        Used in: Main feed screen, home timeline, content discovery
        Expects: User authentication, optional circle_type filter
        Returns: List of FeedType objects with posts and connection context
        Performance issues: Multiple database queries, could be optimized with bulk operations
        Edge cases: Handles users with no connections, blocked user filtering
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        log_in_user_node = Users.nodes.get(user_id=user_id)

        # Get blocked users and their IDs for filtering
        blocked_users = users.get_blocked_users(user_id)
        blocked_user_ids = {user['user_id'] for user in blocked_users}

        # Fetch all posts (performance concern: loads all posts)
        all_posts = Post.nodes.all()

        # Filter posts based on blocking and ownership rules
        filtered_posts = filter(
            lambda post: (
                post.created_by.single().user_id not in blocked_user_ids and
                post.created_by.single().user_id != str(user_id)  # Exclude user's own posts
            ),
            all_posts
        )
        
        # Reverse chronological order (latest first)
        reversed_posts = list(filtered_posts)[::-1]
        
        result_feed = []
        feed_count = 0
        user_has_connection = False
        
        # Process each post for feed inclusion (limited to 100 posts)
        for post_data in reversed_posts:
            if feed_count >= 100:
                break  # Prevent excessive processing
            
            post_user = post_data.created_by.single()  # Get post creator

            # Query connection between viewing user and post creator using Cypher
            query = """
            MATCH (byuser:Users {uid: $log_in_user_node_uid})-[c1:HAS_CONNECTION]->(conn:Connection)
            MATCH (conn)-[c3:HAS_CIRCLE]->(circle:Circle)
            MATCH (touser:Users {uid: $post_user_uid})-[c2:HAS_CONNECTION]->(conn)
            RETURN conn, circle
            """
            
            params = {
                "log_in_user_node_uid": log_in_user_node.uid,
                "post_user_uid": post_user.uid,
            }
        
            results = db.cypher_query(query, params)

            if results and results[0]: 
                user_has_connection = True
                connection_node = results[0][0][0]
                circle_node = results[0][0][1]
                original_circle_type = circle_node.get('circle_type')
                
                # Include post if circle type matches filter or no filter specified
                if circle_type is None or original_circle_type == circle_type.value:
                    result_feed.append(FeedType.from_neomodel(post_data, connection_node, circle_node,log_in_user_node))
            else: 
                # Include posts from non-connected users if no circle filter
                if circle_type is None:
                    result_feed.append(FeedType.from_neomodel(post_data, connection_node=None, circle_node=None,log_in_user_node=log_in_user_node))

        # Return empty if circle type specified but user has no connections
        if not user_has_connection and circle_type is not None:
            return []
        return result_feed

    # Get posts by specific user ID
    post_by_userid = graphene.List(PostType,user_id=graphene.String(required=True))
    
    @handle_graphql_post_errors
    @login_required
    def resolve_post_by_userid(self,info,user_id):
        """
        Fetch all posts created by a specific user.
        
        Used in: User profile viewing, content browsing, user post exploration
        Expects: user_id (string) - ID of the user whose posts to fetch
        Returns: List of PostType objects created by the specified user
        Filters: Excludes soft-deleted posts
        """
        user_node = Users.nodes.get(user_id=user_id)
        my_post = list(user_node.post.all())
        my_posts = [post for post in my_post if not post.is_deleted]
        return [PostType.from_neomodel(post,info) for post in my_posts]

    # Optimized feed query with better performance
    my_feed_test = graphene.List(FeedTestType,circle_type=CircleTypeEnum())
    
    @login_required
    def resolve_my_feed_test(self, info, circle_type=None):
        """
        Generate optimized personalized feed using raw Cypher queries (IMPROVED VERSION).
        
        This is an optimized version of the feed resolver that uses raw Cypher queries
        for better performance. Pre-loads file URLs and reaction data for efficient rendering.
        
        Used in: Main feed screen (optimized version), performance-critical contexts
        Expects: User authentication, optional circle_type filter
        Returns: List of FeedTestType objects with enhanced performance
        Performance improvements: Bulk data loading, pre-cached file URLs, optimized queries
        Features: Includes engagement scoring, file URL pre-loading, reaction analytics
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        
        params = {
            "log_in_user_node_id": str(user_id)  # ID of the logged-in user
        }

        # Execute optimized Cypher query for feed generation
        results, _ = db.cypher_query(post_queries.post_feed_query, params)
        
        result_feed = []
        user_has_connection = False

        # Initialize reaction mapping and vibe data for performance
        PostReactionUtils.initialize_map(results)
        IndividualVibeManager.store_data()  # Cache vibe data

        # Collect all file IDs for bulk URL generation
        file_ids = []
        for post in results:
            post_data = post[0]
            file_id = post_data.get('post_file_id')
            if file_id:
                for id in file_id:
                    if id:
                        file_ids.append(id)

        # Pre-generate file URLs for better performance
        FileURL.store_file_urls(file_ids)

        # Process each post result for feed display
        for post in results:
            post_node = post[0] if post[0] else None
            connection = post[4] if post[4] else None
            likes = post[3] if post[3] else None  # Reaction data
            user_node = post[1] if post[1] else None
            circle = post[5] if post[5] else None
            profile_node = post[2] if post[2] else None
            share_count = post[6] if len(post) > 6 and post[6] is not None else 0
            calculated_overall_score = post[7] if len(post) > 7 and post[7] is not None else 2.0

            if connection is not None:
                user_has_connection = True
                       
            original_circle_type = circle.get('circle_type') if circle else None

            # Include post if circle type matches filter or no filter specified
            if circle_type is None or original_circle_type == circle_type.value:
                result_feed.append(FeedTestType.from_neomodel(
                    post_node, likes, connection, circle, user_node, profile_node, share_count, calculated_overall_score
                ))

        # Return empty if circle type specified but user has no connections
        if not user_has_connection:
            if circle_type is not None:
                return []

        return result_feed

    # Content recommendation system
    recommended_post = graphene.List(PostCategoryType)
    
    @handle_graphql_post_errors
    @login_required
    def resolve_recommended_post(self,info):
        """
        Generate categorized post recommendations for content discovery.
        
        Creates different categories of recommended content including:
        - Top vibes by content type (memes, podcasts, videos, etc.)
        - Posts from connections
        - Popular posts by engagement
        - Recent posts
        
        Used in: Discovery screen, recommendation sections, content exploration
        Expects: User authentication
        Returns: List of PostCategoryType objects with categorized recommendations
        Categories: Includes 8 different recommendation categories for diverse content
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        # Define recommendation categories
        details = [
            "Top Vibes - Meme", "Top Vibes - Podcasts", "Top Vibes - Videos", 
            "Top Vibes - Music", "Top Vibes - Articles", "Post From Connection", 
            "Popular Post", "Recent Post"
        ]
        return [PostCategoryType.from_neomodel(user_node,detail) for detail in details]


class QueryV2(graphene.ObjectType):
    """
    Version 2 GraphQL Query class with improved connection handling and performance.
    
    This class provides upgraded versions of queries with better connection management,
    improved circle relationship handling, and enhanced performance optimizations.
    Uses ConnectionV2 and CircleV2 models for advanced relationship features.
    """

    # Optimized feed with version 2 connection handling
    my_feed_test = graphene.List(FeedTestTypeV2,circle_type=CircleTypeEnumV2())

    @handle_graphql_post_errors
    @login_required
    def resolve_my_feed_test(self, info, circle_type=None):
        """
        Generate optimized feed using version 2 connection and circle models.
        
        Enhanced version with improved user relationship handling and better
        circle type management. Uses JSON-based user relations for flexible
        relationship modeling.
        
        Used in: Main feed (v2), advanced relationship contexts, enhanced personalization
        Expects: User authentication, optional CircleTypeEnumV2 filter
        Returns: List of FeedTestTypeV2 objects with enhanced relationship context
        Improvements: Better circle type handling, JSON-based user relations, enhanced performance
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
           
        params = {
            "log_in_user_node_id": str(user_id)
        }

        # Execute version 2 feed query
        results, _ = db.cypher_query(post_queries.post_feed_queryV2, params)
        
        result_feed = []
        user_has_connection = False

        # Initialize performance optimization utilities
        PostReactionUtils.initialize_map(results)
        IndividualVibeManager.store_data()

        # Pre-load file URLs for performance
        file_ids = []
        for post in results:
            post_data = post[0]
            file_id = post_data.get('post_file_id')
            if file_id:
                for id in file_id:
                    if id:
                        file_ids.append(id)
        
        FileURL.store_file_urls(file_ids)
                
        login_user_node = Users.nodes.get(user_id=user_id)
        login_user_uid = login_user_node.uid
        
        # Process feed results with enhanced relationship context
        for post in results:
            post_node = post[0] if post[0] else None
            connection = post[4] if post[4] else None
            likes = post[3] if post[3] else None
            user_node = post[1] if post[1] else None
            circle = post[5] if post[5] else None
            profile_node = post[2] if post[2] else None

            if connection is not None:
                user_has_connection = True

            # Enhanced circle type handling with JSON user relations
            if circle:
                user_relations = json.loads(circle.get("user_relations", "{}"))
                original_circle_type = user_relations.get(login_user_uid, {}).get("circle_type")
            else:
                original_circle_type = None
                user_relations = None
            
            # Include post based on circle type matching
            if circle_type is None or original_circle_type == circle_type.value:
                result_feed.append(FeedTestTypeV2.from_neomodel(
                    post_node, likes, connection, circle, user_node, profile_node, user_relations, login_user_uid
                ))

        if not user_has_connection:
            if circle_type is not None:
                return []

        return result_feed

    # Inherit common queries from main Query class
    post_by_uid = Query.post_by_uid
    resolve_post_by_uid = Query.resolve_post_by_uid

    my_post = Query.my_post
    resolve_my_post = Query.resolve_my_post

    post_by_userid = Query.post_by_userid
    resolve_post_by_userid = Query.resolve_post_by_userid

    post_reactions_by_post_uid = Query.post_reactions_by_post_uid
    resolve_post_reactions_by_post_uid = Query.resolve_post_reactions_by_post_uid

    post_reactions_analytic_by_post_uid = Query.post_reactions_analytic_by_post_uid
    resolve_post_reactions_analytic_by_post_uid = Query.resolve_post_reactions_analytic_by_post_uid

    postcomments_by_post_uid = Query.postcomments_by_post_uid
    resolve_postcomments_by_post_uid = Query.resolve_postcomments_by_post_uid

    # Enhanced recommendation system for version 2
    recommended_post = graphene.List(PostCategoryTypeV2)
    
    @handle_graphql_post_errors
    @login_required
    def resolve_recommended_post(self,info):
        """
        Generate version 2 categorized recommendations with enhanced features.
        
        Improved recommendation system with better category handling and
        enhanced content discovery algorithms.
        
        Used in: Discovery screen (v2), enhanced recommendations, improved content exploration
        Expects: User authentication
        Returns: List of PostCategoryTypeV2 objects with enhanced recommendation features
        Improvements: Better categorization, enhanced algorithms, improved performance
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            details = [
                "Top Vibes - Meme", "Top Vibes - Podcasts", "Top Vibes - Videos", 
                "Top Vibes - Music", "Top Vibes - Articles", "Post From Connection", 
                "Popular Post", "Recent Post"
            ]
            return [PostCategoryTypeV2.from_neomodel(user_node,detail) for detail in details]
        except Exception as e:
            raise Exception(e)
    all_posts = graphene.List(PostType)
    
    @login_required
    @superuser_required
    def resolve_all_posts(self, info):
        """
        Fetch all posts in the system for administrative purposes.
        
        Used by: Admin dashboard, system monitoring
        Requires: Superuser privileges
        Returns: List of all PostType objects
        Security: Only accessible to superusers
        """
        return [PostType.from_neomodel(post,info) for post in Post.nodes.all()]

    # Get specific post by unique identifier
    post_by_uid = graphene.Field(PostType, post_uid = graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_post_by_uid(self, info, post_uid):
        """
        Retrieve a single post by its unique identifier.
        
        Handles both regular posts and community posts. Returns empty if post is deleted.
        Used in: Post detail screens, direct post links, post sharing
        
        Expects: post_uid (string) - unique identifier for the post
        Returns: PostType object or raises exception if not found
        Edge cases: Checks for soft-deleted posts, falls back to community posts
        """
        try:
            post = Post.nodes.get(uid=post_uid)
            if post.is_deleted:
                return []
            return PostType.from_neomodel(post,info)
        except Post.DoesNotExist:
            try:
                # Fallback to community posts if regular post not found
                post = CommunityPost.nodes.get(uid=post_uid)
                if post.is_deleted:
                    return []
                return PostType.from_neomodel(post,info)
            except CommunityPost.DoesNotExist:
                raise Exception("Post not found")

    # Get posts created by the current logged-in user
    my_post = graphene.List(PostType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post(self,info):
        """
        Fetch all posts created by the currently authenticated user.
        
        Used in: User profile screen, "My Posts" section, post management
        Expects: User authentication via JWT token
        Returns: List of user's own posts (excluding deleted ones)
        Filters: Automatically excludes soft-deleted posts
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        my_post = list(user_node.post.all())
        my_posts = [post for post in my_post if not post.is_deleted]

        return [PostType.from_neomodel(post,info) for post in my_posts]
        
    # Tag-related queries
    all_tags = graphene.List(TagType)
    
    @login_required
    @superuser_required
    def resolve_all_tags(self, info):
        """
        Administrative query to fetch all tags in the system.
        
        Used by: Admin dashboard, tag management, content moderation
        Requires: Superuser privileges
        Returns: List of all TagType objects
        """
        return [TagType.from_neomodel(tag) for tag in Tag.nodes.all()]

    # Get tags associated with a specific post
    tags_by_post_uid = graphene.List(TagType, post_uid = graphene.String(required=True))
    
    @login_required
    def resolve_tags_by_post_uid(self, info, post_uid):
        """
        Retrieve all tags associated with a specific post.
        
        Used in: Post detail view, tag display, content categorization
        Expects: post_uid (string) - identifier of the post
        Returns: List of TagType objects for the post
        Assumptions: Post exists and user has permission to view it
        """
        post_node = Post.nodes.get(uid=post_uid)
        tags = list(post_node.tag.all())
        return [TagType.from_neomodel(tag) for tag in tags]

    # Get tags from all posts created by current user
    my_posttags = graphene.List(TagType)
    
    @login_required
    def resolve_my_posttags(self, info):
        """
        Fetch all tags from posts created by the current user.
        
        Used in: Tag management, user's content organization, tag analytics
        Expects: User authentication
        Returns: List of tags from user's posts
        Performance note: Iterates through all user posts to collect tags
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            my_posts = user_node.post.all()
            tags = []
            for post in my_posts:
                tags.extend(list(post.tag))
            return [TagType.from_neomodel(x) for x in tags]
        except Exception as e:
            raise Exception(e)

    # Reaction/Like queries
    all_postreactions = graphene.List(LikeType)
    
    @login_required
    @superuser_required
    def resolve_all_postreactions(self, info):
        """
        Administrative query to fetch all post reactions/likes.
        
        Used by: Admin analytics, reaction monitoring, system insights
        Requires: Superuser privileges
        Returns: List of all LikeType objects
        """
        return [LikeType.from_neomodel(like) for like in Like.nodes.all()]

    # Get reactions for a specific post (limited to 10 for performance)
    post_reactions_by_post_uid = graphene.List(LikeType, post_uid = graphene.String(required=True))
    
    @handle_graphql_post_errors
    @login_required
    def resolve_post_reactions_by_post_uid(self, info, post_uid):
        """
        Fetch reactions/likes for a specific post with performance optimization.
        
        Used in: Post detail screen, reaction display, engagement metrics
        Expects: post_uid (string) - identifier of the post
        Returns: List of up to 10 LikeType objects (for performance)
        Edge cases: Handles both regular and community posts, excludes deleted posts
        Performance: Limited to 10 reactions to prevent large data loads
        """
        try:
            post_node = Post.nodes.get(uid=post_uid)
            if post_node.is_deleted:
                return []

            like_node = post_node.like.all()
            likes_detail = like_node[:10]  # Limit to 10 for performance
            likes = list(likes_detail)
            return [LikeType.from_neomodel(like) for like in likes]
        except Post.DoesNotExist:
            # Fallback to community posts
            post_node = CommunityPost.nodes.get(uid=post_uid)
            if post_node.is_deleted:
                return []
            like_node = post_node.like.all()
            likes_detail = like_node[:10]
            likes = list(likes_detail)
            return [LikeType.from_neomodel(like) for like in likes]

    # Get aggregated vibe analytics for a specific post
    post_reactions_analytic_by_post_uid = graphene.List(VibeAnalyticType, post_uid = graphene.String(required=True))
    
    @handle_graphql_post_errors
    @login_required
    def resolve_post_reactions_analytic_by_post_uid(self, info, post_uid):
        """
        Fetch aggregated reaction analytics for a specific post.
        
        Provides detailed vibe breakdown with counts and cumulative scores.
        Used in: Analytics dashboard, post insights, engagement reports
        
        Expects: post_uid (string) - identifier of the post
        Returns: List of VibeAnalyticType with aggregated vibe data
        Data source: PostReactionManager for optimized analytics
        """
        try:
            post_node = Post.nodes.get(uid=post_uid)
            if post_node.is_deleted:
                return []
            return VibeAnalyticType.from_neomodel(post_uid)
        except Post.DoesNotExist:
            post_node = CommunityPost.nodes.get(uid=post_uid)
            if post_node.is_deleted:
                return []
            return VibeAnalyticType.from_neomodel(post_uid)

    # Get reactions from all posts by current user
    my_postreactions = graphene.List(LikeType)
    
    @handle_graphql_post_errors
    @login_required
    def resolve_my_postreactions(self, info):
        """
        Fetch all reactions received on posts created by the current user.
        
        Used in: User analytics, engagement overview, notification systems
        Expects: User authentication
        Returns: List of all reactions on user's posts
        Performance consideration: May be expensive for users with many posts
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        
        my_posts = user_node.post.all()
        reactions = []
        for post in my_posts:
            reactions.extend(list(post.like))
        return [LikeType.from_neomodel(x) for x in reactions]
        
    # Comment queries
    all_postcomments = graphene.List(CommentType)
    
    @login_required
    @superuser_required
    def resolve_all_postcomments(self, info):
        """
        Administrative query to fetch all comments in the system.
        
        Used by: Admin dashboard, comment moderation, system monitoring
        Requires: Superuser privileges
        Returns: List of all CommentType objects
        """
        return [CommentType.from_neomodel(comment) for comment in Comment.nodes.all()]

    #