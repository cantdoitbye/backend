import graphene
from graphene import Mutation
from graphql import GraphQLError
import asyncio

from .raw_query.block_exist import relationship_exists
from .types import *
from auth_manager.models import Users
from msg.models import *
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