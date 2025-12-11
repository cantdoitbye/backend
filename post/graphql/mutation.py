# post/graphql/mutations.py

"""
Post GraphQL Mutation Resolvers - API endpoints for modifying post-related data.

This module contains all GraphQL mutation resolvers for creating, updating, and deleting:
- Posts (creation, updates, soft deletion)
- Tags (hashtag management)
- Comments (user discussions)
- Likes/Reactions (engagement actions)
- Shares, Views, Reviews (interaction tracking)
- Saved/Pinned posts (user personalization)

All mutations handle authentication, validation, error handling, and notifications.
Used by: Mobile app, web frontend for all post-related write operations
"""

import graphene
from graphene import Mutation
from graphql import GraphQLError
from neomodel import db
from django.utils import timezone

from post.services.notification_service import NotificationService
from .types import *
from auth_manager.models import Users
from post.models import *
from .inputs import *
from .messages import PostMessages
from graphql_jwt.decorators import login_required,superuser_required
from post.redis import increment_post_comment_count,get_post_comment_count,increment_post_like_count
from vibe_manager.models import IndividualVibe
from community.models import CommunityPost
from post.utils.post_decorator import handle_graphql_post_errors
from auth_manager.Utils.generate_presigned_url import get_valid_image
from post.utils import generate_tag
from vibe_manager.utils import VibeUtils
import asyncio
from post.redis import increment_post_like_count
from user_activity.services.activity_service import ActivityService
from vibe_manager.services.vibe_activity_service import VibeActivityService
from post.services.mention_service import MentionService
from post.utils.feed_history import hide_post_today, mute_creator



