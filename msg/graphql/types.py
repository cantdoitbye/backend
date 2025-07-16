import graphene
from graphene import ObjectType

from auth_manager.graphql.types import UserType
from auth_manager.Utils import generate_presigned_url
from msg.models import MatrixProfile
from graphene_django.types import DjangoObjectType

class ConversationType(ObjectType):
    uid = graphene.String()
    members = graphene.List(UserType)
    name = graphene.String()
    timestamp = graphene.DateTime()
    created_by = graphene.Field(UserType)
    @classmethod
    def from_neomodel(cls, conversation):
        return cls(
            uid=conversation.uid,
            members=[UserType.from_neomodel(member) for member in conversation.members.all()],
            created_by=UserType.from_neomodel(conversation.created_by.single()) if conversation.created_by.single() else None,
            name=conversation.name,
            timestamp=conversation.timestamp
        )
    
class ConversationMessageType(ObjectType):
    uid = graphene.String()
    conversation = graphene.Field(ConversationType)
    sender = graphene.Field(UserType)
    content = graphene.String()
    title = graphene.String()
    is_read = graphene.Boolean()
    is_deleted = graphene.Boolean()
    file_id=graphene.String()
    file_url=graphene.String()
    timestamp = graphene.DateTime()
    visible_to_blocked = graphene.Boolean()

    @classmethod
    def from_neomodel(cls, message):
        return cls(
            uid=message.uid,
            conversation=ConversationType.from_neomodel(message.conversation.single()) if message.conversation.single() else None,
            sender=UserType.from_neomodel(message.sender.single()) if message.sender.single() else None,
            content=message.content,
            title=message.title,
            is_read=message.is_read,
            is_deleted=message.is_deleted,
            timestamp=message.timestamp,
            visible_to_blocked=message.visible_to_blocked,
            file_id=message.file_id,
            file_url=generate_presigned_url.generate_presigned_url(message.file_id),
        )

class ReactionType(ObjectType):
    uid = graphene.String()
    conv_message = graphene.Field(ConversationMessageType)
    reacted_by = graphene.Field(UserType)
    reaction_type = graphene.String()
    emoji = graphene.String()
    timestamp = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, reaction):
        return cls(
            uid=reaction.uid,
            conv_message=ConversationMessageType.from_neomodel(reaction.conv_message.single()) if reaction.conv_message.single() else None,
            reacted_by=UserType.from_neomodel(reaction.reacted_by.single()) if reaction.reacted_by.single() else None,
            reaction_type=reaction.reaction_type,
            emoji=reaction.emoji,
            timestamp=reaction.timestamp,
        )

class BlockType(ObjectType):
    uid = graphene.String()
    blocker = graphene.Field(UserType)
    blocked = graphene.Field(UserType)
    created_at = graphene.DateTime()

    @classmethod
    def from_neomodel(cls, block):
        return cls(
            uid=block.uid,
            blocker=UserType.from_neomodel(block.blocker.single())if block.blocker.single() else None,
            blocked=UserType.from_neomodel(block.blocked.single()) if block.blocked.single() else None,
            created_at=block.created_at,
        )


class MatrixProfileType(DjangoObjectType):
    class Meta:
        model = MatrixProfile
        fields = ("user", "matrix_user_id", "access_token", "pending_matrix_registration")