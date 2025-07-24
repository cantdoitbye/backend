"""Connection GraphQL Mutations

This module contains all GraphQL mutations for managing user connections in the social platform.
It provides functionality for creating, updating, and deleting connections between users,
as well as managing connection circles and relationships.

The module includes both legacy (v1) and new (v2) implementations of connection mutations,
with v2 providing enhanced features and improved data structures.

Key Features:
- Connection creation and management
- Circle-based relationship categorization (Inner, Outer, Universal)
- Bidirectional and unidirectional relationship support
- Real-time notifications for connection events
- Connection statistics tracking
- Authorization and permission checks

Author: Development Team
Version: 2.0
"""

import graphene
from graphene import Mutation
from graphql import GraphQLError
from .types import(
    ConnectionType
)
from auth_manager.models import Users
from connection.models import *
from .inputs import *
from .messages import ConnectionMessages
from graphql_jwt.decorators import login_required,superuser_required
from auth_manager.Utils import connection_count
from .feature_flag import feature_flags
from connection.utils import relation
from connection.graphql.raw_queries import user_related_queries
from neomodel import db
from connection.utils.connection_decorator import handle_graphql_connection_errors
import asyncio
from connection.services.notification_service import NotificationService

class CreateConnection(Mutation):
    """Legacy Connection Creation Mutation (Deprecated)
    
    Creates a new connection request between two users using the legacy connection system.
    This mutation is deprecated in favor of CreateConnectionV2 which provides enhanced
    features and better data structure.
    
    Features:
    - Prevents duplicate connection requests
    - Creates circle-based relationships
    - Sends push notifications to receiver
    - Updates connection statistics
    - Supports Inner, Outer, and Universal circles
    
    Returns:
        connection (ConnectionType): The created connection object
        success (Boolean): Whether the operation was successful
        message (String): Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: For various business logic violations
    
    Note:
        This mutation is deprecated. Use CreateConnectionV2 instead.
    """
    connection = graphene.Field(ConnectionType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateConnectionInput()
    
    @handle_graphql_connection_errors
    @login_required
    def mutate(self, info, input):
        """Execute the connection creation mutation.
        
        Args:
            info: GraphQL execution info containing user context
            input (CreateConnectionInput): Input data for creating connection
            
        Returns:
            CreateConnection: Mutation result with connection data
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by_node = Users.nodes.get(user_id=user_id)
            receiver = Users.nodes.get(uid=input.receiver_uid)
            
            connection_node = created_by_node.connection.all()

            for connection in connection_node:
                old_receiver = connection.receiver.single()
                if old_receiver:  # or any other status
                   
                    if connection.connection_status == 'Received' and old_receiver.email== receiver.email:
                         return CreateConnection(connection=None, success=False, message="Connection already Sent.")
                    if connection.connection_status == 'Accepted' and old_receiver.email== receiver.email:
                         return CreateConnection(connection=None, success=False, message="Connection already exist.")


            connection = Connection(
                connection_status="Received",
            )
            connection.save()
            connection.receiver.connect(receiver)
            connection.created_by.connect(created_by_node)
            created_by_node.connection.connect(connection)
            receiver.connection.connect(connection)

            circle_choice=Circle(
                    circle_type=input.circle.value,
                    sub_relation=input.sub_relation,
                    relation=input.relation
            )
            circle_choice.save()
            connection.circle.connect(circle_choice)
            try:
                connection_count.get_received_connections_count(receiver)
                connection_count.get_send_connections_count(created_by_node)
            except:
                pass

            # Send notification to receiver about new connection request
            receiver_profile = receiver.profile.single()
            if receiver_profile and receiver_profile.device_id:
                notification_service = NotificationService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(notification_service.notifyConnectionRequest(
                        sender_name=created_by_node.username,
                        receiver_device_id=receiver_profile.device_id,
                        connection_id=connection.uid
                    ))
                finally:
                    loop.close()

            return CreateConnection(connection=ConnectionType.from_neomodel(connection), success=True, message=ConnectionMessages.CONNECTION_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateConnection(connection=None, success=False, message=message)


class UpdateConnection(Mutation):
    """Legacy Connection Update Mutation
    
    Updates the status of an existing connection request (accept, reject, cancel).
    Handles authorization checks and updates connection statistics accordingly.
    
    Supported Operations:
    - Accept connection request (updates circle counts)
    - Reject connection request
    - Cancel sent connection request
    
    Features:
    - Authorization validation (only receiver can accept/reject)
    - Connection statistics updates
    - Circle count management
    - Push notifications for status changes
    - Prevents duplicate status updates
    
    Returns:
        connection (ConnectionType): The updated connection object
        success (Boolean): Whether the operation was successful
        message (String): Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: For authorization failures or invalid operations
    """
    connection = graphene.Field(ConnectionType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateConnectionInput()
    
    @handle_graphql_connection_errors
    @login_required
    def mutate(self, info, input):
        """Execute the connection update mutation.
        
        Args:
            info: GraphQL execution info containing user context
            input (UpdateConnectionInput): Input data for updating connection
            
        Returns:
            UpdateConnection: Mutation result with updated connection data
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node=Users.nodes.get(user_id=user_id) #login user
            
            connection = Connection.nodes.get(uid=input.uid) #connection attempted to update

            
            
            


            sender=connection.created_by.single()
            if input.connection_status == 'Cancelled' and user_node.email == sender.email:
                
                for key, value in input.items():
                    setattr(connection, key, value)
                connection.save()
                return UpdateConnection(connection=ConnectionType.from_neomodel(connection), success=True, message=ConnectionMessages.CONNECTION_UPDATED)
            #Handle the logic:- This connection belong to login user or not
            receiver_node=connection.receiver.single() 
            if(user_node.email != receiver_node.email):
                 return UpdateConnection(connection=None, success=False, message="You are not Authorized to Update this connection")
            
            #Handle the logic if connection already accepted
            if connection.connection_status == 'Accepted':
                
                return UpdateConnection(connection=None, success=False, message="You have already accepted the connection")
            
            connection_stat_receiver =user_node.connection_stat.single()
            sender=connection.created_by.single()
            connection_stat_sender =sender.connection_stat.single()

            for key, value in input.items():
                setattr(connection, key, value)

            if input.connection_status == 'Accepted':
                circle = connection.circle.single()
                
                connection_stat_receiver.accepted_connections_count+=1
                connection_stat_receiver.save()
                
                
                if circle and circle.circle_type == 'Inner':
                    connection_stat_receiver.inner_circle_count += 1
                    connection_stat_receiver.save()
                    connection_stat_sender.inner_circle_count += 1
                    connection_stat_sender.save()

                if circle and circle.circle_type == 'Outer':
                    connection_stat_receiver.outer_circle_count += 1
                    connection_stat_receiver.save()
                    connection_stat_sender.outer_circle_count += 1
                    connection_stat_sender.save()

                if circle and circle.circle_type == 'Universal':
                    connection_stat_receiver.universal_circle_count += 1
                    connection_stat_receiver.save()
                    connection_stat_sender.universal_circle_count += 1
                    connection_stat_sender.save()

                # Send notification to sender about accepted connection
                sender_profile = sender.profile.single()
                if sender_profile and sender_profile.device_id:
                    notification_service = NotificationService()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(notification_service.notifyConnectionAccepted(
                            receiver_name=receiver_node.username,
                            sender_device_id=sender_profile.device_id,
                            connection_id=connection.uid
                        ))
                    finally:
                        loop.close()

            if input.connection_status == 'REJECTED':
                connection_stat_receiver.rejected_connections_count+=1
                connection_stat_receiver.save()

                # Send notification to sender about rejected connection
                sender_profile = sender.profile.single()
                if sender_profile and sender_profile.device_id:
                    notification_service = NotificationService()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(notification_service.notifyConnectionRejected(
                            receiver_name=receiver_node.username,
                            sender_device_id=sender_profile.device_id,
                            connection_id=connection.uid
                        ))
                    finally:
                        loop.close()

            connection.save()

            

            return UpdateConnection(connection=ConnectionType.from_neomodel(connection), success=True, message=ConnectionMessages.CONNECTION_UPDATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateConnection(connection=None, success=False, message=message)

class DeleteConnection(Mutation):
    """Connection Deletion Mutation
    
    Permanently deletes a connection between two users. This operation removes
    the connection record and all associated data from the database.
    
    Features:
    - Complete connection removal
    - Authorization checks
    - Cascade deletion of related data
    
    Returns:
        success (Boolean): Whether the deletion was successful
        message (String): Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If connection not found or deletion fails
        
    Warning:
        This operation is irreversible. Use with caution.
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteInput()

    @handle_graphql_connection_errors        
    @login_required
    def mutate(self, info, input):
        """Execute the connection deletion mutation.
        
        Args:
            info: GraphQL execution info containing user context
            input (DeleteInput): Input data containing connection UID to delete
            
        Returns:
            DeleteConnection: Mutation result with success status
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')

            connection = Connection.nodes.get(uid=input.uid)
            connection.delete()
            return DeleteConnection(success=True, message= ConnectionMessages.CONNECTION_DELETED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return DeleteConnection(success=False, message=message)


class UpdateConnectionRelationOrCircle(Mutation):
    """Legacy Connection Relationship/Circle Update Mutation
    
    Updates the relationship type or circle classification of an existing accepted connection.
    Only works with connections that have been accepted by both parties.
    
    Features:
    - Circle type modification (Inner, Outer, Universal)
    - Sub-relationship updates
    - Connection statistics recalculation
    - Authorization for both connection parties
    
    Circle Types:
    - Inner: Close personal connections
    - Outer: Professional or acquaintance connections  
    - Universal: Public or broad network connections
    
    Returns:
        success (Boolean): Whether the update was successful
        message (String): Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If connection not accepted or user unauthorized
        
    Note:
        Requires optimization and review as indicated in original code.
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateConnectionRelationOrCircleInput()

    @handle_graphql_connection_errors       
    @login_required
    def mutate(self, info, input):
        """Execute the connection relationship/circle update mutation.
        
        Args:
            info: GraphQL execution info containing user context
            input (UpdateConnectionRelationOrCircleInput): Input data for updating relationship
            
        Returns:
            UpdateConnectionRelationOrCircle: Mutation result with success status
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')

            connection = Connection.nodes.get(uid=input.connection_uid)

            if connection.connection_status != 'Accepted':
                return UpdateConnectionRelationOrCircle(success=False, message=ConnectionMessages.CONNECTION_NOT_ACCEPTED)
            
            sender=connection.created_by.single()
            receiver_node=connection.receiver.single()
            user_node=Users.nodes.get(user_id=user_id)

            if(user_node.email == receiver_node.email or user_node.email == sender.email):
                circle = connection.circle.single()
                
                connection_stat_receiver = receiver_node.connection_stat.single()
                connection_stat_sender = sender.connection_stat.single()

                circle_type_to_field = {
                    'Inner': 'inner_circle_count',
                    'Outer': 'outer_circle_count',
                    'Universal': 'universal_circle_count'
                }
                
                if circle:
                    # Adjust counts for the current circle type
                    current_field_name = circle_type_to_field.get(circle.circle_type)
                    new_field_name = circle_type_to_field.get(input.circle_type.value)

                    for field_name in (current_field_name, new_field_name):
                        if field_name:
                            increment = 1 if field_name == new_field_name else -1
                            setattr(connection_stat_receiver, field_name, getattr(connection_stat_receiver, field_name) + increment)
                            setattr(connection_stat_sender, field_name, getattr(connection_stat_sender, field_name) + increment)
                    
                        connection_stat_receiver.save()
                        connection_stat_sender.save()

                
                circle.circle_type = input.circle_type.value
                circle.sub_relation = input.sub_relation
                circle.save()
                return UpdateConnectionRelationOrCircle(success=True, message= "You have Updated the connection successfully.")
            else:
                return UpdateConnectionRelationOrCircle(success=False, message= "You are not Authorized to Update this connection")
            
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateConnectionRelationOrCircle(success=False, message=message)





class CreateConnectionV2(Mutation):
    """Enhanced Connection Creation Mutation (V2)
    
    Creates a new connection request using the improved V2 connection system.
    This version provides enhanced features including bidirectional relationships,
    improved data structures, and better relationship management.
    
    Key Improvements over V1:
    - Enhanced relationship directionality support
    - Improved circle management with user-specific relations
    - Better data structure for scalability
    - Advanced relationship modification tracking
    - Feature flag protection for gradual rollout
    
    Features:
    - Bidirectional and unidirectional relationship support
    - Advanced circle management with CircleV2
    - Relationship modification count tracking
    - Duplicate connection prevention
    - Connection statistics updates
    
    Returns:
        connection (ConnectionType): The created connection object (currently None)
        success (Boolean): Whether the operation was successful
        message (String): Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated or feature not enabled
        Exception: For various business logic violations
    """
    connection = graphene.Field(ConnectionType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateConnectionInputV2()
    
    @handle_graphql_connection_errors
    @login_required
    def mutate(self, info, input):
        """Execute the V2 connection creation mutation.
        
        Args:
            info: GraphQL execution info containing user context
            input (CreateConnectionInputV2): Input data for creating V2 connection
            
        Returns:
            CreateConnectionV2: Mutation result with connection data
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            if not feature_flags.USE_NEW_CONNECTION:
                raise GraphQLError("This feature is not yet available")

            payload = info.context.payload
            user_id = payload.get('user_id')
            created_by_node = Users.nodes.get(user_id=user_id)
            receiver = Users.nodes.get(uid=input.receiver_uid)

            params = {"login_user_uid": created_by_node.uid,"secondary_user_uid":receiver.uid}
            results,_ = db.cypher_query(user_related_queries.get_connection_details_query,params)
            
            

            for connections in results:
                connection_details = connections[0]
                if connection_details:  # or any other status
                    if connection_details['connection_status'] == 'Received':
                         return CreateConnectionV2(connection=None, success=False, message="Connection already Sent.")
                    if connection_details["connection_status"] == 'Accepted':
                         return CreateConnectionV2(connection=None, success=False, message="Connection already exist.")


            connection = ConnectionV2(
                connection_status="Received",
            )
            connection.save()
            connection.receiver.connect(receiver)
            connection.created_by.connect(created_by_node)
            created_by_node.connectionv2.connect(connection)
            receiver.connectionv2.connect(connection)

            relations=relation.get_subrelation(input.sub_relation)
            created_by_relation=relations.sub_relation_name
            created_by_circle=relations.default_circle
            receiver_relation=relations.reverse_connection
            receiver_circle=relations.default_circle
            directionality=relations.directionality

            # print(created_by_relation,created_by_circle,receiver_relation,receiver_circle,directionality)

            if(directionality == 'Unidirectional'):
                receiver_relation=input.sub_relation
                
            circle_choice=CircleV2(
                    initial_sub_relation=input.sub_relation,
                    initial_directionality=directionality,
                    user_relations={
                        created_by_node.uid: {
                            "sub_relation": created_by_relation,
                            "circle_type": created_by_circle,
                            "sub_relation_modification_count": 0
                        },
                        input.receiver_uid: {
                            "sub_relation": receiver_relation,
                            "circle_type": receiver_circle,
                            "sub_relation_modification_count": 0
                        }
                }
                    
            )
            circle_choice.save()
            connection.circle.connect(circle_choice)
            try:
                connection_count.get_received_connections_count(receiver)
                connection_count.get_send_connections_count(created_by_node)
            except:
                pass

# connection=ConnectionType.from_neomodel(connection)
            return CreateConnectionV2(connection=None, success=True, message=ConnectionMessages.CONNECTION_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateConnectionV2(connection=None, success=False, message=message)


class UpdateConnectionV2(Mutation):
    """Enhanced Connection Update Mutation (V2)
    
    Updates the status of a V2 connection request with simplified logic
    compared to the legacy version. Focuses on core status changes without
    complex statistics management.
    
    Supported Operations:
    - Accept connection request
    - Reject connection request  
    - Cancel sent connection request
    
    Features:
    - Simplified authorization logic
    - Basic status validation
    - Streamlined update process
    - Error handling and messaging
    
    Returns:
        success (Boolean): Whether the operation was successful
        message (String): Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: For authorization failures or invalid operations
        
    Note:
        Connection field is commented out, indicating simplified return structure.
    """
    # connection = graphene.Field(ConnectionType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateConnectionInput()
    
    @handle_graphql_connection_errors
    @login_required
    def mutate(self, info, input):
        """Execute the V2 connection update mutation.
        
        Args:
            info: GraphQL execution info containing user context
            input (UpdateConnectionInput): Input data for updating V2 connection
            
        Returns:
            UpdateConnectionV2: Mutation result with success status
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node=Users.nodes.get(user_id=user_id) #login user
            
            connection = ConnectionV2.nodes.get(uid=input.uid) #connection attempted to update

            
            
            


            sender=connection.created_by.single()
            if input.connection_status == 'Cancelled' and user_node.email == sender.email:
                
                for key, value in input.items():
                    setattr(connection, key, value)
                connection.save()
                return UpdateConnectionV2( success=True, message=ConnectionMessages.CONNECTION_UPDATED)
            #Handle the logic:- This connection belong to login user or not
            receiver_node=connection.receiver.single() 
            if(user_node.email != receiver_node.email):
                 return UpdateConnectionV2( success=False, message="You are not Authorized to Update this connection")
            
            #Handle the logic if connection already accepted
            if connection.connection_status == 'Accepted':
                
                return UpdateConnectionV2(success=False, message="You have already accepted the connection")
            
            
            sender=connection.created_by.single()
            

            for key, value in input.items():
                setattr(connection, key, value)

            connection.save()

            

            return UpdateConnectionV2(success=True, message=ConnectionMessages.CONNECTION_UPDATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateConnectionV2( success=False, message=message)


class UpdateConnectionRelationOrCircleV2(Mutation):
    """Enhanced Connection Relationship/Circle Update Mutation (V2)
    
    Updates relationship types and circles for V2 connections with advanced features
    including modification count limits and bidirectional relationship handling.
    
    Key Features:
    - Modification count tracking (max 4 changes per user)
    - Bidirectional relationship synchronization
    - Unidirectional relationship support
    - Advanced circle management with CircleV2
    - User-specific relationship data
    
    Relationship Types:
    - Bidirectional: Changes affect both users symmetrically
    - Unidirectional: Changes affect only the initiating user
    
    Limitations:
    - Maximum 4 relationship modifications per user per connection
    - Only works with accepted connections
    - Requires authorization from connection participants
    
    Returns:
        success (Boolean): Whether the update was successful
        message (String): Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If connection not accepted, user unauthorized, or modification limit exceeded
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateConnectionRelationOrCircleInputV2()

    @handle_graphql_connection_errors       
    @login_required
    def mutate(self, info, input):
        """Execute the V2 connection relationship/circle update mutation.
        
        Args:
            info: GraphQL execution info containing user context
            input (UpdateConnectionRelationOrCircleInputV2): Input data for updating V2 relationship
            
        Returns:
            UpdateConnectionRelationOrCircleV2: Mutation result with success status
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication Failure")

            payload = info.context.payload
            user_id = payload.get('user_id')

            connection = ConnectionV2.nodes.get(uid=input.connection_uid)

            if connection.connection_status != 'Accepted':
                return UpdateConnectionRelationOrCircleV2(success=False, message=ConnectionMessages.CONNECTION_NOT_ACCEPTED)
            
            sender=connection.created_by.single()
            receiver_node=connection.receiver.single()
            user_node=Users.nodes.get(user_id=user_id)
            if receiver_node.uid != user_node.uid:
                connected_user_uid=receiver_node.uid
            else:
                connected_user_uid=sender.uid
                                
            if(user_node.email == receiver_node.email or user_node.email == sender.email):
                circle = connection.circle.single()
                
                if input.sub_relation:
                    current_count=circle.get_sub_relation_modification_count(user_node.uid)
                    if current_count <= 4:
                        relation_details=relation.get_subrelation(input.sub_relation)
                        directionality=relation_details.directionality
                        # print(directionality)
                        if directionality == 'Bidirectional':
                            circle.update_user_relation_only(connected_user_uid, relation_details.reverse_connection)
                            if input.circle_type:
                                circle.update_user_relation(user_node.uid, input.sub_relation, input.circle_type.value)
                            else:
                                circle.update_user_relation(user_node.uid, input.sub_relation,None)
                        else:
                            if input.circle_type:
                                circle.update_user_relation(user_node.uid, input.sub_relation, input.circle_type.value)
                            else:
                                circle.update_user_relation(user_node.uid, input.sub_relation,None)
                            
                            circle.update_user_relation_only(connected_user_uid, input.sub_relation)
                    else:
                        return UpdateConnectionRelationOrCircleV2(success=False, message= "You have reached the maximum modification count for this relation")
                else:
                        circle.update_user_relation(user_node.uid, input.sub_relation, input.circle_type.value)
                return UpdateConnectionRelationOrCircleV2(success=True, message= "You have Updated the connection successfully.")
            
            
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateConnectionRelationOrCircleV2(success=False, message=message)




class Mutation(graphene.ObjectType):
    """Legacy Connection Mutations Schema
    
    Contains all legacy (V1) connection mutations with mixed V1/V2 support.
    This schema is maintained for backward compatibility while transitioning
    to the new V2 system.
    
    Available Mutations:
    - send_connection: Legacy connection creation (deprecated)
    - send_connection_v2: New V2 connection creation (recommended)
    - update_connection: Legacy connection updates
    - delete_connection: Connection deletion (shared between V1/V2)
    - update_connection_relation_or_circle: Legacy relationship updates
    
    Migration Path:
    - Use send_connection_v2 instead of send_connection
    - Consider MutationV2 schema for full V2 experience
    """
    # send_connection=CreateConnection.Field()
    send_connection = CreateConnection.Field(
        description="⚠️ Deprecated! Use sendConnectionV2 instead."
    )
    send_connection_v2 = CreateConnectionV2.Field()  # New recommended mutation
    update_connection=UpdateConnection.Field()
    delete_connection=DeleteConnection.Field()
    update_connection_relation_or_circle=UpdateConnectionRelationOrCircle.Field()
    


class MutationV2(graphene.ObjectType):
    """Enhanced Connection Mutations Schema (V2)
    
    Contains all V2 connection mutations providing the latest features
    and improved functionality for connection management.
    
    Available Mutations:
    - send_connection: V2 connection creation with enhanced features
    - update_connection: V2 connection updates with simplified logic
    - delete_connection: Connection deletion (shared with V1)
    - update_connection_relation_or_circle: V2 relationship updates with advanced features
    
    Key Improvements:
    - Enhanced relationship directionality
    - Advanced circle management
    - Modification count tracking
    - Improved data structures
    - Better scalability
    
    Recommended Usage:
    Use this schema for new implementations requiring the latest
    connection management features.
    """
    send_connection=CreateConnectionV2.Field()
    update_connection=UpdateConnectionV2.Field()
    delete_connection=DeleteConnection.Field()
    update_connection_relation_or_circle=UpdateConnectionRelationOrCircleV2.Field()
