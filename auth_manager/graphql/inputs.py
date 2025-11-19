# autm_manager/graphql/inputs.py
import graphene
from .types import DeleteTypeEnum
# from auth_manager.Utils.auth_manager_validation import NonSpecialCharacterString
from auth_manager.validators import custom_graphql_validator
from auth_manager.validators.custom_graphql_validator import CreateAchievementWhatValidator, CreateAchievementFromSourceValidator
from auth_manager.graphql.enums.profile_content_category_enum import ProfileContentCategoryEnum

class InviteTypeEnum(graphene.Enum):
    MENU = "menu"
    COMMUNITY = "community"
    TRUTH_SECTION="truth_section"

class ProfiledataTypeEnum(graphene.Enum):
    ACHIEVEMENT = "achievement"
    EXPERIENCE = "experience"
    EDUCATION="education"
    SKILL="skill"

class CreateInviteInput(graphene.InputObjectType):
    origin_type = InviteTypeEnum(required=True)



class CreateUserInput(graphene.InputObjectType):
    email = custom_graphql_validator.String.add_option("email", "CreateUser")(required=True)
    password = custom_graphql_validator.String.add_option("password", "CreateUser")(required=True)
    user_type=custom_graphql_validator.String.add_option("userType", "CreateUser")(required=False)
    invite_token = custom_graphql_validator.String.add_option("inviteToken", "CreateUser")(required=False)
    is_bot = custom_graphql_validator.Boolean.add_option("isBot", "CreateUser")(required=False)
    persona = custom_graphql_validator.String.add_option("persona", "CreateUser")(required=False)


class CreateUserInputV2(graphene.InputObjectType):
    email = custom_graphql_validator.String.add_option("email", "CreateUserV2")(required=True)
    password = custom_graphql_validator.String.add_option("password", "CreateUserV2")(required=True)
    user_type=custom_graphql_validator.String.add_option("userType", "CreateUserV2")(required=False)
    invite_token=custom_graphql_validator.String.add_option("inviteToken", "CreateUserV2")(required=False)
    is_bot = custom_graphql_validator.Boolean.add_option("isBot", "CreateUserV2")(required=False)
    persona = custom_graphql_validator.String.add_option("persona", "CreateUserV2")(required=False)

class CreateVerifiedUserInput(graphene.InputObjectType):
    email = custom_graphql_validator.String.add_option("email", "CreateVerifiedUser")(required=True)
    first_name = custom_graphql_validator.NonSpecialCharacterString2_30.add_option("firstName", "CreateVerifiedUser")(required=True)
    last_name = custom_graphql_validator.NonSpecialCharacterString2_30.add_option("lastName", "CreateVerifiedUser")(required=True)
    password = custom_graphql_validator.String.add_option("password", "CreateVerifiedUser")(required=True)
    user_type = custom_graphql_validator.String.add_option("userType", "CreateVerifiedUser")(required=False)
    is_bot = custom_graphql_validator.Boolean.add_option("isBot", "CreateVerifiedUser")(required=False)
    persona = custom_graphql_validator.String.add_option("persona", "CreateVerifiedUser")(required=False)
    gender = custom_graphql_validator.String.add_option("gender", "CreateVerifiedUser")(required=False)
    bio = custom_graphql_validator.NonSpecialCharacterString1_200.add_option("bio", "CreateVerifiedUser")(required=False)
    designation = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("designation", "CreateVerifiedUser")(required=False)
    worksat = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("worksat", "CreateVerifiedUser")(required=False)
    lives_in = custom_graphql_validator.String.add_option("livesIn", "CreateVerifiedUser")(required=False)
    state = custom_graphql_validator.String.add_option("state", "CreateVerifiedUser")(required=False)
    city = custom_graphql_validator.String.add_option("city", "CreateVerifiedUser")(required=False)
    profile_pic_id = custom_graphql_validator.String.add_option("profilePicId", "CreateVerifiedUser")(required=False)
    cover_image_id = custom_graphql_validator.String.add_option("coverImageId", "CreateVerifiedUser")(required=False)

class SocialLoginInput(graphene.InputObjectType):
    """Input for social login authentication"""
    access_token = graphene.String(required=True)
    provider = graphene.String(required=True)  # 'google', 'facebook', 'apple'
    invite_token = graphene.String()  # Optional invite token
    device_id = graphene.String()  # Optional device ID

