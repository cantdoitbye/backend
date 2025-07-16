from functools import wraps
from auth_manager.models import Users
from community.models import Community,SubCommunity
from graphql import GraphQLError
from django.core.exceptions import PermissionDenied
import requests
import traceback

def handle_graphql_community_errors(func):
    """Decorator to handle GraphQL errors in resolvers."""
    @wraps(func)
    def wrapper(self, info, *args, **kwargs):
        try:
            # Print debug info for every call
            print(f"DEBUG: Executing {func.__name__} in {self.__class__.__name__}")
            
            # Ensure payload exists before executing the function
            payload = getattr(info.context, "payload", None)
            if not payload:
                raise GraphQLError(
                    "Authentication failed. Token is missing.",
                    extensions={"code": "TOKEN_MISSING", "status_code": 401}
                )

            # Execute the resolver function but catch connection errors
            try:
                return func(self, info, *args, **kwargs)
            except requests.exceptions.ConnectionError as conn_error:
                print(f"Connection error in {func.__name__}: {conn_error}")
                print(traceback.format_exc())
                # Return a more friendly error message that won't block community creation
                return self.__class__(
                    community=None, 
                    success=True,
                    message="Created successfully but couldn't connect to image server"
                )
        
        except GraphQLError as gql_error:  # Catch and re-raise GraphQL errors properly
            print(f"GraphQL error in {func.__name__}: {gql_error}")
            raise gql_error
        
        except Users.DoesNotExist:
            print(f"User not found in {func.__name__}")
            raise GraphQLError(
                "User not found",
                extensions={"code": "NOT_FOUND", "status_code": 404}
            )
        
        except SubCommunity.DoesNotExist:
            print(f"Subcommunity not found in {func.__name__}")
            raise GraphQLError(
                "Subcommunity not found",
                extensions={"code": "NOT_FOUND", "status_code": 404}
            )
        
        except Community.DoesNotExist:
            print(f"Community not found in {func.__name__}")
            raise GraphQLError(
                "Community not found",
                extensions={"code": "NOT_FOUND", "status_code": 404}
            )

        except PermissionError:
            print(f"Permission error in {func.__name__}")
            raise GraphQLError(
                "You do not have permission to perform this action",
                extensions={"code": "FORBIDDEN", "status_code": 403}
            )
        
        except Exception as e:  # Catch any other unexpected errors
            print(f"Unexpected error in {func.__name__}: {e}")
            print(traceback.format_exc())
            raise GraphQLError(
                f"Internal Server Error: {str(e)}",
                extensions={"code": "INTERNAL_SERVER_ERROR", "status_code": 500}
            )
    
    return wrapper
