from graphql_jwt.settings import jwt_settings
from graphql_jwt.utils import jwt_payload
from graphql_jwt.utils import jwt_decode
from graphql import GraphQLError

def custom_jwt_payload(user, context=None):
    payload = jwt_payload(user, context)
    payload['user_id'] = user.id
    payload['username'] = user.username
    payload['email'] = user.email
    return payload


def get_user_from_info(info):
    auth_header = info.context.META.get('HTTP_AUTHORIZATION', None)
    if not auth_header:
        raise GraphQLError("Authorization header missing")

    try:
        token = auth_header.split(' ')[1]
        payload = jwt_decode(token)
        return payload
    except Exception as e:
        raise GraphQLError(f"Invalid token: {str(e)}")

