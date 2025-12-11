import asyncio
import graphene
from graphene import Mutation
from graphql import GraphQLError
import logging

from .raw_query.block_exist import relationship_exists
from .types import *
from auth_manager.models import Users
from msg.models import *
from msg.models import DebateChatRequest, MatrixProfile
from neomodel import db
from msg.util.matrix_vibe_sender import send_vibe_reaction_to_matrix
from msg.util.matrix_message_utils import (
    get_community_matrix_messages,
    send_matrix_message,
    get_matrix_credentials_for_community,
    flag_agent_messages,
    MatrixMessageError,
    delete_matrix_message,
    kick_user_from_room,
    ban_user_from_room,
    unban_user_from_room
)

logger = logging.getLogger(__name__)
from agentic.models import Agent
from vibe_manager.utils import VibeUtils
from vibe_manager.models import IndividualVibe
from .inputs import *
from .messages import MsgMessages
from graphql_jwt.decorators import login_required,superuser_required
from msg.services.notification_service import NotificationService
from community.models import Community, Membership
from post.models import Post, Comment
from community.utils.create_matrix_room_with_token import create_room
from community.utils.matrix_invites import process_matrix_invites

class CreateConversation(Mutation):
    conversation = graphene.Field(ConversationType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateConversationInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)

            member_nodes = [Users.nodes.get(uid=uid) for uid in input.member_uids]

            conversation = Conversation(name=input.name)
            conversation.save()
            for member in member_nodes:
                conversation.members.connect(member)
                member.conversation.connect(conversation)
            conversation.members.connect(user_node)
            conversation.created_by.connect(user_node)
            user_node.conversation.connect(conversation)


            creator = conversation.created_by.single()
            creator_profile = creator.profile.single()
            
            if creator_profile and creator_profile.device_id and creator.uid != user_node.uid:
                notification_service = NotificationService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(notification_service.notifyChatInvitationAccepted(
                        accepter_name=user_node.username,
                        inviter_device_id=creator_profile.device_id,
                        chat_id=conversation.uid,
                        chat_name=conversation.name
                    ))
                finally:
                    loop.close()


            return CreateConversation(conversation=ConversationType.from_neomodel(conversation, current_user_id=user_id), success=True, message=MsgMessages.CONVERSATION_CREATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return CreateConversation(conversation=None, success=False, message=message)

class UpdateConversation(Mutation):
    conversation = graphene.Field(ConversationType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateConversationInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            
            payload = info.context.payload
            user_id = payload.get('user_id')

            conversation = Conversation.nodes.get(uid=input.uid)

            if input.name is not None:
                conversation.name = input.name

            if input.member_uids is not None:
                member_nodes = [Users.nodes.get(uid=uid) for uid in input.member_uids]
                conversation.members.disconnect_all()
                for member in member_nodes:
                    conversation.members.connect(member)

            conversation.save()

            # Notify existing members when new members are added to the conversation
            if input.member_uids is not None:
                # Get all existing conversation members for notification
                existing_members = conversation.members.all()
                members_to_notify = []
                
                for member in existing_members:
                    if member.uid != user.uid:
                        profile = member.profile.single()
                        if profile and profile.device_id:
                            members_to_notify.append({
                                'device_id': profile.device_id,
                                'uid': member.uid
                            })
                
                # Get the names of new members added
                new_member_names = [Users.nodes.get(uid=uid).username for uid in input.member_uids]
                new_members_text = ", ".join(new_member_names[:2])  # Show first 2 names
                if len(new_member_names) > 2:
                    new_members_text += f" and {len(new_member_names) - 2} others"
                
                # Send notifications about new members
                if members_to_notify:
                    notification_service = NotificationService()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(notification_service.notifyNewChatMessage(
                            sender_name="System",
                            followers=members_to_notify,
                            chat_id=conversation.uid,
                            message_preview=f"{new_members_text} joined the chat"
                        ))
                    finally:
                        loop.close()

            return UpdateConversation(conversation=ConversationType.from_neomodel(conversation, current_user_id=user_id), success=True, message=MsgMessages.CONVERSATION_UPDATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return UpdateConversation(conversation=None, success=False, message=message)

class DeleteConversation(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()
    
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            conversation = Conversation.nodes.get(uid=input.uid)
            conversation.delete()

            return DeleteConversation(success=True, message=MsgMessages.CONVERSATION_DELETED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return DeleteConversation(success=False, message=message)

class CreateConversationMessage(Mutation):
    msg = graphene.Field(ConversationMessageType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateConversationMessageInput()
    
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            
            payload = info.context.payload
            user_id = payload.get('user_id')

            sender = Users.nodes.get(user_id=user_id)
            conversation = Conversation.nodes.get(uid=input.conversation_uid)
            

            msg = ConversationMessages(
                content=input.content,
                title=input.title,
                file_id=input.file_id,
            )
            msg.save()
            msg.conversation.connect(conversation)
            msg.sender.connect(sender)
            conversation.conv_message.connect(msg)

            # Track activity for analytics
            try:
                from user_activity.services.activity_service import ActivityService
                from django.contrib.auth.models import User
                
                # Get Django user for activity tracking
                django_user = User.objects.get(id=user_id)
                activity_service = ActivityService()
                
                # Track message sending as social interaction
                activity_service.track_social_interaction(
                    user=django_user,
                    target_user=None,  # Group message, no specific target
                    interaction_type='message_send',
                    context_type='conversation',
                    context_id=str(conversation.uid),
                    metadata={
                        'conversation_id': conversation.uid,
                        'message_id': msg.uid,
                        'content_length': len(input.content) if input.content else 0,
                        'has_file': bool(input.file_id)
                    }
                )
            except Exception as e:
                # Don't fail the mutation if activity tracking fails
                logger.error(f"Failed to track message activity: {e}")

            # Notify all conversation members except the sender
            # members_to_notify = []
            # for member in conversation.members.all():
            #     if member.uid != sender.uid:
            #         profile = member.profile.single()
            #         if profile and profile.device_id:
            #             members_to_notify.append({
            #                 'device_id': profile.device_id,
            #                 'uid': member.uid
            #             })

            # if members_to_notify:
            #     notification_service = NotificationService()
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     try:
            #         loop.run_until_complete(notification_service.notifyNewChatMessage(
            #             sender_name=sender.username,
            #             followers=members_to_notify,
            #             chat_id=conversation.uid,
            #             message_preview=msg.content[:50] if msg.content else ""
            #         ))
            #     finally:
            #         loop.close()

            return CreateConversationMessage(msg=ConversationMessageType.from_neomodel(msg, current_user_id=user_id), success=True, message=MsgMessages.CONVERSATION_MSG_CREATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return CreateConversationMessage(msg=None, success=False, message=message)

class UpdateConversationMessage(Mutation):
    msg = graphene.Field(ConversationMessageType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateConversationMessageInput()
    
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            
            payload = info.context.payload
            user_id = payload.get('user_id')

            msg_node = ConversationMessages.nodes.get(uid=input.uid)

            if 'content' in input:
                msg_node.content = input['content']
            if 'title' in input:
                msg_node.title = input['title']
            if 'is_read' in input:
                msg_node.is_read = input['is_read']
            if 'is_deleted' in input:
                msg_node.is_deleted = input['is_deleted']
            if 'visible_to_blocked' in input:
                msg_node.visible_to_blocked = input['visible_to_blocked']

            msg_node.save()

            return UpdateConversationMessage(msg=ConversationMessageType.from_neomodel(msg_node, current_user_id=user_id), success=True, message=MsgMessages.CONVERSATION_MSG_UPDATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return UpdateConversationMessage(msg=None, success=False, message=message)
        
class DeleteConversationMessage(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()
    
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            msg_node = ConversationMessages.nodes.get(uid=input.uid)
            msg_node.delete()

            return DeleteConversationMessage(success=True, message=MsgMessages.CONVERSATION_MSG_DELETED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return DeleteConversationMessage(success=False, message=message)

class CreateReaction(Mutation):
    reaction = graphene.Field(ReactionType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateReactionInput()
    
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            conv_message = ConversationMessages.nodes.get(uid=input.conv_message_uid)
           
            payload = info.context.payload
            user_id = payload.get('user_id')

            reacted_by = Users.nodes.get(user_id=user_id)
            reaction = Reaction(
                reaction_type=input.reaction_type,
                emoji=input.emoji
            )
            reaction.save()
            reaction.conv_message.connect(conv_message)
            reaction.reacted_by.connect(reacted_by)
            conv_message.reaction.connect(reaction)

            return CreateReaction(reaction=ReactionType.from_neomodel(reaction), success=True, message=MsgMessages.CONVERSATION_REACTION_CREATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return CreateReaction(reaction=None, success=False, message=message)
        

class UpdateReaction(Mutation):
    reaction = graphene.Field(ReactionType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateReactionInput()
    
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            reaction = Reaction.nodes.get(uid=input.uid)

            if input.reaction_type is not None:
                reaction.reaction_type = input.reaction_type
            if input.emoji is not None:
                reaction.emoji = input.emoji

            reaction.save()

            return UpdateReaction(reaction=ReactionType.from_neomodel(reaction), success=True, message=MsgMessages.CONVERSATION_REACTION_UPDATED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return UpdateReaction(reaction=None, success=False, message=message)

class DeleteReaction(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            reaction = Reaction.nodes.get(uid=input.uid)
            reaction.delete()

            return DeleteReaction(success=True, message=MsgMessages.CONVERSATION_REACTION_DELETED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return DeleteReaction(success=False, message=message)


class CreateBlock(Mutation):
    block = graphene.Field(BlockType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateBlockInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            blocker = Users.nodes.get(user_id=user_id)
            blocked = Users.nodes.get(uid=input.blocked_uid)
            ans=relationship_exists(blocker,blocked)
            if ans:
                return CreateBlock(block=None, success=False, message="User Already exist in your Block list.")

            block = Block()
            block.save()
            block.blocker.connect(blocker)
            blocker.blocked.connect(block)
            block.blocked.connect(blocked)

            return CreateBlock(block=BlockType.from_neomodel(block), success=True, message=MsgMessages.BLOCKED_CREATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateBlock(block=None, success=False, message=message)

class DeleteBlock(Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()
        
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            block = Block.nodes.get(uid=input.uid)
            block.delete()

            return DeleteBlock(success=True, message=MsgMessages.BLOCKED_DELETED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return DeleteBlock(success=False, message=message)
        
class SendVibeToMessage(graphene.Mutation):
    """
    Sends a vibe reaction to a message in Matrix chat using existing vibe system.
    """
    success = graphene.Boolean()
    message = graphene.String()
    vibe_reaction = graphene.Field('msg.graphql.types.VibeReactionType')
    
    class Arguments:
        room_id = graphene.String(required=True)
        message_event_id = graphene.String(required=True)
        individual_vibe_id = graphene.Int(required=True)  # ID from IndividualVibe
        vibe_intensity = graphene.Float(required=False)    # 1.0 to 5.0
    
    @login_required
    def mutate(self, info, room_id, message_event_id, individual_vibe_id, vibe_intensity):
        try:
            # Get authenticated user
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            # Validate vibe intensity (1.0 to 5.0)
            if not (1.0 <= vibe_intensity <= 5.0):
                return SendVibeToMessage(
                    success=False,
                    message="Vibe intensity must be between 1.0 and 5.0"
                )
            try:
                clean_intensity = round(float(vibe_intensity), 2)
            except (ValueError, TypeError):
                return SendVibeToMessage(
                    success=False,
                    message="Invalid vibe intensity format"
                )
            if not (1.0 <= clean_intensity <= 5.0):
               return SendVibeToMessage(
                   success=False,
                   message="Vibe intensity must be between 1.0 and 5.0"
                )
            
            # Get the individual vibe from PostgreSQL
            try:
                individual_vibe = IndividualVibe.objects.get(id=individual_vibe_id)
            except IndividualVibe.DoesNotExist:
                return SendVibeToMessage(
                    success=False,
                    message="Invalid vibe selected"
                )
            
            # Get user's Matrix profile
            try:
                matrix_profile = MatrixProfile.objects.get(user=user_id)
                if not matrix_profile.access_token:
                    return SendVibeToMessage(
                        success=False,
                        message="Matrix profile not available"
                    )
            except MatrixProfile.DoesNotExist:
                return SendVibeToMessage(
                    success=False,
                    message="Matrix profile not found"
                )
            
            # Get user's profile image URL from profile_pic_id
            profile_image_url = None
            if hasattr(user_node, 'profile_pic_id') and user_node.profile_pic_id:
                try:
                    from auth_manager.Utils.generate_presigned_url import generate_file_info
                    file_info = generate_file_info(user_node.profile_pic_id)
                    if file_info and file_info.get('url'):
                        profile_image_url = file_info['url']
                except Exception as e:
                    profile_image_url = None
            
            # Send vibe reaction to Matrix
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                matrix_event_id = loop.run_until_complete(
                    send_vibe_reaction_to_matrix(
                        access_token=matrix_profile.access_token,
                        user_id=matrix_profile.matrix_user_id,
                        room_id=room_id,
                        original_event_id=message_event_id,
                        vibe_name=individual_vibe.name_of_vibe,
                        vibe_intensity=clean_intensity,
                        individual_vibe_id=individual_vibe_id,
                        profile_image_url=profile_image_url
                    )
                )
            finally:
                loop.close()
            
            if not matrix_event_id:
                return SendVibeToMessage(
                    success=False,
                    message="Failed to send vibe reaction to Matrix"
                )
            
            # Store vibe reaction in Neo4j
            vibe_reaction = VibeReaction(
                individual_vibe_id=individual_vibe_id,
                vibe_name=individual_vibe.name_of_vibe,
                vibe_intensity=clean_intensity,
                matrix_event_id=matrix_event_id,
                matrix_room_id=room_id
            ).save()
            
            # Connect to user
            vibe_reaction.reacted_by.connect(user_node)
            
            
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
            
            return SendVibeToMessage(
                success=True,
                message="Vibe sent successfully!",
                vibe_reaction=None  # Will implement type conversion later
            )
            
        except Exception as e:
            return SendVibeToMessage(
                success=False,
                message=f"Error sending vibe: {str(e)}"
            )


class GetMatrixMessages(graphene.Mutation):
    """
    Fetches paginated messages from a community's Matrix room with agent flagging.
    
    This mutation retrieves messages from the Matrix room associated with a community,
    automatically flags messages sent by agents, and supports pagination for efficient
    message loading.
    
    Args:
        input (GetMatrixMessagesInput): Contains:
            - community_uid: UID of the community
            - limit: Number of messages to retrieve (default: 20)
            - from_token: Pagination token for older messages
    
    Returns:
        MatrixMessagesResponse: Contains messages, pagination tokens, and status
    
    Note:
        - Uses community creator's Matrix credentials for access
        - Automatically flags messages from assigned agents
        - Supports pagination for large message histories
    """
    
    class Arguments:
        input = GetMatrixMessagesInput(required=True)
    
    Output = MatrixMessagesResponse
    
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            
            community_uid = input.community_uid
            limit = input.limit or 20
            from_token = input.from_token
            
            # Get the community and verify it exists
            try:
                community = Community.nodes.get(uid=community_uid)
            except Community.DoesNotExist:
                return MatrixMessagesResponse(
                    messages=[],
                    success=False,
                    message="Community not found"
                )
            
            # Check if community has a Matrix room
            if not community.room_id:
                return MatrixMessagesResponse(
                    messages=[],
                    success=False,
                    message="Community does not have a Matrix room"
                )
            
            # Get Matrix credentials for the community
            credentials = get_matrix_credentials_for_community(community_uid)
            if not credentials:
                return MatrixMessagesResponse(
                    messages=[],
                    success=False,
                    message="No Matrix credentials available for this community"
                )
            
            # Fetch messages from Matrix
            try:
                result = asyncio.run(get_community_matrix_messages(
                    access_token=credentials['access_token'],
                    user_id=credentials['user_id'],
                    room_id=community.room_id,
                    limit=limit,
                    from_token=from_token
                ))
                
                # Flag agent messages
                flagged_messages = flag_agent_messages(result['messages'], community_uid)
                
                # Convert to GraphQL types
                matrix_messages = [
                    MatrixMessageType(
                        event_id=msg['event_id'],
                        sender=msg['sender'],
                        timestamp=msg['timestamp'],
                        content=msg['content'],
                        formatted_content=msg.get('formatted_content'),
                        message_type=msg['message_type'],
                        is_agent=msg['is_agent'],
                        raw_event=msg['raw_event']
                    ) for msg in flagged_messages
                ]
                
                return MatrixMessagesResponse(
                    messages=matrix_messages,
                    next_token=result['next_token'],
                    prev_token=result['prev_token'],
                    total_messages=result['total_messages'],
                    success=True,
                    message="Messages retrieved successfully"
                )
                
            except MatrixMessageError as e:
                return MatrixMessagesResponse(
                    messages=[],
                    success=False,
                    message=f"Matrix error: {str(e)}"
                )
                
        except Exception as e:
            return MatrixMessagesResponse(
                messages=[],
                success=False,
                message=f"Error retrieving messages: {str(e)}"
            )


class SendMatrixMessage(graphene.Mutation):
    """
    Sends a message to a community's Matrix room.
    
    This mutation allows authenticated users to send messages to the Matrix room
    associated with a community. It uses the community creator's Matrix credentials
    for sending the message.
    
    Args:
        input (SendMatrixMessageInput): Contains:
            - community_uid: UID of the community
            - message: Message content to send
            - message_type: Type of message (default: "m.text")
    
    Returns:
        SendMatrixMessageResponse: Contains event ID and status
    
    Note:
        - Requires user authentication
        - Uses community creator's Matrix credentials
        - Returns Matrix event ID for the sent message
    """
    
    class Arguments:
        input = SendMatrixMessageInput(required=True)
    
    Output = SendMatrixMessageResponse
    
    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            
            community_uid = input.community_uid
            message = input.message
            message_type = input.message_type or "m.text"
            
            # Get the community and verify it exists
            try:
                community = Community.nodes.get(uid=community_uid)
            except Community.DoesNotExist:
                return SendMatrixMessageResponse(
                    success=False,
                    message="Community not found"
                )
            
            # Check if community has a Matrix room
            if not community.room_id:
                return SendMatrixMessageResponse(
                    success=False,
                    message="Community does not have a Matrix room"
                )
            
            # Get Matrix credentials for the community
            credentials = get_matrix_credentials_for_community(community_uid)
            if not credentials:
                return SendMatrixMessageResponse(
                    success=False,
                    message="No Matrix credentials available for this community"
                )
            
            # Send message to Matrix using credentials
            try:
                event_id = asyncio.run(send_matrix_message(
                    access_token=credentials['access_token'],
                    user_id=credentials['user_id'],
                    room_id=community.room_id,
                    message=message,
                    message_type=message_type
                ))
                
                # Track activity for analytics
                try:
                    from user_activity.services.activity_service import ActivityService
                    from django.contrib.auth.models import User
                    
                    payload = info.context.payload
                    user_id = payload.get('user_id')
                    
                    # Get Django user for activity tracking
                    django_user = User.objects.get(id=user_id)
                    activity_service = ActivityService()
                    
                    # Track matrix message sending as social interaction
                    activity_service.track_social_interaction(
                        user=django_user,
                        target_user=None,  # Community message, no specific target
                        interaction_type='message_send',
                        context_type='matrix_community',
                        context_id=str(community_uid),
                        metadata={
                            'community_id': community_uid,
                            'room_id': community.room_id,
                            'message_type': message_type,
                            'message_length': len(message),
                            'event_id': event_id
                        }
                    )
                except Exception as e:
                    # Don't fail the mutation if activity tracking fails
                    logger.error(f"Failed to track matrix message activity: {e}")
                
                return SendMatrixMessageResponse(
                    event_id=event_id,
                    success=True,
                    message="Message sent successfully"
                )
                
            except MatrixMessageError as e:
                return SendMatrixMessageResponse(
                    success=False,
                    message=f"Matrix error: {str(e)}"
                )
                
        except Exception as e:
            return SendMatrixMessageResponse(
                success=False,
                message=f"Error sending message: {str(e)}"
            )


class SendMatrixMessageByAgent(graphene.Mutation):
    """
    Sends a message to a community's Matrix room using agent ID and community ID.
    
    This mutation allows agents to send messages to the Matrix room
    associated with a community using agent and community identifiers.
    
    Args:
        input (SendMatrixMessageByAgentInput): Contains:
            - agent_id: ID of the agent sending the message
            - community_id: ID of the community
            - message: Message content to send
            - message_type: Type of message (default: "m.text")
    
    Returns:
        SendMatrixMessageResponse: Contains event ID and status
    
    Note:
        - Does not require user authentication (agent-based)
        - Uses agent's own Matrix credentials
        - Returns Matrix event ID for the sent message
    """
    
    class Arguments:
        input = SendMatrixMessageByAgentInput(required=True)
    
    Output = SendMatrixMessageResponse
    
    def mutate(self, info, input):
        try:
            agent_id = input.agent_uid
            community_id = input.community_id
            message = input.content
            message_type = input.message_type or "m.text"
            
            # Get the agent and verify it exists
            try:
                agent = Agent.nodes.get(uid=agent_id)
            except Agent.DoesNotExist:
                return SendMatrixMessageResponse(
                    success=False,
                    message="Agent not found"
                )
            
            # Check if agent has Matrix credentials
            if not agent.matrix_user_id or not agent.access_token:
                return SendMatrixMessageResponse(
                    success=False,
                    message="Agent does not have Matrix credentials"
                )
            
            # Get the community and verify it exists
            try:
                community = Community.nodes.get(uid=community_id)
            except Community.DoesNotExist:
                return SendMatrixMessageResponse(
                    success=False,
                    message="Community not found"
                )
            
            # Check if community has a Matrix room
            if not community.room_id:
                return SendMatrixMessageResponse(
                    success=False,
                    message="Community does not have a Matrix room"
                )
            
            # Send message to Matrix
            try:
                event_id = asyncio.run(send_matrix_message(
                    access_token=agent.access_token,
                    user_id=agent.matrix_user_id,
                    room_id=community.room_id,
                    message=message,
                    message_type=message_type
                ))
                
                return SendMatrixMessageResponse(
                    event_id=event_id,
                    success=True,
                    message=f"Message sent successfully by agent {agent_id}"
                )
                
            except MatrixMessageError as e:
                return SendMatrixMessageResponse(
                    success=False,
                    message=f"Matrix error: {str(e)}"
                )
                
        except Exception as e:
            return SendMatrixMessageResponse(
                success=False,
                message=f"Error sending message: {str(e)}"
            )


class DeleteMatrixMessageByAgent(graphene.Mutation):
    class Arguments:
        input = DeleteMatrixMessageByAgentInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input):
        try:
            # Get agent by UID
            try:
                agent = Agent.nodes.get(uid=input.agent_uid)
            except Agent.DoesNotExist:
                return DeleteMatrixMessageByAgent(
                    success=False,
                    message="Agent not found"
                )
            
            if not hasattr(agent, 'access_token') or not agent.access_token:
                return DeleteMatrixMessageByAgent(
                    success=False,
                    message="Agent does not have Matrix credentials"
                )

            # Get community and validate agent membership
            try:
                community = Community.nodes.get(uid=input.community_id)
            except Community.DoesNotExist:
                return DeleteMatrixMessageByAgent(
                    success=False,
                    message="Community not found"
                )
            
            # Check if agent is assigned to community
            try:
                from agentic.models import AgentCommunityAssignment
                # Find assignment by checking all assignments and matching connected nodes
                assignment = None
                for assign in AgentCommunityAssignment.nodes.filter(status='ACTIVE'):
                    assign_agent = assign.agent.single()
                    assign_community = assign.community.single()
                    if (assign_agent and assign_agent.uid == agent.uid and 
                        assign_community and assign_community.uid == community.uid):
                        assignment = assign
                        break
                is_assigned = assignment is not None
            except Exception:
                is_assigned = False
            
            if not is_assigned:
                return DeleteMatrixMessageByAgent(
                    success=False,
                    message="Agent is not assigned to this community"
                )

            # Delete the message
            asyncio.run(delete_matrix_message(
                access_token=agent.access_token,
                user_id=agent.matrix_user_id,
                room_id=community.room_id,
                event_id=input.event_id,
                reason=input.reason
            ))

            return DeleteMatrixMessageByAgent(
                success=True,
                message="Message deleted successfully"
            )

        except Agent.DoesNotExist:
            return DeleteMatrixMessageByAgent(
                success=False,
                message="Agent not found"
            )
        except Community.DoesNotExist:
            return DeleteMatrixMessageByAgent(
                success=False,
                message="Community not found"
            )
        except Exception as e:
            return DeleteMatrixMessageByAgent(
                success=False,
                message=f"Error deleting message: {str(e)}"
            )


class KickUserByAgent(graphene.Mutation):
    class Arguments:
        input = KickUserByAgentInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input):
        try:
            # Get agent by UID
            try:
                agent = Agent.nodes.get(uid=input.agent_uid)
            except Agent.DoesNotExist:
                return KickUserByAgent(
                    success=False,
                    message="Agent not found"
                )
            
            if not hasattr(agent, 'access_token') or not agent.access_token:
                return KickUserByAgent(
                    success=False,
                    message="Agent does not have Matrix credentials"
                )

            # Get community and validate agent membership
            try:
                community = Community.nodes.get(uid=input.community_id)
            except Community.DoesNotExist:
                return KickUserByAgent(
                    success=False,
                    message="Community not found"
                )
            
            # Check if agent is assigned to community
            try:
                from agentic.models import AgentCommunityAssignment
                # Find assignment by checking all assignments and matching connected nodes
                assignment = None
                for assign in AgentCommunityAssignment.nodes.filter(status='ACTIVE'):
                    assign_agent = assign.agent.single()
                    assign_community = assign.community.single()
                    if (assign_agent and assign_agent.uid == agent.uid and 
                        assign_community and assign_community.uid == community.uid):
                        assignment = assign
                        break
                is_assigned = assignment is not None
            except Exception:
                is_assigned = False
            
            if not is_assigned:
                return KickUserByAgent(
                    success=False,
                    message="Agent is not assigned to this community"
                )

            # Kick the user
            asyncio.run(kick_user_from_room(
                access_token=agent.access_token,
                user_id=agent.matrix_user_id,
                room_id=community.room_id,
                target_user_id=input.target_user_id,
                reason=input.reason
            ))

            return KickUserByAgent(
                success=True,
                message="User kicked successfully"
            )

        except Agent.DoesNotExist:
            return KickUserByAgent(
                success=False,
                message="Agent not found"
            )
        except Community.DoesNotExist:
            return KickUserByAgent(
                success=False,
                message="Community not found"
            )
        except Exception as e:
            return KickUserByAgent(
                success=False,
                message=f"Error kicking user: {str(e)}"
            )


class BanUserByAgent(graphene.Mutation):
    class Arguments:
        input = BanUserByAgentInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input):
        try:
            # Get agent by UID
            try:
                agent = Agent.nodes.get(uid=input.agent_uid)
            except Agent.DoesNotExist:
                return BanUserByAgent(
                    success=False,
                    message="Agent not found"
                )
            
            if not hasattr(agent, 'access_token') or not agent.access_token:
                return BanUserByAgent(
                    success=False,
                    message="Agent does not have Matrix credentials"
                )

            # Get community and validate agent membership
            try:
                community = Community.nodes.get(uid=input.community_id)
            except Community.DoesNotExist:
                return BanUserByAgent(
                    success=False,
                    message="Community not found"
                )
            
            # Check if agent is assigned to community
            try:
                from agentic.models import AgentCommunityAssignment
                # Find assignment by checking all assignments and matching connected nodes
                assignment = None
                for assign in AgentCommunityAssignment.nodes.filter(status='ACTIVE'):
                    assign_agent = assign.agent.single()
                    assign_community = assign.community.single()
                    if (assign_agent and assign_agent.uid == agent.uid and 
                        assign_community and assign_community.uid == community.uid):
                        assignment = assign
                        break
                is_assigned = assignment is not None
            except Exception:
                is_assigned = False
            
            if not is_assigned:
                return BanUserByAgent(
                    success=False,
                    message="Agent is not assigned to this community"
                )

            # Ban the user
            asyncio.run(ban_user_from_room(
                access_token=agent.access_token,
                user_id=agent.matrix_user_id,
                room_id=community.room_id,
                target_user_id=input.target_user_id,
                reason=input.reason
            ))

            return BanUserByAgent(
                success=True,
                message="User banned successfully"
            )

        except Agent.DoesNotExist:
            return BanUserByAgent(
                success=False,
                message="Agent not found"
            )
        except Community.DoesNotExist:
            return BanUserByAgent(
                success=False,
                message="Community not found"
            )
        except Exception as e:
            return BanUserByAgent(
                success=False,
                message=f"Error banning user: {str(e)}"
            )


class UnbanUserByAgent(graphene.Mutation):
    class Arguments:
        input = UnbanUserByAgentInput(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, input):
        try:
            # Get agent by UID
            try:
                agent = Agent.nodes.get(uid=input.agent_uid)
            except Agent.DoesNotExist:
                return UnbanUserByAgent(
                    success=False,
                    message="Agent not found"
                )
            
            if not hasattr(agent, 'access_token') or not agent.access_token:
                return UnbanUserByAgent(
                    success=False,
                    message="Agent does not have Matrix credentials"
                )

            # Get community and validate agent membership
            try:
                community = Community.nodes.get(uid=input.community_id)
            except Community.DoesNotExist:
                return UnbanUserByAgent(
                    success=False,
                    message="Community not found"
                )
            
            # Check if agent is assigned to community
            try:
                from agentic.models import AgentCommunityAssignment
                # Find assignment by checking all assignments and matching connected nodes
                assignment = None
                for assign in AgentCommunityAssignment.nodes.filter(status='ACTIVE'):
                    assign_agent = assign.agent.single()
                    assign_community = assign.community.single()
                    if (assign_agent and assign_agent.uid == agent.uid and 
                        assign_community and assign_community.uid == community.uid):
                        assignment = assign
                        break
                is_assigned = assignment is not None
            except Exception:
                is_assigned = False
            
            if not is_assigned:
                return UnbanUserByAgent(
                    success=False,
                    message="Agent is not assigned to this community"
                )

            # Unban the user
            asyncio.run(unban_user_from_room(
                access_token=agent.access_token,
                user_id=agent.matrix_user_id,
                room_id=community.room_id,
                target_user_id=input.target_user_id
            ))

            return UnbanUserByAgent(
                success=True,
                message="User unbanned successfully"
            )

        except Agent.DoesNotExist:
            return UnbanUserByAgent(
                success=False,
                message="Agent not found"
            )
        except Community.DoesNotExist:
            return UnbanUserByAgent(
                success=False,
                message="Community not found"
            )
        except Exception as e:
            return UnbanUserByAgent(
                success=False,
                message=f"Error unbanning user: {str(e)}"
            )



class CreateDebateChatRequest(Mutation):
    request = graphene.Field('msg.graphql.types.DebateChatRequestType')
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateDebateChatRequestInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            requester = Users.nodes.get(user_id=user_id)

            source_type = input.source_type.lower()
            source_uid = input.source_uid

            responder = None
            topic_text = None
            post_node = None
            comment_node = None

            if source_type == 'post':
                post_node = Post.nodes.get(uid=source_uid)
                responder = post_node.created_by.single()
                topic_text = post_node.post_title or ''
            else:
                comment_node = Comment.nodes.get(uid=source_uid)
                responder = comment_node.user.single()
                topic_text = comment_node.content or ''

            if not responder or responder.uid == requester.uid:
                return CreateDebateChatRequest(request=None, success=False, message="Invalid chat request target")

            # Prevent duplicate pending/active requests for same source and participants
            dup_query = (
                "MATCH (req:DebateChatRequest {source_uid: $source_uid, source_type: $source_type}) "
                "MATCH (req)-[:CHAT_REQUESTER]->(:Users {uid: $requester_uid}) "
                "MATCH (req)-[:CHAT_RESPONDER]->(:Users {uid: $responder_uid}) "
                "WHERE req.status IN ['PENDING','ACCEPTED'] "
                "RETURN req LIMIT 1"
            )
            dup_params = {
                'source_uid': source_uid,
                'source_type': source_type,
                'requester_uid': requester.uid,
                'responder_uid': responder.uid
            }
            dup_results, _ = db.cypher_query(dup_query, dup_params)
            if dup_results and dup_results[0]:
                try:
                    existing_req = DebateChatRequest.inflate(dup_results[0][0])
                    return CreateDebateChatRequest(
                        request=DebateChatRequestType.from_neomodel(existing_req),
                        success=False,
                        message="Debate chat request already exists"
                    )
                except Exception:
                    return CreateDebateChatRequest(
                        request=None,
                        success=False,
                        message="Debate chat request already exists"
                    )

            # Set default opposing stance when source has a stance
            requester_stance = None
            responder_stance = None
            if comment_node and getattr(comment_node, 'stance', None):
                responder_stance = str(comment_node.stance).lower()
                if responder_stance in ['for','against']:
                    requester_stance = 'against' if responder_stance == 'for' else 'for'

            req = DebateChatRequest(
                source_type=source_type,
                source_uid=source_uid,
                topic_text=topic_text,
                status='PENDING'
            )
            req.save()
            req.requester.connect(requester)
            req.responder.connect(responder)
            if post_node:
                req.post.connect(post_node)
            if comment_node:
                req.comment.connect(comment_node)
            if requester_stance:
                req.requester_stance = requester_stance
            if responder_stance:
                req.responder_stance = responder_stance
            req.save()

            return CreateDebateChatRequest(request=DebateChatRequestType.from_neomodel(req), success=True, message="Chat request created")
        except Exception as error:
            message=getattr(error,'message',str(error))
            return CreateDebateChatRequest(request=None, success=False, message=message)

class RespondDebateChatRequest(Mutation):
    request = graphene.Field('msg.graphql.types.DebateChatRequestType')
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = RespondDebateChatRequestInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')

            req = DebateChatRequest.nodes.get(uid=input.uid)
            responder = req.responder.single()
            if not responder or responder.user_id != str(user_id):
                return RespondDebateChatRequest(request=None, success=False, message="Permission denied")

            if input.accept is False:
                req.status = 'DECLINED'
                req.save()
                return RespondDebateChatRequest(request=DebateChatRequestType.from_neomodel(req), success=True, message="Chat request declined")

            matrix_profile = MatrixProfile.objects.filter(user=user_id).first()
            if not matrix_profile or not matrix_profile.matrix_user_id or not matrix_profile.access_token:
                return RespondDebateChatRequest(request=None, success=False, message="Matrix not available")

            room_id = asyncio.run(create_room(
                access_token=matrix_profile.access_token,
                user_id=matrix_profile.matrix_user_id,
                room_name=req.topic_text or "Debate",
                topic=req.topic_text or "",
                visibility="private",
                preset="private_chat"
            ))

            if isinstance(room_id, tuple):
                room_id = room_id[0] if room_id[0] else None

            if not room_id:
                return RespondDebateChatRequest(request=None, success=False, message="Failed to create room")

            req.matrix_room_id = room_id
            req.status = 'ACCEPTED'
            from django.utils import timezone
            from datetime import timedelta
            req.expires_at = timezone.now() + timedelta(hours=24)
            req.requester_turns_used = 0
            req.responder_turns_used = 0
            req.save()

            members = []
            requester = req.requester.single()
            if requester:
                members.append(requester.uid)
            process_matrix_invites(admin_user_id=user_id, room_id=room_id, member_ids=members)

            return RespondDebateChatRequest(request=DebateChatRequestType.from_neomodel(req), success=True, message="Chat room created")
        except Exception as error:
            message=getattr(error,'message',str(error))
            return RespondDebateChatRequest(request=None, success=False, message=message)

class RegisterDebateChatTurn(Mutation):
    request = graphene.Field('msg.graphql.types.DebateChatRequestType')
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = RegisterDebateChatTurnInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')

            req = DebateChatRequest.nodes.get(uid=input.request_uid)
            from django.utils import timezone
            if req.status != 'ACCEPTED' or (req.expires_at and timezone.now() > req.expires_at):
                try:
                    req.status = 'EXPIRED'
                    req.save()
                except Exception:
                    pass
                return RegisterDebateChatTurn(request=DebateChatRequestType.from_neomodel(req), success=False, message="Session expired or not active")

            actor = input.actor.lower()
            requester = req.requester.single()
            responder = req.responder.single()
            is_requester = requester and requester.user_id == str(user_id)
            is_responder = responder and responder.user_id == str(user_id)
            if actor == 'requester' and not is_requester:
                return RegisterDebateChatTurn(request=None, success=False, message="Actor mismatch")
            if actor == 'responder' and not is_responder:
                return RegisterDebateChatTurn(request=None, success=False, message="Actor mismatch")

            if actor == 'requester':
                if req.requester_turns_used >= req.max_turns_per_user:
                    return RegisterDebateChatTurn(request=DebateChatRequestType.from_neomodel(req), success=False, message="Turn limit reached")
                req.requester_turns_used += 1
            else:
                if req.responder_turns_used >= req.max_turns_per_user:
                    return RegisterDebateChatTurn(request=DebateChatRequestType.from_neomodel(req), success=False, message="Turn limit reached")
                req.responder_turns_used += 1

            req.save()
            return RegisterDebateChatTurn(request=DebateChatRequestType.from_neomodel(req), success=True, message="Turn registered")
        except Exception as error:
            message=getattr(error,'message',str(error))
            return RegisterDebateChatTurn(request=None, success=False, message=message)

class ExpireDebateChatSession(Mutation):
    request = graphene.Field('msg.graphql.types.DebateChatRequestType')
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = ExpireDebateChatSessionInput()

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')

            req = DebateChatRequest.nodes.get(uid=input.request_uid)
            requester = req.requester.single()
            responder = req.responder.single()
            allowed = (requester and requester.user_id == str(user_id)) or (responder and responder.user_id == str(user_id))
            if not allowed:
                return ExpireDebateChatSession(request=None, success=False, message="Permission denied")

            from django.utils import timezone
            req.status = 'EXPIRED'
            req.expires_at = timezone.now()
            req.save()
            return ExpireDebateChatSession(request=DebateChatRequestType.from_neomodel(req), success=True, message="Session expired")
        except Exception as error:
            message=getattr(error,'message',str(error))
            return ExpireDebateChatSession(request=None, success=False, message=message)


class Mutation(graphene.ObjectType):
    Create_Conversation = CreateConversation.Field()
    Update_Conversation= UpdateConversation.Field()
    Delete_Conversation= DeleteConversation.Field()
    Create_Conversation_Msg=CreateConversationMessage.Field()
    Update_Conversation_Msg=UpdateConversationMessage.Field()
    Delete_Conversation_Msg=DeleteConversationMessage.Field()
    Create_Conv_Reaction=CreateReaction.Field()
    update_conv_Reaction=UpdateReaction.Field()
    Delete_Conv_Reaction=DeleteReaction.Field()
    block_user=CreateBlock.Field()
    unblock_user=DeleteBlock.Field()
    send_vibe_to_message = SendVibeToMessage.Field()
    get_matrix_messages = GetMatrixMessages.Field()
    send_matrix_message = SendMatrixMessage.Field()
    send_matrix_message_by_agent = SendMatrixMessageByAgent.Field()
    delete_matrix_message_by_agent = DeleteMatrixMessageByAgent.Field()
    kick_user_by_agent = KickUserByAgent.Field()
    ban_user_by_agent = BanUserByAgent.Field()
    unban_user_by_agent = UnbanUserByAgent.Field()
    create_debate_chat_request = CreateDebateChatRequest.Field()
    respond_debate_chat_request = RespondDebateChatRequest.Field()
    register_debate_chat_turn = RegisterDebateChatTurn.Field()
    expire_debate_chat_session = ExpireDebateChatSession.Field()