class CreatePost(Mutation):
    """
    CreatePost mutation for publishing new posts to the platform.
    
    Handles post creation with media files, privacy settings, and automatic notification
    to user's connections. Validates file IDs and establishes relationships between
    post, creator, and followers for notification delivery.
    
    Used in: Post creation screen, content publishing, media sharing
    Expects: CreatePostInput with title, text, type, privacy, and optional file IDs
    Returns: Success boolean and message, triggers notifications to followers
    Side effects: Creates notification tasks, validates media files, establishes relationships
    """
    # post = graphene.Field(PostType)  # Commented out - returns only success/message
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreatePostInput()

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, input):
        """
        Execute post creation with validation and notification handling.
        
        Process: Validate user auth → validate files → create post → connect relationships
        → gather followers → send notifications asynchronously
        
        Error handling: Returns success=False with error message on any failure
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by = Users.nodes.get(user_id=user_id)
            
            # Validate uploaded files if any are provided
            if input.post_file_id:
                for id in input.post_file_id:
                    valid_id=get_valid_image(id)  # Validate each file ID

            # Extract input data for post creation
            post_title=input.post_title
            post_text=input.post_text
            post_type=input.post_type
            privacy=input.privacy
            post_file_id = input.post_file_id if input.post_file_id else None
            tags = input.tags if input.tags else None
            
            # Create and save the new post
            post = Post(
                post_title=post_title,
                post_text=post_text,
                post_type=post_type,
                privacy=privacy,
                post_file_id=post_file_id,
                tags=tags
            )
            post.save()
            
            # Establish bidirectional relationships between post and creator
            post.created_by.connect(created_by)
            created_by.post.connect(post)
            
            # Extract mentions from post content (title and text)
            from post.utils.mention_extractor import MentionExtractor
            
            # Combine post title and text for mention extraction
            post_content = f"{post_title or ''} {post_text or ''}".strip()
            
            # Extract usernames from post content and convert to UIDs
            mentioned_user_uids = MentionExtractor.extract_and_convert_mentions(post_content)
            
            if mentioned_user_uids:
               MentionService.create_mentions(
                 mentioned_user_uids=mentioned_user_uids,
                 content_type='post',
                 content_uid=post.uid,
                 mentioned_by_uid=created_by.uid,
                 mention_context='post_content'
                )
            # Track post creation activity
            try:
                activity_service = ActivityService()
                activity_service.track_content_interaction(
                    user=user,
                    content_type='post',
                    content_id=str(post.uid),
                    interaction_type='create',
                    ip_address=info.context.META.get('REMOTE_ADDR'),
                    user_agent=info.context.META.get('HTTP_USER_AGENT', ''),
                    metadata={
                        'post_type': post_type,
                        'privacy': privacy,
                        'has_media': bool(post_file_id),
                        'has_tags': bool(tags)
                    }
                )
            except Exception as e:
                # Log error but don't fail the post creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to track post creation activity: {e}")

            if input.reaction and input.vibe:
                try:
                    # Check if user already liked their own post to prevent duplicates
                    check_query = (
                        "MATCH (user:Users {user_id: $user_id})-[:HAS_USER]->(like:Like) "
                        "MATCH (like)-[:HAS_POST]->(post {uid: $post_uid}) "
                        "RETURN like"
                    )
                    check_params = {'user_id': user_id, 'post_uid': post.uid}
                    existing_results, _ = db.cypher_query(check_query, check_params)
                    
                    # Only add vibe if user hasn't already reacted
                    if not existing_results:
                        # Create PostReactionManager for user post if it doesn't exist
                        try:
                            post_reaction_manager = PostReactionManager.objects.get(post_uid=post.uid)
                        except PostReactionManager.DoesNotExist:
                            post_reaction_manager = PostReactionManager(post_uid=post.uid)
                            post_reaction_manager.initialize_reactions()
                            post_reaction_manager.save()

                        # Add this reaction to the aggregated analytics
                        post_reaction_manager.add_reaction(
                            vibes_name=input.reaction,
                            score=input.vibe
                        )
                        post_reaction_manager.save()

                        # Create the individual like record
                        like = Like(
                            reaction=input.reaction,
                            vibe=input.vibe
                        )
                        like.save()
                        
                        # Establish relationships
                        like.user.connect(created_by)
                        post.like.connect(like)

                        # Update engagement metrics in Redis
                        increment_post_like_count(post.uid)
                    
                except Exception as vibe_error:
                    # Log the error but don't fail the post creation
                    print(f"Error adding vibe to user post: {str(vibe_error)}")

            # ============= NOTIFICATION CODE START =============
            # Get all connections of the post creator for notification delivery
            connections = created_by.connection.all()
            recipients = []
            
            for connection in connections:
                # Get the other user in the connection (not the post creator)
                other_user = connection.receiver.single() if connection.created_by.single().uid == created_by.uid else connection.created_by.single()
                if other_user:
                    profile = other_user.profile.single()
                    if profile and profile.device_id:
                        recipients.append({
                            'device_id': profile.device_id,
                            'uid': other_user.uid
                        })
            
            # === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
            # if followers:
            #     notification_service = NotificationService()
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     try:
            #         loop.run_until_complete(notification_service.notifyNewPost(
            #             post_creator_name=created_by.username,
            #             followers=followers,
            #             post_id=post.uid,
            #             post_image_url=FileDetailType(**generate_presigned_url.generate_file_info(post_file_id[0])).url if post_file_id else None
            #         ))
            #     finally:
            #         loop.close()
            
            # === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
            if recipients:
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    service = GlobalNotificationService()
                    service.send(
                        event_type="new_post_from_connection",
                        recipients=recipients,
                        username=created_by.username,
                        post_title=post_title[:50] if post_title else "New post",
                        post_id=post.uid,
                        post_image_url=FileDetailType(**generate_presigned_url.generate_file_info(post_file_id[0])).url if post_file_id else None,
                        sender_uid=created_by.uid,
                        sender_id=created_by.user_id
                    )
                except Exception as e:
                    print(f"Failed to send post notification: {e}")
            # ============= NOTIFICATION CODE END =============
        
            return CreatePost(success=True, message=PostMessages.POST_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreatePost(success=False, message=message)
        

class CreateDebate(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateDebateInput()

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by = Users.nodes.get(user_id=user_id)

            file_ids = []
            if input.image_ids:
                file_ids.extend([fid for fid in input.image_ids if fid])
            if input.video_ids:
                file_ids.extend([fid for fid in input.video_ids if fid])

            if file_ids:
                for fid in file_ids:
                    get_valid_image(fid)

            tags = input.tags or []
            if input.category:
                tags = list(set(tags + [input.category]))

            privacy = (input.circle or 'public').lower()

            post = Post(
                post_title=input.debate_title,
                post_text=input.background_context,
                post_type='debate',
                privacy=privacy,
                post_file_id=file_ids if file_ids else None,
                tags=tags if tags else None
            )
            post.save()

            post.created_by.connect(created_by)
            created_by.post.connect(post)

            content = f"{input.debate_title or ''} {input.background_context or ''}".strip()
            mentioned_user_uids = []
            try:
                from post.utils.mention_extractor import MentionExtractor
                mentioned_user_uids = MentionExtractor.extract_and_convert_mentions(content)
            except Exception:
                mentioned_user_uids = []

            if mentioned_user_uids:
               MentionService.create_mentions(
                 mentioned_user_uids=mentioned_user_uids,
                 content_type='post',
                 content_uid=post.uid,
                 mentioned_by_uid=created_by.uid,
                 mention_context='post_content'
                )

            try:
                activity_service = ActivityService()
                activity_service.track_content_interaction(
                    user=user,
                    content_type='post',
                    content_id=str(post.uid),
                    interaction_type='create',
                    ip_address=info.context.META.get('REMOTE_ADDR'),
                    user_agent=info.context.META.get('HTTP_USER_AGENT', ''),
                    metadata={
                        'post_type': 'debate',
                        'privacy': privacy,
                        'has_media': bool(file_ids),
                        'has_tags': bool(tags)
                    }
                )
            except Exception:
                pass

            if input.reaction and input.vibe:
                try:
                    check_query = (
                        "MATCH (user:Users {user_id: $user_id})-[:HAS_USER]->(like:Like) "
                        "MATCH (like)-[:HAS_POST]->(post {uid: $post_uid}) "
                        "RETURN like"
                    )
                    check_params = {'user_id': user_id, 'post_uid': post.uid}
                    existing_results, _ = db.cypher_query(check_query, check_params)
                    if not existing_results:
                        try:
                            post_reaction_manager = PostReactionManager.objects.get(post_uid=post.uid)
                        except PostReactionManager.DoesNotExist:
                            post_reaction_manager = PostReactionManager(post_uid=post.uid)
                            post_reaction_manager.initialize_reactions()
                            post_reaction_manager.save()

                        post_reaction_manager.add_reaction(
                            vibes_name=input.reaction,
                            score=input.vibe
                        )
                        post_reaction_manager.save()

                        like = Like(reaction=input.reaction, vibe=input.vibe)
                        like.save()
                        like.user.connect(created_by)
                        post.like.connect(like)
                        increment_post_like_count(post.uid)
                except Exception:
                    pass

            return CreateDebate(success=True, message=PostMessages.POST_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateDebate(success=False, message=message)

class CreateDebateAnswer(Mutation):
    comment = graphene.Field(CommentType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateDebateAnswerInput()

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, input):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Authentication Failure")

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            target_post = Post.nodes.get(uid=input.post_uid)

            file_ids = input.answer_file_id if input.answer_file_id else None
            stance = (input.stance or '').lower()
            if stance not in ['for','against']:
                return CreateDebateAnswer(comment=None, success=False, message="Invalid stance")
            comment = Comment(
                content=input.content,
                comment_file_id=file_ids,
                is_answer=True,
                stance=stance
            )
            comment.save()

            comment.user.connect(user_node)
            target_post.comment.connect(comment)
            comment.post.connect(target_post)

            increment_post_comment_count(target_post.uid)

            if input.content:
                from post.utils.mention_extractor import MentionExtractor
                mentioned_user_uids = MentionExtractor.extract_and_convert_mentions(input.content)
                if mentioned_user_uids:
                    current_user_uid = Users.nodes.get(user_id=info.context.user.id).uid
                    MentionService.create_mentions(
                        mentioned_user_uids=mentioned_user_uids,
                        content_type='comment',
                        content_uid=comment.uid,
                        mentioned_by_uid=current_user_uid,
                        mention_context='debate_answer'
                    )

            try:
                ActivityService.track_content_interaction(
                    user=user_node,
                    content_id=target_post.uid,
                    content_type='post',
                    interaction_type='comment',
                    metadata={
                        'comment_id': comment.uid,
                        'is_debate_answer': True,
                        'post_type': getattr(target_post, 'post_type', None)
                    }
                )
            except Exception:
                pass

            return CreateDebateAnswer(comment=CommentType.from_neomodel(comment, info), success=True, message=PostMessages.POST_COMMENT_CREATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateDebateAnswer(comment=None, success=False, message=message)


class UpdatePost(Mutation):
    """
    UpdatePost mutation for modifying existing posts.
    
    Allows post owners to update title, text, type, privacy settings, and other fields.
    Maintains audit trail by updating the 'updated_by' relationship and timestamp.
    
    Used in: Post editing screen, content management, privacy adjustments
    Expects: UpdatePostInput with post UID and fields to update
    Returns: Updated PostType object, success status, and message
    Security: Only post creators can update their posts (enforced by relationship)
    """
    post = graphene.Field(PostType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdatePostInput()

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, input):
        """
        Execute post update with field validation and audit tracking.
        
        Process: Validate auth → find post → update fields → update relationships → save
        Note: File validation commented out, may need to be re-enabled
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            updated_by = Users.nodes.get(user_id=user_id)
            
            # File validation currently commented out
            # for id in input.post_file_id:
            #     valid_id=get_valid_image(id)

            # Find and update the post
            post = Post.nodes.get(uid=input.uid)
            for key, value in input.items():
                setattr(post, key, value)  # Dynamically set updated fields
            
            post.save()  # Triggers automatic timestamp update via model's save method
            post.updated_by.connect(updated_by)  # Track who made the update
            
            # Track content modification activity
            try:
                ActivityService.track_content_interaction(
                    user=updated_by,
                    content_id=post.uid,
                    content_type='post',
                    interaction_type='update',
                    metadata={
                        'updated_fields': list(input.keys()),
                        'post_title': getattr(post, 'title', None),
                        'post_type': getattr(post, 'post_type', None)
                    }
                )
            except Exception as e:
                # Log activity tracking error but don't fail the post update
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to track post update activity: {str(e)}")
            
            return UpdatePost(post=PostType.from_neomodel(post,info), success=True, message="Post updated successfully.")
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdatePost(post=None, success=False, message=message)
        

