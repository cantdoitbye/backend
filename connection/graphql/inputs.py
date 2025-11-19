import graphene
from .types import CircleTypeEnum, CircleTypeEnumV2
from auth_manager.validators import custom_graphql_validator


class UpdateDMRoomByRoomIdInput(graphene.InputObjectType):
    """
    Input for updating DM room data by room_id.
    
    Args:
        room_id (String): Matrix room ID (e.g., "!abc123:chat.ooumph.com")
    """
    room_id = graphene.String(
        required=True, 
        description="Matrix room ID starting with '!' (e.g., !abc123:chat.ooumph.com)"
    )

class CreateConnectionInput(graphene.InputObjectType):
    receiver_uid = graphene.String(required=True)
    circle=CircleTypeEnum()
    relation=graphene.String(description="⚠️ Deprecated! Use sub_relation instead.")
    sub_relation=custom_graphql_validator.String.add_option("subRelation", "CreateConnection")()

class CreateConnectionInputV2(graphene.InputObjectType):
    receiver_uid = graphene.String(required=True)
    sub_relation=custom_graphql_validator.NonSpecialCharacterString2_30.add_option("subRelation", "SendConnection")()


class UpdateConnectionInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    connection_status = custom_graphql_validator.String.add_option("connectionStatus", "UpdateConnection")()

class DeleteInput(graphene.InputObjectType):
    uid = graphene.String(required=True)


class UpdateConnectionRelationOrCircleInput(graphene.InputObjectType):
    connection_uid = graphene.String(required=True, desc="The unique identifier of the connection.")
    sub_relation = custom_graphql_validator.String.add_option("subRelation", "UpdateConnectionRelationOrCircle")(required=False, desc="The sub_relation or role of the user in the community.")
    circle_type = CircleTypeEnum(required=True, desc="The circle type associated with the community.")

class UpdateConnectionRelationOrCircleInputV2(graphene.InputObjectType):
    connection_uid = graphene.String(required=True, desc="The unique identifier of the connection.")
    sub_relation = custom_graphql_validator.String.add_option("subRelation", "UpdateConnectionRelationOrCircleV2")(required=False, desc="The sub_relation or role of the user in the community.")
    circle_type = CircleTypeEnumV2(required=False, desc="The circle type associated with the community.")
