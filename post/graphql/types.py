import graphene
from graphene import ObjectType
from neomodel import db
from auth_manager.graphql.types import UserType
from auth_manager.Utils import generate_presigned_url
from auth_manager.models import Profile, Users
from vibe_manager.models import IndividualVibe
from post.redis import increment_post_comment_count,get_post_comment_count,get_post_like_count

from connection.utils import relation as RELATIONUTILLS
from post.utils.time_format import time_ago 
from post.models import PostReactionManager
from datetime import datetime, timezone
from post.graphql.raw_queries import users,post_queries
from post.utils.reaction_manager import PostReactionUtils,IndividualVibeManager
from post.utils.file_url import FileURL
from neomodel import db

class FileDetailType(graphene.ObjectType):
    url = graphene.String()
    file_extension = graphene.String()
    file_type = graphene.String()
    file_size = graphene.Int()


class PostType(ObjectType):
    uid = graphene.String()
    post_title = graphene.String()
    post_text = graphene.String()
    post_type = graphene.String()
    post_file_id =graphene.List(graphene.String)
    post_file_url=graphene.List(FileDetailType)
    privacy = graphene.String()
    comment_count = graphene.Int()
    vibes_count=graphene.Int()
    vibe_score = graphene.Float()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    is_deleted = graphene.Boolean()
    created_by = graphene.Field(lambda:UserFeedType)
    updated_by=graphene.Field(lambda:UserFeedType)
    comment=graphene.List(lambda:CommentNonPostType)
    like= graphene.List(lambda:LikeNonPostType)
    share_count=graphene.Int()
    my_vibe_details = graphene.List(lambda:ReactionFeedType)
    vibe_feed_List=graphene.List(lambda:VibeFeedListType)
    connection = graphene.Field(lambda:ConnectionFeedType)


    @classmethod
    def from_neomodel(cls, post, info):
        if post.is_deleted==False:
            reactions_nodes = post.like.all()
            uid=post.uid
        
            post_reaction_manager = PostReactionUtils.get_reaction_manager(uid)

            post_reaction_manager = PostReactionManager.objects.filter(post_uid=post.uid).first()

            if post_reaction_manager:
                all_reactions = post_reaction_manager.post_vibe
                sorted_reactions = sorted(all_reactions, key=lambda x: x.get('cumulative_vibe_score', 0), reverse=True)
            else:
                # Handle case when data hasn't been stored yet
                try:
                    sorted_reactions = IndividualVibeManager.get_data()
                except ValueError:
                    # If data hasn't been stored, store it and try again
                    try:
                        IndividualVibeManager.store_data()
                        sorted_reactions = IndividualVibeManager.get_data()
                    except Exception:
                        # If still fails, provide empty list as fallback
                        sorted_reactions = []

            user_node=Users.nodes.get(uid=info.context.user)
            post_creator = post.created_by.single() if post.created_by.single() else None
            profile = user_node.profile.single() if user_node.profile.single() else None
            
            # Get connection between viewing user and post creator
            connection_node = None
            circle_node = None
            
            if post_creator:
                # Cypher query to find connection between viewing user and post creator
                query = """
                MATCH (viewer:Users {uid: $viewer_uid})-[:HAS_CONNECTION]->(connection:Connection)-[:HAS_CIRCLE]->(circle:Circle),
                      (creator:Users {uid: $creator_uid})-[:HAS_CONNECTION]->(connection)
                WHERE connection.connection_status = "Accepted"
                RETURN connection, circle
                LIMIT 1
                """
                
                params = {
                    "viewer_uid": user_node.uid,
                    "creator_uid": post_creator.uid
                }
                
                results, _ = db.cypher_query(query, params)
                
                if results and len(results) > 0:
                    connection_data = results[0][0]
                    circle_data = results[0][1]
                   
                    try:
                        # Convert to dictionary format expected by ConnectionFeedType
                        connection_node = {
                            'uid': connection_data['uid'],
                            'connection_status': connection_data['connection_status'],
                            'timestamp': connection_data['timestamp']
                        }
                      
                        # Convert to dictionary format expected by CircleFeedType
                        circle_node = {
                            'uid': circle_data['uid'],
                            'circle_type': circle_data['circle_type'],
                            'sub_relation': circle_data['sub_relation']
                        }
                    except (AttributeError, KeyError, TypeError) as e:
                        print(f"Error accessing attributes: {e}")
                        connection_node = None
                        circle_node = None
            
            return cls(
                uid=post.uid,
                post_title=post.post_title,
                post_text=post.post_text,
                post_type=post.post_type,
                post_file_id=post.post_file_id,
                post_file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in post.post_file_id] if post.post_file_id else None),
                privacy=post.privacy,
                comment_count=get_post_comment_count(post.uid),
                vibes_count=get_post_like_count(post.uid),
                vibe_score=post.vibe_score,
                created_at=post.created_at,
                updated_at=post.updated_at,
                is_deleted=post.is_deleted,
                created_by=UserFeedType.from_neomodel(user_node,profile) if user_node and profile else None,
                comment=[CommentNonPostType.from_neomodel(comment) for comment in post.comment],
                like=[LikeNonPostType.from_neomodel(like) for like in post.like],
                share_count=post.share_count,
                my_vibe_details=[ReactionFeedType.from_neomodel(r) for r in reactions_nodes] if reactions_nodes else None,
                vibe_feed_List=[VibeFeedListType.from_neomodel(vibe) for vibe in sorted_reactions],
                connection=ConnectionFeedType.from_neomodel(connection_node, circle_node) if connection_node else None,
            )
    