class UpdateDebate(Mutation):
    post = graphene.Field(PostType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateDebateInput()

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            updated_by = Users.nodes.get(user_id=user_id)

            post = Post.nodes.get(uid=input.uid)
            if post.post_type != 'debate':
                raise GraphQLError("Invalid content type for debate update")

            if input.debate_title is not None:
                post.post_title = input.debate_title
            if input.background_context is not None:
                post.post_text = input.background_context
            if input.circle is not None:
                post.privacy = (input.circle or 'public').lower()

            file_ids = None
            combined_ids = []
            if input.image_ids:
                combined_ids.extend([fid for fid in input.image_ids if fid])
            if input.video_ids:
                combined_ids.extend([fid for fid in input.video_ids if fid])
            if combined_ids:
                for fid in combined_ids:
                    get_valid_image(fid)
                file_ids = combined_ids
            if file_ids is not None:
                post.post_file_id = file_ids

            if input.tags is not None or input.category is not None:
                tags = list(post.tags or [])
                if input.tags is not None:
                    tags = list(set((input.tags or [])))
                if input.category:
                    tags = list(set(tags + [input.category]))
                post.tags = tags

            post.save()
            post.updated_by.connect(updated_by)

            try:
                ActivityService.track_content_interaction(
                    user=updated_by,
                    content_id=post.uid,
                    content_type='post',
                    interaction_type='update',
                    metadata={
                        'updated_fields': [k for k in input.keys()],
                        'post_type': 'debate'
                    }
                )
            except Exception:
                pass

            return UpdateDebate(post=PostType.from_neomodel(post,info), success=True, message="Debate updated successfully.")
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateDebate(post=None, success=False, message=message)

class UpdateDebateAnswer(Mutation):
    comment = graphene.Field(CommentType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateDebateAnswerInput()

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            comment = Comment.nodes.get(uid=input.uid)
            if not getattr(comment, 'is_answer', False):
                raise GraphQLError("Not a debate answer")

            if 'content' in input:
                comment.content = input['content']
            if 'is_deleted' in input:
                comment.is_deleted = input['is_deleted']
            if 'answer_file_id' in input and input['answer_file_id'] is not None:
                comment.comment_file_id = input['answer_file_id']
            if 'stance' in input and input['stance'] is not None:
                s = str(input['stance']).lower()
                if s in ['for','against']:
                    comment.stance = s

            comment.save()

            return UpdateDebateAnswer(comment=CommentType.from_neomodel(comment), success=True, message=PostMessages.POST_COMMENT_UPDATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateDebateAnswer(comment=None, success=False, message=message)


class DeletePost(Mutation):
    """
    DeletePost mutation for soft-deleting posts (sets is_deleted=True).
    
    Implements soft deletion to preserve data integrity and relationships.
    Only allows post creators to delete their own posts for security.
    
    Used in: Post management, content removal, user post cleanup
    Expects: DeleteInput with post UID
    Returns: Success status and message
    Security: Verifies post ownership before allowing deletion
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()
    
    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, input):
        """
        Execute soft deletion with ownership verification.
        
        Process: Validate auth → find post → verify ownership → soft delete → save
        Security check: Ensures only post creator can delete the post
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            
            post = Post.nodes.get(uid=input.uid)
            created_by=post.created_by.single()

            # Security check: Only post creator can delete
            if created_by.user_id != str(user_id):
                return DeletePost(success=False, message=PostMessages.POST_DELETE_PERMISSION_DENIED)

            # Soft delete (preserve data and relationships)
            post.is_deleted = True
            post.save()
            
            # Track content deletion activity
            try:
                user_node = Users.nodes.get(user_id=user_id)
                ActivityService.track_content_interaction(
                    user=user_node,
                    content_id=post.uid,
                    content_type='post',
                    interaction_type='delete',
                    metadata={
                        'post_title': getattr(post, 'title', None),
                        'post_type': getattr(post, 'post_type', None),
                        'deletion_type': 'soft_delete'
                    }
                )
            except Exception as e:
                # Log activity tracking error but don't fail the post deletion
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to track post deletion activity: {str(e)}")
            
            return DeletePost(success=True, message=PostMessages.POST_DELETED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeletePost(success=False, message=message)


class DeleteDebate(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')

            post = Post.nodes.get(uid=input.uid)
            if post.post_type != 'debate':
                return DeleteDebate(success=False, message=PostMessages.POST_DELETE_PERMISSION_DENIED)

            created_by = post.created_by.single()
            if created_by.user_id != str(user_id):
                return DeleteDebate(success=False, message=PostMessages.POST_DELETE_PERMISSION_DENIED)

            post.is_deleted = True
            post.save()

            try:
                user_node = Users.nodes.get(user_id=user_id)
                ActivityService.track_content_interaction(
                    user=user_node,
                    content_id=post.uid,
                    content_type='post',
                    interaction_type='delete',
                    metadata={
                        'post_type': 'debate',
                        'deletion_type': 'soft_delete'
                    }
                )
            except Exception:
                pass

            return DeleteDebate(success=True, message=PostMessages.POST_DELETED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeleteDebate(success=False, message=message)

class DeleteDebateAnswer(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            comment = Comment.nodes.get(uid=input.uid)
            if not getattr(comment, 'is_answer', False):
                return DeleteDebateAnswer(success=False, message=PostMessages.POST_DELETE_PERMISSION_DENIED)

            comment.delete()
            return DeleteDebateAnswer(success=True, message=PostMessages.POST_COMMENT_DELETED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeleteDebateAnswer(success=False, message=message)


class HidePostFromFeed(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        post_uid = graphene.String(required=True)

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, post_uid):
        try:
            payload = info.context.payload
            user_id = str(payload.get('user_id'))
            hide_post_today(user_id, post_uid)
            return HidePostFromFeed(success=True, message="Post hidden from your feed today")
        except Exception as e:
            return HidePostFromFeed(success=False, message=str(e))


class MuteCreatorInFeed(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        creator_uid = graphene.String(required=True)

    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, creator_uid):
        try:
            payload = info.context.payload
            user_id = str(payload.get('user_id'))
            mute_creator(user_id, creator_uid)
            return MuteCreatorInFeed(success=True, message="Creator muted for your feed")
        except Exception as e:
            return MuteCreatorInFeed(success=False, message=str(e))


class CreateTag(Mutation):
    """
    CreateTag mutation for adding hashtags and keywords to posts.
    
    Creates tag entities with arrays of tag names and associates them with posts.
    Supports content categorization and discovery through tagging system.
    
    Used in: Post creation, content organization, hashtag management
    Expects: CreateTagInput with tag names array and post UID
    Returns: Created TagType object with relationships
    Access: Currently restricted to superusers (may need review)
    """
    tag = graphene.Field(TagType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateTagInput()

    @login_required
    @superuser_required  # Note: Consider if this restriction is appropriate
    def mutate(self, info, input):
        """
        Create tag entity and establish post relationships.
        
        Process: Validate auth → get post → create tag → connect relationships
        Creates bidirectional relationships between tag and post
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by = Users.nodes.get(user_id=user_id)

            post = Post.nodes.get(uid=input.post_uid)
            
            # Create tag with array of names
            tag = Tag(
                names=input.get('names', [])
            )
            tag.save()
            
            # Establish relationships
            tag.created_by.connect(created_by)
            tag.post.connect(post)
            post.tag.connect(tag)
            
            return CreateTag(tag=TagType.from_neomodel(tag), success=True, message=PostMessages.POST_TAG_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateTag(tag=None, success=False, message=message)


class UpdateTag(Mutation):
    """
    UpdateTag mutation for modifying existing tag information.
    
    Allows updating tag names and deletion status for content management.
    
    Used in: Tag management, content moderation, hashtag updates
    Expects: UpdateTagInput with tag UID and fields to update
    Returns: Updated TagType object
    Access: Restricted to superusers
    """
    tag = graphene.Field(TagType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateTagInput()

    @login_required
    @superuser_required
    def mutate(self, info, input):
        """Execute tag update with field validation."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            # updated_by = Users.nodes.get(user_id=user_id)  # Commented out - not used
            
            tag = Tag.nodes.get(uid=input.uid)
            
            # Update provided fields
            if 'names' in input:
                tag.names = input['names']
            if 'is_deleted' in input:
                tag.is_deleted = input['is_deleted']
            
            tag.save()
            
            return UpdateTag(tag=TagType.from_neomodel(tag), success=True, message=PostMessages.POST_TAG_UPDATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateTag(tag=None, success=False, message=message)


class DeleteTag(Mutation):
    """
    DeleteTag mutation for permanently removing tag entities.
    
    Performs hard deletion of tags (unlike posts which are soft-deleted).
    
    Used in: Tag cleanup, content moderation, hashtag management
    Expects: DeleteInput with tag UID
    Returns: Success status and message
    Access: Restricted to superusers
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()
    
    @login_required
    @superuser_required
    def mutate(self, info, input):
        """Execute permanent tag deletion."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            deleted_by = Users.nodes.get(user_id=user_id)  # Track who deleted (variable not used currently)

            tag = Tag.nodes.get(uid=input.uid)
            tag.delete()  # Hard delete
            
            return DeleteTag(success=True, message=PostMessages.POST_TAG_DELETED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeleteTag(success=False, message=message)


class CreateComment(Mutation):
    """
    CreateComment mutation for adding user comments to posts.
    NOW SUPPORTS: Optional nested replies via parent_comment_uid
    
    Creates comment entities, updates engagement metrics, and sends notifications
    to post creators. Supports both regular posts and community posts.
    
    Used in: Post detail screen, comment sections, user discussions
    Expects: CreateCommentInput with post UID and comment content, optional parent_comment_uid
    Returns: Created CommentType object with relationships
    Side effects: Increments comment count in Redis, sends notifications
    """
    comment = graphene.Field(CommentType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateCommentInput()

    @handle_graphql_post_errors   
    @login_required
    def mutate(self, info, input):
        """
        Create comment with engagement tracking and notifications.
        Process: Validate auth → find post (regular or community) → create comment
        → update metrics → send notification to post creator
        NOW ALSO: Handle optional parent comment for replies
        """
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Authentication Failure")

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        
        try:
            try:
                target_post = Post.nodes.get(uid=input.post_uid)
            except Post.DoesNotExist:
                target_post = CommunityPost.nodes.get(uid=input.post_uid)
            print(f"🔍 DEBUG: Error getting related_post: {target_post}")

            parent_comment = None
            if hasattr(input, 'parent_comment_uid') and input.parent_comment_uid:
                try:
                    parent_comment = Comment.nodes.get(uid=input.parent_comment_uid)
                    
                    # Ensure parent comment belongs to the same post
                    # parent_post = parent_comment.post.single()
                    # if not parent_post or parent_post.uid != target_post.uid:
                      # Use Cypher query to validate parent comment belongs to same post
                    validation_query = """
                    MATCH (comment:Comment {uid: $comment_uid})
                    MATCH (post {uid: $post_uid})
                    WHERE (comment)-[:HAS_POST]->(post) OR (post)-[:HAS_COMMENT]->(comment)
                    RETURN count(*) as relationship_exists
                    """

                    result, _ = db.cypher_query(validation_query, {
                        "comment_uid": input.parent_comment_uid,
                        "post_uid": input.post_uid
                    })

                    if not result or result[0][0] == 0:
                        print(f"🔍 DEBUG: Parent comment validation passed via Cypher")  
                        raise GraphQLError("Parent comment does not belong to the specified post")
                    
                    # Check if parent comment is deleted
                    if parent_comment.is_deleted:
                        raise GraphQLError("Cannot reply to a deleted comment")
                    
                    # Optional: Limit reply depth to prevent excessive nesting
                    if hasattr(parent_comment, 'get_reply_depth') and parent_comment.get_reply_depth() >= 5:
                        raise GraphQLError("Maximum reply depth reached")
                        
                except Comment.DoesNotExist:
                    raise GraphQLError("Parent comment not found")
                        
            comment_file_id = input.comment_file_id if input.comment_file_id else None
            # EXISTING LOGIC - Create and save comment
            comment = Comment(
                content=input.content,
                comment_file_id=comment_file_id
            )
            comment.save()
            print(f"🔍 DEBUG: Error getting comment related_post: {comment}")

            
            comment.user.connect(user_node)
            target_post.comment.connect(comment)
            # comment.post.connect(target_post) 
            print(f"🔍 DEBUG: About to call comment.post.connect(target_post)")
            if isinstance(target_post, Post):
               comment.post.connect(target_post)
            elif isinstance(target_post, CommunityPost):
               comment.community_post.connect(target_post)
            # try:
            #    comment.post.connect(target_post)
            #    print(f"🔍 DEBUG: Comment-Post connection established successfully")
            # except Exception as e:
            #    print(f"🔍 DEBUG: ERROR in comment.post.connect(target_post): {e}")
            #    print(f"🔍 DEBUG: Error type: {type(e)}")
            #    raise e
            
            if parent_comment:
                comment.parent_comment.connect(parent_comment)

            # EXISTING LOGIC - Increment comment count in Redis for performance
            increment_post_comment_count(target_post.uid)

            # Extract mentions from comment content
            if comment and input.content:
                from post.utils.mention_extractor import MentionExtractor
                
                # Extract usernames from comment content and convert to UIDs
                mentioned_user_uids = MentionExtractor.extract_and_convert_mentions(input.content)
                
                if mentioned_user_uids:
                
                # Get current user's UID
                     current_user_uid = Users.nodes.get(user_id=info.context.user.id).uid
                
                    # Create mentions for the comment
                     MentionService.create_mentions(
                        mentioned_user_uids=mentioned_user_uids,
                        content_type='comment',
                        content_uid=comment.uid,
                        mentioned_by_uid=current_user_uid,
                        mention_context='comment_content'
                     )

            # ============= NOTIFICATION CODE START (CreateComment) =============
            # === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
            # post_creator = None
            # if isinstance(target_post, Post):
            #     post_creator = target_post.created_by.single()
            # elif isinstance(target_post, CommunityPost):
            #     post_creator = target_post.creator.single()
            # 
            # if post_creator and isinstance(post_creator, Users) and post_creator.uid != user_node.uid:
            #     if isinstance(post_creator, Users):
            #         profile = post_creator.profile.single()
            #         if profile and profile.device_id:
            #             notification_service = NotificationService()
            #             loop = asyncio.new_event_loop()
            #             asyncio.set_event_loop(loop)
            #             try:
            #                 loop.run_until_complete(notification_service.notifyNewComment(
            #                     commenter_name=user_node.username,
            #                     post_creator_device_id=profile.device_id,
            #                     post_id=target_post.uid,
            #                     comment_id=comment.uid,
            #                     comment_content=input.content[:50] + "..." if len(input.content) > 50 else input.content
            #                 ))
            #             finally:
            #                 loop.close()
            
            # === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
            # Send notification to post creator about new comment
            post_creator = None
            if isinstance(target_post, Post):
                post_creator = target_post.created_by.single()
            elif isinstance(target_post, CommunityPost):
                post_creator = target_post.creator.single()
            
            if post_creator and isinstance(post_creator, Users) and post_creator.uid != user_node.uid:
                profile = post_creator.profile.single()
                if profile and profile.device_id:
                    try:
                        from notification.global_service import GlobalNotificationService
                        
                        service = GlobalNotificationService()
                        # Truncate long comments for notification
                        comment_preview = input.content[:50] + "..." if len(input.content) > 50 else input.content
                        
                        service.send(
                            event_type="post_comment",
                            recipients=[{
                                'device_id': profile.device_id,
                                'uid': post_creator.uid
                            }],
                            username=user_node.username,
                            comment_text=comment_preview,
                            post_id=target_post.uid,
                            comment_id=comment.uid,
                            sender_uid=user_node.uid,
                            sender_id=user_node.user_id
                        )
                    except Exception as e:
                        print(f"Failed to send comment notification: {e}")

            # Notify parent comment author if this is a reply
            if parent_comment:
                parent_comment_author = parent_comment.user.single()
                if (parent_comment_author and 
                    parent_comment_author.uid != user_node.uid and 
                    parent_comment_author.uid != post_creator.uid):
                    
                    parent_profile = parent_comment_author.profile.single()
                    if parent_profile and parent_profile.device_id:
                        try:
                            from notification.global_service import GlobalNotificationService
                            
                            service = GlobalNotificationService()
                            reply_preview = f"Replied: {input.content[:50]}..." if len(input.content) > 50 else f"Replied: {input.content}"
                            
                            service.send(
                                event_type="post_comment",
                                recipients=[{
                                    'device_id': parent_profile.device_id,
                                    'uid': parent_comment_author.uid
                                }],
                                username=user_node.username,
                                comment_text=reply_preview,
                                post_id=target_post.uid,
                                comment_id=comment.uid,
                                sender_uid=user_node.uid,
                                sender_id=user_node.user_id
                            )
                        except Exception as e:
                            print(f"Failed to send reply notification: {e}")
            # ============= NOTIFICATION CODE END =============

            # Track comment creation activity
            try:
                ActivityService.track_content_interaction(
                    user=user_node,
                    content_id=target_post.uid,
                    content_type='post',
                    interaction_type='comment',
                    metadata={
                        'comment_id': comment.uid,
                        'comment_content_length': len(input.content),
                        'is_reply': parent_comment is not None,
                        'parent_comment_id': parent_comment.uid if parent_comment else None,
                        'post_type': getattr(target_post, 'post_type', None)
                    }
                )
            except Exception as e:
                # Log activity tracking error but don't fail the comment creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to track comment creation activity: {str(e)}")
            
            return CreateComment(comment=CommentType.from_neomodel(comment, info), success=True, message=PostMessages.POST_COMMENT_CREATED)
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateComment(comment=None, success=False, message=message)

class UpdateComment(Mutation):
    """
    UpdateComment mutation for modifying existing comments.
    
    Allows users to edit their comment content and deletion status.
    
    Used in: Comment editing, content moderation, comment management
    Expects: UpdateCommentInput with comment UID and fields to update
    Returns: Updated CommentType object
    Security: Should verify comment ownership (not currently implemented)
    """
    comment = graphene.Field(CommentType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateCommentInput()

    @handle_graphql_post_errors   
    @login_required
    def mutate(self, info, input):
        """Execute comment update with field validation."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)  # Track user (variable not used currently)

            comment = Comment.nodes.get(uid=input.uid)
            
            # Update provided fields
            if 'content' in input:
                comment.content = input['content']
            if 'is_deleted' in input:
                comment.is_deleted = input['is_deleted']
            
            comment.save()

            return UpdateComment(comment=CommentType.from_neomodel(comment), success=True, message=PostMessages.POST_COMMENT_UPDATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateComment(comment=None, success=False, message=message)
        

class DeleteComment(Mutation):
    """
    DeleteComment mutation for permanently removing comments.
    
    Performs hard deletion of comment entities.
    
    Used in: Comment management, content moderation, user cleanup
    Expects: DeleteInput with comment UID
    Returns: Success status and message
    Security: Should verify comment ownership (not currently implemented)
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()

    @handle_graphql_post_errors   
    @login_required
    def mutate(self, info, input):
        """Execute permanent comment deletion."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)  # Track user (variable not used currently)

            comment = Comment.nodes.get(uid=input.uid)
            comment.delete()  # Hard delete
            
            return DeleteComment(success=True, message=PostMessages.POST_COMMENT_DELETED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeleteComment(success=False, message=message)


class CreateLike(Mutation):
    """
    CreateLike mutation for adding reactions/vibes to posts.
    
    Creates like entities with reaction types and vibe scores, updates analytics,
    and manages aggregated reaction data for posts. Supports both regular and 
    community posts with complex vibe scoring system.
    
    Used in: Reaction buttons, post engagement, vibe analytics
    Expects: CreateLikeInput with post UID, reaction type, and vibe score
    Returns: Created LikeType object
    Side effects: Updates PostReactionManager analytics, increments Redis counters
    Note: Contains complex analytics logic that needs review and optimization
    """
    like = graphene.Field(LikeType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateLikeInput()

    @handle_graphql_post_errors   
    @login_required
    def mutate(self, info, input):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Authentication Failure")
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        
        try:
            try:
                post = Post.nodes.get(uid=input.post_uid)
            except Post.DoesNotExist:
                post = CommunityPost.nodes.get(uid=input.post_uid)

            query = (
                "MATCH (user:Users {user_id: $user_id})-[r:HAS_USER]->(like:Like) "
                "MATCH (like)-[:HAS_POST]->(post {uid: $post_uid}) "
                "RETURN like"
            )
            params = {'user_id': user_id, 'post_uid': input.post_uid}
            results, _ = db.cypher_query(query, params)
            existing_like_node = [Like.inflate(row[0]) for row in results]

            post_reaction_manager, _ = PostReactionManager.objects.get_or_create(
                post_uid=input.post_uid,
                defaults={}
            )
            if not post_reaction_manager.post_vibe:
                post_reaction_manager.initialize_reactions()

            message = ""
            if existing_like_node:
                like = existing_like_node[0]
                old_reaction = like.reaction
                old_vibe = like.vibe

                post_reaction_manager.update_reaction(
                    old_vibes_name=old_reaction,
                    new_vibes_name=input.reaction,
                    old_score=old_vibe,
                    new_score=input.vibe
                )

                like.reaction = input.reaction
                like.vibe = input.vibe
                like.save()
                message = PostMessages.POST_REACTION_UPDATED
            else:
                post_reaction_manager.add_reaction(
                    vibes_name=input.reaction,
                    score=input.vibe
                )
                like = Like(reaction=input.reaction, vibe=input.vibe)
                like.save()
                like.user.connect(user_node)
                post.like.connect(like)
                increment_post_like_count(post.uid)
                message = PostMessages.POST_REACTION_CREATED
                
                # ============= NOTIFICATION CODE START =============
                # Notify post creator about new vibe reaction (only for new likes, not updates)
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    post_creator = post.created_by.single()
                    if post_creator and post_creator.uid != user_node.uid:
                        creator_profile = post_creator.profile.single()
                        if creator_profile and creator_profile.device_id:
                            service = GlobalNotificationService()
                            service.send(
                                event_type="vibe_reaction_on_post",
                                recipients=[{
                                    'device_id': creator_profile.device_id,
                                    'uid': post_creator.uid
                                }],
                                username=user_node.username,
                                vibe_type=input.reaction,
                                post_id=post.uid
                            )
                except Exception as e:
                    print(f"Failed to send vibe reaction notification: {e}")
                # ============= NOTIFICATION CODE END =============

            post_reaction_manager.save()

            try:
                ActivityService.track_content_interaction(
                    user=user_node,
                    content_type='post',
                    content_id=post.uid,
                    interaction_type='like',
                    metadata={
                        'reaction': input.reaction,
                        'vibe_score': input.vibe,
                        'like_id': like.uid
                    }
                )
                post_owner = post.created_by.single()
                VibeActivityService.track_vibe_sending(
                    sender=user_node,
                    receiver_id=post_owner.user_id if post_owner else None,
                    vibe_data={
                        'vibe_id': like.uid,
                        'vibe_name': input.reaction,
                        'vibe_type': 'individual',
                        'category': 'post_reaction'
                    },
                    vibe_score=input.vibe,
                    ip_address=info.context.META.get('REMOTE_ADDR'),
                    user_agent=info.context.META.get('HTTP_USER_AGENT', ''),
                    metadata={
                        'post_id': post.uid,
                        'like_id': like.uid,
                        'post_type': getattr(post, 'post_type', 'unknown')
                    }
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to track like activity: {str(e)}")

            return CreateLike(like=LikeType.from_neomodel(like), success=True, message=message)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateLike(like=None, success=False, message=message)


class UpdateLike(Mutation):
    """
    UpdateLike mutation for modifying existing reactions.
    
    Allows users to change their reaction type, vibe score, or deletion status.
    
    Used in: Reaction management, user preference updates
    Expects: UpdateLikeInput with like UID and fields to update
    Returns: Updated LikeType object
    Note: Should update PostReactionManager analytics when vibe scores change
    """
    like = graphene.Field(LikeType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateLikeInput()

    @handle_graphql_post_errors  
    @login_required
    def mutate(self, info, input):
        """Execute reaction update with field validation."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)  # Track user (variable not used currently)

            like = Like.nodes.get(uid=input.uid)
            
            # Update provided fields
            if 'reaction' in input:
                like.reaction = input['reaction']
            if 'vibe' in input:
                like.vibe = input['vibe']
            if 'is_deleted' in input:
                like.is_deleted = input['is_deleted']

            like.save()

            # Track vibe activity for updated reaction
            try:
                # Get the post associated with this like
                post = like.post.single()
                if post:
                    post_owner = post.created_by.single()
                    
                    # Track vibe update activity
                    VibeActivityService.track_vibe_sending(
                        sender=user_node,
                        receiver_id=post_owner.user_id if post_owner else None,
                        vibe_data={
                            'vibe_id': like.uid,
                            'vibe_name': like.reaction,
                            'vibe_type': 'individual',
                            'category': 'post_reaction_update'
                        },
                        vibe_score=like.vibe,
                        ip_address=info.context.META.get('REMOTE_ADDR'),
                        user_agent=info.context.META.get('HTTP_USER_AGENT', ''),
                        metadata={
                            'post_id': post.uid,
                            'like_id': like.uid,
                            'post_type': getattr(post, 'post_type', 'unknown'),
                            'action': 'update'
                        }
                    )
            except Exception as e:
                # Log error but don't fail the like update
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to track vibe update activity: {str(e)}")

            return UpdateLike(like=LikeType.from_neomodel(like), success=True, message=PostMessages.POST_REACTION_UPDATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateLike(like=None, success=False, message=message)


class DeleteLike(Mutation):
    """
    DeleteLike mutation for removing reactions from posts.
    
    Permanently deletes like/reaction entities.
    
    Used in: Reaction removal, user preference changes
    Expects: DeleteInput with like UID
    Returns: Success status and message
    Note: Should update PostReactionManager analytics when reactions are deleted
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()

    @handle_graphql_post_errors   
    @login_required
    def mutate(self, info, input):
        """Execute permanent reaction deletion."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)  # Track user (variable not used currently)

            like = Like.nodes.get(uid=input.uid)
            
            # Track vibe activity for deleted reaction (before deletion)
            try:
                # Get the post associated with this like before deletion
                post = like.post.single()
                if post:
                    post_owner = post.created_by.single()
                    
                    # Track vibe deletion activity
                    VibeActivityService.track_vibe_sending(
                        sender=user_node,
                        receiver_id=post_owner.user_id if post_owner else None,
                        vibe_data={
                            'vibe_id': like.uid,
                            'vibe_name': like.reaction,
                            'vibe_type': 'individual',
                            'category': 'post_reaction_delete'
                        },
                        vibe_score=like.vibe,
                        ip_address=info.context.META.get('REMOTE_ADDR'),
                        user_agent=info.context.META.get('HTTP_USER_AGENT', ''),
                        metadata={
                            'post_id': post.uid,
                            'like_id': like.uid,
                            'post_type': getattr(post, 'post_type', 'unknown'),
                            'action': 'delete'
                        }
                    )
            except Exception as e:
                # Log error but don't fail the like deletion
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to track vibe deletion activity: {str(e)}")
            
            like.delete()  # Hard delete
            
            return DeleteLike(success=True, message=PostMessages.POST_REACTION_DELETED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeleteLike(success=False, message=message)


class CreatePostShare(Mutation):
    """
    CreatePostShare mutation for tracking when users share posts.
    
    Records sharing activity to different platforms for analytics and viral tracking.
    
    Used in: Share buttons, viral analytics, platform distribution tracking
    Expects: CreatePostShareInput with post UID and share platform type
    Returns: Created PostShareType object
    Access: Currently restricted to superusers (may need review for general use)
    """
    post_share = graphene.Field(PostShareType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreatePostShareInput()
    
    @login_required
    @superuser_required  # Note: Consider if this restriction is appropriate
    def mutate(self, info, input):
        """Create share record with platform tracking."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            post = Post.nodes.get(uid=input.post_uid)

            # Create share record
            post_share = PostShare(
                share_type=input.share_type 
            )
            post_share.save()
            
            # Establish relationships
            post_share.post.connect(post)
            post_share.user.connect(user_node)
            post.postshare.connect(post_share)

            # Track activity for analytics
            try:
                ActivityService.track_content_interaction(
                    user=user_node,
                    content_type='post',
                    content_id=post.uid,
                    interaction_type='share',
                    metadata={
                        'share_type': input.share_type,
                        'share_id': post_share.uid
                    }
                )
            except Exception as e:
                # Log error but don't fail the share creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to track share activity: {str(e)}")

            return CreatePostShare(post_share=PostShareType.from_neomodel(post_share), success=True, message=PostMessages.POST_SHARE)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreatePostShare(post_share=None, success=False, message=message)
        

class CreatePostView(Mutation):
    """
    CreatePostView mutation for tracking post impressions.
    
    Records when users view posts for analytics and engagement tracking.
    Essential for calculating reach metrics and content performance.
    
    Used in: Automatic view tracking, analytics, feed algorithms
    Expects: CreatePostViewInput with post UID
    Returns: Created PostViewType object
    Usage: Should be called automatically when posts are displayed
    """
    post_view = graphene.Field(PostViewType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreatePostViewInput()
        
    @handle_graphql_post_errors  
    @login_required
    def mutate(self, info, input):
        """Create view record for analytics tracking."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            post = Post.nodes.get(uid=input.post_uid)

            # Create view record
            post_view = PostView()
            post_view.save()
            
            # Establish relationships
            post_view.post.connect(post)
            post_view.user.connect(user_node)
            post.view.connect(post_view)
            
            # Track activity for analytics
            try:
                ActivityService.track_content_interaction(
                    user=user_node,
                    content_type='post',
                    content_id=post.uid,
                    interaction_type='view',
                    metadata={
                        'view_id': post_view.uid
                    }
                )
            except Exception as e:
                # Log error but don't fail the view creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to track view activity: {str(e)}")
            
            return CreatePostView(post_view=PostViewType.from_neomodel(post_view), success=True, message=PostMessages.POST_VIEW)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreatePostView(post_view=None, success=False, message=message)


class CreateSavedPost(Mutation):
    """
    CreateSavedPost mutation for bookmarking posts.
    
    Allows users to save posts to their personal collection for later viewing.
    
    Used in: Bookmark functionality, saved posts collection, content curation
    Expects: CreateSavedPostInput with post UID
    Returns: Created SavedPostType object
    Access: Currently restricted to superusers (should be available to all users)
    """
    saved_post = graphene.Field(SavedPostType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateSavedPostInput()

    @login_required
    @superuser_required  # Note: Should this be restricted to superusers?
    def mutate(self, info, input):
        """Create saved post record for user's collection."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            post = Post.nodes.get(uid=input.post_uid)

            # Create saved post record
            saved_post = SavedPost()
            saved_post.save()
            
            # Establish relationships
            saved_post.post.connect(post)
            saved_post.user.connect(user_node)
            post.postsave.connect(saved_post)

            return CreateSavedPost(saved_post=SavedPostType.from_neomodel(saved_post), success=True, message=PostMessages.POST_SAVED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateSavedPost(saved_post=None, success=False, message=message)


class DeleteSavedPost(Mutation):
    """
    DeleteSavedPost mutation for removing posts from saved collection.
    
    Allows users to unsave previously bookmarked posts.
    
    Used in: Bookmark management, saved posts cleanup
    Expects: DeleteInput with saved post UID
    Returns: Success status and message
    Access: Currently restricted to superusers (should be available to all users)
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()
    
    @login_required
    @superuser_required  # Note: Should this be restricted to superusers?
    def mutate(self, info, input):
        """Remove post from user's saved collection."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)  # Track user (variable not used currently)

            saved_post = SavedPost.nodes.get(uid=input.uid)
            saved_post.delete()  # Hard delete
            
            return DeleteSavedPost(success=True, message=PostMessages.POST_UNSAVED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeleteSavedPost(success=False, message=message)


class CreateReview(Mutation):
    """
    CreateReview mutation for detailed post feedback.
    
    Creates comprehensive reviews with numerical ratings and text feedback.
    Different from comments as reviews include structured rating systems.
    
    Used in: Content evaluation, detailed feedback, quality assessment
    Expects: CreateReviewInput with post UID, rating (1-5), and review text
    Returns: Created ReviewType object
    Access: Currently restricted to superusers
    """
    review = graphene.Field(ReviewType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateReviewInput()

    @login_required
    @superuser_required
    def mutate(self, info, input):
        """Create structured review with rating and feedback."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            post = Post.nodes.get(uid=input.post_uid)

            # Create review with rating and text
            review = Review(
                rating=input.rating,
                review_text=input.review_text
            )
            review.save()
            
            # Establish relationships
            review.post.connect(post)
            review.user.connect(user_node)
            post.review.connect(review)

            return CreateReview(review=ReviewType.from_neomodel(review), success=True, message=PostMessages.POST_REVIEW_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateReview(review=None, success=False, message=message)


class UpdateReview(Mutation):
    """
    UpdateReview mutation for modifying existing reviews.
    
    Allows users to update their review ratings and text content.
    
    Used in: Review management, feedback updates, content revision
    Expects: UpdateReviewInput with review UID and fields to update
    Returns: Updated ReviewType object
    Access: Currently restricted to superusers
    """
    review = graphene.Field(ReviewType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateReviewInput()

    @login_required
    @superuser_required
    def mutate(self, info, input):
        """Execute review update with field validation."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)  # Track user (variable not used currently)

            review = Review.nodes.get(uid=input.uid)
            
            # Update provided fields
            if 'rating' in input:
                review.rating = input['rating']
            if 'review_text' in input:
                review.review_text = input['review_text']

            review.save()

            return UpdateReview(review=ReviewType.from_neomodel(review), success=True, message=PostMessages.POST_REVIEW_UPDATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateReview(review=None, success=False, message=message)


class DeleteReview(Mutation):
    """
    DeleteReview mutation for removing review entries.
    
    Permanently deletes review entities from the system.
    
    Used in: Review cleanup, content moderation, user management
    Expects: DeleteInput with review UID
    Returns: Success status and message
    Access: Currently restricted to superusers
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()
    
    @login_required
    @superuser_required
    def mutate(self, info, input):
        """Execute permanent review deletion."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)  # Track user (variable not used currently)

            review = Review.nodes.get(uid=input.uid)
            review.delete()  # Hard delete
            
            return DeleteReview(success=True, message=PostMessages.POST_REVIEW_DELETED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeleteReview(success=False, message=message)
        

class CreatePinedPost(Mutation):
    """
    CreatePinedPost mutation for highlighting important posts on profiles.
    
    Allows users to pin posts to the top of their profile for prominence.
    Pinned posts remain visible regardless of chronological order.
    
    Used in: Profile management, content highlighting, important post promotion
    Expects: CreatePinedPostInput with post UID
    Returns: Created PinedPostType object
    Access: Currently restricted to superusers (should be available to post owners)
    """
    pined_post = graphene.Field(PinedPostType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreatePinedPostInput()

    @login_required
    @superuser_required  # Note: Should post owners be able to pin their own posts?
    def mutate(self, info, input):
        """Create pinned post record for profile highlighting."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            post = Post.nodes.get(uid=input.post_uid)

            # Create pinned post record with default name
            pined_post = PinedPost(name="pin")
            pined_post.save()
            
            # Establish relationships
            pined_post.post.connect(post)
            pined_post.user.connect(user_node)
            post.pinpost.connect(pined_post)

            return CreatePinedPost(pined_post=PinedPostType.from_neomodel(pined_post), success=True, message=PostMessages.POST_PINNED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreatePinedPost(pined_post=None, success=False, message=message)


class DeletePinedPost(Mutation):
    """
    DeletePinedPost mutation for removing pinned status from posts.
    
    Allows users to unpin previously highlighted posts from their profile.
    
    Used in: Profile management, pin cleanup, content reorganization
    Expects: DeleteInput with pinned post UID
    Returns: Success status and message
    Access: Currently restricted to superusers
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()
        
    @login_required
    @superuser_required
    def mutate(self, info, input):
        """Remove pinned status from post."""
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)  # Track user (variable not used currently)

            pined_post = PinedPost.nodes.get(uid=input.uid)
            pined_post.delete()  # Hard delete
            
            return DeletePinedPost(success=True, message=PostMessages.POST_UNPINNED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeletePinedPost(success=False, message=message)


class SendVibeToComment(Mutation):
    """
    Sends a vibe reaction to a comment using existing vibe system.
    """
    success = graphene.Boolean()
    message = graphene.String()
    comment_vibe = graphene.Field('post.graphql.types.CommentVibeType')
    
    class Arguments:
        input = SendVibeToCommentInput()
    
    @handle_graphql_post_errors
    @login_required
    def mutate(self, info, input):
        try:
            # Get authenticated user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Validate vibe intensity (1.0 to 5.0)
            if not (1.0 <= input.vibe_intensity <= 5.0):
                return SendVibeToComment(
                    success=False,
                    message="Vibe intensity must be between 1.0 and 5.0"
                )
            try:
                clean_intensity = round(float(input.vibe_intensity), 2)
            except (ValueError, TypeError):
                return SendVibeToComment(
                    success=False,
                    message="Invalid vibe intensity format"
                )
            if not (1.0 <= clean_intensity <= 5.0):
               return SendVibeToComment(
                   success=False,
                   message="Vibe intensity must be between 1.0 and 5.0"
                )
            
            # Get the individual vibe from PostgreSQL
            try:
                individual_vibe = IndividualVibe.objects.get(id=input.individual_vibe_id)
            except IndividualVibe.DoesNotExist:
                return SendVibeToComment(
                    success=False,
                    message="Invalid vibe selected"
                )
            
            # Find the comment
            try:
                comment = Comment.nodes.get(uid=input.comment_uid)
            except Comment.DoesNotExist:
                return SendVibeToComment(
                    success=False,
                    message="Comment not found"
                )
            
            # Check if user has already reacted to this comment with the same vibe
            existing_vibe = None
            try:
                # Use Cypher query to check for existing vibe reaction (any vibe type from this user)
                query = """
                MATCH (u:Users {uid: $user_uid})-[:REACTED_BY]-(cv:CommentVibe)<-[:HAS_VIBE_REACTION]-(c:Comment {uid: $comment_uid})
                WHERE cv.is_active = true
                RETURN cv
                """
                results, _ = db.cypher_query(query, {
                    'user_uid': user_node.uid,
                    'comment_uid': input.comment_uid
                })
                
                if results:
                    # Update existing vibe instead of creating new one
                    existing_vibe_node = CommentVibe.inflate(results[0][0])
                    existing_vibe_node.individual_vibe_id = input.individual_vibe_id  # Update to new vibe type
                    existing_vibe_node.vibe_name = individual_vibe.name_of_vibe
                    existing_vibe_node.vibe_intensity = clean_intensity
                    existing_vibe_node.reaction_type = "vibe"
                    existing_vibe_node.timestamp = timezone.now()
                    existing_vibe_node.is_active = True
                    existing_vibe_node.save()
                    
                    return SendVibeToComment(
                        success=True,
                        message="Vibe updated successfully",
                        comment_vibe=CommentVibeType.from_neomodel(existing_vibe_node)
                    )
            except Exception as e:
                # Continue if query fails - better to allow duplicate than block valid reactions
                pass
            
            # Store vibe reaction in Neo4j
            comment_vibe = CommentVibe(
                individual_vibe_id=input.individual_vibe_id,
                vibe_name=individual_vibe.name_of_vibe,
                vibe_intensity=clean_intensity,
                reaction_type="vibe"
            )
            comment_vibe.save()
            
            # Connect to user and comment using correct relationship names
            comment_vibe.reacted_by.connect(user_node)
            
            # Connect from comment side (CommentVibe uses RelationshipFrom)
            comment.vibe_reactions.connect(comment_vibe)
            
            # Update user's vibe score using existing system
            # Use the weightage values from IndividualVibe
            vibe_score_multiplier = clean_intensity / 5.0  # Convert to 0.0-1.0 multiplier
            
            # Apply weightages from your vibe system
            adjusted_score = (
                individual_vibe.weightage_iaq + 
                individual_vibe.weightage_iiq + 
                individual_vibe.weightage_ihq + 
                individual_vibe.weightage_isq
            ) / 4.0 * vibe_score_multiplier
            
            VibeUtils.onVibeCreated(user_node, individual_vibe.name_of_vibe, adjusted_score)
            
            # ============= NOTIFICATION CODE START (SendVibeToComment) =============
            # Send notification to comment author about vibe reaction
            comment_author = comment.user.single()
            if comment_author and comment_author.uid != user_node.uid:  # Don't notify yourself
                author_profile = comment_author.profile.single()
                if author_profile and author_profile.device_id:
                    try:
                        from notification.global_service import GlobalNotificationService
                        
                        # Get the post this comment belongs to
                        post = comment.post.single() if hasattr(comment, 'post') else comment.community_post.single()
                        
                        service = GlobalNotificationService()
                        service.send(
                            event_type="comment_vibe_reaction",
                            recipients=[{
                                'device_id': author_profile.device_id,
                                'uid': comment_author.uid
                            }],
                            username=user_node.username,
                            vibe_name=individual_vibe.name_of_vibe,
                            post_id=post.uid if post else comment.uid,
                            comment_id=comment.uid
                        )
                    except Exception as e:
                        print(f"Failed to send comment vibe notification: {e}")
            # ============= NOTIFICATION CODE END =============
            
            return SendVibeToComment(
                success=True,
                message="Vibe sent to comment successfully!",
                comment_vibe=CommentVibeType.from_neomodel(comment_vibe)
            )
            
        except Exception as e:
            return SendVibeToComment(
                success=False,
                message=f"Error sending vibe: {str(e)}"
            )


class Mutation(graphene.ObjectType):
    """
    Main GraphQL Mutation class exposing all post-related write operations.
    
    This class aggregates all mutation resolvers and makes them available through
    the GraphQL API. Each field corresponds to a specific mutation operation
    for different aspects of the post system.
    
    Used by: Frontend applications, mobile apps, admin interfaces
    Structure: Groups mutations by functionality (posts, tags, comments, etc.)
    """
    
    # Post CRUD operations
    Create_post = CreatePost.Field()        # Create new posts
    update_post=UpdatePost.Field()          # Modify existing posts
    delete_post=DeletePost.Field()          # Soft delete posts

    # Debate CRUD operations
    create_debate = CreateDebate.Field()
    update_debate = UpdateDebate.Field()
    delete_debate = DeleteDebate.Field()
    create_debate_answer = CreateDebateAnswer.Field()
    update_debate_answer = UpdateDebateAnswer.Field()
    delete_debate_answer = DeleteDebateAnswer.Field()

    # Tag management operations
    add_tag=CreateTag.Field()               # Add hashtags to posts
    edit_tag=UpdateTag.Field()              # Modify existing tags
    delete_tag=DeleteTag.Field()            # Remove tags

    # Comment interaction operations
    create_post_comment=CreateComment.Field()      # Add comments to posts
    update_post_comment=UpdateComment.Field()      # Edit existing comments
    delete_post_comment=DeleteComment.Field()      # Remove comments
    send_vibe_to_comment=SendVibeToComment.Field()  # Send vibes to comments

    # Reaction/Like operations
    create_post_reaction=CreateLike.Field()         # Add reactions/vibes to posts
    update_post_reaction=UpdateLike.Field()         # Modify existing reactions
    delete_post_reaction=DeleteLike.Field()         # Remove reactions

    # Sharing operations
    post_share=CreatePostShare.Field()              # Track post sharing

    # Bookmarking operations
    save_post=CreateSavedPost.Field()               # Save posts to collection
    unsave_post=DeleteSavedPost.Field()             # Remove from saved collection

    # Review system operations
    create_post_review=CreateReview.Field()         # Add detailed reviews
    update_post_review=UpdateReview.Field()         # Modify existing reviews
    delete_post_review=DeleteReview.Field()         # Remove reviews

    # Profile highlighting operations
    pin_post=CreatePinedPost.Field()                # Pin posts to profile
    unpin_post=DeletePinedPost.Field()              # Remove pinned status

    # Analytics operations
    view_post=CreatePostView.Field()                # Track post views
    # Feed controls
    hide_post_from_feed = HidePostFromFeed.Field()
    mute_creator_in_feed = MuteCreatorInFeed.Field()
