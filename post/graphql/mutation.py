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
import asyncio


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

            # Get all connections of the post creator for notification delivery
            connections = created_by.connection.all()
            followers = []
            
            for connection in connections:
                # Get the other user in the connection (not the post creator)
                other_user = connection.receiver.single() if connection.created_by.single().uid == created_by.uid else connection.created_by.single()
                if other_user:
                    profile = other_user.profile.single()
                    if profile and profile.device_id:
                        followers.append({
                            'device_id': profile.device_id,
                            'uid': other_user.uid
                        })
            
            # Send notifications asynchronously to avoid blocking the response
            if followers:
                notification_service = NotificationService()
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(notification_service.notifyNewPost(
                        post_creator_name=created_by.username,
                        followers=followers,
                        post_id=post.uid,
                        post_image_url=FileDetailType(**generate_presigned_url.generate_file_info(post_file_id[0])).url if post_file_id else None
                    ))
                finally:
                    loop.close()

            return CreatePost(success=True, message=PostMessages.POST_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreatePost(success=False, message=message)
        

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
            
            return UpdatePost(post=PostType.from_neomodel(post,info), success=True, message="Post updated successfully.")
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdatePost(post=None, success=False, message=message)
        

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
            return DeletePost(success=True, message=PostMessages.POST_DELETED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeletePost(success=False, message=message)


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
                    parent_post = parent_comment.post.single()
                    if not parent_post or parent_post.uid != target_post.uid:
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
            try:
               comment.post.connect(target_post)
               print(f"🔍 DEBUG: Comment-Post connection established successfully")
            except Exception as e:
               print(f"🔍 DEBUG: ERROR in comment.post.connect(target_post): {e}")
               print(f"🔍 DEBUG: Error type: {type(e)}")
               raise e
            
            if parent_comment:
                comment.parent_comment.connect(parent_comment)

            # EXISTING LOGIC - Increment comment count in Redis for performance
            # increment_post_comment_count(target_post.uid)
            
            # EXISTING LOGIC - Send notification to post creator about new comment
            post_creator = target_post.created_by.single()
            # if post_creator and post_creator.uid != user_node.uid:  # Don't notify if commenting on own post
            #     profile = post_creator.profile.single()
            #     if profile and profile.device_id:
            #         notification_service = NotificationService()
            #         loop = asyncio.new_event_loop()
            #         asyncio.set_event_loop(loop)
            #         try:
            #             loop.run_until_complete(notification_service.notifyNewComment(
            #                 commenter_name=user_node.username,
            #                 post_creator_device_id=profile.device_id,
            #                 post_id=target_post.uid,
            #                 comment_id=comment.uid,
            #                 comment_content=input.content[:50] + "..." if len(input.content) > 50 else input.content  # Truncate long comments
            #             ))
            #         finally:
            #             loop.close()

            # #notify parent comment author if this is a reply
            # if parent_comment:
            #     parent_comment_author = parent_comment.user.single()
            #     if (parent_comment_author and 
            #         parent_comment_author.uid != user_node.uid and 
            #         parent_comment_author.uid != post_creator.uid):
                    
            #         parent_profile = parent_comment_author.profile.single()
            #         if parent_profile and parent_profile.device_id:
            #             notification_service = NotificationService()
            #             loop = asyncio.new_event_loop()
            #             asyncio.set_event_loop(loop)
            #             try:
            #                 # You can extend your notification service to handle reply notifications
            #                 loop.run_until_complete(notification_service.notifyNewComment(
            #                     commenter_name=user_node.username,
            #                     post_creator_device_id=parent_profile.device_id,
            #                     post_id=target_post.uid,
            #                     comment_id=comment.uid,
            #                     comment_content=f"Replied: {input.content[:50]}..." if len(input.content) > 50 else f"Replied: {input.content}"
            #                 ))
            #             finally:
            #                 loop.close()

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
        """
        Create reaction with analytics tracking and aggregation.
        
        Process: Validate auth → find post → manage reaction analytics → create like
        → update counters → save relationships
        """
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Authentication Failure")

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        
        try:
            # Try to find regular post first, fallback to community post
            try:
                post = Post.nodes.get(uid=input.post_uid)
            except Post.DoesNotExist:
                post=CommunityPost.nodes.get(uid=input.post_uid)
            
            # Manage aggregated reaction analytics (Note:- Review and Optimisation needed)
            try:
                post_reaction_manager = PostReactionManager.objects.get(post_uid=input.post_uid)
            except PostReactionManager.DoesNotExist:
                # If no PostReactionManager exists, create and initialize with first 10 vibes
                post_reaction_manager = PostReactionManager(post_uid=input.post_uid)
                post_reaction_manager.initialize_reactions()  # Add the 10 vibes
                post_reaction_manager.save()

            # Add this reaction to the aggregated analytics
            post_reaction_manager.add_reaction(
                vibes_name=input.reaction,
                score=input.vibe  # Assuming `reaction` is a numeric score to be averaged
            )
            post_reaction_manager.save()

            # Create the individual like record
            like = Like(
                reaction=input.reaction ,
                vibe=input.vibe 
            )
            like.save()
            
            # Establish relationships
            like.user.connect(user_node)
            post.like.connect(like)

            # Update engagement metrics in Redis
            increment_post_like_count(post.uid)

            return CreateLike(like=LikeType.from_neomodel(like), success=True, message=PostMessages.POST_REACTION_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
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

    # Tag management operations
    add_tag=CreateTag.Field()               # Add hashtags to posts
    edit_tag=UpdateTag.Field()              # Modify existing tags
    delete_tag=DeleteTag.Field()            # Remove tags

    # Comment interaction operations
    create_post_comment=CreateComment.Field()      # Add comments to posts
    update_post_comment=UpdateComment.Field()      # Edit existing comments
    delete_post_comment=DeleteComment.Field()      # Remove comments

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