class TagType(ObjectType):
    uid=graphene.String()
    names = graphene.List(graphene.String)
    created_on = graphene.DateTime()
    created_by = graphene.Field(UserType)
    post = graphene.Field(PostType)
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, tag):
        return cls(
            names=tag.names,
            created_on=tag.created_on,
            created_by=UserType.from_neomodel(tag.created_by.single()) if tag.created_by.single() else None,
            post=PostType.from_neomodel(tag.post.single()) if tag.post.single() else None,
            is_deleted=tag.is_deleted,
            uid=tag.uid
        )

class CommentType(ObjectType):
    uid = graphene.String()
    post = graphene.Field(PostType)
    user = graphene.Field(UserType)
    content = graphene.String()
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()
    score = graphene.Float()
    views = graphene.Int()
    comments = graphene.Int()
    shares = graphene.Int()
    vibes = graphene.Int()   

    @classmethod
    def from_neomodel(cls, comment):
        related_post = comment.post.single() if comment.post.single() else None
        
        if not post_metrics:
            post_metrics = {
                'score': 2.0,
                'views': 0,
                'comments': 0,
                'shares': 0,
                'vibes': 0
            }
        
        if related_post:
            try:
                post_metrics = {
                    'score': getattr(related_post, 'vibe_score', 2.0),
                    'views': len([view for view in related_post.view.all() if not view.is_deleted]) if hasattr(related_post, 'view') else 0,
                    'comments': len([c for c in related_post.comment.all() if not c.is_deleted]) if hasattr(related_post, 'comment') else 0,
                    'shares': len([share for share in related_post.postshare.all() if not share.is_deleted]) if hasattr(related_post, 'postshare') else 0,
                    'vibes': len([like for like in related_post.like.all() if not like.is_deleted]) if hasattr(related_post, 'like') else 0
                }
            except Exception as e:
                print(f"Error calculating post metrics: {e}")
        
        return cls(
            uid=comment.uid,
            post=PostType.from_neomodel(related_post) if related_post else None,
            user=UserType.from_neomodel(comment.user.single()) if comment.user.single() else None,
            content=comment.content,
            timestamp=comment.timestamp,
            is_deleted=comment.is_deleted,
            score=post_metrics['score'],
            views=post_metrics['views'],
            comments=post_metrics['comments'],
            shares=post_metrics['shares'],
            vibes=post_metrics['vibes']
        )

class LikeType(ObjectType):
    uid = graphene.String()
    # post = graphene.Field(PostType)
    user = graphene.Field(UserType)
    reaction = graphene.String()
    vibe = graphene.Float()
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, like):
        return cls(
            uid=like.uid,
            # post=PostType.from_neomodel(like.post.single()) if like.post.single() else None,
            user=UserType.from_neomodel(like.user.single()) if like.user.single() else None,
            reaction=like.reaction,
            vibe=like.vibe,
            timestamp=like.timestamp,
            is_deleted=like.is_deleted
        )

class PostShareType(ObjectType):
    uid = graphene.String()
    post = graphene.Field(PostType)
    user = graphene.Field(UserType)
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()
    share_type = graphene.String()
    shared_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, post_share):
        return cls(
            uid=post_share.uid,
            post=PostType.from_neomodel(post_share.post.single()) if post_share.post.single() else None,
            user=UserType.from_neomodel(post_share.user.single()) if post_share.user.single() else None,
            timestamp=post_share.timestamp,
            is_deleted=post_share.is_deleted,
            share_type=post_share.share_type,
            shared_at=post_share.shared_at
        )

