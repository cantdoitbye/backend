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

class GetMatrixMessagesInput(graphene.InputObjectType):
    community_uid = graphene.String(required=True)
    limit = graphene.Int(default_value=20)
    from_token = graphene.String()

class SendMatrixMessageInput(graphene.InputObjectType):
    community_uid = graphene.String(required=True)
    message = graphene.String(required=True)
    message_type = graphene.String(default_value="m.text")

class SendMatrixMessageByAgentInput(graphene.InputObjectType):
    agent_uid = graphene.String(required=True)
    community_id = graphene.ID(required=True)
    content = graphene.String(required=True)
    message_type = graphene.String(required=False, default_value="m.text")


class DeleteMatrixMessageByAgentInput(graphene.InputObjectType):
    agent_uid = graphene.String(required=True)
    community_id = graphene.ID(required=True)
    event_id = graphene.String(required=True)
    reason = graphene.String(required=False, default_value="Message deleted by moderator")


class KickUserByAgentInput(graphene.InputObjectType):
    agent_uid = graphene.String(required=True)
    community_id = graphene.ID(required=True)
    target_user_id = graphene.String(required=True)
    reason = graphene.String(required=False, default_value="Kicked by moderator")


class BanUserByAgentInput(graphene.InputObjectType):
    agent_uid = graphene.String(required=True)
    community_id = graphene.ID(required=True)
    target_user_id = graphene.String(required=True)
    reason = graphene.String(required=False, default_value="Banned by moderator")


class UnbanUserByAgentInput(graphene.InputObjectType):
    agent_uid = graphene.String(required=True)
    community_id = graphene.ID(required=True)
    target_user_id = graphene.String(required=True)