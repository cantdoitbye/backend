# autm_manager/graphql/mutations.py
import asyncio
from enum import Enum
import graphene
from graphene import Mutation
from graphql import GraphQLError
from graphene_django import DjangoObjectType


from auth_manager.Utils.otp_generator import generate_otp

from auth_manager.services import send_otp,feedback
from msg.graphql.types import MatrixProfileType
from .types import *

from auth_manager.models import *
from django.contrib.auth.models import User
from django.db.models import Q
import re

from .inputs import *
from .messages import UserMessages                    

from graphql_jwt.shortcuts import create_refresh_token, get_token
from graphql_jwt.shortcuts import get_user_by_token
from neomodel import db
from graphql_jwt.decorators import login_required,superuser_required
from django.contrib.auth import authenticate

from auth_manager.validators.rules import user_validations,validate_dob,string_validation
from .messages import UserMessages,ErrorMessages

from django.utils import timezone
from django.contrib.auth.models import update_last_login,User

from auth_manager.Utils.generate_username_suggestions import generate_username_suggestions
from auth_manager.enums.otp_purpose_enum import OtpPurposeEnum
from graphene import Enum as GrapheneEnum

from graphql_jwt.refresh_token.models import RefreshToken
from msg.models import MatrixProfile

from msg.utils import login_user_on_matrix,update_matrix_profile

from auth_manager.Utils.generate_presigned_url import get_valid_image
from auth_manager.Utils.auth_manager_decorator import handle_graphql_auth_manager_errors
from connection.models import ConnectionV2,CircleV2
from auth_manager.services.email_template import generate_payload 

from auth_manager.redis import *

class UploadContactType(DjangoObjectType):
    class Meta:
        model = UploadContact

class OTPType(DjangoObjectType):
    class Meta:
        model = OTP


class InviteType(DjangoObjectType):
    class Meta:
        model = Invite
        fields = "__all__"

class OTPPurpose(GrapheneEnum):
    FORGET_PASSWORD = OtpPurposeEnum.FORGET_PASSWORD.value
    EMAIL_VERIFICATION = OtpPurposeEnum.EMAIL_VERIFICATION.value
    OTHER = OtpPurposeEnum.OTHER.value

