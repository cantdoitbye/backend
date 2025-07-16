import graphene

class CreateConversationInput(graphene.InputObjectType):
    member_uids = graphene.List(graphene.String, required=True)
    name = graphene.String(required=True)

class UpdateConversationInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    member_uids = graphene.List(graphene.String)
    name = graphene.String()

class DeleteInput(graphene.InputObjectType):
    uid = graphene.String(required=True)

class CreateConversationMessageInput(graphene.InputObjectType):
    conversation_uid = graphene.String(required=True)
    content = graphene.String(required=True)
    title = graphene.String()
    file_id=graphene.String()

class UpdateConversationMessageInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    content = graphene.String()
    title = graphene.String()
    is_read = graphene.Boolean()
    is_deleted = graphene.Boolean()
    visible_to_blocked = graphene.Boolean()

class CreateReactionInput(graphene.InputObjectType):
    conv_message_uid = graphene.String(required=True)
    reaction_type = graphene.String()
    emoji = graphene.String()

class UpdateReactionInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    reaction_type = graphene.String()
    emoji = graphene.String()

class CreateBlockInput(graphene.InputObjectType):
    blocked_uid = graphene.String(required=True)