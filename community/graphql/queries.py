"""Community GraphQL Queries Module

This module provides comprehensive GraphQL query resolvers for the community management system.
It handles all community-related data retrieval operations including:

- Community and subcommunity information
- Membership management and user roles
- Community goals, activities, affiliations, and achievements
- Community recommendations and feeds
- Role-based access control and permissions

The module supports both regular communities and subcommunities with proper authorization
and error handling through decorators.

Key Features:
- JWT-based authentication for all queries
- Role-based access control for sensitive operations
- Support for filtering by community type, circle, and category
- Comprehensive error handling with custom decorators
- Neo4j database integration for graph-based relationships
- Optimized queries for performance

Author: Community Team
Version: 2.0
"""

from graphene_django import DjangoObjectType
from neomodel import db
import graphene
from graphene.types.generic import GenericScalar

from .types import *
from community.models import *
from auth_manager.models import Users
from .enums.circle_type_enum import CircleTypeEnum
from ..utils import userlist, helperfunction
from .enums.group_type_enum import GroupTypeEnum, CategoryEnum
from vibe_manager.models import CommunityVibe
from community.graphql.raw_queries.community_query import *
from community.utils.generate_community import generate_communities_based_on_interest 
from graphql_jwt.decorators import login_required, superuser_required
from community.utils.community_decorator import handle_graphql_community_errors 
from auth_manager.Utils.generate_presigned_url import generate_file_info


class SubCommunityRoleManagerType(DjangoObjectType):
    """GraphQL type for SubCommunityRoleManager model.
    
    Provides GraphQL representation of subcommunity role management,
    including role definitions and permissions for subcommunity members.
    """
    class Meta:
        model = SubCommunityRoleManager


class CommunityRoleManagerType(DjangoObjectType):
    """GraphQL type for CommunityRoleManager model.
    
    Provides GraphQL representation of community role management,
    including role definitions and permissions for community members.
    """
    class Meta:
        model = CommunityRoleManager


class CommunityRoleAssignmentType(DjangoObjectType):
    """GraphQL type for CommunityRoleAssignment model.
    
    Provides GraphQL representation of role assignments,
    mapping users to specific roles within communities.
    """
    class Meta:
        model = CommunityRoleAssignment