class PostViewType(ObjectType):
    uid = graphene.String()
    post = graphene.Field(PostType)
    user = graphene.Field(UserType)
    viewed_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, post_view):
        return cls(
            uid=post_view.uid,
            post=PostType.from_neomodel(post_view.post.single()) if post_view.post.single() else None,
            user=UserType.from_neomodel(post_view.user.single()) if post_view.user.single() else None,
            viewed_at=post_view.viewed_at
        )

class SavedPostType(ObjectType):
    uid = graphene.String()
    post = graphene.Field(PostType)
    user = graphene.Field(UserType)
    saved_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, saved_post):
        return cls(
            uid=saved_post.uid,
            post=PostType.from_neomodel(saved_post.post.single()) if saved_post.post.single() else None,
            user=UserType.from_neomodel(saved_post.user.single()) if saved_post.user.single() else None,
            saved_at=saved_post.saved_at
        )

class ReviewType(ObjectType):
    uid = graphene.String()
    post = graphene.Field(PostType)
    user = graphene.Field(UserType)
    rating = graphene.Int()
    review_text = graphene.String()
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, review):
        return cls(
            uid=review.uid,
            post=PostType.from_neomodel(review.post.single()) if review.post.single() else None,
            user=UserType.from_neomodel(review.user.single()) if review.user.single() else None,
            rating=review.rating,
            review_text=review.review_text,
            timestamp=review.timestamp,
            is_deleted=review.is_deleted
        )

class PinedPostType(ObjectType):
    uid = graphene.String()
    post = graphene.Field(PostType)
    user = graphene.Field(UserType)
    name = graphene.String()
    pined_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, pined_post):
        return cls(
            uid=pined_post.uid,
            post=PostType.from_neomodel(pined_post.post.single()) if pined_post.post.single() else None,
            user=UserType.from_neomodel(pined_post.user.single()) if pined_post.user.single() else None,
            name=pined_post.name,
            pined_at=pined_post.pined_at
        )

class TagNonPostType(ObjectType):
    uid=graphene.String()
    names = graphene.List(graphene.String)
    created_on = graphene.DateTime()
    created_by = graphene.Field(UserType)
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, tag):
        return cls(
            names=tag.names,
            created_on=tag.created_on,
            created_by=UserType.from_neomodel(tag.created_by.single()) if tag.created_by.single() else None,    
            is_deleted=tag.is_deleted,
            uid=tag.uid
        )
    
class CommentNonPostType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    content = graphene.String()
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, comment):
        return cls(
            uid=comment.uid,
            user=UserType.from_neomodel(comment.user.single()) if comment.user.single() else None,
            content=comment.content,
            timestamp=comment.timestamp,
            is_deleted=comment.is_deleted
        )
    
class LikeNonPostType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    reaction = graphene.String()
    vibe = graphene.Float()
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, like):
        return cls(
            uid=like.uid,
            user=UserType.from_neomodel(like.user.single()) if like.user.single() else None,
            reaction=like.reaction,
            vibe=like.vibe,
            timestamp=like.timestamp,
            is_deleted=like.is_deleted
        )
    
# This is for showing my_vibes_detail in feed type
class LikeNonPostNonUserType(ObjectType):
    uid = graphene.String()
    reaction = graphene.String()
    vibe = graphene.Float()
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, like):
        return cls(
            uid=like.uid,
            reaction=like.reaction,
            vibe=like.vibe,
            timestamp=like.timestamp,
            is_deleted=like.is_deleted
        )




class PostShareNonPostType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()
    share_type = graphene.String()
    shared_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, post_share):
        return cls(
            uid=post_share.uid,
            user=UserType.from_neomodel(post_share.user.single()) if post_share.user.single() else None,
            timestamp=post_share.timestamp,
            is_deleted=post_share.is_deleted,
            share_type=post_share.share_type,
            shared_at=post_share.shared_at
        )
    
class PostViewNonPostType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    viewed_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, post_view):
        return cls(
            uid=post_view.uid,
            user=UserType.from_neomodel(post_view.user.single()) if post_view.user.single() else None,
            viewed_at=post_view.viewed_at
        )
    
class SavedNonPostType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    saved_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, saved_post):
        return cls(
            uid=saved_post.uid,
            user=UserType.from_neomodel(saved_post.user.single()) if saved_post.user.single() else None,
            saved_at=saved_post.saved_at
        )
    
