from django.shortcuts import render

# Create your views here.
from graphene_django.views import GraphQLView
from graphql import GraphQLError
from django.http import JsonResponse

class CustomGraphQLView(GraphQLView):
    def format_error(self, error):
        """Custom error formatting to include status codes."""
        status_code = 400  # Default status code

        error_message = str(error)

        # Handle expired token error message
        if "Invalid token: Signature has expired" in error_message:
            return {
                "message": "Authentication failed. Token has expired.",
                "extensions": {
                    "code": "TOKEN_EXPIRED",
                    "status_code": 401
                },
                "path": error.path,
            }

        if isinstance(error, GraphQLError) and getattr(error, "extensions", None):
            status_code = error.extensions.get("status_code", 400)  # Ensure extracted status code

        return {
            "message": error.message,
            "extensions": {
                "code": error.extensions.get("code", "BAD_REQUEST"),
                "status_code": status_code
            },
            "path": error.path,
        }

    def render_graphql_response(self, response, request):
        """Modify response to return correct status code while keeping HTTP 200."""
        formatted_errors = [self.format_error(error) for error in response.errors] if response.errors else None

        response_data = {
            "data": response.data if response.data else None,
            "errors": formatted_errors if formatted_errors else None,
            "path": response.path if response.path else None,
        }

        return JsonResponse(response_data, status=200)
