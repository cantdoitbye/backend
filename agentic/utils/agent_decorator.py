# Agent Utility Decorators
# This module provides decorators for agent-related operations.

import functools
import logging
from typing import Any, Callable

from ..services.auth_service import AgentAuthService, AgentAuthError, AgentAuthenticationError, AgentAuthorizationError
from ..services.agent_service import AgentServiceError, AgentNotFoundError, CommunityNotFoundError, UserNotFoundError
from ..services.memory_service import AgentMemoryError, MemoryNotFoundError, MemoryExpiredError


logger = logging.getLogger(__name__)


def handle_agent_errors(func: Callable) -> Callable:
    """
    Decorator to handle common agent-related errors.
    
    This decorator catches and logs common exceptions that can occur
    during agent operations and ensures consistent error handling.
    
    Args:
        func: The function to wrap with error handling
        
    Returns:
        Callable: The wrapped function with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (AgentNotFoundError, CommunityNotFoundError, UserNotFoundError) as e:
            logger.warning(f"Resource not found in {func.__name__}: {str(e)}")
            raise
        except (AgentAuthenticationError, AgentAuthorizationError) as e:
            logger.warning(f"Authentication/authorization error in {func.__name__}: {str(e)}")
            raise
        except (AgentServiceError, AgentAuthError, AgentMemoryError) as e:
            logger.error(f"Service error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise
    
    return wrapper


def require_authentication(func: Callable) -> Callable:
    """
    Decorator to require user authentication for agent operations.
    
    This decorator ensures that the user is authenticated before
    allowing agent operations to proceed.
    
    Args:
        func: The function to wrap with authentication requirement
        
    Returns:
        Callable: The wrapped function with authentication check
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get the GraphQL info object (usually the second argument)
        info = None
        if len(args) >= 2:
            info = args[1]
        
        # Check if user is authenticated
        if not info or not hasattr(info, 'context') or not hasattr(info.context, 'user'):
            logger.warning(f"Unauthenticated access attempt to {func.__name__}")
            raise AgentAuthenticationError("Authentication required for this operation")
        
        if not info.context.user or not hasattr(info.context.user, 'uid'):
            logger.warning(f"Invalid user context in {func.__name__}")
            raise AgentAuthenticationError("Valid user authentication required")
        
        return func(*args, **kwargs)
    
    return wrapper


def require_agent_permission(permission: str):
    """
    Decorator factory to require specific agent permissions.
    
    This decorator ensures that the agent has the required permission
    before allowing the operation to proceed.
    
    Args:
        permission: The permission required for the operation
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract agent_uid and community_uid from kwargs or args
            agent_uid = kwargs.get('agent_uid')
            community_uid = kwargs.get('community_uid')
            
            # If not in kwargs, try to extract from input object
            if not agent_uid or not community_uid:
                input_obj = kwargs.get('input')
                if input_obj:
                    agent_uid = agent_uid or getattr(input_obj, 'agent_uid', None)
                    community_uid = community_uid or getattr(input_obj, 'community_uid', None)
            
            if not agent_uid or not community_uid:
                logger.error(f"Missing agent_uid or community_uid for permission check in {func.__name__}")
                raise AgentAuthorizationError("Agent and community identification required for permission check")
            
            # Check permission
            auth_service = AgentAuthService()
            if not auth_service.check_permission(agent_uid, community_uid, permission):
                logger.warning(f"Permission denied: {permission} for agent {agent_uid} in community {community_uid}")
                raise AgentAuthorizationError(f"Agent does not have required permission: {permission}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_agent_action(action_type: str):
    """
    Decorator factory to automatically log agent actions.
    
    This decorator logs agent actions for audit purposes.
    
    Args:
        action_type: The type of action being performed
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract agent_uid and community_uid
            agent_uid = kwargs.get('agent_uid')
            community_uid = kwargs.get('community_uid')
            
            # If not in kwargs, try to extract from input object
            if not agent_uid or not community_uid:
                input_obj = kwargs.get('input')
                if input_obj:
                    agent_uid = agent_uid or getattr(input_obj, 'agent_uid', None)
                    community_uid = community_uid or getattr(input_obj, 'community_uid', None)
            
            start_time = None
            success = False
            error_message = None
            
            try:
                import time
                start_time = time.time()
                
                result = func(*args, **kwargs)
                success = True
                return result
                
            except Exception as e:
                error_message = str(e)
                raise
                
            finally:
                # Log the action if we have the required information
                if agent_uid and community_uid and start_time is not None:
                    try:
                        import time
                        execution_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
                        
                        auth_service = AgentAuthService()
                        auth_service.log_agent_action(
                            agent_uid=agent_uid,
                            community_uid=community_uid,
                            action_type=action_type,
                            details=kwargs,
                            success=success,
                            error_message=error_message,
                            execution_time_ms=execution_time
                        )
                    except Exception as log_error:
                        logger.error(f"Failed to log agent action: {str(log_error)}")
        
        return wrapper
    return decorator