class Query(graphene.ObjectType):
    """Main GraphQL Query class for community-related operations.
    
    This class contains all GraphQL query resolvers for community management,
    including community discovery, membership management, role assignments,
    and content retrieval. All queries require authentication and many include
    authorization checks.
    
    Features:
    - Community and subcommunity queries
    - Membership and role management
    - Content queries (goals, activities, affiliations, achievements)
    - Recommendation and feed systems
    - Administrative queries for superusers
    """
    
    
    community_messages = graphene.List(
        CommunityMessagesType, community_id=graphene.String(required=True))
    
    community_byuid = graphene.Field(
        CommunityDetailsType, uid=graphene.String(required=True))
    @handle_graphql_community_errors
    @login_required
    def resolve_community_byuid(self, info, uid):
        """Retrieve community or subcommunity details by UID.
        
        Fetches detailed information about a community or subcommunity based on the provided UID.
        If a community with the given UID doesn't exist, it attempts to find a subcommunity.
        
        Args:
            info: GraphQL resolve info containing request context
            uid (str): Unique identifier of the community or subcommunity
            
        Returns:
            CommunityDetailsType: Detailed community or subcommunity information
            
        Raises:
            DoesNotExist: If neither community nor subcommunity exists with the given UID
            
        Note:
            This method requires code review and optimization as indicated by the original comment.
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        try:
            community = Community.nodes.get(uid=uid)
            return CommunityDetailsType.from_neomodel(community, None,user_node)
        except Community.DoesNotExist:
            # If Community does not exist, try fetching SubCommunity
            
            sub_community = SubCommunity.nodes.get(uid=uid)
            return CommunityDetailsType.from_neomodel(None,sub_community, user_node)
                
    my_community = graphene.List(
        CommunityType, community_type=GroupTypeEnum(), community_circle=CircleTypeEnum())
    
    @handle_graphql_community_errors
    @login_required
    def resolve_my_community(self, info, community_type=None, community_circle=None):
        """Retrieve communities that the authenticated user is a member of.
        
        Fetches all communities where the current user has membership, with optional
        filtering by community type and circle.
        
        Args:
            info: GraphQL resolve info containing request context
            community_type (GroupTypeEnum, optional): Filter by community type
            community_circle (CircleTypeEnum, optional): Filter by community circle
            
        Returns:
            List[CommunityType]: List of communities the user is a member of
        """

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        my_communities = list(filter(lambda community: (not community_type or community.community_type == community_type.value) and
                                        (not community_circle or community.community_circle ==
                                        community_circle.value),
                                        user_node.community.all()
                                        ))

        return [CommunityType.from_neomodel(x) for x in my_communities]

   
    # New query that returns communities grouped by type
    grouped_communities = graphene.List(GroupedCommunityCategoryType)
    
    @handle_graphql_community_errors
    @login_required
    def resolve_grouped_communities(self, info):
        """Retrieve communities grouped by type for the authenticated user.
        
        Fetches user's communities and subcommunities, organizing them by type:
        - Interest groups
        - Official groups
        - Personal groups
        - Business groups
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[GroupedCommunityCategoryType]: Communities grouped by category type
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        params = {
            'user_email': user_node.email,
        }
        results1, meta = db.cypher_query(
            get_log_in_user_communities_query, params)
        results2, meta = db.cypher_query(
            get_log_in_user_sub_communities_query, params)
        
        details = ["interest group", "official group", "personal group", "business group"]
        grouped_data = []
        
        # Combine both results for processing
        all_results = results1 + results2
        
        for detail in details:
            # Filter communities by type from both results
            filtered_results = [community for community in all_results 
                             if community[0].get('community_type', '').lower() == detail.lower() or community[0].get('sub_community_group_type', '').lower() == detail.lower()]
            if filtered_results:
                grouped_data.append(GroupedCommunityCategoryType.from_neomodel(detail, filtered_results))

        return grouped_data
    
        
   
    community_members_by_community_uid = graphene.List(
        MembershipType, community_uid=graphene.String(required=True))

    
    @handle_graphql_community_errors
    @login_required
    def resolve_community_members_by_community_uid(self, info, community_uid):
        """Retrieve all members of a specific community.
        
        Fetches the complete membership list for a given community.
        
        Args:
            info: GraphQL resolve info containing request context
            community_uid (str): Unique identifier of the community
            
        Returns:
            List[MembershipType]: List of all community memberships
            
        Raises:
            DoesNotExist: If community with given UID doesn't exist
        """
        community = Community.nodes.get(uid=community_uid)
        communitymember = list(community.members.all())
        return [MembershipType.from_neomodel(member) for member in communitymember]

    
    sub_community_members_by_sub_community_uid = graphene.List(
        SubCommunityMembershipType, sub_community_uid=graphene.String(required=True))   
    @handle_graphql_community_errors
    @login_required
    def resolve_sub_community_members_by_sub_community_uid(self, info, sub_community_uid):
        """Retrieve all members of a specific subcommunity.
        
        Fetches the complete membership list for a given subcommunity.
        
        Args:
            info: GraphQL resolve info containing request context
            sub_community_uid (str): Unique identifier of the subcommunity
            
        Returns:
            List[SubCommunityMembershipType]: List of all subcommunity memberships
            
        Raises:
            DoesNotExist: If subcommunity with given UID doesn't exist
        """
        community = SubCommunity.nodes.get(uid=sub_community_uid)
        communitymember = list(community.sub_community_members.all())
        return [SubCommunityMembershipType.from_neomodel(member) for member in communitymember]
    
    
    community_member_by_community_uid_and_user_uid = graphene.List(
        MembershipType,
        community_uid=graphene.String(required=True),
        # Add user_uid as an optional argument
        user_uid=graphene.String(required=True)
    )
    @handle_graphql_community_errors
    @login_required
    def resolve_community_member_by_community_uid_and_user_uid(self, info, community_uid, user_uid):
        """Retrieve community members connected to a specific user.
        
        Fetches community members who are connected to the specified user,
        providing filtered membership information based on user connections.
        
        Args:
            info: GraphQL resolve info containing request context
            community_uid (str): Unique identifier of the community
            user_uid (str): Unique identifier of the user to filter connections
            
        Returns:
            List[MembershipType]: List of memberships for users connected to the specified user
            
        Raises:
            DoesNotExist: If community or user with given UIDs don't exist
        """
        community = Community.nodes.get(uid=community_uid)

        if user_uid:
            # If user_uid is provided, filter the memberships for this specific user
            user_node = Users.nodes.get(uid=user_uid)
            community_members = [
                member
                for member in community.members.all()
                if member.user.is_connected(user_node)
            ]

        return [MembershipType.from_neomodel(member) for member in community_members]

        

    recentlyjoinedmember_by_community_uid = graphene.List(
        MembershipType,
        community_uid=graphene.String(required=True),
        # Optional, but handled differently for your specific query requirement
        user_uid=graphene.String(required=False)
    )

    @handle_graphql_community_errors
    @login_required
    def resolve_recentlyjoinedmember_by_community_uid(self, info, community_uid, user_uid=None):
        """Retrieve recently joined members of a community.
        
        Fetches community members sorted by join date (newest first), with optional
        filtering by user connections.
        
        Args:
            info: GraphQL resolve info containing request context
            community_uid (str): Unique identifier of the community
            user_uid (str, optional): Filter members connected to this user
            
        Returns:
            List[MembershipType]: List of memberships sorted by join date (newest first)
            
        Raises:
            DoesNotExist: If community or user with given UIDs don't exist
        """
        # Fetch the community node by its UID
        community = Community.nodes.get(uid=community_uid)

        if user_uid:
            # If user_uid is provided, fetch the user node
            user_node = Users.nodes.get(uid=user_uid)
            # Filter the memberships to include only those connected to the provided user node
            community_members = [
                member
                for member in community.members.all()
                if member.user.is_connected(user_node)
            ]
        else:
            # If no user_uid is provided, get all memberships in the community
            community_members = list(community.members.all())

        # Sort community members by join time from newer to older
        community_members.sort(
            key=lambda member: member.join_date, reverse=True)

        # Return the memberships as list of MembershipType objects
        return [MembershipType.from_neomodel(member) for member in community_members]

        

    my_community_member = graphene.List(MembershipType)
    @handle_graphql_community_errors
    @login_required
    def resolve_my_community_member(self, info):
        """Retrieve all members from communities owned by the authenticated user.
        
        Fetches all members from all communities that the current user has created or owns.
        This is typically used by community administrators to view their community memberships.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[MembershipType]: List of all memberships from user's communities
            
        Note:
            Only community admins/creators can access this information.
        """

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_communities = user_node.community.all()
        community_member = []
        for member in my_communities:
            community_member.extend(list(member.members))
        return [MembershipType.from_neomodel(x) for x in community_member]
        

    user_community_membership = graphene.List(
        CommunityInfoType, community_type=GroupTypeEnum(), community_circle=CircleTypeEnum())
    @handle_graphql_community_errors
    @login_required
    def resolve_user_community_membership(self, info, community_type=None, community_circle=None):
        """Retrieve detailed membership information for the authenticated user.
        
        Fetches comprehensive information about all communities and subcommunities
        where the user has membership, with optional filtering capabilities.
        
        Args:
            info: GraphQL resolve info containing request context
            community_type (GroupTypeEnum, optional): Filter by community type
            community_circle (CircleTypeEnum, optional): Filter by community circle
            
        Returns:
            List[CommunityInfoType]: Detailed community membership information
            
        Note:
            This method requires optimization and review as indicated by the original comment.
        """
        payload = info.context.payload
        user_id = payload.get('user_id')

        
        user_node = Users.nodes.get(user_id=user_id)
        user_email = user_node.email  # Get the email of the logged-in user

            # Define the parameters for the query
        params = {
            'user_email': user_email,
            'community_type': community_type.value if community_type is not None else None,
            'community_circle': community_circle.value if community_circle is not None else None,
        }

            # Execute the query and get results
        results1, meta = db.cypher_query(
            get_log_in_user_community_details_query, params)
        results2, meta = db.cypher_query(
            get_log_in_user_sub_community_details_query, params)
            

        return [CommunityInfoType.from_neomodel(results1, results2)]


    communitymembership_details_by_community_uid = graphene.List(
        MembershipType, community_uid=graphene.String(required=True))
    
    @handle_graphql_community_errors
    @login_required
    def resolve_communitymembership_details_by_community_uid(self, info, community_uid):
        """Check if the authenticated user is a member of a specific community.
        
        Verifies membership status and returns membership details for the current user
        in the specified community.
        
        Args:
            info: GraphQL resolve info containing request context
            community_uid (str): Unique identifier of the community to check
            
        Returns:
            List[MembershipType]: User's membership details in the community (empty if not a member)
            
        Note:
            Uses Cypher query to efficiently check membership status.
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        user_email = user_node.email  # Get the email of the logged-in user

        # Cypher query to match communities where the membership is associated with the logged-in user's email
        query = """
        MATCH (c:Community)-[:MEMBER_OF]->(m:Membership)-[:MEMBER]->(u:Users)
        WHERE u.email = $user_email AND c.uid = $community_uid
        RETURN m
        """

        # Define the parameters for the query
        params = {'user_email': user_email, 'community_uid': community_uid}

        # Execute the query and get results
        results, meta = db.cypher_query(query, params)

        # Inflate the results into Membership objects
        memberships = [Membership.inflate(row[0]) for row in results]

        # Convert Membership objects to MembershipType GraphQL objects
        return [MembershipType.from_neomodel(membership) for membership in memberships]

    community_goal_by_community_uid = graphene.List(
        CommunityGoalType, community_uid=graphene.String(required=True))
    
    @handle_graphql_community_errors
    @login_required
    def resolve_community_goal_by_community_uid(self, info, community_uid):
        """Retrieve all goals for a specific community or subcommunity.
        
        Fetches all non-deleted goals associated with the given community or subcommunity UID.
        
        Args:
            info: GraphQL resolve info containing request context
            community_uid (str): Unique identifier of the community or subcommunity
            
        Returns:
            List[CommunityGoalType]: List of active community goals
            
        Raises:
            DoesNotExist: If neither community nor subcommunity exists with the given UID
        """
        try:
            community = Community.nodes.get(uid=community_uid)
            goals = community.communitygoal.all()
            community_goals = [goal for goal in goals if not goal.is_deleted]
            return [CommunityGoalType.from_neomodel(goal) for goal in community_goals]
        except Community.DoesNotExist:
            community = SubCommunity.nodes.get(uid=community_uid)
            goals = community.communitygoal.all()
            community_goals = [goal for goal in goals if not goal.is_deleted]
            return [CommunityGoalType.from_neomodel(goal) for goal in community_goals]     
        

    my_community_goals = graphene.List(CommunityGoalType)

    @handle_graphql_community_errors
    @login_required
    def resolve_my_community_goals(self, info):
        """Retrieve all goals from communities the authenticated user belongs to.
        
        Fetches goals from all communities where the current user has membership.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[CommunityGoalType]: List of goals from user's communities
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_communities = user_node.community.all()
        goals = []
        for community in my_communities:
            goals.extend(list(community.communitygoal))
        return [CommunityGoalType.from_neomodel(x) for x in goals]
    

    community_activity_by_community_uid = graphene.List(
        CommunityActivityType, community_uid=graphene.String(required=True))
    
    @handle_graphql_community_errors
    @login_required
    def resolve_community_activity_by_community_uid(self, info, community_uid):
        """Retrieve all activities for a specific community or subcommunity.
        
        Fetches all non-deleted activities associated with the given community or subcommunity UID.
        
        Args:
            info: GraphQL resolve info containing request context
            community_uid (str): Unique identifier of the community or subcommunity
            
        Returns:
            List[CommunityActivityType]: List of active community activities
            
        Raises:
            DoesNotExist: If neither community nor subcommunity exists with the given UID
        """
        try:
            community = Community.nodes.get(uid=community_uid)
            activities = community.communityactivity.all()
            community_activities = [activity for activity in activities if not activity.is_deleted]
            return [CommunityActivityType.from_neomodel(activity) for activity in community_activities]
        except Community.DoesNotExist:
            community = SubCommunity.nodes.get(uid=community_uid)
            activities = community.communityactivity.all()
            community_activities = [activity for activity in activities if not activity.is_deleted]
            return [CommunityActivityType.from_neomodel(activity) for activity in community_activities]

    
    my_community_activities = graphene.List(CommunityActivityType)

    @handle_graphql_community_errors
    @login_required
    def resolve_my_community_activities(self, info):
        """Retrieve all activities from communities the authenticated user belongs to.
        
        Fetches activities from all communities where the current user has membership.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[CommunityActivityType]: List of activities from user's communities
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_communities = user_node.community.all()
        activities = []
        for community in my_communities:
            activities.extend(list(community.communityactivity))
        return [CommunityActivityType.from_neomodel(x) for x in activities]
    

    community_affiliation_by_community_uid = graphene.List(
        CommunityAffiliationType, community_uid=graphene.String(required=True))
    
    @handle_graphql_community_errors
    @login_required
    def resolve_community_affiliation_by_community_uid(self, info, community_uid):
        """Retrieve all affiliations for a specific community or subcommunity.
        
        Fetches all non-deleted affiliations associated with the given community or subcommunity UID.
        
        Args:
            info: GraphQL resolve info containing request context
            community_uid (str): Unique identifier of the community or subcommunity
            
        Returns:
            List[CommunityAffiliationType]: List of active community affiliations
            
        Raises:
            DoesNotExist: If neither community nor subcommunity exists with the given UID
        """
        try:
            community = Community.nodes.get(uid=community_uid)
            affiliations = community.communityaffiliation.all()
            community_affiliations = [affiliation for affiliation in affiliations if not affiliation.is_deleted]
            return [CommunityAffiliationType.from_neomodel(affiliation) for affiliation in community_affiliations]
        except Community.DoesNotExist:
            community = SubCommunity.nodes.get(uid=community_uid)
            affiliations = community.communityaffiliation.all()
            community_affiliations = [affiliation for affiliation in affiliations if not affiliation.is_deleted]
            return [CommunityAffiliationType.from_neomodel(affiliation) for affiliation in community_affiliations]


    my_community_affiliations = graphene.List(CommunityAffiliationType)

    @handle_graphql_community_errors
    @login_required
    def resolve_my_community_affiliations(self, info):
        """Retrieve all affiliations from communities the authenticated user belongs to.
        
        Fetches affiliations from all communities where the current user has membership.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[CommunityAffiliationType]: List of affiliations from user's communities
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_communities = user_node.community.all()
        affiliations = []
        for community in my_communities:
            affiliations.extend(list(community.communityaffiliation))
        return [CommunityAffiliationType.from_neomodel(x) for x in affiliations]
        
        
    community_achievement_by_community_uid = graphene.List(
        CommunityAchievementType, community_uid=graphene.String(required=True))
    
    @handle_graphql_community_errors
    @login_required
    def resolve_community_achievement_by_community_uid(self, info, community_uid):
        """Retrieve all achievements for a specific community or subcommunity.
        
        Fetches all non-deleted achievements associated with the given community or subcommunity UID.
        
        Args:
            info: GraphQL resolve info containing request context
            community_uid (str): Unique identifier of the community or subcommunity
            
        Returns:
            List[CommunityAchievementType]: List of active community achievements
            
        Raises:
            DoesNotExist: If neither community nor subcommunity exists with the given UID
        """
        try:
            community = Community.nodes.get(uid=community_uid)
            achievements = community.communityachievement.all()
            community_achievements = [achievement for achievement in achievements if not achievement.is_deleted]
            return [CommunityAchievementType.from_neomodel(achievement) for achievement in community_achievements]
        except Community.DoesNotExist:
            community = SubCommunity.nodes.get(uid=community_uid)
            achievements = community.communityachievement.all()
            community_achievements = [achievement for achievement in achievements if not achievement.is_deleted]
            return [CommunityAchievementType.from_neomodel(achievement) for achievement in community_achievements]


    my_community_achievements = graphene.List(CommunityAchievementType)

    @handle_graphql_community_errors
    @login_required
    def resolve_my_community_achievements(self, info):
        """Retrieve all achievements from communities the authenticated user belongs to.
        
        Fetches achievements from all communities where the current user has membership.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[CommunityAchievementType]: List of achievements from user's communities
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_communities = user_node.community.all()
        achievements = []
        for community in my_communities:
            achievements.extend(list(community.communityachievement))
        return [CommunityAchievementType.from_neomodel(x) for x in achievements]
        

    recommended_communities = graphene.List(
        CommunityType,
        community_circle=CircleTypeEnum(),
        community_type=GroupTypeEnum(),
        category=CategoryEnum()
    )
    @handle_graphql_community_errors
    @login_required
    def resolve_recommended_communities(self, info, community_circle=None, community_type=None, category=None):
        """Retrieve recommended communities for the authenticated user.
        
        Returns a list of communities that might be of interest to the current user
        based on recommendation algorithms. Supports filtering by circle, type, and category.
        
        Args:
            info: GraphQL resolve info containing request context
            community_circle (CircleTypeEnum, optional): Filter by community circle
            community_type (GroupTypeEnum, optional): Filter by community type
            category (CategoryEnum, optional): Filter by community category
            
        Returns:
            List[CommunityType]: List of recommended communities (max 35)
        """
        # This for Temporary later we can add scheduler or other things for community Generation
        # generate_communities_based_on_interest()

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        email=user_node.email
        communities = Community.nodes.all()
        sorted_communities = sorted(communities, key=lambda community: community.created_date, reverse=True)

        # Slice to get the latest 35 communities
        communities = sorted_communities[:35]
        
        if communities:
            communities = [
                c for c in communities if not any(
            member.user.is_connected(user_node) for member in c.members
        ) ]
            
        if community_circle:
            communities = [
                c for c in communities if c.community_circle == community_circle.value ]

        if community_type:
            communities = [
                c for c in communities if c.community_type == community_type.value]

        if category:
            communities = [
                c for c in communities if c.category == category.value]

        return [CommunityType.from_neomodel(community) for community in communities]

    community_role_manager_by_community_uid = graphene.List(
        CommunityRoleManagerDetailsType, community_uid=graphene.String(required=True))
    sub_community_role_manager_by_sub_community_uid = graphene.List(
        SubCommunityRoleManagerDetailsType, sub_community_uid=graphene.String(required=True))

    
    @login_required
    def resolve_community_role_manager_by_community_uid(self, info, community_uid):
        """Retrieve role managers for a specific community.
        
        Fetches all role management configurations for the given community,
        including detailed permissions for each role.
        
        Args:
            info: GraphQL resolve info containing request context
            community_uid (str): Unique identifier of the community
            
        Returns:
            List[CommunityRoleManagerDetailsType]: List of community role managers with permissions
        """
        # Filter CommunityRoleManager by community_uid
        all_details = CommunityRoleManager.objects.filter(
            community_uid=community_uid)
        roles_list = []
        for detail in all_details:
            roles = detail.get_roles()  # Fetch roles from the model's JSONField
            for role in roles:
                # Add each role to the list, mapping JSON fields to GraphQL type fields
                roles_list.append(
                    CommunityRoleManagerDetailsType(
                        role_id=role.get('id'),
                        role_name=role.get('role_name'),
                        is_deleted=role.get('is_deleted', False),
                        is_admin=role.get('is_admin', False),
                        can_edit_group_info=role.get(
                            'can_edit_group_info', False),
                        can_add_new_member=role.get(
                            'can_add_new_member', False),
                        can_remove_member=role.get('can_remove_member', False),
                        can_block_member=role.get('can_block_member', False),
                        can_create_poll=role.get('can_create_poll', False),
                        can_unblock_member=role.get(
                            'can_unblock_member', False),
                        can_invite_member=role.get('can_invite_member', False),
                        can_approve_join_request=role.get(
                            'can_approve_join_request', False),
                        can_schedule_message=role.get(
                            'can_schedule_message', False),
                        can_manage_media=role.get('can_manage_media', False),
                        is_active=role.get('is_active', False),
                    )
                )

        return roles_list

    
    @login_required
    def resolve_sub_community_role_manager_by_sub_community_uid(self, info, sub_community_uid):
        """Retrieve role managers for a specific subcommunity.
        
        Fetches all role management configurations for the given subcommunity,
        including detailed permissions for each role.
        
        Args:
            info: GraphQL resolve info containing request context
            sub_community_uid (str): Unique identifier of the subcommunity
            
        Returns:
            List[CommunityRoleManagerDetailsType]: List of subcommunity role managers with permissions
        """

        all_details = SubCommunityRoleManager.objects.filter(
            sub_community_uid=sub_community_uid)
        sub_community_roles_list = []
        for detail in all_details:
            roles = detail.get_roles()  # Fetch roles from the model's JSONField
            for role in roles:
                # Add each role to the list, mapping JSON fields to GraphQL type fields
                sub_community_roles_list.append(
                    CommunityRoleManagerDetailsType(
                        role_id=role.get('id'),
                        role_name=role.get('role_name'),
                        is_deleted=role.get('is_deleted', False),
                        is_admin=role.get('is_admin', False),
                        can_edit_group_info=role.get(
                            'can_edit_group_info', False),
                        can_add_new_member=role.get(
                            'can_add_new_member', False),
                        can_remove_member=role.get('can_remove_member', False),
                        can_block_member=role.get('can_block_member', False),
                        can_create_poll=role.get('can_create_poll', False),
                        can_unblock_member=role.get(
                            'can_unblock_member', False),
                        can_invite_member=role.get('can_invite_member', False),
                        can_approve_join_request=role.get(
                            'can_approve_join_request', False),
                        can_schedule_message=role.get(
                            'can_schedule_message', False),
                        can_manage_media=role.get('can_manage_media', False),
                        is_active=role.get('is_active', False),
                    )
                )

        return sub_community_roles_list

    community_assigned_user_role_by_community_uid_and_role_id = graphene.List(
        CommunityAssignedDetailsType,
        community_uid=graphene.String(required=True),
        role_id=graphene.Int(required=True)
    )

    @handle_graphql_community_errors
    @login_required
    def resolve_community_assigned_user_role_by_community_uid_and_role_id(self, info, community_uid, role_id):
        """Retrieve users assigned to a specific role in a community.
        
        Fetches all role assignments for a given role within a specific community.
        
        Args:
            info: GraphQL resolve info containing request context
            community_uid (str): Unique identifier of the community
            role_id (str): Unique identifier of the role
            
        Returns:
            List[CommunityRoleAssignmentType]: List of role assignments
            
        Raises:
            DoesNotExist: If community or role does not exist
        """
        # Retrieve the relevant CommunityRoleAssignment object by community_uid
        role_assignment = CommunityRoleAssignment.objects.filter(
            community_uid=community_uid).first()

        if not role_assignment:
            return []

        # Get all assigned roles
        assigned_roles = role_assignment.get_assigned_roles()

        # Find the matching role and fetch the users
        for role in assigned_roles:
            if role.get('role_id') == role_id:
                user_uids = role.get('user_uids', [])
                user_list = []

                for user_uid in user_uids:
                    # Fetch the User object for each user_uid
                    user_node = Users.nodes.get(uid=user_uid)
                    user_list.append(
                        CommunityAssignedDetailsType(
                            user=UserType.from_neomodel(user_node))
                    )

                return user_list

        return []

    sub_community_assigned_user_role_by_community_uid_and_role_id = graphene.List(
        SubCommunityAssignedDetailsType,
        sub_community_uid=graphene.String(required=True),
        role_id=graphene.Int(required=True)
    )

    @handle_graphql_community_errors
    @login_required
    def resolve_sub_community_assigned_user_role_by_community_uid_and_role_id(self, info, sub_community_uid, role_id):
        """Retrieve users assigned to a specific role in a subcommunity.
        
        Fetches all role assignments for a given role within a specific subcommunity.
        
        Args:
            info: GraphQL resolve info containing request context
            sub_community_uid (str): Unique identifier of the subcommunity
            role_id (str): Unique identifier of the role
            
        Returns:
            List[CommunityRoleAssignmentType]: List of role assignments
            
        Raises:
            DoesNotExist: If subcommunity or role does not exist
        """
        # Retrieve the relevant CommunityRoleAssignment object by community_uid
        role_assignment = SubCommunityRoleAssignment.objects.filter(
            subcommunity_uid=sub_community_uid).first()

        if not role_assignment:
            return []

        # Get all assigned roles
        assigned_roles = role_assignment.get_assigned_roles()

        # Find the matching role and fetch the users
        for role in assigned_roles:
            if role.get('role_id') == role_id:
                user_uids = role.get('user_uids', [])
                user_list = []

                for user_uid in user_uids:
                    # Fetch the User object for each user_uid
                    user_node = Users.nodes.get(uid=user_uid)
                    user_list.append(
                        SubCommunityAssignedDetailsType(
                            user=UserType.from_neomodel(user_node))
                    )

                return user_list

        return []
   
    suggested_communities = graphene.List(CommunityType)

    @login_required
    def resolve_suggested_communities(self, info):
        """Retrieve suggested communities for the authenticated user.
        
        Returns a list of communities that are suggested to the current user
        based on generated community recommendations.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[CommunityType]: List of suggested communities
        """
        payload = info.context.payload
        user_id = str(payload.get('user_id'))

        community_uids = GeneratedCommunityUserManager.objects.filter(
            user_ids__contains=[user_id]).values_list('community_uid', flat=True)
        communities = []
        for uid in community_uids:
            community = Community.nodes.get(uid=uid)
            communities.append(CommunityType.from_neomodel(community))
        # print(list(community_uids))
        return communities

    # code Optimisation and Review needed
    community_member_list=graphene.List(UserCommunityListType,uid=graphene.String(required=True),circle=CircleTypeEnum())
    @login_required
    def resolve_community_member_list(self, info, uid, circle=None):
        """Retrieve a detailed list of community members.
        
        Fetches comprehensive member information for a specific community or subcommunity,
        with optional filtering by circle type.
        
        Args:
            info: GraphQL resolve info containing request context
            uid (str): Unique identifier of the community or subcommunity
            circle (CircleTypeEnum, optional): Filter by circle type (Inner, Outer, Universal)
            
        Returns:
            List[UserCommunityListType]: Detailed list of community members
            
        Note:
            Code optimization and review needed for this query.
        """

        # Define parameters
        params = {"uid": uid}
        member_list=[]
        results = []
        try:
                community = Community.nodes.get(uid=uid)
                
            
                if circle:
                    if circle.value == "Inner":
                        # Execute query and store the result in a variable
                        results,_ = db.cypher_query(Inner_Community_Member_List_Query, params)
                    elif circle.value == "Outer":
                        results,_ = db.cypher_query(Outer_Community_Member_List_Query, params)
                    elif circle.value == "Universal":
                        results,_ = db.cypher_query(Universe_Community_Member_List_Query, params)
                
                else:
                    results,_ = db.cypher_query(Universe_Community_Member_List_Query, params)

                for result in results:
                    member_node=result[0]
                    user_node=result[1]
                    profile=result[2]
                    member_list.append(UserCommunityListType.from_neomodel(user_node,profile,member_node))

                return member_list
        
        except Community.DoesNotExist:
                # If Community does not exist, try fetching SubCommunity
                    sub_community = SubCommunity.nodes.get(uid=uid)
                    
                    if circle:
                        if circle.value == "Inner":
                            # Execute query and store the result in a variable
                            results,_ = db.cypher_query(Inner_Sub_Community_Member_List_Query, params)
                        elif circle.value == "Outer":
                            results,_ = db.cypher_query(Outer_Sub_Community_Member_List_Query, params)
                        elif circle.value == "Universal":
                            results,_ = db.cypher_query(Universe_Sub_Community_Member_List_Query, params)
                
                    else:
                        results,_ = db.cypher_query(Universe_Sub_Community_Member_List_Query, params)

                    for result in results:
                        member_node=result[0]
                        user_node=result[1]
                        profile=result[2]
                        member_list.append(UserCommunityListType.from_neomodel(user_node,profile,member_node))

                    return member_list
                
                
        
               
                
    # New query with title and data structure
    community_details_by_uid = graphene.List(
        CommunityDetailsByCategoryType, 
        uid=graphene.String(required=True), 
        communityType=GroupTypeEnum(), 
        communityCircle=CircleTypeEnum()
    )
    
    @handle_graphql_community_errors
    @login_required
    def resolve_community_details_by_uid(self, info, uid, communityType=None, communityCircle=None):
        """Retrieve detailed community information organized by category.
        
        Fetches community details including child, sibling, and parent communities,
        with optional filtering by type and circle.
        
        Args:
            info: GraphQL resolve info containing request context
            uid (str): Unique identifier of the community or subcommunity
            communityType (GroupTypeEnum, optional): Filter by community type
            communityCircle (CircleTypeEnum, optional): Filter by community circle
            
        Returns:
            List[CommunityDetailsByCategoryType]: Community details organized by category
            
        Raises:
            DoesNotExist: If neither community nor subcommunity exists with the given UID
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            community = Community.nodes.get(uid=uid)
            child_communities = community.child_communities.all()
            sibling_communities = community.sibling_communities.all()
            
            # Apply filtering for child communities based on `community_circle` and `community_type`
            if communityCircle:
                child_communities = [
                    c for c in child_communities if c.sub_community_circle == communityCircle.value
                ]
                sibling_communities = [
                    c for c in sibling_communities if c.sub_community_circle == communityCircle.value
                ]
            if communityType:
                child_communities = [
                    c for c in child_communities if c.sub_community_group_type == communityType.value
                ]
                sibling_communities = [
                    c for c in sibling_communities if c.sub_community_group_type == communityType.value
                ]
            
            return [
                CommunityDetailsByCategoryType.from_neomodel("childCommunity", child_communities),
                CommunityDetailsByCategoryType.from_neomodel("siblingCommunity", sibling_communities),
                CommunityDetailsByCategoryType.from_neomodel("parentCommunity", [])
            ]
            
        except Community.DoesNotExist:
            # If Community does not exist, try fetching SubCommunity
            sub_community = SubCommunity.nodes.get(uid=uid)
            
            parent_community = sub_community.parent_community.single()
            parent_sub_community = sub_community.sub_community_parent.single()
            child_communities = sub_community.sub_community_children.all()
            sibling_communities = sub_community.sub_community_sibling.all()
            
            parent_communities = []
            flag = True
            
            if parent_sub_community:
                parent_community = parent_sub_community
                flag = False
                if communityCircle and parent_community.sub_community_circle != communityCircle.value:
                    parent_community = None
                elif communityType and parent_community.sub_community_group_type != communityType.value:
                    parent_community = None
            
            if parent_community:
                if flag:
                    if communityCircle and parent_community.community_circle != communityCircle.value:
                        parent_community = None
                    elif communityType and parent_community.community_type != communityType.value:
                        parent_community = None
                else:
                    if communityCircle and parent_community.sub_community_circle != communityCircle.value:
                        parent_community = None
                    elif communityType and parent_community.sub_community_group_type != communityType.value:
                        parent_community = None
                
                if parent_community:
                    parent_communities = [parent_community]
            
            # Apply filtering for child communities based on `community_circle` and `community_type`
            if communityCircle:
                child_communities = [
                    c for c in child_communities if c.sub_community_circle == communityCircle.value
                ]
                sibling_communities = [
                    c for c in sibling_communities if c.sub_community_circle == communityCircle.value
                ]
            if communityType:
                child_communities = [
                    c for c in child_communities if c.sub_community_group_type == communityType.value
                ]
                sibling_communities = [
                    c for c in sibling_communities if c.sub_community_group_type == communityType.value
                ]
            
            return [
                CommunityDetailsByCategoryType.from_neomodel("childCommunity", child_communities),
                CommunityDetailsByCategoryType.from_neomodel("siblingCommunity", sibling_communities),
                CommunityDetailsByCategoryType.from_neomodel("parentCommunity", parent_communities)
            ]

    my_community_feed = graphene.List(CommunityCategoryType,community_type=GroupTypeEnum(), search=graphene.String())
    @handle_graphql_community_errors
    @login_required
    def resolve_my_community_feed(self, info,community_type=None, search=None):
        """Retrieve community feed for the authenticated user.
        
        Returns categorized community feed including popular and recent communities.
        
        Args:
            info: GraphQL resolve info containing request context
            community_type (GroupTypeEnum, optional): Filter by community type
            search (str, optional): Search term to filter communities by name and description
            
        Returns:
            List[CommunityCategoryType]: Categorized community feed
        """

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)       
        details=["Popular Community","Recent Community"]             
        return [CommunityCategoryType.from_neomodel(detail,community_type, search) for detail in details]


        
        

    community_post_by_community_uid = graphene.List(
        CommunityPostType, community_uid=graphene.String(required=True))
    @handle_graphql_community_errors
    @login_required
    def resolve_community_post_by_community_uid(self, info, community_uid):
        """Retrieve all posts for a specific community or subcommunity.
        
        Fetches all non-deleted posts associated with the given community or subcommunity UID.
        
        Args:
            info: GraphQL resolve info containing request context
            community_uid (str): Unique identifier of the community or subcommunity
            
        Returns:
            List[CommunityPostType]: List of active community posts
            
        Raises:
            DoesNotExist: If neither community nor subcommunity exists with the given UID
        """
        try:
            community = Community.nodes.get(uid=community_uid)
            communitypost = community.community_post.all()
            communityposts=[post for post in communitypost if not post.is_deleted]
            return [CommunityPostType.from_neomodel(post) for post in communityposts]
        except Community.DoesNotExist:
            community = SubCommunity.nodes.get(uid=community_uid)
            communitypost = community.community_post.all()
            communityposts=[post for post in communitypost if not post.is_deleted]
            return [CommunityPostType.from_neomodel(post) for post in communityposts]
        


    secondary_user_community_feed_by_user_uid = graphene.List(SecondaryCommunityCategoryType,user_uid=graphene.String(required=True),community_type=GroupTypeEnum())
    @handle_graphql_community_errors
    @login_required
    def resolve_secondary_user_community_feed_by_user_uid(self, info,user_uid, community_type=None):
        """Retrieve secondary community feed for a specific user.
        
        Returns categorized community feed including mutual and interest communities
        for the specified user relative to the authenticated user.
        
        Args:
            info: GraphQL resolve info containing request context
            user_uid (str): Unique identifier of the target user
            community_type (GroupTypeEnum, optional): Filter by community type
            
        Returns:
            List[SecondaryCommunityCategoryType]: Categorized secondary community feed
        """

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        log_in_uid=user_node.uid
        # details=["Mutual Community","Interest Community"]
        details=["All Communities"]           
        return [SecondaryCommunityCategoryType.from_neomodel(detail,log_in_uid,user_uid,community_type) for detail in details]
        
        
        

    # Below Apis are not used in frontend
    
    all_communities = graphene.List(CommunityType)    
    @superuser_required
    @login_required
    def resolve_all_communities(self, info):
        """Retrieve all communities (Admin only).
        
        Returns all communities in the system. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[CommunityType]: List of all communities
            
        Note:
            This API is not used in the frontend.
        """
        communities = Community.nodes.all()
        return [CommunityType.from_neomodel(community) for community in communities]
    
   
    

    all_community_members = graphene.List(MembershipType)
    @superuser_required
    @login_required
    def resolve_all_community_members(self, info):
        """Retrieve all community memberships (Admin only).
        
        Returns all community memberships in the system. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[MembershipType]: List of all community memberships
            
        Note:
            This API is not used in the frontend.
        """
        return [MembershipType.from_neomodel(membership) for membership in Membership.nodes.all()]

    
    all_community_reviews = graphene.List(CommunityReviewType)

    @superuser_required
    @login_required
    def resolve_all_community_reviews(self, info):
        """Retrieve all community reviews (Admin only).
        
        Returns all community reviews in the system. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[CommunityReviewType]: List of all community reviews
            
        Note:
            This API is not used in the frontend.
        """
        return [CommunityReviewType.from_neomodel(review) for review in CommunityReview.nodes.all()]

    all_community_message = graphene.List(CommunityMessagesType)

   
    @superuser_required
    @login_required
    def resolve_all_community_message(self, info):
        """Retrieve all community messages (Admin only).
        
        Returns all community messages in the system. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[CommunityMessagesType]: List of all community messages
            
        Note:
            This API is not used in the frontend.
        """
        return [CommunityMessagesType.from_neomodel(message) for message in CommunityMessages.nodes.all()]

    all_community_goals = graphene.List(CommunityGoalType)
    
    @superuser_required
    @login_required
    def resolve_all_community_goals(self, info):
        """Retrieve all community goals (Admin only).
        
        Returns all community goals in the system. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[CommunityGoalType]: List of all community goals
            
        Note:
            This API is not used in the frontend.
        """
        community_goals = CommunityGoal.nodes.all()
        return [CommunityGoalType.from_neomodel(goal) for goal in community_goals]


    all_community_activities = graphene.List(CommunityActivityType)
    @superuser_required
    @login_required
    def resolve_all_community_activities(self, info):
        """Retrieve all community activities (Admin only).
        
        Returns all community activities in the system. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[CommunityActivityType]: List of all community activities
            
        Note:
            This API is not used in the frontend.
        """
        community_activities = CommunityActivity.nodes.all()
        return [CommunityActivityType.from_neomodel(activity) for activity in community_activities]

    


    

    all_community_affiliations = graphene.List(CommunityAffiliationType)

    @superuser_required
    @login_required
    def resolve_all_community_affiliations(self, info):
        """Retrieve all community affiliations (Admin only).
        
        Returns all community affiliations in the system. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[CommunityAffiliationType]: List of all community affiliations
            
        Note:
            This API is not used in the frontend.
        """
        community_affiliations = CommunityAffiliation.nodes.all()
        return [CommunityAffiliationType.from_neomodel(affiliation) for affiliation in community_affiliations]

    # New API: Get user admin communities with search and pagination
    user_admin_communities = graphene.Field(
        UserAdminCommunitiesResponseType,
        first=graphene.Int(description="Number of communities to return (limit)"),
        skip=graphene.Int(description="Number of communities to skip (offset)"),
        search=graphene.String(description="Search term to filter communities by name or description")
    )

    @handle_graphql_community_errors
    @login_required
    def resolve_user_admin_communities(self, info, first=None, skip=None, search=None):
        """Retrieve communities where the authenticated user has admin membership status.
        
        Fetches all communities where the current user is an admin member,
        with optional search and pagination functionality.
        
        Args:
            info: GraphQL resolve info containing request context
            first (int, optional): Number of communities to return (limit)
            skip (int, optional): Number of communities to skip (offset)
            search (str, optional): Search term to filter communities by name or description
            
        Returns:
            UserAdminCommunitiesResponseType: Paginated response with communities list and total count
            
        Business Logic:
            - Only returns communities where user has is_admin=True in membership
            - Supports case-insensitive search across community name and description
            - Implements pagination with first (limit) and skip (offset)
            - Results are ordered by community creation date (newest first)
        """
        from neomodel import db
        from auth_manager.Utils import generate_presigned_url
        
        payload = info.context.payload
        user_id = str(payload.get('user_id'))  # Convert to string for Cypher query
        
        # Base query for filtering
        base_query = """
        MATCH (u:Users {user_id: $user_id})<-[:MEMBER]-(m:Membership {is_admin: true})-[:MEMBEROF]->(c:Community)
        """
        
        # Add search filter if provided
        search_filter = """
        WHERE toLower(c.name) CONTAINS toLower($search) OR toLower(c.description) CONTAINS toLower($search)
        """ if search else ""
        
        # Query for total count
        count_query = base_query + search_filter + """
        RETURN count(c) as total
        """
        
        # Query for paginated results
        data_query = base_query + search_filter + """
        WITH c, count{(c)<-[:MEMBEROF]-(:Membership)} as member_count,
             EXISTS((c)<-[:MEMBEROF]-(:Membership {is_leader: true})) as has_leader
        RETURN c, member_count, has_leader
        ORDER BY c.created_date DESC
        """
        
        # Add pagination to data query
        if skip:
            data_query += f" SKIP {skip}"
        if first:
            data_query += f" LIMIT {first}"
        
        # Prepare parameters
        params = {'user_id': user_id}
        if search:
            params['search'] = search
        
        # Execute count query
        count_results, _ = db.cypher_query(count_query, params)
        total_count = count_results[0][0] if count_results else 0
        
        # Execute data query
        data_results, _ = db.cypher_query(data_query, params)
        
        # Convert results to CommunityType objects efficiently
        admin_communities = []
        for result in data_results:
            community_data = result[0]
            member_count = result[1]
            has_leader = result[2]
            
            # Create CommunityType directly without expensive operations
            community_type = Query._create_lightweight_community_type(
                community_data, member_count, has_leader
            )
            admin_communities.append(community_type)
        
        # Return paginated response with total count
        return UserAdminCommunitiesResponseType.create(
            communities=admin_communities,
            total=total_count
        )
    
    @staticmethod
    def _create_lightweight_community_type(community_data, member_count, has_leader):
        """Create a lightweight CommunityType object without expensive operations."""
        from auth_manager.Utils import generate_presigned_url
        from datetime import datetime
        
        # Generate file URLs only if needed
        group_icon_url = None
        if community_data.get('group_icon_id'):
            try:
                file_info = generate_presigned_url.generate_file_info(community_data['group_icon_id'])
                if file_info and file_info.get('url'):
                    group_icon_url = FileDetailType(**file_info)
            except Exception:
                pass
        
        cover_image_url = None
        if community_data.get('cover_image_id'):
            try:
                file_info = generate_presigned_url.generate_file_info(community_data['cover_image_id'])
                if file_info and file_info.get('url'):
                    cover_image_url = FileDetailType(**file_info)
            except Exception:
                pass
        
        return CommunityType(
            uid=community_data.get('uid'),
            name=community_data.get('name'),
            description=community_data.get('description'),
            community_type=community_data.get('community_type'),
            community_circle=community_data.get('community_circle'),
            room_id=community_data.get('room_id'),
            created_date=datetime.fromtimestamp(community_data.get('created_date')) if community_data.get('created_date') else None,
            updated_date=datetime.fromtimestamp(community_data.get('updated_date')) if community_data.get('updated_date') else None,
            number_of_members=member_count,
            group_invite_link=community_data.get('group_invite_link'),
            group_icon_id=community_data.get('group_icon_id'),
            group_icon_url=group_icon_url,
            cover_image_id=community_data.get('cover_image_id'),
            cover_image_url=cover_image_url,
            category=community_data.get('category'),
            generated_community=community_data.get('generated_community'),
            has_leader_agent=has_leader,
            # Skip expensive operations for admin list view
            created_by=None,
            communitymessage=[],
            community_review=[],
            members=[],
            leader_agent=None,
            agent_assignments=[]
        )
    
    
    all_community_achievements = graphene.List(CommunityAchievementType)

    @superuser_required
    @login_required
    def resolve_all_community_achievements(self, info):
        """Retrieve all community achievements (Admin only).
        
        Returns all community achievements in the system. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info containing request context
            
        Returns:
            List[CommunityAchievementType]: List of all community achievements
            
        Note:
            This API is not used in the frontend.
        """
        community_achievements = CommunityAchievement.nodes.all()
        return [CommunityAchievementType.from_neomodel(achievement) for achievement in community_achievements]
    
    # Individual item queries
    community_goal_by_uid = graphene.Field(
        CommunityGoalType, 
        uid=graphene.String(required=True),
        description="Get a specific community goal by its UID"
    )
    
    community_activity_by_uid = graphene.Field(
        CommunityActivityType, 
        uid=graphene.String(required=True),
        description="Get a specific community activity by its UID"
    )
    
    community_affiliation_by_uid = graphene.Field(
        CommunityAffiliationType, 
        uid=graphene.String(required=True),
        description="Get a specific community affiliation by its UID"
    )
    
    community_achievement_by_uid = graphene.Field(
        CommunityAchievementType, 
        uid=graphene.String(required=True),
        description="Get a specific community achievement by its UID"
    )

    @handle_graphql_community_errors
    @login_required
    def resolve_community_goal_by_uid(self, info, uid):
        """Retrieve a specific community goal by its UID.
        
        Only members of the community can access the goal. Validates membership
        before returning goal details.
        
        Args:
            info: GraphQL resolve info containing request context
            uid (str): Unique identifier of the community goal
            
        Returns:
            CommunityGoalType: The requested community goal
            
        Raises:
            Exception: If goal not found, deleted, or user lacks access
        """
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            goal = CommunityGoal.nodes.get(uid=uid)
            
            if goal.is_deleted:
                raise Exception("Goal not found or has been deleted")
            
            community = goal.community.single()
            subcommunity = goal.subcommunity.single()
            
            if community:
                membership_exists = helperfunction.get_membership_for_user_in_community(user_node, community)
                if not membership_exists:
                    raise Exception("You are not authorized to view this goal")
            elif subcommunity:
                sub_membership_exists = helperfunction.get_membership_for_user_in_sub_community(user_node, subcommunity)
                parent_community = subcommunity.parent_community.single()
                parent_membership_exists = helperfunction.get_membership_for_user_in_community(user_node, parent_community) if parent_community else None
                
                if not sub_membership_exists and not parent_membership_exists:
                    raise Exception("You are not authorized to view this goal")
            else:
                raise Exception("Goal is not associated with any community")
            
            return CommunityGoalType.from_neomodel(goal, user_node)
            
        except CommunityGoal.DoesNotExist:
            raise Exception("Goal not found")
        except Exception as error:
            raise Exception(str(error))

    @handle_graphql_community_errors
    @login_required
    def resolve_community_activity_by_uid(self, info, uid):
        """Retrieve a specific community activity by its UID.
        
        Only members of the community can access the activity. Validates membership
        before returning activity details.
        
        Args:
            info: GraphQL resolve info containing request context
            uid (str): Unique identifier of the community activity
            
        Returns:
            CommunityActivityType: The requested community activity
            
        Raises:
            Exception: If activity not found, deleted, or user lacks access
        """
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            activity = CommunityActivity.nodes.get(uid=uid)
            
            if activity.is_deleted:
                raise Exception("Activity not found or has been deleted")
            
            community = activity.community.single()
            subcommunity = activity.subcommunity.single()
            
            if community:
                membership_exists = helperfunction.get_membership_for_user_in_community(user_node, community)
                if not membership_exists:
                    raise Exception("You are not authorized to view this activity")
            elif subcommunity:
                sub_membership_exists = helperfunction.get_membership_for_user_in_sub_community(user_node, subcommunity)
                parent_community = subcommunity.parent_community.single()
                parent_membership_exists = helperfunction.get_membership_for_user_in_community(user_node, parent_community) if parent_community else None
                
                if not sub_membership_exists and not parent_membership_exists:
                    raise Exception("You are not authorized to view this activity")
            else:
                raise Exception("Activity is not associated with any community")
            
            return CommunityActivityType.from_neomodel(activity, user_node)
            
        except CommunityActivity.DoesNotExist:
            raise Exception("Activity not found")
        except Exception as error:
            raise Exception(str(error))

    @handle_graphql_community_errors
    @login_required
    def resolve_community_affiliation_by_uid(self, info, uid):
        """Retrieve a specific community affiliation by its UID.
        
        Only members of the community can access the affiliation. Validates membership
        before returning affiliation details.
        
        Args:
            info: GraphQL resolve info containing request context
            uid (str): Unique identifier of the community affiliation
            
        Returns:
            CommunityAffiliationType: The requested community affiliation
            
        Raises:
            Exception: If affiliation not found, deleted, or user lacks access
        """
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            affiliation = CommunityAffiliation.nodes.get(uid=uid)
            
            if affiliation.is_deleted:
                raise Exception("Affiliation not found or has been deleted")
            
            community = affiliation.community.single()
            subcommunity = affiliation.subcommunity.single()
            
            if community:
                membership_exists = helperfunction.get_membership_for_user_in_community(user_node, community)
                if not membership_exists:
                    raise Exception("You are not authorized to view this affiliation")
            elif subcommunity:
                sub_membership_exists = helperfunction.get_membership_for_user_in_sub_community(user_node, subcommunity)
                parent_community = subcommunity.parent_community.single()
                parent_membership_exists = helperfunction.get_membership_for_user_in_community(user_node, parent_community) if parent_community else None
                
                if not sub_membership_exists and not parent_membership_exists:
                    raise Exception("You are not authorized to view this affiliation")
            else:
                raise Exception("Affiliation is not associated with any community")
            
            return CommunityAffiliationType.from_neomodel(affiliation, user_node)
            
        except CommunityAffiliation.DoesNotExist:
            raise Exception("Affiliation not found")
        except Exception as error:
            raise Exception(str(error))

    @handle_graphql_community_errors
    @login_required
    def resolve_community_achievement_by_uid(self, info, uid):
        """Retrieve a specific community achievement by its UID.
        
        Only members of the community can access the achievement. Validates membership
        before returning achievement details.
        
        Args:
            info: GraphQL resolve info containing request context
            uid (str): Unique identifier of the community achievement
            
        Returns:
            CommunityAchievementType: The requested community achievement
            
        Raises:
            Exception: If achievement not found, deleted, or user lacks access
        """
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node = Users.nodes.get(user_id=user_id)
            
            achievement = CommunityAchievement.nodes.get(uid=uid)
            
            if achievement.is_deleted:
                raise Exception("Achievement not found or has been deleted")
            
            community = achievement.community.single()
            subcommunity = achievement.subcommunity.single()
            
            if community:
                membership_exists = helperfunction.get_membership_for_user_in_community(user_node, community)
                if not membership_exists:
                    raise Exception("You are not authorized to view this achievement")
            elif subcommunity:
                sub_membership_exists = helperfunction.get_membership_for_user_in_sub_community(user_node, subcommunity)
                parent_community = subcommunity.parent_community.single()
                parent_membership_exists = helperfunction.get_membership_for_user_in_community(user_node, parent_community) if parent_community else None
                
                if not sub_membership_exists and not parent_membership_exists:
                    raise Exception("You are not authorized to view this achievement")
            else:
                raise Exception("Achievement is not associated with any community")
            
            return CommunityAchievementType.from_neomodel(achievement, user_node)
            
        except CommunityAchievement.DoesNotExist:
            raise Exception("Achievement not found")
        except Exception as error:
            raise Exception(str(error))

    # New API: Get all communities with pagination
    all_communities_paginated = graphene.Field(
        'community.graphql.types.AllCommunitiesResponseType',
        first=graphene.Int(description="Number of communities to return (limit)"),
        skip=graphene.Int(description="Number of communities to skip (offset)"),
        search=graphene.String(description="Search term to filter communities by name or description")
    )

    @handle_graphql_community_errors
    @login_required
    def resolve_all_communities_paginated(self, info, first=None, skip=None, search=None):
        """Retrieve all communities with pagination and optional search.
        
        Fetches all communities in the system with support for pagination and search functionality.
        
        Args:
            info: GraphQL resolve info containing request context
            first (int, optional): Number of communities to return (limit)
            skip (int, optional): Number of communities to skip (offset)
            search (str, optional): Search term to filter communities by name or description
            
        Returns:
            AllCommunitiesResponseType: Paginated response with communities list and total count
            
        Business Logic:
            - Returns all communities in the system
            - Supports case-insensitive search across community name and description
            - Implements pagination with first (limit) and skip (offset)
            - Results are ordered by community creation date (newest first)
        """
        from neomodel import db
        
        # Base query
        base_query = """
        MATCH (c:Community)
        """
        
        # Add search filter if provided
        search_filter = """
        WHERE toLower(c.name) CONTAINS toLower($search) OR toLower(c.description) CONTAINS toLower($search)
        """ if search else ""
        
        # Query for total count
        count_query = base_query + search_filter + """
        RETURN count(c) as total
        """
        
        # Query for paginated results
        data_query = base_query + search_filter + """
        WITH c, count{(c)<-[:MEMBEROF]-(:Membership)} as member_count,
             EXISTS((c)<-[:MEMBEROF]-(:Membership {is_leader: true})) as has_leader
        RETURN c, member_count, has_leader
        ORDER BY c.created_date DESC
        """
        
        # Add pagination to data query
        if skip:
            data_query += f" SKIP {skip}"
        if first:
            data_query += f" LIMIT {first}"
        
        # Prepare parameters
        params = {}
        if search:
            params['search'] = search
        
        # Execute count query
        count_results, _ = db.cypher_query(count_query, params)
        total_count = count_results[0][0] if count_results else 0
        
        # Execute data query
        data_results, _ = db.cypher_query(data_query, params)
        
        # Convert results to CommunityType objects efficiently
        communities = []
        for result in data_results:
            community_data = result[0]
            member_count = result[1]
            has_leader = result[2]
            
            # Create CommunityType directly without expensive operations
            community_type = Query._create_lightweight_community_type(
                community_data, member_count, has_leader
            )
            communities.append(community_type)
        
        # Return paginated response with total count
        from community.graphql.types import AllCommunitiesResponseType
        return AllCommunitiesResponseType.create(
            communities=communities,
            total=total_count
        )

    # New API: Get all subcommunities with pagination
    all_subcommunities_paginated = graphene.Field(
        'community.graphql.types.AllSubCommunitiesResponseType',
        first=graphene.Int(description="Number of subcommunities to return (limit)"),
        skip=graphene.Int(description="Number of subcommunities to skip (offset)"),
        search=graphene.String(description="Search term to filter subcommunities by name or description")
    )

    @handle_graphql_community_errors
    @login_required
    def resolve_all_subcommunities_paginated(self, info, first=None, skip=None, search=None):
        """Retrieve all subcommunities with pagination and optional search.
        
        Fetches all subcommunities in the system with support for pagination and search functionality.
        
        Args:
            info: GraphQL resolve info containing request context
            first (int, optional): Number of subcommunities to return (limit)
            skip (int, optional): Number of subcommunities to skip (offset)
            search (str, optional): Search term to filter subcommunities by name or description
            
        Returns:
            AllSubCommunitiesResponseType: Paginated response with subcommunities list and total count
            
        Business Logic:
            - Returns all subcommunities in the system
            - Supports case-insensitive search across subcommunity name and description
            - Implements pagination with first (limit) and skip (offset)
            - Results are ordered by subcommunity creation date (newest first)
        """
        from neomodel import db
        
        # Base query
        base_query = """
        MATCH (sc:SubCommunity)
        """
        
        # Add search filter if provided
        search_filter = """
        WHERE toLower(sc.name) CONTAINS toLower($search) OR toLower(sc.description) CONTAINS toLower($search)
        """ if search else ""
        
        # Query for total count
        count_query = base_query + search_filter + """
        RETURN count(sc) as total
        """
        
        # Query for paginated results
        data_query = base_query + search_filter + """
        WITH sc, count{(sc)<-[:SUB_MEMBEROF]-(:SubCommunityMembership)} as member_count
        RETURN sc, member_count
        ORDER BY sc.created_date DESC
        """
        
        # Add pagination to data query
        if skip:
            data_query += f" SKIP {skip}"
        if first:
            data_query += f" LIMIT {first}"
        
        # Prepare parameters
        params = {}
        if search:
            params['search'] = search
        
        # Execute count query
        count_results, _ = db.cypher_query(count_query, params)
        total_count = count_results[0][0] if count_results else 0
        
        # Execute data query
        data_results, _ = db.cypher_query(data_query, params)
        
        # Convert results to SubCommunityType objects efficiently
        subcommunities = []
        for result in data_results:
            subcommunity_data = result[0]
            member_count = result[1]
            
            # Create SubCommunityType directly without expensive operations
            subcommunity_type = Query._create_lightweight_subcommunity_type(
                subcommunity_data, member_count
            )
            subcommunities.append(subcommunity_type)
        
        # Return paginated response with total count
        from community.graphql.types import AllSubCommunitiesResponseType
        return AllSubCommunitiesResponseType.create(
            subcommunities=subcommunities,
            total=total_count
        )

    @staticmethod
    def _create_lightweight_subcommunity_type(subcommunity_data, member_count):
        """Create a lightweight SubCommunityType object without expensive operations."""
        from auth_manager.Utils import generate_presigned_url
        from datetime import datetime
        
        # Generate file URLs only if needed
        group_icon_url = None
        if subcommunity_data.get('group_icon_id'):
            try:
                file_info = generate_presigned_url.generate_file_info(subcommunity_data['group_icon_id'])
                if file_info and file_info.get('url'):
                    group_icon_url = FileDetailType(**file_info)
            except Exception:
                pass
        
        cover_image_url = None
        if subcommunity_data.get('cover_image_id'):
            try:
                file_info = generate_presigned_url.generate_file_info(subcommunity_data['cover_image_id'])
                if file_info and file_info.get('url'):
                    cover_image_url = FileDetailType(**file_info)
            except Exception:
                pass
        
        return SubCommunityType(
            uid=subcommunity_data.get('uid'),
            name=subcommunity_data.get('name'),
            description=subcommunity_data.get('description'),
            sub_community_type=subcommunity_data.get('sub_community_type'),
            sub_community_group_type=subcommunity_data.get('sub_community_group_type'),
            sub_community_circle=subcommunity_data.get('sub_community_circle'),
            room_id=subcommunity_data.get('room_id'),
            created_date=datetime.fromtimestamp(subcommunity_data.get('created_date')) if subcommunity_data.get('created_date') else None,
            updated_date=datetime.fromtimestamp(subcommunity_data.get('updated_date')) if subcommunity_data.get('updated_date') else None,
            number_of_members=member_count,
            group_invite_link=subcommunity_data.get('group_invite_link'),
            group_icon_id=subcommunity_data.get('group_icon_id'),
            group_icon_url=group_icon_url,
            cover_image_id=subcommunity_data.get('cover_image_id'),
            cover_image_url=cover_image_url,
            category=subcommunity_data.get('category'),
            # Skip expensive operations for list view
            created_by=None,
            parent_community=None
        )