class ReviewNonPostType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    rating = graphene.Int()
    review_text = graphene.String()
    timestamp = graphene.DateTime()
    is_deleted = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, review):
        return cls(
            uid=review.uid,
            user=UserType.from_neomodel(review.user.single()) if review.user.single() else None,
            rating=review.rating,
            review_text=review.review_text,
            timestamp=review.timestamp,
            is_deleted=review.is_deleted
        )
    
class PinedNonPostType(ObjectType):
    uid = graphene.String()
    user = graphene.Field(UserType)
    name = graphene.String()
    pined_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, pined_post):
        return cls(
            uid=pined_post.uid,
            user=UserType.from_neomodel(pined_post.user.single()) if pined_post.user.single() else None,
            name=pined_post.name,
            pined_at=pined_post.pined_at
        )
    

class VibeFeedListType(ObjectType):
    vibe_id=graphene.String()
    vibe_name=graphene.String()
    vibe_cumulative_score=graphene.String()
    @classmethod
    def from_neomodel(cls, vibe):
        if isinstance(vibe, dict):
            # print(vibe.get("cumulative_vibe_score"))
            return cls(
                vibe_id=vibe.get("vibes_id"),  # Use dictionary access
                vibe_name=vibe.get("vibes_name"),
                vibe_cumulative_score=round(vibe.get("cumulative_vibe_score"),1)  # Use dictionary access
            )
        else:
            # Assume it's an IndividualVibe object
            return cls(
                vibe_id=vibe.id,  # Use the attribute directly
                vibe_name=vibe.name_of_vibe,
                vibe_cumulative_score="0"  # Use the attribute directly
            )



class FeedType(ObjectType):
    uid = graphene.String()
    post_title = graphene.String()
    post_text = graphene.String()
    post_type = graphene.String()
    post_file_id =graphene.List(graphene.String)
    post_file_url=graphene.List(FileDetailType)
    privacy = graphene.String()
    vibe_score = graphene.Float()
    created_at = graphene.String()
    updated_at = graphene.DateTime()
    is_deleted = graphene.Boolean()
    created_by = graphene.Field(UserType)
    updated_by=graphene.Field(UserType)
    comment_count=graphene.Int()
    vibes_count=graphene.Int()
    share_count=graphene.Int()
    connection=graphene.Field(lambda:ConnectionNoUserPostType)
    my_vibe_details=graphene.List(lambda:LikeNonPostNonUserType)
    vibe_feed_List=graphene.List(lambda:VibeFeedListType)


    @classmethod
    def from_neomodel(cls, post,connection_node,circle_node,log_in_user_node):
        post_reaction_manager = PostReactionManager.objects.filter(post_uid=post.uid).first()

        # Extract all reactions from the post_vibe field
        # all_reactions = post_reaction_manager.post_vibe
        if post_reaction_manager:
            all_reactions = post_reaction_manager.post_vibe
            sorted_reactions = sorted(all_reactions, key=lambda x: x.get('cumulative_vibe_score', 0), reverse=True)
        else:
            sorted_reactions = IndividualVibe.objects.all()[:10]
            # print(sorted_reactions)
        return cls(
            uid=post.uid,
            post_title=post.post_title,
            post_text=post.post_text,
            post_type=post.post_type,
            post_file_id=post.post_file_id,
            post_file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in post.post_file_id] if post.post_file_id else None),
            privacy=post.privacy,
            comment_count=get_post_comment_count(post.uid),
            vibes_count=get_post_like_count(post.uid),
            share_count=post.share_count,
            vibe_score=post.vibe_score,
            created_at=time_ago(post.created_at),
            updated_at=post.updated_at,
            is_deleted=post.is_deleted,
            connection=ConnectionNoUserPostType.from_neomodel(connection_node,circle_node) if connection_node else None,
           my_vibe_details = [
                LikeNonPostNonUserType.from_neomodel(like)
                for like in sorted(
                    post.like,
                    key=lambda l: l.timestamp,
                    reverse=True
                )
                if like.user.single().uid == log_in_user_node.uid
            ],
            created_by=UserType.from_neomodel(post.created_by.single()) if post.created_by.single() else None,
            updated_by=UserType.from_neomodel(post.updated_by.single()) if post.updated_by.single() else None,
            vibe_feed_List=[VibeFeedListType.from_neomodel(vibe) for vibe in sorted_reactions] 
        )
    

