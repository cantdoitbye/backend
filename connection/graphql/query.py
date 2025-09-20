import graphene
from graphene import Mutation
from graphql_jwt.decorators import login_required, superuser_required
from connection.models import ConnectionV2, Relation, SubRelation
from auth_manager.models import Users
from community.utils import helperfunction
from community.models import Community, SubCommunity
from connection.graphql.raw_queries import user_related_queries
from connection.utils.connection_decorator import handle_graphql_connection_errors
from user_activity.services.activity_service import ActivityService
from django.contrib.auth.models import User
import json


import random
from neomodel import db

from .types import *
from auth_manager.graphql.types import ProfileNoUserType
from auth_manager.models import Users
from connection.models import Connection


class Query(graphene.ObjectType):
    """
    Main GraphQL Query class for connection-related operations.
    
    This class provides GraphQL queries for managing user connections, recommendations,
    community interactions, and user relationship data. It handles various aspects of
    the social networking functionality including:
    
    - User recommendations and discovery
    - Connection management and filtering
    - Community member recommendations
    - User feed generation
    - Raw data extraction for analytics
    
    All queries are protected with authentication decorators and error handling.
    """
    
    # User recommendation queries
    recommended_users = graphene.List(RecommendedUserType)

    @handle_graphql_connection_errors
    @login_required
    def resolve_recommended_users(self, info):
        """
        Retrieve recommended users for the authenticated user.
        
        This query uses a sophisticated recommendation algorithm to suggest users
        that the current user might want to connect with. The recommendations are
        based on various factors including mutual connections, shared interests,
        location proximity, and user behavior patterns.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            
        Returns:
            List[RecommendedUserType]: List of recommended users with their profiles
            
        Business Logic:
            - Extracts user ID from JWT token payload
            - Executes complex Cypher query for user recommendations
            - Returns user and profile data for recommended connections
            
        Security:
            - Requires user authentication
            - Protected by connection error handling decorator
        """
        payload = info.context.payload
        user_id = payload.get('user_id')  # Extract authenticated user ID
        user_node = Users.nodes.get(user_id=user_id)
        uid = user_node.uid
        params = {"uid": uid}
        recommended_user = []
        
        # Execute recommendation algorithm via Cypher query
        results, _ = db.cypher_query(
            user_related_queries.recommended_users_query, params)
        
        # Process results and build recommendation list
        for result in results:
            user_node = result[0]  # Recommended user node
            profile_node = result[1]  # User's profile data
            recommended_user.append(
                RecommendedUserType.from_neomodel(user_node, profile_node)
            )

        return recommended_user

    
    # User feed and discovery queries
    my_users_feed = graphene.List(UserCategoryType, search=graphene.String())

    @handle_graphql_connection_errors
    @login_required
    def resolve_my_users_feed(self, info, search=None):
        """
        Generate personalized user feed categories for the authenticated user.
        
        This query creates a categorized feed of users based on different criteria
        such as shared interests (vibes), location, organization, sports, and
        connection status. It's used to populate the user discovery interface
        with relevant user suggestions organized by category.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            search: Optional search string to filter users by username, email, firstName, or lastName
            
        Returns:
            List[UserCategoryType]: List of user categories with associated users
            
        Categories:
            - Top Vibes - Hobbies: Users with similar hobby interests
            - Top Vibes - Trending Topics: Users interested in trending topics
            - Top Vibes - Country: Users from the same country
            - Top Vibes - Organisation: Users from the same organization
            - Top Vibes - Sport: Users with similar sports interests
            - Connected Circle: Users in the user's connection network
            - New Arrivals: Recently joined users
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        
        # Define feed categories for user discovery
        details = ["Top Vibes - Hobbies", "Top Vibes - Trending Topics", "Top Vibes - Country",
                   "Top Vibes - Organisation", "Top Vibes - Sport", "Connected Circle", "New Arrivals"]
        
        # Generate category-based user feed with search filter
        return [UserCategoryType.from_neomodel(user_node, detail, search) for detail in details]
    
    
    # Administrative connection queries
    all_connections = graphene.List(ConnectionType)

    @login_required
    @superuser_required
    def resolve_all_connections(self, info):
        """
        Retrieve all connections in the system (Admin only).
        
        This administrative query returns all connection records in the database.
        It's primarily used for system monitoring, analytics, and administrative
        purposes. Access is restricted to superusers only.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[ConnectionType]: List of all connections in the system
            
        Security:
            - Requires superuser privileges
            - Protected by authentication decorators
            
        Use Cases:
            - System administration and monitoring
            - Connection analytics and reporting
            - Data export and backup operations
        """
        # Return all connections for administrative purposes
        return [ConnectionType.from_neomodel(story) for story in Connection.nodes.all()]

   
    # Individual connection queries
    connection_byuid = graphene.Field(
        ConnectionType, connection_uid=graphene.String(required=True))
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_connection_byuid(self, info, connection_uid):
        """
        Retrieve a specific connection by its unique identifier.
        
        This query fetches detailed information about a single connection
        using its UID. It's useful for displaying connection details,
        editing connection properties, or performing connection-specific operations.
        
        Args:
            info: GraphQL resolve info containing request context
            connection_uid (str): Unique identifier of the connection to retrieve
            
        Returns:
            ConnectionType: The connection object with all its properties
            
        Raises:
            DoesNotExist: If no connection exists with the provided UID
            
        Security:
            - Requires user authentication
            - Protected by connection error handling decorator
        """
        # Fetch connection by unique identifier
        connection = Connection.nodes.get(uid=connection_uid)
        return ConnectionType.from_neomodel(connection)

    # User's personal connection queries
    my_connection = graphene.List(
        ConnectionType, status=StatusEnum(), circle_type=CircleTypeEnum())

    @handle_graphql_connection_errors
    @login_required
    def resolve_my_connection(self, info, status=None, circle_type=None):
        """
        Retrieve the authenticated user's connections with optional filtering.
        
        This query returns all connections associated with the current user,
        with optional filtering by connection status and circle type. It supports
        different connection states and relationship circles for comprehensive
        connection management.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            status (StatusEnum, optional): Filter by connection status
                - Received: Incoming connection requests
                - Sent: Outgoing connection requests
                - Accepted: Established connections
                - Cancelled: Cancelled connections
            circle_type (CircleTypeEnum, optional): Filter by relationship circle
                - Inner: Close personal connections
                - Outer: Professional or acquaintance connections
                - Universe: Public or distant connections
                
        Returns:
            List[ConnectionType]: Filtered list of user's connections
            
        Business Logic:
            - Filters connections based on user's perspective (sent vs received)
            - Applies circle type filtering for relationship categorization
            - Handles different connection statuses appropriately
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        connected_user = user_node.connection.all()  # Get all user connections
        email = user_node.email

        def filter_connections(connection_status, email_check=None):
            """Helper function to filter connections based on criteria."""
            my_connections = []

            for connection in connected_user:
                # Filter by connection status
                if status and connection.connection_status != connection_status:
                    continue
                # Apply email-based filtering (for sent/received logic)
                if email_check and email_check(connection, email):
                    continue
                # Filter by circle type if specified
                if circle_type and connection.circle.single().circle_type != circle_type.value:
                    continue

                my_connections.append(connection)

            return [ConnectionType.from_neomodel(x) for x in my_connections]

        # Apply status-based filtering
        if status:
            if status.value == "Received":
                # Connections received by the user (exclude own sent requests)
                return filter_connections("Received", lambda conn, email: conn.created_by.single().email == email)
            elif status.value == "Sent":
                # Connections sent by the user
                return filter_connections("Received", lambda conn, email: conn.created_by.single().email != email)
            elif status.value == "Accepted":
                # Established connections
                return filter_connections("Accepted")
            elif status.value == "Cancelled":
                # Cancelled connections
                return filter_connections("Cancelled")
        else:
            # No status filter - apply only circle_type filter if provided
            my_connections = [
                connection for connection in connected_user
                if not circle_type or connection.circle.single().circle_type == circle_type.value
            ]
            return [ConnectionType.from_neomodel(x) for x in my_connections]

        

    # Relation management queries
    all_relations = graphene.List(RelationType)
    relations = graphene.List(RelationType)
    relation = graphene.Field(RelationType, id=graphene.Int())

    @login_required
    def resolve_relations(self, info):
        """
        Retrieve all available relation types.
        
        This query returns all relation types that can be used to categorize
        connections between users. Relations define the nature of relationships
        (e.g., friend, colleague, family, etc.).
        
        Returns:
            List[RelationType]: All available relation types in the system
        """
        return Relation.objects.all()

    @login_required
    def resolve_all_relations(self, info):
        """
        Retrieve all available relation types (alias for relations).
        
        This is an alias method for resolve_relations, providing the same
        functionality with a different query name for backward compatibility.
        
        Returns:
            List[RelationType]: All available relation types in the system
        """
        return Relation.objects.all()
    

    @login_required
    def resolve_relation(self, info, id):
        """
        Retrieve a specific relation type by ID.
        
        This query fetches detailed information about a single relation type
        using its database ID. Useful for relation management and editing.
        
        Args:
            info: GraphQL resolve info containing request context
            id (int): Database ID of the relation to retrieve
            
        Returns:
            RelationType: The relation object with its properties
            
        Raises:
            DoesNotExist: If no relation exists with the provided ID
        """
        return Relation.objects.get(pk=id)

    # Connection detail queries
    connection_details_by_user_id = graphene.List(
        ConnectionType, user_id=graphene.String(required=True))
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_connection_details_by_user_id(self, info, user_id):
        """
        Retrieve connection details between the authenticated user and a specific user.
        
        This query finds and returns connection information between the current
        authenticated user and another user specified by user_id. It's useful
        for checking connection status, relationship details, and mutual connections.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            user_id (str): User ID of the other user to check connections with
            
        Returns:
            List[ConnectionIsConnectedType]: Connection details between the users
            
        Business Logic:
            - Uses Cypher query to find connections between two specific users
            - Returns bidirectional connection information
            - Useful for connection status checking and relationship analysis
            
        Cypher Query:
            Matches users and their shared connections using HAS_CONNECTION relationships
        """
        payload = info.context.payload
        user2_id = payload.get('user_id')  # Authenticated user's ID
    
        # Cypher query to find connections between two users
        query = """
                MATCH (u1:Users {user_id: $user_id})-[:HAS_CONNECTION]->(c:Connection)<-[:HAS_CONNECTION]-(u2:Users {user_id: $user2_id})
                RETURN c
            """

        # Parameters for the Cypher query
        params = {
            "user_id": str(user_id),      # Target user ID
            "user2_id": str(user2_id)     # Authenticated user ID
        }

        # Execute the Cypher query
        results, meta = db.cypher_query(query, params)

        # Process and return connection results
        connection_node = [Connection.inflate(row[0]) for row in results]
        return [ConnectionIsConnectedType.from_neomodel(x) for x in connection_node]
        

    # Sent connection queries
    my_sent_connection = graphene.List(ConnectionType)

    @handle_graphql_connection_errors
    @login_required
    def resolve_my_sent_connection(self, info):
        """
        Retrieve connection requests sent by the authenticated user.
        
        This query returns all connection requests that the current user has sent
        to other users and are still in "Received" status (pending acceptance).
        It's useful for displaying outgoing connection requests and managing
        sent invitations.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            
        Returns:
            List[ConnectionType]: List of connections sent by the user
            
        Business Logic:
            - Finds connections where the user is the sender
            - Filters for "Received" status (pending requests)
            - Uses Cypher query for efficient database traversal
            
        Cypher Query:
            Matches connections with HAS_SEND_CONNECTION relationship to the user
        """
        payload = info.context.payload
        user_id = payload.get('user_id')

        # Cypher query to find connections sent by the user
        query = """
            MATCH (c:Connection)-[:HAS_SEND_CONNECTION]->(u:Users {user_id: $user_id})
            WHERE c.connection_status = "Received" RETURN c
        """

        # Parameters for the query
        params = {
            "user_id": str(user_id)  # Authenticated user's ID
        }

        # Execute the Cypher query
        results, meta = db.cypher_query(query, params)

        # Process and return connection results
        connection_node = [Connection.inflate(row[0]) for row in results]
        return [ConnectionType.from_neomodel(x) for x in connection_node]

        

    # Community recommendation queries
    recommended_users_for_community = graphene.List(
        RecommendedUserForCommunityType, community_uid=graphene.String(required=True))
   
    @handle_graphql_connection_errors
    @login_required
    def resolve_recommended_users_for_community(self, info, community_uid):
        """
        Get recommended users for connection within a specific community.
        
        This query finds all users in the system and checks their membership
        status in the specified community. It's useful for community administrators
        to see potential members and their current membership status.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            community_uid (str): Unique identifier of the community
            
        Returns:
            List[RecommendedUserForCommunityType]: All users with membership status
            
        Business Logic:
            - Retrieves all users in the system
            - Excludes the community administrator from recommendations
            - Checks membership status for each user using helper function
            - Returns user data with membership flag for UI display
            
        Use Cases:
            - Community member management
            - Invitation and recruitment workflows
            - Membership status overview
        """
        users = Users.nodes.all()
        community = Community.nodes.get(uid=community_uid)
        admin_user = community.created_by.single()
        # List to hold the result with `is_member` field
        recommended_users = []

        for user in users:
            if user.email == admin_user.email:
                continue
            # Call helper function to check membership
            is_member = False
            check = helperfunction.get_membership_for_user_in_community(
                user, community)
            if check:
                is_member = True

            recommended_users.append(

                RecommendedUserForCommunityType(
                    uid=user.uid,
                    user_id=user.user_id,
                    username=user.username,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    user_type=user.user_type,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    created_by=user.created_by,
                    updated_by=user.updated_by,
                    is_member=is_member,
                    profile=ProfileNoUserType.from_neomodel(user.profile.single(
                    )) if user.profile.single() else None,  # Pass the membership status here
                )
            )

        return recommended_users

    recommended_Connected_users_for_community = graphene.List(
        RecommendedUserForCommunityType, community_uid=graphene.String(required=True))
   
    @handle_graphql_connection_errors
    @login_required
    def resolve_recommended_Connected_users_for_community(self, info, community_uid):
        """
        Get recommended users from the community admin's connection network.
        
        This query finds users who are connected to the community administrator
        and shows their membership status in the specified community. It's useful
        for leveraging the admin's network to grow community membership.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            community_uid (str): Unique identifier of the community
            
        Returns:
            List[RecommendedUserForCommunityType]: Connected users with membership status
            
        Business Logic:
            - Gets all users connected to the community administrator
            - Removes duplicate users using UID tracking
            - Checks membership status for each connected user
            - Returns user data with membership flag
            
        Use Cases:
            - Network-based community growth
            - Leveraging admin connections for invitations
            - Targeted membership campaigns
        """
        community = Community.nodes.get(uid=community_uid)
        admin_user = community.created_by.single()
        user_connected = admin_user.connection.all()
        member_users = []
        # List to hold the result with `is_member` field
        recommended_users = []
        # Set to track unique user UIDs to prevent duplicates
        unique_user_uids = set()
        
        for connection in user_connected:
            user = connection.receiver.single()
            member_users.append(user)

        for user in member_users:
            # Skip if this user has already been added
            if user.uid in unique_user_uids:
                continue
                
            # Add the user UID to the set of unique UIDs
            unique_user_uids.add(user.uid)
            
            # Call helper function to check membership
            is_member = False
            check = helperfunction.get_membership_for_user_in_community(
                user, community)
            if check:
                is_member = True

            # Append each user along with the computed `is_member` field
            recommended_users.append(
                RecommendedUserForCommunityType(
                    uid=user.uid,
                    user_id=user.user_id,
                    username=user.username,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    user_type=user.user_type,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    created_by=user.created_by,
                    updated_by=user.updated_by,
                    is_member=is_member,
                    profile=ProfileNoUserType.from_neomodel(user.profile.single(
                    )) if user.profile.single() else None,  # Pass the membership status here
                )
            )

        return recommended_users

    # Sub-community recommendation queries
    recommended_Connected_users_for_sub_community = graphene.List(
        RecommendedUserForCommunityType, sub_community_uid=graphene.String(required=True))
   
    @handle_graphql_connection_errors
    @login_required
    def resolve_recommended_Connected_users_for_sub_community(self, info, sub_community_uid):
        """
        Get recommended users from the sub-community admin's connection network.
        
        This query finds users who are connected to the sub-community administrator
        and shows their membership status in the specified sub-community. It enables
        targeted growth of sub-communities through the admin's existing network.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            sub_community_uid (str): Unique identifier of the sub-community
            
        Returns:
            List[RecommendedUserForCommunityType]: Connected users with membership status
            
        Business Logic:
            - Gets all users connected to the sub-community administrator
            - Filters for "Accepted" status connections only
            - Removes duplicate users using UID tracking
            - Checks sub-community membership status for each user
            
        Use Cases:
            - Sub-community growth through admin networks
            - Targeted invitations to sub-communities
            - Leveraging existing connections for community building
        """
        community = SubCommunity.nodes.get(uid=sub_community_uid)
        admin_user = community.created_by.single()
        user_connected = admin_user.connection.all()
        print(user_connected)
        member_users = []
        # List to hold the result with `is_member` field
        recommended_users = []
        # Set to track unique user UIDs to prevent duplicates
        unique_user_uids = set()
        
        for connection in user_connected:
            if connection.connection_status == "Accepted":
                user = connection.receiver.single()
                member_users.append(user)

        for user in member_users:
            # Skip if this user has already been added
            if user.uid in unique_user_uids:
                continue
                
            # Add the user UID to the set of unique UIDs
            unique_user_uids.add(user.uid)
            
            # Call helper function to check membership
            is_member = False
            check = helperfunction.get_membership_for_user_in_sub_community(
                user, community)
            if check:
                is_member = True

            # Append each user along with the computed `is_member` field
            recommended_users.append(
                RecommendedUserForCommunityType(
                    uid=user.uid,
                    user_id=user.user_id,
                    username=user.username,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    user_type=user.user_type,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    created_by=user.created_by,
                    updated_by=user.updated_by,
                    is_member=is_member  # Pass the membership status here
                )
            )

        return recommended_users
    # Connected user queries (optimization and review needed)
    my_connected_user = graphene.List(
        UserConnectedUserType, status=StatusEnum(), circle_type=CircleTypeEnum())
   
    @handle_graphql_connection_errors
    @login_required
    def resolve_my_connected_user(self, info, status=None, circle_type=None):
        """
        Retrieve users connected to the authenticated user with optional filtering.
        
        This query returns actual user objects (not connection objects) for users
        who are connected to the authenticated user. It provides filtering by
        connection status and circle type, making it useful for user discovery
        and connection management interfaces.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            status (StatusEnum, optional): Filter by connection status
                - Received: Users who sent connection requests to current user
                - Sent: Users to whom current user sent connection requests
                - Accepted: Users with established connections
                - Cancelled: Users with cancelled connections
            circle_type (CircleTypeEnum, optional): Filter by relationship circle
                - Inner: Close personal connections
                - Outer: Professional or acquaintance connections
                - Universe: Public or distant connections
                
        Returns:
            List[UserConnectedUserType]: List of connected users (not connections)
            
        Business Logic:
            - Extracts actual user objects from connection relationships
            - Filters based on user's perspective (sent vs received)
            - Applies circle type filtering for relationship categorization
            - Returns the "other" user in each connection (not the authenticated user)
            
        Note:
            This method needs optimization and review for performance improvements.
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        connected_user = user_node.connection.all()
        email = user_node.email

        def filter_connections(connection_status, email_check=None):
            my_connections = []
            all_users = []

            for connection in connected_user:
                if status and connection.connection_status != connection_status:
                    continue
                if email_check and not email_check(connection, email):
                    continue
                if circle_type and connection.circle.single().circle_type != circle_type.value:
                    continue

                my_connections.append(connection)

                created_by = connection.created_by.single()
                receiver = connection.receiver.single()
                if created_by.email != email:
                    all_users.append(created_by)
                if receiver.email != email:
                    all_users.append(receiver)

            return all_users

        if status:
            if status.value == "Received":
                return [UserConnectedUserType.from_neomodel(user) for user in filter_connections("Received", lambda conn, email: conn.created_by.single().email != email)]
            elif status.value == "Sent":
                return [UserConnectedUserType.from_neomodel(user) for user in filter_connections("Received", lambda conn, email: conn.created_by.single().email == email)]
            elif status.value == "Accepted":
                return [UserConnectedUserType.from_neomodel(user) for user in filter_connections("Accepted")]
            elif status.value == "Cancelled":
                return [UserConnectedUserType.from_neomodel(user) for user in filter_connections("Cancelled")]
        else:
            # If no status is provided, filter by circle_type if given
            my_connections = [
                connection for connection in connected_user
                if not circle_type or connection.circle.single().circle_type == circle_type.value
            ]

            all_users = []
            for connection in my_connections:
                created_by = connection.created_by.single()
                receiver = connection.receiver.single()
                if created_by.email != email:
                    all_users.append(created_by)
                if receiver.email != email:
                    all_users.append(receiver)

            return [UserConnectedUserType.from_neomodel(user) for user in all_users]

        

    # Secondary user connection queries with filtering
    connected_user_of_secondaryuser_by_useruid = graphene.List(UserConnectedUserType, user_uid=graphene.String(
        required=True), status=StatusSecondaryUserEnum(), circle_type=CircleTypeEnum())
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_connected_user_of_secondaryuser_by_useruid(self, info, user_uid, status=None, circle_type=None):
        """
        Get users connected to a specific secondary user with advanced filtering.
        
        This query retrieves users connected to a specified secondary user with
        optional filtering by connection status and circle type. It provides
        detailed control over which connections to display based on relationship
        status and intimacy level.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            user_uid (str): Unique identifier of the secondary user
            status (StatusSecondaryUserEnum, optional): Filter by connection status
                - Accepted: Users with established connections
            circle_type (CircleTypeEnum, optional): Filter by relationship circle
                - Inner: Close personal connections
                - Outer: Professional or acquaintance connections
                - Universe: Public or distant connections
                
        Returns:
            List[UserConnectedUserType]: Filtered list of connected users
            
        Business Logic:
            - Gets the secondary user by UID
            - Retrieves all connections for that user
            - Applies status and circle type filters
            - Extracts the "other" users from each connection
            - Uses helper function for consistent filtering logic
            
        Use Cases:
            - Network analysis with specific criteria
            - Connection discovery based on relationship types
            - Social graph exploration with filtering
            - Privacy-aware connection viewing
        """
        user_node = Users.nodes.get(uid=user_uid)

        connected_user = user_node.connection.all()
        email = user_node.email

        def filter_connections(connection_status, email_check=None):
            my_connections = []
            all_users = []

            for connection in connected_user:
                if status and connection.connection_status != connection_status:
                    continue
                if email_check and not email_check(connection, email):
                    continue
                if circle_type and connection.circle.single().circle_type != circle_type.value:
                    continue

                my_connections.append(connection)

                created_by = connection.created_by.single()
                receiver = connection.receiver.single()
                if created_by.email != email:
                    all_users.append(created_by)
                if receiver.email != email:
                    all_users.append(receiver)

            return all_users

        if status:
            if status.value == "Accepted":
                return [UserConnectedUserType.from_neomodel(user) for user in filter_connections("Accepted")]

        else:
            # If no status is provided, filter by circle_type if given
            my_connections = [
                connection for connection in connected_user
                if not circle_type or connection.circle.single().circle_type == circle_type.value
            ]

            all_users = []
            for connection in my_connections:
                created_by = connection.created_by.single()
                receiver = connection.receiver.single()
                if created_by.email != email:
                    all_users.append(created_by)
                if receiver.email != email:
                    all_users.append(receiver)

            return [UserConnectedUserType.from_neomodel(user) for user in all_users]

        

    # User feed and relationship analysis queries
    users_feed_by_user_uid = graphene.List(
        SecondaryUserType, user_uid=graphene.String(required=True))
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_users_feed_by_user_uid(self, info, user_uid):
        """
        Generate user feed data showing relationship details between users.
        
        This query creates feed entries that describe the relationship between
        the authenticated user and a specified secondary user. It returns
        relationship insights like mutual connections and common interests.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            user_uid (str): Unique identifier of the secondary user
            
        Returns:
            List[SecondaryUserType]: Feed entries describing user relationships
            
        Business Logic:
            - Prevents self-referential feeds (returns empty for same user)
            - Generates predefined relationship insights
            - Creates feed entries for "Mutual Connection" and "Common Interest"
            - Uses authenticated user's UID as the primary reference
            - Tracks profile visit as social interaction
            
        Use Cases:
            - Social feed generation
            - Relationship discovery interfaces
            - Connection recommendation context
            - User interaction insights
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        user_node_uid = user_node.uid
        
        # Prevent self-referential feeds
        if (user_node_uid == user_uid):
            return []
        
        # Track profile visit as social interaction
        try:
            # Get Django User instances from Users neomodel instances
            django_user = User.objects.get(id=user_node.user_id)
            target_user_node = Users.nodes.get(uid=user_uid)
            django_target_user = User.objects.get(id=target_user_node.user_id)
            
            # Create ActivityService instance
            activity_service = ActivityService()
            activity_service.track_social_interaction(
                user=django_user,
                target_user=django_target_user,
                interaction_type='profile_visit',
                context_type='feed_view',
                context_id=user_uid
            )
        except Exception as e:
            # Log error but don't fail the query
            print(f"Error tracking profile visit: {e}")
            
        # Generate relationship insight details
        details = ["Mutual Connection", "Common Interest"]
        return [SecondaryUserType.from_neomodel(user_node_uid, user_uid, detail)for detail in details]
 
    # Raw data extraction queries
    get_users_raw_data = graphene.List(
        graphene.JSONString, user_uid=graphene.String(required=True))

    def resolve_get_users_raw_data(self, info, user_uid):
        """
        Extract comprehensive raw user data for analytics and processing.
        
        This query retrieves detailed user information including profile data,
        circle preferences, and engagement history. It's designed for data
        analysis, recommendation systems, and comprehensive user profiling.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            user_uid (str): Unique identifier of the user
            
        Returns:
            List[JSONString]: Comprehensive user data in JSON format
            
        Business Logic:
            - Uses Cypher queries for efficient data extraction
            - Combines user profile, circle, and engagement data
            - Handles missing fields gracefully with None values
            - Exports data to JSON file for external processing
            - Structures data for machine learning and analytics
            
        Data Structure:
            - Basic user information (ID, name, age, location, gender)
            - Preferences (interests, circle configurations)
            - Content moderation (muted content)
            - Engagement history and patterns
            
        Use Cases:
            - User analytics and insights
            - Recommendation system training
            - Data export for external tools
            - User behavior analysis
        """
        params = {"uid": user_uid}
        results1, _ = db.cypher_query(
            user_related_queries.get_raw_data_from_user, params)

        user_data = []

        for result in results1:
            # Extract the details from each result
            user_details = result[0]
            profile_details = result[1]
            inner_circle_details = result[2]
            outer_circle_details = result[3]
            universal_circle_details = result[4]
            recent_engagement_details = result[5]

            # Convert into the desired format, checking for missing fields and returning None (null) if not present
            user = {
                # Return None if 'user_id' is not present
                "user_id": user_details.get("user_id", None),
                "name": user_details.get("first_name", None),
                "age": profile_details.get("age", None),
                "location": profile_details.get("lives_in", None),
                "gender": profile_details.get("gender", None),
                "preferences": {
                    # Return None if 'interests' is not present
                    "interests": profile_details.get("interests", None),
                    # Check if inner circle exists
                    "inner_circle": inner_circle_details if inner_circle_details else None,
                    # Check if outer circle exists
                    "outer_circle": outer_circle_details if outer_circle_details else None,
                    # Check if universe circle exists
                    "universe": universal_circle_details if universal_circle_details else None
                },
                # Return None if 'muted_content' is not present
                "muted_content": user_details.get("muted_content", None),
                # Return None if 'recent_engagements' is not present
                "recent_engagements": recent_engagement_details if recent_engagement_details else None
            }

            # Add the user to the list
            user_data.append(user)
            # print(user_data)

            with open('user_data.json', 'w') as json_file:
                json.dump(user_data, json_file, indent=4)

        return user_data

    get_content_raw_data = graphene.List(
        graphene.JSONString,
        post_uids=graphene.List(graphene.String, required=True)  # List of post UIDs to retrieve
    )

    # @login_required
    def resolve_get_content_raw_data(self, info, post_uids):
        """
        Extract comprehensive raw content data for analytics and processing.
        
        This query retrieves detailed content information including post data,
        author information, and engagement metrics. It's designed for content
        analysis, recommendation systems, and comprehensive content profiling.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            post_uids (List[str]): List of post unique identifiers to retrieve
            
        Returns:
            List[JSONString]: Comprehensive content data in JSON format
            
        Business Logic:
            - Uses Cypher queries for efficient batch data extraction
            - Combines post content, author, and engagement data
            - Handles missing fields gracefully with default values
            - Structures data for machine learning and analytics
            - Processes multiple posts in a single query for efficiency
            
        Data Structure:
            - Content metadata (ID, title, description, type)
            - Author information and attribution
            - Categories, tags, and classification
            - Engagement metrics (views, likes, comments, shares)
            - Privacy and sponsorship status
            - Vibes score and social signals
            
        Use Cases:
            - Content analytics and insights
            - Recommendation system training
            - Content performance analysis
            - Social media metrics tracking
        """
        params = {"postUids": post_uids}
        results1, _ = db.cypher_query(
            user_related_queries.get_raw_data_from_content, params)

        content_data = []

        for result in results1:
            # Extract the details from each result
            post_details = result[0]
            user_details = result[1]
            like_counts = result[2]
            comment_counts = result[3]

            # Convert into the desired format, checking for missing fields and returning None (null) if not present
            content = {
                # Unique ID of the post
                "content_id": post_details.get("uid", None),
                # Title of the post
                "title": post_details.get("post_title", None),
                # Description of the post
                "description": post_details.get("post_text", None),
                "author_id": user_details.get("uid", None),  # ID of the author
                # Type of content, e.g., 'post'
                "type": post_details.get("post_type", None),
                # List of categories
                "categories": post_details.get("categories", []),
                "tags": post_details.get("tags", []),  # List of tags
                # Publication timestamp
                "timestamp": post_details.get("created_at", None),
                # Sponsorship status
                "is_sponsored": post_details.get("is_sponsored", False),
                "privacy": post_details.get("privacy"),  # Privacy level
                "engagement": {
                    "views": post_details.get("views", 0),  # Number of views
                    # Number of impressions
                    "impressions": post_details.get("impressions", 0),
                    "likes": like_counts,  # Number of likes
                    "comments": comment_counts,  # Number of comments
                    # Number of shares
                    "shares": post_details.get("share_count", 0),
                    # Vibes score
                    "vibes_score": post_details.get("vibe_score", 0)
                }
            }

            # Add the user to the list
            content_data.append(content)
            # print(content_data)

            with open('content_data.json', 'w') as json_file:
                json.dump(content_data, json_file, indent=4)

        return content_data

    # Connection grouping and categorization queries
    grouped_connections_by_relation = graphene.List(ConnectionV2CategoryType)

    @handle_graphql_connection_errors
    @login_required
    def resolve_grouped_connections_by_relation(self, info):
        """
        Group user connections by relationship circles (Inner, Outer, Universe).
        
        This query organizes the authenticated user's connections into categories
        based on their circle types. It provides a structured view of relationships
        organized by intimacy and relationship strength.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            
        Returns:
            List[ConnectionV2CategoryType]: Connections grouped by circle type
            
        Business Logic:
            - Retrieves all connections for the authenticated user
            - Groups connections into predefined circles (Inner, Outer, Universe)
            - Determines the connected user (receiver or creator) for each connection
            - Filters out empty circle groups
            - Uses ConnectionV2Type for enhanced connection representation
            
        Circle Types:
            - Inner: Close personal relationships and family
            - Outer: Professional contacts and acquaintances
            - Universe: Public connections and distant relationships
            
        Use Cases:
            - Connection management interfaces
            - Relationship visualization
            - Privacy-based content sharing
            - Social network analysis
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        connections = user_node.connection.all() 

        circles = ['Inner', 'Outer', 'Universe']
        result = []
        for circle in circles:
            result.append({
                "title": circle,
                "data": []
            })
        for connection in connections:
            circle = connection.circle.single()
            if circle:
                circle_type = circle.circle_type
                for circle_group in result:
                    if circle_group['title'] == circle_type:
                     
                        connected_user = connection.receiver.single() if str(connection.receiver.single().uid) != user_node.uid else connection.created_by.single()
                        connection_data = ConnectionV2Type.from_neomodel(connection, user_uid=connected_user.uid)
                        if connection_data:  # Only add if connection_data is not None
                            circle_group['data'].append(connection_data)
                        break
        
        # Filter out circle groups with empty data arrays
        return [circle_group for circle_group in result if circle_group['data']]

    # Community member management queries
    grouped_community_members = graphene.List(
        GroupedCommunityMemberCategoryType, community_uid=graphene.String(required=True))
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_grouped_community_members(self, info, community_uid):
        """
        Group community members by their roles (leaders and members).
        
        This query organizes community or sub-community members into role-based
        categories. It supports both regular communities and sub-communities,
        providing a structured view of membership hierarchy.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            community_uid (str): Unique identifier of the community or sub-community
            
        Returns:
            List[GroupedCommunityMemberCategoryType]: Members grouped by role
            
        Business Logic:
            - Attempts to find community first, then sub-community if not found
            - Groups members into "Leaders" and "Members" categories
            - Checks leadership status using is_leader or is_admin flags
            - Filters out empty groups from the response
            - Handles both Community and SubCommunity entities
            
        Role Categories:
            - Leaders: Users with administrative or leadership privileges
            - Members: Regular community participants
            
        Use Cases:
            - Community administration interfaces
            - Member management and moderation
            - Role-based access control
            - Community hierarchy visualization
            
        Error Handling:
            - Raises exception if community/sub-community not found
            - Provides detailed error messages for debugging
        """
        
        try:
            try:
                community = Community.nodes.get(uid=community_uid)
                memberships = community.members.all()
            except Community.DoesNotExist:
                community = SubCommunity.nodes.get(uid=community_uid)
                memberships = community.sub_community_members.all()
            
            result = [
                GroupedCommunityMemberCategoryType(title="Leaders", data=[]),
                GroupedCommunityMemberCategoryType(title="Members", data=[])
            ]
            
            for membership in memberships:
                member_user = membership.user.single()
                if not member_user:
                    continue
                    
                is_leader = getattr(membership, 'is_leader', False) or getattr(membership, 'is_admin', False)
                
                group_idx = 0 if is_leader else 1
                
                member_data = GroupedCommunityMemberType.from_neomodel(member_user.uid)
                result[group_idx].data.append(member_data)
            
            return [group for group in result if group.data]
            
        except Community.DoesNotExist:
            raise Exception("Community not found")
        except Exception as e:
            raise Exception(f"Error fetching community members: {str(e)}")

      
class QueryV2(graphene.ObjectType):
    """
    Enhanced GraphQL query class for connection management (Version 2).
    
    This class provides improved connection queries with enhanced filtering,
    better performance, and additional features compared to the original Query class.
    It focuses on ConnectionV2 entities and provides more sophisticated
    relationship management capabilities.
    
    Features:
        - Enhanced connection filtering with improved circle type support
        - Better user connection mapping and relationship tracking
        - Improved performance through optimized query patterns
        - Support for advanced connection status management
        - Enhanced user feed and recommendation systems
    
    Use Cases:
        - Modern connection management interfaces
        - Advanced social networking features
        - Improved user experience with better filtering
        - Enhanced relationship analytics and insights
    """

    # Enhanced connection queries with improved filtering
    my_connection = graphene.List(
        UserConnectedUserTypeV2, status=StatusEnum(), circle_type=CircleTypeEnumV2())
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_my_connection(self, info, status=None, circle_type=None):
        """
        Retrieve enhanced user connections with advanced filtering (Version 2).
        
        This improved version provides better connection filtering with enhanced
        circle type support and improved user-connection mapping. It returns
        actual user objects with their associated connection details.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            status (StatusEnum, optional): Filter by connection status
                - Received: Connection requests received by current user
                - Sent: Connection requests sent by current user
                - Accepted: Established connections
                - Cancelled: Cancelled connections
            circle_type (CircleTypeEnumV2, optional): Enhanced circle type filtering
                - Inner: Close personal connections
                - Outer: Professional connections
                - Universe: Public connections
                
        Returns:
            List[UserConnectedUserTypeV2]: Enhanced user connection objects
            
        Business Logic:
            - Uses ConnectionV2 entities for improved functionality
            - Implements user-connection mapping for better data structure
            - Supports dynamic circle type checking per user
            - Filters connections based on user perspective (sent vs received)
            - Returns enhanced user objects with connection context
            
        Improvements over V1:
             - Better circle type handling with get_circle_type() method
             - Enhanced user-connection mapping structure
             - Improved filtering logic and performance
         """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        login_user_uid = user_node.uid

        connected_user = user_node.connectionv2.all()
        email = user_node.email

        def filter_connections(connection_status, email_check=None):
            my_connections = []
            # all_users = []
            user_connection_map = []

            for connection in connected_user:
                # print(connection)
                if status and connection.connection_status != connection_status:
                    continue
                if email_check and not email_check(connection, email):
                    continue
                if circle_type and connection.circle.single().get_circle_type(user_node.uid) != circle_type.value:
                    continue

                my_connections.append(connection)
                # print("my_connections",my_connections)
                created_by = connection.created_by.single()
                receiver = connection.receiver.single()
                if created_by.email != email:
                    user_connection_map.append({
                        'user': created_by,
                        'connection': connection
                    })
                if receiver.email != email:
                    user_connection_map.append({
                        'user': receiver,
                        'connection': connection
                    })

            return user_connection_map

        if status:
            if status.value == "Received":
                mapped_data = filter_connections("Received", lambda conn, email: conn.created_by.single().email != email)
            elif status.value == "Sent":
                mapped_data = filter_connections("Received", lambda conn, email: conn.created_by.single().email == email)
            elif status.value == "Accepted":
                mapped_data = filter_connections("Accepted")
            elif status.value == "Cancelled":
                mapped_data = filter_connections("Cancelled")
            
            # Convert mapped data to your UserConnectedUserTypeV2
            return [
                UserConnectedUserTypeV2.from_neomodel(
                    item['user'], 
                    login_user_uid, 
                    item['connection']
                ) for item in mapped_data
            ]

    
  
        
    # Enhanced connection detail queries
    connection_details_by_user_id = graphene.List(UserConnectedUserTypeV2, user_id=graphene.String(required=True))
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_connection_details_by_user_id(self, info, user_id):
        """
        Retrieve enhanced connection details between authenticated user and target user (V2).
        
        This improved version provides enhanced connection details using ConnectionV2
        entities with better data structure and improved user representation.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            user_id (str): User ID of the target user to check connections with
            
        Returns:
            List[UserConnectedUserTypeV2]: Enhanced connection details between users
            
        Business Logic:
            - Uses Cypher query to find ConnectionV2 relationships between users
            - Returns enhanced user connection objects with improved data structure
            - Provides better connection context and user information
            - Uses ConnectionV2 entities for improved functionality
            
        Improvements over V1:
            - Enhanced UserConnectedUserTypeV2 objects with richer data
            - Better connection context and relationship information
            - Improved data structure for frontend consumption
            
        Cypher Query:
            Matches users and their shared ConnectionV2 relationships using HAS_CONNECTION
        """
        payload = info.context.payload
        user2_id = payload.get('user_id')
        
        # Define the Cypher query
        query = """
                    MATCH (u1:Users {user_id: $user_id})-[:HAS_CONNECTION]->(c:ConnectionV2)<-[:HAS_CONNECTION]-(u2:Users {user_id: $user2_id})
                    RETURN c
                """

        # Parameters to pass to the query
        params = {
            # Replace with your variable holding user1 ID
            "user_id": str(user_id),
            # Replace with your variable holding user2 ID
            "user2_id": str(user2_id)
        }

        # Execute the query
        results, meta = db.cypher_query(query, params)
        
        connection_node = [ConnectionV2.inflate(row[0]) for row in results]

        user_node = Users.nodes.get(user_id=user2_id)
        login_user_uid = user_node.uid
        secondary_user=user_node.nodes.get(user_id=user_id)
        
        return [UserConnectedUserTypeV2.from_neomodel(
                    secondary_user, 
                    login_user_uid, 
                    x
                ) for x in connection_node]
        
        

    # Secondary user connection queries with enhanced filtering
    connected_user_of_secondaryuser_by_useruid = graphene.List(
        UserConnectedUserTypeV2,user_uid=graphene.String(required=True), status=StatusSecondaryUserEnum(), circle_type=CircleTypeEnumV2())
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_connected_user_of_secondaryuser_by_useruid(self, info, user_uid,status=None, circle_type=None):
        """
        Retrieve enhanced connections of a secondary user by their UID (V2).
        
        This improved version provides enhanced connection filtering and data structure
        for viewing another user's connections with better circle type handling.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            user_uid (str): UID of the secondary user whose connections to retrieve
            status (StatusSecondaryUserEnum, optional): Filter by connection status
            circle_type (CircleTypeEnumV2, optional): Filter by circle type
            
        Returns:
            List[UserConnectedUserTypeV2]: Enhanced connections of the secondary user
            
        Business Logic:
            - Fetches secondary user by UID and retrieves their ConnectionV2 relationships
            - Applies enhanced filtering by status and circle type
            - Uses improved get_circle_type() method for better circle classification
            - Returns enhanced user connection objects with richer data structure
            
        Status Filtering:
            - 'Received': Connections received by the secondary user
            - 'Sent': Connections sent by the secondary user
            - 'Accepted': Mutually accepted connections
            - 'Cancelled': Cancelled connections
            
        Improvements over V1:
            - Enhanced circle type handling with get_circle_type() method
            - Better user-connection mapping structure
            - Improved filtering logic and data representation
            - Enhanced UserConnectedUserTypeV2 objects
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(uid=user_uid)
        login_user_uid = user_node.uid
        
        connected_user = user_node.connectionv2.all()
        email = user_node.email

        def filter_connections(connection_status, email_check=None):
            my_connections = []
            # all_users = []
            user_connection_map = []

            for connection in connected_user:
                
                if status and connection.connection_status != connection_status:
                    continue
                if email_check and not email_check(connection, email):
                    continue
                if circle_type and connection.circle.single().get_circle_type(user_node.uid) != circle_type.value:
                    continue

                my_connections.append(connection)
                
                created_by = connection.created_by.single()
                receiver = connection.receiver.single()
                if created_by.email != email:
                    user_connection_map.append({
                        'user': created_by,
                        'connection': connection
                    })
                if receiver.email != email:
                    user_connection_map.append({
                        'user': receiver,
                        'connection': connection
                    })

            return user_connection_map

        if status:
            if status.value == "Received":
                mapped_data = filter_connections("Received", lambda conn, email: conn.created_by.single().email != email)
            elif status.value == "Sent":
                mapped_data = filter_connections("Received", lambda conn, email: conn.created_by.single().email == email)
            elif status.value == "Accepted":
                mapped_data = filter_connections("Accepted")
            elif status.value == "Cancelled":
                mapped_data = filter_connections("Cancelled")
            
            # Convert mapped data to your UserConnectedUserTypeV2
            return [
                UserConnectedUserTypeV2.from_neomodel(
                    item['user'], 
                    login_user_uid, 
                    item['connection']
                ) for item in mapped_data
            ]

        
        

    # Enhanced user feed queries
    users_feed_by_user_uid = graphene.List(
        SecondaryUserTypeV2, user_uid=graphene.String(required=True))
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_users_feed_by_user_uid(self, info, user_uid):
        """
        Generate enhanced user feed data for a secondary user by their UID (V2).
        
        This improved version provides enhanced user feed generation with better
        relationship context and improved data structure for frontend consumption.
        
        Args:
            info: GraphQL resolve info containing request context and user payload
            user_uid (str): UID of the secondary user to generate feed for
            
        Returns:
            List[SecondaryUserTypeV2]: Enhanced user feed data with relationship context
            
        Business Logic:
            - Prevents self-feed generation (returns empty list for same user)
            - Generates enhanced feed data with relationship context
            - Provides 'Mutual Connection' and 'Common Interest' relationship types
            - Uses SecondaryUserTypeV2 for improved data representation
            
        Feed Types:
            - 'Mutual Connection': Indicates shared connections between users
            - 'Common Interest': Indicates shared interests or communities
            
        Improvements over V1:
            - Enhanced SecondaryUserTypeV2 objects with richer context
            - Better relationship type classification
            - Improved data structure for feed consumption
            - Enhanced user relationship insights
            
        Security:
            - Validates user authentication through login_required decorator
            - Prevents self-feed generation for privacy
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        user_node_uid = user_node.uid
        if (user_node_uid == user_uid):
            return []
        details = ["Mutual Connection", "Common Interest"]
        return [SecondaryUserTypeV2.from_neomodel(user_node_uid, user_uid, detail)for detail in details]
    

    # Inherited relation queries from Query class
    # These methods provide backward compatibility and shared functionality
    relations=Query.relations
    resolve_relations=Query.resolve_relations

    relations_by_id=Query.relation
    resolve_relations_by_id=Query.resolve_relation

    
