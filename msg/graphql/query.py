import graphene
from graphene import Mutation
from graphql_jwt.decorators import login_required,superuser_required

from .types import *
from auth_manager.models import Users
from msg.models import *
from msg.models import DebateChatRequest
from .types import DebateChatRequestType

class Query(graphene.ObjectType):
   all_conversations = graphene.List(ConversationType)
   @login_required
   @superuser_required
   def resolve_all_conversations(self, info):
        return [ConversationType.from_neomodel(conversation) for conversation in Conversation.nodes.all()]
   
   conversation_byuid= graphene.Field(ConversationType, conversation_uid=graphene.String(required=True))

   @login_required
   def resolve_conversation_byuid(self, info, conversation_uid):
        payload = info.context.payload
        user_id = payload.get('user_id')
        try:
            conv = Conversation.nodes.get(uid=conversation_uid)
            return ConversationType.from_neomodel(conv, current_user_id=user_id)
        except Conversation.DoesNotExist:
            return None
   

   my_conversation = graphene.List(ConversationType)

   @login_required
   def resolve_my_conversation(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            
            my_conversation=user_node.conversation.all()
            return [ConversationType.from_neomodel(x, current_user_id=user_id) for x in my_conversation]
        except Exception as e:
            raise Exception(e)

   all_conversation_messages = graphene.List(ConversationMessageType)
   @superuser_required
   @login_required
   def resolve_all_conversation_messages(self, info):
        return [ConversationMessageType.from_neomodel(message) for message in ConversationMessages.nodes.all()]

   conversation_message_byuid= graphene.Field(ConversationMessageType, conversation_msg_uid=graphene.String(required=True))

   @login_required
   def resolve_conversation_message_byuid(self, info, conversation_msg_uid):
        payload = info.context.payload
        user_id = payload.get('user_id')
        try:
            conv_msg = ConversationMessages.nodes.get(uid=conversation_msg_uid)
            return ConversationMessageType.from_neomodel(conv_msg, current_user_id=user_id)
        except ConversationMessages.DoesNotExist:
            return None  
  
  #myconversation room all messages
   my_conv_message=graphene.List(ConversationMessageType)
   @login_required
   def resolve_my_conv_message(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            
            my_conversation=user_node.conversation.all()
            convmsg = []
            for conv in my_conversation:
                   convmsg.extend(list(conv.conv_message))
                    # Extend the reactions list with the reactions of the current message
            return [ConversationMessageType.from_neomodel(x, current_user_id=user_id) for x in convmsg]
        except Exception as e:
            raise Exception(e)

   all_reactions = graphene.List(ReactionType)
   @superuser_required
   @login_required
   def resolve_all_reactions(self, info):
        return [ReactionType.from_neomodel(reaction) for reaction in Reaction.nodes.all()]
   
   reactions_byuid = graphene.List(ReactionType, conversation_msg_uid=graphene.String(required=True))
    
   @login_required
   def resolve_reactions_byuid(self, info, conversation_msg_uid):
        payload = info.context.payload
        user_id = payload.get('user_id')
        conv_msg = ConversationMessages.nodes.get(uid=conversation_msg_uid)
        all_reaction = list(conv_msg.reaction.all())
        return [ReactionType.from_neomodel(reaction, current_user_id=user_id) for reaction in all_reaction]
   

   my_conv_reaction=graphene.List(ReactionType)
   @login_required
   def resolve_my_conv_reaction(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            
            my_conversation=user_node.conversation.all()
            reactions = []
            for conv in my_conversation:
               # Loop through each message in the conversation
               for message in conv.conv_message.all():
                   reactions.extend(list(message.reaction))
                    # Extend the reactions list with the reactions of the current message
            return [ReactionType.from_neomodel(x, current_user_id=user_id) for x in reactions]
        except Exception as e:
            raise Exception(e)
        
   my_block_list=graphene.List(BlockType)

   @login_required
   def resolve_my_block_list(self,info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)

        try:
            

            my_blocks=list(user_node.blocked.all())

        
            return [BlockType.from_neomodel(x) for x in my_blocks]
        except Exception as e:
            raise Exception(e)
        
   my_matrix_profile = graphene.Field(MatrixProfileType)
   @login_required
   def resolve_my_matrix_profile(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        return MatrixProfile.objects.get(user=user_id)

   my_debate_chat_requests = graphene.List(DebateChatRequestType, status=graphene.String())
   @login_required
   def resolve_my_debate_chat_requests(self, info, status=None):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        reqs = []
        try:
            reqs.extend(list(user_node.chat_requester))
        except Exception:
            pass
        try:
            reqs.extend(list(user_node.chat_responder))
        except Exception:
            pass
        filtered = [r for r in reqs if (status is None or r.status == status)]
        return [DebateChatRequestType.from_neomodel(r) for r in filtered]
