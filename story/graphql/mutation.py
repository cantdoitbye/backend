# story/graphql/mutation.py

# This file defines GraphQL mutations for the story module
# Handles: Story CRUD operations, interactions (comments, reactions, views), sharing
# Used by: Mobile app, web interface for all story-related user actions
# Security: All mutations require authentication, ownership validation where needed

import graphene
from graphene import Mutation
from graphql import GraphQLError
from .types import *
from auth_manager.models import Users
from story.models import *
from .input import *
from .message import StoryMessages
from graphql_jwt.decorators import login_required, superuser_required
import graphene
from story.redis import add_story_view, store_user_data_in_cache, create_story_cache_key, check_story_cache_key_exists
from story.utils.story_validation import CreateStorySchema
from story.utils.custom_decorator import validate_different_users, handle_graphql_story_errors
from auth_manager.Utils.generate_presigned_url import get_valid_image
import asyncio
from story.services.notification_service import NotificationService
from user_activity.services.activity_service import ActivityService
from vibe_manager.services.vibe_activity_service import VibeActivityService
from post.services.mention_service import MentionService


# Story creation mutation - creates new story with media and privacy settings
# Used by: Story creation flow, content publishing
# Features: Media validation, privacy controls, Redis caching, push notifications
# Security: Requires authentication, validates file ownership
class CreateStory(Mutation):
    success = graphene.Boolean()    # Operation success status
    message = graphene.String()     # User-friendly response message
    
    class Arguments:
        input = CreateStoryInput()  # Story creation data (title, content, privacy, media)
    
    @handle_graphql_story_errors    # Custom error handling decorator
    @login_required                 # JWT authentication required
    def mutate(self, info, input):
        """
        Creates a new story with content, media, and privacy settings.
        Validates media ownership, sets up Redis caching for 24-hour expiration,
        and sends push notifications to user's connections.
        Used by story creation interfaces across mobile and web apps.
        """
        try:
            # Authentication validation
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Extract user information from JWT token
            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by = Users.nodes.get(user_id=user_id)

            # Validate input data using custom schema
            CreateStorySchema(**input)
            
            # Validate media file ownership if image provided
            # Prevents users from using files they don't own
            if input.story_image_id:
                valid_id = get_valid_image(input.story_image_id)

            # Create new story instance with provided data
            story = Story(
                title=input.get('title'), 
                content=input.get('content'), 
                captions=input.get('captions'),
                privacy=input.get('privacy'),          # Privacy circle settings
                story_image_id=input.get('story_image_id'),
            )
           
            # Save story to Neo4j database
            story.save()
            
            # Establish relationships in graph database
            story.created_by.connect(created_by)
            created_by.story.connect(story)

            # Extract mentions from story content (title, content, captions)
            from post.utils.mention_extractor import MentionExtractor
            
            # Combine story title, content, and captions for mention extraction
            story_content = f"{input.get('title', '')} {input.get('content', '')} {input.get('captions', '')}".strip()
            
            print("Extracting mentions from story content...")
            mentioned_user_uids = MentionExtractor.extract_and_convert_mentions(story_content)
            
            if mentioned_user_uids:
                # Create mentions for the story
                MentionService.create_mentions(
                    mentioned_user_uids=mentioned_user_uids,
                    content_type='story',
                    content_uid=story.uid,
                    mentioned_by_uid=created_by.uid,
                    mention_context='story_content'
                )
                
                # ============= NOTIFICATION CODE START (Story Mention) =============
                # Send notification to mentioned users
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    # Collect mentioned users with device IDs
                    mention_recipients = []
                    for mentioned_uid in mentioned_user_uids:
                        try:
                            mentioned_user = Users.nodes.get(uid=mentioned_uid)
                            if mentioned_user.uid != created_by.uid:  # Don't notify yourself
                                profile = mentioned_user.profile.single()
                                if profile and profile.device_id:
                                    mention_recipients.append({
                                        'device_id': profile.device_id,
                                        'uid': mentioned_user.uid
                                    })
                        except Exception as e:
                            print(f"Error getting mentioned user {mentioned_uid}: {e}")
                    
                    if mention_recipients:
                        service = GlobalNotificationService()
                        service.send(
                            event_type="story_mention",
                            recipients=mention_recipients,
                            username=created_by.username,
                            story_id=story.uid
                        )
                except Exception as e:
                    print(f"Failed to send story mention notification: {e}")
                # ============= NOTIFICATION CODE END =============

            # Track story creation activity
            try:
                ActivityService.track_content_interaction(
                    user=created_by,
                    content_type='story',
                    content_id=story.uid,
                    interaction_type='create',
                    metadata={
                        'story_title': story.title,
                        'privacy': story.privacy,
                        'has_image': bool(story.story_image_id)
                    }
                )
            except Exception as e:
                # Log error but don't fail story creation
                import logging
                logging.error(f"Failed to track story creation activity: {str(e)}")

            # Set up Redis cache for 24-hour story expiration
            create_story_cache_key(story.uid)

            # Prepare push notifications for user's connections
            # Get all social connections of the story creator
            connections = created_by.connection.all()
            followers = []
            seen_users = set()  # Prevent duplicate notifications
            
            # Process connections to build notification list
            for connection in connections:
                # Determine the other user in the bidirectional connection
                other_user = connection.receiver.single() if connection.created_by.single().uid == created_by.uid else connection.created_by.single()
                
                # Add unique users with valid device IDs for notifications
                if other_user and other_user.uid not in seen_users:
                    seen_users.add(other_user.uid)
                    profile = other_user.profile.single()
                    
                    # Only include users with FCM device IDs
                    if profile and profile.device_id:
                        followers.append({
                            'device_id': profile.device_id,
                            'uid': other_user.uid
                        })

            # ============= NOTIFICATION CODE START =============
            # === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
            # if followers:
            #     notification_service = NotificationService()
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     try:
            #         loop.run_until_complete(notification_service.notifyNewStory(
            #             story_creator_name=created_by.username,
            #             followers=followers,
            #             story_id=story.uid,
            #             story_image_url=story.story_image_id
            #         ))
            #     finally:
            #         loop.close()
            
            # === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
            if followers:
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    service = GlobalNotificationService()
                    service.send(
                        event_type="new_story_from_connection",
                        recipients=followers,
                        username=created_by.username,
                        story_id=story.uid,
                        story_thumbnail_url=story.story_image_id
                    )
                except Exception as e:
                    print(f"Failed to send story notification: {e}")
            # ============= NOTIFICATION CODE END =============
            
            return CreateStory(success=True, message=StoryMessages.STORY_CREATED)
            
        except Exception as error:
            # Extract error message for user-friendly response
            message = getattr(error, 'message', str(error))
            return CreateStory(success=False, message=message)

