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
    class Meta:
        model = StateInfo
        fields = ("id", "state_name")

class CityType(DjangoObjectType):
    class Meta:
        model = CityInfo
        fields = ("id", "city_name")

class InviteType(DjangoObjectType):
    class Meta:
        model = Invite
        fields = "__all__"

class GetInviteDetails(graphene.ObjectType):
    invite = graphene.Field(InviteType)
    success = graphene.Boolean()
    message = graphene.String()


class UploadContactType(DjangoObjectType):
    class Meta:
        model = UploadContact

class SubInterestType(graphene.ObjectType):
    id = graphene.Int(required=True)
    name = graphene.String(required=True)

class InterestListType(DjangoObjectType):
    sub_interests = graphene.List(SubInterestType)

    class Meta:
        model = InterestList
        fields = ("id", "name", "sub_interests")

    def resolve_sub_interests(self, info):
        # Check if sub_interests is in a correct format
        # Ensure self.sub_interests is a list
        if isinstance(self.sub_interests, list):
            return [
                SubInterestType(id=sub_interest['id'], name=sub_interest['name'])
                for sub_interest in self.sub_interests
            ]
        return []


class Query(graphene.ObjectType):

    all_users = graphene.List(UserType)
    
    @login_required
    def resolve_all_users(self, info, **kwargs):
        # print(info.context.user)
        return [UserType.from_neomodel(user) for user in Users.nodes.all()]

    search_matrix_username = graphene.Field(MatrixUserType, username=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_search_matrix_username(self, info, username):
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
        return WelcomeScreenMessage.objects.all()
    

    profile_by_user_id = graphene.Field(ProfileDetailsVibeType, user_id=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_profile_by_user_id(self, info, user_id):
            
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
        user_node = Users.nodes.get(uid=user_uid)
        profile_node = user_node.profile.single()
        all_scores = list(profile_node.score)
        return [ScoreType.from_neomodel(score) for score in all_scores]
    
   
    my_scores = graphene.List(ScoreType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_scores(self, info):
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
        user_node = Users.nodes.get(uid=user_uid)
        profile_node = user_node.profile.single()
        all_interests = list(profile_node.interest)
        return [InterestType.from_neomodel(interest) for interest in all_interests]
    
   
    my_interests = graphene.List(InterestType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_interests(self, info):
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
        user_node = Users.nodes.get(uid=user_uid)
        profile_node=user_node.profile.single()
        all_achievement = list(profile_node.achievement)
        return [AchievementType.from_neomodel(achievement) for achievement in all_achievement]
        
    my_achievement=graphene.List(AchievementType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_achievement(self,info):

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
        user_node = Users.nodes.get(uid=user_uid)
        profile_node=user_node.profile.single()
        all_education = list(profile_node.education)
        return [EducationType.from_neomodel(education) for education in all_education]

  
    my_education=graphene.List(EducationType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_education(self,info):

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
        user_node = Users.nodes.get(uid=user_uid)
        profile_node=user_node.profile.single()
        all_skill = list(profile_node.skill)
        return [SkillType.from_neomodel(skill) for skill in all_skill]
   
    my_skill=graphene.List(SkillType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_skill(self,info):

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
        user_node = Users.nodes.get(user_id=user_id)
        profile_node=user_node.profile.single()
        all_experience = list(profile_node.experience)
        return [ExperienceType.from_neomodel(experience) for experience in all_experience]

   
    my_experience=graphene.List(ExperienceType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_experience(self,info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)
        profile_node=user_node.profile.single()
        my_experience = list(profile_node.experience)
        my_experiences=[experience for experience in my_experience if not experience.is_deleted]
        return [ExperienceType.from_neomodel(x) for x in my_experiences]
        
        

    interest_lists = graphene.List(InterestListType)

    def resolve_interest_lists(self, info):
        return InterestList.objects.all()
    

    back_profile_vibe_list_by_user_uid = graphene.List(BackProfileListType, user_uid = graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_back_profile_vibe_list_by_user_uid(self, info, user_uid):
        
        user_node = Users.nodes.get(uid=user_uid)
        profile_uid=user_node.profile.single().uid
        return BackProfileListType.from_neomodel(profile_uid)
        
        

    my_back_profile_review=graphene.List(BackProfileReviewType)
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_my_back_profile_review(self,info):

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node=Users.nodes.get(user_id=user_id)    
        my_reviews=list(user_node.user_back_profile_review.all())
        return [BackProfileReviewType.from_neomodel(x) for x in my_reviews]
        
        

    back_profile_review_by_user_uid=graphene.List(BackProfileReviewType,user_uid = graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_back_profile_review_by_user_uid(self,info,user_uid):
        
        user_node=Users.nodes.get(uid=user_uid)   
        my_reviews=list(user_node.user_back_profile_review.all())
        return [BackProfileReviewType.from_neomodel(x) for x in my_reviews]
        
        

    back_profile_review_by_uid=graphene.List(BackProfileReviewType,uid = graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_back_profile_review_by_uid(self,info,uid):
        review_node=BackProfileUsersReview.nodes.get(uid=uid)
        return [BackProfileReviewType.from_neomodel(review_node)]
        
    

    # Below apis are not used by frontend
         
    @login_required
    @superuser_required
    def resolve_all_users(self, info, **kwargs):
        return [UserType.from_neomodel(user) for user in Users.nodes.all()]


    @login_required
    def resolve_user_by_id(self, info, user_id):
        try:
            user = Users.nodes.get(user_id=user_id)
            return UserType.from_neomodel(user)
        except Users.DoesNotExist:
            return None
    
  
    @login_required
    @superuser_required
    def resolve_all_profiles(self, info, **kwargs):
        return [ProfileType.from_neomodel(profile) for profile in Profile.nodes.all()]

       
    all_onboarding = graphene.List(OnboardingStatusType)
    @superuser_required
    @login_required
    def resolve_all_onboarding(self, info, **kwargs):
        return [OnboardingStatusType.from_neomodel(x) for x in OnboardingStatus.nodes.all()]

   
    profileonboarding_by_uid = graphene.List(OnboardingStatusType, user_uid=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_profileonboarding_by_uid(self, info, user_uid):
        user_node = Users.nodes.get(uid=user_uid)
        
        profile_node=user_node.profile.single()
        all_onboarding = list(profile_node.onboarding)
        return [OnboardingStatusType.from_neomodel(onboarding) for onboarding in all_onboarding]
    
             
    all_contact_info = graphene.List(ContactInfoType)
    @login_required
    @superuser_required
    def resolve_all_contact_info(self, info, **kwargs):
        return [ContactInfoType.from_neomodel(x) for x in ContactInfo.nodes.all()]

   
    contactinfo_by_uid = graphene.List(ContactInfoType, user_uid=graphene.String(required=True))
    @login_required
    def resolve_contactinfo_by_uid(self, info, user_uid):
        user_node = Users.nodes.get(uid=user_uid)
        profile_node = user_node.profile.single()
        all_contact_info = list(profile_node.contactinfo)
        return [ContactInfoType.from_neomodel(contact_info) for contact_info in all_contact_info]

   
    my_contact_info = graphene.List(ContactInfoType)

    @login_required
    def resolve_my_contact_info(self, info):
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
        return [ScoreType.from_neomodel(x) for x in Score.nodes.all()]

    
    all_interest = graphene.List(InterestType)
    @superuser_required
    def resolve_all_interest(self, info, **kwargs):
        return [InterestType.from_neomodel(x) for x in Interest.nodes.all()]

                  
    all_achievement=graphene.List(AchievementType)
    @login_required
    @superuser_required
    def resolve_all_achievement(self, info, **kwargs):
        return [AchievementType.from_neomodel(achievement) for achievement in Achievement.nodes.all()]

   
          
    all_education = graphene.List(EducationType)
    
    @login_required
    @superuser_required
    def resolve_all_education(self, info, **kwargs):
        return [EducationType.from_neomodel(education) for education in Education.nodes.all()]

           
    all_skill = graphene.List(SkillType)
    
    @login_required
    @superuser_required
    def resolve_all_skill(self, info, **kwargs):
        return [SkillType.from_neomodel(skill) for skill in Skill.nodes.all()]

            
    all_experience = graphene.List(ExperienceType)
    
    @login_required
    @superuser_required
    def resolve_all_experience(self, info, **kwargs):
        return [ExperienceType.from_neomodel(experience) for experience in Experience.nodes.all()]
   
        
    users_back_profile_by_user_uid = graphene.List(UsersReviewType, uid=graphene.String(required=True))
    all_back_profile = graphene.List(UsersReviewType)

    @login_required
    def resolve_users_back_profile_by_user_uid(self, info, uid):
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
        return [UsersReviewType.from_neomodel(review) for review in UsersReview.nodes.all()]
    
    my_back_profile=graphene.List(UsersReviewType)
    
    @login_required
    def resolve_my_back_profile(self,info):

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
        return StateInfo.objects.all()

    def resolve_get_cities_by_state(self, info, state_id):
        return CityInfo.objects.filter(state_id=state_id)
    
    experience_by_uid = graphene.List(ExperienceType, experience_uid=graphene.String(required=True))

    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_experience_by_uid(self, info, experience_uid):
        experience_data = Experience.nodes.get(uid=experience_uid)
        return [ExperienceType.from_neomodel(experience_data)]
    
    achievement_by_uid = graphene.List(AchievementType, achievement_uid=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_achievement_by_uid(self, info, achievement_uid):
        achievement_data = Achievement.nodes.get(uid=achievement_uid)
        print(achievement_data.uid)
        return [AchievementType.from_neomodel(achievement_data)] 
    
    
    
    education_by_uid = graphene.List(EducationType, education_uid=graphene.String(required=True))
    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_education_by_uid(self, info, education_uid):
        education_data = Education.nodes.get(uid=education_uid)
        return [EducationType.from_neomodel(education_data)] 
    
    
  

    skill_by_uid = graphene.List(SkillType, skill_uid=graphene.String(required=True))

    @handle_graphql_auth_manager_errors
    @login_required
    def resolve_skill_by_uid(self, info, skill_uid):
        skill_data = Skill.nodes.get(uid=skill_uid)
        return [SkillType.from_neomodel(skill_data)]




class QueryV2(graphene.ObjectType):

    all_users = graphene.List(UserInfoType)
    
    @login_required
    def resolve_all_users(self, info, **kwargs):
        # print(info.context.user)
        return [UserInfoType.from_neomodel(user) for user in Users.nodes.all()[:50]]

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
        
        
    
