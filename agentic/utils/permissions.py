# Agent Permission Utilities
# This module provides utilities for agent permission checking and validation.

from typing import List, Dict, Any, Optional, Callable
from functools import wraps
import logging

from ..services.auth_service import AgentAuthService, AgentAuthenticationError, AgentAuthorizationError
from ..models import Agent, AgentCommunityAssignment


logger = logging.getLogger(__name__)


class AgentPermissionError(Exception):
    """Base exception for agent permission errors."""
    pass


class AgentPermissionUtils:
    """
    Utility class for agent permission operations.
    
    This class provides static methods for common permission checking
    and validation operations that can be used throughout the application.
    """
    
    # Standard permission definitions
    STANDARD_PERMISSIONS = {
        # Community management permissions
        'edit_community': {
            'name': 'Edit Community',
            'description': 'Modify community settings and information',
            'category': 'community_management'
        },
        'moderate_users': {
            'name': 'Moderate Users',
            'description': 'Manage community members and moderation actions',
            'category': 'user_management'
        },
        'fetch_metrics': {
            'name': 'Fetch Metrics',
            'description': 'Access community analytics and metrics',
            'category': 'analytics'
        },
        'manage_content': {
            'name': 'Manage Content',
            'description': 'Moderate and manage community content',
            'category': 'content_management'
        },
        'send_messages': {
            'name': 'Send Messages',
            'description': 'Send messages and announcements to community',
            'category': 'communication'
        },
        'manage_events': {
            'name': 'Manage Events',
            'description': 'Create and manage community events',
            'category': 'event_management'
        },
        'view_reports': {
            'name': 'View Reports',
            'description': 'Access community reports and insights',
            'category': 'analytics'
        },
        'manage_roles': {
            'name': 'Manage Roles',
            'description': 'Assign and manage community roles',
            'category': 'user_management'
        },
        'delete_content': {
            'name': 'Delete Content',
            'description': 'Remove inappropriate content from community',
            'category': 'content_management'
        },
        'ban_users': {
            'name': 'Ban Users',
            'description': 'Ban users from the community',
            'category': 'user_management'
        }
    }
    
    # Permission hierarchies - higher level permissions include lower level ones
    PERMISSION_HIERARCHIES = {
        'community_admin': ['edit_community', 'moderate_users', 'fetch_metrics', 'manage_content', 
                           'send_messages', 'manage_events', 'view_reports', 'manage_roles', 
                           'delete_content', 'ban_users'],
        'community_moderator': ['moderate_users', 'manage_content', 'delete_content', 'ban_users'],
        'community_assistant': ['fetch_metrics', 'view_reports', 'send_messages']
    }
    
    @staticmethod
    def get_permission_info(permission: str) -> Dict[str, Any]:
        """
        Get information about a specific permission.
        
        Args:
            permission: The permission to get info for
            
        Returns:
            Dict containing permission information
        """
        return AgentPermissionUtils.STANDARD_PERMISSIONS.get(permission, {
            'name': permission.replace('_', ' ').title(),
            'description': f'Custom permission: {permission}',
            'category': 'custom'
        })
    
    @staticmethod
    def expand_permission_hierarchy(permissions: List[str]) -> List[str]:
        """
        Expand permission hierarchies to include all implied permissions.
        
        Args:
            permissions: List of permissions to expand
            
        Returns:
            List of expanded permissions
        """
        expanded = set(permissions)
        
        for permission in permissions:
            if permission in AgentPermissionUtils.PERMISSION_HIERARCHIES:
                expanded.update(AgentPermissionUtils.PERMISSION_HIERARCHIES[permission])
        
        return list(expanded)
    
    @staticmethod
    def validate_permissions(permissions: List[str]) -> List[str]:
        """
        Validate a list of permissions and return any invalid ones.
        
        Args:
            permissions: List of permissions to validate
            
        Returns:
            List of invalid permissions
        """
        valid_permissions = set(AgentPermissionUtils.STANDARD_PERMISSIONS.keys())
        valid_permissions.update(AgentPermissionUtils.PERMISSION_HIERARCHIES.keys())
        
        invalid_permissions = []
        for permission in permissions:
            if permission not in valid_permissions and not permission.startswith('custom_'):
                invalid_permissions.append(permission)
        
        return invalid_permissions
    
    @staticmethod
    def get_permissions_by_category(category: str) -> List[str]:
        """
        Get all permissions in a specific category.
        
        Args:
            category: The category to filter by
            
        Returns:
            List of permissions in the category
        """
        return [
            perm for perm, info in AgentPermissionUtils.STANDARD_PERMISSIONS.items()
            if info.get('category') == category
        ]
    
    @staticmethod
    def check_agent_permission_sync(agent_uid: str, community_uid: str, permission: str) -> bool:
        """
        Synchronously check if an agent has a specific permission.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            permission: Permission to check
            
        Returns:
            bool: True if agent has permission, False otherwise
        """
        try:
            auth_service = AgentAuthService()
            return auth_service.check_permission(agent_uid, community_uid, permission)
        except Exception as e:
            logger.error(f"Error checking permission {permission} for agent {agent_uid}: {str(e)}")
            return False
    
    @staticmethod
    def get_agent_effective_permissions(agent_uid: str, community_uid: str) -> List[str]:
        """
        Get all effective permissions for an agent in a community.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            
        Returns:
            List of effective permissions
        """
        try:
            auth_service = AgentAuthService()
            return auth_service.get_agent_permissions(agent_uid, community_uid)
        except Exception as e:
            logger.error(f"Error getting permissions for agent {agent_uid}: {str(e)}")
            return []
    
    @staticmethod
    def create_permission_matrix(agents: List[str], communities: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """
        Create a permission matrix for multiple agents and communities.
        
        Args:
            agents: List of agent UIDs
            communities: List of community UIDs
            
        Returns:
            Dict mapping agent_uid -> community_uid -> permissions
        """
        matrix = {}
        
        for agent_uid in agents:
            matrix[agent_uid] = {}
            for community_uid in communities:
                matrix[agent_uid][community_uid] = AgentPermissionUtils.get_agent_effective_permissions(
                    agent_uid, community_uid
                )
        
        return matrix


def agent_required(func: Callable) -> Callable:
    """
    Decorator to require that the current user is an agent.
    
    This decorator checks that the current user context represents
    an agent rather than a regular user.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract context from GraphQL info or other sources
        info = None
        for arg in args:
            if hasattr(arg, 'context'):
                info = arg
                break
        
        if not info:
            raise AgentPermissionError("No GraphQL context available")
        
        # Check if this is an agent context
        # This would need to be implemented based on how agent authentication is handled
        # For now, we'll assume agent context is marked in the request
        agent_context = getattr(info.context, 'agent_context', None)
        if not agent_context:
            raise AgentPermissionError("Agent context required")
        
        return func(*args, **kwargs)
    
    return wrapper


def require_agent_permission(permission: str, community_uid_param: str = 'community_uid'):
    """
    Decorator to require a specific agent permission.
    
    Args:
        permission: The required permission
        community_uid_param: Name of the parameter containing community UID
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract agent and community UIDs from context
            agent_uid = None
            community_uid = None
            
            # Try to get from GraphQL context
            for arg in args:
                if hasattr(arg, 'context'):
                    agent_context = getattr(arg.context, 'agent_context', None)
                    if agent_context:
                        agent_uid = agent_context.get('agent_uid')
                    break
            
            # Try to get community UID from parameters
            if community_uid_param in kwargs:
                community_uid = kwargs[community_uid_param]
            else:
                # Try to extract from input object
                for arg in args:
                    if hasattr(arg, community_uid_param):
                        community_uid = getattr(arg, community_uid_param)
                        break
            
            if not agent_uid or not community_uid:
                raise AgentPermissionError("Agent UID and Community UID required for permission check")
            
            # Check permission
            if not AgentPermissionUtils.check_agent_permission_sync(agent_uid, community_uid, permission):
                raise AgentAuthorizationError(
                    f"Agent {agent_uid} lacks required permission '{permission}' for community {community_uid}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_agent_permission(permissions: List[str], community_uid_param: str = 'community_uid'):
    """
    Decorator to require any one of multiple agent permissions.
    
    Args:
        permissions: List of acceptable permissions
        community_uid_param: Name of the parameter containing community UID
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract agent and community UIDs (similar to require_agent_permission)
            agent_uid = None
            community_uid = None
            
            for arg in args:
                if hasattr(arg, 'context'):
                    agent_context = getattr(arg.context, 'agent_context', None)
                    if agent_context:
                        agent_uid = agent_context.get('agent_uid')
                    break
            
            if community_uid_param in kwargs:
                community_uid = kwargs[community_uid_param]
            else:
                for arg in args:
                    if hasattr(arg, community_uid_param):
                        community_uid = getattr(arg, community_uid_param)
                        break
            
            if not agent_uid or not community_uid:
                raise AgentPermissionError("Agent UID and Community UID required for permission check")
            
            # Check if agent has any of the required permissions
            has_permission = False
            for permission in permissions:
                if AgentPermissionUtils.check_agent_permission_sync(agent_uid, community_uid, permission):
                    has_permission = True
                    break
            
            if not has_permission:
                raise AgentAuthorizationError(
                    f"Agent {agent_uid} lacks any of the required permissions {permissions} for community {community_uid}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_agent_permission_check(permission: str):
    """
    Decorator to log agent permission checks for audit purposes.
    
    Args:
        permission: The permission being checked
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract context for logging
            agent_uid = None
            community_uid = None
            
            for arg in args:
                if hasattr(arg, 'context'):
                    agent_context = getattr(arg.context, 'agent_context', None)
                    if agent_context:
                        agent_uid = agent_context.get('agent_uid')
                        community_uid = agent_context.get('community_uid')
                    break
            
            # Log the permission check
            logger.info(f"Permission check: {permission} for agent {agent_uid} in community {community_uid}")
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"Permission check successful: {permission}")
                return result
            except AgentAuthorizationError as e:
                logger.warning(f"Permission check failed: {permission} - {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Permission check error: {permission} - {str(e)}")
                raise
        
        return wrapper
    return decorator


class AgentPermissionChecker:
    """
    Context manager for checking multiple agent permissions.
    
    This class provides a convenient way to check multiple permissions
    and collect any authorization errors.
    """
    
    def __init__(self, agent_uid: str, community_uid: str):
        """
        Initialize the permission checker.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
        """
        self.agent_uid = agent_uid
        self.community_uid = community_uid
        self.auth_service = AgentAuthService()
        self.errors = []
    
    def check_permission(self, permission: str) -> bool:
        """
        Check a single permission and record any errors.
        
        Args:
            permission: Permission to check
            
        Returns:
            bool: True if agent has permission, False otherwise
        """
        try:
            has_permission = self.auth_service.check_permission(
                self.agent_uid, self.community_uid, permission
            )
            if not has_permission:
                self.errors.append(f"Missing permission: {permission}")
            return has_permission
        except Exception as e:
            self.errors.append(f"Error checking permission {permission}: {str(e)}")
            return False
    
    def require_permission(self, permission: str) -> None:
        """
        Require a permission and raise error if not present.
        
        Args:
            permission: Required permission
            
        Raises:
            AgentAuthorizationError: If permission is not present
        """
        if not self.check_permission(permission):
            raise AgentAuthorizationError(
                f"Agent {self.agent_uid} lacks required permission '{permission}' for community {self.community_uid}"
            )
    
    def check_any_permission(self, permissions: List[str]) -> bool:
        """
        Check if agent has any of the specified permissions.
        
        Args:
            permissions: List of permissions to check
            
        Returns:
            bool: True if agent has at least one permission, False otherwise
        """
        for permission in permissions:
            if self.check_permission(permission):
                return True
        return False
    
    def require_any_permission(self, permissions: List[str]) -> None:
        """
        Require that agent has at least one of the specified permissions.
        
        Args:
            permissions: List of acceptable permissions
            
        Raises:
            AgentAuthorizationError: If agent has none of the permissions
        """
        if not self.check_any_permission(permissions):
            raise AgentAuthorizationError(
                f"Agent {self.agent_uid} lacks any of the required permissions {permissions} for community {self.community_uid}"
            )
    
    def get_errors(self) -> List[str]:
        """
        Get all permission check errors.
        
        Returns:
            List of error messages
        """
        return self.errors.copy()
    
    def has_errors(self) -> bool:
        """
        Check if there are any permission errors.
        
        Returns:
            bool: True if there are errors, False otherwise
        """
        return len(self.errors) > 0


def create_agent_permission_validator(required_permissions: List[str]):
    """
    Create a permission validator function for specific permissions.
    
    Args:
        required_permissions: List of required permissions
        
    Returns:
        Validator function
    """
    def validator(agent_uid: str, community_uid: str) -> Dict[str, Any]:
        """
        Validate agent permissions and return results.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            
        Returns:
            Dict containing validation results
        """
        checker = AgentPermissionChecker(agent_uid, community_uid)
        
        results = {
            'agent_uid': agent_uid,
            'community_uid': community_uid,
            'required_permissions': required_permissions,
            'has_all_permissions': True,
            'missing_permissions': [],
            'errors': []
        }
        
        for permission in required_permissions:
            if not checker.check_permission(permission):
                results['has_all_permissions'] = False
                results['missing_permissions'].append(permission)
        
        results['errors'] = checker.get_errors()
        
        return results
    
    return validator