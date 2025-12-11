# opportunity/graphql/mutations.py

"""
GraphQL Mutation Resolvers for Opportunity Module.

This module contains all GraphQL mutations for creating, updating, and deleting
opportunities. Mutations handle authentication, validation, notifications, and
activity tracking.

Used by: Frontend AI chatbot for opportunity creation and management
"""

import graphene
from graphql import GraphQLError
from graphql_jwt.decorators import login_required
from django.db import transaction
from neomodel import db

from .types import OpportunityType
from .inputs import (
    CreateOpportunityInput,
    UpdateOpportunityInput,
    DeleteOpportunityInput,
    CreateOpportunityCommentInput,
    CreateOpportunityLikeInput,
    ShareOpportunityInput,
    DeleteOpportunityLikeInput,
    ApplyToOpportunityInput

)
from opportunity.models import Opportunity,OpportunityApplication
from auth_manager.models import Users
from auth_manager.Utils.generate_presigned_url import get_valid_image
from user_activity.services.activity_service import ActivityService

# Matrix integration imports
from msg.models import MatrixProfile
from opportunity.utils.create_opportunity_matrix_room import create_opportunity_room
from opportunity.utils.matrix_opportunity_manager import set_opportunity_room_data
import asyncio
from post.models import Comment, Like, PostShare, PostView
from post.graphql.types import CommentType
from vibe_manager.models import IndividualVibe
from opportunity.utils.redis_helper import (
    increment_opportunity_comment_count,
    increment_opportunity_like_count,
    increment_opportunity_share_count
)
from post.models import PostReactionManager
from user_activity.services.activity_service import ActivityService
from post.utils.mention_extractor import MentionExtractor
from post.services.mention_service import MentionService
from opportunity.utils.opportunity_decorator import handle_graphql_opportunity_errors


def send_opportunity_notifications(creator, opportunity):
    """
    Send notifications to creator's connections about new opportunity.
    
    This function is called after DB commit to notify all accepted connections
    about the new job opportunity posting.
    
    Args:
        creator: Users node who created the opportunity
        opportunity: Opportunity node that was created
    """
    try:
        from notification.global_service import GlobalNotificationService
        import logging
        logger = logging.getLogger(__name__)
        
        # ========== GET CREATOR'S CONNECTIONS ==========
        query = """
        MATCH (creator:Users {uid: $creator_uid})-[:HAS_USER_CONNECTION]->(conn:Connection {status: 'accepted'})
        MATCH (conn)<-[:HAS_USER_CONNECTION]-(connected_user:Users)
        WHERE connected_user.uid <> $creator_uid AND connected_user.device_id IS NOT NULL
        RETURN connected_user
        """
        results, _ = db.cypher_query(query, {'creator_uid': creator.uid})
        
        if not results:
            logger.info(f"No connections found for user {creator.uid} to notify about opportunity")
            return
        
        # ========== BUILD RECIPIENTS LIST ==========
        recipients = []
        for record in results:
            connected_user = Users.inflate(record[0])
            if hasattr(connected_user, 'device_id') and connected_user.device_id:
                recipients.append({
                    'device_id': connected_user.device_id,
                    'uid': connected_user.uid
                })
        
        if not recipients:
            logger.info("No recipients with device IDs found")
            return
        
        # ========== SEND NOTIFICATION ==========
        service = GlobalNotificationService()
        service.send(
            event_type="new_opportunity_posted",
            recipients=recipients,
            username=creator.username,
            role=opportunity.role,
            location=opportunity.location,
            job_type=opportunity.job_type,
            opportunity_id=opportunity.uid
        )
        
        logger.info(f"Sent opportunity notifications to {len(recipients)} users")
        
    except Exception as e:
        print(f"Notification sending failed: {e}")