class CircleUserPostType(graphene.ObjectType):
    uid = graphene.String()
    relation = graphene.String()
    sub_relation=graphene.String()
    circle_type = graphene.String()
    

    @classmethod
    def from_neomodel(cls, circle):
        uid = circle.get('uid')
        relation = circle.get('relation')
        circle_type = circle.get('circle_type')
        sub_relation = circle.get('sub_relation')
        
        # NOTE:- Review and optimisation required
        if sub_relation:
            return cls(
                uid=uid,
                sub_relation=sub_relation,
                circle_type=circle_type,
                relation=RELATIONUTILLS.get_relation_from_subrelation(sub_relation),
                
            )
        elif relation:
            return cls(
                uid=uid,
                sub_relation=sub_relation,
                circle_type=circle_type,
                relation=RELATIONUTILLS.get_relation_from_subrelation(relation),
                
            )




class ConnectionNoUserPostType(ObjectType):
    uid = graphene.String()
    connection_status = graphene.String()
    circle = graphene.Field(CircleUserPostType)

    @classmethod
    def from_neomodel(cls, connection_node,circle_node):
        uid = connection_node.get('uid')
        connection_status = connection_node.get('connection_status')
        
        return cls(
                uid=uid,  # Access properties using the dictionary-like interface
                connection_status=connection_status,
                circle=CircleUserPostType.from_neomodel(circle_node) 
            )
    
# Postfileurl can be obtain before execution of this query
# This is optimised FeedType
class FeedTestType(ObjectType):
    uid = graphene.String()
    post_title = graphene.String()
    post_text = graphene.String()
    post_type = graphene.String()
    post_file_id = graphene.List(graphene.String)
    post_file_url = graphene.List(FileDetailType)
    privacy = graphene.String()
    vibe_score = graphene.Float()
    created_at = graphene.String()
    updated_at = graphene.String()
    is_deleted = graphene.Boolean()
    comment_count = graphene.Int()
    vibes_count = graphene.Int()
    share_count = graphene.Int()
    created_by = graphene.Field(lambda:UserFeedType)
    my_vibe_details = graphene.List(lambda:ReactionFeedType)
    connection = graphene.Field(lambda:ConnectionFeedType)
    vibe_feed_List=graphene.List(lambda:VibeFeedListType)
    overall_score = graphene.Float()
    total_shares = graphene.Int()


    @classmethod
    def from_neomodel(cls, post_data,reactions_nodes=None,connection_node=None,circle_node=None,user_node=None,profile=None,query_share_count=None, query_overall_score=None):
        created_at_unix=post_data.get('created_at'),
        created_at=datetime.utcfromtimestamp(created_at_unix[0])
        uid=post_data.get('uid'),
        
        post_reaction_manager = PostReactionUtils.get_reaction_manager(uid[0])

        
        if post_reaction_manager:
           
            all_reactions = post_reaction_manager.post_vibe
            sorted_reactions = sorted(all_reactions, key=lambda x: x.get('cumulative_vibe_score', 0), reverse=True)
        else:
            sorted_reactions = IndividualVibeManager.get_data()
        
        overall_score = query_overall_score if query_overall_score is not None else 2.0
        share_count = query_share_count if query_share_count is not None else 0
        
        return cls(
            uid=post_data.get('uid'),
            post_title=post_data.get('post_title'),
            post_text=post_data.get('post_text'),
            post_type=post_data.get('post_type'),
            post_file_id=post_data.get('post_file_id'),
            post_file_url=([FileDetailType(**FileURL.get_file_url(file_id)) for file_id in post_data.get('post_file_id')] if post_data.get('post_file_id') else None),
            privacy=post_data.get('privacy'),
            vibe_score=post_data.get('vibe_score'),
            created_at=time_ago(created_at),
            updated_at=post_data.get('updated_at'),
            is_deleted=post_data.get('is_deleted'),
            comment_count=get_post_comment_count(uid[0]),
            vibes_count=get_post_like_count(uid[0]),
            share_count=post_data.get('share_count'),
            created_by=UserFeedType.from_neomodel(user_node,profile) if user_node and profile else None,

            my_vibe_details=[ReactionFeedType.from_neomodel(r) for r in reactions_nodes] if reactions_nodes else None,
            connection=ConnectionFeedType.from_neomodel(connection_node, circle_node) if connection_node else None,
            vibe_feed_List=[VibeFeedListType.from_neomodel(vibe) for vibe in sorted_reactions],
            overall_score=overall_score,
            total_shares=share_count
        )

    
