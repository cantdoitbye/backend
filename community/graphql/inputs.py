import graphene
from .enums.circle_type_enum import CircleTypeEnum
from.enums.group_type_enum import GroupTypeEnum
from.enums.sub_community_type_enum import SubCommunityTypeEnum
from auth_manager.validators import custom_graphql_validator


class CreateCommunityInput(graphene.InputObjectType):
    # wiil update after discussion
    name = custom_graphql_validator.NonSpecialCharacterString5_100.add_option("name", "CreateCommunity")(required=True)
    description = custom_graphql_validator.NonSpecialCharacterString10_200.add_option("description", "CreateCommunity")()
    community_type =GroupTypeEnum(required=True)
    community_circle = CircleTypeEnum(required=True)
    category = custom_graphql_validator.String.add_option("category", "CreateCommunity")()
    group_icon_id=custom_graphql_validator.String.add_option("groupIconId", "CreateCommunity")()
    cover_image_id=custom_graphql_validator.String.add_option("coverImageId", "CreateCommunity")()
    member_uid=custom_graphql_validator.ListString.add_option("memberUid", "CreateCommunity")()
    ai_generated = custom_graphql_validator.Boolean.add_option("aiGenerated", "CreateCommunity")(default_value=False, description="Indicates if this community is AI-generated")
    tags = graphene.List(graphene.String, description="List of tags/keywords for community search and categorization")
    mentioned_user_uids = graphene.List(graphene.String)

class UpdateCommunityInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateCommunity")(required=True)
    name = custom_graphql_validator.NonSpecialCharacterString5_100.add_option("name", "UpdateCommunity")()
    description = custom_graphql_validator.NonSpecialCharacterString10_200.add_option("description", "UpdateCommunity")()
    community_type = custom_graphql_validator.String.add_option("communityType", "UpdateCommunity")()
    community_circle = custom_graphql_validator.String.add_option("communityCircle", "UpdateCommunity")()
    category = custom_graphql_validator.String.add_option("category", "UpdateCommunity")()
    group_icon_id=custom_graphql_validator.String.add_option("groupIconId", "UpdateCommunity")()
    cover_image_id=custom_graphql_validator.String.add_option("coverImageId", "UpdateCommunity")()
    mentioned_user_uids = graphene.List(graphene.String)
    
class UpdateSubCommunityInput(graphene.InputObjectType):
    uid = graphene.String(required=True)
    name = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("name", "UpdateSubCommunity")( desc="The name of the sub-community.")
    description = custom_graphql_validator.NonSpecialCharacterString5_200.add_option("description", "UpdateSubCommunity")(desc="The description of the sub-community.")
    sub_community_type = custom_graphql_validator.String.add_option("subCommunityType", "UpdateSubCommunity")( desc="The type of the sub-community.")
    sub_community_group_type = custom_graphql_validator.String.add_option("subCommunityGroupType", "UpdateSubCommunity")( desc="The group type designation of the sub-community.")
    sub_community_circle = CircleTypeEnum( desc="The circle type designation of the sub-community.")
    category = custom_graphql_validator.String.add_option("category", "UpdateSubCommunity")(desc="The category under which the sub-community falls.")
    group_icon_id=graphene.String()
    cover_image_id=graphene.String()


class DeleteInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "Delete")(required=True)

class LeaveCommunityChatInput(graphene.InputObjectType):
    """Input for leaving a community's Matrix chat room"""
    room_id = custom_graphql_validator.String.add_option("roomId", "LeaveCommunityChat")(required=True, description="Matrix room ID to leave")

class CreateCommMessageInput(graphene.InputObjectType):
    community_uid = custom_graphql_validator.String.add_option("communityUid", "createCommMessage")(required=True)
    content = custom_graphql_validator.String.add_option("content", "createCommMessage")()
    file_id = custom_graphql_validator.String.add_option("fileId", "createCommMessage")()
    title = custom_graphql_validator.String.add_option("title", "createCommMessage")()

class UpdateCommMessageInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateCommMessage")(required=True)
    content = custom_graphql_validator.String.add_option("content", "UpdateCommMessage")()
    file_id = custom_graphql_validator.String.add_option("fileId", "UpdateCommMessage")()
    title = custom_graphql_validator.String.add_option("title", "UpdateCommMessage")()
    is_read = custom_graphql_validator.Boolean.add_option("isRead", "UpdateCommMessage")(default=False)
    is_deleted = custom_graphql_validator.Boolean.add_option("isDeleted" ,"UpdateCommMessage")(default=False)
    is_public = custom_graphql_validator.Boolean.add_option("isPublic", "UpdateCommMessage")(default=True)

class AddMemberInput(graphene.InputObjectType):
    community_uid = custom_graphql_validator.String.add_option("communityUid", "AddMember")(required=True)
    user_uid = graphene.List(custom_graphql_validator.String.add_option("userUid", "AddMember"))

class CreateCommunityReviewInput(graphene.InputObjectType):
    title = custom_graphql_validator.NonSpecialCharacterString5_100.add_option("title", "CreateCommunityReview")()
    content = custom_graphql_validator.NonSpecialCharacterString5_100.add_option("content", "CreateCommunityReview")()
    file_id = custom_graphql_validator.String.add_option("fileId", "CreateCommunityReview")()
    reaction = custom_graphql_validator.String.add_option("reaction", "CreateCommunityReview")(default_value='Like')
    vibe = custom_graphql_validator.Float.add_option("vibe", "CreateCommunityReview")(default_value=2.0)
    to_community_uid = custom_graphql_validator.String.add_option("toCommunityUid", "CreateCommunityReview")(required=True)

class UpdateCommunityReviewInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateCommunityReview")(required=True)
    title = custom_graphql_validator.String.add_option("title", "UpdateCommunityReview")()
    content = custom_graphql_validator.String.add_option("content", "UpdateCommunityReview")()
    file_id = custom_graphql_validator.String.add_option("fileId", "UpdateCommunityReview")()
    reaction = custom_graphql_validator.String.add_option("reaction", "UpdateCommunityReview")()
    vibe = custom_graphql_validator.Float.add_option("vibe", "UpdateCommunityReview")()
   
class UpdateCommunityInfoInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateCommunityInfo")(required=True)
    name = custom_graphql_validator.String.add_option("name", "UpdateCommunityInfo")()
    description = custom_graphql_validator.String.add_option("description", "UpdateCommunityInfo")()
    group_icon_id = custom_graphql_validator.String.add_option("groupIconId", "UpdateCommunityInfo")()

class CreateCommunityGoalInput(graphene.InputObjectType):
    name = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("name", "CreateCommunityGoal")(required=True, desc="The name of the community goal.")
    description = custom_graphql_validator.NonSpecialCharacterString5_200.add_option("description", "CreateCommunityGoal")(required=True, desc="The description of the community goal.")
    file_id=graphene.List(graphene.String,desc="The new file ID associated with the community goal.")
    community_uid = custom_graphql_validator.String.add_option("communityUid", "CreateCommunityGoal")(required=True, desc="The unique identifier of the community to which the goal belongs.")
    community_type=custom_graphql_validator.String.add_option("communityType", "CreateCommunityGoal")()

class UpdateCommunityGoalInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateCommunityGoal")(required=True, desc="The unique identifier of the community goal to be updated.")
    name = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("name", "UpdateCommunityGoal")(desc="The new name for the community goal.")
    description = custom_graphql_validator.NonSpecialCharacterString5_200.add_option("description", "UpdateCommunityGoal")(desc="The new description for the community goal.")
    file_id=graphene.List(graphene.String,desc="The new file ID associated with the community goal.")
    is_deleted = custom_graphql_validator.Boolean.add_option("isDeleted", "UpdateCommunityGoal")(desc="Whether the community goal should be marked as deleted or not.")