class CreateOpportunity(graphene.Mutation):
    """
    CreateOpportunity mutation - called when user clicks "Post it!" in AI chatbot.
    
    This mutation receives ALL opportunity data in a single call after the AI
    conversation completes. The frontend chatbot collects all information first,
    then triggers this mutation with the complete payload.
    
    Flow:
    1. User chats with AI bot (role, location, salary, responsibilities, etc.)
    2. AI generates description, key responsibilities, requirements
    3. User optionally uploads documents (JDs, company decks)
    4. User reviews preview carousel showing all details
    5. User clicks "Post it!" → Frontend calls this mutation
    6. Backend creates Opportunity node in Neo4j
    7. Connects relationships (creator, documents)
    8. Sends notifications to user's connections
    9. Tracks activity for analytics
    10. Returns success + opportunity UID
    
    Used by: Frontend AI chatbot "Post it!" button
    Returns: OpportunityType with complete opportunity data
    Side effects: Creates Neo4j node, sends notifications, tracks activity
    """
    
    success = graphene.Boolean()
    message = graphene.String()
    opportunity = graphene.Field(OpportunityType)
    
    class Arguments:
        input = CreateOpportunityInput(required=True)
    
    @handle_graphql_opportunity_errors
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required to create opportunity")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            creator = Users.nodes.get(user_id=user_id)
            
            # ========== VALIDATE DOCUMENT ATTACHMENTS ==========
            if input.document_ids:
                for doc_id in input.document_ids:
                    try:
                        get_valid_image(doc_id)  # Validates file exists in minio
                    except Exception as e:
                        raise GraphQLError(f"Invalid document ID: {doc_id}")
            
            # ========== VALIDATE COVER IMAGE ==========
            if input.cover_image_id:
                try:
                    get_valid_image(input.cover_image_id)
                except Exception as e:
                    raise GraphQLError(f"Invalid cover image ID: {input.cover_image_id}")
            
            # ========== CREATE OPPORTUNITY NODE ==========
            opportunity = Opportunity(
                opportunity_type=input.opportunity_type or 'job',  # Default to 'job'
                role=input.role,
                job_type=input.job_type,
                location=input.location,
                is_remote=input.is_remote or False,
                is_hybrid=input.is_hybrid or False,
                experience_level=input.experience_level,
                salary_range_text=input.salary_range_text,
                salary_min=input.salary_min,
                salary_max=input.salary_max,
                salary_currency=input.salary_currency or 'INR',
                description=input.description,
                key_responsibilities=input.key_responsibilities,
                requirements=input.requirements,
                good_to_have_skills=input.good_to_have_skills or [],
                skills=input.skills,
                document_ids=input.document_ids or [],
                cover_image_id=input.cover_image_id,
                cta_text=input.cta_text or "Apply Now",
                cta_type=input.cta_type or "apply",
                privacy=input.privacy or 'public',
                tags=input.tags or [],
                expires_at=input.expires_at,
                is_active=True,
                is_deleted=False
            )
            opportunity.save()
            
            # ========== CONNECT RELATIONSHIPS ==========
            opportunity.created_by.connect(creator)
            
            # ========== CREATE MATRIX ROOM ==========
            # Create a Matrix room for this opportunity (similar to community rooms)
            # Applicants can join this room to apply and communicate with the creator
            import logging
            logger = logging.getLogger(__name__)
            
            try:
                # Get creator's Matrix credentials
                matrix_profile = MatrixProfile.objects.get(user=creator.user_id)
                
                if matrix_profile.access_token and matrix_profile.matrix_user_id:
                    logger.info(f"Creating Matrix room for opportunity {opportunity.uid}")
                    
                    # Prepare opportunity data for Matrix room creation
                    opportunity_room_data = {
                        'opportunity_uid': opportunity.uid,
                        'opportunity_type': opportunity.opportunity_type,
                        'role': opportunity.role,
                        'location': opportunity.location,
                        'description': opportunity.description[:200] if opportunity.description else "",  # Brief for topic
                    }
                    
                    # Create Matrix room
                    room_id = asyncio.run(create_opportunity_room(
                        access_token=matrix_profile.access_token,
                        user_id=matrix_profile.matrix_user_id,
                        opportunity_data=opportunity_room_data
                    ))
                    
                    logger.info(f"Matrix room created: {room_id}")
                    
                    # Save room_id to opportunity
                    opportunity.room_id = room_id
                    opportunity.save()
                    
                    logger.info(f"room_id saved to opportunity: {opportunity.room_id}")
                    
                    # Set opportunity data in Matrix room state (custom event)
                    # This stores all opportunity details in the room for frontend access
                    asyncio.run(set_opportunity_room_data(
                        access_token=matrix_profile.access_token,
                        user_id=matrix_profile.matrix_user_id,
                        room_id=room_id,
                        opportunity_data=opportunity,
                        creator=creator,
                        timeout=30
                    ))
                    
                    logger.info(f"✓ Created Matrix room {room_id} for opportunity {opportunity.uid}")
                else:
                    logger.warning(f"User {creator.user_id} has no Matrix credentials (access_token: {bool(matrix_profile.access_token)}, matrix_user_id: {bool(matrix_profile.matrix_user_id)})")
                    
            except MatrixProfile.DoesNotExist:
                logger.warning(f"No Matrix profile found for user {creator.user_id}")
            except Exception as matrix_error:
                # Don't fail the entire mutation if Matrix fails
                logger.error(f"Matrix room creation failed: {matrix_error}", exc_info=True)
                # Opportunity is still created, just without Matrix room
            
            # ========== TRACK ACTIVITY ==========
            try:
                ActivityService.track_content_interaction(
                    user=creator,
                    content_type='opportunity',
                    content_id=opportunity.uid,
                    interaction_type='create',
                    metadata={
                        'opportunity_type': opportunity.opportunity_type,
                        'role': input.role,
                        'job_type': input.job_type,
                        'location': input.location,
                        'privacy': opportunity.privacy,
                        'has_documents': bool(input.document_ids),
                        'has_cover_image': bool(input.cover_image_id),
                        'salary_range': f"{input.salary_min}-{input.salary_max}" if input.salary_min and input.salary_max else None
                    }
                )
            except Exception as e:
                print(f"Activity tracking failed: {e}")
            
            # ========== SEND NOTIFICATIONS ==========
            # Use transaction.on_commit to ensure notifications are sent after DB commit
            transaction.on_commit(lambda: send_opportunity_notifications(creator, opportunity))
            
            return CreateOpportunity(
                success=True,
                message="Opportunity posted successfully!",
                opportunity=OpportunityType.from_neomodel(opportunity, info, user)
            )
            
        except GraphQLError:
            raise
        except Exception as error:
            message = getattr(error, 'message', str(error))
            print(f"Error creating opportunity: {message}")
            return CreateOpportunity(
                success=False,
                message=f"Failed to create opportunity: {message}",
                opportunity=None
            )