# This belong to FeedTestType
class ReactionFeedType(ObjectType):
    uid = graphene.String()
    vibe = graphene.Float()
    reaction = graphene.String()
    is_deleted = graphene.Boolean()
    timestamp = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, reaction_node):
        # Check if reaction_node is a dictionary or a Like object
        try:
            unix_timestamp = reaction_node['timestamp']
            return cls(
                uid=reaction_node['uid'],
                vibe=reaction_node['vibe'],
                reaction=reaction_node['reaction'],
                is_deleted=reaction_node['is_deleted'],
                timestamp=datetime.fromtimestamp(unix_timestamp)
            )
        except:
            return cls(
                uid=reaction_node.uid,
                vibe=reaction_node.vibe,
                reaction=reaction_node.reaction,
                is_deleted=reaction_node.is_deleted,
                timestamp=reaction_node.timestamp
            )

# This belong to FeedTestType
class ConnectionFeedType(ObjectType):
    uid = graphene.String()
    connection_status = graphene.String()
    timestamp = graphene.String()
    circle = graphene.Field(lambda:CircleFeedType)

    @classmethod
    def from_neomodel(cls, connection_node, circle_node):
        return cls(
            uid=connection_node['uid'],
            connection_status=connection_node['connection_status'],
            timestamp=str(connection_node['timestamp']),
            circle=CircleFeedType.from_neomodel(circle_node)
        )

# This belong to FeedTestType
class CircleFeedType(ObjectType):
    uid = graphene.String()
    circle_type = graphene.String()
    sub_relation = graphene.String()

    @classmethod
    def from_neomodel(cls, circle_node):
        return cls(
            uid=circle_node['uid'],
            circle_type=circle_node['circle_type'],
            sub_relation=circle_node['sub_relation']
        )

# This belong to FeedTestType
class UserFeedType(ObjectType):
    uid = graphene.String()
    user_id=graphene.String()
    username=graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    is_active = graphene.Boolean()
    user_type = graphene.String()
    profile=graphene.Field(lambda:ProfileFeedType)

    @classmethod
    def from_neomodel(cls, user_node,profile):
        print("Inside user type")
        try:
            return cls(
                uid=user_node['uid'],
                user_id=user_node['user_id'],
                username=user_node['username'] if user_node['username'] else user_node["name"],

                email=user_node['email'],
                first_name=user_node['first_name'],
                last_name=user_node['last_name'],
                is_active=user_node['is_active'],
                user_type=user_node['user_type'],
                profile=ProfileFeedType.from_neomodel(profile)
            )
        except:
            return cls(
                uid=user_node.uid,
                user_id=user_node.user_id,
                username=user_node.username,
                email=user_node.email,
                first_name=user_node.first_name,
                last_name=user_node.last_name,
                is_active=user_node.is_active,
                user_type=user_node.user_type,
                profile=ProfileFeedType.from_neomodel(profile)
            )

# This belong to FeedTestType
class ProfileFeedType(ObjectType):
    uid = graphene.String()
    user_id = graphene.String()
    gender = graphene.String()
    device_id = graphene.String()
    fcm_token = graphene.String()
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
    profile_pic=graphene.List(FileDetailType)
    
    

    @classmethod


    def from_neomodel(cls, profile):
        
        try:
            profile_img_id=profile["profile_pic_id"] if profile["profile_pic_id"] else None

            return cls(
                uid = profile["uid"],
                user_id = profile["user_id"],
                gender = profile["gender"],
                profile_pic_id = profile_img_id,
                profile_pic=([FileDetailType(**generate_presigned_url.generate_file_info(profile_img_id))]) if profile_img_id else None,
            )
        except:
            profile_img_id=profile.profile_pic_id if profile.profile_pic_id else None
            return cls(
                uid = profile.uid,
                user_id = profile.user_id,
                gender = profile.gender,
                profile_pic_id = profile_img_id,
                profile_pic=([FileDetailType(**generate_presigned_url.generate_file_info(profile_img_id))]) if profile_img_id else None,
            )
    


class PostCategoryType(ObjectType):
    title=graphene.String()
    data=graphene.List(lambda:PostRecommendedType)

    @classmethod
    def from_neomodel(cls,user_node=None,detail=None):
            uid=user_node.uid
            params = {"uid": uid}
            data=[]
            

            if detail=="Top Vibes - Meme":
                results3,_ = db.cypher_query(post_queries.get_top_vibes_meme_query)
                for post in results3:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )
                    
            elif detail=="Top Vibes - Podcasts":
                results3,_ = db.cypher_query(post_queries.get_top_vibes_podcasts_query)
                for post in results3:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )

            elif detail=="Top Vibes - Videos":
                results3,_ = db.cypher_query(post_queries.get_top_vibes_videos_query)
                for post in results3:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )
                    
            elif detail=="Top Vibes - Music":
                results3,_ = db.cypher_query(post_queries.get_top_vibes_music_query)
                for post in results3:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )

            elif detail=="Top Vibes - Articles":
                results3,_ = db.cypher_query(post_queries.get_top_vibes_articles_query)
                for post in results3:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )

            elif detail=="Post From Connection":

                results1,_ = db.cypher_query(post_queries.recommended_post_from_connected_user_query, params)
                
                for post in results1:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )

            elif detail=="Popular Post":

                results2,_ = db.cypher_query(post_queries.recommended_post_highest_engagement_score_query)
                for post in results2:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )
                
            elif detail=="Recent Post":
                results3,_ = db.cypher_query(post_queries.recommended_recent_post_query)
                for post in results3:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )

            return cls(
                title=detail,
                data=data
            )




