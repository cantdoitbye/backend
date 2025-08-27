# auth_manager/graphql/queries.py
from neomodel import db
import graphene
from graphql import GraphQLError
from .types import *
from auth_manager.models import *
from graphql_jwt.decorators import login_required,superuser_required
from django.db.models import Count, Avg

from msg.models import MatrixProfile
from auth_manager.Utils.auth_manager_decorator import handle_graphql_auth_manager_errors
from .inputs import ProfiledataTypeEnum



from auth_manager.graphql.raw_queries import profile_details_query

class StateType(DjangoObjectType):
    """
    GraphQL type for StateInfo model.
    
    Represents state information in the GraphQL schema,
    exposing state ID and name fields.
    
    Meta:
        model: StateInfo Django model
        fields: Limited to id and state_name
    """
    class Meta:
        model = StateInfo
        fields = ("id", "state_name")

class CityType(DjangoObjectType):
    """
    GraphQL type for CityInfo model.
    
    Represents city information in the GraphQL schema,
    exposing city ID and name fields.
    
    Meta:
        model: CityInfo Django model
        fields: Limited to id and city_name
    """
    class Meta:
        model = CityInfo
        fields = ("id", "city_name")

class InviteType(DjangoObjectType):
    """
    GraphQL type for Invite model.
    
    Represents invitation records in the GraphQL schema,
    exposing all model fields for invite operations.
    
    Meta:
        model: Invite Django model
        fields: All model fields are exposed
    """
    class Meta:
        model = Invite
        fields = "__all__"

class GetInviteDetails(graphene.ObjectType):
    """
    Response type for invite detail queries.
    
    Provides structured response for invite-related operations
    including the invite object, success status, and messages.
    
    Fields:
        invite: InviteType object containing invite details
        success: Boolean indicating operation success
        message: String containing response message
    """
    invite = graphene.Field(InviteType)
    success = graphene.Boolean()
    message = graphene.String()


class UploadContactType(DjangoObjectType):
    """
    GraphQL type for UploadContact model.
    
    Represents uploaded contact information in the GraphQL schema,
    providing access to contact data fields.
    
    Meta:
        model: UploadContact Django model
    """
    class Meta:
        model = UploadContact

class SubInterestType(graphene.ObjectType):
    """
    GraphQL type for sub-interest data.
    
    Represents individual sub-interest items with ID and name,
    used within interest list structures.
    
    Fields:
        id: Integer ID of the sub-interest (required)
        name: String name of the sub-interest (required)
    """
    id = graphene.Int(required=True)
    name = graphene.String(required=True)

class InterestListType(DjangoObjectType):
    """
    GraphQL type for InterestList model with sub-interests.
    
    Represents interest categories with their associated sub-interests,
    providing hierarchical interest data structure.
    
    Fields:
        sub_interests: List of SubInterestType objects
    
    Meta:
        model: InterestList Django model
        fields: id, name, and sub_interests
    """
    sub_interests = graphene.List(SubInterestType)

    class Meta:
        model = InterestList
        fields = ("id", "name", "sub_interests")

    def resolve_sub_interests(self, info):
        """
        Resolves sub-interests list for an interest category.
        
        Converts sub_interests data into SubInterestType objects,
        ensuring proper format and structure validation.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[SubInterestType]: List of sub-interest objects
        """
        # Check if sub_interests is in a correct format
        # Ensure self.sub_interests is a list
        if isinstance(self.sub_interests, list):
            return [
                SubInterestType(id=sub_interest['id'], name=sub_interest['name'])
                for sub_interest in self.sub_interests
            ]
        return []


