from functools import wraps
from auth_manager.models import Users, Profile,Education,Achievement,Skill,Experience
from graphql import GraphQLError
from django.core.exceptions import PermissionDenied

def handle_graphql_auth_manager_errors(func):
    """Decorator to handle GraphQL errors in resolvers."""
    @wraps(func)
    def wrapper(self, info, *args, **kwargs):
        try:
            # Ensure payload exists before executing the function
            payload = getattr(info.context, "payload", None)
            if not payload:
                raise GraphQLError(
                    "Authentication failed. Token is missing.",
                    extensions={"code": "TOKEN_MISSING", "status_code": 401},
                )

            return func(self, info, *args, **kwargs)  # Execute the resolver function
        
        except GraphQLError as gql_error:  # Catch and re-raise GraphQL errors properly
            raise gql_error
        
        except Users.DoesNotExist:
            raise GraphQLError(
                "User not found",
                extensions={"code": "NOT_FOUND", "status_code": 404}
            )
        
        except Profile.DoesNotExist:
            raise GraphQLError(
                "Profile not found",
                extensions={"code": "NOT_FOUND", "status_code": 404}
            )
        except Achievement.DoesNotExist:
            raise GraphQLError(
                "Achievement not found",
                extensions={"code": "NOT_FOUND", "status_code": 404}
            )
        
        except Experience.DoesNotExist:
            raise GraphQLError(
                "Experience not found",
                extensions={"code": "NOT_FOUND", "status_code": 404}
            )
        
        except Skill.DoesNotExist:
            raise GraphQLError(
                "Skill not found",
                extensions={"code": "NOT_FOUND", "status_code": 404}
            )
        
        except Education.DoesNotExist:
            raise GraphQLError(
                "Education not found",
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