class PostRecommendedType(ObjectType):
    uid = graphene.String()
    post_title = graphene.String()
    post_text = graphene.String()
    post_type = graphene.String()
    post_file_id =graphene.List(graphene.String)
    post_file_url=graphene.List(FileDetailType)
    privacy = graphene.String()
    comment_count = graphene.Int()
    vibes_count=graphene.Int()
    vibe_score = graphene.Float()
    created_at = graphene.String()
    is_deleted = graphene.Boolean()
    # created_by = graphene.Field(UserType)
    

    @classmethod
    def from_neomodel(cls, post):
        created_at_unix=post.get('created_at'),
        created_at=datetime.fromtimestamp(created_at_unix[0])
        uid=post.get('uid'),

        return cls(
            uid=post['uid'],
            post_title=post['post_title'],
            post_text=post['post_text'],
            post_type=post['post_type'],
            post_file_id=post['post_file_id'],
            post_file_url=([FileDetailType(**generate_presigned_url.generate_file_info(file_id)) for file_id in post['post_file_id']] if post['post_file_id'] else None),
            privacy=post['privacy'],
            comment_count=get_post_comment_count(uid[0]),
            vibes_count=get_post_like_count(uid[0]),
            vibe_score=post['vibe_score'],
            created_at=time_ago (created_at),
            is_deleted=post['is_deleted'],
            # created_by=UserType.from_neomodel(post.created_by.single()) if post.created_by.single() else None,
            

        )
    

class VibeAnalyticType(ObjectType):
    vibe_id = graphene.String()
    vibe_name = graphene.String()
    vibes_count = graphene.String()
    vibe_cumulative_score = graphene.String()

    @classmethod
    def from_neomodel(cls, post_uid):
        post_reaction_manager = PostReactionManager.objects.filter(post_uid=post_uid).first()

        if not post_reaction_manager or not post_reaction_manager.post_vibe:
            return []

        all_reactions = post_reaction_manager.post_vibe
        filtered_vibes = [vibe for vibe in all_reactions if vibe.get('vibes_count', 0) != 0]

        # Sort the filtered vibes by cumulative_vibe_score in descending order
        vibes = sorted(filtered_vibes, key=lambda x: x.get('cumulative_vibe_score', 0), reverse=True)


        # Collect all vibe data into a list
        return [
            cls(
                vibe_id=vibe.get('vibes_id'),
                vibe_name=vibe.get('vibes_name'),
                vibes_count=str(vibe.get('vibes_count', 0)),  # Ensure it is a string
                vibe_cumulative_score=str(round(vibe.get('cumulative_vibe_score', 0), 1)),  # Round and convert
            )
            for vibe in vibes
        ]

# version 2 type       
class ConnectionFeedTypeV2(ObjectType):
    uid = graphene.String()
    connection_status = graphene.String()
    timestamp = graphene.String()
    circle = graphene.Field(lambda:CircleFeedType)

    @classmethod
    def from_neomodel(cls, connection_node,circle_node,user_relations,login_user_uid):
        print("connection_node type")
        print(connection_node['uid'])
        return cls(
            uid=connection_node['uid'],
            connection_status=connection_node['connection_status'],
            timestamp=str(connection_node['timestamp']),
            circle=CircleFeedTypeV2.from_neomodel(circle_node,user_relations,login_user_uid)
        )

# This belong to FeedTestType
class CircleFeedTypeV2(ObjectType):
    uid = graphene.String()
    circle_type = graphene.String()
    sub_relation = graphene.String()

    @classmethod
    def from_neomodel(cls, circle_node,user_relations,login_user_uid):
        return cls(
            uid=circle_node['uid'],
            circle_type=user_relations.get(login_user_uid, {}).get("circle_type"),
            sub_relation=user_relations.get(login_user_uid, {}).get("sub_relation")
        )
    

