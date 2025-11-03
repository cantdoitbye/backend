# autm_manager/graphql/mutations.py
import asyncio
from enum import Enum
import os
import graphene
from graphene import Mutation
from graphql import GraphQLError
from graphene_django import DjangoObjectType


from auth_manager.Utils.otp_generator import generate_otp
from auth_manager.Utils.phone_generator import generate_unique_indian_mobile, generate_unique_username, generate_realistic_indian_data

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

from auth_manager.validators.rules import user_validations,validate_dob,string_validation,skill_validation,education_validation,experience_validation
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
from auth_manager.Utils.matrix_avatar_manager import set_user_avatar_and_score
from auth_manager.redis import *
from vibe_manager.services.vibe_activity_service import VibeActivityService
import logging

logger = logging.getLogger(__name__)


class UploadContactType(DjangoObjectType):
    """
    GraphQL type for UploadContact model.
    
    Represents uploaded contact information in the GraphQL schema,
    providing access to contact data fields through GraphQL queries.
    
    Meta:
        model: UploadContact Django model
    """
    class Meta:
        model = UploadContact

class OTPType(DjangoObjectType):
    """
    GraphQL type for OTP (One-Time Password) model.
    
    Represents OTP records in the GraphQL schema, used for
    authentication and verification processes.
    
    Meta:
        model: OTP Django model
    """
    class Meta:
        model = OTP


class InviteType(DjangoObjectType):
    """
    GraphQL type for Invite model.
    
    Represents invitation records in the GraphQL schema,
    exposing all fields for invite management operations.
    
    Meta:
        model: Invite Django model
        fields: All model fields are exposed
    """
    class Meta:
        model = Invite
        fields = "__all__"

class OTPPurpose(GrapheneEnum):
    """
    GraphQL enum for OTP purpose types.
    
    Defines the different purposes for which OTPs can be generated,
    mapping to the underlying OtpPurposeEnum values.
    
    Values:
        FORGET_PASSWORD: OTP for password reset functionality
        EMAIL_VERIFICATION: OTP for email address verification
        OTHER: OTP for other miscellaneous purposes
    """
    FORGET_PASSWORD = OtpPurposeEnum.FORGET_PASSWORD.value
    EMAIL_VERIFICATION = OtpPurposeEnum.EMAIL_VERIFICATION.value
    OTHER = OtpPurposeEnum.OTHER.value