class CreateCommunityActivityInput(graphene.InputObjectType):
    name = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("name", "CreateCommunityActivity")(required=True, desc="The name of the community activity.")
    description = custom_graphql_validator.NonSpecialCharacterString5_200.add_option("description", "CreateCommunityActivity")( desc="The description of the community activity.")
    file_id=graphene.List(graphene.String,desc="The new file ID associated with the community activity.")
    community_uid = custom_graphql_validator.String.add_option("communityUid", "CreateCommunityActivity")(required=True, desc="The unique identifier of the community to which the activity belongs.")
    community_type=custom_graphql_validator.String.add_option("communityType", "CreateCommunityActivity")()
    date = custom_graphql_validator.DateTimeScalar.add_option("date", "CreateCommunityActivity")( desc="The start date and time of the community activity.")
    activity_type = custom_graphql_validator.String.add_option("activityType", "CreateCommunityActivity")( desc="The type of the community activity.")

class UpdateCommunityActivityInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateCommunityActivity")(required=True, desc="The unique identifier of the community activity to be updated.")
    name = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("name", "UpdateCommunityActivity")(desc="The new name for the community activity.")
    description = custom_graphql_validator.NonSpecialCharacterString5_200.add_option("description", "UpdateCommunityActivity")(desc="The new description for the community activity.")
    file_id=graphene.List(graphene.String,desc="The new file ID associated with the community activity.")
    date = custom_graphql_validator.DateTimeScalar.add_option("date", "UpdateCommunityActivity")(desc="The new start date and time of the community activity.")
    activity_type = custom_graphql_validator.String.add_option("activityType", "UpdateCommunityActivity")(desc="The new type of the community activity.")
    is_deleted = custom_graphql_validator.Boolean.add_option("isDeleted", "UpdateCommunityActivity")(desc="Whether the community activity should be marked as deleted or not.")

class CreateCommunityAffiliationInput(graphene.InputObjectType):
    entity = custom_graphql_validator.NonSemiSpecialCharacterString2_100.add_option("entity", "CreateCommunityAffiliation")(required=True, desc="The name of the entity associated with the community.")
    subject= custom_graphql_validator.NonSpecialCharacterString5_100.add_option("subject", "CreateCommunityAffiliation")(required=True, desc="The subject or topic of the affiliation.")
    date= custom_graphql_validator.DateTimeScalar.add_option("date", "CreateCommunityAffiliation")(required=True, desc="The date of the affiliation.")
    community_uid = custom_graphql_validator.String.add_option("communityUid","CreateCommunityAffiliation" )(required=True, desc="The unique identifier of the community to which the affiliation belongs.")
    community_type=GroupTypeEnum(required=True, desc="The type of community for the affiliation.")
    file_id=graphene.List(graphene.String,desc="The new file ID associated with the community affiliation.")

class UpdateCommunityAffiliationInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateCommunityAffiliation")(required=True, desc="The unique identifier of the community affiliation to be updated.")
    entity = custom_graphql_validator.NonSemiSpecialCharacterString2_100.add_option("entity", "UpdateCommunityAffiliation")(desc="The new name of the entity associated with the community.")
    subject= custom_graphql_validator.NonSpecialCharacterString5_100.add_option("subject", "UpdateCommunityAffiliation")(desc="The new subject or topic of the affiliation.")
    date= custom_graphql_validator.DateTimeScalar.add_option("date", "UpdateCommunityAffiliation")(desc="The new date of the affiliation.")
    community_type=GroupTypeEnum(desc="The new type of community for the affiliation.")
    file_id=graphene.List(graphene.String,desc="The new file ID associated with the community affiliation.")
    is_deleted = custom_graphql_validator.Boolean.add_option("isDeleted", "UpdateCommunityAffiliation")(desc="Whether the community affiliation should be marked as deleted or not.")

class CreateCommunityAchievementInput(graphene.InputObjectType):
    entity = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("entity", "CreateCommunityAchievement")(required=True, desc="The name of the entity associated with the community.")
    subject= custom_graphql_validator.NonSpecialCharacterString5_100.add_option("subject", "CreateCommunityAchievement")(required=True, desc="The subject or topic of the achievement.")
    date= custom_graphql_validator.DateTimeScalar.add_option("date", "CreateCommunityAchievement")(desc="The date of the achievement.")
    community_uid = custom_graphql_validator.String.add_option("communityUid", "CreateCommunityAchievement")(required=True, desc="The unique identifier of the community to which the affiliation belongs.")
    community_type=custom_graphql_validator.String.add_option("communityType", "CreateCommunityAchievement")()
    file_id=custom_graphql_validator.ListString.add_option("fileId", "CreateCommunityAchievement")(desc="The new file ID associated with the community achievement.")

class UpdateCommunityAchievementInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateCommunityAchievement")(required=True, desc="The unique identifier of the community achievement to be updated.")
    entity = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("entity", "UpdateCommunityAchievement")(desc="The new name of the entity associated with the community.")
    subject= custom_graphql_validator.NonSpecialCharacterString5_100.add_option("subject", "UpdateCommunityAchievement")(desc="The new subject or topic of the achievement.")
    date= custom_graphql_validator.DateTimeScalar.add_option("date", "UpdateCommunityAchievement")(desc="The new date of the achievement.")
    is_deleted = custom_graphql_validator.Boolean.add_option("isDeleted", "UpdateCommunityAchievement")(desc="Whether the community achievement should be marked as deleted or not.")
    file_id=graphene.List(graphene.String,desc="The new file ID associated with the community achievement.")


class MuteCommunityNoficationInput(graphene.InputObjectType):
    community_uid = custom_graphql_validator.String.add_option("communityUid", "MuteCommunityNofication")(required=True, desc="The unique identifier of the community to which the notification belongs.")

class UnMuteCommunityNoficationInput(graphene.InputObjectType):
    community_uid = custom_graphql_validator.String.add_option("communityUid", "UnMuteCommunityNofication")(required=True, desc="The unique identifier of the community to which the notification belongs.")


class CreateManageRoleInput(graphene.InputObjectType):
    community_uid = custom_graphql_validator.String.add_option("communityUid", "CreateManageRole")(required=True, desc="The unique identifier of the community.")
    role_name = custom_graphql_validator.String.add_option("roleName", "CreateManageRole")(required=True, desc="The name of the role within the community.")
    is_admin = custom_graphql_validator.Boolean.add_option("isAdmin", "CreateManageRole")(desc="Indicates if the role has admin privileges.")
    can_edit_group_info = custom_graphql_validator.Boolean.add_option("canEditGroupInfo", "CreateManageRole")(desc="Permission to edit group information.")
    can_add_new_member = custom_graphql_validator.Boolean.add_option("canAddNewMember", "CreateManageRole")(desc="Permission to add new members to the community.")
    can_remove_member = custom_graphql_validator.Boolean.add_option("canRemoveMember", "CreateManageRole")(desc="Permission to remove members from the community.")
    can_block_member = custom_graphql_validator.Boolean.add_option("canBlockMember", "CreateManageRole")(desc="Permission to block members within the community.")
    can_create_poll = custom_graphql_validator.Boolean.add_option("canCreatePoll", "CreateManageRole")(desc="Permission to create polls in the community.")
    can_unblock_member = custom_graphql_validator.Boolean.add_option("canUnblockMember", "CreateManageRole")(desc="Permission to unblock previously blocked members.")
    can_invite_member = custom_graphql_validator.Boolean.add_option("canInviteMember", "CreateManageRole")(desc="Permission to invite new members to join the community.")
    can_approve_join_request = custom_graphql_validator.Boolean.add_option("canApproveJoinRequest", "CreateManageRole")(desc="Permission to approve new member join requests.")
    can_schedule_message = custom_graphql_validator.Boolean.add_option("canScheduleMessage", "CreateManageRole")(desc="Permission to schedule messages.")
    can_manage_media = custom_graphql_validator.Boolean.add_option("canManageMedia", "CreateManageRole")(desc="Permission to manage media files within the community.")
    is_active = custom_graphql_validator.Boolean.add_option("isActive", "CreateManageRole")(desc="Indicates if the role is currently active.")
    is_deleted=custom_graphql_validator.Boolean.add_option("isDeleted", "CreateManageRole")(desc="Permission to manage media files within the community.")