class FeedTestTypeV2(ObjectType):
    uid = graphene.String()
    post_title = graphene.String()
    post_text = graphene.String()
    post_type = graphene.String()
    post_file_id = graphene.List(graphene.String)
    post_file_url = graphene.List(FileDetailType)
    privacy = graphene.String()
    vibe_score = graphene.Float()
    created_at = graphene.String()
    updated_at = graphene.String()
    is_deleted = graphene.Boolean()
    comment_count = graphene.Int()
    vibes_count = graphene.Int()
    share_count = graphene.Int()
    created_by = graphene.Field(lambda:UserFeedType)
    my_vibe_details = graphene.List(lambda:ReactionFeedType)
    connection = graphene.Field(lambda:ConnectionFeedTypeV2)
    vibe_feed_List=graphene.List(lambda:VibeFeedListType)

    @classmethod
    def from_neomodel(cls, post_data,reactions_nodes=None,connection_node=None,circle_node=None,user_node=None,profile=None,user_relations=None,login_user_uid=None):
        print("Inside type")
        created_at_unix=post_data.get('created_at'),
        created_at=datetime.utcfromtimestamp(created_at_unix[0])
        uid=post_data.get('uid'),
        
        post_reaction_manager = PostReactionUtils.get_reaction_manager(uid[0])

        
        if post_reaction_manager:
           
            all_reactions = post_reaction_manager.post_vibe
            sorted_reactions = sorted(all_reactions, key=lambda x: x.get('cumulative_vibe_score', 0), reverse=True)
        else:
            sorted_reactions = IndividualVibeManager.get_data()
        
        
        return cls(
            uid=post_data.get('uid'),
            post_title=post_data.get('post_title'),
            post_text=post_data.get('post_text'),
            post_type=post_data.get('post_type'),
            post_file_id=post_data.get('post_file_id'),
            post_file_url=([FileDetailType(**FileURL.get_file_url(file_id)) for file_id in post_data.get('post_file_id')] if post_data.get('post_file_id') else None),
            privacy=post_data.get('privacy'),
            vibe_score=post_data.get('vibe_score'),
            created_at=time_ago(created_at),
            updated_at=post_data.get('updated_at'),
            is_deleted=post_data.get('is_deleted'),
            comment_count=get_post_comment_count(uid[0]),
            vibes_count=get_post_like_count(uid[0]),
            share_count=post_data.get('share_count'),
            created_by=UserFeedType.from_neomodel(user_node,profile) if user_node and profile else None,

            my_vibe_details=[ReactionFeedType.from_neomodel(r) for r in reactions_nodes] if reactions_nodes else None,
            connection=ConnectionFeedTypeV2.from_neomodel(connection_node,circle_node,user_relations,login_user_uid)if connection_node else None,
            vibe_feed_List=[VibeFeedListType.from_neomodel(vibe) for vibe in sorted_reactions]
        )
    



class PostCategoryTypeV2(ObjectType):
    title=graphene.String()
    data=graphene.List(lambda:PostRecommendedType)

    @classmethod
    def from_neomodel(cls,user_node=None,detail=None):
            uid=user_node.uid
            params = {"uid": uid}
            data=[]
            

            if detail=="Top Vibes - Meme":
                results3,_ = db.cypher_query(post_queries.get_top_vibes_meme_query)
                for post in results3:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )
                    
            elif detail=="Top Vibes - Podcasts":
                results3,_ = db.cypher_query(post_queries.get_top_vibes_podcasts_query)
                for post in results3:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )

            elif detail=="Top Vibes - Videos":
                results3,_ = db.cypher_query(post_queries.get_top_vibes_videos_query)
                for post in results3:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )
                    
            elif detail=="Top Vibes - Music":
                results3,_ = db.cypher_query(post_queries.get_top_vibes_music_query)
                for post in results3:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )

            elif detail=="Top Vibes - Articles":
                results3,_ = db.cypher_query(post_queries.get_top_vibes_articles_query)
                for post in results3:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )

            elif detail=="Post From Connection":

                results1,_ = db.cypher_query(post_queries.recommended_post_from_connected_user_queryV2, params)
                
                for post in results1:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )

            elif detail=="Popular Post":

                results2,_ = db.cypher_query(post_queries.recommended_post_highest_engagement_score_query)
                for post in results2:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )
                
            elif detail=="Recent Post":
                results3,_ = db.cypher_query(post_queries.recommended_recent_post_query)
                for post in results3:
                    post_node = post[0]
                    data.append(
                        PostRecommendedType.from_neomodel(post_node)
                        )

            return cls(
                title=detail,
                data=data
            )
