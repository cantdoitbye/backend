from functools import wraps
from auth_manager.models import Users
from story.models import Story
from graphql import GraphQLError

def validate_different_users(func):
    @wraps(func)
    def wrapper(self, info, user_uid, *args, **kwargs):
        payload = info.context.payload
        login_user_id = payload.get('user_id')  # Assuming this stores UID
        login_user=Users.nodes.get(user_id=login_user_id)
        if login_user.uid == user_uid:
            raise GraphQLError("You cannot fetch your own stories using this API.")
        return func(self, info, user_uid, *args, **kwargs)
    return wrapper

def handle_graphql_story_errors(func):
    """Decorator to handle GraphQL errors in resolvers."""
    @wraps(func)
    def wrapper(self, info, *args, **kwargs):
        try:
            # Ensure payload exists before executing the function
            payload = getattr(info.context, "payload", None)
            if not payload:
                raise GraphQLError(
                    "Authentication failed. Token is missing.",
                    extensions={"code": "TOKEN_MISSING", "status_code": 401}
                )

            return func(self, info, *args, **kwargs)  # Execute the resolver function
        
        except GraphQLError as gql_error:  # Catch and re-raise GraphQL errors properly
            raise gql_error
        
        except Users.DoesNotExist:
            raise GraphQLError(
                "User not found",
                extensions={"code": "NOT_FOUND", "status_code": 404}
            )
        
        except Story.DoesNotExist:
            raise GraphQLError(
                "Story not found",
                extensions={"code": "NOT_FOUND", "status_code": 404}
            )

        except PermissionError:
            raise GraphQLError(
                "You do not have permission to perform this action",
                extensions={"code": "FORBIDDEN", "status_code": 403}
            )
        
        except Exception as e:  # Catch any other unexpected errors
            raise GraphQLError(
                f"Internal Server Error: {str(e)}",
                extensions={"code": "INTERNAL_SERVER_ERROR", "status_code": 500}
            )
    
    return wrapper