class CreateUser(Mutation):
    user = graphene.Field(UserType)
    token = graphene.String()
    refresh_token = graphene.String()
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input=CreateUserInput(required=True)

    
    def mutate(self, info,input):
        try:
            email = input.get('email')
            password=input.get('password')
            user_type = input.get("user_type", "personal")
            user_validations.validate_create_user_inputs(email=email,password=password)
            # Check if user exists in SQLite
            if User.objects.filter(email=email).exists():
                raise GraphQLError('User with this username or email already exists')
            
            if Users.nodes.get_or_none(email=email):
                raise GraphQLError(f"User with email {email} already exists in Neo4j")

            user=User.objects.create(
                username=email,
                email=email,
            )
            user.set_password(password)
            user.save()
            token = get_token(user)
            refresh_token = create_refresh_token(user)
            user_node =Users.nodes.get(user_id=str(user.id))
            user_node.user_type = user_type
            user_node.save()
            user=UserType.from_neomodel(user_node)


            return CreateUser(user=user, token=token,refresh_token =refresh_token,success=True,message=UserMessages.ACCOUNT_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateUser(user=None, success=False,message=message)


class CreateProfile(Mutation):
    profile = graphene.Field(ProfileType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        
        input=CreateProfileInput()

    @login_required
    @superuser_required
    def mutate(self, info, input):
    
        payload = info.context.payload
        user_id = payload.get('user_id')
        
        try:
            # Fetch the user from Neo4j
            user = Users.nodes.get(user_id=user_id)
            # Check if the user already has a profile
            existing_profile = user.profile.single()
            if existing_profile:
                return CreateProfile(
                    profile=ProfileType.from_neomodel(existing_profile),
                    success=False,
                    message=UserMessages.PROFILE_EXIST
                )
            # Create the profile
            profile = Profile(
                user_id=user_id,
                gender=input.get('gender'),
                device_id=input.get('device_id'),
                fcm_token=input.get('fcm_token'),
                bio=input.get('bio'),
                designation=input.get('designation'),
                worksat=input.get('worksat'),
                phone_number=input.get('phone_number'),
                born=input.get('born'),
                school=input.get('school'),
                college=input.get('college'),
                lives_in=input.get('lives_in'),
                profile_pic_id=input.get('profile_pic_id'),
                professional_life=input.get('professional_life'),
                last_email_otp=input.get('last_email_otp'),
                last_phone_otp=input.get('last_phone_otp'),
                email_otp_expaire=input.get('email_otp_expaire'),
                phone_otp_expaire=input.get('phone_otp_expaire'),
                ai_commenting=input.get('ai_commenting'),
                username_updated=input.get('username_updated'),
                cover_image_id=input.get('cover_image_id')
            )

            # Save the profile
            profile.save()

            # Create relationship between user and profile
            profile.user.connect(user)
            user.profile.connect(profile)  # Ensure two-way connection

            return CreateProfile(profile=ProfileType.from_neomodel(profile), success=True, message=UserMessages.PROFILE_CREATED)

        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateProfile(profile=None, success=False,message=message)
        

#Create a mutations to update user
#create a mutations to update profile




class UpdateUserProfile(graphene.Mutation):
    # user = graphene.Field(UserType)
    profile = graphene.Field(ProfileType)
    success=graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=UpdateProfileInput()

    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info,  input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("User not found")

            payload = info.context.payload
            user_id = payload.get('user_id')
            username=user.username
          # Retrieve the Profile object
       
            profile_node = Profile.nodes.get(user_id=user_id)
            onboarding_status=profile_node.onboarding.single()
            
           


        # Update user fields
            user=User.objects.get(username=username)

          

            if first_name := input.get('first_name'):
                user.first_name = first_name
                onboarding_status.first_name_set = True


            if last_name := input.get('last_name'):
                user.last_name = last_name
                onboarding_status.last_name_set = True
       

        # Update profile fields
            if 'device_id' in input:
                profile_node.device_id = input['device_id']


            if gender := input.get('gender'):
                profile_node.gender = gender
                onboarding_status.gender_set = True

            if 'fcm_token' in input:
                profile_node.fcm_token = input['fcm_token']

            if bio := input.get("bio"):
                profile_node.bio = bio
                onboarding_status.bio_set = True
            
            if state := input.get('state'):
                profile_node.state = state
                onboarding_status.state_set = True

            if city := input.get('city'):
                profile_node.city = city
                onboarding_status.city_set = True

            if designation := input.get('designation'):
                profile_node.designation = designation
                
            if phone_number := input.get('phone_number'):
                profile_node.phone_number = phone_number

            if (born := input.get("born")) and validate_dob.validate_dob(born):
                profile_node.born = born

            if (dob := input.get("dob")) and validate_dob.validate_dob(dob):
                profile_node.dob = dob

            if 'lives_in' in input:
                profile_node.lives_in = input['lives_in']
                
            if 'profile_pic_id' in input:
                get_valid_image(input['profile_pic_id'])
                profile_node.profile_pic_id = input['profile_pic_id']

            if 'cover_image_id' in input:
                get_valid_image(input['cover_image_id'])
                profile_node.cover_image_id = input['cover_image_id']

            # Save the updated user and profile
            user.save()
            profile_node.save()
            onboarding_status.save()
            profile=ProfileType.from_neomodel(profile_node)
            return UpdateUserProfile(profile=profile,success=True,message=UserMessages.PROFILE_UPDATED) 
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return UpdateUserProfile(profile=None,success=False,message=message)

#Delete user 
# Define external functions for user deactivation and deletion
def deactivate_user(user):
    if hasattr(user, 'is_active'):
        try:
            user.is_active = False
            user.save()
           
        except Exception as e:
            
            raise e
    else:
        raise AttributeError("User does not have is_active attribute")

def delete_user(user):
    try:
        with db.transaction:
            profile = user.profile.single()
            if profile:
                profile.delete()
            else:
                print("No profile found for user")
            user.delete()
            print("User deleted successfully")
    except Exception as e:
        print("Error deleting user or profile:", e)
        raise e

class DeleteUserAccount(graphene.Mutation):
    class Arguments:
        input=DeleteUserAccountInput()

    success = graphene.Boolean()
    message=graphene.String()

    @login_required
    @superuser_required
    def mutate(self, info, input):
        try:
            user = Users.nodes.get(username=input.username)
            if user.is_anonymous:
                raise GraphQLError ("User not found")

            if input.deleteType == 'deactivation':
                deactivate_user(user)
            elif input.deleteType == 'delete':
                delete_user(user)
            else:
                return DeleteUserAccount(success=True,message='Invalid deleteType. Use "deactivation" or "delete"')
               
            return DeleteUserAccount(success=True,message=UserMessages.ACCOUNT_DEACTIVATED)
        except Exception as error:
            return DeleteUserAccount(success=False,message = getattr(error, 'message', str(error)))

#Delete Profile 
class DeleteUserProfile(graphene.Mutation):
    class Arguments:
        input=DeleteUserProfileInput()

    success = graphene.Boolean()
    message=graphene.String()
    @login_required
    @superuser_required
    def mutate(self, info, input):
        # Start a Neo4j transaction
        with db.transaction:
            try:
                # Find the user node by username
                
                
                user=info.context.user
                if user.is_anonymous:
                    raise GraphQLError ("User not found")

                user_node = Users.nodes.get(username=input.username)
                # Find the profile node by user relationship

                profile = Profile.nodes.get(user_id=user_node.user_id)
                profile.delete()

                return DeleteUserProfile(success=True,message=UserMessages.DELETE_USER_PROFILE)
            except Exception as error:
                message = getattr(error, 'message', str(error))
                return DeleteUserProfile(success=False,message=message)
#Login 
        #username or email,password 
        #Return AuthToken and Refresh Toekn 
#Logout 
    # Return True 

class LoginUsingUsernameEmail(graphene.Mutation):
    user = graphene.Field(UserType)
    token = graphene.String()
    refresh_token = graphene.String()
    success = graphene.Boolean()
    message=graphene.String()
    chat_available = graphene.Boolean()
    matrix_profile = graphene.Field(MatrixProfileType)

    class Arguments:
        input=LoginInput()

    def mutate(self, info, input):
        # print("Login............")
        try:
            usernameEmail=input.usernameEmail
            password=input.password
            device_id=input.device_id

            user = User.objects.filter(Q(username=usernameEmail) | Q(email=usernameEmail)).first()
            
            if not user:
                return LoginUsingUsernameEmail(success=False, message="User not found", user=None, token=None, refresh_token=None)
            is_authenticate = authenticate(user_id=user.id, password=password)

            if not is_authenticate:
                return LoginUsingUsernameEmail(success=False, message="Please provide correct credentials", user=None, token=None, refresh_token=None)
            
            token = get_token(user)
            refresh_token = create_refresh_token(user)
            user.last_login = timezone.now()
            user.save()
            update_last_login(None, user)

            # Store device_id in profile if provided
            if device_id:
                try:
                    user_node = Users.nodes.get(user_id=user.id)
                    profile = user_node.profile.single()
                    if profile:
                        profile.device_id = device_id
                        profile.save()
                        print(f"Device ID {device_id} stored for user {user.username}")
                    else:
                        print(f"No profile found for user {user.username}")
                except Exception as e:
                    print(f"Error storing device_id: {str(e)}")

           # log in to Matrix to retrieve access token
            chat_available = False
            try:
                # Get or create Matrix profile first
                matrix_profile, created = MatrixProfile.objects.get_or_create(user=user)
                
                # Check if we already have a valid access token
                if matrix_profile.access_token and matrix_profile.matrix_user_id:
                    chat_available = True
                else:
                    # Try to login or register
                    matrix_access_user = asyncio.run(login_user_on_matrix(user.username, user.username))
                    chat_available = matrix_access_user[0] is not None

                    # Update Matrix profile with access token
                    matrix_profile.access_token = matrix_access_user[0]
                    matrix_profile.pending_matrix_registration = not chat_available
                    matrix_profile.matrix_user_id = matrix_access_user[1]
                    matrix_profile.save()

            except Exception as e:
                print(f"Matrix login error: {e}")
                # Don't fail the whole login if Matrix fails
                chat_available = False

            user_node=Users.nodes.get(user_id=user.id)
            user=UserType.from_neomodel(user_node)

            return LoginUsingUsernameEmail(user=user, token=token,refresh_token=refresh_token,success=True,message=UserMessages.LOGIN_SUCCESS,chat_available=chat_available, matrix_profile=matrix_profile)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return LoginUsingUsernameEmail(user=None,success=False,message=message, matrix_profile=None)
        
class Logout(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    @login_required
    def mutate(self, info):
        try:
            token = info.context.headers.get('Authorization')
            if token:
                token = token.split(' ')[1]  # Remove the 'Bearer ' prefix
                user = get_user_by_token(token)
                
                if user:
                    # Remove device_id from user's profile
                    try:
                        user_node = Users.nodes.get(user_id=user.id)
                        profile = user_node.profile.single()
                        if profile and profile.device_id:
                            profile.device_id = None
                            profile.save()
                    except Exception as e:
                        print(f"Error removing device_id during logout: {str(e)}")
                        # Don't fail logout if device_id removal fails
                    
                    return Logout(success=True , message=UserMessages.LOGOUT_SUCCESS)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return Logout(success=False,message=message)




class SearchUsername(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)

    suggested_usernames = graphene.List(graphene.String)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    def mutate(self, info, username, email=None):
        try:
            user=info.context.user
            email=user.email
            string_validation.validate_username(username)
            existing_user = Users.nodes.get_or_none(username=username)
            
            if not existing_user:
                return SearchUsername(suggested_usernames=[username], success=True, message="Username is available")
            # # Suggest alternative usernames
            existing_usernames = [user.username for user in Users.nodes.filter(username__icontains=username)[:50] ]
            suggestions=generate_username_suggestions(base_username=username, email=email,existing_usernames=existing_usernames)

            return SearchUsername(suggestions, success=False, message="Username is not available")
    
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return SearchUsername(success=False, message=message)

          

class SelectUsername(Mutation):
    user = graphene.Field(UserType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input=SelectUsernameInput()

    @login_required
    def mutate(self, info,input):
        try:
            payload = info.context.payload
            user_id = payload.get('user_id')
            string_validation.validate_username(username=input.username)
            # Check if the username already exists
            if Users.nodes.get_or_none(username=input.username):
                raise GraphQLError("Username already taken. Please choose a different username.")

            user = Users.nodes.get(user_id=user_id)
            user.username = input.username
            user.save()
            matrix_profile = MatrixProfile.objects.get(user=user_id)

            if matrix_profile:
                matrix_user_id = matrix_profile.matrix_user_id
                access_token = matrix_profile.access_token
                if matrix_user_id and access_token:
                    asyncio.run(update_matrix_profile(access_token=access_token, user_id=matrix_user_id, display_name=input.username))
                else:
                    pass
            else:
                pass


            onboarding_status=user.profile.single().onboarding.single()
            onboarding_status.username_selected=True
            onboarding_status.save()

            return SelectUsername(user=UserType.from_neomodel(user), success=True, message=UserMessages.USERNAME_SELECTED)
        except Exception as error:
            message=getattr(error,'message',str(error))
            return SelectUsername(user=None,success=False,message=message)


class CreateOnboardingStatus(Mutation):
    onboarding_status = graphene.Field(OnboardingStatusType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=OnboardingInput()

    @login_required
    @superuser_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            profile = Profile.nodes.get(uid=input.profile_uid)
            onboarding_status = OnboardingStatus(
                email_verified=input.get('email_verified', False),
                phone_verified=input.get('phone_verified', False),
                username_selected=input.get('username_selected', False),
                first_name_set=input.get('first_name_set', False),
                last_name_set=input.get('last_name_set', False),
                gender_set=input.get('gender_set', False),
                bio_set=input.get('bio_set', False)
            )
            onboarding_status.save()
            onboarding_status.profile.connect(profile)
            profile.onboarding.connect(onboarding_status)
            return CreateOnboardingStatus(onboarding_status=OnboardingStatusType.from_neomodel(onboarding_status), success=True,message=UserMessages.CREATE_ONBOARDING_STATUS)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateOnboardingStatus(onboarding_status=None, success=False,message=message)


class UpdateOnboardingStatus(Mutation):
    onboarding_status = graphene.Field(OnboardingStatusType)
    success = graphene.Boolean()
    message=graphene.String()
    class Arguments:
        input=UpdateOnboardingInput()
        
    @login_required
    @superuser_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            onboarding_status = OnboardingStatus.nodes.get(uid=input.uid)

            for key, value in input.items():
                setattr(onboarding_status, key, value)

            onboarding_status.save()
            return UpdateOnboardingStatus(onboarding_status=OnboardingStatusType.from_neomodel(onboarding_status), success=True,message=UserMessages.UPDATE_ONBOARDING_STATUS)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateOnboardingStatus(onboarding_status=None, success=False,message=message)

class CreateContactInfo(Mutation):
    contact_info = graphene.Field(ContactInfoType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=ContactinfoInput()

    @login_required
    @superuser_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
            
          # Retrieve the Profile object
       
            profile = Profile.nodes.get(user_id=user_id)
            # profile = Profile.nodes.get(uid=input.profile_uid)
            contact_info = ContactInfo(
                type=input.type,
                value=input.value,
                platform=input.get('platform'),
                link=input.get('link')
            )
            contact_info.save()
            contact_info.profile.connect(profile)
            profile.contactinfo.connect(contact_info)
            return CreateContactInfo(contact_info=ContactInfoType.from_neomodel(contact_info), success=True,message=UserMessages.CREATE_CONTACT_INFO)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateContactInfo(contact_info=None, success=False,message=message)

class UpdateContactInfo(Mutation):
    contact_info = graphene.Field(ContactInfoType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=UpdateContactinfoInput()

    @login_required
    @superuser_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            contact_info = ContactInfo.nodes.get(uid=input.uid)
            

            for key, value in input.items():
                setattr(contact_info, key, value)

            contact_info.save()
            return UpdateContactInfo(contact_info=ContactInfoType.from_neomodel(contact_info), success=True,message=UserMessages.UPDATE_CONTACT_INFO)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateContactInfo(contact_info=None, success=False,message=message)

class DeleteContactInfo(Mutation):
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=DeleteInput()

    @login_required
    @superuser_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            contact_info = ContactInfo.nodes.get(uid=input.uid)
            contact_info.delete()
            return DeleteContactInfo(success=True,message=UserMessages.DELETE_CONTACT_INFO)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteContactInfo(success=False,message=message)

class CreateScore(Mutation):
    score = graphene.Field(ScoreType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
       input=ScoreInput()

    @login_required
    @superuser_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            profile = Profile.nodes.get(uid=input.profile_uid)
            score = Score(
                vibers_count=input.get('vibers_count', 2.0),
                cumulative_vibescore=input.get('cumulative_vibescore', 2.0),
                intelligence_score=input.get('intelligence_score', 2.0),
                appeal_score=input.get('appeal_score', 2.0),
                social_score=input.get('social_score', 2.0),
                human_score=input.get('human_score', 2.0),
                repo_score=input.get('repo_score', 2.0),
            )
            score.save()
            score.profile.connect(profile)
            profile.score.connect(score)
            return CreateScore(score=ScoreType.from_neomodel(score), success=True,message=UserMessages.CREATE_SCORE)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateScore(score=None, success=False,message=message)

class UpdateScore(Mutation):
    score = graphene.Field(ScoreType)
    success = graphene.Boolean()
    message=graphene.String() 

    class Arguments:
        input=UpdateScoreInput()
     
    @login_required
    @superuser_required 
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            score = Score.nodes.get(uid=input.uid)

            for key, value in input.items():
                setattr(score, key, value)

            score.save()

            return UpdateScore(score=ScoreType.from_neomodel(score), success=True,message=UserMessages.UPDATE_SCORE)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateScore(score=None, success=False,message=message)

class DeleteScore(Mutation):
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=DeleteInput()
        
    @login_required
    @superuser_required
    def mutate(self, info, input):
       
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            score = Score.nodes.get(uid=input.uid)
            score.delete()
            return DeleteScore(success=True,message=UserMessages.DELETE_SCORE)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteScore(success=False,message=message)

class CreateInterest(Mutation):
    interest = graphene.Field(InterestType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=InerestInput()

    @login_required
    @handle_graphql_auth_manager_errors
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            payload = info.context.payload
            user_id = payload.get('user_id')
          # Retrieve the Profile object
       
            profile = Profile.nodes.get(user_id=user_id)
            # profile = Profile.nodes.get(uid=input.profile_uid)
            interest = Interest(
                names=input.get('names', [])
            )
            interest.save()
            interest.profile.connect(profile)
            profile.interest.connect(interest)
            return CreateInterest(interest=InterestType.from_neomodel(interest), success=True,message=UserMessages.CREATE_INTEREST)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateInterest(interest=None, success=False,message=message)

class UpdateInterest(Mutation):
    interest = graphene.Field(InterestType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=UpdateInterestInput()

    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info, input):
        
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            interest = Interest.nodes.get(uid=input.uid)

            if 'names' in input:
                interest.names = input['names']
            if 'is_deleted' in input:
                interest.is_deleted = input['is_deleted']

            interest.save()

            return UpdateInterest(interest=InterestType.from_neomodel(interest), success=True,message=UserMessages.UPDATE_INTEREST)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateInterest(interest=None, success=False,message=message)

class DeleteInterest(Mutation):
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=DeleteInput()
    
    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            interest = Interest.nodes.get(uid=input.uid)
            interest.is_deleted=True
            interest.save()

            return DeleteInterest(success=True,message=UserMessages.DELETE_INTEREST)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteInterest(success=False,message=message)
        
class SendOTP(graphene.Mutation):
    success = graphene.Boolean()
    message=graphene.String()
    
    class Arguments:
        email = graphene.String(required=True)
        purpose = OTPPurpose(required=True)
    # No Arguments required
    message=graphene.String()

    # @login_required
    def mutate(self, info,email,purpose):
        try:
            email=email
            user_id=None

            if purpose == OtpPurposeEnum.FORGET_PASSWORD.value:
                user = User.objects.filter(email=email).first()
                if  user is None:
                    raise GraphQLError(str(ErrorMessages.USER_NOT_FOUND))
                user_id=user.id

            elif purpose==OtpPurposeEnum.EMAIL_VERIFICATION.value:
                user = info.context.user
                if user.is_anonymous:
                    raise GraphQLError("Authentication credentials were not provided.")

                email = user.email
                user_id=user.id

            else:
                raise GraphQLError("Other type of otp is not supported.")

            
            otp_count = get_otp_count(user_id)
            print(otp_count)
            if otp_count >= 3:
                raise GraphQLError(str(ErrorMessages.OTP_REQUEST_LIMIT_EXCEEDED))

            # Generate OTP
            otp_code = generate_otp()

            store_otp(user_id, otp_code)

            # Increment OTP count with a 1-hour expiration
            # increment_otp_count(user_id)
            # Send OTP
            user = User.objects.get(id=user_id)
            OTP.objects.create(user=user, otp=otp_code,purpose=purpose)
            # email_utility.render_verification_email(user.first_name,otp_code,email)
            if purpose==OtpPurposeEnum.EMAIL_VERIFICATION.value:
                generate_payload.send_rendered_email(
                        api_url="http://50.28.84.70:32231/v1/mail/send-raw-html",
                        api_key="bf224b31-ffa7-5a40-8392-90307c2153dc",
                        first_name=user.first_name,
                        otp_code=otp_code,
                        user_email=email
                    )
            elif purpose==OtpPurposeEnum.FORGET_PASSWORD.value:
                 generate_payload.send_rendered_forget_email(
                        api_url="http://50.28.84.70:32231/v1/mail/send-raw-html",
                        api_key="bf224b31-ffa7-5a40-8392-90307c2153dc",
                        first_name=user.first_name,
                        otp_code=otp_code,
                        user_email=email
                    )

            # send_otp.send_otp_email(email, otp_code,purpose)
            return SendOTP(success=True,message=UserMessages.OTP_SUCCESS)
        
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return SendOTP(success=False,message=message)
    
class VerifyOTP(graphene.Mutation):
    class Arguments:
        input=VerifyOtpInput()

    success = graphene.Boolean()
    message=graphene.String()
    
    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info,input):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Authentication credentials were not provided.")
        email = user.email
        uid=user.username
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication credentials were not provided.")
            email = user.email
        
            user = User.objects.get(email=email)
            otp_instance = OTP.objects.filter(user=user, otp=input.otp).first()

            if otp_instance is None:
                raise GraphQLError('Invalid OTP')

            if otp_instance.is_expired():
                raise GraphQLError('OTP has expired')

            # OTP is valid
            user_node=Users.nodes.get(uid=uid)
            onboarding_status=user_node.profile.single().onboarding.single()
            onboarding_status.email_verified=True
            onboarding_status.save()

            otp_instance.delete()
            return VerifyOTP(success=True,message=UserMessages.VERIFY_OTP)
        
        except Exception as error:
            message=getattr(error , "message", str(error))
            return VerifyOTP(success=False,message=message)   


class VerifyOTPAndResetPassword(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    token = graphene.String()
    refresh_token = graphene.String()

    class Arguments:
        email = graphene.String(required=True)
        otp = graphene.String(required=True)
        new_password = graphene.String(required=True)

    # @login_required
    def mutate(self, info, email, otp, new_password):
        token = None
        refresh_token = None
        try:
            user = User.objects.get(email=email)
            otp_instance = OTP.objects.filter(user=user, otp=otp).first()

            if otp_instance is None:
                raise GraphQLError('Invalid OTP')

            if otp_instance.is_expired():
                raise GraphQLError('OTP has expired')

            # OTP is valid
            user.set_password(new_password)
            user.save()

            token = get_token(user)
            refresh_token = create_refresh_token(user)

            otp_instance.delete()
            return VerifyOTPAndResetPassword(success=True,token=token,refresh_token=refresh_token, message="Password has been reset successfully.")
        
        except User.DoesNotExist:
            raise GraphQLError('User not found')
        except Exception as error:
            message=getattr(error,'message',str(error))
            return VerifyOTPAndResetPassword(success=False, token=token,refresh_token=refresh_token,message=message)





class DeleteAchievement(Mutation):
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=DeleteInput()

    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            achievement = Achievement.nodes.get(uid=input.uid)
            achievement.is_deleted=True
            achievement.save()

            return DeleteAchievement(success=True,message=UserMessages.DELETE_ACHIEVEMENT)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteAchievement(success=False,message=message)
        

class DeleteEducation(Mutation):
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=DeleteInput()
    
    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            education = Education.nodes.get(uid=input.uid)
            education.is_deleted=True
            education.save()

            return DeleteEducation(success=True,message=UserMessages.DELETE_EDUCATION)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteEducation(success=False,message=message)


class DeleteSkill(Mutation):
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=DeleteInput()
    
    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            skill = Skill.nodes.get(uid=input.uid)
            skill.is_deleted=True
            skill.save()

            return DeleteSkill(success=True,message=UserMessages.DELETE_SKILL)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteSkill(success=False,message=message)


class DeleteExperience(Mutation):
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
        input=DeleteInput()
    
    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
            experience = Experience.nodes.get(uid=input.uid)
            experience.is_deleted=True
            experience.save()

            return DeleteExperience(success=True,message=UserMessages.DELETE_EXPERIENCE)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteExperience(success=False,message=message)



class CreateUsersReview(graphene.Mutation):
    # users_review = graphene.Field(UsersReviewType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateUsersReviewInput(required=True)
    
    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
                
            payload = info.context.payload
            user_id = payload.get('user_id')
            byuser = Users.nodes.get(user_id=user_id)
            touser = Users.nodes.get(uid=input.touser_uid)
            profile=touser.profile.single()

            try:
                profile_reaction_manager = ProfileReactionManager.objects.get(profile_uid=profile.uid)
            except ProfileReactionManager.DoesNotExist:
                # If no PostReactionManager exists, create and initialize with first 10 vibes
                profile_reaction_manager = ProfileReactionManager(profile_uid=profile.uid)
                profile_reaction_manager.initialize_reactions()  # Add the 10 vibes
                profile_reaction_manager.save()

            profile_reaction_manager.add_reaction(
                vibes_name=input.reaction,
                score=input.vibe  # Assuming `reaction` is a numeric score to be averaged
            )
            profile_reaction_manager.save()

            users_review = UsersReview(
                reaction=input.reaction,
                vibe=input.vibe,
                title=input.title,
                content=input.content,
                file_id=input.file_id
            )
            users_review.save()
            users_review.byuser.connect(byuser)
            users_review.touser.connect(touser)
            touser.user_review.connect(users_review)

            return CreateUsersReview( success=True, message="Users Review created successfully.")
        except Exception as error:
            message=getattr(error , "message", str(error))
            return CreateUsersReview(success=False, message=message)


class DeleteUsersReview(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = DeleteUsersReviewInput(required=True)

    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info, input):
        try:
            users_review = UsersReview.nodes.get(uid=input.uid)
            users_review.delete()

            return DeleteUsersReview(success=True, message="Users Review deleted successfully.")
        except Exception as error:
            message=getattr(error , "message", str(error))
            return DeleteUsersReview(success=False, message=message)







class CreateUploadContact(graphene.Mutation):
    class Arguments:
        contact = graphene.List(graphene.String, required=True)
    
    upload_contact = graphene.Field(UploadContactType)
    success = graphene.Boolean()
    message = graphene.String()
    
    @superuser_required
    def mutate(self, info, contact):
        try:
            user = info.context.user  # Gets the currently logged-in user
            if user.is_anonymous:
                raise Exception("Authentication required")

            # Check if the user has already uploaded contacts
            existing_upload = UploadContact.objects.filter(user=user).first()
            if existing_upload:
                return CreateUploadContact(success=False, message="You have already uploaded contacts.")
            
            for item in contact:
                if len(item) != 10:
                    return CreateUploadContact(success=False,message="Each contact in the contact field must have exactly 10 characters.")

            upload_contact = UploadContact.objects.create(user=user, contact=contact)
            return CreateUploadContact(upload_contact=upload_contact, success=True, message="Contacts uploaded successfully.")
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateUploadContact(success=False, message=message)



class UpdateUploadContact(graphene.Mutation):
    
    class Arguments:
        contact = graphene.List(graphene.String)
        is_deleted = graphene.Boolean()
    
    upload_contact = graphene.Field(UploadContactType)
    success = graphene.Boolean()
    message = graphene.String()
    
    @superuser_required
    def mutate(self, info, contact=None, is_deleted=None):
        try:
            user = info.context.user
            # Retrieve the UploadContact object for the given user_id
            upload_contact = UploadContact.objects.get(user=user)
            # Update the contact list if provided
            if contact is not None:
                upload_contact.contact = contact

            # Update the is_deleted flag if provided
            if is_deleted is not None:
                upload_contact.is_deleted = is_deleted

            for item in contact:
                if len(item) != 10:
                    return CreateUploadContact(success=False,message="Each contact in the contact field must have exactly 10 characters.")
            # Save the changes to the database
            upload_contact.save()

            # Return the updated UploadContact object
            return UpdateUploadContact(upload_contact=upload_contact,success=True, message="Contacts updated successfully.")
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateUploadContact(success=False, message=message)



class DeleteUploadContact(graphene.Mutation):
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @superuser_required
    def mutate(self, info):
        try:
            user = info.context.user
            upload_contact = UploadContact.objects.get(user=user)
            upload_contact.delete()
            return DeleteUploadContact(success=True,message="Uploaded Contact deleted Successfully.")
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return DeleteUploadContact(success=False, message=message)



class SendFeedback(graphene.Mutation):
    success = graphene.Boolean()
    message=graphene.String()
    
    class Arguments:
        email = graphene.String(required=True)
        image_id=graphene.String(required=True)
        feedback_message=graphene.String(required=True)
        # purpose = OTPPurpose(required=True)
    # No Arguments required
    message=graphene.String()

    @login_required
    @superuser_required
    def mutate(self, info,email,image_id,feedback_message):
        try:
            email=email
            user_id=None

            # if purpose == OtpPurposeEnum.FORGET_PASSWORD.value:
            #     user = User.objects.filter(email=email).first()
            #     if  user is None:
            #         raise GraphQLError(str(ErrorMessages.USER_NOT_FOUND))
            #     user_id=user.id

            # elif purpose==OtpPurposeEnum.EMAIL_VERIFICATION.value:
            #     user = info.context.user
            #     if user.is_anonymous:
            #         raise GraphQLError("Authentication credentials were not provided.")

            #     email = user.email
            #     user_id=user.id

            # else:
            #     raise GraphQLError("Other type of otp is not supported.")

            # Generate OTP
            # otp_code = generate_otp()
            # Send OTP
            # user = User.objects.get(id=user_id)
            # OTP.objects.create(user=user, otp=otp_code,purpose=purpose)
            image_url=generate_presigned_url.generate_presigned_url(image_id)
            feedback.send_feedback_email(email, image_url, feedback_message)
            return SendFeedback(success=True,message="Mail send successfully")
        
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return SendFeedback(success=False,message=message)



class CreateBackProfileReview(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateBackProfileReviewInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("Authentication Failure")
                
            payload = info.context.payload
            user_id = payload.get('user_id')
            byuser = Users.nodes.get(user_id=user_id)
            touser = Users.nodes.get(uid=input.touser_uid)
            profile=touser.profile.single()

            try:
                profile_reaction_manager = BackProfileReactionManager.objects.get(profile_uid=profile.uid)
            except BackProfileReactionManager.DoesNotExist:
                # If no PostReactionManager exists, create and initialize with first 10 vibes
                profile_reaction_manager = BackProfileReactionManager(profile_uid=profile.uid)
                profile_reaction_manager.initialize_reactions()  # Add the 10 vibes
                profile_reaction_manager.save()

            profile_reaction_manager.add_reaction(
                vibes_name=input.reaction,
                score=input.vibe  # Assuming `reaction` is a numeric score to be averaged
            )
            profile_reaction_manager.save()

            users_review = BackProfileUsersReview(
                reaction=input.reaction,
                vibe=input.vibe,
                title=input.title,
                content=input.content,
                file_id=input.file_id
            )
            users_review.save()
            users_review.byuser.connect(byuser)
            users_review.touser.connect(touser)
            touser.user_back_profile_review.connect(users_review)

            return CreateBackProfileReview( success=True, message="Users Review created successfully.")
        except Exception as error:
            message=getattr(error , "message", str(error))
            return CreateBackProfileReview(success=False, message=message)








class CreateInvite(graphene.Mutation):
    invite = graphene.Field(InviteType)
    invite_link=graphene.String()
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateInviteInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("User not found")

            payload = info.context.payload
            user_id = payload.get('user_id')
            
            user=info.context.user
            login_user = Users.nodes.get(user_id=user_id)
            

            # Validate origin_type
            if input.origin_type.value not in dict(Invite.OriginType.choices):
                raise GraphQLError("Invalid origin type provided")
            
            
            invite = Invite.objects.create(
                inviter=user,
                origin_type=input.origin_type.value,
            )

            invite_link = f"http://104.197.79.25:8001/login/invite/{invite.invite_token}"

            return CreateInvite(invite=invite, invite_link=invite_link,success=True, message="Invite created successfully")

        except Exception as error:
            return CreateInvite(invite=None, success=False, message=str(error))



class CreateUserV2(Mutation):
    # user = graphene.Field(UserType)
    token = graphene.String()
    refresh_token = graphene.String()
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input=CreateUserInputV2(required=True)

    
    def mutate(self, info,input):
        try:
            email = input.get('email')
            password=input.get('password')
            user_type = input.get("user_type", "personal")
            user_validations.validate_create_user_inputs(email=email,password=password)
            # Check if user exists in SQLite
            if User.objects.filter(email=email).exists():
                raise GraphQLError('User with this username or email already exists')
            
            if Users.nodes.get_or_none(email=email):
                raise GraphQLError(f"User with email {email} already exists in Neo4j")
            
            if input.invite_token:    
                invite = Invite.objects.filter(invite_token=input.invite_token, is_deleted=False).first()

                if not invite:
                    return CreateUserV2(
                        success=False,
                        message="Please provide a correct token."
                    )

                # Check if the invite is expired
                if invite.expiry_date < timezone.now():
                    return CreateUserV2(
                        success=False,
                        message="This invite link has expired."
                    )
                
                secondary_user=invite.inviter

                if not secondary_user:
                    return CreateUserV2(
                        success=False,
                        message="Please provide a correct token."
                    )


            user=User.objects.create(
                username=email,
                email=email,
            )
            user.set_password(password)
            user.save()
            token = get_token(user)
            refresh_token = create_refresh_token(user)
            user_node =Users.nodes.get(user_id=str(user.id))
            user_node.user_type = user_type
            user_node.save()
            user=UserType.from_neomodel(user_node)

           
            if input.invite_token:    
                invite = Invite.objects.filter(invite_token=input.invite_token, is_deleted=False).first()

            

                # Check if the invite is expired
                if invite.expiry_date < timezone.now():
                    return CreateUserV2(
                        user=None,
                        success=False,
                        message="This invite link has expired."
                    )
                
                secondary_user=invite.inviter
                secondary_user_node=Users.nodes.get(user_id=str(invite.inviter_id))

                connection = ConnectionV2(
                    connection_status="Accepted",
                )
                connection.save()
                connection.receiver.connect(secondary_user_node)
                connection.created_by.connect(user_node)
               
                user_node.connectionv2.connect(connection)
                
                secondary_user_node.connectionv2.connect(connection)
                

                circle_choice=CircleV2(
                    initial_sub_relation="friend",
                    initial_directionality="Unidirectional",
                    user_relations={
                        user_node.uid: {
                            "sub_relation": "friend",
                            "circle_type": "Outer",
                            "sub_relation_modification_count": 0
                        },
                        secondary_user_node.uid: {
                            "sub_relation": "Friend",
                            "circle_type": "Outer",
                            "sub_relation_modification_count": 0
                        }
                }
                    
                )
                circle_choice.save()
                connection.circle.connect(circle_choice)


            return CreateUserV2(token=token,refresh_token =refresh_token,success=True,message=UserMessages.ACCOUNT_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateUserV2(success=False,message=message)

class CreateProfileDataReactionV2(Mutation):
    like = graphene.Field(ProfileDataReactionType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateProfileDataReactionInputV2()  # Assuming input contains post_uid, reaction, vibe, and category.

    @handle_graphql_auth_manager_errors 
    @login_required
    def mutate(self, info, input):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Authentication Failure")

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            category = input.category.value.lower() if input.category else None  # Convert category to lowercase for consistency
            
            # print(category)
            if category in ["education", "achievement", "skill", "experience"]:
                reaction_manager_mapping = {
                    "education": EducationReactionManager,
                    "achievement": AchievementReactionManager,
                    "skill": SkillReactionManager,
                    "experience": ExperienceReactionManager,
                }

                # Determine the correct reaction manager class
                ReactionManagerClass = reaction_manager_mapping.get(category)
                # print(ReactionManagerClass)

                uid_field_mapping = {
                    "education": "education_uid",
                    "achievement": "achievement_uid",
                    "skill": "skill_uid",
                    "experience": "experience_uid",
                }
                
                uid_field = uid_field_mapping.get(category, "uid")

                try:
                    # print("Inside try clause")
                    profile_reaction_manager = ReactionManagerClass.objects.get(**{uid_field: input.uid})

                except ReactionManagerClass.DoesNotExist:
                    # print("Inside except clause")
                    profile_reaction_manager = ReactionManagerClass(**{uid_field: input.uid})
                    profile_reaction_manager.initialize_reactions()
                    profile_reaction_manager.save()
                # Handle reactions for ProfileDataReactionManager
                
                # print(profile_reaction_manager.achievement_vibe)
                profile_reaction_manager.add_reaction(
                    vibes_name=input.reaction,
                    score=input.vibe
                )
                profile_reaction_manager.save()

                # Create Like object and connect it to Post
                like = ProfileDataReaction(reaction=input.reaction, vibe=input.vibe)
                like.save()
                like.user.connect(user_node)

                # print(like.uid)

                if category == "education":
                    education_node=Education.nodes.get(uid=input.uid)
                    education_node.like.connect(like)
                    like.education.connect(education_node)

                elif category == "experience":
                    experience_node=Experience.nodes.get(uid=input.uid)
                    experience_node.like.connect(like)
                    like.experience.connect(experience_node)

                elif category == "achievement":
                    achievement_node=Achievement.nodes.get(uid=input.uid)
                    achievement_node.like.connect(like)
                    like.achievement.connect(achievement_node)

                elif category == "skill":
                    skill_node=Skill.nodes.get(uid=input.uid)
                    skill_node.like.connect(like)
                    like.skill.connect(skill_node)

                # post.like.connect(like)

                # increment_post_like_count(post.uid)

                return CreateProfileDataReactionV2(like=ProfileDataReactionType.from_neomodel(like), success=True, message=UserMessages.REACTION_CREATED)
            else:
                return CreateProfileDataReactionV2(like=None, success=False, message="Please Select category")

        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateProfileDataReactionV2(like=None, success=False, message=message)


class CreateProfileDataCommentV2(Mutation):
    comment_details = graphene.Field(ProfileDataCommentType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateProfileCommentInputV2()  # Assuming input contains post_uid, reaction, vibe, and category.

    @handle_graphql_auth_manager_errors 
    @login_required
    def mutate(self, info, input):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError("Authentication Failure")

        payload = info.context.payload
        user_id = payload.get('user_id')
        user_node = Users.nodes.get(user_id=user_id)

        try:
            category = input.category.value.lower() if input.category else None  # Convert category to lowercase for consistency
            
            # print(category)
            if category in ["education", "achievement", "skill", "experience"]:
                

                

                # Create Like object and connect it to Post
                comment_data = ProfileDataComment(content=input.content)
                comment_data.save()
                comment_data.user.connect(user_node)

                # print(like.uid)

                if category == "education":
                    education_node=Education.nodes.get(uid=input.uid)
                    education_node.comment.connect(comment_data)
                    comment_data.education.connect(education_node)

                elif category == "experience":
                    experience_node=Experience.nodes.get(uid=input.uid)
                    experience_node.comment.connect(comment_data)
                    comment_data.experience.connect(experience_node)

                elif category == "achievement":
                    achievement_node=Achievement.nodes.get(uid=input.uid)
                    achievement_node.comment.connect(comment_data)
                    comment_data.achievement.connect(achievement_node)

                elif category == "skill":
                    skill_node=Skill.nodes.get(uid=input.uid)
                    skill_node.comment.connect(comment_data)
                    comment_data.skill.connect(skill_node)

                # post.like.connect(like)

                # increment_post_like_count(post.uid)

                return CreateProfileDataCommentV2(comment_details=ProfileDataCommentType.from_neomodel(comment_data), success=True, message=UserMessages.COMMENT_CREATED)
            else:
                return CreateProfileDataCommentV2(comment_details=None, success=False, message=UserMessages.NO_CATEGORY)

        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateProfileDataCommentV2(comment_details=None, success=False, message=message)


class UpdateProfileDataCommentV2(Mutation):
    comment_details = graphene.Field(ProfileDataCommentType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = UpdateProfileCommentInputV2(required=True)
    
    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info, input):
        try:
            comment_data = ProfileDataComment.nodes.get(uid=input.uid)

            if input.content is not None:
                comment_data.content = input.content
            

            comment_data.save()

            return UpdateProfileDataCommentV2(comment_details=ProfileDataCommentType.from_neomodel(comment_data), success=True, message=UserMessages.COMMENT_UPDATED)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return  UpdateProfileDataCommentV2(comment_details=None, success=False, message=message)


class CreateAchievement(Mutation):
    achievement = graphene.Field(AchievementType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
       input=CreateAchievementInput()
    
    @handle_graphql_auth_manager_errors
    @login_required        
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("User not found")

            payload = info.context.payload
            user_id = payload.get('user_id')
            profile = Profile.nodes.get(user_id=user_id)
            
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            achievement = Achievement(
                what=input.get('what', ''),
                description=input.get('description', ''),
                from_source=input.get('from_source', ''),
                created_on =input.get('created_on', ''),
                file_id=input.get('file_id', []) if isinstance(input.get('file_id'), list) else None,
            )
            if 'from_date' in input and input['from_date'] is not None:
                achievement.from_date = input['from_date']
                
            if 'to_date' in input and input['to_date'] is not None:
                achievement.to_date = input['to_date']
            achievement.save()
            achievement.profile.connect(profile)
            profile.achievement.connect(achievement)

            


            return CreateAchievement(achievement=AchievementType.from_neomodel(achievement), success=True,message=UserMessages.CREATE_ACHIEVEMENT)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateAchievement(achievement=None, success=False,message=message)

class UpdateAchievement(Mutation):
    achievement = graphene.Field(AchievementType)
    success = graphene.Boolean()
    message=graphene.String()
    
    class Arguments:
        input=UpdateAchievementInput()

    @handle_graphql_auth_manager_errors    
    @login_required
    def mutate(self, info, input):
        try:
            
            
            achievement = Achievement.nodes.get(uid=input.uid)

            for key, value in input.items():
                setattr(achievement, key, value)

            achievement.save()
            return UpdateAchievement(achievement=AchievementType.from_neomodel(achievement), success=True,message=UserMessages.UPDATE_ACHIEVEMENT)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateAchievement(achievement=None, success=False,message=message)

class CreateEducation(Mutation):
    education = graphene.Field(EducationType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
       input=CreateEducationInput()
    
    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("User not found")

            payload = info.context.payload
            user_id = payload.get('user_id')
            
       
            profile = Profile.nodes.get(user_id=user_id)

            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            
            education = Education(
                    what=input.get('what', ''),
                    field_of_study=input.get('field_of_study', ''),
                    from_source=input.get('from_source', ''),
                    created_on =input.get('created_on', ''),
                    file_id=input.get('file_id', []) if isinstance(input.get('file_id'), list) else None,
                )
            
            if 'from_date' in input and input['from_date'] is not None:
                education.from_date = input['from_date']
                
            if 'to_date' in input and input['to_date'] is not None:
                education.to_date = input['to_date']
            education.save()
            education.profile.connect(profile)
            profile.education.connect(education)
            return CreateEducation(education=EducationType.from_neomodel(education), success=True,message=UserMessages.CREATE_EDUCATION)
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateEducation(education=None, success=False,message=message)

class UpdateEducation(Mutation):
    education = graphene.Field(EducationType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = UpdateEducationInput()

    @handle_graphql_auth_manager_errors    
    @login_required
    def mutate(self, info, input):
        try:
            education = Education.nodes.get(uid=input.uid)

            for key, value in input.items():
                setattr(education, key, value)

            education.save()
            return UpdateEducation(education=EducationType.from_neomodel(education), success=True, message=UserMessages.UPDATE_EDUCATION)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateEducation(education=None, success=False, message=message)



class CreateExperience(Mutation):
    experience = graphene.Field(ExperienceType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
       input=CreateExperienceInput()
    
    @handle_graphql_auth_manager_errors
    @login_required     
    def mutate(self, info,input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("User not found")

            payload = info.context.payload
            user_id = payload.get('user_id')
            
       
            profile = Profile.nodes.get(user_id=user_id)
            # profile = Profile.nodes.get(uid=input.profile_uid)
            
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            experience = Experience(
                what=input.get('what', ''),
                description=input.get('description', ''),
                created_on=input.get('created_on', ''),
                from_source=input.get('from_source', ''),
                file_id=input.get('file_id', []) if isinstance(input.get('file_id'), list) else None,
            )
            if 'from_date' in input and input['from_date'] is not None:
                experience.from_date = input['from_date']
                
            if 'to_date' in input and input['to_date'] is not None:
                experience.to_date = input['to_date']
            experience.save()
            experience.profile.connect(profile)
            profile.experience.connect(experience)
            return CreateExperience(experience=ExperienceType.from_neomodel(experience), success=True,message=UserMessages.CREATE_EXPERIENCE)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateExperience(experience=None, success=False,message=message)

class UpdateExperience(Mutation):
    experience = graphene.Field(ExperienceType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = UpdateExperienceInput()

    @handle_graphql_auth_manager_errors    
    @login_required
    def mutate(self, info, input):
        try:
            experience = Experience.nodes.get(uid=input.uid)

            for key, value in input.items():
                setattr(experience, key, value)

            experience.save()
            return UpdateExperience(experience=ExperienceType.from_neomodel(experience), success=True, message=UserMessages.UPDATE_EXPERIENCE)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateExperience(experience=None, success=False, message=message)




class CreateSkill(Mutation):
    skill = graphene.Field(SkillType)
    success = graphene.Boolean()
    message=graphene.String()

    class Arguments:
       input=CreateSkillInput()

    @handle_graphql_auth_manager_errors
    @login_required
    def mutate(self, info, input):
        try:
            user=info.context.user
            if user.is_anonymous:
                raise GraphQLError ("User not found")

            payload = info.context.payload
            user_id = payload.get('user_id')
            
       
            profile = Profile.nodes.get(user_id=user_id)
            
            
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            skill_data = {
                'what': input.get('what', ''),
                'from_source': input.get('from_source', ''),
                'file_id': input.get('file_id', []) if isinstance(input.get('file_id'), list) else None,
            }
            
            # Only add from_date and to_date if they are provided
            if 'from_date' in input and input['from_date'] is not None:
                skill_data['from_date'] = input['from_date']
                
            if 'to_date' in input and input['to_date'] is not None:
                skill_data['to_date'] = input['to_date']
                
            skill = Skill(**skill_data)
            skill.save()
            skill.profile.connect(profile)
            profile.skill.connect(skill)
            return CreateSkill(skill=SkillType.from_neomodel(skill), success=True,message=UserMessages.CREATE_SKILL)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateSkill(skill=None, success=False,message=message)

class UpdateSkill(Mutation):
    skill = graphene.Field(SkillType)
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        input = UpdateSkillInput()

    @handle_graphql_auth_manager_errors    
    @login_required
    def mutate(self, info, input):
        try:
            skill = Skill.nodes.get(uid=input.uid)

            for key, value in input.items():
                setattr(skill, key, value)

            skill.save()
            return UpdateSkill(skill=SkillType.from_neomodel(skill), success=True, message=UserMessages.UPDATE_SKILL)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateSkill(skill=None, success=False, message=message)





class Mutation(graphene.ObjectType):
    register_user = CreateUser.Field()
    register_userV2 = CreateUserV2.Field()
    login_by_username_email=LoginUsingUsernameEmail.Field()
    logout=Logout.Field()

    update_user_profile = UpdateUserProfile.Field()

    delete_user_account = DeleteUserAccount.Field()
    delete_user_profile = DeleteUserProfile.Field()
    select_username = SelectUsername.Field()

    Create_onboarding=CreateOnboardingStatus.Field()
    update_onboarding=UpdateOnboardingStatus.Field()
    add_contactinfo=CreateContactInfo.Field()
    edit_contactinfo=UpdateContactInfo.Field()
    delete_contactinfo=DeleteContactInfo.Field()
    add_score=CreateScore.Field()
    update_score=UpdateScore.Field()
    delete_score=DeleteScore.Field()
    add_interest=CreateInterest.Field()
    edit_interest=UpdateInterest.Field()
    delete_intrest=DeleteInterest.Field()


    update_achievement = UpdateAchievement.Field()
    update_education = UpdateEducation.Field()
    update_skill = UpdateSkill.Field()

    send_otp = SendOTP.Field()
    verify_otp = VerifyOTP.Field()
    search_username = SearchUsername.Field()
    verify_otp_and_reset_password = VerifyOTPAndResetPassword.Field()
    create_achievement=CreateAchievement.Field()
    create_skill=CreateSkill.Field()
    create_user_review=CreateUsersReview.Field()
    delete_user_review=DeleteUsersReview.Field()

    create_back_profile_review=CreateBackProfileReview.Field()

    create_upload_contact = CreateUploadContact.Field()
    update_upload_contact = UpdateUploadContact.Field()
    delete_upload_contact = DeleteUploadContact.Field()

    send_feedback=SendFeedback.Field()

    delete_education=DeleteEducation.Field()
    delete_achievement=DeleteAchievement.Field()
    delete_skill=DeleteSkill.Field()
    delete_experience=DeleteExperience.Field()

    send_invite=CreateInvite.Field()

    create_education=CreateEducation.Field()
    create_experience=CreateExperience.Field()

    update_experience=UpdateExperience.Field()


    create_profile_data_like=CreateProfileDataReactionV2.Field()
    create_profile_data_comment=CreateProfileDataCommentV2.Field()

class MutationV2(graphene.ObjectType):
    register_user = CreateUserV2.Field()
    login_by_username_email=LoginUsingUsernameEmail.Field()
    logout=Logout.Field()

    update_user_profile = UpdateUserProfile.Field()
    select_username = SelectUsername.Field()

    add_interest=CreateInterest.Field()
    edit_interest=UpdateInterest.Field()
    delete_intrest=DeleteInterest.Field()


    send_otp = SendOTP.Field()
    verify_otp = VerifyOTP.Field()
    search_username = SearchUsername.Field()
    verify_otp_and_reset_password = VerifyOTPAndResetPassword.Field()
    
    create_user_review=CreateUsersReview.Field()
    delete_user_review=DeleteUsersReview.Field()

    create_back_profile_review=CreateBackProfileReview.Field()

    send_invite=CreateInvite.Field()

    create_achievement=CreateAchievement.Field()
    create_education=CreateEducation.Field()
    create_experience=CreateExperience.Field()
    create_skill=CreateSkill.Field()

    update_achievement=UpdateAchievement.Field()
    update_education=UpdateEducation.Field()
    update_skill=UpdateSkill.Field()
    update_experience=UpdateExperience.Field()


    create_profile_data_like=CreateProfileDataReactionV2.Field()
    create_profile_data_comment=CreateProfileDataCommentV2.Field()

