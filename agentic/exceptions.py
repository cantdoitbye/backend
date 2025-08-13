# Agent-Specific Exception Classes
# This module defines custom exception classes for the agentic community management system.

from typing import Optional, Dict, Any


class AgentError(Exception):
    """
    Base exception class for all agent-related errors.
    
    This is the parent class for all agent-specific exceptions and provides
    common functionality for error handling and logging.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize the agent error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code for API responses
            details: Additional error details for debugging
            cause: The underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the exception to a dictionary for API responses.
        
        Returns:
            Dict containing error information
        """
        error_dict = {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details
        }
        
        if self.cause:
            error_dict['cause'] = str(self.cause)
        
        return error_dict
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


# Agent Service Exceptions

class AgentServiceError(AgentError):
    """Base exception for agent service operations."""
    pass


class AgentNotFoundError(AgentServiceError):
    """Raised when an agent cannot be found."""
    
    def __init__(self, agent_uid: str, message: Optional[str] = None):
        self.agent_uid = agent_uid
        message = message or f"Agent not found: {agent_uid}"
        super().__init__(
            message=message,
            error_code="AGENT_NOT_FOUND",
            details={"agent_uid": agent_uid}
        )


class AgentAlreadyExistsError(AgentServiceError):
    """Raised when trying to create an agent that already exists."""
    
    def __init__(self, agent_name: str, message: Optional[str] = None):
        self.agent_name = agent_name
        message = message or f"Agent already exists: {agent_name}"
        super().__init__(
            message=message,
            error_code="AGENT_ALREADY_EXISTS",
            details={"agent_name": agent_name}
        )


class AgentValidationError(AgentServiceError):
    """Raised when agent data fails validation."""
    
    def __init__(self, field: str, value: Any, reason: str, message: Optional[str] = None):
        self.field = field
        self.value = value
        self.reason = reason
        message = message or f"Invalid {field}: {reason}"
        super().__init__(
            message=message,
            error_code="AGENT_VALIDATION_ERROR",
            details={
                "field": field,
                "value": str(value),
                "reason": reason
            }
        )


class AgentCapabilityError(AgentServiceError):
    """Raised when there are issues with agent capabilities."""
    
    def __init__(self, capability: str, agent_uid: str, message: Optional[str] = None):
        self.capability = capability
        self.agent_uid = agent_uid
        message = message or f"Capability error for agent {agent_uid}: {capability}"
        super().__init__(
            message=message,
            error_code="AGENT_CAPABILITY_ERROR",
            details={
                "capability": capability,
                "agent_uid": agent_uid
            }
        )


# Agent Assignment Exceptions

class AgentAssignmentError(AgentError):
    """Base exception for agent assignment operations."""
    pass


class CommunityNotFoundError(AgentAssignmentError):
    """Raised when a community cannot be found."""
    
    def __init__(self, community_uid: str, message: Optional[str] = None):
        self.community_uid = community_uid
        message = message or f"Community not found: {community_uid}"
        super().__init__(
            message=message,
            error_code="COMMUNITY_NOT_FOUND",
            details={"community_uid": community_uid}
        )


class UserNotFoundError(AgentAssignmentError):
    """Raised when a user cannot be found."""
    
    def __init__(self, user_uid: str, message: Optional[str] = None):
        self.user_uid = user_uid
        message = message or f"User not found: {user_uid}"
        super().__init__(
            message=message,
            error_code="USER_NOT_FOUND",
            details={"user_uid": user_uid}
        )


class AssignmentNotFoundError(AgentAssignmentError):
    """Raised when an assignment cannot be found."""
    
    def __init__(self, assignment_uid: str, message: Optional[str] = None):
        self.assignment_uid = assignment_uid
        message = message or f"Assignment not found: {assignment_uid}"
        super().__init__(
            message=message,
            error_code="ASSIGNMENT_NOT_FOUND",
            details={"assignment_uid": assignment_uid}
        )


class CommunityAlreadyHasLeaderError(AgentAssignmentError):
    """Raised when trying to assign a leader to a community that already has one."""
    
    def __init__(self, community_uid: str, existing_leader_uid: str, message: Optional[str] = None):
        self.community_uid = community_uid
        self.existing_leader_uid = existing_leader_uid
        message = message or f"Community {community_uid} already has leader {existing_leader_uid}"
        super().__init__(
            message=message,
            error_code="COMMUNITY_ALREADY_HAS_LEADER",
            details={
                "community_uid": community_uid,
                "existing_leader_uid": existing_leader_uid
            }
        )


