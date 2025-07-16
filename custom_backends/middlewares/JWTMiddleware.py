from graphql_jwt.utils import jwt_decode
from graphql import GraphQLError

class JWTMiddleware:
    def resolve(self, next, root, info, **kwargs):
        auth_header = info.context.META.get('HTTP_AUTHORIZATION', None)
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                payload = jwt_decode(token)
                info.context.payload = payload
            except Exception as e:
                raise GraphQLError(f"Invalid token: {str(e)}")
        return next(root, info, **kwargs)