class UpdateOpportunity(graphene.Mutation):
    """
    UpdateOpportunity mutation for modifying existing opportunities.
    
    Allows opportunity creator to update any field of their posted opportunity.
    Common use cases:
    - Update job description or requirements
    - Change salary range
    - Add/remove documents
    - Close opportunity (set is_active=False)
    - Extend expiry date
    
    Only the opportunity creator can update their own opportunities.
    """
    
    success = graphene.Boolean()
    message = graphene.String()
    opportunity = graphene.Field(OpportunityType)
    
    class Arguments:
        input = UpdateOpportunityInput(required=True)
    
    @handle_graphql_opportunity_errors
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            updater = Users.nodes.get(user_id=user_id)
            
            # ========== GET OPPORTUNITY ==========
            try:
                opportunity = Opportunity.nodes.get(uid=input.uid)
            except Opportunity.DoesNotExist:
                raise GraphQLError("Opportunity not found")
            
            # ========== CHECK OWNERSHIP ==========
            creator = opportunity.created_by.single()
            if not creator or creator.uid != updater.uid:
                raise GraphQLError("You can only update your own opportunities")
            
            # ========== VALIDATE DOCUMENTS IF UPDATING ==========
            if input.document_ids is not None:
                for doc_id in input.document_ids:
                    try:
                        get_valid_image(doc_id)
                    except Exception:
                        raise GraphQLError(f"Invalid document ID: {doc_id}")
            
            # ========== VALIDATE COVER IMAGE IF UPDATING ==========
            if input.cover_image_id is not None:
                try:
                    get_valid_image(input.cover_image_id)
                except Exception:
                    raise GraphQLError(f"Invalid cover image ID")
            
            # ========== UPDATE FIELDS ==========
            # Only update fields that are provided (not None)
            if input.opportunity_type is not None:
                opportunity.opportunity_type = input.opportunity_type
            if input.role is not None:
                opportunity.role = input.role
            if input.job_type is not None:
                opportunity.job_type = input.job_type
            if input.location is not None:
                opportunity.location = input.location
            if input.is_remote is not None:
                opportunity.is_remote = input.is_remote
            if input.is_hybrid is not None:
                opportunity.is_hybrid = input.is_hybrid
            if input.experience_level is not None:
                opportunity.experience_level = input.experience_level
            if input.salary_range_text is not None:
                opportunity.salary_range_text = input.salary_range_text
            if input.salary_min is not None:
                opportunity.salary_min = input.salary_min
            if input.salary_max is not None:
                opportunity.salary_max = input.salary_max
            if input.salary_currency is not None:
                opportunity.salary_currency = input.salary_currency
            if input.description is not None:
                opportunity.description = input.description
            if input.key_responsibilities is not None:
                opportunity.key_responsibilities = input.key_responsibilities
            if input.requirements is not None:
                opportunity.requirements = input.requirements
            if input.good_to_have_skills is not None:
                opportunity.good_to_have_skills = input.good_to_have_skills
            if input.skills is not None:
                opportunity.skills = input.skills
            if input.document_ids is not None:
                opportunity.document_ids = input.document_ids
            if input.cover_image_id is not None:
                opportunity.cover_image_id = input.cover_image_id
            if input.cta_text is not None:
                opportunity.cta_text = input.cta_text
            if input.cta_type is not None:
                opportunity.cta_type = input.cta_type
            if input.privacy is not None:
                opportunity.privacy = input.privacy
            if input.tags is not None:
                opportunity.tags = input.tags
            if input.expires_at is not None:
                opportunity.expires_at = input.expires_at
            if input.is_active is not None:
                opportunity.is_active = input.is_active
            
            opportunity.save()
            
            # ========== CONNECT UPDATER ==========
            if not opportunity.updated_by.is_connected(updater):
                opportunity.updated_by.connect(updater)
            
            # ========== TRACK ACTIVITY ==========
            try:
                updated_fields = [k for k, v in input.__dict__.items() if v is not None and k != 'uid']
                ActivityService.track_content_interaction(
                    user=updater,
                    content_type='opportunity',
                    content_id=opportunity.uid,
                    interaction_type='update',
                    metadata={
                        'updated_fields': updated_fields
                    }
                )
            except Exception as e:
                print(f"Activity tracking failed: {e}")
            
            return UpdateOpportunity(
                success=True,
                message="Opportunity updated successfully",
                opportunity=OpportunityType.from_neomodel(opportunity, info, user)
            )
            
        except GraphQLError:
            raise
        except Exception as error:
            message = getattr(error, 'message', str(error))
            print(f"Error updating opportunity: {message}")
            return UpdateOpportunity(
                success=False,
                message=f"Failed to update opportunity: {message}",
                opportunity=None
            )