class AppleSocialLoginInput(graphene.InputObjectType):
    """Input for Apple social login authentication"""
    identity_token = graphene.String(required=True)  # Apple ID token
    authorization_code = graphene.String()  # Optional authorization code
    invite_token = graphene.String()  # Optional invite token
    device_id = graphene.String()  # Optional device ID




class CreateProfileInput(graphene.InputObjectType):
    gender = custom_graphql_validator.String.add_option("gender", "CreateProfile")()
    fcm_token = custom_graphql_validator.String.add_option("fcmToken", "CreateProfile")()
    bio = custom_graphql_validator.String.add_option("bio", "CreateProfile")()
    device_id = custom_graphql_validator.String.add_option("deviceId", "CreateProfile")()
    designation = custom_graphql_validator.String.add_option("designation", "CreateProfile")()
    worksat = custom_graphql_validator.String.add_option("worksat", "CreateProfile")()
    phone_number = custom_graphql_validator.String.add_option("phoneNumber", "CreateProfile")()
    born = custom_graphql_validator.DateTimeScalar.add_option("born", "CreateProfile")()
    school = custom_graphql_validator.String.add_option("school", "CreateProfile")()
    college = custom_graphql_validator.String.add_option("college", "CreateProfile")()
    lives_in = custom_graphql_validator.String.add_option("livesIn", "CreateProfile")()
    profile_pic_id = custom_graphql_validator.String.add_option("profilePicId", "CreateProfile")()
    cover_image_id = custom_graphql_validator.String.add_option("coverImageId", "CreateProfile")()
    professional_life = custom_graphql_validator.String.add_option("professionalLife", "CreateProfile")()
    last_email_otp = custom_graphql_validator.String.add_option("lastEmailOtp", "CreateProfile")()
    last_phone_otp = custom_graphql_validator.String.add_option("lastPhoneOtp", "CreateProfile")()
    email_otp_expaire = graphene.DateTime()
    phone_otp_expaire = graphene.DateTime()
    ai_commenting = custom_graphql_validator.Boolean.add_option("aiCommenting", "CreateProfile")()
    username_updated = custom_graphql_validator.Boolean.add_option("usernameUpdated", "CreateProfile")()



class UpdateProfileInput(graphene.InputObjectType):
    first_name = custom_graphql_validator.NonSpecialCharacterString2_30.add_option("firstName", "UpdateProfile")()
    last_name = custom_graphql_validator.SpaceSpecialCharacterString2_30.add_option("lastName", "UpdateProfile")()
    gender = custom_graphql_validator.String.add_option("gender", "UpdateProfile")()
    device_id = custom_graphql_validator.String.add_option("deviceId", "UpdateProfile")()
    fcm_token = custom_graphql_validator.String.add_option("fcmToken", "UpdateProfile")()
    bio = custom_graphql_validator.NonSpecialCharacterString1_200.add_option("bio", "UpdateProfile")()
    designation = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("designation", "UpdateProfile")()
    phone_number = custom_graphql_validator.PhoneNumberScalar.add_option("phoneNumber", "UpdateProfile")()
    born = custom_graphql_validator.DateTimeScalar.add_option("born", "UpdateProfile")()
    dob = custom_graphql_validator.DateTimeScalar.add_option("dob", "UpdateProfile")()
    lives_in = custom_graphql_validator.String.add_option("livesIn", "UpdateProfile")() 
    profile_pic_id = custom_graphql_validator.String.add_option("profilePicId", "UpdateProfile")()
    cover_image_id = custom_graphql_validator.String.add_option("coverImageId", "UpdateProfile")()
    state = custom_graphql_validator.String.add_option("state", "UpdateProfile")()
    city = custom_graphql_validator.String.add_option("city", "UpdateProfile")()
    mentioned_user_uids = graphene.List(graphene.String)

class OnboardingInput(graphene.InputObjectType):
    profile_uid = graphene.String()
    email_verified = graphene.Boolean()
    phone_verified = graphene.Boolean()
    username_selected = graphene.Boolean()
    first_name_set = graphene.Boolean()
    last_name_set = graphene.Boolean()
    gender_set = graphene.Boolean()
    bio_set = graphene.Boolean()

