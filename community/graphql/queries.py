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
    class Meta:
        model = SubCommunityRoleManager


class CommunityRoleManagerType(DjangoObjectType):
    class Meta:
        model = CommunityRoleManager


class CommunityRoleAssignmentType(DjangoObjectType):
    class Meta:
        model = CommunityRoleAssignment


class Query(graphene.ObjectType):
    
    
    community_messages = graphene.List(
        CommunityMessagesType, community_id=graphene.String(required=True))
    
    community_byuid = graphene.Field(
        CommunityDetailsType, uid=graphene.String(required=True))
    # code Review and optimisation needed
    @handle_graphql_community_errors
    @login_required
    def resolve_community_byuid(self, info, uid):
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
        community = Community.nodes.get(uid=community_uid)
        communitymember = list(community.members.all())
        return [MembershipType.from_neomodel(member) for member in communitymember]

    
    sub_community_members_by_sub_community_uid = graphene.List(
        SubCommunityMembershipType, sub_community_uid=graphene.String(required=True))   
    @handle_graphql_community_errors
    @login_required
    def resolve_sub_community_members_by_sub_community_uid(self, info, sub_community_uid):
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

        

    # admin(person who created the community) can see all members of a community
    my_community_member = graphene.List(MembershipType)
    @handle_graphql_community_errors
    @login_required
    def resolve_my_community_member(self, info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        my_communities = user_node.community.all()
        community_member = []
        for member in my_communities:
            community_member.extend(list(member.members))
        return [MembershipType.from_neomodel(x) for x in community_member]
        

    # user can see all communities he is member of
    # optimisation and review needed
    user_community_membership = graphene.List(
        CommunityInfoType, community_type=GroupTypeEnum(), community_circle=CircleTypeEnum())
    @handle_graphql_community_errors
    @login_required
    def resolve_user_community_membership(self, info, community_type=None, community_circle=None):
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


    # user can see whether he is member of particular community or not
    communitymembership_details_by_community_uid = graphene.List(
        MembershipType, community_uid=graphene.String(required=True))
    
    @handle_graphql_community_errors
    @login_required
    def resolve_communitymembership_details_by_community_uid(self, info, community_uid):
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

    
    @login_required
    def resolve_community_assigned_user_role_by_community_uid_and_role_id(self, info, community_uid, role_id):
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

    
    @login_required
    def resolve_sub_community_assigned_user_role_by_community_uid_and_role_id(self, info, sub_community_uid, role_id):
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

    my_community_feed = graphene.List(CommunityCategoryType,community_type=GroupTypeEnum())
    @handle_graphql_community_errors
    @login_required
    def resolve_my_community_feed(self, info,community_type=None):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)       
        details=["Popular Community","Recent Community"]             
        return [CommunityCategoryType.from_neomodel(detail,community_type) for detail in details]


        
        

    community_post_by_community_uid = graphene.List(
        CommunityPostType, community_uid=graphene.String(required=True))
    @handle_graphql_community_errors
    @login_required
    def resolve_community_post_by_community_uid(self, info, community_uid):
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

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        log_in_uid=user_node.uid
        details=["Mutual Community","Interest Community"]           
        return [SecondaryCommunityCategoryType.from_neomodel(detail,log_in_uid,user_uid,community_type) for detail in details]
        
        
        

    # Below Apis are not used in frontend
    
    all_communities = graphene.List(CommunityType)    
    @superuser_required
    @login_required
    def resolve_all_communities(self, info):
        communities = Community.nodes.all()
        return [CommunityType.from_neomodel(community) for community in communities]
    
   
    

    all_community_members = graphene.List(MembershipType)
    @superuser_required
    @login_required
    def resolve_all_community_members(self, info):
        return [MembershipType.from_neomodel(membership) for membership in Membership.nodes.all()]

    
    all_community_reviews = graphene.List(CommunityReviewType)

    @superuser_required
    @login_required
    def resolve_all_community_reviews(self, info):
        return [CommunityReviewType.from_neomodel(review) for review in CommunityReview.nodes.all()]

    all_community_message = graphene.List(CommunityMessagesType)

   
    @superuser_required
    @login_required
    def resolve_all_community_message(self, info):
        return [CommunityMessagesType.from_neomodel(message) for message in CommunityMessages.nodes.all()]

    all_community_goals = graphene.List(CommunityGoalType)
    
    @superuser_required
    @login_required
    def resolve_all_community_goals(self, info):
        community_goals = CommunityGoal.nodes.all()
        return [CommunityGoalType.from_neomodel(goal) for goal in community_goals]


    all_community_activities = graphene.List(CommunityActivityType)
    @superuser_required
    @login_required
    def resolve_all_community_activities(self, info):
        community_activities = CommunityActivity.nodes.all()
        return [CommunityActivityType.from_neomodel(activity) for activity in community_activities]

    


    

    all_community_affiliations = graphene.List(CommunityAffiliationType)

    @superuser_required
    @login_required
    def resolve_all_community_affiliations(self, info):
        community_affiliations = CommunityAffiliation.nodes.all()
        return [CommunityAffiliationType.from_neomodel(affiliation) for affiliation in community_affiliations]
    
    
    all_community_achievements = graphene.List(CommunityAchievementType)

    @superuser_required
    @login_required
    def resolve_all_community_achievements(self, info):
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
        """
        Retrieve a specific community goal by its UID.
        Only members of the community can access the goal.
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
        """
        Retrieve a specific community activity by its UID.
        Only members of the community can access the activity.
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
        """
        Retrieve a specific community affiliation by its UID.
        Only members of the community can access the affiliation.
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
        """
        Retrieve a specific community achievement by its UID.
        Only members of the community can access the achievement.
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