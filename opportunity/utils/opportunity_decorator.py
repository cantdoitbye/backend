# opportunity/utils/opportunity_decorator.py

"""
Decorator for handling GraphQL errors in opportunity resolvers.

This decorator provides consistent error handling across all opportunity
mutations and queries, ensuring proper error messages and status codes
are returned to the frontend.
"""

from functools import wraps
from auth_manager.models import Users
from opportunity.models import Opportunity
from graphql import GraphQLError
from django.core.exceptions import PermissionDenied


def handle_graphql_opportunity_errors(func):
    """
    Decorator to handle GraphQL errors in opportunity resolvers.
    
    This decorator wraps opportunity mutations and queries to provide
    consistent error handling. It catches common exceptions and converts
    them to properly formatted GraphQL errors with appropriate status codes.
    
    Handles:
    - Missing authentication tokens
    - User not found errors
    - Opportunity not found errors
    - Permission errors
    - General exceptions
    
    Usage:
        @handle_graphql_opportunity_errors
        @login_required
        def mutate(self, info, input):
            # Your mutation logic here
            pass
    """
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
        
        except GraphQLError as gql_error:
            # Catch and re-raise GraphQL errors properly
            raise gql_error
        
        except Users.DoesNotExist:
            raise GraphQLError(
                "User not found",
                extensions={"code": "NOT_FOUND", "status_code": 404}
            )
        
        except Opportunity.DoesNotExist:
            raise GraphQLError(
                "Opportunity not found",
                extensions={"code": "NOT_FOUND", "status_code": 404}
            )

        except PermissionError:
            raise GraphQLError(
                "You do not have permission to perform this action",
                extensions={"code": "FORBIDDEN", "status_code": 403}
            )
        
        except PermissionDenied:
            raise GraphQLError(
                "Access denied. You do not have permission to perform this action.",
                extensions={"code": "FORBIDDEN", "status_code": 403}
            )
        
        except Exception as e:
            # Catch any other unexpected errors
            raise GraphQLError(
                f"Internal Server Error: {str(e)}",
                extensions={"code": "INTERNAL_SERVER_ERROR", "status_code": 500}
            )
    
    return wrapper