class AgentAlreadyAssignedError(AgentAssignmentError):
    """Raised when trying to assign an agent that is already assigned to the community."""
    
    def __init__(self, agent_uid: str, community_uid: str, message: Optional[str] = None):
        self.agent_uid = agent_uid
        self.community_uid = community_uid
        message = message or f"Agent {agent_uid} is already assigned to community {community_uid}"
        super().__init__(
            message=message,
            error_code="AGENT_ALREADY_ASSIGNED",
            details={
                "agent_uid": agent_uid,
                "community_uid": community_uid
            }
        )


class InvalidAssignmentStatusError(AgentAssignmentError):
    """Raised when trying to perform an operation on an assignment with invalid status."""
    
    def __init__(self, assignment_uid: str, current_status: str, required_status: str, message: Optional[str] = None):
        self.assignment_uid = assignment_uid
        self.current_status = current_status
        self.required_status = required_status
        message = message or f"Assignment {assignment_uid} has status {current_status}, but {required_status} is required"
        super().__init__(
            message=message,
            error_code="INVALID_ASSIGNMENT_STATUS",
            details={
                "assignment_uid": assignment_uid,
                "current_status": current_status,
                "required_status": required_status
            }
        )


# Agent Authentication and Authorization Exceptions

class AgentAuthError(AgentError):
    """Base exception for agent authentication and authorization."""
    pass


class AgentAuthenticationError(AgentAuthError):
    """Raised when agent authentication fails."""
    
    def __init__(self, agent_uid: Optional[str] = None, message: Optional[str] = None):
        self.agent_uid = agent_uid
        message = message or "Agent authentication failed"
        details = {"agent_uid": agent_uid} if agent_uid else {}
        super().__init__(
            message=message,
            error_code="AGENT_AUTHENTICATION_FAILED",
            details=details
        )


class AgentAuthorizationError(AgentAuthError):
    """Raised when agent authorization fails."""
    
    def __init__(self, agent_uid: str, community_uid: str, required_permission: str, message: Optional[str] = None):
        self.agent_uid = agent_uid
        self.community_uid = community_uid
        self.required_permission = required_permission
        message = message or f"Agent {agent_uid} lacks permission {required_permission} in community {community_uid}"
        super().__init__(
            message=message,
            error_code="AGENT_AUTHORIZATION_FAILED",
            details={
                "agent_uid": agent_uid,
                "community_uid": community_uid,
                "required_permission": required_permission
            }
        )


class InvalidPermissionError(AgentAuthError):
    """Raised when an invalid permission is specified."""
    
    def __init__(self, permission: str, message: Optional[str] = None):
        self.permission = permission
        message = message or f"Invalid permission: {permission}"
        super().__init__(
            message=message,
            error_code="INVALID_PERMISSION",
            details={"permission": permission}
        )


class PermissionDeniedError(AgentAuthError):
    """Raised when a specific permission is denied."""
    
    def __init__(self, agent_uid: str, action: str, resource: str, message: Optional[str] = None):
        self.agent_uid = agent_uid
        self.action = action
        self.resource = resource
        message = message or f"Permission denied: Agent {agent_uid} cannot {action} {resource}"
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            details={
                "agent_uid": agent_uid,
                "action": action,
                "resource": resource
            }
        )


# Agent Memory Exceptions

class AgentMemoryError(AgentError):
    """Base exception for agent memory operations."""
    pass


class MemoryNotFoundError(AgentMemoryError):
    """Raised when requested memory cannot be found."""
    
    def __init__(self, agent_uid: str, memory_type: str, message: Optional[str] = None):
        self.agent_uid = agent_uid
        self.memory_type = memory_type
        message = message or f"Memory not found for agent {agent_uid}, type {memory_type}"
        super().__init__(
            message=message,
            error_code="MEMORY_NOT_FOUND",
            details={
                "agent_uid": agent_uid,
                "memory_type": memory_type
            }
        )


class MemoryExpiredError(AgentMemoryError):
    """Raised when trying to access expired memory."""
    
    def __init__(self, agent_uid: str, memory_type: str, expired_at: str, message: Optional[str] = None):
        self.agent_uid = agent_uid
        self.memory_type = memory_type
        self.expired_at = expired_at
        message = message or f"Memory expired for agent {agent_uid}, type {memory_type} at {expired_at}"
        super().__init__(
            message=message,
            error_code="MEMORY_EXPIRED",
            details={
                "agent_uid": agent_uid,
                "memory_type": memory_type,
                "expired_at": expired_at
            }
        )


class MemoryStorageError(AgentMemoryError):
    """Raised when memory storage operations fail."""
    
    def __init__(self, agent_uid: str, operation: str, reason: str, message: Optional[str] = None):
        self.agent_uid = agent_uid
        self.operation = operation
        self.reason = reason
        message = message or f"Memory storage failed for agent {agent_uid}: {operation} - {reason}"
        super().__init__(
            message=message,
            error_code="MEMORY_STORAGE_ERROR",
            details={
                "agent_uid": agent_uid,
                "operation": operation,
                "reason": reason
            }
        )


class MemoryQuotaExceededError(AgentMemoryError):
    """Raised when agent memory quota is exceeded."""
    
    def __init__(self, agent_uid: str, current_usage: int, quota_limit: int, message: Optional[str] = None):
        self.agent_uid = agent_uid
        self.current_usage = current_usage
        self.quota_limit = quota_limit
        message = message or f"Memory quota exceeded for agent {agent_uid}: {current_usage}/{quota_limit} bytes"
        super().__init__(
            message=message,
            error_code="MEMORY_QUOTA_EXCEEDED",
            details={
                "agent_uid": agent_uid,
                "current_usage": current_usage,
                "quota_limit": quota_limit
            }
        )


# Agent Action Exceptions

class AgentActionError(AgentError):
    """Base exception for agent action operations."""
    pass


class InvalidActionError(AgentActionError):
    """Raised when an invalid action is attempted."""
    
    def __init__(self, action_type: str, agent_uid: str, reason: str, message: Optional[str] = None):
        self.action_type = action_type
        self.agent_uid = agent_uid
        self.reason = reason
        message = message or f"Invalid action {action_type} for agent {agent_uid}: {reason}"
        super().__init__(
            message=message,
            error_code="INVALID_ACTION",
            details={
                "action_type": action_type,
                "agent_uid": agent_uid,
                "reason": reason
            }
        )


class ActionExecutionError(AgentActionError):
    """Raised when action execution fails."""
    
    def __init__(self, action_type: str, agent_uid: str, error_details: str, message: Optional[str] = None):
        self.action_type = action_type
        self.agent_uid = agent_uid
        self.error_details = error_details
        message = message or f"Action execution failed: {action_type} by agent {agent_uid}"
        super().__init__(
            message=message,
            error_code="ACTION_EXECUTION_ERROR",
            details={
                "action_type": action_type,
                "agent_uid": agent_uid,
                "error_details": error_details
            }
        )


class ActionTimeoutError(AgentActionError):
    """Raised when an action times out."""
    
    def __init__(self, action_type: str, agent_uid: str, timeout_seconds: int, message: Optional[str] = None):
        self.action_type = action_type
        self.agent_uid = agent_uid
        self.timeout_seconds = timeout_seconds
        message = message or f"Action {action_type} by agent {agent_uid} timed out after {timeout_seconds} seconds"
        super().__init__(
            message=message,
            error_code="ACTION_TIMEOUT",
            details={
                "action_type": action_type,
                "agent_uid": agent_uid,
                "timeout_seconds": timeout_seconds
            }
        )


# Agent Configuration Exceptions

class AgentConfigurationError(AgentError):
    """Base exception for agent configuration issues."""
    pass


class InvalidAgentTypeError(AgentConfigurationError):
    """Raised when an invalid agent type is specified."""
    
    def __init__(self, agent_type: str, valid_types: list, message: Optional[str] = None):
        self.agent_type = agent_type
        self.valid_types = valid_types
        message = message or f"Invalid agent type: {agent_type}. Valid types: {', '.join(valid_types)}"
        super().__init__(
            message=message,
            error_code="INVALID_AGENT_TYPE",
            details={
                "agent_type": agent_type,
                "valid_types": valid_types
            }
        )