class UpdateCommunityGroupInfoInput(graphene.InputObjectType):
    community_uid = custom_graphql_validator.String.add_option("communityUid", "UpdateCommunityGroupInfo")(required=True, desc="The unique identifier of the community.")
    name = custom_graphql_validator.String.add_option("name", "UpdateCommunityGroupInfo")(desc="The new name for the community.")
    description = custom_graphql_validator.String.add_option("description", "UpdateCommunityGroupInfo")(desc="The new description of the community.")
    group_icon_id = custom_graphql_validator.String.add_option("groupIconId", "UpdateCommunityGroupInfo")(desc="The ID of the new group icon for the community.")


class CreateSubCommunityInput(graphene.InputObjectType):
    parent_community_uid = custom_graphql_validator.String.add_option("parentCommunityUid", "CreateSubCommunity")(required=True, desc="The unique identifier of the parent community.")
    name = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("name", "CreateSubCommunity")(required=True, desc="The name of the sub-community.")
    description = custom_graphql_validator.NonSpecialCharacterString5_200.add_option("description", "CreateSubCommunity")(required=True, desc="The description of the sub-community.")
    sub_community_type = SubCommunityTypeEnum(required=True, desc="The type of the sub-community.")
    sub_community_group_type = GroupTypeEnum(required=True, desc="The group type designation of the sub-community.")
    sub_community_circle = CircleTypeEnum(required=True, desc="The circle type designation of the sub-community.")
    category = custom_graphql_validator.String.add_option("category", "CreateSubCommunity")(desc="The category under which the sub-community falls.")
    group_icon_id = custom_graphql_validator.String.add_option("groupIconId", "CreateSubCommunity")(desc="The ID of the group icon for the sub-community.")
    cover_image_id=custom_graphql_validator.String.add_option("coverImageId", "CreateSubCommunity")(desc="The ID of the cover image for the sub-community.")
    member_uid = graphene.List(graphene.String, desc="A list of member unique identifiers.")    


class CreateManageSubCommunityRoleInput(graphene.InputObjectType):
    sub_community_uid = custom_graphql_validator.String.add_option("subCommunityUid", "CreateManageSubCommunityRole")(required=True, desc="The unique identifier of the sub-community.")
    role_name = custom_graphql_validator.String.add_option("roleName", "CreateManageSubCommunityRole")(required=True, desc="The name of the role within the sub-community.")
    is_admin = custom_graphql_validator.Boolean.add_option("isAdmin", "CreateManageSubCommunityRole")(desc="Indicates if the role has admin privileges within the sub-community.")
    can_edit_group_info = custom_graphql_validator.Boolean.add_option("canEditGroupInfo", "CreateManageSubCommunityRole")(desc="Permission to edit sub-community group information.")
    can_add_new_member = custom_graphql_validator.Boolean.add_option("canAddNewMember", "CreateManageSubCommunityRole")(desc="Permission to add new members to the sub-community.")
    can_remove_member = custom_graphql_validator.Boolean.add_option("canRemoveMember", "CreateManageSubCommunityRole")(desc="Permission to remove members from the sub-community.")
    can_block_member = custom_graphql_validator.Boolean.add_option("canBlockMember", "CreateManageSubCommunityRole")(desc="Permission to block members within the sub-community.")
    can_create_poll = custom_graphql_validator.Boolean.add_option("canCreatePoll", "CreateManageSubCommunityRole")(desc="Permission to create polls in the sub-community.")
    can_unblock_member = custom_graphql_validator.Boolean.add_option("canUnblockMember", "CreateManageSubCommunityRole")(desc="Permission to unblock members in the sub-community.")
    can_invite_member = custom_graphql_validator.Boolean.add_option("canInviteMember", "CreateManageSubCommunityRole")(desc="Permission to invite new members to join the sub-community.")
    can_approve_join_request = custom_graphql_validator.Boolean.add_option("canApproveJoinRequest", "CreateManageSubCommunityRole")(desc="Permission to approve new member join requests in the sub-community.")
    can_schedule_message = custom_graphql_validator.Boolean.add_option("canScheduleMessage", "CreateManageSubCommunityRole")(desc="Permission to schedule messages in the sub-community.")
    can_manage_media = custom_graphql_validator.Boolean.add_option("canManageMedia", "CreateManageSubCommunityRole")(desc="Permission to manage media files within the sub-community.")
    is_deleted=custom_graphql_validator.Boolean.add_option("isDeleted", "CreateManageSubCommunityRole")(desc="Permission to manage media files within the sub-community.")
    is_active = custom_graphql_validator.Boolean.add_option("isActive", "CreateManageSubCommunityRole")(desc="Indicates if the role is currently active.")