class UpdateOnboardingInput(graphene.InputObjectType):
    uid = graphene.String()
    email_verified = graphene.Boolean()
    phone_verified = graphene.Boolean()
    username_selected = graphene.Boolean()
    first_name_set = graphene.Boolean()
    last_name_set = graphene.Boolean()
    gender_set = graphene.Boolean()
    bio_set = graphene.Boolean()

class ContactinfoInput(graphene.InputObjectType):
    type = custom_graphql_validator.String.add_option("type", "Contactinfo")(required=True)
    value = custom_graphql_validator.String.add_option("value", "Contactinfo")(required=True)
    platform = custom_graphql_validator.String.add_option("platform", "Contactinfo")()
    link = custom_graphql_validator.String.add_option("link", "Contactinfo")()
    

class UpdateContactinfoInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateContactinfo")(required=True)
    type = custom_graphql_validator.String.add_option("type", "UpdateContactinfo")()
    value = custom_graphql_validator.String.add_option("value", "UpdateContactinfo")()
    platform = custom_graphql_validator.String.add_option("platform", "UpdateContactinfo")()
    link = custom_graphql_validator.String.add_option("link", "UpdateContactinfo")()

class DeleteInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "Delete")(required=True)

class ScoreInput(graphene.InputObjectType):
    vibers_count = custom_graphql_validator.Float.add_option("vibersCount", "Score")()
    cumulative_vibescore = custom_graphql_validator.Float.add_option("cumulativeVibescore", "Score")()
    intelligence_score = custom_graphql_validator.Float.add_option("intelligenceScore", "Score")()
    appeal_score = custom_graphql_validator.Float.add_option("appealScore", "Score")()
    social_score = custom_graphql_validator.Float.add_option("socialScore", "Score")()
    human_score = custom_graphql_validator.Float.add_option("humanScore", "Score")()
    repo_score = custom_graphql_validator.Float.add_option("repoScore", "Score")()
    profile_uid = custom_graphql_validator.String.add_option("profileUid", "Score")(required=True)

class UpdateScoreInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateScore")(required=True)
    vibers_count = custom_graphql_validator.Float.add_option("vibersCount", "UpdateScore")()
    cumulative_vibescore = custom_graphql_validator.Float.add_option("cumulativeVibescore", "UpdateScore")()
    intelligence_score = custom_graphql_validator.Float.add_option("intelligenceScore", "UpdateScore")()
    appeal_score = custom_graphql_validator.Float.add_option("appealScore", "UpdateScore")()
    social_score = custom_graphql_validator.Float.add_option("socialScore", "UpdateScore")()
    human_score = custom_graphql_validator.Float.add_option("humanScore", "UpdateScore")()
    repo_score = custom_graphql_validator.Float.add_option("repoScore", "UpdateScore")()

class InerestInput(graphene.InputObjectType):
    names = custom_graphql_validator.ListString.add_option("names", "Interest")( required=True)
    

class UpdateInterestInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateInterest")(required=True)
    names = custom_graphql_validator.ListString.add_option("names", "UpdateInterest")()
    is_deleted = custom_graphql_validator.Boolean.add_option("isDeleted", "UpdateInterest")()

class VerifyOtpInput(graphene.InputObjectType):
    otp = custom_graphql_validator.String.add_option("otp", "VerifyOtp")(required=True)

# Password Reset Flow Input Types
class FindUserInput(graphene.InputObjectType):
    email_or_username = custom_graphql_validator.String.add_option("emailOrUsername", "FindUser")(required=True)

class SendOTPInput(graphene.InputObjectType):
    user_uid = custom_graphql_validator.String.add_option("userUid", "SendOTP")(required=True)

class VerifyOTPInput(graphene.InputObjectType):
    email = custom_graphql_validator.String.add_option("email", "VerifyOTP")(required=True)
    otp = custom_graphql_validator.String.add_option("otp", "VerifyOTP")(required=True)