def validate_agent_input(func: Callable) -> Callable:
    """
    Decorator to validate agent input parameters.
    
    This decorator performs basic validation on agent-related inputs
    to ensure they meet minimum requirements.
    
    Args:
        func: The function to wrap with input validation
        
    Returns:
        Callable: The wrapped function with input validation
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get input object if present
        input_obj = kwargs.get('input')
        if not input_obj:
            return func(*args, **kwargs)
        
        # Validate agent_uid format if present
        agent_uid = getattr(input_obj, 'agent_uid', None)
        if agent_uid and not _is_valid_uid(agent_uid):
            raise AgentServiceError(f"Invalid agent UID format: {agent_uid}")
        
        # Validate community_uid format if present
        community_uid = getattr(input_obj, 'community_uid', None)
        if community_uid and not _is_valid_uid(community_uid):
            raise AgentServiceError(f"Invalid community UID format: {community_uid}")
        
        # Validate agent name if present
        name = getattr(input_obj, 'name', None)
        if name and (len(name.strip()) < 2 or len(name) > 100):
            raise AgentServiceError("Agent name must be between 2 and 100 characters")
        
        # Validate agent type if present
        agent_type = getattr(input_obj, 'agent_type', None)
        if agent_type and agent_type not in ['COMMUNITY_LEADER', 'MODERATOR', 'ASSISTANT']:
            raise AgentServiceError(f"Invalid agent type: {agent_type}")
        
        # Validate capabilities if present
        capabilities = getattr(input_obj, 'capabilities', None)
        if capabilities:
            if not isinstance(capabilities, list):
                raise AgentServiceError("Capabilities must be a list")
            if len(capabilities) == 0:
                raise AgentServiceError("At least one capability is required")
            for capability in capabilities:
                if not isinstance(capability, str) or len(capability.strip()) == 0:
                    raise AgentServiceError("All capabilities must be non-empty strings")
        
        return func(*args, **kwargs)
    
    return wrapper


def _is_valid_uid(uid: str) -> bool:
    """
    Validate UID format.
    
    Args:
        uid: The UID to validate
        
    Returns:
        bool: True if the UID format is valid
    """
    if not isinstance(uid, str):
        return False
    
    # Basic UID validation - should be non-empty string with reasonable length
    uid = uid.strip()
    if len(uid) < 8 or len(uid) > 64:
        return False
    
    # Should contain only alphanumeric characters, hyphens, and underscores
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', uid):
        return False
    
    return True


def rate_limit(max_calls: int = 100, time_window: int = 60):
    """
    Decorator factory for rate limiting agent operations.
    
    This decorator implements basic rate limiting to prevent abuse
    of agent operations.
    
    Args:
        max_calls: Maximum number of calls allowed in the time window
        time_window: Time window in seconds
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable) -> Callable:
        # Simple in-memory rate limiting (in production, use Redis or similar)
        call_history = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            # Get user identifier
            info = args[1] if len(args) >= 2 else None
            user_id = None
            
            if info and hasattr(info, 'context') and hasattr(info.context, 'user'):
                user_id = getattr(info.context.user, 'uid', None)
            
            if not user_id:
                # If we can't identify the user, allow the operation
                return func(*args, **kwargs)
            
            current_time = time.time()
            
            # Clean old entries
            if user_id in call_history:
                call_history[user_id] = [
                    call_time for call_time in call_history[user_id]
                    if current_time - call_time < time_window
                ]
            else:
                call_history[user_id] = []
            
            # Check rate limit
            if len(call_history[user_id]) >= max_calls:
                logger.warning(f"Rate limit exceeded for user {user_id} in {func.__name__}")
                raise AgentServiceError(f"Rate limit exceeded. Maximum {max_calls} calls per {time_window} seconds.")
            
            # Record this call
            call_history[user_id].append(current_time)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator