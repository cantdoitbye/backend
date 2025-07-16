from community.models import Community, SubCommunity
from community.graphql.messages import CommMessages



def validate_community_admin(user, community_uid, helper_function):
    """
    Validates if a user is an admin of a community or sub-community.

    Args:
        user (Users): The user object to validate.
        community_uid (str): The unique ID of the community or sub-community.
        helper_function (object): An object containing helper methods.

    Returns:
        Tuple[bool, object, str]: 
            - bool: Indicates success of validation.
            - object: The community or sub-community node.
            - str: An error message or None if validation is successful.
    """

    try:
        community = Community.nodes.get(uid=community_uid)
        member_node = helper_function.get_membership_for_user_in_community(user, community)
        if member_node is None:
            return False, None, CommMessages.NOT_A_MEMBER_OF_COMMUNITY
        if not member_node.is_admin:
            return False, None, CommMessages.NOT_AN_ADMIN
        return True, community, None
    except Community.DoesNotExist:
        try:
            sub_community = SubCommunity.nodes.get(uid=community_uid)
            member_node = helper_function.get_membership_for_user_in_sub_community(user, sub_community)
            if member_node is None:
                return False, None, CommMessages.NOT_A_MEMBER_OF_COMMUNITY
            if not member_node.is_admin:
                return False, None, CommMessages.NOT_AN_ADMIN
            return True, sub_community, None
        except SubCommunity.DoesNotExist:
            return False, None, CommMessages.COMMUNITY_NOT_FOUND