class Query(graphene.ObjectType):
    """
    Main GraphQL Query class for auth_manager.
    
    Provides all query resolvers for user authentication, profile management,
    and data retrieval operations. Includes both public and authenticated queries
    for various user-related functionalities.
    
    Features:
        - User profile and data queries
        - Authentication and matrix user searches
        - Interest, achievement, education, skill, and experience queries
        - Contact and invitation management
        - Administrative queries for superusers
    """

    all_users = graphene.List(
        UserType,
        first=graphene.Int(description="Number of users to return (limit)"),
        skip=graphene.Int(description="Number of users to skip (offset)"),
        search=graphene.String(description="Search term to filter users by firstName, lastName, username, or email")
    )
    
    @login_required
    def resolve_all_users(self, info, **kwargs):
        """
        Retrieves all users in the system.
        
        Returns a list of all registered users. Requires user authentication.
        
        Args:
            info: GraphQL resolve info context
            **kwargs: Additional keyword arguments
        
        Returns:
            List[UserType]: List of all user objects
        
        Raises:
            GraphQLError: If user is not authenticated
        
        Note:
            - Requires login authentication
            - Returns all users without filtering
        """
        # print(info.context.user)
        return [UserType.from_neomodel(user) for user in Users.nodes.all()]
    
    get_invitee_details = graphene.Field(GetInviteDetails, invite_token=graphene.String(required=True))

    def resolve_get_invitee_details(self, info, invite_token):
        try:
            # Check if the invite exists
            invite = Invite.objects.filter(invite_token=invite_token, is_deleted=False).first()

            if not invite:
                raise GraphQLError("Invalid invite token")

            # Check if the invite is expired
            if invite.expiry_date < timezone.now():
                return GetInviteDetails(
                    invite=None,
                    success=False,
                    message="This invite link has expired."
                )

            # Return invite details if valid
            return GetInviteDetails(
                invite=invite,
                success=True,
                message="Invite details retrieved successfully."
            )

        except Exception as error:
            return GetInviteDetails(
                invite=None,
                success=False,
                message=str(error)
            )

    search_matrix_username = graphene.Field(MatrixUserType, username=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_search_matrix_username(self, info, username):
        """
        Searches for a user by username and retrieves Matrix profile information.
        
        Finds a user by username and includes their Matrix chat profile data
        if available, enabling Matrix integration features.
        
        Args:
            info: GraphQL resolve info context
            username (str): Username to search for (required)
        
        Returns:
            MatrixUserType: User object with Matrix profile information
        
        Raises:
            GraphQLError: If user not found or Matrix profile doesn't exist
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Validates Matrix profile existence
        """
        try:
            # Fetch user node by username
            user = Users.nodes.get(username=username)
            user_data = MatrixUserType.from_neomodel(user)
            try:
                matrix_profile = MatrixProfile.objects.get(user=user_data.user_id)
                if(matrix_profile.matrix_user_id):
                    user_data.matrix_info = MatrixInfoType(matrix_user_id=matrix_profile.matrix_user_id)
                else:
                    raise GraphQLError(f"Matrix User with username '{username}' does not exist.")
            except:
                matrix_profile=None
            return user_data
        except Users.DoesNotExist:
            raise GraphQLError(f"User with username '{username}' does not exist.")

    welcome_messages = graphene.List(WelcomeScreenMessageType)
    def resolve_welcome_messages(self, info):
        """
        Retrieves all welcome screen messages.
        
        Returns welcome messages displayed to users on app screens,
        typically used for onboarding or announcements.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[WelcomeScreenMessageType]: List of welcome message objects
        
        Note:
            - Public query, no authentication required
            - Returns all available welcome messages
        """
        return WelcomeScreenMessage.objects.all()
    

    profile_by_user_id = graphene.Field(ProfileDetailsVibeType, user_id=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_profile_by_user_id(self, info, user_id):
        """
        Retrieves detailed profile information for a specific user.
        
        Fetches comprehensive profile data for viewing another user's profile,
        including personal information and profile details.
        
        Args:
            info: GraphQL resolve info context
            user_id (str): Target user's ID to retrieve profile for (required)
        
        Returns:
            ProfileDetailsVibeType: Detailed profile information object
        
        Raises:
            GraphQLError: If user or profile not found
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns profile data for viewing other users
        """
        profile = Profile.nodes.get(user_id=user_id)
        payload = info.context.payload
        # print(info.context)
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)
        return ProfileDetailsVibeType.from_neomodel(profile,user_node)
        
        
        
    my_profile=graphene.Field(ProfileInfoType)
    @handle_graphql_auth_manager_errors    
    @login_required
    def resolve_my_profile(self, info):
        """
        Retrieves comprehensive profile information for the authenticated user.
        
        Returns complete profile data including personal info, onboarding status,
        scores, interests, achievements, education, skills, experience, and counts
        for posts, communities, and connections.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            ProfileInfoType: Complete profile information object with all related data
        
        Raises:
            GraphQLError: If user profile not found or database error
        
        Note:
            - Requires login authentication
            - Uses complex Cypher query for comprehensive data retrieval
            - Includes statistical counts for user engagement metrics
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        profile = Profile.nodes.get(user_id=user_id)
        

        params = {
            "log_in_user_profile_uid": profile.uid  # ID of the logged-in user
        }

    
        # Execute the query
        results, _ = db.cypher_query(profile_details_query.get_profile_details_query, params)
       
        
        profile_node=results[0][0] if results[0][0] else None
        user_node=results[0][1] if results[0][1] else None
        onboardingStatus_node=results[0][2] if results[0][2] else None
        score_node=results[0][3] if results[0][3] else None
        interest_node=results[0][4] if results[0][4] else None
        achievement_node=results[0][5] if results[0][5] else None
        education_node=results[0][6] if results[0][6] else None
        skill_node=results[0][7] if results[0][7] else None
        experience_node=results[0][8] if results[0][8] else None
        post_count = results[0][9] if len(results[0]) > 9 else 0
        community_count = results[0][10] if len(results[0]) > 10 else 0
        connection_count = results[0][11] if len(results[0]) > 11 else 0


        return ProfileInfoType.from_neomodel(profile_node,user_node,onboardingStatus_node,score_node,interest_node,achievement_node,education_node,skill_node,experience_node,post_count, community_count, connection_count)
        
        
    my_onboarding=graphene.List(OnboardingStatusType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_onboarding(self,info):
        """
        Retrieves onboarding status information for the authenticated user.
        
        Returns the user's onboarding progress and completion status,
        used to track which onboarding steps have been completed.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[OnboardingStatusType]: List of onboarding status objects
        
        Raises:
            GraphQLError: If user or profile not found
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns all onboarding status records for the user
        """

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)
        profile_node=user_node.profile.single()
        my_onboarding = list(profile_node.onboarding)
        return [OnboardingStatusType.from_neomodel(x) for x in my_onboarding]
       
        
    score_by_uid = graphene.List(ScoreType, user_uid=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_score_by_uid(self, info, user_uid):
        """
        Retrieves all scores for a specific user by their UID.
        
        Fetches score data for a target user, typically used for viewing
        another user's achievements and performance metrics.
        
        Args:
            info: GraphQL resolve info context
            user_uid (str): Target user's UID to retrieve scores for (required)
        
        Returns:
            List[ScoreType]: List of score objects for the specified user
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns all scores without filtering
        """
        user_node = Users.nodes.get(uid=user_uid)
        profile_node = user_node.profile.single()
        all_scores = list(profile_node.score)
        return [ScoreType.from_neomodel(score) for score in all_scores]
    
   
    my_scores = graphene.List(ScoreType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_scores(self, info):
        """
        Retrieves all scores for the authenticated user.
        
        Returns the current user's score data including achievements,
        performance metrics, and any gamification elements.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[ScoreType]: List of score objects for the authenticated user
        
        Raises:
            GraphQLError: If user or profile not found
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns all user's scores without filtering
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        profile_node = user_node.profile.single()
        my_scores = list(profile_node.score)
        return [ScoreType.from_neomodel(x) for x in my_scores]
        

    interest_by_uid = graphene.List(InterestType, user_uid=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_interest_by_uid(self, info, user_uid):
        """
        Retrieves all interests for a specific user by their UID.
        
        Fetches interest data for a target user, used for viewing
        another user's interests and preferences.
        
        Args:
            info: GraphQL resolve info context
            user_uid (str): Target user's UID to retrieve interests for (required)
        
        Returns:
            List[InterestType]: List of interest objects for the specified user
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns all interests including deleted ones
        """
        user_node = Users.nodes.get(uid=user_uid)
        profile_node = user_node.profile.single()
        all_interests = list(profile_node.interest)
        return [InterestType.from_neomodel(interest) for interest in all_interests]
    
   
    my_interests = graphene.List(InterestType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_interests(self, info):
        """
        Retrieves active interests for the authenticated user.
        
        Returns the current user's interest data, filtering out deleted interests
        to show only currently active preferences.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[InterestType]: List of active interest objects for the authenticated user
        
        Raises:
            GraphQLError: If user or profile not found
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Filters out deleted interests (is_deleted=True)
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)
        profile_node = user_node.profile.single()
        my_interest = list(profile_node.interest)
        my_interests=[interest for interest in my_interest if not interest.is_deleted]
        return [InterestType.from_neomodel(x) for x in my_interests]
        
        
    achievement_by_user_id = graphene.List(AchievementType, user_uid=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_achievement_by_user_id(self, info, user_uid):
        """
        Retrieves all achievements for a specific user by their UID.
        
        Fetches achievement data for a target user, used for viewing
        another user's accomplishments and milestones.
        
        Args:
            info: GraphQL resolve info context
            user_uid (str): Target user's UID to retrieve achievements for (required)
        
        Returns:
            List[AchievementType]: List of achievement objects for the specified user
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns all achievements including deleted ones
        """
        user_node = Users.nodes.get(uid=user_uid)
        profile_node=user_node.profile.single()
        all_achievement = list(profile_node.achievement)
        return [AchievementType.from_neomodel(achievement) for achievement in all_achievement]
        
    my_achievement=graphene.List(AchievementType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_achievement(self,info):
        """
        Retrieves active achievements for the authenticated user.
        
        Returns the current user's achievement data, filtering out deleted achievements
        to show only currently active accomplishments.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[AchievementType]: List of active achievement objects for the authenticated user
        
        Raises:
            GraphQLError: If user or profile not found
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Filters out deleted achievements (is_deleted=True)
        """

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)
        profile_node=user_node.profile.single()
        my_achievement = list(profile_node.achievement)
        my_achievements=[achievement for achievement in my_achievement if not achievement.is_deleted]
        return [AchievementType.from_neomodel(x) for x in my_achievements]
        
    
    education_by_user_id = graphene.List(EducationType, user_uid=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_education_by_user_id(self, info, user_uid):
        """
        Retrieves all education records for a specific user by their UID.
        
        Fetches education data for a target user, used for viewing
        another user's educational background and qualifications.
        
        Args:
            info: GraphQL resolve info context
            user_uid (str): Target user's UID to retrieve education for (required)
        
        Returns:
            List[EducationType]: List of education objects for the specified user
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns all education records including deleted ones
        """
        user_node = Users.nodes.get(uid=user_uid)
        profile_node=user_node.profile.single()
        all_education = list(profile_node.education)
        return [EducationType.from_neomodel(education) for education in all_education]

  
    my_education=graphene.List(EducationType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_education(self,info):
        """
        Retrieves active education records for the authenticated user.
        
        Returns the current user's education data, filtering out deleted records
        to show only currently active educational background.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[EducationType]: List of active education objects for the authenticated user
        
        Raises:
            Exception: If user or profile not found, or database error
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Filters out deleted education records (is_deleted=True)
            - Includes additional exception handling
        """

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)

        try:
            profile_node=user_node.profile.single()
            my_education = list(profile_node.education)
            my_educations=[education for education in my_education if not education.is_deleted]
            return [EducationType.from_neomodel(x) for x in my_educations]
        except Exception as e:
            raise Exception(e)
        
    
    skill_by_user_id = graphene.List(SkillType, user_uid=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_skill_by_user_id(self, info, user_uid):
        """
        Retrieves all skills for a specific user by their UID.
        
        Fetches skill data for a target user, used for viewing
        another user's technical and professional skills.
        
        Args:
            info: GraphQL resolve info context
            user_uid (str): Target user's UID to retrieve skills for (required)
        
        Returns:
            List[SkillType]: List of skill objects for the specified user
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns all skills including deleted ones
        """
        user_node = Users.nodes.get(uid=user_uid)
        profile_node=user_node.profile.single()
        all_skill = list(profile_node.skill)
        return [SkillType.from_neomodel(skill) for skill in all_skill]
   
    my_skill=graphene.List(SkillType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_skill(self,info):
        """
        Retrieves active skills for the authenticated user.
        
        Returns the current user's skill data, filtering out deleted skills
        to show only currently active technical and professional skills.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[SkillType]: List of active skill objects for the authenticated user
        
        Raises:
            GraphQLError: If user or profile not found
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Filters out deleted skills (is_deleted=True)
        """

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)
        profile_node=user_node.profile.single()
        my_skill = list(profile_node.skill)
        my_skills=[skill for skill in my_skill if not skill.is_deleted]
        return [SkillType.from_neomodel(x) for x in my_skills]
        
        

    experience_by_user_id = graphene.List(ExperienceType, user_id=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_experience_by_user_id(self, info, user_id):
        """
        Retrieves all work experience records for a specific user by their ID.
        
        Fetches experience data for a target user, used for viewing
        another user's professional work history and career background.
        
        Args:
            info: GraphQL resolve info context
            user_id (str): Target user's ID to retrieve experience for (required)
        
        Returns:
            List[ExperienceType]: List of experience objects for the specified user
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns all experience records including deleted ones
        """
        user_node = Users.nodes.get(user_id=user_id)
        profile_node=user_node.profile.single()
        all_experience = list(profile_node.experience)
        return [ExperienceType.from_neomodel(experience) for experience in all_experience]

   
    my_experience=graphene.List(ExperienceType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_experience(self,info):
        """
        Retrieves active work experience records for the authenticated user.
        
        Returns the current user's experience data, filtering out deleted records
        to show only currently active professional work history.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[ExperienceType]: List of active experience objects for the authenticated user
        
        Raises:
            GraphQLError: If user or profile not found
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Filters out deleted experience records (is_deleted=True)
        """

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)
        profile_node=user_node.profile.single()
        my_experience = list(profile_node.experience)
        my_experiences=[experience for experience in my_experience if not experience.is_deleted]
        return [ExperienceType.from_neomodel(x) for x in my_experiences]
        
        

    interest_lists = graphene.List(InterestListType)

    def resolve_interest_lists(self, info):
        """
        Retrieves all available interest lists.
        
        Returns predefined interest categories and lists that users can
        select from when setting up their profile interests.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[InterestListType]: List of all available interest list objects
        
        Note:
            - Public query, no authentication required
            - Returns all interest lists from Django model
        """
        return InterestList.objects.all()
    

    back_profile_vibe_list_by_user_uid = graphene.List(BackProfileListType, user_uid = graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_back_profile_vibe_list_by_user_uid(self, info, user_uid):
        """
        Retrieves back profile vibe list for a specific user by their UID.
        
        Fetches back profile data and vibes associated with a target user,
        used for viewing profile feedback and impressions.
        
        Args:
            info: GraphQL resolve info context
            user_uid (str): Target user's UID to retrieve back profile list for (required)
        
        Returns:
            List[BackProfileListType]: List of back profile objects for the specified user
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns back profile data based on profile UID
        """
        
        user_node = Users.nodes.get(uid=user_uid)
        profile_uid=user_node.profile.single().uid
        return BackProfileListType.from_neomodel(profile_uid)
        
        

    my_back_profile_review=graphene.List(BackProfileReviewType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_back_profile_review(self,info):
        """
        Retrieves all back profile reviews for the authenticated user.
        
        Returns reviews and feedback that the current user has received
        on their profile from other users.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[BackProfileReviewType]: List of back profile review objects for the authenticated user
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns all reviews received by the user
        """

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)    
        my_reviews=list(user_node.user_back_profile_review.all())
        return [BackProfileReviewType.from_neomodel(x) for x in my_reviews]
        
        

    back_profile_review_by_user_uid=graphene.List(BackProfileReviewType,user_uid = graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_back_profile_review_by_user_uid(self,info,user_uid):
        """
        Retrieves all back profile reviews for a specific user by their UID.
        
        Fetches reviews and feedback that a target user has received
        on their profile from other users.
        
        Args:
            info: GraphQL resolve info context
            user_uid (str): Target user's UID to retrieve reviews for (required)
        
        Returns:
            List[BackProfileReviewType]: List of back profile review objects for the specified user
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns all reviews received by the target user
        """
        
        user_node=Users.nodes.get(uid=user_uid)   
        my_reviews=list(user_node.user_back_profile_review.all())
        return [BackProfileReviewType.from_neomodel(x) for x in my_reviews]
        
        

    back_profile_review_by_uid=graphene.List(BackProfileReviewType,uid = graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_back_profile_review_by_uid(self,info,uid):
        """
        Retrieves a specific back profile review by its UID.
        
        Fetches a single review record by its unique identifier,
        used for viewing detailed review information.
        
        Args:
            info: GraphQL resolve info context
            uid (str): Review's UID to retrieve (required)
        
        Returns:
            List[BackProfileReviewType]: List containing the single review object
        
        Raises:
            GraphQLError: If review not found or database error
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns single review wrapped in list format
        """
        review_node=BackProfileUsersReview.nodes.get(uid=uid)
        return [BackProfileReviewType.from_neomodel(review_node)]
        
    

    # Below apis are not used by frontend
    
    # Administrative queries requiring superuser access
    @login_required
    @superuser_required
    def resolve_all_users(self, info, first=None, skip=None, search=None, **kwargs):
        """
        Retrieves all users in the system with pagination and search (Administrative).
        
        Returns a paginated and searchable list of all registered users for administrative
        purposes. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info context
            first (int, optional): Number of users to return (limit)
            skip (int, optional): Number of users to skip (offset)
            search (str, optional): Search term to filter users by firstName, lastName, username, or email
            **kwargs: Additional keyword arguments
        
        Returns:
            List[UserType]: Paginated and filtered list of user objects
        
        Raises:
            GraphQLError: If user is not authenticated or not a superuser
        
        Note:
            - Requires login authentication and superuser privileges
            - Administrative API not used by frontend
            - Supports pagination with first (limit) and skip (offset) parameters
            - Supports search across username, email, first_name, and last_name fields
            - Search is case-insensitive and matches partial strings
            - Default behavior returns all users if no pagination or search params provided
        """
        # Get all users with verified emails from the database using Cypher query
        query = """
        MATCH (u:Users)-[:HAS_PROFILE]->(p:Profile)-[:HAS_ONBOARDING_STATUS]->(os:OnboardingStatus {email_verified: true})
        RETURN u
        """
        results, meta = db.cypher_query(query)
        all_users = [Users.inflate(row[0]) for row in results]
        
        # Apply search filter if search term is provided
        if search:
            search_term = search.lower()
            filtered_users = []
            for user in all_users:
                # Check if search term matches any of the searchable fields
                if (user.username and search_term in user.username.lower()) or \
                   (user.email and search_term in user.email.lower()) or \
                   (user.first_name and search_term in user.first_name.lower()) or \
                   (user.last_name and search_term in user.last_name.lower()):
                    filtered_users.append(user)
            all_users = filtered_users
        
        # Apply pagination if parameters are provided
        if skip is not None:
            all_users = all_users[skip:]
        
        if first is not None:
            all_users = all_users[:first]
        
        return [UserType.from_neomodel(user) for user in all_users]


    @login_required
    def resolve_user_by_id(self, info, user_id):
        """
        Retrieves a specific user by their ID.
        
        Fetches user information by user ID for administrative or
        internal system purposes.
        
        Args:
            info: GraphQL resolve info context
            user_id: Target user's ID to retrieve
        
        Returns:
            UserType: User object if found, None otherwise
        
        Raises:
            GraphQLError: If user is not authenticated
        
        Note:
            - Requires login authentication
            - Returns None if user doesn't exist instead of raising error
        """
        try:
            user = Users.nodes.get(user_id=user_id)
            return UserType.from_neomodel(user)
        except Users.DoesNotExist:
            return None
    
  
    @login_required
    @superuser_required
    def resolve_all_profiles(self, info, **kwargs):
        """
        Retrieves all user profiles in the system (Administrative).
        
        Returns a complete list of all user profiles for administrative
        purposes. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info context
            **kwargs: Additional keyword arguments
        
        Returns:
            List[ProfileType]: List of all profile objects
        
        Raises:
            GraphQLError: If user is not authenticated or not a superuser
        
        Note:
            - Requires login authentication and superuser privileges
            - Administrative API not used by frontend
            - Returns all profiles without filtering
        """
        return [ProfileType.from_neomodel(profile) for profile in Profile.nodes.all()]

       
    all_onboarding = graphene.List(OnboardingStatusType)
    @superuser_required
    @login_required
    def resolve_all_onboarding(self, info, **kwargs):
        """
        Retrieves all onboarding status records (Administrative).
        
        Returns a complete list of all onboarding status records for
        administrative monitoring and analysis.
        
        Args:
            info: GraphQL resolve info context
            **kwargs: Additional keyword arguments
        
        Returns:
            List[OnboardingStatusType]: List of all onboarding status objects
        
        Raises:
            GraphQLError: If user is not authenticated or not a superuser
        
        Note:
            - Requires login authentication and superuser privileges
            - Administrative API for monitoring onboarding progress
        """
        return [OnboardingStatusType.from_neomodel(x) for x in OnboardingStatus.nodes.all()]

   
    profileonboarding_by_uid = graphene.List(OnboardingStatusType, user_uid=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_profileonboarding_by_uid(self, info, user_uid):
        """
        Retrieves onboarding status for a specific user by their UID.
        
        Fetches onboarding progress and completion status for a target user,
        used for administrative monitoring or support purposes.
        
        Args:
            info: GraphQL resolve info context
            user_uid (str): Target user's UID to retrieve onboarding for (required)
        
        Returns:
            List[OnboardingStatusType]: List of onboarding status objects for the specified user
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Uses error handling decorator
            - Returns all onboarding records for the target user
        """
        user_node = Users.nodes.get(uid=user_uid)
        
        profile_node=user_node.profile.single()
        all_onboarding = list(profile_node.onboarding)
        return [OnboardingStatusType.from_neomodel(onboarding) for onboarding in all_onboarding]
    
             
    all_contact_info = graphene.List(ContactInfoType)
    @login_required
    @superuser_required
    def resolve_all_contact_info(self, info, **kwargs):
        """
        Retrieves all contact information records (Administrative).
        
        Returns a complete list of all contact information for administrative
        purposes. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info context
            **kwargs: Additional keyword arguments
        
        Returns:
            List[ContactInfoType]: List of all contact info objects
        
        Raises:
            GraphQLError: If user is not authenticated or not a superuser
        
        Note:
            - Requires login authentication and superuser privileges
            - Administrative API for contact data management
        """
        return [ContactInfoType.from_neomodel(x) for x in ContactInfo.nodes.all()]

   
    contactinfo_by_uid = graphene.List(ContactInfoType, user_uid=graphene.String(required=True))
    @login_required
    def resolve_contactinfo_by_uid(self, info, user_uid):
        """
        Retrieves contact information for a specific user by their UID.
        
        Fetches contact details for a target user, used for viewing
        another user's contact information.
        
        Args:
            info: GraphQL resolve info context
            user_uid (str): Target user's UID to retrieve contact info for (required)
        
        Returns:
            List[ContactInfoType]: List of contact info objects for the specified user
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Returns all contact information for the target user
        """
        user_node = Users.nodes.get(uid=user_uid)
        profile_node = user_node.profile.single()
        all_contact_info = list(profile_node.contactinfo)
        return [ContactInfoType.from_neomodel(contact_info) for contact_info in all_contact_info]

   
    my_contact_info = graphene.List(ContactInfoType)

    @login_required
    def resolve_my_contact_info(self, info):
        """
        Retrieves contact information for the authenticated user.
        
        Returns the current user's contact details including phone numbers,
        email addresses, and other contact methods.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[ContactInfoType]: List of contact info objects for the authenticated user
        
        Raises:
            Exception: If user or profile not found, or database error
        
        Note:
            - Requires login authentication
            - Includes additional exception handling
            - Returns all contact information for the current user
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            profile_node = user_node.profile.single()
            my_contact_info = list(profile_node.contactinfo)
            return [ContactInfoType.from_neomodel(x) for x in my_contact_info]
        except Exception as e:
            raise Exception(e)

   
    all_score = graphene.List(ScoreType)
    @superuser_required
    def resolve_all_score(self, info, **kwargs):
        """
        Retrieves all score records (Administrative).
        
        Returns a complete list of all user scores for administrative
        analysis and monitoring. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info context
            **kwargs: Additional keyword arguments
        
        Returns:
            List[ScoreType]: List of all score objects
        
        Raises:
            GraphQLError: If user is not a superuser
        
        Note:
            - Requires superuser privileges
            - Administrative API for score data analysis
        """
        return [ScoreType.from_neomodel(x) for x in Score.nodes.all()]

    
    all_interest = graphene.List(InterestType)
    @superuser_required
    def resolve_all_interest(self, info, **kwargs):
        """
        Retrieves all interest records (Administrative).
        
        Returns a complete list of all user interests for administrative
        analysis and monitoring. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info context
            **kwargs: Additional keyword arguments
        
        Returns:
            List[InterestType]: List of all interest objects
        
        Raises:
            GraphQLError: If user is not a superuser
        
        Note:
            - Requires superuser privileges
            - Administrative API for interest data analysis
        """
        return [InterestType.from_neomodel(x) for x in Interest.nodes.all()]

                  
    all_achievement=graphene.List(AchievementType)
    @login_required
    @superuser_required
    def resolve_all_achievement(self, info, **kwargs):
        """
        Retrieves all achievement records (Administrative).
        
        Returns a complete list of all user achievements for administrative
        analysis and monitoring. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info context
            **kwargs: Additional keyword arguments
        
        Returns:
            List[AchievementType]: List of all achievement objects
        
        Raises:
            GraphQLError: If user is not authenticated or not a superuser
        
        Note:
            - Requires login authentication and superuser privileges
            - Administrative API for achievement data analysis
        """
        return [AchievementType.from_neomodel(achievement) for achievement in Achievement.nodes.all()]

   
          
    all_education = graphene.List(EducationType)
    
    @login_required
    @superuser_required
    def resolve_all_education(self, info, **kwargs):
        """
        Retrieves all education records (Administrative).
        
        Returns a complete list of all user education records for administrative
        analysis and monitoring. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info context
            **kwargs: Additional keyword arguments
        
        Returns:
            List[EducationType]: List of all education objects
        
        Raises:
            GraphQLError: If user is not authenticated or not a superuser
        
        Note:
            - Requires login authentication and superuser privileges
            - Administrative API for education data analysis
        """
        return [EducationType.from_neomodel(education) for education in Education.nodes.all()]

           
    all_skill = graphene.List(SkillType)
    
    @login_required
    @superuser_required
    def resolve_all_skill(self, info, **kwargs):
        """
        Retrieves all skill records (Administrative).
        
        Returns a complete list of all user skills for administrative
        analysis and monitoring. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info context
            **kwargs: Additional keyword arguments
        
        Returns:
            List[SkillType]: List of all skill objects
        
        Raises:
            GraphQLError: If user is not authenticated or not a superuser
        
        Note:
            - Requires login authentication and superuser privileges
            - Administrative API for skill data analysis
        """
        return [SkillType.from_neomodel(skill) for skill in Skill.nodes.all()]

            
    all_experience = graphene.List(ExperienceType)
    
    @login_required
    @superuser_required
    def resolve_all_experience(self, info, **kwargs):
        """
        Retrieves all experience records (Administrative).
        
        Returns a complete list of all user experience records for administrative
        analysis and monitoring. Requires superuser privileges.
        
        Args:
            info: GraphQL resolve info context
            **kwargs: Additional keyword arguments
        
        Returns:
            List[ExperienceType]: List of all experience objects
        
        Raises:
            GraphQLError: If user is not authenticated or not a superuser
        
        Note:
            - Requires login authentication and superuser privileges
            - Administrative API for experience data analysis
        """
        return [ExperienceType.from_neomodel(experience) for experience in Experience.nodes.all()]
   
        
    users_back_profile_by_user_uid = graphene.List(UsersReviewType, uid=graphene.String(required=True))
    all_back_profile = graphene.List(UsersReviewType)

    @login_required
    def resolve_users_back_profile_by_user_uid(self, info, uid):
        """
        Retrieves back profile reviews for a specific user by their UID.
        
        Fetches all reviews and feedback given to a target user,
        used for viewing another user's reputation and reviews.
        
        Args:
            info: GraphQL resolve info context
            uid (str): Target user's UID to retrieve reviews for (required)
        
        Returns:
            List[UsersReviewType]: List of review objects for the specified user
            None: If user or reviews not found
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Returns all reviews for the target user
            - Includes exception handling for missing reviews
        """
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')
            user_node=Users.nodes.get(uid=uid)
            
            users_review = user_node.user_review.all()
            # print(users_review)
            return [UsersReviewType.from_neomodel(review) for review in users_review]
        except UsersReview.DoesNotExist:
            return None

      
    @login_required
    def resolve_all_back_profile(self, info):
        """
        Retrieves all back profile reviews (Administrative).
        
        Returns a complete list of all user reviews for administrative
        monitoring and analysis purposes.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[UsersReviewType]: List of all review objects
        
        Raises:
            GraphQLError: If user not authenticated or database error
        
        Note:
            - Requires login authentication
            - Administrative API for review data analysis
        """
        return [UsersReviewType.from_neomodel(review) for review in UsersReview.nodes.all()]
    
    my_back_profile=graphene.List(UsersReviewType)
    
    @login_required
    def resolve_my_back_profile(self,info):
        """
        Retrieves back profile reviews for the authenticated user.
        
        Returns all reviews and feedback received by the current user,
        allowing them to view their reputation and ratings.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[UsersReviewType]: List of review objects for the authenticated user
        
        Raises:
            Exception: If user not found or database error
        
        Note:
            - Requires login authentication
            - Includes additional exception handling
            - Returns all reviews received by the current user
        """
        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)

        try:
            
            my_reviews=list(user_node.user_review.all())

            return [UsersReviewType.from_neomodel(x) for x in my_reviews]
        except Exception as e:
            raise Exception(e)

     
    my_connection_list_user = graphene.Field(graphene.List(UserType))
    
    def resolve_my_connection_list_user(self, info):
        """
        Retrieves users from the authenticated user's uploaded contact list.
        
        Matches uploaded contacts with existing users in the system,
        returning users who have phone numbers in the contact list.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[UserType]: List of users matching uploaded contacts
            None: If user is anonymous or no contacts uploaded
        
        Raises:
            Exception: If contact upload not found or database error
        
        Note:
            - No explicit authentication decorator (checks anonymous status)
            - Uses Neo4j Cypher query for contact matching
            - Matches users by phone number from uploaded contacts
        """
        user = info.context.user
        if user.is_anonymous:
            return None
       
        upload_contact = UploadContact.objects.get(user=user)
        contact_list = upload_contact.contact
        # print(contact_list)
        payload = info.context.payload
        user_id = payload.get('user_id')
            
            

        query = """
                MATCH (u:Users)-[:HAS_PROFILE]->(p:Profile)
                WHERE p.phone_number IN $contact
                RETURN u
            """
        results, meta = db.cypher_query(query, {"contact": contact_list})
            
        suggested_user = [Users.inflate(row[0]) for row in results]
        users = [UserType.from_neomodel(user) for user in suggested_user]
        return users


     
    my_uploaded_Contact = graphene.Field(UploadContactType)
    
    def resolve_my_uploaded_Contact(self, info):
        """
        Retrieves the authenticated user's uploaded contact information.
        
        Returns the contact upload record for the current user,
        containing their uploaded contact list data.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            UploadContactType: User's uploaded contact data
            None: If user is anonymous or no contacts uploaded
        
        Raises:
            None: Handles DoesNotExist exception gracefully
        
        Note:
            - No explicit authentication decorator (checks anonymous status)
            - Includes exception handling for missing contact uploads
            - Returns Django model instance directly
        """
        user = info.context.user
        if user.is_anonymous:
            return None
        try:
            upload_contact = UploadContact.objects.get(user=user)
            return upload_contact
        except UploadContact.DoesNotExist:
            return None

   
    my_invitation_list_user = graphene.Field(InviteListType)
    
   
    @login_required
    def resolve_my_invitation_list_user(self, info):
        """
        Retrieves contacts that can be invited (not yet on the platform).
        
        Compares the user's uploaded contact list with existing users
        to identify contacts who haven't joined the platform yet.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            InviteListType: List of contacts available for invitation
        
        Raises:
            Exception: If contact upload not found or database error
        
        Note:
            - Requires login authentication
            - Uses Neo4j Cypher query to find existing contacts
            - Returns contacts not found in the user database
        """
        user = info.context.user
        upload_contact = UploadContact.objects.get(user=user)
        contact_list = upload_contact.contact
        
        query = """
            UNWIND $contact as contact
            MATCH (u:Users)-[:HAS_PROFILE]->(p:Profile)
            WHERE p.phone_number = contact
            RETURN contact as existing_contact
        """
        
        # results, meta = db.cypher_query(query, {"contact": contact_list})
        
        existing_contacts, meta = db.cypher_query(query, {"contact": contact_list})
        existing_contacts = [row[0] for row in existing_contacts]

        unavailable_contacts = [contact for contact in contact_list if contact not in existing_contacts]
        
        # suggested_user = [Users.inflate(row[0]) for row in results]
        # users = [UserType.from_neomodel(user) for user in suggested_user]
        return InviteListType.from_neomodel(unavailable_contacts)
    

   
    user_reviews = graphene.List(CustomUserReviewType, user_uid=graphene.String(required=True))
    @login_required
    def resolve_user_reviews(self, info, user_uid):
        """
        Retrieves aggregated review statistics for a specific user.
        
        Processes all reviews for a user and groups them by reaction type,
        calculating statistics like count, average vibe, and vibe distribution.
        
        Args:
            info: GraphQL resolve info context
            user_uid (str): Target user's UID to retrieve review stats for (required)
        
        Returns:
            List[CustomUserReviewType]: Aggregated review statistics by reaction type
        
        Raises:
            GraphQLError: If user not found or database error
        
        Note:
            - Requires login authentication
            - Groups reviews by reaction type (e.g., 'positive', 'negative')
            - Calculates vibe range distribution and averages
            - Returns custom aggregated review objects
        """
        # Initialize an empty list to store the user reviews
        user_reviews = []

        # Retrieve the user by UID
        user = Users.nodes.get(uid=user_uid)
        
        # Get all reviews associated with the user
        reviews = list(user.user_review.all())
        
        # Find all distinct reactions for the user's reviews
        reactions = list(set(review.reaction for review in reviews))

        # Loop through each distinct reaction and process the reviews associated with it
        for reaction in reactions:
            # Initialize vibe range count for the current reaction
            vibe_range_count = {
                'lessthen1': 0,
                'lessthen2': 0,
                'lessthen3': 0,
                'lessthen4': 0,
                'lessthen5': 0,
            }

            # Filter reviews by reaction
            reaction_reviews = [review for review in reviews if review.reaction == reaction]

            # Calculate vibe range count for the current reaction
            total_vibe = 0
            for review in reaction_reviews:
                vibe = review.vibe
                total_vibe += vibe
                if vibe < 1:
                    vibe_range_count['lessthen1'] += 1
                elif vibe < 2:
                    vibe_range_count['lessthen2'] += 1
                elif vibe < 3:
                    vibe_range_count['lessthen3'] += 1
                elif vibe < 4:
                    vibe_range_count['lessthen4'] += 1
                elif vibe < 5:
                    vibe_range_count['lessthen5'] += 1

            # Calculate average vibe
            average_vibe = total_vibe / len(reaction_reviews) if reaction_reviews else 0

            # Append the processed reaction data to the user_reviews list
            user_reviews.append(CustomUserReviewType(
                reaction=reaction,
                count=len(reaction_reviews),
                average_vibe=average_vibe,
                vibe_range_count=VibeRangeCountType(**vibe_range_count),
                
            ))

        return user_reviews
    

    get_all_states = graphene.List(StateType)
    get_cities_by_state = graphene.List(CityType, state_id=graphene.Int(required=True))

    def resolve_get_all_states(self, info):
        """
        Retrieves all available states.
        
        Returns a complete list of all states for location selection
        and geographic filtering purposes.
        
        Args:
            info: GraphQL resolve info context
        
        Returns:
            List[StateType]: List of all state objects
        
        Note:
            - No authentication required (public data)
            - Returns Django model instances directly
        """
        return StateInfo.objects.all()

    def resolve_get_cities_by_state(self, info, state_id):
        """
        Retrieves cities for a specific state.
        
        Returns all cities belonging to the specified state,
        used for location selection and filtering.
        
        Args:
            info: GraphQL resolve info context
            state_id (int): State ID to retrieve cities for (required)
        
        Returns:
            List[CityType]: List of city objects for the specified state
        
        Note:
            - No authentication required (public data)
            - Filters cities by state relationship
        """
        return CityInfo.objects.filter(state_id=state_id)
    
    experience_by_uid = graphene.List(ExperienceType, experience_uid=graphene.String(required=True))

    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_experience_by_uid(self, info, experience_uid):
        """
        Retrieves a specific experience record by its UID.
        
        Fetches detailed information about a single experience entry
        using its unique identifier.
        
        Args:
            info: GraphQL resolve info context
            experience_uid (str): Experience UID to retrieve (required)
        
        Returns:
            List[ExperienceType]: Single experience object in list format
        
        Raises:
            GraphQLError: If experience not found or database error
        
        Note:
            - Requires login authentication
            - Includes error handling decorator
            - Returns single object wrapped in list
        """
        experience_data = Experience.nodes.get(uid=experience_uid)
        return [ExperienceType.from_neomodel(experience_data)]
    
    achievement_by_uid = graphene.List(AchievementType, achievement_uid=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_achievement_by_uid(self, info, achievement_uid):
        """
        Retrieves a specific achievement record by its UID.
        
        Fetches detailed information about a single achievement entry
        using its unique identifier.
        
        Args:
            info: GraphQL resolve info context
            achievement_uid (str): Achievement UID to retrieve (required)
        
        Returns:
            List[AchievementType]: Single achievement object in list format
        
        Raises:
            GraphQLError: If achievement not found or database error
        
        Note:
            - Requires login authentication
            - Includes error handling decorator
            - Returns single object wrapped in list
            - Includes debug print statement
        """
        achievement_data = Achievement.nodes.get(uid=achievement_uid)
        print(achievement_data.uid)
        return [AchievementType.from_neomodel(achievement_data)] 
    
    
    
    education_by_uid = graphene.List(EducationType, education_uid=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_education_by_uid(self, info, education_uid):
        """
        Retrieves a specific education record by its UID.
        
        Fetches detailed information about a single education entry
        using its unique identifier.
        
        Args:
            info: GraphQL resolve info context
            education_uid (str): Education UID to retrieve (required)
        
        Returns:
            List[EducationType]: Single education object in list format
        
        Raises:
            GraphQLError: If education not found or database error
        
        Note:
            - Requires login authentication
            - Includes error handling decorator
            - Returns single object wrapped in list
        """
        education_data = Education.nodes.get(uid=education_uid)
        return [EducationType.from_neomodel(education_data)] 
    
    
  

    skill_by_uid = graphene.List(SkillType, skill_uid=graphene.String(required=True))

    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_skill_by_uid(self, info, skill_uid):
        """
        Retrieves a specific skill record by its UID.
        
        Fetches detailed information about a single skill entry
        using its unique identifier.
        
        Args:
            info: GraphQL resolve info context
            skill_uid (str): Skill UID to retrieve (required)
        
        Returns:
            List[SkillType]: Single skill object in list format
        
        Raises:
            GraphQLError: If skill not found or database error
        
        Note:
            - Requires login authentication
            - Includes error handling decorator
            - Returns single object wrapped in list
        """
        skill_data = Skill.nodes.get(uid=skill_uid)
        return [SkillType.from_neomodel(skill_data)]

    # Statistics query
    statistics = graphene.Field(StatisticsType)
    
    @login_required
    @superuser_required
    def resolve_statistics(self, info):
        """
        Retrieve platform statistics including total counts of users, communities, and posts.
        
        Args:
            info: GraphQL resolve info
            
        Returns:
            StatisticsType: Object containing total counts
            
        Note:
            - Requires login authentication and superuser privileges
            - Returns aggregated counts from the database
        """
        return StatisticsType.get_statistics()




class QueryV2(graphene.ObjectType):
    """
    Version 2 of the GraphQL Query class.
    
    Provides enhanced query resolvers and additional functionality
    for the GraphQL API, including invite management and user queries.
    
    Note:
        - Inherits from graphene.ObjectType
        - Includes both new resolvers and inherited ones from Query class
        - Provides versioned API functionality
    """

    all_users = graphene.List(UserInfoType)
    
    @login_required
    def resolve_all_users(self, info, **kwargs):
        """
        Retrieves all users with enhanced user information (V2).
        
        Returns a limited list of users with extended user information
        for administrative and discovery purposes.
        
        Args:
            info: GraphQL resolve info context
            **kwargs: Additional keyword arguments
        
        Returns:
            List[UserInfoType]: List of enhanced user info objects (limited to 50)
        
        Raises:
            GraphQLError: If user not authenticated
        
        Note:
            - Requires login authentication
            - Returns enhanced UserInfoType instead of basic UserType
            - Limited to first 50 users for performance
        """
        # print(info.context.user)
        return [UserInfoType.from_neomodel(user) for user in Users.nodes.all()[:50]]

    get_invitee_details = graphene.Field(GetInviteDetails, invite_token=graphene.String(required=True))

    def resolve_get_invitee_details(self, info, invite_token):
        """
        Retrieves invite details using an invite token.
        
        Validates and returns information about an invitation,
        including expiry status and invite validity.
        
        Args:
            info: GraphQL resolve info context
            invite_token (str): Invitation token to validate (required)
        
        Returns:
            GetInviteDetails: Object containing invite info, success status, and message
        
        Raises:
            GraphQLError: If invite token is invalid
        
        Note:
            - No authentication required (public invite validation)
            - Checks invite existence, deletion status, and expiry
            - Returns structured response with success/error information
        """
        try:
            # Check if the invite exists
            invite = Invite.objects.filter(invite_token=invite_token, is_deleted=False).first()

            if not invite:
                raise GraphQLError("Invalid invite token")

            # Check if the invite is expired
            if invite.expiry_date < timezone.now():
                return GetInviteDetails(
                    invite=None,
                    success=False,
                    message="This invite link has expired."
                )

            # Return invite details if valid
            return GetInviteDetails(
                invite=invite,
                success=True,
                message="Invite details retrieved successfully."
            )

        except Exception as error:
            return GetInviteDetails(
                invite=None,
                success=False,
                message=str(error)
            )
        

    search_matrix_username = Query.search_matrix_username
    resolve_search_matrix_username = Query.resolve_search_matrix_username

    welcome_messages = Query.welcome_messages
    resolve_welcome_messages = Query.resolve_welcome_messages

    back_profile_vibe_list_by_user_uid = Query.back_profile_vibe_list_by_user_uid
    resolve_back_profile_vibe_list_by_user_uid = Query.resolve_back_profile_vibe_list_by_user_uid

    interest_lists = Query.interest_lists
    resolve_interest_lists = Query.resolve_interest_lists

    
    my_onboarding = Query.my_onboarding
    resolve_my_onboarding = Query.resolve_my_onboarding



    profile_data_comment_by_uid = graphene.List(
        ProfileDataCommentTypeV2, 
        profiledata_type=ProfiledataTypeEnum(required=True), 
        uid=graphene.String(required=True)
    )

    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_profile_data_comment_by_uid(self, info, profiledata_type, uid):
        category_mapping = {
            ProfiledataTypeEnum.SKILL: "Skill",
            ProfiledataTypeEnum.EXPERIENCE: "Experience",
            ProfiledataTypeEnum.EDUCATION: "Education",
            ProfiledataTypeEnum.ACHIEVEMENT: "Achievement",
        }

        relationship_mapping = {
            ProfiledataTypeEnum.SKILL: "HAS_SKILL",
            ProfiledataTypeEnum.EXPERIENCE: "HAS_EXPERIENCE",
            ProfiledataTypeEnum.EDUCATION: "HAS_EDUCATION",
            ProfiledataTypeEnum.ACHIEVEMENT: "HAS_ACHIEVEMENT",
        }

        category = category_mapping.get(profiledata_type)
        relationship = relationship_mapping.get(profiledata_type)
        
        if not category or not relationship:
            raise GraphQLError("Invalid profiledata_type", extensions={"code": "NOT_FOUND", "status_code": 400}, path=["profile_data_comment_by_uid"])

        # Use the query from profile_details_query module
        query = profile_details_query.get_profile_data_comments_query(relationship, category)
        
        results, _ = db.cypher_query(query, {"uid": uid})
        
        if not results:
            raise GraphQLError(f"No data found for the provided UID: {uid}", extensions={"code": "NOT_FOUND", "status_code": 400}, path=["profile_data_comment_by_uid"])
        
        return [
            ProfileDataCommentTypeV2.from_neomodel(row[0], row[1], row[2])
            for row in results if row
        ]
        

    profile_data_vibes_by_uid = graphene.List(
        ProfileDataReactionType, 
        profiledata_type=ProfiledataTypeEnum(required=True), 
        uid=graphene.String(required=True)
    )

    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_profile_data_vibes_by_uid(self, info, profiledata_type, uid):
        model_mapping = {
            ProfiledataTypeEnum.SKILL: Skill,
            ProfiledataTypeEnum.EXPERIENCE: Experience,
            ProfiledataTypeEnum.EDUCATION: Education,  # Assuming you have an EducationV2 model
            ProfiledataTypeEnum.ACHIEVEMENT: Achievement,  # Assuming you have an AchievementV2 model
        }

        model = model_mapping.get(profiledata_type)
        if not model:
            raise ValueError("Invalid profiledata_type")

        profile_data = model.nodes.get(uid=uid)
        vibe_node = profile_data.like.all()
        vibe_detail = vibe_node[:10]
        vibes = list(vibe_detail)

        return [ProfileDataReactionType.from_neomodel(vibe) for vibe in vibes]
    
    
    profile_data_vibes_analytics_by_uid = graphene.List(
        ProfileDataVibeListType, 
        profiledata_type=ProfiledataTypeEnum(required=True), 
        uid=graphene.String(required=True)
    )

    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_profile_data_vibes_analytics_by_uid(self, info, profiledata_type, uid):
        category_mapping = {
            ProfiledataTypeEnum.SKILL: "skill" ,
            ProfiledataTypeEnum.EXPERIENCE: "experience",
            ProfiledataTypeEnum.EDUCATION: "education",  
            ProfiledataTypeEnum.ACHIEVEMENT: "achievement",  
        }

        category = category_mapping.get(profiledata_type)
        if not category:
            raise GraphQLError("Invalid profiledata_type")
        
        model_mapping = {
            ProfiledataTypeEnum.SKILL: Skill,
            ProfiledataTypeEnum.EXPERIENCE: Experience,
            ProfiledataTypeEnum.EDUCATION: Education,  # Assuming you have an EducationV2 model
            ProfiledataTypeEnum.ACHIEVEMENT: Achievement,  # Assuming you have an AchievementV2 model
        }

        model = model_mapping.get(profiledata_type)
        if not model:
            raise ValueError("Invalid profiledata_type")

        profile_data = model.nodes.get(uid=uid)
        
        return ProfileDataVibeListType.from_neomodel(uid,category)
    
    

    profile_by_user_id = graphene.Field(UserProfileDataType, user_id=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_profile_by_user_id(self, info, user_id):
            
            profile = Profile.nodes.get(user_id=user_id)
            payload = info.context.payload
            # print(info.context)
            user_id = payload.get('user_id')
            user_node=Users.nodes.get(user_id=user_id)
            return UserProfileDataType.from_neomodel(profile)

    my_profile = graphene.Field(UserProfileDataType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_profile(self, info):
            payload = info.context.payload
            user_id = payload.get('user_id')
        
            profile = Profile.nodes.get(user_id=user_id)
            user_node=Users.nodes.get(user_id=user_id)
            
            return UserProfileDataType.from_neomodel(profile)
    

    get_states_by_country = graphene.List(StateType, country_id=graphene.Int(required=True))
    get_all_states = graphene.List(StateType)
    get_cities_by_state = graphene.List(CityType, state_id=graphene.Int(required=True))

    def resolve_get_states_by_country(self, info, country_id):
        return StateInfo.objects.filter(country_id=country_id)

    def resolve_get_all_states(self, info):
        return StateInfo.objects.all()

    def resolve_get_cities_by_state(self, info, state_id):
        return CityInfo.objects.filter(state_id=state_id)
    
    get_mutual_connections = graphene.List(UserType, user_id=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_get_mutual_connections(self, info, user_id):
        payload = info.context.payload
        logged_in_user_id = payload.get('user_id')

        # Corrected Cypher query to find mutual connections
        query = """
        MATCH (u1:Users {user_id: $user_id1})-[:HAS_CONNECTION]->(c1:ConnectionV2)-[:HAS_RECIEVED_CONNECTION]->(mutual:Users)
        MATCH (u2:Users {user_id: $user_id2})-[:HAS_CONNECTION]->(c2:ConnectionV2)-[:HAS_RECIEVED_CONNECTION]->(mutual)
        WHERE c1.connection_status = 'Accepted' AND c2.connection_status = 'Accepted'
        RETURN mutual
        """
        params = {
            "user_id1": logged_in_user_id,
            "user_id2": user_id
        }

        results, _ = db.cypher_query(query, params)
        mutual_connections = [Users.inflate(row[0]) for row in results]
        
        return [UserType.from_neomodel(user) for user in mutual_connections]
        
        
    
