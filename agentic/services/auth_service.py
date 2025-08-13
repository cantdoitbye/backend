# Agent Authentication and Authorization Service
# This module provides authentication and authorization services for AI agents.
# It handles agent access control, permission validation, and action logging.

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..models import Agent, AgentCommunityAssignment, AgentActionLog
from community.models import Community


logger = logging.getLogger(__name__)


class AgentAuthError(Exception):
    """Base exception for agent authentication errors."""
    pass


class AgentAuthenticationError(AgentAuthError):
    """Raised when agent authentication fails."""
    pass


class AgentAuthorizationError(AgentAuthError):
    """Raised when agent lacks required permissions."""
    pass


class AgentAuthService:
    """
    Handles agent authentication and authorization.
    
    This service provides comprehensive access control for AI agents, including:
    - Agent authentication and session validation
    - Permission checking and authorization
    - Action logging and audit trail
    - Security policy enforcement
    
    The service ensures that agents can only perform actions they are authorized
    for within their assigned communities, maintaining security and audit compliance.
    """
    
    # Standard agent capabilities and their descriptions
    STANDARD_CAPABILITIES = {
        'edit_community': 'Modify community settings and information',
        'moderate_users': 'Manage community members and moderation actions',
        'fetch_metrics': 'Access community analytics and metrics',
        'manage_content': 'Moderate and manage community content',
        'send_messages': 'Send messages and announcements to community',
        'manage_events': 'Create and manage community events',
        'view_reports': 'Access community reports and insights',
        'manage_roles': 'Assign and manage community roles',
        'delete_content': 'Remove inappropriate content from community',
        'ban_users': 'Ban users from the community'
    }
    
    def authenticate_agent(self, agent_uid: str, community_uid: str) -> bool:
        """
        Verify agent has access to specified community.
        
        This method validates that:
        1. The agent exists and is active
        2. The community exists
        3. The agent has an active assignment to the community
        
        Args:
            agent_uid: UID of the agent to authenticate
            community_uid: UID of the community to check access for
            
        Returns:
            bool: True if agent is authenticated for the community, False otherwise
            
        Raises:
            AgentAuthenticationError: If authentication fails due to invalid agent or community
        """
        try:
            logger.debug(f"Authenticating agent {agent_uid} for community {community_uid}")
            
            # Validate agent exists and is active
            try:
                agent = Agent.nodes.get(uid=agent_uid)
            except Agent.DoesNotExist:
                logger.warning(f"Authentication failed: Agent {agent_uid} not found")
                raise AgentAuthenticationError(f"Agent {agent_uid} not found")
            
            if not agent.is_active():
                logger.warning(f"Authentication failed: Agent {agent_uid} is not active (status: {agent.status})")
                raise AgentAuthenticationError(f"Agent {agent_uid} is not active")
            
            # Validate community exists
            try:
                community = Community.nodes.get(uid=community_uid)
            except Community.DoesNotExist:
                logger.warning(f"Authentication failed: Community {community_uid} not found")
                raise AgentAuthenticationError(f"Community {community_uid} not found")
            
            # Check if agent has active assignment to this community
            assignments = agent.assigned_communities.all()
            for assignment in assignments:
                assignment_community = assignment.community.single()
                if (assignment_community and 
                    assignment_community.uid == community_uid and 
                    assignment.is_active()):
                    
                    logger.debug(f"Agent {agent_uid} authenticated for community {community_uid}")
                    return True
            
            logger.warning(f"Authentication failed: Agent {agent_uid} has no active assignment to community {community_uid}")
            return False
            
        except AgentAuthenticationError:
            # Re-raise authentication errors
            raise
        except Exception as e:
            logger.error(f"Authentication error for agent {agent_uid} in community {community_uid}: {str(e)}")
            raise AgentAuthenticationError(f"Authentication failed: {str(e)}")
    
    def get_agent_permissions(self, agent_uid: str, community_uid: str) -> List[str]:
        """
        Get list of permissions for agent in specific community.
        
        This method combines the agent's base capabilities with any assignment-specific
        permissions to provide the complete list of what the agent can do in the community.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            
        Returns:
            List[str]: List of permissions the agent has in the community
            
        Raises:
            AgentAuthenticationError: If agent is not authenticated for the community
        """
        try:
            logger.debug(f"Getting permissions for agent {agent_uid} in community {community_uid}")
            
            # First authenticate the agent
            if not self.authenticate_agent(agent_uid, community_uid):
                raise AgentAuthenticationError(f"Agent {agent_uid} not authenticated for community {community_uid}")
            
            # Get the agent and find the relevant assignment
            agent = Agent.nodes.get(uid=agent_uid)
            assignments = agent.assigned_communities.all()
            
            for assignment in assignments:
                assignment_community = assignment.community.single()
                if (assignment_community and 
                    assignment_community.uid == community_uid and 
                    assignment.is_active()):
                    
                    # Get effective permissions from the assignment
                    permissions = assignment.get_effective_permissions()
                    logger.debug(f"Agent {agent_uid} has {len(permissions)} permissions in community {community_uid}")
                    return permissions
            
            # This shouldn't happen if authentication passed, but handle gracefully
            logger.warning(f"No active assignment found for authenticated agent {agent_uid} in community {community_uid}")
            return []
            
        except AgentAuthenticationError:
            # Re-raise authentication errors
            raise
        except Exception as e:
            logger.error(f"Error getting permissions for agent {agent_uid} in community {community_uid}: {str(e)}")
            raise AgentAuthError(f"Failed to get agent permissions: {str(e)}")
    
    def check_permission(self, agent_uid: str, community_uid: str, permission: str) -> bool:
        """
        Check if agent has specific permission in community.
        
        This is a convenience method that checks for a single permission
        without retrieving the full permissions list.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            permission: The specific permission to check for
            
        Returns:
            bool: True if agent has the permission, False otherwise
            
        Raises:
            AgentAuthenticationError: If agent is not authenticated for the community
        """
        try:
            logger.debug(f"Checking permission '{permission}' for agent {agent_uid} in community {community_uid}")
            
            permissions = self.get_agent_permissions(agent_uid, community_uid)
            has_permission = permission in permissions
            
            logger.debug(f"Agent {agent_uid} {'has' if has_permission else 'does not have'} permission '{permission}' in community {community_uid}")
            return has_permission
            
        except Exception as e:
            logger.error(f"Error checking permission '{permission}' for agent {agent_uid} in community {community_uid}: {str(e)}")
            # For security, default to no permission on error
            return False
    
    def require_permission(self, agent_uid: str, community_uid: str, permission: str) -> None:
        """
        Require that an agent has a specific permission, raising an exception if not.
        
        This method is useful for enforcing permissions at the start of operations
        that require specific capabilities.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            permission: The required permission
            
        Raises:
            AgentAuthorizationError: If agent lacks the required permission
            AgentAuthenticationError: If agent is not authenticated for the community
        """
        if not self.check_permission(agent_uid, community_uid, permission):
            logger.warning(f"Authorization failed: Agent {agent_uid} lacks permission '{permission}' in community {community_uid}")
            raise AgentAuthorizationError(
                f"Agent {agent_uid} lacks required permission '{permission}' for community {community_uid}"
            )
    
    def log_agent_action(
        self, 
        agent_uid: str, 
        community_uid: str, 
        action_type: str, 
        details: Dict[str, Any],
        success: bool,
        error_message: str = None,
        execution_time_ms: int = None,
        user_context: Dict[str, Any] = None
    ) -> AgentActionLog:
        """
        Log agent action for audit trail.
        
        This method creates a comprehensive audit log entry for every action
        performed by an agent, supporting compliance and debugging requirements.
        
        Args:
            agent_uid: UID of the agent that performed the action
            community_uid: UID of the community where action was performed
            action_type: Type of action performed (e.g., 'edit_community', 'moderate_user')
            details: Detailed information about the action
            success: Whether the action succeeded
            error_message: Error details if action failed
            execution_time_ms: How long the action took to execute
            user_context: Additional context information
            
        Returns:
            AgentActionLog: The created log entry
        """
        try:
            logger.debug(f"Logging action '{action_type}' by agent {agent_uid} in community {community_uid}")
            
            log_entry = AgentActionLog.objects.create(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type=action_type,
                action_details=details or {},
                success=success,
                error_message=error_message,
                execution_time_ms=execution_time_ms,
                user_context=user_context or {}
            )
            
            logger.info(f"Logged action '{action_type}' by agent {agent_uid}: {'SUCCESS' if success else 'FAILED'}")
            return log_entry
            
        except Exception as e:
            logger.error(f"Failed to log action '{action_type}' by agent {agent_uid}: {str(e)}")
            # Don't raise exception for logging failures to avoid breaking the main operation
            return None
    
    def get_agent_action_history(
        self, 
        agent_uid: str, 
        community_uid: str = None,
        action_type: str = None,
        limit: int = 100
    ) -> List[AgentActionLog]:
        """
        Get action history for an agent.
        
        Args:
            agent_uid: UID of the agent
            community_uid: Optional community UID to filter by
            action_type: Optional action type to filter by
            limit: Maximum number of log entries to return
            
        Returns:
            List[AgentActionLog]: List of action log entries
        """
        try:
            logger.debug(f"Getting action history for agent {agent_uid}")
            
            # Build query filters
            filters = {'agent_uid': agent_uid}
            if community_uid:
                filters['community_uid'] = community_uid
            if action_type:
                filters['action_type'] = action_type
            
            # Get log entries
            logs = AgentActionLog.objects.filter(**filters).order_by('-timestamp')[:limit]
            
            logger.debug(f"Retrieved {len(logs)} action log entries for agent {agent_uid}")
            return list(logs)
            
        except Exception as e:
            logger.error(f"Error getting action history for agent {agent_uid}: {str(e)}")
            return []
    
    def validate_action_permission(
        self, 
        agent_uid: str, 
        community_uid: str, 
        action_type: str
    ) -> bool:
        """
        Validate that an agent has permission to perform a specific action type.
        
        This method maps action types to required permissions and validates
        that the agent has the necessary capabilities.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            action_type: Type of action to validate
            
        Returns:
            bool: True if agent can perform the action, False otherwise
        """
        try:
            logger.debug(f"Validating action '{action_type}' for agent {agent_uid} in community {community_uid}")
            
            # Map action types to required permissions
            action_permission_map = {
                'edit_community': 'edit_community',
                'update_community_description': 'edit_community',
                'update_community_settings': 'edit_community',
                'moderate_user': 'moderate_users',
                'ban_user': 'ban_users',
                'remove_user': 'moderate_users',
                'delete_message': 'delete_content',
                'delete_post': 'delete_content',
                'send_announcement': 'send_messages',
                'create_event': 'manage_events',
                'get_community_metrics': 'fetch_metrics',
                'view_community_reports': 'view_reports',
                'assign_role': 'manage_roles'
            }
            
            required_permission = action_permission_map.get(action_type)
            if not required_permission:
                logger.warning(f"Unknown action type '{action_type}' - defaulting to deny")
                return False
            
            # Check if agent has the required permission
            has_permission = self.check_permission(agent_uid, community_uid, required_permission)
            
            logger.debug(f"Agent {agent_uid} {'can' if has_permission else 'cannot'} perform action '{action_type}' in community {community_uid}")
            return has_permission
            
        except Exception as e:
            logger.error(f"Error validating action '{action_type}' for agent {agent_uid}: {str(e)}")
            # For security, default to deny on error
            return False
    
    def get_available_actions(self, agent_uid: str, community_uid: str) -> List[str]:
        """
        Get list of actions the agent can perform in the community.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            
        Returns:
            List[str]: List of action types the agent can perform
            
        Raises:
            AgentAuthenticationError: If agent is not authenticated for the community
        """
        try:
            logger.debug(f"Getting available actions for agent {agent_uid} in community {community_uid}")
            
            permissions = self.get_agent_permissions(agent_uid, community_uid)
            
            # Map permissions to available actions
            permission_action_map = {
                'edit_community': ['edit_community', 'update_community_description', 'update_community_settings'],
                'moderate_users': ['moderate_user', 'remove_user'],
                'ban_users': ['ban_user'],
                'delete_content': ['delete_message', 'delete_post'],
                'send_messages': ['send_announcement'],
                'manage_events': ['create_event'],
                'fetch_metrics': ['get_community_metrics'],
                'view_reports': ['view_community_reports'],
                'manage_roles': ['assign_role']
            }
            
            available_actions = []
            for permission in permissions:
                actions = permission_action_map.get(permission, [])
                available_actions.extend(actions)
            
            # Remove duplicates and sort
            available_actions = sorted(list(set(available_actions)))
            
            logger.debug(f"Agent {agent_uid} can perform {len(available_actions)} actions in community {community_uid}")
            return available_actions
            
        except Exception as e:
            logger.error(f"Error getting available actions for agent {agent_uid} in community {community_uid}: {str(e)}")
            return []
    
    def is_agent_admin(self, agent_uid: str, community_uid: str) -> bool:
        """
        Check if agent has administrative privileges in the community.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            
        Returns:
            bool: True if agent has admin privileges, False otherwise
        """
        try:
            # Admin agents typically have edit_community and moderate_users permissions
            admin_permissions = ['edit_community', 'moderate_users']
            agent_permissions = self.get_agent_permissions(agent_uid, community_uid)
            
            # Check if agent has all admin permissions
            has_admin_perms = all(perm in agent_permissions for perm in admin_permissions)
            
            logger.debug(f"Agent {agent_uid} {'has' if has_admin_perms else 'does not have'} admin privileges in community {community_uid}")
            return has_admin_perms
            
        except Exception as e:
            logger.error(f"Error checking admin status for agent {agent_uid} in community {community_uid}: {str(e)}")
            return False
    
    def get_permission_description(self, permission: str) -> str:
        """
        Get human-readable description of a permission.
        
        Args:
            permission: The permission to describe
            
        Returns:
            str: Description of the permission
        """
        return self.STANDARD_CAPABILITIES.get(permission, f"Custom permission: {permission}")
    
    def audit_agent_access(self, agent_uid: str, community_uid: str) -> Dict[str, Any]:
        """
        Generate comprehensive audit report for agent access to community.
        
        Args:
            agent_uid: UID of the agent
            community_uid: UID of the community
            
        Returns:
            Dict[str, Any]: Audit report with agent access details
        """
        try:
            logger.debug(f"Generating audit report for agent {agent_uid} in community {community_uid}")
            
            # Get basic authentication status
            is_authenticated = self.authenticate_agent(agent_uid, community_uid)
            
            if not is_authenticated:
                return {
                    'agent_uid': agent_uid,
                    'community_uid': community_uid,
                    'authenticated': False,
                    'permissions': [],
                    'available_actions': [],
                    'is_admin': False,
                    'audit_timestamp': datetime.now().isoformat()
                }
            
            # Get detailed access information
            permissions = self.get_agent_permissions(agent_uid, community_uid)
            available_actions = self.get_available_actions(agent_uid, community_uid)
            is_admin = self.is_agent_admin(agent_uid, community_uid)
            
            # Get recent action history
            recent_actions = self.get_agent_action_history(agent_uid, community_uid, limit=10)
            
            audit_report = {
                'agent_uid': agent_uid,
                'community_uid': community_uid,
                'authenticated': True,
                'permissions': permissions,
                'permission_descriptions': {perm: self.get_permission_description(perm) for perm in permissions},
                'available_actions': available_actions,
                'is_admin': is_admin,
                'recent_actions': [
                    {
                        'action_type': log.action_type,
                        'timestamp': log.timestamp.isoformat(),
                        'success': log.success,
                        'error_message': log.error_message
                    }
                    for log in recent_actions
                ],
                'audit_timestamp': datetime.now().isoformat()
            }
            
            logger.debug(f"Generated audit report for agent {agent_uid} in community {community_uid}")
            return audit_report
            
        except Exception as e:
            logger.error(f"Error generating audit report for agent {agent_uid} in community {community_uid}: {str(e)}")
            return {
                'agent_uid': agent_uid,
                'community_uid': community_uid,
                'error': str(e),
                'audit_timestamp': datetime.now().isoformat()
            }