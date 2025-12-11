"""
JWT Authentication Middleware for Django Channels WebSocket
"""
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs
import logging

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token):
    """
    Get user from JWT token
    """
    try:
        from graphql_jwt.utils import jwt_decode
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Decode the token
        payload = jwt_decode(token)
        user_id = payload.get('user_id')
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                return user
            except User.DoesNotExist:
                logger.warning(f"User with id {user_id} not found")
                return AnonymousUser()
        
        return AnonymousUser()
        
    except Exception as e:
        logger.error(f"Error decoding JWT token: {e}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.
    
    Supports token in:
    1. Query parameter: ?token=xxx
    2. Authorization header: Authorization: Bearer xxx
    """
    
    async def __call__(self, scope, receive, send):
        # Get token from query string or headers
        token = None
        
        # Try to get from query parameters
        query_string = scope.get('query_string', b'').decode()
        if query_string:
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]
        
        # Try to get from headers if not in query
        if not token:
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode()
            
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Authenticate user with token
        if token:
            scope['user'] = await get_user_from_token(token)
            logger.info(f"WebSocket auth: User {scope['user']} authenticated")
        else:
            scope['user'] = AnonymousUser()
            logger.warning("WebSocket auth: No token provided")
        
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """
    Convenience function to wrap URLRouter with JWT auth middleware
    """
    return JWTAuthMiddleware(inner)