class DeleteOpportunity(graphene.Mutation):
    """
    DeleteOpportunity mutation for soft-deleting opportunities.
    
    Performs a soft delete by setting is_deleted=True rather than actually
    removing the opportunity from the database. This preserves data for
    analytics and allows potential recovery.
    
    Only the opportunity creator can delete their own opportunities.
    """
    
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = DeleteOpportunityInput(required=True)
    
    @handle_graphql_opportunity_errors
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            deleter = Users.nodes.get(user_id=user_id)
            
            # ========== GET OPPORTUNITY ==========
            try:
                opportunity = Opportunity.nodes.get(uid=input.uid)
            except Opportunity.DoesNotExist:
                raise GraphQLError("Opportunity not found")
            
            # ========== CHECK OWNERSHIP ==========
            creator = opportunity.created_by.single()
            if not creator or creator.uid != deleter.uid:
                raise GraphQLError("You can only delete your own opportunities")
            
            # ========== SOFT DELETE ==========
            opportunity.is_deleted = True
            opportunity.is_active = False
            opportunity.save()
            
            # ========== TRACK ACTIVITY ==========
            try:
                ActivityService.track_content_interaction(
                    user=deleter,
                    content_type='opportunity',
                    content_id=opportunity.uid,
                    interaction_type='delete',
                    metadata={'soft_delete': True}
                )
            except Exception as e:
                print(f"Activity tracking failed: {e}")
            
            return DeleteOpportunity(
                success=True,
                message="Opportunity deleted successfully"
            )
            
        except GraphQLError:
            raise
        except Exception as error:
            message = getattr(error, 'message', str(error))
            print(f"Error deleting opportunity: {message}")
            return DeleteOpportunity(
                success=False,
                message=f"Failed to delete opportunity: {message}"
            )




