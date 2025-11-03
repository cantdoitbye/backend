from neomodel import db
from graphql import GraphQLError
from auth_manager.models import Users
from community.models import Community



def is_community_created_by_admin(user_id, community_uid):
    try:
        user = Users.nodes.get(user_id=user_id)

        # Check if the user has a CREATED_BY relationship with the community
        for created_community in user.community.all():
            if created_community.uid == community_uid:
                return True

        return False
    except Exception as e:
        # Handle any exceptions that may occur
        raise Exception(f"Error checking community ownership: {str(e)}")
    

def get_membership_for_user_in_community(user_node, community_node):
    """
    Check if a user is a member of a community and return the membership if it exists.

    :param user_node: The user node to check.
    :param community_node: The community node to check.
    :return: The membership node if it exists, else None.
    """
    for membership in community_node.members.all():
        if membership.user.is_connected(user_node):
            return membership
    return None


def get_membership_for_user_in_sub_community(user_node, sub_community_node):
    """
    Check if a user is a member of a community and return the membership if it exists.

    :param user_node: The user node to check.
    :param community_node: The community node to check.
    :return: The membership node if it exists, else None.
    """
    for membership in sub_community_node.sub_community_members.all():
        if membership.user.is_connected(user_node):
            return membership
    return None


def get_community_members(community_or_subcommunity):
    """
    Get members from either Community or SubCommunity instances.
    
    This helper abstracts the difference in member relationship names
    between Community (uses 'members') and SubCommunity (uses 'sub_community_members').
    
    :param community_or_subcommunity: Community or SubCommunity instance
    :return: QuerySet of membership objects (Membership or SubCommunityMembership)
    :raises TypeError: If the input is neither Community nor SubCommunity
    """
    from community.models import SubCommunity
    
    if isinstance(community_or_subcommunity, Community):
        return community_or_subcommunity.members.all()
    elif isinstance(community_or_subcommunity, SubCommunity):
        return community_or_subcommunity.sub_community_members.all()
    else:
        raise TypeError(f"Expected Community or SubCommunity, got {type(community_or_subcommunity)}")