class InvalidAgentStatusError(AgentConfigurationError):
    """Raised when an invalid agent status is specified."""
    
    def __init__(self, status: str, valid_statuses: list, message: Optional[str] = None):
        self.status = status
        self.valid_statuses = valid_statuses
        message = message or f"Invalid agent status: {status}. Valid statuses: {', '.join(valid_statuses)}"
        super().__init__(
            message=message,
            error_code="INVALID_AGENT_STATUS",
            details={
                "status": status,
                "valid_statuses": valid_statuses
            }
        )


class AgentVersionMismatchError(AgentConfigurationError):
    """Raised when agent version is incompatible."""
    
    def __init__(self, agent_uid: str, current_version: str, required_version: str, message: Optional[str] = None):
        self.agent_uid = agent_uid
        self.current_version = current_version
        self.required_version = required_version
        message = message or f"Agent {agent_uid} version {current_version} is incompatible with required version {required_version}"
        super().__init__(
            message=message,
            error_code="AGENT_VERSION_MISMATCH",
            details={
                "agent_uid": agent_uid,
                "current_version": current_version,
                "required_version": required_version
            }
        )


# Agent Integration Exceptions

class AgentIntegrationError(AgentError):
    """Base exception for agent integration issues."""
    pass


class WebhookDeliveryError(AgentIntegrationError):
    """Raised when webhook delivery fails."""
    
    def __init__(self, webhook_url: str, event_type: str, status_code: int, message: Optional[str] = None):
        self.webhook_url = webhook_url
        self.event_type = event_type
        self.status_code = status_code
        message = message or f"Webhook delivery failed: {event_type} to {webhook_url} (HTTP {status_code})"
        super().__init__(
            message=message,
            error_code="WEBHOOK_DELIVERY_ERROR",
            details={
                "webhook_url": webhook_url,
                "event_type": event_type,
                "status_code": status_code
            }
        )


class NotificationDeliveryError(AgentIntegrationError):
    """Raised when notification delivery fails."""
    
    def __init__(self, notification_type: str, recipient: str, reason: str, message: Optional[str] = None):
        self.notification_type = notification_type
        self.recipient = recipient
        self.reason = reason
        message = message or f"Notification delivery failed: {notification_type} to {recipient} - {reason}"
        super().__init__(
            message=message,
            error_code="NOTIFICATION_DELIVERY_ERROR",
            details={
                "notification_type": notification_type,
                "recipient": recipient,
                "reason": reason
            }
        )


class ExternalServiceError(AgentIntegrationError):
    """Raised when external service integration fails."""
    
    def __init__(self, service_name: str, operation: str, error_details: str, message: Optional[str] = None):
        self.service_name = service_name
        self.operation = operation
        self.error_details = error_details
        message = message or f"External service error: {service_name} {operation} - {error_details}"
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={
                "service_name": service_name,
                "operation": operation,
                "error_details": error_details
            }
        )


# Utility functions for exception handling

def handle_agent_exception(exception: Exception) -> AgentError:
    """
    Convert generic exceptions to agent-specific exceptions.
    
    Args:
        exception: The original exception
        
    Returns:
        AgentError: Converted agent-specific exception
    """
    if isinstance(exception, AgentError):
        return exception
    
    # Convert common database exceptions
    if hasattr(exception, '__class__'):
        exception_name = exception.__class__.__name__
        
        if 'DoesNotExist' in exception_name:
            if 'Agent' in str(exception):
                return AgentNotFoundError("unknown", str(exception))
            elif 'Community' in str(exception):
                return CommunityNotFoundError("unknown", str(exception))
            elif 'User' in str(exception):
                return UserNotFoundError("unknown", str(exception))
        
        elif 'ValidationError' in exception_name:
            return AgentValidationError("unknown", str(exception), "Validation failed", str(exception))
        
        elif 'IntegrityError' in exception_name:
            return AgentAlreadyExistsError("unknown", str(exception))
    
    # Default to generic agent error
    return AgentError(
        message=str(exception),
        error_code="UNKNOWN_AGENT_ERROR",
        details={"original_exception": exception.__class__.__name__},
        cause=exception
    )


def get_error_response(exception: AgentError) -> Dict[str, Any]:
    """
    Get a standardized error response for API endpoints.
    
    Args:
        exception: The agent exception
        
    Returns:
        Dict containing standardized error response
    """
    return {
        "success": False,
        "error": exception.to_dict(),
        "message": exception.message,
        "error_code": exception.error_code
    }