# Story update mutation - modifies existing story content and settings
# Used by: Story editing interfaces, content management
# Security: Only story creator can update, validates ownership
class UpdateStory(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateStoryInput()  # Update data (uid + fields to modify)
    
    @handle_graphql_story_errors 
    @login_required
    def mutate(self, info, input):
        """
        Updates an existing story's content, media, or settings.
        Only the story creator can perform updates.
        Validates media ownership for new images.
        Used by story editing and management interfaces.
        """
        try:
            # Authentication check
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Get current user information
            payload = info.context.payload
            user_id = payload.get('user_id')
            updated_by = Users.nodes.get(user_id=user_id)
    
            # Fetch story to update
            story = Story.nodes.get(uid=input.uid)

            # Ownership validation - only creator can update
            if(story.created_by.single().email != updated_by.email):
                return UpdateStory(success=False, message=StoryMessages.STORY_NOT_CREATED_BY_USER)
            
            # Validate new media file if provided
            if input.story_image_id:
                valid_id = get_valid_image(input.story_image_id)

            # Update story fields dynamically
            for key, value in input.items():
                setattr(story, key, value)
            
            # Save changes (triggers automatic timestamp update)
            story.save()
            
            # Track story update activity
            try:
                ActivityService.track_content_interaction(
                    user=updated_by,
                    content_type='story',
                    content_id=story.uid,
                    interaction_type='update',
                    metadata={
                        'story_title': story.title,
                        'updated_fields': list(input.keys())
                    }
                )
            except Exception as e:
                # Log error but don't fail story update
                import logging
                logging.error(f"Failed to track story update activity: {str(e)}")
            
            return UpdateStory(success=True, message=StoryMessages.STORY_UPDATED)
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateStory(story=None, success=False, message=message)

# Story deletion mutation - removes story and all related data
# Used by: Story management, content moderation, user cleanup
# Security: Only story creator can delete, validates ownership
class DeleteStory(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()  # Contains story UID to delete
    
    @handle_graphql_story_errors 
    @login_required
    def mutate(self, info, input):
        """
        Permanently deletes a story and all associated data.
        Only the story creator can delete their stories.
        Removes story from database and clears Redis cache.
        Used by content management and user cleanup operations.
        """
        try:
            # Authentication validation
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Get current user
            payload = info.context.payload
            user_id = payload.get('user_id')
            deleted_by = Users.nodes.get(user_id=user_id)
            
            # Fetch story to delete
            story = Story.nodes.get(uid=input.uid)
            
            # Ownership validation - only creator can delete
            if(story.created_by.single().email != deleted_by.email):
                return DeleteStory(success=False, message=StoryMessages.STORY_NOT_CREATED_BY_USER)
            
            # Permanently delete story (cascades to relationships)
            story.delete()
            
            return DeleteStory(success=True, message=StoryMessages.STORY_DELETED)
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteStory(success=False, message=message)

# Comment creation mutation - adds user comment to story
# Used by: Comment interfaces, user engagement features
# Features: Story expiration checking, relationship creation
class CreateStoryComment(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = StoryCommentInput()  # Comment data (story_uid, content)

    @handle_graphql_story_errors 
    @login_required    
    def mutate(self, info, input):
        """
        Creates a new comment on a story.
        Validates story exists and hasn't expired (24-hour window).
        Establishes relationships between comment, story, and user.
        Used by comment interfaces and engagement features.
        """
        try:
            # Authentication check
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Get current user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)
            
            story_uid = input.story_uid 
            
            # Check if story still exists (not expired)
            if check_story_cache_key_exists(story_uid) == False:
                raise Exception("Story does not exist or has expired")

            # Get story and create comment
            story = Story.nodes.get(uid=story_uid)
            comment = StoryComment(
                content=input.get('content', ''),
            )
            comment.save()
            
            # Establish graph relationships
            comment.story.connect(story)
            comment.user.connect(user)
            story.storycomment.connect(comment)
            
            # Track story comment activity
            try:
                ActivityService.track_content_interaction(
                    user=user,
                    content_type='story',
                    content_id=story.uid,
                    interaction_type='comment',
                    metadata={
                        'comment_id': comment.uid,
                        'comment_content': comment.content[:100],  # First 100 chars
                        'story_title': story.title
                    }
                )
            except Exception as e:
                # Log error but don't fail comment creation
                import logging
                logging.error(f"Failed to track story comment activity: {str(e)}")
            
            return CreateStoryComment(success=True, message=StoryMessages.STORY_COMMENT_CREATED)
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateStoryComment(success=False, message=message)

# Comment update mutation - modifies existing comment content
# Used by: Comment editing, content moderation
# Security: Only comment author can update
class UpdateStoryComment(Mutation):
    story_comment = graphene.Field(StoryCommentType)  # Updated comment data
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = UpdateStoryCommentInput()  # Update data (uid + content)

    @handle_graphql_story_errors        
    @login_required
    def mutate(self, info, input):
        """
        Updates content of an existing story comment.
        Only the comment author can perform updates.
        Used by comment editing and moderation interfaces.
        """
        try:
            # Authentication validation
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Get current user
            payload = info.context.payload
            user_id = payload.get('user_id')
            updated_by = Users.nodes.get(user_id=user_id)
        
            # Fetch comment to update
            storycomment = StoryComment.nodes.get(uid=input.uid)
            
            # Ownership validation - only comment author can update
            original_user = storycomment.user.single().uid
            payload_user = updated_by.uid
            
            if payload_user != original_user:
                raise GraphQLError("This Story doesnot belong to you")

            # Update comment fields dynamically
            for key, value in input.items():
                setattr(storycomment, key, value)

            # Save changes (triggers timestamp update)
            storycomment.save()
            
            return UpdateStoryComment(
                story_comment=StoryCommentType.from_neomodel(storycomment), 
                success=True, 
                message=StoryMessages.STORY_COMMENT_UPDATED
            )
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateStoryComment(story_comment=None, success=False, message=message)

# Comment deletion mutation - removes comment permanently
# Used by: Content moderation, user comment management
# Security: Only comment author can delete
class DeleteStoryComment(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
       input = DeleteInput()  # Comment UID to delete
    
    @handle_graphql_story_errors 
    @login_required
    def mutate(self, info, input):
        """
        Permanently deletes a story comment.
        Used by content moderation and user comment management.
        Removes comment and all associated relationships.
        """
        try:
            # Authentication check
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                    
            # Get current user (for potential ownership validation)
            payload = info.context.payload
            user_id = payload.get('user_id')
            deleted_by = Users.nodes.get(user_id=user_id)
            
            # Delete comment (should include ownership validation)
            storycomment = StoryComment.nodes.get(uid=input.uid)
            storycomment.delete()
            
            return DeleteStoryComment(success=True, message=StoryMessages.STORY_COMMENT_DELETED)
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteStoryComment(success=False, message=message)

# Reaction creation mutation - adds emotional reaction to story
# Used by: Reaction interfaces, vibe tracking, engagement features
# Features: Vibe aggregation, reaction analytics, story expiration checking
class CreateStoryReaction(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = StoryReactionInput()  # Reaction data (story_uid, reaction, vibe_score)
    
    @handle_graphql_story_errors 
    @login_required    
    def mutate(self, info, input):
        """
        Creates a new emotional reaction (vibe) on a story.
        Updates aggregated vibe analytics for story ranking.
        Validates story exists and hasn't expired.
        Used by reaction interfaces and engagement tracking.
        """
        try:
            # Authentication validation
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Get current user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)
            
            story_uid = input.story_uid 

            # Validate story exists and hasn't expired
            if check_story_cache_key_exists(story_uid) == False:
                raise Exception("Story does not exist or has expired")
            
            story = Story.nodes.get(uid=story_uid)
            
            # Check if user already reacted to this story to prevent duplicates
            from neomodel import db
            check_query = (
                "MATCH (user:Users {user_id: $user_id})-[:HAS_USER]->(reaction:StoryReaction) "
                "MATCH (reaction)-[:HAS_STORY]->(story:Story {uid: $story_uid}) "
                "RETURN reaction"
            )
            check_params = {'user_id': user_id, 'story_uid': story_uid}
            existing_results, _ = db.cypher_query(check_query, check_params)
            
            # Update aggregated reaction analytics
            # Get or create StoryReactionManager for vibe tracking
            try:
                story_reaction_manager = StoryReactionManager.objects.get(story_uid=input.story_uid)
            except StoryReactionManager.DoesNotExist:
                # Initialize with default 10 vibes if first reaction
                story_reaction_manager = StoryReactionManager(story_uid=input.story_uid)
                story_reaction_manager.initialize_reactions()
                story_reaction_manager.save()

            message = ""
            if existing_results:
                # User already reacted - update existing reaction
                existing_reaction = StoryReaction.inflate(existing_results[0][0])
                old_reaction = existing_reaction.reaction
                old_vibe = existing_reaction.vibe
                
                # Update the reaction manager analytics
                story_reaction_manager.update_reaction(
                    old_vibes_name=old_reaction,
                    new_vibes_name=input.reaction,
                    old_score=old_vibe,
                    new_score=input.vibe
                )
                
                # Update the existing reaction
                existing_reaction.reaction = input.reaction
                existing_reaction.vibe = input.vibe
                existing_reaction.save()
                reaction = existing_reaction
                message = StoryMessages.STORY_REACTION_UPDATED
            else:
                # Add reaction to aggregated analytics
                story_reaction_manager.add_reaction(
                    vibes_name=input.reaction,  # Vibe name (e.g., "Happy", "Sad")
                    score=input.vibe            # Intensity score (1-5)
                )
                
                # Create individual reaction record
                reaction = StoryReaction(
                    reaction=input.reaction,
                    vibe=input.vibe
                )
                reaction.save()
                
                # Establish graph relationships
                reaction.story.connect(story)
                reaction.user.connect(user)
                story.storyreaction.connect(reaction)
                message = StoryMessages.STORY_REACTION_CREATED
            
            story_reaction_manager.save()
            
            # Track story reaction activity
            try:
                ActivityService.track_content_interaction(
                    user=user,
                    content_type='story',
                    content_id=story.uid,
                    interaction_type='reaction',
                    metadata={
                        'reaction_id': reaction.uid,
                        'reaction_type': input.reaction,
                        'vibe_score': input.vibe,
                        'story_title': story.title
                    }
                )
            except Exception as e:
                # Log error but don't fail reaction creation
                import logging
                logging.error(f"Failed to track story reaction activity: {str(e)}")
            
            # Track vibe activity for sender and receiver
            try:
                # Get story owner for receiver tracking
                story_owner = story.created_by.single()
                
                # Track vibe sending activity for the user who reacted
                VibeActivityService.track_vibe_sending(
                    sender=user,
                    receiver_id=story_owner.user_id if story_owner else None,
                    vibe_data={
                        'vibe_id': reaction.uid,
                        'vibe_name': input.reaction,
                        'vibe_type': 'individual',
                        'category': 'story_reaction'
                    },
                    vibe_score=input.vibe,
                    ip_address=info.context.META.get('REMOTE_ADDR'),
                    user_agent=info.context.META.get('HTTP_USER_AGENT', ''),
                    metadata={
                        'story_id': story.uid,
                        'reaction_id': reaction.uid,
                        'story_title': story.title
                    }
                )
            except Exception as e:
                # Log error but don't fail the reaction creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to track vibe activity: {str(e)}")
            
            # ============= NOTIFICATION CODE START (CreateStoryReaction) =============
            # Send notification to story creator about new reaction (only for new reactions, not updates)
            if not existing_results:  # Only notify for new reactions, not updates
                try:
                    from notification.global_service import GlobalNotificationService
                    
                    story_creator = story.created_by.single()
                    if story_creator and story_creator.uid != user.uid:  # Don't notify yourself
                        creator_profile = story_creator.profile.single()
                        if creator_profile and creator_profile.device_id:
                            service = GlobalNotificationService()
                            service.send(
                                event_type="story_reaction",
                                recipients=[{
                                    'device_id': creator_profile.device_id,
                                    'uid': story_creator.uid
                                }],
                                username=user.username,
                                story_id=story.uid,
                                reaction_type=input.reaction
                            )
                except Exception as e:
                    print(f"Failed to send story reaction notification: {e}")
            # ============= NOTIFICATION CODE END =============
            
            return CreateStoryReaction(success=True, message=message)
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateStoryReaction(success=False, message=message)

# Reaction update mutation - modifies existing reaction
# Used by: Reaction editing, vibe adjustments
# Security: Only reaction author can update
class UpdateStoryReaction(Mutation):
    story_reaction = graphene.Field(StoryReactionType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateStoryReactionInput()  # Update data (uid + new reaction/vibe)
    
    @handle_graphql_story_errors 
    @login_required
    def mutate(self, info, input):
        """
        Updates an existing story reaction/vibe.
        Only the reaction author can modify their reactions.
        Used for vibe adjustments and reaction corrections.
        """
        try:
            # Authentication check
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Get current user
            payload = info.context.payload
            user_id = payload.get('user_id')
            updated_by = Users.nodes.get(user_id=user_id)
       
            # Fetch reaction to update
            storyreaction = StoryReaction.nodes.get(uid=input.uid)
            
            # Ownership validation - only reaction author can update
            original_user = storyreaction.user.single().uid
            payload_user = updated_by.uid
            
            if payload_user != original_user:
                raise GraphQLError("This Reaction doesnot belong to you")

            # Update reaction fields
            for key, value in input.items():
                setattr(storyreaction, key, value)

            storyreaction.save()
           
            return UpdateStoryReaction(
                story_reaction=StoryReactionType.from_neomodel(storyreaction), 
                success=True, 
                message=StoryMessages.STORY_REACTION_UPDATED
            )
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateStoryReaction(story_reaction=None, success=False, message=message)

# Reaction deletion mutation - removes reaction permanently
# Used by: Reaction management, content cleanup
# Security: Only reaction author can delete
class DeleteStoryReaction(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()  # Reaction UID to delete
    
    @handle_graphql_story_errors 
    @login_required    
    def mutate(self, info, input):
        """
        Permanently deletes a story reaction.
        Should include ownership validation to ensure only reaction author can delete.
        Used by reaction management and content cleanup operations.
        """
        try:
            # Authentication validation
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Get current user (for potential ownership validation)
            payload = info.context.payload
            user_id = payload.get('user_id')
            deleted_by = Users.nodes.get(user_id=user_id)
        
            # Delete reaction (should add ownership validation)
            storyreaction = StoryReaction.nodes.get(uid=input.uid)
            storyreaction.delete()
            
            return DeleteStoryReaction(success=True, message=StoryMessages.STORY_REACTION_DELETED)
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteStoryReaction(success=False, message=message)

# Rating creation mutation - adds numeric rating to story
# Used by: Quality feedback, story evaluation, content scoring
# Features: 1-5 scale rating system, quality analytics
class CreateStoryRating(Mutation):
    story_rating = graphene.Field(StoryRatingType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = StoryRatingInput()  # Rating data (story_uid, rating_value)

    @handle_graphql_story_errors        
    @login_required
    def mutate(self, info, input):
        """
        Creates a numeric rating (1-5) for a story.
        Used for quality feedback and content evaluation.
        Establishes relationships for rating analytics.
        """
        try:
            # Authentication check
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Get current user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)
            
            # Get story to rate
            story_uid = input.story_uid 
            story = Story.nodes.get(uid=story_uid)

            # Create rating record
            rating = StoryRating(
                rating=input.get('rating', '')  # 1-5 numeric rating
            )
            rating.save()
            
            # Establish graph relationships
            rating.story.connect(story)
            rating.user.connect(user)
            story.storyrating.connect(rating)
            
            return CreateStoryRating(
                story_rating=StoryRatingType.from_neomodel(rating), 
                success=True, 
                message=StoryMessages.STORY_RATING_CREATED
            )
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateStoryRating(story_rating=None, success=False, message=message)

# Rating update mutation - modifies existing rating value
# Used by: Rating corrections, user preference changes
# Security: Only rating author can update
class UpdateStoryRating(Mutation):
    story_rating = graphene.Field(StoryRatingType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateStoryRatingInput()  # Update data (uid + new rating)
    
    @handle_graphql_story_errors 
    @login_required
    def mutate(self, info, input):
        """
        Updates an existing story rating value.
        Only the rating author can modify their ratings.
        Used for rating corrections and preference updates.
        """
        try:
            # Authentication validation
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Get current user
            payload = info.context.payload
            user_id = payload.get('user_id')
            updated_by = Users.nodes.get(user_id=user_id)
        
            # Fetch rating to update
            storyrating = StoryRating.nodes.get(uid=input.uid)

            # Update rating fields (should include ownership validation)
            for key, value in input.items():
                setattr(storyrating, key, value)

            storyrating.save()
           
            return UpdateStoryRating(
                story_rating=StoryRatingType.from_neomodel(storyrating), 
                success=True, 
                message=StoryMessages.STORY_RATING_UPDATED
            )
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateStoryRating(story_rating=None, success=False, message=message)

# Rating deletion mutation - removes rating permanently
# Used by: Rating management, user cleanup
# Security: Only rating author can delete
class DeleteStoryRating(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()  # Rating UID to delete
    
    @handle_graphql_story_errors 
    @login_required
    def mutate(self, info, input):
        """
        Permanently deletes a story rating.
        Should include ownership validation for security.
        Used by rating management and user cleanup operations.
        """
        try:
            # Authentication check
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Get current user (for potential ownership validation)
            payload = info.context.payload
            user_id = payload.get('user_id')
            deleted_by = Users.nodes.get(user_id=user_id)
        
            # Delete rating (should add ownership validation)
            storyrating = StoryRating.nodes.get(uid=input.uid)
            storyrating.delete()
            
            return DeleteStoryRating(success=True, message=StoryMessages.STORY_RATING_DELETED)
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteStoryRating(success=False, message=message)

# View tracking mutation - records when user views a story
# Used by: Analytics, "viewed by" lists, engagement tracking
# Features: Redis caching, user data storage, view counting
class ViewStory(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
       input = ViewStoryInput()  # View data (story_uid)
        
    @handle_graphql_story_errors         
    @login_required
    def mutate(self, info, input):
        """
        Records a story view for analytics and tracking.
        Updates both Neo4j relationships and Redis cache for performance.
        Validates story exists and hasn't expired before recording view.
        Used by story viewing interfaces and analytics systems.
        """
        try:
            # Authentication validation
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Get current user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)
            
            story_uid = input.story_uid 
            
            # Validate story exists and hasn't expired
            if check_story_cache_key_exists(story_uid) == False:
                raise Exception("Story does not exist or has expired")

            # Get story and create view record
            story = Story.nodes.get(uid=story_uid)
            view = StoryView()
            view.save()
            
            # Establish graph relationships for analytics
            view.story.connect(story)
            view.user.connect(user)
            story.storyview.connect(view)

            # Track story view activity
            try:
                ActivityService.track_content_interaction(
                    user=user,
                    content_type='story',
                    content_id=story.uid,
                    interaction_type='view',
                    metadata={
                        'story_title': story.title,
                        'view_id': view.uid
                    }
                )
            except Exception as e:
                # Log error but don't fail view tracking
                import logging
                logging.error(f"Failed to track story view activity: {str(e)}")

            # Update Redis cache for fast view tracking
            add_story_view(story_uid, user_id)  # Add to view count and viewer list
            store_user_data_in_cache(user)      # Cache user data for quick access
            
            return ViewStory(success=True, message=StoryMessages.STORY_VIEW)
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return ViewStory(success=False, message=message)
        
# Story sharing mutation - records story sharing across platforms
# Used by: Viral tracking, platform analytics, sharing features
# Features: Platform tracking, sharing analytics, social media integration
class ShareStory(Mutation):
    story_share = graphene.Field(StoryShareType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = ShareStoryInput()  # Share data (story_uid, share_platform)
        
    @handle_graphql_story_errors        
    @login_required
    def mutate(self, info, input):
        """
        Records a story share event with platform tracking.
        Used for viral analytics and platform-specific sharing metrics.
        Tracks how stories spread across different social platforms.
        """
        try:
            # Authentication validation
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
                
            # Get current user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user = Users.nodes.get(user_id=user_id)
            
            # Extract sharing data
            story_uid = input.story_uid 
            share_type = input.share_type  # Platform (WhatsApp, Facebook, etc.)
            story = Story.nodes.get(uid=story_uid)
           
            # Create share record with platform information
            share = StoryShare(
                share_type=share_type
            )
            share.save()
            
            # Establish graph relationships for analytics
            share.story.connect(story)
            share.user.connect(user)
            story.storyshare.connect(share)
            
            # Track story share activity
            try:
                ActivityService.track_content_interaction(
                    user=user,
                    content_type='story',
                    content_id=story.uid,
                    interaction_type='share',
                    metadata={
                        'share_id': share.uid,
                        'share_type': share_type,
                        'story_title': story.title
                    }
                )
            except Exception as e:
                # Log error but don't fail share creation
                import logging
                logging.error(f"Failed to track story share activity: {str(e)}")
            
            return ShareStory(
                story_share=StoryShareType.from_neomodel(share), 
                success=True, 
                message=StoryMessages.STORY_SHARE
            )
            
        except Exception as error:
           message = getattr(error, 'message', str(error))
           return ShareStory(story_share=None, success=False, message=message)

# Main mutation class - aggregates all story-related mutations
# Used by: GraphQL schema, API endpoints, client applications
# Provides: Complete CRUD operations for stories and all interactions
class Mutation(graphene.ObjectType):
    # Story CRUD operations
    create_story = CreateStory.Field()     # Create new story
    update_story = UpdateStory.Field()     # Edit existing story
    delete_story = DeleteStory.Field()     # Delete story

    # Comment operations
    create_story_comment = CreateStoryComment.Field()     # Add comment
    edit_story_comment = UpdateStoryComment.Field()       # Edit comment
    delete_story_comment = DeleteStoryComment.Field()     # Delete comment

    # Reaction/vibe operations
    create_story_reaction = CreateStoryReaction.Field()   # Add reaction
    update_story_reaction = UpdateStoryReaction.Field()   # Edit reaction
    delete_story_reaction = DeleteStoryReaction.Field()   # Delete reaction

    # Rating operations
    create_story_rating = CreateStoryRating.Field()       # Add rating
    update_story_rating = UpdateStoryRating.Field()       # Edit rating
    delete_story_rating = DeleteStoryRating.Field()       # Delete rating

    # Engagement tracking
    view_story = ViewStory.Field()         # Record story view
    share_story = ShareStory.Field()       # Record story share