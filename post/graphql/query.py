# post/graphql/query.py
import json
import graphene
from graphene import Mutation
from neomodel import db
from graphql_jwt.decorators import login_required, superuser_required

from post.utils.file_url import FileURL
from post.utils.reaction_manager import PostReactionUtils, IndividualVibeManager
from post.utils.feed_metrics import log_feed_metrics, monitor_feed_performance
from post.utils.feed_validation import validate_feed_algorithm_requirements, validate_feed_quality
from post.utils.feed_fallbacks import get_appropriate_fallback_feed
from .types import *
from auth_manager.models import Users, Profile
from post.models import *
from connection.models import Circle
from connection.graphql.types import CircleTypeEnum, CircleTypeEnumV2
from community.models import CommunityPost
from post.utils.post_decorator import handle_graphql_post_errors
from community.models import CommunityPost

from post.graphql.raw_queries import users, post_queries
from post.utils.feed_algorithm import apply_feed_algorithm
from datetime import datetime
import time
import logging
import base64


logger = logging.getLogger(__name__)


class Query(graphene.ObjectType):

    all_posts = graphene.List(PostType)

    @login_required
    @superuser_required
    def resolve_all_posts(self, info):
        return [PostType.from_neomodel(post, info) for post in Post.nodes.all()]

    post_by_uid = graphene.Field(
        PostType, post_uid=graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_post_by_uid(self, info, post_uid):
        try:
            post = Post.nodes.get(uid=post_uid)
            if post.is_deleted:
                return []
            return PostType.from_neomodel(post, info)
        except Post.DoesNotExist:
            try:
                post = CommunityPost.nodes.get(uid=post_uid)
                if post.is_deleted:
                    return []
                return PostType.from_neomodel(post, info)
            except CommunityPost.DoesNotExist:
                raise Exception("Post not found")

    my_post = graphene.List(PostType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post(self, info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        my_post = list(user_node.post.all())
        my_posts = [post for post in my_post if not post.is_deleted]

        return [PostType.from_neomodel(post, info) for post in my_posts]

    # Tag Queries
    all_tags = graphene.List(TagType)

    @login_required
    @superuser_required
    def resolve_all_tags(self, info):
        return [TagType.from_neomodel(tag) for tag in Tag.nodes.all()]

    # Tag Queries by Post
    tags_by_post_uid = graphene.List(
        TagType, post_uid=graphene.String(required=True))

    @login_required
    def resolve_tags_by_post_uid(self, info, post_uid):
        post_node = Post.nodes.get(uid=post_uid)
        tags = list(post_node.tag.all())
        return [TagType.from_neomodel(tag) for tag in tags]

    # My Tags
    my_posttags = graphene.List(TagType)

    @login_required
    def resolve_my_posttags(self, info):
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

    all_postreactions = graphene.List(LikeType)

    @login_required
    @superuser_required
    def resolve_all_postreactions(self, info):
        return [LikeType.from_neomodel(like) for like in Like.nodes.all()]

    # Tag Queries by Post
    post_reactions_by_post_uid = graphene.List(
        LikeType, post_uid=graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_post_reactions_by_post_uid(self, info, post_uid):
        try:
            post_node = Post.nodes.get(uid=post_uid)
            if post_node.is_deleted:
                return []

            like_node = post_node.like.all()
            likes_detail = like_node[:10]
            likes = list(likes_detail)
            return [LikeType.from_neomodel(like) for like in likes]
        except Post.DoesNotExist:
            post_node = CommunityPost.nodes.get(uid=post_uid)
            if post_node.is_deleted:
                return []
            like_node = post_node.like.all()
            likes_detail = like_node[:10]
            likes = list(likes_detail)
            return [LikeType.from_neomodel(like) for like in likes]

    post_reactions_analytic_by_post_uid = graphene.List(
        VibeAnalyticType, post_uid=graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_post_reactions_analytic_by_post_uid(self, info, post_uid):
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

    # My Tags
    my_postreactions = graphene.List(LikeType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_postreactions(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        my_posts = user_node.post.all()
        reactions = []
        for post in my_posts:
            reactions.extend(list(post.like))
        return [LikeType.from_neomodel(x) for x in reactions]

    all_postcomments = graphene.List(CommentType)

    @login_required
    @superuser_required
    def resolve_all_postcomments(self, info):
        return [CommentType.from_neomodel(comment) for comment in Comment.nodes.all()]

    # Tag Queries by Post
    postcomments_by_post_uid = graphene.List(
        CommentType, 
        post_uid=graphene.String(required=True),
        include_replies=graphene.Boolean(default_value=True),  # NEW: Option to include/exclude replies
        max_depth=graphene.Int(default_value=2)  # NEW: Control nesting depth
    )

    @handle_graphql_post_errors
    @login_required
    def resolve_postcomments_by_post_uid(self, info, post_uid, include_replies=True, max_depth=2):
        """
        UPDATED: Your existing resolver with nested comment support.
        Preserves all existing functionality while adding nested features.
        """
        try:
            if include_replies:
                # Use enhanced query that includes nested structure
                params = {"post_uid": post_uid}
                results, _ = db.cypher_query(
                    post_queries.post_comments_with_metrics_nested_query, params)
            else:
                # Use optimized query for top-level comments only
                params = {"post_uid": post_uid}
                results, _ = db.cypher_query(
                    post_queries.top_level_comments_with_metrics_query, params)

            if not results:
                return []

            enhanced_comments = []
            comment_cache = {}  # Cache to build nested structure efficiently

            for result in results:
                comment_data = result[0]
                parent_comment_data = result[1] if len(result) > 1 and result[1] else None
                post_data = result[2] if len(result) > 2 and result[2] else None  # Fixed: Get post data
                vibes_count = result[3] if len(result) > 3 else 0
                views_count = result[4] if len(result) > 4 else 0
                comments_count = result[5] if len(result) > 5 else 0
                shares_count = result[6] if len(result) > 6 else 0
                likes_count = result[7] if len(result) > 7 else 0
                calculated_score = result[8] if len(result) > 8 else 2.0
                reply_count = result[9] if len(result) > 9 else 0
                is_reply = result[10] if len(result) > 10 else 0

                # Create comment object from neomodel
                comment_uid = comment_data.get('uid')
                comment_node = Comment.nodes.get(uid=comment_uid)

                # Get post object from neomodel for full PostType data
                post_object = None
                if post_data:
                    try:
                        post_uid_from_data = post_data.get('uid')
                        post_node = Post.nodes.get(uid=post_uid_from_data)
                        post_object = PostType.from_neomodel(post_node, info)
                    except Exception as e:
                        print(f"Error getting post object: {e}")
                        # Fallback to the relationship-based approach
                        post_object = PostType.from_neomodel(comment_node.post.single(), info) if comment_node.post.single() else None

                # Create parent comment if this is a reply
                parent_comment = None
                if parent_comment_data and include_replies:
                    parent_uid = parent_comment_data.get('uid')
                    if parent_uid not in comment_cache:
                        parent_node = Comment.nodes.get(uid=parent_uid)
                        parent_comment = CommentType(
                            uid=parent_node.uid,
                            post=post_object,  # Use the same post object
                            user=UserType.from_neomodel(parent_node.user.single()) if parent_node.user.single() else None,
                            content=parent_node.content,
                            timestamp=parent_node.timestamp,
                            is_deleted=parent_node.is_deleted,
                            score=2.0,  # Simplified for parent
                            views=0,
                            comments=0,
                            shares=0,
                            vibes=0,
                            # Nested fields
                            parent_comment=None,
                            replies=[],
                            reply_count=0,
                            depth_level=0,
                            is_reply=False
                        )
                        comment_cache[parent_uid] = parent_comment
                    else:
                        parent_comment = comment_cache[parent_uid]

                # Create CommentType with metrics from Cypher (PRESERVE YOUR EXISTING STRUCTURE)
                enhanced_comment = CommentType(
                    uid=comment_node.uid,
                    post=post_object,  # Fixed: Use the post object from Cypher query
                    user=UserType.from_neomodel(comment_node.user.single()) if comment_node.user.single() else None,
                    content=comment_node.content,
                    timestamp=comment_node.timestamp,
                    is_deleted=comment_node.is_deleted,
                    score=float(calculated_score) if calculated_score is not None else 2.0,
                    views=int(views_count) if views_count is not None else 0,
                    comments=int(comments_count) if comments_count is not None else 0,
                    shares=int(shares_count) if shares_count is not None else 0,
                    vibes=int(vibes_count) if vibes_count is not None else 0,
                    
                    # NEW: Add nested comment fields
                    parent_comment=parent_comment,
                    replies=[],  # Will be populated in a second pass
                    reply_count=int(reply_count) if reply_count is not None else 0,
                    depth_level=1 if is_reply else 0,
                    is_reply=bool(is_reply)
                )

                enhanced_comments.append(enhanced_comment)
                comment_cache[comment_uid] = enhanced_comment

            # Second pass: Build nested structure if including replies
            if include_replies and max_depth > 1:
                # Organize comments into nested structure
                top_level_comments = []
                for comment in enhanced_comments:
                    if not comment.is_reply:
                        top_level_comments.append(comment)
                    else:
                        # Find parent and add this as a reply
                        parent_uid = comment.parent_comment.uid if comment.parent_comment else None
                        if parent_uid and parent_uid in comment_cache:
                            parent = comment_cache[parent_uid]
                            if parent.replies is None:
                                parent.replies = []
                            parent.replies.append(comment)

                return top_level_comments
            else:
                # Return all comments (flat structure) or just top-level
                return [c for c in enhanced_comments if not c.is_reply] if not include_replies else enhanced_comments

        except Exception as e:
            print(f"Error in resolve_postcomments_by_post_uid: {e}")
            return []       
    comment_replies = graphene.List(
        CommentType,
        comment_uid=graphene.String(required=True),
        max_depth=graphene.Int(default_value=2)
    )    


    @handle_graphql_post_errors
    @login_required
    def resolve_comment_replies(self, info, comment_uid, max_depth=2):
        """
        NEW: Get replies for a specific comment with metrics.
        """
        try:
            params = {"parent_comment_uid": comment_uid}
            results, _ = db.cypher_query(
                post_queries.comment_replies_with_metrics_query, params)

            if not results:
                return []

            replies = []
            for result in results:
                reply_data = result[0]
                vibes_count = result[1] if len(result) > 1 else 0
                views_count = result[2] if len(result) > 2 else 0
                comments_count = result[3] if len(result) > 3 else 0
                shares_count = result[4] if len(result) > 4 else 0
                likes_count = result[5] if len(result) > 5 else 0
                calculated_score = result[6] if len(result) > 6 else 2.0
                reply_count = result[7] if len(result) > 7 else 0

                # Create reply object from neomodel
                reply_uid = reply_data.get('uid')
                reply_node = Comment.nodes.get(uid=reply_uid)

                # Get parent comment for context
                parent_comment = None
                try:
                    parent_node = Comment.nodes.get(uid=comment_uid)
                    parent_comment = CommentType(
                        uid=parent_node.uid,
                        post=None,  # Simplified for performance
                        user=UserType.from_neomodel(parent_node.user.single()) if parent_node.user.single() else None,
                        content=parent_node.content,
                        timestamp=parent_node.timestamp,
                        is_deleted=parent_node.is_deleted,
                        score=2.0,
                        views=0,
                        comments=0,
                        shares=0,
                        vibes=0,
                        parent_comment=None,
                        replies=[],
                        reply_count=0,
                        depth_level=0,
                        is_reply=False
                    )
                except:
                    pass

                # Create reply with metrics
                reply = CommentType(
                    uid=reply_node.uid,
                    post=PostType.from_neomodel(reply_node.post.single(), info) if reply_node.post.single() else None,
                    user=UserType.from_neomodel(reply_node.user.single()) if reply_node.user.single() else None,
                    content=reply_node.content,
                    timestamp=reply_node.timestamp,
                    is_deleted=reply_node.is_deleted,
                    score=float(calculated_score) if calculated_score is not None else 2.0,
                    views=int(views_count) if views_count is not None else 0,
                    comments=int(comments_count) if comments_count is not None else 0,
                    shares=int(shares_count) if shares_count is not None else 0,
                    vibes=int(vibes_count) if vibes_count is not None else 0,
                    
                    # Nested fields
                    parent_comment=parent_comment,
                    replies=[],  # Can be expanded recursively if needed
                    reply_count=int(reply_count) if reply_count is not None else 0,
                    depth_level=1,
                    is_reply=True
                )

                replies.append(reply)

            return replies

        except Exception as e:
            print(f"Error in resolve_comment_replies: {e}")
            return [] 
  
    # except Exception as e:
    #     print(f"Error in resolve_postcomments_by_post_uid: {e}")
    #     return []

    # My Tags
    my_postcomment = graphene.List(CommentType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_postcomments(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_posts = user_node.post.all()
        comments = []
        for post in my_posts:
            comments.extend(list(post.comment))
        return [CommentType.from_neomodel(x) for x in comments]

    all_postreviews = graphene.List(ReviewType)

    @login_required
    @superuser_required
    def resolve_all_postreviews(self, info):
        return [ReviewType.from_neomodel(review) for review in Review.nodes.all()]

    # Tag Queries by Post
    postreviews_by_post_uid = graphene.List(
        CommentType, post_uid=graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_postreviews_by_post_uid(self, info, post_uid):
        post_node = Post.nodes.get(uid=post_uid)
        review = list(post_node.review.all())
        return [ReviewType.from_neomodel(review) for review in review]

    # My Tags
    my_postreview = graphene.List(ReviewType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_postreview(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_posts = user_node.post.all()
        reviews = []
        for post in my_posts:
            reviews.extend(list(post.review))
        return [ReviewType.from_neomodel(x) for x in reviews]

    all_postview = graphene.List(PostViewType)

    @login_required
    @superuser_required
    def resolve_all_postview(self, info):
        return [PostViewType.from_neomodel(view) for view in PostView.nodes.all()]

    postview_byuid = graphene.List(
        PostViewType, post_uid=graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_postview_byuid(self, info, post_uid):
        post_node = Post.nodes.get(uid=post_uid)
        postview = list(post_node.view.all())
        return [PostViewType.from_neomodel(view) for view in postview]

    my_post_views = graphene.List(PostViewType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post_views(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_posts = user_node.post.all()
        views = []
        for post in my_posts:
            views.extend(list(post.view))
        return [PostViewType.from_neomodel(x) for x in views]

    all_postshare = graphene.List(PostShareType)

    @superuser_required
    @login_required
    def resolve_all_postshare(self, info):
        return [PostShareType.from_neomodel(share) for share in PostShare.nodes.all()]

    postshare_byuid = graphene.List(
        PostShareType, post_uid=graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_postshare_byuid(self, info, post_uid):
        post_node = Post.nodes.get(uid=post_uid)
        postshare = list(post_node.postshare.all())
        return [PostShareType.from_neomodel(share) for share in postshare]

    my_post_shares = graphene.List(PostShareType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post_shares(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_posts = user_node.post.all()
        shares = []
        for post in my_posts:
            shares.extend(list(post.postshare))
        return [PostShareType.from_neomodel(x) for x in shares]

    all_postpined = graphene.List(PinedPostType)

    @superuser_required
    @login_required
    def resolve_all_postpined(self, info):
        return [PinedPostType.from_neomodel(pined, info) for pined in PinedPost.nodes.all()]

    postpined_byuid = graphene.List(PinedPostType, post_uid=graphene.String())

    @handle_graphql_post_errors
    @login_required
    def resolve_postshare_byuid(self, info, post_uid):
        post_node = Post.nodes.get(uid=post_uid)
        pinpost = list(post_node.pinpost.all())
        return [PinedPostType.from_neomodel(pined, info) for pined in pinpost]

    my_post_pined = graphene.List(PinedPostType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post_pined(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_posts = user_node.post.all()
        pined = []
        for post in my_posts:
            pined.extend(list(post.postpin))
        return [PinedPostType.from_neomodel(x) for x in pined]

    all_savedpost = graphene.List(SavedPostType)

    @superuser_required
    @login_required
    def resolve_all_savedpost(self, info):
        return [SavedPostType.from_neomodel(saved) for saved in SavedPost.nodes.all()]

    savedpost_byuid = graphene.List(
        SavedPostType, post_uid=graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_savedpost_byuid(self, info, post_uid):
        post_node = Post.nodes.get(uid=post_uid)
        savedpost = list(post_node.postsave.all())
        return [SavedPostType.from_neomodel(x) for x in savedpost]

    my_post_saved = graphene.List(SavedPostType)

    @handle_graphql_post_errors
    @login_required
    def resolve_my_post_saved(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_posts = user_node.post.all()
        saved = []
        for post in my_posts:
            saved.extend(list(post.postsave))
        return [SavedPostType.from_neomodel(x) for x in saved]

    # Optimisation and review required for this query
    my_feed = graphene.List(FeedType, circle_type=CircleTypeEnum())

    @handle_graphql_post_errors
    @login_required
    def resolve_my_feed(self, info, circle_type=None):
        payload = info.context.payload
        user_id = payload.get('user_id')
        log_in_user_node = Users.nodes.get(user_id=user_id)

        # Get blocked users and their IDs
        blocked_users = users.get_blocked_users(user_id)
        blocked_user_ids = {user['user_id'] for user in blocked_users}

        # Fetch all posts
        all_posts = Post.nodes.all()

        # Filter posts based on two conditions:
        # 1. The post should not be created by a blocked user.
        # 2. The post should not be created by the logged-in user.
        filtered_posts = filter(
            lambda post: (
                post.created_by.single().user_id not in blocked_user_ids and
                post.created_by.single().user_id != str(
                    user_id)  # Exclude posts by logged-in user
            ),
            all_posts
        )
        # Reverse the list of filtered posts to get the latest posts first
        reversed_posts = list(filtered_posts)[::-1]

        # print("Reversed Posts:", reversed_posts)  # Add this line for debugging
        result_feed = []
        feed_count = 0
        user_has_connection = False
        for post_data in reversed_posts:
            if feed_count >= 100:
                break  # Stop processing if we've reached the limit
            post_user = post_data.created_by.single()  # The user who created the post

            # Query the connection and circle using Cypher
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

            # print(results)
            if results and results[0]:
                user_has_connection = True
                connection_node = results[0][0][0]
                circle_node = results[0][0][1]
                original_circle_type = circle_node.get('circle_type')
                if circle_type is None or original_circle_type == circle_type.value:
                    # If no circle_type is selected, or the circle_type matches, include the post
                    result_feed.append(FeedType.from_neomodel(
                        post_data, connection_node, circle_node, log_in_user_node))

            else:
                if circle_type is None:
                    result_feed.append(FeedType.from_neomodel(
                        post_data, connection_node=None, circle_node=None, log_in_user_node=log_in_user_node))

        if not user_has_connection and circle_type is not None:
            return []
        return result_feed

    post_by_userid = graphene.List(
        PostType, user_id=graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_post_by_userid(self, info, user_id):

        user_node = Users.nodes.get(user_id=user_id)

        my_post = list(user_node.post.all())
        my_posts = [post for post in my_post if not post.is_deleted]

        return [PostType.from_neomodel(post, info) for post in my_posts]

    # This is optimised feed
    # my_feed_test = graphene.List(FeedTestType,circle_type=CircleTypeEnum())
    # @login_required
    # def resolve_my_feed_test(self, info, circle_type=None):
    #     payload = info.context.payload
    #     user_id = payload.get('user_id')

    #     params = {
    #             "log_in_user_node_id": str(user_id)  # ID of the logged-in user
    #         }

    #     # Execute the query
    #     results, _ = db.cypher_query(post_queries.post_feed_query, params)

    #     result_feed = []
    #     user_has_connection = False

    #     PostReactionUtils.initialize_map(results)
    #     IndividualVibeManager.store_data()  # Fetches and stores data

    #     file_ids = []

    #     for post in results:
    #         post_data=post[0]
    #         file_id=post_data.get('post_file_id')
    #         if file_id:
    #             for id in file_id:
    #                 if id:
    #                     file_ids.append(id)

    #     # for file_id in file_ids:
    #     #     print(file_id)  # Print each file\_id

    #     FileURL.store_file_urls(file_ids)

    #     for post in results:

    #         post_node = post[0]if post[0]else None
    #         connection=post[4] if post[4] else None
    #         likes = post[3] if post[3] else None # Likes are the third element in each tuple
    #         user_node=post[1]if post[1] else None

    #         circle=post[5] if post[5] else None
    #         profile_node=post[2] if post[2] else None
    #         share_count = post[6] if len(post) > 6 and post[6] is not None else 0
    #         calculated_overall_score = post[7] if len(post) > 7 and post[7] is not None else 2.0

    #         if connection is not None:
    #             user_has_connection = True

    #         # profile_uid=profile_node["uid"]
    #         # profile=Profile.nodes.get(uid=profile_uid)

    #         original_circle_type = circle.get('circle_type') if circle else None

    #         # Append for all posts if no circle_type is selected or its value is null
    #         if circle_type is None or original_circle_type == circle_type.value:
    #             result_feed.append(FeedTestType.from_neomodel(post_node,likes,connection,circle,user_node,profile_node,share_count,calculated_overall_score))

    #         # each_end_time = time.time()  # Record the end time

    #         # each_processing_time = each_end_time - each_start_time  # Calculate the total processing time
    #         # print(f"Processing Time: {each_processing_time:.4f} seconds")

    #     if not user_has_connection:
    #         if circle_type is not None:
    #             return []  # No feed if a circle type is selected but no connections

    #     return result_feed
    my_feed_test = graphene.List(FeedTestType, circle_type=CircleTypeEnum(), first=graphene.Int(default_value=20), after=graphene.String())


    @handle_graphql_post_errors
    @login_required
    @monitor_feed_performance
    def resolve_my_feed_test(self, info, circle_type=None, first=20, after=None):
        """
        Working pagination that provides all required parameters to existing query.
        """
        import base64
        start_time = time.time()

        try:
            # Extract user context
            payload = info.context.payload
            user_id = payload.get('user_id')

            # Validate pagination parameters
            first = min(max(1, first), 50)
            logger.info(f"Generating feed for user {user_id}: first={first}, after={after}")

            # Parse cursor for timestamp-based pagination
            cursor_timestamp = None
            cursor_post_uid = None
            if after:
                try:
                    raw = str(after).strip()
                    if 'cursor' in raw:
                        import re
                        m = re.search(r'"?cursor"?\s*:\s*"([A-Za-z0-9_\-+/=]+)"', raw)
                        if m:
                            raw = m.group(1)
                    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
                        raw = raw[1:-1]
                    pad = (-len(raw)) % 4
                    if pad:
                        raw = raw + ('=' * pad)
                    decoded_cursor = base64.b64decode(raw.encode()).decode()
                    cursor_parts = decoded_cursor.split('_', 1)
                    if len(cursor_parts) == 2:
                        cursor_timestamp = cursor_parts[0]
                        cursor_post_uid = cursor_parts[1]
                        logger.info(f"Using cursor: timestamp={cursor_timestamp}, post_uid={cursor_post_uid}")
                    else:
                        logger.warning(f"Invalid cursor format after decode: {decoded_cursor}")
                except Exception as cursor_error:
                    logger.warning(f"Cursor parsing failed: {cursor_error}")
                    cursor_timestamp = None
                    cursor_post_uid = None

            # Validate algorithm requirements
            validation = validate_feed_algorithm_requirements(user_id)
            if not validation.get('algorithm_ready'):
                logger.warning(f"Algorithm not ready for user {user_id}")
                fallback_feed = get_appropriate_fallback_feed(
                    validation.get('user_category', 'unknown'),
                    user_id
                )
                if fallback_feed:
                    return fallback_feed[:first]  # Simple slice for fallback
                return []

            # Provide ALL required parameters to your existing query
            params = {
                "log_in_user_node_id": str(user_id),
                "cursor_timestamp": cursor_timestamp,  # Can be None for first page
                "cursor_post_uid": cursor_post_uid,    # Can be None for first page
                "limit": first * 2  # Get more posts to account for algorithm filtering
            }

            # Execute your existing query with all required parameters
            logger.debug("Executing post_feed_query with all parameters...")
            logger.info(f"Debug: About to query with cursor_timestamp={cursor_timestamp}")
            logger.info(f"Debug: Will show posts older than: {cursor_timestamp}")

            results, _ = db.cypher_query(post_queries.post_feed_query, params)

            if not results:
                logger.warning(f"No content found for user {user_id}")
                return []

            logger.info(f"Retrieved {len(results)} items from query")

            # Initialize utilities (your existing code)
            Query.initialize_feed_utilities(results)

            # Apply your existing algorithm
            algorithm_start = time.time()
            try:
                algorithmically_sorted_results = apply_feed_algorithm(
                    user_id=user_id,
                    raw_content=results,
                    circle_type=circle_type
                )
                algorithm_time = time.time() - algorithm_start
                logger.info(f"Algorithm completed in {algorithm_time:.3f}s")
            except Exception as algo_error:
                logger.error(f"Algorithm failed: {algo_error}")
                algorithmically_sorted_results = results
                algorithm_time = 0.0

            # Use your existing build_feed_response method
            result_feed = Query.build_feed_response(algorithmically_sorted_results, circle_type)

            # Limit to requested amount
            final_feed = result_feed[:first]

            # Add cursors using timestamp + uid format (matching your query expectations)
            for item in final_feed:
                if hasattr(item, 'uid'):
                    try:
                        # Find the real Unix timestamp from the original results
                        real_unix_timestamp = None
                        for result in algorithmically_sorted_results:
                            post_data = result[0] if result[0] else {}
                            if post_data.get('uid') == item.uid:
                                real_unix_timestamp = post_data.get('created_at')
                                break
                        # Use the Unix timestamp directly in cursor
                        if real_unix_timestamp:
                            cursor_data = f"{real_unix_timestamp}_{item.uid}"
                        else:
                            cursor_data = f"1000000000_{item.uid}"  # Very old Unix timestamp
                        item.cursor = base64.b64encode(cursor_data.encode()).decode()
                    except Exception as cursor_error:
                        logger.warning(f"Cursor generation failed for {item.uid}: {cursor_error}")
                        item.cursor = base64.b64encode(f"1000000000_{item.uid}".encode()).decode()
            # Validate feed quality
            if result_feed:
                quality_metrics = validate_feed_quality(result_feed)
                if quality_metrics['quality_score'] < 0.3:
                    logger.warning(f"Low quality feed detected for user {user_id}")

            # Log metrics
            total_time = time.time() - start_time
            log_feed_metrics(user_id, len(results), len(final_feed), algorithm_time, total_time)

            # Debug: check what we got from the query
            logger.info(f"Debug: Query returned {len(results)} results")
            if results:
                first_post = results[0][0] if results[0] and results[0][0] else {}
                logger.info(f"Debug: First post timestamp: {first_post.get('created_at')}, uid: {first_post.get('uid')}")
                logger.info(f"Debug: Cursor timestamp: {cursor_timestamp}, cursor_post_uid: {cursor_post_uid}")
                logger.info(f"Feed completed: {len(final_feed)} items in {total_time:.3f}s")
            return final_feed

        except Exception as e:
            logger.error(f"Error in my_feed_test: {e}")
            try:
                # Emergency fallback
                emergency_feed = get_appropriate_fallback_feed('unknown', user_id, limit=first)
                return emergency_feed[:first] if emergency_feed else []
            except Exception:
                return []
        

    @staticmethod
    def simple_sort_posts(results):
        """
        Simple sorting without complex algorithm - just by engagement and time.
        """
        # Sort by created_at (most recent first) and engagement score
        def sort_key(post):
            try:
                # Get created_at from post data
                post_data = post[0] if post[0] else {}
                created_at = post_data.get('created_at', 0)

                # Get engagement metrics
                share_count = post[6] if len(post) > 6 and post[6] is not None else 0
                overall_score = post[7] if len(post) > 7 and post[7] is not None else 2.0

                # Simple engagement calculation
                engagement = overall_score + (share_count * 0.1)

                # Return tuple for sorting: (engagement_desc, time_desc)
                return (-engagement, -created_at)
            except Exception:
                return (0, 0)

        try:
            sorted_results = sorted(results, key=sort_key)
            logger.info(f"Simple sort: {len(results)} -> {len(sorted_results)} items")
            return sorted_results
        except Exception as e:
            logger.error(f"Simple sorting failed: {e}")
            return results

    @staticmethod
    def build_feed_response_no_diversity(sorted_results, circle_type):
        """
        Build feed response WITHOUT diversity filtering to keep more posts.
        """
        result_feed = []
        user_has_connection = False

        for post in sorted_results:
            try:
                # Extract post components (your existing logic)
                post_node = post[0] if post[0] else None
                user_node = post[1] if len(post) > 1 and post[1] else None
                profile_node = post[2] if len(post) > 2 and post[2] else None
                likes = post[3] if len(post) > 3 and post[3] else None
                connection = post[4] if len(post) > 4 and post[4] else None
                circle = post[5] if len(post) > 5 and post[5] else None
                share_count = post[6] if len(post) > 6 and post[6] is not None else 0
                calculated_overall_score = post[7] if len(post) > 7 and post[7] is not None else 2.0

                if connection is not None:
                    user_has_connection = True

                # Circle type filtering (your existing logic)
                original_circle_type = None
                if circle:
                    if isinstance(circle, dict):
                        original_circle_type = circle.get('circle_type')
                    else:
                        original_circle_type = getattr(circle, 'circle_type', None)

                # Apply circle filter - simplified logic
                should_include_post = True
                if circle_type is not None:
                    # Only apply filter if circle_type is specified
                    if connection is None or not circle:
                        should_include_post = False
                    elif original_circle_type != circle_type.value:
                        should_include_post = False

                if should_include_post:
                    feed_item = FeedTestType.from_neomodel(
                        post_data=post_node,
                        reactions_nodes=likes,
                        connection_node=connection,
                        circle_node=circle,
                        user_node=user_node,
                        profile=profile_node,
                        query_share_count=share_count,
                        query_overall_score=calculated_overall_score
                    )
                    result_feed.append(feed_item)

            except Exception as item_error:
                logger.error(f"Error processing feed item: {item_error}")
                continue

        # Handle edge case for circle filter
        if not user_has_connection and circle_type is not None:
            logger.info(f"No connections found with circle filter {circle_type}")
            return []

        logger.info(f"Feed response built: {len(result_feed)} items (no diversity filter)")
        return result_feed

    @staticmethod
    def initialize_feed_utilities(results):
        """Initialize post reaction utilities and file processing."""
        PostReactionUtils.initialize_map(results)
        IndividualVibeManager.store_data()

        # Extract and store file URLs for optimization
        file_ids = []
        for post in results:
            post_data = post[0]
            file_id = post_data.get('post_file_id')
            if file_id:
                file_ids.extend([id for id in file_id if id])

        if file_ids:
            FileURL.store_file_urls(file_ids)
    
    @staticmethod
    def build_feed_response(sorted_results, circle_type):
        """Build the final feed response from sorted results."""

        result_feed = []
        user_has_connection = False

        for post in sorted_results:
            try:
                # Extract post components
                post_node = post[0] if post[0] else None
                user_node = post[1] if post[1] else None
                profile_node = post[2] if post[2] else None
                likes = post[3] if post[3] else None
                connection = post[4] if post[4] else None
                circle = post[5] if post[5] else None
                share_count = post[6] if len(
                    post) > 6 and post[6] is not None else 0
                calculated_overall_score = post[7] if len(
                    post) > 7 and post[7] is not None else 2.0

                # Track connection status
                if connection is not None:
                    user_has_connection = True

                # Extract circle type for filtering with proper handling
                original_circle_type = None
                if circle:
                    if isinstance(circle, dict):
                        original_circle_type = circle.get('circle_type')
                    else:
                        original_circle_type = getattr(circle, 'circle_type', None)

                # Apply circle type filtering
                should_include_post = False

                if circle_type is None:
                    # No filter - include all posts
                    should_include_post = True
                elif connection is not None and circle and original_circle_type:
                    # Only include posts from connections with matching circle type
                    if original_circle_type == circle_type.value:
                        should_include_post = True

                if should_include_post:
                    feed_item = FeedTestType.from_neomodel(
                        post_data=post_node,
                        reactions_nodes=likes,
                        connection_node=connection,
                        circle_node=circle,
                        user_node=user_node,
                        profile=profile_node,
                        query_share_count=share_count,
                        query_overall_score=calculated_overall_score
                    )
                    result_feed.append(feed_item)

            except Exception as item_error:
                logger.error(f"Error processing feed item: {item_error}")
                continue

        # Handle edge case: no connections with circle filter
        if not user_has_connection and circle_type is not None:
            logger.info(f"No connections found with circle filter {circle_type}")
            return []

        return result_feed

    @staticmethod
    def process_fallback_feed(fallback_results):
        """Process fallback feed results into proper format."""
        if not fallback_results:
            return []

        try:
            # Initialize utilities for fallback content
            Query.initialize_feed_utilities(fallback_results)

            # Build response using same logic
            return Query.build_feed_response(fallback_results, None)

        except Exception as e:
            logger.error(f"Error processing fallback feed: {e}")
            return []
    @staticmethod
    def process_emergency_fallback_feed(emergency_feed, user_id):
        """Process emergency fallback feed with full error handling."""
        if not emergency_feed:
            return []

        try:
            # Process emergency fallback directly
            Query.initialize_feed_utilities(emergency_feed)

            # Build emergency feed response
            emergency_result = []
            for post in emergency_feed:
                try:
                    post_node = post[0] if post[0] else None
                    user_node = post[1] if post[1] else None
                    profile_node = post[2] if post[2] else None
                    likes = post[3] if post[3] else None
                    connection = post[4] if post[4] else None
                    circle = post[5] if post[5] else None
                    share_count = post[6] if len(
                        post) > 6 and post[6] is not None else 0
                    calculated_overall_score = post[7] if len(
                        post) > 7 and post[7] is not None else 2.0

                    feed_item = FeedTestType.from_neomodel(
                        post_data=post_node,
                        reactions_nodes=likes,
                        connection_node=connection,
                        circle_node=circle,
                        user_node=user_node,
                        profile=profile_node,
                        query_share_count=share_count,
                        query_overall_score=calculated_overall_score
                    )
                    emergency_result.append(feed_item)
                except Exception as item_error:
                    logger.error(
                        f"Error processing emergency feed item: {item_error}")
                    continue

            return emergency_result
        except Exception as e:
            logger.error(
                f"Error processing emergency fallback feed for user {user_id}: {e}")
            return []
    recommended_post = graphene.List(PostCategoryType, search=graphene.String())

    @handle_graphql_post_errors
    @login_required
    def resolve_recommended_post(self, info, search=None):
        """
        Resolve recommended posts with optional search functionality.
        
        Args:
            search (str, optional): Search term to filter posts by postTitle and postText
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        details = ["Top Vibes - Meme", "Top Vibes - Podcasts", "Top Vibes - Videos", "Top Vibes - Music",
                   "Top Vibes - Articles", "Post From Connection", "Popular Post", "Recent Post"]
        return [PostCategoryType.from_neomodel(user_node, detail, search) for detail in details]


class QueryV2(graphene.ObjectType):
    # version2 api
    my_feed_test = graphene.List(
        FeedTestTypeV2, circle_type=CircleTypeEnumV2())

    @handle_graphql_post_errors
    @login_required
    def resolve_my_feed_test(self, info, circle_type=None):
        payload = info.context.payload
        user_id = payload.get('user_id')

        params = {
            "log_in_user_node_id": str(user_id)  # ID of the logged-in user
        }

        # Execute the query
        results, _ = db.cypher_query(post_queries.post_feed_queryV2, params)

        result_feed = []
        user_has_connection = False

        PostReactionUtils.initialize_map(results)
        IndividualVibeManager.store_data()  # Fetches and stores data

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

        for post in results:

            post_node = post[0]if post[0]else None
            connection = post[4] if post[4] else None
            # Likes are the third element in each tuple
            likes = post[3] if post[3] else None
            user_node = post[1]if post[1] else None

            circle = post[5] if post[5] else None
            profile_node = post[2] if post[2] else None

            if connection is not None:
                user_has_connection = True

            if circle:
                user_relations = json.loads(circle.get("user_relations", "{}"))
                original_circle_type = user_relations.get(
                    login_user_uid, {}).get("circle_type")
            else:
                original_circle_type = None
                user_relations = None

            # Append for all posts if no circle_type is selected or its value is null
            if circle_type is None or original_circle_type == circle_type.value:
                result_feed.append(FeedTestTypeV2.from_neomodel(
                    post_node, likes, connection, circle, user_node, profile_node, user_relations, login_user_uid))

        if not user_has_connection:
            if circle_type is not None:
                return []  # No feed if a circle type is selected but no connections

        return result_feed

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

    recommended_post = graphene.List(PostCategoryTypeV2)

    @handle_graphql_post_errors
    @login_required
    def resolve_recommended_post(self, info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            details = ["Top Vibes - Meme", "Top Vibes - Podcasts", "Top Vibes - Videos", "Top Vibes - Music",
                       "Top Vibes - Articles", "Post From Connection", "Popular Post", "Recent Post"]
            return [PostCategoryTypeV2.from_neomodel(user_node, detail) for detail in details]

        except Exception as e:
            raise Exception(e)
