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
from post.utils.feed_history import get_viewed_today, mark_viewed, get_hidden_today, get_muted_creators, get_creator_counts, increment_creator_counts
from post.utils.feed_selection import diversify, compose_with_quotas, creator_key, inject_exploration
from post.utils.ab_config import get_feed_config
from post.utils.trending import fetch_trending
from post.utils.interest_vectors import get_user_interest_vector
from .types import *
from auth_manager.models import Users, Profile
from post.models import *
from connection.models import Circle
from connection.graphql.types import CircleTypeEnum
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

    # Dedicated debate-by-uid (ensures post_type='debate')
    debate_by_uid = graphene.Field(PostType, debate_uid=graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_debate_by_uid(self, info, debate_uid):
        try:
            post = Post.nodes.get(uid=debate_uid)
            if post.is_deleted or getattr(post, 'post_type', '') != 'debate':
                return None
            return PostType.from_neomodel(post, info)
        except Post.DoesNotExist:
            return None

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

    my_feed = graphene.List(FeedTestType, circle_type=CircleTypeEnum(), first=graphene.Int(default_value=20), after=graphene.String())

    @handle_graphql_post_errors
    @login_required
    def resolve_my_feed(self, info, circle_type=None, first=20, after=None):
        payload = info.context.payload
        user_id = payload.get('user_id')
        try:
            first = min(max(1, int(first)), 50)
        except Exception:
            first = 20

        cursor_timestamp = None
        cursor_post_uid = None
        if after:
            try:
                raw = str(after).strip()
                if raw.startswith('{') and 'cursor' in raw:
                    import re
                    m = re.search(r'"cursor"\s*:\s*"([A-Za-z0-9_\-+/=]+)"', raw)
                    if m:
                        raw = m.group(1)
                if raw.startswith('"') and raw.endswith('"'):
                    raw = raw[1:-1]
                pad = (-len(raw)) % 4
                if pad:
                    raw = raw + ('=' * pad)
                decoded = base64.b64decode(raw.encode()).decode()
                parts = decoded.split('_', 1)
                if len(parts) == 2:
                    ts = parts[0]
                    cursor_post_uid = parts[1]
                    try:
                        cursor_timestamp = float(ts)
                    except Exception:
                        try:
                            from datetime import datetime
                            tsc = ts.replace('Z', '')
                            dt = None
                            try:
                                dt = datetime.fromisoformat(tsc)
                            except Exception:
                                try:
                                    dt = datetime.strptime(tsc, "%Y-%m-%dT%H:%M:%S.%f")
                                except Exception:
                                    dt = datetime.strptime(tsc, "%Y-%m-%dT%H:%M:%S")
                            cursor_timestamp = dt.timestamp() if dt else None
                        except Exception:
                            cursor_timestamp = None
            except Exception:
                cursor_timestamp = None
                cursor_post_uid = None

        params = {
            "log_in_user_node_id": str(user_id),
            "cursor_timestamp": cursor_timestamp,
            "cursor_post_uid": cursor_post_uid,
            "limit": first * 3
        }

        results, _ = db.cypher_query(post_queries.post_feed_query, params)
        interests = get_user_interest_vector(str(user_id))
        print("feed_interests", user_id, sorted(interests.get('post_types', {}).items(), key=lambda x: x[1], reverse=True)[:3])

        viewed = get_viewed_today(str(user_id))
        hidden = get_hidden_today(str(user_id))
        muted = get_muted_creators(str(user_id))

        def get_blocked_creators(u_id: str):
            try:
                q = (
                    "MATCH (me:Users {user_id: $uid})-[:HAS_BLOCK]->(b:Block)-[:BLOCKED]->(u:Users) "
                    "RETURN u.uid"
                )
                res, _ = db.cypher_query(q, {"uid": str(u_id)})
                return set([row[0] for row in res if row and row[0]])
            except Exception:
                return set()

        blocked = get_blocked_creators(user_id)
        print("feed_filters", user_id, len(viewed), len(hidden), len(muted), len(blocked), len(results))
        filtered = []
        for r in results:
            pd = r[0] if r else {}
            puid = None
            if isinstance(pd, dict):
                puid = pd.get('uid') or pd.get('post_uid')
            else:
                puid = getattr(pd, 'uid', None) or getattr(pd, 'post_uid', None)
            ck = creator_key(r)
            allow = ck not in muted and ck not in blocked
            if puid and (puid in viewed or puid in hidden):
                allow = False
            if allow:
                filtered.append(r)

        if len(filtered) < max(5, first // 2):
            seen = set()
            loose = []
            for r in results:
                pd = r[0] if r else {}
                puid = None
                if isinstance(pd, dict):
                    puid = pd.get('uid') or pd.get('post_uid')
                else:
                    puid = getattr(pd, 'uid', None) or getattr(pd, 'post_uid', None)
                ck = creator_key(r)
                if ck in muted or ck in blocked:
                    continue
                if puid and puid in seen:
                    continue
                loose.append(r)
                if puid:
                    seen.add(puid)
                if len(loose) >= first:
                    break
            filtered = loose

        def circle_weight(c):
            try:
                t = None
                if isinstance(c, dict):
                    t = c.get('circle_type')
                else:
                    t = getattr(c, 'circle_type', None)
                wmap = {
                    'family': 1.0,
                    'close': 0.8,
                    'friends': 0.6,
                    'acquaintance': 0.3
                }
                return wmap.get(str(t).lower(), 0.2) if t else 0.2
            except Exception:
                return 0.2

        def final_score(row):
            try:
                post_data = row[0] if row else {}
                circle = row[5] if len(row) > 5 else None
                overall = row[7] if len(row) > 7 and row[7] is not None else 2.0
                created = row[8] if len(row) > 8 and row[8] is not None else post_data.get('created_at', 0)
                import time as _t
                import random as _rand
                age_h = max(0.0, (_t.time() - float(created)) / 3600.0) if created else 0.0
                recency = 0.25 if age_h < 24 else (0.1 if age_h < 72 else 0.0)
                cboost = circle_weight(circle)
                jitter = _rand.uniform(-0.03, 0.03)
                iboost = 0.0
                try:
                    pt = post_data.get('post_type', '')
                    if pt:
                        iboost += float(interests.get('post_types', {}).get(pt, 0.0)) * 0.4
                    tags = post_data.get('tags') or []
                    if isinstance(tags, list) and tags:
                        s = 0.0
                        for t in tags:
                            if t:
                                s += float(interests.get('tags', {}).get(str(t).lower(), 0.0))
                                if s >= 2.0:
                                    break
                        iboost += min(s * 0.1, 0.4)
                except Exception:
                    iboost = 0.0
                return overall + recency + cboost + iboost + jitter
            except Exception:
                return 2.0

        scored = sorted(filtered, key=final_score, reverse=True)
        cfg = get_feed_config(str(user_id))
        session_counts = get_creator_counts(str(user_id))
        selected = compose_with_quotas(
            scored,
            first,
            connected_ratio=cfg.get('connected_ratio', 0.6),
            max_per_creator=cfg.get('creator_cap', 2),
            session_counts=session_counts,
            session_limit=cfg.get('session_limit', 5)
        )
        print("feed_selection", user_id, len(filtered), len(selected), len(session_counts))

        exploration_count = max(1, int(first * cfg.get('exploration_ratio', 0.2)))
        if exploration_count > 0:
            exclude_uids = set()
            for r in selected:
                pd = r[0] if r else {}
                uid = pd.get('uid') if isinstance(pd, dict) else getattr(pd, 'uid', None)
                if uid:
                    exclude_uids.add(uid)
            trending_rows = fetch_trending(max(exploration_count * 2, 5), exclude_uids)
            safe_trending = []
            for r in trending_rows:
                pd = r[0] if r else {}
                puid = None
                if isinstance(pd, dict):
                    puid = pd.get('uid') or pd.get('post_uid')
                else:
                    puid = getattr(pd, 'uid', None) or getattr(pd, 'post_uid', None)
                ck2 = creator_key(r)
                allow2 = ck2 not in muted and ck2 not in blocked
                if puid and (puid in viewed or puid in hidden) and len(selected) >= 10:
                    allow2 = False
                if allow2:
                    safe_trending.append(r)
            selected = inject_exploration(selected, safe_trending, exploration_count)

        if len(selected) < first:
            extra_needed = first - len(selected)
            exclude_uids2 = set()
            for r in selected:
                pd = r[0] if r else {}
                uid2 = pd.get('uid') if isinstance(pd, dict) else getattr(pd, 'uid', None)
                if uid2:
                    exclude_uids2.add(uid2)
            more_trending = fetch_trending(max(extra_needed * 2, 10), exclude_uids2)
            safe_more = []
            for r in more_trending:
                pd = r[0] if r else {}
                puid = None
                if isinstance(pd, dict):
                    puid = pd.get('uid') or pd.get('post_uid')
                else:
                    puid = getattr(pd, 'uid', None) or getattr(pd, 'post_uid', None)
                ck3 = creator_key(r)
                allow3 = ck3 not in muted and ck3 not in blocked
                if puid and (puid in viewed or puid in hidden) and len(selected) >= 10:
                    allow3 = False
                if allow3:
                    safe_more.append(r)
            selected = inject_exploration(selected, safe_more, extra_needed)

        if len(selected) < first:
            try:
                category = 'new_user' if not interests.get('post_types') else 'unknown'
                need = first - len(selected)
                fallback_rows = get_appropriate_fallback_feed(category, str(user_id), limit=max(need * 3, 10))
                added = []
                used_uids = set()
                for r in selected:
                    pd = r[0] if r else {}
                    puid0 = pd.get('uid') if isinstance(pd, dict) else getattr(pd, 'uid', None)
                    if puid0:
                        used_uids.add(puid0)
                # Prefer non-duplicates
                for r in fallback_rows:
                    if len(added) >= need:
                        break
                    pd = r[0] if r else {}
                    puid = None
                    if isinstance(pd, dict):
                        puid = pd.get('uid') or pd.get('post_uid')
                    else:
                        puid = getattr(pd, 'uid', None) or getattr(pd, 'post_uid', None)
                    if puid and puid not in used_uids:
                        added.append(r)
                        used_uids.add(puid)
                # Emergency fill: allow soft duplicates if still short
                if len(added) < need:
                    for r in fallback_rows:
                        if len(added) >= need:
                            break
                        pd = r[0] if r else {}
                        puid = None
                        if isinstance(pd, dict):
                            puid = pd.get('uid') or pd.get('post_uid')
                        else:
                            puid = getattr(pd, 'uid', None) or getattr(pd, 'post_uid', None)
                        # Allow duplicate only when current feed is very short
                        if puid and len(selected) + len(added) < 10:
                            added.append(r)
                selected += added
                print("feed_fallback", user_id, category, len(added))
            except Exception:
                pass

        try:
            PostReactionUtils.initialize_map(selected)
            IndividualVibeManager.store_data()
            fids = []
            for r in selected:
                pd = r[0] if r else {}
                ids = pd.get('post_file_id')
                if ids:
                    for i in ids:
                        if i:
                            fids.append(i)
            if fids:
                FileURL.store_file_urls(fids)
        except Exception:
            pass

        feed_items = []
        for row in selected:
            try:
                post_node = row[0] if row[0] else None
                user_node = row[1] if len(row) > 1 else None
                profile_node = row[2] if len(row) > 2 else None
                reactions = row[3] if len(row) > 3 else None
                connection = row[4] if len(row) > 4 else None
                circle = row[5] if len(row) > 5 else None
                share_count = row[6] if len(row) > 6 and row[6] is not None else 0
                overall_score = row[7] if len(row) > 7 and row[7] is not None else 2.0
                post_data = post_node

                include = True
                if circle_type is not None:
                    original = None
                    if circle:
                        if isinstance(circle, dict):
                            original = circle.get('circle_type')
                        else:
                            original = getattr(circle, 'circle_type', None)
                    val = getattr(circle_type, 'value', None)
                    if val == 'Universe':
                        include = (connection is None)
                    else:
                        include = bool(connection and circle and original == val)

                if include:
                    item = FeedTestType.from_neomodel(
                        post_data=post_data,
                        reactions_nodes=reactions,
                        connection_node=connection,
                        circle_node=circle,
                        user_node=user_node,
                        profile=profile_node,
                        query_share_count=share_count,
                        query_overall_score=overall_score
                    )
                    if item is not None:
                        feed_items.append(item)
            except Exception:
                continue

        try:
            mark_viewed(str(user_id), [x.uid for x in feed_items if hasattr(x, 'uid')])
            for r in selected:
                increment_creator_counts(str(user_id), creator_key(r), 1)
        except Exception:
            pass

        print("feed_return", user_id, len(feed_items))
        return feed_items

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
        
    post_vibes_analytics = graphene.Field(
        PostVibesAnalyticsType,
        post_uid=graphene.String(required=True),
        vibe_filter=graphene.String(),  # Filter by specific vibe name
        limit=graphene.Int(default_value=20),
        offset=graphene.Int(default_value=0)
    )

    @handle_graphql_post_errors
    @login_required
    def resolve_post_vibes_analytics(self, info, post_uid, vibe_filter=None, limit=20, offset=0):
        try:
            # Try to find regular post first, fallback to community post
            try:
                post_node = Post.nodes.get(uid=post_uid)
            except Post.DoesNotExist:
                post_node = CommunityPost.nodes.get(uid=post_uid)
            
            if post_node.is_deleted:
                return None

            # Get aggregated vibe analytics
            post_reaction_manager = PostReactionManager.objects.filter(post_uid=post_uid).first()
            
            # Get all likes for this post
            all_likes = list(post_node.like.all())
            active_likes = [like for like in all_likes if not like.is_deleted]
            
            total_vibers = len(active_likes)
            overall_average_vibe = sum(like.vibe for like in active_likes) / total_vibers if total_vibers > 0 else 0
            
            # Get top vibes data
            if post_reaction_manager:
                all_reactions = post_reaction_manager.post_vibe
                # Sort by count first, then by average score
                sorted_reactions = sorted(
                    all_reactions, 
                    key=lambda x: (x.get('vibes_count', 0), x.get('cumulative_vibe_score', 0)), 
                    reverse=True
                )
                top_vibes = [VibeDetailType.from_neomodel(vibe) for vibe in sorted_reactions[:10]]
            else:
                # Fallback to default vibes if no manager exists
                default_vibes = IndividualVibe.objects.all()[:10]
                top_vibes = [VibeDetailType.from_neomodel(vibe) for vibe in default_vibes]
            
            # Filter users by vibe if specified
            if vibe_filter:
                filtered_likes = [like for like in active_likes if like.reaction == vibe_filter]
            else:
                filtered_likes = active_likes
            
            # Sort users by timestamp (most recent first)
            sorted_likes = sorted(filtered_likes, key=lambda x: x.timestamp, reverse=True)
            
            # Apply pagination
            paginated_likes = sorted_likes[offset:offset + limit]
            total_users_count = len(filtered_likes)
            has_more_users = (offset + limit) < total_users_count
            
            vibed_users = [VibeUserType.from_neomodel(like) for like in paginated_likes]
            
            return PostVibesAnalyticsType(
                post_uid=post_uid,
                total_vibers=total_vibers,
                overall_average_vibe=round(overall_average_vibe, 2),
                top_vibes=top_vibes,
                vibed_users=vibed_users,
                has_more_users=has_more_users,
                total_users_count=total_users_count
            )
            
        except Exception as error:
            logger.error(f"Error in resolve_post_vibes_analytics: {str(error)}")
            raise Exception(f"Failed to fetch post vibes analytics: {str(error)}")    

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
        include_replies=graphene.Boolean(default_value=True), 
        max_depth=graphene.Int(default_value=2),
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0)
    )

    @handle_graphql_post_errors
    @login_required
    def resolve_postcomments_by_post_uid(self, info, post_uid, include_replies=True, max_depth=2, limit=10, offset=0):
        """
        UPDATED: Your existing resolver with nested comment support and pagination.
        Includes media interaction tracking for comments with media files.
        """
        try:
            print(f"DEBUG: Querying post_uid: {post_uid}")
            print(f"DEBUG: include_replies: {include_replies}, limit: {limit}, offset: {offset}")
            
            # Add pagination parameters
            params = {
                "post_uid": post_uid,
                "limit": limit,
                "offset": offset
            }
            
            if include_replies:
                print(f"DEBUG: Running nested query with params: {params}")
                results, _ = db.cypher_query(
                    post_queries.post_comments_with_metrics_nested_query, params)
                print(f"DEBUG: Query results length: {len(results) if results else 0}")
            else:
                results, _ = db.cypher_query(
                    post_queries.top_level_comments_with_metrics_query, params)

            # Initialize variables for media tracking BEFORE checking results
            current_user = info.context.user
            activity_service = None
            ip_address = None
            user_agent = None
            
            if current_user and current_user.is_authenticated:
                try:
                    from user_activity.services.activity_service import ActivityService
                    request = info.context
                    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] if request.META.get('HTTP_X_FORWARDED_FOR') else request.META.get('REMOTE_ADDR')
                    user_agent = request.META.get('HTTP_USER_AGENT', '')
                    activity_service = ActivityService()
                except Exception as e:
                    logger.error(f"Failed to initialize activity service for media tracking: {e}")

            # Track the interaction even if no comments are returned
            if activity_service and current_user and current_user.is_authenticated:
                try:
                    activity_service.track_media_interaction(
                        user=current_user,
                        media_type='comment_media',
                        media_id=post_uid,
                        interaction_type='view',
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata={
                            'post_uid': post_uid,
                            'include_replies': include_replies,
                            'query_type': 'postcomments_by_post_uid',
                            'limit': limit,
                            'offset': offset,
                            'comments_found': len(results) if results else 0,
                            'empty_result': not bool(results)
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to track post comment media interaction: {e}")

            if not results:
                return []

            enhanced_comments = []
            comment_cache = {} 

            for result in results:
                comment_data = result[0]
                parent_comment_data = result[1] if len(result) > 1 and result[1] else None
                post_data = result[2] if len(result) > 2 and result[2] else None
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
                       try:
                           post_node = Post.nodes.get(uid=post_uid_from_data)
                           post_object = PostType.from_neomodel(post_node, info)
                       except Post.DoesNotExist:
                           from community.models import CommunityPost
                           post_node = CommunityPost.nodes.get(uid=post_uid_from_data)
                           post_object = None
                   except Exception as e:
                      print(f"Error getting post object: {e}")
                      post_object = None

                # Create parent comment if this is a reply
                parent_comment = None
                if parent_comment_data and include_replies:
                    parent_uid = parent_comment_data.get('uid')
                    if parent_uid not in comment_cache:
                        parent_node = Comment.nodes.get(uid=parent_uid)
                        
                        # Fetch vibe reactions for parent comment
                        parent_vibe_reactions = []
                        try:
                            if hasattr(parent_node, 'vibe_reactions'):
                                vibe_reaction_nodes = list(parent_node.vibe_reactions.all())
                                active_vibes = [vr for vr in vibe_reaction_nodes if vr.is_active]
                                active_vibes.sort(key=lambda x: x.timestamp, reverse=True)
                                parent_vibe_reactions = [CommentVibeType.from_neomodel(vr) for vr in active_vibes]
                        except Exception as e:
                            print(f"Error fetching parent vibe reactions: {e}")
                            parent_vibe_reactions = []
                        
                        parent_comment = CommentType(
                            uid=parent_node.uid,
                            post=post_object,
                            user=UserType.from_neomodel(parent_node.user.single()) if parent_node.user.single() else None,
                            content=parent_node.content,
                            timestamp=parent_node.timestamp,
                            is_deleted=parent_node.is_deleted,
                            score=2.0,
                            views=0,
                            comments=0,
                            shares=0,
                            vibes=0,
                            comment_file_id=getattr(parent_node, 'comment_file_id', []) or [],
                            comment_file_url=[],
                            parent_comment=None,
                            replies=[],
                            reply_count=0,
                            depth_level=0,
                            is_reply=False,
                            vibe_reactions=parent_vibe_reactions
                        )
                        comment_cache[parent_uid] = parent_comment
                    else:
                        parent_comment = comment_cache[parent_uid]

                # Fetch vibe reactions for this comment
                comment_vibe_reactions = []
                try:
                    print(f"DEBUG: Fetching vibe reactions for comment {comment_node.uid}")
                    if hasattr(comment_node, 'vibe_reactions'):
                        vibe_reaction_nodes = list(comment_node.vibe_reactions.all())
                        print(f"DEBUG: Found {len(vibe_reaction_nodes)} vibe reaction nodes")
                        active_vibes = [vr for vr in vibe_reaction_nodes if vr.is_active]
                        print(f"DEBUG: Found {len(active_vibes)} active vibe reactions")
                        active_vibes.sort(key=lambda x: x.timestamp, reverse=True)
                        comment_vibe_reactions = [CommentVibeType.from_neomodel(vr) for vr in active_vibes]
                        print(f"DEBUG: Created {len(comment_vibe_reactions)} CommentVibeType objects")
                    else:
                        print(f"DEBUG: Comment {comment_node.uid} does not have vibe_reactions attribute")
                except Exception as e:
                    print(f"Error fetching comment vibe reactions: {e}")
                    comment_vibe_reactions = []

                # Track specific media interactions for comments with media files
                comment_file_ids = getattr(comment_node, 'comment_file_id', []) or []
                if comment_file_ids and activity_service and current_user and current_user.is_authenticated:
                    try:
                        # Track each media file in the comment
                        for file_id in comment_file_ids:
                            activity_service.track_media_interaction(
                                user=current_user,
                                media_type='image',  # Assuming most comment media are images
                                media_id=str(file_id),
                                interaction_type='view',
                                ip_address=ip_address,
                                user_agent=user_agent,
                                metadata={
                                    'comment_uid': comment_node.uid,
                                    'post_uid': post_uid,
                                    'comment_has_media': True,
                                    'media_count': len(comment_file_ids),
                                    'query_type': 'comment_media_view'
                                }
                            )
                    except Exception as e:
                        logger.error(f"Failed to track individual comment media interaction: {e}")

                # Create CommentType with metrics from Cypher
                enhanced_comment = CommentType(
                    uid=comment_node.uid,
                    post=post_object,
                    user=UserType.from_neomodel(comment_node.user.single()) if comment_node.user.single() else None,
                    content=comment_node.content,
                    timestamp=comment_node.timestamp,
                    is_deleted=comment_node.is_deleted,
                    score=float(calculated_score) if calculated_score is not None else 2.0,
                    views=int(views_count) if views_count is not None else 0,
                    comments=int(comments_count) if comments_count is not None else 0,
                    shares=int(shares_count) if shares_count is not None else 0,
                    vibes=int(vibes_count) if vibes_count is not None else 0,
                    comment_file_id=comment_file_ids,
                    comment_file_url=[],
                    parent_comment=parent_comment,
                    replies=[],
                    reply_count=int(reply_count) if reply_count is not None else 0,
                    depth_level=1 if is_reply else 0,
                    is_reply=bool(is_reply),
                    vibe_reactions=comment_vibe_reactions
                )

                enhanced_comments.append(enhanced_comment)
                comment_cache[comment_uid] = enhanced_comment

            # Second pass: Build nested structure if including replies
            if include_replies and max_depth > 1:
                top_level_comments = []
                for comment in enhanced_comments:
                    if not comment.is_reply:
                        top_level_comments.append(comment)
                    else:
                        parent_uid = comment.parent_comment.uid if comment.parent_comment else None
                        if parent_uid and parent_uid in comment_cache:
                            parent = comment_cache[parent_uid]
                            if parent.replies is None:
                                parent.replies = []
                            parent.replies.append(comment)

                return top_level_comments
            else:
                return [c for c in enhanced_comments if not c.is_reply] if not include_replies else enhanced_comments

        except Exception as e:
            print(f"Error in resolve_postcomments_by_post_uid: {e}")
            return []    
    debate_answers_by_post_uid = graphene.List(CommentType, post_uid=graphene.String(required=True))

    @handle_graphql_post_errors
    @login_required
    def resolve_debate_answers_by_post_uid(self, info, post_uid):
        try:
            post_node = Post.nodes.get(uid=post_uid)
            comments = list(post_node.comment.all())
            answers = [c for c in comments if getattr(c, 'is_answer', False) and not c.is_deleted]
            return [CommentType.from_neomodel(c, info) for c in answers]
        except Post.DoesNotExist:
            return []
           
    comment_replies = graphene.List(
        CommentType,
        comment_uid=graphene.String(required=True),
        max_depth=graphene.Int(default_value=2),
        # NEW: Pagination parameters
        limit=graphene.Int(default_value=10),
        offset=graphene.Int(default_value=0)
    )  


    @handle_graphql_post_errors
    @login_required
    def resolve_comment_replies(self, info, comment_uid, max_depth=2, limit=10, offset=0):
        """
        NEW: Get replies for a specific comment with metrics and pagination.
        """
        try:
            # Add pagination parameters
            params = {
                "parent_comment_uid": comment_uid,
                "limit": limit,
                "offset": offset
            }
            
            print(f"DEBUG: Getting replies for comment: {comment_uid} with limit: {limit}, offset: {offset}")
            
            results, _ = db.cypher_query(
                post_queries.comment_replies_with_metrics_query, params)

            if not results:
                return []

            replies = []
            for result in results:
                reply_data = result[0]
                related_post_data = result[1] if len(result) > 1 else None
            
                # SAFE parsing with proper type checking
                vibes_count = result[2] if len(result) > 2 and isinstance(result[2], (int, float)) else 0
                views_count = result[3] if len(result) > 3 and isinstance(result[3], (int, float)) else 0
                comments_count = result[4] if len(result) > 4 and isinstance(result[4], (int, float)) else 0
                shares_count = result[5] if len(result) > 5 and isinstance(result[5], (int, float)) else 0
                likes_count = result[6] if len(result) > 6 and isinstance(result[6], (int, float)) else 0
                calculated_score = result[7] if len(result) > 7 and isinstance(result[7], (int, float)) else 2.0
                reply_count = result[8] if len(result) > 8 and isinstance(result[8], (int, float)) else 0

                print(f"DEBUG: Processing reply with vibes_count type: {type(vibes_count)}, value: {vibes_count}")

                # Create reply object from neomodel
                reply_uid = reply_data.get('uid')
                reply_node = Comment.nodes.get(uid=reply_uid)

                # Get parent comment for context
                parent_comment = None
                try:
                    parent_node = Comment.nodes.get(uid=comment_uid)
                    
                    # Fetch vibe reactions for parent comment
                    parent_vibe_reactions = []
                    try:
                        if hasattr(parent_node, 'vibe_reactions'):
                            vibe_reaction_nodes = list(parent_node.vibe_reactions.all())
                            active_vibes = [vr for vr in vibe_reaction_nodes if vr.is_active]
                            active_vibes.sort(key=lambda x: x.timestamp, reverse=True)
                            parent_vibe_reactions = [CommentVibeType.from_neomodel(vr) for vr in active_vibes]
                    except Exception as e:
                        print(f"Error fetching parent vibe reactions in replies: {e}")
                        parent_vibe_reactions = []
                    
                    parent_comment = CommentType(
                       uid=parent_node.uid,
                       post=None,
                       user=UserType.from_neomodel(parent_node.user.single()) if parent_node.user.single() else None,
                       content=parent_node.content,
                       timestamp=parent_node.timestamp,
                       is_deleted=parent_node.is_deleted,
                       score=2.0,
                       views=0,
                       comments=0,
                       shares=0,
                       vibes=0,
                       comment_file_id=getattr(parent_node, 'comment_file_id', []) or [],
                       comment_file_url=[],
                       parent_comment=None,
                       replies=[],
                       reply_count=0,
                       depth_level=0,
                       is_reply=False,
                       vibe_reactions=parent_vibe_reactions
                    )
                except:
                    pass

                # Fetch vibe reactions for this reply
                reply_vibe_reactions = []
                try:
                    if hasattr(reply_node, 'vibe_reactions'):
                        vibe_reaction_nodes = list(reply_node.vibe_reactions.all())
                        active_vibes = [vr for vr in vibe_reaction_nodes if vr.is_active]
                        active_vibes.sort(key=lambda x: x.timestamp, reverse=True)
                        reply_vibe_reactions = [CommentVibeType.from_neomodel(vr) for vr in active_vibes]
                except Exception as e:
                    print(f"Error fetching reply vibe reactions: {e}")
                    reply_vibe_reactions = []

                # Create reply with metrics
                reply = CommentType(
                   uid=reply_node.uid,
                   post=None,
                   user=UserType.from_neomodel(reply_node.user.single()) if reply_node.user.single() else None,
                   content=reply_node.content,
                   timestamp=reply_node.timestamp,
                   is_deleted=reply_node.is_deleted,
                   score=float(calculated_score) if calculated_score is not None else 2.0,
                   views=int(views_count) if views_count is not None else 0,
                   comments=int(comments_count) if comments_count is not None else 0,
                   shares=int(shares_count) if shares_count is not None else 0,
                   vibes=int(vibes_count) if vibes_count is not None else 0,
                   comment_file_id=getattr(reply_node, 'comment_file_id', []) or [],
                   comment_file_url=[],
                   parent_comment=parent_comment,
                   replies=[],
                   reply_count=int(reply_count) if reply_count is not None else 0,
                   depth_level=1,
                   is_reply=True,
                   vibe_reactions=reply_vibe_reactions
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
    # my_feed = graphene.List(FeedType, circle_type=CircleTypeEnum())

    # @handle_graphql_post_errors
    # @login_required
    # def resolve_my_feed(self, info, circle_type=None):
    #     payload = info.context.payload
    #     user_id = payload.get('user_id')
    #     log_in_user_node = Users.nodes.get(user_id=user_id)

    #     # Get blocked users and their IDs
    #     blocked_users = users.get_blocked_users(user_id)
    #     blocked_user_ids = {user['user_id'] for user in blocked_users}

    #     # Fetch all posts
    #     all_posts = Post.nodes.all()

    #     # Filter posts based on two conditions:
    #     # 1. The post should not be created by a blocked user.
    #     # 2. The post should not be created by the logged-in user.
    #     filtered_posts = filter(
    #         lambda post: (
    #             post.created_by.single().user_id not in blocked_user_ids and
    #             post.created_by.single().user_id != str(
    #                 user_id)  # Exclude posts by logged-in user
    #         ),
    #         all_posts
    #     )
    #     # Reverse the list of filtered posts to get the latest posts first
    #     reversed_posts = list(filtered_posts)[::-1]

    #     # print("Reversed Posts:", reversed_posts)  # Add this line for debugging
    #     result_feed = []
    #     feed_count = 0
    #     user_has_connection = False
    #     for post_data in reversed_posts:
    #         if feed_count >= 100:
    #             break  # Stop processing if we've reached the limit
    #         post_user = post_data.created_by.single()  # The user who created the post

    #         # Query the connection and circle using Cypher
    #         query = """
    #         MATCH (byuser:Users {uid: $log_in_user_node_uid})-[c1:HAS_CONNECTION]->(conn:Connection)
    #         MATCH (conn)-[c3:HAS_CIRCLE]->(circle:Circle)
    #         MATCH (touser:Users {uid: $post_user_uid})-[c2:HAS_CONNECTION]->(conn)
    #         RETURN conn, circle
    #         """

    #         params = {
    #             "log_in_user_node_uid": log_in_user_node.uid,
    #             "post_user_uid": post_user.uid,
    #         }

    #         results = db.cypher_query(query, params)

    #         # print(results)
    #         if results and results[0]:
    #             user_has_connection = True
    #             connection_node = results[0][0][0]
    #             circle_node = results[0][0][1]
    #             original_circle_type = circle_node.get('circle_type')
    #             if circle_type is None or original_circle_type == circle_type.value:
    #                 # If no circle_type is selected, or the circle_type matches, include the post
    #                 result_feed.append(FeedType.from_neomodel(
    #                     post_data, connection_node, circle_node, log_in_user_node))

    #         else:
    #             if circle_type is None:
    #                 result_feed.append(FeedType.from_neomodel(
    #                     post_data, connection_node=None, circle_node=None, log_in_user_node=log_in_user_node))

    #     if not user_has_connection and circle_type is not None:
    #         return []
    #     return result_feed

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
        Analytics-Based Feed Algorithm
        
        Production-ready feed algorithm with:
        - User analytics-based personalization
        - Proper duplicate prevention for same day
        - Tag-based preferences from user's created content
        - Fallback mechanisms for all scenarios
        - Frontend-compatible response structure
        """
        import base64
        from datetime import datetime, timedelta
        from django.utils import timezone
        start_time = time.time()

        try:
            # Extract user context
            payload = info.context.payload
            user_id = payload.get('user_id')

            # Validate pagination parameters
            first = min(max(1, first), 50)
            logger.info(f"Generating analytics-based feed for user {user_id}: first={first}, after={after}")

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
                        cursor_timestamp = float(cursor_parts[0])
                        cursor_post_uid = cursor_parts[1]
                        logger.info(f"Using cursor: timestamp={cursor_timestamp}, post_uid={cursor_post_uid}")
                    else:
                        logger.warning(f"Invalid cursor format after decode: {decoded_cursor}")
                except Exception as cursor_error:
                    logger.warning(f"Cursor parsing failed: {cursor_error}")
                    cursor_timestamp = None
                    cursor_post_uid = None

            # Generate analytics-based personalized feed
            final_feed = Query._generate_analytics_based_feed(
                user_id=user_id,
                first=first,
                cursor_timestamp=cursor_timestamp,
                cursor_post_uid=cursor_post_uid,
                circle_type=circle_type
            )

            # Add cursors to feed items
            for item in final_feed:
                if hasattr(item, 'uid'):
                    try:
                        # Extract timestamp from created_at (which is already a Unix timestamp string)
                        timestamp = getattr(item, 'created_at', '1000000000')
                        if isinstance(timestamp, str):
                            timestamp = timestamp
                        else:
                            timestamp = str(timestamp)
                        cursor_data = f"{timestamp}_{item.uid}"
                        item.cursor = base64.b64encode(cursor_data.encode()).decode()
                    except Exception as cursor_error:
                        logger.warning(f"Cursor generation failed for {item.uid}: {cursor_error}")
                        item.cursor = base64.b64encode(f"1000000000_{item.uid}".encode()).decode()

            # Log metrics
            total_time = time.time() - start_time
            logger.info(f"Analytics-based feed completed: {len(final_feed)} items in {total_time:.3f}s")
            
            return final_feed

        except Exception as e:
            logger.error(f"Error in analytics-based feed: {e}")
            try:
                # Emergency fallback - get any available content
                emergency_feed = Query._get_emergency_fallback_feed(user_id, first)
                return emergency_feed
            except Exception:
                return []

    @staticmethod
    def _generate_analytics_based_feed(user_id, first, cursor_timestamp=None, cursor_post_uid=None, circle_type=None):
        """
        Generate personalized feed based on user activity analytics
        """
        from user_activity.models import ContentInteraction, SocialInteraction, ProfileActivity
        from post.graphql.raw_queries import post_queries
        from collections import defaultdict
        from datetime import datetime, timedelta
        from django.utils import timezone
        import time
        
        try:
            logger.info(f"Generating analytics-based feed for user {user_id}")
            
            # Step 1: Build user analytics profile
            user_profile = Query._build_user_analytics_profile(user_id)
            logger.info(f"User profile built: new_user={user_profile['is_new_user']}, preferences={user_profile['preferred_content_types']}")
            
            # Step 2: Get today's viewed content to prevent duplicates
            today_viewed = Query._get_today_viewed_content(user_id, timezone.now().date())
            logger.info(f"User has viewed {len(today_viewed)} items today")
            
            # Step 3: Get base content pool using existing query
            params = {
                "log_in_user_node_id": str(user_id),
                "cursor_timestamp": cursor_timestamp,
                "cursor_post_uid": cursor_post_uid,
                "limit": first * 3  # Get more content for filtering
            }

            results, _ = db.cypher_query(post_queries.post_feed_query, params)
            logger.info(f"Base query returned {len(results)} results")
            
            # Step 4: Filter out today's viewed content
            filtered_results = []
            for result in results:
                post_data = result[0] if result else {}
                post_uid = post_data.get('uid')
                if post_uid and post_uid not in today_viewed:
                    filtered_results.append(result)
            
            logger.info(f"After duplicate filtering: {len(filtered_results)} results")
            
            # Step 5: Score and rank based on user analytics
            if user_profile['is_new_user']:
                # For new users, use diverse content with basic scoring
                scored_results = Query._score_content_for_new_user(filtered_results, user_id)
            else:
                # For existing users, use analytics-based scoring
                scored_results = Query._score_content_with_analytics(filtered_results, user_profile, user_id)
            
            # Step 6: Apply final filtering and convert to feed response
            final_results = scored_results[:first]
            
            # Step 7: Initialize feed utilities and convert to GraphQL response
            if final_results:
                Query.initialize_feed_utilities(final_results)
                feed_items = Query.build_feed_response(final_results, circle_type)
                
                # Track viewed content for future duplicate prevention
                Query._track_viewed_content(user_id, [item.uid for item in feed_items if hasattr(item, 'uid')], content_source='analytics_feed')
                
                logger.info(f"Generated {len(feed_items)} feed items for user {user_id}")
                return feed_items
            
            # Step 8: Fallback if no content found
            logger.warning(f"No content after filtering for user {user_id}, using fallback")
            return Query._get_fallback_content(user_id, first)
            
        except Exception as e:
            logger.error(f"Error in _generate_analytics_based_feed: {e}")
            import traceback
            traceback.print_exc()
            return Query._get_fallback_content(user_id, first)
    
    @staticmethod
    def _build_user_analytics_profile(user_id):
        """
        Build comprehensive user profile from activity analytics
        """
        from user_activity.models import ContentInteraction, SocialInteraction, ProfileActivity
        from collections import defaultdict
        from datetime import timedelta
        from django.utils import timezone
        
        profile = {
            'content_preferences': defaultdict(float),
            'interaction_preferences': defaultdict(float),
            'social_behavior': defaultdict(float),
            'tag_preferences': defaultdict(float),
            'temporal_patterns': defaultdict(int),
            'engagement_depth': 0.0,
            'is_new_user': True,
            'preferred_content_types': [],
            'active_hours': [],
        }
        
        try:
            # Analyze content interactions (last 30 days)
            recent_cutoff = timezone.now() - timedelta(days=30)
            content_interactions = ContentInteraction.objects.filter(
                    user_id=user_id,
                created_at__gte=recent_cutoff
            )
            
            if content_interactions.exists():
                profile['is_new_user'] = False
                
                # Content type preferences
                for interaction in content_interactions:
                    weight = Query._get_interaction_weight(interaction.interaction_type)
                    profile['content_preferences'][interaction.content_type] += weight
                    profile['interaction_preferences'][interaction.interaction_type] += weight
                    
                    # Add engagement depth scoring
                    if interaction.duration_seconds:
                        profile['engagement_depth'] += min(interaction.duration_seconds / 60, 10) * 0.1
                    if interaction.scroll_depth_percentage:
                        profile['engagement_depth'] += interaction.scroll_depth_percentage / 100 * 0.2
                    
                    # Temporal patterns
                    hour = interaction.created_at.hour
                    profile['temporal_patterns'][hour] += 1
            
            # Analyze social interactions
            social_interactions = SocialInteraction.objects.filter(
                user_id=user_id,
                created_at__gte=recent_cutoff
            )
            
            for interaction in social_interactions:
                profile['social_behavior'][interaction.interaction_type] += 1.0
            
            # Get user's tag preferences from their created content
            user_tags = Query._get_user_tag_preferences(user_id)
            profile['tag_preferences'] = user_tags
            
            # Determine preferred content types
            if profile['content_preferences']:
                sorted_prefs = sorted(profile['content_preferences'].items(), key=lambda x: x[1], reverse=True)
                profile['preferred_content_types'] = [item[0] for item in sorted_prefs[:3]]
            
            # Determine active hours
            if profile['temporal_patterns']:
                sorted_hours = sorted(profile['temporal_patterns'].items(), key=lambda x: x[1], reverse=True)
                profile['active_hours'] = [hour for hour, count in sorted_hours[:6]]  # Top 6 hours
            
            logger.info(f"Built profile for user {user_id}: new_user={profile['is_new_user']}, prefs={profile['preferred_content_types']}")
            
        except Exception as e:
            logger.error(f"Error building user profile: {e}")
            
        return profile
    
    @staticmethod
    def _get_interaction_weight(interaction_type):
        """
        Get weight for different interaction types
        """
        weights = {
            'view': 1.0,
            'like': 3.0,
            'comment': 5.0,
            'share': 7.0,
            'create': 10.0,
            'save': 6.0,
            'reaction': 4.0,
            'send_request': 2.0,
            'accepted': 8.0,
        }
        return weights.get(interaction_type, 1.0)
    
    @staticmethod
    def _get_user_tag_preferences(user_id):
        """
        Get user's tag preferences from their created content and interactions
        """
        from collections import defaultdict
        
        tag_preferences = defaultdict(float)
        
        try:
            from auth_manager.models import Users
            user_node = Users.nodes.get(user_id=user_id)
            
            # Get tags from user's created posts
            user_posts = user_node.post.all()
            for post in user_posts:
                # Since posts don't have tags field, use post_type as preference indicator
                if hasattr(post, 'post_type') and post.post_type:
                    tag_preferences[post.post_type.lower()] += 2.0  # Weight by content type they create
            
            # Get tags from user's created communities  
            user_communities = user_node.community.all()
            for community in user_communities:
                if hasattr(community, 'community_name') and community.community_name:
                    # Use community name as tag preference
                    community_words = community.community_name.lower().split()
                    for word in community_words:
                        if len(word) > 2:  # Only meaningful words
                            tag_preferences[word] += 1.5
            
            logger.info(f"Extracted {len(tag_preferences)} tag preferences for user {user_id}")

        except Exception as e:
            logger.error(f"Error getting user tag preferences: {e}")
        
        return dict(tag_preferences)
    
    @staticmethod
    def _score_content_for_new_user(results, user_id):
        """
        Score content for new users with basic diversity
        """
        try:
            # For new users, provide diverse content with simple scoring
            scored_results = []
            content_type_counts = {'post': 0, 'community': 0, 'story': 0}
            
            for result in results:
                post_data = result[0] if result else {}
                
                # Basic diversity scoring
                content_type = post_data.get('post_type', 'unknown')
                base_score = 1.0
                
                # Promote diversity by reducing score for over-represented types
                if content_type in content_type_counts:
                    if content_type_counts[content_type] < 3:
                        base_score += 0.2  # Boost under-represented types
                    content_type_counts[content_type] += 1
                
                # Add some randomness for new users
                import random
                base_score += random.uniform(-0.1, 0.1)
                
                scored_results.append({
                    'result': result,
                    'score': base_score,
                    'post_data': post_data
                })
            
            # Sort by score
            scored_results.sort(key=lambda x: x['score'], reverse=True)
            return [item['result'] for item in scored_results]
            
        except Exception as e:
            logger.error(f"Error scoring content for new user: {e}")
            return results
    
    @staticmethod
    def _get_today_viewed_content(user_id, date):
        """
        Get content UIDs that user has already seen today
        """
        from user_activity.models import ContentInteraction, MediaInteraction
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        try:
            start_of_day = timezone.make_aware(datetime.combine(date, datetime.min.time()))
            end_of_day = start_of_day + timedelta(days=1)
            
            viewed_content = set()
            
            # From content interactions
            interactions = ContentInteraction.objects.filter(
                user_id=user_id,
                created_at__gte=start_of_day,
                created_at__lt=end_of_day,
                interaction_type__in=['view', 'like', 'comment', 'share']
            )
            
            for interaction in interactions:
                viewed_content.add(interaction.content_id)
            
            # From media interactions (posts viewed through comments)
            media_interactions = MediaInteraction.objects.filter(
                user_id=user_id,
                created_at__gte=start_of_day,
                created_at__lt=end_of_day,
                media_type='comment_media'
            )
            
            for interaction in media_interactions:
                if interaction.metadata and 'post_uid' in interaction.metadata:
                    viewed_content.add(interaction.metadata['post_uid'])
            
            logger.info(f"User {user_id} has viewed {len(viewed_content)} items today")
            return viewed_content
            
        except Exception as e:
            logger.error(f"Error getting today's viewed content: {e}")
            return set()
    
    @staticmethod
    def _get_today_viewed_fallback_content(user_id, date):
        """
        Get ONLY fallback content UIDs that user has seen today (not analytics content)
        """
        from user_activity.models import ContentInteraction
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        try:
            start_of_day = timezone.make_aware(datetime.combine(date, datetime.min.time()))
            end_of_day = start_of_day + timedelta(days=1)
            
            viewed_fallback_content = set()
            
            # Get only content viewed as fallback or fallback_cycle
            fallback_interactions = ContentInteraction.objects.filter(
                user_id=user_id,
                created_at__gte=start_of_day,
                created_at__lt=end_of_day,
                interaction_type='view',
                metadata__source='feed_view',
                metadata__content_source__in=['fallback', 'fallback_cycle']
            )
            
            for interaction in fallback_interactions:
                viewed_fallback_content.add(interaction.content_id)
            
            logger.info(f"User {user_id} has viewed {len(viewed_fallback_content)} fallback items today")
            return viewed_fallback_content
            
        except Exception as e:
            logger.error(f"Error getting today's viewed fallback content: {e}")
            return set()
    
    @staticmethod
    def _smart_randomize_content(results, user_id, limit, randomize_type='fallback_cycle'):
        """
        Smart randomization that considers user preferences and avoids predictable patterns
        """
        try:
            import random
            import time
            
            if randomize_type == 'fallback_cycle':
                # For fallback cycles, use minute-based randomization for more frequent changes
                current_minute = int(time.time() // 60)  # Changes every minute
                seed_base = f"{user_id}_{current_minute}"
            else:
                # For other randomization, use hour-based for more stability
                current_hour = int(time.time() // 3600)  # Changes every hour
                seed_base = f"{user_id}_{current_hour}"
            
            random.seed(hash(seed_base))
            
            # Create a copy and shuffle
            shuffled_results = results.copy()
            random.shuffle(shuffled_results)
            
            # Take the required number of items
            selected_results = shuffled_results[:limit]
            
            logger.info(f"Smart randomized {len(selected_results)} items for user {user_id} (type: {randomize_type}, seed: {seed_base})")
            return selected_results
            
        except Exception as e:
            logger.error(f"Error in smart randomization: {e}")
            # Fallback to simple selection
            return results[:limit]
    
    @staticmethod
    def _score_content_with_analytics(results, user_profile, user_id):
        """Score content based on user analytics profile"""
        scored_results = []
        try:
            for result in results:
                post_data = result[0] if result else {}
                if not post_data:
                    continue
                score = Query._calculate_content_score(post_data, user_profile, user_id)
                scored_results.append({
                    'result': result,
                    'score': score,
                    'post_data': post_data
                })
            
            # Sort by score descending
            scored_results.sort(key=lambda x: x['score'], reverse=True)
            return [item['result'] for item in scored_results]
            
        except Exception as e:
            logger.error(f"Error scoring content: {e}")
            return results
    
    @staticmethod
    def _calculate_content_score(post_data, user_profile, user_id):
        """Calculate personalized score for content item"""
        try:
            base_score = 1.0
            
            # Content type preference scoring
            post_type = post_data.get('post_type', '').lower()
            if post_type in user_profile['content_preferences']:
                base_score += user_profile['content_preferences'][post_type] * 0.3
            
            # Tag/type preference scoring (using post_type as tag)
            if post_type in user_profile['tag_preferences']:
                base_score += user_profile['tag_preferences'][post_type] * 0.2
            
            # Engagement scoring based on vibe_score
            vibe_score = post_data.get('vibe_score', 2.0)
            if vibe_score > 2.0:
                base_score += (vibe_score - 2.0) * 0.4
            
            # Recency bonus (newer content gets slight boost)
            created_at = post_data.get('created_at', 0)
            if created_at:
                import time
                current_time = time.time()
                age_hours = (current_time - created_at) / 3600
                if age_hours < 24:  # Content less than 24 hours old
                    base_score += 0.2
                elif age_hours < 72:  # Content less than 3 days old
                    base_score += 0.1
            
            return max(base_score, 0.1)
            
        except Exception as e:
            logger.error(f"Error calculating content score: {e}")
            return 1.0
    
    @staticmethod
    def _track_viewed_content(user_id, post_uids, content_source='analytics_feed'):
        """Track viewed content for duplicate prevention"""
        try:
            from user_activity.models import ContentInteraction
            from django.utils import timezone
            
            for post_uid in post_uids:
                # Always create a new record for tracking purposes (don't use get_or_create)
                # This ensures we track each view with the correct content_source
                ContentInteraction.objects.create(
                    user_id=user_id,
                    content_type='post',
                    content_id=post_uid,
                    interaction_type='view',
                    timestamp=timezone.now(),
                    metadata={
                        'source': 'feed_view',
                        'algorithm': 'analytics_based',
                        'content_source': content_source
                    }
                )
            logger.info(f"Tracked {len(post_uids)} viewed items for user {user_id} (source: {content_source})")
            
        except Exception as e:
            logger.error(f"Error tracking viewed content: {e}")
    
    @staticmethod
    def _get_fallback_content(user_id, limit):
        """Get fallback content when personalized content fails - ALWAYS PROVIDES CONTENT"""
        try:
            from post.graphql.raw_queries import post_queries
            from django.utils import timezone
            
            # Get today's viewed FALLBACK content only (not all content)
            today_viewed_fallback = Query._get_today_viewed_fallback_content(user_id, timezone.now().date())
            
            params = {
                "log_in_user_node_id": str(user_id),
                "cursor_timestamp": None,
                "cursor_post_uid": None,
                "limit": limit * 2  # Get more content for filtering
            }
            results, _ = db.cypher_query(post_queries.post_feed_query, params)
            
            if results:
                # Filter out only previously viewed FALLBACK content
                filtered_results = []
                for result in results:
                    post_data = result[0] if result else {}
                    post_uid = post_data.get('uid')
                    if post_uid and post_uid not in today_viewed_fallback:
                        filtered_results.append(result)
                    
                    # Stop when we have enough content
                    if len(filtered_results) >= limit:
                        break
                
                logger.info(f"Fallback content: {len(results)} total, {len(filtered_results)} after fallback duplicate filtering")
                
                # If we have filtered results, use them
                if filtered_results:
                    Query.initialize_feed_utilities(filtered_results)
                    fallback_feed = Query.build_feed_response(filtered_results, None)
                    
                    # Track fallback content as viewed
                    fallback_uids = [item.uid for item in fallback_feed if hasattr(item, 'uid')]
                    Query._track_viewed_content(user_id, fallback_uids, content_source='fallback')
                    
                    return fallback_feed
                
                # If no unviewed fallback content, provide fresh fallback (restart the cycle)
                else:
                    logger.info(f"User {user_id} has viewed all fallback content, restarting fallback cycle")
                    
                    # Smart randomization to avoid same sequence on every refresh
                    fresh_results = Query._smart_randomize_content(results, user_id, limit, 'fallback_cycle')
                    
                    Query.initialize_feed_utilities(fresh_results)
                    fresh_fallback_feed = Query.build_feed_response(fresh_results, None)
                    
                    # Track as new fallback cycle
                    fresh_uids = [item.uid for item in fresh_fallback_feed if hasattr(item, 'uid')]
                    Query._track_viewed_content(user_id, fresh_uids, content_source='fallback_cycle')
                    
                    logger.info(f"Restarted fallback cycle with {len(fresh_results)} randomized items")
                    return fresh_fallback_feed
            
            # This should never happen - emergency fallback
            logger.error(f"No content available in database for user {user_id} - using emergency fallback")
            return Query._get_emergency_fallback_feed(user_id, limit)

        except Exception as e:
            logger.error(f"Error getting fallback content: {e}")
            return Query._get_emergency_fallback_feed(user_id, limit)
    
    @staticmethod
    def _get_emergency_fallback_feed(user_id, limit):
        """Emergency fallback - get any available content, ignoring duplicates if necessary"""
        try:
            # First try with duplicate prevention
            fallback_feed = Query._get_fallback_content(user_id, min(limit, 10))
            
            if fallback_feed:
                return fallback_feed
            
            # If no content found even with fallback, get fresh content ignoring today's views
            logger.warning(f"User {user_id} has viewed all available content today, providing fresh content")
            
            from post.graphql.raw_queries import post_queries
            params = {
                "log_in_user_node_id": str(user_id),
                "cursor_timestamp": None,
                "cursor_post_uid": None,
                "limit": min(limit * 2, 20)  # Get more content for randomization
            }
            results, _ = db.cypher_query(post_queries.post_feed_query, params)
            
            if results:
                # Smart randomization for emergency content
                emergency_results = Query._smart_randomize_content(results, user_id, min(limit, 10), 'emergency')
                
                Query.initialize_feed_utilities(emergency_results)
                emergency_feed = Query.build_feed_response(emergency_results, None)
                
                # Track emergency content as viewed
                emergency_uids = [item.uid for item in emergency_feed if hasattr(item, 'uid')]
                Query._track_viewed_content(user_id, emergency_uids, content_source='emergency')
                
                logger.info(f"Provided {len(emergency_feed)} randomized emergency items")
                return emergency_feed
            
                return []
            
        except Exception as e:
            logger.error(f"Error in emergency fallback: {e}")
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
                # Extract post components - FIXED INDEXING to match query structure
                # Query returns: post, user, profile, reactions, connection, circle, share_count, calculated_overall_score, created_at
                post_node = post[0] if post[0] else None
                user_node = post[1] if post[1] else None
                profile_node = post[2] if post[2] else None
                likes = post[3] if post[3] else None  # reactions
                connection = post[4] if post[4] else None
                circle = post[5] if post[5] else None
                share_count = post[6] if len(post) > 6 and post[6] is not None else 0
                calculated_overall_score = post[7] if len(post) > 7 and post[7] is not None else 2.0
                # created_at is at post[8] but we don't need it here

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
                
                # Debug logging only when there are actual issues
                if post_node is None:
                    logger.warning(f"Null post_node found in feed results")
                    continue

                # Apply circle type filtering
                should_include_post = False

                if circle_type is None:
                    # No filter - include all posts
                    should_include_post = True
                else:
                    # Filter is applied - check if post matches the filter
                    if connection is not None and circle and original_circle_type:
                        # Post has connection and circle - check if it matches filter
                        if original_circle_type == circle_type.value:
                            should_include_post = True
                    # Note: Posts without connections are excluded when filter is active

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
                    # Only add non-None feed items
                    if feed_item is not None:
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

    # New: Global debate feed for everyone with title/data pattern
    global_debate_feed = graphene.List(PostCategoryType)

    @handle_graphql_post_errors
    @login_required
    def resolve_global_debate_feed(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        def fetch_posts(query, params=None):
            params = params or {}
            results, _ = db.cypher_query(query, params)
            items = []
            for row in results:
                post_data = row[0]
                items.append(PostRecommendedType.from_neomodel(post_data))
            return items

        # Top in World: best debate posts by vibe_score
        world_query = (
            "MATCH (p:Post) "
            "WHERE p.is_deleted = false AND p.post_type = 'debate' "
            "RETURN p ORDER BY p.vibe_score DESC, p.created_at DESC LIMIT 12"
        )
        top_world = fetch_posts(world_query)
        world_section = PostCategoryType(title="Top in World", data=top_world)

        # Static India sections (same selection for now)
        india_random_query = (
            "MATCH (p:Post) "
            "WHERE p.is_deleted = false AND p.post_type = 'debate' "
            "RETURN p ORDER BY rand() LIMIT 12"
        )
        top_delhi = fetch_posts(india_random_query)
        top_mumbai = fetch_posts(india_random_query)
        top_bangalore = fetch_posts(india_random_query)

        india_sections = [
            PostCategoryType(title="Top in India - Delhi", data=top_delhi),
            PostCategoryType(title="Top in India - Mumbai", data=top_mumbai),
            PostCategoryType(title="Top in India - Bangalore", data=top_bangalore),
        ]

        return [world_section] + india_sections