class UpdatePasswordInput(graphene.InputObjectType):
    email = custom_graphql_validator.String.add_option("email", "UpdatePassword")(required=True)
    new_password = custom_graphql_validator.String.add_option("newPassword", "UpdatePassword")(required=True)
    otp_verified = custom_graphql_validator.Boolean.add_option("otpVerified", "UpdatePassword")(required=True)

class DeleteUserAccountInput(graphene.InputObjectType):
    username = custom_graphql_validator.String.add_option("username", "DeleteUserAccount")(required=True)
    deleteType = DeleteTypeEnum(required=True)

class DeleteUserProfileInput(graphene.InputObjectType):
    username = custom_graphql_validator.String.add_option("username", "DeleteUserProfile")(required=True)

class LoginInput(graphene.InputObjectType):
    usernameEmail = custom_graphql_validator.String.add_option("usernameEmail", "Login")(required=True)
    password = custom_graphql_validator.String.add_option("password", "Login")(required=True)
    device_id = custom_graphql_validator.String.add_option("deviceId", "Login")()

class SelectUsernameInput(graphene.InputObjectType):
    username = custom_graphql_validator.String.add_option("username", "SelectUsername")(required=True)


class CreateAchievementInput(graphene.InputObjectType):
    what = CreateAchievementWhatValidator.add_option("what", "CreateAchievement")(required=True)
    from_source = CreateAchievementFromSourceValidator.add_option("fromSource", "CreateAchievement")(required=True)
    description = custom_graphql_validator.SpecialCharacterString2_100.add_option("description", "CreateAchievement")()
    from_date = custom_graphql_validator.DateTimeScalar.add_option("fromDate", "CreateAchievement")(required=True)
    to_date = custom_graphql_validator.DateTimeScalar.add_option("toDate", "CreateAchievement")()
    created_on = graphene.DateTime()
    file_id=custom_graphql_validator.ListString.add_option("fileId", "CreateAchievement")()
    
class UpdateAchievementInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateAchievement")(required=True)
    what = custom_graphql_validator.SpecialCharacterString2_100.add_option("what", "UpdateAchievement")()
    from_source = custom_graphql_validator.SpecialCharacterString2_100.add_option("fromSource", "UpdateAchievement")()
    description = custom_graphql_validator.SpecialCharacterString2_100.add_option("description", "UpdateAchievement")()
    from_date = custom_graphql_validator.DateTimeScalar.add_option("fromDate", "UpdateAchievement")()
    to_date = custom_graphql_validator.DateTimeScalar.add_option("toDate", "UpdateAchievement")()
    file_id=custom_graphql_validator.ListString.add_option("fileId", "UpdateAchievement")()



class CreateUsersReviewInput(graphene.InputObjectType):
    touser_uid = custom_graphql_validator.String.add_option("touserUid", "CreateUsersReview")(required=True)
    reaction = custom_graphql_validator.String.add_option("reaction", "CreateUsersReview")(required=True)
    vibe = custom_graphql_validator.Float.add_option("vibe", "CreateUsersReview")()
    title = custom_graphql_validator.String.add_option("title", "CreateUsersReview")()
    content = custom_graphql_validator.String.add_option("content", "CreateUsersReview")()
    file_id = custom_graphql_validator.String.add_option("fileId", "CreateUsersReview")()


class CreateBackProfileReviewInput(graphene.InputObjectType):
    touser_uid = custom_graphql_validator.String.add_option("touserUid", "CreateBackProfileReview")(required=True)
    reaction = custom_graphql_validator.String.add_option("reaction", "CreateBackProfileReview")(required=True)
    vibe = custom_graphql_validator.Float.add_option("vibe", "CreateBackProfileReview")()
    title = custom_graphql_validator.String.add_option("title", "CreateBackProfileReview")()
    content = custom_graphql_validator.String.add_option("content", "CreateBackProfileReview")()
    # file_id = custom_graphql_validator.String.add_option("fileId", "CreateBackProfileReview")()
    # image_ids = graphene.List(custom_graphql_validator.String.add_option("imageIds", "CreateBackProfileReview"))
    image_ids = custom_graphql_validator.ListString.add_option("imageIds", "CreateBackProfileReview")()
    rating = custom_graphql_validator.Int.add_option("rating", "CreateBackProfileReview")()

class UpdateUsersReviewInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateUsersReview")(required=True)
    reaction = custom_graphql_validator.String.add_option("reaction", "UpdateUsersReview")()
    vibe = custom_graphql_validator.Float.add_option("vibe", "UpdateUsersReview")()
    title = custom_graphql_validator.String.add_option("title", "UpdateUsersReview")()
    content = custom_graphql_validator.String.add_option("content", "UpdateUsersReview")()
    file_id = custom_graphql_validator.String.add_option("fileId", "UpdateUsersReview")()
    is_deleted = custom_graphql_validator.Boolean.add_option("isDeleted", "UpdateUsersReview")()

class DeleteUsersReviewInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "DeleteUsersReview")(required=True)





class CreateProfileDataReactionInputV2(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "CreateProfileDataReactionV2")(required=True)
    category = ProfiledataTypeEnum(required=True)
    reaction = custom_graphql_validator.String.add_option("reaction", "CreateProfileDataReactionV2")()
    vibe = custom_graphql_validator.Float.add_option("vibe", "CreateProfileDataReactionV2")()

class CreateProfileCommentInputV2(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "CreateProfileCommentV2")(required=True)
    category=ProfiledataTypeEnum(required=True)
    content = custom_graphql_validator.NonSpecialCharacterString1_200.add_option("content", "CreateProfileCommentV2")(required=True)