class CreateOpportunityComment(graphene.Mutation):
    """
    Create a comment on an opportunity.
    Supports nested replies, mentions, file attachments, and notifications.
    
    Pattern: Follows Post comment creation exactly
    """
    comment = graphene.Field(CommentType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateOpportunityCommentInput(required=True)

    @handle_graphql_opportunity_errors
    @login_required
    def mutate(self, info, input):
        try:
            # Get authenticated user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            # Get the opportunity
            try:
                opportunity = Opportunity.nodes.get(uid=input.opportunity_uid)
            except Opportunity.DoesNotExist:
                return CreateOpportunityComment(
                    comment=None,
                    success=False,
                    message="Opportunity not found"
                )

            # Handle nested replies
            parent_comment = None
            if input.parent_comment_uid:
                try:
                    parent_comment = Comment.nodes.get(uid=input.parent_comment_uid)
                    
                    # Optional: Limit reply depth
                    if hasattr(parent_comment, 'get_reply_depth') and parent_comment.get_reply_depth() >= 5:
                        return CreateOpportunityComment(
                            comment=None,
                            success=False,
                            message="Maximum reply depth reached"
                        )
                except Comment.DoesNotExist:
                    return CreateOpportunityComment(
                        comment=None,
                        success=False,
                        message="Parent comment not found"
                    )

            # Create comment
            comment_file_id = input.comment_file_id if input.comment_file_id else None
            comment = Comment(
                content=input.content,
                comment_file_id=comment_file_id
            )
            comment.save()

            # Establish relationships
            comment.user.connect(user_node)
            opportunity.comment.connect(comment)
            comment.opportunity.connect(opportunity)
            
            if parent_comment:
                comment.parent_comment.connect(parent_comment)

            # Increment comment count in Redis
            increment_opportunity_comment_count(opportunity.uid)

            # Extract and create mentions
            if input.content:
                mentioned_user_uids = MentionExtractor.extract_and_convert_mentions(input.content)
                if mentioned_user_uids:
                    MentionService.create_mentions(
                        mentioned_user_uids=mentioned_user_uids,
                        content_type='opportunity_comment',
                        content_uid=comment.uid,
                        mentioned_by_uid=user_node.uid,
                        mention_context='opportunity_comment'
                    )

            # Send notification to opportunity creator
            opportunity_creator = opportunity.created_by.single()
            if opportunity_creator and opportunity_creator.uid != user_node.uid:
                creator_profile = opportunity_creator.profile.single()
                if creator_profile and creator_profile.device_id:
                    try:
                        from notification.global_service import GlobalNotificationService
                        
                        comment_preview = input.content[:50] + "..." if len(input.content) > 50 else input.content
                        
                        service = GlobalNotificationService()
                        service.send(
                            event_type="opportunity_comment",
                            recipients=[{
                                'device_id': creator_profile.device_id,
                                'uid': opportunity_creator.uid
                            }],
                            username=user_node.username,
                            comment_text=comment_preview,
                            opportunity_id=opportunity.uid,
                            comment_id=comment.uid
                        )
                    except Exception as e:
                        print(f"Failed to send opportunity comment notification: {e}")

            # If reply, notify parent comment author
            if parent_comment:
                parent_comment_author = parent_comment.user.single()
                if parent_comment_author and parent_comment_author.uid != user_node.uid:
                    parent_profile = parent_comment_author.profile.single()
                    if parent_profile and parent_profile.device_id:
                        try:
                            from notification.global_service import GlobalNotificationService
                            
                            reply_preview = input.content[:50] + "..." if len(input.content) > 50 else input.content
                            
                            service = GlobalNotificationService()
                            service.send(
                                event_type="opportunity_comment_reply",
                                recipients=[{
                                    'device_id': parent_profile.device_id,
                                    'uid': parent_comment_author.uid
                                }],
                                username=user_node.username,
                                comment_text=reply_preview,
                                opportunity_id=opportunity.uid,
                                comment_id=comment.uid
                            )
                        except Exception as e:
                            print(f"Failed to send reply notification: {e}")

            # Track activity
            try:
                ActivityService.track_content_interaction(
                    user=user_node,
                    content_id=opportunity.uid,
                    content_type='opportunity',
                    interaction_type='comment',
                    metadata={
                        'comment_id': comment.uid,
                        'comment_content_length': len(input.content),
                        'is_reply': parent_comment is not None,
                        'parent_comment_id': parent_comment.uid if parent_comment else None,
                        'opportunity_type': opportunity.opportunity_type
                    }
                )
            except Exception as e:
                print(f"Failed to track comment activity: {str(e)}")

            return CreateOpportunityComment(
                comment=CommentType.from_neomodel(comment, info),
                success=True,
                message="Comment posted successfully!"
            )

        except Exception as error:
            return CreateOpportunityComment(
                comment=None,
                success=False,
                message=str(error)
            )



class CreateOpportunityLike(graphene.Mutation):
    """
    Create a like/vibe reaction on an opportunity.
    Supports multiple vibe types with intensity scoring.
    
    Pattern: Follows Post like creation exactly
    """
    success = graphene.Boolean()
    message = graphene.String()
    like_count = graphene.Int()

    class Arguments:
        input = CreateOpportunityLikeInput(required=True)

    @handle_graphql_opportunity_errors
    @login_required
    def mutate(self, info, input):
        try:
            # Get authenticated user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            # Get the opportunity
            try:
                opportunity = Opportunity.nodes.get(uid=input.opportunity_uid)
            except Opportunity.DoesNotExist:
                return CreateOpportunityLike(
                    success=False,
                    message="Opportunity not found",
                    like_count=0
                )

            # Get the vibe type
            try:
                individual_vibe = IndividualVibe.objects.get(id=input.individual_vibe_id)
            except IndividualVibe.DoesNotExist:
                return CreateOpportunityLike(
                    success=False,
                    message="Vibe type not found",
                    like_count=0
                )

            # Check if user already liked this opportunity
            existing_query = """
            MATCH (u:Users {uid: $user_uid})-[:HAS_USER]-(like:Like)-[:HAS_OPPORTUNITY]->(o:Opportunity {uid: $opportunity_uid})
            WHERE like.is_deleted = false
            RETURN like
            """
            results, _ = db.cypher_query(existing_query, {
                'user_uid': user_node.uid,
                'opportunity_uid': opportunity.uid
            })

            if results:
                # Update existing like
                existing_like = Like.inflate(results[0][0])
                existing_like.reaction = individual_vibe.name_of_vibe
                existing_like.vibe = input.vibe
                existing_like.timestamp = timezone.now()
                existing_like.save()

                message = "Vibe updated successfully!"
            else:
                # Create new like
                like = Like(
                    reaction=individual_vibe.name_of_vibe,
                    vibe=input.vibe
                )
                like.save()

                # Establish relationships
                like.user.connect(user_node)
                opportunity.like.connect(like)
                like.opportunity.connect(opportunity)

                # Update PostReactionManager for analytics
                try:
                    post_reaction_manager = PostReactionManager.objects.get(post_uid=opportunity.uid)
                except PostReactionManager.DoesNotExist:
                    post_reaction_manager = PostReactionManager(post_uid=opportunity.uid)
                    post_reaction_manager.initialize_reactions()
                    post_reaction_manager.save()

                post_reaction_manager.add_reaction(
                    vibes_name=individual_vibe.name_of_vibe,
                    score=input.vibe
                )
                post_reaction_manager.save()

                # Increment like count in Redis
                increment_opportunity_like_count(opportunity.uid)

                message = "Vibe sent successfully!"

            # Send notification to opportunity creator
            opportunity_creator = opportunity.created_by.single()
            if opportunity_creator and opportunity_creator.uid != user_node.uid:
                creator_profile = opportunity_creator.profile.single()
                if creator_profile and creator_profile.device_id:
                    try:
                        from notification.global_service import GlobalNotificationService
                        
                        service = GlobalNotificationService()
                        service.send(
                            event_type="opportunity_like",
                            recipients=[{
                                'device_id': creator_profile.device_id,
                                'uid': opportunity_creator.uid
                            }],
                            username=user_node.username,
                            vibe_name=individual_vibe.name_of_vibe,
                            opportunity_id=opportunity.uid,
                            role=opportunity.role
                        )
                    except Exception as e:
                        print(f"Failed to send like notification: {e}")

            # Track activity
            try:
                ActivityService.track_content_interaction(
                    user=user_node,
                    content_id=opportunity.uid,
                    content_type='opportunity',
                    interaction_type='like',
                    metadata={
                        'vibe_type': individual_vibe.name_of_vibe,
                        'vibe_intensity': input.vibe,
                        'opportunity_type': opportunity.opportunity_type
                    }
                )
            except Exception as e:
                print(f"Failed to track like activity: {str(e)}")

            # Get current like count
            like_count_query = """
            MATCH (o:Opportunity {uid: $opportunity_uid})-[:HAS_OPPORTUNITY]-(like:Like)
            WHERE like.is_deleted = false
            RETURN count(like) as count
            """
            count_results, _ = db.cypher_query(like_count_query, {
                'opportunity_uid': opportunity.uid
            })
            like_count = count_results[0][0] if count_results else 0

            return CreateOpportunityLike(
                success=True,
                message=message,
                like_count=like_count
            )

        except Exception as error:
            return CreateOpportunityLike(
                success=False,
                message=str(error),
                like_count=0
            )



class ShareOpportunity(graphene.Mutation):
    """
    Share an opportunity to user's feed/connections.
    Tracks shares and sends notification to opportunity creator.
    
    Pattern: Follows Post share exactly
    """
    success = graphene.Boolean()
    message = graphene.String()
    share_count = graphene.Int()

    class Arguments:
        input = ShareOpportunityInput(required=True)

    @handle_graphql_opportunity_errors
    @login_required
    def mutate(self, info, input):
        try:
            # Get authenticated user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            # Get the opportunity
            try:
                opportunity = Opportunity.nodes.get(uid=input.opportunity_uid)
            except Opportunity.DoesNotExist:
                return ShareOpportunity(
                    success=False,
                    message="Opportunity not found",
                    share_count=0
                )

            # Create share
            share = PostShare(
                share_text=input.share_text if input.share_text else ""
            )
            share.save()

            # Establish relationships
            share.user.connect(user_node)
            opportunity.share.connect(share)
            share.opportunity.connect(opportunity)

            # Increment share count in Redis
            increment_opportunity_share_count(opportunity.uid)

            # Send notification to opportunity creator
            opportunity_creator = opportunity.created_by.single()
            if opportunity_creator and opportunity_creator.uid != user_node.uid:
                creator_profile = opportunity_creator.profile.single()
                if creator_profile and creator_profile.device_id:
                    try:
                        from notification.global_service import GlobalNotificationService
                        
                        service = GlobalNotificationService()
                        service.send(
                            event_type="opportunity_share",
                            recipients=[{
                                'device_id': creator_profile.device_id,
                                'uid': opportunity_creator.uid
                            }],
                            username=user_node.username,
                            opportunity_id=opportunity.uid,
                            role=opportunity.role,
                            location=opportunity.location
                        )
                    except Exception as e:
                        print(f"Failed to send share notification: {e}")

            # Track activity
            try:
                ActivityService.track_content_interaction(
                    user=user_node,
                    content_id=opportunity.uid,
                    content_type='opportunity',
                    interaction_type='share',
                    metadata={
                        'share_text_length': len(input.share_text) if input.share_text else 0,
                        'opportunity_type': opportunity.opportunity_type
                    }
                )
            except Exception as e:
                print(f"Failed to track share activity: {str(e)}")

            # Get current share count
            share_count_query = """
            MATCH (o:Opportunity {uid: $opportunity_uid})-[:HAS_OPPORTUNITY]-(share:PostShare)
            WHERE share.is_deleted = false
            RETURN count(share) as count
            """
            count_results, _ = db.cypher_query(share_count_query, {
                'opportunity_uid': opportunity.uid
            })
            share_count = count_results[0][0] if count_results else 0

            return ShareOpportunity(
                success=True,
                message="Opportunity shared successfully!",
                share_count=share_count
            )

        except Exception as error:
            return ShareOpportunity(
                success=False,
                message=str(error),
                share_count=0
            )



class DeleteOpportunityLike(graphene.Mutation):
    """
    Remove a like/vibe from an opportunity.
    Soft deletes the like and updates analytics.
    """
    success = graphene.Boolean()
    message = graphene.String()
    like_count = graphene.Int()

    class Arguments:
        input = DeleteOpportunityLikeInput(required=True)

    @handle_graphql_opportunity_errors
    @login_required
    def mutate(self, info, input):
        try:
            # Get authenticated user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            # Find the like
            like_query = """
            MATCH (u:Users {uid: $user_uid})-[:HAS_USER]-(like:Like)-[:HAS_OPPORTUNITY]->(o:Opportunity {uid: $opportunity_uid})
            WHERE like.is_deleted = false
            RETURN like
            """
            results, _ = db.cypher_query(like_query, {
                'user_uid': user_node.uid,
                'opportunity_uid': input.opportunity_uid
            })

            if not results:
                return DeleteOpportunityLike(
                    success=False,
                    message="Like not found",
                    like_count=0
                )

            # Soft delete the like
            like = Like.inflate(results[0][0])
            like.is_deleted = True
            like.save()

            # Get updated like count
            like_count_query = """
            MATCH (o:Opportunity {uid: $opportunity_uid})-[:HAS_OPPORTUNITY]-(like:Like)
            WHERE like.is_deleted = false
            RETURN count(like) as count
            """
            count_results, _ = db.cypher_query(like_count_query, {
                'opportunity_uid': input.opportunity_uid
            })
            like_count = count_results[0][0] if count_results else 0

            return DeleteOpportunityLike(
                success=True,
                message="Like removed successfully",
                like_count=like_count
            )

        except Exception as error:
            return DeleteOpportunityLike(
                success=False,
                message=str(error),
                like_count=0
            )

# ============================================================================
# APPLY TO OPPORTUNITY MUTATION
# ============================================================================

class ApplyToOpportunityInput(graphene.InputObjectType):
    """Input type for applying to an opportunity"""
    opportunity_uid = graphene.String(required=True, description="UID of the opportunity to apply to")


class ApplyToOpportunity(graphene.Mutation):
    """
    Apply to an opportunity by joining its Matrix room and tracking application.
    
    Flow:
    1. Check if user already applied
    2. Create application record in Neo4j
    3. Join user to Matrix room
    4. Send notification to opportunity creator
    5. Track application activity
    """
    success = graphene.Boolean()
    message = graphene.String()
    room_id = graphene.String()
    application = graphene.Field('opportunity.graphql.types.OpportunityApplicationType')

    class Arguments:
        input = ApplyToOpportunityInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            # Get authenticated user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            # Get the opportunity
            try:
                opportunity = Opportunity.nodes.get(uid=input.opportunity_uid)
            except Opportunity.DoesNotExist:
                return ApplyToOpportunity(
                    success=False,
                    message="Opportunity not found",
                    room_id=None,
                    application=None
                )

            # Check if user already applied
            existing_query = """
            MATCH (u:Users {uid: $user_uid})-[:APPLIED_TO]->(app:OpportunityApplication)<-[:HAS_APPLICATION]-(o:Opportunity {uid: $opportunity_uid})
            WHERE app.is_active = true
            RETURN app
            """
            results, _ = db.cypher_query(existing_query, {
                'user_uid': user_node.uid,
                'opportunity_uid': opportunity.uid
            })
            
            if results:
                from opportunity.graphql.types import OpportunityApplicationType
                existing_app = OpportunityApplication.inflate(results[0][0])
                return ApplyToOpportunity(
                    success=False,
                    message="You have already applied to this opportunity",
                    room_id=opportunity.room_id,
                    application=OpportunityApplicationType.from_neomodel(existing_app, info)
                )

            # Create application record
            application = OpportunityApplication(
                status='pending',
                is_active=True
            )
            application.save()
            
            # Establish relationships
            application.applicant.connect(user_node)
            opportunity.applications.connect(application)
            application.opportunity.connect(opportunity)
            
            print(f"✓ Application record created: {application.uid}")

            # Join Matrix room if it exists
            if opportunity.room_id:
                try:
                    from msg.models import MatrixProfile
                    matrix_profile = MatrixProfile.objects.get(user=user_id)
                    
                    if matrix_profile.access_token and matrix_profile.matrix_user_id:
                        import asyncio
                        from nio import AsyncClient, JoinError
                        
                        async def join_room():
                            """Join the opportunity Matrix room"""
                            client = AsyncClient(
                                "https://chat.ooumph.com",
                                matrix_profile.matrix_user_id
                            )
                            client.access_token = matrix_profile.access_token
                            
                            try:
                                response = await client.join(opportunity.room_id)
                                
                                if isinstance(response, JoinError):
                                    print(f"❌ Failed to join room: {response.message}")
                                    await client.close()
                                    return False
                                
                                print(f"✓ User {user_node.username} joined opportunity room {opportunity.room_id}")
                                await client.close()
                                return True
                                
                            except Exception as e:
                                print(f"❌ Error joining room: {str(e)}")
                                await client.close()
                                return False
                        
                        # Execute the async function
                        joined = asyncio.run(join_room())
                        
                        if joined:
                            print(f"✓ Successfully joined Matrix room")
                        else:
                            print(f"⚠ Failed to join Matrix room, but application recorded")
                            
                except MatrixProfile.DoesNotExist:
                    print(f"⚠ User has no Matrix profile, application recorded but not joined to room")
                except Exception as matrix_error:
                    print(f"⚠ Matrix error: {str(matrix_error)}, but application recorded")

            # Send notification to opportunity creator
            opportunity_creator = opportunity.created_by.single()
            if opportunity_creator and opportunity_creator.uid != user_node.uid:
                creator_profile = opportunity_creator.profile.single()
                if creator_profile and creator_profile.device_id:
                    try:
                        from notification.global_service import GlobalNotificationService
                        
                        service = GlobalNotificationService()
                        service.send(
                            event_type="opportunity_application",
                            recipients=[{
                                'device_id': creator_profile.device_id,
                                'uid': opportunity_creator.uid
                            }],
                            username=user_node.username,
                            opportunity_id=opportunity.uid,
                            role=opportunity.role,
                            room_id=opportunity.room_id if opportunity.room_id else ""
                        )
                        print(f"✓ Notification sent to opportunity creator")
                    except Exception as e:
                        print(f"⚠ Failed to send application notification: {e}")

            # Track application activity
            try:
                from activity.services import ActivityService
                
                ActivityService.track_content_interaction(
                    user=user_node,
                    content_id=opportunity.uid,
                    content_type='opportunity',
                    interaction_type='apply',
                    metadata={
                        'application_uid': application.uid,
                        'opportunity_type': opportunity.opportunity_type,
                        'opportunity_role': opportunity.role,
                        'room_id': opportunity.room_id if opportunity.room_id else None,
                        'has_room': bool(opportunity.room_id)
                    }
                )
                print(f"✓ Application activity tracked")
            except Exception as e:
                print(f"⚠ Failed to track application activity: {str(e)}")

            # Return success
            from opportunity.graphql.types import OpportunityApplicationType
            return ApplyToOpportunity(
                success=True,
                message="Application submitted successfully! The opportunity creator will review your application.",
                room_id=opportunity.room_id if opportunity.room_id else None,
                application=OpportunityApplicationType.from_neomodel(application, info)
            )

        except Exception as error:
            import traceback
            print(f"❌ Apply to opportunity error: {str(error)}")
            print(traceback.format_exc())
            return ApplyToOpportunity(
                success=False,
                message=f"Failed to apply: {str(error)}",
                room_id=None,
                application=None
            )       

class OpportunityMutations(graphene.ObjectType):
    """
    Container for all opportunity-related mutations.
    
    This class groups all opportunity mutations and makes them available
    through the GraphQL API schema.
    """
    
    create_opportunity = CreateOpportunity.Field()
    update_opportunity = UpdateOpportunity.Field()
    delete_opportunity = DeleteOpportunity.Field()

    create_opportunity_comment = CreateOpportunityComment.Field()
    create_opportunity_like = CreateOpportunityLike.Field()
    delete_opportunity_like = DeleteOpportunityLike.Field()
    share_opportunity = ShareOpportunity.Field()

    apply_to_opportunity = ApplyToOpportunity.Field()