class CreateUser(Mutation):
    """
    Creates a new user account with authentication tokens.
    
    This mutation handles user registration by creating accounts in both
    Django's User model and Neo4j's Users node, then generates JWT tokens
    for immediate authentication.
    
    Args:
        input (CreateUserInput): User creation data containing:
            - email: User's email address (used as username)
            - password: User's password
            - user_type: Type of user account (defaults to "personal")
    
    Returns:
        CreateUser: Response containing:
            - user: Created user object from Neo4j
            - token: JWT access token
            - refresh_token: JWT refresh token
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user already exists in Django or Neo4j
        Exception: For validation errors or database issues
    
    Note:
        - Validates email and password before creation
        - Creates user in both Django (SQLite) and Neo4j databases
        - Automatically generates authentication tokens
        - Sets user_type in Neo4j node
    """
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
            invite_token = input.get('invite_token')
            is_bot = input.get('is_bot', False)
            persona = input.get('persona')

            user_validations.validate_create_user_inputs(email=email,password=password)
            # Check if user exists in SQLite
            if User.objects.filter(email=email).exists():
                raise GraphQLError('User with this username or email already exists')
            
            if Users.nodes.get_or_none(email=email):
                raise GraphQLError(f"User with email {email} already exists in Neo4j")
            invite = None
            secondary_user = None
            if invite_token:    
                invite = Invite.objects.filter(invite_token=invite_token, is_deleted=False).first()

                if not invite:
                    return CreateUser(
                        user=None,
                        token=None,
                        refresh_token=None,
                        success=False,
                        message="Please provide a correct token."
                    )

                # Check if the invite is expired
                if invite.expiry_date < timezone.now():
                    return CreateUser(
                        user=None,
                        token=None,
                        refresh_token=None,
                        success=False,
                        message="This invite link has expired."
                    )
                
                secondary_user = invite.inviter
                if not secondary_user:
                    return CreateUser(
                        user=None,
                        token=None,
                        refresh_token=None,
                        success=False,
                        message="Inviter not found."
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
            user_node.is_bot = is_bot
            if persona:
                user_node.persona = persona
            user_node.save()
            user=UserType.from_neomodel(user_node)

            # Process invite
            if invite and secondary_user:
                try:
                    secondary_user_node = Users.nodes.get(user_id=str(secondary_user.id))
                    
                    # Create connection between inviter and new user
                    connection = ConnectionV2(
                        connection_status="Accepted",
                    )
                    connection.save()
                    connection.receiver.connect(secondary_user_node)
                    connection.created_by.connect(user_node)
                   
                    user_node.connectionv2.connect(connection)
                    secondary_user_node.connectionv2.connect(connection)

                    # Create circle relationship
                    circle_choice = CircleV2(
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

                    invite.usage_count += 1
                    invite.last_used_timestamp = timezone.now()
                    invite.login_users.add(user)
                    invite.save()
                    
                except Exception as e:
                    # Log the error but don't fail the user creation
                    print(f"Error processing invite connection: {e}")


            return CreateUser(user=user, token=token,refresh_token =refresh_token,success=True,message=UserMessages.ACCOUNT_CREATED)
        except Exception as error:
            message=getattr(error , 'message' , str(error) )
            return CreateUser(user=None, success=False,message=message)


class CreateProfile(Mutation):
    """
    Creates a user profile with detailed personal information.
    
    This mutation creates a comprehensive user profile in Neo4j with
    personal, professional, and preference data. Requires superuser
    privileges and prevents duplicate profile creation.
    
    Args:
        input (CreateProfileInput): Profile data containing:
            - gender: User's gender
            - device_id: Device identifier
            - fcm_token: Firebase Cloud Messaging token
            - bio: User biography
            - designation: Job title/designation
            - worksat: Workplace information
            - phone_number: Contact phone number
            - born: Birth date
            - school: School information
            - college: College information
            - lives_in: Current location
            - profile_pic_id: Profile picture ID
            - professional_life: Professional background
            - ai_commenting: AI commenting preference
            - cover_image_id: Cover image ID
    
    Returns:
        CreateProfile: Response containing:
            - profile: Created profile object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If profile already exists or creation fails
    
    Note:
        - Requires login and superuser privileges
        - Prevents duplicate profiles for the same user
        - Creates bidirectional relationship between user and profile
        - Supports extensive profile customization options
    """
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
            print(f"DEBUG: profile_pic_id provided1: {input.get('profile_pic_id')}")
            # Auto-update Matrix avatar if profile_pic_id is being updated
            if input.get('profile_pic_id'):
               print(f"DEBUG: profile_pic_id provided: {input.get('profile_pic_id')}")
               try:
                   matrix_profile = MatrixProfile.objects.get(user=user_id)
                   if matrix_profile.access_token and matrix_profile.matrix_user_id:
                       avatar_result = asyncio.run(set_user_avatar_and_score(
                       access_token=matrix_profile.access_token,
                       user_id=matrix_profile.matrix_user_id,
                       database_user_id=user_id,
                       user_uid=user_id,
                       image_id=input.get('profile_pic_id'),
                       score=4.0
                       ))
            
                       if avatar_result["success"]:
                          logger.info(f"Auto-updated Matrix avatar for user {user_id}")
                       else:
                           logger.warning(f"Failed to auto-update Matrix avatar: {avatar_result.get('error')}")
                
               except MatrixProfile.DoesNotExist:
                      print(f"DEBUG: No Matrix profile found for user {user_id}")
                      logger.warning(f"No Matrix profile found for user {user_id}")
               except Exception as e:
                      print(f"DEBUG: Exception in Matrix avatar update: {e}")
                      logger.warning(f"Error auto-updating Matrix avatar: {e}")
            # Don't fail the profile update if avatar update fails

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
    """
    Updates user profile information and onboarding status.
    
    This mutation allows authenticated users to update their profile
    information including personal details, location, and preferences.
    It also tracks onboarding completion status for various fields.
    
    Args:
        input (UpdateProfileInput): Profile update data containing:
            - first_name: User's first name
            - last_name: User's last name
            - device_id: Device identifier
            - gender: User's gender
            - fcm_token: Firebase Cloud Messaging token
            - bio: User biography
            - state: User's state/province
            - city: User's city
            - designation: Job title/designation
            - phone_number: Contact phone number
            - born: Birth date
            - dob: Date of birth
            - lives_in: Current location
            - profile_pic_id: Profile picture ID
            - cover_image_id: Cover image ID
    
    Returns:
        UpdateUserProfile: Response containing:
            - profile: Updated profile object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: For validation errors or update failures
    
    Note:
        - Requires user authentication
        - Updates both Django User model and Neo4j Profile node
        - Validates image IDs and date of birth
        - Tracks onboarding completion status
        - Updates onboarding flags when fields are set
    """
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
            
            user_uid= profile_node.uid


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

            if bio := input.get("bio"):
               profile_node.bio = bio
               onboarding_status.bio_set = True
            
            # Extract mentions from bio text content
            if bio_text := input.get('bio'):
                from post.utils.mention_extractor import MentionExtractor
                from post.services.mention_service import MentionService
                
                # Extract usernames from bio text and convert to UIDs
                mentioned_user_uids = MentionExtractor.extract_and_convert_mentions(bio_text)
                
                if mentioned_user_uids:
                    # Get current user's UID
                    current_user = Users.nodes.get(user_id=user_id)
                    
                    # Create mentions for the bio
                    MentionService.create_mentions(
                        mentioned_user_uids=mentioned_user_uids,
                        content_type='bio',
                        content_uid=profile_node.uid,
                        mentioned_by_uid=current_user.uid,
                        mention_context='bio_content'
                    )
        

            # Track activity for analytics
            try:
                from analytics.services import ActivityService
                ActivityService.track_content_interaction_by_id(
                    user_id=user_id,
                    content_type='profile',
                    content_id=user_uid,
                    interaction_type='update',
                    metadata={
                        'updated_fields': list(input.keys()),
                        'profile_id': user_uid
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to track profile update activity: {e}")

            print(f"DEBUG: profile_pic_id provided1: {input.get('profile_pic_id')}")
            # Auto-update Matrix avatar if profile_pic_id is being updated
            if input.get('profile_pic_id'):
               print(f"DEBUG: profile_pic_id provided: {input.get('profile_pic_id')}")
               try:
                   matrix_profile = MatrixProfile.objects.get(user=user_id)
                   if matrix_profile.access_token and matrix_profile.matrix_user_id:
                       avatar_result = asyncio.run(set_user_avatar_and_score(
                       access_token=matrix_profile.access_token,
                       user_id=matrix_profile.matrix_user_id,
                       database_user_id=user_id,
                       user_uid=user_uid,
                       image_id=input.get('profile_pic_id'),
                       score=4.0
                       ))
            
                       if avatar_result["success"]:
                          logger.info(f"Auto-updated Matrix avatar for user {user_id}")
                       else:
                           logger.warning(f"Failed to auto-update Matrix avatar: {avatar_result.get('error')}")
                
               except MatrixProfile.DoesNotExist:
                      print(f"DEBUG: No Matrix profile found for user {user_id}")
                      logger.warning(f"No Matrix profile found for user {user_id}")
               except Exception as e:
                      print(f"DEBUG: Exception in Matrix avatar update: {e}")
                      logger.warning(f"Error auto-updating Matrix avatar: {e}")
            # Don't fail the profile update if avatar update fails

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
    """
    Deletes or deactivates a user account.
    
    This mutation provides two options for removing user accounts:
    deactivation (sets is_active=False) or complete deletion from
    both Django and Neo4j databases.
    
    Args:
        input (DeleteUserAccountInput): Deletion data containing:
            - username: Username of the account to delete
            - deleteType: Type of deletion ("deactivation" or "delete")
    
    Returns:
        DeleteUserAccount: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not found
        Exception: For database operation failures
    
    Note:
        - Requires login and superuser privileges
        - "deactivation" sets user.is_active = False
        - "delete" removes user and profile from databases
        - Uses transaction for safe deletion
        - Validates deleteType parameter
    """
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
    """
    Deletes a user's profile from the Neo4j database.
    
    This mutation removes a user's profile while keeping the user
    account intact. The operation is performed within a transaction
    to ensure data consistency.
    
    Args:
        input (DeleteUserProfileInput): Profile deletion data containing:
            - username: Username of the profile to delete
    
    Returns:
        DeleteUserProfile: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If profile is not found or deletion fails
    
    Note:
        - Requires login and superuser privileges
        - Uses Neo4j transaction for safe deletion
        - Only deletes the profile, not the user account
        - Maintains referential integrity
    """
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
    """
    Authenticates a user using username/email and password.
    
    This mutation handles user authentication, generates JWT tokens,
    updates last login time, stores device ID, and manages Matrix
    chat integration for authenticated users.
    
    Args:
        input (LoginInput): Login credentials containing:
            - usernameEmail: Username or email address
            - password: User's password
            - device_id: Optional device identifier
    
    Returns:
        LoginUsingUsernameEmail: Response containing:
            - user: Authenticated user object
            - token: JWT access token
            - refresh_token: JWT refresh token
            - success: Boolean indicating authentication success
            - message: Success or error message
            - chat_available: Boolean indicating Matrix chat availability
            - matrix_profile: Matrix profile information
    
    Raises:
        Exception: If authentication fails or user not found
    
    Note:
        - Supports login with username or email
        - Automatically handles Matrix chat registration/login
        - Stores device ID in user profile if provided
        - Updates last login timestamp
        - Gracefully handles Matrix service failures
    """
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
        
class SocialLogin(graphene.Mutation):
    """
    Social login mutation for Google and Facebook authentication.
    
    This mutation handles authentication via social providers (Google/Facebook),
    creates new users if they don't exist, and returns JWT tokens for authentication.
    """
    user = graphene.Field(UserType)
    token = graphene.String()
    refresh_token = graphene.String()
    success = graphene.Boolean()
    message = graphene.String()
    chat_available = graphene.Boolean()
    matrix_profile = graphene.Field(MatrixProfileType)
    is_new_user = graphene.Boolean()  # Indicates if this is a new user

    class Arguments:
        input = SocialLoginInput()

    def mutate(self, info, input):
        try:
            from auth_manager.services.social_auth_service import SocialAuthService
            
            access_token = input.access_token
            provider = input.provider.lower()
            invite_token = input.invite_token
            device_id = input.device_id

            # Verify token and get user data from social provider
            if provider == 'google':
                social_data = SocialAuthService.verify_google_token(access_token)
            elif provider == 'facebook':
                social_data = SocialAuthService.verify_facebook_token(access_token)
            else:
                raise GraphQLError("Unsupported social provider")

            # Get or create user from social data
            django_user, users_node, is_new_user = SocialAuthService.get_or_create_user_from_social_data(
                social_data, invite_token
            )

            # Generate JWT tokens
            token = get_token(django_user)
            refresh_token = create_refresh_token(django_user)

            # Update last login
            django_user.last_login = timezone.now()
            django_user.save()
            update_last_login(None, django_user)

            # Store device_id in profile if provided
            if device_id:
                try:
                    profile = users_node.profile.single()
                    if profile:
                        profile.device_id = device_id
                        profile.save()
                except Exception as e:
                    print(f"Error storing device_id: {str(e)}")

            # Handle Matrix chat integration
            chat_available = False
            matrix_profile = None
            try:
                matrix_profile, created = MatrixProfile.objects.get_or_create(user=django_user)
                
                if matrix_profile.access_token and matrix_profile.matrix_user_id:
                    chat_available = True
                else:
                    matrix_access_user = asyncio.run(login_user_on_matrix(django_user.username, django_user.username))
                    chat_available = matrix_access_user[0] is not None
                    
                    matrix_profile.access_token = matrix_access_user[0]
                    matrix_profile.pending_matrix_registration = not chat_available
                    matrix_profile.matrix_user_id = matrix_access_user[1]
                    matrix_profile.save()

            except Exception as e:
                print(f"Matrix login error: {e}")
                chat_available = False

            # Convert to UserType
            user = UserType.from_neomodel(users_node)

            return SocialLogin(
                user=user,
                token=token,
                refresh_token=refresh_token,
                success=True,
                message="Social login successful",
                chat_available=chat_available,
                matrix_profile=matrix_profile,
                is_new_user=is_new_user
            )

        except Exception as error:
            message = getattr(error, 'message', str(error))
            return SocialLogin(
                success=False,
                message=message,
                user=None,
                token=None,
                refresh_token=None,
                chat_available=False,
                matrix_profile=None,
                is_new_user=False
            )


class AppleSocialLogin(graphene.Mutation):
    """
    Apple social login mutation.
    
    This mutation handles authentication via Apple Sign-In,
    creates new users if they don't exist, and returns JWT tokens.
    """
    user = graphene.Field(UserType)
    token = graphene.String()
    refresh_token = graphene.String()
    success = graphene.Boolean()
    message = graphene.String()
    chat_available = graphene.Boolean()
    matrix_profile = graphene.Field(MatrixProfileType)
    is_new_user = graphene.Boolean()

    class Arguments:
        input = AppleSocialLoginInput()

    def mutate(self, info, input):
        try:
            from auth_manager.services.social_auth_service import SocialAuthService
            
            identity_token = input.identity_token
            invite_token = input.invite_token
            device_id = input.device_id

            # Verify Apple token and get user data
            social_data = SocialAuthService.verify_apple_token(identity_token)

            # Get or create user from social data
            django_user, users_node, is_new_user = SocialAuthService.get_or_create_user_from_social_data(
                social_data, invite_token
            )

            # Generate JWT tokens
            token = get_token(django_user)
            refresh_token = create_refresh_token(django_user)

            # Update last login
            django_user.last_login = timezone.now()
            django_user.save()
            update_last_login(None, django_user)

            # Store device_id in profile if provided
            if device_id:
                try:
                    profile = users_node.profile.single()
                    if profile:
                        profile.device_id = device_id
                        profile.save()
                except Exception as e:
                    print(f"Error storing device_id: {str(e)}")

            # Handle Matrix chat integration
            chat_available = False
            matrix_profile = None
            try:
                matrix_profile, created = MatrixProfile.objects.get_or_create(user=django_user)
                
                if matrix_profile.access_token and matrix_profile.matrix_user_id:
                    chat_available = True
                else:
                    matrix_access_user = asyncio.run(login_user_on_matrix(django_user.username, django_user.username))
                    chat_available = matrix_access_user[0] is not None
                    
                    matrix_profile.access_token = matrix_access_user[0]
                    matrix_profile.pending_matrix_registration = not chat_available
                    matrix_profile.matrix_user_id = matrix_access_user[1]
                    matrix_profile.save()

            except Exception as e:
                print(f"Matrix login error: {e}")
                chat_available = False

            # Convert to UserType
            user = UserType.from_neomodel(users_node)

            return AppleSocialLogin(
                user=user,
                token=token,
                refresh_token=refresh_token,
                success=True,
                message="Apple login successful",
                chat_available=chat_available,
                matrix_profile=matrix_profile,
                is_new_user=is_new_user
            )

        except Exception as error:
            message = getattr(error, 'message', str(error))
            return AppleSocialLogin(
                success=False,
                message=message,
                user=None,
                token=None,
                refresh_token=None,
                chat_available=False,
                matrix_profile=None,
                is_new_user=False
            )        
        
class Logout(graphene.Mutation):
    """
    Logs out the authenticated user and cleans up session data.
    
    This mutation handles user logout by removing device ID from
    the user's profile and performing necessary cleanup operations.
    
    Returns:
        Logout: Response containing:
            - success: Boolean indicating logout success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If logout process fails
    
    Note:
        - Requires user authentication
        - Removes device ID from user profile
        - Gracefully handles cleanup failures
        - Does not invalidate JWT tokens (client-side responsibility)
    """
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
    """
    Checks username availability and provides suggestions if unavailable.
    
    This mutation validates a username and returns availability status.
    If the username is taken, it generates alternative suggestions
    based on the requested username and user's email.
    
    Args:
        username (str): The username to check for availability
    
    Returns:
        SearchUsername: Response containing:
            - suggested_usernames: List of available username suggestions
            - success: Boolean indicating if username is available
            - message: Availability status message
    
    Raises:
        GraphQLError: If user is not authenticated
        ValidationError: If username format is invalid
        Exception: If username check fails
    
    Note:
        - Requires user authentication
        - Validates username format before checking availability
        - Generates intelligent suggestions using email and base username
        - Limits suggestion search to 50 similar usernames for performance
    """
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
    """
    Sets the username for an authenticated user during onboarding.
    
    This mutation allows users to select and set their username,
    updates their Matrix profile display name, and marks the
    username selection step as completed in onboarding.
    
    Args:
        input (SelectUsernameInput): Username selection data containing:
            - username: The chosen username
    
    Returns:
        SelectUsername: Response containing:
            - user: Updated user object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated or username is taken
        ValidationError: If username format is invalid
        Exception: If username update fails
    
    Note:
        - Requires user authentication
        - Validates username format and availability
        - Updates Matrix profile display name if available
        - Marks onboarding username selection as complete
        - Gracefully handles Matrix profile update failures
    """
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
    """
    Creates an onboarding status record for a user profile.
    
    This mutation initializes the onboarding tracking system
    for a user profile, setting various completion flags for
    different onboarding steps.
    
    Args:
        input (OnboardingInput): Onboarding data containing:
            - profile_uid: UID of the profile to create onboarding for
            - email_verified: Email verification status (default: False)
            - phone_verified: Phone verification status (default: False)
            - username_selected: Username selection status (default: False)
            - first_name_set: First name completion status (default: False)
            - last_name_set: Last name completion status (default: False)
            - gender_set: Gender selection status (default: False)
            - bio_set: Bio completion status (default: False)
    
    Returns:
        CreateOnboardingStatus: Response containing:
            - onboarding_status: Created onboarding status object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If profile not found or creation fails
    
    Note:
        - Requires login and superuser privileges
        - Links onboarding status to specified profile
        - All onboarding flags default to False if not specified
    """
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
    """
    Updates an existing onboarding status record.
    
    This mutation allows modification of onboarding completion
    flags for tracking user progress through the onboarding
    process.
    
    Args:
        input (UpdateOnboardingInput): Update data containing:
            - uid: UID of the onboarding status to update
            - Various onboarding flags to update
    
    Returns:
        UpdateOnboardingStatus: Response containing:
            - onboarding_status: Updated onboarding status object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If onboarding status not found or update fails
    
    Note:
        - Requires login and superuser privileges
        - Dynamically updates any provided fields
        - Uses setattr for flexible field updates
    """
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
    """
    Creates contact information for a user profile.
    
    This mutation adds contact information such as social media
    profiles, websites, or other contact methods to a user's
    profile.
    
    Args:
        input (ContactinfoInput): Contact information data containing:
            - type: Type of contact information
            - value: Contact value (e.g., username, URL)
            - platform: Optional platform name
            - link: Optional direct link
    
    Returns:
        CreateContactInfo: Response containing:
            - contact_info: Created contact information object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If profile not found or creation fails
    
    Note:
        - Requires login and superuser privileges
        - Links contact info to authenticated user's profile
        - Supports various contact types and platforms
    """
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
    """
    Updates existing contact information for a user profile.
    
    This mutation modifies contact information fields such as
    type, value, platform, or link for an existing contact
    information record.
    
    Args:
        input (UpdateContactinfoInput): Update data containing:
            - uid: UID of the contact info to update
            - Fields to update (type, value, platform, link)
    
    Returns:
        UpdateContactInfo: Response containing:
            - contact_info: Updated contact information object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If contact info not found or update fails
    
    Note:
        - Requires login and superuser privileges
        - Dynamically updates any provided fields
        - Uses setattr for flexible field updates
    """
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
    """
    Deletes contact information from a user profile.
    
    This mutation removes a specific contact information
    record from the database.
    
    Args:
        input (DeleteInput): Deletion data containing:
            - uid: UID of the contact info to delete
    
    Returns:
        DeleteContactInfo: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If contact info not found or deletion fails
    
    Note:
        - Requires login and superuser privileges
        - Permanently removes contact information
        - Cannot be undone
    """
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
    """
    Creates a score record for a user profile.
    
    This mutation initializes various scoring metrics for a user
    profile, including vibes, intelligence, appeal, social, human,
    and repository scores.
    
    Args:
        input (ScoreInput): Score data containing:
            - profile_uid: UID of the profile to create scores for
            - vibers_count: Number of vibers (default: 2.0)
            - cumulative_vibescore: Cumulative vibe score (default: 2.0)
            - intelligence_score: Intelligence rating (default: 2.0)
            - appeal_score: Appeal rating (default: 2.0)
            - social_score: Social interaction score (default: 2.0)
            - human_score: Human authenticity score (default: 2.0)
            - repo_score: Repository/work score (default: 2.0)
    
    Returns:
        CreateScore: Response containing:
            - score: Created score object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If profile not found or creation fails
    
    Note:
        - Requires login and superuser privileges
        - Links score to specified profile
        - All scores default to 2.0 if not specified
    """
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
    """
    Updates an existing score record for a user profile.
    
    This mutation modifies scoring metrics for a user profile,
    allowing updates to various score components.
    
    Args:
        input (UpdateScoreInput): Update data containing:
            - uid: UID of the score to update
            - Score fields to update (vibers_count, cumulative_vibescore, etc.)
    
    Returns:
        UpdateScore: Response containing:
            - score: Updated score object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If score not found or update fails
    
    Note:
        - Requires login and superuser privileges
        - Dynamically updates any provided score fields
        - Uses setattr for flexible field updates
    """
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
    """
    Deletes a score record from a user profile.
    
    This mutation removes a score record from the database,
    permanently deleting all scoring metrics for the profile.
    
    Args:
        input (DeleteInput): Deletion data containing:
            - uid: UID of the score to delete
    
    Returns:
        DeleteScore: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If score not found or deletion fails
    
    Note:
        - Requires login and superuser privileges
        - Permanently removes score record
        - Cannot be undone
    """
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
    """
    Creates an interest record for a user profile.
    
    This mutation adds interest information to a user's profile,
    storing a list of interest names that represent the user's
    areas of interest.
    
    Args:
        input (InerestInput): Interest data containing:
            - names: List of interest names (default: [])
    
    Returns:
        CreateInterest: Response containing:
            - interest: Created interest object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If profile not found or creation fails
    
    Note:
        - Requires user authentication
        - Links interest to authenticated user's profile
        - Supports multiple interest names in a single record
        - Uses error handling decorator
    """
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
    """
    Updates an existing interest record for a user profile.
    
    This mutation modifies interest information, allowing updates
    to the list of interest names or deletion status.
    
    Args:
        input (UpdateInterestInput): Update data containing:
            - uid: UID of the interest to update
            - names: Updated list of interest names
            - is_deleted: Deletion status flag
    
    Returns:
        UpdateInterest: Response containing:
            - interest: Updated interest object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If interest not found or update fails
    
    Note:
        - Requires user authentication
        - Supports updating interest names and deletion status
        - Uses error handling decorator
    """
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
    """
    Soft deletes an interest record for a user profile.
    
    This mutation marks an interest record as deleted rather
    than permanently removing it from the database.
    
    Args:
        input (DeleteInput): Deletion data containing:
            - uid: UID of the interest to delete
    
    Returns:
        DeleteInterest: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If interest not found or deletion fails
    
    Note:
        - Requires user authentication
        - Performs soft delete (sets is_deleted=True)
        - Uses error handling decorator
        - Data can be recovered by updating is_deleted flag
    """
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
    """
    Sends an OTP (One-Time Password) to a user's email.
    
    This mutation generates and sends an OTP for various purposes
    such as email verification or password reset. It includes
    rate limiting to prevent abuse.
    
    Args:
        email (str): Email address to send OTP to
        purpose (OTPPurpose): Purpose of the OTP (EMAIL_VERIFICATION or FORGET_PASSWORD)
    
    Returns:
        SendOTP: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
            - otp: The generated OTP code (for testing/debugging)
    
    Raises:
        GraphQLError: If user not found, rate limit exceeded, or invalid purpose
        Exception: If OTP generation or sending fails
    
    Note:
        - Rate limited to 3 OTP requests per hour per user
        - For FORGET_PASSWORD: validates email exists in system
        - For EMAIL_VERIFICATION: requires authentication
        - Stores OTP in database and cache
        - Sends email using external mail service
    """
    success = graphene.Boolean()
    message=graphene.String()
    otp = graphene.String()
    
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
                        api_url=os.getenv('EMAIL_API_URL'),
                        api_key=os.getenv('EMAIL_API_KEY'),
                        first_name=user.first_name,
                        otp_code=otp_code,
                        user_email=email
                    )
            elif purpose==OtpPurposeEnum.FORGET_PASSWORD.value:
                 generate_payload.send_rendered_forget_email(
                        api_url=os.getenv('EMAIL_API_URL'),
                        api_key=os.getenv('EMAIL_API_KEY'),
                        first_name=user.first_name,
                        otp_code=otp_code,
                        user_email=email
                    )

            # send_otp.send_otp_email(email, otp_code,purpose)
            return SendOTP(success=True,message=UserMessages.OTP_SUCCESS, otp=otp_code)
        
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return SendOTP(success=False,message=message, otp=None)
    
class VerifyOTP(graphene.Mutation):
    """
    Verifies an OTP for email verification purposes.
    
    This mutation validates an OTP sent to the user's email
    and marks their email as verified in the onboarding status.
    
    Args:
        input (VerifyOtpInput): OTP verification data containing:
            - otp: The OTP code to verify
    
    Returns:
        VerifyOTP: Response containing:
            - success: Boolean indicating verification success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user not authenticated, OTP invalid, or expired
        Exception: If verification process fails
    
    Note:
        - Requires user authentication
        - Validates OTP against database records
        - Checks OTP expiration
        - Updates onboarding email verification status
        - Deletes OTP after successful verification
        - Uses error handling decorator
    """
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
    """
    Verifies OTP and resets user password in a single operation.
    
    This mutation validates an OTP for password reset and updates
    the user's password, then generates new authentication tokens.
    
    Args:
        email (str): User's email address
        otp (str): OTP code for verification
        new_password (str): New password to set
    
    Returns:
        VerifyOTPAndResetPassword: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
            - token: New JWT access token
            - refresh_token: New JWT refresh token
    
    Raises:
        GraphQLError: If user not found, OTP invalid, or expired
        Exception: If password reset fails
    
    Note:
        - Does not require authentication (password reset flow)
        - Validates OTP against database records
        - Checks OTP expiration
        - Updates user password using Django's set_password
        - Generates new authentication tokens
        - Deletes OTP after successful verification
    """
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


class FindUserByEmailOrUsername(graphene.Mutation):
    """
    Step 1: Find user by email or username for password reset flow.
    
    This mutation searches for a user account using either email or username
    and returns the user's UID if found.
    
    Args:
        input (FindUserInput): Contains email_or_username field
    
    Returns:
        FindUserByEmailOrUsername: Response containing:
            - success: Boolean indicating if user was found
            - message: Success or error message
            - uid: User's UID if found
    
    Raises:
        GraphQLError: If user not found
        Exception: If search fails
    
    Note:
        - Does not require authentication
        - Searches by email or username
        - Returns UID for next step in password reset flow
    """
    success = graphene.Boolean()
    message = graphene.String()
    uid = graphene.String()
    email = graphene.String()
    username = graphene.String()
    
    class Arguments:
        input = FindUserInput(required=True)

    def mutate(self, info, input):
        try:
            email_or_username = input.email_or_username.strip()
            
            # Try to find user by email first, then by username in Neo4j Users model
            user = None
            if '@' in email_or_username:
                # It's an email - search in Neo4j Users model
                user = Users.nodes.filter(email=email_or_username.lower()).first()
            else:
                # It's a username - search in Neo4j Users model (case-sensitive)
                user = Users.nodes.filter(username=email_or_username).first()
            
            if not user:
                raise GraphQLError('User not found with the provided email or username')
            
            return FindUserByEmailOrUsername(
                success=True,
                message="User found successfully",
                uid=user.uid,
                email=user.email,
                username=user.username
            )
        
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return FindUserByEmailOrUsername(
                success=False,
                message=message,
                uid=None
            )


class SendOTPForPasswordReset(graphene.Mutation):
    """
    Step 2: Send OTP for password reset using user's UID.
    
    This mutation generates and sends an OTP to the user's email
    for password reset verification.
    
    Args:
        input (SendOTPInput): Contains uid field
    
    Returns:
        SendOTPForPasswordReset: Response containing:
            - success: Boolean indicating if OTP was sent
            - message: Success or error message
    
    Raises:
        GraphQLError: If user not found or email sending fails
        Exception: If OTP generation fails
    
    Note:
        - Does not require authentication
        - Generates OTP with FORGET_PASSWORD purpose
        - Sends email using existing email service
        - Rate limited to prevent abuse
    """
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = SendOTPInput(required=True)

    def mutate(self, info, input):
        try:
            uid = input.user_uid.strip()
            
            # Find user by UID (username)
            user = User.objects.filter(username=uid).first()
            if not user:
                raise GraphQLError('User not found')
            
            # Check rate limiting (similar to existing SendOTP)
            # existing_otp = OTP.objects.filter(
            #     user=user, 
            #     purpose=OtpPurposeEnum.FORGET_PASSWORD.value
            # ).first()
            
            # if existing_otp and not existing_otp.is_expired():
            #     raise GraphQLError('OTP already sent. Please wait before requesting a new one.')
            
            # Delete any existing OTPs for this user and purpose
            OTP.objects.filter(
                user=user, 
                purpose=OtpPurposeEnum.FORGET_PASSWORD.value
            ).delete()
            
            # Generate new OTP
            otp_code = generate_otp()
            
            # Create OTP record
            otp_instance = OTP.objects.create(
                user=user,
                otp=otp_code,
                purpose=OtpPurposeEnum.FORGET_PASSWORD.value
            )
            
            # Send OTP email
            generate_payload.send_rendered_forget_email(
                api_url=os.getenv('EMAIL_API_URL'),
                api_key=os.getenv('EMAIL_API_KEY'),
                first_name=user.first_name,
                otp_code=otp_code,
                user_email=user.email
            )
            
            return SendOTPForPasswordReset(
                success=True,
                message="OTP sent successfully to your email"
            )
        
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return SendOTPForPasswordReset(
                success=False,
                message=message
            )


class VerifyOTPForPasswordReset(graphene.Mutation):
    """
    Step 3: Verify OTP for password reset.
    
    This mutation validates the OTP sent for password reset
    and marks it as verified for the final password update step.
    
    Args:
        input (VerifyOTPInput): Contains uid and otp fields
    
    Returns:
        VerifyOTPForPasswordReset: Response containing:
            - success: Boolean indicating if OTP was verified
            - message: Success or error message
            - verification_token: Token to use for password update
    
    Raises:
        GraphQLError: If user not found, OTP invalid, or expired
        Exception: If verification fails
    
    Note:
        - Does not require authentication
        - Validates OTP against database records
        - Checks OTP expiration
        - Returns verification token for next step
        - Does not delete OTP (kept for password update step)
    """
    success = graphene.Boolean()
    message = graphene.String()
    verification_token = graphene.String()

    class Arguments:
        input = VerifyOTPInput(required=True)

    def mutate(self, info, input):
        try:
            email = input.email.strip()
            otp_code = input.otp.strip()
            
            # Find user by email
            user = User.objects.filter(email=email).first()
            if not user:
                raise GraphQLError('User not found')
            
            # Find OTP record
            otp_instance = OTP.objects.filter(
                user=user,
                otp=otp_code,
                purpose=OtpPurposeEnum.FORGET_PASSWORD.value
            ).first()
            
            if not otp_instance:
                raise GraphQLError('Invalid OTP')
            
            if otp_instance.is_expired():
                raise GraphQLError('OTP has expired')
            
            # Generate verification token (simple token for this step)
            verification_token = f"{user.id}:{otp_code}:{timezone.now().timestamp()}"
            
            return VerifyOTPForPasswordReset(
                success=True,
                message="OTP verified successfully",
                verification_token=verification_token
            )
        
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return VerifyOTPForPasswordReset(
                success=False,
                message=message,
                verification_token=None
            )


class UpdatePasswordWithOTPVerification(graphene.Mutation):
    """
    Step 4: Update password after OTP verification.
    
    This mutation updates the user's password after successful OTP verification,
    following the same password validation rules as user creation.
    
    Args:
        input (UpdatePasswordInput): Contains uid, verification_token, and new_password
    
    Returns:
        UpdatePasswordWithOTPVerification: Response containing:
            - success: Boolean indicating if password was updated
            - message: Success or error message
            - token: New JWT access token
            - refresh_token: New JWT refresh token
    
    Raises:
        GraphQLError: If verification token invalid, user not found, or password validation fails
        Exception: If password update fails
    
    Note:
        - Does not require authentication
        - Validates verification token from previous step
        - Applies same password validation rules as createUser
        - Updates user password using Django's set_password
        - Generates new authentication tokens
        - Deletes OTP after successful password update
    """
    success = graphene.Boolean()
    message = graphene.String()
    token = graphene.String()
    refresh_token = graphene.String()

    class Arguments:
        input = UpdatePasswordInput(required=True)

    def mutate(self, info, input):
        from auth_manager.validators.rules.password_validation import validate_password
        
        token = None
        refresh_token = None
        
        try:
            email = input.email.strip()
            new_password = input.new_password
            otp_verified = input.otp_verified
            
            # Check if OTP is verified
            if not otp_verified:
                return UpdatePasswordWithOTPVerification(
                    success=False,
                    message="OTP verification is required before updating password"
                )
            
            # Find user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return UpdatePasswordWithOTPVerification(
                    success=False,
                    message="User not found with this email"
                )
            
            # Validate new password using existing validation rules
            validate_password(new_password)
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Track activity for analytics
            try:
                from analytics.services import ActivityService
                ActivityService.track_content_interaction_by_id(
                    user_id=user.id,
                    content_type='user',
                    content_id=str(user.id),
                    interaction_type='password_change',
                    metadata={
                        'email': email,
                        'method': 'otp_verification'
                    }
                )
            except Exception as e:
                # Don't fail password update if activity tracking fails
                pass
            
            # Generate new tokens
            token = get_token(user)
            refresh_token = create_refresh_token(user)
            
            return UpdatePasswordWithOTPVerification(
                success=True,
                message="Password updated successfully",
                token=token,
                refresh_token=refresh_token
            )
        
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdatePasswordWithOTPVerification(
                success=False,
                message=message,
                token=token,
                refresh_token=refresh_token
            )





class DeleteAchievement(Mutation):
    """
    Soft deletes an achievement record from a user profile.
    
    This mutation marks an achievement as deleted rather than
    permanently removing it from the database.
    
    Args:
        input (DeleteInput): Deletion data containing:
            - uid: UID of the achievement to delete
    
    Returns:
        DeleteAchievement: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If achievement not found or deletion fails
    
    Note:
        - Requires user authentication
        - Performs soft delete (sets is_deleted=True)
        - Uses error handling decorator
        - Data can be recovered by updating is_deleted flag
    """
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
    """
    Soft deletes an education record from a user profile.
    
    This mutation marks an education record as deleted rather than
    permanently removing it from the database.
    
    Args:
        input (DeleteInput): Deletion data containing:
            - uid: UID of the education record to delete
    
    Returns:
        DeleteEducation: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If education record not found or deletion fails
    
    Note:
        - Requires user authentication
        - Performs soft delete (sets is_deleted=True)
        - Uses error handling decorator
        - Data can be recovered by updating is_deleted flag
    """
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
    """
    Soft deletes a skill record from a user profile.
    
    This mutation marks a skill record as deleted rather than
    permanently removing it from the database.
    
    Args:
        input (DeleteInput): Deletion data containing:
            - uid: UID of the skill to delete
    
    Returns:
        DeleteSkill: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If skill not found or deletion fails
    
    Note:
        - Requires user authentication
        - Performs soft delete (sets is_deleted=True)
        - Uses error handling decorator
        - Data can be recovered by updating is_deleted flag
    """
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
    """
    Soft deletes an experience record from a user profile.
    
    This mutation marks an experience record as deleted rather than
    permanently removing it from the database.
    
    Args:
        input (DeleteInput): Deletion data containing:
            - uid: UID of the experience record to delete
    
    Returns:
        DeleteExperience: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If experience record not found or deletion fails
    
    Note:
        - Requires user authentication
        - Performs soft delete (sets is_deleted=True)
        - Uses error handling decorator
        - Data can be recovered by updating is_deleted flag
    """
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
    """
    Creates a review from one user to another user.
    
    This mutation allows users to create reviews with reactions,
    vibes, and content for other users. It also manages profile
    reaction tracking and scoring.
    
    Args:
        input (CreateUsersReviewInput): Review data containing:
            - touser_uid: UID of the user being reviewed
            - reaction: Reaction/vibe name
            - vibe: Numeric vibe score
            - title: Review title
            - content: Review content
            - file_id: Optional file attachment ID
    
    Returns:
        CreateUsersReview: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If user not found or review creation fails
    
    Note:
        - Requires user authentication
        - Creates or updates ProfileReactionManager for target user
        - Tracks reactions and vibe scores
        - Links review to both reviewer and reviewee
        - Uses error handling decorator
    """
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
    """
    Permanently deletes a user review.
    
    This mutation removes a user review from the database
    completely, unlike soft delete operations.
    
    Args:
        input (DeleteUsersReviewInput): Deletion data containing:
            - uid: UID of the review to delete
    
    Returns:
        DeleteUsersReview: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If review not found or deletion fails
    
    Note:
        - Requires user authentication
        - Performs hard delete (permanent removal)
        - Uses error handling decorator
        - Cannot be undone
    """
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
    """
    Creates an upload contact record for a user.
    
    This mutation allows users to upload their contact list,
    with validation to ensure each contact has exactly 10 digits
    and prevents duplicate uploads.
    
    Args:
        contact (List[str]): List of contact numbers (each must be 10 digits)
    
    Returns:
        CreateUploadContact: Response containing:
            - upload_contact: Created upload contact object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user not authenticated, already uploaded, or validation fails
    
    Note:
        - Requires superuser privileges
        - Validates each contact has exactly 10 characters
        - Prevents duplicate uploads per user
        - Stores contact list for the authenticated user
    """
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
    """
    Updates an existing upload contact record for a user.
    
    This mutation allows users to modify their uploaded contact list
    or mark it as deleted. Validates contact format if provided.
    
    Args:
        contact (List[str], optional): Updated list of contact numbers
        is_deleted (bool, optional): Flag to mark record as deleted
    
    Returns:
        UpdateUploadContact: Response containing:
            - upload_contact: Updated upload contact object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user not authenticated or validation fails
    
    Note:
        - Requires superuser privileges
        - Validates each contact has exactly 10 characters if provided
        - Can update contact list and/or deletion status
        - Saves changes to database
    """
    
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
    """
    Permanently deletes an upload contact record for a user.
    
    This mutation removes the user's uploaded contact list
    from the database completely.
    
    Returns:
        DeleteUploadContact: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        Exception: If user not authenticated or record not found
    
    Note:
        - Requires superuser privileges
        - Performs hard delete (permanent removal)
        - Cannot be undone
        - Removes contact list for authenticated user
    """
    
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
    """
    Sends feedback from a user with email, image, and message.
    
    This mutation allows authenticated superusers to submit feedback
    with an associated email, image, and feedback message.
    
    Args:
        email (str): Email address for feedback
        image_id (str): ID of the associated image
        feedback_message (str): The feedback content
    
    Returns:
        SendFeedback: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user not authenticated or not superuser
        Exception: If feedback submission fails
    
    Note:
        - Requires user authentication and superuser privileges
        - Contains commented code for OTP purposes
        - Implementation appears incomplete
    """
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
    """
    Creates a back profile review from one user to another.
    
    This mutation allows users to create reviews for other users' back profiles,
    including reactions, vibes, and content. It manages back profile reaction
    tracking and scoring.
    
    Args:
        input (CreateBackProfileReviewInput): Review data containing:
            - touser_uid: UID of the user being reviewed
            - reaction: Reaction/vibe name
            - vibe: Numeric vibe score
            - title: Review title
            - content: Review content
            - image_ids: Optional file attachment IDs
            - rating: user start ratings
    
    Returns:
        CreateBackProfileReview: Response containing:
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If user not found or review creation fails
    
    Note:
        - Requires user authentication
        - Creates or updates BackProfileReactionManager for target user
        - Tracks reactions and vibe scores for back profiles
        - Links review to both reviewer and reviewee
        - Uses error handling decorator
    """
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

            # profile_reaction_manager.add_reaction(
            #     vibes_name=input.reaction,
            #     score=input.vibe  # Assuming `reaction` is a numeric score to be averaged
            # )
            # profile_reaction_manager.save()

            users_review = BackProfileUsersReview(
                reaction=input.reaction,
                vibe=input.vibe,
                title=input.title,
                content=input.content,
                image_ids=input.image_ids or [],
                rating=input.rating or 4         
            )
            users_review.save()
            users_review.byuser.connect(byuser)
            users_review.touser.connect(touser)
            touser.user_back_profile_review.connect(users_review)

            return CreateBackProfileReview( success=True, message="User Peer Review created successfully.")
        except Exception as error:
            message=getattr(error , "message", str(error))
            return CreateBackProfileReview(success=False, message=message)








class CreateInvite(graphene.Mutation):
    """
    Creates an invitation for a user to join the platform.
    
    This mutation generates an invite with a unique token and link
    that can be shared with others to join the platform.
    
    Args:
        input (CreateInviteInput): Invitation data containing:
            - origin_type: Type/source of the invitation
    
    Returns:
        CreateInvite: Response containing:
            - invite: Created invite object
            - invite_link: Generated invitation link
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user not authenticated or invalid origin type
        Exception: If invite creation fails
    
    Note:
        - Requires user authentication
        - Validates origin_type against allowed choices
        - Generates unique invite token and link
        - Links invite to the inviting user
    """
    invite = graphene.Field(InviteType)
    invite_link = graphene.String()
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateInviteInput(required=True)

    @login_required
    def mutate(self, info, input):
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("User not found")

            payload = info.context.payload
            user_id = payload.get('user_id')
            
            login_user = Users.nodes.get(user_id=user_id)

            # Validate origin_type
            if input.origin_type.value not in dict(Invite.OriginType.choices):
                raise GraphQLError("Invalid origin type provided")
            
            # Create invite
            invite = Invite.objects.create(
                inviter=user,
                origin_type=input.origin_type.value,
            )

            # Use the correct backend URL
            invite_link = f"https://backend.ooumph.com/signup/invite/{invite.invite_token}"

            return CreateInvite(
                invite=invite, 
                invite_link=invite_link, 
                success=True, 
                message="Invite created successfully"
            )

        except Exception as error:
            return CreateInvite(invite=None, invite_link=None, success=False, message=str(error))



class CreateUserV2(Mutation):
    """
    Creates a new user account (version 2) with optional invite token support.
    
    This mutation creates a new user account with enhanced features including
    invite token validation, automatic connections, and user type specification.
    
    Args:
        input (CreateUserInputV2): User creation data containing:
            - email: User's email address
            - password: User's password
            - user_type: Type of user account (default: "personal")
            - invite_token: Optional invitation token
    
    Returns:
        CreateUserV2: Response containing:
            - token: JWT authentication token
            - refresh_token: JWT refresh token
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user already exists or validation fails
        Exception: If user creation fails
    
    Note:
        - Validates email and password inputs
        - Checks for existing users in both SQLite and Neo4j
        - Processes invite tokens and creates automatic connections
        - Generates authentication tokens upon successful creation
        - Creates user nodes in Neo4j database
    """
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
            is_bot = input.get('is_bot', False)
            persona = input.get('persona')
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
            user_node.is_bot = is_bot
            if persona:
                user_node.persona = persona
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
    """
    Creates a reaction (like) for profile data items (education, achievement, skill, experience).
    
    This mutation allows users to react to various profile data items with
    specific reactions and vibe scores. It manages reaction tracking and
    scoring for different profile categories.
    
    Args:
        input (CreateProfileDataReactionInputV2): Reaction data containing:
            - uid: UID of the profile data item
            - reaction: Type of reaction
            - vibe: Numeric vibe score
            - category: Category of profile data (education, achievement, skill, experience)
    
    Returns:
        CreateProfileDataReactionV2: Response containing:
            - like: Created reaction object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If reaction creation fails
    
    Note:
        - Requires user authentication
        - Supports education, achievement, skill, and experience categories
        - Creates or updates appropriate ReactionManager for the category
        - Links reaction to both user and profile data item
        - Uses error handling decorator
    """
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

                # Track vibe activity
                try:
                    # Get the profile data owner based on category
                    profile_data_owner = None
                    if category == "education":
                        profile_data_owner = education_node.user.single()
                    elif category == "experience":
                        profile_data_owner = experience_node.user.single()
                    elif category == "achievement":
                        profile_data_owner = achievement_node.user.single()
                    elif category == "skill":
                        profile_data_owner = skill_node.user.single()
                    
                    if profile_data_owner and input.reaction and input.vibe:
                        vibe_data = {
                            'vibe_name': input.reaction,
                            'vibe_score': input.vibe,
                            'vibe_type': 'profile_data',
                            'category': f'profile_{category}_reaction'
                        }
                        
                        context_data = {
                            'profile_data_uid': input.uid,
                            'profile_data_category': category,
                            'ip_address': info.context.META.get('REMOTE_ADDR'),
                            'user_agent': info.context.META.get('HTTP_USER_AGENT')
                        }
                        
                        VibeActivityService.track_vibe_sending(
                            sender=user_node,
                            receiver_id=profile_data_owner.uid,
                            vibe_data=vibe_data,
                            vibe_score=input.vibe,
                            context=context_data
                        )
                        
                        logger.info(f"Vibe activity tracked for profile {category} reaction: {user_node.user_id} -> {profile_data_owner.user_id}")
                        
                except Exception as vibe_error:
                    logger.error(f"Failed to track vibe activity for profile {category} reaction: {str(vibe_error)}")
                    # Don't fail the main operation if vibe tracking fails

                # post.like.connect(like)

                # increment_post_like_count(post.uid)

                return CreateProfileDataReactionV2(like=ProfileDataReactionType.from_neomodel(like), success=True, message=UserMessages.REACTION_CREATED)
            else:
                return CreateProfileDataReactionV2(like=None, success=False, message="Please Select category")

        except Exception as error:
            message = getattr(error, 'message', str(error))
            return CreateProfileDataReactionV2(like=None, success=False, message=message)


class CreateProfileDataCommentV2(Mutation):
    """
    Creates a comment for profile data items (education, achievement, skill, experience).
    
    This mutation allows users to add comments to various profile data items
    across different categories.
    
    Args:
        input (CreateProfileCommentInputV2): Comment data containing:
            - uid: UID of the profile data item
            - content: Comment content
            - category: Category of profile data (education, achievement, skill, experience)
    
    Returns:
        CreateProfileDataCommentV2: Response containing:
            - comment_details: Created comment object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If comment creation fails
    
    Note:
        - Requires user authentication
        - Supports education, achievement, skill, and experience categories
        - Links comment to both user and profile data item
        - Uses error handling decorator
        - Returns specific error message if category not selected
    """
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
    """
    Updates an existing profile data comment.
    
    This mutation allows users to modify the content of their
    existing comments on profile data items.
    
    Args:
        input (UpdateProfileCommentInputV2): Update data containing:
            - uid: UID of the comment to update
            - content: New comment content
    
    Returns:
        UpdateProfileDataCommentV2: Response containing:
            - comment_details: Updated comment object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If comment not found or update fails
    
    Note:
        - Requires user authentication
        - Updates existing comment content
        - Uses error handling decorator
        - Maintains existing relationships
    """
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
    """
    Creates a new achievement record for a user's profile.
    
    This mutation allows users to add achievements to their profile
    with details like description, source, dates, and file attachments.
    
    Args:
        input (CreateAchievementInput): Achievement data containing:
            - what: Achievement title/name
            - description: Achievement description
            - from_source: Source of the achievement
            - created_on: Creation timestamp
            - file_id: List of file attachment IDs
            - from_date: Start date (optional)
            - to_date: End date (optional)
    
    Returns:
        CreateAchievement: Response containing:
            - achievement: Created achievement object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If achievement creation fails or file validation fails
    
    Note:
        - Requires user authentication
        - Validates file IDs if provided
        - Links achievement to user's profile
        - Uses error handling decorator
    """
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
                description=input.get('description', None),
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
    """
    Updates an existing achievement record.
    
    This mutation allows users to modify their existing achievement
    records with new information.
    
    Args:
        input (UpdateAchievementInput): Update data containing:
            - uid: UID of the achievement to update
            - Additional fields to update
    
    Returns:
        UpdateAchievement: Response containing:
            - achievement: Updated achievement object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If achievement not found or update fails
    
    Note:
        - Requires user authentication
        - Updates all provided fields dynamically
        - Uses error handling decorator
        - Maintains existing relationships
    """
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
    """
    Creates a new education record for a user's profile.
    
    This mutation allows users to add education entries to their profile
    with details like institution, field of study, dates, and file attachments.
    
    Args:
        input (CreateEducationInput): Education data containing:
            - what: Institution or degree name
            - field_of_study: Field of study
            - from_source: Source of the education record
            - description: Education description
            - created_on: Creation timestamp
            - file_id: List of file attachment IDs
            - from_date: Start date (optional)
            - to_date: End date (optional)
    
    Returns:
        CreateEducation: Response containing:
            - education: Created education object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If education creation fails or file validation fails
    
    Note:
        - Requires user authentication
        - Validates file IDs if provided
        - Links education to user's profile
        - Uses error handling decorator
    """
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
            
            # Validate education input
            # from_source = institution/school name
            # what = degree/qualification
            # field_of_study = academic field/major
            school_name = input.get('from_source', '')
            degree = input.get('what', '')
            field_of_study = input.get('field_of_study', '')
            
            validation_result = education_validation.validate_education_input(school_name, degree, field_of_study)
            if not validation_result.get('valid'):
                raise GraphQLError(validation_result.get('error'))

            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            
            education = Education(
                    what=degree,
                    field_of_study=field_of_study,
                    from_source=school_name,
                    description=input.get('description', ''),
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
    """
    Updates an existing education record.
    
    This mutation allows users to modify their existing education
    records with new information.
    
    Args:
        input (UpdateEducationInput): Update data containing:
            - uid: UID of the education record to update
            - Additional fields to update
    
    Returns:
        UpdateEducation: Response containing:
            - education: Updated education object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If education record not found or update fails
    
    Note:
        - Requires user authentication
        - Updates all provided fields dynamically
        - Uses error handling decorator
        - Maintains existing relationships
    """
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

            # If education fields are being updated, validate them
            school_name = input.get('from_source', education.from_source)
            degree = input.get('what', education.what)
            field_of_study = input.get('field_of_study', education.field_of_study)
            
            # Only validate if at least one of the three key fields is being updated
            if 'from_source' in input or 'what' in input or 'field_of_study' in input:
                validation_result = education_validation.validate_education_input(school_name, degree, field_of_study)
                if not validation_result.get('valid'):
                    raise GraphQLError(validation_result.get('error'))

            for key, value in input.items():
                setattr(education, key, value)

            education.save()
            return UpdateEducation(education=EducationType.from_neomodel(education), success=True, message=UserMessages.UPDATE_EDUCATION)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateEducation(education=None, success=False, message=message)



class CreateExperience(Mutation):
    """
    Creates a new experience record for a user's profile.
    
    This mutation allows users to add work experience entries to their profile
    with details like position, description, dates, and file attachments.
    
    Args:
        input (CreateExperienceInput): Experience data containing:
            - what: Position or role title
            - description: Experience description
            - created_on: Creation timestamp
            - from_source: Source of the experience record
            - file_id: List of file attachment IDs
            - from_date: Start date (optional)
            - to_date: End date (optional)
    
    Returns:
        CreateExperience: Response containing:
            - experience: Created experience object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If experience creation fails or file validation fails
    
    Note:
        - Requires user authentication
        - Validates file IDs if provided
        - Links experience to user's profile
        - Uses error handling decorator
    """
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
            
            # Validate experience input
            # from_source = company/organization name
            # what = title/position/role
            # description = work summary/responsibilities
            company_name = input.get('from_source', '')
            title = input.get('what', '')
            description = input.get('description', '')
            
            validation_result = experience_validation.validate_experience_input(company_name, title, description)
            if not validation_result.get('valid'):
                raise GraphQLError(validation_result.get('error'))
            
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            experience = Experience(
                what=title,
                description=description,
                created_on=input.get('created_on', ''),
                from_source=company_name,
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
    """
    Updates an existing experience record.
    
    This mutation allows users to modify their existing work experience
    records with new information.
    
    Args:
        input (UpdateExperienceInput): Update data containing:
            - uid: UID of the experience record to update
            - Additional fields to update
    
    Returns:
        UpdateExperience: Response containing:
            - experience: Updated experience object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If experience record not found or update fails
    
    Note:
        - Requires user authentication
        - Updates all provided fields dynamically
        - Uses error handling decorator
        - Maintains existing relationships
    """
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

            # If experience fields are being updated, validate them
            company_name = input.get('from_source', experience.from_source)
            title = input.get('what', experience.what)
            description = input.get('description', experience.description)
            
            # Only validate if at least one of the three key fields is being updated
            if 'from_source' in input or 'what' in input or 'description' in input:
                validation_result = experience_validation.validate_experience_input(company_name, title, description)
                if not validation_result.get('valid'):
                    raise GraphQLError(validation_result.get('error'))

            for key, value in input.items():
                setattr(experience, key, value)

            experience.save()
            return UpdateExperience(experience=ExperienceType.from_neomodel(experience), success=True, message=UserMessages.UPDATE_EXPERIENCE)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateExperience(experience=None, success=False, message=message)




class CreateSkill(Mutation):
    """
    Creates a new skill record for a user's profile.
    
    This mutation allows users to add skills to their profile
    with details like skill name, source, dates, and file attachments.
    
    Args:
        input (CreateSkillInput): Skill data containing:
            - what: Skill name or title
            - from_source: Source of the skill record
            - file_id: List of file attachment IDs
            - from_date: Start date (optional)
            - to_date: End date (optional)
    
    Returns:
        CreateSkill: Response containing:
            - skill: Created skill object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If skill creation fails or file validation fails
    
    Note:
        - Requires user authentication
        - Validates file IDs if provided
        - Links skill to user's profile
        - Uses error handling decorator
        - Handles optional date fields
    """
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
            
            # Validate skill input
            from_source = input.get('from_source', '')
            what = input.get('what', '')
            
            validation_result = skill_validation.validate_skill_input(from_source, what)
            if not validation_result.get('valid'):
                raise GraphQLError(validation_result.get('error'))
            
            if input.file_id:
                for id in input.file_id:
                    valid_id=get_valid_image(id)

            skill_data = {
                'what': what,
                'from_source': from_source,
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
    """
    Updates an existing skill record.
    
    This mutation allows users to modify their existing skill
    records with new information.
    
    Args:
        input (UpdateSkillInput): Update data containing:
            - uid: UID of the skill record to update
            - Additional fields to update
    
    Returns:
        UpdateSkill: Response containing:
            - skill: Updated skill object
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user is not authenticated
        Exception: If skill record not found or update fails
    
    Note:
        - Requires user authentication
        - Updates all provided fields dynamically
        - Uses error handling decorator
        - Maintains existing relationships
    """
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

            # If from_source or what are being updated, validate them
            from_source = input.get('from_source', skill.from_source)
            what = input.get('what', skill.what)
            
            # Only validate if either field is being updated
            if 'from_source' in input or 'what' in input:
                validation_result = skill_validation.validate_skill_input(from_source, what)
                if not validation_result.get('valid'):
                    raise GraphQLError(validation_result.get('error'))

            for key, value in input.items():
                setattr(skill, key, value)

            skill.save()
            return UpdateSkill(skill=SkillType.from_neomodel(skill), success=True, message=UserMessages.UPDATE_SKILL)
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return UpdateSkill(skill=None, success=False, message=message)





class GenerateTokenByEmail(graphene.Mutation):
    """
    Generates authentication tokens for a user by email ID.
    
    This mutation allows generating JWT tokens for an existing user
    using only their email address. Useful for administrative purposes
    or trusted integrations.
    
    Args:
        email (str): User's email address
    
    Returns:
        GenerateTokenByEmail: Response containing:
            - user: User object from Neo4j
            - token: JWT access token
            - refresh_token: JWT refresh token
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user not found or token generation fails
        Exception: If authentication process fails
    
    Note:
        - Requires user to exist in both Django and Neo4j databases
        - Generates fresh JWT tokens without password verification
        - Updates last login timestamp
        - Should be used with appropriate authorization controls
    """
    user = graphene.Field(UserType)
    token = graphene.String()
    refresh_token = graphene.String()
    success = graphene.Boolean()
    message = graphene.String()
    
    class Arguments:
        email = graphene.String(required=True)
    
    def mutate(self, info, email):
        try:
            # Validate email format
            if not email or '@' not in email:
                raise GraphQLError('Invalid email format')
            
            # Check if user exists in Django
            django_user = User.objects.filter(email=email).first()
            if not django_user:
                raise GraphQLError('User not found')
            
            # Check if user exists in Neo4j
            neo4j_user = Users.nodes.get_or_none(email=email)
            if not neo4j_user:
                raise GraphQLError('User profile not found in Neo4j')
            
            # Generate JWT tokens
            token = get_token(django_user)
            refresh_token = create_refresh_token(django_user)
            
            # Update last login
            django_user.last_login = timezone.now()
            django_user.save()
            update_last_login(None, django_user)
            
            return GenerateTokenByEmail(
                user=neo4j_user,
                token=token,
                refresh_token=refresh_token,
                success=True,
                message="Tokens generated successfully"
            )
            
        except GraphQLError:
            raise
        except Exception as error:
            message = getattr(error, 'message', str(error))
            return GenerateTokenByEmail(
                user=None,
                token=None,
                refresh_token=None,
                success=False,
                message=f"Token generation failed: {message}"
            )


class CreateVerifiedUser(Mutation):
    """
    Creates a fully verified user account with complete profile setup.
    
    This mutation creates a comprehensive user account that includes:
    - Django User model with authentication
    - Neo4j Users node with all relationships
    - Complete Profile with generated phone number
    - Verified OnboardingStatus (all fields set to True)
    - Default Score values
    - ConnectionStats for networking
    - Matrix profile for chat integration
    
    Args:
        input (CreateVerifiedUserInput): User creation data containing:
            - email: User's email address
            - first_name: User's first name
            - last_name: User's last name
            - password: User's password
            - user_type: Account type (defaults to "personal")
            - is_bot: Bot flag (defaults to False)
            - persona: Bot persona (optional)
            - gender: User gender (optional)
            - bio: User biography (optional)
            - designation: Job title (optional)
            - worksat: Workplace (optional)
            - lives_in: Location (optional)
            - state: State (optional)
            - city: City (optional)
            - profile_pic_id: Profile picture file ID (optional)
            - cover_image_id: Cover image file ID (optional)
    
    Returns:
        CreateVerifiedUser: Response containing:
            - user: Created user object from Neo4j
            - token: JWT access token
            - refresh_token: JWT refresh token
            - success: Boolean indicating operation success
            - message: Success or error message
    
    Raises:
        GraphQLError: If user already exists or creation fails
    
    Note:
        - Creates fully verified account (no OTP verification needed)
        - Generates unique Indian mobile number automatically
        - Sets up all required relationships and default values
        - Includes Matrix chat registration
    """
    user = graphene.Field(UserType)
    token = graphene.String()
    refresh_token = graphene.String()
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        input = CreateVerifiedUserInput(required=True)

    def mutate(self, info, input):
        try:
            # Extract input data
            email = input.get('email')
            first_name = input.get('first_name')
            last_name = input.get('last_name')
            password = input.get('password')
            user_type = input.get('user_type', 'personal')
            is_bot = input.get('is_bot', False)
            persona = input.get('persona')
            gender = input.get('gender')
            bio = input.get('bio')
            designation = input.get('designation')
            worksat = input.get('worksat')
            lives_in = input.get('lives_in')
            state = input.get('state')
            city = input.get('city')
            profile_pic_id = input.get('profile_pic_id')
            cover_image_id = input.get('cover_image_id')

            # Validate required fields
            if not email or not first_name or not last_name or not password:
                raise GraphQLError('Email, first name, last name, and password are required')

            # Validate email and password using existing validators
            user_validations.validate_create_user_inputs(email=email, password=password)

            # Check if user already exists
            if User.objects.filter(email=email).exists():
                raise GraphQLError(f'User with email {email} already exists')
            
            if Users.nodes.get_or_none(email=email):
                raise GraphQLError(f'User with email {email} already exists in Neo4j')

            # Generate unique username and mobile number
            username = generate_unique_username(f"{first_name}_{last_name}")
            mobile_number = generate_unique_indian_mobile()
            
            # Get realistic Indian data if not provided
            if is_bot and not (designation and worksat and city and state):
                indian_data = generate_realistic_indian_data()
                designation = designation or indian_data['designation']
                worksat = worksat or indian_data['company']
                city = city or indian_data['city']
                state = state or indian_data['state']
                lives_in = lives_in or indian_data['lives_in']

            # 1. Create Django User
            django_user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            django_user.set_password(password)
            django_user.save()

            # 2. Get the automatically created Neo4j Users node (created by signal)
            user_node = Users.nodes.get(user_id=str(django_user.id))
            user_node.first_name = first_name
            user_node.last_name = last_name
            user_node.user_type = user_type
            user_node.is_bot = is_bot
            user_node.is_active = True  # Set as active (verified)
            if persona:
                user_node.persona = persona
            user_node.save()

            # 3. Update the automatically created Profile with complete data
            profile = user_node.profile.single()
            if profile:
                profile.phone_number = mobile_number
                if gender:
                    profile.gender = gender
                if bio:
                    profile.bio = bio
                if designation:
                    profile.designation = designation
                if worksat:
                    profile.worksat = worksat
                if lives_in:
                    profile.lives_in = lives_in
                if state:
                    profile.state = state
                if city:
                    profile.city = city
                if profile_pic_id:
                    profile.profile_pic_id = profile_pic_id
                if cover_image_id:
                    profile.cover_image_id = cover_image_id
                profile.save()

                # 4. Update OnboardingStatus to fully verified
                onboarding = profile.onboarding.single()
                if onboarding:
                    onboarding.email_verified = True
                    onboarding.phone_verified = True
                    onboarding.username_selected = True
                    onboarding.first_name_set = True
                    onboarding.last_name_set = True
                    onboarding.gender_set = bool(gender)
                    onboarding.bio_set = bool(bio)
                    onboarding.state = bool(state)
                    onboarding.city = bool(city)
                    onboarding.save()

            # 5. Generate authentication tokens
            token = get_token(django_user)
            refresh_token = create_refresh_token(django_user)

            # 6. Create/Update Matrix profile (if it was created by signal)
            try:
                matrix_profile = MatrixProfile.objects.get(user=django_user)
                # Matrix registration was already attempted by signal
                # We can update it if needed, but signal handles the creation
            except MatrixProfile.DoesNotExist:
                # Create Matrix profile if signal didn't create it
                MatrixProfile.objects.create(
                    user=django_user,
                    pending_matrix_registration=True
                )

            return CreateVerifiedUser(
                user=UserType.from_neomodel(user_node),
                token=token,
                refresh_token=refresh_token,
                success=True,
                message="Verified user account created successfully with all required data"
            )

        except GraphQLError as error:
            return CreateVerifiedUser(
                user=None,
                token=None,
                refresh_token=None,
                success=False,
                message=str(error)
            )
        except Exception as error:
            # Better error message handling
            error_message = str(error)
            if hasattr(error, 'message'):
                error_message = error.message
            elif hasattr(error, 'args') and error.args:
                error_message = str(error.args[0])
            
            # Fallback for empty error messages
            if not error_message or error_message in ['{}', '']:
                error_message = f"User creation failed: {type(error).__name__}"
            
            return CreateVerifiedUser(
                user=None,
                token=None,
                refresh_token=None,
                success=False,
                message=error_message
            )


class Mutation(graphene.ObjectType):
    register_user = CreateUser.Field()
    register_userV2 = CreateUserV2.Field()
    login_by_username_email=LoginUsingUsernameEmail.Field()
    social_login = SocialLogin.Field()
    apple_social_login = AppleSocialLogin.Field()
    logout=Logout.Field()
    generate_token_by_email = GenerateTokenByEmail.Field()

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
    
    # Password Reset Flow (4-step process)
    find_user_by_email_or_username = FindUserByEmailOrUsername.Field()
    send_otp_for_password_reset = SendOTPForPasswordReset.Field()
    verify_otp_for_password_reset = VerifyOTPForPasswordReset.Field()
    update_password_with_otp_verification = UpdatePasswordWithOTPVerification.Field()
    
    # Password Reset Flow (4-step process)
    find_user_by_email_or_username = FindUserByEmailOrUsername.Field()
    send_otp_for_password_reset = SendOTPForPasswordReset.Field()
    verify_otp_for_password_reset = VerifyOTPForPasswordReset.Field()
    update_password_with_otp_verification = UpdatePasswordWithOTPVerification.Field()
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
    
    create_verified_user=CreateVerifiedUser.Field()


