import graphene
from graphene import Mutation
from graphql import GraphQLError
import asyncio

from .raw_query.block_exist import relationship_exists
from .types import *
from auth_manager.models import Users
from msg.models import *
from msg.util.matrix_vibe_sender import send_vibe_reaction_to_matrix
from vibe_manager.utils import VibeUtils
from vibe_manager.models import IndividualVibe
from .inputs import *
from .messages import MsgMessages
from graphql_jwt.decorators import login_required,superuser_required
from msg.services.notification_service import NotificationService

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


            return CreateConversation(conversation=ConversationType.from_neomodel(conversation), success=True, message=MsgMessages.CONVERSATION_CREATED)
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

            return UpdateConversation(conversation=ConversationType.from_neomodel(conversation), success=True, message=MsgMessages.CONVERSATION_UPDATED)
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

            return CreateConversationMessage(msg=ConversationMessageType.from_neomodel(msg), success=True, message=MsgMessages.CONVERSATION_MSG_CREATED)
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

            return UpdateConversationMessage(msg=ConversationMessageType.from_neomodel(msg_node), success=True, message=MsgMessages.CONVERSATION_MSG_UPDATED)
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
                        individual_vibe_id=individual_vibe_id
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
