# Agent Error Handling Middleware
# This module provides middleware for handling agent-related errors consistently.

import logging
import traceback
from typing import Any, Dict, Optional
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from graphql import GraphQLError

from ..exceptions import (
    AgentError, AgentServiceError, AgentAuthError, AgentMemoryError,
    AgentNotFoundError, CommunityNotFoundError, UserNotFoundError,
    AgentAuthenticationError, AgentAuthorizationError,
    handle_agent_exception, get_error_response
)


logger = logging.getLogger(__name__)


class AgentErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware for handling agent-related errors in HTTP requests.
    
    This middleware catches agent exceptions and converts them to
    appropriate HTTP responses with consistent error formatting.
    """
    
    def process_exception(self, request, exception):
        """
        Process exceptions that occur during request handling.
        
        Args:
            request: The HTTP request object
            exception: The exception that occurred
            
        Returns:
            JsonResponse with error details or None to continue normal processing
        """
        # Only handle agent-related exceptions
        if not isinstance(exception, AgentError):
            # Try to convert generic exceptions to agent exceptions
            try:
                agent_exception = handle_agent_exception(exception)
                if not isinstance(agent_exception, AgentError):
                    return None  # Let Django handle non-agent exceptions
                exception = agent_exception
            except Exception:
                return None  # Let Django handle if conversion fails
        
        # Log the error
        logger.error(
            f"Agent error in {request.method} {request.path}: {exception}",
            extra={
                'exception_type': exception.__class__.__name__,
                'error_code': exception.error_code,
                'details': exception.details,
                'user': getattr(request, 'user', None),
                'request_data': self._get_safe_request_data(request)
            }
        )
        
        # Determine HTTP status code based on exception type
        status_code = self._get_status_code_for_exception(exception)
        
        # Create error response
        error_response = get_error_response(exception)
        
        # Add request context if available
        if hasattr(request, 'user') and request.user:
            error_response['request_context'] = {
                'user_id': getattr(request.user, 'uid', None),
                'path': request.path,
                'method': request.method
            }
        
        return JsonResponse(error_response, status=status_code)
    
    def _get_status_code_for_exception(self, exception: AgentError) -> int:
        """
        Determine the appropriate HTTP status code for an agent exception.
        
        Args:
            exception: The agent exception
            
        Returns:
            int: HTTP status code
        """
        status_code_map = {
            # Not found errors
            AgentNotFoundError: 404,
            CommunityNotFoundError: 404,
            UserNotFoundError: 404,
            
            # Authentication errors
            AgentAuthenticationError: 401,
            
            # Authorization errors
            AgentAuthorizationError: 403,
            
            # Validation errors
            'AgentValidationError': 400,
            'AgentCapabilityError': 400,
            'InvalidAgentTypeError': 400,
            'InvalidAgentStatusError': 400,
            
            # Conflict errors
            'AgentAlreadyExistsError': 409,
            'CommunityAlreadyHasLeaderError': 409,
            'AgentAlreadyAssignedError': 409,
            
            # Service errors
            'MemoryStorageError': 500,
            'ActionExecutionError': 500,
            'WebhookDeliveryError': 502,
            'ExternalServiceError': 502,
        }
        
        # Check by exception class
        for exc_class, status_code in status_code_map.items():
            if isinstance(exception, exc_class):
                return status_code
        
        # Check by exception class name (for string keys)
        exception_name = exception.__class__.__name__
        if exception_name in status_code_map:
            return status_code_map[exception_name]
        
        # Default to 500 for unknown errors
        return 500
    
    def _get_safe_request_data(self, request) -> Dict[str, Any]:
        """
        Extract safe request data for logging (excluding sensitive information).
        
        Args:
            request: The HTTP request object
            
        Returns:
            Dict containing safe request data
        """
        safe_data = {
            'method': request.method,
            'path': request.path,
            'content_type': request.content_type,
        }
        
        # Add query parameters (excluding sensitive ones)
        if request.GET:
            sensitive_params = {'password', 'token', 'secret', 'key'}
            safe_params = {
                k: v for k, v in request.GET.items()
                if not any(sensitive in k.lower() for sensitive in sensitive_params)
            }
            if safe_params:
                safe_data['query_params'] = safe_params
        
        # Add headers (excluding sensitive ones)
        if hasattr(request, 'META'):
            sensitive_headers = {'authorization', 'cookie', 'x-api-key'}
            safe_headers = {
                k: v for k, v in request.META.items()
                if k.startswith('HTTP_') and 
                not any(sensitive in k.lower() for sensitive in sensitive_headers)
            }
            if safe_headers:
                safe_data['headers'] = safe_headers
        
        return safe_data


class GraphQLAgentErrorHandler:
    """
    Error handler for GraphQL operations involving agents.
    
    This class provides methods to handle agent exceptions in GraphQL
    resolvers and mutations, converting them to appropriate GraphQL errors.
    """
    
    @staticmethod
    def handle_agent_error(exception: Exception, context: Optional[Dict[str, Any]] = None) -> GraphQLError:
        """
        Handle agent exceptions in GraphQL operations.
        
        Args:
            exception: The exception that occurred
            context: Additional context information
            
        Returns:
            GraphQLError: Formatted GraphQL error
        """
        # Convert to agent exception if needed
        if not isinstance(exception, AgentError):
            exception = handle_agent_exception(exception)
        
        # Log the error
        logger.error(
            f"GraphQL agent error: {exception}",
            extra={
                'exception_type': exception.__class__.__name__,
                'error_code': exception.error_code,
                'details': exception.details,
                'context': context
            }
        )
        
        # Create GraphQL error with extensions
        extensions = {
            'code': exception.error_code,
            'exception_type': exception.__class__.__name__,
            'details': exception.details
        }
        
        if context:
            extensions['context'] = context
        
        return GraphQLError(
            message=exception.message,
            extensions=extensions
        )
    
    @staticmethod
    def wrap_resolver(resolver_func):
        """
        Decorator to wrap GraphQL resolvers with agent error handling.
        
        Args:
            resolver_func: The resolver function to wrap
            
        Returns:
            Wrapped resolver function
        """
        def wrapper(*args, **kwargs):
            try:
                return resolver_func(*args, **kwargs)
            except Exception as e:
                # Extract context from resolver arguments
                context = {}
                if len(args) >= 2:
                    info = args[1]
                    if hasattr(info, 'context'):
                        context['user'] = getattr(info.context, 'user', None)
                        context['request_path'] = getattr(info.context, 'path', None)
                
                raise GraphQLAgentErrorHandler.handle_agent_error(e, context)
        
        return wrapper
    
    @staticmethod
    def wrap_mutation(mutation_func):
        """
        Decorator to wrap GraphQL mutations with agent error handling.
        
        Args:
            mutation_func: The mutation function to wrap
            
        Returns:
            Wrapped mutation function
        """
        def wrapper(*args, **kwargs):
            try:
                return mutation_func(*args, **kwargs)
            except Exception as e:
                # Extract context from mutation arguments
                context = {}
                if len(args) >= 2:
                    info = args[1]
                    if hasattr(info, 'context'):
                        context['user'] = getattr(info.context, 'user', None)
                        context['request_path'] = getattr(info.context, 'path', None)
                
                # For mutations, we might want to return error responses instead of raising
                if isinstance(e, AgentError):
                    # Return mutation response with error
                    return {
                        'success': False,
                        'message': e.message,
                        'errors': [e.message],
                        'error_code': e.error_code
                    }
                
                raise GraphQLAgentErrorHandler.handle_agent_error(e, context)
        
        return wrapper


class AgentErrorLogger:
    """
    Specialized logger for agent errors with structured logging.
    """
    
    def __init__(self, logger_name: str = 'agentic.errors'):
        """
        Initialize the error logger.
        
        Args:
            logger_name: Name of the logger to use
        """
        self.logger = logging.getLogger(logger_name)
    
    def log_agent_error(
        self,
        exception: AgentError,
        operation: str,
        agent_uid: Optional[str] = None,
        community_uid: Optional[str] = None,
        user_uid: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """
        Log an agent error with structured information.
        
        Args:
            exception: The agent exception
            operation: The operation that failed
            agent_uid: UID of the agent involved
            community_uid: UID of the community involved
            user_uid: UID of the user involved
            additional_context: Additional context information
        """
        log_data = {
            'operation': operation,
            'exception_type': exception.__class__.__name__,
            'error_code': exception.error_code,
            'message': exception.message,
            'details': exception.details
        }
        
        if agent_uid:
            log_data['agent_uid'] = agent_uid
        if community_uid:
            log_data['community_uid'] = community_uid
        if user_uid:
            log_data['user_uid'] = user_uid
        if additional_context:
            log_data['additional_context'] = additional_context
        
        # Include stack trace for debugging
        if exception.cause:
            log_data['stack_trace'] = traceback.format_exception(
                type(exception.cause),
                exception.cause,
                exception.cause.__traceback__
            )
        
        self.logger.error(
            f"Agent operation failed: {operation}",
            extra=log_data
        )
    
    def log_agent_warning(
        self,
        message: str,
        operation: str,
        agent_uid: Optional[str] = None,
        community_uid: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """
        Log an agent warning with structured information.
        
        Args:
            message: Warning message
            operation: The operation that generated the warning
            agent_uid: UID of the agent involved
            community_uid: UID of the community involved
            additional_context: Additional context information
        """
        log_data = {
            'operation': operation,
            'message': message
        }
        
        if agent_uid:
            log_data['agent_uid'] = agent_uid
        if community_uid:
            log_data['community_uid'] = community_uid
        if additional_context:
            log_data['additional_context'] = additional_context
        
        self.logger.warning(
            f"Agent operation warning: {operation}",
            extra=log_data
        )


# Global error logger instance
agent_error_logger = AgentErrorLogger()


# Decorator functions for easy use

def handle_agent_errors(func):
    """
    Decorator to handle agent errors in regular functions.
    
    Args:
        func: Function to wrap with error handling
        
    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if not isinstance(e, AgentError):
                e = handle_agent_exception(e)
            
            # Log the error
            agent_error_logger.log_agent_error(
                exception=e,
                operation=func.__name__,
                additional_context={'args': str(args), 'kwargs': str(kwargs)}
            )
            
            raise e
    
    return wrapper


def handle_graphql_agent_errors(func):
    """
    Decorator to handle agent errors in GraphQL resolvers/mutations.
    
    Args:
        func: GraphQL function to wrap with error handling
        
    Returns:
        Wrapped function
    """
    return GraphQLAgentErrorHandler.wrap_resolver(func)