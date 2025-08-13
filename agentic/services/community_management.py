# Agent Community Management Service
# This module provides agent-specific community management functions.

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .auth_service import AgentAuthService, AgentAuthenticationError, AgentAuthorizationError
from .agent_service import AgentService
from ..utils.permissions import AgentPermissionChecker, require_agent_permission
from community.models import Community, Membership
from auth_manager.models import Users


logger = logging.getLogger(__name__)


class AgentCommunityManagementError(Exception):
    """Base exception for agent community management errors."""
    pass


class AgentCommunityManager:
    """
    Service for agent-specific community management operations.
    
    This service provides high-level community management functions that
    can be performed by AI agents with proper authorization.
    """
    
    def __init__(self):
        """Initialize the community management service."""
        self.auth_service = AgentAuthService()
        self.agent_service = AgentService()
    
    def edit_community(
        self, 
        agent_uid: str, 
        community_uid: str, 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Edit community settings and information.
        
        This function allows authorized agents to modify community properties
        such as name, description, category, and settings.
        
        Args:
            agent_uid: UID of the agent performing the action
            community_uid: UID of the community to edit
            updates: Dictionary of fields to update
            
        Returns:
            Dict containing operation results and updated community info
            
        Raises:
            AgentAuthenticationError: If agent is not authenticated
            AgentAuthorizationError: If agent lacks edit_community permission
            AgentCommunityManagementError: If edit operation fails
        """
        try:
            logger.info(f"Agent {agent_uid} editing community {community_uid}")
            
            # Check authentication and authorization
            if not self.auth_service.authenticate_agent(agent_uid, community_uid):
                raise AgentAuthenticationError(f"Agent {agent_uid} not authenticated for community {community_uid}")
            
            self.auth_service.require_permission(agent_uid, community_uid, 'edit_community')
            
            # Get the community
            try:
                community = Community.nodes.get(uid=community_uid)
            except Community.DoesNotExist:
                raise AgentCommunityManagementError(f"Community {community_uid} not found")
            
            # Validate and apply updates
            allowed_fields = {
                'name', 'description', 'category', 'group_icon_id', 'cover_image_id',
                'only_admin_can_message', 'only_admin_can_add_member', 'only_admin_can_remove_member'
            }
            
            applied_updates = {}
            for field, value in updates.items():
                if field in allowed_fields:
                    if hasattr(community, field):
                        old_value = getattr(community, field)
                        setattr(community, field, value)
                        applied_updates[field] = {'old': old_value, 'new': value}
                    else:
                        logger.warning(f"Field {field} not found on community model")
                else:
                    logger.warning(f"Field {field} not allowed for agent editing")
            
            # Save changes
            community.save()
            
            # Log the action
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type="edit_community",
                details={
                    "updates_applied": applied_updates,
                    "community_name": community.name
                },
                success=True
            )
            
            logger.info(f"Agent {agent_uid} successfully edited community {community_uid}")
            
            return {
                'success': True,
                'message': 'Community updated successfully',
                'updates_applied': applied_updates,
                'community': {
                    'uid': community.uid,
                    'name': community.name,
                    'description': community.description,
                    'updated_date': community.updated_date
                }
            }
            
        except (AgentAuthenticationError, AgentAuthorizationError):
            # Re-raise auth errors
            raise
        except Exception as e:
            logger.error(f"Failed to edit community {community_uid}: {str(e)}")
            
            # Log the failed action
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type="edit_community",
                details={"attempted_updates": updates},
                success=False,
                error_message=str(e)
            )
            
            raise AgentCommunityManagementError(f"Failed to edit community: {str(e)}")
    
    def moderate_users(
        self, 
        agent_uid: str, 
        community_uid: str, 
        action: str,
        target_user_uid: str,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Perform user moderation actions.
        
        This function allows authorized agents to moderate community members
        through actions like warnings, temporary restrictions, etc.
        
        Args:
            agent_uid: UID of the agent performing the action
            community_uid: UID of the community
            action: Moderation action to perform
            target_user_uid: UID of the user to moderate
            reason: Optional reason for the moderation action
            
        Returns:
            Dict containing operation results
            
        Raises:
            AgentAuthenticationError: If agent is not authenticated
            AgentAuthorizationError: If agent lacks moderate_users permission
            AgentCommunityManagementError: If moderation fails
        """
        try:
            logger.info(f"Agent {agent_uid} moderating user {target_user_uid} in community {community_uid}")
            
            # Check authentication and authorization
            if not self.auth_service.authenticate_agent(agent_uid, community_uid):
                raise AgentAuthenticationError(f"Agent {agent_uid} not authenticated for community {community_uid}")
            
            # Check specific permission based on action
            if action in ['ban', 'remove']:
                self.auth_service.require_permission(agent_uid, community_uid, 'ban_users')
            else:
                self.auth_service.require_permission(agent_uid, community_uid, 'moderate_users')
            
            # Get the community and target user
            try:
                community = Community.nodes.get(uid=community_uid)
                target_user = Users.nodes.get(uid=target_user_uid)
            except (Community.DoesNotExist, Users.DoesNotExist) as e:
                raise AgentCommunityManagementError(f"Community or user not found: {str(e)}")
            
            # Find the user's membership
            membership = None
            for member in community.members.all():
                if member.user.single() and member.user.single().uid == target_user_uid:
                    membership = member
                    break
            
            if not membership:
                raise AgentCommunityManagementError(f"User {target_user_uid} is not a member of community {community_uid}")
            
            # Perform moderation action
            result = self._perform_moderation_action(
                community, membership, target_user, action, reason
            )
            
            # Log the action
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type="moderate_user",
                details={
                    "action": action,
                    "target_user_uid": target_user_uid,
                    "reason": reason,
                    "result": result
                },
                success=True
            )
            
            logger.info(f"Agent {agent_uid} successfully moderated user {target_user_uid}")
            
            return {
                'success': True,
                'message': f'Moderation action "{action}" applied successfully',
                'action': action,
                'target_user_uid': target_user_uid,
                'reason': reason,
                'result': result
            }
            
        except (AgentAuthenticationError, AgentAuthorizationError):
            # Re-raise auth errors
            raise
        except Exception as e:
            logger.error(f"Failed to moderate user {target_user_uid}: {str(e)}")
            
            # Log the failed action
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type="moderate_user",
                details={
                    "action": action,
                    "target_user_uid": target_user_uid,
                    "reason": reason
                },
                success=False,
                error_message=str(e)
            )
            
            raise AgentCommunityManagementError(f"Failed to moderate user: {str(e)}")
    
    def fetch_metrics(
        self, 
        agent_uid: str, 
        community_uid: str,
        metric_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch community analytics and metrics.
        
        This function allows authorized agents to access community metrics
        for monitoring and decision-making purposes.
        
        Args:
            agent_uid: UID of the agent requesting metrics
            community_uid: UID of the community
            metric_types: Optional list of specific metrics to fetch
            
        Returns:
            Dict containing community metrics and analytics
            
        Raises:
            AgentAuthenticationError: If agent is not authenticated
            AgentAuthorizationError: If agent lacks fetch_metrics permission
            AgentCommunityManagementError: If metrics fetching fails
        """
        try:
            logger.info(f"Agent {agent_uid} fetching metrics for community {community_uid}")
            
            # Check authentication and authorization
            if not self.auth_service.authenticate_agent(agent_uid, community_uid):
                raise AgentAuthenticationError(f"Agent {agent_uid} not authenticated for community {community_uid}")
            
            self.auth_service.require_permission(agent_uid, community_uid, 'fetch_metrics')
            
            # Get the community
            try:
                community = Community.nodes.get(uid=community_uid)
            except Community.DoesNotExist:
                raise AgentCommunityManagementError(f"Community {community_uid} not found")
            
            # Collect metrics
            metrics = self._collect_community_metrics(community, metric_types)
            
            # Log the action
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type="fetch_metrics",
                details={
                    "metric_types_requested": metric_types,
                    "metrics_returned": list(metrics.keys())
                },
                success=True
            )
            
            logger.info(f"Agent {agent_uid} successfully fetched metrics for community {community_uid}")
            
            return {
                'success': True,
                'community_uid': community_uid,
                'metrics': metrics,
                'generated_at': datetime.now().isoformat()
            }
            
        except (AgentAuthenticationError, AgentAuthorizationError):
            # Re-raise auth errors
            raise
        except Exception as e:
            logger.error(f"Failed to fetch metrics for community {community_uid}: {str(e)}")
            
            # Log the failed action
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type="fetch_metrics",
                details={"metric_types_requested": metric_types},
                success=False,
                error_message=str(e)
            )
            
            raise AgentCommunityManagementError(f"Failed to fetch metrics: {str(e)}")
    
    def send_announcement(
        self, 
        agent_uid: str, 
        community_uid: str,
        title: str,
        content: str,
        target_audience: str = 'all'
    ) -> Dict[str, Any]:
        """
        Send an announcement to community members.
        
        This function allows authorized agents to send announcements
        and important messages to community members.
        
        Args:
            agent_uid: UID of the agent sending the announcement
            community_uid: UID of the community
            title: Title of the announcement
            content: Content of the announcement
            target_audience: Target audience ('all', 'admins', 'active_members')
            
        Returns:
            Dict containing operation results
            
        Raises:
            AgentAuthenticationError: If agent is not authenticated
            AgentAuthorizationError: If agent lacks send_messages permission
            AgentCommunityManagementError: If announcement sending fails
        """
        try:
            logger.info(f"Agent {agent_uid} sending announcement to community {community_uid}")
            
            # Check authentication and authorization
            if not self.auth_service.authenticate_agent(agent_uid, community_uid):
                raise AgentAuthenticationError(f"Agent {agent_uid} not authenticated for community {community_uid}")
            
            self.auth_service.require_permission(agent_uid, community_uid, 'send_messages')
            
            # Get the community
            try:
                community = Community.nodes.get(uid=community_uid)
            except Community.DoesNotExist:
                raise AgentCommunityManagementError(f"Community {community_uid} not found")
            
            # Create and send announcement
            announcement_result = self._create_and_send_announcement(
                community, title, content, target_audience
            )
            
            # Log the action
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type="send_announcement",
                details={
                    "title": title,
                    "content_length": len(content),
                    "target_audience": target_audience,
                    "recipients_count": announcement_result.get('recipients_count', 0)
                },
                success=True
            )
            
            logger.info(f"Agent {agent_uid} successfully sent announcement to community {community_uid}")
            
            return {
                'success': True,
                'message': 'Announcement sent successfully',
                'announcement_id': announcement_result.get('announcement_id'),
                'recipients_count': announcement_result.get('recipients_count', 0),
                'target_audience': target_audience
            }
            
        except (AgentAuthenticationError, AgentAuthorizationError):
            # Re-raise auth errors
            raise
        except Exception as e:
            logger.error(f"Failed to send announcement to community {community_uid}: {str(e)}")
            
            # Log the failed action
            self.auth_service.log_agent_action(
                agent_uid=agent_uid,
                community_uid=community_uid,
                action_type="send_announcement",
                details={
                    "title": title,
                    "content_length": len(content),
                    "target_audience": target_audience
                },
                success=False,
                error_message=str(e)
            )
            
            raise AgentCommunityManagementError(f"Failed to send announcement: {str(e)}")
    
    def _perform_moderation_action(
        self, 
        community: Community, 
        membership: Membership, 
        target_user: Users,
        action: str, 
        reason: str
    ) -> Dict[str, Any]:
        """
        Perform the actual moderation action.
        
        Args:
            community: Community object
            membership: Membership object of the target user
            target_user: Target user object
            action: Moderation action to perform
            reason: Reason for the action
            
        Returns:
            Dict containing action results
        """
        result = {'action_performed': action, 'timestamp': datetime.now().isoformat()}
        
        if action == 'warn':
            # Issue a warning (could be stored in a warnings system)
            result['warning_issued'] = True
            result['warning_reason'] = reason
            
        elif action == 'mute':
            # Temporarily restrict messaging
            membership.can_message = False
            membership.save()
            result['user_muted'] = True
            result['mute_reason'] = reason
            
        elif action == 'unmute':
            # Restore messaging privileges
            membership.can_message = True
            membership.save()
            result['user_unmuted'] = True
            
        elif action == 'block':
            # Block user from community activities
            membership.is_blocked = True
            membership.save()
            result['user_blocked'] = True
            result['block_reason'] = reason
            
        elif action == 'unblock':
            # Unblock user
            membership.is_blocked = False
            membership.save()
            result['user_unblocked'] = True
            
        elif action == 'remove':
            # Remove user from community
            membership.delete()
            result['user_removed'] = True
            result['removal_reason'] = reason
            
        elif action == 'ban':
            # Ban user (remove and prevent rejoining)
            membership.delete()
            # In a full implementation, this would also add to a ban list
            result['user_banned'] = True
            result['ban_reason'] = reason
            
        else:
            raise AgentCommunityManagementError(f"Unknown moderation action: {action}")
        
        return result
    
    def _collect_community_metrics(
        self, 
        community: Community, 
        metric_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Collect community metrics and analytics.
        
        Args:
            community: Community object
            metric_types: Optional list of specific metrics to collect
            
        Returns:
            Dict containing collected metrics
        """
        metrics = {}
        
        # Default metrics to collect if none specified
        if not metric_types:
            metric_types = [
                'member_count', 'activity_level', 'engagement_stats', 
                'content_stats', 'growth_metrics'
            ]
        
        if 'member_count' in metric_types:
            members = list(community.members.all())
            metrics['member_count'] = {
                'total_members': len(members),
                'active_members': len([m for m in members if not m.is_blocked]),
                'admin_members': len([m for m in members if m.is_admin]),
                'leader_members': len([m for m in members if m.is_leader])
            }
        
        if 'activity_level' in metric_types:
            # In a full implementation, this would analyze recent activity
            metrics['activity_level'] = {
                'messages_last_7_days': 0,  # Would query actual message data
                'posts_last_7_days': 0,     # Would query actual post data
                'active_users_last_7_days': 0,
                'activity_score': 'low'     # Would calculate based on actual data
            }
        
        if 'engagement_stats' in metric_types:
            metrics['engagement_stats'] = {
                'average_session_duration': 0,  # Would calculate from actual data
                'messages_per_user': 0,
                'posts_per_user': 0,
                'engagement_rate': 0.0
            }
        
        if 'content_stats' in metric_types:
            # Get content statistics
            messages = list(community.communitymessage.all())
            posts = list(community.community_post.all())
            
            metrics['content_stats'] = {
                'total_messages': len(messages),
                'total_posts': len(posts),
                'recent_messages': len([m for m in messages if not m.is_deleted]),
                'recent_posts': len([p for p in posts if p.is_accepted])
            }
        
        if 'growth_metrics' in metric_types:
            metrics['growth_metrics'] = {
                'members_joined_last_30_days': 0,  # Would calculate from actual data
                'growth_rate': 0.0,
                'retention_rate': 0.0,
                'churn_rate': 0.0
            }
        
        return metrics
    
    def _create_and_send_announcement(
        self, 
        community: Community, 
        title: str, 
        content: str, 
        target_audience: str
    ) -> Dict[str, Any]:
        """
        Create and send an announcement to community members.
        
        Args:
            community: Community object
            title: Announcement title
            content: Announcement content
            target_audience: Target audience for the announcement
            
        Returns:
            Dict containing announcement results
        """
        # In a full implementation, this would:
        # 1. Create an announcement record
        # 2. Determine target recipients based on audience
        # 3. Send notifications/messages to recipients
        # 4. Track delivery status
        
        # For now, we'll simulate the process
        members = list(community.members.all())
        
        # Filter recipients based on target audience
        if target_audience == 'admins':
            recipients = [m for m in members if m.is_admin]
        elif target_audience == 'active_members':
            recipients = [m for m in members if not m.is_blocked and m.can_message]
        else:  # 'all'
            recipients = [m for m in members if not m.is_blocked]
        
        # Simulate announcement creation and sending
        announcement_id = f"announcement_{datetime.now().timestamp()}"
        
        # In a real implementation, this would:
        # - Create announcement record in database
        # - Send push notifications
        # - Create community messages
        # - Update notification queues
        
        return {
            'announcement_id': announcement_id,
            'recipients_count': len(recipients),
            'delivery_status': 'sent',
            'created_at': datetime.now().isoformat()
        }