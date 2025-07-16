import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from graphql_jwt.utils import jwt_decode
from graphql_jwt.exceptions import JSONWebTokenError, JSONWebTokenExpired
from rest_framework.exceptions import AuthenticationFailed
from urllib.parse import urlparse
import requests

User = get_user_model()

def get_user_from_token(request):
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        raise AuthenticationFailed('Authorization Faliure')

    try:
        token = auth_header.split(' ')[1]  # Assuming the header is in the format "Bearer <token>"
        decoded_token = jwt_decode(token)  # Decode the token using graphql_jwt's utility

        user_id = decoded_token.get('user_id')
        if not user_id:
            raise AuthenticationFailed('User ID not found in token.')

        try:
            user = User.objects.get(id=user_id)
            return user
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found.')

    except JSONWebTokenExpired:
        raise AuthenticationFailed('Token has expired.')
    except (JSONWebTokenError, jwt.DecodeError):
        raise AuthenticationFailed('Token is invalid.')




def extract_hostname(url):
    parsed_url = urlparse(url)
    return parsed_url.hostname



def get_image_url(image_id, context):
    if not image_id:
        return None

    url = f"http://localhost:8000/image/{image_id}/"
    try:
        response = requests.get(url, headers={'Authorization': context.META.get('HTTP_AUTHORIZATION')})
        if response.status_code == 200:
            return response.text
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image URL: {e}")
        return None
