import requests
from django.conf import settings
from django.contrib.auth.models import User
from auth_manager.models import Users
from graphql import GraphQLError
from graphql_jwt.shortcuts import create_refresh_token, get_token

class SocialAuthService:
    
    @staticmethod
    def verify_google_token(access_token):
        """
        Verify Google access token and get user info
        """
        try:
            # Verify token with Google
            url = f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
            response = requests.get(url)
            
            if response.status_code != 200:
                raise GraphQLError("Invalid Google access token")
            
            token_info = response.json()
            
            # Check if token is for our app
            if token_info.get('audience') != settings.GOOGLE_CLIENT_ID:
                raise GraphQLError("Token not for this application")
            
            # Get user info from Google
            user_info_url = f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
            user_response = requests.get(user_info_url)
            
            if user_response.status_code != 200:
                raise GraphQLError("Failed to get user info from Google")
            
            user_data = user_response.json()
            
            return {
                'provider_id': user_data.get('id'),
                'email': user_data.get('email'),
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', ''),
                'profile_picture': user_data.get('picture', ''),
                'verified_email': user_data.get('verified_email', False),
                'provider': 'google'
            }
            
        except requests.RequestException as e:
            raise GraphQLError(f"Error verifying Google token: {str(e)}")
    
    @staticmethod
    def verify_facebook_token(access_token):
        """
        Verify Facebook access token and get user info
        """
        try:
            # Verify token with Facebook
            app_token = f"{settings.FACEBOOK_APP_ID}|{settings.FACEBOOK_APP_SECRET}"
            verify_url = f"https://graph.facebook.com/debug_token"
            verify_params = {
                'input_token': access_token,
                'access_token': app_token
            }
            
            verify_response = requests.get(verify_url, params=verify_params)
            
            if verify_response.status_code != 200:
                raise GraphQLError("Invalid Facebook access token")
            
            verify_data = verify_response.json()
            
            if not verify_data.get('data', {}).get('is_valid'):
                raise GraphQLError("Facebook token is not valid")
            
            # Check if token is for our app
            if verify_data.get('data', {}).get('app_id') != settings.FACEBOOK_APP_ID:
                raise GraphQLError("Token not for this application")
            
            # Get user info from Facebook
            user_info_url = f"https://graph.facebook.com/me"
            user_params = {
                'access_token': access_token,
                'fields': 'id,email,first_name,last_name,picture'
            }
            
            user_response = requests.get(user_info_url, params=user_params)
            
            if user_response.status_code != 200:
                raise GraphQLError("Failed to get user info from Facebook")
            
            user_data = user_response.json()
            
            return {
                'provider_id': user_data.get('id'),
                'email': user_data.get('email'),
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'profile_picture': user_data.get('picture', {}).get('data', {}).get('url', ''),
                'verified_email': True,
                'provider': 'facebook'
            }
            
        except requests.RequestException as e:
            raise GraphQLError(f"Error verifying Facebook token: {str(e)}")
    
    @staticmethod
    def get_or_create_user_from_social_data(social_data, invite_token=None):
        """
        Get or create user from social authentication data
        Works with both Django User and Neo4j Users models
        """
        try:
            email = social_data['email']
            provider = social_data['provider']
            
            if not email:
                raise GraphQLError("Email is required for social login")
            
            # Check if Django User with this email already exists
            django_user = User.objects.filter(email=email).first()
            
            if django_user:
                # User exists, check if Users node exists
                try:
                    users_node = Users.nodes.get(user_id=str(django_user.id))
                    return django_user, users_node, False
                except Users.DoesNotExist:
                    # Django user exists but Users node doesn't - create it
                    users_node = Users(
                        user_id=str(django_user.id),
                        username=django_user.username,
                        email=django_user.email,
                        first_name=django_user.first_name or social_data['first_name'],
                        last_name=django_user.last_name or social_data['last_name'],
                        user_type="personal",
                        is_active=True
                    )
                    users_node.save()
                    return django_user, users_node, False
            
            # Create username with provider info to track social login
            base_username = email
            username = f"{base_username}_{provider}"
            
            # Ensure username is unique
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}_{counter}"
                counter += 1
            
            # Create new Django User
            django_user = User.objects.create_user(
                username=username,
                email=email,
                first_name=social_data['first_name'],
                last_name=social_data['last_name']
            )
            
            # Create Neo4j Users node
            users_node = Users(
                user_id=str(django_user.id),
                username=django_user.username,
                email=django_user.email,
                first_name=social_data['first_name'],
                last_name=social_data['last_name'],
                user_type="personal",
                is_active=True
            )
            users_node.save()
            
            # Handle invite if provided
            if invite_token:
                SocialAuthService.process_invite_for_social_user(django_user, users_node, invite_token)
            
            return django_user, users_node, True
            
        except Exception as e:
            raise GraphQLError(f"Error creating user from social data: {str(e)}")
    
    @staticmethod
    def process_invite_for_social_user(django_user, users_node, invite_token):
        """
        Process invite token for social login user
        """
        try:
            from auth_manager.models import Invite
            from connection.models import ConnectionV2, CircleV2
            from django.utils import timezone
            
            invite = Invite.objects.filter(invite_token=invite_token, is_deleted=False).first()
            
            if not invite:
                return
            
            if invite.expiry_date < timezone.now():
                return
            
            secondary_user = invite.inviter
            if not secondary_user:
                return
            
            # Get inviter's Users node
            secondary_user_node = Users.nodes.get(user_id=str(secondary_user.id))
            
            # Create connection between inviter and new user
            connection = ConnectionV2(
                connection_status="Accepted",
            )
            connection.save()
            connection.receiver.connect(secondary_user_node)
            connection.created_by.connect(users_node)
           
            users_node.connectionv2.connect(connection)
            secondary_user_node.connectionv2.connect(connection)

            # Create circle relationship
            circle_choice = CircleV2(
                initial_sub_relation="friend",
                initial_directionality="Unidirectional",
                user_relations={
                    users_node.uid: {
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

            # Update invite usage
            invite.usage_count += 1
            invite.last_used_timestamp = timezone.now()
            invite.login_users.add(django_user)
            invite.save()
            
        except Exception as e:
            print(f"Error processing invite for social user: {e}")
    
    @staticmethod
    def is_social_login_user(django_user):
        """
        Check if user was created via social login
        """
        return '_google' in django_user.username or '_facebook' in django_user.username
    
    @staticmethod
    def get_social_provider(django_user):
        """
        Get social provider from username
        """
        if '_google' in django_user.username:
            return 'google'
        elif '_facebook' in django_user.username:
            return 'facebook'
        return None