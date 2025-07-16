import graphene
from graphene import Mutation
from graphql_jwt.decorators import login_required, superuser_required
from connection.models import ConnectionV2, Relation, SubRelation
from auth_manager.models import Users
from community.utils import helperfunction
from community.models import Community, SubCommunity
from connection.graphql.raw_queries import user_related_queries
from connection.utils.connection_decorator import handle_graphql_connection_errors
import json


import random
from neomodel import db

from .types import *
from auth_manager.graphql.types import ProfileNoUserType
from auth_manager.models import Users
from connection.models import Connection


class Query(graphene.ObjectType):
    recommended_users = graphene.List(RecommendedUserType)

    @handle_graphql_connection_errors
    @login_required
    def resolve_recommended_users(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        uid = user_node.uid
        params = {"uid": uid}
        recommended_user = []
        results, _ = db.cypher_query(
            user_related_queries.recommended_users_query, params)
        for result in results:
            user_node = result[0]
            profile_node = result[1]
            recommended_user.append(
                RecommendedUserType.from_neomodel(user_node, profile_node)
            )

        return recommended_user

    
    my_users_feed = graphene.List(UserCategoryType)

    @handle_graphql_connection_errors
    @login_required
    def resolve_my_users_feed(self, info):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        details = ["Top Vibes - Hobbies", "Top Vibes - Trending Topics", "Top Vibes - Country",
                   "Top Vibes - Organisation", "Top Vibes - Sport", "Connected Circle", "New Arrivals"]
        return [UserCategoryType.from_neomodel(user_node, detail)for detail in details]
    
    

    all_connections = graphene.List(ConnectionType)

    @login_required
    @superuser_required
    def resolve_all_connections(self, info):
        return [ConnectionType.from_neomodel(story) for story in Connection.nodes.all()]

   
    connection_byuid = graphene.Field(
        ConnectionType, connection_uid=graphene.String(required=True))
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_connection_byuid(self, info, connection_uid):
        connection = Connection.nodes.get(uid=connection_uid)
        return ConnectionType.from_neomodel(connection)

    my_connection = graphene.List(
        ConnectionType, status=StatusEnum(), circle_type=CircleTypeEnum())

    @handle_graphql_connection_errors
    @login_required
    def resolve_my_connection(self, info, status=None, circle_type=None):
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            connected_user = user_node.connection.all()
            email = user_node.email

            def filter_connections(connection_status, email_check=None):
                my_connections = []

                for connection in connected_user:
                    if status and connection.connection_status != connection_status:
                        continue
                    if email_check and email_check(connection, email):
                        continue
                    if circle_type and connection.circle.single().circle_type != circle_type.value:
                        continue

                    my_connections.append(connection)

                return [ConnectionType.from_neomodel(x) for x in my_connections]

            if status:
                if status.value == "Received":
                    return filter_connections("Received", lambda conn, email: conn.created_by.single().email == email)
                elif status.value == "Sent":
                    return filter_connections("Received", lambda conn, email: conn.created_by.single().email != email)
                elif status.value == "Accepted":
                    return filter_connections("Accepted")
                elif status.value == "Cancelled":
                    return filter_connections("Cancelled")
            else:
                # If no status is provided, filter by circle_type if given
                my_connections = [
                    connection for connection in connected_user
                    if not circle_type or connection.circle.single().circle_type == circle_type.value
                ]
                return [ConnectionType.from_neomodel(x) for x in my_connections]

        

    all_relations = graphene.List(RelationType)
    relations = graphene.List(RelationType)
    relation = graphene.Field(RelationType, id=graphene.Int())

    
    @login_required
    def resolve_relations(self, info):
        return Relation.objects.all()

    @login_required
    def resolve_all_relations(self, info):
        return Relation.objects.all()
    

    @login_required
    def resolve_relation(self, info, id):
        return Relation.objects.get(pk=id)

    connection_details_by_user_id = graphene.List(
        ConnectionType, user_id=graphene.String(required=True))
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_connection_details_by_user_id(self, info, user_id):
            payload = info.context.payload
            user2_id = payload.get('user_id')
        
            query = """
                    MATCH (u1:Users {user_id: $user_id})-[:HAS_CONNECTION]->(c:Connection)<-[:HAS_CONNECTION]-(u2:Users {user_id: $user2_id})
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

            connection_node = [Connection.inflate(row[0]) for row in results]
            return [ConnectionIsConnectedType.from_neomodel(x) for x in connection_node]
        

    my_sent_connection = graphene.List(ConnectionType)

    @handle_graphql_connection_errors
    @login_required
    def resolve_my_sent_connection(self, info):
        # Define the Cypher query to retrieve connections sent by the user
        
            payload = info.context.payload
            user_id = payload.get('user_id')

            query = """
                MATCH (c:Connection)-[:HAS_SEND_CONNECTION]->(u:Users {user_id: $user_id})
                WHERE c.connection_status = "Received" RETURN c
            """

            # Parameters to pass to the query
            params = {
                # User ID for whom connections are to be fetched
                "user_id": str(user_id)
            }

            # Execute the query
            results, meta = db.cypher_query(query, params)

            # Inflate the connection node results
            connection_node = [Connection.inflate(row[0]) for row in results]

            # Return the connection data as a list of ConnectionType
            return [ConnectionType.from_neomodel(x) for x in connection_node]

        

    

    recommended_users_for_community = graphene.List(
        RecommendedUserForCommunityType, community_uid=graphene.String(required=True))
   
    @handle_graphql_connection_errors
    @login_required
    def resolve_recommended_users_for_community(self, info, community_uid):
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

    recommended_Connected_users_for_sub_community = graphene.List(
        RecommendedUserForCommunityType, sub_community_uid=graphene.String(required=True))
    @handle_graphql_connection_errors
    @login_required
    def resolve_recommended_Connected_users_for_sub_community(self, info, sub_community_uid):
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
    # optimisation and review needed
    
    my_connected_user = graphene.List(
        UserConnectedUserType, status=StatusEnum(), circle_type=CircleTypeEnum())
    @handle_graphql_connection_errors
    @login_required
    def resolve_my_connected_user(self, info, status=None, circle_type=None):
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

        

    connected_user_of_secondaryuser_by_useruid = graphene.List(UserConnectedUserType, user_uid=graphene.String(
        required=True), status=StatusSecondaryUserEnum(), circle_type=CircleTypeEnum())
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_connected_user_of_secondaryuser_by_useruid(self, info, user_uid, status=None, circle_type=None):

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

        

    users_feed_by_user_uid = graphene.List(
        SecondaryUserType, user_uid=graphene.String(required=True))
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_users_feed_by_user_uid(self, info, user_uid):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        user_node_uid = user_node.uid
        if (user_node_uid == user_uid):
            return []
        details = ["Mutual Connection", "Common Interest"]
        return [SecondaryUserType.from_neomodel(user_node_uid, user_uid, detail)for detail in details]
 
    get_users_raw_data = graphene.List(
        graphene.JSONString, user_uid=graphene.String(required=True))

    
    def resolve_get_users_raw_data(self, info, user_uid):
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
        # Proper placement of `required=True`
        post_uids=graphene.List(graphene.String, required=True)
    )

    # @login_required
    def resolve_get_content_raw_data(self, info, post_uids):
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

    grouped_connections_by_relation = graphene.List(ConnectionV2CategoryType)

    @handle_graphql_connection_errors
    @login_required
    def resolve_grouped_connections_by_relation(self, info):
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

    grouped_community_members = graphene.List(
        GroupedCommunityMemberCategoryType, community_uid=graphene.String(required=True))
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_grouped_community_members(self, info, community_uid):
        """
        Group community members by their roles (leaders and members)
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

    my_connection = graphene.List(
        UserConnectedUserTypeV2, status=StatusEnum(), circle_type=CircleTypeEnumV2())
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_my_connection(self, info, status=None, circle_type=None):
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

    
  
        
    connection_details_by_user_id = graphene.List(UserConnectedUserTypeV2, user_id=graphene.String(required=True))
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_connection_details_by_user_id(self, info, user_id):
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
        
        

    connected_user_of_secondaryuser_by_useruid = graphene.List(
        UserConnectedUserTypeV2,user_uid=graphene.String(required=True), status=StatusSecondaryUserEnum(), circle_type=CircleTypeEnumV2())
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_connected_user_of_secondaryuser_by_useruid(self, info, user_uid,status=None, circle_type=None):
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

        
        

    users_feed_by_user_uid = graphene.List(
        SecondaryUserTypeV2, user_uid=graphene.String(required=True))
    
    @handle_graphql_connection_errors
    @login_required
    def resolve_users_feed_by_user_uid(self, info, user_uid):
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        user_node_uid = user_node.uid
        if (user_node_uid == user_uid):
            return []
        details = ["Mutual Connection", "Common Interest"]
        return [SecondaryUserTypeV2.from_neomodel(user_node_uid, user_uid, detail)for detail in details]
    

    relations=Query.relations
    resolve_relations=Query.resolve_relations

    relations_by_id=Query.relation
    resolve_relations_by_id=Query.resolve_relation

    