class UpdateProfileCommentInputV2(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateProfileCommentV2")(required=True)
    content = custom_graphql_validator.NonSpecialCharacterString1_200.add_option("content", "UpdateProfileCommentV2")(required=True)

class CreateEducationInput(graphene.InputObjectType):
    what = custom_graphql_validator.SpecialCharacterString2_100.add_option("what", "CreateEducation")(required=True)
    from_date = custom_graphql_validator.DateTimeScalar.add_option("fromDate", "CreateEducation")(required=True)
    to_date = custom_graphql_validator.DateTimeScalar.add_option("toDate", "CreateEducation")()
    from_source = custom_graphql_validator.SpecialCharacterString2_100.add_option("fromSource", "CreateEducation")(required=True)
    field_of_study=custom_graphql_validator.SpecialCharacterString2_50.add_option("fieldOfStudy", "CreateEducation")()
    created_on = graphene.DateTime()
    description = custom_graphql_validator.SpecialCharacterString5_200.add_option("description", "CreateEducation")()
    file_id=custom_graphql_validator.ListString.add_option("fileId", "CreateEducation")()


class UpdateEducationInput(graphene.InputObjectType):
    uid= custom_graphql_validator.String.add_option("uid", "UpdateEducation")(required=True)
    what = custom_graphql_validator.SpecialCharacterString2_100.add_option("what", "UpdateEducation")()
    from_date = custom_graphql_validator.DateTimeScalar.add_option("fromDate", "UpdateEducation")()
    to_date = custom_graphql_validator.DateTimeScalar.add_option("toDate", "UpdateEducation")()
    from_source = custom_graphql_validator.SpecialCharacterString2_100.add_option("fromSource", "UpdateEducation")()
    field_of_study=custom_graphql_validator.SpecialCharacterString2_50.add_option("fieldOfStudy", "UpdateEducation")()
    description = custom_graphql_validator.SpecialCharacterString5_200.add_option("description", "UpdateEducation")()
    file_id=custom_graphql_validator.ListString.add_option("fileId", "UpdateEducation")()


class CreateExperienceInput(graphene.InputObjectType):
    what = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("what", "CreateExperience")(required=True)
    description = custom_graphql_validator.SpecialCharacterString5_200.add_option("description", "CreateExperience")()
    created_on = graphene.DateTime()
    from_source = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("fromSource", "CreateExperience")(required=True)
    from_date = custom_graphql_validator.DateTimeScalar.add_option("fromDate", "CreateExperience")(required=True)
    to_date = custom_graphql_validator.DateTimeScalar.add_option("toDate", "CreateExperience")()
    file_id=custom_graphql_validator.ListString.add_option("fileId", "CreateExperience")()


class UpdateExperienceInput(graphene.InputObjectType):
    uid= custom_graphql_validator.String.add_option("uid", "UpdateExperience")(required=True)
    what = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("what", "UpdateExperience")()
    description = custom_graphql_validator.SpecialCharacterString5_200.add_option("description", "UpdateExperience")()
    from_source = custom_graphql_validator.NonSpecialCharacterString2_100.add_option("fromSource", "UpdateExperience")()
    from_date = custom_graphql_validator.DateTimeScalar.add_option("fromDate", "UpdateExperience")()
    to_date = custom_graphql_validator.DateTimeScalar.add_option("toDate", "UpdateExperience")()
    file_id=custom_graphql_validator.ListString.add_option("fileId", "UpdateExperience")()

class CreateSkillInput(graphene.InputObjectType):
    what = custom_graphql_validator.SpecialCharacterString2_100.add_option("what", "CreateSkill")(required=True)
    from_source = custom_graphql_validator.SpecialCharacterString2_100.add_option("fromSource", "CreateSkill")()
    file_id=custom_graphql_validator.ListString.add_option("fileId", "CreateSkill")()
    from_date = custom_graphql_validator.DateTimeScalar.add_option("fromDate", "CreateSkill")()
    to_date = custom_graphql_validator.DateTimeScalar.add_option("toDate", "CreateSkill")()


class UpdateSkillInput(graphene.InputObjectType):
    uid= custom_graphql_validator.String.add_option("uid", "UpdateSkill")(required=True)
    what = custom_graphql_validator.SpecialCharacterString2_100.add_option("what", "UpdateSkill")()
    from_source = custom_graphql_validator.NonSemiSpecialCharacterString2_100.add_option("fromSource", "UpdateSkill")()
    from_date = custom_graphql_validator.DateTimeScalar.add_option("fromDate", "UpdateSkill")()
    to_date = custom_graphql_validator.DateTimeScalar.add_option("toDate", "UpdateSkill")()
    file_id=custom_graphql_validator.ListString.add_option("fileId", "UpdateSkill")()

class CreateStoryInput(graphene.InputObjectType):
    title = custom_graphql_validator.SpecialCharacterString1_50.add_option("title", "CreateStory")(required=True)
    content = custom_graphql_validator.SpecialCharacterString1_50.add_option("content", "CreateStory")(required=True)
    captions = custom_graphql_validator.SpecialCharacterString1_100.add_option("captions", "CreateStory")(required=True)

class UpdateStoryInput(graphene.InputObjectType):
    uid = custom_graphql_validator.String.add_option("uid", "UpdateStory")(required=True)
    title = custom_graphql_validator.SpecialCharacterString1_50.add_option("title", "UpdateStory")()
    content = custom_graphql_validator.SpecialCharacterString1_50.add_option("content", "UpdateStory")()
    captions = custom_graphql_validator.SpecialCharacterString1_100.add_option("captions", "UpdateStory")()

class SendVibeToProfileContentInput(graphene.InputObjectType):
    """
    Input type for sending vibe reactions to profile content.
    
    This input defines the required parameters for sending a vibe reaction
    to profile content (achievements, education, skills, experience).
    
    Fields:
        content_uid: UID of the content item (achievement, education, skill, experience)
        content_category: Category of content - DROPDOWN with options:
            - ACHIEVEMENT: User achievements and accomplishments
            - EDUCATION: Educational background and qualifications
            - SKILL: User skills and competencies
            - EXPERIENCE: Professional work experience
        individual_vibe_id: ID of the IndividualVibe from PostgreSQL
        vibe_intensity: Intensity of the vibe (1.0 to 5.0)
    
    Usage:
        Used in SendVibeToProfileContent mutation to specify which content
        to react to and the vibe details.
    """
    content_uid = custom_graphql_validator.String.add_option("contentUid", "SendVibeToProfileContent")(required=True, description="UID of the content item")
    content_category = graphene.Field(ProfileContentCategoryEnum, required=True, description="Category of profile content (dropdown: ACHIEVEMENT, EDUCATION, SKILL, EXPERIENCE)")
    individual_vibe_id = custom_graphql_validator.Int.add_option("individualVibeId", "SendVibeToProfileContent")(required=True, description="ID of the vibe from IndividualVibe table")
    vibe_intensity = custom_graphql_validator.Float.add_option("vibeIntensity", "SendVibeToProfileContent")(required=True, description="Intensity of the vibe (range: 1.0 to 5.0)")