class CreateAssignSubCommunityRoleInput(graphene.InputObjectType):
    role_id = custom_graphql_validator.Int.add_option("roleId", "CreateAssignSubCommunityRole")(required=True, description="ID of the role to be assigned")
    assigned_to = custom_graphql_validator.String.add_option("assignedTo", "CreateAssignSubCommunityRole")(required=True)


class AssignRoleInput(graphene.InputObjectType):
    user_uids = graphene.List(graphene.String, required=True)
    role_id = custom_graphql_validator.Int.add_option("roleId", "AssignRole")(required=True)
    community_uid = custom_graphql_validator.String.add_option("communityUid", "AssignRole")(required=True)
    # user_uids = custom_graphql_validator.String.add_option("userUids", "AssignRole")(required=True)

class AssignSubCommunityRoleInput(graphene.InputObjectType):
    role_id = custom_graphql_validator.Int.add_option("roleId", "AssignSubCommunityRole")(required=True)
    sub_community_uid = custom_graphql_validator.String.add_option("subCommunityUid", "AssignSubCommunityRole")(required=True)
    # user_uids = custom_graphql_validator.String.add_option("userUids", "AssignSubCommunityRole")(required=True)
    user_uids = graphene.List(graphene.String, required=True)

class AddSubCommunityMemberInput(graphene.InputObjectType):
    sub_community_uid = custom_graphql_validator.String.add_option("subCommunityUid", "AddSubCommunityMember")(required=True)
    # user_uid = custom_graphql_validator.String.add_option("userUid", "AddSubCommunityMember")()
    user_uid = graphene.List(graphene.String)

class CommunityPermissionInput(graphene.InputObjectType):
    community_uid = custom_graphql_validator.String.add_option("communityUid", "CommunityPermission")(required=True, desc="The unique identifier of the community.")
    only_admin_can_message=custom_graphql_validator.Boolean.add_option("onlyAdminCanMessage", "CommunityPermission")(desc="Permission to manage media files within the community.")
    only_admin_can_add_member=custom_graphql_validator.Boolean.add_option("onlyAdminCanAddMember", "CommunityPermission")(desc="Permission to manage media files within the community.")
    only_admin_can_remove_member=custom_graphql_validator.Boolean.add_option("onlyAdminCanRemoveMember", "CommunityPermission")(desc="Permission to manage media files within the community.")


class CreateCommunityPostInput(graphene.InputObjectType):
    community_uid=custom_graphql_validator.String.add_option("communityUid", "CreateCommunityPost")(required=True, desc="The unique identifier of the community.")
    post_title = custom_graphql_validator.SpecialCharacterString2_100.add_option("postTitle", "CreateCommunityPost")(required=True, desc="The title of the post.")
    post_text = custom_graphql_validator.SpecialCharacterString2_200.add_option("postText", "CreateCommunityPost")(required=True, desc="The text content of the post.")
    post_type = custom_graphql_validator.String.add_option("postType", "CreateCommunityPost")(desc="The type of the post.")
    privacy = custom_graphql_validator.String.add_option("privacy", "CreateCommunityPost")(desc="The privacy setting of the post.")
    post_file_id=graphene.List(graphene.String)
    tags = graphene.List(graphene.String, description="List of tags/keywords for community search and categorization")
    reaction = custom_graphql_validator.String.add_option("reaction", "CreateCommunityPost")()
    vibe = custom_graphql_validator.Float.add_option("vibe", "CreateCommunityPost")()
    mentioned_user_uids = graphene.List(graphene.String)
